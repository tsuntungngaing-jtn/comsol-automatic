# Eça–Hoekstra (2014): original-PDF numerical uncertainty guidance

## Verified source

L. Eça and M. Hoekstra, "A procedure for the estimation of the numerical
uncertainty of CFD calculations based on grid refinement studies",
*Journal of Computational Physics* **262** (2014), 104–130,
DOI: 10.1016/j.jcp.2014.01.006.

**Provenance:** user-supplied 27-page publisher PDF
`1-s2.0-S0021999114000278-main.pdf`; read text and inspected rendered
publisher pages 5, 22, 23. The PDF is **not** distributed with the Skill.
This is not a claim that the external Elsevier webpage is freely accessible.

## Verified methodology, with source-page mapping

1. Printed p. 105 (PDF p. 2), §2.1: numerical error includes **roundoff,
   iterative, and discretization** errors. Grid-based uncertainty estimation
   presumes discretization dominates. The authors cite a suggestion that
   iterative error be two–three orders of magnitude smaller; do not turn
   that into an unqualified COMSOL/Fluent universal numerical threshold.
2. Printed pp. 105–106 (PDF pp. 2–3), Eqs. (1)–(4):
   `phi(h) - phi_0 = alpha * h**p`; the three-grid apparent-order
   relation is conditional on suitable systematic, geometrically
   comparable meshes and nearly asymptotic behavior.
3. Printed p. 106 (PDF p. 3), Eqs. (5)–(7): three additional candidate
   error models: `alpha*h`, `alpha*h**2`, and
   `alpha1*h + alpha2*h**2`, particularly for noisy/non-monotonic
   practical CFD results.
4. Printed pp. 106–107 (PDF pp. 3–4), §2.3, Eqs. (8)–(17):
   compare weighted and unweighted least-squares fits. With scatter,
   **at least four grids are highly recommended**; a three-grid fit
   does not have redundancy for a fitting-quality check.
5. Printed p. 108 (PDF p. 5), §3, Eqs. (18)–(21):
   uncertainty combines a safety-factored estimated discretization
   error, fit scatter `sigma`, and fitted-point discrepancy. It
   is **not** merely the finest/coarsest difference, and 95%
   coverage is the methodological target, not proof in a new case.
6. Printed p. 125 (PDF p. 22), Appendix A: ordered decision flow
   for `delta_RE` versus fixed-order candidates, then `Delta_phi`,
   safety factor and `U_phi`. Printed pp. 126–128 (PDF pp. 23–25),
   Appendix B: analytic weighted/unweighted least-squares equations.
7. **Source-internal discrepancy requiring manual review:** printed
   p. 108 (PDF p. 5), Eq. (19) discussion uses
   `0.5 <= p < 2.14` for the `Fs=1.25` condition (confirmed visually);
   Appendix A on printed p. 125 (PDF p. 22) uses
   `0.5 <= p < 2.1`. Do NOT silently choose one. The distinct
   condition on printed p. 108, §2.4.1 for accepting the
   Richardson-derived **error estimator** is `0.5 <= p <= 2`.
   A production implementation must document author clarification
   or make the safety-factor ambiguity an explicit review item.

## What the Skill may safely automate immediately

- Check mesh family: at least four **comparable** grids, consistent
  physics/geometry/BC/observable definition, explicit characteristic
  mesh size `h`, mesh quality and wall treatment; do not equate
  element count to geometrical similarity.
- Check each grid's solver stopping criteria, nonlinear/linear residual
  monitoring, numerical precision and relevant conserved quantities.
  If iterative error is not demonstrated small enough, **do not**
  certify a discretization uncertainty.
- Annotate source-backed scope, identify which numerical runs could be
  used for an eventual least-squares fit. Preserve full run/mesh IDs
  and native saved artifacts; do not fabricate extra grid solutions.
- When only two grids or inconsistent data exist, return
  `GRID_SENSITIVITY_ONLY` or `INSUFFICIENT_EVIDENCE`, never a
  published-method `U_phi` or Scientific PASS.
- For a real estimator, independently implement and test all candidate
  models/weighting, fit-quality, anomalous data and degeneracy cases,
  and explicitly resolve the noted source discrepancy before adopting
  a safety factor. Do **not** infer a GCI or error bar from two grids.

## Case-specific interpretation (reported, NOT verified)

The supplied LAB9 records for one geometry report a 0.3 mm
vs 0.2 mm change of approximately **6.44% and 13.00%** in two
CV metrics, whereas a 20 to 19 mm parameter change yielded
approximately **3.58% and 1.49%**. These are not matching
like-for-like sensitivity and uncertainty intervals; they
flag an immediate **need to prioritize numerical verification**
over speculative parameter calibration. The numbers are
reported history, not authenticated solver outputs.

For Fluent, the same scientific methodology can apply to
finite-volume results; this does not mean COMSOL and Fluent
have identical wall treatment, discretization orders, mesh
families or native result expressions. Each solver needs
its own independently measured provenance and run-quality
evidence. No solver runs were performed for this memo.

## Follow-up validation

- On each machine, gather >=4 grids with comparable settings only when
  resource admission permits. Do not exhaust memory in pursuit of a
  prescribed grid count.
- Compare iteration error and mesh sensitivity for each observable
  before authorizing parameter tuning.
- Fit candidates and uncertainty on synthetic known-order data and
  non-monotonic/noisy data; verify against original paper examples
  before any scientific PASS.
- Keep errors from the paper-vs-simulation reference definition
  **separate** from numerical discretization uncertainty.

Reference: DOI https://doi.org/10.1016/j.jcp.2014.01.006.
