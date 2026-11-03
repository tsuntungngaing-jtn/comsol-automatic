"""Resolve SOFTWARE_DOC_DEFAULT feature-class defaults from official docs."""
from __future__ import annotations

from typing import Any


# Institutional defaults already used in CHT gates (not paper-reported).
_KNOWN_DEFAULTS: dict[str, dict[str, Any]] = {
    "inlet_thermal_bc": {
        "feature_class": "Inflow",
        "property_hint": "Tustr",
        "locus": "Heat Transfer Module docs — open inlet thermal condition",
        "marker": "[SOFTWARE_DOC_DEFAULT: HT open-inlet Inflow/Tustr]",
    },
    "outlet_thermal_bc": {
        "feature_class": "ConvectiveOutflow",
        "property_hint": None,
        "locus": "Heat Transfer Module docs — open outlet",
        "marker": "[SOFTWARE_DOC_DEFAULT: HT open-outlet ConvectiveOutflow]",
    },
    "stationary_turbulent_cht_solver_class": {
        "feature_class": "Segregated",
        "property_hint": "subdtech/maxsubiter",
        "locus": "CFD/CHT practice + skill cht-coupling-energy-gates",
        "marker": "[SOFTWARE_DOC_DEFAULT: Segregated sequence class]",
    },
}


def doc_default_resolve(
    parameter_or_role: str,
    *,
    paper_reported: Any = None,
    extra_catalog: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Look up an official-documentation default for a modeling role.

    If ``paper_reported`` is not None and disagrees with the doc default feature
    class, return status=conflict (paper wins for values; doc still recorded).
    """
    catalog = dict(_KNOWN_DEFAULTS)
    if extra_catalog:
        catalog.update(extra_catalog)

    key = parameter_or_role.strip()
    # allow aliases
    aliases = {
        "inlet_T_bc": "inlet_thermal_bc",
        "outlet_T_bc": "outlet_thermal_bc",
        "solver_class": "stationary_turbulent_cht_solver_class",
    }
    key = aliases.get(key, key)

    if key not in catalog:
        return {
            "status": "NOT_FOUND",
            "parameter": parameter_or_role,
            "has_software_doc_default": False,
            "evidence": None,
        }

    entry = dict(catalog[key])
    evidence = {
        "provenance": "DEFAULT",
        "source": "installed_official_docs",
        "locus": entry["locus"],
        "marker": entry["marker"],
        "feature_class": entry["feature_class"],
        "property_hint": entry.get("property_hint"),
        "value": entry["feature_class"],
        "context_similarity": 1.0,
    }

    if paper_reported is not None and str(paper_reported) != str(entry["feature_class"]):
        return {
            "status": "conflict",
            "parameter": parameter_or_role,
            "has_software_doc_default": True,
            "paper_reported": paper_reported,
            "doc_default": entry["feature_class"],
            "winner": "paper_reported",
            "evidence": evidence,
            "notes": "Paper reported value wins; doc default retained as non-overriding candidate.",
        }

    return {
        "status": "ok",
        "parameter": parameter_or_role,
        "has_software_doc_default": True,
        "doc_default": entry["feature_class"],
        "evidence": evidence,
        "marker": entry["marker"],
    }
