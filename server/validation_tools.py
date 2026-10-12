"""Typed MCP facade; Java work remains serialized by the existing runtime."""
from .contracts import validate_document
from .compatibility import geometry_version_policy
from .geometry_validation import accept_geometry, validate_selection, bind_selection
from .geometry_workflows import perturb, import_cad


def register_validation_tools(mcp, runtime):
    def execute(model_name, function, *args, **kwargs):
        model = runtime.manager.get_model(model_name)
        if model is None:
            return {'success':False,'status':'BLOCKED','error':'Tracked model not found'}
        try:
            from com.comsol.model.util import ModelUtil
            policy = geometry_version_policy(str(ModelUtil.getComsolVersion()))
            if policy['status'] != 'PASS':
                return {'success':False, **policy}
            result = function(model,*args,**kwargs)
            result['version_policy'] = policy
            return result
        except Exception as error:
            return {'success':False,'status':'FAIL','error':str(error)}

    @mcp.tool()
    async def simulation_spec_validate(document: dict, kind: str = 'simulation-spec') -> dict:
        """Validate specification/report structure and task dependencies; no COMSOL calls."""
        if kind not in ('simulation-spec','validation-report'):
            return {'success':False,'status':'FAIL','error':'Unknown document kind'}
        return validate_document(document,kind)

    @mcp.tool()
    async def geometry_accept(requirements: list[dict], model_name: str | None = None,
                              component: str = 'comp1', geometry: str = 'geom1', rebuild: bool = False) -> dict:
        """Measure final geometry against explicit references in geometry units; unsupported checks are NOT_RUN. Rebuild mutates geometry and invalidates solutions."""
        return await runtime.call(execute,model_name,accept_geometry,requirements,component,geometry,rebuild)

    @mcp.tool()
    async def selection_validate(contract: dict, model_name: str | None = None,
                                 component: str = 'comp1', geometry: str = 'geom1') -> dict:
        """Resolve a named/generated/spatial selection now and check dimension, count, measurements and physical bindings."""
        return await runtime.call(execute,model_name,validate_selection,contract,component,geometry)

    @mcp.tool()
    async def selection_bind_checked(contract: dict, physics: str, feature: str,
                                     model_name: str | None = None, component: str = 'comp1', geometry: str = 'geom1') -> dict:
        """Rebuild, validate a selection contract, bind by name only if valid, then verify effective entities."""
        return await runtime.call(execute,model_name,bind_selection,contract,physics,feature,component,geometry)

    @mcp.tool()
    async def geometry_perturb(spec: dict, model_name: str | None = None) -> dict:
        """Save a unique recovery snapshot, vary declared parameters, rebuild/measure/rebind-check, finally restore baseline parameters and geometry. Does not restore old solutions."""
        return await runtime.call(execute,model_name,perturb,spec,runtime.output_root)

    @mcp.tool()
    async def geometry_import_cad(spec: dict, model_name: str | None = None) -> dict:
        """License/version-gated BRep import into a new geometry, explicit units/finalization/repair/transforms, measurements and provenance. Contact checks may remain NOT_RUN."""
        def run():
            from com.comsol.model.util import ModelUtil
            version = str(ModelUtil.getComsolVersion())
            environment={'version': version,'build':version,
                         'products':{'CADIMPORT':bool(ModelUtil.hasProduct('CADIMPORT'))}}
            return execute(model_name,import_cad,spec,runtime.output_root,environment)
        try:
            return await runtime.call(run)
        except Exception as error:
            return {'success':False,'status':'BLOCKED','error':str(error)}
