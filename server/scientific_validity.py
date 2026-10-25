"""
Scientific validity under inferred / uncertain inputs.

Separate from execution success and numerical convergence.
Does not mutate contracts.aggregate STATES used by existing layers.
"""
from __future__ import annotations

from typing import Any


SCIENTIFIC_STATUSES = (
    "PASS",
    "FAIL",
    "BLOCKED",
    "NOT_RUN",
    "CONDITIONAL",
    "INSUFFICIENT_EVIDENCE",
)


def evaluate_scientific_validity(
    *,
    execution_status: str,
    numerical_status: str,
    parameter_beliefs: list[dict[str, Any]] | None = None,
    required_checks_status: str | None = None,
    conclusion_stable: bool | None = None,
) -> dict[str, Any]:
    """
    Rules (V0.1):
    - Solver / execution PASS ≠ scientific PASS
    - INFERRED + decision_impact HIGH/CRITICAL → not PASS
    - coverage insufficient → INSUFFICIENT_EVIDENCE (legal, not FAIL)
    - conclusion unstable under endpoints → CONDITIONAL or block PASS
    """
    beliefs = parameter_beliefs or []
    inferred_high = [
        b
        for b in beliefs
        if (
            b.get("status") == "inferred"
            or "INFERRED" in (b.get("provenance") or [])
        )
        and b.get("decision_impact") in ("HIGH", "CRITICAL")
    ]
    insufficient = [
        b for b in beliefs if b.get("coverage") == "insufficient" or b.get("reliability") == "INSUFFICIENT"
    ]

    layers = {
        "execution": execution_status,
        "numerical": numerical_status,
        "required_checks": required_checks_status or "NOT_RUN",
    }

    if insufficient and any(
        b.get("decision_impact") in ("HIGH", "CRITICAL", None) for b in insufficient
    ):
        return {
            "scientific_status": "INSUFFICIENT_EVIDENCE",
            "execution_status": execution_status,
            "numerical_status": numerical_status,
            "reason": "Critical/high-impact parameter lacks sufficient evidence",
            "inferred_high_impact": inferred_high,
            "layers": layers,
            "final_scientific_pass": False,
        }

    if inferred_high:
        status = "CONDITIONAL"
        if conclusion_stable is False:
            status = "INSUFFICIENT_EVIDENCE"
        return {
            "scientific_status": status,
            "execution_status": execution_status,
            "numerical_status": numerical_status,
            "reason": (
                "Inferred high/critical-impact parameter present; "
                "solver convergence is not scientific certainty"
            ),
            "inferred_high_impact": inferred_high,
            "conclusion_stable": conclusion_stable,
            "layers": layers,
            "final_scientific_pass": False,
        }

    if execution_status != "PASS" or numerical_status != "PASS":
        return {
            "scientific_status": "NOT_RUN"
            if "NOT_RUN" in (execution_status, numerical_status)
            else "FAIL",
            "execution_status": execution_status,
            "numerical_status": numerical_status,
            "reason": "Execution/numerical prerequisites not PASS",
            "layers": layers,
            "final_scientific_pass": False,
        }

    if required_checks_status not in (None, "PASS"):
        return {
            "scientific_status": required_checks_status
            if required_checks_status in SCIENTIFIC_STATUSES
            else "NOT_RUN",
            "execution_status": execution_status,
            "numerical_status": numerical_status,
            "reason": "Required scientific checks not PASS",
            "layers": layers,
            "final_scientific_pass": False,
        }

    # Low-impact inferred may remain CONDITIONAL for honesty, or PASS if only LOW
    low_inferred = [
        b
        for b in beliefs
        if b.get("status") == "inferred" and b.get("decision_impact") == "LOW"
    ]
    if low_inferred:
        return {
            "scientific_status": "CONDITIONAL",
            "execution_status": execution_status,
            "numerical_status": numerical_status,
            "reason": "Low-impact inferred inputs disclosed; acceptable for screening",
            "inferred_high_impact": [],
            "layers": layers,
            "final_scientific_pass": False,
            "acceptable_for": ["screening", "exploratory_simulation"],
        }

    return {
        "scientific_status": "PASS",
        "execution_status": execution_status,
        "numerical_status": numerical_status,
        "reason": "No high-impact inferred gaps; prerequisites PASS",
        "layers": layers,
        "final_scientific_pass": True,
    }
