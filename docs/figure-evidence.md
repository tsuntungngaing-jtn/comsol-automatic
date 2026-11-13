# Scientific paper figure evidence (v0.6.0)

Status: offline executable extraction implemented; **real-paper accuracy benchmarking and real-COMSOL physical validation NOT_RUN**.

The new MCP tool `paper_figure_analyze(operation, source_path, spec)` reads paper PDFs and raster figures **only**; it never reads or controls the COMSOL interface. Install dependencies with `pip install -e ".[figure-analysis]"`. OCR additionally requires a local Tesseract executable on PATH. Place source files inside `COMSOL_OUTPUT_ROOT`; all output is saved into unique `figure-evidence/<uuid>/` directories.

Supported operations (image coordinates originate at upper-left; ROIs are [left, top, right, bottom], right/bottom exclusive):

- `pdf_crop`: `{"page":2,"bbox":[72,100,500,400],"dpi":250}` — 1-based page; bbox in PDF points. Produces figure.png. For scanned sources, image extraction precision is limited by source resolution.
- `pixel`: `{"samples":[[120,45],[180,92]],"radius":0}` — exact RGB or local mean RGB at given image pixels; exports pixels.csv.
- `curve`: `{"roi":[20,20,800,500],"rgb":[10,35,210],"rgb_distance_max":24,"x_axis":{"pixels":[80,750],"values":[0,100],"scale":"linear"},"y_axis":{"pixels":[470,40],"values":[0,10],"scale":"linear"}}` — single target-color tracing and pixel-to-physical-axis mapping; both axes can use linear or log10 scale. Exports curve.csv and curve_overlay.png. Disjoint vertical color intersections are skipped as ambiguous; multiple curves/colors need separate extraction runs.
- `field`: `{"field_roi":[60,60,300,200],"colorbar_roi":[330,75,350,195],"top_value":350,"bottom_value":300,"rgb_distance_max":30}` — source colorbar sampled top-to-bottom; each pixel assigned nearest observed RGB and mapped value (with match mask and RGB residual). Exports field_pixels.csv and field_match_mask.png. Restrict bar ROI to its colored strip, without ticks or numbers.
- `ocr`: `{}` — local Tesseract text, bounding boxes and engine confidence in ocr.csv. Verify scientific units/values manually.

Image size capped at 25 million pixels, field ROI at 200000 pixels; all results are `digitized_estimate`, status `REVIEW_REQUIRED`, and scientific status `NOT_RUN`. Source SHA-256, exact calibration/ROI, origin and outputs are kept in manifest.json. Never promote digitized figures to reported paper numbers or independent validation. Do not use the same digitized figure as both calibration target and validation holdout.

**Limitations:** pixel color is not uniquely recoverable to a physical field where the palette is non-injective; compression, anti-aliasing, transparency, sRGB color profiles, legends, overlaid vectors, and interpolation can distort inversion. Current matching uses Euclidean RGB, not CIE ΔE; numeric uncertainties are **not** certified confidence intervals. Coordinate and colorbar anchors are user/operator specified, not autonomously detected. For scientific comparisons predeclare acceptance thresholds and independently verify overlays, matched-fraction, physical units, masks, and a measured ground-truth sample. This version does not include Fiji/ImageJ or third-party WebPlotDigitizer code.

Synthetic unit tests: `python -m unittest tests.test_figure_analysis`. Tests do not require COMSOL, but require Pillow and NumPy.

## v0.7.2 adaptive configuration routing

`paper_figure_route` selects among pre-reviewed curve or field/colorbar configurations using non-probabilistic, synthetic-untested-on-real-papers quality proxies. It is **not** automatic calibration, PIV, training, or scientific validation. See [adaptive figure routing](adaptive-figure-routing.md).
