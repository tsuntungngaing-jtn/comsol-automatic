"""Offline paper-figure evidence extraction. Never calls or controls COMSOL.

Optional dependencies are loaded only for the requested operation. All paths stay
within COMSOL_OUTPUT_ROOT; extraction is always a digitized estimate, not a
scientifically validated paper value.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from uuid import uuid4

from .runtime import inside

ORIGIN = "digitized_estimate"
MAX_PIXELS = 25_000_000
MAX_FIELD_PIXELS = 200_000  # bound expensive palette matching / CSV export


def _number(value, name):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"{name} must be finite")
    return x


def _rect(values, width, height):
    if not isinstance(values, (list, tuple)) or len(values) != 4:
        raise ValueError("ROI must be [left, top, right, bottom] in image pixels")
    x0, y0, x1, y1 = [int(v) for v in values]
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError("ROI is empty or outside the image")
    return (x0, y0, x1, y1)


def _axis(point, axis):
    pixels = [_number(v, "axis pixel") for v in axis["pixels"]]
    values = [_number(v, "axis value") for v in axis["values"]]
    if len(pixels) != 2 or len(values) != 2 or pixels[0] == pixels[1]:
        raise ValueError("Each axis needs two distinct pixel anchors and two values")
    scale = axis.get("scale", "linear")
    if scale not in ("linear", "log10"):
        raise ValueError("Axis scale must be linear or log10")
    if scale == "log10":
        if min(values) <= 0:
            raise ValueError("Log axes require positive values")
        values = [math.log10(v) for v in values]
    t = (point - pixels[0]) / (pixels[1] - pixels[0])
    value = values[0] + t * (values[1] - values[0])
    return 10 ** value if scale == "log10" else value


def _save_csv(path, headings, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headings)
        writer.writerows(rows)


def _image(source):
    from PIL import Image, ImageOps
    with Image.open(source) as raw:
        if raw.width * raw.height > MAX_PIXELS:
            raise ValueError("Image exceeds 25 million pixels")
        return ImageOps.exif_transpose(raw).convert("RGB")


def _pixel(image, spec, out):
    import numpy as np
    data = np.asarray(image, dtype=np.float32)
    radius = int(spec.get("radius", 0))
    if not 0 <= radius <= 20:
        raise ValueError("radius must be 0..20")
    positions = spec.get("samples", [])
    if not positions or len(positions) > 1000:
        raise ValueError("Provide 1..1000 samples as [x,y] image pixels")
    rows = []
    for pos in positions:
        if len(pos) != 2:
            raise ValueError("Each sample must be [x,y]")
        x, y = int(pos[0]), int(pos[1])
        if not (0 <= x < image.width and 0 <= y < image.height):
            raise ValueError("Sample outside image")
        p = data[max(y-radius, 0):min(y+radius+1, image.height),
                 max(x-radius, 0):min(x+radius+1, image.width)]
        rgb = np.mean(p, axis=(0, 1)).tolist()
        rows.append((x, y, *[round(v, 4) for v in rgb]))
    target = out / "pixels.csv"
    _save_csv(target, ["pixel_x", "pixel_y", "R_mean", "G_mean", "B_mean"], rows)
    return {"samples": len(rows), "files": [str(target)], "preview": rows[:10]}


def _curve(image, spec, out):
    import numpy as np
    from PIL import ImageDraw
    roi = _rect(spec["roi"], image.width, image.height)
    color = np.asarray(spec["rgb"], dtype=float)
    if color.shape != (3,) or not np.all(np.isfinite(color)) or not np.all((0 <= color) & (color <= 255)):
        raise ValueError("rgb must have three values in 0..255")
    tolerance = _number(spec.get("rgb_distance_max", 24), "rgb_distance_max")
    if not 0 <= tolerance <= 441.673:
        raise ValueError("rgb_distance_max must be nonnegative and <= 441.673")
    x0, y0, x1, y1 = roi
    # Reject invalid calibration even if no unambiguous curve pixels are found.
    _axis(x0, spec["x_axis"])
    _axis(y0, spec["y_axis"])
    data = np.asarray(image, dtype=np.int16)[y0:y1, x0:x1, :].astype(float)
    distances = np.sqrt(((data-color)**2).sum(axis=2))
    mask = distances <= tolerance
    rows, ambiguity = [], 0
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    for ix in range(mask.shape[1]):
        matches = np.flatnonzero(mask[:, ix])
        if len(matches) == 0:
            continue
        if int(matches[-1])-int(matches[0]) > int(spec.get("max_vertical_spread_px", 5)):
            ambiguity += 1
            continue  # never guess which overlapping curve is correct
        x = x0 + ix
        y = y0 + float(np.median(matches))
        X = _axis(x, spec["x_axis"])
        Y = _axis(y, spec["y_axis"])
        rows.append((x, round(y, 3), X, Y))
        draw.point((x, round(y)), fill=(255, 0, 255))
    file_csv, file_png = out / "curve.csv", out / "curve_overlay.png"
    _save_csv(file_csv, ["pixel_x", "pixel_y", "x_value", "y_value"], rows)
    overlay.save(file_png)
    return {"points": len(rows), "ambiguous_columns_skipped": ambiguity,
            "missing_columns": (x1-x0)-len(rows)-ambiguity,
            "files": [str(file_csv), str(file_png)],
            "warnings": (["Multiple colored paths overlap; ambiguous columns were skipped."] if ambiguity else []) +
                        (["No trace found; inspect ROI, RGB and tolerance."] if not rows else [])}


def _field(image, spec, out):
    import numpy as np
    from PIL import Image
    field = _rect(spec["field_roi"], image.width, image.height)
    bar = _rect(spec["colorbar_roi"], image.width, image.height)
    left, top, right, bottom = field
    if (right-left)*(bottom-top) > MAX_FIELD_PIXELS:
        raise ValueError("field ROI exceeds 200000 pixels; crop or downsample first")
    if bar[3]-bar[1] < 3:
        raise ValueError("Colorbar must contain at least 3 rows")
    top_value = _number(spec["top_value"], "top_value")
    bottom_value = _number(spec["bottom_value"], "bottom_value")
    if top_value == bottom_value:
        raise ValueError("Colorbar endpoints must differ")
    threshold = _number(spec.get("rgb_distance_max", 30), "rgb_distance_max")
    if not 0 <= threshold <= 441.673:
        raise ValueError("Invalid color distance")
    data = np.asarray(image, dtype=np.uint8)
    bx0, by0, bx1, by1 = bar
    # Median of central strip of the actual figure's legend, not a guessed colormap.
    margin = max(0, (bx1-bx0)//3)
    strip = data[by0:by1, bx0+margin:bx1-margin]
    palette = np.median(strip, axis=1).astype(np.float32)
    values = np.linspace(top_value, bottom_value, num=len(palette))
    patch = data[top:bottom, left:right].reshape(-1, 3).astype(np.float32)
    best_idx = np.zeros(len(patch), dtype=np.int32)
    errors = np.zeros(len(patch), dtype=np.float32)
    # Bounded batches avoid building a whole-image N_pixels x N_palette array.
    for start in range(0, len(patch), 512):
        block = patch[start:start+512]
        diff = block[:, None, :] - palette[None, :, :]
        sqdist = np.sum(diff*diff, axis=2)
        idx = np.argmin(sqdist, axis=1)
        end = start + len(block)
        best_idx[start:end] = idx
        errors[start:end] = np.sqrt(sqdist[np.arange(len(block)), idx])
    keep = errors <= threshold
    outfile, maskfile = out / "field_pixels.csv", out / "field_match_mask.png"
    def generate():
        for i, rgb in enumerate(patch.astype(np.uint8)):
            x, y = left + i % (right-left), top + i // (right-left)
            yield (x, y, *[int(z) for z in rgb],
                   float(values[best_idx[i]]) if keep[i] else "", round(float(errors[i]), 4),
                   "matched" if keep[i] else "unmatched")
    _save_csv(outfile, ["pixel_x", "pixel_y", "R", "G", "B", "value_estimate", "rgb_distance", "match_status"], generate())
    binary = (keep.reshape(bottom-top, right-left).astype(np.uint8)*255)
    Image.fromarray(binary, mode="L").save(maskfile)
    return {"field_pixels": len(patch), "matched_pixels": int(keep.sum()),
            "matched_fraction": float(np.mean(keep)),
            "colorbar_step": abs(top_value-bottom_value)/(len(palette)-1),
            "mean_rgb_distance_matched": float(np.mean(errors[keep])) if keep.any() else None,
            "files": [str(outfile), str(maskfile)],
            "warnings": ["Colors may be nonunique or distorted by compression, transparency or interpolation; manual review required."]}


def _ocr(image, spec, out):
    try:
        import pytesseract
        from pytesseract import Output
        results = pytesseract.image_to_data(image, output_type=Output.DICT, config="--psm 11")
    except (ImportError, FileNotFoundError) as error:
        raise RuntimeError("OCR requires pytesseract and a local Tesseract executable") from error
    rows = []
    for i, label in enumerate(results["text"]):
        if label.strip():
            rows.append([label, results["left"][i], results["top"][i],
                         results["width"][i], results["height"][i], results["conf"][i]])
    target = out / "ocr.csv"
    _save_csv(target, ["text", "left", "top", "width", "height", "confidence"], rows)
    return {"text_boxes": len(rows), "files": [str(target)], "warnings": ["OCR values and units require checking against the source figure."]}


def _pdf_crop(pdf, spec, out):
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("PDF figure extraction requires PyMuPDF (pymupdf)") from error
    page_no = int(spec["page"]) - 1  # human-readable 1-based page
    dpi = int(spec.get("dpi", 250))
    if not 72 <= dpi <= 600:
        raise ValueError("dpi must be 72..600")
    with fitz.open(pdf) as doc:
        if not 0 <= page_no < len(doc):
            raise ValueError("Page number outside PDF")
        page = doc[page_no]
        if "bbox" not in spec:
            raise ValueError("PDF crop requires [left,top,right,bottom] PDF-point bbox")
        rect = fitz.Rect(*[float(v) for v in spec["bbox"]])
        if rect.is_empty or rect.is_infinite or not page.rect.contains(rect):
            raise ValueError("PDF bbox outside page or empty")
        if rect.width*rect.height*(dpi/72)**2 > MAX_PIXELS:
            raise ValueError("PDF render exceeds 25 million pixels")
        pix = page.get_pixmap(clip=rect, dpi=dpi, alpha=False)
        path = out / "figure.png"
        pix.save(str(path))
        return {"page": page_no + 1, "bbox_pdf_points": list(rect),
                "image_size": [pix.width, pix.height], "files": [str(path)]}


def analyze_figure(output_root, operation: str, source_path: str, spec: dict) -> dict:
    """Perform one offline operation with a fresh, immutable output directory."""
    try:
        if not isinstance(spec, dict):
            raise ValueError("spec must be an object")
        operation = str(operation).lower()
        if operation not in ("pdf_crop", "pixel", "curve", "field", "ocr"):
            raise ValueError("Supported operations: pdf_crop, pixel, curve, field, ocr")
        root = Path(output_root).resolve()
        source = inside(root, source_path)
        if not source.is_file():
            raise FileNotFoundError("Source must be an existing file inside COMSOL_OUTPUT_ROOT")
        suffix = ".pdf" if operation == "pdf_crop" else None
        if suffix and source.suffix.lower() != suffix:
            raise ValueError("pdf_crop requires PDF input")
        if operation != "pdf_crop" and source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
            raise ValueError("Image operation requires a raster image")
        image = None if operation == "pdf_crop" else _image(source)
        destination = inside(root, "figure-evidence/" + uuid4().hex)
        destination.mkdir(parents=True, exist_ok=False)
        actions = {"pdf_crop": _pdf_crop, "pixel": _pixel, "curve": _curve,
                   "field": _field, "ocr": _ocr}
        result = actions[operation](source if operation == "pdf_crop" else image, spec, destination)
        h = hashlib.sha256()
        with source.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        manifest = {"operation": operation, "source": str(source), "source_sha256": h.hexdigest(),
                    "spec": spec, "origin": ORIGIN, "source_type": "figure",
                    "may_promote_to_reported": False, "scientific_status": "NOT_RUN",
                    "status": "REVIEW_REQUIRED", "result": result}
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"success": True, "status": "REVIEW_REQUIRED", "origin": ORIGIN,
                "may_promote_to_reported": False, "scientific_status": "NOT_RUN",
                "manifest": str(destination / "manifest.json"), **result}
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, OverflowError) as error:
        return {"success": False, "status": "BLOCKED", "origin": ORIGIN,
                "scientific_status": "NOT_RUN", "error": str(error)}


def register_figure_tools(mcp, runtime):
    @mcp.tool()
    async def paper_figure_analyze(operation: str, source_path: str, spec: dict) -> dict:
        """Offline paper figure: pdf_crop, pixel RGB sampling, RGB-based curve tracing, calibrated field/colorbar inversion, or optional OCR. All files must be inside COMSOL_OUTPUT_ROOT; creates new evidence files only. No COMSOL interaction. Numeric results are digitized_estimate, never scientific PASS."""
        return analyze_figure(runtime.output_root, operation, source_path, spec)
