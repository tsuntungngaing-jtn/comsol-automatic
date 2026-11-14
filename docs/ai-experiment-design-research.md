# Paper2Simu Research Branch — AI Experiment Design v0.1.0

**Status:** isolated research scaffold, **NOT a production solver/optimizer**. The main Paper2Simu package remains v0.2.0; this branch is optional and MUST NOT be merged or enabled on running COMSOL/Fluent workstations without separate review.

## Purpose

Make future simulation optimization a rigorously evaluable research project:

**Paper-to-Simulation (reproduction) → trusted baseline → research question → legal design space → candidate selection → authorized solver run → evidence-gated observation → update decision policy.**

This branch implements only the *design space* and *candidate planning* stages. It does **not** train surrogates, run Bayesian optimization, compute EIG, issue solver jobs, alter MCP servers, claim scientific validity or discover novel physics.

## Source and scope

Inspired by *Designing physics experiments with artificial intelligence*, **Nature** (published 2 September 2026), DOI: [10.1038/s41586-026-10898-6](https://doi.org/10.1038/s41586-026-10898-6). Its four high-level design concerns motivate this branch: search space, simulator, objective function and search strategy. The specific Python classes, normalized scores and heuristic ranking here are **Paper2Simu research design choices**, not algorithms copied or attributed to the Nature review.

For numerical credibility use the original [Eça–Hoekstra 2014](../docs/eca-hoekstra-2014-original-paper-review.md) source review and the existing [Paper2Simu scientific gates](../paper2simu/SKILL.md). Vendor-native termination does not equal validated physics. Do not create unjustified residual requirements to make a candidate appear more/less desirable.

## Source tree

- [\`contracts.py\`](../research_design/contracts.py) — frozen, hashable, auditable **DISCOVERY** design spaces with continuous, integer, and categorical hardware decisions, fixed inputs, objectives, source references, budgets and limited inspectable pairwise constraints
- [\`selector.py\`](../research_design/selector.py) — deterministic, offline candidate eligibility and transparent user-weighted cost/information/uncertainty/risk heuristic; it refuses illegal/disallowed/over-budget proposals and selects **for human review**, never for execution
- [\`tests/test_research_design.py\`](../tests/test_research_design.py) — synthetic negative and positive tests: source freezes, units, bounds, hardware choices, budgets, stale plans, duplicate IDs, normalized estimates and no-run status

## Crucial separation of responsibilities

**Loop A — Replication/Recovery.** Keep literature-reported geometry, BCs and material values fixed by source evidence. Diagnose true failures via RSA/RSI; never claim an optimized geometry was the author's actual model.

**Loop B — Discovery/Optimization.** Change design variables *explicitly reclassified as new user-defined design choices* in a new study, record provenance and baseline reference, and respect manufacturing and computational constraints. Outputs are new design proposals, not replicated paper results.

Solver adaptation remains at the host's isolated MCP connectors. LAB7/8 continue on their existing Fluent/PyFluent path; LAB9/10 remain on COMSOL. This research package neither calls COMSOL MPh/Java nor Fluent APIs.

## Transparent ranking — not a trained acquisition function

For candidate \`i\` the proof-of-concept score is:

\`\`\`
score_i = w_I * I_i + w_P * P_i - w_U * U_i - w_R * R_i
          - w_C * (predicted_minutes_i / frozen_total_minutes)
\`\`\`

Here \`I_i\`, \`P_i\`, \`U_i\`, \`R_i\` are **caller-supplied** [0,1] subjective estimates for information value, expected improvement, uncertainty and failure risk. They are **not independently inferred probabilities, expected information gain, calibrated confidence, or physical measurements.** Weights are explicitly provided and may differ per research question.

A candidate is omitted from ranking if it violates the design contract, solver authorization, estimated available memory, or time/job budget. **This is no guarantee an actual run fits in RAM.** A selected candidate is \`PROPOSED_NOT_SCHEDULED\`; operator approval, authenticated run identity, native preflight, true available budget and save/reopen verification remain prerequisites.

## How to try this branch offline

\`\`\`powershell
python -m unittest tests.test_research_design -v
python -m unittest discover -s tests -v
\`\`\`

Example input: [microchannel research design](../research_design/examples/microchannel_design.json). All numerical ranges and budgets are **illustrative only** and are not attributed to a particular research paper.

\`\`\`python
import json
from research_design import validate_space, assess_design, select_next_simulation

space = json.load(open("research_design/examples/microchannel_design.json"))
report = validate_space(space)
print(report["status"], report["design_space_hash"])
# To propose a simulation, supply a hypothesis, one design per candidate,
# nonzero time/RAM estimates, source-tagged normalized values and weights.
# The selector returns no-run evidence only and NEVER opens the solver.
\`\`\`

## Future research milestones — not yet implemented

1. **Evidence-secured observations:** read solver-native artifacts, metrics, reference definitions, source hashes and resource costs, and record failures instead of silently filtering them.
2. **Benchmarking:** random sampling, Latin Hypercube Sampling and cost-aware acquisition; equal high-fidelity budget, independent held-out test designs and repetitions across seeds.
3. **Proper active learning/optimization:** uncertainty-calibrated Gaussian Process, constrained Bayesian optimization, Pareto optimization and expected information gain where justified; no universal claim that a new algorithm is better.
4. **Multi-fidelity evidence:** identify when reduced mesh/physics variants are comparable to a verified high-fidelity baseline, preserve biases and prevent low-fidelity outputs being marked scientific PASS.
5. **Bounded autorun (separate approval):** pre-solve effective BC readbacks, run ownership lease, job deduplication, measured resource admission, native solver stop reasons, native case/data save/reopen and physics/mesh/conservation checks.
6. **Physical and experimental feasibility:** microchannel geometry, fluid operation, fabrication and measurement constraints. Avoid overclaiming improvements based on surrogate-only estimates.
7. **Retain policy:** require a reproducible holdout improvement without increasing erroneous scientific PASS before replacing a previous selector policy.

## Rollback and migration

No core server files have to change to use offline planning. To stop using the research branch, switch back to \`main\`. No persistent solver, MCP config, credential, job or model is changed by this branch. Do not distribute user-owned paper PDFs or private data in release archives.
