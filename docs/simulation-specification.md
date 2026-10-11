# Simulation specification and run identity
Before building, record scope, COMSOL version, required products, geometry/units, domain and boundary selections, material provenance and temperature range, physics/couplings, study, mesh strategy and observables. Distinguish documented values from assumptions. Specify acceptance thresholds before solving.

Assign a unique run_id and capture source/specification hashes, actual parameters, solver settings, model filename and result definitions. Changed geometry must be verified in the built geometry. Do not silently reuse datasets or CSV files from a different run. Maintain separate states for execution completion and scientific claim validation.
