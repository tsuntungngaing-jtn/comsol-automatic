---
name: comsoflent
description: Plan evidence-grounded paper-to-simulation replication across COMSOL and Ansys Fluent. Prefer verified, isolated MCP connectors; route to solver-specific APIs only through trusted MCP tools; provide manual software discovery when unavailable. No unverified physics claims.
license: MIT
metadata:
  display_name: ComsoFlent
  version: "0.1.0"
  compatibility: "COMSOL Automatic 0.7.6 + official PyFluent MCP (separate installation)"
---

# ComsoFlent — dual-solver skill preview v0.1.0

This is a **new workflow layer**, not a renamed/installed Fluent server.
Read [the migration and connector plan](../docs/comsoflent-v0.1.0.md) and the
original [COMSOL skill](../SKILL.md). The existing COMSOL workflow and protection
rules remain in force. Preserve the original author's attributions.

## Reliability and incident response (candidate)

Before any live COMSOL or Fluent solver call, apply the shared, **offline** [operations guard](../docs/operations-reliability-v0.7.7-rc1.md) and `server/reproduction_guard.py`. Its evidence inventory is reported by the host, so matching does not mean it has independently inspected or connected to the solver. Compare the paper's requested *effective* heat input, boundary conditions, selections, material/coupling, initialization and time window with actual native API readbacks. Source and unit provenance are required for all hard acceptance thresholds; diagnostic alerts are not paper criteria. Reconcile stale or unknown solver jobs before resubmission; use a unique local task lease, not simultaneous control from multiple agents. Establish resource budgets from the same physics/host, examine accepted steps rather than elapsed wall-clock alone, and require save/reopen/identity verification before interpreting scientific results.

LAB7/LAB8 remain on their authorized PyFluent route; LAB9/LAB10 remain on their designated COMSOL route. Do not start or connect the other solver merely because the unified Skill is loaded. Do not alter an ongoing job, automatically cancel, force-kill, retry, acquire another machine's task, or silently loosen targets. A user's intentional skip is SCOPE_CHANGED, never scientific PASS. The reported <15% all-main-paper-metrics rule is a **user-scoped** acceptance policy requiring a declared formula, reference, condition and source, not a default physical law.

## Grid uncertainty: original-paper verification gate

Follow [Eça & Hoekstra (2014), original-PDF verification](../docs/eca-hoekstra-2014-original-paper-review.md) before interpreting a mesh-refinement study. Use `server/grid_uncertainty_admission.py` **offline** to check whether a solver-provenance grid family is a candidate for later fitting; the checker never calculates a numerical uncertainty or claims scientific PASS. The paper recommends at least four geometrically comparable grids for noisy engineering CFD data, with iterative error negligible relative to discretization error. Two-grid changes are only grid sensitivity evidence, not a GCI or uncertainty interval. The paper contains a genuine discrepancy between the p upper bound for a safety-factor condition at printed p.108 (`2.14`) and Appendix A at printed p.125 (`2.1`); require human/source review before implementing this threshold. Do not expand an expensive grid family without available RAM and task budget. Verification uncertainty and comparison against paper claims are separate quantities.

## Sequence

1. Extract original paper text/table numerical values before digitized figures,
   schematics or inferred values. Keep conflicting, uncertain and missing inputs.
2. Freeze a reviewed solver-neutral simulation spec, observables, dimensional
   units, expected conservation equations and reproducibility criteria.
3. Ask the host for actual registered MCP server/tool inventory. Prefer
   `solver_route_plan` to plan, not claim discovery. Select **one** solver and
   session. Never combine tool lists without namespace+ownership.
4. COMSOL: inspect via existing COMSOL MCP. Fluent: inspect using installed
   **official** `ansys/pyfluent-mcp` tool schemas, beginning with read-only
   discovery. Do not invoke third-party `launch_fluent` naming on official MCP.
5. If not connected, locate installed software metadata and explain MCP
   registration. Do not silently execute direct API scripts or GUI clicks.
6. Obtain authorization before solver launch, license consumption, writes or
   solves. Save native output with an audit trail and independent readbacks.
7. Gate on numerical convergence, mesh quality/independence, conservation,
   physical consistency and reference source quality. A successful solve is
   not proof of paper reproduction; unknown checks remain NOT_RUN.
8. For COMSOL->Fluent or Fluent->COMSOL recreation, explicitly audit differences
   in turbulence closures, wall treatment, discretization, mesh, solver, BCs,
   and thermal coupling. Do not claim they are mathematically identical.
9. Keep RSA/RSI diagnosis and Retain separate from original-paper claims;
   retain changed policies only after independently replayable evidence.

The preview routing tool **never connects or executes** a simulation. Its
inventories are caller-supplied and may be stale. No cross-platform simulation
is verified by this documentation alone.
