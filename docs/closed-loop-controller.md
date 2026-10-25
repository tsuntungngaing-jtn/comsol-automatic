# Closed-loop controller

Status: **implemented** for deterministic Python state/provenance; **tested_with_mock**; **NOT_RUN** on real COMSOL. No extra agents.

Literature tags:

| Mechanism | Basis | Support class |
|---|---|---|
| Paper → structured resources → tests → repair | Miao et al., Nature 2026, 10.1038/s41586-026-11044-y | LITERATURE_ADAPTED |
| Supervisory discrete-event control | Ramadge & Wonham, SIAM J. Control Optim. 1987, 10.1137/0325013 | LITERATURE_ADAPTED (not a COMSOL paper) |
| Provenance graph Evidence→Spec→Model→Run→Observation→Validation | Huber et al., Scientific Data 2020, 10.1038/s41597-020-00638-4 | LITERATURE_ADAPTED |
| Constrained NL → deterministic gates → solver | Upadhyay & Reinhart, arXiv:2606.10928 | LITERATURE_ADAPTED |
| Execution ≠ physical correctness | Oefner et al. 2021; FEABench arXiv:2504.06260; ChatCFD | LITERATURE_SUPPORTED |
| Diagnose → repair → retest | Bhat et al. RESCORE arXiv:2604.04324; Shi & Zhang arXiv:2609.03718 | LITERATURE_ADAPTED |
| One-change isolation | Zeller & Hildebrandt, IEEE TSE 2002 | LITERATURE_ADAPTED |
| Exact state names, rollback table, MPH reopen | this repository | DESIGN_POLICY |
| Thin orchestrator, not six agents | Shi & Zhang arXiv:2609.03718 | LITERATURE_SUPPORTED |

## Architecture

LLM: extract, propose, diagnose, choose existing MCP tools.  
Deterministic layer (`server/orchestrator.py`, `workflow_state.py`, `contracts.py`, `scientific_gates.py`): schema, admission, transitions, revisions, PASS/FAIL.  
COMSOL via existing MCP only.

## States

`NEW` → `EVIDENCE_INTAKE` → `SPEC_COMPILATION` → `MODEL_BUILD` → `PRECHECK` → `SOLVE_READY` → `SOLVING` → `VALIDATION` → `REOPEN_VERIFY` → `DELIVERY_READY` → `PASS`

Also: `WAITING_FOR_USER`, `DIAGNOSIS`, `REPAIR_READY`, `REPAIRING`, `FAIL`, `BLOCKED`, `BUDGET_EXHAUSTED`, `CALIBRATED_NOT_INDEPENDENTLY_VALIDATED`.

`WAITING_FOR_USER` cannot enter `SOLVING`. `FAIL` cannot enter `DELIVERY_READY`. State JSON is persisted under `{COMSOL_OUTPUT_ROOT}/workflow-cases/`, including `evidence_records` (origin/certainty) and `spec`. Restart reloads those records; it does not re-run COMSOL or mark recovered jobs verified.

## Rollback (DESIGN_POLICY)

| Failure | Next stage |
|---|---|
| stale result | SOLVE / freshness FAIL |
| geometry or selection contract | MODEL_BUILD / PRECHECK |
| wrong BC interpretation | SPEC_COMPILATION (epistemic → user) |
| missing source | EVIDENCE_INTAKE |
| high-impact assumption | WAITING_FOR_USER |
| numerical solver failure | DIAGNOSIS / REPAIR |

## Repair

Mechanical (tag/API/stale dataset): auto-admissible. Epistemic (geometry assumption, BC meaning, material source, constitutive model, fitting): `WAITING_FOR_USER`. Failed baseline immutable. Repair increments `model_revision` and invalidates dependent PASS.

## Calibration

Fitted origin stays `fitted`. Same claim cannot independently validate. Without hold-out: `CALIBRATED_NOT_INDEPENDENTLY_VALIDATED`, never `VALIDATED`.

## Validation semantics

Layers stay separate: api, geometry, selection, physics, numerical, scientific, reopen. Conservatively aggregate FAIL > BLOCKED > NOT_RUN > PASS. Missing required check is NOT_RUN, not PASS. Reopen not performed → `reopen=NOT_RUN`.

## Outer RSI layer (0.3.0)

Cross-task uncertainty-aware RSI (`rsi/`, `uncertainty/`) wraps this controller and does not change its state names. See [closed-loop-rsi-note.md](closed-loop-rsi-note.md) and [uncertainty-aware-rsi.md](uncertainty-aware-rsi.md).
