# Filled task-card example — COMSOL conduction reconstruction

**Illustrative training example, not a published paper and not an executed simulation.** Supply this card together with the full `prompts/paper-reproduction-task.md`; the card alone is not a replacement policy.

- Solver: COMSOL, via the simulation machine's configured COMSOL MCP. Discover actual version/modules/session before modeling; do not launch Fluent. No machine connection or launch authorization is asserted by this example.
- Source: analytical constant-property one-dimensional conduction benchmark. Reference derivation, not claimed paper data: L=0.01 m, A=0.0001 m², k=10 W/(m K), end temperatures 310 K/300 K, insulated lateral walls. Q=k A ΔT/L=1 W; midpoint T=305 K.
- Scope: stationary solid heat transfer, rectangular prism 0.01 ×0.01 ×0.01 m, explicit constant conductivity; no convection/radiation. Conditional model replaces any unresolved material identity with the stated constant k and labels it an assumed benchmark material.
- Output: a new `conduction-reconstruction` directory under the configured output root; never overwrite input models.
- Main reference quantity: integrated axial heat rate Q in W, both end sections with sign convention documented, reference magnitude1 W. Primary comparison Q error <15%. Midpoint temperature is supplementary diagnostic, not an extra acceptance criterion.
- Conservation: stationary inward plus outward heat rate zero with no volumetric source/storage. Normalize absolute imbalance by1 W; example engineering tolerance <1%, predeclared for this simple benchmark, not universal.
- Mesh: two meaningfully refined meshes with at least twice the axial subdivisions, compare Q; example sensitivity target <2%. Report two-grid sensitivity only. If unmet, use third mesh within budget or report incomplete. Time step: not applicable (stationary).
- Native convergence: retain actual configured stopping test and observed reason; no extra residual floor. Record warnings and native flux definitions.
- Budget proposal for an operator to authorize: ≤3 solves, ≤2 reversible repair rounds, ≤30 minutes, ≤4 cores and8 GB. If unsuitable for the discovered host, revise before running.
- Declared necessary checks: numerical (actual native convergence), scientific (conservation and mesh sensitivity), reopen (saved-model readback and Q). Required check results and actual evidence paths must be attached; do not prefill PASS.
- Expected reconstruction type: conditional analytical benchmark. All execution/check results initially NOT_RUN.

Example controller comparison contract (a project input, not a skill default):

```json
{"acceptance_spec":{"required_checks":["numerical","scientific","reopen"],"criteria":[{"id":"case1:Q","metric":"relative_error","reference":1.0,"tolerance":0.15,"unit":"W"}]}}
```

## Same prompt, Fluent selection

Reuse the full `prompts/paper-reproduction-task.md` without a second acceptance policy. Change only the task card solver line, for example:

- Solver: Fluent, via the simulation machine's configured official PyFluent MCP. Discover actual version/session before modeling; do not launch COMSOL.
- Keep the same metric IDs, relative-error `<15%` (or an explicit override), conservation and two-grid sensitivity definitions, budgets and `acceptance_spec` shape.
- Route Fluent native reports for fluxes/residuals; still report execution, checks and paper agreement separately.

Do not maintain a Fluent-only acceptance document. For a real paper replace the analytical source and task quantities with verified paper-specific inputs and locations. Do not relabel this example as real-COMSOL or real-Fluent testing evidence.
