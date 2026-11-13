"""Offline synthetic classification; no commercial solver required."""
import unittest
from server.native_convergence import review_native_convergence


def example(solver="COMSOL"):
    return {"solver": solver, "execution": "success", "termination": "converged",
            "configured_criterion": "solution-estimate", "termination_log_ref": "job-12:solver-log",
            "warnings": []}


class NativeConvergenceTests(unittest.TestCase):
    def test_solver_converged_extra_diagnostic_not_hard_veto(self):
        data = example()
        data["extra_residual"] = {"value": .2, "limit": .001, "source_ref": "run-a:history"}
        result = review_native_convergence(data)
        self.assertEqual(result["status"], "NATIVE_CONVERGENCE_REPORTED")
        self.assertEqual(result["extra_residual"]["status"], "ABOVE_DECLARED_LIMIT")
        self.assertFalse(result["extra_residual"]["automatic_veto"])
        self.assertFalse(result["automatic_rerun"])
        self.assertEqual(result["scientific_status"], "NOT_RUN")

    def test_saved_result_is_not_native_convergence(self):
        data = example("Fluent")
        data.update(execution="completed", termination="unknown")
        self.assertEqual(review_native_convergence(data)["status"], "TERMINATION_NOT_VERIFIED")

    def test_native_failure(self):
        data = example()
        data["termination"] = "max_iterations"
        self.assertEqual(review_native_convergence(data)["status"], "NATIVE_CONVERGENCE_NOT_MET")

    def test_explicit_contract_remains_visible(self):
        data = example()
        data["extra_residual"] = {"value": .2, "limit": .001, "source_ref": "paper:table",
                                  "kind": "explicit_contract", "threshold_authority": "paper",
                                  "residual_definition": "normalized mass residual"}
        review = review_native_convergence(data)
        self.assertTrue(review["extra_residual"]["requires_contract_review"])
        self.assertTrue(review["native_converged_reported"])

    def test_contract_requires_provenance(self):
        data = example()
        data["extra_residual"] = {"value": .2, "limit": .001,
                                  "source_ref": "unspecified", "kind": "explicit_contract"}
        with self.assertRaises(ValueError):
            review_native_convergence(data)

    def test_warnings_preserved(self):
        data = example()
        data["warnings"] = ["nonlinear solver warning"]
        self.assertEqual(review_native_convergence(data)["status"], "NATIVE_CONVERGENCE_REPORTED_WITH_WARNINGS")


if __name__ == "__main__":
    unittest.main()
