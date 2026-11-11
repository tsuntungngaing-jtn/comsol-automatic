"""Tests for bounded retrieval and evidence-gated A/B retention."""
from __future__ import annotations

import tempfile
import unittest

from rsi.context_retrieval import retrieve_context
from rsi.controller import RSIController
from rsi.evaluation import evaluate_paired_heldout


def _obs(task: str, variant: str, *, scientific: str = "PASS",
         claimed: bool = True, calls: int = 2):
    return {
        "identity": {
            "run_id": f"{task}-{variant}",
            "model_revision": 1,
            "study": "std1", "solver": "sol1",
            "solution": f"solution-{variant}", "dataset": f"data-{variant}",
            "parameters_hash": "parameters-frozen",
        },
        "evidence": {
            "origin": "real_comsol_mcp",
            "artifact_sha256": "a" * 64,
            "collector_run_id": f"{task}-{variant}",
        },
        "spec_hash": "frozen-spec",
        "conditions_hash": "conditions",
        "materials_hash": "materials",
        "metric_definitions_hash": "metrics",
        "checks": {
            "numerical": "PASS",
            "scientific": scientific,
            "reopen": "PASS",
            "conservation": scientific,
            "mesh_independence": scientific,
        },
        "claimed_success": claimed,
        "solver_calls": calls,
    }


def _pairs(n=3, new_status="PASS"):
    return [
        {
            "task_id": f"t{i}",
            "dataset_split": "held_out",
            "task_kind": "physical",
            "spec_hash": "frozen-spec",
            "required_checks": [
                "numerical", "scientific", "reopen",
                "conservation", "mesh_independence",
            ],
            "old": _obs(f"t{i}", "old", scientific="FAIL", claimed=False, calls=3),
            "new": _obs(f"t{i}", "new", scientific=new_status, calls=1),
        }
        for i in range(n)
    ]


class TestRetrieval(unittest.TestCase):
    def test_budget_dedup_and_heldout_isolation(self):
        records = [
            {"experience_id": "1", "task_id": "train1", "dataset_split": "experience",
             "task_family": "fluid", "diagnosis": "pressure inlet geometry problem"},
            {"experience_id": "2", "task_id": "test1", "dataset_split": "held_out",
             "task_family": "fluid", "diagnosis": "pressure inlet geometry problem secret"},
            {"experience_id": "3", "task_id": "train2", "dataset_split": "experience",
             "task_family": "fluid", "diagnosis": "pressure inlet geometry problem"},
            {"experience_id": "4", "task_id": "train3", "dataset_split": "experience",
             "task_family": "thermal", "diagnosis": "temperature conservation"},
        ]
        result = retrieve_context(
            records, "pressure inlet geometry", task_family="fluid", max_chars=35
        )
        self.assertEqual(len(result["items"]), 1)
        self.assertLessEqual(result["chars_used"], 35)
        self.assertTrue(result["held_out_excluded"])
        self.assertEqual(result["items"][0]["experience_id"], "1")

    def test_optional_embedder(self):
        class FakeEmbedder:
            def encode(self, texts):
                return [[1.0, 0.0]] + [[1.0, 0.0] for _ in texts[1:]]

        result = retrieve_context(
            [{"experience_id": "x", "dataset_split": "experience",
              "diagnosis": "failed solve"}],
            "solver", embedder=FakeEmbedder()
        )
        self.assertEqual(result["method"], "embedding")
        self.assertEqual(result["items"][0]["similarity"], 1.0)


class TestEvaluation(unittest.TestCase):
    def test_absent_real_verifier_blocks(self):
        result = evaluate_paired_heldout(_pairs())
        self.assertEqual(result["status"], "NOT_RUN")

    def test_verified_pairs_measure_success_and_cost(self):
        result = evaluate_paired_heldout(_pairs(), evidence_verifier=lambda obs: True)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["new_metrics"]["performance"], 1.0)
        self.assertEqual(result["new_metrics"]["cost"], 3)
        self.assertEqual(result["old_metrics"]["cost"], 9)

    def test_overlap_blocks(self):
        result = evaluate_paired_heldout(
            _pairs(), learning_task_ids={"t0"},
            evidence_verifier=lambda obs: True,
        )
        self.assertEqual(result["status"], "NOT_RUN")

    def test_missing_mesh_independence_blocks(self):
        pairs = _pairs()
        pairs[0]["new"]["checks"]["mesh_independence"] = "NOT_RUN"
        result = evaluate_paired_heldout(pairs, evidence_verifier=lambda obs: True)
        self.assertEqual(result["status"], "NOT_RUN")

    def test_geometry_requires_geometry_and_selection(self):
        cases = _pairs()
        cases[0]["task_kind"] = "geometry"
        cases[0]["required_checks"] = ["numerical", "scientific", "reopen"]
        result = evaluate_paired_heldout(cases, evidence_verifier=lambda obs: True)
        self.assertEqual(result["status"], "NOT_RUN")

    def test_unpaired_conditions_block(self):
        cases = _pairs()
        cases[0]["new"]["materials_hash"] = "changed"
        result = evaluate_paired_heldout(cases, evidence_verifier=lambda obs: True)
        self.assertEqual(result["status"], "NOT_RUN")

    def test_legacy_metrics_cannot_promote_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctrl = RSIController(tmp)
            result = ctrl.propose_and_gate(
                old_metrics={"performance": 0.4, "scientific_validity": 0.7,
                             "false_pass_rate": 0, "regression": 0, "cost": 4},
                new_metrics={"performance": 1.0, "scientific_validity": 1.0,
                             "false_pass_rate": 0, "regression": 0, "cost": 1},
            )
            self.assertEqual(result["gate"]["decision"], "REJECT")
            self.assertEqual(result["gate"]["status"], "NOT_RUN")
            self.assertEqual(ctrl.versions.active_id(), "A0")

    def test_candidate_retained_only_after_verified_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctrl = RSIController(tmp)
            result = ctrl.propose_and_gate(
                paired_heldout_cases=_pairs(),
                evidence_verifier=lambda obs: True,
            )
            self.assertEqual(result["gate"]["decision"], "RETAIN")
            self.assertNotEqual(ctrl.versions.active_id(), "A0")


if __name__ == "__main__":
    unittest.main()
