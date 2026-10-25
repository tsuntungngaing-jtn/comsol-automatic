"""Propagate endpoint simulation outcomes → conclusion stability."""
from __future__ import annotations

from typing import Any


def propagate_endpoints(
    plan: dict[str, Any],
    outcomes: list[dict[str, Any]],
    *,
    ranking_key: str = "design_rank",
    constraint_key: str = "constraint_ok",
    metric_key: str = "metric",
) -> dict[str, Any]:
    """
    outcomes: list of {label, metric?, design_rank?, constraint_ok?, scientific_conclusion?}
    """
    if plan.get("status") not in ("planned", "measured", "propagated") or not plan.get("runs"):
        return {
            "status": "NOT_RUN",
            "reason": "No endpoint plan",
            "conclusion_stable": None,
            "sensitivity": {"status": "unknown"},
        }
    if len(outcomes) < 2:
        return {
            "status": "NOT_RUN",
            "reason": "Need at least two endpoint outcomes",
            "conclusion_stable": None,
            "sensitivity": {"status": "unknown"},
        }

    metrics = [o.get(metric_key) for o in outcomes if o.get(metric_key) is not None]
    ranks = [o.get(ranking_key) for o in outcomes if o.get(ranking_key) is not None]
    constraints = [o.get(constraint_key) for o in outcomes if constraint_key in o]
    conclusions = [o.get("scientific_conclusion") for o in outcomes if "scientific_conclusion" in o]

    ranking_stable = len(set(ranks)) <= 1 if ranks else None
    constraint_stable = len(set(constraints)) <= 1 if constraints else None
    conclusion_stable = len(set(conclusions)) <= 1 if conclusions else None

    metric_range = None
    if metrics:
        metric_range = {"low": min(metrics), "high": max(metrics)}

    # Sensitivity score: unstable conclusion → high
    if conclusion_stable is False or ranking_stable is False:
        score = 0.9
    elif constraint_stable is False:
        score = 0.7
    elif metric_range and metrics and abs(max(metrics) - min(metrics)) > 0:
        mid = 0.5 * (max(metrics) + min(metrics)) or 1.0
        rel = abs(max(metrics) - min(metrics)) / abs(mid)
        score = min(1.0, rel)
    else:
        score = 0.15

    summary = (
        "Although the parameter is uncertain, the design ranking/conclusion "
        "remains unchanged across the plausible interval."
        if conclusion_stable and (ranking_stable in (True, None))
        else "The inferred range changes the reported conclusion enough to reverse "
        "or destabilize it; user evidence is required before final scientific PASS."
        if conclusion_stable is False or ranking_stable is False
        else "Endpoint propagation completed; interpret metric range with disclosure."
    )

    return {
        "status": "propagated",
        "method": "endpoint",
        "output_range": metric_range,
        "ranking_stable": ranking_stable,
        "constraint_stable": constraint_stable,
        "conclusion_stable": conclusion_stable,
        "summary": summary,
        "sensitivity": {
            "status": "propagated",
            "method": "endpoint",
            "score": score,
            "conclusion_stable": conclusion_stable,
            "ranking_stable": ranking_stable,
        },
        "outcomes": outcomes,
    }
