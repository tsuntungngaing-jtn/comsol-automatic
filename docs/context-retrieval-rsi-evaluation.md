# Optional context retrieval and evidence-gated RSI (experimental)

This update preserves the MCP-only COMSOL controller. No Transformer can replace geometry, solver, conservation, or scientific validation. The extra modules do NOT run COMSOL.

## 1. Bounded context retrieval

Implementation: rsi/context_retrieval.py; API: RSIController.retrieve_experience_context().

Embedding-based retrieval reduces historical context **included in a prompt**, not the tokens already present in the active ChatGPT/Claude conversation.

- Defaults to deterministic lexical matching: no dependencies, no downloads, no network.
- Optional injected embedder must expose encode(list_of_texts). An optional locally loaded SentenceTransformer can be passed explicitly.
- Rejects held-out experiences; deduplicates texts; filters by task family; caps result count and character budget.
- Returns the originating experience_id and task_id with each snippet; tags text as untrusted historical context.
- Similarity does not imply a confirmed physical cause or authorization to mutate COMSOL.
- Indexes must be invalidated when source records, embedding weights, tokenizer or provenance change.
- Do not upload private papers or simulation results to third-party embedding services without permission.

Example:

    from rsi.controller import RSIController
    ctrl = RSIController('./workspace/rsi')
    hits = ctrl.retrieve_experience_context(
        'stationary SST residual plateau', task_family='fluid',
        max_records=4, max_chars=2000)

Optional embedding example (requires separately installing sentence-transformers and may download weights):

    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    hits = ctrl.retrieve_experience_context('SST residual plateau', embedder=embedder)

## 2. Independent Evaluate / Retain

Implementation: rsi/evaluation.py; API: RSIController.propose_and_gate().

**Breaking safety change**: the old API accepting old_metrics/new_metrics alone can no longer promote an AgentVersion. These kwargs remain accepted but are ignored as unverified. Without complete evidence the result is REJECT / NOT_RUN.

Evaluation requirements:

1. Freeze task IDs, specification, scientific metrics, physical conditions, materials and case-specific required checks before execution.
2. Compare the old and new agents on exactly the same held-out task IDs; held-out cases may not enter experience learning, retrieval or calibration.
3. Record distinct run IDs and immutable artifact hashes for the baseline and candidate.
4. Physical tasks require numerical, scientific, reopen, conservation and mesh-independence checks. Geometry tasks require numerical, scientific, reopen, geometry and selection checks. Declare any additional case-specific tests.
5. Every required check must have an observed PASS or FAIL for both runs. Any missing, NOT_RUN or BLOCKED check blocks the retention evaluation; these are not assigned a fabricated success score.
6. A trusted evidence_verifier callback must independently inspect real COMSOL MCP artifacts, hashes, run/study/solver/solution/dataset identity and the provenance of all scientific checks. A boolean field supplied by an LLM is not trusted. **A real COMSOL verifier is NOT_IMPLEMENTED in this branch**; without one, promotion is intentionally blocked.
7. Three paired tasks is only a software smoke-test minimum, not statistical evidence of scientific superiority. Preregister a larger representative benchmark with uncertainty and regression analysis.
8. Passing the evidence checks only admits metrics to the existing RetentionGate; it does not override scientific failures or establish independent replication.
9. Repeated tuning to held-out results contaminates the test. Lock the test set; use distinct development cases and a genuinely untouched final test set.

API sketch:

    result = ctrl.propose_and_gate(
        paired_heldout_cases=locked_pairs,
        evidence_verifier=verify_real_mcp_artifacts,
        min_cases=3,
    )

Each pair includes task_id, dataset_split='held_out', task_kind ('physical' or 'geometry'), spec_hash, required_checks, old and new observations. Observations include identity, evidence, checks, claimed_success, solver_calls, spec_hash, conditions_hash, materials_hash and metric_definitions_hash.

Mandatory identity fields: run_id, model_revision, study, solver, solution, dataset, parameters_hash. Evidence declarations: origin='real_comsol_mcp', artifact_sha256, collector_run_id. These declarations do not authenticate themselves.

## Tests and current validation status

Run: python -m unittest discover -s tests

Unit tests use stubbed evidence_verifier callbacks. They demonstrate software behavior only; never claim tested_with_real_COMSOL or scientific PASS on that basis.

Real COMSOL end-to-end independent verification: **NOT_RUN**. Effective retrieval quality on a large research corpus: **NOT_RUN**.

Measure retrieval Recall@k, effective prompt-token savings, science false-success rate, held-out paired task completion, conservation and mesh-independence coverage, solver calls, real wall time, and reopen identity validity.