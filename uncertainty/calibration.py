"""Cross-task calibration: prediction vs observation without single-sample overwrite."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compare_prediction_to_observation(
    prediction: dict[str, Any],
    observed: dict[str, Any],
) -> dict[str, Any]:
    """
    prediction: {central_estimate?, plausible_range?, parameter, agent_version, ...}
    observed: {value, unit?, source provenance}
    Never mutates prediction.
    """
    pred = dict(prediction)
    obs_value = observed.get("value")
    rng = pred.get("plausible_range") or {}
    low, high = rng.get("low"), rng.get("high")
    coverage_success = None
    if obs_value is not None and low is not None and high is not None:
        coverage_success = float(low) <= float(obs_value) <= float(high)
    err = None
    if obs_value is not None and pred.get("central_estimate") is not None:
        err = float(obs_value) - float(pred["central_estimate"])
    return {
        "calibration_id": "cal-" + uuid.uuid4().hex[:12],
        "parameter": pred.get("parameter"),
        "prediction": pred,  # frozen copy
        "observed": dict(observed),
        "coverage_success": coverage_success,
        "prediction_error": err,
        "created_at": _now(),
    }


class PriorStore:
    """
    Context-keyed prior accumulator.
    A single sample must not overwrite an entire material-family prior.
    """

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _key(parameter: str, context: dict[str, Any]) -> str:
        family = context.get("material_family") or "unknown_family"
        return f"{parameter}::{family}"

    def update(
        self,
        *,
        parameter: str,
        context: dict[str, Any],
        observed_value: float,
        evidence_quality: float = 1.0,
        context_similarity: float = 1.0,
    ) -> dict[str, Any]:
        key = self._key(parameter, context)
        entry = self._entries.get(key)
        if entry is None:
            entry = {
                "parameter": parameter,
                "material_family": context.get("material_family"),
                "sample_count": 0,
                "values": [],
                "weights": [],
                "mean": None,
                "plausible_range": None,
            }
        # Soft update: append sample; never replace wholesale.
        w = max(0.0, float(evidence_quality) * float(context_similarity))
        entry["values"].append(float(observed_value))
        entry["weights"].append(w)
        entry["sample_count"] = len(entry["values"])
        # Weighted mean
        num = sum(v * wt for v, wt in zip(entry["values"], entry["weights"]))
        den = sum(entry["weights"]) or 1.0
        entry["mean"] = num / den
        vals = entry["values"]
        entry["plausible_range"] = {"low": min(vals), "high": max(vals)}
        # Widen if few samples (epistemic caution)
        if entry["sample_count"] < 3 and entry["mean"] is not None:
            span = max(abs(entry["mean"]) * 0.25, 1e-12)
            entry["plausible_range"] = {
                "low": entry["mean"] - span,
                "high": entry["mean"] + span,
            }
            # still include observed extrema
            entry["plausible_range"]["low"] = min(entry["plausible_range"]["low"], min(vals))
            entry["plausible_range"]["high"] = max(entry["plausible_range"]["high"], max(vals))
        self._entries[key] = entry
        return dict(entry)

    def get(self, parameter: str, context: dict[str, Any]) -> dict[str, Any] | None:
        return self._entries.get(self._key(parameter, context))

    def all(self) -> list[dict[str, Any]]:
        return [dict(v) for v in self._entries.values()]
