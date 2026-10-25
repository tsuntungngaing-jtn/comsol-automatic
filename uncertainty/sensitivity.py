"""Low-cost endpoint sensitivity planning (V0.1: low / mid / high only)."""
from __future__ import annotations

from typing import Any

from .parameter_belief import ParameterBelief


def plan_endpoint_runs(belief: ParameterBelief) -> dict[str, Any]:
    """
    Build a baseline + lower + upper solve plan.
    Does not execute COMSOL; returns a plan for the outer controller / operator.
    """
    if belief.plausible_range is None or belief.central_estimate is None:
        return {
            "status": "NOT_RUN",
            "method": "endpoint",
            "reason": "No plausible_range/central_estimate — cannot plan endpoints",
            "runs": [],
        }
    low = belief.plausible_range["low"]
    high = belief.plausible_range["high"]
    mid = belief.central_estimate
    return {
        "status": "planned",
        "method": "endpoint",
        "parameter": belief.parameter,
        "symbol": belief.symbol,
        "unit": belief.unit,
        "runs": [
            {"label": "lower_bound", "value": low},
            {"label": "baseline", "value": mid},
            {"label": "upper_bound", "value": high},
        ],
        "notes": "V0.1 prefers endpoint simulation over Monte Carlo.",
    }
