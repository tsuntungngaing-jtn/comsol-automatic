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
