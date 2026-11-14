# Paper2Simu — Paper-to-Simulation for COMSOL and Ansys Fluent

**Project generation: v0.2.0 (unified codebase; solver-specific scientific validation ongoing).**

Paper2Simu unifies the evidence-first COMSOL Automatic pipeline (up to v0.7.6) and the ComsoFlent v0.1.0 MCP-routing preview. The project is no longer named ComsoFlent. The repository URL may still display the old GitHub slug until the repository owner renames it in GitHub Settings. Legacy names in historical notes are attribution and compatibility references, not separate active products.

**Execution scope:** The user reports an actual Fluent-workstation connection. This does not independently establish that all Ansys simulation tools, restart flows, or full CFD reproductions have been verified. COMSOL and Fluent use separate MCP providers, environments, model files and solver settings. The unified Skill orchestrates routing and scientific evidence; it does not silently load or operate a different solver.

**Skill entry:** [paper2simu/SKILL.md](paper2simu/SKILL.md) or the compatibility [root SKILL.md](SKILL.md). Additional architecture: [legacy ComsoFlent migration design](docs/comsoflent-v0.1.0.md), [operations guard](docs/operations-reliability-v0.7.7-rc1.md), [vendor-native convergence](docs/native-convergence-policy.md).

**Installation:** Python project `paper2simu==0.2.0` retains `comsol-automatic` and `comsol-skill-mcp` command aliases for existing COMSOL setups; new aliases: `paper2simu`, `paper2simu-comsol-mcp`. These aliases start the **COMSOL MCP service**, not a Fluent solver. Install official [Ansys PyFluent MCP](https://github.com/ansys/pyfluent-mcp) separately with its documented Python environment and register a distinct host server ID. Do not assume a single shared virtualenv can satisfy both products.

**Release migration:** `python scripts/release.py --output ../Paper2Simu-v0.2.0.zip` and `python scripts/install_skill.py` produce the new package/install name without overwriting an existing directory. Keep the old install until a complete rollback-tested integration is accepted. Never transfer COMSOL tokens or private solver artifacts into the public Git repository.

## Execution/acceptance separation (candidate)

The [canonical skill](paper2simu/SKILL.md) now handles solver connection, authorized execution and evidence delivery. Supply the [unified COMSOL/Fluent reproduction prompt](prompts/paper-reproduction-task.md) separately to define inference and acceptance; its configurable paper-metric default is strict <15%. A modeling task without acceptance criteria can still execute and deliver results without a reproduction PASS claim. See [migration/API notes](docs/execution-acceptance-separation.md) and [filled example](examples/paper-reproduction-task-example.md).

The controller reports execution, checks and paper comparisons separately. Failed/partial artifacts are deliverable. Optional legacy checks remain available, but historical policies below are not automatically activated by loading the skill. Live solver validation of this change remains NOT_RUN.

## Previous COMSOL Automatic capabilities (preserved)


Version **0.7.6** adds **paper-first source precedence and authoritative supplementation review**. `input_intake` now exposes a direct-text/table preference audit and blocks reviewed figure/schematic/engineering inputs from overriding an explicitly located and reviewed original paper numeric input for the same approved physical quantity. A new offline reviewer-mode MCP tool `source_precedence_review` distinguishes original author supplements, institutional standards, relevant peer-reviewed research, quantitative figure digitization, schematic estimates, engineering assumptions and ML outputs. External sources require reviewer-declared provenance/version/physical applicability; "supplement not obtained" and ML imputation never become original evidence. The tool does not verify claims against the internet, select a value, run COMSOL or certify physics. See [authoritative source precedence](docs/authoritative-source-precedence.md).

Version **0.7.5** introduces an **offline knowledge-guided commissioning and evidence-gated recovery harness**, inspired by GCH. Four new MCP tools (`recovery_contract_freeze`, `recovery_commission`, `recovery_propose`, `recovery_assess`) support immutable hash-frozen contracts, reported parameter readback audits, bounded one-parameter repair proposals tied to v0.7.4 diagnostic evidence, and per-observable comparisons against fixed acceptance thresholds. All reported results remain **NOT_RUN** scientifically, and no solver is operated or repair automatically applied. COMSOL/MCP and Fluent/PyFluent are declaration types; only existing COMSOL integration is available. See [knowledge-guided recovery](docs/knowledge-guided-recovery.md).

Version **0.7.4** adds **offline, evidence-driven physical diagnostic hypothesis planning**, inspired by DEScover. New read-only MCP tools `physics_diagnostic_plan` and `physics_diagnostic_record` predeclare falsifiable mechanisms, budgets, source identities, units and tests, order experiments by cost, and preserve reported results in immutable provenance reports. A matched test does **not** prove root cause; `causal_status` remains `UNCONFIRMED`, scientific status `NOT_RUN`, and automatic repair is not authorized. No new COMSOL execution, neural hypothesis discovery, commercial solver code modification or RSI policy mutation is implemented. See [physics diagnostic hypotheses](docs/physics-diagnostic-hypotheses.md).

Version **0.7.3** adds an **offline simulation dataset and Design of Experiments foundation** informed by high-fidelity transonic-wing dataset generation. It provides `simulation_dataset_plan` and `simulation_dataset_record` for evidence-tagged parameter ranges, seeded bounded randomized LHS, supported unit-consistent constraints, case-level train/validation/test labels, per-observable validation placeholders and immutable reported outcome/failure reviews. It does **not** run COMSOL, authenticate source claims, generate optimized LHS/OOD data, certify mesh independence, perform automatic repairs or produce training-ready scientific datasets. Synthetic Python unit tests cover the planning and report layer; COMSOL physical integration **NOT_RUN**. See [simulation dataset and DoE](docs/simulation-dataset-doe.md).

Version **0.7.2** introduces an **offline, conservative figure-configuration selection tool** `paper_figure_route` for 2–6 pre-approved curve or field/colorbar extraction configurations. It executes the existing `paper_figure_analyze` methods, compares bounded quality proxies, records all source/candidate manifests and abstains if results are weak, ambiguous or inconsistent. Inspired by ART of PIV's agentic estimator selection, **not a trained neural selector, PIV optical flow or autonomous ROI discovery**. Real-paper accuracy benchmarking and real-COMSOL physical verification remain **NOT_RUN**. See [adaptive figure routing](docs/adaptive-figure-routing.md).

Version **0.7.1** adds **offline mesh-aware diagnostics** for reviewer-supplied, 2D triangular meshes with nodal scalar values: input schema checks, piecewise-linear spatial comparisons with coverage and numeric error metrics, immutable hash-backed audit reports, and a read-only COMSOL MCP tool `mesh_native_analyze`. This is **not MNC ML**, COMSOL mesh export, automatic mesh repair or mesh independence certification. Tested with synthetic Python unit tests; real COMSOL integration and physical validation remain **NOT_RUN**. See [mesh-native diagnostics](docs/mesh-native-diagnostics.md).

Version **0.7.0** adds **offline paper-to-input intake**, requiring no COMSOL machine or connection. A standard-library-only CLI ingests the 12-column Chinese source ledger in CSV/JSON/ZIP format, distinguishes paper/figure/supplement/assumption sources, highlights potential numeric conflicts and missing/unrecognized units, retains all candidates, and emits reviewed-only `INPUT_DRAFT_ONLY` records. No value is automatically approved and **no simulation is executed**. Usage, limits and test instructions: [offline input intake](docs/offline-input-intake.md).



Version **0.6.0** adds a real **offline scientific figure evidence tool** `paper_figure_analyze` (PDF crop, RGB sampling, single-color plot tracing, colorbar-to-field inversion, optional local OCR). Install optional dependencies with `pip install -e ".[figure-analysis]"`; OCR additionally requires a local Tesseract executable. Read [figure evidence](docs/figure-evidence.md). Inputs/outputs are confined to `COMSOL_OUTPUT_ROOT`; every extraction is `digitized_estimate` and requires review. Synthetic software unit tests exist; published-figure accuracy and physical COMSOL validation remain **NOT_RUN**.


Version **0.5.1** adds [SST diagnosis and pressure validation](docs/sst-pressure-validation.md) and [cross-section dimension checks](docs/geometry-workflow.md#dimensions-across-sections-of-a-paper-figure).

Version **0.5.0** (RSI Infer/Evaluate strengthen, bounded harness RSI):

- Autonomy profiles `COMSOL_RSI_AUTONOMY=strict|assisted|auto` ([rsi-autonomy-profiles](docs/rsi-autonomy-profiles.md))
- Channels: official `doc_default_resolve`, figure `digitized_estimate`, peer `peer_range_prior`
- Endpoint sensitivity budget; DecisionRequest packing; harness retention heuristics (AgentVersion only)
- Digitized/peer never → `reported` / final Scientific PASS

Version **0.4.1**: MCP-only control; add on-disk **agent audit trail** (`.java` / Copy-as-Code snippets + step/progress logs under `COMSOL_OUTPUT_ROOT`) per official blog audit practice—see [agent audit trail](docs/agent-audit-trail.md). No dual bare-Java control path.

Version **0.4.0** (official agentic / Codex alignment, MCP-first):

- Position this package as an **external agent harness**, not Desktop Chatbot; Multiphysics Server ≠ COMSOL Server™
- Client–server status/license notes, connect smoke (`param_set`/`param_get`), MCP mapping of the public agent loop
- Copy-as-Code / live `properties()` discovery; bounded segregated/nonlinear tuning with KPI gates
- Docs: [agentic official alignment](docs/agentic-official-alignment.md), [nonlinear solver tuning](docs/nonlinear-solver-tuning.md)
- Blog ~25%/~30% speed claims remain `NOT_VALIDATED_BASELINE` only—never scientific VALIDATED

Version **0.3.6** (skill hygiene): operator docs state **generalizable rules only**. No trial names, workspace paths, wall-clock control numbers, paper figure IDs, or one-shot geometry recipes in the skill tree. Put case-specific runbooks under `COMSOL_OUTPUT_ROOT`.

Version **0.3.5** (SKILL_UPLIFT_GENERAL_20261029): SegregatedStep API true names (`subdtech`/`maxsubiter`); one-class solver ladder + telemetry classes; forensic≠builder partition A/B; HARD GATE persist after expensive steps; `BLOCKED_SOLVER` delivery matrix. Trial numbers remain forensic only.

- [CHT coupling and energy gates](docs/cht-coupling-energy-gates.md) — outlet `SOFTWARE_DOC_DEFAULT`; S0 requires Inflow + ConvectiveOutflow + Segregated sequence; copy solver **class** not counterpart node tags; missing HT outlet feature is a first-class BC gap before mesh
- Companion ERS: `decision-gate` / `paper-analysis` / `comsol-debug` / `validation` (NONPHYSICAL veto retained)
- Principles index: [docs/uplift-20261029/GENERALIZABLE_PRINCIPLES.md](docs/uplift-20261029/GENERALIZABLE_PRINCIPLES.md)

Version **0.3.2** institutionalizes **paper-silent → official software documentation** defaults for CHT (not a single-case exception):

- Hierarchy: paper explicit > installed official product docs (`SOFTWARE_DOC_DEFAULT`) > option cards / ask user > never GUI/prior-trial habit; counterpart MPH is post-solve compare only
- [CHT coupling and energy gates](docs/cht-coupling-energy-gates.md) — P0 `5b` Inflow default when paper silent; inlet thermal migration playbook (Temperature→Inflow) without greenwashing enthalpy
- Companion ERS policy lives in `paper-analysis` / `decision-gate` / `session-boot` (software-doc default)

Version **0.3.1** added CHT / compare hygiene docs (no new MCP tools; does not upgrade scientific VALIDATED status):

- [CHT coupling and energy gates](docs/cht-coupling-energy-gates.md) — inlet **Inflow** preference, coupling probe export, independent hydraulic vs enthalpy gates
- [Paper-only vs oracle compare](docs/paper-only-vs-oracle-compare.md) — counterpart labels (`Z_ORACLE` / `B_REPLICA` / `PAPER_FIGURE` / `NONE`); build vs compare phase separation

Mandatory global NITF velocity-wiring rewrite rules remain deferred pending clean probe evidence.

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
