"""Software fault injection only; no COMSOL physics validation."""
import asyncio
import copy
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from server.contracts import validate_document, admit_task, new_report
from server.runtime import Runtime
from server.scientific_gates import evaluate

ROOT=Path(__file__).resolve().parents[1]
class PortfolioTests(unittest.TestCase):
    def spec(self):
        return json.loads((ROOT/'benchmarks/tasks/simple_block.json').read_text())

    def test_malformed_previously_ignored_fields(self):
        for key in ('physics','mesh','study','solver','observables','assumptions','missing_information'):
            doc=self.spec(); doc[key]=42
            self.assertEqual(validate_document(doc)['status'],'FAIL',key)
        doc=self.spec();doc['physics']={'boundaries':[42]}
        self.assertEqual(validate_document(doc)['status'],'FAIL')

    def test_dependency_blocks_only_affected_task(self):
        doc=self.spec();doc['missing_information']=[{'description':'missing thickness','affects':['solve']}]
        report=validate_document(doc)
        self.assertEqual(report['schema_status'],'PASS')
        self.assertFalse(report['execution_admissible'])
        self.assertEqual(report['status'],'BLOCKED')
        self.assertFalse(admit_task(doc,'solve')['success'])
        self.assertTrue(admit_task(doc,'independent_geometry')['success'])

    def test_wrong_run_and_unobserved_evidence(self):
        doc=new_report('new','a'*64,{})
        check={'id':'x','status':'PASS','run_id':'old','measured':1,'reference':1,'unit':'m','tolerance':{},'evidence':'artifact','required':True}
        doc['layers']['geometry']={'status':'PASS','checks':[check]}
        self.assertFalse(validate_document(doc,'validation-report')['success'])
        check['run_id']='new';check['measured']=None
        self.assertFalse(validate_document(doc,'validation-report')['success'])

    def identity(self):
        expected=dict(run_id='new',model_revision=1,study='std1',solver='s1',solution='sol1',dataset='d1',parameters_hash='a'*64)
        return {'expected':expected,'observed':dict(expected,solve_status='PASS',new_solution=True)}

    def test_old_dataset_blocks_metrics(self):
        identity=self.identity();identity['observed']['run_id']='old'
        self.assertEqual(evaluate('freshness',identity)['status'],'FAIL')
        self.assertEqual(evaluate('conservation',{'identity':identity})['status'],'NOT_RUN')

    def test_plateau_and_incompatible_histories(self):
        samples=[dict(iteration=i,residual=1500,group='u,p,T',scaling='relative',termination_criterion='1e-3') for i in range(9)]
        payload=dict(samples=samples,window=8,minimum_fractional_drop=.01)
        result=evaluate('plateau',payload)
        self.assertTrue(result['plateau_alarm']);self.assertFalse(result['solver_stopped'])
        samples[-1]['scaling']='absolute'
        self.assertEqual(evaluate('plateau',payload)['status'],'NOT_RUN')

    def test_conservation_missing_terms_and_signed_units(self):
        terms=[dict(id=k,value=1,sign=sign,expression='integral',selection=k,evidence='artifact',unit='W') for k,sign in [('in',1),('out',-1)]]
        p=dict(identity=self.identity(),required_terms=['in','out'],terms=terms,unit='W',normalization=1,normalization_definition='input power',tolerance=.01)
        self.assertEqual(evaluate('conservation',p)['status'],'PASS')
        p['required_terms'].append('storage')
        self.assertEqual(evaluate('conservation',p)['status'],'NOT_RUN')

    def test_unrun_comparison_is_not_pass(self):
        self.assertEqual(evaluate('comparison',{'runs':[]})['status'],'NOT_RUN')

    def test_persistent_jobs_busy_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime=Runtime(output_root=directory); start=threading.Event(); release=threading.Event()
            model=SimpleNamespace(name=lambda:'mock',solve=lambda study:(start.set(),release.wait(3)))
            runtime.manager=SimpleNamespace(current_model='mock',is_connected=True,get_model=lambda name:model)
            try:
                job=runtime.submit_study(None,'mock')['job_id'];self.assertTrue(start.wait(2))
                self.assertTrue(runtime.queue_status()['busy'])
                self.assertEqual(asyncio.run(runtime.call(lambda:42))['error'],'JVM_BUSY')
                self.assertEqual(runtime.cancel_job(job)['cancellation'],'cancel_not_supported')
                release.set();runtime.futures[job].result(3)
            finally:
                release.set();runtime.executor.shutdown()
            restored=Runtime(output_root=directory)
            try:
                self.assertEqual(restored.job_status(job)['status'],'recovery_pending')
                self.assertFalse(restored.futures)
            finally:restored.executor.shutdown()

    def test_reviewer_has_no_code_or_mutation(self):
        from server.main import create_server
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'COMSOL_TOOL_ROLE':'reviewer'}):
            runtime=Runtime(output_root=directory)
            try:
                mcp,_=create_server(runtime)
                names={t.name for t in asyncio.run(mcp.list_tools())}
                self.assertIn('validation_gate',names)
                self.assertNotIn('comsol_model_code',names)
                self.assertNotIn('model_create',names)
                self.assertFalse(asyncio.run(mcp.list_resources()))
            finally:runtime.executor.shutdown()

    def test_submission_budget_denies_without_new_job(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'COMSOL_MAX_SUBMISSIONS':'1'}):
            runtime=Runtime(output_root=directory)
            runtime.jobs['prior']={'job_id':'prior','status':'recovery_pending'}
            try:
                result=runtime.submit_study(None,'mock')
                self.assertEqual(result['error'],'SUBMISSION_BUDGET_EXHAUSTED')
                self.assertEqual(len(runtime.jobs),1)
            finally: runtime.executor.shutdown()
