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
