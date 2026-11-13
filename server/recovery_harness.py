"""Offline knowledge-guided commissioning and evidence-gated recovery.

This module NEVER operates COMSOL/Fluent, authenticates caller evidence,
approves an actual repair, or certifies numerical/physical success.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from uuid import uuid4

SCHEMA = "recovery-harness/0.7.5"
ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
GATES = ("convergence", "conservation", "mesh_independence", "physics_consistency")
MAX_BYTES = 2 * 1024 * 1024


class RecoveryError(ValueError):
    """Invalid or inconsistent scientific-evidence contract."""


def require_keys(value, required, optional=(), label="object"):
    if not isinstance(value, dict) or set(required) - set(value) or set(value) - set(required) - set(optional):
        raise RecoveryError(f"{label}: required {sorted(required)}, optional {sorted(optional)}")


def ident(value, label):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise RecoveryError(f"{label}: invalid identifier")
    return value


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise RecoveryError(f"{label}: nonempty bounded text required")
    return value


def digest(value, label):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise RecoveryError(f"{label}: lowercase SHA-256 required")
    return value


def finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RecoveryError(f"{label}: finite numeric required")
    try:
        result = float(value)
    except (OverflowError, ValueError, TypeError) as exc:
        raise RecoveryError(f"{label}: finite numeric required") from exc
    if not math.isfinite(result):
        raise RecoveryError(f"{label}: finite numeric required")
    return result


def canonical(document):
    return (json.dumps(document, sort_keys=True, ensure_ascii=False,
                       allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")


def workspace_path(root, path):
    root = Path(root).resolve()
    if not isinstance(path, (str, Path)):
        raise RecoveryError("Workspace-contained path required")
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise RecoveryError("Path escapes COMSOL_OUTPUT_ROOT")
    return resolved


def read_json(root, path):
    target = workspace_path(root, path)
    if not target.is_file() or target.stat().st_size > MAX_BYTES:
        raise RecoveryError("Input must be a JSON file no larger than 2 MiB")
    contents = target.read_bytes()
    try:
        document = json.loads(contents.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise RecoveryError("Invalid UTF-8 JSON") from exc
    return document, hashlib.sha256(contents).hexdigest()


def save_report(root, group, report):
    target = workspace_path(root, Path("recovery-harness") / group /
                            uuid4().hex / "report.json")
    target.parent.mkdir(parents=True, exist_ok=False)
    target.write_bytes(canonical(report))
    return str(target)


def validate_contract(contract):
    require_keys(contract, ("schema", "case_id", "software", "baseline",
                            "source_sha256", "parameters", "observables"), label="contract")
    if contract["schema"] != SCHEMA:
        raise RecoveryError("Unsupported contract schema")
    ident(contract["case_id"], "case_id")
    digest(contract["source_sha256"], "source_sha256")
    require_keys(contract["software"], ("name", "version", "interface", "knowledge_ref"), label="software")
    software = contract["software"]
    if (software["name"], software["interface"]) not in (
        ("COMSOL", "MCP"), ("Fluent", "PyFluent")
    ):
        raise RecoveryError("Unsupported declared software interface")
    text(software["version"], "software.version")
    text(software["knowledge_ref"], "software.knowledge_ref")
    baseline = contract["baseline"]
    require_keys(baseline, ("run_id", "model_revision", "spec_hash", "model_hash"), label="baseline")
    ident(baseline["run_id"], "baseline.run_id")
    text(baseline["model_revision"], "baseline.model_revision")
    digest(baseline["spec_hash"], "baseline.spec_hash")
    digest(baseline["model_hash"], "baseline.model_hash")
    params = contract["parameters"]
    if not isinstance(params, list) or not 1 <= len(params) <= 32:
        raise RecoveryError("1..32 parameters required")
    seen = set()
    for p in params:
        require_keys(p, ("name", "binding", "unit", "expected", "tolerance",
                         "role", "evidence_ref"), label="parameter")
        name = ident(p["name"], "parameter.name")
        if name in seen:
            raise RecoveryError("Duplicate parameter")
        seen.add(name)
        for key in ("binding", "unit", "evidence_ref"):
            text(p[key], "parameter." + key)
        if p["role"] not in ("fixed", "calibratable"):
            raise RecoveryError("Parameter must be fixed or calibratable")
        finite(p["expected"], "parameter.expected")
        if finite(p["tolerance"], "parameter.tolerance") < 0:
            raise RecoveryError("Negative parameter tolerance")
    observables = contract["observables"]
    if not isinstance(observables, list) or not 1 <= len(observables) <= 32:
        raise RecoveryError("1..32 observables required")
    seen = set()
    for o in observables:
        require_keys(o, ("name", "expression", "selection", "unit",
                         "reference", "abs_tolerance", "required_gates"), label="observable")
        name = ident(o["name"], "observable.name")
        if name in seen:
            raise RecoveryError("Duplicate observable")
        seen.add(name)
        for key in ("expression", "selection", "unit"):
            text(o[key], "observable." + key)
        finite(o["reference"], "observable.reference")
        if finite(o["abs_tolerance"], "observable.abs_tolerance") < 0:
            raise RecoveryError("Negative observable tolerance")
        gates = o["required_gates"]
        if not isinstance(gates, list) or not gates or len(gates) != len(set(gates)) or any(g not in GATES for g in gates):
            raise RecoveryError("Required gates must be unique and recognized")
    return contract


def freeze_contract(contract, source_digest=None):
    validate_contract(contract)
    frozen = json.loads(canonical(contract))
    return {"schema": SCHEMA, "kind": "FROZEN_CONTRACT",
            "contract": frozen, "contract_sha256": hashlib.sha256(canonical(frozen)).hexdigest(),
            "contract_file_sha256": source_digest,
            "status": "FROZEN_UNCOMMISSIONED", "scientific_status": "NOT_RUN",
            "limitations": "Contract format only; source digests and API bindings are caller attestations."}


def checked_frozen(record):
    if not isinstance(record, dict) or record.get("schema") != SCHEMA or record.get("kind") != "FROZEN_CONTRACT":
        raise RecoveryError("Frozen contract required")
    contract = record.get("contract")
    validate_contract(contract)
    if hashlib.sha256(canonical(contract)).hexdigest() != record.get("contract_sha256"):
        raise RecoveryError("Frozen contract was modified")
    return contract


def evaluate_commissioning(frozen, evidence):
    contract = checked_frozen(frozen)
    require_keys(evidence, ("contract_sha256", "run_id", "model_revision",
                            "spec_hash", "model_hash", "readbacks",
                            "available_observables", "source_ref", "source_sha256"),
                 label="commissioning evidence")
    if evidence["contract_sha256"] != frozen["contract_sha256"]:
        raise RecoveryError("Commissioning contract mismatch")
    baseline = contract["baseline"]
    for key in ("run_id", "model_revision", "spec_hash", "model_hash"):
        if evidence[key] != baseline[key]:
            raise RecoveryError("Commissioning baseline mismatch: " + key)
    text(evidence["source_ref"], "commissioning.source_ref")
    digest(evidence["source_sha256"], "commissioning.source_sha256")
    readbacks = evidence["readbacks"]
    if not isinstance(readbacks, dict) or set(readbacks) - {p["name"] for p in contract["parameters"]}:
        raise RecoveryError("Unknown readback parameter")
    available = evidence["available_observables"]
    if not isinstance(available, list) or len(available) != len(set(available)) or set(available) - {o["name"] for o in contract["observables"]}:
        raise RecoveryError("Invalid observable list")
    checks = []
    for p in contract["parameters"]:
        record = readbacks.get(p["name"])
        if record is None:
            checks.append({"check": "parameter_readback", "parameter": p["name"], "status": "NOT_RUN"})
            continue
        require_keys(record, ("value", "unit", "binding"), label="parameter readback")
        val = finite(record["value"], "readback.value")
        if record["unit"] != p["unit"] or record["binding"] != p["binding"]:
            raise RecoveryError("Readback unit or binding mismatch")
        ok = abs(val - p["expected"]) <= p["tolerance"]
        checks.append({"check": "parameter_readback", "parameter": p["name"],
                       "status": "REPORTED_PASS" if ok else "REPORTED_FAIL",
                       "difference": val - p["expected"]})
    for o in contract["observables"]:
        checks.append({"check": "observable_availability", "observable": o["name"],
                       "status": "REPORTED_PASS" if o["name"] in available else "NOT_RUN"})
    statuses = {x["status"] for x in checks}
    status = ("REPORTED_COMMISSIONING_FAIL" if "REPORTED_FAIL" in statuses else
              "REPORTED_COMMISSIONING_INCOMPLETE" if "NOT_RUN" in statuses else
              "REPORTED_COMMISSIONING_PASS")
    return {"schema": SCHEMA, "kind": "COMMISSIONING_REVIEW",
            "contract_sha256": frozen["contract_sha256"], "case_id": contract["case_id"],
            "status": status, "checks": checks, "reported_source": evidence,
            "verified_execution": "NOT_RUN", "scientific_status": "NOT_RUN",
            "independent_validation": "NOT_RUN"}


def propose_recovery(frozen, commissioning, diagnosis, change):
    contract = checked_frozen(frozen)
    if (commissioning.get("kind") != "COMMISSIONING_REVIEW" or
        commissioning.get("contract_sha256") != frozen["contract_sha256"] or
        commissioning.get("status") != "REPORTED_COMMISSIONING_PASS"):
        raise RecoveryError("Complete matching commissioning review required")
    if (diagnosis.get("schema") != "physics-diagnostic/0.7.4" or
        diagnosis.get("case_id") != contract["case_id"] or
        diagnosis.get("reported_test_status") != "REPORTED_EXECUTED" or
        diagnosis.get("interpretation") != "REPORTED_TEST_SUPPORTS_PREDICTION" or
        diagnosis.get("root_cause_confirmed") is not False or
        diagnosis.get("scientific_status") != "NOT_RUN" or
        diagnosis.get("repair_authorized") is not False):
        raise RecoveryError("Matching eligible unconfirmed v0.7.4 diagnosis required")
    require_keys(change, ("parameter", "new_value", "unit",
                          "rationale", "expected_effect", "authorization_required"),
                 label="proposed repair")
    parameter = next((p for p in contract["parameters"] if p["name"] == change["parameter"]), None)
    if parameter is None or parameter["role"] != "calibratable":
        raise RecoveryError("Only declared calibratable parameters may be proposed")
    if change["unit"] != parameter["unit"]:
        raise RecoveryError("Repair unit mismatch")
    finite(change["new_value"], "repair.new_value")
    text(change["rationale"], "repair.rationale")
    text(change["expected_effect"], "repair.expected_effect")
    if change["authorization_required"] is not True:
        raise RecoveryError("Separate permission requirement must be declared")
    return {"schema": SCHEMA, "kind": "RECOVERY_PROPOSAL", "case_id": contract["case_id"],
            "contract_sha256": frozen["contract_sha256"], "baseline": contract["baseline"],
            "parameter": parameter["name"], "binding": parameter["binding"],
            "old_value": parameter["expected"], "new_value": change["new_value"],
            "unit": parameter["unit"], "rationale": change["rationale"],
            "expected_effect": change["expected_effect"],
            "diagnostic_hypothesis": diagnosis.get("hypothesis_id"),
            "diagnostic_test": diagnosis.get("test_id"), "status": "PROPOSED_ONLY",
            "requires_separate_user_authorization": True,
            "execution_status": "NOT_RUN", "scientific_status": "NOT_RUN",
            "root_cause_confirmed": False, "repair_authorized": False}


def evaluate_recovery(frozen, proposal, evidence):
    contract = checked_frozen(frozen)
    if (proposal.get("kind") != "RECOVERY_PROPOSAL" or
        proposal.get("contract_sha256") != frozen["contract_sha256"] or
        proposal.get("baseline") != contract["baseline"] or
        proposal.get("status") != "PROPOSED_ONLY" or
        proposal.get("execution_status") != "NOT_RUN" or
        proposal.get("repair_authorized") is not False):
        raise RecoveryError("Incompatible or modified repair proposal")
    require_keys(evidence, ("contract_sha256", "baseline_run_id", "candidate_run_id",
                            "candidate_model_revision", "spec_hash", "authorization_ref",
                            "source_ref", "source_sha256", "values"),
                 label="reported recovery evidence")
    base = contract["baseline"]
    if evidence["contract_sha256"] != frozen["contract_sha256"] or evidence["spec_hash"] != base["spec_hash"] or evidence["baseline_run_id"] != base["run_id"]:
        raise RecoveryError("Recovery contract/spec/baseline mismatch")
    ident(evidence["candidate_run_id"], "candidate_run_id")
    if evidence["candidate_run_id"] == base["run_id"]:
        raise RecoveryError("Candidate run must be distinct")
    for field in ("candidate_model_revision", "authorization_ref", "source_ref"):
        text(evidence[field], field)
    if evidence["candidate_model_revision"] == base["model_revision"]:
        raise RecoveryError("Candidate model revision must differ from baseline")
    digest(evidence["source_sha256"], "candidate.source_sha256")
    values = evidence["values"]
    if not isinstance(values, dict) or set(values) - {o["name"] for o in contract["observables"]}:
        raise RecoveryError("Unknown observable in recovery evidence")
    results = []
    for o in contract["observables"]:
        record = values.get(o["name"])
        if record is None:
            results.append({"observable": o["name"], "status": "NOT_RUN"})
            continue
        require_keys(record, ("value", "unit", "reported_gates"), label="observable result")
        if record["unit"] != o["unit"]:
            raise RecoveryError("Observable unit mismatch")
        val = finite(record["value"], "observable.value")
        gates = record["reported_gates"]
        if (not isinstance(gates, dict) or set(gates) != set(o["required_gates"]) or
            any(x not in ("PASS", "FAIL", "BLOCKED", "NOT_RUN") for x in gates.values())):
            raise RecoveryError("Incomplete per-observable gate definitions")
        delta = abs(val - o["reference"])
        ok = delta <= o["abs_tolerance"] and all(x == "PASS" for x in gates.values())
        results.append({"observable": o["name"],
                        "status": "REPORTED_WITHIN_TOLERANCE" if ok else "REPORTED_NOT_ACCEPTABLE",
                        "abs_error": delta, "reported_gates": gates, "reported_value": val, "unit": o["unit"]})
    all_ok = bool(results) and all(x["status"] == "REPORTED_WITHIN_TOLERANCE" for x in results)
    return {"schema": SCHEMA, "kind": "RECOVERY_ASSESSMENT", "case_id": contract["case_id"],
            "contract_sha256": frozen["contract_sha256"],
            "status": "REPORTED_CRITERIA_MET_NEEDS_VERIFICATION" if all_ok else "REPORTED_CRITERIA_NOT_MET",
            "observables": results, "reported_evidence": evidence,
            "root_cause_confirmed": False, "scientific_status": "NOT_RUN",
            "verified_execution": "NOT_RUN", "independent_validation": "NOT_RUN",
            "candidate_accepted": False,
            "limitations": "Caller-reported data: no independent solver run, conservation, mesh verification or causal proof"}


def invoke(operation, root, *, contract_path=None, evidence_path=None,
           commissioning_path=None, diagnostic_path=None, proposal_path=None,
           change_path=None):
    try:
        if operation == "freeze":
            contract, source_sha = read_json(root, contract_path)
            result = freeze_contract(contract, source_sha)
        elif operation == "commission":
            frozen, _ = read_json(root, contract_path)
            evidence, source_sha = read_json(root, evidence_path)
            result = evaluate_commissioning(frozen, evidence)
            result["evidence_file_sha256"] = source_sha
        elif operation == "propose":
            frozen, _ = read_json(root, contract_path)
            commissioned, _ = read_json(root, commissioning_path)
            diagnosis, _ = read_json(root, diagnostic_path)
            change, _ = read_json(root, change_path)
            result = propose_recovery(frozen, commissioned, diagnosis, change)
            result["commissioning_file_sha256"] = hashlib.sha256(canonical(commissioned)).hexdigest()
            result["diagnosis_file_sha256"] = hashlib.sha256(canonical(diagnosis)).hexdigest()
        elif operation == "assess":
            frozen, _ = read_json(root, contract_path)
            proposal, _ = read_json(root, proposal_path)
            evidence, source_sha = read_json(root, evidence_path)
            result = evaluate_recovery(frozen, proposal, evidence)
            result["evidence_file_sha256"] = source_sha
        else:
            raise RecoveryError("Unknown operation")
        path = save_report(root, operation, result)
        return {"success": True, "status": result["status"], "record_path": path,
                "record_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                "scientific_status": "NOT_RUN"}
    except (RecoveryError, OSError, KeyError, TypeError, OverflowError) as exc:
        return {"success": False, "status": "BLOCKED", "scientific_status": "NOT_RUN", "error": str(exc)}


def register_recovery_tools(mcp, runtime):
    @mcp.tool()
    async def recovery_contract_freeze(contract_path: str) -> dict:
        """Offline frozen contract; NEVER gives permission to operate a solver."""
        return invoke("freeze", runtime.output_root, contract_path=contract_path)

    @mcp.tool()
    async def recovery_commission(contract_path: str, evidence_path: str) -> dict:
        """Review caller-reported parameter readbacks and observable availability."""
        return invoke("commission", runtime.output_root,
                      contract_path=contract_path, evidence_path=evidence_path)

    @mcp.tool()
    async def recovery_propose(contract_path: str, commissioning_path: str,
                               diagnostic_path: str, change_path: str) -> dict:
        """Plan a one-parameter change after v0.7.4 diagnosis; never mutate COMSOL."""
        return invoke("propose", runtime.output_root, contract_path=contract_path,
                      commissioning_path=commissioning_path,
                      diagnostic_path=diagnostic_path, change_path=change_path)

    @mcp.tool()
    async def recovery_assess(contract_path: str, proposal_path: str,
                              evidence_path: str) -> dict:
        """Compare reported candidate values and gates, never certify physical recovery."""
        return invoke("assess", runtime.output_root, contract_path=contract_path,
                      proposal_path=proposal_path, evidence_path=evidence_path)
