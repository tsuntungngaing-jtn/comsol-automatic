# Validation scope — 2026-10-12
Base commit: ef476da8c14cc73662b7c8aad7d091e9d641ba9c. The initial audit on COMSOL 6.4 build 293 reproduced rejected ConvectiveHeatFlux creation, rejected inlet U0, an empty-material success/warning, repeated-material failure, version-save junction escape, same-second collision and missing wheel resources. This repair release targets those findings.

Real COMSOL tests must use MCP. Python tests and wheel protocol discovery cannot establish physical validity. The upstream general physics, chemistry, acoustics, structural, transient coupling and HPC paths are not comprehensively validated. Original heat_sink_3d is legacy teaching source with explicit constant aluminum properties, not a verified 6.4 turbulent conjugate-heat-transfer case.

Read [the repair validation record](repair-validation.md) for executed tests. Never claim blanket scientific certification. Formal studies still require appropriate mesh/wall treatment, conservation, residual criteria, material ranges, boundary justification and independently reproduced observables.
