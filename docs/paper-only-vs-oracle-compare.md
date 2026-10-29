# Paper-only build vs oracle compare

Separates **construction from paper evidence** from **authorized post-build comparison** to a frozen counterpart.
Never use Zhang / Blind / benchmark MPH as a modeling template.

## Two phases

| Phase | Allowed inputs | Forbidden |
|-------|----------------|-----------|
| **Build (paper-only)** | Paper text/figures/tables, user decisions, manuals, ledger origins | Oracle Ain, entity IDs, settings cards, Blind MPH trees as build recipes |
| **Compare (authorized)** | Built model outputs vs declared counterpart QoI | Claiming paper-only VALIDATED from Blind field likeness alone |

Build must finish (or fail honestly) before compare. Compare never rewrites geometry/physics to match oracle.

## Counterpart labels (must match SESSION_CONFIG)

| Label | Means | Must not be used to claim |
|-------|-------|---------------------------|
| `Z_ORACLE` | Independent frozen QoI/settings | Paper-only geometry was copied correctly |
| `B_REPLICA` | Same-lineage re-solve ≈ oracle | Skill reconstructed the paper from text |
| `PAPER_FIGURE` | Visual/digitised figure | Exact scalar VALIDATED |
| `NONE` | No counterpart | — |

Blind-replica TypeI/II field montages that match oracle panels only support `B_REPLICA`, not paper-only success.

## Oracle nine-case compare hygiene

1. Declare the case matrix labels the user authorized (e.g. IT/LT) with disclosure; do not silently expand the matrix.
2. Same metric definitions, units, and dataset identity for each compared case.
3. Report missing cases as `NOT_RUN`, not as PASS by omission.
4. Keep software reopen checks separate from scientific QoI match.
5. Report gates separately: `GATE_DP` vs `GATE_ENTHALPY` vs `GATE_TW_HEFF`. Hydraulic MATCH with enthalpy FAIL → PARTIAL/CONDITIONAL, never single green PASS.
6. Forbidden in build phase: reading oracle Ain, named entity IDs, BL face lists, or settings_card into geometry/physics builders. Allowed: case matrix labels user explicitly chose (e.g. IT/LT as USER_SPECIFY targets) with disclosure.

## Related

- ERS `session-boot` / `templates/SESSION_CONFIG.md` (`compare.counterpart`)
- ERS `validation` independent gates
- `docs/cht-coupling-energy-gates.md`
## Forensic CAD / oracle geometry (institutional) — 0.3.5

After blind build, a STEP/volume/bbox diff vs benchmark is **forensic only**:

- Record “geometry family differs” (e.g. lateral fluid span, V_fluid delta).
- **Do not** set builder targets to oracle volumes or entity tags.
- Re-open **decision-gate** with **paper** evidence only (partition A/B, inlet face class, …).
- Same-recipe CAD↔COMSOL match proves **implementation consistency**, not paper correctness.

| Do not | Why |
|--------|-----|
| Align `V_fluid` to benchmark | Peek-fix |
| Treat SW≡COMSOL as paper PASS | Same silent wrong recipe |
| Call discrete partition ΔV a “round-off” | Wrong failure class |

Round-off vs semantics: measured Ain/size vs the **same** formula at ~1e-12…1e-15 relative error is float; fluid bbox jumping to `0`/`wunit` vs indented `ww`, or clean integer mm³ fluid↔solid swap, is **lateral partition A/B** — reopen decision-gate, do not call it round-off.

