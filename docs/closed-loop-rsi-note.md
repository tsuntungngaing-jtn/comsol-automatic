# Closed-loop + RSI boundary

The existing closed-loop controller (`server/orchestrator.py`) remains the **inner** Evidence→Spec→Build→Solve→Validate→Repair machine.

The RSI layer (`rsi/`, `uncertainty/`) sits **outside** it:

- Detect / infer unknown parameters before admission
- Disclose uncertainty and decide AUTO / SENSITIVITY / ASK
- Record ExperienceRecord after task outcomes
- Calibrate and retain AgentVersion only after gated evaluation

Do not conflate model revision with agent/policy version. See [uncertainty-aware-rsi.md](uncertainty-aware-rsi.md) and [closed-loop-controller.md](closed-loop-controller.md).
