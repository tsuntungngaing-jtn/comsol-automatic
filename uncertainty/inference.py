"""Parameter inference engine: plausible ranges or INSUFFICIENT — never silent guesses."""
from __future__ import annotations

from typing import Any

from .evidence_ranker import coverage_from_ranked, evidence_grade, rank_evidence
from .parameter_belief import ParameterBelief


def _span_uncertainty(low: float, high: float, mid: float | None = None) -> float:
    if high <= low:
        return 0.0
    center = mid if mid is not None else 0.5 * (low + high)
    if center == 0:
        return abs(high - low)
    return abs(high - low) / abs(center)


def infer_parameter_belief(
    finding: dict[str, Any],
    *,
    evidence_sources: list[dict[str, Any]] | None = None,
    task_context: dict[str, Any] | None = None,
    agent_version: str = "A0",
    prior_beliefs: list[dict[str, Any]] | None = None,
) -> ParameterBelief:
    """
    Build a ParameterBelief from a detector finding + ranked evidence.

    If coverage is insufficient, returns unresolved belief with no fabricated range.
    """
    name = finding["parameter"]
    symbol = finding.get("symbol") or name
    unit = finding.get("unit")
    why = "; ".join(finding.get("reasons") or []) or "unknown parameter"

    sources = list(evidence_sources or [])
    # Attach prior-task beliefs as evidence candidates (with their contexts).
    for prior in prior_beliefs or []:
        if prior.get("parameter") != name and prior.get("symbol") != symbol:
            continue
        sources.append(
            {
                "provenance": "VALIDATED_PRIOR_TASK",
                "value": prior.get("central_estimate"),
                "plausible_range": prior.get("plausible_range"),
                "context": prior.get("context") or {},
                "source": prior.get("task_id", "prior_task"),
            }
        )

    ranked = rank_evidence(sources, task_context=task_context)
    coverage = coverage_from_ranked(ranked)
    grade = evidence_grade(ranked)

    if coverage == "insufficient" or not ranked:
        return ParameterBelief(
            parameter=name,
            symbol=symbol,
            unit=unit,
            status="unresolved",
            central_estimate=None,
            plausible_range=None,
            range_kind="none",
            evidence_sources=ranked,
            evidence_grade=grade,
            coverage="insufficient",
            reliability="INSUFFICIENT",
            recommended_action="ASK_USER",
            safe_for=[],
            provenance=["UNKNOWN"],
            agent_version=agent_version,
            why_unknown=why,
            notes="INSUFFICIENT is a legal scientific conclusion; no range invented.",
        )

    top = ranked[0]
    # Dissimilar context: do not transfer a narrow prior as a tight range.
    if top.get("context_similarity", 1.0) < 0.4:
        return ParameterBelief(
            parameter=name,
            symbol=symbol,
            unit=unit,
            status="unresolved",
            coverage="insufficient",
            range_kind="none",
            evidence_sources=ranked,
            evidence_grade=grade,
            reliability="INSUFFICIENT",
            recommended_action="SEEK_MORE_EVIDENCE",
            safe_for=[],
            provenance=["UNKNOWN"],
            agent_version=agent_version,
            why_unknown=why + "; evidence context dissimilar",
            notes="Refusing narrow prior transfer across dissimilar material/context.",
        )

    rng = top.get("plausible_range")
    value = top.get("value")
    if rng and rng.get("low") is not None and rng.get("high") is not None:
        low, high = float(rng["low"]), float(rng["high"])
        mid = float(value) if value is not None else 0.5 * (low + high)
    elif value is not None and top.get("relative_uncertainty") is not None:
        mid = float(value)
        rel = float(top["relative_uncertainty"])
        low, high = mid * (1 - rel), mid * (1 + rel)
    elif value is not None and top.get("provenance") in (
        "USER_SUPPLIED",
        "MEASURED",
        "MANUFACTURER_SPEC",
    ):
        # Known supplied value — not an inference.
        return ParameterBelief(
            parameter=name,
            symbol=symbol,
            unit=unit,
            status="known",
            central_estimate=value,
            plausible_range=None,
            range_kind="none",
            evidence_sources=ranked,
            evidence_grade=grade,
            coverage=coverage,
            epistemic_uncertainty=0.0,
            reliability="RELIABLE",
            recommended_action="AUTO_ACCEPT",
            safe_for=["screening", "exploratory_simulation", "optimization", "final_validation"],
            provenance=[top.get("provenance", "USER_SUPPLIED")],
            agent_version=agent_version,
            why_unknown=None,
        )
    else:
        # Have ranked evidence but cannot form a defensible range.
        return ParameterBelief(
            parameter=name,
            symbol=symbol,
            unit=unit,
            status="unresolved",
            coverage="insufficient",
            range_kind="none",
            evidence_sources=ranked,
            evidence_grade=grade,
            reliability="INSUFFICIENT",
            recommended_action="ASK_USER",
            safe_for=[],
            provenance=["UNKNOWN"],
            agent_version=agent_version,
            why_unknown=why + "; ranked evidence lacks usable range",
        )

    u = _span_uncertainty(low, high, mid)
    return ParameterBelief(
        parameter=name,
        symbol=symbol,
        unit=unit,
        status="inferred",
        central_estimate=mid,
        plausible_range={"low": low, "high": high},
        range_kind="estimated_plausible_range",
        evidence_sources=ranked,
        evidence_grade=grade,
        coverage=coverage,
        epistemic_uncertainty=u,
        reliability="RELIABLE" if coverage in ("high", "moderate") else "UNRELIABLE",
        recommended_action="AUTO_ACCEPT",  # decision_gate may override
        safe_for=["screening", "exploratory_simulation"],
        provenance=["INFERRED", top.get("provenance", "LITERATURE")],
        agent_version=agent_version,
        why_unknown=why,
        notes="Estimated plausible range — not a confidence interval.",
    )
