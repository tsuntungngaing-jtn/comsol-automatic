---
name: paper2simu
description: Plan evidence-grounded paper-to-simulation replication across COMSOL and Ansys Fluent. Prefer verified, isolated MCP connectors; route to solver-specific APIs only through trusted MCP tools; provide manual software discovery when unavailable. No unverified physics claims.
license: MIT
metadata:
  display_name: Paper2Simu
  version: "0.2.0"
  compatibility: "COMSOL Automatic 0.7.6 + official PyFluent MCP (separate installation)"
---

# Paper2Simu — unified paper-to-simulation skill v0.2.0

This is the **primary project and Skill entrypoint**, built from COMSOL Automatic v0.7.6 and ComsoFlent v0.1.0. It does not bundle/install the official Ansys Fluent MCP; a configured authorized solver connection remains necessary. A Fluent machine connection was confirmed by the user, but full CFD paper-reproduction acceptance has not been independently verified.
Read [the migration and connector plan](../docs/comsoflent-v0.1.0.md) and the
original [COMSOL skill](../SKILL.md). The existing COMSOL workflow and protection
rules remain in force. Preserve the original author's attributions.

## Reliability and incident response (candidate)

Before any live COMSOL or Fluent solver call, apply the shared, **offline** [operations guard](../docs/operations-reliability-v0.7.7-rc1.md) and `server/reproduction_guard.py`. Its evidence inventory is reported by the host, so matching does not mean it has independently inspected or connected to the solver. Compare the paper's requested *effective* heat input, boundary conditions, selections, material/coupling, initialization and time window with actual native API readbacks. Source and unit provenance are required for all hard acceptance thresholds; diagnostic alerts are not paper criteria. Reconcile stale or unknown solver jobs before resubmission; use a unique local task lease, not simultaneous control from multiple agents. Establish resource budgets from the same physics/host, examine accepted steps rather than elapsed wall-clock alone, and require save/reopen/identity verification before interpreting scientific results.

LAB7/LAB8 remain on their authorized PyFluent route; LAB9/LAB10 remain on their designated COMSOL route. Do not start or connect the other solver merely because the unified Skill is loaded. Do not alter an ongoing job, automatically cancel, force-kill, retry, acquire another machine's task, or silently loosen targets. A user's intentional skip is SCOPE_CHANGED, never scientific PASS. The reported <15% all-main-paper-metrics rule is a **user-scoped** acceptance policy requiring a declared formula, reference, condition and source, not a default physical law.

## Grid uncertainty: original-paper verification gate

Follow [Eça & Hoekstra (2014), original-PDF verification](../docs/eca-hoekstra-2014-original-paper-review.md) before interpreting a mesh-refinement study. Use `server/grid_uncertainty_admission.py` **offline** to check whether a solver-provenance grid family is a candidate for later fitting; the checker never calculates a numerical uncertainty or claims scientific PASS. The paper recommends at least four geometrically comparable grids for noisy engineering CFD data, with iterative error negligible relative to discretization error. Two-grid changes are only grid sensitivity evidence, not a GCI or uncertainty interval. The apparent `2.14` in PDF text extraction is actually `2.1` followed by superscript footnote 4, confirmed visually on printed p.108; Appendix A also states `p<2.1`. Do not treat the footnote marker as a digit. Do not expand an expensive grid family without available RAM and task budget. Verification uncertainty and comparison against paper claims are separate quantities.

## Solver-native convergence and execution decisions

The commercial solver's *configured* and **observed** native termination reasons are the default iteration-convergence authority. Do not add an unexplained residual floor or rerun an otherwise correctly terminated solver solely because an independent plateau diagnostic is noisy. Inspect actual warnings, native stopping reason, convergence criteria, and physics quantities. A saved file or completed job alone does not imply the solver reported convergence. An extra residual threshold is diagnostic unless documented as a specific paper/user/engineering acceptance contract. Scientific agreement, conservation, discretization uncertainty, and input provenance are separate gates. See [convergence policy](../docs/native-convergence-policy.md).

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

## Conditional reconstruction and final-claim separation (v0.2.1 candidate)

Read [the source-backed conditional-reconstruction and RSI audit](../docs/conditional-reconstruction-and-rsi-evidence-v0.2.1.md) before enforcing any inherited CHT or uncertainty gate. **Missing final verification does not prevent independent evidence retrieval, model preparation or other separately authorized well-posed conditional work.** It does prevent unqualified final scientific PASS. Explicit solver FAIL/BLOCKED/NOT_RUN have priority over inferred-parameter limitations; missing required checks never yield PASS. Respect vendor-native configured termination; diagnostic residuals do not create new universal solver requirements. Use the revised [CHT verification policy](../docs/cht-coupling-energy-gates.md) instead of old mandatory node/Inflow/10–20% rules. All successful but unverified RSI metrics are REVIEW_REQUIRED, not RETAIN. This is an offline candidate policy; COMSOL and Fluent tests are NOT_RUN.


## Discovery Mode — surrogate-assisted CFD screening (v0.3.0 research branch)

**Mode choice is explicit.** Default is REPRODUCTION for a user asking to recreate an existing paper. Enter DISCOVERY only for a separately authorized new design/search research question; assign a separate study ID and freeze original-paper inputs and scope. The existing conditional reconstruction, native convergence, coupled heat transfer, source-precedence, case identity, resource/lease and scientific verification rules continue unchanged.

Read the [Discovery Mode workflow](../docs/discovery-surrogate-workflow-v0.3.0.md) and [original research roadmap](../docs/ai-experiment-design-research.md) before candidate selection.

1. Declare variables, bounds, physical/manufacturing constraints, source refs, objective units, allowed solver and budget. Do not change paper-reported geometry or BCs merely to improve reported agreement.
2. Import only properly source-tagged actual CFD outcome records (configuration/case/result hashes; solver; fidelity; metrics; native convergence/conservation/physics/mesh checks). The current code validates **caller declarations** but does not open files or independently authenticate a run.
3. Use the lightweight IDW baseline with grouped leave-one-design-out objective-specific errors. At least four distinct design points are required. Do not treat a low temperature aggregate error as assurance for wall heat transfer, pressure drop, species transport or full-field reconstruction.
4. Explicitly declare per-objective screening-error ceilings; when a required metric fails, request more data/review rather than forcing a model PASS. Reject unseen categorical settings and outside-observed-range surrogate predictions.
5. Rank **proposals**, not solver commands, using transparent distance/desirability heuristics and caller-declared cost/risk. Scores are neither calibrated probabilities nor expected improvement. A selected ID is NOT a validated optimum, and no CFD calculation has happened.
6. Any high-fidelity COMSOL or Fluent experiment requires fresh host authorization, native tool discovery and readbacks, task lease, real resource budget, valid numerical termination and saved/reopened auditable result. Never initiate solver jobs from the offline package.
7. Separate discovery outputs from REPRODUCTION conclusions. Retain new agent policy only with independently verified held-out evidence, including erroneous PASS and unnecessary-blocking rates.

The offline public APIs are research_design.validate_space, admit_observations, fit_idw_baseline, predict_idw and screen_and_rank. Tests: tests/test_research_design.py and tests/test_discovery_surrogate.py. This branch is a prototype: no neural-network training, Bayesian optimization, active solver control or real CFD performance evidence.
