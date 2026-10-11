# Claim-by-claim validation
Create a comparison table before solving: claim, source figure/table, observable, units, domain/time selection, extraction method, tolerances and required numerical evidence. Use COMSOL evaluations as primary metrics and independent analytic estimates only as cross-checks.

Check solver termination, warnings, mass/energy conservation, discretization sensitivity and physical ranges relevant to the claim. For transients, evaluate storage and flux terms at solver time points. Compare saved-and-reopened results using a new evaluation run ID. Report PASS, FAIL, BLOCKED or NOT_RUN per claim; completion, file existence and successful node creation alone do not prove reproduction.
