"""Synthetic tests: no COMSOL/Fluent session or scientific validation."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from server.recovery_harness import (
    RecoveryError, SCHEMA, freeze_contract, evaluate_commissioning,
    propose_recovery, evaluate_recovery, invoke,
)


def contract():
    return {
        "schema": SCHEMA, "case_id": "microchannel",
        "software": {"name": "COMSOL", "interface": "MCP", "version": "6.4",
                     "knowledge_ref": "installed-documentation"},
        "baseline": {"run_id": "run_A", "model_revision": "rev0",
                     "spec_hash": "a" * 64, "model_hash": "b" * 64},
        "source_sha256": "c" * 64,
        "parameters": [
            {"name": "inlet_width", "binding": "comp1.geom1.width", "unit": "mm",
             "expected": 0.6, "tolerance": 0.01, "role": "fixed",
             "evidence_ref": "paper"},
            {"name": "heat_coeff", "binding": "comp1.ht.h", "unit": "W/(m2*K)",
             "expected": 150., "tolerance": 5., "role": "calibratable",
             "evidence_ref": "inferred"},
        ],
        "observables": [
            {"name": "pressure_drop", "expression": "p_in-p_out",
             "selection": "inlet-outlet", "unit": "Pa", "reference": 100.,
             "abs_tolerance": 10.,
             "required_gates": ["convergence", "conservation", "mesh_independence"]},
            {"name": "max_temperature", "expression": "maxop1(T)",
             "selection": "channel", "unit": "K", "reference": 315.,
             "abs_tolerance": 2.,
             "required_gates": ["convergence", "physics_consistency"]},
        ],
    }


def commissioning(frozen):
    return {"contract_sha256": frozen["contract_sha256"],
            "run_id": "run_A", "model_revision": "rev0",
            "spec_hash": "a" * 64, "model_hash": "b" * 64,
            "source_ref": "readback-file", "source_sha256": "d" * 64,
            "readbacks": {
                "inlet_width": {"value": 0.6, "unit": "mm",
                                "binding": "comp1.geom1.width"},
                "heat_coeff": {"value": 150., "unit": "W/(m2*K)",
                               "binding": "comp1.ht.h"},
            },
            "available_observables": ["pressure_drop", "max_temperature"]}


def diagnosis():
    return {"schema": "physics-diagnostic/0.7.4", "case_id": "microchannel",
            "reported_test_status": "REPORTED_EXECUTED",
            "interpretation": "REPORTED_TEST_SUPPORTS_PREDICTION",
            "root_cause_confirmed": False, "scientific_status": "NOT_RUN",
            "repair_authorized": False, "hypothesis_id": "temperature_mismatch",
            "test_id": "temperature_test"}


def change():
    return {"parameter": "heat_coeff", "new_value": 175., "unit": "W/(m2*K)",
            "rationale": "Evaluate an alternate heat-transfer coefficient",
            "expected_effect": "Reduce temperature deviation without worsening flow",
            "authorization_required": True}


def result(frozen, complete=True):
    return {"contract_sha256": frozen["contract_sha256"],
            "baseline_run_id": "run_A", "candidate_run_id": "run_B",
            "candidate_model_revision": "rev1", "spec_hash": "a" * 64,
            "authorization_ref": "operator-approved", "source_ref": "candidate-mph",
            "source_sha256": "e" * 64, "values": {
                "pressure_drop": {"value": 105., "unit": "Pa",
                                  "reported_gates": {
                                      "convergence": "PASS", "conservation": "PASS",
                                      "mesh_independence": "PASS"}},
                "max_temperature": {"value": 315.5, "unit": "K",
                                    "reported_gates": {
                                        "convergence": "PASS",
                                        "physics_consistency": "PASS" if complete else "NOT_RUN"}},
            }}


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.frozen = freeze_contract(contract())
        self.commission = evaluate_commissioning(self.frozen, commissioning(self.frozen))
        self.proposal = propose_recovery(self.frozen, self.commission, diagnosis(), change())

    def test_frozen_stable_hash(self):
        self.assertEqual(freeze_contract(contract())["contract_sha256"], self.frozen["contract_sha256"])
        self.assertEqual(self.frozen["status"], "FROZEN_UNCOMMISSIONED")
        self.assertEqual(self.frozen["scientific_status"], "NOT_RUN")

    def test_contract_tamper(self):
        modified = copy.deepcopy(self.frozen)
        modified["contract"]["parameters"][0]["expected"] = 9
        with self.assertRaises(RecoveryError):
            evaluate_commissioning(modified, commissioning(self.frozen))

    def test_unsupported_interface(self):
        data = contract()
        data["software"]["interface"] = "GUI_Automation"
        with self.assertRaises(RecoveryError):
            freeze_contract(data)

    def test_commission_is_reported_only(self):
        self.assertEqual(self.commission["status"], "REPORTED_COMMISSIONING_PASS")
        self.assertEqual(self.commission["verified_execution"], "NOT_RUN")

    def test_wrong_readback(self):
        data = commissioning(self.frozen)
        data["readbacks"]["inlet_width"]["value"] = 1.1
        review = evaluate_commissioning(self.frozen, data)
        self.assertEqual(review["status"], "REPORTED_COMMISSIONING_FAIL")
        with self.assertRaises(RecoveryError):
            propose_recovery(self.frozen, review, diagnosis(), change())

    def test_missing_readback(self):
        data = commissioning(self.frozen)
        del data["readbacks"]["heat_coeff"]
        self.assertEqual(
            evaluate_commissioning(self.frozen, data)["status"],
            "REPORTED_COMMISSIONING_INCOMPLETE")

    def test_unit_guard(self):
        data = commissioning(self.frozen)
        data["readbacks"]["inlet_width"]["unit"] = "m"
        with self.assertRaises(RecoveryError):
            evaluate_commissioning(self.frozen, data)

    def test_run_identity_guard(self):
        data = commissioning(self.frozen)
        data["run_id"] = "run_Z"
        with self.assertRaises(RecoveryError):
            evaluate_commissioning(self.frozen, data)

    def test_fixed_parameter_protection(self):
        bad = change()
        bad["parameter"], bad["unit"] = "inlet_width", "mm"
        with self.assertRaises(RecoveryError):
            propose_recovery(self.frozen, self.commission, diagnosis(), bad)

    def test_diagnosis_cannot_confirm_cause(self):
        bad = diagnosis()
        bad["interpretation"] = "REPORTED_TEST_DOES_NOT_SUPPORT_PREDICTION"
        with self.assertRaises(RecoveryError):
            propose_recovery(self.frozen, self.commission, bad, change())
        self.assertEqual(self.proposal["status"], "PROPOSED_ONLY")
        self.assertFalse(self.proposal["repair_authorized"])
        self.assertFalse(self.proposal["root_cause_confirmed"])

    def test_reported_success_is_not_certification(self):
        review = evaluate_recovery(self.frozen, self.proposal, result(self.frozen))
        self.assertEqual(review["status"], "REPORTED_CRITERIA_MET_NEEDS_VERIFICATION")
        self.assertEqual(review["independent_validation"], "NOT_RUN")
        self.assertFalse(review["candidate_accepted"])

    def test_incomplete_gate_is_not_accepted(self):
        review = evaluate_recovery(self.frozen, self.proposal,
                                   result(self.frozen, complete=False))
        self.assertEqual(review["status"], "REPORTED_CRITERIA_NOT_MET")

    def test_candidate_identity_must_change(self):
        for patch in ({"candidate_run_id": "run_A"},
                      {"candidate_model_revision": "rev0"},
                      {"spec_hash": "f" * 64}):
            with self.subTest(patch=patch), self.assertRaises(RecoveryError):
                evaluate_recovery(self.frozen, self.proposal,
                                  {**result(self.frozen), **patch})

    def test_missing_observable_fails(self):
        data = result(self.frozen)
        del data["values"]["pressure_drop"]
        self.assertEqual(
            evaluate_recovery(self.frozen, self.proposal, data)["status"],
            "REPORTED_CRITERIA_NOT_MET")

    def test_fluent_is_declarative_only(self):
        data = contract()
        data["software"] = {"name": "Fluent", "interface": "PyFluent",
                            "version": "2026R2", "knowledge_ref": "fluent-workflow"}
        self.assertEqual(freeze_contract(data)["status"], "FROZEN_UNCOMMISSIONED")

    def test_workspace_immutable_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "contract.json").write_text(json.dumps(contract()))
            a = invoke("freeze", root, contract_path="contract.json")
            b = invoke("freeze", root, contract_path="contract.json")
            self.assertTrue(a["success"] and b["success"])
            self.assertNotEqual(a["record_path"], b["record_path"])
            self.assertEqual(hashlib.sha256(Path(a["record_path"]).read_bytes()).hexdigest(),
                             a["record_sha256"])
            saved = json.loads(Path(a["record_path"]).read_text())
            (root / "readback.json").write_text(json.dumps(commissioning(saved)))
            review = invoke("commission", root, contract_path=a["record_path"],
                            evidence_path="readback.json")
            self.assertEqual(review["status"], "REPORTED_COMMISSIONING_PASS")
            self.assertFalse(invoke("freeze", root, contract_path="../escape.json")["success"])


if __name__ == "__main__":
    unittest.main()
