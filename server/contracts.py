"""Executable contracts. No COMSOL imports; usable by offline evaluators."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from jsonschema import Draft202012Validator

STATES = {'PASS', 'FAIL', 'BLOCKED', 'NOT_RUN'}
LAYERS = ('api', 'geometry', 'selection', 'physics', 'numerical', 'scientific', 'reopen')

def aggregate(checks):
    required = [c for c in checks if c.get('required', True)]
    statuses = [c.get('status', 'NOT_RUN') for c in required]
    if any(s not in STATES for s in statuses):
        return 'FAIL'
    for state in ('FAIL', 'BLOCKED', 'NOT_RUN'):
        if state in statuses:
            return state
    return 'PASS' if required else 'NOT_RUN'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()

def compare(measured, requirement, source, error=None):
    record = dict(requirement, measured=measured, evidence=source, status='NOT_RUN')
    if error is not None:
        record['error'] = str(error)
        return record
    if measured is None:
        record['error'] = 'Measurement unavailable'
        return record
    try:
        if 'reference' in requirement:
            reference = requirement['reference']
            absolute = requirement.get('atol', 0)
            relative = requirement.get('rtol', 0)
            if absolute < 0 or relative < 0:
                raise ValueError('Tolerances must be nonnegative')
            def close(a, b):
                if isinstance(b, str):
                    return a == b
                return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(a-b) <= absolute + relative*abs(b)
            if isinstance(reference, list):
                passed = len(measured) == len(reference) and all(close(a,b) for a,b in zip(measured, reference))
            else:
                passed = close(measured, reference)
        elif 'range' in requirement:
            lo, hi = requirement['range']
            passed = math.isfinite(float(measured)) and lo <= measured <= hi
        else:
            raise ValueError('A reference or range is required')
        record['status'] = 'PASS' if passed else 'FAIL'
    except (TypeError, ValueError, OverflowError) as error:
        record.update(status='FAIL', error=str(error))
    return record

def validate_document(document, kind='simulation-spec'):
    if kind not in ('simulation-spec', 'validation-report'):
        return {'success':False, 'status':'FAIL', 'errors':[{'error':'Unknown document kind'}]}
    root = Path(__file__).resolve().parent
    resources = root/'resources' if (root/'resources'/'schemas').exists() else root.parent
    schema = json.loads((resources/'schemas'/f'{kind}.schema.json').read_text(encoding='utf-8'))
    errors = [{'path': '/'.join(map(str,e.path)), 'error': e.message}
              for e in Draft202012Validator(schema).iter_errors(document)]
    dependencies = []
    if kind == 'simulation-spec' and not errors:
        tags = [c['id'] for c in document['selections']]
        if len(tags) != len(set(tags)):
            errors.append({'path':'selections', 'error':'Duplicate selection IDs'})
        for condition in document['physics'].get('boundaries', []):
            if condition.get('selection') not in tags:
                dependencies.append({'task': condition.get('id'), 'status':'BLOCKED', 'reason':'Unknown selection contract'})
        for missing in document['missing_information']:
            dependencies.extend({'task': task, 'status':'BLOCKED', 'reason': missing['description']}
                                for task in missing['affects'])
        for contract in document['selections']:
            if contract['dimension'] > document['geometry']['dimension']:
                errors.append({'path':contract['id'], 'error':'Selection dimension exceeds geometry dimension'})
    if kind == 'validation-report' and not errors:
        for name, layer in document['layers'].items():
            for check in layer['checks']:
                if check['run_id'] != document['run_id']:
                    errors.append({'path':'layers/'+name, 'error':'Evidence belongs to another run'})
                if check['status'] == 'PASS' and check['measured'] is None:
                    errors.append({'path':'layers/'+name, 'error':'PASS requires an observed value'})
            if layer['status'] == 'PASS' and aggregate(layer['checks']) != 'PASS':
                errors.append({'path': 'layers/'+name, 'error': 'PASS requires executed passing evidence'})
        computed = aggregate(document['layers'].values())
        if document['status'] != computed:
            errors.append({'path':'status', 'error':f'Expected conservative aggregate {computed}'})
    status = 'FAIL' if errors else ('BLOCKED' if dependencies else 'PASS')
    return {'success':status == 'PASS', 'status':status, 'schema_status':'FAIL' if errors else 'PASS',
            'dependency_status':'BLOCKED' if dependencies else 'PASS',
            'execution_admissible':status == 'PASS', 'errors':errors, 'dependencies':dependencies}

def new_report(run_id, spec_hash, environment):
    return {'run_id':run_id, 'spec_hash':spec_hash, 'environment':environment, 'status':'NOT_RUN',
            'layers':{key:{'status':'NOT_RUN','checks':[]} for key in LAYERS}, 'repair_history':[]}

def repair_event(stage, error, change, executions, solves, elapsed_seconds, validation,
                 repeated_failures=0, stop_reason=None, operation='repair'):
    if min(executions, solves, elapsed_seconds, repeated_failures) < 0 or solves > executions:
        raise ValueError('Invalid execution accounting')
    if operation not in ('necessary', 'repair'):
        raise ValueError('Unknown operation category')
    return dict(stage=stage, error=error, warnings=validation.get('warnings', []), change=change,
                executions=executions, solves=solves, elapsed_seconds=elapsed_seconds,
                validation=validation, repeated_failures=repeated_failures,
                stop_reason=stop_reason, operation=operation)


def admit_task(document, task):
    """Missing evidence blocks only tasks explicitly dependent on it."""
    result = validate_document(document)
    blockers = [d for d in result.get('dependencies', []) if d['task'] == task]
    allowed = result.get('schema_status') == 'PASS' and not blockers
    return {'success':allowed, 'status':'PASS' if allowed else 'BLOCKED',
            'task':task, 'blockers':blockers, 'schema_errors':result.get('errors', [])}
