# Harness retention heuristics (AgentVersion only)

Policy helpers in `rsi/harness_heuristics.py`, inspired by regularized harness
self-improvement literature (e.g. RRSI): prefer OOD-stable, token-efficient,
small edit bundles; penalize benchmark-specific memorization.

## Effect

- Inputs: in-distribution gain, out-of-distribution gain, token cost ratio, edit
  bundle size, benchmark-specific flag.
- Output: `RETAIN_CANDIDATE` / `REJECT_CANDIDATE` folded into retention
  **performance** nudge via `merge_into_retention_metrics`.
- **Does not** change Scientific VALIDATED, paper claims, or ParameterBelief
  origins.

## Separation from peer CFD priors

| Corpus | Guides |
|--------|--------|
| Obsidian RSI theory/agent papers | Harness / AgentVersion heuristics |
| Same-physics CFD/HT literature | Numeric `peer_range_prior` for parameters |

Do not mix these provenance streams.
