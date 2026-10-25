"""CASE4: user supplies true parameter → calibration vs frozen prediction."""
from __future__ import annotations

import unittest

from uncertainty.calibration import PriorStore, compare_prediction_to_observation
from uncertainty.evidence_ranker import context_similarity


class TestCalibration(unittest.TestCase):
    def test_case4_compare_prediction_to_observed(self):
        prediction = {
            "parameter": "E_ink",
            "central_estimate": 2.25,
            "plausible_range": {"low": 0.5, "high": 4.0},
            "agent_version": "A0",
        }
        cal = compare_prediction_to_observation(
            prediction, {"value": 1.7, "provenance": "USER_SUPPLIED"}
        )
        self.assertTrue(cal["coverage_success"])
        self.assertAlmostEqual(cal["prediction_error"], 1.7 - 2.25)
        # prediction object in record is a copy — mutating observed must not alter stored prediction fields identity-wise
        self.assertEqual(cal["prediction"]["plausible_range"]["low"], 0.5)

    def test_single_sample_does_not_replace_family_wholesale(self):
        store = PriorStore()
        e1 = store.update(
            parameter="E",
            context={"material_family": "ink"},
            observed_value=1.7,
        )
        self.assertEqual(e1["sample_count"], 1)
        e2 = store.update(
            parameter="E",
            context={"material_family": "ink"},
            observed_value=1.9,
        )
        self.assertEqual(e2["sample_count"], 2)
        self.assertEqual(len(e2["values"]), 2)
        # Still a range, not a single overwritten point pretending to be the family
        self.assertIn("low", e2["plausible_range"])
        self.assertIn("high", e2["plausible_range"])

    def test_dissimilar_material_similarity_low(self):
        sim = context_similarity(
            {"material_family": "steel", "physics_type": "solid"},
            {"material_family": "conductive_ink", "physics_type": "solid"},
        )
        self.assertLess(sim, 0.3)


if __name__ == "__main__":
    unittest.main()
