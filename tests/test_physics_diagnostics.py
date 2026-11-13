"""Offline hypothesis planning and evidence report unit tests (no COMSOL)."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from server.physics_diagnostics import (
    SCHEMA, DiagnosticError, create_plan, evaluate_report, plan, record_test, review_spec,
)


def spec():
    base = {"schema": SCHEMA, "case_id": "microchannel",
            "baseline": {"run_id": "run_A", "model_revision": "rev0",
                         "spec_hash": "a" * 64, "model_hash": "b" * 64},
            "observations": [{"id": "obs_dp", "quantity": "pressure_drop", "value": 150,
                              "unit": "Pa", "source_ref": "solver-log",
                              "source_sha256": "c" * 64, "run_id": "run_A"}],
            "budget": {"max_tier": 2, "max_tests": 2}}
    def hypothesis(name, category, kind, observable, unit, support):
        return {"id": name, "category": category, "claim": "Investigate " + name,
                "mechanism": "A physical/numerical mechanism needs testing",
                "falsifier": "Measure an inconsistent response",
                "supporting_observation_ids": support,
                "test": {"id": "test_" + name, "kind": kind, "observable": observable,
                         "unit": unit, "support_if": {
                             "operator": "abs_diff_gt", "reference": 0.6, "tolerance": 0.01},
                         "rationale": "Check observable against declared threshold",
                         "required_source": "Recorded COMSOL evidence"}}
    base["hypotheses"] = [
        hypothesis("geometry", "GEOMETRY", "static_readback", "inlet_width", "mm", ["obs_dp"]),
        hypothesis("mesh", "MESH", "controlled_rerun", "grid_difference", "mm", ["obs_dp"]),
        hypothesis("solver", "SOLVER", "existing_result", "residual", "mm", []),
    ]
    return base


def reported(name="geometry", value=.55, run="run_A", revision="rev0", unit="mm"):
    return {"hypothesis_id": name, "test_id": "test_" + name,
            "status": "REPORTED_EXECUTED", "value": value,
            "unit": unit, "run_id": run, "model_revision": revision,
            "spec_hash": "a" * 64, "source_ref": "readback",
            "source_sha256": "d" * 64}


class PhysicsDiagnosticTests(unittest.TestCase):
    def test_plan_prioritizes_read_only(self):
        p = plan(spec())
        self.assertEqual([x["hypothesis_id"] for x in p["proposals"]],
                         ["geometry", "solver", "mesh"])
        self.assertEqual([x["status"] for x in p["proposals"]],
                         ["PROPOSED", "NEEDS_EVIDENCE", "PROPOSED"])
        self.assertEqual(p["eligible_tests"], 2)
        self.assertEqual(p["scientific_status"], "NOT_RUN")
        self.assertFalse(p["root_cause_confirmed"])

    def test_budget_tier_and_count(self):
        s = spec()
        s["budget"]["max_tier"] = 0
        self.assertEqual(plan(s)["proposals"][-1]["status"], "OVER_BUDGET")
        s["budget"] = {"max_tier": 2, "max_tests": 1}
        self.assertEqual(plan(s)["proposals"][-1]["status"], "OVER_TEST_COUNT_BUDGET")

    def test_tier_requires_integer(self):
        s = spec()
        s["budget"]["max_tier"] = 1.0
        with self.assertRaises(DiagnosticError):
            review_spec(s)

    def test_reported_support_and_refutation_not_causality(self):
        a = evaluate_report(plan(spec()), reported(value=.55))
        self.assertTrue(a["decision_rule_satisfied"])
        self.assertFalse(a["root_cause_confirmed"])
        self.assertFalse(a["repair_authorized"])
        self.assertEqual(a["scientific_status"], "NOT_RUN")
        b = evaluate_report(plan(spec()), reported(value=.599))
        self.assertEqual(b["interpretation"],
                         "REPORTED_TEST_DOES_NOT_SUPPORT_PREDICTION")

    def test_rerun_auth_and_run_identity(self):
        e = reported("mesh", .50, run="run_B", revision="rev1")
        with self.assertRaises(DiagnosticError):
            evaluate_report(plan(spec()), e)
        e["authorization_ref"] = "operator-approved"
        self.assertTrue(evaluate_report(plan(spec()), e)["decision_rule_satisfied"])
        e["run_id"] = "run_A"
        with self.assertRaises(DiagnosticError):
            evaluate_report(plan(spec()), e)

    def test_readback_rejects_wrong_identity_or_unit(self):
        for patch in ({"run_id": "other"}, {"model_revision": "old"},
                      {"spec_hash": "e" * 64}, {"unit": "cm"}):
            with self.subTest(patch=patch), self.assertRaises(DiagnosticError):
                evaluate_report(plan(spec()), {**reported(), **patch})

    def test_incomplete_test_cannot_contain_observation(self):
        p = plan(spec())
        incomplete = {"hypothesis_id": "geometry", "test_id": "test_geometry",
                      "status": "NOT_RUN", "reason": "No source"}
        self.assertIsNone(evaluate_report(p, incomplete)["decision_rule_satisfied"])
        with self.assertRaises(DiagnosticError):
            evaluate_report(p, {**reported(), "status": "NOT_RUN", "reason": "No source"})

    def test_missing_support_cannot_be_reported(self):
        with self.assertRaises(DiagnosticError):
            evaluate_report(plan(spec()), {"hypothesis_id": "solver", "test_id": "test_solver",
                                           "status": "BLOCKED", "reason": "Missing log"})

    def test_tamper_rule_not_permitted(self):
        p = plan(spec())
        p["proposals"][0]["expected_decision_rule"]["reference"] = 999
        with self.assertRaises(DiagnosticError):
            evaluate_report(p, reported())

    def test_bad_sources_and_falsification(self):
        s = spec()
        s["observations"][0]["source_ref"] = ""
        with self.assertRaises(DiagnosticError):
            review_spec(s)
        s = spec()
        s["hypotheses"][0]["falsifier"] = ""
        with self.assertRaises(DiagnosticError):
            review_spec(s)

    def test_bad_reference_and_units(self):
        for value in (float("nan"), float("inf"), True):
            s = spec()
            s["hypotheses"][0]["test"]["support_if"]["reference"] = value
            with self.subTest(value=value), self.assertRaises(DiagnosticError):
                review_spec(s)
        s = spec()
        s["hypotheses"][0]["test"]["unit"] = ""
        with self.assertRaises(DiagnosticError):
            review_spec(s)

    def test_unknown_or_duplicate_support_id(self):
        s = spec()
        s["hypotheses"][0]["supporting_observation_ids"] = ["missing"]
        with self.assertRaises(DiagnosticError):
            review_spec(s)
        s = spec()
        s["observations"].append(s["observations"][0])
        with self.assertRaises(DiagnosticError):
            review_spec(s)

    def test_unknown_comparator(self):
        s = spec()
        s["hypotheses"][0]["test"]["support_if"]["operator"] = "execute"
        with self.assertRaises(DiagnosticError):
            review_spec(s)

    def test_immutable_reports_and_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "spec.json").write_text(json.dumps(spec()))
            a, b = create_plan("spec.json", root), create_plan("spec.json", root)
            self.assertTrue(a["success"] and b["success"])
            self.assertNotEqual(a["plan_path"], b["plan_path"])
            plan_file = Path(a["plan_path"])
            report = json.loads(plan_file.read_text())
            self.assertEqual(report["input_sha256"],
                             hashlib.sha256((root / "spec.json").read_bytes()).hexdigest())
            (root / "result.json").write_text(json.dumps(reported()))
            output = record_test(plan_file, "result.json", root)
            self.assertTrue(output["success"], output)
            data = json.loads(Path(output["report_path"]).read_text())
            self.assertFalse(data["root_cause_confirmed"])
            self.assertFalse(data["repair_authorized"])
            self.assertFalse(create_plan("../escape.json", root)["success"])
            self.assertFalse(record_test("../bad.json", "result.json", root)["success"])


if __name__ == "__main__":
    unittest.main()
