"""Paired, held-out RSI evaluation. This module does NOT authenticate COMSOL.

A separate trusted evidence verifier MUST validate real artifacts and run
identities. Missing verification means NOT_RUN and cannot promote a policy.
"""
from __future__ import annotations

import re
from typing import Any, Callable

_CORE = frozenset(("numerical", "scientific", "reopen"))
_PHYSICAL = frozenset(("conservation", "mesh_independence"))
_GEOMETRY = frozenset(("geometry", "selection"))
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_IDENTITY = ("run_id", "model_revision", "study", "solver",
             "solution", "dataset", "parameters_hash")


def _artifact_declared(obs: dict[str, Any]) -> bool:
    identity = obs.get("identity")
    if not isinstance(identity, dict):
        return False
    if any(identity.get(k) is None or identity.get(k) == "" for k in _IDENTITY):
        return False
    evidence = obs.get("evidence")
    return (isinstance(evidence, dict)
            and evidence.get("origin") == "real_comsol_mcp"
            and bool(_SHA256.fullmatch(str(evidence.get("artifact_sha256") or "")))
            and bool(evidence.get("collector_run_id"))
            and evidence["collector_run_id"] == identity["run_id"])


def _verified(obs: dict[str, Any], verifier: Callable[[dict[str, Any]], bool] | None) -> bool:
    if not _artifact_declared(obs) or verifier is None:
        return False
    try:
        # A bool in user-supplied JSON is not authentication. The external
        # verifier must inspect immutable artifacts and actual run identity.
        return verifier(obs) is True
    except Exception:
        return False


def evaluate_paired_heldout(
    pairs: list[dict[str, Any]],
    *,
    learning_task_ids: set[str] | None = None,
    evidence_verifier: Callable[[dict[str, Any]], bool] | None = None,
    min_cases: int = 3,
) -> dict[str, Any]:
    """Compute comparable A/B metrics only on verified, never-learned cases.

    Each pair: task_id, dataset_split='held_out', task_kind='physical'/'geometry',
    spec_hash, old, new. Each observation: identity, evidence, checks (statuses),
    claimed_success, solver_calls. The independent verifier should check
    artifact SHA, run identity, data provenance and check integrity.
    """
    errors: list[str] = []
    if min_cases < 1:
        raise ValueError("min_cases must be positive")
    if len(pairs) < min_cases:
        errors.append(f"Requires at least {min_cases} paired held-out cases")
    if evidence_verifier is None:
        errors.append("Independent real-COMSOL evidence verifier unavailable")
    seen: set[str] = set()
    scored: list[tuple[bool, bool, bool, bool, int, int]] = []
    learning = learning_task_ids or set()

    for idx, pair in enumerate(pairs):
        task_id = pair.get("task_id")
        prefix = f"case[{idx}]"
        if not task_id or task_id in seen or task_id in learning:
            errors.append(f"{prefix}: duplicate, missing, or learning-overlapping task_id")
            continue
        seen.add(task_id)
        if pair.get("dataset_split") != "held_out":
            errors.append(f"{prefix}: not in held_out split")
            continue
        kind = pair.get("task_kind")
        if kind not in ("physical", "geometry"):
            errors.append(f"{prefix}: task_kind must be physical or geometry")
            continue
        if not pair.get("spec_hash"):
            errors.append(f"{prefix}: frozen spec_hash missing")
            continue
        required = set(_CORE) | (_PHYSICAL if kind == "physical" else _GEOMETRY)
        declared = pair.get("required_checks")
        if not isinstance(declared, list) or not set(declared).issuperset(required):
            errors.append(f"{prefix}: missing mandatory scientific/geometry check declarations")
            continue
        required.update(declared)

        observations = [pair.get("old"), pair.get("new")]
        if not all(isinstance(o, dict) for o in observations):
            errors.append(f"{prefix}: missing baseline/candidate observation")
            continue
        old, new = observations
        # Must compare like-for-like physical conditions and metric definitions.
        fields = ("spec_hash", "conditions_hash", "materials_hash", "metric_definitions_hash")
        if any(not old.get(k) or old.get(k) != new.get(k) for k in fields):
            errors.append(f"{prefix}: A/B inputs or metrics are not comparable")
            continue
        if old["spec_hash"] != pair["spec_hash"]:
            errors.append(f"{prefix}: observation spec differs from frozen case")
            continue
        if (old["identity"].get("run_id") == new["identity"].get("run_id") or
                old["evidence"].get("artifact_sha256") == new["evidence"].get("artifact_sha256")):
            errors.append(f"{prefix}: baseline and candidate need distinct run/artifact identities")
            continue
        if not _verified(old, evidence_verifier) or not _verified(new, evidence_verifier):
            errors.append(f"{prefix}: independent artifact/identity verification missing")
            continue
        if not isinstance(old.get("checks"), dict) or not isinstance(new.get("checks"), dict):
            errors.append(f"{prefix}: validation checks missing")
            continue
        if any(name not in old["checks"] or name not in new["checks"] for name in required):
            errors.append(f"{prefix}: validation evidence is incomplete")
            continue
        if any(old["checks"][k] not in ("PASS", "FAIL") or
               new["checks"][k] not in ("PASS", "FAIL") for k in required):
            errors.append(f"{prefix}: NOT_RUN/BLOCKED checks cannot enter retention")
            continue
        if type(old.get("claimed_success")) is not bool or type(new.get("claimed_success")) is not bool:
            errors.append(f"{prefix}: explicit success claims required")
            continue
        costs = [old.get("solver_calls"), new.get("solver_calls")]
        if any(type(v) is not int or v < 0 for v in costs):
            errors.append(f"{prefix}: measured nonnegative solver_calls required")
            continue

        passed = [all(o["checks"][k] == "PASS" for k in required) for o in (old, new)]
        scored.append((
            passed[0], passed[1],
            old["claimed_success"] and not passed[0],
            new["claimed_success"] and not passed[1],
            costs[0], costs[1],
        ))

    if errors:
        return {"status": "NOT_RUN", "case_count": len(scored),
                "requested_cases": len(pairs), "errors": errors,
                "reason": "Held-out comparison does not have verified complete evidence"}
    n = len(scored)
    if not n:
        return {"status": "NOT_RUN", "case_count": 0, "errors": ["Empty evaluation"]}
    old_pass = sum(row[0] for row in scored)
    new_pass = sum(row[1] for row in scored)
    old_claims = sum(bool(p["old"]["claimed_success"]) for p in pairs)
    new_claims = sum(bool(p["new"]["claimed_success"]) for p in pairs)
    old_false = sum(row[2] for row in scored)
    new_false = sum(row[3] for row in scored)
    regression = sum(row[0] and not row[1] for row in scored) / n
    old_cost = sum(row[4] for row in scored)
    new_cost = sum(row[5] for row in scored)

    return {
        "status": "PASS",  # Evidence completeness, NOT scientific PASS for each run.
        "case_count": n,
        "evaluation_split": "held_out",
        "evidence_scope": "externally_verified_via_callback",
        "old_metrics": {
            "performance": old_pass / n,
            "scientific_validity": old_pass / n,
            "false_pass_rate": old_false / old_claims if old_claims else 0.0,
            "regression": 0.0,
            "cost": old_cost,
        },
        "new_metrics": {
            "performance": new_pass / n,
            "scientific_validity": new_pass / n,
            "false_pass_rate": new_false / new_claims if new_claims else 0.0,
            "regression": regression,
            "cost": new_cost,
        },
        "false_pass_count": new_false,
        "regressed_cases": int(regression * n + 1e-9),
    }
