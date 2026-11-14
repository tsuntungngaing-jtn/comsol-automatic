# Paper2Simu 0.2.1 candidate: conditional reconstruction, scientific states and independent RSI evaluation

Status: implementation candidate, **no live COMSOL / Fluent execution**. This document is scoped to the code review of the original main branch at 5533f605 and the subsequent isolated repair branch. No implied correction of existing saved scientific results.

## External technical basis

1. COMSOL 6.4 Heat Transfer, Inflow — the virtual upstream domain and Danckwerts enthalpy condition differ from strictly specified inlet boundary temperature. A paper's Tin value alone does not mandate an Inflow feature: https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_ht_features.09.070.html
2. COMSOL, Specifying the Temperature at a Flow Inlet — inlet BC choice depends on how temperature is physically prescribed: https://www.comsol.com/blogs/specifying-the-temperature-at-a-flow-inlet
3. NASA NPARC CFD Verification Assessment — examine iterative convergence, conservation/consistency, spatial and temporal convergence separately: https://www.grc.nasa.gov/www/wind/valid/tutorial/verassess.html
4. NIST AI RMF, Measure — benchmarks, uncertainty, independent review, repeatable evaluation and documentation: https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
5. ASME V&V 20, Verification and Validation in Computational Fluid Dynamics and Heat Transfer — assessment scoped to defined variables and model conditions.

These sources motivate policies, not proof of user case root causes or benchmark results.

## Distinguish four decisions

| Decision | Question | Blocking rule |
|---|---|---|
| Model preparation | Is any independent paper/source/geometry work possible? | Do not block independent work due to final verification gaps |
| Conditional modeling | Is at least one physically well-defined hypothesis plausible? | Source-tag the assumed case and authorize real solver use separately |
| Native execution | Did the selected solver actually terminate according to its configured criteria? | Explicit FAIL/BLOCKED/NOT_RUN keep their distinct meanings |
| Final scientific certification | Are specific claims independently supported by physics, numerical verification and actual paper comparisons? | Missing checks never imply PASS; inferred input limitations stay disclosed |

Scientific failure cannot be turned into CONDITIONAL simply because an inferred parameter is high impact. Execution BLOCKED cannot be relabeled FAIL. Unknown validation or missing required checks must not yield PASS.

The corrected controller separates requires_user from final_validation_blocked, while retaining conservative callback execution. For a final-validation blocker, **nondependent preparation and evidence gathering remain allowed**; arbitrary mutate/solve callbacks are NOT automatically authorized.

## CHT policy update

The previous checklist made three unwarranted universal requirements:
- exact NonIsothermalFlow node or no solve;
- universal Inflow(Tustr) default instead of an inlet Temperature condition;
- constant-cp enthalpy closure with 20% / 10% fixed acceptance limits.

The replacement is an evidence-based **functional** coupling and boundary audit. An energy deficit is a diagnostic requiring complete control-volume accounting, not automatically a coupling failure. The source-specific old ladder is historical experience, never a universal mandatory sequence.

## RSI policy update

Prior main RetentionGate could RETAIN arbitrary caller-provided positive metrics. Now favorable unverified scores yield REVIEW_REQUIRED and **never auto-promote**. A metric regression still yields REJECT. The registry's active version is left unchanged for a favorable candidate pending independent review.

A future trusted evaluator must verify, independently of policy candidate author:
- immutable evaluation dataset identity and split/holdout definitions;
- test methodology, metric definition and replayable results;
- held-out, cross-paper/geometry and failure-case comparisons;
- model/run IDs, solver provenance, source and artifact hashes;
- false PASS rate and **unnecessary-block rate** (not completing authorized well-posed tasks);
- cost, number of solver calls, false retries, actual time, numerical/physical outcomes;
- authorization and reviewer identity.

The existing offline code **cannot authenticate a human-entered source path or arbitrary metric dict**. Consequently, no automated RETAIN is implemented in this patch. PR #8 may be useful as a later source of retrieval/evaluation improvements but must be reviewed separately and not merged unchanged.

## Regression matrix

- Missing required checks: NOT_RUN, never PASS.
- Solver execution FAIL plus inferred input: FAIL.
- Execution BLOCKED: BLOCKED, distinct from FAIL.
- High impact inferred inputs with completed checks: CONDITIONAL.
- Critical unknown inputs: bounded modeling/sensitivity only, no definitive claim.
- Positive caller-only retention metrics: REVIEW_REQUIRED, active policy unchanged.
- Inferior retention metrics: REJECT.
- No real solver status or independent numerical verification is asserted.

## Next engineering work, not included in this commit

1. Implement native API readback of effective coupling, CHT energy/enthalpy terms and boundary selections; test version-specific COMSOL nodes.
2. Add a dependency-graph-based task planner so each missing input blocks only the jobs that actually need it. Keep user authorization and solver budgets.
3. Integrate approved retrieval via documented COMSOL material libraries, official model help and peer-reviewed same-physics papers, with source ranking and conflict disclosure.
4. Implement an independently authenticated held-out evaluator with reproducible evaluation report artifacts. Only then permit a separately authorized RSI promotion route.
5. Expand evaluation to unnecessary blocking rate, fraction of valid conditional cases completed, false PASS rate, job retries and solver cost, using frozen realistic cases.
6. Test original Simple Block, Laminar Channel and Heat Conduction in actual COMSOL; test Fluent separately under its own MCP session. No project paper reproduction PASS from this policy-only patch.

## Merge rule

Leave as DRAFT until offline CI passes, scope/compatibility reviewed, and operator has checked numerical implications. This patch corrects *logical* gates, not live model physics.
