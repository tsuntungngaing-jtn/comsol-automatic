# Execution skill and task acceptance (candidate)

The canonical skill is `paper2simu/SKILL.md`. Root `SKILL.md`, `COMSOFLENT_SKILL.md` and `comsoflent/SKILL.md` only route to it. No inherited instruction chain reactivates historical paper acceptance rules. The full package is required; copying a router alone is insufficient.

The host supplies `prompts/paper-reproduction-task.md` as a **separate task input** when requesting paper reproduction. The Chinese prompt applies to either COMSOL or Fluent, with one solver selected per task. Its configurable default is strict paper-metric relative error <15%, not a default in skill code. Conservation, mesh and stability criteria are task-specific and predeclared. Existing calculation/diagnostic tools remain available on explicit request.

## Controller interface

`workflow_start(case_id, spec)` accepts execution information without acceptance thresholds. Modeling/solve calls still use the selected existing solver MCP; this controller persists caller reports and **does not call a solver or authenticate evidence**.

Optional `spec.acceptance_spec` contains:

```json
{
  "required_checks": ["numerical", "scientific"],
  "criteria": [
    {"id": "case1:temperature_rise", "metric": "relative_error",
     "reference": 20.0, "tolerance": 0.15, "unit": "K"}
  ]
}
```

Each ID identifies one metric in one condition. Every criterion is required. `metric` is `relative_error` or `absolute_error`; comparisons use strict `< tolerance`. No default tolerance is inserted. References/tolerances must be finite; relative comparison to zero is rejected. Near-zero policy, physical quantity meaning, reference provenance, averaging and sampling must be resolved in the task before constructing this contract. Units must match exactly; this tool does not convert units or align curves. Zero/near-zero values need an absolute-error criterion. Formula choice is part of the predeclared task, not posthoc fitting.

- `workflow_admit(case_id, task)` checks missing inputs affecting that task. A claim-validation gap does not block solve. Genuine missing solve inputs still block dependent work. `decision_resolve` records supplied values and origin; it does not relabel inference as paper evidence.
- `workflow_record_execution(case_id, run_id, status)` records an outcome under a unique run ID with current model/spec revisions. Status values: PASS (legacy), COMPLETED, SUCCESS, FAIL, BLOCKED, NOT_RUN, ABORTED, PARTIAL. COMPLETED is an execution report, not proof of native convergence. Keep native termination/log references in task artifacts and requested numerical checks.
- `workflow_submit_checks(case_id, layers, required)` records explicitly requested legacy layer statuses. Supported layers: api, geometry, selection, physics, numerical, scientific, reopen. These statuses remain caller-supplied. Preserve underlying raw diagnostics and evidence in artifacts. Optional mesh/conservation checks can be recorded under scientific with their individual reports; there is no built-in mesh or conservation threshold.
- `workflow_evaluate_acceptance(case_id, run_id, model_revision, spec_revision, observations)` compares `{id: {value, unit}}` to the explicit contract. Missing observations remain NOT_RUN; invalid units/values fail; old run/revision reports are STALE. Caller data is labeled `caller_supplied_unverified`.
- `workflow_deliver(case_id, artifacts)` records artifact metadata and returns independent `execution_status`, `check_status`, `paper_comparison_status`. It is callable for failed or partial work and does not change failure into PASS. Artifact paths are reports, not verified file existence or uploads.

Absent acceptance spec yields `paper_comparison_status=NOT_CONFIGURED`; configured but not compared yields NOT_RUN. Comparison PASS means only supplied metrics match the configured criteria. Final workflow PASS additionally requires current checks listed by `required_checks`. The controller cannot certify that a caller's PASS assertion is true. Use the task report to disclose conditional/calibrated reconstruction and incomplete evidence. Do not interpret workflow PASS as independent authentication or general physical validity.

Acceptance configuration is frozen at case start; use a new case for a revised contract and retain the old result. Existing legacy `validation_gate`, `simulation_spec_validate`, explicit validation/repair and RSI APIs retain their documented opt-in behavior; they are not a mandatory default pipeline. Generic contract schema validation and legacy geometry checks retain their original semantics. No changes are made to connectors, solver namespaces, live job ownership or source-file protections.

## Migration

1. Load the canonical execution skill through any supported entrypoint.
2. For execution only, supply a well-posed execution task and budget. Do not fabricate acceptance criteria.
3. For reproduction, copy the unified prompt, fill its task card and fix criteria before comparing results. Infer missing inputs as instructed, with provenance and sensitivity; block only dependencies that cannot be defined.
4. Pass optional comparison criteria explicitly to the controller. Attach actual logs/native data separately. Do not pass old datasets as current results.
5. Report execution, checks, paper agreement and reconstruction type separately. Missing final validation limits claims, not delivery of useful failed/conditional artifacts.

See `examples/paper-reproduction-task-example.md` for an illustrative filled COMSOL task. It is not a real paper result. Real COMSOL and Fluent verification of this separation is NOT_RUN until an authorized machine run supplies evidence. Retrieval benchmarks and RSI promotion are outside this change.
