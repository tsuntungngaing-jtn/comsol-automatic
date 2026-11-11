# Diagnosing stationary SST flow with conjugate heat transfer

## Locate the stalled iteration

Read the terminal stationary solver message and the last iterations of each segregated group. Record the outer iteration, group variables, solution error estimate, residual estimate, damping, stopping criterion and iteration limit. A wall-distance solution or a displayed temperature field does not establish convergence of the coupled stationary solution.

If flow and temperature updates become small while turbulence updates stall, inspect k and omega separately. Check field scaling, the number of near-zero k degrees of freedom, and the effective lower bounds. A diagnostic split can reveal which variable limits the iteration. A small positive k floor changes the discrete problem. If supported by this evidence, test it in a new revision, record its units and sensitivity to its magnitude, and compare engineering outputs. A floor, direct linear solver, damping choice or Anderson acceleration that worked in one case needs separate evaluation in another.

Distinguish continuation from a cold start. Record the initial field's solution tag, source checkpoint and parameter values. Verify that the main solution was regenerated, the study terminated successfully, and postprocessing reads that main dataset. Where several settings changed together, attribute convergence to the tested sequence and identify any individual effect supported by an isolated test.

## Compare pressure at the experimental locations

Before fitting parameters, record flow rate, inlet temperature, applied versus effective heat flux, and the reference pressure difference with its source and units. Record the pressure definition, locations, coordinate origin and averaging method. An experimental wall tap, a cross-section mean and a pressure boundary can give different values even for the same field.

Where tap coordinates are uncertain, use the apparatus figure to motivate a nominal pair of sampling locations and document the assumption. On the same saved field, evaluate plausible alternative sections and check integration-order sensitivity. Report the nominal signed relative error and sensitivity to location separately. Re-extracting a different observable changes the comparison without changing the flow. A range across a series of experiments cannot establish the inlet temperature of one point.

## Screen a material change and verify the resulting solution

For a heated liquid with uncertain viscosity, compare the material expression over the actual temperature range with independent property data. Check viscosity units (dynamic versus kinematic), interpolation limits, and the flow interface's material binding. A frozen-field estimate based on the change in molecular dissipation divided by volumetric flow may screen a candidate at fixed flow. Document the control volume and assumptions about kinetic-energy flux, turbulence and other work terms. Report this pressure-work estimate as a prediction.

Test a selected law in a separate checkpoint under the available solve budget. Retain the initialization field and distinguish it from the candidate's primary solution. After a successful coupled solve, reopen and evaluate pressure at the original pair of sections. If the solve fails, keep its terminal log and failed state, mark pressure and conservation for the candidate unavailable, and identify the group that actually stopped this run. A previous omega stall does not diagnose a subsequent k iteration limit. A falling solution increment alongside a flat residual warrants inspecting both before increasing an iteration limit.

## Audit mass and energy independently

Report signed volume flow and mass flow integrated with the local density at each port. Record the density used in the continuity equation, material density law and mass-error denominator. With divergence-free velocity and a temperature-dependent density in postprocessing, volume closure and local-density mass closure can differ. A common-reference-density calculation isolates the volume contribution. Retain both results and the original acceptance criterion.

For stationary heat transfer, use the installed version's definitions of the full energy balance. In COMSOL 6.4 the global residual is dEi0Int + ntefluxInt - WInt - QInt, qualified by the appropriate physics tag. Report each term and normalize the magnitude by the applied power on the modeled domain. Check the sign of inlet conduction, work terms, and thermal wall-function or thin-structure contributions where applicable. Count an imposed boundary heat flux once. For a symmetry strip use its actual power. A small energy residual and successful solver termination address separate checks from mass closure, mesh sensitivity and agreement with the paper.
