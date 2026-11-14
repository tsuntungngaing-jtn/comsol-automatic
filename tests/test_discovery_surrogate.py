"""Synthetic offline Discovery Mode tests; NO COMSOL/Fluent model or measurement."""
import copy
import unittest

from research_design import validate_space
from research_design.observations import admit_observations
from research_design.surrogate import fit_idw_baseline, predict_idw
from research_design.discovery_loop import screen_and_rank
from research_design.contracts import DesignError
from tests.test_research_design import space as make_space, design


CONFIG = "1" * 64
CASE = "2" * 64
RESULT = "3" * 64


def dataset(space=None, widths=(.3, .4, .5, .6, .7), held_out_width=None):
    s = space or make_space()
    frozen = validate_space(s)["design_space_hash"]
    records = []
    for i, w in enumerate(widths):
        records.append({
            "id": f"synthetic_{i}", "design": design(s, width=w, height=.9),
            "split": "train", "solver": "COMSOL",
            "configuration_sha256": CONFIG, "fidelity_group": "SYNTHETIC_BASE",
            "native_case_sha256": CASE, "native_result_sha256": RESULT,
            "evidence_ref": f"SYNTHETIC_FIXTURE_NOT_NATIVE_CFD_{i}",
            "checks": {
                "native_convergence": "PASS", "conservation": "PASS",
                "physical_consistency": "PASS", "numerical_verification": "PASS",
            },
            "metrics": {
                "pressure_drop": {"value": 200*w, "unit": "Pa"},
                "heat_transfer": {"value": 10 + 10*w, "unit": "W"},
            },
            "cost_minutes": 12.0,
        })
    if held_out_width is not None:
        extra = copy.deepcopy(records[0])
        extra["id"] = "synthetic_held_out"
        extra["split"] = "held_out"
        extra["design"] = design(s, width=held_out_width, height=.9)
        extra["evidence_ref"] = "SYNTHETIC_HELDOUT_NOT_TRAINED"
        records.append(extra)
    return {
        "schema": "paper2simu-discovery-observations/0.3.0",
        "design_space_hash": frozen, "configuration_sha256": CONFIG,
        "fidelity_group": "SYNTHETIC_BASE", "records": records,
    }


def request(s, *, candidates=None, error_limit=.9):
    if candidates is None:
        candidates = [.45, .55, .65]
    cases = []
    for i, width in enumerate(candidates):
        cases.append({
            "id": f"candidate_{i}", "design": design(s, width=width, height=.9),
            "solver": "COMSOL", "estimated_minutes": 15,
            "estimated_peak_ram_gib": 5, "failure_risk": .1,
            "estimate_source": "SYNTHETIC_USER_ESTIMATE_NOT_CFD",
            "hypothesis": "Does interpolation prioritize an informative point?",
            "falsification_condition": "A future independent CFD value contradicts the prediction",
        })
    return {
        "candidate_cases": cases,
        "remaining_budget": {"jobs": 2, "minutes": 60, "ram_gib": 10},
        "weights": {"information": 1., "improvement": 1.,
                    "uncertainty_penalty": .1, "risk_penalty": .1,
                    "cost_penalty": .2},
        "max_loso_nmae_by_objective": {
            "pressure_drop": error_limit, "heat_transfer": error_limit,
        },
    }


class DiscoverySurrogateTests(unittest.TestCase):
    def test_baseline_fit_and_grouped_validation(self):
        s = make_space()
        admitted = admit_observations(s, dataset(s))
        self.assertEqual(len(admitted["train_rows"]), 5)
        self.assertIn("NOT_AUTHENTICATED", admitted["status"])
        fit = fit_idw_baseline(s, admitted)
        self.assertEqual(fit["unique_designs"], 5)
        self.assertEqual(fit["model"]["grouped_loso_metrics"]["pressure_drop"]["folds"], 5)
        self.assertFalse(fit["model"]["independent_held_out_evaluated"])
        self.assertFalse(fit["model"]["prediction_is_cfd"])

    def test_predict_bounded_interpolation_not_physics(self):
        s = make_space()
        fit = fit_idw_baseline(s, admit_observations(s, dataset(s)))
        result = predict_idw(s, fit, design(s, width=.55, height=.9))
        self.assertEqual(result["status"], "SCREENING_PREDICTION_ONLY")
        self.assertFalse(result["predicted_metrics"]["pressure_drop"]["uncertainty_calibrated"])
        self.assertTrue(result["requires_high_fidelity_confirmation"])
        self.assertFalse(result["solver_contacted"])

    def test_external_extrapolation_rejected(self):
        s = make_space()
        fit = fit_idw_baseline(s, admit_observations(s, dataset(s)))
        self.assertEqual(predict_idw(s, fit, design(s, width=1., height=.9))["status"],
                         "OUTSIDE_OBSERVED_SUPPORT")
        self.assertEqual(predict_idw(s, fit, design(s, width=.55, height=.9, layout="serpentine"))["status"],
                         "OUTSIDE_OBSERVED_SUPPORT")

    def test_minimum_unique_design_groups_not_duplicate_rows(self):
        s = make_space()
        data = dataset(s, widths=(.3, .4, .5))
        duplicate = copy.deepcopy(data["records"][0])
        duplicate["id"] = "replicate_not_new_design"
        data["records"].append(duplicate)
        fit = fit_idw_baseline(s, admit_observations(s, data))
        self.assertEqual(fit["status"], "INSUFFICIENT_INDEPENDENT_DESIGNS")
        self.assertEqual(fit["unique_designs"], 3)

    def test_frozen_heldout_not_used_or_leaked(self):
        s = make_space()
        data = dataset(s, held_out_width=.8)
        admitted = admit_observations(s, data)
        self.assertEqual(admitted["held_out_count"], 1)
        self.assertEqual(len(admitted["train_rows"]), 5)
        data["records"][-1]["design"] = copy.deepcopy(data["records"][0]["design"])
        with self.assertRaises(DesignError):
            admit_observations(s, data)

    def test_failed_run_and_different_fidelity_excluded(self):
        s = make_space()
        data = dataset(s)
        data["records"][0]["checks"]["conservation"] = "FAIL"
        data["records"][1]["fidelity_group"] = "LOW_FIDELITY_NOT_COMPARABLE"
        admitted = admit_observations(s, data)
        self.assertEqual(len(admitted["train_rows"]), 3)
        self.assertEqual(len(admitted["excluded"]), 2)
        self.assertEqual(fit_idw_baseline(s, admitted)["status"], "INSUFFICIENT_INDEPENDENT_DESIGNS")

    def test_mixed_solver_training_not_pooled(self):
        s = make_space()
        data = dataset(s)
        data["records"][1]["solver"] = "Fluent"
        with self.assertRaises(DesignError):
            fit_idw_baseline(s, admit_observations(s, data))

    def test_wrong_units_and_stale_design_hash(self):
        s = make_space()
        data = dataset(s)
        data["records"][0]["metrics"]["pressure_drop"]["unit"] = "W"
        with self.assertRaises(DesignError):
            admit_observations(s, data)
        data = dataset(s)
        data["design_space_hash"] = "deadbeef"
        self.assertEqual(admit_observations(s, data)["status"], "STALE_DESIGN_SPACE")

    def test_complete_selection_never_authorizes_solver(self):
        s = make_space()
        result = screen_and_rank(s, dataset(s), request(s))
        self.assertEqual(result["status"], "SCREENED_FOR_HUMAN_REVIEW_NOT_SCHEDULED")
        self.assertIn(result["selection"]["selected"], ["candidate_0", "candidate_1", "candidate_2"])
        self.assertEqual(result["research_mode"], "DISCOVERY")
        self.assertFalse(result["solver_contacted"])
        self.assertFalse(result["solver_execution_authorized"])
        self.assertEqual(result["scientific_status"], "NOT_RUN")

    def test_cv_error_limit_blocks_heuristic_ranking(self):
        s = make_space()
        result = screen_and_rank(s, dataset(s), request(s, error_limit=0.0))
        self.assertEqual(result["status"], "LOSO_ERROR_EXCEEDS_DECLARED_SCREENING_LIMIT")
        self.assertIsNone(result["selection"])

    def test_excluded_candidate_does_not_silently_extrapolate(self):
        s = make_space()
        result = screen_and_rank(s, dataset(s), request(s, candidates=[.55, 1.0]))
        self.assertEqual(result["status"], "SCREENED_FOR_HUMAN_REVIEW_NOT_SCHEDULED")
        self.assertEqual(len(result["excluded_candidates"]), 1)
        self.assertEqual(result["excluded_candidates"][0]["reason"], "OUTSIDE_OBSERVED_SUPPORT")

    def test_source_paper_not_design_space(self):
        s = make_space()
        s["mode"] = "REPRODUCTION"
        with self.assertRaises(DesignError):
            screen_and_rank(s, dataset(make_space()), request(make_space()))


if __name__ == "__main__":
    unittest.main()
