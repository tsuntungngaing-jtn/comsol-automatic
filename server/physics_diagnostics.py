"""Offline, evidence-first diagnostic hypothesis planning inspired by DEScover.

No COMSOL session, generated solver code, causal certification, or automatic repair.
Caller-provided evidence is treated as reported, never independently verified.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
from uuid import uuid4

SCHEMA = "physics-diagnostic/0.7.4"
MAX_BYTES = 1024 * 1024
MAX_HYPOTHESES = 16
MAX_OBSERVATIONS = 64
CATEGORIES = {"GEOMETRY", "MESH", "BOUNDARY_PHYSICS", "MATERIAL", "COUPLING",
              "SOLVER", "RESOURCE", "LICENSE", "DATA_EXPORT", "UNKNOWN"}
KINDS = {"static_readback": 0, "existing_result": 1,
         "controlled_rerun": 2, "full_revalidation": 3}
OPERATORS = {"greater_than", "less_than", "abs_diff_gt", "abs_diff_le"}
ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


class DiagnosticError(ValueError):
    """Invalid diagnostic plan or untrusted report."""


def _keys(data, required, optional=(), label="object"):
    if not isinstance(data, dict) or set(data) - set(required) - set(optional) or set(required) - set(data):
        raise DiagnosticError(f"{label}: expected keys {', '.join(required)}; allowed optional {', '.join(optional)}")


def _id(value, label):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise DiagnosticError(f"{label} must be a bounded ASCII identifier")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 1024:
        raise DiagnosticError(f"{label} must be nonempty text (<=1024 characters)")
    return value


def _sha(value, label):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise DiagnosticError(f"{label} must be a 64-character lowercase SHA-256 digest")
    return value


def _num(value, label):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise DiagnosticError(f"{label} must be finite numeric")
    try:
        out = float(value)
    except (ValueError, OverflowError) as exc:
        raise DiagnosticError(f"{label} must be finite numeric") from exc
    if not math.isfinite(out):
        raise DiagnosticError(f"{label} must be finite numeric")
    return out


def _within(root, path):
    if not isinstance(path, (str, Path)):
        raise DiagnosticError("A workspace-relative or workspace-contained path is required")
    root = Path(root).resolve()
    p = Path(path)
    resolved = (p if p.is_absolute() else root / p).resolve()
    if not resolved.is_relative_to(root):
        raise DiagnosticError("Diagnostic input must remain inside COMSOL_OUTPUT_ROOT")
    return resolved


def _read(path):
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise DiagnosticError("Expected a JSON file no larger than 1 MiB")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise DiagnosticError("Invalid UTF-8 JSON") from exc


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save_report(root, directory, report):
    path = _within(root, Path("diagnostics") / directory / uuid4().hex / "report.json")
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return str(path)


def review_spec(spec):
    """Validate a closed, falsifiable diagnostic contract. This is not a physics proof."""
    _keys(spec, ("schema", "case_id", "baseline", "observations", "hypotheses", "budget"), label="diagnostic")
    if spec["schema"] != SCHEMA:
        raise DiagnosticError(f"schema must be {SCHEMA}")
    _id(spec["case_id"], "case_id")
    base = spec["baseline"]
    _keys(base, ("run_id", "model_revision", "spec_hash", "model_hash"), label="baseline")
    _id(base["run_id"], "baseline.run_id")
    _text(base["model_revision"], "baseline.model_revision")
    for name in ("spec_hash", "model_hash"):
        _sha(base[name], f"baseline.{name}")
    budget = spec["budget"]
    _keys(budget, ("max_tier", "max_tests"), label="budget")
    if type(budget["max_tier"]) is not int or budget["max_tier"] not in range(4):
        raise DiagnosticError("budget.max_tier must be integer 0..3")
    if isinstance(budget["max_tests"], bool) or not isinstance(budget["max_tests"], int) or not 1 <= budget["max_tests"] <= 16:
        raise DiagnosticError("budget.max_tests must be integer 1..16")
    observations = spec["observations"]
    if not isinstance(observations, list) or not 1 <= len(observations) <= MAX_OBSERVATIONS:
        raise DiagnosticError("observations must contain 1..64 items")
    obs_ids = set()
    for o in observations:
        _keys(o, ("id", "quantity", "value", "unit", "source_ref", "source_sha256", "run_id"), label="observation")
        obs_id = _id(o["id"], "observation.id")
        if obs_id in obs_ids:
            raise DiagnosticError("Duplicate observation id")
        obs_ids.add(obs_id)
        _id(o["quantity"], "observation.quantity")
        _num(o["value"], "observation.value")
        _text(o["unit"], "observation.unit")
        _text(o["source_ref"], "observation.source_ref")
        _sha(o["source_sha256"], "observation.source_sha256")
        if o["run_id"] != base["run_id"]:
            raise DiagnosticError("Baseline observation run identity mismatch")
    hypotheses = spec["hypotheses"]
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= MAX_HYPOTHESES:
        raise DiagnosticError("hypotheses must contain 1..16 entries")
    hypothesis_ids, test_ids = set(), set()
    for h in hypotheses:
        _keys(h, ("id", "category", "claim", "mechanism", "falsifier", "supporting_observation_ids", "test"), label="hypothesis")
        hid = _id(h["id"], "hypothesis.id")
        if hid in hypothesis_ids:
            raise DiagnosticError("Duplicate hypothesis id")
        hypothesis_ids.add(hid)
        if h["category"] not in CATEGORIES:
            raise DiagnosticError("Unsupported failure category")
        for label in ("claim", "mechanism", "falsifier"):
            _text(h[label], f"hypothesis.{label}")
        support = h["supporting_observation_ids"]
        if not isinstance(support, list) or len(support) != len(set(support)) or any(v not in obs_ids for v in support):
            raise DiagnosticError("Hypothesis must reference unique known observation IDs")
        test = h["test"]
        _keys(test, ("id", "kind", "observable", "unit", "support_if", "rationale", "required_source"), label="test")
        tid = _id(test["id"], "test.id")
        if tid in test_ids:
            raise DiagnosticError("Duplicate test id")
        test_ids.add(tid)
        if test["kind"] not in KINDS:
            raise DiagnosticError("Unsupported test kind")
        _id(test["observable"], "test.observable")
        _text(test["unit"], "test.unit")
        _text(test["rationale"], "test.rationale")
        _text(test["required_source"], "test.required_source")
        rule = test["support_if"]
        _keys(rule, ("operator", "reference", "tolerance"), label="support_if")
        if rule["operator"] not in OPERATORS:
            raise DiagnosticError("Unsupported comparison operator")
        _num(rule["reference"], "support_if.reference")
        tolerance = _num(rule["tolerance"], "support_if.tolerance")
        if tolerance < 0:
            raise DiagnosticError("support_if.tolerance cannot be negative")
    return spec


def plan(spec):
    review_spec(spec)
    candidates = []
    for h in spec["hypotheses"]:
        t = h["test"]
        tier = KINDS[t["kind"]]
        supported = len(h["supporting_observation_ids"]) > 0
        if tier > spec["budget"]["max_tier"]:
            status = "OVER_BUDGET"
        elif not supported:
            status = "NEEDS_EVIDENCE"
        else:
            status = "PROPOSED"
        candidates.append({
            "hypothesis_id": h["id"], "test_id": t["id"], "category": h["category"],
            "tier": tier, "kind": t["kind"], "status": status,
            "test_status": "NOT_RUN", "root_cause": "UNKNOWN",
            "requires_user_authorization": tier >= 2,
            "requires_solve": tier >= 2,
            "required_source": t["required_source"],
            "rationale": t["rationale"],
            "expected_decision_rule": copy.deepcopy(t["support_if"]),
            "unit": t["unit"], "observable": t["observable"],
        })
    candidates.sort(key=lambda x: (x["tier"], x["hypothesis_id"]))
    used = 0
    for row in candidates:
        if row["status"] == "PROPOSED":
            if used >= spec["budget"]["max_tests"]:
                row["status"] = "OVER_TEST_COUNT_BUDGET"
            else:
                used += 1
    return {"schema": SCHEMA, "case_id": spec["case_id"], "baseline": spec["baseline"],
            "review_status": "CONTRACT_REVIEWED_NOT_PHYSICALLY_VALIDATED",
            "status": "PROPOSED_ONLY", "scientific_status": "NOT_RUN",
            "root_cause_confirmed": False, "eligible_tests": used,
            "proposals": candidates, "spec": copy.deepcopy(spec)}


def _satisfies(rule, observed):
    reference, tolerance = rule["reference"], rule["tolerance"]
    return {"greater_than": lambda: observed > reference + tolerance,
            "less_than": lambda: observed < reference - tolerance,
            "abs_diff_gt": lambda: abs(observed - reference) > tolerance,
            "abs_diff_le": lambda: abs(observed - reference) <= tolerance}[rule["operator"]]()


def evaluate_report(plan_doc, observation):
    if not isinstance(plan_doc, dict) or plan_doc.get("schema") != SCHEMA or "spec" not in plan_doc:
        raise DiagnosticError("Not a v0.7.4 diagnostic plan")
    original = plan(plan_doc["spec"])
    if plan_doc.get("baseline") != original["baseline"] or plan_doc.get("case_id") != original["case_id"] or plan_doc.get("proposals") != original["proposals"]:
        raise DiagnosticError("Plan content differs from a freshly checked plan")
    if not isinstance(observation, dict):
        raise DiagnosticError("Reported test result must be an object")
    _keys(observation, ("hypothesis_id", "test_id", "status"),
          ("value", "unit", "run_id", "model_revision", "spec_hash", "source_ref", "source_sha256", "authorization_ref", "reason"), "reported test")
    proposal = next((p for p in original["proposals"] if p["hypothesis_id"] == observation["hypothesis_id"] and p["test_id"] == observation["test_id"]), None)
    if proposal is None or proposal["status"] != "PROPOSED":
        raise DiagnosticError("Only a planned eligible test can be reported")
    status = observation["status"]
    if status not in ("REPORTED_EXECUTED", "NOT_RUN", "BLOCKED"):
        raise DiagnosticError("Unsupported reported test status")
    if status != "REPORTED_EXECUTED":
        if set(observation) != {"hypothesis_id", "test_id", "status", "reason"}:
            raise DiagnosticError("Incomplete tests accept only a reason, not a measurement")
        _text(observation["reason"], "reason")
        interpretation = "NO_DIAGNOSTIC_EVIDENCE"
        agrees = None
    else:
        required = {"hypothesis_id", "test_id", "status", "value", "unit", "run_id", "model_revision", "spec_hash", "source_ref", "source_sha256"}
        if proposal["tier"] >= 2:
            required.add("authorization_ref")
        if set(observation) != required:
            raise DiagnosticError("Reported executed test has missing or unexpected evidence fields")
        measured = _num(observation["value"], "reported.value")
        if observation["unit"] != proposal["unit"]:
            raise DiagnosticError("Test unit mismatch; conversion requires a new reviewed contract")
        _id(observation["run_id"], "reported.run_id")
        _text(observation["model_revision"], "reported.model_revision")
        _text(observation["source_ref"], "reported.source_ref")
        _sha(observation["source_sha256"], "reported.source_sha256")
        _sha(observation["spec_hash"], "reported.spec_hash")
        baseline = original["baseline"]
        if observation["spec_hash"] != baseline["spec_hash"]:
            raise DiagnosticError("Spec hash mismatch; diagnostic contract must be reviewed again")
        if proposal["tier"] <= 1:
            if observation["run_id"] != baseline["run_id"] or observation["model_revision"] != baseline["model_revision"]:
                raise DiagnosticError("Read-only evidence must match baseline run and model revision")
        else:
            _text(observation["authorization_ref"], "authorization_ref")
            if observation["run_id"] == baseline["run_id"]:
                raise DiagnosticError("A reported rerun requires a distinct run ID")
        agrees = _satisfies(proposal["expected_decision_rule"], measured)
        interpretation = "REPORTED_TEST_SUPPORTS_PREDICTION" if agrees else "REPORTED_TEST_DOES_NOT_SUPPORT_PREDICTION"
    return {"schema": SCHEMA, "case_id": original["case_id"],
            "hypothesis_id": proposal["hypothesis_id"], "test_id": proposal["test_id"],
            "reported_test_status": status, "interpretation": interpretation,
            "decision_rule_satisfied": agrees,
            "causal_status": "UNCONFIRMED", "root_cause_confirmed": False,
            "scientific_status": "NOT_RUN", "repair_authorized": False,
            "reported_evidence": observation,
            "limitations": "External reported data only; no COMSOL acquisition, independent validation, causal proof or automatic model repair"}


def create_plan(spec_path, output_root):
    try:
        source = _within(output_root, spec_path)
        result = plan(_read(source))
        result["input_sha256"] = _digest(source)
        path = _save_report(output_root, "plans", result)
        return {"success": True, "status": "PROPOSED_ONLY", "plan_path": path,
                "input_sha256": result["input_sha256"],
                "eligible_tests": result["eligible_tests"], "scientific_status": "NOT_RUN"}
    except (DiagnosticError, OSError, KeyError, TypeError, OverflowError) as exc:
        return {"success": False, "status": "BLOCKED", "scientific_status": "NOT_RUN", "error": str(exc)}


def record_test(plan_path, evidence_path, output_root):
    try:
        plan_file = _within(output_root, plan_path)
        evidence_file = _within(output_root, evidence_path)
        result = evaluate_report(_read(plan_file), _read(evidence_file))
        result["plan_sha256"] = _digest(plan_file)
        result["evidence_file_sha256"] = _digest(evidence_file)
        path = _save_report(output_root, "reports", result)
        return {"success": True, "status": "REVIEW_RECORDED", "report_path": path,
                "interpretation": result["interpretation"], "scientific_status": "NOT_RUN",
                "root_cause_confirmed": False}
    except (DiagnosticError, OSError, KeyError, TypeError, OverflowError) as exc:
        return {"success": False, "status": "BLOCKED", "scientific_status": "NOT_RUN", "error": str(exc)}


def register_diagnostic_tools(mcp, runtime):
    @mcp.tool()
    async def physics_diagnostic_plan(spec_path: str) -> dict:
        """Offline diagnostic hypotheses: validate evidence & physics-test contracts; propose bounded tiered tests. No solve, code execution, causal claim, or repair."""
        return create_plan(spec_path, runtime.output_root)

    @mcp.tool()
    async def physics_diagnostic_record(plan_path: str, evidence_path: str) -> dict:
        """Record a caller-reported test observation against a preregistered rule. Never authenticate COMSOL or certify root cause; writes immutable provenance."""
        return record_test(plan_path, evidence_path, runtime.output_root)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline diagnostic hypothesis tests; never operates COMSOL")
    parser.add_argument("operation", choices=("plan", "record"))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--spec")
    parser.add_argument("--plan")
    parser.add_argument("--evidence")
    a = parser.parse_args(argv)
    result = create_plan(a.spec, a.output_root) if a.operation == "plan" else record_test(a.plan, a.evidence, a.output_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
