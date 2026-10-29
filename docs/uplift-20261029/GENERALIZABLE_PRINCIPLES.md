# Generalizable principles (cross-paper)

Applies to **any** microfluidic / MMC / CHT paper reproduction or blind evaluation. Skill text must state **rules and failure classes**, never a particular trial’s recipes, paths, wall clocks, figure IDs, or entity tags.

---

## G0. Three object layers never mix

| Layer | Use | Forbidden |
|-------|-----|-----------|
| Paper / skill build | Geometry, BC, solve | Counterpart truth values, entity IDs |
| Self-consistency | Same-recipe CAD↔COMSOL | “Implementation match” as “paper correct” |
| Forensic / counterpart compare | Post-hoc volume, wall-clock, field-class checks | Writing counterpart numbers back into builder parameters |

**Failure modes:** Treating counterpart field likeness as paper-only success; discovering ΔV then peek-fixing.

---

## G1. Paper silence ≠ silent habit

When the paper does not name a feature class / partition / solver detail:

1. Mark `[NOT IN PAPER]` or open a **decision-gate** option card; or
2. Mark `[SOFTWARE_DOC_DEFAULT: <installed-doc locus>]` (CFD/HT/REF/API, page-level when available);
3. **Never** use a benchmark MPH as the build default.

Reusable defaults (still require a documented locus):

- Open fluid inlet + Tin only → HT **Inflow(Tustr)**, not Temperature
- Open outlet + pressure only → HT **ConvectiveOutflow**
- Turbulent CHT Stationary → **Segregated** sequence before a long Fully Coupled first attempt
- Wall width that enters the unit-cell width formula → lateral occupation must be explicit **A/B** (or equivalent options); no silent default

---

## G2. Geometry: identity closure, not answer closure

Before build and after:

- Lateral occupation options (e.g. A = side-wall solids / B = fluid full width) + `claim_id`
- Analytic identities: `V_fluid_analytic` / `V_solid_analytic` / `A_in`
- Measured vs analytic tolerance (default 0.1%)

If forensic compare shows a different partition than the counterpart:

- Record “geometry family differs”;
- **Re-open decision with paper evidence**;
- **Never** set counterpart `V_fluid` as a builder target.

**Round-off vs semantics:** same formula measured vs analytic at machine precision → float; discrete partition jumps (bbox to cell boundary, clean integer-unit fluid↔solid swap) → **semantic choice**, not rounding.

---

## G3. Hydraulic and thermal gates stay separate

| Gate green does **not** mean |
|------------------------------|
| `GATE_DP` / mass conservation → enthalpy or Tw PASS |
| `GATE_INLET_BC` Inflow → already converged |
| `GATE_ENTHALPY` → permission to disable nitf |
| Solver completed → mph delivered on disk |

Hydraulic MATCH + enthalpy FAIL → **PARTIAL**, never a single green light.

---

## G4. Solver ladder: one class per shot + honest telemetry

When Inflow + NITF is hard to converge (paper BC class already green):

```
S0 probe → S1 Segregated+init → S2 qw continuation ONLY
→ S3 damping/iter ONLY (SegregatedStep: subdtech — not mistaken dtech)
→ S4 freeze flow, nitf ON → S5 BLOCKED_SOLVER + matrix
```

Hard rules:

- **One class per attempt** (do not open S2+S3+mesh together)
- **Forbidden:** disable nitf / revert Temperature / mesh-first / copy counterpart solver nodes
- Telemetry: prefer `~\.comsol\v*\logs\mphserver*.log` and post-job `message`; mid-solve `model_code` is often lock-empty
- Distinguish **SLOW** / **NONCONV** / **STALL_UNKNOWN**; do not only lengthen timeout without residual evidence
- Counterpart clear+resolve fast on the same host while paper-only stalls → check **BC class / solver class / geometry family**, not “the machine”

---

## G5. Expensive steps: no file = did not happen

Long geometry / long solve:

1. Before solve: `model_save(file_path=…_pre.mph)` succeeds under `COMSOL_OUTPUT_ROOT`
2. After solve: `_solved.mph` immediately; verify on disk
3. API argument names follow the tool schema (`file_path` ≠ `path`)
4. Unwrap `comsol_model_code` business fields from `result` before judging `ok`
5. Another MCP session **cannot** recover an unsaved in-memory model

---

## G6. BLOCKED is a legal scientific status

When the ladder is exhausted without a physical thermal solve:

- Status: `BLOCKED_SOLVER` (≠ mesh FAIL ≠ coupling missing)
- Deliver the matrix (BC classes, nitf, ladder outcomes, geometry A/B, bans honored)
- Escalate: reopen paper decision / change research question; **not** Temperature greenwashing of enthalpy

---

## One-liner

**The skill governs wrong class / missing class / unfinished persist. Trial-specific numbers are forensic or regression samples only — never global geometry truth.**
