"""Auditable, conservative offline selection among paper-figure extraction configurations.

Inspired by ART of PIV's budgeted algorithm choice; this is NOT its learned
agent, PIV optical flow, automatic ROI discovery, or scientific certification.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from uuid import uuid4

from .figure_analysis import ORIGIN, _axis, _image, _rect, analyze_figure
from .runtime import inside

MAX_CANDIDATES = 6
ALLOWED_OPERATIONS = ("curve", "field")
DEFAULT_MIN_SCORE = 0.75
DEFAULT_MIN_MARGIN = 0.08
_ID = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{0,31}\Z")


def _finite_fraction(value, label, *, allow_zero=True):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not (0 <= number <= 1):
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    if not allow_zero and number == 0:
        raise ValueError(f"{label} must be positive")
    return number


def _policy(values):
    if values is None:
        values = {}
    if not isinstance(values, dict) or set(values) - {"min_score", "min_margin"}:
        raise ValueError("policy may specify only min_score and min_margin")
    return {
        "min_score": _finite_fraction(values.get("min_score", DEFAULT_MIN_SCORE), "min_score"),
        "min_margin": _finite_fraction(values.get("min_margin", DEFAULT_MIN_MARGIN),
                                        "min_margin", allow_zero=False),
    }


def _common(candidate, op):
    """Only compare configurations with identical target/calibration/threshold.

    Candidate selection cannot change the target ROI to cherry-pick agreement.
    """
    s = candidate["spec"]
    if op == "curve":
        keys = ("roi", "x_axis", "y_axis", "rgb_distance_max", "max_vertical_spread_px")
        required = ("roi", "x_axis", "y_axis", "rgb")
    else:
        keys = ("field_roi", "top_value", "bottom_value", "rgb_distance_max")
        required = ("field_roi", "top_value", "bottom_value", "colorbar_roi")
    if any(k not in s for k in required):
        raise ValueError(f"{op} candidate missing required calibration or ROI")
    # Defaulted thresholds must also be comparable across candidates.
    defaults = {"rgb_distance_max": 24 if op == "curve" else 30,
                "max_vertical_spread_px": 5}
    return {k: s.get(k, defaults.get(k)) for k in keys}


def _precheck(image, candidates):
    if not isinstance(candidates, list) or not 2 <= len(candidates) <= MAX_CANDIDATES:
        raise ValueError("Provide 2..6 pre-approved candidate configurations")
    ids = set()
    op = None
    baseline = None
    exact_specs = set()
    for i, item in enumerate(candidates):
        if not isinstance(item, dict) or set(item) != {"id", "operation", "spec"}:
            raise ValueError(f"Candidate {i} must have exactly id, operation, spec")
        cid = item["id"]
        if not isinstance(cid, str) or _ID.fullmatch(cid) is None or cid in ids:
            raise ValueError("Each candidate id must be unique and match [A-Za-z][A-Za-z0-9_-]{0,31}")
        ids.add(cid)
        name = item["operation"]
        if name not in ALLOWED_OPERATIONS or (op is not None and op != name):
            raise ValueError("All candidates must use the same supported operation (curve or field)")
        op = name
        spec = item["spec"]
        if not isinstance(spec, dict):
            raise ValueError("Candidate spec must be an object")
        if op == "curve":
            _rect(spec["roi"], image.width, image.height)
            _axis(0, spec["x_axis"])
            _axis(0, spec["y_axis"])
            color = spec["rgb"]
            if not isinstance(color, (list, tuple)) or len(color) != 3:
                raise ValueError("Each curve candidate needs an RGB triplet")
        else:
            _rect(spec["field_roi"], image.width, image.height)
            _rect(spec["colorbar_roi"], image.width, image.height)
        shared = _common(item, op)
        if baseline is None:
            baseline = shared
        elif shared != baseline:
            raise ValueError("Candidate targets, axes, units or thresholds differ; not comparable")
        token = json.dumps(spec, sort_keys=True, ensure_ascii=False)
        if token in exact_specs:
            raise ValueError("Duplicate candidate configurations are not informative")
        exact_specs.add(token)
    return op, baseline


def _score(operation, result, common):
    if not result.get("success"):
        return None
    if operation == "curve":
        width = common["roi"][2] - common["roi"][0]
        points = result["points"]
        ambiguous = result["ambiguous_columns_skipped"]
        if points <= 0:
            return 0.0
        return max(0.0, (points - ambiguous) / width)
    return float(result["matched_fraction"])


def route_figure(output_root, source_path, candidates, policy=None):
    """Run all comparable candidates and conservatively abstain on near ties.

    The scores are extraction quality proxies, NOT calibrated probabilities or
    measures of scientific accuracy. All outputs remain REVIEW_REQUIRED.
    """
    try:
        root = Path(output_root).resolve()
        source = inside(root, source_path)
        if not source.is_file() or source.suffix.lower() not in (
            ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"
        ):
            raise ValueError("Source must be a raster image inside COMSOL_OUTPUT_ROOT")
        decision_policy = _policy(policy)
        image = _image(source)
        operation, common = _precheck(image, candidates)
        runs = []
        for item in candidates:
            result = analyze_figure(root, operation, str(source), item["spec"])
            runs.append({
                "id": item["id"], "operation": operation,
                "score": _score(operation, result, common),
                "result_status": result["status"],
                "manifest": result.get("manifest"), "metrics": {
                    key: result[key] for key in (
                        "points", "ambiguous_columns_skipped", "missing_columns",
                        "matched_pixels", "field_pixels", "matched_fraction",
                        "mean_rgb_distance_matched"
                    ) if key in result
                },
                "error": result.get("error"),
            })
        successful = [r for r in runs if r["score"] is not None]
        if len(successful) != len(runs):
            chosen, reason = None, "One or more extraction configurations failed"
        else:
            ordered = sorted(runs, key=lambda r: (-r["score"], r["id"]))
            top, second = ordered[:2]
            margin = top["score"] - second["score"]
            if top["score"] < decision_policy["min_score"]:
                chosen, reason = None, "Best quality proxy below min_score"
            elif margin < decision_policy["min_margin"]:
                chosen, reason = None, "Quality-proxy margin below min_margin"
            else:
                chosen = top["id"]
                reason = "Highest quality proxy exceeds minimum score and separation margin"
        report = {
            "version": "0.7.2", "operation": operation,
            "source_path": str(source),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "policy": decision_policy,
            "candidates": runs, "selected_candidate": chosen,
            "decision_reason": reason, "selection_rule": (
                "curve: (traced_columns-ambiguous_columns)/ROI_width; "
                "field: colorbar_matched_fraction"
            ),
            "status": "REVIEW_REQUIRED" if chosen else "ABSTAIN",
            "origin": ORIGIN, "may_promote_to_reported": False,
            "scientific_status": "NOT_RUN",
            "uncertainty": "NOT_CALIBRATED",
            "limitations": (
                "Quality proxy is not accuracy. No ground truth, trained selector, "
                "automatic ROI selection, PIV, or independent physical validation."
            ),
        }
        destination = inside(root, "figure-routing/" + uuid4().hex)
        destination.mkdir(parents=True, exist_ok=False)
        path = destination / "routing_manifest.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"success": bool(chosen), "manifest": str(path), **report}
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        return {
            "success": False, "status": "BLOCKED", "origin": ORIGIN,
            "scientific_status": "NOT_RUN", "error": str(error),
        }


def register_figure_routing_tools(mcp, runtime):
    @mcp.tool()
    async def paper_figure_route(source_path: str, candidates: list[dict],
                                 policy: dict | None = None) -> dict:
        """Offline rule-based selection across 2..6 comparable pre-reviewed curve/field figure configurations. Requires caller-calibrated ROIs, axes and colorbars. Abstains on ambiguity. Does not operate COMSOL or independently verify figure values."""
        return route_figure(runtime.output_root, source_path, candidates, policy)
