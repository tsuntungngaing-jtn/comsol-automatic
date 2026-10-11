# Material and model consistency
Prefer the installed Material Library for standard materials and nearby Application Library cases for equations and operating scales. Read back rho, viscosity, conductivity, heat capacity and their units where applicable. Preserve temperature/pressure dependencies; document custom constants and their valid range. Sanity-check printed paper formulas numerically instead of blindly copying coefficients.

Inspect boundary type, subtype, selection, overridden features, study activation and multiphysics references. Boundary temperature and upstream inflow temperature are not interchangeable. A zero local heat-transfer velocity field may be overridden by a coupling; inspect references and domain scope before diagnosing it. Do not claim coupling merely because a velocity was entered manually.

For new models avoid known obsolete node types. For old models preserve the original and compare equations and selections in a copy. API acceptance is weaker than semantic equivalence. Unresolved warnings or failed conservation are failures under a strict audit, not successful simulations.
