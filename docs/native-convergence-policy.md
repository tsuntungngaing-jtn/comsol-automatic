# Paper2Simu: vendor-native numerical convergence (candidate v0.2.0)

## Why this matters

The original COMSOL Automatic code includes a numerical residual plateau
observer in `server/scientific_gates.py`. It checks whether an observed
history improved sufficiently over a declared window, but its result is
explicitly **not a solver convergence verdict**. Do not silently wire that
diagnostic's FAIL into a blanket requirement to rerun a completed solver.

New `server/native_convergence.py` returns a *reported* native
termination status and independently reports any additional residual
diagnostic. It does not execute a solver, authenticate caller logs, or
replace the case's conservation, uncertainty or science checks.

## Decision policy

1. Read the **actual solver termination reason and configured criteria**
   from the solver log and official native API; a saved case/data file,
   plot or job-completed flag alone is not evidence of convergence.
2. If native solver reports convergence and no unresolved warning,
   record `NATIVE_CONVERGENCE_REPORTED`. Do not invent another
   arbitrary global residual target or automatically rerun.
3. Extra residual alarms remain informative diagnostics. An additional
   **explicit** user/paper/engineering contract, frozen before viewing
   results, remains independently reviewable; do not silently discard it.
4. Distinguish convergence of nonlinear/linear iterations from the
   **physical time evolution** of a transient model. A changing
   temperature at accepted time steps need not mean numerical failure.
5. Separate native numerical termination, finite-volume/finite-element
   conservation, mesh/temporal discretization evidence, correct physics
   and paper result agreement in the final report.
6. Retain all raw warning messages and failed numerical states.
   Successful termination is not validation of an inferred geometry,
   wrong heating/cooling BC, contaminated dataset or missing energy term.
7. For surrogate models and physics-informed ML, physics losses are
   research hypotheses to validate against held-out predictions, not
   automatically better; the CFD numerical gate is conceptually
   different from the network's training loss.

## Sources

- COMSOL 6.4 documentation: configured nonlinear convergence methods
  (solution, residual, both/either as supported), and study logs.
- Ansys Fluent User's Guide: convergence requires interpreting solver
  residuals in relation to monitored quantities; universal residual
  thresholds are unreliable.
- L. Eça and M. Hoekstra, JCP 262 (2014) 104-130,
  DOI 10.1016/j.jcp.2014.01.006: error contributions from iteration,
  discretization, roundoff; mesh-based uncertainty requires appropriate
  numerical conditions. A vendor-native 'converged' status does **not**
  by itself demonstrate discretization error is negligible.
- Original uploaded PDF analyzed in
  `docs/eca-hoekstra-2014-original-paper-review.md`.

This is a **policy and offline classification improvement**, not a
verified COMSOL/Fluent production integration. Real vendor API log
collection and independent replay remain required before claiming
tested operational reliability.
