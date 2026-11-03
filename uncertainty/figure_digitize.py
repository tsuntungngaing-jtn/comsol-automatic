"""Offline figure/axis digitization MVP — digitized_estimate only."""
from __future__ import annotations

from typing import Any


ORIGIN = "digitized_estimate"


def digitize_axis_span(
    *,
    axis_min: float,
    axis_max: float,
    pixel_low: float,
    pixel_high: float,
    pixel_sample: float,
    relative_uncertainty: float = 0.05,
    quality: str = "ok",
) -> dict[str, Any]:
    """
    Linear map from pixel sample on an axis to a value interval.

    ``quality`` in {ok, low, unusable}. Unusable → NOT_RUN clue.
    """
    if quality == "unusable" or pixel_high == pixel_low:
        return {
            "status": "NOT_RUN",
            "origin": ORIGIN,
            "value": None,
            "interval": None,
            "notes": "Digitization quality insufficient; clue discarded.",
        }
    t = (pixel_sample - pixel_low) / (pixel_high - pixel_low)
    value = axis_min + t * (axis_max - axis_min)
    span = abs(axis_max - axis_min)
    u = max(relative_uncertainty, 0.1 if quality == "low" else relative_uncertainty)
    half = 0.5 * u * span
    return {
        "status": "ok",
        "origin": ORIGIN,
        "value": value,
        "interval": {"low": value - half, "high": value + half},
        "unit": None,
        "may_promote_to_reported": False,
        "notes": "digitized_estimate — never upgrade to reported without textual paper number + user confirmation that keeps digitized provenance.",
    }


def digitize_colorbar_fraction(
    *,
    cmin: float,
    cmax: float,
    fraction_from_bottom: float,
    relative_uncertainty: float = 0.08,
    quality: str = "ok",
) -> dict[str, Any]:
    """Sample a colorbar by fractional position in [0, 1] from the low end."""
    if quality == "unusable" or not (0.0 <= fraction_from_bottom <= 1.0):
        return {
            "status": "NOT_RUN",
            "origin": ORIGIN,
            "value": None,
            "interval": None,
            "notes": "Colorbar sample unusable.",
        }
    value = cmin + fraction_from_bottom * (cmax - cmin)
    span = abs(cmax - cmin)
    u = max(relative_uncertainty, 0.12 if quality == "low" else relative_uncertainty)
    half = 0.5 * u * span
    return {
        "status": "ok",
        "origin": ORIGIN,
        "value": value,
        "interval": {"low": value - half, "high": value + half},
        "may_promote_to_reported": False,
        "claim_use": "bracket_or_sensitivity_only",
        "notes": "For claim brackets only — forbids EXACT figure reproduction claims.",
    }


def assert_not_reported(digitized: dict[str, Any]) -> None:
    """Hard guard used by tests and callers."""
    if digitized.get("origin") == ORIGIN and digitized.get("promoted_to_reported"):
        raise ValueError("digitized_estimate must not be promoted to reported")
    if digitized.get("may_promote_to_reported") is True:
        raise ValueError("may_promote_to_reported must remain False for digitized_estimate")


def overlap_with_kpi(digitized: dict[str, Any], kpi_value: float) -> dict[str, Any]:
    """Weak RSI Evaluate signal: whether KPI falls in digitized interval."""
    if digitized.get("status") != "ok" or not digitized.get("interval"):
        return {"status": "NOT_RUN", "overlap": None}
    lo = float(digitized["interval"]["low"])
    hi = float(digitized["interval"]["high"])
    inside = lo <= float(kpi_value) <= hi
    return {
        "status": "ok",
        "overlap": inside,
        "origin": ORIGIN,
        "notes": "Weak calibration only — does not alone retain AgentVersion.",
    }
