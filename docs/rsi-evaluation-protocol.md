# RSI evaluation protocol

Status: **implemented** harness-side gates; held-out real-COMSOL audit **NOT_RUN**.

## Splits

| Split | May train priors / policies? |
|---|---|
| experience | yes |
| development | gate only |
| held_out | **never** |

## Ablations (report separately)

1. Static baseline (A0)
2. + Cross-task memory
3. + ParameterBelief
4. + Sensitivity-aware inference
5. + Calibration
6. Full RSI

## Retention

Retain candidate `A_{k+1}` only if:

- Performance(new) > Performance(old)
- ScientificValidity(new) >= ScientificValidity(old)
- FalsePassRate(new) <= threshold
- Regression(new) <= threshold
- Cost acceptable

Otherwise REJECT and keep `A_k`.

Unit-test PASS is not physical validation.
