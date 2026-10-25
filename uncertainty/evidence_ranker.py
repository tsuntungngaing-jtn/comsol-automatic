"""Evidence ranking and context-similarity weighting."""
from __future__ import annotations

from typing import Any

SOURCE_RANK = {
    "USER_SUPPLIED": 100,
    "MEASURED": 95,
    "MANUFACTURER_SPEC": 90,
    "VALIDATED_PRIOR_TASK": 80,
    "LITERATURE": 70,
    "DATABASE": 55,
    "INFERRED": 25,
    "DEFAULT": 10,
    "UNKNOWN": 0,
}

GRADE_FROM_RANK = (
    (90, "A"),
    (70, "B"),
    (40, "C"),
    (0, "D"),
)


def context_similarity(context_a: dict[str, Any], context_b: dict[str, Any]) -> float:
    """
    Simple structured similarity in [0, 1].
    Dissimilar material family → strong downweight (CASE 7).
    """
    if not context_a or not context_b:
        return 0.0
    keys = ("material_family", "physics_type", "manufacturing_process", "geometry_class")
    scores: list[float] = []
    for key in keys:
        a, b = context_a.get(key), context_b.get(key)
        if a is None or b is None:
            continue
        if key == "material_family" and a != b:
            return 0.15  # hard penalty: do not transfer narrow priors
        scores.append(1.0 if a == b else 0.0)
    if not scores:
        return 0.3
    return sum(scores) / len(scores)


def rank_evidence(
    sources: list[dict[str, Any]],
    *,
    task_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for src in sources:
        provenance = src.get("provenance", "UNKNOWN")
        base = float(SOURCE_RANK.get(provenance, 0))
        sim = 1.0
        if task_context is not None and src.get("context"):
            sim = context_similarity(task_context, src["context"])
        weight = base * sim
        item = dict(src)
        item["rank_score"] = weight
        item["context_similarity"] = sim
        ranked.append(item)
    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    return ranked


def evidence_grade(ranked: list[dict[str, Any]]) -> str:
    if not ranked:
        return "D"
    top = ranked[0]["rank_score"]
    for threshold, grade in GRADE_FROM_RANK:
        if top >= threshold:
            return grade
    return "D"


def coverage_from_ranked(ranked: list[dict[str, Any]], min_similarity: float = 0.4) -> str:
    usable = [r for r in ranked if r.get("context_similarity", 1.0) >= min_similarity]
    if not usable:
        return "insufficient"
    top = usable[0]
    if top.get("provenance") in ("UNKNOWN", "DEFAULT") and top.get("value") is None:
        return "insufficient"
    if top["rank_score"] < 20:
        return "insufficient"
    if top["rank_score"] >= 85 and top.get("context_similarity", 0) >= 0.75:
        return "high"
    if top["rank_score"] >= 55:
        return "moderate"
    if top["rank_score"] >= 25:
        return "low"
    return "insufficient"
