# Simulation Dataset and DoE Foundation — v0.7.3

**Offline capability.** Inspired by *High-Fidelity Aerostructural Dataset of Transonic Wings in Cruise Conditions* (arXiv:2610.36442). This implements an auditable sampling/manifest layer, NOT ADflow, TACS, MPhys, COMSOL batch solves, automatic mesh warping, experimental validation, or surrogate training.

## Design-space contract

Each input is a reviewed JSON file under `COMSOL_OUTPUT_ROOT`. Example:

```json
{
  "schema": "simulation-dataset/0.7.3",
  "study_id": "microchannel",
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "seed": 42,
  "parameters": [
    {"name":"width","unit":"mm","lower":0.3,"upper":1.0,"kind":"continuous","role":"geometry","origin":"USER_SUPPLIED","evidence_ref":"source-table-1"},
    {"name":"height","unit":"mm","lower":0.8,"upper":1.5,"kind":"continuous","role":"geometry","origin":"INFERRED","evidence_ref":"documented-assumption-1"}
  ],
  "constraints": [
    {"type":"le","left":"width","right":"height"}
  ],
  "observables": [
    {"name":"pressure_drop","unit":"Pa","required_checks":["solver_convergence","conservation","mesh_independence"]},
    {"name":"max_temperature","unit":"K","required_checks":["solver_convergence","mesh_independence","scientific_comparison"]}
  ],
  "splits":{"train":0.7,"validation":0.2,"test":0.1}
}
```

The digest shown is a **placeholder**, not a valid provenance for real work: provide the actual SHA-256 of the relevant source file. Origin and evidence_ref must accurately represent how each range was chosen; `INFERRED` must never be promoted into `MEASURED` or a paper-reported value. This is a separate DoE schema, not a replacement for `simulation-spec.schema.json`.

Supported numeric parameter kinds: `continuous`, `integer`. Roles: `geometry`, `condition`, `material`, `other`. Constraints: `le`, `lt` and positive-denominator `ratio` for two variables with exactly matching unit strings. More sophisticated dimensional relations, nonlinear equations, derived parameters, geometric topology checks, materials and physics feasibility must be reviewed externally. Unit equality is only string comparison; automatic conversion is absent.

## Offline workflows

```bash
python -m server.simulation_dataset plan --spec design.json --count 20 --output-root /my/workspace
python -m server.simulation_dataset record --plan /my/workspace/simulation-datasets/microchannel-<id>/plan.json --case-id case-00001 --evidence observed.json --output-root /my/workspace
python -m unittest tests.test_simulation_dataset
```

MCP interfaces:
- `simulation_dataset_plan(spec_path, count)`
- `simulation_dataset_record(plan_path, case_id, evidence_path)`

Both use `COMSOL_OUTPUT_ROOT`, are available in read-only reviewer mode, and do **not** start a COMSOL session. Each plan is saved to a unique directory with its source-file digest. Results become independent outcome-review JSON records with input digests; neither the plan nor source evidence is overwritten.

`plan` uses a **seeded randomized Latin hypercube**, with bounded rejection and redraw under constraints. It is **not optimized LHS** and constrained rejection may damage global space-filling properties; the report records rejection counts and flags this. Integer bins can repeat when integer levels are fewer than samples. Split labels are assigned at the **case level** using specified fractions: they do not prove statistical independence. If derived samples or multiple geometries share a common origin, independently enforce grouping to prevent leakage. OOD examples are **NOT_GENERATED** by this release.

## Reported outcomes and failure taxonomy

Example `observed.json` (reported, never authenticated by this module):

```json
{
  "outcome": "REPORTED_FAILURE",
  "run_id": "trial1",
  "evidence_ref": "COMSOL log stored in authorized workspace",
  "observables": {},
  "failure_category": "MESH",
  "failure_stage": "mesh_build"
}
```

Recognized categories: `GEOMETRY`, `MESH`, `BOUNDARY_PHYSICS`, `COUPLING`, `SOLVER`, `LICENSE`, `RESOURCE`, `DATA_EXPORT`, `UNKNOWN`. The operator supplies these categories from actual evidence. A solver error alone is NOT proof of mesh root cause.

Reported success may include numerical observations, each with exact declared units and its own `evidence_ref`; mismatched units are blocked, not auto-converted. `NOT_RUN` cannot contain numerical observations. Reports keep `verified_execution: NOT_RUN`, `scientific_status: NOT_RUN`, `dataset_ready: false` and explicit per-observable `NOT_RUN` gates. Receiving a caller-provided result does not establish an authenticated solve, conservation, mesh independence, or publication-ready data. Later versions may bind the manifest to fresh run/revision/solver/dataset identities and actual validation gate evidence.

## Scope and limits

Maximum 500 cases and 32 parameters; bounded input JSON and generated files. The planner is single-process and has no queueing, scheduling, COMSOL export, solver control, data-driven correction or automated batch retry. It cannot independently authenticate source SHA strings supplied in design specs. No training data are published by this feature. Synthetic Python tests do not establish COMSOL scientific validity.

**Future potential:** authorized COMSOL case dispatcher, run metadata verification, artifact hashes, per-observable actual convergence gates, multi-level mesh studies, OOD holdouts, intelligent mesh strategy and retained failure datasets. These are explicitly NOT_IMPLEMENTED in v0.7.3.
