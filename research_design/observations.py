"""Evidence-aware, offline CFD observation admission for Discovery Mode.

Caller evidence is checked for STRUCTURE, consistency and freeze, never
authenticated against the solver. An admitted record remains externally
unverified until a trusted host reopens native solver artifacts.
"""
from __future__ import annotations

import math
import re

from .contracts import DesignError, assess_design, fingerprint, validate_space

SCHEMA = "paper2simu-discovery-observations/0.3.0"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CHECKS = ("native_convergence", "conservation", "physical_consistency",
          "numerical_verification")
MAX_RECORDS = 500
ALLOWED_SPLITS = ("train", "held_out")


def _sha(s, label):
    if not isinstance(s, str) or not SHA256.fullmatch(s):
        raise DesignError(f"{label}: expected SHA-256 hex")
    return s


def _numeric(x, label, positive=False):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise DesignError(f"{label}: finite numeric required")
    v = float(x)
    if not math.isfinite(v) or (positive and v <= 0):
        raise DesignError(f"{label}: finite {'positive ' if positive else ''}numeric required")
    return v


def admit_observations(space, dataset):
    """Return trainable rows while refusing unverifiable/unsafe source mixes.

    Study design/physics/mesh family is pinned via a caller-supplied
    configuration SHA and an explicit comparable-fidelity group. Different
    groups must be analyzed separately. Raw records are never edited.
    """
    contract = validate_space(space)
    if not isinstance(dataset, dict) or set(dataset) != {
        "schema", "design_space_hash", "configuration_sha256",
        "fidelity_group", "records"
    }:
        raise DesignError("Dataset needs schema, design hash, configuration SHA, fidelity group and records")
    if dataset["schema"] != SCHEMA:
        raise DesignError("Unsupported observation dataset schema")
    if dataset["design_space_hash"] != contract["design_space_hash"]:
        return {"status": "STALE_DESIGN_SPACE", "train_rows": [], "held_out_count": 0,
                "scientific_status": "NOT_RUN", "solver_contacted": False}
    _sha(dataset["configuration_sha256"], "configuration_sha256")
    group = dataset["fidelity_group"]
    if not isinstance(group, str) or not group.strip() or len(group) > 128:
        raise DesignError("fidelity_group must be bounded nonempty text")
    records = dataset["records"]
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        raise DesignError("Need 1..500 records")
    objectives = {o["name"]: o["unit"] for o in space["objectives"]}
    seen, group_splits = set(), {}
    training = []
    excluded = []
    held_count = 0
    for rec in records:
        fields = {"id", "design", "split", "solver", "configuration_sha256",
                  "fidelity_group", "native_case_sha256", "native_result_sha256",
                  "evidence_ref", "checks", "metrics", "cost_minutes"}
        if not isinstance(rec, dict) or set(rec) != fields:
            raise DesignError("Observation record has missing/unknown fields")
        ident = rec["id"]
        if not isinstance(ident, str) or not 0 < len(ident) <= 80 or ident in seen:
            raise DesignError("Record IDs must be unique and bounded")
        seen.add(ident)
        if rec["split"] not in ALLOWED_SPLITS:
            raise DesignError("Only train/held_out splits allowed")
        for field in ("native_case_sha256", "native_result_sha256", "configuration_sha256"):
            _sha(rec[field], f"{ident}.{field}")
        if not isinstance(rec["evidence_ref"], str) or not rec["evidence_ref"].strip():
            raise DesignError("Each record needs a native evidence reference")
        if not isinstance(rec["checks"], dict) or set(rec["checks"]) != set(CHECKS):
            raise DesignError("Each record needs all four declared physics/numerical checks")
        if any(value not in ("PASS", "FAIL", "BLOCKED", "NOT_RUN", "UNKNOWN")
               for value in rec["checks"].values()):
            raise DesignError("Invalid check state")
        if not isinstance(rec["metrics"], dict) or set(rec["metrics"]) != set(objectives):
            raise DesignError("Metrics must match all declared objectives")
        for name, result in rec["metrics"].items():
            if not isinstance(result, dict) or set(result) != {"value", "unit"}:
                raise DesignError(f"{ident}.{name}: metric needs value/unit")
            _numeric(result["value"], f"{ident}.{name}")
            if result["unit"] != objectives[name]:
                raise DesignError(f"{ident}.{name}: incompatible units")
        _numeric(rec["cost_minutes"], f"{ident}.cost_minutes", positive=True)
        if rec["solver"] not in space["allowed_solvers"]:
            raise DesignError("Observation solver not in declared study")
        check = assess_design(space, rec["design"])
        if not check["eligible"]:
            raise DesignError(f"{ident}: design invalid: {check.get('issues', [])}")
        fingerprint_design = check["candidate_hash"]
        existing = group_splits.setdefault(fingerprint_design, rec["split"])
        if existing != rec["split"]:
            raise DesignError("Train/held-out leakage: same design in both splits")
        if rec["split"] == "held_out":
            held_count += 1
            excluded.append({"id": ident, "reason": "HELD_OUT_NEVER_FIT"})
            continue
        if rec["configuration_sha256"] != dataset["configuration_sha256"]:
            excluded.append({"id": ident, "reason": "DIFFERENT_CONFIGURATION"})
            continue
        if rec["fidelity_group"] != group:
            excluded.append({"id": ident, "reason": "DIFFERENT_FIDELITY"})
            continue
        if any(state != "PASS" for state in rec["checks"].values()):
            excluded.append({"id": ident, "reason": "INCOMPLETE_OR_FAILED_NATIVE_CHECKS"})
            continue
        training.append({
            "id": ident, "design": rec["design"]["values"],
            "design_hash": fingerprint_design,
            "metrics": {name: float(value["value"]) for name, value in rec["metrics"].items()},
            "solver": rec["solver"], "evidence_ref": rec["evidence_ref"],
            "cost_minutes": float(rec["cost_minutes"])
        })
    return {
        "status": "ADMITTED_DECLARED_EVIDENCE_NOT_AUTHENTICATED" if training else "NO_TRAINABLE_ROWS",
        "design_space_hash": contract["design_space_hash"],
        "dataset_hash": fingerprint(dataset),
        "configuration_sha256": dataset["configuration_sha256"],
        "fidelity_group": group,
        "train_rows": training,
        "held_out_count": held_count,
        "excluded": excluded,
        "authentication": "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "scientific_status": "NOT_RUN",
        "solver_contacted": False,
    }
