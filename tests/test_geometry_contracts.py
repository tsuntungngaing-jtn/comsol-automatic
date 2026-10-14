"""Mock/software tests: these establish tool behavior, never physical correctness."""
import asyncio
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from server.contracts import aggregate, compare, new_report, validate_document, repair_event
from server.geometry_validation import accept_geometry, validate_selection, bind_selection
from server.geometry_workflows import import_cad, perturb

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/installed-mcp'))
v=importlib.import_module('src.tools.geometry')

class GeometryFaultTests(unittest.TestCase):
    def test_property_failure_is_not_success_and_readback_is_separate(self):
        node=Mock()
        def prop(key,*value):
            if key=='bad': raise RuntimeError('Unknown property bad')
            return 'accepted'
        node.property.side_effect=prop
        result=v._configure_feature(node,{'size':['w','2[mm]','3[mm]'],'bad':42})
        self.assertFalse(result['success'])
        self.assertEqual(result['creation_status'],'PASS')
        self.assertEqual(result['configuration_status'],'FAIL')
        self.assertEqual(result['build_status'],'NOT_RUN')
        self.assertEqual(result['properties']['bad']['requested'],42)
        self.assertIn('Unknown property',result['properties']['bad']['error'])
        self.assertEqual(result['properties']['size']['readback'],'accepted')

    def test_readback_failure_does_not_claim_geometry_validity(self):
        node=Mock()
        node.property.side_effect=[None,RuntimeError('read unavailable')]
        result=v._configure_feature(node,{'r':'radius'})
        self.assertTrue(result['success'])
        self.assertFalse(result['safe_for_solve'])
        self.assertIn('readback_error',result['properties']['r'])

    def test_numeric_meter_contract_and_expressions(self):
        self.assertEqual(v._vector([0.001,'w','2[mm]'],3),['0.001[m]','w','2[mm]'])
        for value in [float('nan'),float('inf'),True,None,'']:
            with self.subTest(value=value),self.assertRaises(ValueError): v._length(value)
        with self.assertRaises(ValueError): v._vector([1,2],3)

    def test_primitive_auto_tag_uses_java_tags_and_preserves_unit(self):
        registry={}
        class Registry:
            def tool(self):
                def register(f): registry[f.__name__]=f; return f
                return register
        v.register_geometry_tools(Registry())
        geom=Mock();geom.feature.return_value.tags.return_value=['fin']
        geom.lengthUnit.return_value='mm'
        with patch.object(v.session_manager,'get_model',return_value=Mock()), patch.object(v,'_get_geometry_node',return_value=(geom,None)):
            result=registry['geometry_add_cylinder'](radius=0.001,height='h')
        self.assertTrue(result['success'])
        geom.feature.return_value.create.return_value.set.assert_any_call('r','0.001[m]')
        geom.feature.return_value.create.return_value.set.assert_any_call('h','h')

    def test_dimension_failure_creates_no_primitive(self):
        registry={}
        class Registry:
            def tool(self):
                def register(f):registry[f.__name__]=f;return f
                return register
        v.register_geometry_tools(Registry())
        geom=Mock()
        with patch.object(v.session_manager,'get_model',return_value=Mock()),patch.object(v,'_get_geometry_node',return_value=(geom,None)):
            result=registry['geometry_add_block'](size=[1,2])
        self.assertFalse(result['success']);geom.feature.assert_not_called()


class ContractTests(unittest.TestCase):
    def test_unknown_and_missing_required_layers_do_not_pass(self):
        self.assertEqual(aggregate([]),'NOT_RUN')
        self.assertEqual(aggregate([{'status':'PASS'},{'status':'NOT_RUN'}]),'NOT_RUN')
        self.assertEqual(aggregate([{'status':'PASS'},{'status':'UNKNOWN'}]),'FAIL')
        self.assertEqual(compare(None,{'reference':1},'missing')['status'],'NOT_RUN')
        self.assertEqual(compare(float('nan'),{'reference':1},'bad')['status'],'FAIL')
        self.assertEqual(compare(1,{'reference':1,'atol':-1},'bad')['status'],'FAIL')
        self.assertEqual(compare([1,2],{'reference':[1]},'bad')['status'],'FAIL')

    def test_report_cannot_claim_pass_with_unrun_science(self):
        report=new_report('run','a'*64,{})
        self.assertTrue(validate_document(report,'validation-report')['success'])
        report['status']='PASS'
        self.assertFalse(validate_document(report,'validation-report')['success'])

    def test_version_gate_rejects_other_or_unknown_versions(self):
        from server.compatibility import geometry_version_policy
        for version in ('6.2','6.3','6.40','unknown'):
            self.assertEqual(geometry_version_policy(version)['status'],'BLOCKED')
        self.assertEqual(geometry_version_policy('COMSOL Multiphysics 6.4 (Build 293)')['status'],'PASS')

    def test_exact_measure_requirement_is_not_falsely_passed(self):
        model=Mock();geom=model.java.component.return_value.geom.return_value
        geom.lengthUnit.return_value='mm'
        with patch('server.geometry_validation.diagnostics',return_value=[{'status':'PASS'}]):
            result=accept_geometry(model,[{'metric':'volume','reference':1,'require_exact':True}])
        self.assertEqual(result['status'],'NOT_RUN')
        geom.measureFinal.assert_not_called()

    def test_repair_costs(self):
        with self.assertRaises(ValueError): repair_event('solve','bad',{},1,2,1,{})
        self.assertEqual(repair_event('build','bad',{},2,0,1,{},operation='necessary')['operation'],'necessary')

    def test_unknown_measurement_is_not_pass(self):
        model=Mock();geom=model.java.component.return_value.geom.return_value
        geom.feature.return_value.tags.return_value=['blk']
        geom.feature.return_value.status.return_value='built';geom.feature.return_value.message.return_value=''
        geom.lengthUnit.return_value='mm'
        result=accept_geometry(model,[{'metric':'connectivity','reference':1}])
        self.assertEqual(result['status'],'NOT_RUN')

    def test_empty_selection_prevents_binding(self):
        model=Mock();comp=model.java.component.return_value
        comp.selection.return_value.dim.return_value=2
        comp.selection.return_value.entities.return_value=[]
        contract={'id':'inlet','tag':'inlet','dimension':2,'count':{'reference':1},'allow_empty':False,'purpose':'flow inlet'}
        with patch('server.geometry_validation.accept_geometry',return_value={'status':'PASS'}), patch('server.geometry_validation.diagnostics',return_value=[{'status':'PASS'}]):
            result=bind_selection(model,contract,'spf','inl')
        self.assertEqual(result['status'],'FAIL')
        comp.physics.assert_not_called()

    def test_cad_missing_license_never_creates_nodes(self):
        model=Mock()
        with tempfile.TemporaryDirectory() as directory:
            result=import_cad(model,{},directory,{'version':'6.4','products':{}})
        self.assertEqual(result['status'],'BLOCKED');model.java.component.assert_not_called()

    def test_perturb_restores_after_failed_variant(self):
        model=Mock();model.java.param.return_value.get.return_value='1[mm]'
        model.save.side_effect=lambda p:Path(p).write_bytes(b'mock recovery snapshot')
        with tempfile.TemporaryDirectory() as directory,patch('server.geometry_workflows.accept_geometry',side_effect=[{'status':'PASS'},RuntimeError('build failed'),{'status':'PASS'}]):
            result=perturb(model,{'parameters':['w'],'baseline_requirements':[], 'variants':[{'id':'bad','parameters':{'w':'-1[mm]'},'requirements':[]}]},directory)
        self.assertEqual(result['status'],'FAIL')
        self.assertEqual(result['restoration']['status'],'PASS')
        self.assertEqual(model.java.param.return_value.set.call_args.args,('w','1[mm]'))


class SchemaAndBenchmarkTests(unittest.TestCase):
    def test_all_specs_validate_and_missing_cad_blocks_only_cad(self):
        import json
        for path in (ROOT/'benchmarks/tasks').glob('*.json'):
            with self.subTest(path=path.name):
                result=validate_document(json.loads(path.read_text()))
                self.assertEqual(result['schema_status'],'PASS',result)
                if path.stem=='cad_import': self.assertEqual(result['dependencies'][0]['task'],'cad_import')

    def test_bbox_uses_final_entity_measurement_not_padded_sequence(self):
        from server.geometry_validation import measure
        geom=Mock();geom.getSDim.return_value=1;geom.getBoundingBox.return_value=[-0.1,1.1]
        geom.measureFinal.return_value.getBoundingBox.return_value=[0,1]
        self.assertEqual(measure(geom,'bbox'),[0,1])
        geom.getBoundingBox.assert_not_called()

    def test_score_does_not_invent_absent_metrics(self):
        from benchmarks.score import score
        result=score(new_report('run','b'*64,{}))
        self.assertIsNone(result['geometry']['pass_fraction'])
        self.assertIsNone(result['false_success_rate'])

    def test_failed_check_cannot_be_hidden_under_passing_layer(self):
        report=new_report('run','a'*64,{})
        report['layers']['geometry']={'status':'PASS','checks':[{'status':'FAIL'}]}
        self.assertFalse(validate_document(report,'validation-report')['success'])

if __name__=='__main__':unittest.main()
