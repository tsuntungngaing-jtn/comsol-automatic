# Scientific validity under uncertainty

Status: **implemented** in `server/scientific_validity.py`; mock-tested.

## Rules

- `SOLVER PASS ≠ SCIENTIFIC PASS`
- If any scientifically relevant parameter is `INFERRED` with `decision_impact` in `{HIGH, CRITICAL}`, scientific status is `CONDITIONAL` or `INSUFFICIENT_EVIDENCE` — never silent final `PASS`.
- `INSUFFICIENT_EVIDENCE` is not `FAIL`.
- `NOT_RUN` remains visible and is not `PASS`.
- Low-impact inferred inputs may continue for screening with disclosure; still `CONDITIONAL` for final scientific PASS.

## Aggregation note

Existing layer aggregate (`PASS/FAIL/BLOCKED/NOT_RUN`) is unchanged for geometry/API contracts. Scientific-under-uncertainty is a **separate** evaluator used by the RSI outer layer and operators.

## v0.2.1 proposed correction

Numerical/solver FAIL, BLOCKED and NOT_RUN must keep priority over inferred-parameter status. Required scientific checks missing => NOT_RUN, never PASS. Inferred impact can limit claim scope even when a conditional model is solvable; it does not itself cancel independent model preparation. RSI retention from self-reported metrics is prohibited pending independent evaluation. See [candidate audit](conditional-reconstruction-and-rsi-evidence-v0.2.1.md).
