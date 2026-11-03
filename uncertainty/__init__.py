"""Uncertainty-aware parameter inference for COMSOL Automatic RSI."""

from .parameter_belief import ParameterBelief, PROVENANCE_STATES
from .detector import detect_unknown_parameters
from .inference import infer_parameter_belief
from .decision_gate import decide_action, DecisionImpact
from .user_report import render_disclosure_report
from .autonomy import get_autonomy_profile, apply_autonomy_policy, pack_decision_requests
from .doc_default import doc_default_resolve
from .peer_prior import peer_range_prior, as_inference_evidence
from .figure_digitize import (
    digitize_axis_span,
    digitize_colorbar_fraction,
    assert_not_reported,
    overlap_with_kpi,
)
from .sensitivity_budget import plan_sensitivity_with_budget

__all__ = [
    "ParameterBelief",
    "PROVENANCE_STATES",
    "detect_unknown_parameters",
    "infer_parameter_belief",
    "decide_action",
    "DecisionImpact",
    "render_disclosure_report",
    "get_autonomy_profile",
    "apply_autonomy_policy",
    "pack_decision_requests",
    "doc_default_resolve",
    "peer_range_prior",
    "as_inference_evidence",
    "digitize_axis_span",
    "digitize_colorbar_fraction",
    "assert_not_reported",
    "overlap_with_kpi",
    "plan_sensitivity_with_budget",
]
