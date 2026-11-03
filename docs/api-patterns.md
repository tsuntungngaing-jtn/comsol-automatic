# Version-anchored API patterns
The following paths were exercised on COMSOL 6.4 build 293. On another build/version, inspect installed documentation and actual node properties before applying them. A matching method name alone does not establish matching equations.

## Solid convection
Create `HeatFluxBoundary`, then set `HeatFluxType=ConvectiveHeatFlux`, `h` in W/(m^2*K), and `Text` in K. Do not create a node with type ConvectiveHeatFlux. Use the geometry's boundary dimension and explicit selections. Integrate outward `ht.ntflux` for heat balance; confirm signs independently against prescribed sources. Source: https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_ht_features.09.065.html

## Single-phase k-epsilon flow
The verified interface is `TurbulentFlowkeps`; the turbulence property group reports `TurbulenceModel=keps` and `TurbulenceModelType=RANS`. Use `InletBoundary`, `BoundaryCondition=Velocity`, `U0in`; use `OutletBoundary` and `p0` for the pressure outlet. U0 is rejected in this context. Do not globally replace U0 in unrelated interfaces.

For a k-epsilon inlet, explicitly set `RANSVarOption=SpecifyTurbulentLengthScaleAndIntensity`, `IT_list=user_defined`, `IT` (dimensionless), `LT_list=user_defined`, and `LT` (length). The repaired shortcut requires both quantities. Other turbulence models and direct k/epsilon/omega inlet specifications require separate version-specific checks. Source: https://doc.comsol.com/6.4/doc/com.comsol.help.cfd/cfd_ug_fluidflow_single.06.032.html

5% intensity and 0.07 times channel width are suitable illustrative scales, not universal boundary data. Match a nearby official model and justify operating conditions. A tiny mass imbalance does not replace mesh, wall-function or nonlinear convergence checks. `segtermonres=auto` can terminate on solution error while residual estimates remain larger; inspect the actual stopping criterion and log.

## Discovering setters (Copy as Code)

When a property name is unknown, do not guess after the first API-shape error. Probe `properties()` on the live node, search installed documentation, or ask the engineer to use Desktop **Copy as Code to Clipboard** / Record Method and paste the setters into an MCP step. Apply through structured tools or opt-in `comsol_model_code`. Official API overview: https://www.comsol.com/support/learning-center/article/overview-of-the-comsol-api-107912

## Enum sweeps outside Parametric Sweep

Dropdown/enum interface options (for example Laminar Flow compressibility) may be cycled via API when UI Parametric Sweep cannot express them. Compare KPI, time, and iterations, but keep the physically justified setting—not the fastest spurious one. Bounded segregated/nonlinear tuning with KPI anti-cheat gates: [nonlinear-solver-tuning](nonlinear-solver-tuning.md).

## Material Library
Use `component.material().insert(local_library_path, [verified_material_tag])`. The basic library under the actual installation's data directory contains air, water,_liquid, copper and silicon. Read labels, property groups and dependencies. Use the material identifier, not necessarily its raw tag, in expressions. The repaired shortcut verifies required properties; existing materials are reported as existing, never falsely claimed newly imported.

## Output and identity
Set COMSOL_OUTPUT_ROOT explicitly. Regular and version saves must resolve destinations inside it, including junction/symlink targets. Model version labels must be plain names. History paths use a unique suffix and exclusive reservation; latest intentionally replaces the latest copy. A failed save can leave a reserved empty history file: treat it as a failed attempt, not a model. Reopen valid MPH files and evaluate again. Preserve the live model label around MPh save, which may change it.
