# Underspec decision loop

Status: **P0 skill + gate text implemented**; `figure_colorbar_sample` offline tool is **P1 / NOT_IMPLEMENTED** until shipped; sensitivity child workflows are **P2**. Product policy **C** is locked.

| Mechanism | Basis | Support class |
|---|---|---|
| Underspecification to clarification | Kirchhof et al., ICML 2025 | LITERATURE_ADAPTED |
| Digitized is not reported | this repository (policy C) | DESIGN_POLICY |
| Sensitivity brackets without EXACT claim | this repository (policy C) | DESIGN_POLICY |
| Paper clue methods as candidates only | this repository | DESIGN_POLICY |

## Locked product policy (C)

| ID | Rule |
|---|---|
| P-C1 | Digitized values default to `digitized_estimate` with uncertainty; **not** `reported`. |
| P-C2 | Entering `SOLVING` for a **single** contested parameter requires `user_approved`, or clean `reported` / `derived` with no conflict. |
| P-C3 | If the user chooses **sensitivity**, run endpoints (optional mid) under `admit_with_sensitivity`; claims limited to bracket effects; **no** EXACT figure reproduction. |
| P-C4 | Epistemic repairs never auto-admit; mechanical API repairs may. |

## Gate behavior

Before geometry admit / study submit for high-impact gaps (`blocks_geometry`, `blocks_bc`, `blocks_claim`):

1. Build `EvidenceRecord[]` with origin, certainty, `paper_locus`, impact, conflicts.
2. Run PaperClueSearch (methods M01-M12 below); attach locus and origin; candidates only.
3. Call `underspec_report` (or equivalent DecisionGate path). On WAITING: emit `DecisionRequest[]`.
4. Present the request to the user; do **not** submit studies until `decision_resolve`.
5. `default_if_timeout` must stay **null** for high-impact items (no silent continue under AFK/deadline pressure).

## Admit paths

- `admit_single_value`: `origin in {reported, derived, user_approved}` and `certainty != conflict`, with no open conflict on that quantity.
- `admit_with_sensitivity`: user option `sensitivity` (or explicit approved value list); budget `max_bracket_jobs` (default 2 endpoints). Child cases tagged `SENSITIVITY_BRACKET` cannot promote the parent claim to `VALIDATED` / EXACT figure match.

## Digitization

Colorbar / axis / layer readings are intervals with uncertainty and origin `digitized_estimate`. Schema and ledger reject promotion to `reported`. Low-quality digitization yields `NOT_RUN` for that clue; still ask with textual clues. Hard rule: M03/M04 outputs never upgrade to `reported` without a textual number in the paper or explicit user confirmation that still keeps digitized provenance.

## Paper clue methods (candidates only)

| ID | Method | Typical use |
|---|---|---|
| M01 | Table vs equation cross-check | Envelope vs layer sums |
| M02 | Figure layer / scale bar | Stacking ambiguity |
| M03 | Colorbar digitization | Continuous maps without tables |
| M04 | Axis endpoint mining | Sweep panel ranges |
| M05 | Cross-figure consistency | Digitization sanity |
| M06 | BC phrase harvest | Tin, qw, outlet, walls |
| M07 | Material print vs library | eta(T), cp, k at Tin |
| M08 | Turbulence disclosure audit | Declared turbulence/wall-treatment labels → assumption_bundle |
| M09 | Caption operating-point parse | uin mismatch to QUALITATIVE |
| M10 | Experiment vs unit-CFD split | Validation figs without data to NOT_RUN |
| M11 | Supplement availability | DOI/SM; on fail keep MISSING |
| M12 | Volume/domain self-consistency | Fluid/solid volume vs envelope |

## Logging

Persist under `{COMSOL_OUTPUT_ROOT}/workflow-cases/<id>/underspec/`.
