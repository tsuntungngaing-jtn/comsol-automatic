"""ParameterBelief schema/rules tests."""
from __future__ import annotations

import unittest

from uncertainty.parameter_belief import ParameterBelief


class TestParameterBelief(unittest.TestCase):
    def test_insufficient_forbids_fabricated_range(self):
        with self.assertRaises(ValueError):
            ParameterBelief(
                parameter="E",
                symbol="E",
                unit="GPa",
                status="unresolved",
                coverage="insufficient",
                central_estimate=2.0,
                plausible_range={"low": 1.0, "high": 3.0},
                range_kind="estimated_plausible_range",
                recommended_action="ASK_USER",
                provenance=["UNKNOWN"],
            )

    def test_plausible_range_not_confidence_interval_by_default(self):
        b = ParameterBelief(
            parameter="E",
            symbol="E",
            unit="GPa",
            status="inferred",
            central_estimate=2.0,
            plausible_range={"low": 1.0, "high": 3.0},
            range_kind="estimated_plausible_range",
            coverage="moderate",
            evidence_grade="B",
            reliability="UNRELIABLE",
            recommended_action="AUTO_ACCEPT",
            provenance=["INFERRED"],
        )
        self.assertEqual(b.range_kind, "estimated_plausible_range")
        self.assertNotEqual(b.range_kind, "confidence_interval")

    def test_confidence_interval_requires_definition(self):
        with self.assertRaises(ValueError):
            ParameterBelief(
                parameter="E",
                symbol="E",
                status="inferred",
                range_kind="confidence_interval",
                coverage="moderate",
                plausible_range={"low": 1, "high": 2},
                central_estimate=1.5,
                recommended_action="AUTO_ACCEPT",
                provenance=["INFERRED"],
            )

    def test_blocks_final_pass_when_high_inferred(self):
        b = ParameterBelief(
            parameter="E",
            symbol="E",
            status="inferred",
            coverage="moderate",
            central_estimate=2.0,
            plausible_range={"low": 1.0, "high": 3.0},
            range_kind="estimated_plausible_range",
            decision_impact="HIGH",
            recommended_action="RUN_SENSITIVITY",
            provenance=["INFERRED"],
            reliability="UNRELIABLE",
        )
        self.assertTrue(b.blocks_final_scientific_pass())


if __name__ == "__main__":
    unittest.main()
