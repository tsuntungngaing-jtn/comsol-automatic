# Nonlinear / segregated solver tuning (MCP, 0.4.0)

Agentic pattern aligned with COMSOL's public blog demonstration on a heat-sink
CFD tutorial: probe segregated-solver settings, run a **bounded** sweep, keep
only changes that preserve physical KPIs. Primary control remains MCP—not a
bare `comsolcompile` harness.

See [agentic-official-alignment](agentic-official-alignment.md) for Chatbot vs
agent vs Multiphysics Server positioning.

## Preconditions

1. Live tracked model identity known (`comsol_status` / inspect). Client–server
   preferred so the engineer can watch Desktop.
2. Baseline solve already converges. Capture wall time, nonlinear/segregated
   iteration counts (from logs), and **at least one physical KPI** (probe or
   Evaluation Group).
3. Named selections for physics BCs; do not “speed up” by weakening termination
   into a non-physical result.

## Discover editable properties

Do **not** hardcode property names as universal API truth.

1. Live `properties()` on the Segregated feature (via inspector or
   `comsol_model_code` when allowed).
2. Engineer **Copy as Code to Clipboard** from the solver node in Desktop.
3. Local installed docs / `pdf_search` when the knowledge base is available.

Blog heat-sink examples used a path shaped like
`model.sol("sol1").feature("s1").feature("se1").set(...)`. Tags and keys are
**model-specific**.

### Candidate keys (verify on the live node)

From the official blog prompt (candidates only):

`segterm`, `maxsegiter`, `ntolfact`, `segtermonres`, `segreserrfact`,
`segstabacc`, `segcfltech`, `subinitcfl`, `submincfl`, `subforcecfl`,
`subkppid`, `subkipid`, `subkdpid`, `subcfltol`, `subadaptcfltol`,
`segcflaa`, `segcflaacfl`, `segcflaaset`, `segcflaadim`, `segcflaamix`,
`segcflaadelay`, `segcflaafact`, `segcfljtech`, `consistencycheck`, `plot`,
`probesel`.

For CHT segregated ladders in this skill's other docs, also respect
version-anchored names such as SegregatedStep **`subdtech` / `maxsubiter`**
([api-patterns](api-patterns.md), [cht-coupling-energy-gates](cht-coupling-energy-gates.md))—do not
confuse those with Fully Coupled `dtech` on the wrong node.

## Bounded experiment protocol

1. From properties + docs, pick **at most three** promising knobs.
2. For each knob, try **three values** (nine runs max unless the user asks for
   more).
3. Between runs: restore baseline settings or reload a checkpoint MPH under
   `COMSOL_OUTPUT_ROOT`.
4. Record per run: setting delta, solve success, time, iteration counts, KPI(s).
5. Accept a candidate only if:
   - the solve still converges under a physically justified termination mode;
   - KPI change stays within an agreed tolerance;
   - logs do not show a fake “win” from truncated iteration caps.

### Anti-pattern (reject immediately)

Changing termination to iteration-count and setting the maximum to `1` can
collapse iteration counts without a sound solution. Reject via KPI gates and
log inspection (`segtermonres` / residual vs solution-error stopping—see
[api-patterns](api-patterns.md)).

## Enum / dropdown sweeps outside Parametric Sweep

Some interface enums (blog example: Laminar Flow compressibility options) are
awkward or impossible via UI Parametric Sweep. An agent may cycle API values,
re-solve, and compare KPI / time / iterations. **Retain the physically correct
option**, not the fastest spurious one.

## Reporting and claims

Write a short table under `COMSOL_OUTPUT_ROOT`:

| run | property | value | ok | time | iters | KPI |

State baseline vs best **accepted** candidate. Persist winning settings in a
new checkpoint MPH.

The official blog's ~25% fewer nonlinear iterations / ~30% faster runtime are
**reported** narrative for their example only. Label them
`NOT_VALIDATED_BASELINE` for this skill. Never promote them to scientific
VALIDATED or to a delivery guarantee.

## Related

- [agentic-official-alignment](agentic-official-alignment.md)
- [stage-contracts](stage-contracts.md)
- [persist-hard-gate](persist-hard-gate.md)
- Official blog: https://www.comsol.com/blogs/using-agentic-workflows-with-comsol-multiphysics
