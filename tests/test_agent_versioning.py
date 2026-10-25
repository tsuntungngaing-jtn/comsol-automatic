"""AgentVersion A0→candidate→retain/reject."""
from __future__ import annotations

import tempfile
import unittest

from rsi.controller import RSIController


class TestAgentVersioning(unittest.TestCase):
    def test_retain_promotes_active_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctrl = RSIController(tmp)
            self.assertEqual(ctrl.versions.active_id(), "A0")
            # seed an experience so improver has something
            exp = ctrl.start_experience(
                task_id="t1",
                task_family="family",
                context={"material_family": "ink"},
                inference={
                    "findings": [],
                    "beliefs": [
                        {
                            "parameter": "E",
                            "status": "inferred",
                            "central_estimate": 2.0,
                        }
                    ],
                    "recommended_actions": ["AUTO_ACCEPT"],
                },
            )
            ctrl.complete_experience(
                exp["experience_id"],
                actual_outcome={"parameter_value": 1.7},
                lesson_learned="prefer sensitivity before ask_user",
            )
            out = ctrl.propose_and_gate(
                old_metrics={
                    "performance": 0.4,
                    "scientific_validity": 0.7,
                    "false_pass_rate": 0.01,
                    "regression": 0.0,
                    "cost": 10,
                },
                new_metrics={
                    "performance": 0.6,
                    "scientific_validity": 0.75,
                    "false_pass_rate": 0.01,
                    "regression": 0.0,
                    "cost": 8,
                },
            )
            self.assertEqual(out["gate"]["decision"], "RETAIN")
            self.assertNotEqual(ctrl.versions.active_id(), "A0")
            self.assertTrue(ctrl.versions.active_id().startswith("A"))

    def test_reject_keeps_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctrl = RSIController(tmp)
            out = ctrl.propose_and_gate(
                old_metrics={
                    "performance": 0.5,
                    "scientific_validity": 0.9,
                    "false_pass_rate": 0.0,
                    "regression": 0.0,
                    "cost": 5,
                },
                new_metrics={
                    "performance": 0.8,
                    "scientific_validity": 0.5,
                    "false_pass_rate": 0.1,
                    "regression": 0.2,
                    "cost": 4,
                },
            )
            self.assertEqual(out["gate"]["decision"], "REJECT")
            self.assertEqual(ctrl.versions.active_id(), "A0")


if __name__ == "__main__":
    unittest.main()
