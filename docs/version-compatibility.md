# COMSOL version and measurement compatibility

The verified runtime is COMSOL 6.4 build 293, MPh 1.4.0 and JPype 1.7.1. The new checked MCP geometry workflows query `ModelUtil.getComsolVersion()` before executing. A different or unreadable major/minor version returns `BLOCKED / VERSION_MISMATCH`; offline schema validation remains independent. Legacy tools retain their existing scope and do not inherit blanket compatibility claims.

| Operation | 6.4 reference | Local finding / policy |
|---|---|---|
| Measurement semantics | [Measurement Methods](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_geom.48.047.html) | Volume/area/length are polygonal approximations corresponding to fine rendering detail. `require_exact:true` returns NOT_RUN; never claim analytic precision. |
| Current object selection | [Selecting Objects and Entities](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_geom.48.048.html) | `measure().selection().init(dim)` applies to object measurements. It is not interchangeable with final mesh/entity selection. |
| Final entity selection | [GeomMeasureFinal](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/api/com/comsol/model/GeomMeasureFinal.html), [Selection](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/api/com/comsol/model/Selection.html) | Actual `measureFinal().selection().geom(dim)` then `all()`/`set(ids)`. Using `init` was rejected by the actual final-selection API. |
| Entity counts | [GeomInfo](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/api/com/comsol/model/GeomInfo.html) | `getNEntities()[dimension]`; geometry units on bbox/measures. |
| Named selection dimension | [AbstractSelection](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/api/com/comsol/model/AbstractSelection.html) | `dim()` is scalar. `dimension()` returned an array; the adapter uses `dim()`. |
| CAD Import | [CAD API Import](https://doc.comsol.com/6.4/doc/com.comsol.help.cad/cad_ug_ref.6.21.html) | `unit=source|current`, `importtol`, documented repair fields; simple STEP tested. |
| Finalize | [Finalize](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_geom.48.090.html) | Union/Assembly and pair settings are explicit. Union exercised; assembly/contact correctness NOT_RUN. |
| Turbulent inlet | [CFD inlet](https://doc.comsol.com/6.4/doc/com.comsol.help.cfd/cfd_ug_fluidflow_single.06.032.html) | Actual `InletBoundary` exposes IT_list/LT_list; the different `Inlet` type did not. Do not substitute names merely because both create nodes. |

Local documentation is under `<COMSOL_ROOT>/doc/help/wtpwebapps/ROOT/doc/` with the same paths as the linked pages. Commercial manual contents are not bundled. These are method/semantic references, not performance claims.

The cylinder strict-volume failure is consistent with the documented approximate measurement method. Geometry size/unit validation passed, but exact curved-volume validation needs an independently validated numerical integration or other suitable evaluator. The code reports this limitation; it does not adjust results or loosen supplied tolerances.

For 6.2, 6.3 or a later release, obtain that installation's docs, inspect method/property availability and active physics options, rerun the fixtures and save/reopen checks, then deliberately extend the gate with version-specific evidence. Successful node creation alone is insufficient to change the policy.

The laminar-flow manual, `com.comsol.help.cfd/cfd_ug_fluidflow_single.06.008.html`, documents default P1+P1 interpolation and higher-order alternatives. The tested fixture retains this default and its failing mass-balance result. No unverified mapping from integer `order_fluid` options to named discretizations is assumed; a future refinement study must confirm that mapping and retain streamline diffusion where required.
