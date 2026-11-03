"""COMSOL_RSI_AUTONOMY profiles: strict | assisted | auto."""
from __future__ import annotations

import os
from typing import Any

from .parameter_belief import ParameterBelief

PROFILES = ("strict", "assisted", "auto")

# Actions that never auto-execute regardless of profile.
ALWAYS_HUMAN_ACTIONS = frozenset(
    {
        "enable_arbitrary_code",
        "overwrite_source_mph",
        "delete_audit_tree",
        "final_scientific_validated",
        "cross_machine_license_change",
    }
)


def get_autonomy_profile(override: str | None = None) -> str:
    raw = (override or os.getenv("COMSOL_RSI_AUTONOMY") or "strict").strip().lower()
    if raw not in PROFILES:
        return "strict"
    return raw


def apply_autonomy_policy(
    belief: ParameterBelief,
    *,
    profile: str | None = None,
    has_software_doc_default: bool = False,
    dual_source_agree: bool = False,
    claim_critical: bool = False,
    high_risk_action: str | None = None,
) -> ParameterBelief:
    """
    Adjust recommended_action after the base U×S gate.

    Does not invent sensitivity. Never clears CRITICAL human gates for
    ALWAYS_HUMAN_ACTIONS.
    """
    mode = get_autonomy_profile(profile)
    belief.notes = (belief.notes or "") + f" autonomy={mode};"

    if high_risk_action in ALWAYS_HUMAN_ACTIONS:
        belief.recommended_action = "ASK_USER"
        belief.decision_impact = belief.decision_impact or "CRITICAL"
        belief.notes += " hard_ban_auto;"
        return belief

    impact = (belief.decision_impact or "HIGH").upper()
    action = belief.recommended_action

    if mode == "strict":
        if impact in ("HIGH", "CRITICAL") and action == "AUTO_ACCEPT":
            belief.recommended_action = "ASK_USER"
        if belief.status == "inferred" and not has_software_doc_default and not dual_source_agree:
            if action == "AUTO_ACCEPT" and impact != "LOW":
                belief.recommended_action = "ASK_USER"
        return belief

    if mode == "assisted":
        if impact == "LOW" and (has_software_doc_default or dual_source_agree or belief.status == "known"):
            belief.recommended_action = "AUTO_ACCEPT"
        elif impact == "MEDIUM" and (has_software_doc_default or dual_source_agree):
            if belief.sensitivity and belief.sensitivity.get("status") not in (None, "unknown"):
                belief.recommended_action = "AUTO_ACCEPT"
            else:
                belief.recommended_action = "RUN_SENSITIVITY"
        elif impact == "HIGH":
            belief.recommended_action = "ASK_USER"
            belief.notes += " pack_with_related;"
        elif impact == "CRITICAL":
            belief.recommended_action = "ASK_USER"
        return belief

    # auto
    if impact == "LOW":
        belief.recommended_action = "AUTO_ACCEPT"
    elif impact == "MEDIUM":
        belief.recommended_action = "RUN_SENSITIVITY"
        belief.notes += " auto_sensitivity_budget;"
    elif impact == "HIGH":
        if has_software_doc_default and not claim_critical:
            belief.recommended_action = "AUTO_ACCEPT"
            belief.notes += " CONDITIONAL_scientific;"
            if "final_validation" in belief.safe_for:
                belief.safe_for = [s for s in belief.safe_for if s != "final_validation"]
        else:
            belief.recommended_action = "ASK_USER"
    else:
        belief.recommended_action = "ASK_USER"
    return belief


def pack_decision_requests(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Merge related ASK_USER items into fewer DecisionRequests (assisted default).

    Groups by (task_id, claim_id) when present; otherwise returns as-is batches
    of at most 5 related parameters under one synthetic pack id.
    """
    if not requests:
        return []
    groups: dict[str, list[dict[str, Any]]] = {}
    for req in requests:
        key = f"{req.get('task_id', '_')}|{req.get('claim_id', '_')}"
        groups.setdefault(key, []).append(req)

    packed: list[dict[str, Any]] = []
    for key, items in groups.items():
        if len(items) == 1:
            packed.append(items[0])
            continue
        packed.append(
            {
                "decision_id": f"pack:{key}:{items[0].get('decision_id', 'x')}",
                "kind": "packed",
                "task_id": items[0].get("task_id"),
                "claim_id": items[0].get("claim_id"),
                "questions": items,
                "reason": "Packed related underspecification questions (assisted/auto).",
                "action_needed": "ASK_USER",
            }
        )
    return packed
