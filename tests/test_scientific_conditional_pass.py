"""Scientific validity under inferred inputs."""
from __future__ import annotations

import unittest

from server.scientific_validity import evaluate_scientific_validity


class TestScientificConditionalPass(unittest.TestCase):
    def test_solver_pass_not_scientific_pass_when_inferred_high(self):
        result = evaluate_scientific_validity(
            execution_status="PASS",
            numerical_status="PASS",
            parameter_beliefs=[
                {
                    "status": "inferred",
                    "decision_impact": "HIGH",
                    "provenance": ["INFERRED"],
                    "coverage": "moderate",
                }
            ],
            required_checks_status="PASS",
        )
        self.assertEqual(result["execution_status"], "PASS")
        self.assertEqual(result["numerical_status"], "PASS")
        self.assertNotEqual(result["scientific_status"], "PASS")
        self.assertIn(result["scientific_status"], ("CONDITIONAL", "INSUFFICIENT_EVIDENCE"))
        self.assertFalse(result["final_scientific_pass"])

    def test_insufficient_evidence_not_fail(self):
        result = evaluate_scientific_validity(
            execution_status="PASS",
            numerical_status="PASS",
            parameter_beliefs=[
                {
                    "status": "unresolved",
                    "coverage": "insufficient",
                    "reliability": "INSUFFICIENT",
                    "decision_impact": "CRITICAL",
                }
            ],
        )
        self.assertEqual(result["scientific_status"], "INSUFFICIENT_EVIDENCE")
        self.assertNotEqual(result["scientific_status"], "FAIL")

    def test_unstable_conclusion_blocks_pass(self):
        result = evaluate_scientific_validity(
            execution_status="PASS",
            numerical_status="PASS",
            parameter_beliefs=[
                {"status": "inferred", "decision_impact": "HIGH", "provenance": ["INFERRED"]}
            ],
            required_checks_status="PASS",
            conclusion_stable=False,
        )
        self.assertEqual(result["scientific_status"], "INSUFFICIENT_EVIDENCE")

    def test_known_params_can_pass(self):
        result = evaluate_scientific_validity(
            execution_status="PASS",
            numerical_status="PASS",
            parameter_beliefs=[
                {"status": "known", "decision_impact": "LOW", "provenance": ["USER_SUPPLIED"]}
            ],
            required_checks_status="PASS",
        )
        self.assertEqual(result["scientific_status"], "PASS")
        self.assertTrue(result["final_scientific_pass"])


if __name__ == "__main__":
    unittest.main()
