# Adaptive Figure Routing — v0.7.2

**Status:** a conservative **rule-based** selector for scientific-paper curve and field image extraction. Does not use ART of PIV's neural classifier, optical flow, PIV, closed-loop flow control or learned ROI detection. **Synthetic software tests only; real published-paper benchmarks and COMSOL validation NOT_RUN.**

## Why

Inspired by the algorithm-selection insight in *ART of PIV: Agentic Real-Time Particle Image Velocimetry for Active Flow Control* (https://arxiv.org/abs/2610.41304), the router compares a bounded set of **pre-approved** extraction configurations and keeps an auditable selection and abstention decision. This is an adaptation of the *selection principle*, not a replication of PIV algorithms.

The existing offline `paper_figure_analyze` is unchanged. The new `paper_figure_route` calls it to produce independent, per-candidate evidence manifests. Only image inputs inside `COMSOL_OUTPUT_ROOT` are accepted; no COMSOL JVM, UI access, or solver runs occur.

## MCP invocation

```json
{
  "source_path": "paper-figures/figure.png",
  "candidates": [
    {
      "id": "red",
      "operation": "curve",
      "spec": {
        "roi": [5, 8, 45, 32],
        "rgb": [255, 0, 0],
        "rgb_distance_max": 0,
        "x_axis": {"pixels": [5, 44], "values": [0, 39]},
        "y_axis": {"pixels": [31, 8], "values": [0, 23]}
      }
    },
    {
      "id": "blue",
      "operation": "curve",
      "spec": {
        "roi": [5, 8, 45, 32],
        "rgb": [0, 0, 255],
        "rgb_distance_max": 0,
        "x_axis": {"pixels": [5, 44], "values": [0, 39]},
        "y_axis": {"pixels": [31, 8], "values": [0, 23]}
      }
    }
  ],
  "policy": {"min_score": 0.75, "min_margin": 0.08}
}
```

The default `min_score` is 0.75 and `min_margin` is 0.08. These are engineering heuristics, **not statistically validated thresholds**. The candidate IDs are unique and constrained; 2–6 candidates are required. All candidates must use the same operation and exactly the same comparison target/calibration/tolerances.

For **curve** candidates: the ROI, x/y axes, RGB distance threshold and maximum vertical spread must remain equal. Candidates may differ in the supplied target RGB. Score is `(traced_columns - ambiguous_columns) / ROI_width`, clipped at zero. It measures coverage only, not ground-truth correctness. A filled background or a wrong color can score highly.

For **field** candidates: the field ROI, colorbar endpoint values and RGB threshold must remain equal. Candidates may differ in **pre-reviewed** colorbar ROI. Score is `matched_fraction`. It does not prove that the selected colorbar represents the intended field, that the palette is injective, or that numeric values are correct.

No automatic ROI discovery, OCR interpretation, image classification, uncertainty calibration, multi-method image synthesis, source-material reconstruction, or generation of calibrated ground-truth labels is implemented. The operator must supply meaningful candidate ROIs and scales and verify which curve or physical quantity was intended.

## Selection, errors, and abstention

- All comparable candidates are executed; outputs include per-candidate source hash-backed extraction manifests.
- If any candidate fails, selection **abstains**.
- If best score < `min_score` or best-second margin < `min_margin`, selection **abstains**.
- Otherwise, router returns a selected candidate ID but overall `REVIEW_REQUIRED` for human inspection. The selected candidate is **not** declared scientifically correct.
- Mismatched candidate targets, duplicate IDs/configurations, invalid image/path/ROI/calibration/policy inputs return `BLOCKED`.
- Every result is `digitized_estimate` and has `scientific_status=NOT_RUN`, `uncertainty=NOT_CALIBRATED` (where selection completed), and `may_promote_to_reported=false`.
- Never use the selector score alone for scientific acceptance, parameter inference, simulation model repair, or RSI AgentVersion retention.

## Audit and evaluation

Each extraction creates its existing immutable `figure-evidence/<uuid>/manifest.json`. Routing writes `figure-routing/<uuid>/routing_manifest.json` containing candidate IDs, quality proxies, selection rationale, policy, source hash and links to per-candidate manifests. No original research image is overwritten.

Run synthetic regression tests using:

```sh
python -m unittest tests.test_figure_routing
```

Optional dependencies: `pip install -e ".[figure-analysis]"`.

Before making empirical accuracy claims, benchmark against a **held-out** suite of annotated scientific figures with ground-truth numerical values, and report per-class error, failure/abstention rates, latency, calibration quality and fixed-rule baselines. Compare to the fixed best configuration under equal candidate/compute budgets. Do not use the same digitized figure as both calibration and independent reference.

## Future work (not implemented)

- Multi-algorithm candidate pool (CIELAB color distances, alternative curve tracers, vector-PDF extraction);
- explicit ROI proposals with expert-approved target and unbiased review;
- learned selector trained on held-out labeled figure benchmarks;
- uncertainty-calibrated decision policies and cross-figure generalization;
- physical comparison with COMSOL after an authorized simulation.
