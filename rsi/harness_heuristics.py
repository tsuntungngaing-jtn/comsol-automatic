"""Harness retention heuristics inspired by RRSI-style regularization (docs only as policy).

These heuristics affect AgentVersion RETAIN/REJECT signals. They never upgrade
physical Scientific VALIDATED status.
"""
from __future__ import annotations

from typing import Any


def score_harness_candidate(
    *,
    in_distribution_gain: float,
    out_of_distribution_gain: float,
    token_cost_ratio: float = 1.0,
    edit_bundle_size: int = 1,
    benchmark_specific: bool = False,
) -> dict[str, Any]:
    """
    Prefer reusable harness mechanisms over benchmark-specific memorization.

    Roughly mirrors RRSI ideas: constrain edit bundles, favor OOD retention,
    penalize token bloat and tiny/noisy edits.
    """
    reasons: list[str] = []
    score = 0.0

    if out_of_distribution_gain > 0:
        score += 2.0 * out_of_distribution_gain
        reasons.append("ood_gain")
    if in_distribution_gain > 0:
        score += 1.0 * in_distribution_gain
        reasons.append("id_gain")
    if out_of_distribution_gain < 0 and in_distribution_gain > 0.05:
        score -= 1.5
        reasons.append("likely_overfit_id")
    if benchmark_specific:
        score -= 1.0
        reasons.append("benchmark_specific_penalty")
    if edit_bundle_size > 3:
        score -= 0.5 * (edit_bundle_size - 3)
        reasons.append("large_edit_bundle")
    if token_cost_ratio > 1.0:
        score -= 0.5 * (token_cost_ratio - 1.0)
        reasons.append("token_cost")
    elif token_cost_ratio < 0.9 and out_of_distribution_gain >= 0:
        score += 0.3
        reasons.append("token_efficiency")

    recommend = "RETAIN_CANDIDATE" if score >= 0.5 else "REJECT_CANDIDATE"
    return {
        "score": score,
        "recommend": recommend,
        "reasons": reasons,
        "affects": "AgentVersion_gate_only",
        "notes": "Does not change Scientific VALIDATED / paper claim status.",
    }


def merge_into_retention_metrics(
    base_metrics: dict[str, Any],
    harness_score: dict[str, Any],
) -> dict[str, Any]:
    """Fold harness heuristic into retention metric dict (performance nudge only)."""
    out = dict(base_metrics)
    bonus = 0.05 if harness_score.get("recommend") == "RETAIN_CANDIDATE" else -0.05
    out["performance"] = float(out.get("performance", 0)) + bonus
    out["harness_heuristic"] = harness_score
    return out
