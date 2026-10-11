# Read-only Inspector
Start with status and an explicitly named tracked model. `inspect_current_model` and `get_model_tree` report identity, parameters, component trees, geometry, selections, materials, physics, mesh, study, solver and datasets. They do not build, solve, evaluate or save. Use narrower sections and limits for large models.

Retain provenance paths, disabled nodes and truncation statuses. Own/ancestor activity is not equivalent to study activation or effective boundary equations. LaminarFlow raw type alone does not determine whether turbulence options are enabled. Empty or absent solution data must not be called converged. Inspector does not identify the active Desktop document and has no automatic Audit/Diff/Diagnosis guarantee.
