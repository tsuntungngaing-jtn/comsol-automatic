"""Offline, deterministic mesh-aware diagnostics for small 2D triangular exports.

No COMSOL connection, mesh generation, ML training, or scientific certification.
Input arrays must already be aligned by their producer (nodal data, not DOFs).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import uuid

SCHEMA = "mesh-native/0.7.1"
MAX_BYTES = 16 * 1024 * 1024
REQUIRED_IDENTITY = ("case_id", "run_id", "mesh_id", "geometry_hash",
                     "conditions_hash", "coordinate_frame", "coordinate_unit")


class MeshInputError(ValueError):
    """Malformed or inadmissible mesh evidence."""


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MeshInputError(f"{name} must be a finite numeric value")
    try:
        numeric = float(value)
    except (ValueError, OverflowError) as exc:
        raise MeshInputError(f"{name} must be a finite numeric value") from exc
    if not math.isfinite(numeric):
        raise MeshInputError(f"{name} must be a finite numeric value")
    return numeric


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise MeshInputError(f"{name} must be a nonempty string")
    return value


def _triangle_area(a, b, c):
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2


def validate_mesh(document):
    """Validate a limited, explicit nodal triangle schema (not solver validity)."""
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise MeshInputError(f"schema must equal {SCHEMA!r}")
    identity = document.get("identity")
    if not isinstance(identity, dict):
        raise MeshInputError("identity must be an object")
    for key in REQUIRED_IDENTITY:
        _text(identity.get(key), f"identity.{key}")
    nodes = document.get("nodes")
    cells = document.get("cells")
    fields = document.get("fields")
    if not isinstance(nodes, list) or len(nodes) < 3 or len(nodes) > 100000:
        raise MeshInputError("nodes must contain 3..100000 2D coordinates")
    for i, p in enumerate(nodes):
        if not isinstance(p, list) or len(p) != 2:
            raise MeshInputError(f"nodes[{i}] must be [x,y]")
        for j, v in enumerate(p):
            _number(v, f"nodes[{i}][{j}]")
    if not isinstance(cells, list) or not cells or len(cells) > 200000:
        raise MeshInputError("cells must contain 1..200000 triangles")
    areas = []
    for i, tri in enumerate(cells):
        if not isinstance(tri, list) or len(tri) != 3 or any(
            isinstance(k, bool) or not isinstance(k, int) or not 0 <= k < len(nodes) for k in tri
        ) or len(set(tri)) != 3:
            raise MeshInputError(f"cells[{i}] must contain three distinct zero-based node indices")
        area = _triangle_area(*(nodes[k] for k in tri))
        if not math.isfinite(area) or area <= 0:
            raise MeshInputError(f"cells[{i}] is degenerate")
        areas.append(area)
    if not isinstance(fields, dict) or not fields:
        raise MeshInputError("fields must contain at least one named nodal scalar field")
    for name, field in fields.items():
        _text(name, "field name")
        if not isinstance(field, dict):
            raise MeshInputError(f"fields.{name} must be an object")
        _text(field.get("unit"), f"fields.{name}.unit")
        values = field.get("values")
        if not isinstance(values, list) or len(values) != len(nodes):
            raise MeshInputError(f"fields.{name}.values must have exactly {len(nodes)} nodes")
        for i, v in enumerate(values):
            _number(v, f"fields.{name}.values[{i}]")
    xs, ys = zip(*nodes)
    return {
        "status": "INPUT_VALID", "scientific_status": "NOT_RUN", "schema": SCHEMA,
        "identity": dict(identity), "node_count": len(nodes), "triangle_count": len(cells),
        "bounds": [[min(xs), min(ys)], [max(xs), max(ys)]],
        "area_sum": sum(areas), "min_triangle_area": min(areas),
        "fields": {name: item["unit"] for name, item in fields.items()},
        "scope": "Input structure only; overlapping triangles, orientation, solver validity and mesh independence NOT_RUN",
    }


def _interpolate(nodes, cells, values, p, *, inside_epsilon=1e-10):
    """Piecewise-linear triangle interpolation; no extrapolation."""
    x, y = p
    for a, b, c in cells:
        ax, ay = nodes[a]
        bx, by = nodes[b]
        cx, cy = nodes[c]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if den == 0:
            continue  # validation rejects degenerate triangles first
        w0 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / den
        w1 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / den
        w2 = 1 - w0 - w1
        if min(w0, w1, w2) >= -inside_epsilon:
            return w0 * values[a] + w1 * values[b] + w2 * values[c]
    return None


def compare_meshes(reference, candidate, field, *, min_coverage=0.98, max_pairs=2_000_000):
    """Compare nodal scalars by sampling a *reference* triangle mesh at candidate nodes.

    Node-weighted errors are diagnostics only. They are not conservative transfer,
    formal discretization error, or a trained Mesh-Native Tokeniser.
    """
    ref_report = validate_mesh(reference)
    cand_report = validate_mesh(candidate)
    _text(field, "field")
    for name in ("case_id", "geometry_hash", "conditions_hash", "coordinate_frame", "coordinate_unit"):
        if reference["identity"][name] != candidate["identity"][name]:
            return {"status": "BLOCKED", "reason": f"identity.{name} mismatch",
                    "scientific_status": "NOT_RUN"}
    if reference["identity"]["mesh_id"] == candidate["identity"]["mesh_id"]:
        return {"status": "BLOCKED", "reason": "Distinct mesh_id required for cross-mesh diagnosis",
                "scientific_status": "NOT_RUN"}
    if field not in reference["fields"] or field not in candidate["fields"]:
        return {"status": "BLOCKED", "reason": "Requested field missing", "scientific_status": "NOT_RUN"}
    rfield, cfield = reference["fields"][field], candidate["fields"][field]
    if rfield["unit"] != cfield["unit"]:
        return {"status": "BLOCKED", "reason": "Field units differ; no automatic unit conversion",
                "scientific_status": "NOT_RUN"}
    min_coverage = _number(min_coverage, "min_coverage")
    if not 0 < min_coverage <= 1:
        raise MeshInputError("min_coverage must be in (0,1]")
    if isinstance(max_pairs, bool) or not isinstance(max_pairs, int) or max_pairs < 1:
        raise MeshInputError("max_pairs must be a positive integer")
    pairs = len(reference["cells"]) * len(candidate["nodes"])
    if pairs > max_pairs:
        return {"status": "NOT_RUN", "reason": f"Comparison budget exceeded ({pairs}>{max_pairs})",
                "scientific_status": "NOT_RUN"}
    errors, target, unmatched = [], [], 0
    for i, p in enumerate(candidate["nodes"]):
        predicted = _interpolate(reference["nodes"], reference["cells"], rfield["values"], p)
        if predicted is None:
            unmatched += 1
            continue
        value = float(cfield["values"][i])
        errors.append(value - predicted)
        target.append(predicted)
    coverage = len(errors) / len(candidate["nodes"])
    report = {
        "status": "DIAGNOSTIC_ONLY" if coverage >= min_coverage else "INSUFFICIENT_COVERAGE",
        "scientific_status": "NOT_RUN", "field": field, "unit": rfield["unit"],
        "reference_run": reference["identity"]["run_id"], "candidate_run": candidate["identity"]["run_id"],
        "matched_nodes": len(errors), "unmatched_nodes": unmatched,
        "coverage": coverage, "min_coverage": min_coverage,
        "method": "piecewise_linear_reference_triangles_at_candidate_nodes",
        "weighting": "uniform_candidate_nodes (not area/volume weighted)",
        "limitations": "No conservative transfer, mesh independence, physical PASS, geometry proof or ML/MNC training",
        "reference_summary": {"nodes": ref_report["node_count"], "cells": ref_report["triangle_count"]},
        "candidate_summary": {"nodes": cand_report["node_count"], "cells": cand_report["triangle_count"]},
    }
    if errors:
        n = len(errors)
        e2 = sum(e * e for e in errors)
        reference_norm = sum(v * v for v in target)
        report["metrics"] = {
            "mae": sum(abs(e) for e in errors) / n,
            "rmse": math.sqrt(e2 / n),
            "max_abs": max(abs(e) for e in errors),
            "relative_l2": math.sqrt(e2 / reference_norm) if reference_norm > 0 else None,
        }
    else:
        report["metrics"] = None
    return report


def load_document(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_BYTES:
        raise MeshInputError("Input must be an existing JSON file at most 16 MiB")
    data = p.read_bytes()
    try:
        doc = json.loads(data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise MeshInputError("Invalid UTF-8 JSON input") from exc
    validate_mesh(doc)
    return doc, hashlib.sha256(data).hexdigest()


def analyze(operation, reference_path, candidate_path=None, field=None, *,
            min_coverage=0.98, max_pairs=2_000_000, output_root=None):
    """Run an offline analysis and optionally persist an immutable evidence report."""
    try:
        reference, ref_hash = load_document(reference_path)
        if operation == "validate":
            if candidate_path is not None:
                raise MeshInputError("validate does not accept candidate_path")
            report = validate_mesh(reference)
            hashes = {"reference_sha256": ref_hash}
        elif operation == "compare":
            if not candidate_path or not field:
                raise MeshInputError("compare requires candidate_path and field")
            candidate, cand_hash = load_document(candidate_path)
            report = compare_meshes(reference, candidate, field,
                                    min_coverage=min_coverage, max_pairs=max_pairs)
            hashes = {"reference_sha256": ref_hash, "candidate_sha256": cand_hash}
        else:
            raise MeshInputError("operation must be validate or compare")
        report = {"operation": operation, **report, "input_hashes": hashes}
        if output_root is not None:
            dest = Path(output_root).resolve() / "mesh-native"
            dest.mkdir(parents=True, exist_ok=True)
            path = dest / ("report-" + uuid.uuid4().hex + ".json")
            path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            report["report_path"] = str(path)
        return report
    except (MeshInputError, OSError) as exc:
        return {"status": "BLOCKED", "scientific_status": "NOT_RUN", "error": str(exc)}


def _in_workspace(path, root):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(Path(root).resolve()):
        raise MeshInputError("Input must be inside COMSOL_OUTPUT_ROOT")
    return resolved


def register_mesh_native_tools(mcp, runtime):
    """Read-only-to-COMSOL MCP adapter; only accesses the configured workspace."""
    @mcp.tool()
    async def mesh_native_analyze(operation: str, reference_path: str,
                                  candidate_path: str | None = None, field: str | None = None,
                                  min_coverage: float = 0.98, max_pairs: int = 2_000_000) -> dict:
        """Offline triangle-nodal mesh schema check or cross-mesh scalar comparison; NOT a COMSOL solve or physical validation. Inputs must reside in COMSOL_OUTPUT_ROOT."""
        try:
            ref = _in_workspace(reference_path, runtime.output_root)
            cand = _in_workspace(candidate_path, runtime.output_root) if candidate_path else None
            return analyze(operation, ref, cand, field, min_coverage=min_coverage,
                           max_pairs=max_pairs, output_root=runtime.output_root)
        except MeshInputError as exc:
            return {"status": "BLOCKED", "scientific_status": "NOT_RUN", "error": str(exc)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline 2D triangular mesh diagnosis (no COMSOL required)")
    parser.add_argument("operation", choices=("validate", "compare"))
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate")
    parser.add_argument("--field")
    parser.add_argument("--min-coverage", type=float, default=0.98)
    parser.add_argument("--max-pairs", type=int, default=2_000_000)
    parser.add_argument("--output-root", help="Optional workspace for immutable reports")
    args = parser.parse_args(argv)
    result = analyze(args.operation, args.reference, args.candidate, args.field,
                     min_coverage=args.min_coverage, max_pairs=args.max_pairs,
                     output_root=args.output_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("INPUT_VALID", "DIAGNOSTIC_ONLY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
