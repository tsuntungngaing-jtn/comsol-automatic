# Geometry reliability implementation plan

Baseline: a012b21bcfd604adb8843f3b0e734478fc13b4a3. No AGENTS.md is present in this checkout. Isolated branch; no production installation or remote publication.

1. Preserve existing API fixes and verify the 38-test baseline. Repair property failure reporting and meter-valued primitive inputs, with fault-injection tests.
2. Add a pure contract engine and a serialized Java adapter for geometry measurements, selection validation and guarded binding. Unsupported evidence stays NOT_RUN.
3. Add baseline-preserving perturbations and provenance-bearing CAD import, using actual 6.4 APIs and explicit prerequisites.
4. Add schemas, layered reports, structured repair costs, tutorial metadata and ten benchmark specifications with a fixed-condition experiment entrypoint.
5. Run software/protocol tests and representative MCP-only COMSOL experiments; record independent reopen, limitations and package provenance. Deliver an English skill ZIP and Chinese summary.

Geometry validation is separate from Inspector. Legacy tools remain available; acceptance tools provide an explicit guarded route, not a sandbox for arbitrary Java code. Connectivity/contact checks without a supported evaluator remain NOT_RUN and block acceptance when required.
