# Agent audit trail (.java and logs)

Keep a durable audit under `COMSOL_OUTPUT_ROOT` for agent steps that change or
solve a model. This mirrors the official COMSOL agentic blog practice of saving
Java sources and progress logs for later review—**without** adopting a second
bare-Java control path. Control remains MCP-only.

## Layout

```text
COMSOL_OUTPUT_ROOT/<case_id>/
  audit/
    steps.jsonl                 # one JSON object per step (append-only)
    java/                       # Java or Copy-as-Code snippets actually applied
      <YYYYMMDDTHHMMSS>_<step>_<short>.java
      <YYYYMMDDTHHMMSS>_<step>_<short>.snippet.txt
    logs/
      <YYYYMMDDTHHMMSS>_<step>_mcp.json      # tool name, args summary, result summary
      <YYYYMMDDTHHMMSS>_<step>_stdout.txt    # code/tool text output when present
      <YYYYMMDDTHHMMSS>_<step>_stderr.txt
      <YYYYMMDDTHHMMSS>_<step>_progress.txt  # time, memory, DOF, warnings when available
    checkpoints/                # MPH from HARD GATE persist (unchanged policy)
```

Use a stable `<case_id>` (model tag or workspace folder name). Never write audit
files inside the skill package tree.

## What to record

| Event | Required artifacts |
|-------|--------------------|
| Session connect / model identity | `steps.jsonl` entry with host, port, standalone flag, model name/tag |
| Structured MCP mutate (`param_*`, physics, geometry, …) | `logs/*_mcp.json` + `steps.jsonl` |
| `comsol_model_code` or any Java/API snippet | **`audit/java/*.java` or `.snippet.txt`** (full source as executed) + stdout/stderr |
| Copy-as-Code from Desktop applied via MCP | Save the pasted setters under `audit/java/` before/with the apply step |
| Study / job run | progress log (time, memory, DOF, warnings) when the tool or COMSOL exposes them; else note `NOT_AVAILABLE` |
| KPI / evaluation | values in `steps.jsonl` or a small `logs/*_kpi.txt` |
| Failed step | keep failing source + stderr; do not delete on retry |

### `steps.jsonl` fields (minimum)

`ts`, `step_id`, `action`, `model`, `tools`, `java_path` (or null), `log_paths`,
`ok`, `notes`. Optional: `kpi`, `iters`, `wall_s`.

## Rules

1. **MCP remains the only control plane.** Audit files are evidence, not a
   license to drive COMSOL via shell `comsolcompile` by default.
2. If code ran, the source that ran must exist on disk under `audit/java/`.
   “Described in chat only” is not an audit.
3. Prefer one step → one timestamped stem shared by java + logs.
4. Redact secrets (passwords, tokens). Do not put license credentials in logs.
5. Expensive solves still require MPH checkpoints per [persist-hard-gate](persist-hard-gate.md);
   audit logs do not replace MPH delivery.

## Delivery mention

When handing off, cite the case audit directory path together with MPH path,
model name, and server port so the engineer can replay what the agent changed.
