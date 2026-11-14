"""Scientific status under uncertain inputs, separate from execution and modeling admission.

Fail-closed for *final scientific certification*: a solver's successful
termination does not imply validated model physics or source agreement.
This function never launches a solver and does not determine what preparatory
work is authorized.
"""
from __future__ import annotations

from typing import Any

SCIENTIFIC_STATUSES = (
    "PASS", "FAIL", "BLOCKED", "NOT_RUN", "CONDITIONAL",
    "INSUFFICIENT_EVIDENCE",
)
NUMERICAL_STATES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}


def evaluate_scientific_validity(
    *,
    execution_status: str,
    numerical_status: str,
    parameter_beliefs: list[dict[str, Any]] | None = None,
    required_checks_status: str | None = None,
    conclusion_stable: bool | None = None,
) -> dict[str, Any]:
    """Evaluate FINAL scientific claims without turning missing evidence into PASS.

    Precedence: actual failure > blocked/not run > explicit required checks
    > uncertainty restrictions > PASS. This is a final claim gate, NOT the
    decision whether engineering preflight, diagnostic or sensitivity work
    may continue.
    """
    beliefs = parameter_beliefs or []
    inferred_high = [
        b for b in beliefs
        if (b.get("status") == "inferred" or "INFERRED" in (b.get("provenance") or []))
        and b.get("decision_impact") in ("HIGH", "CRITICAL")
    ]
    insufficient = [
        b for b in beliefs
        if b.get("coverage") == "insufficient" or b.get("reliability") == "INSUFFICIENT"
    ]
    layers = {
        "execution": execution_status,
        "numerical": numerical_status,
        "required_checks": required_checks_status if required_checks_status is not None else "NOT_RUN",
    }

    def result(status: str, reason: str, **extra: Any) -> dict[str, Any]:
        return {
            "scientific_status": status,
            "execution_status": execution_status,
            "numerical_status": numerical_status,
            "reason": reason,
            "layers": layers,
            "inferred_high_impact": inferred_high,
            "final_scientific_pass": status == "PASS",
            "scope": "final_scientific_claim_only",
            **extra,
        }

    # Resolve actual run failures before evaluating uncertain input assumptions.
    if "FAIL" in (execution_status, numerical_status):
        return result("FAIL", "Execution or numerical solver explicitly failed; cannot be masked by inferred inputs")
    if "BLOCKED" in (execution_status, numerical_status):
        return result("BLOCKED", "Execution or numerical computation is blocked; not an executed failure")
    if "NOT_RUN" in (execution_status, numerical_status):
        return result("NOT_RUN", "Execution or numerical computation has not run")
    if execution_status not in NUMERICAL_STATES or numerical_status not in NUMERICAL_STATES:
        return result("INSUFFICIENT_EVIDENCE", "Unrecognized execution/numerical status")

    # Required validation must be explicitly supplied, never silently default to PASS.
    if required_checks_status is None or required_checks_status == "NOT_RUN":
        return result("NOT_RUN", "Required scientific checks not provided or not run")
    if required_checks_status == "FAIL":
        return result("FAIL", "Required scientific validation explicitly failed")
    if required_checks_status == "BLOCKED":
        return result("BLOCKED", "Required scientific checks blocked")
    if required_checks_status == "INSUFFICIENT_EVIDENCE":
        return result("INSUFFICIENT_EVIDENCE", "Required scientific check evidence insufficient")
    if required_checks_status == "CONDITIONAL":
        return result("CONDITIONAL", "Required scientific checks are conditional")
    if required_checks_status != "PASS":
        return result("INSUFFICIENT_EVIDENCE", "Unrecognized required-check status")

    if conclusion_stable is False:
        return result("INSUFFICIENT_EVIDENCE", "Scientific conclusion changes under plausible parameter endpoints",
                      conclusion_stable=False)
    if insufficient and any(b.get("decision_impact") in ("HIGH", "CRITICAL", None)
                            for b in insufficient):
        return result("INSUFFICIENT_EVIDENCE", "High-impact input lacks adequate provenance or plausible range")

    if inferred_high:
        return result("CONDITIONAL", "High-impact inferred inputs remain disclosed and limit final claims",
                      conclusion_stable=conclusion_stable,
                      acceptable_for=["screening", "exploratory_simulation"])

    low_inferred = [b for b in beliefs if b.get("status") == "inferred"
                    and b.get("decision_impact") == "LOW"]
    if low_inferred:
        return result("CONDITIONAL", "Low-impact inferred inputs: conditional use with disclosure",
                      acceptable_for=["screening", "exploratory_simulation"])

    return result("PASS", "Explicit required checks and execution/numerical prerequisites PASS")
