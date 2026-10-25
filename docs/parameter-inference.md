# Parameter inference

Status: **implemented** detector + ParameterBelief + plausible-range engine; literature scraping **NOT_IMPLEMENTED**.

## Protocol

1. Detect missing / unprovenanced / unitless scientifically relevant parameters.
2. Retrieve and rank evidence with context similarity.
3. If coverage insufficient → `reliability=INSUFFICIENT` (legal). Do **not** fabricate a range.
4. Otherwise construct an **estimated plausible range** (never labeled confidence interval without formal stats).
5. Assess U×S decision impact → AUTO_ACCEPT / RUN_SENSITIVITY / ASK_USER / BLOCK_FINAL_VALIDATION.
6. Disclose via Inference Disclosure Report.
7. Endpoint sensitivity (low/mid/high) when impact warrants.

## Forbidden

Silent COMSOL default fill for scientifically relevant unknowns.
