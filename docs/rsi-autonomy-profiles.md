# RSI autonomy profiles (0.4.2+)

Bounded harness-side RSI only. Not open-ended strict RSI. Users choose how much
human gating to keep via `COMSOL_RSI_AUTONOMY` (default **`strict`**). A single
`decision_resolve` call may override the profile for that decision.

## Profiles

| Profile | Env value | Behavior |
|---------|-----------|----------|
| Strict | `strict` (default) | HIGH/CRITICAL, physics reinterpretation, missing modules → human. Digitized / peer priors stay candidates. |
| Assisted | `assisted` | LOW/MEDIUM with official-doc default or dual-source agreement → `AUTO_ACCEPT` or auto 2-endpoint sensitivity. HIGH still asks; questions are **packed**. |
| Auto | `auto` | LOW auto-accept; MEDIUM auto `RUN_SENSITIVITY` (budget capped); HIGH only if sole `SOFTWARE_DOC_DEFAULT` and non-claim-critical → accept as `CONDITIONAL`. CRITICAL / overwrite sources / `COMSOL_ALLOW_CODE` / delete audit **always** human. |

Delivery must disclose: `autonomy_profile`, parameter origins, sensitivity runs, scientific status.

## Three evidence channels (Infer)

| Channel | Origin / marker | May become |
|---------|-----------------|------------|
| COMSOL official docs | `DEFAULT` / `[SOFTWARE_DOC_DEFAULT: locus]` / Evidence `library` | Feature **class** defaults (e.g. Inflow) |
| Paper figure/axis digitization | `digitized_estimate` | Plausible **interval** only — never `reported` |
| Peer / similar-physics papers | `INFERRED` + `LITERATURE` with DOI/table | Plausible **range** — not a CI |

Compose: docs pick feature class; peer papers pick magnitude range; figures bound claims for brackets. Paper `reported` always beats doc defaults on conflict (`conflict` status).

## Hard bans (all profiles)

- Digitized or peer values → `reported` or final Scientific VALIDATED
- RSI theory-paper numbers as CFD physical priors
- Desktop Chatbot / Import App automation
- Silent inventing of sensitivity scalars (`unknown` until measured or endpoint plan)

See [parameter-inference](parameter-inference.md), [underspec-decision-loop](underspec-decision-loop.md),
[human-decision-gates](human-decision-gates.md), [uncertainty-aware-rsi](uncertainty-aware-rsi.md).
