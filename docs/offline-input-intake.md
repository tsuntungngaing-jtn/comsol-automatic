# Offline paper input intake (v0.7.0)

**No COMSOL machine, COMSOL licence, JVM, MCP session, solver or study is needed.**
This tool is a conservative pre-simulation input review, NOT simulation or scientific validation.

## Usage

Run directly from the repository root using Python 3.10+ standard library:

```bash
python -m server.input_intake --source "/path/to/source_rows.json" --output-root "/path/to/research-workspace"
python -m server.input_intake --source "/path/to/四机文章信息来源_20261112.zip" --output-root "/path/to/research-workspace"
python -m unittest tests.test_input_intake
```

Accepted input: CSV with the twelve Chinese headers from the source ledger, JSON array containing header+rows or objects, or ZIP with a single `source_rows.json`. The original ledger is never modified or uploaded. A new `offline-input-audit/<uuid>/input_audit.json` is written each run, including source SHA-256.

## Safeguards and output

- All 12 columns are retained as provenance and audit metadata; no spreadsheet formula is evaluated.
- Values are classified as numeric / array / expression / text / missing. Numeric inputs with missing or unrecognized units are NOT compiled.
- Limited explicit conversion covers mm/m/µm, Pa/kPa, kelvin/°C, and dimensionless '1'. Unknown or composite units (e.g. "SI；单位见参数名/原文") stay `UNREVIEWED`; no unit is guessed from a parameter name.
- Paper numeric records, image estimates, engineering assumptions and supplementary statuses keep distinct origins.
- Unobtained/unverified supplementary records NEVER become numeric evidence merely because their category says "supplementary".
- No automatic synonym matching or semantic identity inference. Two distinct fields may describe the same physical quantity; provide an operator-reviewed alias map after confirming physical meaning.
- Exact same `paper::parameter` repeated with incompatible scalar values (after recognized unit normalization) raises a potential conflict. Mixed text/numeric representations are flagged. No automatic winner chosen.
- No candidate becomes `admitted_input_drafts` without explicit decision and explanation. Even approved candidates are marked `INPUT_DRAFT_ONLY` and cannot be claimed as executed COMSOL inputs.
- The `paper_faithful` mode rejects non-reported candidates. In `engineering_completed` mode an explicitly reviewed engineering/digitized candidate may be drafted, but its source stays unchanged.
- `scientific_validation=NOT_RUN`, `simulation_execution=NOT_RUN`; no model is built, run, or validated.

Example operator-reviewed alias file `aliases.json` (never automatically generated):

```json
{"P008::channel_height_from_Fig1_pixels": "P008::collector_channel_height"}
```

A potential conflict appears once both values refer to the *same explicitly reviewed physical quantity*. The original keys remain in each candidate.

Example `decisions.json`:

```json
{
  "P008::collector_channel_height": {
    "approved": true,
    "candidate_id": "row-00002",
    "reason": "Reviewed explicit tabular height; retaining source provenance"
  }
}
```

Invoke with `--aliases aliases.json --decisions decisions.json`. Row IDs are specific to a single intake; inspect the freshly generated candidate list before choosing. For scientific use, separately verify the original PDF, source location, definitions (Darcy vs Fanning, geometry topology, Reynolds number, thermal averaging), assumptions, and effective COMSOL settings after a later authorized build.

This v0.7.0 module **does not** infer semantic aliasing, fully parse physical formulae, accept compound-unit scalars, automate text extraction, or perform a physical run. Uncertainty fields are preserved as source text; no confidence interval is fabricated.

## Offline synthetic tests

`python -m unittest tests.test_input_intake`

Test cases cover manual admission, units, contradictory values, reviewed aliases, missing supplements, formulas, unknown units, engineering mode and ZIP ingestion. No benchmark in this release establishes true published-paper extraction accuracy or real-COMSOL reproducibility.
