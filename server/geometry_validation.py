"""COMSOL geometry measurements and selection contracts, run on the JVM thread."""
from __future__ import annotations
from .contracts import aggregate, compare, digest


def measure(geom, metric, dimension=None, entities=None):
    if metric == 'dimension': return int(geom.getSDim())
    if metric == 'unit': return str(geom.lengthUnit())
    if metric == 'counts': return [int(x) for x in geom.getNEntities()]
    if metric == 'sequence_bbox': return [float(x) for x in geom.getBoundingBox()]
    if metric.startswith('count_'): return int(geom.getNEntities()[int(metric[6:])])
    measurement = geom.measureFinal()
    measurement.selection().geom(int(dimension if dimension is not None else geom.getSDim()))
    if entities is None: measurement.selection().all()
    else: measurement.selection().set(entities)
    methods = {'volume':'getVolume', 'area':'getArea', 'length':'getLength', 'bbox':'getBoundingBox', 'finite_voids':'getNFiniteVoids'}
    if metric not in methods: raise NotImplementedError(f'No verified evaluator for {metric}')
    value = getattr(measurement, methods[metric])()
    return [float(x) for x in value] if metric == 'bbox' else float(value)


def diagnostics(geom):
    records = []
    for tag in geom.feature().tags():
        node = geom.feature(str(tag))
        try:
            status = str(node.status())
            message = str(node.message())
            records.append({'tag':str(tag), 'state':status, 'message':message,
                            'status':'PASS' if status == 'built' and not message else 'FAIL'})
        except Exception as error:
            records.append({'tag':str(tag), 'status':'NOT_RUN', 'error':str(error)})
    return records


def accept_geometry(model, requirements, component='comp1', geometry='geom1', rebuild=False):
    checks = []
    try:
        geom = model.java.component(component).geom(geometry)
        if rebuild:
            geom.run()
        diag = diagnostics(geom)
        checks.append({'metric':'build_diagnostics', 'status':aggregate(diag), 'evidence':diag})
        for requirement in requirements:
            metric = requirement['metric']
            try:
                if requirement.get('require_exact') and metric in ('volume','area','length'):
                    raise NotImplementedError('6.4 geometric measures use polygonal approximation; exact measurement requires a separately validated evaluator')
                value = measure(geom, metric, requirement.get('dimension'), requirement.get('entities'))
                check = compare(value, requirement, f'{component}/{geometry}:GeomInfo/measureFinal')
            except Exception as error:
                check = compare(None, requirement, f'{component}/{geometry}:unavailable', error)
            check['geometry_unit'] = str(geom.lengthUnit())
            power = {'volume':3, 'area':2, 'length':1, 'bbox':1, 'sequence_bbox':1}.get(metric)
            check['measurement_unit'] = (str(geom.lengthUnit()) + (f'^{power}' if power != 1 else '')) if power else 'dimensionless or label'
            if metric in ('volume','area','length'):
                check['measurement_basis'] = 'Approximate polygonal/rendering mesh; not an analytic measure'
                check['manual'] = 'com.comsol.help.comsol/comsol_api_geom.48.047.html'
            checks.append(check)
        return {'success':aggregate(checks)=='PASS', 'status':aggregate(checks), 'checks':checks,
                'snapshot_hash':digest(checks), 'rebuild':rebuild}
    except Exception as error:
        return {'success':False,'status':'FAIL','error':str(error),'checks':checks}


def validate_selection(model, contract, component='comp1', geometry='geom1'):
    checks = []
    try:
        comp = model.java.component(component)
        geom = comp.geom(geometry)
        checks.append({'metric':'build_diagnostics','status':aggregate(diagnostics(geom)), 'evidence':'Current geometry feature status'})
        selection = comp.selection(contract['tag'])
        dimension = int(selection.dim())
        entities = [int(x) for x in selection.entities(contract['dimension'])]
        checks.append(compare(dimension, {'metric':'dimension','reference':contract['dimension']}, 'Selection.dimension'))
        checks.append(compare(len(entities), {'metric':'count', **contract['count']}, 'Selection.entities'))
        if not contract.get('allow_empty', False):
            checks.append(compare(int(bool(entities)), {'metric':'nonempty','reference':1}, 'Selection.entities'))
        for requirement in contract.get('measurements', []):
            try:
                if requirement.get('require_exact') and requirement['metric'] in ('volume','area','length'):
                    raise NotImplementedError('Exact measure unavailable through polygonal geometry measurement')
                value = measure(geom, requirement['metric'], contract['dimension'], entities)
                checks.append(compare(value, requirement, 'measureFinal on resolved selection'))
            except Exception as error:
                checks.append(compare(None, requirement, 'selection measurement', error))
        for binding in contract.get('bindings', []):
            node = comp.physics(binding['physics'])
            if binding.get('feature'): node = node.feature(binding['feature'])
            actual = sorted(int(x) for x in node.selection().entities())
            checks.append(compare(actual, {'metric':'physics_entities','reference':sorted(entities)}, str(binding)))
            if binding.get('type'):
                checks.append(compare(str(node.getType()), {'metric':'physics_type','reference':binding['type']}, str(binding)))
        return {'id':contract['id'], 'purpose':contract['purpose'], 'status':aggregate(checks),
                'success':aggregate(checks)=='PASS','entities':entities,'checks':checks}
    except Exception as error:
        return {'id':contract.get('id'), 'success':False, 'status':'FAIL','checks':checks,'error':str(error)}


def bind_selection(model, contract, physics, feature, component='comp1', geometry='geom1'):
    # Re-resolve after a full rebuild, never trust a cached list of boundary IDs.
    built = accept_geometry(model, [], component, geometry, True)
    if built['status'] != 'PASS': return {'success':False,'status':built['status'],'geometry':built}
    pre = validate_selection(model, {**contract, 'bindings':[]}, component, geometry)
    if pre['status'] != 'PASS': return {'success':False,'status':pre['status'],'selection':pre}
    try:
        target = model.java.component(component).physics(physics).feature(feature)
        target.selection().named(contract['tag'])
        return validate_selection(model, {**contract,'bindings':[{'physics':physics,'feature':feature}]}, component, geometry)
    except Exception as error:
        return {'success':False,'status':'FAIL','error':str(error),'selection':pre}
