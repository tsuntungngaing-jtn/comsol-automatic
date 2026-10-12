# Selection contracts

Prefer component named selections, geometry-generated selections, or existing `geometry_create_box_selection` spatial rules over saved entity numbers. A contract has `id`, `tag`, entity `dimension`, `count` (`reference` or `[min,max]` range), `allow_empty`, physical `purpose`, optional `measurements` and `bindings`.

```json
{"id":"inlet","tag":"inlet","dimension":2,"count":{"reference":1},
 "allow_empty":false,"purpose":"Prescribed inflow",
 "measurements":[{"metric":"area","reference":2,"atol":0.000001}],
 "bindings":[{"physics":"spf","feature":"inl","type":"InletBoundary"}]}
```

`selection_validate` reads the current dimension/entities, checks current build diagnostics, compares optional bounding box/area/volume and checks effective entities on each physical feature. A missing tag, wrong count, stale geometry or mismatched binding fails. Re-run it after every topology change; do not reuse its entity list as a future contract.

`selection_bind_checked` rebuilds geometry, checks the contract before assignment, binds with `selection().named(tag)` and reads effective entities again. A failed precondition leaves the physics binding untouched. A failed postcondition reports failure and may leave the new binding; inspect it before solving. Matching entity lists alone does not verify a boundary's numerical values, units, equations, material assignment or coupling. Include those in the physical validation layer.

Use separate contracts for inlet, outlet, heater, fluid, solid and interface. Add area/location checks to distinguish equally sized selections. Count alone is weak evidence. For Assembly contacts, verify actual pair source/destination/contact relations separately: this generic selection validator does not infer contact correctness.
