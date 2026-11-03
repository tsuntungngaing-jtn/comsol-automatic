# Uncertainty-aware RSI (V0.5)

Status: **implemented** (harness-side API + unit tests); **tested_with_mock**; real-COMSOL sensitivity propagation **NOT_RUN**. Bounded self-refinement — not open strict RSI.

## Position in the stack

```
Cross-task RSI Controller  (rsi/ + harness_heuristics)
        ↓
Unknown-parameter / ParameterBelief layer  (uncertainty/ + autonomy)
        ↓
Existing ClosedLoopController  (server/orchestrator.py)
        ↓
MCP COMSOL execution
```

RSI does **not** replace the closed-loop state machine. Model revision `M₀→M₁` alone is not RSI. RSI requires a persistent agent/policy component `A₀→A₁` retained only after gated evaluation.

## Loop

Experience → Infer → Improve → Evaluate → Calibrate → Retain

Infer channels (see [rsi-autonomy-profiles](rsi-autonomy-profiles.md)): official docs → figure digitize → peer priors. Autonomy: `COMSOL_RSI_AUTONOMY`.

## Non-goals

LLM fine-tuning, full Bayesian posteriors, Monte Carlo UQ, open-ended autonomous RSI, Desktop UI automation, promoting digitized/peer values to paper-reported.

## Distinctions

| Claim | Meaning |
|---|---|
| Execution PASS | Job finished / tools succeeded |
| Numerical PASS | Residuals / solver criteria |
| Scientific PASS / CONDITIONAL / INSUFFICIENT_EVIDENCE | Claim-level validity under inputs |
| INFERRED | Not measured / not user-supplied |
| Estimated plausible range | Not a confidence interval |

See also: [parameter-inference.md](parameter-inference.md), [scientific-validity-under-uncertainty.md](scientific-validity-under-uncertainty.md), [rsi-evaluation-protocol.md](rsi-evaluation-protocol.md).
