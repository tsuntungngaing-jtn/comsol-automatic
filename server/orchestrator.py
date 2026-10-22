"""Thin closed-loop controller over existing MCP/contracts. No extra agents."""
from __future__ import annotations

from typing import Any

from .contracts import aggregate
from .decisions import DecisionGate
from .evidence import EvidenceLedger
from .workflow_state import WorkflowStore

LAYER_ORDER = ('api', 'geometry', 'selection', 'physics', 'numerical', 'scientific', 'reopen')


class ClosedLoopController:
    def __init__(self, root, budgets: dict | None = None):
        extra = {}
        if budgets:
            extra.update(budgets)
        self.store = WorkflowStore(root)
        self._evidence: dict[str, EvidenceLedger] = {}
        self._specs: dict[str, dict] = {}
        self._gate = DecisionGate()
        self._default_budgets = extra

    def start(self, case_id: str, spec: dict | None = None) -> dict:
        extra = dict(self._default_budgets)
        case = self.store.create(case_id, **extra)
        spec = dict(spec or {})
        self._specs[case_id] = spec
        self._evidence[case_id] = EvidenceLedger()
        missing = spec.get('missing_information') or []
        decisions = []
        for item in missing:
            req = self._gate.evaluate_missing(
                quantity_id=item.get('quantity_id') or item['description'],
                description=item['description'], affects=item.get('affects') or [],
                current_task='solve', candidates=item.get('candidates') or [],
                sensitivity='unknown')
            if req:
                decisions.append(req)
        case = self.store.get(case_id)
        case['pending_decisions'] = decisions
        case['spec'] = spec
        self.store.save(case)
        if decisions:
            return self.store.transition(case_id, 'WAITING_FOR_USER')
        return self.store.transition(case_id, 'EVIDENCE_INTAKE')

    def state(self, case_id: str) -> dict:
        return self.store.get(case_id)

    def evidence(self, case_id: str) -> list[dict]:
        return self._evidence[case_id].all()

    def pending_decisions(self, case_id: str) -> list[dict]:
        return list(self.store.get(case_id).get('pending_decisions') or [])

    def admit(self, case_id: str, task: str) -> dict:
        spec = self._specs.get(case_id) or self.store.get(case_id).get('spec') or {}
        missing = spec.get('missing_information') or []
        blockers = [{'task': task, 'reason': m['description']}
                    for m in missing if task in (m.get('affects') or [])]
        allowed = not blockers
        return {'success': allowed, 'status': 'PASS' if allowed else 'BLOCKED',
                'task': task, 'blockers': blockers}

    def resolve_decision(self, case_id: str, decision_id: str, action: str, **payload) -> dict:
        case = self.store.get(case_id)
        pending = [d for d in case.get('pending_decisions') or [] if d['decision_id'] != decision_id]
        matched = [d for d in case.get('pending_decisions') or [] if d['decision_id'] == decision_id]
        origin = payload.get('origin') or ('library' if action == 'select_candidate' else 'user_supplied')
        rec = self._evidence[case_id].add(
            quantity_id=(matched[0].get('quantity_id') if matched else 'user'),
            value=payload.get('value'), unit=payload.get('unit'),
            origin=origin, certainty=payload.get('certainty') or 'user_confirmed',
            source_type='user', affects=matched[0].get('affected_tasks') if matched else [])
        if action in ('select_candidate', 'approve_assumption', 'supply_value'):
            rec = self._evidence[case_id].apply_user_decision(
                rec['evidence_id'], action=action, decision='user_approved',
                value=payload.get('value'), unit=payload.get('unit'), origin=origin)
        case['pending_decisions'] = pending
        case['spec_revision'] = int(case['spec_revision']) + 1
        case['evidence_revision'] = int(case['evidence_revision']) + 1
        case['budgets']['user_question_count'] += 1
        self.store.save(case)
        if case['workflow_state'] == 'WAITING_FOR_USER' and not pending:
            self.store.transition(case_id, 'SPEC_COMPILATION')
        return rec

    def mutate_model(self, case_id: str, kind: str, note: str = '') -> dict:
        case = self.store.get(case_id)
        case['model_revision'] = int(case['model_revision']) + 1
        invalidated = ['geometry', 'selections', 'material_domains', 'physics_bindings',
                       'mesh', 'numerical', 'scientific']
        case['invalidated_checks'] = invalidated
        case['requires_revalidation'] = True
        case['last_mutation'] = {'kind': kind, 'note': note, 'model_revision': case['model_revision']}
        self.store.save(case)
        return {'model_revision': case['model_revision'], 'invalidated_checks': invalidated}

    def may_reuse_validation(self, case_id: str, run_id: str, model_revision: int) -> bool:
        case = self.store.get(case_id)
        return (run_id == case.get('current_run_id')
                and model_revision == case['model_revision']
                and not case.get('invalidated_checks'))

    def submit_validation(self, case_id: str, layers: dict, required: list[str] | None = None) -> dict:
        required = required or list(layers)
        checks = [{'status': layers.get(name, 'NOT_RUN'), 'required': name in required, 'id': name}
                  for name in LAYER_ORDER]
        status = aggregate(checks)
        case = self.store.get(case_id)
        case['last_validation'] = {'status': status, 'layers': layers}
        self.store.save(case)
        if status == 'FAIL':
            try:
                self.store.transition(case_id, 'DIAGNOSIS')
            except Exception:
                self.store.force_state(case_id, 'DIAGNOSIS')
            case = self.store.get(case_id)
            case['last_failure'] = {'kind': 'NUMERICAL_FAILURE' if layers.get('numerical') == 'FAIL' else 'CLAIM_MISMATCH',
                                    'layers': layers}
            self.store.save(case)
        elif status == 'PASS':
            try:
                self.store.transition(case_id, 'REOPEN_VERIFY')
            except Exception:
                pass
        return {'status': status, 'layers': layers, 'workflow_state': self.state(case_id)['workflow_state']}

    def block(self, case_id: str, reason: str) -> dict:
        case = self.store.get(case_id)
        case['last_failure'] = {'kind': 'BLOCKED', 'reason': reason}
        self.store.save(case)
        if case['workflow_state'] == 'NEW':
            self.store.transition(case_id, 'BLOCKED')
        else:
            try:
                self.store.transition(case_id, 'BLOCKED')
            except Exception:
                self.store.force_state(case_id, 'BLOCKED')
        return self.state(case_id)

    def force_state(self, case_id: str, target: str) -> dict:
        return self.store.force_state(case_id, target)

    def record_execution(self, case_id: str, run_id: str, status: str) -> dict:
        case = self.store.get(case_id)
        case['runs'][run_id] = {'status': status, 'verified': False, 'run_id': run_id,
                                'spec_revision': case['spec_revision'],
                                'model_revision': case['model_revision']}
        case['current_run_id'] = run_id
        case['budgets']['solve_count'] += 1
        self.store.save(case)
        return case['runs'][run_id]

    def bind_selection(self, case_id: str, selection_id: str, empty: bool, allow_empty: bool) -> dict:
        if empty and not allow_empty:
            return {'status': 'BLOCKED', 'selection_id': selection_id, 'fallback': False,
                    'reason': 'Empty required selection'}
        return {'status': 'PASS', 'selection_id': selection_id, 'fallback': False}

    def reopen_verify(self, case_id: str, performed: bool, saved_identity: str | None = None,
                      reopened_identity: str | None = None, observables_match: bool = False) -> dict:
        if not performed:
            return {'status': 'NOT_RUN', 'reopen': 'NOT_RUN',
                    'workflow_state': self.state(case_id)['workflow_state']}
        if not saved_identity or not reopened_identity or saved_identity == reopened_identity:
            return {'status': 'FAIL', 'reopen': 'FAIL', 'reason': 'Reopen identity must be distinct'}
        if not observables_match:
            return {'status': 'FAIL', 'reopen': 'FAIL'}
        try:
            self.store.transition(case_id, 'DELIVERY_READY')
        except Exception:
            self.store.force_state(case_id, 'DELIVERY_READY')
        return {'status': 'PASS', 'reopen': 'PASS', 'saved_identity': saved_identity,
                'reopened_identity': reopened_identity}

    def requires_revalidation(self, case_id: str) -> bool:
        return bool(self.store.get(case_id).get('requires_revalidation'))

    def delivery_report(self, case_id: str) -> dict:
        case = self.state(case_id)
        return {
            'case_id': case_id, 'final_workflow_state': case['workflow_state'],
            'MPH_path': case.get('current_mph_path'), 'model_revision': case['model_revision'],
            'spec_revision': case['spec_revision'], 'run_id': case.get('current_run_id'),
            'assumptions': case.get('accepted_assumptions'),
            'unresolved_information': case.get('pending_decisions'),
            'repair_count': case['budgets']['repair_count'],
            'solve_count': case['budgets']['solve_count'],
            'failed_baselines': case.get('failed_baselines'),
        }
