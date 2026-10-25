"""Harness-side improver: propose AgentVersion candidates from experiences."""
from __future__ import annotations

from typing import Any

from .versioning import AgentVersionRegistry


def synthesize_candidate(
    registry: AgentVersionRegistry,
    experiences: list[dict[str, Any]],
    *,
    reason: str = "experience synthesis",
) -> dict[str, Any]:
    """
    Update policies from non-held-out experiences.
    V0.1: adjust parameter prior hints and ask_policy thresholds from lessons.
    """
    parent = registry.active()
    policies = dict(parent.get("policies") or {})
    priors = dict(policies.get("parameter_priors") or {})
    changes: list[dict[str, Any]] = []
    used: list[str] = []

    for exp in experiences:
        if exp.get("dataset_split") == "held_out":
            continue
        used.append(exp["experience_id"])
        for belief in exp.get("parameter_beliefs") or []:
            if belief.get("status") != "inferred":
                continue
            if exp.get("actual_outcome") and exp["actual_outcome"].get("parameter_value") is not None:
                key = belief.get("parameter")
                ctx = (exp.get("context") or {}).get("material_family", "unknown")
                priors[f"{key}::{ctx}"] = {
                    "central_estimate": exp["actual_outcome"]["parameter_value"],
                    "from_experience": exp["experience_id"],
                    "sample_note": "single-sample hint; PriorStore should accumulate",
                }
                changes.append(
                    {
                        "component": "parameter_priors",
                        "summary": f"calibrated hint for {key} in {ctx}",
                    }
                )
        lesson = exp.get("lesson_learned")
        if lesson and "ask_user" in lesson.lower():
            policies["ask_policy"] = "prefer_sensitivity_before_ask"
            changes.append(
                {
                    "component": "ask_policy",
                    "summary": "prefer sensitivity before asking user when impact high",
                }
            )

    policies["parameter_priors"] = priors
    if not changes:
        changes.append({"component": "workflow", "summary": "no-op candidate from empty lessons"})

    return registry.propose_candidate(
        changes=changes,
        experience_used=used,
        policies=policies,
        reason=reason,
    )
