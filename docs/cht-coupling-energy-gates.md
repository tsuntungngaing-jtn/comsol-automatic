# CHT coupling and energy gates

Checklist for conjugate heat transfer (CHT) / non-isothermal flow campaigns.
Software correctness and scientific correctness are reported separately.
This document does **not** authorize copying settings from oracle or Blind MPH templates.

## P0 — Admit (pre-solve)

| # | Requirement | On fail |
|---|-------------|---------|
| 1 | Flowing fluid domains assigned to SPF (or equivalent) only | Fix |
| 2 | Fluid HT feature on flowing fluid; solid HT on solid | Fix |
| 3 | NonIsothermalFlow (or equivalent) multiphysics present | Fix |
| 4 | Heater / heat flux on heated face only; selection nonempty | Fix |
| 5 | Named BCs nonempty: **inlet thermal**, heated flux/wall, outlet pressure | Fix |
| 5b | Inlet thermal feature type recorded; prefer **Inflow** (`Tustr`); see below | Fix or FAIL `GATE_INLET_BC` |
| 6 | Mesh present; study/solver tree admits stationary or stated transient | Fix |

## P0 — Inlet thermal BC (blocking for enthalpy claims)

COMSOL HT guidance (modeling / HT features): open inlet should use **Inflow** with upstream temperature `Tustr`, not a bulk **Temperature** Dirichlet on the port, and not Heat Flux on the inlet.

| Inlet feature | Pre-solve | Post-solve energy |
|---------------|-----------|-------------------|
| `Inflow` + `Tustr` = Tin (or paper) | OK for CHT gate path | Evaluate `Qsens≈Qapp` |
| `Temperature` on inlet | Allowed only with **waiver**; expect possible port heat sink/source | If `|ht.ntflux|_inlet` is O(Qapp) → BC FAIL; do not blame mesh |
| Heat Flux on inlet | **Forbidden** for this gate set | FAIL |

If the campaign changes Temperature → Inflow and the solve **does not converge**, status = `BLOCKED_SOLVER` (separate from coupling FAIL). Do **not** silently revert to Temperature to greenwash enthalpy. Solver recovery playbook is **out of scope for this checklist revision** (operator Round 2).

## P0 — Coupling probe (export before thermal PASS)

Emit a small probe table/JSON (names flexible; fields mandatory):

| Probe | Pass |
|-------|------|
| `nitf_type` | `NonIsothermalFlow` present on component |
| `spf_domains` | flowing fluid only |
| `ht_fluid_feature` | fluid HT feature on flowing fluid |
| `ht_solid_feature` | solid on metal |
| `inlet_ht_type` | `Inflow` (or waived + justified) |
| `heater_not_on_inlet` | true |
| `ht_ntflux_inlet_W` | recorded after solve (informational; large magnitude flags BC) |
| `minput_velocity_src` | record actual UI/API value (`from multiphysics` / `userdef` / expression). **Round 1:** record only — do not invent a global mandatory rewrite rule |

`physics_list` containing `nitf1` **alone** is **not** a probe PASS.

### 6.4 API

Anchor feature names and property tags to the installed COMSOL 6.4 local documentation.
Do not assume MPh shorthand equals a solved coupling. Prefer Inspector / property readback after create.

## Post-solve energy

| Check | Pass condition |
|-------|----------------|
| Applied heat `Qapp` | Integral of heater flux (or stated source) with units |
| Sensible fluid rise `Qsens` | `ṁ cp ΔT` (or COMSOL derived equivalent) |
| Relative error `err` | declare threshold in report (e.g. \|Qsens−Qapp\|/Qapp) |
| Inlet `ht.ntflux` | recorded; large sink/source with Dirichlet T → BC FAIL |

Creation/solve completion alone is not energy PASS.

## Independent gate reminder

| Fragment | May claim alone? |
|----------|------------------|
| ΔP / ṁ / Ain vs oracle | Hydraulic QoI fragment only |
| Enthalpy `err` + inlet BC gate | Required before Tw/heff claims |
| NITF node exists | Necessary, not sufficient |

ΔP MATCH + enthalpy FAIL ⇒ stay CONDITIONAL; see validation skill independent gates.

## Out of scope (Round 2)

- Stepwise solver recovery after Inflow fails to converge
- Mandating a global `minput_velocity` rewrite rule for all NITF setups
