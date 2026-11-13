"""Offline mesh diagnostics, no COMSOL required."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from server.mesh_native import MeshInputError, analyze, compare_meshes, validate_mesh, _in_workspace


def mesh(name="coarse", fine=False):
    nodes = [[0.,0.],[1.,0.],[0.,1.]]
    cells = [[0,1,2]]
    if fine:
        nodes = [[0.,0.],[1.,0.],[0.,1.],[.5,0.],[.5,.5],[0.,.5]]
        cells = [[0,3,5],[3,1,4],[5,4,2],[3,4,5]]
    return {"schema":"mesh-native/0.7.1",
            "identity":{"case_id":"c","run_id":name,"mesh_id":name,
                        "geometry_hash":"g","conditions_hash":"p",
                        "coordinate_frame":"global","coordinate_unit":"m"},
            "nodes":nodes,"cells":cells,
            "fields":{"T":{"unit":"K","values":[300+5*x+3*y for x,y in nodes]}}}


class MeshNativeTests(unittest.TestCase):
    def test_validate(self):
        self.assertEqual(validate_mesh(mesh())["status"],"INPUT_VALID")

    def test_linear_exact(self):
        result=compare_meshes(mesh(),mesh("fine",True),"T")
        self.assertEqual(result["status"],"DIAGNOSTIC_ONLY")
        self.assertAlmostEqual(result["metrics"]["rmse"],0)
        self.assertEqual(result["scientific_status"],"NOT_RUN")

    def test_partial_overlap(self):
        fine=mesh("fine",True)
        fine["nodes"][1]=[1.5,0]
        self.assertEqual(compare_meshes(mesh(),fine,"T")["status"],"INSUFFICIENT_COVERAGE")

    def test_units_blocked(self):
        fine=mesh("fine",True)
        fine["fields"]["T"]["unit"]="degC"
        self.assertEqual(compare_meshes(mesh(),fine,"T")["status"],"BLOCKED")

    def test_identity_blocked(self):
        for key in ("geometry_hash","conditions_hash","coordinate_frame","coordinate_unit"):
            with self.subTest(key=key):
                fine=mesh("fine",True)
                fine["identity"][key]="changed"
                self.assertEqual(compare_meshes(mesh(),fine,"T")["status"],"BLOCKED")

    def test_bad_triangles(self):
        bad=mesh()
        bad["nodes"][2]=[2.,0.]
        with self.assertRaises(MeshInputError):
            validate_mesh(bad)
        bad=mesh()
        bad["cells"][0]=[0,1,99]
        with self.assertRaises(MeshInputError):
            validate_mesh(bad)

    def test_bad_values(self):
        bad=mesh()
        bad["fields"]["T"]["values"][0]=float("nan")
        with self.assertRaises(MeshInputError):
            validate_mesh(bad)

    def test_budget(self):
        self.assertEqual(compare_meshes(mesh(),mesh("fine",True),"T",max_pairs=2)["status"],"NOT_RUN")

    def test_same_mesh_id(self):
        self.assertEqual(compare_meshes(mesh(),mesh(),"T")["status"],"BLOCKED")

    def test_report_hashes(self):
        with TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            a.write_text(json.dumps(mesh()),encoding="utf8")
            b.write_text(json.dumps(mesh("fine",True)),encoding="utf8")
            result=analyze("compare",a,b,"T",output_root=td)
            self.assertEqual(result["status"],"DIAGNOSTIC_ONLY")
            self.assertTrue(Path(result["report_path"]).exists())
            self.assertEqual(len(result["input_hashes"]["reference_sha256"]),64)

    def test_workspace(self):
        with TemporaryDirectory() as td:
            with self.assertRaises(MeshInputError):
                _in_workspace(Path(td).parent/"outside.json",td)


if __name__ == "__main__":
    unittest.main()
