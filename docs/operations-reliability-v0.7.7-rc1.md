# COMSOL operations reliability — v0.7.7-rc1 (candidate, not released)

This candidate is based on 0.7.6 main. The reports come from the user's
LAB7/8, P010/P011 and P031 incident notes; numerical details are *reported*,
not verified against raw solver logs or native case files.

## Existing coverage audited

- \`server/workflow_state.py\`: persistent named states and legal transitions,
  but writes JSON directly; it does not implement a cross-chat single writer.
- \`server/scientific_gates.py\`: check solution identity, conservation,
  residual plateau and cross-run comparison, but the evidence is supplied
  by callers and does not authenticate solver-side measurements.
- \`server/recovery_harness.py\`: version 0.7.5 knowledge contracts and
  bounded proposals but no execution connection.
- \`docs/persist-hard-gate.md\`: pre-solve and post-solve native MPH
  checkpoints are required; users must not conflate solve-complete and saved.
- \`server/main.py\`: active studies cannot be force-cancelled through the
  exposed job cancellation tool. Do not claim a request stopped a job.
- Source precedence (0.7.6): original article explicit text/table beats
  inferred schematic dimensions; preserve source disagreements.

## Failure-to-guard map (historical record, NOT independent log verification)

| Incident | Prior evidence | Implemented offline guard | Unknown |
|---|---|---|---|
| P031 heating study with cooling-effective BC | Reported ~2 h wasted, heater zero | \`effective_case_check\` compares expected physics against reported actual readback, not study label | Real readback integration not built |
| P031 invented 1e-6 K startup threshold | Reported 4.61e-5 K difference triggered extra solve | \`threshold_audit\` requires source/category/unit; diagnostic-only hard gates rejected | Physical relevance of any genuine threshold |
| 32 GiB / 4 core mesh runs | Reported 0.2 mm 8.03M DOF/26.13 GiB/4.5 h; 0.3 mm 2.56M DOF/12.26 GiB/47.5 min | \`resource_check\` requires >=2 same host+physics baselines, exposes linear DOF screen | Predictive RAM accuracy, swap/pagefile and live memory telemetry |
| P031 long assembly / step collapse | Reported hours per 30s cooling simulation | \`progress_review\` flags no accepted step or time advancement after operator-defined window; never stops solver | Root cause and real step collection |
| MPh node label / dataset alias | Reported slash-containing dataset labels and stale tracked model | \`identity_check\` binds expected vs reported run, revision, parameter hash, mesh/study/solver; post-solve also solution/dataset/artifact hash | Authenticity of solver-side hashes |
| Concurrent chat/timer control, stale job state | Reported old rounds and unknown statuses | \`TaskLease\` adds local exclusive owner, operation idempotency, atomic state file write/readback | Network FS semantics; runtime/inventory integration |
| P011 Chai Re200 reference case vs main paper | Reported scope conflation | \`reproduction_gate\` cannot mark main-paper pass without main paper claims | Full dashboard/queue integration |
| LAB7/8 on PyFluent | Reported existing vendor-native backend | No COMSOL SDK import in guards; reuse through ComsoFlent host route | Actual Fluent MCP bridge |

## Operator runbook

1. Acquire an exclusive task ownership lease only on a private **local**
   workspace; inspect a pre-existing lease manually, never steal/delete it.
2. Identify active solver from actual MCP host, device assignment, task
   record and project scope. LAB7/8 uses the configured Fluent path;
   LAB9/10 uses COMSOL. Never register COMSOL MCP into Fluent jobs implicitly.
3. Freeze original paper claims with conditions, definitions, units,
   source reference and the **user-declared** acceptance policy. Original
   text and tables take precedence over schematic pixel measurements.
4. Resolve installed licensed vendor API. Before solve, record run identity,
   actual effective source terms, boundary/selection tags, materials,
   initialization, study/time configuration and resolved solver settings.
   An observed mismatch blocks submission. A study named \`heating\` does
   not imply positive heat input.
5. \`threshold_audit\`: distinguish PAPER / SOLVER / ENGINEERING /
   DIAGNOSTIC; source provenance and physical meaning must be auditable;
   an exploratory threshold is never a paper reproduction hard gate.
6. Resource budget: DOF, available RAM, realistic pagefile/commit, measured
   same-physics baselines, cores, peak RAM, and max authorized budget.
   Linear DOF screening is **heuristic** and must not be sold as an upper
   bound. Unknown resource proof requires review rather than a solve.
7. Freeze one hypothesis, prediction, disconfirming condition, cost,
   time/iteration limits and stop plan per experiment. First analyze saved
   outputs, then one-factor bounded tests. Do not repeat falsified tweaks.
8. Save \`*_pre.mph\`; test a short window; save \`*_solved.mph\` before
   post-processing; independently reopen, verify exact model/run/dataset
   identities, then consider extending. Each expensive metric should have
   its own checkpoint, not one giant blocking MCP call.
9. Observe accepted steps, wall time, failures, residuals, memory and
   physical observables. An alarm is NOT an implemented cancellation:
   only authenticated vendor-supported cancellation may be used.
10. Report execution, numerical validity, comparison and scientific
    validity separately. A 15% relative error policy is **not universal**;
    if selected by the user's project, record its source, comparison
    definition, denominator and applicable claims. Strictly less-than,
    not less-than-or-equal, when contract says \`<15%\`.
11. An unresolved queued/running/unknown job MUST be reconciled before
    any repeat submission. User skips = scope change, NOT validation PASS.
    Claim success is contingent on independent artifacts, conservation,
    mesh/refinement, reopen and the actual main-paper claims.

## Offline API and sample invocation

\`python -m server.reproduction_guard preflight snapshot.json\`:
runs a **caller-supplied** effective-case and provenance review, does not
attach or call COMSOL. Separate commands: \`progress\` and \`acceptance\`.

\`TaskLease(workspace, case_id).acquire(owner)\` reserves a local workflow
owner. \`record(owner, expected_revision, operation_id, stage=..., job_id=...)\`
guards duplicate actions and atomically saves and reads back state. A
returned SUBMISSION_UNVERIFIED is not proof of a scheduler job.

## Tests

\`python -m unittest tests.test_reproduction_guard -v\`

\`python -m unittest discover -s tests -v\`

Synthetic cases include P031 heating/cooling mismatch, invented threshold,
resource overrun, stalled accepted steps, stale dataset, duplicate submit
and a Chai Re200-only completion attempt. **Tests are authored, NOT_RUN
against the target machines.** No real solver, physical certification,
runtime acceleration measurements or automatic task/dashboards changes.

## Outstanding P0/P1

1. Integrate authenticated, vendor API native effective-physics readback
   and study/solution artifact identity acquisition.
2. Implement real safe job leases across all controlling chat/task
   processes; reconcile expired/unknown jobs, reconnect without force
   killing and verify Windows local filesystem semantics.
3. Connect resource and progress probes to live COMSOL/Fluent sessions;
   add authorized short-window and reopen checks.
4. Verify conservation budgets: enthalpy/reference enthalpy, pressure
   work, advection, storage, source, heat flux and area units, including
   wall treatment. A near-zero built-in diagnostic alone is insufficient.
5. Implement provenance-preserving dashboard write-and-readback and
   device queue claim rules. Do not auto-take the next paper from a table.
6. Measure recovery time, duplicate submissions, invalid run time,
   peak memory, save/reopen rate, continuation rate, and false PASS.

## References

- COMSOL KB 1030, Out of Memory: https://www.comsol.com/support/knowledgebase/1030
- COMSOL KB 1262, Improving Convergence of Transient Models:
  https://www.comsol.com/support/knowledgebase/1262
- Eca & Hoekstra (2014), Numerical uncertainty based on grid refinement,
  Journal of Computational Physics: https://doi.org/10.1016/j.jcp.2014.01.006
- ASME V&V 20, Verification and Validation in Computational Fluid Dynamics
  and Heat Transfer: https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty
- Official PyFluent MCP: https://github.com/ansys/pyfluent-mcp

Do not make unsupported source assertions or claim these works prove a
particular reported run's numerical root cause.
