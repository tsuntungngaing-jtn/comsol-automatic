# CHT coupling and energy gates (COMSOL 6.4)

Lesson source: Approach A blind campaign `blind_paper_20261025_paper_only` (2026-10-25/26).  
Status: **operator checklist** (not a new MCP tool). Applies before claiming thermal metrics (Tw, heff, Fig.8/12/13 fields).

## Why this exists

Models with separate `TurbulentFlowkeps` + `HeatTransfer` can **solve and look plausible** while fluid advection in HT is uncoupled. In that failure mode:

- `ht.ntflux` port residuals may look near-zero (**false energy PASS**)
- Sensible enthalpy `Qsens = ṁ cp (Tout − Tin)` can be several× `Qapp`
- Mesh ladders of Tw/heff are **scientifically invalid** until coupling is fixed

## P0 — Admit / pre-solve contract (blocking)

Before `study_solve` on conjugate heat transfer (CHT):

| # | Check | Fail action |
|---|--------|-------------|
| 1 | Multiphysics node exists with type **`NonIsothermalFlow`** | Create or abort; do not solve |
| 2 | HT has a **fluid** domain feature (`FluidHeatTransferModel` or `Fluid`) on flowing-fluid selection | Add feature; abort if impossible |
| 3 | SPF selection = **flowing fluid only** (still-water arch **excluded**) | Fix selection |
| 4 | HT covers fluid + solid (+ still-water arch if conduction-only) | Fix selection |
| 5 | Named BCs nonempty: **inlet thermal**, heated flux/wall, outlet pressure | Fix |
| 5b | Inlet thermal type recorded; if paper silent → **Inflow(`Tustr`)** per HT docs (`SOFTWARE_DOC_DEFAULT`), not silent Temperature | Fix or FAIL `GATE_INLET_BC` |

### 6.4 API that worked on this install

```text
# Preferred create (component multiphysics API + camel case)
comp.multiphysics().create('nitf1', 'NonIsothermalFlow')

# Often FAILS (do not rely on):
# model.multiphysics().create('nitf1', 'NonisothermalFlow', 'comp1')
```

After create, confirm `comp.multiphysics().tags()` contains the node. Manual `fluid1.set('u','u')` is **not** equivalent to full turbulent NITF (stabilization / keff / wall functions).

### Study solve identity

```text
std = model.study().create('std1')
std.create('stat', 'Stationary')
std.label('Stationary')   # required: study_solve often matches LABEL
# Verify tags/labels before study_solve(..., study_name='Stationary')
```

Chained `study().create('std1').create('stat','Stationary')` without `label` caused **"Stationary does not exist"** in campaign scripts.

## P0 — Post-solve energy (blocking for THERMAL claims)

**Primary observable (required for CHT thermal PASS):**

```text
Qapp  = qw · A_heated
Qsens = |ṁ| · cp · (Tout − Tin)     # ṁ from SPF density·(u·n) at inlet
err   = |Qsens − Qapp| / |Qapp|
```

| Gate | Use |
|------|-----|
| `err < 0.20` | Minimum for reporting Tw/heff as coupled-campaign metrics |
| `err < 0.10` | Preferred for Baseline-class claims |
| `ht.ntflux`-only residual | **Accounting check only** — never sole energy PASS |

If Qsens ≫ Qapp with a finished solve → treat as **coupling FAIL**, not mesh FAIL. Invalidate prior thermal mesh studies.

## P1 — Still-water / TRDF arch geometry contract

When the paper defines a still-water arch (conduction only):

| # | Check | Fail action |
|---|--------|-------------|
| 1 | After Difference+`keep`, **domain count ≥ 3** (solid, flowing fluid, arch) | Repair keep / boolean; do not proceed |
| 2 | Named `sel_arch` nonempty; SPF does **not** include arch | Fix selections |
| 3 | Material: arch = water (or stated still fluid); solid = metal | Fix |
| 4 | Geometry probe must include Difference+keep+domain assert — not WorkPlane alone | Extend probe |

### WorkPlane units (mm geom)

Under `geom.lengthUnit('mm')`, prefer:

```text
wp.set('quickx', '2[mm]')      # not bare 2 if that means meters in context
ext.set('distance', '2[mm]')
```

Bare numeric offsets caused empty arch / wrong placement in early sine attempts. Overlapping block-slice unions (`size * 1.001`) caused mesh edge failures; use abutting or ~0.002 mm overlap and coarser `autoMeshSize` fallback (7→6→8).

### Mesh-study invalidation

If NITF (or HT fluid feature / SPF domain) changes:

- Mark prior Tw/heff mesh ladders **SUPERSEDED**
- Do not cite uncoupled heff mesh % as Fig.8 evidence
- Re-run method-level ladder on the **coupled** parent when claiming mesh behavior

## P2 — RSI / inference hooks (outer loop)

Treat as scientifically relevant unknowns (disclosure + impact):

- Panel ηL/ηH (Fig.12/13)
- Lmc interpretation
- `arch_method` (block / slice-sine / WorkPlane curve)
- Energy observable definition (enthalpy vs ntflux)

HIGH impact + INFERRED → scientific ceiling **CONDITIONAL** / **INSUFFICIENT_EVIDENCE**; never silent VALIDATED. See [uncertainty-aware RSI](uncertainty-aware-rsi.md).

## Institutional inlet thermal default (paper silent)

If the paper gives **Tin** (or equivalent) but does **not** specify the inlet *feature class*:

- Status: `[SOFTWARE_DOC_DEFAULT]` — **not** paper-reported.
- Default for **open channel / manifold fluid inlets** in COMSOL HT/CHT: **`Inflow` with upstream `Tustr`** (Heat Transfer User’s Guide modeling / HT features: open inlet fed by unmodeled upstream duct).
- Do **not** default to bulk **Temperature** Dirichlet on the port (port heat sink/source risk; enthalpy gates fail).
- Do **not** take the default from a benchmark MPH during build; oracle is post-solve compare only.
- Build **Inflow from the start** when possible; Temperature→Inflow migration needs the playbook below.

## Inlet BC migration — convergence playbook (CHT + NITF)

When changing inlet thermal BC **Temperature → Inflow(Tustr)** (or recovering from a wrong Temperature habit)
on an already-meshed turbulent CHT model:

### Hard rules

1. Keep **NonIsothermalFlow (nitf)** **ON** for any claim that needs conjugate heat transfer.
   Turning nitf off to force a numeric finish that yields **nonphysical T** (e.g. Tw ≪ Tin)
   → status `BLOCKED_SOLVER` / `NONPHYSICAL`, never enthalpy PASS.
2. Do **not** silently revert to Temperature to greenwash `GATE_ENTHALPY`.
3. Solver failure after Inflow is **`BLOCKED_SOLVER`**, distinct from coupling FAIL / mesh FAIL.
4. Export probe before/after: `inlet_ht_type`, nitf on/off, `ht.ntflux`@inlet, Tw sanity
   (campaign band e.g. `Tin − 5 K < Tw < Tin + 200 K`; else NONPHYSICAL).

### Recommended attempt ladder (stop at first physical converge)

| Step | Action | Pass if |
|------|--------|---------|
| S0 | Confirm Inflow + Tustr; nitf ON; heater not on inlet | probe green |
| S1 | Init from previous solution (flow+T if any); **fully coupled** Stationary, moderate timeout | completed + Tw physical + evaluate enthalpy |
| S2 | **Continuation:** ramp `qw` 0→full (or heat-flux multiplier) with Inflow+nitf ON | same |
| S3 | Segregated / more Newton iterations / smaller initial damping (doc-driven) | same |
| S4 | Optional: freeze **flow DOFs** only while keeping wall thermal coupling / nitf ON — if API allows without deactivating nitf | same |
| S5 | If all fail within campaign budget | `BLOCKED_SOLVER`; record matrix; escalate — **no Temperature revert** |

### Anti-patterns

| Do not | Why |
|--------|-----|
| Deactivate nitf to “get a number” | Seen: Tw ~ O(10) K, negative Qsens |
| Blame mesh first when Inflow+nitf fails and Temperature case already had ΔP MATCH | Prefer BC/solver ladder |
| Copy oracle MPH solver nodes / selections | Compare-only |
| Blind-wait multi-hour identical qw ramp with no residual telemetry | Cap budget; escalate to next ladder step or BLOCKED |

Prefer open-channel inlets as **Inflow(Tustr)** over bulk **Temperature** (COMSOL HT modeling / features). Record `GATE_INLET_BC`.

## Explicit non-claims

Passing these gates does **not** imply paper-figure numerical reproduction. They only prevent known false thermal PASS modes from this campaign.

For authorized post-build oracle tables, Fig.8 METHOD-LEVEL ceilings, and IT/LT isolates, see [paper-only vs oracle compare](paper-only-vs-oracle-compare.md).
