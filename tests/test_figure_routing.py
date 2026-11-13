"""Synthetic tests for conservative adaptive figure routing; no COMSOL needed."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from server.figure_routing import route_figure

try:
    from PIL import Image
except ImportError:
    Image = None


@unittest.skipUnless(Image, "Install figure-analysis extras")
class RoutingTests(unittest.TestCase):
    def setUp(self):
        td = TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.path = self.root / "example.png"
        im = Image.new("RGB", (60, 40), "white")
        # Two distinct colored traces; user provides ROI and coordinate calibration.
        for x in range(5, 45):
            im.putpixel((x, 20), (255, 0, 0))
        for x in range(5, 25):
            im.putpixel((x, 25), (0, 0, 255))
        im.save(self.path)

    def _curve(self, rgb, name):
        return {"id": name, "operation": "curve", "spec": {
            "roi": [5, 8, 45, 32], "rgb": rgb, "rgb_distance_max": 0,
            "x_axis": {"pixels": [5, 44], "values": [0, 39]},
            "y_axis": {"pixels": [31, 8], "values": [0, 23]},
        }}

    def test_select_with_evidence_provenance(self):
        result = route_figure(self.root, "example.png", [
            self._curve([255, 0, 0], "red"), self._curve([0, 0, 255], "blue")
        ], {"min_score": .75, "min_margin": .08})
        self.assertTrue(result["success"], result)
        self.assertEqual(result["selected_candidate"], "red")
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["scientific_status"], "NOT_RUN")
        self.assertEqual(result["uncertainty"], "NOT_CALIBRATED")
        manifest = json.loads(Path(result["manifest"]).read_text())
        self.assertEqual(len(manifest["source_sha256"]), 64)
        self.assertEqual(len(manifest["candidates"]), 2)
        self.assertTrue(all(c["manifest"] for c in manifest["candidates"]))

    def test_tie_abstains(self):
        result = route_figure(self.root, self.path, [
            self._curve([255, 0, 0], "red"), self._curve([254, 0, 0], "near_red")
        ])
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "ABSTAIN")
        self.assertIsNone(result["selected_candidate"])

    def test_failing_candidate_abstains(self):
        bad = self._curve([0, 0, 255], "bad")
        bad["spec"]["rgb"] = [999, 0, 0]
        result = route_figure(self.root, self.path, [
            self._curve([255, 0, 0], "good"), bad])
        self.assertEqual(result["status"], "ABSTAIN")

    def test_mismatched_roi_blocks(self):
        second = self._curve([0, 0, 255], "blue")
        second["spec"]["roi"] = [5, 8, 46, 32]
        result = route_figure(self.root, self.path, [
            self._curve([255, 0, 0], "red"), second
        ])
        self.assertEqual(result["status"], "BLOCKED")

    def test_duplicate_ids_and_configs_block(self):
        a = self._curve([255, 0, 0], "red")
        b = self._curve([255, 0, 0], "red")
        self.assertEqual(route_figure(self.root, self.path, [a, b])["status"], "BLOCKED")
        b["id"] = "other"
        self.assertEqual(route_figure(self.root, self.path, [a, b])["status"], "BLOCKED")

    def test_field_colorbar_selection(self):
        im = Image.new("RGB", (60, 40), "white")
        colors = [(255, 0, 0), (200, 0, 55), (128, 0, 128),
                  (55, 0, 200), (0, 0, 255)]
        for idx, color in enumerate(colors):
            for x in range(45, 50):
                im.putpixel((x, idx + 5), color)
        for y in range(12, 17):
            for x in range(5, 20):
                im.putpixel((x, y), colors[2])
        im.save(self.path)
        common = {"field_roi": [5, 12, 20, 17], "top_value": 400,
                  "bottom_value": 300, "rgb_distance_max": 0}
        candidates = [
            {"id": "correct", "operation": "field",
             "spec": {**common, "colorbar_roi": [45, 5, 50, 10]}},
            {"id": "wrong", "operation": "field",
             "spec": {**common, "colorbar_roi": [54, 5, 59, 10]}},
        ]
        result = route_figure(self.root, self.path, candidates)
        self.assertEqual(result["selected_candidate"], "correct")
        self.assertEqual(result["candidates"][0]["score"], 1.0)
        self.assertEqual(result["candidates"][1]["score"], 0.0)
        self.assertEqual(result["scientific_status"], "NOT_RUN")

    def test_path_escape_blocks(self):
        result = route_figure(self.root, "../escape.png", [
            self._curve([255, 0, 0], "r"), self._curve([0, 0, 255], "b")
        ])
        self.assertEqual(result["status"], "BLOCKED")

    def test_bad_policy_blocks(self):
        result = route_figure(self.root, self.path, [
            self._curve([255, 0, 0], "r"), self._curve([0, 0, 255], "b")
        ], {"min_margin": float("nan")})
        self.assertEqual(result["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
