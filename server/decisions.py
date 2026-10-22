"""Human decision gate. DESIGN_POLICY for ask-vs-continue; no invented sensitivity."""
from __future__ import annotations

from typing import Any
import uuid

CRITICAL_TASKS = {
    'solve', 'claim_validation', 'physics_binding', 'material_assignment',
    'calibration', 'delivery',
}


class DecisionGate:
    def evaluate_missing(self, *, quantity_id: str, description: str, affects: list[str],
                         current_task: str, candidates: list[dict],
                         sensitivity: str | None = None) -> dict | None:
        """Ask only when the missing item blocks the current task or a critical claim path."""
        sensitivity = sensitivity or 'unknown'
        if sensitivity != 'unknown' and not isinstance(sensitivity, dict):
            # Do not accept LLM-guessed scalars as measured sensitivity.
            sensitivity = 'unknown'
        blocks_current = current_task in affects
        critical = bool(set(affects) & CRITICAL_TASKS)
        if not blocks_current and not (critical and current_task in CRITICAL_TASKS):
            return None
        return {
            'decision_id': 'dec-' + uuid.uuid4().hex[:12],
            'question': description,
            'reason': 'Missing information blocks a dependent task',
            'affected_tasks': list(affects),
            'affected_claims': [a for a in affects if a.startswith('claim')],
            'candidate_options': list(candidates),
            'candidate_sources': [c.get('source') for c in candidates],
            'consequence_if_unresolved': 'Dependent task remains BLOCKED',
            'recommended_option': candidates[0] if candidates else None,
            'recommendation_basis': 'candidate order only; sensitivity=unknown' if sensitivity == 'unknown' else 'supplied sensitivity evidence',
            'requires_user': True,
            'status': 'pending',
            'quantity_id': quantity_id,
            'sensitivity': sensitivity,
        }

    def task_may_proceed(self, current_task: str, blocked_affects: list[str]) -> bool:
        return current_task not in blocked_affects
