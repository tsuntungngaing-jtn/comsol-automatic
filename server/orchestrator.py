"""Thin closed-loop controller over existing MCP/contracts. No extra agents."""
from __future__ import annotations

from typing import Any
import math
import copy

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
        self._hydrate()

    def _hydrate(self):
        for case_id, case in self.store._cases.items():
            self._specs[case_id] = dict(case.get('spec') or {})
            self._evidence[case_id] = EvidenceLedger.from_records(case.get('evidence_records') or [])

    def _flush_evidence(self, case_id: str):
        case = self.store.get(case_id)
        case['evidence_records'] = self._evidence[case_id].all()
        case['spec'] = self._specs.get(case_id, case.get('spec') or {})
        self.store.save(case)

    def start(self, case_id: str, spec: dict | None = None) -> dict:
        extra = dict(self._default_budgets)
        spec = copy.deepcopy(spec or {})
        self._validate_acceptance(spec.get('acceptance_spec'))
        case = self.store.create(case_id, **extra)
        self._specs[case_id] = spec
        self._evidence[case_id] = EvidenceLedger()
        missing = spec.get('missing_information') or []
        decisions = []
        for item in missing:
            if item.get('resolved'):
                continue
            req = self._gate.evaluate_missing(
                quantity_id=item.get('quantity_id') or item['description'],
                description=item['description'], affects=item.get('affects') or [],
                current_task=(item.get('affects') or ['solve'])[0], candidates=item.get('candidates') or [],
                sensitivity='unknown')
            if req:
                decisions.append(req)
        case = self.store.get(case_id)
        case['pending_decisions'] = decisions
        case['spec'] = spec
        case['evidence_records'] = self._evidence[case_id].all()
        self.store.save(case)
        if not self.admit(case_id, spec.get('current_task', 'solve'))['success']:
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
                    for m in missing if not m.get('resolved') and task in (m.get('affects') or [])]
        allowed = not blockers
        return {'success': allowed, 'status': 'PASS' if allowed else 'BLOCKED',
                'task': task, 'blockers': blockers}

    def resolve_decision(self, case_id: str, decision_id: str, action: str, **payload) -> dict:
        case = self.store.get(case_id)
        pending = [d for d in case.get('pending_decisions') or [] if d['decision_id'] != decision_id]
        matched = [d for d in case.get('pending_decisions') or [] if d['decision_id'] == decision_id]
        if not matched:
            raise ValueError('Unknown or already resolved decision')
        if action not in ('select_candidate', 'approve_assumption', 'supply_value'):
            raise ValueError('Unsupported decision action')
        if payload.get('value') is None:
            raise ValueError('A supplied value is required to resolve missing information')
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
        for item in self._specs[case_id].get('missing_information') or []:
            if (item.get('quantity_id') or item['description']) == matched[0]['quantity_id']:
                item['resolved'] = True
        case.pop('acceptance_result', None)
        if case['workflow_state'] == 'PASS':
            case['workflow_state'] = 'SPEC_COMPILATION'
        case['pending_decisions'] = pending
        case['spec_revision'] = int(case['spec_revision']) + 1
        case['evidence_revision'] = int(case['evidence_revision']) + 1
        case['budgets']['user_question_count'] += 1
        case['evidence_records'] = self._evidence[case_id].all()
        case['spec'] = self._specs.get(case_id) or case.get('spec') or {}
        self.store.save(case)
        if case['workflow_state'] == 'WAITING_FOR_USER' and self.admit(case_id, case['spec'].get('current_task', 'solve'))['success']:
            self.store.transition(case_id, 'SPEC_COMPILATION')
            flushed = self.store.get(case_id)
            flushed['evidence_records'] = self._evidence[case_id].all()
            self.store.save(flushed)
        return rec

    def mutate_model(self, case_id: str, kind: str, note: str = '') -> dict:
        case = self.store.get(case_id)
        case['model_revision'] = int(case['model_revision']) + 1
        invalidated = ['geometry', 'selections', 'material_domains', 'physics_bindings',
                       'mesh', 'numerical', 'scientific']
        case['invalidated_checks'] = invalidated
        case['requires_revalidation'] = True
        if case['workflow_state'] == 'PASS':
            case['workflow_state'] = 'MODEL_BUILD'
        case['last_mutation'] = {'kind': kind, 'note': note, 'model_revision': case['model_revision']}
        self.store.save(case)
        return {'model_revision': case['model_revision'], 'invalidated_checks': invalidated}

    def may_reuse_validation(self, case_id: str, run_id: str, model_revision: int) -> bool:
        case = self.store.get(case_id)
        return (run_id == case.get('current_run_id')
                and model_revision == case['model_revision']
                and case['runs'].get(run_id, {}).get('spec_revision') == case['spec_revision']
                and not case.get('invalidated_checks'))

    def submit_validation(self, case_id: str, layers: dict, required: list[str] | None = None,
                          *, run_id: str | None = None, model_revision: int | None = None,
                          spec_revision: int | None = None) -> dict:
        case = self.store.get(case_id)
        if any(v is not None for v in (run_id, model_revision, spec_revision)):
            run = case['runs'].get(run_id, {})
            if (run_id != case.get('current_run_id') or model_revision != case['model_revision']
                    or spec_revision != case['spec_revision'] or run.get('model_revision') != model_revision
                    or run.get('spec_revision') != spec_revision):
                return {'status': 'STALE', 'layers': layers}
        required = list(layers) if required is None else required
        if set(layers) - set(LAYER_ORDER) or set(required) - set(LAYER_ORDER):
            raise ValueError('Unknown validation layer')
        checks = [{'status': layers.get(name, 'NOT_RUN'), 'required': name in required, 'id': name}
                  for name in LAYER_ORDER]
        status = aggregate(checks)
        case = self.store.get(case_id)
        case['last_validation'] = {'status': status, 'layers': layers,
                                   'run_id': case.get('current_run_id'),
                                   'model_revision': case['model_revision'],
                                   'spec_revision': case['spec_revision']}
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

    def record_execution(self, case_id: str, run_id: str, status: str, details: dict | None = None) -> dict:
        case = self.store.get(case_id)
        if status not in ('PASS', 'COMPLETED', 'SUCCESS', 'FAIL', 'BLOCKED', 'NOT_RUN', 'ABORTED', 'PARTIAL', 'recovery_pending'):
            raise ValueError('Unknown execution status')
        if run_id in case['runs']:
            raise ValueError('Run IDs cannot be reused')
        case.pop('acceptance_result', None)
        if case['workflow_state'] == 'PASS':
            case['workflow_state'] = 'VALIDATION'
        if status in ('FAIL', 'ABORTED'):
            case['workflow_state'] = 'FAIL'
        elif status == 'BLOCKED':
            case['workflow_state'] = 'BLOCKED'
        case['runs'][run_id] = {'status': status, 'verified': False, 'run_id': run_id,
                                'details': copy.deepcopy(details or {}),
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
            'execution_status': case['runs'].get(case.get('current_run_id'), {}).get('status', 'NOT_RUN'),
            'execution_details': case['runs'].get(case.get('current_run_id'), {}).get('details', {}),
            'check_status': self._current_check_status(case),
            'paper_comparison_status': self.acceptance_status(case_id),
            'acceptance_result': case.get('acceptance_result'),
            'delivery_status': 'AVAILABLE',
            'artifacts': case.get('artifacts', []),
            'case_id': case_id, 'final_workflow_state': case['workflow_state'],
            'MPH_path': case.get('current_mph_path'), 'model_revision': case['model_revision'],
            'spec_revision': case['spec_revision'], 'run_id': case.get('current_run_id'),
            'assumptions': case.get('accepted_assumptions'),
            'unresolved_information': case.get('pending_decisions'),
            'repair_count': case['budgets']['repair_count'],
            'solve_count': case['budgets']['solve_count'],
            'failed_baselines': case.get('failed_baselines'),
        }

    @staticmethod
    def _validate_acceptance(spec):
        if spec is None:
            return
        if not isinstance(spec, dict) or not isinstance(spec.get('criteria'), list) or not spec['criteria']:
            raise ValueError('acceptance_spec requires nonempty criteria')
        required = spec.get('required_checks', [])
        if not isinstance(required, list) or any(name not in LAYER_ORDER for name in required):
            raise ValueError('required_checks must name supported validation layers')
        ids = set()
        for criterion in spec['criteria']:
            if not isinstance(criterion, dict) or not isinstance(criterion.get('id'), str) or not criterion['id'] or criterion['id'] in ids:
                raise ValueError('Criteria require unique IDs')
            ids.add(criterion['id'])
            if criterion.get('metric') not in ('relative_error', 'absolute_error'):
                raise ValueError('Explicit relative_error or absolute_error metric required')
            for key in ('reference', 'tolerance'):
                value = criterion.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError('Finite reference and tolerance required')
            if criterion['tolerance'] < 0 or (criterion['metric'] == 'relative_error' and criterion['reference'] == 0):
                raise ValueError('Invalid tolerance or zero relative-error reference')
            if not isinstance(criterion.get('unit'), str) or not criterion['unit'].strip():
                raise ValueError('Explicit unit required; use 1 for dimensionless values')

    @staticmethod
    def _current_check_status(case):
        result = case.get('last_validation')
        if not result:
            return 'NOT_RUN'
        if any(result.get(key) != case.get(key) for key in ('model_revision', 'spec_revision')) or result.get('run_id') != case.get('current_run_id'):
            return 'STALE'
        return result['status']

    def acceptance_status(self, case_id):
        case = self.state(case_id)
        if not case.get('spec', {}).get('acceptance_spec'):
            return 'NOT_CONFIGURED'
        result = case.get('acceptance_result')
        if not result:
            return 'NOT_RUN'
        if any(result[key] != case[key] for key in ('model_revision', 'spec_revision')) or result['run_id'] != case.get('current_run_id'):
            return 'STALE'
        return result['status']

    def evaluate_acceptance(self, case_id: str, run_id: str, model_revision: int,
                            spec_revision: int, observations: dict) -> dict:
        case = self.state(case_id)
        contract = case.get('spec', {}).get('acceptance_spec')
        if not contract:
            return {'status': 'NOT_CONFIGURED', 'criteria': []}
        run = case['runs'].get(run_id, {})
        if (run_id != case.get('current_run_id') or model_revision != case['model_revision']
                or spec_revision != case['spec_revision'] or run.get('model_revision') != model_revision
                or run.get('spec_revision') != spec_revision):
            return {'status': 'STALE', 'criteria': []}
        checks = []
        for criterion in contract['criteria']:
            obs = observations.get(criterion['id'])
            check = {'id': criterion['id'], 'status': 'NOT_RUN', 'criterion': criterion,
                     'evidence_authentication': 'caller_supplied_unverified'}
            if obs is not None:
                value = obs.get('value') if isinstance(obs, dict) else None
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or obs.get('unit') != criterion['unit']):
                    check['status'] = 'FAIL'
                    check['reason'] = 'Invalid value or mismatched unit'
                else:
                    error = abs(value - criterion['reference'])
                    if criterion['metric'] == 'relative_error':
                        error /= abs(criterion['reference'])
                    check.update(status='PASS' if error < criterion['tolerance'] else 'FAIL',
                                 error=error, observation=obs)
            checks.append(check)
        status = aggregate([{**c, 'required': True} for c in checks])
        if run.get('status') not in ('PASS', 'COMPLETED', 'SUCCESS'):
            status = 'BLOCKED'
        result = {'status': status, 'criteria': checks, 'run_id': run_id,
                  'model_revision': model_revision, 'spec_revision': spec_revision,
                  'scope': 'configured_criteria_only', 'evidence_authentication': 'caller_supplied_unverified'}
        case['acceptance_result'] = result
        self.store.save(case)
        return result

    def deliver(self, case_id: str, artifacts: list[dict] | None = None) -> dict:
        """Record deliverable paths, including failed models/logs, without judging success."""
        case = self.state(case_id)
        case['artifacts'] = list(artifacts or [])
        self.store.save(case)
        return self.delivery_report(case_id)
