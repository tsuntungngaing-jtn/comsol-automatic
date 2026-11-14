# Parameter inference

Status: **implemented** detector + ParameterBelief + plausible-range engine + doc/peer/digitize helpers; autonomous web scraping **NOT_IMPLEMENTED**.

## Protocol

1. Detect missing / unprovenanced / unitless scientifically relevant parameters.
2. Retrieve and rank evidence with context similarity, including:
   - `doc_default_resolve` → feature-class `[SOFTWARE_DOC_DEFAULT]`
   - `peer_range_prior` → same-physics literature magnitude ranges
   - figure digitize → `digitized_estimate` intervals (brackets only)
3. If coverage insufficient → `reliability=INSUFFICIENT` (legal). Do **not** fabricate a range.
4. Otherwise construct an **estimated plausible range** (never labeled confidence interval without formal stats).
5. Assess U×S decision impact → AUTO_ACCEPT / RUN_SENSITIVITY / ASK_USER / BLOCK_FINAL_VALIDATION, then apply `COMSOL_RSI_AUTONOMY`.
6. Disclose via Inference Disclosure Report.
7. Endpoint sensitivity via `plan_sensitivity_with_budget` (default max 2 bracket jobs).

## Compose rules

- Docs set **feature class**; peers set **numeric range**; figures bound **claim brackets**.
- Paper `reported` wins over doc default on conflict.
- Digitized/peer never upgrade to `reported`.

## Forbidden

Silent COMSOL default fill for scientifically relevant unknowns without provenance markers.

## v0.2.1 proposed clarification

Final scientific certification, permitted conditional modeling and user approvals are independent. Missing paper inputs should first prompt bounded physics-consistent derivations, installed material/library research and scenario branches; unresolved essential unbounded inputs block only their dependent predictions. See [candidate audit](conditional-reconstruction-and-rsi-evidence-v0.2.1.md). No unapproved solver execution is implied.
