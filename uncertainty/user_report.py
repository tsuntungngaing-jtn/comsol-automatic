"""Inference Disclosure Report for users."""
from __future__ import annotations

from typing import Any

from .parameter_belief import ParameterBelief


def render_disclosure_report(belief: ParameterBelief) -> dict[str, Any]:
    """Structured + human-readable disclosure. Avoids false precision."""
    rng = belief.plausible_range
    range_text = "not established (INSUFFICIENT evidence)"
    if rng and rng.get("low") is not None and rng.get("high") is not None:
        # Round to avoid pseudo-precision like 1.927364
        low, high = float(rng["low"]), float(rng["high"])
        range_text = f"approximately {low:g} – {high:g} {belief.unit or ''}".strip()

    center_text = "none (not forced)"
    if belief.central_estimate is not None and belief.coverage != "insufficient":
        center_text = f"approximately {float(belief.central_estimate):g} {belief.unit or ''}".strip()

    body = f"""Unknown parameter detected:
{belief.parameter}

Status:
{"Inferred — not directly supplied or measured" if belief.status == "inferred" else belief.status}

Why considered unknown:
{belief.why_unknown or "n/a"}

Current working estimate:
{center_text}

Estimated plausible range:
{range_text}
(range_kind={belief.range_kind}; NOT a confidence interval unless formally defined)

Evidence basis:
{belief.evidence_sources[:5]!r}

Evidence coverage:
{belief.coverage}

Evidence grade:
{belief.evidence_grade}

Sensitivity to reported output:
{(belief.sensitivity or {}).get("status", "unknown")}
score={(belief.sensitivity or {}).get("score")}

Decision impact:
{belief.decision_impact}

Current recommendation:
{belief.recommended_action}

Safe for:
{', '.join(belief.safe_for) or 'none'}

Reliability:
{belief.reliability}

To improve confidence:
Provide manufacturer datasheet, measured value, curing/process condition, or validated calibration data.
"""
    return {
        "parameter": belief.parameter,
        "symbol": belief.symbol,
        "status": belief.status,
        "why_unknown": belief.why_unknown,
        "central_estimate_display": center_text,
        "plausible_range_display": range_text,
        "range_kind": belief.range_kind,
        "evidence_coverage": belief.coverage,
        "evidence_grade": belief.evidence_grade,
        "sensitivity": belief.sensitivity,
        "decision_impact": belief.decision_impact,
        "recommended_action": belief.recommended_action,
        "safe_for": list(belief.safe_for),
        "reliability": belief.reliability,
        "text": body.strip(),
        "belief": belief.to_dict(),
    }
