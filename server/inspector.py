"""Phase 1: bounded, read-only traversal of a tracked live COMSOL model.

Only documented getters are called. No build, evaluate-result, run, setter,
save, create, Java reflection invocation, or model-supplied code execution.
This is a fact reader, not an audit, a persistent snapshot, or a solver monitor.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
from numbers import Integral, Real


SECTIONS = {"parameters", "definitions", "geometry", "selections", "materials",
            "physics", "multiphysics", "mesh", "study", "solver", "results"}
GETTERS = {name: "get" + name for name in (
    "Boolean", "BooleanArray", "BooleanMatrix", "Int", "IntArray", "IntMatrix",
    "Double", "DoubleArray", "DoubleMatrix", "String", "StringArray", "StringMatrix")}
GETTERS.update(File="getString", DoubleRowMatrix="getDoubleMatrix")


def annotate_tree_activity(nodes):
    """Derive ancestor flags from captured facts, never effective equation activity.

    No new Java calls. In particular a WorkPlane child retains its own active
    flag while exposing the disabled WorkPlane ancestor in blocked_by.
    Study overrides, feature precedence and dependency graphs are not resolved.
    """
    by_path = {node['path']: node for node in nodes}
    for node in nodes:
        parts = node['path'].split('/')
        lineage = [by_path[path] for end in range(2, len(parts) + 1)
                   if (path := '/'.join(parts[:end])) in by_path]
        blocked = [n['path'] for n in lineage if n['active'].get('status') == 'ok'
                   and n['active'].get('value') is False]
        unknown = [n['path'] for n in lineage if n['active'].get('status') != 'ok'
                   or not isinstance(n['active'].get('value'), bool)]
        field = {'status': 'ok', 'source': 'derived_from_captured_active_flags',
                 'blocked_by': blocked, 'unknown_at': unknown,
                 'study_activation': 'not_checked',
                 'meaning': 'Own and captured ancestor flags only; not effective physics, study or dependency activity'}
        if blocked: field['value'] = False
        elif unknown: field['status'] = 'unavailable'
        else: field['value'] = True
        node['tree_activation'] = field


class Reader:
    def __init__(self, max_nodes, max_depth, max_properties, max_items, max_string, include_properties):
        self.max_nodes, self.max_depth = max_nodes, max_depth
        self.max_properties, self.max_items, self.max_string = max_properties, max_items, max_string
        self.include_properties = include_properties
        self.nodes, self.collections, self.limitations, self.boundaries = [], {}, [], []
        self.geometry_dimensions = {}

    def issue(self, path, status, reason):
        item = {"path": path, "status": status, "reason": str(reason)[:400]}
        self.limitations.append(item)
        return {"status": status, "source": path, "reason": item["reason"]}

    def convert(self, value):
        """Convert typed getter values with explicit, recursively propagated limits."""
        if value is None or isinstance(value, bool): return value, False
        if isinstance(value, str): return value[:self.max_string], len(value) > self.max_string
        if isinstance(value, Integral): return int(value), False
        if isinstance(value, Real):
            number = float(value)
            if not math.isfinite(number): raise ValueError("Non-finite numeric value")
            return number, False
        # JPype strings may be exposed as java.lang.String if convertStrings=False.
        if type(value).__name__ == "java.lang.String": return self.convert(str(value))
        if hasattr(value, "__len__") and hasattr(value, "__iter__"):
            values, truncated = [], len(value) > self.max_items
            for i, entry in enumerate(value):
                if i >= self.max_items: break
                item, clipped = self.convert(entry)
                values.append(item)
                truncated |= clipped
            return values, truncated
        raise TypeError("Unsupported getter return type: " + type(value).__name__)

    def read(self, path, function):
        try:
            value, clipped = self.convert(function())
            if clipped:
                field = self.issue(path, "truncated", "Value exceeds max_items or max_string; returned value is a prefix")
                field["value"] = value
                return field
            return {"status": "ok", "value": value, "source": path}
        except AttributeError as error:
            return self.issue(path, "unsupported", error)
        except Exception as error:
            return self.issue(path, "unavailable", error)

    def properties(self, obj, path):
        if not self.include_properties:
            return {"status": "not_requested"}
        if not hasattr(obj, "properties"):
            return {"status": "not_applicable", "reason": "Node does not expose a property interface"}
        try:
            names = [str(x) for x in obj.properties()]
        except Exception as error:
            return self.issue(path, "unavailable", error)
        result = {"status": "ok", "total": len(names), "items": {}}
        for name in names[:self.max_properties]:
            source = path + "/" + name
            try:
                kind = str(obj.getValueType(name))
                if kind == "None":
                    field = {"status": "ok", "value": None, "source": source}
                elif kind == "Selection":
                    field = self.selection(obj.selection(name), source, True)
                elif kind in GETTERS:
                    field = self.read(source, lambda: getattr(obj, GETTERS[kind])(name))
                else:
                    field = self.issue(source, "unsupported", "Property type " + kind + " is not implemented; no value inferred")
                field["value_type"] = kind
            except Exception as error:
                field = self.issue(source, "unavailable", error)
            result["items"][name] = field
        if len(names) > self.max_properties:
            self.issue(path, "truncated", f"{len(names)} properties; read first {self.max_properties}")
            result["status"] = "truncated"
        elif any(v["status"] != "ok" for v in result["items"].values()):
            result["status"] = "partial"
        return result

    def selection(self, obj, path, named_node=False):
        try:
            if not named_node and hasattr(obj, "hasSelection") and not obj.hasSelection():
                return {"status": "not_applicable", "reason": "API hasSelection() is false"}
            sel = obj if named_node else obj.selection()
        except AttributeError:
            return {"status": "not_applicable", "reason": "Node has no selection accessor"}
        except Exception as error:
            return self.issue(path, "unavailable", error)
        result = {"status": "ok"}
        methods = [("dimension", "dim"), ("geometry", "geom")]
        object_selection = hasattr(sel, "objects")
        if not object_selection:
            methods += [("is_global", "isGlobal"), ("is_whole_geometry", "isGeom"), ("entities", "entities")]
        for key, method in methods:
            result[key] = self.read(path + "/" + key, lambda m=method: getattr(sel, m)())
        if object_selection:
            result["objects"] = self.read(path + "/objects", lambda: sel.objects())
            result["entities_by_object"] = {}
            if result["dimension"].get("value", -1) >= 0:
                for name in result["objects"].get("value", []):
                    result["entities_by_object"][name] = self.read(path + "/entities/" + name, lambda n=name: sel.entities(n))
            if any(v['status'] != 'ok' for v in result['entities_by_object'].values()):
                result['status'] = 'partial'
        result["named"] = (self.read(path + "/named", lambda: sel.named()) if hasattr(sel, "named")
                           else {"status": "not_applicable"})
        result["semantics"] = "API selection membership, not effective membership after feature overrides"
        if any(isinstance(v, dict) and "status" in v and v["status"] not in {"ok", "not_applicable"} for v in result.values()):
            result["status"] = "partial"
        return result

    def expressions(self, obj, path):
        try:
            names = [str(x) for x in obj.varnames()]
        except Exception as error:
            return self.issue(path, "unavailable", error)
        rows = []
        for name in names[:self.max_items]:
            row = {"name": name, "expression": self.read(path + "/" + name, lambda: obj.get(name)),
                   "description": self.read(path + "/" + name + "/description", lambda: obj.descr(name))}
            if hasattr(obj, "evaluateUnit"):
                row["unit"] = self.read(path + "/" + name + "/unit", lambda: obj.evaluateUnit(name))
            rows.append(row)
        status = "ok"
        if len(names) > self.max_items:
            self.issue(path, "truncated", f"{len(names)} expressions; first {self.max_items} returned")
            status = "truncated"
        elif any(v.get("status") != "ok" for r in rows for v in r.values() if isinstance(v, dict)):
            status = "partial"
        return {"status": status, "total": len(names), "items": rows}

    def collection(self, owner, accessor, path, kind, depth=0, component=None):
        try:
            container = getattr(owner, accessor)()
            tags = [str(x) for x in container.tags()]
        except Exception as error:
            self.collections[path] = self.issue(path, "unavailable", error)
            return
        record = {"status": "ok", "total": len(tags), "items": []}
        self.collections[path] = record
        if tags and (depth > self.max_depth or len(self.nodes) >= self.max_nodes):
            record.update(self.issue(path, "truncated", "max_depth or max_nodes reached"))
            return
        for tag in tags:
            if len(self.nodes) >= self.max_nodes:
                record.update(self.issue(path, "truncated", "max_nodes reached"))
                break
            child_path = path + "/" + tag
            try:
                obj = getattr(owner, accessor)(tag)
                self.node(obj, tag, child_path, kind, depth, component)
                record["items"].append(child_path)
            except Exception as error:
                record["status"] = "partial"
                self.issue(child_path, "unavailable", error)

    def node(self, obj, tag, path, kind, depth, component=None):
        node = {"path": path, "tag": tag, "kind": kind, "component": component,
                "label": self.read(path + "/label", lambda: obj.label()),
                "type": self.read(path + "/type", lambda: obj.getType()) if hasattr(obj, "getType") else {"status": "not_applicable"},
                "active": self.read(path + "/active", lambda: obj.isActive()),
                "properties": self.properties(obj, path + "/properties")}
        self.nodes.append(node)
        if kind not in {"component", "study", "solver", "results_group", "geometry"}:
            node["selection"] = self.selection(obj, path + "/selection", kind == "selection")
        details = {}
        if kind == "geometry":
            for key, method in [("space_dimension", "getSDim"), ("length_unit", "lengthUnit"), ("representation", "geomRep"),
                                ("num_domains", "getNDomains"), ("num_boundaries", "getNBoundaries")]:
                details[key] = self.read(path + "/" + key, lambda m=method: getattr(obj, m)())
            self.geometry_dimensions[(component, tag)] = details["space_dimension"].get("value")
        if kind == "mesh":
            details["is_empty"] = self.read(path + "/is_empty", lambda: obj.isEmpty())
            if details["is_empty"].get("value") is False:
                details["num_elements"] = self.read(path + "/num_elements", lambda: obj.getNumElem())
                details["element_types"] = self.read(path + "/element_types", lambda: obj.getTypes())
            else:
                details["num_elements"] = {"status": "not_applicable" if details["is_empty"].get("value") is True else "not_checked",
                                           "reason": "No known nonempty mesh; not built by Inspector"}
            details["freshness"] = {"status": "not_checked", "reason": "Nonempty mesh does not prove up-to-date geometry or valid quality"}
        if kind == "solver":
            details["is_empty"] = self.read(path + "/is_empty", lambda: obj.isEmpty())
            details["is_initialized"] = self.read(path + "/is_initialized", lambda: obj.isInitialized())
            details["solution_validity"] = {"status": "not_checked", "reason": "A nonempty solution does not establish convergence or current-parameter validity"}
        if kind == "variable": node["expressions"] = self.expressions(obj, path + "/expressions")
        if details: node["details"] = details
        if kind == "physics_feature":
            selection = node.get("selection", {})
            dim = selection.get("dimension", {}).get("value")
            geom = selection.get("geometry", {}).get("value")
            sdim = self.geometry_dimensions.get((component, geom))
            if isinstance(sdim, int) and sdim > 0 and dim == sdim - 1:
                self.boundaries.append(path)
            elif not isinstance(sdim, int) or dim is None:
                self.issue(path + "/boundary_classification", "unavailable", "Cannot classify by geometry/selection dimension")
        if kind == "component": return
        if hasattr(obj, "feature"):
            child_kind = "physics_feature" if kind in {"physics", "physics_feature"} else kind + "_feature" if not kind.endswith("_feature") else kind
            self.collection(obj, "feature", path + "/features", child_kind, depth + 1, component)
        if kind == "physics" and hasattr(obj, "prop"):
            self.collection(obj, "prop", path + "/property_groups", "physics_property", depth + 1, component)
        if kind == "material" and hasattr(obj, "propertyGroup"):
            self.collection(obj, "propertyGroup", path + "/property_groups", "material_property", depth + 1, component)
        if kind in {"material", "material_property"} and hasattr(obj, "func"):
            self.collection(obj, "func", path + "/functions", "function", depth + 1, component)
        if node["type"].get("value") == "WorkPlane":
            try:
                self.collection(obj.geom(), "feature", path + "/plane_geometry/features", "geometry_feature", depth + 1, component)
            except Exception as error:
                self.collections[path + "/plane_geometry"] = self.issue(path + "/plane_geometry", "unavailable", error)


def inspect_model(manager, model_name=None, *, sections=None, include_properties=True,
                  max_nodes=600, max_depth=10, max_properties=128, max_items=128, max_string=1200):
    """Read only a tracked model; never start, load, select, modify or save one."""
    if not manager or not manager.is_connected:
        return {"success": False, "error": "No connected COMSOL session; Inspector does not start one."}
    handle = model_name if model_name is not None else manager.current_model
    if not handle or handle not in manager.models:
        return {"success": False, "error": "No matching tracked model; specify model_name or load/select one explicitly."}
    limits = [(max_nodes, 1, 5000), (max_depth, 0, 30), (max_properties, 0, 1000),
              (max_items, 1, 10000), (max_string, 32, 16000)]
    if any(not isinstance(x, int) or isinstance(x, bool) or not low <= x <= high for x, low, high in limits):
        return {"success": False, "error": "Inspector limits are outside allowed ranges."}
    wanted = SECTIONS if sections is None else set(sections)
    if not wanted <= SECTIONS:
        return {"success": False, "error": "Unknown sections: " + ", ".join(sorted(wanted - SECTIONS))}
    reader = Reader(max_nodes, max_depth, max_properties, max_items, max_string, include_properties)
    model = manager.get_model(handle)
    if model is None: return {"success": False, "error": "Model is no longer tracked."}
    java = model.java
    result = {"success": True, "schema_version": "inspector/1", "read_only": True,
              "source": "live_comsol_model_api", "captured_at": datetime.now(timezone.utc).isoformat(),
              "scope": sorted(wanted), "model": {"session_handle": handle,
              "name": reader.read("/model/name", model.name),
              "tag": reader.read("/model/tag", lambda: java.tag()),
              "saved_version": reader.read("/model/saved_version", model.version),
              "runtime_version": reader.read("/model/runtime_version", lambda: manager.client.version)},
              "current_model_scope": "MCP tracked model, not the active Desktop document",
              "limits": {"max_nodes": max_nodes, "max_depth": max_depth, "max_properties": max_properties,
                         "max_items": max_items, "max_string": max_string, "include_properties": include_properties}}
    if "parameters" in wanted:
        try: result["parameters"] = reader.expressions(java.param(), "/parameters")
        except Exception as error: result["parameters"] = reader.issue("/parameters", "unavailable", error)
    else: result["parameters"] = {"status": "not_requested"}
    for section, accessor, kind in [("definitions", "variable", "variable"), ("definitions", "func", "function"),
                                     ("selections", "selection", "selection"), ("materials", "material", "material")]:
        if section in wanted: reader.collection(java, accessor, "/global/" + accessor, kind)
    reader.collection(java, "component", "/components", "component")
    component_paths = list(reader.collections["/components"].get("items", []))
    groups = [("geometry", "geom", "geometry"), ("definitions", "variable", "variable"),
              ("definitions", "func", "function"), ("definitions", "cpl", "coupling"),
              ("definitions", "probe", "probe"), ("selections", "selection", "selection"),
              ("materials", "material", "material"), ("physics", "physics", "physics"),
              ("multiphysics", "multiphysics", "multiphysics"), ("mesh", "mesh", "mesh")]
    for path in component_paths:
        tag = path.rsplit("/", 1)[-1]
        try: component = java.component(tag)
        except Exception as error:
            reader.issue(path, "unavailable", error)
            continue
        for section, accessor, kind in groups:
            if section in wanted or (section == "geometry" and "physics" in wanted):
                reader.collection(component, accessor, path + "/" + section + ("/" + accessor if section == "definitions" else ""), kind, 1, tag)
    for section, accessor, kind in [("study", "study", "study"), ("solver", "sol", "solver")]:
        if section in wanted: reader.collection(java, accessor, "/" + section, kind)
    if "results" in wanted:
        try:
            results = java.result()
            reader.collection(results, "dataset", "/results/datasets", "dataset")
        except Exception as error:
            reader.collections["/results/datasets"] = reader.issue("/results/datasets", "unavailable", error)
    annotate_tree_activity(reader.nodes)
    result.update(nodes=reader.nodes, collections=reader.collections, limitations=reader.limitations,
                  boundary_conditions={"status": "not_requested" if "physics" not in wanted else "partial" if any(i['path'].startswith('/components') for i in reader.limitations) else "ok",
                                       "items": reader.boundaries,
                                       "meaning": "Physics feature nodes on codimension-one selections; defaults/disabled nodes retained; not an effective-BC audit"},
                  completeness="partial" if reader.limitations else "complete_for_requested_scope")
    return result


def register_inspector_tools(mcp, runtime):
    """Register additive tools; every read remains on Runtime's single JVM thread."""
    from mcp.types import ToolAnnotations
    annotations = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)

    @mcp.tool(annotations=annotations)
    async def inspect_current_model(model_name: str | None = None, sections: list[str] | None = None,
                                    include_properties: bool = True, max_nodes: int = 600, max_depth: int = 10,
                                    max_properties: int = 128, max_items: int = 128, max_string: int = 1200) -> dict:
        """Phase 1 READ: inspect an explicitly named or MCP-current tracked live model. Returns identity, parameters, all components, geometry, selections/entities, materials/property groups, physics/nested features, boundary-feature index, multiphysics, mesh, study, solver and datasets. Unknown/unavailable/truncated fields are explicit. Does not start/load/build/mesh/solve/evaluate results/save/change the model or execute model text. Desktop active document is NOT inferred. No Audit, Diff or Diagnosis. Use sections to limit output; preserve limitations in your answer."""
        return await runtime.call(inspect_model, runtime.manager, model_name, sections=sections,
                                  include_properties=include_properties, max_nodes=max_nodes, max_depth=max_depth,
                                  max_properties=max_properties, max_items=max_items, max_string=max_string)

    for name, sections, props in [
        ("get_model_tree", None, False), ("get_parameters", ["parameters"], True),
        ("get_selections", ["selections"], True), ("get_materials", ["materials"], True),
        ("get_physics", ["physics", "multiphysics"], True), ("get_mesh_info", ["mesh"], True),
        ("get_study", ["study"], True), ("get_solver", ["solver", "results"], True)]:
        def make_reader(selected, properties):
            async def tool(model_name: str | None = None) -> dict:
                return await runtime.call(inspect_model, runtime.manager, model_name,
                                          sections=selected, include_properties=properties)
            return tool
        tool = make_reader(sections, props)
        tool.__name__ = name
        mcp.tool(name=name, description="Phase 1 read-only Inspector projection: " + name +
                 ". Same explicit status/identity schema as inspect_current_model. For custom limits use that tool with sections. Does not change or solve the model.", annotations=annotations)(tool)
