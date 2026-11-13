# Current validation scope — 0.2.0

Read [geometry validation results](geometry-validation-results.md) for this extension, based on a012b21bcfd604adb8843f3b0e734478fc13b4a3. Software, geometry, physics and scientific conclusions are separate; no blanket certification is claimed.

# Validation scope — 2026-10-12
Base commit: ef476da8c14cc73662b7c8aad7d091e9d641ba9c. The initial audit on COMSOL 6.4 build 293 reproduced rejected ConvectiveHeatFlux creation, rejected inlet U0, an empty-material success/warning, repeated-material failure, version-save junction escape, same-second collision and missing wheel resources. This repair release targets those findings.

Real COMSOL tests must use MCP. Python tests and wheel protocol discovery cannot establish physical validity. The upstream general physics, chemistry, acoustics, structural, transient coupling and HPC paths are not comprehensively validated. Original heat_sink_3d is legacy teaching source with explicit constant aluminum properties, not a verified 6.4 turbulent conjugate-heat-transfer case.

Read [the repair validation record](repair-validation.md) for executed tests. Never claim blanket scientific certification. Formal studies still require appropriate mesh/wall treatment, conservation, residual criteria, material ranges, boundary justification and independently reproduced observables.

## v0.7.1 mesh-aware diagnostics

The offline input validator and cross-mesh interpolation tests are synthetic only. Real COMSOL mesh export, nodal result alignment, genuine mesh convergence studies and physical validation are **NOT_RUN**. A `DIAGNOSTIC_ONLY` result must never be upgraded to Scientific PASS without independent physical evidence. See [mesh-native diagnostics](mesh-native-diagnostics.md).

## v0.7.2 adaptive scientific figure analysis

The adaptive configuration router applies deterministic uncalibrated coverage/match-fraction proxies to a fixed scientific figure and explicitly abstains on weak or near-tied scores. Its performance on real published figures, empirical accuracy calibration and downstream COMSOL physical correctness are **NOT_RUN**. Candidate selection is not independently validated paper evidence.

## v0.7.3 simulation dataset and DoE foundation

An offline seeded randomized LHS planner, typed parameter/constraint schema, per-observable NOT_RUN placeholders, and caller-reported immutable outcome reviews are implemented. Local synthetic planner/unit tests were executed; real COMSOL batch simulation, mesh studies, authentic solve identity, physics validation, data-based agent learning and independent scientific benchmarks are **NOT_RUN**. Reports are not treated as verified physical data.

## v0.7.4 physical diagnostic hypothesis planning

Implemented only a deterministic offline schema review, cost-tiered proposed experiments, externally reported observation comparison against predeclared rules, and UUID-scoped provenance reports. Synthetic tests exist and were run for the development module. No COMSOL solver launched; genuine model readbacks, root-cause identification accuracy, physical revalidation, causal attribution, or automatic repair remain **NOT_RUN**. Reported test agreement is never converted to physical PASS or confirmed cause. See [physics diagnostic hypotheses](physics-diagnostic-hypotheses.md).

## v0.7.5 GCH-inspired commissioning and recovery contracts

New offline recovery harness: frozen canonical contract hashes, caller-reported parameter readback checks, one-calibratable-parameter change proposals and frozen per-observable comparison reports. Development-copy synthetic unit tests passed; GitHub/installed-package end-to-end tests, trusted COMSOL/Fluent commissioning, physical solver runs, independent artifact verification, scientific repair validation and true GCH optimization are **NOT_RUN/NOT_IMPLEMENTED**. The harness never accepts a candidate or confirms root cause on reported claims alone. See [knowledge-guided recovery](knowledge-guided-recovery.md).

## v0.7.6 paper-first evidence precedence and authoritative supplementation

Implemented deterministic offline source ranking, original-author supplement distinction, operator-declared external-source metadata/applicability gates, and direct-paper-over-pixel/assumption blocking inside existing input intake. Synthetic software test cases were authored. Full repository suite and independent verification against actual DOI/author supplementary/source files, scientific result validation and COMSOL execution: **NOT_RUN**. No numeric evidence is automatically admitted and no authority claims are authenticated by the tool. See [authoritative source precedence](authoritative-source-precedence.md).
