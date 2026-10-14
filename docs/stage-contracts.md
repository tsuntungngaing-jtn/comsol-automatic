# Stage contracts and solver safeguards

These six cards describe sequential responsibilities of the existing operator. They do not install agents or an orchestrator. Every handoff records case_id, run_id, stage, spec_hash, model_revision, input/output artifact paths and hashes, errors, events, next action, and checks invalidated by changes. Revision tracking is currently an operator contract, not a server-enforced single-writer lease.

## Evidence
1. Trigger: new source or changed interpretation.
2. Exclude: solving or filling missing paper values by guesswork.
3. Input: source hash and page/figure/table locator, experimental condition.
4. Output: value, units, source_certainty, value_origin, admissibility, conflicts and dependent tasks.
5. Tools: authorized document readers; no COMSOL mutation.
6. Loop/budget: count extraction attempts; stop on inaccessible evidence.
7. Handoff: preserve assumed/reconstructed labels; never promote them to paper facts.
8. Acceptance: missing bottom-plate thickness blocks thickness-dependent claims only.

## Specification
1. Trigger: evidence ready or changed.
2. Exclude: inferred universal linear parameter relationships.
3. Input: provenance and task requirements.
4. Output: simulation specification and explicit missing-information dependencies.
5. Tools: simulation_spec_validate, simulation_task_admit.
6. Loop/budget: bounded correction of schema errors; no solve.
7. Handoff: schema_status and dependency_status separately.
8. Acceptance: malformed physics fails; an independent geometry task can proceed.

## Model
1. Trigger: admitted construction or repair.
2. Exclude: unsupported API substitutions between COMSOL versions.
3. Input: immutable baseline and installed-version documentation.
4. Output: geometry/selection/physics readbacks, warnings and source hashes.
5. Tools: existing geometry, Inspector and checked-selection MCP tools.
6. Loop/budget: distinguish necessary builds from repair builds.
7. Handoff: every geometry change invalidates prior selection/physics/solution checks.
8. Acceptance: empty inlet or rotated device in the wrong position fails.

## Solver
1. Trigger: admitted configuration and idle JVM.
2. Exclude: forced process termination or queued speculative repair.
3. Input: DOFs, elements, quality, memory estimate, threads, linear/nonlinear settings and budgets.
4. Output: actual log, iteration groups, scaling, criteria, termination reason and solution identity.
5. Tools: asynchronous solve and nonblocking job/queue metadata.
6. Loop/budget: server submission caps apply; detailed build/repair accounting remains manual.
7. Handoff: manual Stop needs actual terminal/idle confirmation. Snapshot only afterward.
8. Acceptance: decreasing turbulence residual alone cannot clear a coupled residual plateau.

Record initialization_executed, state_verified and effect_tested separately. A snapshot should include a new MPH copy/hash, solver tree, real warnings/logs, materials, couplings, selections, mesh and dataset list. Do not promise intermediate solutions that were not saved. Capture variable-level contributions if available; otherwise mark unavailable. Preserve an immutable failed baseline before a one-change repair. Isothermal SST and fixed-flow heat studies are independent diagnostic copies, not validation of the coupled target.

## Validation
1. Trigger: newly completed solve with verified identity.
2. Exclude: old sol1/dataset reuse after a failed solve.
3. Input: run/revision/study/solver/solution/dataset/parameter identity and COMSOL derived integrals.
4. Output: separate convergence, conservation, mesh and scientific checks.
5. Tools: validation_gate and Inspector/evaluation tools after the JVM is idle.
6. Loop/budget: report executions, solves and elapsed time; no hidden criterion relaxation.
7. Handoff: missing prerequisites produce NOT_RUN/BLOCKED, not PASS.
8. Acceptance: B prepared but unsolved means A/B comparison NOT_RUN.

Declare every inlet/outlet/source/storage term, integral expression, selection, sign, unit, denominator and tolerance before conservation evaluation. Thresholds from the incident are case-specific. Mesh independence requires at least two individually converged/conservative levels with fixed physics/conditions and identical metric definitions. Predeclare relative-change denominator, temperature in kelvin versus temperature rise, and absolute tolerance near zero. This release does not automate the mesh-independence gate.

## Delivery
1. Trigger: validation report ready, including failures.
2. Exclude: unsupported paper-reproduction or speedup claims.
3. Input: report, fresh artifacts, hashes and limitations.
4. Output: editable MPH and explicitly scoped conclusions.
5. Tools: explicit-path save, independently tracked reopen and reevaluation.
6. Loop/budget: count reopening separately; do not silently re-solve.
7. Handoff: plot run/dataset, units, section, color limits and diagnostics-only labels.
8. Acceptance: failed fields cannot become publication evidence; A/B uses common plot scales.
