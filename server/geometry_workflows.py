"""Stateful validation workflows. All COMSOL calls belong on the MCP JVM thread."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from time import perf_counter
from uuid import uuid4
from .contracts import aggregate, compare
from .compatibility import geometry_version_policy
from .geometry_validation import accept_geometry, validate_selection, measure
from .runtime import inside


def perturb(model, spec, output_root):
    """Save recovery evidence, restore parameters in finally, and verify restoration."""
    run_id = uuid4().hex
    directory = inside(Path(output_root), 'perturbations'/Path(run_id))
    directory.mkdir(parents=True, exist_ok=False)
    path = directory/'baseline.mph'
    report = {'run_id':run_id,'status':'NOT_RUN','success':False,'baseline':str(path),'variants':[],
              'associations':spec.get('associations', []), 'restoration':{'status':'NOT_RUN'}}
    original = {}
    started = perf_counter()
    try:
        parameters = model.java.param()
        for name in spec['parameters']:
            original[name] = str(parameters.get(name))
        # The snapshot is a recovery artifact, not a claim of full solution restoration.
        model.save(str(path))
        report['baseline_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        baseline = accept_geometry(model, spec['baseline_requirements'], rebuild=True)
        report['baseline_validation'] = baseline
        if baseline['status'] != 'PASS':
            report['status'] = baseline['status']
            return report
        geom = model.java.component('comp1').geom('geom1')
        for variant in spec['variants']:
            if set(variant['parameters']) - set(original):
                raise ValueError('Variant parameter missing from declared baseline parameters')
            for name, value in original.items(): parameters.set(name, value)
            for name, value in variant['parameters'].items(): parameters.set(name, str(value))
            geometry = accept_geometry(model, variant['requirements'], rebuild=True)
            selections = [validate_selection(model, c) for c in variant.get('selections', [])]
            records = [geometry, *selections]
            for relation in variant.get('relations', []):
                metric = relation['metric']
                base = next(c['measured'] for c in baseline['checks'] if c.get('metric') == metric)
                actual = measure(geom, metric)
                mode = relation['operation']
                if mode == 'ratio': value = actual/base
                elif mode == 'difference': value = actual-base
                else: raise ValueError('Relations support explicit ratio or difference only')
                records.append(compare(value, relation, 'Measured variant versus measured baseline'))
            report['variants'].append({'id':variant['id'],'parameters':variant['parameters'],
                                       'status':aggregate(records),'geometry':geometry,'selections':selections,'checks':records})
        report['status'] = aggregate(report['variants'])
    except Exception as error:
        report.update(status='FAIL', error=str(error))
    finally:
        try:
            for name, value in original.items(): model.java.param().set(name, value)
            if original:
                geometry = accept_geometry(model, spec['baseline_requirements'], rebuild=True)
                selections = [validate_selection(model,c) for c in spec.get('baseline_selections', [])]
                report['restoration'] = {'status':aggregate([geometry,*selections]), 'geometry':geometry,'selections':selections,
                                         'solution':'NOT_RUN: rebuild invalidates old solution; solve again before evaluation'}
                report['status'] = aggregate([{'status':report['status']}, report['restoration']])
        except Exception as error:
            report['restoration'] = {'status':'FAIL','error':str(error),'recovery':str(path)}
            report['status'] = 'FAIL'
        report['elapsed_seconds'] = perf_counter()-started
        report['success'] = report['status']=='PASS'
        (directory/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def import_cad(model, spec, output_root, environment):
    """Import into a new, empty geometry only. Never overwrite an existing sequence."""
    report = {'run_id':uuid4().hex,'success':False,'status':'NOT_RUN','environment':environment,
              'editability':'Imported BRep; no recovery of the source CAD feature tree', 'provenance':dict(spec)}
    directory = inside(Path(output_root), Path('cad-imports')/report['run_id'])
    directory.mkdir(parents=True, exist_ok=False)
    created = []
    try:
        if geometry_version_policy(environment['version'])['status'] != 'PASS':
            report.update(status='BLOCKED', error='VERSION_MISMATCH: re-anchor CAD APIs to installed documentation')
            return report
        if not environment.get('products', {}).get('CADIMPORT'):
            report.update(status='BLOCKED', error='CADIMPORT entitlement unavailable or unverified')
            return report
        source = Path(spec['path']).resolve(strict=True)
        if source.suffix.lower() not in {'.step','.stp','.iges','.igs','.x_t','.sat'}:
            raise ValueError('Supported workflow is BRep CAD, not an imported mesh')
        report['provenance'].update(path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),format=source.suffix.lower())
        for key in ('source_unit','geometry_unit','unit_policy','finalization','interior_boundaries','pair_strategy','repair_tolerance','repair_actions','transforms','requirements'):
            if key not in spec: raise ValueError(f'Missing CAD specification field: {key}')
        if spec['unit_policy'] not in ('source','current'): raise ValueError('Invalid unit policy')
        if spec['finalization'] not in ('union','assembly'): raise ValueError('Invalid finalization')
        if spec['pair_strategy'] not in ('none','identity','contact'): raise ValueError('Invalid pair strategy')
        if spec['finalization']=='union' and spec['pair_strategy']!='none': raise ValueError('Pairs require assembly')
        comp = model.java.component(spec.get('component','comp1'))
        tag = spec.get('geometry','geom1')
        if tag in [str(t) for t in comp.geom().tags()]:
            raise ValueError('CAD import requires a new geometry tag to preserve existing geometry')
        geom = comp.geom().create(tag,3)
        created.append(tag)
        geom.lengthUnit(spec['geometry_unit'])
        node = geom.create('cad1','Import');created.append('cad1')
        node.set('filename',str(source));node.set('unit',spec['unit_policy'])
        node.set('importtol',str(spec['repair_tolerance']))
        for key, value in spec['repair_actions'].items():
            if key not in ('fixerrors','simplify','knit','formsolid','healedges','minimizetol'):
                raise ValueError(f'Unreviewed repair action: {key}')
            node.set(key,value)
        node.set('selresult','on')
        previous = 'cad1'
        for index, transform in enumerate(spec['transforms']):
            kind = transform['type']
            allowed = {'Move':{'displ'},'Rotate':{'axis','pos','rot'},'Scale':{'factor','pos'}}
            if kind not in allowed or set(transform['properties'])-allowed[kind]:
                raise ValueError('Unsupported transform or property')
            name = f'transform{index+1}'
            step = geom.create(name,kind);created.append(name)
            step.selection('input').set([previous])
            for key,value in transform['properties'].items(): step.set(key,value)
            previous=name
        # Explicit Union keeps/removes internal boundaries; Finalize handles Assembly.
        if spec['finalization']=='union':
            union=geom.create('cad_union','Union');created.append('cad_union')
            union.selection('input').set([previous]);union.set('intbnd','on' if spec['interior_boundaries'] else 'off')
        final=geom.feature('fin');final.set('action',spec['finalization'])
        final.set('createpairs','off' if spec['pair_strategy']=='none' else 'on')
        if spec['pair_strategy']!='none': final.set('pairtype',spec['pair_strategy'])
        report['geometry']=accept_geometry(model,spec['requirements'],spec.get('component','comp1'),tag,True)
        report['pairs']=[str(t) for t in comp.pair().tags()]
        report['status']=report['geometry']['status']
        if spec.get('contact_requirements'):
            report['contact']={'status':'NOT_RUN','reason':'Contact topology requires task-specific adjacency/pair evaluator; pair presence is insufficient'}
            report['status']=aggregate([report['geometry'],report['contact']])
        model.save(str(directory/'imported.mph'))
        report['mph']=str(directory/'imported.mph')
        report['mph_sha256']=hashlib.sha256((directory/'imported.mph').read_bytes()).hexdigest()
    except Exception as error:
        report.update(status='FAIL',error=str(error),partial_nodes=created,
                      recovery='Retained isolated geometry; inspect or explicitly remove before reuse')
    finally:
        report['success']=report['status']=='PASS'
        (directory/'provenance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
