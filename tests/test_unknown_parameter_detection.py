"""CASE coverage for unknown parameter detection."""
from __future__ import annotations

import unittest

from uncertainty.detector import classify_provenance, detect_unknown_parameters, unknown_only


class TestUnknownParameterDetection(unittest.TestCase):
    def test_missing_value_is_unknown(self):
        findings = detect_unknown_parameters(
            [
                {
                    "parameter": "Young's modulus",
                    "symbol": "E_ink",
                    "value": None,
                    "unit": "GPa",
                    "provenance": "UNKNOWN",
                    "affects": ["solve"],
                }
            ],
            physics_interfaces=["solid_mechanics"],
        )
        unk = unknown_only(findings)
        self.assertEqual(len(unk), 1)
        self.assertTrue(unk[0]["is_unknown"])

    def test_nominal_without_provenance_is_unknown(self):
        findings = detect_unknown_parameters(
            [{"parameter": "E", "symbol": "E", "value": 2.0, "unit": "GPa"}],
            physics_interfaces=["solid_mechanics"],
        )
        self.assertTrue(unknown_only(findings)[0]["is_unknown"])
        self.assertIn("without evidence provenance", " ".join(findings[0]["reasons"]))

    def test_user_supplied_not_unknown(self):
        findings = detect_unknown_parameters(
            [
                {
                    "parameter": "E",
                    "symbol": "E",
                    "value": 1.7,
                    "unit": "GPa",
                    "origin": "user_supplied",
                    "affects": ["solve"],
                }
            ]
        )
        self.assertEqual(unknown_only(findings), [])

    def test_irrelevant_physics_not_escalated(self):
        findings = detect_unknown_parameters(
            [
                {
                    "parameter": "plot_color",
                    "value": None,
                    "provenance": "UNKNOWN",
                    "scientifically_relevant": False,
                    "affects": ["plot"],
                }
            ],
            physics_interfaces=["heat_transfer"],
        )
        self.assertFalse(findings[0]["is_unknown"])

    def test_classify_inferred_origin(self):
        self.assertEqual(classify_provenance({"origin": "inferred"}), "INFERRED")


if __name__ == "__main__":
    unittest.main()
