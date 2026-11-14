"""Offline, opt-in loop: admitted observations -> surrogate -> budgeted proposals.

Does not call a solver, submit a CFD queue job, optimize physics or interpret
an unverified surrogate prediction as a paper's original CFD result.
"""
from __future__ import annotations

import math

from .contracts import DesignError, validate_space
from .observations import admit_observations
from .selector import select_next_simulation
from .surrogate import fit_idw_baseline, predict_idw


def screen_and_rank(space, dataset, request):
    """Build surrogate-derived *heuristic* candidate scores for operator review.

    The caller MUST declare a per-metric LOSO admissibility limit; this is a
    screening policy, not an independent physics error tolerance.
    The current method cannot claim expected improvement, Bayesian acquisition,
    calibrated uncertainty, or generalization to new geometry families.
    """
    contract = validate_space(space)
    if not isinstance(request, dict) or set(request) != {
        "candidate_cases", "remaining_budget", "weights",
        "max_loso_nmae_by_objective",
    }:
        raise DesignError("Expected candidate_cases, remaining_budget, weights and per-objective LOSO limits")
    limits = request["max_loso_nmae_by_objective"]
    target_names = {o["name"] for o in space["objectives"]}
    if not isinstance(limits, dict) or set(limits) != target_names:
        raise DesignError("Every objective requires an explicit LOSO normalized MAE limit")
    for k, v in limits.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            raise DesignError(f"Invalid screening error limit: {k}")
    admitted = admit_observations(space, dataset)
    if admitted["status"] != "ADMITTED_DECLARED_EVIDENCE_NOT_AUTHENTICATED":
        return _blocked("NO_ADMITTED_CFD_DATA", admitted, None)
    fit = fit_idw_baseline(space, admitted)
    if fit["model"] is None:
        return _blocked("INSUFFICIENT_INDEPENDENT_DESIGNS", admitted, fit)
    problems = {
        name: {"measured_loso_nmae": err["loso_normalized_mae"],
               "declared_max_loso_nmae": limits[name]}
        for name, err in fit["model"]["grouped_loso_metrics"].items()
        if err["loso_normalized_mae"] > limits[name]
    }
    if problems:
        return {
            **_blocked("LOSO_ERROR_EXCEEDS_DECLARED_SCREENING_LIMIT", admitted, fit),
            "unreliable_objectives": problems,
        }
    cases = request["candidate_cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= 100:
        raise DesignError("Expected 1..100 planned CFD candidate cases")
    prepared = []
    warnings = []
    seen_ids = set()
    for case in cases:
        expected = {"id", "design", "solver", "estimated_minutes",
                    "estimated_peak_ram_gib", "failure_risk",
                    "estimate_source", "hypothesis", "falsification_condition"}
        if not isinstance(case, dict) or set(case) != expected:
            raise DesignError("Candidate case requires design, cost, risk, hypothesis and evidence")
        if case["id"] in seen_ids:
            raise DesignError("Candidate IDs must be unique")
        seen_ids.add(case["id"])
        prediction = predict_idw(space, fit, case["design"])
        if prediction["status"] != "SCREENING_PREDICTION_ONLY":
            warnings.append({"id": case["id"], "reason": prediction["status"],
                             "detail": prediction.get("issues", [])})
            continue
        if any(g["design_hash"] == prediction["design_hash"] for g in fit["model"]["groups"]):
            warnings.append({"id": case["id"], "reason": "ALREADY_OBSERVED_DESIGN"})
            continue
        estimates = []
        for objective in space["objectives"]:
            name = objective["name"]
            y = prediction["predicted_metrics"][name]["value"]
            observed = [g["metrics"][name] for g in fit["model"]["groups"]]
            lo, hi = min(observed), max(observed)
            # Merit in the observed range, not Bayesian improvement. IDW is a
            # convex average, so it cannot extrapolate beyond observed optima.
            if hi == lo:
                desirability = 0.0
            elif objective["direction"] == "maximize":
                desirability = (y-lo)/(hi-lo)
            else:
                desirability = (hi-y)/(hi-lo)
            estimates.append(min(1.0, max(0.0, desirability)))
        feature_dim = sum(len(v["choices"]) if v["type"] == "categorical" else 1
                          for v in space["variables"])
        information_proxy = min(1., prediction["nearest_observed_feature_distance"]
                                 / math.sqrt(feature_dim))
        score = {
            **case,
            # Explicit heuristics, never physical probabilities.
            "information_value": information_proxy,
            "improvement_value": sum(estimates)/len(estimates),
            "uncertainty": min(1., max(
                fit["model"]["grouped_loso_metrics"][o]["loso_normalized_mae"]
                for o in target_names)),
        }
        prepared.append(score)
    if not prepared:
        return {
            **_blocked("NO_CANDIDATES_INSIDE_OBSERVED_SUPPORT", admitted, fit),
            "excluded_candidates": warnings,
        }
    proposal = {
        "design_space_hash": contract["design_space_hash"],
        "remaining_budget": request["remaining_budget"],
        "weights": request["weights"],
        "candidates": prepared,
    }
    decision = select_next_simulation(space, proposal)
    return {
        "status": "SCREENED_FOR_HUMAN_REVIEW_NOT_SCHEDULED",
        "admission_status": admitted["status"],
        "fit_status": fit["status"],
        "training_designs": fit["unique_designs"],
        "held_out_count": admitted["held_out_count"],
        "model_hash": fit["model_hash"],
        "normalized_loso_errors": {
            name: fit["model"]["grouped_loso_metrics"][name]["loso_normalized_mae"]
            for name in sorted(target_names)
        },
        "selection": decision,
        "excluded_candidates": warnings,
        "information_score_definition": "nearest-training-design feature distance normalized by sqrt(feature count)",
        "improvement_score_definition": "relative desirability inside observed target range; NOT expected improvement",
        "uncertainty_score_definition": "maximum grouped LOSO normalized MAE; NOT calibrated uncertainty",
        "research_mode": "DISCOVERY",
        "scientific_status": "NOT_RUN",
        "solver_contacted": False,
        "solver_execution_authorized": False,
        "requires_operator_review_and_native_cfd_verification": True,
        "authentication": "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
    }


def _blocked(status, admitted, fit):
    return {
        "status": status, "admission_status": admitted["status"],
        "training_designs": fit.get("unique_designs", 0) if fit else 0,
        "selection": None, "scientific_status": "NOT_RUN",
        "solver_contacted": False, "solver_execution_authorized": False,
        "requires_operator_review_and_native_cfd_verification": True,
    }
