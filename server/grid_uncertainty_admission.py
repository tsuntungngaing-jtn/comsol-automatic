"""Read-only admission of grid-refinement evidence; NOT a numerical uncertainty estimator.

Based on Eca & Hoekstra, JCP 262 (2014), 104-130, Appendix A.
Never computes U_phi, Richardson order, GCI, or scientific PASS.
"""
from __future__ import annotations

import math

SCHEMA = "grid-evidence-admission/0.1.0"
FIELDS = ("geometry_hash", "physics_hash", "boundary_hash",
          "observable_definition_hash", "solver_settings_hash")


def review_grid_family(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("A grid study object is required")
    grids = payload.get("grids")
    if not isinstance(grids, list) or len(grids) > 50:
        raise ValueError("grids must be a list of up to 50 runs")
    issues, identities = [], set()
    if len(grids) < 4:
        issues.append("At least four comparable grid solutions are recommended by Eca & Hoekstra for noisy practical CFD")
    if not grids:
        return _result("INSUFFICIENT_EVIDENCE", ["No grid studies supplied"])
    base = grids[0]
    if not isinstance(base, dict):
        raise ValueError("Each grid record must be an object")
    for i, g in enumerate(grids):
        if not isinstance(g, dict):
            raise ValueError("Each grid record must be an object")
        identifier = g.get("run_id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in identities:
            issues.append(f"grid[{i}]: missing or duplicate run_id")
        identities.add(identifier)
        for key in FIELDS:
            if not g.get(key):
                issues.append(f"grid[{i}]: missing {key}")
            elif base.get(key) and g[key] != base[key]:
                issues.append(f"grid[{i}]: different {key}")
        for key in ("h", "observable_value"):
            value = g.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                issues.append(f"grid[{i}]: invalid {key}")
            elif key == "h" and value <= 0:
                issues.append(f"grid[{i}]: positive characteristic mesh size h required")
        if g.get("mesh_geometric_similarity") is not True:
            issues.append(f"grid[{i}]: geometric similarity not demonstrated")
        if g.get("mesh_quality_review") != "PASS":
            issues.append(f"grid[{i}]: mesh quality not reviewed")
        if g.get("iterative_error_negligible") is not True:
            issues.append(f"grid[{i}]: iterative error not shown negligible versus discretization error")
        if g.get("numerical_convergence") != "PASS":
            issues.append(f"grid[{i}]: numerical convergence missing")
        if not g.get("artifact_sha256") or not g.get("solution_id"):
            issues.append(f"grid[{i}]: native artifact/solution provenance incomplete")
    hs = [g.get("h") for g in grids]
    if all(isinstance(h, (int, float)) and not isinstance(h, bool) and math.isfinite(h) and h > 0 for h in hs):
        if len(set(hs)) != len(hs):
            issues.append("Mesh characteristic sizes h must be distinct")
    if not isinstance(payload.get("h_definition"), str) or not payload["h_definition"].strip():
        issues.append("Document a physical and comparable mesh size h definition")
    if not isinstance(payload.get("mesh_family_review_evidence"), str) or not payload["mesh_family_review_evidence"].strip():
        issues.append("A human/API evidence reference for comparable refinement is required")
    if issues:
        return _result("GRID_SENSITIVITY_ONLY" if len(grids) >= 2 else "INSUFFICIENT_EVIDENCE", issues)
    return _result("CANDIDATE_FOR_FIT_NOT_VALIDATED", [], extra={
        "next": "Implement and independently validate Appendix A/B weighted and unweighted fits; the Appendix A/B numerical implementation needs independent verification",
        "eligible_for_parameter_fitting": False,
    })


def _result(status, issues, extra=None):
    return {
        "schema": SCHEMA, "status": status, "issues": issues,
        "uncertainty_computed": False, "scientific_status": "NOT_RUN",
        "source": "Eca & Hoekstra 2014, JCP 262, 104-130, DOI 10.1016/j.jcp.2014.01.006",
        "author_safety_factor_note": "Printed p.108: p<2.1 followed by footnote 4; Appendix A p.125: p<2.1. No numeric discrepancy.",
        **(extra or {}),
    }
