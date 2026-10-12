# Geometry reliability validation results — 0.2.0

## Baseline and implementation scope

The actual remote HEAD on 2026-10-12 was `a012b21bcfd604adb8843f3b0e734478fc13b4a3`. Work used independent branch `codex/geometry-validation-20261012` in a fresh clone. No AGENTS.md was present. The prior 0.1.1 heat-flux/inlet/material/save/wheel fixes were retained; all 38 baseline tests passed. No production connector was replaced, research data uploaded, release published or default branch pushed.

Confirmed geometry faults: swallowed generic-property exceptions; numerical meter inputs interpreted in geometry units; `len(JavaFeatureList)` failing automatic tags; MPh `create` receiving the feature name as an extra positional Java argument. All four were repaired. The generic MCP interface now exposes an explicit `properties` object while preserving direct Python keyword callers.

New modules implement pure schema/semantic checks, conservative layered statuses, final geometry acceptance, current selection contracts/guarded binding, recoverable perturbations and CAD provenance. Six MCP tools use the existing serialized JVM runtime. Schemas/tutorials/benchmarks are included in wheels and source ZIPs. The existing 47-case catalog remains unchanged.

## Real environment and evidence

COMSOL Multiphysics 6.4 build 293, MPh 1.4.0, JPype 1.7.1, Java 21.0.7, Python 3.12.14. Product queries for COMSOL, HEATTRANSFER, CFD, MATLIB and CADIMPORT returned true; this is not a full license inventory. All real operations went through the active MCP connection. New checkout modules were imported through its trusted code tool; the production installation stayed unchanged. Independent protocol tests exercise the new server registration.

Evidence resides outside the source distribution in the sibling `comsol-geometry-evidence` directory: original/failed and repaired API results, parameter recovery snapshots and reports, CAD provenance and hashes, four solved MPH files, configuration readbacks and independently reopened evaluations. Raw models and commercial resources are excluded from the skill ZIP.

| Check | Actual result | Scope |
|---|---|---|
| Mixed numeric/expression block in mm geometry | PASS: 0.001 m × w=2 mm × 3 mm measured 6 mm³ | Numeric unit and parameter retention |
| Cylinder in mm geometry | Dimension/unit PASS; strict volume FAIL (12.2742481 versus 12.2831853 mm³ including the block) | Official manual documents polygonal approximation; exact measure remains unverified; no tolerance relaxation |
| Invalid generic property | Expected FAIL with partial node tag, requested value, error and readback | No false configuration success |
| Width 10 to 20 mm | PASS: 2000 to 4000 mm³; named temperature face binding retained; baseline restored | Geometry and selection binding |
| Array 3 to 5 devices | PASS: domain count and volume change; named heated-domain binding re-resolves from 3 to 5; restored | Topology-changing selection |
| Rotation 0 to 180 degrees | PASS: raised off-center marker and body boxes move to specified coordinates; restored; a translation-only negative control passes the body box but FAILS the marker contract | Position/orientation evidence, no mere node-existence test |
| Boolean through-bore fixture | PASS volume 30 mm³, one domain and zero finite voids | Bounded topology check; arbitrary connectivity remains unverified |
| STEP block import | PASS: final bbox [0,10,0,20,0,30] mm, volume 6000 mm³, one domain | Simple BRep only; source/result hashes and repair/unit/finalization provenance |
| Conduction | PASS bounded numerical checks: mean 343.15 K, heat flow 400 W, imbalance 1.79e-14 | Copper library, prescribed temperatures |
| Solid convection | PASS bounded checks: mean surface 309.816666667 K, input 0.1 W, imbalance 3.09e-11 | HeatFluxBoundary regression |
| k-epsilon channel | PASS mass-balance regression: imbalance 1.15e-16; no reported model problems | Does not establish turbulence accuracy or mesh convergence |
| Laminar channel | FAIL mass balance: 5.633e-4 exceeds 1e-6 threshold; mean velocity 0.00997077 m/s | Completed solve is deliberately not counted as physical PASS |
| Independent reopen | PASS: all four saved physical models reproduce evaluated metrics with zero observed difference | Re-evaluation, not a fresh solve or mesh study |

A bounded laminar repair tightened stationary tolerance from 1e-3 to 1e-7 and performed one additional solve. Mass imbalance remained 5.633e-4. The threshold was not relaxed; refinement/stabilization analysis remains follow-up work. The saved baseline/reopen evidence remains the first solve, and the repair result is recorded separately.

CAD acceptance initially failed because GeomInfo's sequence bbox included a 0.0025 mm kernel pad. Direct comparison with final-entity `measureFinal().getBoundingBox()` returned the exact block bounds. The evaluator now uses final-entity bbox; `sequence_bbox` remains available as a diagnostic. The original failure is retained. Small meter-unit primitive measure error (~1e-7 relative) is covered by a documented 1e-6 geometry-measure tolerance, separate from PDE criteria.

## Software verification

The suite extends the 38 baseline tests with unit/expression and dimension checks, property write/read failures, missing/unknown evidence, empty-selection binding prevention, baseline restoration on a failed build, license-blocked CAD, report contradictions, task schema checks, bbox API regression and absent-score behavior. Mock tests are explicitly labeled and do not establish physics. Real stdio discovery checks all six new tools, the generic property map input, schema failure output and missing-model BLOCKED propagation; existing HTTP/SSE/authentication tests remain.

The final software suite ran 56 tests successfully. Independent wheel installation outside the checkout discovered 114 tools and loaded schemas, vendor, examples, benchmarks and tutorials. Exact final wheel/release hashes are included in the external delivery manifest. No benchmark agent-condition results are invented.

## NOT_RUN / limitations

Complex external assemblies; imported-mesh workflow; general connectivity/blockage/contact proof; CAD formats other than the simple STEP fixture; Assembly pair correctness; nonidentity CAD transforms as a combined import workflow; mesh convergence; transient conservation; broad multiphysics and scientific paper reproduction; complete agent ablations and statistical performance comparisons remain NOT_RUN. Unsupported required metrics block acceptance. Raw/legacy operations can bypass opt-in contracts and remain the operator's responsibility.

The two named research papers were not located as matching supplied attachments. No quotations, scores or claims of performance reproduction are made. In particular, these tests do not generalize a finite-element benchmark into complex CAD support.

Formal research use requires passing the task-specific selection, materials, physics, conservation, mesh and claim checks. The package is usable for modeling and validation development, but this report is not blanket authorization of unvalidated scientific results. Follow `benchmarks/README.md` for simulation-machine execution.

The official 6.4 Measurement Methods reference confirms approximate polygonal volume/area/length semantics. See [version compatibility](version-compatibility.md) for the API matrix and explicit non-6.4 gate.
