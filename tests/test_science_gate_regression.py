"""Offline regression for scientific-state precedence and evidence-trust boundary."""
import tempfile
import unittest
from unittest.mock import patch

from server.scientific_validity import evaluate_scientific_validity
from rsi.retention_gate import RetentionGate
from rsi.controller import RSIController


def sci(execution="PASS", numerical="PASS", checks="PASS", beliefs=None):
    return evaluate_scientific_validity(
        execution_status=execution, numerical_status=numerical,
        required_checks_status=checks, parameter_beliefs=beliefs or [],
    )


class ScienceGateRegression(unittest.TestCase):
    def test_missing_required_checks_not_pass(self):
        r = evaluate_scientific_validity(execution_status="PASS", numerical_status="PASS")
        self.assertNotEqual(r["scientific_status"], "PASS")
        self.assertFalse(r["final_scientific_pass"])

    def test_solver_failed_with_high_impact_inference_is_failure(self):
        belief = [{"status": "inferred", "decision_impact": "HIGH"}]
        r = sci(execution="FAIL", beliefs=belief)
        self.assertEqual(r["scientific_status"], "FAIL")

    def test_solver_blocked_not_failure(self):
        self.assertEqual(sci(execution="BLOCKED")["scientific_status"], "BLOCKED")

    def test_conditional_high_impact_cannot_certify(self):
        belief = [{"status": "inferred", "decision_impact": "HIGH"}]
        r = sci(beliefs=belief)
        self.assertEqual(r["scientific_status"], "CONDITIONAL")
        self.assertFalse(r["final_scientific_pass"])

    def test_explicit_missing_check_overrides_known_inputs(self):
        self.assertEqual(sci(checks="NOT_RUN")["scientific_status"], "NOT_RUN")

    def test_validated_good_inputs_remain_pass(self):
        self.assertEqual(sci()["scientific_status"], "PASS")

    def test_validation_failure_not_misclassified(self):
        self.assertEqual(sci(checks="FAIL")["scientific_status"], "FAIL")

    def test_unstable_result_not_final_pass(self):
        result = evaluate_scientific_validity(
            execution_status="PASS", numerical_status="PASS",
            required_checks_status="PASS", conclusion_stable=False)
        self.assertEqual(result["scientific_status"], "INSUFFICIENT_EVIDENCE")

    def test_unverified_great_metrics_cannot_upgrade(self):
        g = RetentionGate()
        old = {"performance": .4, "scientific_validity": .7,
               "false_pass_rate": .01, "regression": 0., "cost": 10}
        new = {"performance": .9, "scientific_validity": .9,
               "false_pass_rate": 0., "regression": 0., "cost": 1}
        r = g.evaluate(old_metrics=old, new_metrics=new)
        self.assertEqual(r["decision"], "REVIEW_REQUIRED")
        self.assertFalse(r["promote_active_version"])

    def test_missing_or_nan_metrics_cannot_upgrade(self):
        g = RetentionGate()
        m = {"performance": .5, "scientific_validity": .5,
             "false_pass_rate": .02, "regression": 0., "cost": 5}
        self.assertEqual(g.evaluate(old_metrics=m, new_metrics={"performance": .9})["decision"], "REVIEW_REQUIRED")
        self.assertEqual(g.evaluate(old_metrics=m, new_metrics={**m,"performance":float("nan")})["decision"], "REVIEW_REQUIRED")

    def test_final_validation_blocker_keeps_independent_work_without_auto_solve(self):
        with tempfile.TemporaryDirectory() as folder:
            controller = RSIController(folder)
            inference = {
                "findings": [], "beliefs": [], "recommended_actions": ["BLOCK_FINAL_VALIDATION"],
                "may_enter_closed_loop": False, "requires_user": False,
                "final_validation_blocked": True, "nondependent_work_allowed": True,
                "permitted_nonmutating_steps": ["source_retrieval", "geometry_preparation"],
            }
            calls = []
            with patch.object(controller, "infer_task_parameters", return_value=inference):
                result = controller.run_with_closed_loop(
                    parameters=[], task_id="case", task_family="CHT",
                    context={}, closed_loop_fn=lambda _: calls.append("attempted_solve"))
            self.assertEqual(calls, [])
            self.assertIsNone(result["closed_loop"])
            self.assertTrue(result["inference"]["nondependent_work_allowed"])
            self.assertTrue(result["inference"]["final_validation_blocked"])

if __name__ == "__main__":
    unittest.main()
