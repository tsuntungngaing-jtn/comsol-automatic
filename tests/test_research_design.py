"""Offline experimental design regression. No solver or remote calls."""
import copy
import unittest

from research_design import DesignError, validate_space, assess_design, select_next_simulation

def space():
    return {
        "schema": "paper2simu-design-space/0.1.0",
        "study_id": "microchannel_demo",
        "research_question": "Which geometries justify expensive CFD validation?",
        "source_refs": ["user-defined exploratory study; not a source-paper replication"],
        "mode": "DISCOVERY",
        "variables": [
            {"name": "width", "type": "continuous", "unit": "mm", "bounds": [0.2, 1.2],
             "origin": "USER_DEFINED_DESIGN", "source_ref": "design brief"},
            {"name": "height", "type": "continuous", "unit": "mm", "bounds": [0.3, 1.5],
             "origin": "USER_DEFINED_DESIGN", "source_ref": "design brief"},
            {"name": "channels", "type": "integer", "unit": "1", "bounds": [2, 10],
             "origin": "USER_DEFINED_DESIGN", "source_ref": "design brief"},
            {"name": "layout", "type": "categorical", "unit": "category",
             "choices": ["parallel", "serpentine"], "origin": "USER_DEFINED_DESIGN",
             "source_ref": "design brief"},
        ],
        "fixed_inputs": [
            {"name": "fluid", "value": "water", "unit": "name",
             "source_ref": "design brief", "origin": "USER_DEFINED_DESIGN"},
        ],
        "constraints": [
            {"type": "less_equal", "left": "width", "right": "height",
             "source_ref": "declared geometry constraint"},
        ],
        "objectives": [
            {"name": "pressure_drop", "direction": "minimize", "unit": "Pa",
             "source_ref": "research proposal"},
            {"name": "heat_transfer", "direction": "maximize", "unit": "W",
             "source_ref": "research proposal"},
        ],
        "allowed_solvers": ["COMSOL", "Fluent"],
        "budget": {"max_jobs": 6, "max_total_minutes": 300, "max_ram_gib": 24},
    }

def design(s, width=0.5, height=0.7, channels=4, layout="parallel"):
    return {"design_space_hash": validate_space(s)["design_space_hash"],
            "values": {"width": width, "height": height, "channels": channels,
                       "layout": layout}}

def option(s, id, benefit, cost=30, solver="COMSOL"):
    return {
        "id": id, "design": design(s), "solver": solver,
        "estimated_minutes": cost, "estimated_peak_ram_gib": 8,
        "information_value": benefit, "improvement_value": .3,
        "uncertainty": .2, "failure_risk": .1,
        "estimate_source": "hypothetical and uncalibrated pilot estimates",
        "hypothesis": "Compare pressure drop sensitivity to layout",
        "falsification_condition": "Validated metrics do not change",
    }

def proposal(s, options):
    return {
        "design_space_hash": validate_space(s)["design_space_hash"],
        "remaining_budget": {"jobs": 4, "minutes": 120, "ram_gib": 16},
        "weights": {"information": 1, "improvement": .5,
                    "uncertainty_penalty": .3, "risk_penalty": .2,
                    "cost_penalty": .3},
        "candidates": options,
    }

class DesignResearchTests(unittest.TestCase):
    def test_contract_is_discovery_not_reproduction(self):
        x = space()
        self.assertEqual(validate_space(x)["status"], "CONTRACT_REVIEWED_NOT_AUTHENTICATED")
        x["mode"] = "REPRODUCTION"
        with self.assertRaises(DesignError):
            validate_space(x)

    def test_reported_paper_dimensions_cannot_be_mutated_as_facts(self):
        x = space()
        x["variables"][0]["origin"] = "PAPER_REPORTED"
        with self.assertRaises(DesignError):
            validate_space(x)

    def test_mixed_design_and_bounds(self):
        x = space()
        self.assertTrue(assess_design(x, design(x))["eligible"])
        self.assertFalse(assess_design(x, design(x, width=1, height=.5))["eligible"])
        self.assertFalse(assess_design(x, design(x, layout="imaginary"))["eligible"])
        self.assertFalse(assess_design(x, design(x, channels=3.5))["eligible"])

    def test_constraint_does_not_silently_drop_unit_mismatch(self):
        x = space()
        x["variables"][0]["unit"] = "inch"
        with self.assertRaises(DesignError):
            validate_space(x)

    def test_valid_candidates_rank_by_declared_heuristic(self):
        x = space()
        result = select_next_simulation(x, proposal(x, [option(x, "low", .1), option(x, "high", .9)]))
        self.assertEqual(result["selected"], "high")
        self.assertFalse(result["execution_performed"])
        self.assertFalse(result["solver_contacted"])
        self.assertEqual(result["scientific_status"], "NOT_RUN")
        self.assertEqual(result["method"], "DECLARED_WEIGHTED_HEURISTIC_NOT_EIG")

    def test_over_budget_cannot_be_selected(self):
        x = space()
        result = select_next_simulation(x, proposal(x, [option(x, "expensive", .9, cost=200)]))
        self.assertEqual(result["status"], "NO_ADMISSIBLE_CANDIDATES")
        self.assertIsNone(result["selected"])

    def test_stale_contract_not_scheduled(self):
        x = space()
        p = proposal(x, [option(x, "trial", .7)])
        x["budget"]["max_jobs"] = 7
        self.assertEqual(select_next_simulation(x, p)["status"], "STALE_SPACE_BLOCKED")

    def test_disallowed_solver_blocked(self):
        x = space()
        x["allowed_solvers"] = ["COMSOL"]
        r = select_next_simulation(x, proposal(x, [option(x, "fluent", .9, solver="Fluent")]))
        self.assertEqual(r["status"], "NO_ADMISSIBLE_CANDIDATES")

    def test_duplicated_candidate_not_accepted(self):
        x = space()
        trial = option(x, "same", .5)
        with self.assertRaises(DesignError):
            select_next_simulation(x, proposal(x, [trial, copy.deepcopy(trial)]))

    def test_no_fabricated_probability_or_unsupported_score(self):
        x = space()
        trial = option(x, "invalid", 2.5)
        with self.assertRaises(DesignError):
            select_next_simulation(x, proposal(x, [trial]))

if __name__ == "__main__":
    unittest.main()
