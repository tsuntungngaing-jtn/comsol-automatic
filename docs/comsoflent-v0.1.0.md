# ComsoFlent 0.1.0 — MCP-first dual-solver preview

This is a **new workflow/skill generation**, not an assertion that the legacy
COMSOL package has been converted into a fully functioning Fluent executor.
The existing package and SKILL.md retain version **0.7.6**. No solver was run
and no connection to a user's workstation was established.

## Name and compatibility

Display name: **ComsoFlent** (COMSOL + Fluent). This is a proposed name, not
a claim of affiliation with COMSOL or Ansys.
Skill version: **0.1.0** (new dual-solver capability line).
Python distribution and original COMSOL entrypoint: unchanged (0.7.6).
Do not rename or remove original tools, script paths, installer directories,
output paths, auth variables, or existing MCP service registrations.

## Architecture

Paper/PDF evidence and authoritative source precedence
  -> frozen, uncertainty-aware SimulationSpec + observable gates
  -> `solver_route_plan` (offline tool-inventory decision only)
  -> host-controlled MCP tool calls (separate server/session per solver)
     - COMSOL: this repository's installed COMSOL MCP
     - Fluent: https://github.com/ansys/pyfluent-mcp
  -> solver-native execution evidence
  -> solver-neutral conservation, mesh, physics and source checks
  -> artifact+provenance review and retained RSI experiment

**The host, not this MCP server, owns client tool registration and actual
calls to the two leaf servers.** This preview deliberately does not create
nested MCP clients or proxy remote arbitrary code. This avoids recursive
MCP registration, duplicate tool collisions, and unverified cross-session
ownership. Distinguish `available` (caller-reported) from live handshakes.

## Official Ansys versus third-party Fluent CFD Skill

Official https://github.com/ansys/pyfluent-mcp publishes tool names such as
`connect`, `disconnect`, `session_status`, `find_api`, `get_state`,
`validate_code`, `run_code`, `mesh_quality` and `simulation_report`.
Its source tree requires **Python >=3.12** at the time of review.

The third-party https://github.com/cavoiie/fluent-cfd-skill describes
`server_info`, `launch_fluent`, `run_tui`, `iterate`, etc. These are
**not assumed aliases** of the official tool names. Borrow its scientific
workflow (mesh, BC, turbulence, convergence, conservation), not its tool
invocations, unless that distinct backend is actually installed and verified.

The existing COMSOL package supports Python >=3.10. Prefer two isolated
virtual environments instead of forcing conflicting dependencies into one.

## Discovery and control policy

1. Inspect the user's active MCP tool inventory through the host and assign
   unique IDs (for example `comsol_local`, `fluent_local`). Never guess tools.
2. Use `solver_route_plan` with this inventory. Its output is advice, not a
   connection check or permission to act.
3. If no MCP is available, ask the host/computer-access layer to search
   **approved installation metadata** (Windows installed-app registry,
   `COMSOL_ROOT`, `COMSOL_VERSION`, Ansys `AWP_ROOT*`, and known executable
   paths). Do not execute discovered binaries just to probe them.
4. Offer the documented connector setup through user-controlled/local setup.
   Any API adapter is a separately approved, auditable MCP implementation.
   Do not silently bypass a failed MCP by using direct Python or UI automation.
5. If a user explicitly asks for a GUI/manual workflow and the host supports
   computer use, give instructions to locate the installed app or operate
   visible controls with approval. Mark it `GUI_ASSISTED`, never `MCP_VERIFIED`.
   COMSOL's legacy policy **still prohibits automated clicking**; only its
   documented manual Desktop import is supported.
6. Require user authorization for licensing, launch, mutation, solve, and
   writing model files. Read-only inspection does not authorize modification.
7. Use source-native artifacts (`.mph` and Fluent case/data), preserve raw
   solver errors, version numbers, units, BCs, mesh, convergence, readbacks,
   model identity, and provenance. Cross-solver changes need science review.

## Example — caller-supplied (not live) inventory

```json
{
  "preferred_solver": "fluent",
  "source_solver": "comsol",
  "task": "inspect",
  "servers": [{
    "id": "fluent_local",
    "solver": "fluent",
    "available": true,
    "tools": ["connect","session_status","find_api","get_state"]
  }]
}
```

Expected status: `CROSS_SOLVER_RECONSTRUCTION_REVIEW` (not execution).
Never equate a tool-name match to proof of a running app or solver license.

## Release gates still outstanding

- Independent host-level discovery and schema handshake for both registered MCP
  servers; session acquisition and reconnect/misrouting tests on Windows.
- Implement an actual authorized Fluent executor/provenance bridge.
- Run real solver cases, verify observables and source/target physics equivalence.
- Test isolation of multiple projects, missing licenses, user denial, stale
  sessions, interrupted solve, save/reopen, and partial failures.
- Update distribution packaging, README and user-facing release metadata in a
  later deliberate migration. Do not label this preview as production-ready.

Offline test: `python -m unittest tests.test_solver_router -v`.
