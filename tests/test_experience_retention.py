"""ExperienceRecord + CASE5/CASE6 retention behavior."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rsi.controller import RSIController
from rsi.retention_gate import RetentionGate


class TestExperienceRetention(unittest.TestCase):
    def test_prediction_not_overwritten_by_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctrl = RSIController(tmp)
            inference = ctrl.infer_task_parameters(
                [{"parameter": "E", "symbol": "E", "value": None, "unit": "GPa", "provenance": "UNKNOWN"}],
                evidence_by_parameter={
                    "E": [
                        {
                            "provenance": "LITERATURE",
                            "plausible_range": {"low": 1.0, "high": 3.0},
                            "value": 2.0,
                            "context": {"material_family": "ink"},
                        }
                    ]
                },
                task_context={"material_family": "ink"},
            )
            exp = ctrl.start_experience(
                task_id="t1",
                task_family="modulus",
                context={"material_family": "ink"},
                inference=inference,
            )
            frozen = dict(exp["prediction"])
            ctrl.complete_experience(
                exp["experience_id"],
                actual_outcome={"parameter_value": 1.7, "solver": "PASS"},
                scientific_validation={"scientific_status": "CONDITIONAL"},
                lesson_learned="calibrate E",
            )
            updated = ctrl.experiences.get(exp["experience_id"])
            self.assertEqual(updated["prediction"], frozen)
            self.assertIsNotNone(updated["actual_outcome"])
            self.assertIsNotNone(updated["prediction_error"])

    def test_held_out_excluded_from_learning(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctrl = RSIController(tmp)
            inference = {"findings": [], "beliefs": [], "recommended_actions": []}
            ctrl.start_experience(
                task_id="hold",
                task_family="x",
                context={},
                inference=inference,
                dataset_split="held_out",
            )
            learning = ctrl.experiences.list(for_learning=True)
            self.assertEqual(learning, [])

    def test_case5_reject_when_false_pass_increases(self):
        gate = RetentionGate(false_pass_rate_threshold=0.05, regression_threshold=0.0)
        result = gate.evaluate(
            old_metrics={
                "performance": 0.5,
                "scientific_validity": 0.8,
                "false_pass_rate": 0.01,
                "regression": 0.0,
                "cost": 10,
            },
            new_metrics={
                "performance": 0.9,
                "scientific_validity": 0.8,
                "false_pass_rate": 0.2,
                "regression": 0.0,
                "cost": 5,
            },
        )
        self.assertEqual(result["decision"], "REJECT")

    def test_case6_retain_when_cost_down_and_sci_ok(self):
        gate = RetentionGate(false_pass_rate_threshold=0.05, regression_threshold=0.0)
        result = gate.evaluate(
            old_metrics={
                "performance": 0.5,
                "scientific_validity": 0.8,
                "false_pass_rate": 0.02,
                "regression": 0.0,
                "cost": 10,
            },
            new_metrics={
                "performance": 0.7,
                "scientific_validity": 0.85,
                "false_pass_rate": 0.02,
                "regression": 0.0,
                "cost": 6,
            },
        )
        self.assertEqual(result["decision"], "RETAIN")


if __name__ == "__main__":
    unittest.main()
