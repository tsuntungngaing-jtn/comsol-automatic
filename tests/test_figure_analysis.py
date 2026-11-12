"""Offline synthetic scientific figure checks; no COMSOL or real-paper benchmark."""
import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from server.figure_analysis import analyze_figure

try:
    from PIL import Image
except ImportError:
    Image = None


@unittest.skipUnless(Image, "Install figure-analysis optional deps")
class FigureAnalysisTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root / "figure.png"

    def test_rgb_and_provenance(self):
        image = Image.new("RGB", (40, 30), "white")
        image.putpixel((4, 5), (2, 80, 170))
        image.save(self.path)
        result = analyze_figure(self.root, "pixel", "figure.png", {"samples": [[4, 5]]})
        self.assertTrue(result["success"], result)
        self.assertEqual(tuple(result["preview"][0]), (4, 5, 2, 80, 170))
        manifest = json.loads(Path(result["manifest"]).read_text())
        self.assertEqual(manifest["origin"], "digitized_estimate")
        self.assertFalse(manifest["may_promote_to_reported"])
        self.assertEqual(result["scientific_status"], "NOT_RUN")

    def test_curve_calibration(self):
        im = Image.new("RGB", (40, 30), "white")
        for x in range(5, 35):
            im.putpixel((x, 24 - (x - 5) // 2), (12, 20, 210))
        im.save(self.path)
        spec = {"roi": [5, 6, 35, 25], "rgb": [12, 20, 210],
                "rgb_distance_max": 0,
                "x_axis": {"pixels": [5, 34], "values": [0, 29]},
                "y_axis": {"pixels": [24, 6], "values": [0, 18]}}
        result = analyze_figure(self.root, "curve", self.path.name, spec)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["points"], 30)
        with open(result["files"][0], newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(float(rows[0]["x_value"]), 0)
        self.assertEqual(float(rows[0]["y_value"]), 0)
        self.assertEqual(float(rows[-1]["x_value"]), 29)

    def test_colorbar_recovery(self):
        im = Image.new("RGB", (40, 30), "white")
        colors = [(255, 0, 0), (200, 0, 55), (128, 0, 128),
                  (55, 0, 200), (0, 0, 255)]
        for y, color in enumerate(colors):
            for x in range(32, 38):
                im.putpixel((x, y + 5), color)
        for y in range(10, 15):
            for x in range(5, 15):
                im.putpixel((x, y), colors[2])
        im.save(self.path)
        spec = {"field_roi": [5, 10, 15, 15], "colorbar_roi": [32, 5, 38, 10],
                "top_value": 400, "bottom_value": 300, "rgb_distance_max": 0}
        result = analyze_figure(self.root, "field", "figure.png", spec)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["matched_fraction"], 1)
        with open(result["files"][0], newline="") as f:
            row = next(csv.DictReader(f))
        self.assertEqual(float(row["value_estimate"]), 350)

    def test_ambiguous_curve_is_not_guessed(self):
        im = Image.new("RGB", (40, 30), "white")
        im.putpixel((8, 5), (255, 0, 0))
        im.putpixel((8, 20), (255, 0, 0))
        im.save(self.path)
        spec = {"roi": [7, 4, 10, 22], "rgb": [255, 0, 0],
                "x_axis": {"pixels": [7, 9], "values": [0, 2]},
                "y_axis": {"pixels": [20, 4], "values": [0, 16]}}
        result = analyze_figure(self.root, "curve", "figure.png", spec)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["ambiguous_columns_skipped"], 1)
        self.assertEqual(result["points"], 0)

    def test_path_and_axis_guards(self):
        Image.new("RGB", (40, 30), "white").save(self.path)
        forbidden = analyze_figure(self.root, "pixel", "../escape.png", {"samples": [[0, 0]]})
        self.assertFalse(forbidden["success"])
        invalid = analyze_figure(self.root, "curve", "figure.png",
            {"roi": [0, 0, 40, 30], "rgb": [255, 255, 255],
             "x_axis": {"pixels": [0, 0], "values": [0, 1]},
             "y_axis": {"pixels": [29, 0], "values": [0, 1]}})
        self.assertFalse(invalid["success"])
