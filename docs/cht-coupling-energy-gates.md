# CHT coupling and energy verification — conditional, evidence-based guidance

Status: supersedes previous universal CHT hard gates. COMSOL 6.4 implementation guidance, not a solver validation result. Do not change a running model merely to satisfy named nodes.

## Modeling versus certification

**Modeling admission** asks whether the actual selected PDEs, domain, materials, boundary conditions and source terms form a well-defined physical task. A bounded interpretation of incomplete paper information can proceed as a conditional engineering case.

**Scientific certification** separately asks whether native termination, physical consistency, conservation accounting, numerical uncertainty and main-paper comparisons support particular claims. Lack of final validation never automatically blocks unrelated source retrieval, geometry preparation or authorized bounded diagnostics.

Keep execution, numerical termination, physics verification, paper comparison and final scientific certification as independent statuses.

## Coupling checks, not mandatory node names

The COMSOL NonIsothermalFlow node is a documented, often convenient coupling implementation, especially for turbulent and temperature-dependent flow. It is not the only physically possible implementation.

Inspect effective velocity/heat coupling, thermophysical properties, turbulent heat conduction and wall treatment, appropriate solid/fluid domain selections, source terms and solver equations. Another coupling implementation needs a supported equivalence audit rather than an automatic ban. Manual velocity assignment alone is not proof of full turbulent coupling equivalence.

An apparent energy imbalance must not be automatically classified as coupling FAIL. Investigate actual energy terms, domains, normals, materials and boundary semantics first.

## Inlet / outlet heat transport boundary conditions

A known inlet-plane temperature may support a Temperature condition; a known upstream temperature feeding a virtual unmodeled duct may support an Inflow condition. COMSOL describes an Inflow heat condition through a virtual domain; the upstream temperature need not be strictly imposed at the physical inlet when conduction and other effects matter.

If a paper only reports Tin without boundary-feature semantics, register both reasonable interpretations as conditional, investigate installed-version documentation and downstream sensitivity, and justify a baseline choice. Neither boundary class is universally mandatory. ConvectiveOutflow is likewise an available option, not universally compulsory.

## Control-volume energy accounting

Withdraw prior global numerical hard gates based on Qapp = qw*A, Qsens = |m_dot|*cp*(Tout-Tin) and fixed 20% or 10% error thresholds.

For the selected physics and control volume, account where applicable for:
- transient energy storage;
- advective enthalpy, conductive/radiative heat flux and source terms;
- pressure/viscous work, kinetic energy and other work/energy effects;
- temperature-dependent enthalpy and material properties;
- correctly selected inlet/outlet surfaces, mass integration, flux sign, units, normals and applied heat zones.

The constant-cp formula remains a useful approximate steady-flow diagnostic only where assumptions justify it. A near-zero heat-transfer flux residual alone does not certify full energy balance. Report discrepancies as ENERGY_ACCOUNTING_REVIEW until the terms and physical cause have been examined. Quantitative acceptance tolerances must have source-backed definitions; do not invent universal 10%/20% thresholds.

## Practical, version-specific COMSOL evidence

- Enumerate study (tag, label) pairs before invoking the current wrapper by study_name: tag and label may differ.
- Inspect nonempty fluid, solid, still-fluid and heat-transfer selections and actual velocity/temperature transport; conduction-only islands must not be accidentally treated as flowing fluid.
- For geometry in mm, use explicit units where appropriate; verify work-plane shifts, boolean operations and topology through native model readback.
- If coupling, governing equations or geometry changes, old thermal mesh studies are not automatically transferable; label incompatible evidence SUPERSEDED.
- Segregated, FullyCoupled, continuation, damping and flow freezing are alternative numerical strategies, not required globally. Verify installed properties and log results. Change one controlled hypothesis per authorized attempt.
- Record solver telemetry, accepted iterations/steps and native completion reason. A saved file or a timeout alone is not proof of convergence. Do not force-kill or resubmit an unknown active job.

## Conditional cases

With incomplete but reasonably bounded input, continue read-only evidence gathering, geometry preparation, and separately authorized bounded sensitivity / conditional simulations. Preserve all assumptions, plausible intervals and provenance. If an essential physical quantity has no supportable bound, block only tasks that depend on its absolute value; continue independent preparatory tasks.

Neither tuning an alternative geometry nor successfully running an alternative BC proves the original paper's unknown geometry or BC. Reporting status must reflect scope: paper reproduction, conditional reconstruction, or new design.

## Sources

- COMSOL 6.4 Heat Transfer, Inflow: https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_ht_features.09.070.html
- COMSOL blog, Specifying the Temperature at a Flow Inlet: https://www.comsol.com/blogs/specifying-the-temperature-at-a-flow-inlet
- NASA NPARC CFD Verification Assessment: https://www.grc.nasa.gov/www/wind/valid/tutorial/verassess.html
- ASME V&V 20: https://www.asme.org/codes-standards/find-codes-standards/v-v-20-standard-verification-validation-computational-fluid-dynamics-heat-transfer

The original detailed numerical solver ladder is historical problem-specific guidance, not an authoritative algorithm for all COMSOL cases. Real COMSOL and Fluent execution for this revision: NOT_RUN.
