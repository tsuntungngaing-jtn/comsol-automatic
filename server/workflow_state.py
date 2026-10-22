"""Persistent controller state. Exact state names are DESIGN_POLICY."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATES = (
    'NEW', 'EVIDENCE_INTAKE', 'SPEC_COMPILATION', 'WAITING_FOR_USER', 'MODEL_BUILD',
    'PRECHECK', 'SOLVE_READY', 'SOLVING', 'VALIDATION', 'DIAGNOSIS', 'REPAIR_READY',
    'REPAIRING', 'REOPEN_VERIFY', 'DELIVERY_READY', 'PASS', 'FAIL', 'BLOCKED',
    'BUDGET_EXHAUSTED', 'CALIBRATED_NOT_INDEPENDENTLY_VALIDATED',
)

TRANSITIONS = {
    'NEW': {'EVIDENCE_INTAKE', 'WAITING_FOR_USER', 'BLOCKED'},
    'EVIDENCE_INTAKE': {'SPEC_COMPILATION', 'WAITING_FOR_USER', 'BLOCKED', 'FAIL'},
    'SPEC_COMPILATION': {'WAITING_FOR_USER', 'MODEL_BUILD', 'BLOCKED', 'FAIL'},
    'WAITING_FOR_USER': {'EVIDENCE_INTAKE', 'SPEC_COMPILATION', 'BLOCKED', 'FAIL'},
    'MODEL_BUILD': {'PRECHECK', 'WAITING_FOR_USER', 'FAIL', 'BLOCKED'},
    'PRECHECK': {'SOLVE_READY', 'MODEL_BUILD', 'FAIL', 'BLOCKED', 'WAITING_FOR_USER'},
    'SOLVE_READY': {'SOLVING', 'BLOCKED', 'FAIL'},
    'SOLVING': {'VALIDATION', 'FAIL', 'BLOCKED'},
    'VALIDATION': {'DIAGNOSIS', 'REOPEN_VERIFY', 'FAIL', 'BLOCKED', 'DELIVERY_READY'},
    'DIAGNOSIS': {'REPAIR_READY', 'WAITING_FOR_USER', 'EVIDENCE_INTAKE', 'SPEC_COMPILATION',
                  'MODEL_BUILD', 'FAIL', 'BLOCKED'},
    'REPAIR_READY': {'REPAIRING', 'WAITING_FOR_USER', 'BUDGET_EXHAUSTED'},
    'REPAIRING': {'PRECHECK', 'MODEL_BUILD', 'VALIDATION', 'FAIL', 'BUDGET_EXHAUSTED'},
    'REOPEN_VERIFY': {'DELIVERY_READY', 'FAIL', 'BLOCKED'},
    'DELIVERY_READY': {'PASS', 'FAIL'},
    'FAIL': {'DIAGNOSIS', 'REPAIR_READY', 'WAITING_FOR_USER', 'EVIDENCE_INTAKE', 'SPEC_COMPILATION',
             'MODEL_BUILD', 'BLOCKED', 'BUDGET_EXHAUSTED'},
    'BLOCKED': {'WAITING_FOR_USER', 'EVIDENCE_INTAKE', 'SPEC_COMPILATION', 'FAIL'},
    'BUDGET_EXHAUSTED': set(),
    'PASS': set(),
    'CALIBRATED_NOT_INDEPENDENTLY_VALIDATED': {'DELIVERY_READY', 'FAIL'},
}


class INVALID(ValueError):
    """Illegal workflow transition."""


class WorkflowStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._cases: dict[str, dict[str, Any]] = {}
        self._load_all()

    def _path(self, case_id: str) -> Path:
        return self.root / f'{case_id}.json'

    def _load_all(self):
        for path in self.root.glob('*.json'):
            data = json.loads(path.read_text(encoding='utf-8'))
            self._cases[data['case_id']] = data

    def _write(self, case: dict):
        self._path(case['case_id']).write_text(json.dumps(case, indent=2, sort_keys=True), encoding='utf-8')

    def create(self, case_id: str, **extra) -> dict:
        case = {
            'case_id': case_id, 'workflow_state': 'NEW', 'evidence_revision': 1,
            'spec_revision': 1, 'model_revision': 1, 'current_model_identity': None,
            'current_mph_path': None, 'current_run_id': None, 'study_id': None,
            'solver_id': None, 'solution_id': None, 'dataset_id': None,
            'accepted_assumptions': [], 'pending_decisions': [], 'invalidated_checks': [],
            'last_failure': None, 'repair_history': [], 'failed_baselines': [],
            'runs': {}, 'budgets': {'build_count': 0, 'solve_count': 0, 'repair_count': 0,
                                    'user_question_count': 0, 'calibration_run_count': 0,
                                    'max_builds': extra.get('max_builds', 20),
                                    'max_solves': extra.get('max_solves', 20),
                                    'max_repairs': extra.get('max_repairs', 10),
                                    'max_user_questions': extra.get('max_user_questions', 20)},
            'timestamps': {}, 'requires_revalidation': False, **extra,
        }
        self._cases[case_id] = case
        self._write(case)
        return dict(case)

    def get(self, case_id: str) -> dict:
        return dict(self._cases[case_id])

    def save(self, case: dict):
        self._cases[case['case_id']] = case
        self._write(case)

    def transition(self, case_id: str, target: str) -> dict:
        case = self._cases[case_id]
        current = case['workflow_state']
        if target not in TRANSITIONS.get(current, set()):
            raise INVALID(f'Cannot transition {current} -> {target}')
        case['workflow_state'] = target
        self._write(case)
        return dict(case)

    def force_state(self, case_id: str, target: str) -> dict:
        """Test/helper only: set state without a transition check."""
        if target not in STATES:
            raise INVALID(target)
        self._cases[case_id]['workflow_state'] = target
        self._write(self._cases[case_id])
        return dict(self._cases[case_id])
