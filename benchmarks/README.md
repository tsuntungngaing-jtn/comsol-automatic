# Reproducible validation and scoring

These original fixtures are separate from the existing official case catalog. Run COMSOL operations only through MCP. Software mocks establish behavior, not physical correctness. No generic-agent/skill/tutorial ablation has been run; no experimental scores are supplied.

## Software

Install with `python -m pip install -e ".[test]"`, then `python -m unittest discover -s tests`. On hosts with proxy interception, set `NO_PROXY=127.0.0.1,localhost` for local protocol tests. Validate each task with `simulation_spec_validate`. Build wheels with `python -m pip wheel . --no-deps -w <outside-directory>` and install/test from outside the checkout to check resource inclusion.

## Simulation machine entrypoint

1. `comsol_doctor`, `comsol_status`; start/reuse 6.4, read exact build and required products using the MCP Java API. Record Python/MPh/JPype/Java and source/spec hashes. Other versions require re-anchoring.
2. `model_create(name="<unique-run-id>", set_current=False)`. Load `benchmarks/mcp_cases.py` from this checkout through `comsol_model_code` using `importlib.util.spec_from_file_location`, then call `build(model, task_id)`. It rejects models with existing components.
3. Call `geometry_accept` with the task JSON's geometry requirements, plus dimension and unit. Call `selection_validate` for the contracts returned by `build`. For physical cases, invoke `configure_physics(model, task_id, local_basic_material_library_path)` through the same MCP code tool, then read back materials, boundary types/values/selections. This configures an original fixture, not an official Library reproduction.
4. Call `study_solve_async(model_name=...)`. Poll the returned job ID until completion/failure. Call `evaluate(model, task_id)` via MCP. Compare observables with task references, including conservation. Record `model.problems()`, actual solver criteria and mesh. A completed job does not imply a PASS.
5. Save a new MPH, hash it, `model_load` separately, inspect identity with Inspector, and reevaluate the same metrics. Record reopen differences and exact model identity. Do not reuse an old CSV.
6. For parameter tasks, use `geometry_perturb` and `perturbations.json`. Create the stated physical bindings first. For rotation select the raised asymmetric marker top using z bounds 1.249999 to 1.250001 mm and baseline theta=0 deg; check its full xyz box and the whole-body box. The off-center marker distinguishes rotation from mere translation of a symmetric block. For array topology use a Box domain selection around the full array and contracts of 3 then 5 domains, bound by name.
7. For CAD, export the original simple block to STEP through MCP (`geom.export(path)`), then import in a fresh tracked model with `geometry_import_cad`. Require source units mm, geometry mm, source-unit policy, explicit union/internal boundaries/repair/pairs. Use the CAD task's metrics. This fixture proves only simple STEP BRep import; complex assemblies, contact and other formats remain separate required tests.

The `boolean_channel` fixture subtracts a through-bore and checks volume, domain count and finite void count. These bounded checks do not prove arbitrary channel connectivity; task-specific inlet/outlet and blockage evidence is still required for a real fluid device.

## Reports and experiments

Create a report with `server.contracts.new_report`; populate separate API, geometry, selection, physics, numerical, scientific and reopen layers. Each layer contains checks with status and evidence; unknown/unsupported data remains explicit. `simulation_spec_validate(kind="validation-report")` rejects contradictory success. Scientific reproduction stays NOT_RUN unless actual claim-level evidence exists.

Score a report with `python -m benchmarks.score <report.json>`. It reports per-layer pass fractions **and coverage**, null scores for absent evidence, final objective errors, independent false-success judgments and repair-only cost. Tree similarity is diagnostic only. Supply `tool_claims` with independent outcomes; the scorer does not fabricate a ground truth from the tool's own success flag.

Generate a controlled trial manifest:

```text
python -m benchmarks.experiment --model EXACT_MODEL_ID --tool-environment-sha256 HEX64 --repeats 3 --max-tool-calls 100 --max-solves 4 --seconds 1800 --output experiment.json
```

The four conditions keep the same model/tool/task/environment/budget, adding skill, versioned tutorial, then acceptance instructions. Execute each condition in a fresh context/model with seeded randomized order. Log mandatory builds/solves separately from repair operations using `repair_event`; count true tool executions and solver invocations, elapsed time and stop reason. The manifest is a configuration, not an agent orchestrator. No external agent API credentials or unrequested orchestration are introduced.

The papers named in the request were not available as matching local attachments during this implementation. No quotations or performance numbers are attributed to them. Layer separation and tutorial/feedback experiments are evaluation design choices; neither proves complex CAD reliability or agent performance.
