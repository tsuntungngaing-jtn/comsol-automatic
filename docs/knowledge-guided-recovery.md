# Knowledge-Guided Diagnosis & Recovery Harness — v0.7.5

Inspired by *Delegating Earth science model calibration to knowledge-guided LLM agents* (GCH, arXiv:2610.18378), this is a **small, offline GCH-inspired contract and evidence layer** on top of v0.7.4's hypothesis reviews. It does not implement GCH's LLM planning, a numerical optimization algorithm, automated COMSOL/Fluent execution, causal proof or repair application.

**Status:** deterministic synthetic software tests exist; real commercial-solver diagnosis, parameter bindings, physical correction and end-to-end scientific verification are **NOT_RUN**.

## Separation of responsibilities

- **Agent/operator (offline)**: formulate a reviewed contract from knowledge, model API readbacks, provenance, parameter roles and observable definitions. Formulate competing falsifiable hypotheses using v0.7.4.
- **Harness (implemented here)**: freeze the contract by content hash, review *reported* parameter readback and observable availability, allow only one predeclared calibratable parameter in a proposed change, score *reported* candidate observables against the original frozen objectives and per-observable gates.
- **Numerical engines (not implemented here)**: execute actual COMSOL via authorized MCP, or Fluent via an independently configured official PyFluent adapter. Neither engine is invoked by these offline tools.
- **Independent assessment (required externally)**: authenticate model/solution/dataset identity and source artifacts, recompute residual/conservation/mesh checks, compare independent observations, and replay after saving/reloading. Never claim achieved in this release.

The declarations for COMSOL/MCP and Fluent/PyFluent identify *intended* backend only; no PyFluent connector is supplied or installed. Do not use screenshots, GUI clicks, OCR or unofficial code execution to control commercial software.

## Four new read-only/offline MCP tools

1. \`recovery_contract_freeze(contract_path)\` — validate an explicit model/observable contract, store its frozen canonical hash, status \`FROZEN_UNCOMMISSIONED\`.
2. \`recovery_commission(contract_path, evidence_path)\` — check *caller-reported* readbacks and observable availability against the exact frozen baseline; statuses \`REPORTED_COMMISSIONING_PASS\`, \`REPORTED_COMMISSIONING_FAIL\` or \`REPORTED_COMMISSIONING_INCOMPLETE\`.
3. \`recovery_propose(contract_path, commissioning_path, diagnostic_path, change_path)\` — require reported commissioning and a supporting (not causally confirmed) v0.7.4 diagnosis; propose exactly one **calibratable** parameter change. Fixed paper parameters cannot be changed. Output is \`PROPOSED_ONLY\`, \`repair_authorized=false\`.
4. \`recovery_assess(contract_path, proposal_path, evidence_path)\` — compare a distinct, externally reported candidate run with precommitted tolerances and separate gates for every declared observable; status may be \`REPORTED_CRITERIA_MET_NEEDS_VERIFICATION\`, **never** a scientifically verified PASS.

All file paths resolve inside \`COMSOL_OUTPUT_ROOT\`. Each output gets a new UUID-scoped JSON file under \`recovery-harness/{freeze,commission,propose,assess}/\`. Frozen content and input-file digest are recorded; inputs are never overwritten. The module does not modify an MPH file, solver parameters, an RSI policy, a scientific gate, or an existing research record.

## Minimal frozen contract

The example values and SHA-256 strings below are **synthetic placeholders** and are not valid real research provenance. Before actual research, source digests, model API names, parameter effects and observable expressions need independent verification.

\`\`\`json
{
  "schema": "recovery-harness/0.7.5",
  "case_id": "microchannel",
  "software": {
    "name": "COMSOL",
    "version": "6.4",
    "interface": "MCP",
    "knowledge_ref": "installed COMSOL documentation and approved readbacks"
  },
  "baseline": {
    "run_id": "run_A",
    "model_revision": "rev0",
    "spec_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "model_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "source_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "parameters": [
    {
      "name": "inlet_width", "binding": "verified-model-inlet-width",
      "unit": "mm", "expected": 0.6, "tolerance": 0.01,
      "role": "fixed", "evidence_ref": "reviewed-paper-spec"
    },
    {
      "name": "heat_coeff", "binding": "verified-heat-transfer-coefficient",
      "unit": "W/(m2*K)", "expected": 150, "tolerance": 5,
      "role": "calibratable", "evidence_ref": "reviewed-inferred-range"
    }
  ],
  "observables": [
    {
      "name": "pressure_drop", "expression": "verified-pressure-drop-expression",
      "selection": "inlet-outlet", "unit": "Pa", "reference": 100,
      "abs_tolerance": 10,
      "required_gates": ["convergence", "conservation", "mesh_independence"]
    },
    {
      "name": "max_temperature", "expression": "verified-temperature-expression",
      "selection": "channel", "unit": "K", "reference": 315,
      "abs_tolerance": 2,
      "required_gates": ["convergence", "physics_consistency"]
    }
  ]
}
\`\`\`

A frozen contract is **not** an executable COMSOL model or a guarantee that listed bindings/units are true. All recorded readbacks and validation flags are caller declarations. Numeric comparisons use exact declared unit strings and a predeclared **absolute** tolerance (no implicit unit conversion). A complete physical study may require additional checks and conditions outside this deliberately narrow schema. No separate calibration dataset, cross-validation or optimizer is implemented.

### Commissioning evidence

Record the original frozen contract SHA, exact baseline run/model/spec/model hashes, \`source_ref\` and \`source_sha256\`, a \`readbacks\` object (each parameter has \`value\`, \`unit\`, \`binding\`) and \`available_observables\` names. All required readbacks must be supplied and within tolerance for a reported commissioning PASS. The tool **does not** independently verify that a parameter affects the geometry or physics; perturbation/sensitivity and reference replay are future tasks.

### Recovery proposal

Use a v0.7.4 diagnosis **report** with \`REPORTED_TEST_SUPPORTS_PREDICTION\`, \`root_cause_confirmed=false\`, \`scientific_status=NOT_RUN\`, \`repair_authorized=false\`. This is a provisional proposal, not authentication of the v0.7.4 evidence. The change document must have exactly:

\`\`\`json
{
  "parameter": "heat_coeff",
  "new_value": 175,
  "unit": "W/(m2*K)",
  "rationale": "Investigate sensitivity to a reviewed coefficient",
  "expected_effect": "Reduce temperature deviation without degrading other KPIs",
  "authorization_required": true
}
\`\`\`

The tool does not execute the proposed change. Any real mutation/solve requires separate current user authorization and the existing COMSOL MCP controls.

### Candidate assessment

An external candidate-evidence JSON declares the exact \`contract_sha256\`, baseline/candidate run IDs (distinct), a new candidate model revision, original \`spec_hash\`, actual authorization and evidence references, source SHA-256, and an observable map such as:

\`\`\`json
{
  "contract_sha256": "<frozen contract hash>",
  "baseline_run_id": "run_A",
  "candidate_run_id": "run_B",
  "candidate_model_revision": "rev1",
  "spec_hash": "<original spec hash>",
  "authorization_ref": "approved external operation record",
  "source_ref": "actual candidate result record",
  "source_sha256": "<actual result file hash>",
  "values": {
    "pressure_drop": {
      "value": 105, "unit": "Pa",
      "reported_gates": {
        "convergence": "PASS", "conservation": "PASS",
        "mesh_independence": "PASS"
      }
    },
    "max_temperature": {
      "value": 315.5, "unit": "K",
      "reported_gates": {
        "convergence": "PASS", "physics_consistency": "PASS"
      }
    }
  }
}
\`\`\`

The \`<...>\` values are placeholders, not working SHA-256 strings. All declared observables and gates must be reported for the criteria to be recorded as met. The module does **not** authenticate the source evidence or recompute the gate results: they remain reported claims, not scientific PASS. Outputs always set \`candidate_accepted=false\`, \`verified_execution=NOT_RUN\`, \`scientific_status=NOT_RUN\`, \`independent_validation=NOT_RUN\`, \`root_cause_confirmed=false\`.

## Software verification and next research stage

Run the synthetic offline tests with:

\`\`\`bash
python -m unittest tests.test_recovery_harness -v
\`\`\`

The stronger next step is to implement **trusted MCP commissioning acquisition** with actual parameter readback and observable result identity, test whether parameters affect the expected model parts, connect a deterministic numerical optimizer with a frozen evaluation function, and independently rerun candidate solutions. Benchmark injected failures by diagnosis accuracy, incorrect repairs, additional computation and physical validation. None of these are claims of v0.7.5.
