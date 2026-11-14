import asyncio
import tempfile
import unittest
from types import SimpleNamespace
from server.orchestrator import ClosedLoopController
from server.controller_tools import register_controller_tools
from server.workflow_state import INVALID


class ExecutionAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ctrl = ClosedLoopController(self.tmp.name)

    def start(self, tolerance=None):
        spec = {} if tolerance is None else {'acceptance_spec': {'criteria': [
            {'id': 'T', 'metric': 'relative_error', 'reference': 100,
             'tolerance': tolerance, 'unit': 'K'}]}}
        self.ctrl.start('c', spec)
        self.ctrl.record_execution('c', 'r', 'COMPLETED')

    def test_no_criteria_executes_and_delivers_without_pass(self):
        self.start()
        result = self.ctrl.deliver('c', [{'path': 'model.mph'}])
        self.assertEqual(result['execution_status'], 'COMPLETED')
        self.assertEqual(result['paper_comparison_status'], 'NOT_CONFIGURED')
        self.ctrl.force_state('c', 'DELIVERY_READY')
        with self.assertRaises(INVALID):
            self.ctrl.store.transition('c', 'PASS')

    def test_explicit_fifteen_percent_and_custom_tolerance(self):
        for tolerance, expected in [(0.15, 'PASS'), (0.05, 'FAIL')]:
            with self.subTest(tolerance=tolerance):
                self.start(tolerance)
                result = self.ctrl.evaluate_acceptance('c', 'r', 1, 1, {'T': {'value': 110, 'unit': 'K'}})
                self.assertEqual(result['status'], expected)
                self.assertEqual(result['evidence_authentication'], 'caller_supplied_unverified')

    def test_failure_logs_deliver_without_acceptance(self):
        self.ctrl.start('c')
        self.ctrl.record_execution('c', 'failed', 'FAIL')
        self.ctrl.force_state('c', 'FAIL')
        result = self.ctrl.deliver('c', [{'path': 'failed.mph'}, {'path': 'solve.log'}])
        self.assertEqual(result['execution_status'], 'FAIL')
        self.assertEqual(result['final_workflow_state'], 'FAIL')
        self.assertEqual(len(result['artifacts']), 2)

    def test_validation_information_does_not_block_solve(self):
        result = self.ctrl.start('c', {'missing_information': [
            {'quantity_id': 'reference', 'description': 'reference unavailable', 'affects': ['claim_validation']}]})
        self.assertEqual(result['workflow_state'], 'EVIDENCE_INTAKE')
        self.assertTrue(self.ctrl.admit('c', 'solve')['success'])
        self.assertFalse(self.ctrl.admit('c', 'claim_validation')['success'])
        self.assertTrue(self.ctrl.pending_decisions('c'))

    def test_real_solve_dependency_remains_until_supplied(self):
        result = self.ctrl.start('c', {'missing_information': [
            {'quantity_id': 'thickness', 'description': 'thickness missing', 'affects': ['solve']}]})
        self.assertEqual(result['workflow_state'], 'WAITING_FOR_USER')
        self.assertFalse(self.ctrl.admit('c', 'solve')['success'])
        decision = self.ctrl.pending_decisions('c')[0]
        self.ctrl.resolve_decision('c', decision['decision_id'], 'supply_value', value=1, unit='mm')
        self.assertTrue(self.ctrl.admit('c', 'solve')['success'])
        self.assertEqual(self.ctrl.evidence('c')[-1]['origin'], 'user_supplied')

    def test_stale_run_revision_and_spec_never_pass(self):
        self.start(.15)
        obs = {'T': {'value': 100, 'unit': 'K'}}
        self.assertEqual(self.ctrl.evaluate_acceptance('c', 'r', 1, 1, obs)['status'], 'PASS')
        self.ctrl.mutate_model('c', 'geometry')
        self.assertEqual(self.ctrl.acceptance_status('c'), 'STALE')
        self.assertEqual(self.ctrl.evaluate_acceptance('c', 'r', 1, 1, obs)['status'], 'STALE')
        self.assertEqual(self.ctrl.evaluate_acceptance('c', 'r', 2, 1, obs)['status'], 'STALE')
        self.ctrl.record_execution('c', 'new', 'COMPLETED')
        self.assertEqual(self.ctrl.evaluate_acceptance('c', 'new', 2, 2, obs)['status'], 'STALE')
        self.assertEqual(self.ctrl.acceptance_status('c'), 'NOT_RUN')

    def test_missing_values_and_wrong_units_not_pass(self):
        self.start(.15)
        self.assertEqual(self.ctrl.evaluate_acceptance('c', 'r', 1, 1, {})['status'], 'NOT_RUN')
        self.assertEqual(self.ctrl.evaluate_acceptance('c', 'r', 1, 1, {'T': {'value': 100, 'unit': 'C'}})['status'], 'FAIL')

    def test_failed_run_cannot_pass_matching_criteria(self):
        self.start(.15)
        self.ctrl.record_execution('c', 'failed', 'FAIL')
        result = self.ctrl.evaluate_acceptance('c', 'failed', 1, 1, {'T': {'value': 100, 'unit': 'K'}})
        self.assertEqual(result['status'], 'BLOCKED')

    def test_exact_threshold_fails_and_absolute_zero_reference_works(self):
        self.start(.15)
        self.assertEqual(self.ctrl.evaluate_acceptance('c', 'r', 1, 1,
                         {'T': {'value': 115, 'unit': 'K'}})['status'], 'FAIL')
        self.ctrl.start('absolute', {'acceptance_spec': {'criteria': [
            {'id': 'delta', 'metric': 'absolute_error', 'reference': 0,
             'tolerance': .1, 'unit': 'Pa'}]}})
        self.ctrl.record_execution('absolute', 'r', 'COMPLETED')
        self.assertEqual(self.ctrl.evaluate_acceptance('absolute', 'r', 1, 1,
                         {'delta': {'value': .05, 'unit': 'Pa'}})['status'], 'PASS')

    def test_required_checks_do_not_disappear_behind_paper_match(self):
        self.ctrl.start('c', {'acceptance_spec': {'required_checks': ['numerical', 'scientific'],
            'criteria': [{'id': 'q', 'metric': 'relative_error', 'reference': 10,
                          'tolerance': .15, 'unit': 'W'}]}})
        self.ctrl.record_execution('c', 'r', 'COMPLETED')
        self.ctrl.evaluate_acceptance('c', 'r', 1, 1, {'q': {'value': 10, 'unit': 'W'}})
        self.ctrl.force_state('c', 'DELIVERY_READY')
        with self.assertRaises(INVALID):
            self.ctrl.store.transition('c', 'PASS')
        self.ctrl.submit_validation('c', {'numerical': 'PASS', 'scientific': 'NOT_RUN'})
        self.ctrl.force_state('c', 'DELIVERY_READY')
        with self.assertRaises(INVALID):
            self.ctrl.store.transition('c', 'PASS')
        self.ctrl.submit_validation('c', {'numerical': 'PASS', 'scientific': 'PASS'})
        self.ctrl.force_state('c', 'DELIVERY_READY')
        self.assertEqual(self.ctrl.store.transition('c', 'PASS')['workflow_state'], 'PASS')

    def test_remaining_final_validation_question_does_not_keep_solve_waiting(self):
        self.ctrl.start('c', {'missing_information': [
            {'description': 'thickness', 'affects': ['solve']},
            {'description': 'reference', 'affects': ['claim_validation']}]})
        decision = self.ctrl.pending_decisions('c')[0]
        self.ctrl.resolve_decision('c', decision['decision_id'], 'supply_value', value=1, unit='mm')
        self.assertEqual(self.ctrl.state('c')['workflow_state'], 'SPEC_COMPILATION')
        self.assertFalse(self.ctrl.admit('c', 'claim_validation')['success'])

    def test_restart_preserves_contract_and_comparison(self):
        self.start(.07)
        self.ctrl.evaluate_acceptance('c', 'r', 1, 1, {'T': {'value': 110, 'unit': 'K'}})
        restored = ClosedLoopController(self.tmp.name)
        self.assertEqual(restored.delivery_report('c')['paper_comparison_status'], 'FAIL')

    def test_invalid_contract_has_no_created_case(self):
        with self.assertRaises(ValueError):
            self.ctrl.start('bad', {'acceptance_spec': {'criteria': [
                {'id': 'zero', 'metric': 'relative_error', 'reference': 0,
                 'tolerance': .15, 'unit': 'W'}]}})
        with self.assertRaises(KeyError):
            self.ctrl.state('bad')

    def test_registered_tools_use_persisted_contract(self):
        class MCP:
            def __init__(self): self.tools = {}
            def tool(self):
                def register(fn):
                    self.tools[fn.__name__] = fn
                    return fn
                return register
        mcp = MCP()
        register_controller_tools(mcp, SimpleNamespace(output_root=self.tmp.name))
        async def exercise():
            await mcp.tools['workflow_start']('tools')
            await mcp.tools['workflow_record_execution']('tools', 'run', 'COMPLETED')
            report = await mcp.tools['workflow_deliver']('tools', [{'path': 'out.mph'}])
            self.assertEqual(report['paper_comparison_status'], 'NOT_CONFIGURED')
            result = await mcp.tools['workflow_evaluate_acceptance']('tools', 'run', 1, 1, {})
            self.assertEqual(result['status'], 'NOT_CONFIGURED')
        asyncio.run(exercise())
