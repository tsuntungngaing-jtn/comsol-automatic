"""Unknown / incomplete parameter detection with provenance classification."""
from __future__ import annotations

from typing import Any

from .parameter_belief import PROVENANCE_STATES


KNOWN_ORIGINS_TO_PROVENANCE = {
    "user_supplied": "USER_SUPPLIED",
    "reported": "MEASURED",  # only when explicitly measured; caller may override
    "library": "DATABASE",
    "documented_default": "DEFAULT",
    "assumption": "INFERRED",
    "inferred": "INFERRED",
    "fitted": "INFERRED",
    "derived": "LITERATURE",
    "missing": "UNKNOWN",
}


def classify_provenance(record: dict[str, Any]) -> str:
    """Map an input parameter / evidence record to a provenance state."""
    explicit = record.get("provenance") or record.get("parameter_provenance")
    if isinstance(explicit, str) and explicit in PROVENANCE_STATES:
        return explicit
    if isinstance(explicit, list) and explicit:
        first = explicit[0]
        if first in PROVENANCE_STATES:
            return first
    origin = (record.get("origin") or "").lower()
    if origin in KNOWN_ORIGINS_TO_PROVENANCE:
        # measured override
        if origin == "reported" and record.get("source_type") in (
            "measurement",
            "experiment",
            "lab",
        ):
            return "MEASURED"
        if origin == "reported" and record.get("source_type") in (
            "manufacturer",
            "datasheet",
        ):
            return "MANUFACTURER_SPEC"
        if origin == "reported" and record.get("source_type") in ("paper", "literature"):
            return "LITERATURE"
        if origin == "derived" and record.get("source_type") == "validated_prior_task":
            return "VALIDATED_PRIOR_TASK"
        return KNOWN_ORIGINS_TO_PROVENANCE[origin]
    value = record.get("value", record.get("central_estimate"))
    if value is None and not record.get("plausible_range"):
        return "UNKNOWN"
    if record.get("origin") is None and value is not None:
        # Nominal value without provenance is not permission to treat as known.
        return "UNKNOWN"
    return "UNKNOWN"


def _missing_unit(record: dict[str, Any]) -> bool:
    unit = record.get("unit")
    return unit is None or (isinstance(unit, str) and not unit.strip())


def _affects_current_physics(record: dict[str, Any], physics_interfaces: list[str]) -> bool:
    affects = record.get("affects") or record.get("physics_interfaces") or []
    if not physics_interfaces:
        return True  # conservative: treat as relevant until scoped
    if not affects:
        return bool(record.get("scientifically_relevant", True))
    return any(a in physics_interfaces or a in ("solve", "claim_validation", "material_assignment") for a in affects)


def detect_unknown_parameters(
    parameters: list[dict[str, Any]],
    *,
    physics_interfaces: list[str] | None = None,
    report_objectives: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Detect scientifically relevant unknowns / incomplete parameters.

    Returns detector findings (not yet full ParameterBelief). Never invents values.
    """
    physics_interfaces = list(physics_interfaces or [])
    report_objectives = list(report_objectives or [])
    findings: list[dict[str, Any]] = []

    for raw in parameters:
        name = raw.get("parameter") or raw.get("name") or raw.get("quantity_id") or "unnamed"
        symbol = raw.get("symbol") or name
        provenance = classify_provenance(raw)
        value = raw.get("value", raw.get("central_estimate"))
        unit_missing = _missing_unit(raw)
        relevant = _affects_current_physics(raw, physics_interfaces)
        impacts_objective = True
        if report_objectives and raw.get("affects"):
            impacts_objective = any(
                o in raw["affects"] or o in report_objectives for o in report_objectives
            ) or any(a in ("solve", "claim_validation") for a in raw.get("affects", []))

        reasons: list[str] = []
        is_unknown = False

        if provenance == "UNKNOWN" or provenance == "DEFAULT" and value is None:
            is_unknown = True
            reasons.append("parameter provenance is UNKNOWN or value missing")
        if value is None and not raw.get("plausible_range"):
            is_unknown = True
            reasons.append("value is missing and no plausible_range supplied")
        if value is not None and provenance == "UNKNOWN":
            is_unknown = True
            reasons.append("nominal value present without evidence provenance")
        if unit_missing and (value is not None or is_unknown):
            reasons.append("unit missing")
            is_unknown = True
        if not relevant:
            # Not relevant to current physics: do not escalate as unknown for solve.
            findings.append(
                {
                    "parameter": name,
                    "symbol": symbol,
                    "unit": raw.get("unit"),
                    "provenance": provenance,
                    "is_unknown": False,
                    "scientifically_relevant": False,
                    "impacts_objective": False,
                    "reasons": ["not relevant to current physics interfaces"],
                    "raw": raw,
                }
            )
            continue

        findings.append(
            {
                "parameter": name,
                "symbol": symbol,
                "unit": raw.get("unit"),
                "provenance": provenance,
                "is_unknown": is_unknown,
                "scientifically_relevant": True,
                "impacts_objective": impacts_objective,
                "reasons": reasons
                or (["known with provenance"] if not is_unknown else ["unclassified"]),
                "value": value,
                "raw": raw,
            }
        )
    return findings


def unknown_only(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [f for f in findings if f.get("is_unknown") and f.get("scientifically_relevant")]
