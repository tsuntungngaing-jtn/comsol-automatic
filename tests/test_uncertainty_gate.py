"""CASE1/CASE2/CASE3/CASE7: uncertainty decision gate and inference."""
from __future__ import annotations

import unittest

from uncertainty.decision_gate import decide_action
from uncertainty.detector import detect_unknown_parameters, unknown_only
from uncertainty.inference import infer_parameter_belief
from uncertainty.propagation import propagate_endpoints
from uncertainty.sensitivity import plan_endpoint_runs
from uncertainty.user_report import render_disclosure_report


class TestUncertaintyGate(unittest.TestCase):
    def test_case1_low_sensitivity_auto_accept_with_disclosure(self):
        finding = unknown_only(
            detect_unknown_parameters(
                [
                    {
                        "parameter": "emissivity",
                        "symbol": "eps",
                        "value": None,
                        "unit": "1",
                        "provenance": "UNKNOWN",
                        "affects": ["solve"],
                    }
                ]
            )
        )[0]
        belief = infer_parameter_belief(
            finding,
            evidence_sources=[
                {
                    "provenance": "LITERATURE",
                    "plausible_range": {"low": 0.8, "high": 0.95},
                    "value": 0.9,
                    "context": {"material_family": "metal", "physics_type": "ht"},
                }
            ],
            task_context={"material_family": "metal", "physics_type": "ht"},
        )
        belief = decide_action(
            belief, sensitivity={"status": "propagated", "score": 0.05, "conclusion_stable": True}
        )
        self.assertEqual(belief.recommended_action, "AUTO_ACCEPT")
        self.assertEqual(belief.decision_impact, "LOW")
        report = render_disclosure_report(belief)
        self.assertIn("Unknown parameter detected", report["text"])
        self.assertIn("plausible", report["plausible_range_display"].lower() + report["text"].lower())

    def test_case2_high_sensitivity_unstable_asks_or_blocks(self):
        finding = {
            "parameter": "Young's modulus",
            "symbol": "E_ink",
            "unit": "GPa",
            "reasons": ["missing"],
            "provenance": "UNKNOWN",
        }
        belief = infer_parameter_belief(
            finding,
            evidence_sources=[
                {
                    "provenance": "LITERATURE",
                    "plausible_range": {"low": 0.5, "high": 4.0},
                    "value": 2.0,
                    "context": {"material_family": "conductive_ink"},
                }
            ],
            task_context={"material_family": "conductive_ink"},
        )
        plan = plan_endpoint_runs(belief)
        prop = propagate_endpoints(
            plan,
            [
                {"label": "lower_bound", "metric": 0.01, "design_rank": 2, "scientific_conclusion": "A_better"},
                {"label": "baseline", "metric": 0.05, "design_rank": 1, "scientific_conclusion": "B_better"},
                {"label": "upper_bound", "metric": 0.09, "design_rank": 1, "scientific_conclusion": "B_better"},
            ],
        )
        self.assertFalse(prop["conclusion_stable"])
        belief = decide_action(belief, sensitivity=prop["sensitivity"])
        self.assertIn(belief.recommended_action, ("ASK_USER", "BLOCK_FINAL_VALIDATION", "RUN_SENSITIVITY", "SEEK_MORE_EVIDENCE"))
        self.assertIn(belief.decision_impact, ("HIGH", "CRITICAL"))

    def test_case3_no_evidence_insufficient(self):
        finding = {
            "parameter": "E_ink",
            "symbol": "E_ink",
            "unit": "GPa",
            "reasons": ["missing"],
        }
        belief = infer_parameter_belief(finding, evidence_sources=[])
        self.assertEqual(belief.coverage, "insufficient")
        self.assertIsNone(belief.plausible_range)
        self.assertIsNone(belief.central_estimate)
        self.assertEqual(belief.reliability, "INSUFFICIENT")

    def test_case7_dissimilar_context_no_narrow_prior(self):
        finding = {"parameter": "E", "symbol": "E", "unit": "GPa", "reasons": ["missing"]}
        belief = infer_parameter_belief(
            finding,
            evidence_sources=[
                {
                    "provenance": "VALIDATED_PRIOR_TASK",
                    "value": 200.0,
                    "plausible_range": {"low": 190.0, "high": 210.0},
                    "context": {"material_family": "steel", "physics_type": "solid"},
                }
            ],
            task_context={"material_family": "conductive_ink", "physics_type": "solid"},
        )
        self.assertEqual(belief.coverage, "insufficient")
        self.assertIsNone(belief.plausible_range)


if __name__ == "__main__":
    unittest.main()
