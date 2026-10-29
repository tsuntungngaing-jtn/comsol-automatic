# CHT coupling and energy gates (COMSOL 6.4)

Status: **operator checklist** (not a new MCP tool). Applies before claiming conjugate-heat-transfer thermal metrics (wall temperature, effective heat-transfer coefficient, enthalpy balance).

This document states **reusable institutional rules** for turbulent / laminar CHT. It must not encode any single paper’s figure IDs, case matrix, wall-clock timings, entity tags, or workspace paths.

## Why this exists

Models with separate `TurbulentFlowkeps` (or similar SPF) + `HeatTransfer` can **solve and look plausible** while fluid advection in HT is uncoupled. In that failure mode:

- `ht.ntflux` port residuals may look near-zero (**false energy PASS**)
- Sensible enthalpy `Qsens = ṁ cp (Tout − Tin)` can be several× `Qapp`
- Mesh ladders of Tw/heff are **scientifically invalid** until coupling is fixed

## P0 — Admit / pre-solve contract (blocking)

Before `study_solve` on conjugate heat transfer (CHT):

| # | Check | Fail action |
|---|--------|-------------|
| 1 | Multiphysics node exists with type **`NonIsothermalFlow`** | Create or abort; do not solve |
| 2 | HT has a **fluid** domain feature (`FluidHeatTransferModel` or `Fluid`) on flowing-fluid selection | Add feature; abort if impossible |
| 3 | SPF selection = **flowing fluid only** (still-fluid conduction islands **excluded**) | Fix selection |
| 4 | HT covers fluid + solid (+ still-fluid islands if conduction-only) | Fix selection |
| 5 | Named BCs nonempty: **inlet thermal**, heated flux/wall, outlet pressure | Fix |
| 5b | Inlet thermal type recorded; if paper silent → **Inflow(`Tustr`)** per HT docs (`SOFTWARE_DOC_DEFAULT`), not silent Temperature | Fix or FAIL `GATE_INLET_BC` |

### 6.4 API pattern (verify on the installed build)

```text
# Preferred create (component multiphysics API + camel case)
comp.multiphysics().create('nitf1', 'NonIsothermalFlow')

# Often FAILS (do not rely on):
# model.multiphysics().create('nitf1', 'NonisothermalFlow', 'comp1')
```

After create, confirm `comp.multiphysics().tags()` contains the node. Manual `fluid1.set('u','u')` is **not** equivalent to full turbulent NITF (stabilization / keff / wall functions).

### Study solve identity (tag ≠ label)

MPh / MCP `study_solve` / `study_solve_async` resolve **`study_name` by LABEL**, not Java tag.

```text
std = model.study().create('std1')
std.create('stat', 'Stationary')
std.label('Stationary')   # required: study_solve matches LABEL
# Verify (tag, label) pairs before study_solve(..., study_name=<LABEL>)
```

| Failure mode | Typical message | Cause |
|--------------|-----------------|-------|
| Create without `label()` | `Study "Stationary" does not exist.` | Assumed label never set |
| Pass **tag** on loaded MPH | `Study "<tag>" does not exist.` | Tag ≠ label on an existing study |

**Rule:** Enumerate `(tag, label)` pairs before every solve on an existing MPH. Pass the **label**. Instant `LookupError` on a tag string is an identity bug, not a physics/mesh failure. Chained `study().create(...).create(...)` without `label()` causes the same class of miss.

## P0 — Post-solve energy (blocking for THERMAL claims)

**Primary observable (required for CHT thermal PASS):**

```text
Qapp  = qw · A_heated
Qsens = |ṁ| · cp · (Tout − Tin)     # ṁ from SPF density·(u·n) at inlet
err   = |Qsens − Qapp| / |Qapp|
```

| Gate | Use |
|------|-----|
| `err < 0.20` | Minimum for reporting Tw/heff as coupled thermal metrics |
| `err < 0.10` | Preferred for baseline-class thermal claims |
| `ht.ntflux`-only residual | **Accounting check only** — never sole energy PASS |

If Qsens ≫ Qapp with a finished solve → treat as **coupling FAIL**, not mesh FAIL. Invalidate prior thermal mesh studies.

Keep **hydraulic** and **thermal** gates separate: ΔP / mass MATCH does not imply enthalpy PASS.

## P1 — Still-fluid / conduction-island geometry contract

When the paper defines a still-fluid region that is conduction-only:

| # | Check | Fail action |
|---|--------|-------------|
| 1 | After boolean keep, domain count matches the declared topology (solid, flowing fluid, still-fluid) | Repair keep / boolean; do not proceed |
| 2 | Named still-fluid selection nonempty; SPF does **not** include it | Fix selections |
| 3 | Materials match the paper (still fluid vs solid metal) | Fix |
| 4 | Geometry probe asserts the boolean keep + domain count — not sketch alone | Extend probe |

### WorkPlane units (mm geom)

Under `geom.lengthUnit('mm')`, prefer explicit unit strings in expressions that must stay in mm. Bare numeric offsets have caused empty islands / wrong placement; oversized boolean overlaps have caused mesh edge failures — prefer abutting or tiny intentional overlap and a documented mesh-size fallback ladder.

### Mesh-study invalidation

If NITF (or HT fluid feature / SPF domain) changes:

- Mark prior Tw/heff mesh ladders **SUPERSEDED**
- Do not cite uncoupled heff mesh sensitivity as thermal evidence
- Re-run method-level ladders on the **coupled** parent when claiming mesh behavior

## P2 — RSI / inference hooks (outer loop)

Treat paper-silent thermal/geometric choices as scientifically relevant unknowns (disclosure + impact), for example:

- Efficiency / figure-panel digitization assumptions when panels are under-specified
- Channel-length or manifold interpretation when symbols are ambiguous
- Still-fluid construction method (block / slice / WorkPlane curve)
- Energy observable definition (enthalpy vs ntflux)

HIGH impact + INFERRED → scientific ceiling **CONDITIONAL** / **INSUFFICIENT_EVIDENCE**; never silent VALIDATED. See [uncertainty-aware RSI](uncertainty-aware-rsi.md).

## Institutional inlet / outlet thermal defaults (paper silent)

If the paper gives **Tin** (or equivalent) but does **not** specify the inlet *feature class*:

- Status: `[SOFTWARE_DOC_DEFAULT]` — **not** paper-reported.
- Default for **open channel / manifold fluid inlets** in COMSOL HT/CHT: **`Inflow` with upstream `Tustr`** (Heat Transfer User’s Guide: open inlet fed by unmodeled upstream duct).
- Do **not** default to bulk **Temperature** Dirichlet on the port (port heat sink/source risk; enthalpy gates fail).
- Do **not** take the default from a counterpart / benchmark MPH during build; counterparts are post-solve compare only.
- Build **Inflow from the start** when possible; Temperature→Inflow migration needs the playbook below.

If the paper specifies a **pressure outlet** (or open discharge) but does **not** name the HT outlet feature class:

- Status: `[SOFTWARE_DOC_DEFAULT]`.
- Default for **open fluid outlets** in HT/CHT: **`ConvectiveOutflow`** on the outlet selection (pair with SPF `OutletBoundary`), not a silent omission of all HT outlet features.
- Missing HT outlet feature is a **first-class BC gap** before blaming mesh or hardware. Builders create their own tags; never copy counterpart feature tags into the builder.

### Pre-solve solver sequence (turbulent CHT)

Before a long `Stationary` job on turbulent flow + NITF:

1. Ensure a solution sequence exists (`sol.createAutoSequence(studyTag)` or equivalent).
2. Probe that a **`Segregated`** node is present for the default turbulent Stationary path (typical product path; confirm `stol` order of magnitude from installed docs / sequence).
3. Do **not** burn the full job timeout on an unspecified auto Fully Coupled first attempt when Segregated is the product default for this physics class.
4. Counterpart solver *trees* remain compare-only — copy the **class** (Segregated / stol order), not node tags.

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
   (declare a physical band relative to Tin; else NONPHYSICAL).

### Recommended attempt ladder (stop at first physical converge)

| Step | Action | Pass if |
|------|--------|---------|
| S0 | Confirm Inflow + Tustr; **ConvectiveOutflow on outlet** (if paper-silent); nitf ON; heater not on inlet; **Segregated sequence present** | probe green |
| S1 | Init from previous solution (flow+T if any); Stationary with **Segregated** (preferred), moderate timeout | completed + Tw physical + evaluate enthalpy |
| S2 | **Continuation:** ramp `qw` 0→full (or heat-flux multiplier) with Inflow+nitf ON | same |
| S3 | More Newton iterations / smaller initial damping / then try Fully Coupled only if Segregated failed honestly | same |
| S4 | Optional: freeze **flow DOFs** only while keeping wall thermal coupling / nitf ON — if API allows without deactivating nitf | same |
| S5 | If all fail within declared budget | `BLOCKED_SOLVER`; record matrix; escalate — **no Temperature revert** |

### Anti-patterns

| Do not | Why |
|--------|-----|
| Deactivate nitf to “get a number” | Yields nonphysical Tw / negative Qsens |
| Blame mesh first when Inflow+nitf fails and a Temperature case already had ΔP MATCH | Prefer BC/solver ladder |
| Copy counterpart MPH solver nodes / selections | Compare-only |
| Idle-wait multi-hour identical qw ramp with no residual telemetry | Cap budget; escalate to next ladder step or BLOCKED |

Prefer open-channel inlets as **Inflow(Tustr)** over bulk **Temperature**. Record `GATE_INLET_BC`.

## Explicit non-claims

Passing these gates does **not** imply paper-figure numerical reproduction. They only prevent known false thermal PASS modes for CHT coupling and BC class.

For authorized post-build counterpart tables and method-level ceilings, see [paper-only vs oracle compare](paper-only-vs-oracle-compare.md).

## Solver ladder API names (SegregatedStep)

Use installed Programming Reference property names. Wrong names raise *Unknown property*.

| Node | Properties | Notes |
|------|------------|-------|
| Stationary study | `useparam`, `pname`, `plistarr`, `pcontinuationmode`, `preusesol` | S2 continuation |
| **SegregatedStep** | **`subdtech`**, **`maxsubiter`**, `subdamp`, `subinitsteph` | **Not** `dtech` / `maxiter` on SegStep |
| FullyCoupled | `dtech`, `maxiter`, `initsteph` | FC node only |
| Segregated | `maxsegiter` | default stationary often 100 |

S3 preferred: `subdtech='hnlin'` + raise `maxsubiter`. Alternate: `subdtech='const'`, `subdamp=0.1`.

### One class per job

Change **one** ladder class per solve attempt: continuation **XOR** damping **XOR** freeze-flow **XOR** FullyCoupled swap. Do not mix S2+S3+mesh in one attempt.

### Telemetry hygiene

- Mid-solve `comsol_model_code` often returns empty under client lock — prefer tailing `~\.comsol\vXX\logs\mphserver*.log` and post-job / post-cancel `message` on sol features.
- Classify: `SLOW_IMPROVING` | `NONCONV_FLAT` | `NONCONV_MAX_NEWTON` | `STALL_UNKNOWN`.
- Do not extend wall-clock on identical settings without residual evidence.
- If a counterpart clear+resolve finishes promptly on the same machine while the paper-only build stalls, blame **BC class / solver class / geometry family**, not hardware.

### S4 freeze-flow note

Thermal segment must keep **`activate(nitf, True)`**. Isothermal flow seed may turn ht/nitf off; thermal segment must not. After flow `completed`, still require ΔP eval; eval failure goes into the BLOCKED matrix.

## BLOCKED_SOLVER matrix (ladder exhausted)

When S0–S4 (or declared budget) is exhausted and Inflow+NITF still has no physical thermal solve, deliver:

```yaml
status: BLOCKED_SOLVER
inlet_ht_type: Inflow|...
outlet_ht_type: ConvectiveOutflow|missing|...
nitf: on
geometry_partition: A|B|AMBIGUOUS|NA
ladder:
  S2: timeout|failed|skipped + note
  S3: ...
  S4: failed_max_newton|timeout|...
telemetry_class: NONCONV_MAX_NEWTON|STALL_UNKNOWN|...
counterpart_control_wall_min: <number or NA>   # compare-only, optional
bans_honored: [no_nitf_off, no_Temperature, no_entity_copy, no_mesh_first]
escalation: reopen_decision_gate|change_research_question|optional_FC_one_shot
```

Forbidden: Temperature to force enthalpy PASS; turn nitf off for Tw; infinite identical Stationary; rewrite BLOCKED as mesh FAIL without mesh evidence.
