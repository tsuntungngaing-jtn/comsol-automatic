"""Autonomy profiles, doc defaults, peer priors, digitization guards."""
from __future__ import annotations

import os
import unittest

from uncertainty.autonomy import apply_autonomy_policy, get_autonomy_profile, pack_decision_requests
from uncertainty.decision_gate import decide_action
from uncertainty.doc_default import doc_default_resolve
from uncertainty.figure_digitize import (
    assert_not_reported,
    digitize_axis_span,
    digitize_colorbar_fraction,
    overlap_with_kpi,
)
from uncertainty.inference import infer_parameter_belief
from uncertainty.parameter_belief import ParameterBelief
from uncertainty.peer_prior import as_inference_evidence, peer_range_prior
from uncertainty.sensitivity_budget import plan_sensitivity_with_budget
from rsi.harness_heuristics import merge_into_retention_metrics, score_harness_candidate
from rsi.retention_gate import RetentionGate


class TestAutonomy(unittest.TestCase):
    def test_default_profile_strict(self):
        os.environ.pop("COMSOL_RSI_AUTONOMY", None)
        self.assertEqual(get_autonomy_profile(), "strict")

    def test_assisted_low_doc_auto_accept(self):
        belief = ParameterBelief(
            parameter="inlet_bc",
            symbol="inlet_bc",
            status="inferred",
            central_estimate="Inflow",
            plausible_range={"low": 0.0, "high": 1.0},
            range_kind="estimated_plausible_range",
            coverage="moderate",
            epistemic_uncertainty=0.1,
            reliability="RELIABLE",
            recommended_action="ASK_USER",
            decision_impact="LOW",
            provenance=["INFERRED", "DEFAULT"],
        )
        out = apply_autonomy_policy(
            belief, profile="assisted", has_software_doc_default=True
        )
        self.assertEqual(out.recommended_action, "AUTO_ACCEPT")

    def test_hard_ban_overwrite(self):
        belief = ParameterBelief(
            parameter="x",
            symbol="x",
            status="known",
            central_estimate=1,
            coverage="high",
            reliability="RELIABLE",
            recommended_action="AUTO_ACCEPT",
            decision_impact="LOW",
            provenance=["USER_SUPPLIED"],
        )
        out = apply_autonomy_policy(
            belief, profile="auto", high_risk_action="overwrite_source_mph"
        )
        self.assertEqual(out.recommended_action, "ASK_USER")

    def test_pack_decisions(self):
        reqs = [
            {"decision_id": "a", "task_id": "t1", "claim_id": "c1", "q": 1},
            {"decision_id": "b", "task_id": "t1", "claim_id": "c1", "q": 2},
            {"decision_id": "c", "task_id": "t2", "claim_id": "c9", "q": 3},
        ]
        packed = pack_decision_requests(reqs)
        self.assertEqual(len(packed), 2)
        kinds = {p.get("kind") for p in packed}
        self.assertIn("packed", kinds)


class TestDocDefault(unittest.TestCase):
    def test_inflow_default(self):
        r = doc_default_resolve("inlet_thermal_bc")
        self.assertEqual(r["status"], "ok")
        self.assertTrue(r["has_software_doc_default"])
        self.assertEqual(r["doc_default"], "Inflow")

    def test_conflict_keeps_paper(self):
        r = doc_default_resolve("inlet_thermal_bc", paper_reported="Temperature")
        self.assertEqual(r["status"], "conflict")
        self.assertEqual(r["winner"], "paper_reported")


class TestPeerAndDigitize(unittest.TestCase):
    def test_peer_range(self):
        prior = peer_range_prior(
            "Re",
            [
                {"doi": "10.1/a", "value": 100},
                {"doi": "10.1/b", "low": 80, "high": 120},
            ],
            unit="1",
        )
        self.assertEqual(prior["status"], "ok")
        self.assertEqual(prior["range_kind"], "estimated_plausible_range")
        ev = as_inference_evidence(prior)
        finding = {"parameter": "Re", "symbol": "Re", "unit": "1", "reasons": ["missing"]}
        belief = infer_parameter_belief(finding, evidence_sources=ev)
        self.assertEqual(belief.status, "inferred")
        belief = decide_action(belief, autonomy_profile="auto", dual_source_agree=True)
        self.assertIn(belief.recommended_action, ("AUTO_ACCEPT", "RUN_SENSITIVITY", "ASK_USER"))

    def test_digitize_not_reported(self):
        d = digitize_colorbar_fraction(cmin=300, cmax=400, fraction_from_bottom=0.5)
        self.assertEqual(d["origin"], "digitized_estimate")
        self.assertFalse(d["may_promote_to_reported"])
        assert_not_reported(d)
        with self.assertRaises(ValueError):
            assert_not_reported({**d, "may_promote_to_reported": True})
        ov = overlap_with_kpi(d, 350.0)
        self.assertTrue(ov["overlap"])

    def test_axis_unusable(self):
        d = digitize_axis_span(
            axis_min=0, axis_max=1, pixel_low=0, pixel_high=0, pixel_sample=0, quality="unusable"
        )
        self.assertEqual(d["status"], "NOT_RUN")

    def test_sensitivity_budget(self):
        belief = ParameterBelief(
            parameter="k",
            symbol="k",
            status="inferred",
            central_estimate=1.0,
            plausible_range={"low": 0.5, "high": 1.5},
            range_kind="estimated_plausible_range",
            coverage="moderate",
            reliability="RELIABLE",
            provenance=["INFERRED"],
        )
        plan = plan_sensitivity_with_budget(belief, max_bracket_jobs=2, autonomy_profile="auto")
        self.assertEqual(plan["status"], "planned")
        self.assertLessEqual(len(plan["runs"]), 2)


class TestHarnessHeuristics(unittest.TestCase):
    def test_overfit_penalty(self):
        h = score_harness_candidate(
            in_distribution_gain=0.2,
            out_of_distribution_gain=-0.05,
            benchmark_specific=True,
        )
        self.assertEqual(h["recommend"], "REJECT_CANDIDATE")
        metrics = merge_into_retention_metrics(
            {"performance": 0.5, "scientific_validity": 0.5, "false_pass_rate": 0.01, "regression": 0.0, "cost": 1},
            h,
        )
        gate = RetentionGate().evaluate(
            old_metrics={"performance": 0.5, "scientific_validity": 0.5, "false_pass_rate": 0.01, "regression": 0.0, "cost": 1},
            new_metrics=metrics,
        )
        self.assertEqual(gate["decision"], "REJECT")


if __name__ == "__main__":
    unittest.main()
