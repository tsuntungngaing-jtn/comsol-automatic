# Where principles land

When merging: **keep existing rules, fill gaps and fix wrong API names**; do not wholesale-overwrite and lose prior institutional clauses.

| Principle | Live landing | Notes |
|-----------|--------------|-------|
| G0 three layers / forensic | `paper-analysis`, `geometry-reconstruction`, `decision-gate`, comsol `paper-only-vs-oracle-compare.md` | Build ≠ compare |
| G1 SOFTWARE_DOC_DEFAULT | `paper-analysis`, `decision-gate`, comsol `cht-coupling-energy-gates.md` | Align SegregatedStep property names |
| G2 fluid partition A/B | `checklists/fluid-partition-gate.md`, `paper-analysis`, `geometry-reconstruction`, `decision-gate` | Explicit option card |
| G3 hydraulic vs thermal gates | `validation` | PARTIAL allowed |
| G4 solver ladder | `comsol-debug`, `cht-coupling-energy-gates.md` | One class per attempt |
| G5 persist | `delivery` / `persist-hard-gate.md` | No mph ⇒ not delivered |
| G6 BLOCKED | `comsol-debug`, `validation`, `cht-coupling` | Legal scientific status |

## Suggested paste order

1. Checklists (whole files)
2. Persist hard gate
3. `cht-coupling-energy-gates` S2–S5 + `subdtech`
4. `comsol-debug` ladder pointer
5. `paper-analysis` / `geometry-reconstruction` / `decision-gate` partition + forensic
6. `validation` separate gates + BLOCKED matrix

## Acceptance (generalization)

On **another** microchannel paper (different authors, different geometry family), can the operator answer:

- [ ] Will work stop if lateral A/B is undecided?
- [ ] What HT inlet feature label is used when the paper is silent?
- [ ] What are the true SegregatedStep damping property names?
- [ ] Does a finished solve without an mph count as delivery?
- [ ] May a counterpart volume delta rewrite the builder?
