"""Offline, budget-aware next-simulation selector for Paper2Simu research.

This is a *transparent, user-weighted heuristic*, NOT a learned acquisition
function, a Bayesian EIG estimator, an optimizer, or an execution engine.
All estimated benefits/uncertainty/cost come from the caller. Never infer
their validity, submit jobs, mutate solvers or claim scientific PASS.
"""
from __future__ import annotations

import math

from .contracts import assess_design, fingerprint, validate_space, DesignError

SCHEMA = "paper2simu-simulation-selection/0.1.0"
MAX_CANDIDATES = 100


def number(value, field, *, lower=None, upper=None):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise DesignError(f"{field}: numeric required")
    try:
        x = float(value)
    except (OverflowError, ValueError) as exc:
        raise DesignError(f"{field}: finite number required") from exc
    if not math.isfinite(x) or (lower is not None and x < lower) or (upper is not None and x > upper):
        raise DesignError(f"{field}: must be finite in declared bounds")
    return x


def _weights(weights):
    if not isinstance(weights, dict) or set(weights) != {"information", "improvement", "uncertainty_penalty", "risk_penalty", "cost_penalty"}:
        raise DesignError("Explicit information, improvement, uncertainty, risk and cost weights required")
    values = {k: number(v, f"weights.{k}", lower=0, upper=100) for k, v in weights.items()}
    if sum(values.values()) == 0:
        raise DesignError("At least one nonzero weighting required")
    return values


def select_next_simulation(space, proposal):
    """Inspect and rank hypothetical candidates, without scheduling any job.

    Required scores are *caller-supplied* normalized [0,1] estimates,
    NOT physical predictions or calibrated probabilities. Do not use
    this output as a publication result or model-fit target.
    """
    contract = validate_space(space)
    if not isinstance(proposal, dict) or set(proposal) != {"design_space_hash", "remaining_budget", "weights", "candidates"}:
        raise DesignError("Selection proposal requires exact keys: design_space_hash, remaining_budget, weights, candidates")
    if proposal["design_space_hash"] != contract["design_space_hash"]:
        return {"schema": SCHEMA, "status": "STALE_SPACE_BLOCKED", "proposals": [],
                "selected": None, "execution_performed": False, "scientific_status": "NOT_RUN"}
    remaining = proposal["remaining_budget"]
    if not isinstance(remaining, dict) or set(remaining) != {"jobs", "minutes", "ram_gib"}:
        raise DesignError("Remaining budget requires jobs/minutes/ram_gib")
    jobs = remaining["jobs"]
    if type(jobs) is not int or jobs < 0 or jobs > space["budget"]["max_jobs"]:
        raise DesignError("Remaining job budget invalid")
    minutes = number(remaining["minutes"], "remaining.minutes", lower=0)
    ram = number(remaining["ram_gib"], "remaining.ram_gib", lower=0)
    if minutes > space["budget"]["max_total_minutes"] or ram > space["budget"]["max_ram_gib"]:
        raise DesignError("Remaining resource budget exceeds frozen study contract")
    weights = _weights(proposal["weights"])
    candidates = proposal["candidates"]
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= MAX_CANDIDATES:
        raise DesignError("Must provide 1..100 candidate proposals")
    ids = set()
    results = []
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != {
            "id", "design", "solver", "estimated_minutes", "estimated_peak_ram_gib",
            "information_value", "improvement_value", "uncertainty", "failure_risk",
            "estimate_source", "hypothesis", "falsification_condition",
        }:
            raise DesignError("Candidate must specify identity, design, solver, cost, scores, provenance, hypothesis and falsification")
        name = candidate["id"]
        if not isinstance(name, str) or not name or len(name) > 64 or name in ids:
            raise DesignError("Candidate IDs must be unique bounded strings")
        ids.add(name)
        for field in ("estimate_source", "hypothesis", "falsification_condition"):
            value = candidate[field]
            if not isinstance(value, str) or not value.strip() or len(value) > 512:
                raise DesignError(f"{name}: {field} requires bounded provenance/description")
        effective = assess_design(space, candidate["design"])
        if candidate["solver"] not in ("COMSOL", "Fluent"):
            raise DesignError("Only COMSOL and Fluent may be proposed")
        cost = number(candidate["estimated_minutes"], f"{name}.estimated_minutes", lower=0)
        peak = number(candidate["estimated_peak_ram_gib"], f"{name}.estimated_peak_ram_gib", lower=0)
        if not cost or not peak:
            raise DesignError("Estimated duration and RAM must be positive")
        benefit = number(candidate["information_value"], f"{name}.information_value", lower=0, upper=1)
        improvement = number(candidate["improvement_value"], f"{name}.improvement_value", lower=0, upper=1)
        uncertainty = number(candidate["uncertainty"], f"{name}.uncertainty", lower=0, upper=1)
        risk = number(candidate["failure_risk"], f"{name}.failure_risk", lower=0, upper=1)
        blockers = []
        if effective["status"] != "FEASIBLE_ON_DECLARED_CONSTRAINTS":
            blockers.extend(effective["issues"])
        if candidate["solver"] not in space["allowed_solvers"]:
            blockers.append("Not authorized in declared solver set")
        if jobs < 1 or cost > minutes or peak > ram:
            blockers.append("Estimated cost exceeds remaining budget")
        if cost > space["budget"]["max_total_minutes"] or peak > space["budget"]["max_ram_gib"]:
            blockers.append("Estimated cost exceeds frozen study budget")
        # Unitless heuristic: informative/improving proposals get credit;
        # uncertainty, risk and time fraction incur explicit penalties.
        # Weights are declared, never fitted to ground-truth output.
        penalty_fraction = cost / space["budget"]["max_total_minutes"]
        raw_score = (weights["information"] * benefit
                     + weights["improvement"] * improvement
                     - weights["uncertainty_penalty"] * uncertainty
                     - weights["risk_penalty"] * risk
                     - weights["cost_penalty"] * penalty_fraction)
        results.append({
            "id": name, "candidate_hash": effective.get("candidate_hash"),
            "status": "ELIGIBLE_FOR_OPERATOR_REVIEW" if not blockers else "BLOCKED",
            "blocking_reasons": blockers,
            "heuristic_score": round(raw_score, 9) if not blockers else None,
            "estimated_minutes": cost, "estimated_peak_ram_gib": peak,
            "estimate_source": candidate["estimate_source"],
            "hypothesis": candidate["hypothesis"],
            "falsification_condition": candidate["falsification_condition"],
            "score_is_ground_truth": False,
        })
    ranked = sorted((r for r in results if r["status"] == "ELIGIBLE_FOR_OPERATOR_REVIEW"),
                    key=lambda r: (-r["heuristic_score"], r["estimated_minutes"], r["id"]))
    return {
        "schema": SCHEMA,
        "status": "PROPOSED_NOT_SCHEDULED" if ranked else "NO_ADMISSIBLE_CANDIDATES",
        "selected": ranked[0]["id"] if ranked else None,
        "ranked_ids": [r["id"] for r in ranked],
        "proposals": results,
        "design_space_hash": contract["design_space_hash"],
        "selection_hash": fingerprint({"space": contract["design_space_hash"], "proposal": proposal}),
        "method": "DECLARED_WEIGHTED_HEURISTIC_NOT_EIG",
        "scientific_status": "NOT_RUN", "execution_performed": False,
        "solver_contacted": False, "authorization_granted": False,
        "warnings": ["Caller-supplied scores are not calibrated probabilities or surrogate predictions.",
                     "No resource, paper evidence, solver availability or numerical success was independently verified.",
                     "No solver run may be launched on this result without separate authorization and live preflight."],
    }
