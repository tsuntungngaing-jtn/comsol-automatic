# Physics-Aware Diagnostic Hypothesis Planning — v0.7.4

**Status: offline deterministic contract review and reported-evidence testing, not automated cause discovery.** Inspired by the scientific hypothesis/review/evaluation workflow in *Automated Discovery of Physically Interpretable Subgrid Length Scales for Detached Eddy Simulation via Agentic AI* (DEScover, arXiv:2610.29850). We adapt its **method**, not the DES closure, OpenFOAM code changes, trained agent, or turbulent-model discovery experiments.

Use this tool only for permitted exported research evidence. **Do not use image/OCR/mouse automation to control COMSOL.** No COMSOL APIs are called by these tools; operator uses existing approved MCP tools separately if readback/solve is authorized.

## Design and scientific limits

Each diagnostic hypothesis declares an interpretable mechanism, a falsifier, baseline observations, a predeclared numeric test, unit and evidence source. The planner rejects mismatched run identity and malformed inputs; prioritizes inexpensive readback over reruns. Reporting a favorable test result **does not confirm causality or root cause**. A successful tool invocation merely means a syntactically valid offline plan/report was recorded. All scientific results remain `NOT_RUN`.

Four cost tiers:

0. `static_readback` — check geometry, selections, units, configuration; no solve.
1. `existing_result` — inspect previously generated outputs/logs, with consistent baseline identity.
2. `controlled_rerun` — proposed one-variable controlled test; requires separate user authorization before real execution.
3. `full_revalidation` — proposed full re-solve and physical review; requires separate user authorization.

`max_tier` and `max_tests` cap eligible tests. A proposed tier 2/3 test does **not** grant COMSOL tool permission. Only limited descriptive, predefined comparison operations are supported; the module never executes user-provided formulas, arbitrary Python, or a solver.

## Example: pressure-drop discrepancy

Put this reviewed JSON in `COMSOL_OUTPUT_ROOT/diagnostic-spec.json`:

```json
{
  "schema": "physics-diagnostic/0.7.4",
  "case_id": "microchannel",
  "baseline": {
    "run_id": "run_A",
    "model_revision": "rev0",
    "spec_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "model_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "observations": [
    {
      "id": "obs_dp",
      "quantity": "pressure_drop",
      "value": 150,
      "unit": "Pa",
      "source_ref": "approved-solver-output",
      "source_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "run_id": "run_A"
    }
  ],
  "hypotheses": [
    {
      "id": "geometry_mismatch",
      "category": "GEOMETRY",
      "claim": "The inlet width differs from the reviewed design",
      "mechanism": "Geometry changes cross-sectional flow resistance",
      "falsifier": "MCP geometric readback matches the reference within tolerance",
      "supporting_observation_ids": ["obs_dp"],
      "test": {
        "id": "read_width",
        "kind": "static_readback",
        "observable": "inlet_width",
        "unit": "mm",
        "support_if": {
          "operator": "abs_diff_gt",
          "reference": 0.6,
          "tolerance": 0.01
        },
        "rationale": "Check inlet geometry before spending solver time",
        "required_source": "authorized COMSOL geometry readback"
      }
    }
  ],
  "budget": {"max_tier": 1, "max_tests": 2}
}
```

All hashes and values above are **illustrative placeholders**. Replace with actually acquired source hashes, stable physical definitions, approved units, and predeclared tolerances. Do not fake evidence IDs, revise thresholds after seeing an outcome, or treat high pressure drop alone as proof of a geometry defect.

### Run the offline planner

```sh
python -m server.physics_diagnostics plan --spec diagnostic-spec.json --output-root /your/COMSOL_OUTPUT_ROOT
python -m unittest tests.test_physics_diagnostics
```

Or call MCP `physics_diagnostic_plan(spec_path)`. The tool writes an immutable, UUID-named plan under `COMSOL_OUTPUT_ROOT/diagnostics/plans/`. It records proposal priority and status (`PROPOSED`, `NEEDS_EVIDENCE`, `OVER_BUDGET`, `OVER_TEST_COUNT_BUDGET`). Each remains `test_status: NOT_RUN`.

### Record a *reported*, externally acquired result

```json
{
  "hypothesis_id": "geometry_mismatch",
  "test_id": "read_width",
  "status": "REPORTED_EXECUTED",
  "value": 0.55,
  "unit": "mm",
  "run_id": "run_A",
  "model_revision": "rev0",
  "spec_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "source_ref": "reviewed-COMSOL-readback",
  "source_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
}
```

Use `physics_diagnostic_record(plan_path, evidence_path)` or:

```sh
python -m server.physics_diagnostics record --plan /path/to/plan.json --evidence evidence.json --output-root /your/COMSOL_OUTPUT_ROOT
```

Only tests with status `PROPOSED` can be reported. `REPORTED_EXECUTED` values must have exact units, source, spec/run identity and (for tier 2/3) an authorization reference and distinct run ID. A `NOT_RUN` or `BLOCKED` entry contains a reason, not a measurement. Each record is a new immutable report with hashes of the plan and evidence JSON, and always retains `causal_status: UNCONFIRMED`, `scientific_status: NOT_RUN`, `repair_authorized: false`.

Supported `support_if.operator`: `greater_than`, `less_than`, `abs_diff_gt`, `abs_diff_le`. Equality with threshold boundaries follows these strict/weak inequalities. This is **only a simple prespecified test of a reported number**; no statistical intervals, multivariate diagnostics or causal intervention evaluation are performed.

## Safety, authority, and future work

The source SHA-256 values in caller-provided evidence records are syntactically validated, not authenticated against the underlying original COMSOL artifact by this module. Source files remain operator responsibility. Existing `validation_gate`, `scientific_validity`, `RepairController` and `simulation_dataset` are **not automatically chained**: the planner has no mutation capabilities, no autonomous tool execution, no approval bypass and no RSI retention side effect.

Proposed future work: trusted MCP acquisition of solver/geometry evidence; additional mechanism-level diagnostics (conservation terms, mesh quality, boundaries); an authenticated single-factor experiment orchestrator; benchmark with injected, known-root-cause cases and false-diagnosis rates. **These are not v0.7.4 claims.**

Tested with synthetic offline Python tests only. Real COMSOL diagnosis and physical root-cause verification: **NOT_RUN**.
