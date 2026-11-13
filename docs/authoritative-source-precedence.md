# Authoritative Source Precedence & Evidence Gating — v0.7.6

## Goal and evidence policy

v0.7.6 codifies a **conservative default** for paper reproduction:

1. **Original paper's explicit numeric text and tables** outrank schematic-pixel estimates, graph-based inference and engineering assumptions for the **same physical quantity**, after source and quantity identity are reviewed.
2. **Original author-published supplementary material** is distinct from an outside paper, a related dissertation, a repository of unknown provenance or a record saying "supplement not obtained". Only acquired, source-attributed supplementary evidence is eligible for ranking.
3. **Externally sourced quantities** should preferentially come from authoritative institutions, recognized standards/curated databases, and relevant peer-reviewed research. An impressive publisher/impact factor alone does not demonstrate applicability. Material, flow regime, geometry, temperature, version, units and exact cited location must fit the target task.
4. **Quantitative original-figure curves** can supply **digitized estimates with uncertainty**, but do not silently outrank explicit text/table values. **Schematic proportions** are weaker still.
5. **ML outputs/virtual sensors** and engineering guesses may inform sensitivity and screening but are never identified as original-author reported values.

This is a **source-precedence rule, not an automatic truth selector**: errata, version changes, differing coordinate systems, different physical quantities, author text-table discrepancies or improperly marked sources all require explicit human investigation. No evidence of sufficient quality -> \`INSUFFICIENT_EVIDENCE\`.

## Existing input ledger integration

\`server/input_intake.py\` retains the 12-column Chinese source-ledger format, its reviewed alias mappings and explicit decisions. It now adds \`source_precedence_reviews\`:

- An *eligible numeric* origin-\`reported\` record, explicitly located in a **Table/paragraph/section** and with a positive review trace (e.g. "已核对"/"已回读"), is a direct-paper candidate.
- Given such a candidate for the **same paper::parameter** (including manually approved aliases), manually approving a pixel/figure estimate or engineering assumption **does not admit that lower-priority input**, even in \`engineering_completed\` mode. Reason: \`LOWER_PRIORITY_CANNOT_OVERRIDE_VERIFIED_PAPER_TEXT_TABLE\`.
- Different directly reported numeric values are flagged \`DIRECT_PAPER_CONFLICT_REQUIRES_REVIEW\`; a conflict is not silently solved by ranking.
- The original source ledger is unchanged. No numeric candidate is selected without an explicit reviewed decision; even a decision yields only \`INPUT_DRAFT_ONLY\`, never a physically validated COMSOL input.
- Vague/unreviewed "paper" labels do **not** establish explicit text/table superiority. Failure to identify a physical quantity or provide an alias remains a separate obstacle.

For example, for P008, if \`collector_channel_height\` is explicitly reported **1 mm** in the original paper and a schematic is interpreted as **approximately 1.5 mm**, the reported value is the default paper-reproduction candidate. Keep the 1.5 mm readout in the audit; do not automatically substitute it. First verify both measurements refer to the same feature and coordinate interpretation.

## New external evidence tool

\`source_precedence_review(source_path)\` is an offline reviewer-mode MCP tool. It reads a \`source-evidence/0.7.6\` JSON file **within \`COMSOL_OUTPUT_ROOT\`** and writes a separate UUID-named report to \`source-precedence/<uuid>/review.json\`.

Example (all values, references and SHA strings **synthetic placeholders**, not authenticated):

\`\`\`json
{
  "schema": "source-evidence/0.7.6",
  "case_id": "P008",
  "candidates": [
    {
      "id": "original_paper_height", "paper_id": "P008",
      "quantity": "collector_channel_height",
      "source_type": "PAPER_TEXT_TABLE", "value": 1, "unit": "mm",
      "locator": "page 14, last paragraph", "source_ref": "reviewed source PDF",
      "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "verification": "OPERATOR_REVIEWED",
      "conditions": {
        "material": "water", "regime": "laminar",
        "geometry": "P008 collector channel", "temperature": "298 K"
      }
    },
    {
      "id": "figure_schematic", "paper_id": "P008",
      "quantity": "collector_channel_height",
      "source_type": "SCHEMATIC_PIXEL", "value": 1.5, "unit": "mm",
      "locator": "Fig. 1 pixel estimate", "source_ref": "reviewed image extract",
      "source_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "verification": "OPERATOR_REVIEWED",
      "conditions": {
        "material": "water", "regime": "laminar",
        "geometry": "P008 collector channel", "temperature": "298 K"
      }
    }
  ]
}
\`\`\`

Allowed source types, in default ascending rank: \`PAPER_TEXT_TABLE\`, \`AUTHOR_SUPPLEMENT\`, \`INSTITUTIONAL_STANDARD\`, \`PEER_REVIEWED\`, \`FIGURE_CURVE\`, \`SCHEMATIC_PIXEL\`, then \`ENGINEERING_ASSUMPTION\` and \`ML_ESTIMATE\`.

### Required metadata for author supplements

For \`AUTHOR_SUPPLEMENT\`, additionally provide:

\`\`\`json
"supplement": {
  "obtained": true,
  "original_author": true,
  "version_ref": "official publication supplementary data v1"
}
\`\`\`

These are **operator assertions**. If not obtained, not from original authors, or not independently reviewed, the candidate is blocked. An outside peer-reviewed paper cannot masquerade as the original article's supplement.

### Required metadata for external authoritative sources

For \`INSTITUTIONAL_STANDARD\` and \`PEER_REVIEWED\`, provide:

\`\`\`json
"authority": {
  "issuer": "reviewed authoritative organization or journal",
  "identifier": "DOI, standard identifier or database accession",
  "version": "specific release / year / edition",
  "applicability": "MATCHED",
  "applicability_basis": "matching material, temperature, fluid regime and relevant definition"
}
\`\`\`

\`PARTIAL\` and \`UNREVIEWED\` applicability block promotion into the ranked eligible subset. Source-reported provenance and applicability are not equivalent to independently authenticated DOI/database records.

### Important limits

- A successful review never automatically selects or admits a value to the model. It produces \`REVIEW_REQUIRED\`, \`SAME_TIER_CONFLICT_REQUIRES_REVIEW\`, \`UNIT_OR_CONDITION_REVIEW_REQUIRED\`, or \`INSUFFICIENT_EVIDENCE\` per quantity. An explicit original text source is preferred only after physical identity and conditions match.
- The tool does not download the original article, verify web domains, DOIs or institutional credentials, independently confirm supplementary authenticity, or check a paper's scientific merit.
- It does not convert units, estimate numeric uncertainty, perform model validation or substitute ML predictions. \`ML_ESTIMATE\` is never a primary scientific data source.
- This tool reads *research source documents*, not screenshots of a commercial solver UI. All COMSOL actions continue to require officially supported MCP APIs and separate permission.
- Real-paper field validation, scientific verification and COMSOL execution: **NOT_RUN**.

Synthetic policy tests: \`python -m unittest tests.test_source_precedence tests.test_input_intake -v\`.
