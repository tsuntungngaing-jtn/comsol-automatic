"""Uncertainty-aware parameter inference for COMSOL Automatic RSI V0.1."""

from .parameter_belief import ParameterBelief, PROVENANCE_STATES
from .detector import detect_unknown_parameters
from .inference import infer_parameter_belief
from .decision_gate import decide_action, DecisionImpact
from .user_report import render_disclosure_report

__all__ = [
    "ParameterBelief",
    "PROVENANCE_STATES",
    "detect_unknown_parameters",
    "infer_parameter_belief",
    "decide_action",
    "DecisionImpact",
    "render_disclosure_report",
]
