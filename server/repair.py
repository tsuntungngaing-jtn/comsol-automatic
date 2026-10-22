"""Mechanical vs epistemic repair; immutable failed baselines; one-change default."""
from __future__ import annotations

from typing import Any
import uuid

from .orchestrator import ClosedLoopController
from .workflow_state import INVALID


class RepairController:
    def __init__(self, controller: ClosedLoopController):
        self.ctrl = controller
        self._plans: dict[str, dict[str, Any]] = {}

    def freeze_failed_baseline(self, case_id: str, failure_id: str) -> dict:
        state = self.ctrl.state(case_id)
        baseline = {
            'failure_id': failure_id, 'case_id': case_id,
            'model_revision': state['model_revision'],
            'spec_revision': state['spec_revision'],
            'current_run_id': state.get('current_run_id'),
            'immutable': True,
        }
        case = self.ctrl.store.get(case_id)
        case['failed_baselines'] = list(case.get('failed_baselines') or []) + [baseline]
        self.ctrl.store.save(case)
        return dict(baseline)

    def propose(self, *, case_id: str, failure_id: str, hypothesis: str, repair_type: str,
                proposed_change: str, baseline_revision: int, expected_effect: str | None = None,
                atomic_multi_change: bool = False) -> dict:
        mechanical = repair_type == 'mechanical'
        plan = {
            'repair_id': 'rp-' + uuid.uuid4().hex[:12], 'failure_id': failure_id,
            'case_id': case_id, 'hypothesis': hypothesis, 'supporting_evidence': [],
            'repair_type': repair_type, 'proposed_change': proposed_change,
            'expected_effect': expected_effect, 'affected_checks': [],
            'requires_user': not mechanical, 'admitted_automatically': mechanical,
            'baseline_revision': baseline_revision, 'budget_cost': 1,
            'status': 'proposed', 'atomic_multi_change': atomic_multi_change,
        }
        self._plans[plan['repair_id']] = plan
        return dict(plan)

    def apply(self, repair_id: str, admitted: bool) -> dict:
        plan = self._plans[repair_id]
        case_id = plan['case_id']
        state = self.ctrl.state(case_id)
        budgets = state['budgets']
        if budgets['repair_count'] >= budgets.get('max_repairs', 10):
            self.ctrl.store.force_state(case_id, 'BUDGET_EXHAUSTED')
            return {'status': 'BUDGET_EXHAUSTED', 'repair_id': repair_id}
        if plan['requires_user'] and not admitted:
            try:
                self.ctrl.store.transition(case_id, 'WAITING_FOR_USER')
            except INVALID:
                self.ctrl.store.force_state(case_id, 'WAITING_FOR_USER')
            plan['status'] = 'WAITING_FOR_USER'
            return {'status': 'WAITING_FOR_USER', 'repair_id': repair_id}
        before = state['model_revision']
        mutated = self.ctrl.mutate_model(case_id, kind='repair', note=plan['proposed_change'])
        case = self.ctrl.store.get(case_id)
        case['budgets']['repair_count'] = case['budgets']['repair_count'] + 1
        case['repair_history'] = list(case.get('repair_history') or []) + [{
            'repair_id': repair_id, 'before_revision': before,
            'after_revision': mutated['model_revision'], 'repair_delta': plan['proposed_change'],
            'failure_id': plan['failure_id'],
        }]
        case['requires_revalidation'] = True
        self.ctrl.store.save(case)
        plan['status'] = 'applied'
        return {'status': 'applied', 'repair_id': repair_id, 'before_revision': before,
                'after_revision': mutated['model_revision']}
