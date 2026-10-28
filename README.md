# COMSOL Automatic 6.4 English — 0.3.1

Version **0.3.1** adds Round-1 CHT / compare hygiene docs (no new MCP tools; does not upgrade scientific VALIDATED status):

- [CHT coupling and energy gates](docs/cht-coupling-energy-gates.md) — inlet **Inflow** preference, coupling probe export, independent hydraulic vs enthalpy gates
- [Paper-only vs oracle compare](docs/paper-only-vs-oracle-compare.md) — counterpart labels (`Z_ORACLE` / `B_REPLICA` / `PAPER_FIGURE` / `NONE`); build vs compare phase separation

Inflow solver-recovery playbooks and mandatory NITF velocity-wiring rules remain deferred (Round 2).

Version **0.3.0** added an **outer** uncertainty-aware recursive self-improvement (RSI) layer:

`Experience → Infer → Improve → Evaluate → Calibrate → Retain`

It does **not** replace the existing MCP-only closed-loop controller. Model edits alone are not RSI; only gated `AgentVersion` updates (`A₀ → A₁`) count as harness-side self-improvement.

### V0.1 RSI scope (from 0.3.0)

- Unknown parameter detection + `ParameterBelief`
- Evidence provenance including EvidenceRecord origin `inferred`
- Plausible-range inference (not silent point guesses; not fake confidence intervals)
- U×S decision gate + endpoint sensitivity plan/propagation helpers
- Inference disclosure reports
- Conditional / insufficient scientific validity under inferred inputs
- `ExperienceRecord`, calibration compare, AgentVersion retain/reject
- Unit tests CASE1–7 — **`tested_with_mock`**
- Real-COMSOL endpoint propagation and held-out physical audit — **`NOT_RUN`**

No new MCP tools in 0.3.0 (API + tests first). P3 full Bayesian / MC UQ remains **NOT_IMPLEMENTED**.

Closed-loop reconstruction (EvidenceRecord, DecisionRequest, persistent controller, repair/calibration provenance) remains **`tested_with_mock`**, **not** `tested_with_real_COMSOL`. See [closed-loop controller](docs/closed-loop-controller.md) and [uncertainty-aware RSI](docs/uncertainty-aware-rsi.md).

Geometry reliability extension based on commit a012b21bcfd604adb8843f3b0e734478fc13b4a3 of tsuntungngaing-jtn/comsol-automatic. Not an official COMSOL product. Original provenance and licenses are in NOTICE.md and vendor/installed-mcp/LICENSE.

This package contains the skill, MCP adapter, vendored tools, catalog metadata, original teaching source, tests and installation scripts. It contains no commercial COMSOL models, manuals, research results, credentials or Python environment.

On Windows, extract the full folder to a new directory, then run `powershell -ExecutionPolicy Bypass -File scripts/install.ps1`. Register the MCP command using the new folder's `.venv/Scripts/python.exe -m server.main serve --transport stdio` and its working directory. Set COMSOL_OUTPUT_ROOT to your research workspace, not this folder. See docs/connectors.md for details. Existing skills/connectors are not replaced automatically.

The executable and package remain named comsol-automatic for compatibility. The discoverable skill name is comsol-automatic-6-4-en.

Run `python -m unittest discover -s tests` for Python/protocol checks. Real COMSOL validation must run through MCP. Read docs/validation.md before using results in research.

Software correctness and scientific correctness are reported separately.
