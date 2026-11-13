"""Offline, evidence-first Design of Experiments and simulation dataset records.

No COMSOL API access, solver execution, verified physical results, or ML training.
Generated tasks have PLANNED status; reported results remain UNVERIFIED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import uuid

SCHEMA = "simulation-dataset/0.7.3"
MAX_SPEC_BYTES = 1024 * 1024
MAX_PLAN_BYTES = 16 * 1024 * 1024
MAX_CASES = 500
MAX_PARAMETERS = 32
MAX_ATTEMPT_BATCHES = 20
VALID_ORIGINS = {"USER_SUPPLIED", "MEASURED", "MANUFACTURER_SPEC", "LITERATURE",
                 "DATABASE", "VALIDATED_PRIOR_TASK", "INFERRED", "DEFAULT"}
FAILURE_CATEGORIES = {"GEOMETRY", "MESH", "BOUNDARY_PHYSICS", "COUPLING", "SOLVER",
                      "LICENSE", "RESOURCE", "DATA_EXPORT", "UNKNOWN"}
CHECKS = ("solver_convergence", "conservation", "mesh_independence", "scientific_comparison")
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")


class DatasetError(ValueError):
    pass


def _finite(v, label):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise DatasetError(f"{label} must be finite numeric")
    try:
        value = float(v)
    except (OverflowError, ValueError) as exc:
        raise DatasetError(f"{label} must be finite numeric") from exc
    if not math.isfinite(value):
        raise DatasetError(f"{label} must be finite numeric")
    return value


def _name(value, label):
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise DatasetError(f"{label} must match [A-Za-z][A-Za-z0-9_-]{{0,63}}")
    return value


def _nonempty(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise DatasetError(f"{label} requires a nonempty bounded string")
    return value


def _exact_keys(d, required, optional, label):
    if not isinstance(d, dict) or set(d) - set(required) - set(optional) or set(required) - set(d):
        raise DatasetError(f"{label} must have required keys {required} and optional keys {optional}")


def validate_spec(spec):
    """Require provenance and units for every design variable and observable."""
    _exact_keys(spec, ("schema", "study_id", "source_sha256", "seed", "parameters", "observables"),
                ("constraints", "splits"), "spec")
    if spec["schema"] != SCHEMA:
        raise DatasetError(f"schema must be {SCHEMA}")
    _name(spec["study_id"], "study_id")
    if not isinstance(spec["source_sha256"], str) or not HASH.fullmatch(spec["source_sha256"]):
        raise DatasetError("source_sha256 must be an authentic 64-character SHA-256 supplied by caller")
    if isinstance(spec["seed"], bool) or not isinstance(spec["seed"], int) or not 0 <= spec["seed"] < 2**32:
        raise DatasetError("seed must be an integer in [0, 2^32)")
    pars = spec["parameters"]
    if not isinstance(pars, list) or not 1 <= len(pars) <= MAX_PARAMETERS:
        raise DatasetError("parameters must contain 1..32 items")
    seen = set()
    for p in pars:
        _exact_keys(p, ("name", "unit", "lower", "upper", "kind", "role", "origin", "evidence_ref"), (), "parameter")
        n = _name(p["name"], "parameter.name")
        if n in seen:
            raise DatasetError(f"duplicate parameter {n}")
        seen.add(n)
        _nonempty(p["unit"], f"{n}.unit")
        _nonempty(p["evidence_ref"], f"{n}.evidence_ref")
        if p["origin"] not in VALID_ORIGINS:
            raise DatasetError(f"{n}: invalid provenance origin")
        if p["kind"] not in ("continuous", "integer") or p["role"] not in ("geometry", "condition", "material", "other"):
            raise DatasetError(f"{n}: invalid kind or role")
        lo, hi = _finite(p["lower"], f"{n}.lower"), _finite(p["upper"], f"{n}.upper")
        if lo >= hi:
            raise DatasetError(f"{n}: lower must be < upper")
        if p["kind"] == "integer" and (not lo.is_integer() or not hi.is_integer()):
            raise DatasetError(f"{n}: integer parameter bounds must be integers")
    observations = spec["observables"]
    if not isinstance(observations, list) or not observations or len(observations) > 32:
        raise DatasetError("observables must contain 1..32 quantities")
    seen_obs = set()
    for o in observations:
        _exact_keys(o, ("name", "unit", "required_checks"), (), "observable")
        n = _name(o["name"], "observable.name")
        if n in seen_obs:
            raise DatasetError(f"duplicate observable {n}")
        seen_obs.add(n)
        _nonempty(o["unit"], f"observable {n}.unit")
        req = o["required_checks"]
        if not isinstance(req, list) or not req or len(req) != len(set(req)) or any(x not in CHECKS for x in req):
            raise DatasetError(f"observable {n} needs unique, recognized required_checks")
    by_name = {p["name"]: p for p in pars}
    constraints = spec.get("constraints", [])
    if not isinstance(constraints, list) or len(constraints) > 64:
        raise DatasetError("constraints must have <=64 entries")
    for c in constraints:
        _exact_keys(c, ("type", "left", "right"), ("min", "max"), "constraint")
        if c["type"] not in ("le", "lt", "ratio") or c["left"] not in by_name or c["right"] not in by_name:
            raise DatasetError("constraint has invalid type/parameter")
        if c["left"] == c["right"] or by_name[c["left"]]["unit"] != by_name[c["right"]]["unit"]:
            raise DatasetError("constraint parameters must be distinct with identical units")
        if c["type"] == "ratio":
            if set(c) != {"type", "left", "right", "min", "max"}:
                raise DatasetError("ratio requires exactly min/max")
            lo, hi = _finite(c["min"], "ratio.min"), _finite(c["max"], "ratio.max")
            if lo > hi or by_name[c["right"]]["lower"] <= 0:
                raise DatasetError("ratio requires min<=max and positive denominator bounds")
        elif set(c) != {"type", "left", "right"}:
            raise DatasetError("le/lt constraints accept no extra keys")
    splits = spec.get("splits", {"train": 1.0, "validation": 0.0, "test": 0.0})
    if not isinstance(splits, dict) or set(splits) != {"train", "validation", "test"}:
        raise DatasetError("splits require train, validation and test")
    weights = [_finite(splits[x], f"splits.{x}") for x in ("train", "validation", "test")]
    if any(w < 0 for w in weights) or not math.isclose(sum(weights), 1, abs_tol=1e-10):
        raise DatasetError("split fractions must be nonnegative and sum to 1")
    return spec


def _allowed(values, constraints):
    for c in constraints:
        a, b = values[c["left"]], values[c["right"]]
        if c["type"] == "le" and not (a <= b):
            return False
        if c["type"] == "lt" and not (a < b):
            return False
        if c["type"] == "ratio" and not (c["min"] <= a / b <= c["max"]):
            return False
    return True


def _lhs_batch(pars, count, rng):
    columns = {}
    for p in pars:
        strata = [(i + rng.random()) / count for i in range(count)]
        rng.shuffle(strata)
        lo, hi = p["lower"], p["upper"]
        if p["kind"] == "integer":
            choices = int(hi - lo + 1)
            columns[p["name"]] = [int(lo) + min(choices - 1, int(x * choices)) for x in strata]
        else:
            columns[p["name"]] = [lo + x * (hi - lo) for x in strata]
    return [{p["name"]: columns[p["name"]][i] for p in pars} for i in range(count)]


def _split_assignments(n, weights, rng):
    # Largest remainder apportionment avoids assigning individual sample fragments.
    kinds = ("train", "validation", "test")
    raw = [n * weights[x] for x in kinds]
    counts = [int(x) for x in raw]
    for idx in sorted(range(3), key=lambda i: (-(raw[i] - counts[i]), i))[:n - sum(counts)]:
        counts[idx] += 1
    labels = [name for name, cnt in zip(kinds, counts) for _ in range(cnt)]
    rng.shuffle(labels)
    return labels


def plan_cases(spec, count):
    validate_spec(spec)
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_CASES:
        raise DatasetError("count must be an integer in 1..500")
    rng = random.Random(spec["seed"])
    accepted, rejected, attempts = [], 0, 0
    constraints = spec.get("constraints", [])
    while len(accepted) < count and attempts < MAX_ATTEMPT_BATCHES:
        attempts += 1
        remaining = count - len(accepted)
        for vals in _lhs_batch(spec["parameters"], remaining, rng):
            if _allowed(vals, constraints):
                accepted.append(vals)
            else:
                rejected += 1
    if len(accepted) != count:
        raise DatasetError(f"constraints reject too many samples: accepted {len(accepted)}/{count}; no plan written")
    weights = spec.get("splits", {"train": 1.0, "validation": 0.0, "test": 0.0})
    labels = _split_assignments(count, weights, rng)
    cases = []
    for i, (values, split) in enumerate(zip(accepted, labels), start=1):
        cases.append({
            "case_id": f"case-{i:05d}", "split": split, "parameters": {
                p["name"]: {"value": values[p["name"]], "unit": p["unit"],
                            "origin": p["origin"], "evidence_ref": p["evidence_ref"]}
                for p in spec["parameters"]},
            "execution_status": "PLANNED", "failure_category": None,
            "observable_validation": {
                o["name"]: {"unit": o["unit"], "required_checks": {
                    name: "NOT_RUN" for name in o["required_checks"]},
                    "scientific_status": "NOT_RUN"} for o in spec["observables"]},
        })
    return {"schema": SCHEMA, "study_id": spec["study_id"], "source_sha256": spec["source_sha256"],
            "seed": spec["seed"], "sampling": "randomized_lhs_with_rejection_not_optimized",
            "attempt_batches": attempts, "rejected_candidates": rejected,
            "constraint_bias_warning": bool(constraints), "ood_status": "NOT_GENERATED",
            "scientific_status": "NOT_RUN", "cases": cases,
            "spec": spec}


def _json_bytes(document):
    return (json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _read_json(path, max_bytes=MAX_SPEC_BYTES):
    p = Path(path)
    if not p.is_file() or p.stat().st_size > max_bytes:
        raise DatasetError("JSON input must be an existing bounded-size file")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise DatasetError("Invalid UTF-8 JSON input") from exc


def _inside(root, path):
    root = Path(root).resolve()
    if not isinstance(path, (str, Path)):
        raise DatasetError("Path must be a string or Path")
    p = Path(path)
    path = (p if p.is_absolute() else root / p).resolve()
    if not path.is_relative_to(root):
        raise DatasetError("Path must stay within COMSOL_OUTPUT_ROOT")
    return path


def create_plan(spec_path, count, output_root):
    try:
        spec_path = _inside(output_root, spec_path)
        spec = _read_json(spec_path)
        plan = plan_cases(spec, count)
        plan["design_spec_file_sha256"] = hashlib.sha256(spec_path.read_bytes()).hexdigest()
        root = Path(output_root).resolve()
        folder = root / "simulation-datasets" / (spec["study_id"] + "-" + uuid.uuid4().hex)
        folder.mkdir(parents=True, exist_ok=False)
        destination = folder / "plan.json"
        destination.write_bytes(_json_bytes(plan))
        return {"success": True, "status": "PLANNED", "case_count": count,
                "plan_path": str(destination), "plan_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "scientific_status": "NOT_RUN", "rejected_candidates": plan["rejected_candidates"]}
    except (DatasetError, OSError, TypeError, KeyError) as exc:
        return {"success": False, "status": "BLOCKED", "scientific_status": "NOT_RUN", "error": str(exc)}


def record_outcome(plan_path, case_id, evidence_path, output_root):
    """Append an immutable *reported* outcome, never assert that a solve was checked."""
    try:
        plan_path = _inside(output_root, plan_path)
        evidence_path = _inside(output_root, evidence_path)
        plan, evidence = _read_json(plan_path, MAX_PLAN_BYTES), _read_json(evidence_path)
        if plan.get("schema") != SCHEMA or "cases" not in plan or "spec" not in plan:
            raise DatasetError("Expected a v0.7.3 plan.json")
        validate_spec(plan["spec"])
        case = next((c for c in plan["cases"] if c["case_id"] == case_id), None)
        if not case:
            raise DatasetError("Case ID not found in plan")
        _exact_keys(evidence, ("outcome", "run_id", "evidence_ref", "observables"),
                    ("failure_category", "failure_stage"), "outcome")
        if evidence["outcome"] not in ("REPORTED_SUCCESS", "REPORTED_FAILURE", "NOT_RUN"):
            raise DatasetError("Unsupported reported outcome")
        if evidence["outcome"] != "NOT_RUN":
            _name(evidence["run_id"], "run_id")
            _nonempty(evidence["evidence_ref"], "evidence_ref")
        if evidence["outcome"] == "REPORTED_FAILURE":
            if evidence.get("failure_category") not in FAILURE_CATEGORIES:
                raise DatasetError("A reported failure needs an explicit category, UNKNOWN allowed")
            _nonempty(evidence.get("failure_stage"), "failure_stage")
        elif evidence.get("failure_category") is not None or evidence.get("failure_stage") is not None:
            raise DatasetError("Failure fields only valid for reported failures")
        if not isinstance(evidence["observables"], dict):
            raise DatasetError("observables must be a map")
        expected = {o["name"]: o["unit"] for o in plan["spec"]["observables"]}
        if set(evidence["observables"]) - set(expected):
            raise DatasetError("Unexpected observable name")
        if evidence["outcome"] == "NOT_RUN" and evidence["observables"]:
            raise DatasetError("NOT_RUN cannot provide numerical observations")
        for key, value in evidence["observables"].items():
            _exact_keys(value, ("value", "unit", "evidence_ref"), (), "observable result")
            _finite(value["value"], f"observable {key}.value")
            if value["unit"] != expected[key]:
                raise DatasetError("Observable unit mismatch; explicit conversion required")
            _nonempty(value["evidence_ref"], f"observable {key}.evidence_ref")
        report = {
            "schema": SCHEMA, "study_id": plan["study_id"], "case_id": case_id,
            "reported_outcome": evidence["outcome"], "reported_evidence": evidence,
            "plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
            "evidence_file_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            "verified_execution": "NOT_RUN", "scientific_status": "NOT_RUN",
            "per_observable_verified_checks": {
                name: {check: "NOT_RUN" for check in info["required_checks"]}
                for name, info in case["observable_validation"].items()},
            "dataset_ready": False,
            "limitations": "Caller-reported evidence; no authenticated COMSOL solve, conservation, mesh convergence, or scientific audit",
        }
        folder = _inside(output_root, Path("simulation-datasets") / "outcome-reviews" / uuid.uuid4().hex)
        folder.mkdir(parents=True, exist_ok=False)
        destination = folder / "report.json"
        destination.write_bytes(_json_bytes(report))
        return {"success": True, "status": "REVIEW_RECORDED", "report_path": str(destination),
                "scientific_status": "NOT_RUN", "dataset_ready": False}
    except (DatasetError, OSError, TypeError, KeyError) as exc:
        return {"success": False, "status": "BLOCKED", "scientific_status": "NOT_RUN", "error": str(exc)}


def register_simulation_dataset_tools(mcp, runtime):
    @mcp.tool()
    async def simulation_dataset_plan(spec_path: str, count: int) -> dict:
        """Offline seeded randomized LHS; constrained parameter/observable schema, no COMSOL solve or publication-quality DoE claim. Input path must stay inside workspace."""
        return create_plan(spec_path, count, runtime.output_root)

    @mcp.tool()
    async def simulation_dataset_record(plan_path: str, case_id: str, evidence_path: str) -> dict:
        """Persist caller-reported result or failure with immutable provenance. Does not verify COMSOL or mark scientific PASS."""
        return record_outcome(plan_path, case_id, evidence_path, runtime.output_root)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline simulation Design of Experiments / dataset evidence")
    parser.add_argument("operation", choices=("plan", "record"))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--spec")
    parser.add_argument("--count", type=int)
    parser.add_argument("--plan")
    parser.add_argument("--case-id")
    parser.add_argument("--evidence")
    a = parser.parse_args(argv)
    if a.operation == "plan":
        result = create_plan(a.spec, a.count, a.output_root)
    else:
        result = record_outcome(a.plan, a.case_id, a.evidence, a.output_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
