"""Synthetic grid-family admission only, no physics solve."""
import unittest
from server.grid_uncertainty_admission import review_grid_family

def grid(i):
    return {
        "run_id": f"g{i}", "h": float(i), "observable_value": 20.0+i**2,
        "geometry_hash": "g", "physics_hash": "p", "boundary_hash": "b",
        "observable_definition_hash": "o", "solver_settings_hash": "s",
        "mesh_geometric_similarity": True, "mesh_quality_review": "PASS",
        "iterative_error_negligible": True, "numerical_convergence": "PASS",
        "artifact_sha256": "a"*64, "solution_id": f"sol{i}",
    }
def study(*grids):
    return {"grids": list(grids), "h_definition":"characteristic cell size in mm",
            "mesh_family_review_evidence":"reviewed mesh generation log"}
class GridAdmissionTests(unittest.TestCase):
    def test_two_grids_not_uncertainty(self):
        x=review_grid_family(study(grid(1),grid(2)))
        self.assertEqual(x["status"],"GRID_SENSITIVITY_ONLY")
        self.assertFalse(x["uncertainty_computed"])
    def test_four_eligible_not_pass(self):
        x=review_grid_family(study(*[grid(i) for i in range(1,5)]))
        self.assertEqual(x["status"],"CANDIDATE_FOR_FIT_NOT_VALIDATED")
        self.assertEqual(x["scientific_status"],"NOT_RUN")
    def test_noncomparable_or_unconverged_blocks(self):
        gs=[grid(i) for i in range(1,5)]
        gs[1]["boundary_hash"]="different"
        gs[2]["iterative_error_negligible"]=False
        x=review_grid_family(study(*gs))
        self.assertEqual(x["status"],"GRID_SENSITIVITY_ONLY")
        self.assertTrue(any("boundary_hash" in i for i in x["issues"]))
    def test_missing_h_definition_blocks(self):
        d=study(*[grid(i) for i in range(1,5)])
        d["h_definition"]=""
        self.assertEqual(review_grid_family(d)["status"],"GRID_SENSITIVITY_ONLY")
    def test_duplicate_mesh_size_blocks(self):
        gs=[grid(i) for i in range(1,5)]
        gs[2]["h"]=gs[1]["h"]
        self.assertEqual(review_grid_family(study(*gs))["status"],"GRID_SENSITIVITY_ONLY")
if __name__ == "__main__":
    unittest.main()
