"""Peer / similar-physics paper priors — plausible ranges only."""
from __future__ import annotations

from typing import Any


def peer_range_prior(
    parameter: str,
    peers: list[dict[str, Any]],
    *,
    unit: str | None = None,
    min_peers: int = 1,
) -> dict[str, Any]:
    """
    Build a literature plausible range from peer records.

    Each peer dict: {doi|source, value|low|high, unit?, physics_family?, note?}
    Never labels the result as a confidence interval.
    """
    usable: list[dict[str, Any]] = []
    for p in peers or []:
        if p.get("value") is None and (p.get("low") is None or p.get("high") is None):
            continue
        usable.append(p)

    if len(usable) < min_peers:
        return {
            "status": "INSUFFICIENT",
            "parameter": parameter,
            "plausible_range": None,
            "evidence": usable,
            "notes": "Too few peer values for a defensible range.",
        }

    lows: list[float] = []
    highs: list[float] = []
    for p in usable:
        if p.get("low") is not None and p.get("high") is not None:
            lows.append(float(p["low"]))
            highs.append(float(p["high"]))
        else:
            v = float(p["value"])
            # ±20% envelope when only a point is published (explicitly not a CI).
            lows.append(v * 0.8)
            highs.append(v * 1.2)

    low, high = min(lows), max(highs)
    mid = 0.5 * (low + high)
    evidence = [
        {
            "provenance": "LITERATURE",
            "source": p.get("doi") or p.get("source") or "peer",
            "value": p.get("value"),
            "plausible_range": (
                {"low": p.get("low"), "high": p.get("high")}
                if p.get("low") is not None
                else None
            ),
            "unit": p.get("unit") or unit,
            "physics_family": p.get("physics_family"),
            "context_similarity": float(p.get("context_similarity", 0.6)),
            "note": p.get("note"),
        }
        for p in usable
    ]
    return {
        "status": "ok",
        "parameter": parameter,
        "unit": unit,
        "central_estimate": mid,
        "plausible_range": {"low": low, "high": high},
        "range_kind": "estimated_plausible_range",
        "provenance": ["INFERRED", "LITERATURE"],
        "evidence": evidence,
        "notes": "Peer-paper plausible range — not a confidence interval; not paper-reported for the target study.",
    }


def as_inference_evidence(prior: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten peer_range_prior result into infer_parameter_belief evidence_sources."""
    if prior.get("status") != "ok":
        return list(prior.get("evidence") or [])
    return [
        {
            "provenance": "LITERATURE",
            "value": prior.get("central_estimate"),
            "plausible_range": prior.get("plausible_range"),
            "source": "peer_range_prior",
            "context_similarity": 0.65,
            "relative_uncertainty": None,
            "note": prior.get("notes"),
        }
    ] + list(prior.get("evidence") or [])
