# Uncertainty-aware RSI (V0.1)

Status: **implemented** (harness-side API + unit tests); **tested_with_mock**; real-COMSOL sensitivity propagation **NOT_RUN**.

## Position in the stack

```
Cross-task RSI Controller  (rsi/)
        ↓
Unknown-parameter / ParameterBelief layer  (uncertainty/)
        ↓
Existing ClosedLoopController  (server/orchestrator.py)
        ↓
MCP COMSOL execution
```

RSI does **not** replace the closed-loop state machine. Model revision `M₀→M₁` alone is not RSI. RSI requires a persistent agent/policy component `A₀→A₁` retained only after gated evaluation.

## Loop

Experience → Infer → Improve → Evaluate → Calibrate → Retain

## Non-goals (V0.1)

LLM fine-tuning, full Bayesian posteriors, Monte Carlo UQ, autonomous literature scraping, new MCP tools.

## Distinctions

| Claim | Meaning |
|---|---|
| Execution PASS | Job finished / tools succeeded |
| Numerical PASS | Residuals / solver criteria |
| Scientific PASS / CONDITIONAL / INSUFFICIENT_EVIDENCE | Claim-level validity under inputs |
| INFERRED | Not measured / not user-supplied |
| Estimated plausible range | Not a confidence interval |

See also: [parameter-inference.md](parameter-inference.md), [scientific-validity-under-uncertainty.md](scientific-validity-under-uncertainty.md), [rsi-evaluation-protocol.md](rsi-evaluation-protocol.md).
