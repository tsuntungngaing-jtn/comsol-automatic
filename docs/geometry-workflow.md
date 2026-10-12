# Geometry workflow

The baseline is commit `a012b21bcfd604adb8843f3b0e734478fc13b4a3`. Existing convection, inlet, material, save confinement and wheel repairs remain in place. This extension adds acceptance capabilities without replacing Inspector, the serialized JVM runtime, asynchronous jobs or license checks.

## Construction and units

`geometry_add_feature(properties={...})` accepts an explicit property map over MCP. Legacy direct Python keyword properties still work. The response separates `creation_status`, `configuration_status` and `build_status`, and exposes each requested property, write status, available readback and error. A write accepted by COMSOL is not a built geometry. Failed nodes are retained with their tag for explicit correction/removal; no rollback is promised.

Primitive numeric lengths retain the original documented meter convention: `0.001` becomes `0.001[m]`, even inside millimeter geometry. Strings are passed unchanged: `w`, `2[mm]`, `2*w` retain parameter dependence. Bare numeric strings follow COMSOL's current geometry unit. Use explicit unit expressions when crossing interfaces. Dimension/finite-value errors are rejected before primitive creation. A subsequent COMSOL property error may retain the named partial primitive.

## Acceptance

Call `geometry_accept(requirements, model_name, rebuild=True)` only when a rebuild is authorized. It reads feature diagnostics, final dimension/unit, entity counts, bounding boxes, area, volume and length. Measurements use the **geometry length unit and its powers**, not automatically SI. Entity counts are indexed by dimension (0 vertices through 3 domains). Bounding boxes use `measureFinal().getBoundingBox()`; `sequence_bbox` exposes the broader GeomInfo box for diagnostics. The CAD kernel may pad the latter (observed 0.0025 mm on the STEP fixture). Bounding boxes are `[xmin,xmax,ymin,ymax,zmin,zmax]`.

Example requirements:

```json
[{"metric":"unit","reference":"mm"},
 {"metric":"volume","reference":6000,"rtol":0.000001},
 {"metric":"bbox","reference":[0,10,0,20,0,30],"atol":0.00001},
 {"metric":"count_3","reference":1}]
```

`atol + rtol*abs(reference)` is the comparison threshold. Never derive a tolerance by fitting a target result; specify it according to measurement precision and engineering purpose. Actual 6.4 geometry measurements on small meter-scale solids differ by about 1e-7 relative from exact primitives; the benchmark uses 1e-6 for this geometric check, separately from solver tolerances.

Unknown metrics (including general connectivity, blockage, contact, arbitrary directional vectors) return `NOT_RUN` with the failed evaluator. For orientation, use task-specific asymmetric geometry and measured positions of named tip/base faces. A rotation node alone is no evidence. Optional checks can set `required:false`; required unavailable checks prevent a PASS. Invalid or stale feature states and unresolved messages fail acceptance. Disabled feature diagnostics are conservative and may need a task-specific review.

## Perturbation

`geometry_perturb` operates on `comp1/geom1`, saves a unique recovery MPH before changes, varies only declared existing parameters, rebuilds and compares each variant with its own explicit requirements and selection contracts. `relations` support explicit `ratio` or `difference`, with a supplied reference/tolerance; no linearity is inferred. `associations` record parameter/feature/selection/physics dependencies. All original parameter expressions are restored in `finally`, then the baseline geometry and selections are checked again. Rebuilding invalidates solutions: old solution restoration is **not** claimed. Recover a failed restoration by loading the baseline artifact separately.

See `benchmarks/perturbations.json` for width, device count and 180-degree rotation. Selection contracts must include relevant physical bindings for multiphysics tasks; empty contracts only establish geometry behavior.

## CAD workflow

`geometry_import_cad` requires a fresh geometry tag in a tracked model, real version/license readback, a source path and explicit source/geometry unit, unit policy (`source` or `current`), transforms, repair tolerance/actions, Union/Assembly, internal-boundary and pair strategy, and acceptance requirements. It records a SHA-256 of the source and saved MPH plus an external provenance JSON. Supported transforms are Move (`displ`), Rotate (`axis`,`pos`,`rot`) and Scale (`factor`,`pos`), applied in order. Their values remain COMSOL expressions.

The 6.4 path uses Import `unit=source|current`, `importtol`, documented repair actions, optional explicit Union `intbnd`, and Finalize `action/createpairs/pairtype`. Check the local CAD Import Module manual, `cad_ug_ref.6.21.html`, and COMSOL API Finalize `comsol_api_geom.48.090.html`. Other versions return BLOCKED pending re-anchoring. Missing CADIMPORT entitlement returns BLOCKED before node creation. Unsupported mesh formats fail this BRep workflow. Source-unit declarations are provenance, not proof: final dimensions must independently match the specification.

Native geometry retains its COMSOL feature parameters. Imported CAD retains editable import/transform/repair features and resulting BRep, **not** the external CAD program's original feature tree. Imported meshes require a separate workflow. Pair presence does not establish valid contact; required contact checks without a task-specific evaluator return NOT_RUN. Failure retains an isolated partial sequence with explicit identities.

## Limits

Checked tools are an opt-in guarded route. Legacy/raw Java calls can bypass contracts; this is not a sandbox or universal solver gate. Before solving, validate every relevant selection and physical configuration. Inspector continues to report facts and does not certify equations, conservation or paper claims.

Curved-body caution: the cylinder fixture returned a geometry volume differing from its analytic reference by approximately 7.3e-4 relative (combined block/cylinder). The strict check failed. Do not assume `measureFinal` gives an exact analytic measure for every kernel/body; retain the failed check and obtain an independent validated measure when needed.

See [version and measurement compatibility](version-compatibility.md). Official 6.4 Measurement Methods documents polygonal approximation. Set `require_exact:true` on a measure to demand a separate exact evaluator; this route returns NOT_RUN instead of claiming exactness.
