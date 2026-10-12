# Simulation specification and run identity
Before building, record scope, COMSOL version, required products, geometry/units, domain and boundary selections, material provenance and temperature range, physics/couplings, study, mesh strategy and observables. Distinguish documented values from assumptions. Specify acceptance thresholds before solving.

Assign a unique run_id and capture source/specification hashes, actual parameters, solver settings, model filename and result definitions. Changed geometry must be verified in the built geometry. Do not silently reuse datasets or CSV files from a different run. Maintain separate states for execution completion and scientific claim validation.

Executable structure is in `schemas/simulation-spec.schema.json`; layered results use `schemas/validation-report.schema.json`. `simulation_spec_validate` performs structural and dependency checks without COMSOL. Report PASS requires executed passing checks in each required layer. `server.contracts.repair_event` records operation category, stage, real errors/warnings, change, execution/solve counts, elapsed seconds, validation and stop reason. See the benchmark entrypoints for repeatable use.
