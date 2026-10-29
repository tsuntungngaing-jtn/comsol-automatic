# HARD GATE — persist after every expensive COMSOL step

Version **0.3.5** institutional rule (from SKILL_UPLIFT_GENERAL_20261029).

1. Before a long solve: `model_save` with **`file_path`** (schema name — **not** `path`) under **`COMSOL_OUTPUT_ROOT`**. Failure ⇒ STOP; do not solve.
2. After solve success: save `*_solved.mph`; verify the file exists on disk.
3. “study completed” without an mph on disk = **not delivered**.
4. Unwrap tool payloads: business fields often live under `result`; top-level `ok` may be absent.
5. A new MCP stdio session cannot recover unsaved in-memory models from another session.

Script shape: `save_pre → assert success → solve → save_solved → assert exists → eval`.
