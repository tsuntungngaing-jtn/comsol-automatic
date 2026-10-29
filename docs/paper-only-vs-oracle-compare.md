# Paper-only build vs counterpart compare

Separates **construction from paper evidence** from **authorized post-build comparison** to a frozen counterpart.
Never use a counterpart MPH, benchmark MPH, or prior-trial model tree as a modeling template.

## Two phases

| Phase | Allowed inputs | Forbidden |
|-------|----------------|-----------|
| **Build (paper-only)** | Paper text/figures/tables, user decisions, manuals, ledger origins | Counterpart Ain, entity IDs, settings cards, prior-trial MPH trees as build recipes |
| **Compare (authorized)** | Built model outputs vs declared counterpart QoI | Claiming paper-only VALIDATED from field-likeness to a counterpart alone |

Build must finish (or fail honestly) before compare. Compare never rewrites geometry/physics to match the counterpart.

## Counterpart labels (must match SESSION_CONFIG)

| Label | Means | Must not be used to claim |
|-------|-------|---------------------------|
| `Z_ORACLE` | Independent frozen QoI/settings pack | Paper-only geometry was copied correctly |
| `B_REPLICA` | Same-lineage re-solve ≈ counterpart | Skill reconstructed the paper from text |
| `PAPER_FIGURE` | Visual/digitised figure | Exact scalar VALIDATED |
| `NONE` | No counterpart | — |

Label strings are opaque session enums (kept for config compatibility). They do **not** authorize naming or copying any particular trial’s MPH, tags, or volumes into the builder.

Field montages that match a counterpart only support `B_REPLICA`, not paper-only success.

## Compare hygiene (any case matrix)

1. Declare the case-matrix labels the user authorized, with disclosure; do not silently expand the matrix.
2. Same metric definitions, units, and dataset identity for each compared case.
3. Report missing cases as `NOT_RUN`, not as PASS by omission.
4. Keep software reopen checks separate from scientific QoI match.
5. Report gates separately: `GATE_DP` vs `GATE_ENTHALPY` vs `GATE_TW_HEFF`. Hydraulic MATCH with enthalpy FAIL → PARTIAL/CONDITIONAL, never single green PASS.
6. Forbidden in build phase: reading counterpart Ain, named entity IDs, face lists, or settings cards into geometry/physics builders. Allowed: case labels the user explicitly chose as USER_SPECIFY targets, with disclosure.

## Related

- ERS `session-boot` / `templates/SESSION_CONFIG.md` (`compare.counterpart`)
- ERS `validation` independent gates
- `docs/cht-coupling-energy-gates.md`

## Forensic CAD / counterpart geometry

After a paper-only build, a STEP/volume/bbox diff vs a benchmark is **forensic only**:

- Record “geometry family differs” (e.g. lateral fluid span, V_fluid delta).
- **Do not** set builder targets to counterpart volumes or entity tags.
- Re-open **decision-gate** with **paper** evidence only (partition A/B, inlet face class, …).
- Same-recipe CAD↔COMSOL match proves **implementation consistency**, not paper correctness.

| Do not | Why |
|--------|-----|
| Align `V_fluid` to benchmark | Peek-fix |
| Treat SW≡COMSOL as paper PASS | Same silent wrong recipe |
| Call discrete partition ΔV a “round-off” | Wrong failure class |

Round-off vs semantics: measured Ain/size vs the **same** formula at ~1e-12…1e-15 relative error is float; fluid bbox jumping to full width vs wall-indented span, or clean integer-unit fluid↔solid swap, is a **lateral partition decision** — reopen decision-gate, do not call it round-off.
