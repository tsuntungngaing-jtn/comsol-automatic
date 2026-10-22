# Human decision gates

Status: **implemented** DecisionRequest + resolve path; PDF extraction and measured sensitivity ranking **NOT_IMPLEMENTED**.

| Mechanism | Basis | Support class |
|---|---|---|
| Underspecification → clarification → uncertainty reduction | Kirchhof et al., ICML 2025 | LITERATURE_ADAPTED |
| Human oversight of scientific judgment | Miao et al. Nature 2026 HITL boundary | LITERATURE_ADAPTED |
| When to ask / priority formula | this repository | DESIGN_POLICY |
| Do not invent sensitivity | this repository | DESIGN_POLICY |

## When to ask

Ask when missing information would: block the current task; change a target claim; change physics interpretation; or leave unacceptable scientific ambiguity.

## When not to ask

Unrelated missing fields (e.g. plot cosmetics) do not block geometry construction. Continue independent stages. Do not question-bomb every empty field.

## Sensitivity

If no measured sensitivity evidence exists, write `sensitivity=unknown`. Do not let an LLM invent a number.

## Candidate presentation

Each DecisionRequest lists question, reason, affected tasks/claims, candidates with sources, consequence if unresolved, optional recommendation labeled as candidate order only when sensitivity is unknown.

## User decision provenance

Allowed actions: supply value, select candidate, approve assumption or range, keep unresolved, reject all, provide new evidence. After confirmation, retain original origin. Library pick stays `library` + `decision=user_approved`.
