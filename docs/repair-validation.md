# Repair validation record — 2026-10-12

Status: **PASS_WITH_GAPS for the repaired release scope**, not universal physical validation. The original pinned submission failed its audit; this is a separate modified derivative.

## Executed checks

- COMSOL 6.4 build 293 through MCP; Heat Transfer, CFD and basic Material Library available.
- Patched convection shortcut: six HeatFluxBoundary nodes with ConvectiveHeatFlux subtype; Copper imported from the local library; repeat binding succeeds. A 10 mm cube with 0.1 W total heat gives 0.10000000000365551 W outward flux, relative imbalance 3.66e-11, and average surface temperature 309.8166666672613 K. No model problems were returned.
- Patched k-epsilon shortcut: missing intensity/length inputs rejected before boundary creation; complete inputs accepted and read back as U0in=2 m/s, IT=0.05, LT=0.007 m. Material Library Air is used. The two-dimensional 1 m by 0.1 m channel gives signed inlet/outlet mass flux -0.2408635148510873 / +0.24086351485108734 kg/(m s), relative imbalance 1.15e-16. k and epsilon minima are positive; model problems are empty.
- Both repaired models were saved, loaded into separate tracked models and their derived values recomputed consistently, with distinct evaluation run IDs and file hashes in the external audit evidence.
- Laminar guard: TurbulenceModelType=None correctly distinguishes laminar flow even though an inactive keps parameter default exists. Laminar inlet/outlet setup succeeds without turbulence inputs.
- Empty existing material and unknown material mapping are rejected instead of reported configured. Water import produced a COMSOL object-renaming message; the strict shortcut returned failure pending inspection. After inspecting the imported material identifier and required properties, repeated binding succeeded with provenance explicitly marked existing, not newly imported. Import messages are not silently suppressed.
- Output tests executed the repaired Runtime wrapper and actual model/versioning functions with mock saves: root escapes and existing junction redirects rejected; root-contained ordinary saves accepted; same-second versions use distinct reserved paths and the first version remains unchanged.
- Python/unit/protocol suite: 38 tests passed. Localhost HTTP tests required NO_PROXY=127.0.0.1,localhost in this machine's proxy environment; this did not disable authentication assertions.
- Wheel built and installed with dependencies in a new isolated environment outside the source tree. MCP stdio initialization, tool enumeration and status succeeded; all 47 catalog entries and bundled vendor resources were available. No COMSOL session was started by that wheel protocol probe.
- Skill frontmatter validator passed. The final archive is source-only and English operational documentation; inherited license texts and proper-name provenance are retained.

## Changes

`vendor/installed-mcp/src/tools/physics.py`: current convection subtype; U0in; explicit 6.4 k-epsilon inputs; laminar/turbulence distinction; real verified material imports and repeat lookup; refusal of incomplete materials; corrected interactive guidance.

`server/runtime.py`, `vendor/installed-mcp/src/utils/versioning.py`: containment for version saves, strict plain model names, UUID plus exclusive reservation, preserved labels, and a user-home output default outside installed source. Set COMSOL_OUTPUT_ROOT explicitly for research projects. Latest intentionally updates; failed saves may leave an empty reserved historical attempt that must not be treated as a model.

`setup.py`, `MANIFEST.in`, `pyproject.toml`: wheel resource bundling and version 0.1.1. `server/runtime.py` locates bundled resources from installed wheels. `scripts/release.py` produces the new side-by-side English folder and rejects CSV/PNG result files as well as proprietary model files. Historical vendor provenance remains separately available.

SKILL.md, root README, docs, runtime instructions, catalog metadata and corrected embedded prompts are English. Case IDs and local Library paths are retained; inherited validation claims are not carried forward. COMSOL's raw diagnostic language still follows the user's installed COMSOL language.

## Not run / remaining limits

- No blanket audit of all inherited physics tools, all dynamic settings, modules or versions. Flow shortcut support is deliberately limited to checked 6.4 single-phase laminar/k-epsilon contexts.
- No full official Library re-solve, grid-convergence/wall-treatment certification, or stricter simultaneous solution-and-residual stopping-rule study. The default segregated solver can terminate using solution error; small linear residuals and mass balance do not prove nonlinear or discretization accuracy.
- No full original heat-sink transient regression or time-point energy audit, no k-omega/SST/LES or nonisothermal turbulent coupling certification, and no HPC execution.
- Existing directory junctions were tested. Adversarial filesystem races, network shares and arbitrary-code security are not covered; trusted MCP code execution is not a sandbox.
- No installation over an existing skill, connector replacement, publication, or upload was performed.

Formal research use remains conditional on validation appropriate to each scientific claim. Keep the full external audit report and raw evidence outside the distributable skill.
