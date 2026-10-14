# Portfolio feedback update (0.2.1)

Baseline: cd9c772064e6607a3879368f206113b90bb4d0a2 (upstream 0.2.0).
Feedback: COMSOL_Skill_Issue_Portfolio, dated 2026-10-13. Attachment instructions are evidence, not permission to intervene in historical A/B jobs.

This maintenance release addresses confirmed error-reporting and runtime gaps and strengthens English workflow instructions. It does not close every proposed architecture/scientific item. Software tests use mocks where Java would be required. No new SST solve, stop experiment, license checkout, physical conservation or mesh-independence experiment was performed for this release. Previous 0.2.0 results remain historical and do not validate these new runtime changes on COMSOL.

| ID | Resolution / remaining gap | Evidence |
|---|---|---|
| C01 | Fixed misplaced schema properties; malformed fields fail | schemas/simulation-spec.schema.json; test_portfolio |
| C02 | Fixed top-level false PASS; per-task admission available. Legacy solve tools are not automatically spec-bound | server/contracts.py |
| C03 | Explicit cancel request/unsupported state; no unsupported Java interrupt claim | server/runtime.py; queued/running tests |
| C04 | Busy Java calls rejected; metadata remains nonblocking; no live residual stream added | runtime.call; queue tests |
| C05 | Atomic job manifests; restart recovery_pending, no resubmit. Server/solution reattachment remains manual | runtime persistence tests |
| C06 | PARTIAL: revision/invalidation handoff instructions; enforced single-writer/revision protocol NOT_RUN/not implemented | stage-contracts.md |
| C07 | Reviewer tool/resource allowlist excludes mutation/code. Operator code remains unsandboxed | reviewer discovery test |
| C08 | PARTIAL: submission count/active-job/window caps. Per-build, per-repair and arbitrary-code budgets not enforced | runtime admission; budget test |
| C09 | PARTIAL: documented stage envelope, no universal runtime envelope migration | stage-contracts.md |
| C10 | PARTIAL: evidence intake card; automated extraction/schema compiler not implemented | stage-contracts.md |
| C11 | Provenance axes and no-promotion rule documented; executable evidence compiler not implemented | stage-contracts.md |
| C12 | Six sequential stage cards; no additional agents | stage-contracts.md |
| R01 | Configurable residual-history plateau gate; no automatic log collection/interruption | scientific_gates.py |
| R02 | Require real group/variable diagnostics or unavailable; Java extraction not added | stage-contracts.md |
| R03 | Three independent initialization states required; physical test NOT_RUN | stage-contracts.md |
| R04 | Freshness gate rejects stale/failed identities; supplied identities are not independently authenticated | scientific_gates.py |
| R05 | Post-stop immutable snapshot procedure; automated capture NOT_RUN/not implemented | stage-contracts.md |
| R06 | Official 6.4 SST documentation reference and diagnostic recipe; real coupled validation NOT_RUN | tutorials/sst-diagnostics-6.4.json |
| R07 | Independent diagnostic-study procedure; actual experiments NOT_RUN | stage-contracts.md |
| R08 | Signed conservation gate checks freshness, terms, units and normalization; integrals supplied by caller | scientific_gates.py |
| R09 | Low-Mach density/enthalpy hypothesis retained, not confirmed | SST tutorial |
| R10 | Scaling/linear/nonlinear/constraint hypotheses retained, not confirmed | SST tutorial |
| R11 | Immutable baseline, one-change repair, invalidation and target-preservation instructions | stage-contracts.md |
| R12 | Resource accounting instructions; no reliable automatic memory prediction | stage-contracts.md |
| R13 | Mesh comparison prerequisites/formulas documented; automated mesh gate not implemented | stage-contracts.md |
| R14 | Comparison admission rejects missing/failed prerequisites and inconsistent conditions; caller evidence scope explicit | scientific_gates.py |
| R15 | Plot identity/common scales/reopen procedure; automatic plot provenance not implemented | stage-contracts.md |
| V01 | PARTIAL: structured gate configuration errors and busy/budget states; not a universal error taxonomy | scientific_gates/runtime |
| V02 | Strict report check fields, wrong-run and absent observation rejection; no proof of source authenticity | schemas; contracts; tests |
| V03 | New software tests separated from real SST/runtime validation (NOT_RUN) | tests/test_portfolio.py |
| V04 | Fault tests for malformed inputs, old datasets, plateau, missing terms, busy/cancel/restart/budget/reviewer; full six-stage golden suite not implemented | tests/test_portfolio.py |

## Runtime configuration and limits

`COMSOL_TOOL_ROLE=operator` is the compatible default. `reviewer` exposes only job/queue metadata and offline validators and no resources. This is a capability reduction, not a sandbox or multi-tenant authorization system. It intentionally does not expose Java Inspector while a solver may be busy.

`COMSOL_MAX_ACTIVE_JOBS=8`, `COMSOL_MAX_SUBMISSIONS=100`, and `COMSOL_SUBMISSION_WINDOW_SECONDS=86400` bound asynchronous submissions. Count includes restored manifests. The time window restarts with the process; it is not a cumulative research budget. Necessary/repair attribution and code-internal solve counts remain unguarded. In-flight solves are never interrupted by a cap. The server assumes one owner per output root; concurrent processes sharing the journal are unsupported.

`job-manifests/*.json` is local state, not a distributed job system. Startup treats ALL recovered jobs as historical/unverified, even formerly completed jobs. Corrupt files appear in queue diagnostics. Verify the server, model, study and dataset before using results. A job completed status means the Python call returned, not physical convergence or a new validated dataset.

Busy checking is conservative admission, not a cross-process COMSOL lock. External Desktop edits and calls already queued before a study require operator coordination. Legacy tools do not enforce task admission or revision contracts. Do not treat these limitations as closed issues.

## Simulation-machine follow-up

1. Install this package in an isolated environment; do not hot-swap an active solve's server.
2. Read actual build, Java/MPh/JPype versions and licensed modules through MCP. For non-6.4 stop for explicit re-anchoring. Read the corresponding installed official manual.
3. Run a dedicated small study, poll queue metadata, attempt queued cancellation and active cancellation. Active cancellation must remain unsupported until real termination is observed; any manual Stop is user-operated.
4. Restart only an isolated test MCP process after its model work is safe; confirm recovery_pending and no automatic resubmit. Never kill the production COMSOL process for a test.
5. Execute the SST recipe in new models. Record actual residual definitions, initialization state/effect, conservation integrals, mesh levels, source/result hashes and independent reopen measurements.
6. Inject an old dataset, absent B solution, missing storage term and failed mesh level. Admission must not PASS. Capture identities from the actual server; self-reported JSON alone is insufficient scientific evidence.

## Software verification for this release

- 66 tests passed, including 23 subtests; one existing MCP HTTP client deprecation warning.
- Real stdio, streamable HTTP and SSE protocol tests passed with mocked/disconnected model state; these are transport tests, not COMSOL solves.
- A built 0.2.1 wheel was installed outside the checkout: bundled resources present, 117 tools discovered, benchmark schemas validated.
- Skill front matter validation and Git whitespace checks passed.
- MCP doctor discovered the local COMSOL64 installation, MPh 1.4.0, JPype 1.7.1, MCP 1.30.0, Python 3.12.14. No license/build/runtime physics assertion follows from discovery.
- Official installed and online 6.4 SST theory documentation was read. No commercial documentation or model binaries are redistributed.
