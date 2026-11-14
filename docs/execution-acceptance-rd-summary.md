# R&D summary - execution skill / acceptance prompt separation

Candidate worktree based on `0bf2143` (contains current `main` / `a110d79`). This change does not merge PR #8 and does not fold retrieval or RSI promotion into the split.

## Development Status

Implemented the planned split: canonical `paper2simu/SKILL.md` is connection/execution/evidence only; compatibility routers add no acceptance policy; `prompts/paper-reproduction-task.md` is the shared COMSOL/Fluent reproduction task input; controller APIs expose optional `acceptance_spec` with separate execution / check / paper-comparison statuses; migration notes and a filled example (including Fluent selection of the same prompt) are included.

## Software Testing

Targeted suite `tests/test_execution_acceptance.py`: 14/14 PASS.

Related offline suites PASS: closed-loop, release packaging, scientific conditional, reproduction guard, solver router, native convergence, grid uncertainty admission.

Full `unittest discover` on this machine: 270 tests, 2 FAIL + 3 ERROR that also reproduce on clean HEAD without these edits (missing `mph` for geometry contracts; figure-routing tie case; MCP stdio/HTTP runtime environment). They are recorded as environment/pre-existing, not introduced by this split.

## Real-COMSOL Testing

NOT_RUN. No authorized live COMSOL session was used to validate the separation on LAB9/LAB10 or another host.

## Retrieval Performance

Not measured. Retrieval/RSI ranking work was intentionally excluded from this change.

## RSI Reliability

Not measured. RSI promotion and policy learning remain separate opt-in development tasks and were not exercised here.

## Unresolved Issues

- Live Fluent and COMSOL verification of the new skill/prompt contract remains NOT_RUN / BLOCKED until an authorized machine run.
- Full-suite environment failures above still need a clean test host with project dependencies (`mph`, MCP runtime auth fixtures).
- Historical docs that describe older acceptance workflows remain readable for reference; they are not activated by loading the skill, but callers must still avoid mistaking them for the current default.

## Merge Recommendation

Ready for review after CI is green. Do not treat offline PASS as real-solver certification. Prefer merging after a reviewer confirms skill/prompt boundary text and the controller contract tests; schedule separate real-COMSOL and real-Fluent smoke runs before any "reproduction verified" claim.
