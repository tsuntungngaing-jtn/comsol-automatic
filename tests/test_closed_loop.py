"""Deterministic closed-loop controller tests. Mock only; no COMSOL physics."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from server.calibration import CalibrationLedger
from server.decisions import DecisionGate
from server.evidence import EvidenceLedger, PromotionError
from server.observation_collector import ObservationCollector
from server.orchestrator import ClosedLoopController
from server.repair import RepairController
from server.workflow_state import INVALID, STATES, WorkflowStore


class EvidenceTests(unittest.TestCase):
    def test_reported_value_retained(self):
        ledger = EvidenceLedger()
        rec = ledger.add(quantity_id='thickness', value=0.5, unit='mm', origin='reported',
                         certainty='exact', source_type='paper', source_document='paper.pdf')
        self.assertEqual(rec['origin'], 'reported')
        self.assertEqual(ledger.get(rec['evidence_id'])['value'], 0.5)

    def test_library_cannot_become_reported(self):
        ledger = EvidenceLedger()
        rec = ledger.add(quantity_id='k', value=400, unit='W/(m*K)', origin='library',
                         certainty='exact_for_installed_library', source_type='material_library')
        with self.assertRaises(PromotionError):
            ledger.relabel_origin(rec['evidence_id'], 'reported')
        self.assertEqual(ledger.get(rec['evidence_id'])['origin'], 'library')

    def test_fitted_cannot_become_reported(self):
        ledger = EvidenceLedger()
        rec = ledger.add(quantity_id='theta', value=1.2, unit='1', origin='fitted',
                         certainty='estimated', source_type='calibration')
        with self.assertRaises(PromotionError):
            ledger.relabel_origin(rec['evidence_id'], 'reported')

    def test_missing_remains_missing(self):
        ledger = EvidenceLedger()
        rec = ledger.add(quantity_id='gap', value=None, unit='mm', origin='missing',
                         certainty='unknown', source_type='paper')
        self.assertEqual(rec['origin'], 'missing')
        self.assertEqual(rec['status'], 'missing')

    def test_conflicts_remain_conflict(self):
        ledger = EvidenceLedger()
        ledger.add(quantity_id='h', value=10, unit='mm', origin='reported', certainty='ambiguous',
                   source_type='paper', source_location='Table 1')
        ledger.add(quantity_id='h', value=12, unit='mm', origin='reported', certainty='ambiguous',
                   source_type='supplement', source_location='S2')
        conflict = ledger.conflicts('h')
        self.assertEqual(conflict['status'], 'conflict')
        self.assertEqual(len(conflict['candidate_values']), 2)


class DecisionTests(unittest.TestCase):
    def test_critical_missing_creates_decision(self):
        gate = DecisionGate()
        req = gate.evaluate_missing(
            quantity_id='thickness', description='paper missing thickness',
            affects=['solve', 'claim_validation'], current_task='solve',
            candidates=[{'value': 1.0, 'origin': 'library', 'source': 'Material Library'}],
            sensitivity='unknown')
        self.assertEqual(req['status'], 'pending')
        self.assertTrue(req['requires_user'])

    def test_unrelated_missing_does_not_block(self):
        gate = DecisionGate()
        req = gate.evaluate_missing(
            quantity_id='color', description='plot color scale',
            affects=['delivery_plot'], current_task='geometry_construction',
            candidates=[], sensitivity='unknown')
        self.assertIsNone(req)
        self.assertTrue(gate.task_may_proceed('geometry_construction', ['delivery_plot']))

    def test_user_supplied_retains_provenance(self):
        ledger = EvidenceLedger()
        rec = ledger.add(quantity_id='k', value=400, unit='W/(m*K)', origin='library',
                         certainty='exact_for_installed_library', source_type='material_library')
        resolved = ledger.apply_user_decision(rec['evidence_id'], action='select_candidate',
                                              decision='user_approved')
        self.assertEqual(resolved['origin'], 'library')
        self.assertEqual(resolved['decision'], 'user_approved')
        self.assertNotEqual(resolved['origin'], 'reported')


class StateMachineTests(unittest.TestCase):
    def test_invalid_transition_rejected(self):
        store = WorkflowStore(tempfile.mkdtemp())
        case = store.create('case-a')
        with self.assertRaises(INVALID):
            store.transition(case['case_id'], 'SOLVING')

    def test_waiting_cannot_silently_solve(self):
        store = WorkflowStore(tempfile.mkdtemp())
        case = store.create('case-b')
        store.transition(case['case_id'], 'EVIDENCE_INTAKE')
        store.transition(case['case_id'], 'SPEC_COMPILATION')
        store.transition(case['case_id'], 'WAITING_FOR_USER')
        with self.assertRaises(INVALID):
            store.transition(case['case_id'], 'SOLVING')
        self.assertEqual(store.get(case['case_id'])['workflow_state'], 'WAITING_FOR_USER')

    def test_fail_cannot_enter_delivery(self):
        store = WorkflowStore(tempfile.mkdtemp())
        case = store.create('case-c')
        store.force_state(case['case_id'], 'FAIL')
        with self.assertRaises(INVALID):
            store.transition(case['case_id'], 'DELIVERY_READY')

    def test_restart_loads_persistent_state(self):
        directory = tempfile.mkdtemp()
        store = WorkflowStore(directory)
        case = store.create('case-d')
        store.transition(case['case_id'], 'EVIDENCE_INTAKE')
        restored = WorkflowStore(directory)
        self.assertEqual(restored.get('case-d')['workflow_state'], 'EVIDENCE_INTAKE')
        self.assertIn('EVIDENCE_INTAKE', STATES)


class RevisionTests(unittest.TestCase):
    def test_mutation_increases_revision_and_invalidates(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        ctrl.start('rev-1', spec={'schema_version': 1})
        before = ctrl.state('rev-1')['model_revision']
        result = ctrl.mutate_model('rev-1', kind='geometry', note='change thickness')
        after = ctrl.state('rev-1')
        self.assertEqual(result['model_revision'], before + 1)
        self.assertTrue(after['invalidated_checks'])
        self.assertFalse(ctrl.may_reuse_validation('rev-1', run_id='old-run', model_revision=before))

    def test_old_run_cannot_validate_new_revision(self):
        collector = ObservationCollector()
        obs = collector.record(case_id='c', run_id='r1', spec_revision=1, model_revision=1,
                               expression='intop1(mflux)', value=0.1, unit='kg/s',
                               study='std1', solver='s1', solution='sol1', dataset='dset1')
        self.assertFalse(collector.admissible_for(obs, spec_revision=1, model_revision=2, run_id='r2'))


class ValidationLayerTests(unittest.TestCase):
    def test_solver_complete_conservation_fail_is_overall_fail(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        ctrl.start('val-a')
        ctrl.force_state('val-a', 'VALIDATION')
        report = ctrl.submit_validation('val-a', layers={
            'api': 'PASS', 'geometry': 'PASS', 'selection': 'PASS', 'physics': 'PASS',
            'numerical': 'FAIL', 'scientific': 'NOT_RUN', 'reopen': 'NOT_RUN',
        }, required=['api', 'geometry', 'selection', 'physics', 'numerical'])
        self.assertEqual(report['status'], 'FAIL')
        self.assertNotEqual(ctrl.state('val-a')['workflow_state'], 'DELIVERY_READY')
        self.assertNotEqual(ctrl.state('val-a')['workflow_state'], 'PASS')

    def test_required_check_missing_not_overall_pass(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        ctrl.start('val-b')
        ctrl.force_state('val-b', 'VALIDATION')
        report = ctrl.submit_validation('val-b', layers={
            'api': 'PASS', 'geometry': 'PASS', 'selection': 'PASS', 'physics': 'PASS',
            'numerical': 'NOT_RUN', 'scientific': 'PASS', 'reopen': 'NOT_RUN',
        }, required=['api', 'geometry', 'selection', 'physics', 'numerical', 'scientific'])
        self.assertEqual(report['status'], 'NOT_RUN')
        self.assertNotEqual(report['status'], 'PASS')

    def test_missing_module_blocked(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        ctrl.start('val-c')
        report = ctrl.block('val-c', reason='missing CFD module')
        self.assertEqual(report['workflow_state'], 'BLOCKED')


class RepairTests(unittest.TestCase):
    def test_failed_baseline_preserved_and_new_revision(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        repair = RepairController(ctrl)
        ctrl.start('rep-1')
        ctrl.force_state('rep-1', 'FAIL')
        baseline = repair.freeze_failed_baseline('rep-1', failure_id='f1')
        before = ctrl.state('rep-1')['model_revision']
        plan = repair.propose(case_id='rep-1', failure_id='f1', hypothesis='outlet selection wrong',
                              repair_type='mechanical', proposed_change='rebind outlet',
                              baseline_revision=before)
        applied = repair.apply(plan['repair_id'], admitted=True)
        self.assertEqual(baseline['immutable'], True)
        self.assertEqual(applied['after_revision'], before + 1)
        self.assertNotEqual(applied['after_revision'], baseline['model_revision'])
        self.assertTrue(ctrl.state('rep-1')['failed_baselines'])

    def test_repair_budget_enforced(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp(), budgets={'max_repairs': 1})
        repair = RepairController(ctrl)
        ctrl.start('rep-2')
        ctrl.force_state('rep-2', 'FAIL')
        repair.freeze_failed_baseline('rep-2', failure_id='f1')
        p1 = repair.propose(case_id='rep-2', failure_id='f1', hypothesis='a',
                            repair_type='mechanical', proposed_change='fix tag',
                            baseline_revision=ctrl.state('rep-2')['model_revision'])
        repair.apply(p1['repair_id'], admitted=True)
        p2 = repair.propose(case_id='rep-2', failure_id='f2', hypothesis='b',
                            repair_type='mechanical', proposed_change='fix tag2',
                            baseline_revision=ctrl.state('rep-2')['model_revision'])
        result = repair.apply(p2['repair_id'], admitted=True)
        self.assertEqual(result['status'], 'BUDGET_EXHAUSTED')
        self.assertEqual(ctrl.state('rep-2')['workflow_state'], 'BUDGET_EXHAUSTED')

    def test_mechanical_vs_epistemic(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        repair = RepairController(ctrl)
        ctrl.start('rep-3')
        mech = repair.propose(case_id='rep-3', failure_id='f1', hypothesis='bad tag',
                              repair_type='mechanical', proposed_change='rename tag',
                              baseline_revision=0)
        self.assertTrue(mech['admitted_automatically'])
        epi = repair.propose(case_id='rep-3', failure_id='f2', hypothesis='change BC meaning',
                             repair_type='epistemic', proposed_change='reinterpret outlet BC',
                             baseline_revision=0)
        self.assertTrue(epi['requires_user'])
        self.assertFalse(epi['admitted_automatically'])
        denied = repair.apply(epi['repair_id'], admitted=False)
        self.assertEqual(denied['status'], 'WAITING_FOR_USER')


class CalibrationTests(unittest.TestCase):
    def test_fitted_stays_fitted_and_cannot_self_validate(self):
        cal = CalibrationLedger()
        rec = cal.fit(parameter_id='theta', value=0.3, unit='1', target_claim_id='A',
                      method='least_squares', run_id='r-fit')
        self.assertEqual(rec['origin'], 'fitted')
        self.assertFalse(cal.may_independently_validate(parameter_id='theta', claim_id='A'))
        self.assertTrue(cal.may_independently_validate(parameter_id='theta', claim_id='B'))
        self.assertEqual(cal.final_status(parameter_id='theta', independent_claim_ids=[]),
                         'CALIBRATED_NOT_INDEPENDENTLY_VALIDATED')
        self.assertNotEqual(cal.final_status(parameter_id='theta', independent_claim_ids=[]), 'VALIDATED')


class DeliveryTests(unittest.TestCase):
    def test_reopen_required_or_not_run(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        ctrl.start('del-1')
        ctrl.force_state('del-1', 'REOPEN_VERIFY')
        report = ctrl.reopen_verify('del-1', performed=False)
        self.assertEqual(report['reopen'], 'NOT_RUN')
        self.assertNotEqual(report['status'], 'PASS')
        ctrl.force_state('del-1', 'REOPEN_VERIFY')
        ok = ctrl.reopen_verify('del-1', performed=True, saved_identity='mph-a',
                                reopened_identity='mph-b', observables_match=True)
        self.assertEqual(ok['reopen'], 'PASS')
        self.assertNotEqual(ok['saved_identity'], ok['reopened_identity'])


class GoldenFixtures(unittest.TestCase):
    def test_case_a_missing_thickness(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        started = ctrl.start('A', spec={'missing_information': [
            {'description': 'missing thickness', 'affects': ['solve']}]})
        admit_geom = ctrl.admit('A', 'geometry_construction')
        admit_solve = ctrl.admit('A', 'solve')
        self.assertTrue(admit_geom['success'])
        self.assertFalse(admit_solve['success'])
        self.assertEqual(started['workflow_state'], 'WAITING_FOR_USER')
        decision = ctrl.pending_decisions('A')[0]
        ctrl.resolve_decision('A', decision['decision_id'], action='supply_value',
                              value=0.8, unit='mm', origin='user_supplied')
        self.assertEqual(ctrl.evidence('A')[-1]['origin'], 'user_supplied')
        self.assertGreater(ctrl.state('A')['spec_revision'], 1)

    def test_case_b_mass_conservation_fail_repair(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        repair = RepairController(ctrl)
        ctrl.start('B')
        ctrl.record_execution('B', run_id='r12', status='PASS')
        ctrl.force_state('B', 'VALIDATION')
        report = ctrl.submit_validation('B', layers={
            'api': 'PASS', 'numerical': 'FAIL', 'scientific': 'NOT_RUN',
            'geometry': 'PASS', 'selection': 'PASS', 'physics': 'PASS', 'reopen': 'NOT_RUN',
        }, required=['api', 'numerical'])
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(ctrl.state('B')['workflow_state'], 'DIAGNOSIS')
        baseline = repair.freeze_failed_baseline('B', failure_id='mass')
        plan = repair.propose(case_id='B', failure_id='mass', hypothesis='outlet selection wrong',
                              repair_type='mechanical', proposed_change='rebind outlet',
                              baseline_revision=baseline['model_revision'])
        applied = repair.apply(plan['repair_id'], admitted=True)
        self.assertGreater(applied['after_revision'], baseline['model_revision'])
        self.assertTrue(ctrl.requires_revalidation('B'))

    def test_case_c_empty_selection_no_silent_fallback(self):
        ctrl = ClosedLoopController(tempfile.mkdtemp())
        ctrl.start('C')
        result = ctrl.bind_selection('C', selection_id='inlet', empty=True, allow_empty=False)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertFalse(result.get('fallback'))

    def test_case_d_stale_dataset(self):
        collector = ObservationCollector()
        obs = collector.record(case_id='D', run_id='old', spec_revision=1, model_revision=1,
                               expression='T', value=300, unit='K',
                               study='std1', solver='s1', solution='sol1', dataset='dset1')
        self.assertFalse(collector.admissible_for(obs, spec_revision=1, model_revision=1, run_id='new'))

    def test_case_e_fitted_parameter(self):
        cal = CalibrationLedger()
        cal.fit(parameter_id='theta', value=2.0, unit='1', target_claim_id='A',
                method='nlls', run_id='fit1')
        self.assertEqual(cal.get('theta')['origin'], 'fitted')
        self.assertFalse(cal.may_independently_validate('theta', 'A'))
        self.assertTrue(cal.may_independently_validate('theta', 'holdout_B'))

    def test_case_f_restart_historical(self):
        directory = tempfile.mkdtemp()
        ctrl = ClosedLoopController(directory)
        ctrl.start('F')
        ctrl.record_execution('F', run_id='job-1', status='recovery_pending')
        restored = ClosedLoopController(directory)
        job = restored.state('F')['runs']['job-1']
        self.assertEqual(job['status'], 'recovery_pending')
        self.assertFalse(job.get('verified'))
        self.assertNotEqual(restored.state('F')['workflow_state'], 'PASS')


class ClaimContractTests(unittest.TestCase):
    def test_claim_cannot_be_calibration_and_validation(self):
        from server.claims import ClaimContract
        with self.assertRaises(ValueError):
            ClaimContract.validate({
                'claim_id': 'A', 'observable': 'T', 'paper_value': 1, 'paper_unit': 'K',
                'validation_role': ['calibration', 'validation'],
            })


class SchemaTests(unittest.TestCase):
    def test_evidence_record_schema(self):
        from server.contracts import validate_document
        from server.evidence import EvidenceLedger
        rec = EvidenceLedger().add(quantity_id='h', value=1, unit='mm', origin='reported',
                                   certainty='exact', source_type='paper')
        result = validate_document(rec, 'evidence-record')
        self.assertEqual(result['schema_status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
