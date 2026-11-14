"""Transparent, deterministic IDW surrogate baseline for bounded CFD screening.

NOT a trained neural network, calibrated uncertainty estimate, physical solver,
cross-fidelity model, expected information gain or scientific validation.
Grouped leave-one-DESIGN-out CV prevents replicates of a design from leaking.
"""
from __future__ import annotations

import math

from .contracts import DesignError, assess_design, fingerprint, validate_space


SCHEMA = "paper2simu-surrogate-baseline/0.3.0"
MIN_DESIGNS = 4
MAX_DESIGNS = 500


def _features(space, values):
    result = []
    for v in space["variables"]:
        name = v["name"]
        if v["type"] == "categorical":
            # One-hot representation prevents invented ordering of categories.
            result.extend(float(values[name] == x) for x in v["choices"])
        else:
            lo, hi = v["bounds"]
            result.append((float(values[name]) - lo) / (hi - lo))
    return result


def _distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def _idw(points, query, *, k=3):
    scored = sorted(
        ((_distance(x, query), group_hash, metric) for x, group_hash, metric in points),
        key=lambda row: (row[0], row[1])
    )
    if not scored:
        raise DesignError("No independent training design remains")
    if scored[0][0] < 1e-12:
        return scored[0][2]
    nearest = scored[:k]
    weights = [1.0 / max(d, 1e-12)**2 for d, _, _ in nearest]
    return sum(w * row[2] for w, row in zip(weights, nearest)) / sum(weights)


def _group_rows(space, rows):
    by_hash = {}
    for r in rows:
        key = r["design_hash"]
        if key not in by_hash:
            by_hash[key] = {"values": r["design"], "features": _features(space, r["design"]),
                            "metrics": {name: [] for name in [o["name"] for o in space["objectives"]]}}
        elif r["design"] != by_hash[key]["values"]:
            raise DesignError("Same design hash has conflicting values")
        for name, value in r["metrics"].items():
            if not math.isfinite(value):
                raise DesignError("Nonfinite observed metric")
            by_hash[key]["metrics"][name].append(value)
    result = []
    for key in sorted(by_hash):
        x = by_hash[key]
        result.append({"design_hash": key, "values": x["values"], "features": x["features"],
                       "metrics": {name: sum(vals)/len(vals) for name, vals in x["metrics"].items()},
                       "replicates": len(next(iter(x["metrics"].values())))})
    return result


def fit_idw_baseline(space, admitted):
    """Only caller-declared admission; use per-metric LOSO errors for screening.

    No held-out dataset is consumed and no claimed physical uncertainty interval
    is produced. Models are not auto-authorized for expensive CFD decisions.
    """
    contract = validate_space(space)
    if not isinstance(admitted, dict) or admitted.get("design_space_hash") != contract["design_space_hash"]:
        raise DesignError("Admitted dataset must match frozen design space")
    if admitted.get("status") != "ADMITTED_DECLARED_EVIDENCE_NOT_AUTHENTICATED":
        raise DesignError("No admitted training evidence")
    if admitted.get("authentication") != "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED":
        raise DesignError("Unsupported provenance regime")
    rows = admitted["train_rows"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_DESIGNS:
        raise DesignError("Invalid observed-row count")
    solvers = {r["solver"] for r in rows}
    if len(solvers) != 1:
        raise DesignError("Mixed solver results cannot be pooled without a validated comparability study")
    groups = _group_rows(space, rows)
    if len(groups) < MIN_DESIGNS:
        return {
            "schema": SCHEMA, "status": "INSUFFICIENT_INDEPENDENT_DESIGNS",
            "unique_designs": len(groups), "minimum_designs": MIN_DESIGNS,
            "scientific_status": "NOT_RUN", "solver_contacted": False,
            "model": None,
        }
    objectives = [o["name"] for o in space["objectives"]]
    errors = {}
    for name in objectives:
        observed = [r["metrics"][name] for r in groups]
        scale = max(max(abs(y) for y in observed), 1e-12)
        absolute = []
        normalized = []
        for group in groups:
            other = [(p["features"], p["design_hash"], p["metrics"][name])
                     for p in groups if p["design_hash"] != group["design_hash"]]
            guess = _idw(other, group["features"])
            err = abs(guess - group["metrics"][name])
            absolute.append(err)
            normalized.append(err / scale)
        errors[name] = {
            "loso_mean_absolute_error": sum(absolute) / len(absolute),
            "loso_normalized_mae": sum(normalized) / len(normalized),
            "loso_max_absolute_error": max(absolute),
            "normalization": "max_absolute_observed_target_not_local_relative_error",
            "observed_scale": scale,
            "folds": len(groups),
        }
    feature_domain = {}
    for var in space["variables"]:
        name = var["name"]
        present = [g["values"][name] for g in groups]
        feature_domain[name] = (
            {"seen": sorted(set(present))}
            if var["type"] == "categorical"
            else {"minimum": min(present), "maximum": max(present)}
        )
    model = {
        "schema": SCHEMA, "method": "IDW_K3_INVERSE_DISTANCE_SQUARED",
        "status": "SCREENING_BASELINE_NO_CALIBRATED_CONFIDENCE",
        "dataset_hash": admitted["dataset_hash"],
        "design_space_hash": contract["design_space_hash"],
        "configuration_sha256": admitted["configuration_sha256"],
        "fidelity_group": admitted["fidelity_group"],
        "solver": next(iter(solvers)),
        "unique_designs": len(groups),
        "grouped_loso_metrics": errors,
        "observed_domain": feature_domain,
        "groups": groups,
        "authentication": "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "independent_held_out_evaluated": False,
        "prediction_is_cfd": False,
        "scientific_status": "NOT_RUN",
        "solver_contacted": False,
    }
    return {"schema": SCHEMA, "status": model["status"], "unique_designs": len(groups),
            "model": model, "model_hash": fingerprint(model),
            "scientific_status": "NOT_RUN", "solver_contacted": False}


def predict_idw(space, fit, proposed):
    """Return screening-only predictions inside observed coordinate ranges.

    Reject out-of-support predictions; proposed points can still be sent for
    separately authorized *real* CFD exploration (not a surrogate result).
    """
    contract = validate_space(space)
    if not isinstance(fit, dict) or fit.get("status") != "SCREENING_BASELINE_NO_CALIBRATED_CONFIDENCE":
        raise DesignError("Surrogate baseline is not fit")
    model = fit.get("model")
    if not isinstance(model, dict) or fit.get("model_hash") != fingerprint(model):
        raise DesignError("Surrogate model altered after fitting")
    if model["design_space_hash"] != contract["design_space_hash"]:
        raise DesignError("Surrogate belongs to a different design-space revision")
    screening = assess_design(space, proposed)
    if not screening["eligible"]:
        return {"status": "INVALID_DESIGN", "issues": screening["issues"],
                "predicted_metrics": None, "scientific_status": "NOT_RUN"}
    values = proposed["values"]
    violations = []
    for name, domain in model["observed_domain"].items():
        value = values[name]
        if "seen" in domain and value not in domain["seen"]:
            violations.append(f"{name}: categorical choice unseen in training")
        if "minimum" in domain and not domain["minimum"] <= value <= domain["maximum"]:
            violations.append(f"{name}: outside observed numerical extent")
    if violations:
        return {"status": "OUTSIDE_OBSERVED_SUPPORT", "issues": violations,
                "predicted_metrics": None, "scientific_status": "NOT_RUN",
                "may_propose_separate_cfd_run": True}
    vector = _features(space, values)
    predictions = {}
    for objective in space["objectives"]:
        name = objective["name"]
        points = [(r["features"], r["design_hash"], r["metrics"][name])
                  for r in model["groups"]]
        predictions[name] = {
            "value": _idw(points, vector),
            "unit": objective["unit"],
            "loso_normalized_mae": model["grouped_loso_metrics"][name]["loso_normalized_mae"],
            "uncertainty_calibrated": False,
            "claim_type": "SURROGATE_SCREENING_PREDICTION",
        }
    nearest = min(_distance(r["features"], vector) for r in model["groups"])
    return {
        "status": "SCREENING_PREDICTION_ONLY",
        "predicted_metrics": predictions,
        "nearest_observed_feature_distance": nearest,
        "distance_is_uncertainty": False,
        "model_hash": fit["model_hash"],
        "design_hash": screening["candidate_hash"],
        "scientific_status": "NOT_RUN",
        "solver_contacted": False,
        "requires_high_fidelity_confirmation": True,
    }
