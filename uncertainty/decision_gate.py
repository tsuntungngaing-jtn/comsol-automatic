"""Uncertainty × Sensitivity decision gate (Unknown Parameter Decision Gate)."""
from __future__ import annotations

from enum import Enum
from typing import Any

from .parameter_belief import ParameterBelief


class DecisionImpact(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def normalize_uncertainty(belief: ParameterBelief) -> float:
    """Map epistemic uncertainty / coverage to U in [0, 1]."""
    if belief.coverage == "insufficient" or belief.reliability == "INSUFFICIENT":
        return 1.0
    if belief.status == "known":
        return 0.0
    if belief.epistemic_uncertainty is not None:
        # Relative span ~0 → 0; ~2 (200%) → 1
        return _clip01(belief.epistemic_uncertainty / 2.0)
    coverage_u = {"high": 0.2, "moderate": 0.45, "low": 0.75}.get(belief.coverage, 1.0)
    return coverage_u


def normalize_sensitivity(sensitivity: dict[str, Any] | None) -> float:
    """
    Map sensitivity evidence to S in [0, 1].
    If unknown / not measured, return None sentinel via raising? We use explicit status.
    """
    if not sensitivity or sensitivity.get("status") in (None, "unknown"):
        return -1.0  # sentinel: unknown
    if sensitivity.get("status") == "planned":
        return -1.0
    score = sensitivity.get("score")
    if score is not None:
        return _clip01(float(score))
    # From endpoint stability: unstable → high S
    if sensitivity.get("conclusion_stable") is False:
        return 0.9
    if sensitivity.get("conclusion_stable") is True:
        return 0.15
    return 0.5


def impact_from_product(u: float, s: float) -> DecisionImpact:
    """Standardized I = U × S with thresholds (DESIGN_POLICY)."""
    i = u * s
    if i < 0.08:
        return DecisionImpact.LOW
    if i < 0.25:
        return DecisionImpact.MEDIUM
    if i < 0.55:
        return DecisionImpact.HIGH
    return DecisionImpact.CRITICAL


def decide_action(
    belief: ParameterBelief,
    *,
    sensitivity: dict[str, Any] | None = None,
    allow_sensitivity_run: bool = True,
) -> ParameterBelief:
    """
    Update belief.recommended_action / decision_impact / safe_for.

    Avoids both extremes: ask-everything and guess-everything.
    """
    u = normalize_uncertainty(belief)
    sens = sensitivity if sensitivity is not None else belief.sensitivity
    s_norm = normalize_sensitivity(sens)

    if belief.coverage == "insufficient" or belief.reliability == "INSUFFICIENT":
        belief.decision_impact = DecisionImpact.CRITICAL.value
        belief.recommended_action = "ASK_USER"
        belief.safe_for = []
        belief.sensitivity = sens or {"status": "unknown"}
        return belief

    if belief.status == "known":
        belief.decision_impact = DecisionImpact.LOW.value
        belief.recommended_action = "AUTO_ACCEPT"
        belief.safe_for = [
            "screening",
            "exploratory_simulation",
            "optimization",
            "final_validation",
        ]
        return belief

    if s_norm < 0:
        # Sensitivity unknown: do not invent a scalar. Prefer information-seeking.
        belief.sensitivity = {"status": "unknown"}
        if u <= 0.25:
            belief.decision_impact = DecisionImpact.LOW.value
            belief.recommended_action = "AUTO_ACCEPT"
            belief.safe_for = ["screening", "exploratory_simulation"]
        elif allow_sensitivity_run:
            belief.decision_impact = DecisionImpact.HIGH.value
            belief.recommended_action = "RUN_SENSITIVITY"
            belief.safe_for = ["screening"]
        else:
            belief.decision_impact = DecisionImpact.HIGH.value
            belief.recommended_action = "ASK_USER"
            belief.safe_for = []
        return belief

    impact = impact_from_product(u, s_norm)
    belief.decision_impact = impact.value
    belief.sensitivity = dict(sens or {})
    belief.sensitivity["normalized"] = s_norm
    belief.sensitivity["uncertainty_normalized"] = u
    belief.sensitivity["impact_score"] = u * s_norm

    if impact == DecisionImpact.LOW:
        belief.recommended_action = "AUTO_ACCEPT"
        belief.safe_for = ["screening", "exploratory_simulation"]
        if u < 0.15:
            belief.safe_for.append("optimization")
    elif impact == DecisionImpact.MEDIUM:
        belief.recommended_action = "AUTO_ACCEPT"
        belief.safe_for = ["screening", "exploratory_simulation"]
        belief.notes = (belief.notes or "") + " MEDIUM impact: disclose and prefer endpoint propagation."
    elif impact == DecisionImpact.HIGH:
        belief.recommended_action = (
            "RUN_SENSITIVITY" if allow_sensitivity_run else "SEEK_MORE_EVIDENCE"
        )
        belief.safe_for = ["screening"]
    else:
        belief.recommended_action = "BLOCK_FINAL_VALIDATION"
        if u >= 0.8:
            belief.recommended_action = "ASK_USER"
        belief.safe_for = []

    return belief
