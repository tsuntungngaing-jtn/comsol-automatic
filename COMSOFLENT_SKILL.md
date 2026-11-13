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
Read [the migration and connector plan](docs/comsoflent-v0.1.0.md) and the
original [COMSOL skill](SKILL.md). The existing COMSOL workflow and protection
rules remain in force. Preserve the original author's attributions.

## Sequence

1. Extract original paper text/table numerical values before digitized figures,
   schematics or inferred values. Keep conflicting, uncertain and missing inputs.
2. Freeze a reviewed solver-neutral simulation spec, observables, dimensional
   units, expected conservation equations and reproducibility criteria.
3. Ask the host for actual registered MCP server/tool inventory. Prefer
   \`solver_route_plan\` to plan, not claim discovery. Select **one** solver and
   session. Never combine tool lists without namespace+ownership.
4. COMSOL: inspect via existing COMSOL MCP. Fluent: inspect using installed
   **official** \`ansys/pyfluent-mcp\` tool schemas, beginning with read-only
   discovery. Do not invoke third-party \`launch_fluent\` naming on official MCP.
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
