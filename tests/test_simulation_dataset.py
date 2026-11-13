"""Synthetic offline Design-of-Experiments tests; do not require COMSOL."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from server.simulation_dataset import DatasetError, SCHEMA, create_plan, plan_cases, record_outcome, validate_spec


def spec():
    return {
        "schema": SCHEMA, "study_id": "microchannel", "source_sha256": "a" * 64,
        "seed": 42,
        "parameters": [
            {"name": "width", "unit": "mm", "lower": .3, "upper": 1.,
             "kind": "continuous", "role": "geometry", "origin": "USER_SUPPLIED", "evidence_ref": "paper-2"},
            {"name": "height", "unit": "mm", "lower": .8, "upper": 1.5,
             "kind": "continuous", "role": "geometry", "origin": "INFERRED", "evidence_ref": "assumption-1"},
            {"name": "steps", "unit": "count", "lower": 3, "upper": 7,
             "kind": "integer", "role": "other", "origin": "USER_SUPPLIED", "evidence_ref": "plan"},
        ],
        "constraints": [{"type": "le", "left": "width", "right": "height"}],
        "observables": [
            {"name": "delta_p", "unit": "Pa", "required_checks": [
                "solver_convergence", "conservation", "mesh_independence"]},
            {"name": "max_T", "unit": "K", "required_checks": [
                "solver_convergence", "mesh_independence", "scientific_comparison"]},
        ],
        "splits": {"train": .7, "validation": .2, "test": .1},
    }


class DatasetTests(unittest.TestCase):
    def test_seed_determinism_case_count_and_splits(self):
        a, b = plan_cases(spec(), 10), plan_cases(spec(), 10)
        self.assertEqual(a, b)
        self.assertEqual(len(a["cases"]), 10)
        self.assertEqual([sum(c["split"] == k for c in a["cases"])
                          for k in ("train", "validation", "test")], [7, 2, 1])
        self.assertTrue(all(c["execution_status"] == "PLANNED" for c in a["cases"]))
        self.assertTrue(all(c["observable_validation"]["delta_p"]["required_checks"]["mesh_independence"] == "NOT_RUN"
                            for c in a["cases"]))
        self.assertEqual(a["ood_status"], "NOT_GENERATED")

    def test_lhs_and_constraints(self):
        d = spec()
        d["constraints"] = []
        p = plan_cases(d, 10)
        bins = sorted(int((c["parameters"]["width"]["value"] - .3) / .7 * 10)
                      for c in p["cases"])
        self.assertEqual(bins, list(range(10)))
        self.assertTrue(all(isinstance(c["parameters"]["steps"]["value"], int)
                            and 3 <= c["parameters"]["steps"]["value"] <= 7 for c in p["cases"]))
        d["constraints"] = [{"type": "ratio", "left": "width", "right": "height",
                             "min": .25, "max": 1.5}]
        p = plan_cases(d, 12)
        self.assertTrue(all(.25 <= c["parameters"]["width"]["value"] /
                            c["parameters"]["height"]["value"] <= 1.5 for c in p["cases"]))
        self.assertTrue(p["constraint_bias_warning"])

    def test_provenance_required(self):
        d = spec()
        del d["parameters"][0]["evidence_ref"]
        with self.assertRaises(DatasetError):
            validate_spec(d)

    def test_nonfinite_is_rejected(self):
        d = spec()
        d["parameters"][1]["upper"] = float("nan")
        with self.assertRaises(DatasetError):
            validate_spec(d)

    def test_unit_mismatch_constraint(self):
        d = spec()
        d["parameters"][1]["unit"] = "m"
        with self.assertRaises(DatasetError):
            validate_spec(d)

    def test_impossible_constraint_fails_closed(self):
        d = spec()
        d["constraints"] = [{"type": "lt", "left": "height", "right": "width"}]
        with self.assertRaises(DatasetError):
            plan_cases(d, 4)

    def test_invalid_count_and_splits(self):
        with self.assertRaises(DatasetError):
            plan_cases(spec(), 501)
        d = spec()
        d["splits"] = {"train": .8, "validation": .1, "test": .3}
        with self.assertRaises(DatasetError):
            plan_cases(d, 5)

    def test_write_plan_and_report_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "design.json").write_text(json.dumps(spec()), encoding="utf-8")
            a = create_plan("design.json", 4, root)
            b = create_plan("design.json", 4, root)
            self.assertTrue(a["success"] and b["success"])
            self.assertNotEqual(a["plan_path"], b["plan_path"])
            path = Path(a["plan_path"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), a["plan_sha256"])
            evidence = {"outcome": "REPORTED_SUCCESS", "run_id": "run1",
                        "evidence_ref": "lablog-1",
                        "observables": {"delta_p": {"value": 120, "unit": "Pa",
                                                    "evidence_ref": "result-file"}}}
            (root / "evidence.json").write_text(json.dumps(evidence))
            r = record_outcome(path, "case-00001", "evidence.json", root)
            self.assertTrue(r["success"], r)
            report = json.loads(Path(r["report_path"]).read_text())
            self.assertFalse(report["dataset_ready"])
            self.assertEqual(report["verified_execution"], "NOT_RUN")
            self.assertEqual(report["per_observable_verified_checks"]["delta_p"]["mesh_independence"], "NOT_RUN")
            self.assertEqual(report["reported_evidence"]["observables"]["delta_p"]["value"], 120)

    def test_failure_taxonomy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "design.json").write_text(json.dumps(spec()))
            plan = create_plan("design.json", 1, root)["plan_path"]
            evidence = {"outcome": "REPORTED_FAILURE", "run_id": "run1",
                        "evidence_ref": "solver-log", "observables": {},
                        "failure_category": "MESH", "failure_stage": "meshing"}
            (root / "evidence.json").write_text(json.dumps(evidence))
            self.assertTrue(record_outcome(plan, "case-00001", "evidence.json", root)["success"])
            evidence["failure_category"] = "INVALID"
            (root / "evidence.json").write_text(json.dumps(evidence))
            self.assertFalse(record_outcome(plan, "case-00001", "evidence.json", root)["success"])

    def test_unit_and_unknown_case_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "design.json").write_text(json.dumps(spec()))
            plan = create_plan("design.json", 1, root)["plan_path"]
            evidence = {"outcome": "REPORTED_SUCCESS", "run_id": "run1",
                        "evidence_ref": "solver-log",
                        "observables": {"delta_p": {"value": 120, "unit": "kPa",
                                                    "evidence_ref": "file-1"}}}
            (root / "evidence.json").write_text(json.dumps(evidence))
            self.assertFalse(record_outcome(plan, "case-00001", "evidence.json", root)["success"])
            self.assertFalse(record_outcome(plan, "missing", "evidence.json", root)["success"])

    def test_workspace_guards(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(create_plan("../escape.json", 1, td)["success"])
            self.assertFalse(create_plan(None, 1, td)["success"])
            self.assertFalse(record_outcome("../plan.json", "case-00001", "../e.json", td)["success"])


if __name__ == "__main__":
    unittest.main()
