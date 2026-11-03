"""Endpoint sensitivity budgets for assisted/auto autonomy."""
from __future__ import annotations

from typing import Any

from .parameter_belief import ParameterBelief
from .sensitivity import plan_endpoint_runs


DEFAULT_MAX_BRACKET_JOBS = 2


def plan_sensitivity_with_budget(
    belief: ParameterBelief,
    *,
    max_bracket_jobs: int = DEFAULT_MAX_BRACKET_JOBS,
    autonomy_profile: str = "strict",
) -> dict[str, Any]:
    """
    Wrap endpoint planning with an explicit job budget.

    Never invents a sensitivity scalar; returns status=planned|blocked.
    """
    if belief.plausible_range is None:
        return {
            "status": "unknown",
            "reason": "No plausible_range for endpoints",
            "max_bracket_jobs": max_bracket_jobs,
            "autonomy_profile": autonomy_profile,
        }
    plan = plan_endpoint_runs(belief)
    if plan.get("status") != "planned":
        return {
            "status": plan.get("status", "unknown"),
            "reason": plan.get("reason"),
            "max_bracket_jobs": max_bracket_jobs,
            "autonomy_profile": autonomy_profile,
            "runs": [],
        }
    runs = list(plan.get("runs") or [])
    # Prefer lower/upper extremes when budget is 2 (drop baseline mid if needed).
    if len(runs) > max_bracket_jobs:
        extremes = [r for r in runs if r.get("label") in ("lower_bound", "upper_bound")]
        runs = (extremes or runs)[:max_bracket_jobs]
    return {
        "status": "planned",
        "parameter": belief.parameter,
        "runs": runs,
        "max_bracket_jobs": max_bracket_jobs,
        "autonomy_profile": autonomy_profile,
        "tag": "SENSITIVITY_BRACKET",
        "notes": "Child cases cannot promote parent claim to VALIDATED / EXACT figure match.",
    }
