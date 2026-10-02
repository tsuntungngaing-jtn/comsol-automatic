"""Inspector contracts without a JVM; real-MPH acceptance uses MCP separately."""
import asyncio
import importlib
import importlib.util
import json
from pathlib import Path
import ast
import tempfile
import threading
from types import SimpleNamespace
import unittest


class Collection:
    def __init__(self, nodes=()):
        self.nodes = {n.tag(): n for n in nodes}
    def tags(self):
        return list(self.nodes)
    def __call__(self, tag=None):
        return self if tag is None else self.nodes[tag]


class Selection:
    def __init__(self, entities=(27,), dim=2, named="inlet"):
        self.ids, self.dimension_value, self.ref = entities, dim, named
    def dim(self): return self.dimension_value
    def geom(self): return "geom1"
    def named(self): return self.ref
    def entities(self): return list(self.ids)
    def isGlobal(self): return False
    def isGeom(self): return False
    def inputEntities(self): return list(self.ids)


class Node:
    def __init__(self, tag, kind="Feature", props=None, features=(), active=True, selection=None, **groups):
        self._tag, self.kind, self.props, self.enabled = tag, kind, props or {}, active
        self.feature = Collection(features)
        self._selection = selection
        for key, value in groups.items(): setattr(self, key, Collection(value))
    def tag(self): return self._tag
    def label(self): return "label:" + self._tag
    def getType(self): return self.kind
    def isActive(self): return self.enabled
    def properties(self): return list(self.props)
    def getValueType(self, name): return self.props[name][0]
    def getString(self, name): return self.props[name][1]
    def getStringArray(self, name): return self.props[name][1]
    def getDouble(self, name): return self.props[name][1]
    def selection(self):
        if self._selection is None: raise RuntimeError("no entity selection")
        return self._selection
    def geom(self): return "geom1"
    def getSDim(self): return 3
    def isEmpty(self): return True
    def isInitialized(self): return False
    def getNumElem(self):
        raise RuntimeError("empty mesh must not be measured")
    def getNDomains(self): return 11
    def getNBoundaries(self): return 76
    def hasSelection(self): return self._selection is not None
    def lengthUnit(self): return "mm"
    def geomRep(self): return "comsol"


class Params:
    def varnames(self): return ["u_in", "broken"]
    def get(self, key):
        if key == "broken": raise RuntimeError("unreadable expression")
        return "0.5[m/s]"
    def descr(self, key): return "input speed"
    def evaluateUnit(self, key): return "m/s"


def model_fixture():
    inlet = Node("inl1", "Inlet", {"U0in": ("String", "u_in")}, selection=Selection())
    spf = Node("spf", "LaminarFlow", {"TurbulenceModel": ("String", "Rkeps")}, [inlet])
    geom = Node("geom1", features=[Node("wp6", active=False)])
    comp1 = Node("comp1", geom=[geom], selection=[Node("inlet", "Explicit", selection=Selection())],
                 material=[Node("water", propertyGroup=[Node("def", props={"density": ("String", "rho(T)")})])],
                 physics=[spf], multiphysics=[Node("nitf1")], mesh=[Node("mesh1")],
                 variable=[], func=[], cpl=[], probe=[])
    comp2 = Node("comp2", geom=[], selection=[], material=[], physics=[], multiphysics=[], mesh=[], variable=[], func=[], cpl=[], probe=[])
    java = Node("model1", component=[comp1, comp2], study=[Node("std1", features=[Node("stat", "Stationary")])],
                sol=[Node("sol1")], variable=[], func=[], selection=[], material=[])
    java.param = lambda: Params()
    java.result = lambda: Node("results", dataset=[Node("dset1", "Solution", {"solution": ("String", "sol1")})])
    model = SimpleNamespace(java=java, name=lambda: "sample", version=lambda: "6.1")
    manager = SimpleNamespace(is_connected=True, current_model="sample", models={"sample": model}, client=SimpleNamespace(version="6.4"))
    manager.get_model = lambda name=None: manager.models.get(name or manager.current_model)
    return manager


class InspectorTests(unittest.TestCase):
    def api(self):
        spec = importlib.util.find_spec("server.inspector")
        self.assertIsNotNone(spec, "Phase 1 inspector module is not implemented")
        return importlib.import_module("server.inspector")

    def test_live_facts_cover_all_components_and_preserve_physics_type(self):
        result = self.api().inspect_model(model_fixture())
        self.assertTrue(result["success"])
        self.assertEqual(result["model"]["session_handle"], "sample")
        self.assertEqual(result["model"]["runtime_version"]["value"], "6.4")
        nodes = result["nodes"]
        self.assertTrue(any(n["path"] == "/components/comp2" for n in nodes))
        inlet = next(n for n in nodes if n["tag"] == "inl1")
        self.assertEqual(inlet["selection"]["entities"]["value"], [27])
        self.assertEqual(inlet["properties"]["items"]["U0in"]["value"], "u_in")
        physics = next(n for n in nodes if n["tag"] == "spf")
        self.assertEqual(physics["type"]["value"], "LaminarFlow")
        self.assertEqual(physics["properties"]["items"]["TurbulenceModel"]["value"], "Rkeps")
        self.assertIn(inlet["path"], result["boundary_conditions"]["items"])
        self.assertFalse(next(n for n in nodes if n["tag"] == "wp6")["active"]["value"])
        self.assertTrue(any('/property_groups/def' in n["path"] for n in nodes))
        self.assertTrue(any(n["tag"] == "dset1" for n in nodes))
        self.assertEqual(next(n for n in nodes if n['tag']=='geom1')['details']['num_domains']['value'], 11)
        json.dumps(result, allow_nan=False)

    def test_unknowns_are_not_empty_or_zero_and_empty_solution_is_explicit(self):
        result = self.api().inspect_model(model_fixture())
        broken = next(p for p in result["parameters"]["items"] if p["name"] == "broken")
        self.assertEqual(broken["expression"]["status"], "unavailable")
        self.assertNotIn("value", broken["expression"])
        mesh = next(n for n in result["nodes"] if n["tag"] == "mesh1")
        self.assertTrue(mesh["details"]["is_empty"]["value"])
        self.assertEqual(mesh["details"]["num_elements"]["status"], "not_applicable")
        sol = next(n for n in result["nodes"] if n["tag"] == "sol1")
        self.assertTrue(sol["details"]["is_empty"]["value"])

    def test_limits_are_explicit_and_do_not_invent_complete_tree(self):
        result = self.api().inspect_model(model_fixture(), max_nodes=3, max_depth=1, max_properties=1)
        self.assertLessEqual(len(result["nodes"]), 3)
        self.assertEqual(result["completeness"], "partial")
        self.assertTrue(any(x["status"] == "truncated" for x in result["limitations"]))

    def test_model_selection_never_falls_back_to_first_or_starts_session(self):
        api = self.api()
        manager = model_fixture()
        manager.current_model = None
        self.assertFalse(api.inspect_model(manager)["success"])
        self.assertTrue(api.inspect_model(manager, model_name="sample")["success"])
        self.assertFalse(api.inspect_model(manager, model_name="missing")["success"])
        manager.is_connected = False
        self.assertFalse(api.inspect_model(manager, model_name="sample")["success"])

    def test_unreadable_collection_is_not_reported_as_empty(self):
        manager = model_fixture()
        def fail(): raise RuntimeError("server failed")
        manager.models['sample'].java.component = fail
        result = self.api().inspect_model(manager)
        collection = result['collections']['/components']
        self.assertEqual(collection['status'], 'unavailable')
        self.assertNotIn('items', collection)
        self.assertEqual(result['boundary_conditions']['status'], 'partial')

    def test_unknown_property_type_and_nonfinite_are_recorded(self):
        manager=model_fixture()
        spf=manager.models['sample'].java.component('comp1').physics('spf')
        spf.props.update({'opaque': ('Alien', object()), 'bad': ('Double', float('nan'))})
        result=self.api().inspect_model(manager)
        props=next(n for n in result['nodes'] if n['tag']=='spf')['properties']['items']
        self.assertEqual(props['opaque']['status'],'unsupported')
        self.assertEqual(props['bad']['status'],'unavailable')
        json.dumps(result,allow_nan=False)

    def test_boundary_index_is_partial_when_physics_collection_fails(self):
        manager = model_fixture()
        def fail(): raise RuntimeError('cannot access physics')
        manager.models['sample'].java.component('comp1').physics = fail
        result = self.api().inspect_model(manager)
        self.assertEqual(result['boundary_conditions']['status'], 'partial')

    def test_missing_active_getter_is_recorded_in_limitations(self):
        manager = model_fixture()
        class NoActive(Node):
            def __getattribute__(self, name):
                if name == 'isActive': raise AttributeError('isActive not supported')
                return super().__getattribute__(name)
        manager.models['sample'].java.component('comp1').mesh = Collection([NoActive('mesh2')])
        result = self.api().inspect_model(manager, sections=['mesh'])
        self.assertTrue(any(x['path'].endswith('/mesh2/active') for x in result['limitations']))
        self.assertEqual(result['completeness'], 'partial')

    def test_nonempty_mesh_statistics_are_read_without_building(self):
        manager = model_fixture()
        mesh = manager.models['sample'].java.component('comp1').mesh('mesh1')
        mesh.isEmpty = lambda: False
        mesh.getNumElem = lambda: 125
        mesh.getTypes = lambda: ['tet', 'tri']
        result = self.api().inspect_model(manager, sections=['mesh'])
        details = next(n for n in result['nodes'] if n['tag'] == 'mesh1')['details']
        self.assertEqual(details['num_elements']['value'], 125)
        self.assertEqual(details['element_types']['value'], ['tet', 'tri'])
        self.assertEqual(details['freshness']['status'], 'not_checked')

    def test_selection_property_uses_geometry_objects_not_physics_ids(self):
        manager = model_fixture()
        class ObjectSelection:
            def dim(self): return -1
            def geom(self): return 'geom1'
            def objects(self): return ['blk1', 'ext1']
            def named(self): return ''
        feature = Node('uni1', props={'input': ('Selection', None)})
        feature.selection = lambda name: ObjectSelection()
        manager.models['sample'].java.component('comp1').geom('geom1').feature = Collection([feature])
        result = self.api().inspect_model(manager, sections=['geometry'])
        value = next(n for n in result['nodes'] if n['tag'] == 'uni1')['properties']['items']['input']
        self.assertEqual(value['status'], 'ok')
        self.assertEqual(value['objects']['value'], ['blk1', 'ext1'])
        self.assertNotIn('entities', value)

    def test_only_inspector_getters_no_mutating_api_calls(self):
        tree = ast.parse(Path(self.api().__file__).read_text(encoding='utf-8'))
        denied = {'set', 'create', 'remove', 'clear', 'run', 'runAll', 'build',
                  'save', 'load', 'solve', 'evaluate', 'set_current_model', 'execute_code'}
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertFalse(calls & denied)

    def test_tree_activation_retains_disabled_parent_evidence(self):
        manager = model_fixture()
        parent = manager.models['sample'].java.component('comp1').geom('geom1').feature('wp6')
        parent.feature = Collection([Node('child', active=True)])
        result = self.api().inspect_model(manager, sections=['geometry'])
        child = next(n for n in result['nodes'] if n['tag'] == 'child')
        self.assertTrue(child['active']['value'])
        self.assertFalse(child['tree_activation']['value'])
        self.assertTrue(child['tree_activation']['blocked_by'][0].endswith('/wp6'))
        self.assertEqual(child['tree_activation']['study_activation'], 'not_checked')

    def test_tree_activation_unknown_is_not_enabled(self):
        nodes = [{'path':'/parent', 'active':{'status':'unsupported'}},
                 {'path':'/parent/features/child', 'active':{'status':'ok','value':True}}]
        self.api().annotate_tree_activity(nodes)
        self.assertEqual(nodes[1]['tree_activation']['status'], 'unavailable')
        self.assertNotIn('value', nodes[1]['tree_activation'])

    def test_tree_activation_uses_path_segments_not_tag_prefixes(self):
        nodes = [{'path':'/features/a', 'active':{'status':'ok','value':False}},
                 {'path':'/features/ab', 'active':{'status':'ok','value':True}}]
        self.api().annotate_tree_activity(nodes)
        self.assertTrue(nodes[1]['tree_activation']['value'])

    def test_registered_tools_use_serialized_runtime_and_read_annotations(self):
        from mcp.server.fastmcp import FastMCP
        from server.runtime import Runtime
        with tempfile.TemporaryDirectory() as output:
            runtime = Runtime(output_root=Path(output))
            runtime.manager = model_fixture()
            threads = []
            original = runtime.manager.get_model
            def tracked(name=None):
                threads.append(threading.get_ident())
                return original(name)
            runtime.manager.get_model = tracked
            mcp = FastMCP('Inspector test')
            self.api().register_inspector_tools(mcp, runtime)
            async def check():
                listing = await mcp.list_tools()
                self.assertEqual(len(listing), 9)
                for tool in listing:
                    self.assertTrue(tool.annotations.readOnlyHint)
                    self.assertFalse(tool.annotations.destructiveHint)
                await asyncio.gather(*(mcp.call_tool(name, {}) for name in ['get_parameters', 'get_physics', 'inspect_current_model']))
            try:
                asyncio.run(check())
                self.assertEqual(len(threads), 3)
                self.assertEqual(len(set(threads)), 1)
                self.assertNotEqual(threads[0], threading.get_ident())
            finally:
                runtime.executor.shutdown()


if __name__ == '__main__': unittest.main()
