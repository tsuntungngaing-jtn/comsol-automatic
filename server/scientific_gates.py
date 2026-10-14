"""Deterministic gates over supplied evidence, not independent physics certification."""
import math

IDENTITY = ('run_id', 'model_revision', 'study', 'solver', 'solution', 'dataset', 'parameters_hash')

def freshness(payload):
    expected, observed = payload['expected'], payload['observed']
    missing = [key for key in IDENTITY if key not in expected or key not in observed or expected[key] is None or observed[key] is None or expected[key] == '' or observed[key] == '']
    if missing:
        return {'status':'NOT_RUN', 'missing':missing}
    mismatch = [key for key in IDENTITY if expected[key] != observed[key]]
    passed = not mismatch and observed.get('solve_status') == 'PASS' and observed.get('new_solution') is True
    return {'status':'PASS' if passed else 'FAIL', 'mismatch':mismatch,
            'evidence_scope':'Caller-supplied identity; requires independently acquired artifact evidence'}

def plateau(payload):
    samples = payload['samples']; window = payload['window']
    if not isinstance(window, int) or isinstance(window, bool) or window < 2:
        raise ValueError('window must be an integer >= 2')
    fraction = float(payload['minimum_fractional_drop'])
    if not 0 <= fraction <= 1:
        raise ValueError('minimum_fractional_drop must be between zero and one')
    if len(samples) < window:
        return {'status':'NOT_RUN', 'reason':'Insufficient residual history'}
    tail = samples[-window:]
    for key in ('group','scaling','termination_criterion'):
        if any(not item.get(key) or item[key] != tail[0][key] for item in tail):
            return {'status':'NOT_RUN','reason':'Residual definitions differ or are missing'}
    values = [float(s['residual']) for s in tail]
    if any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError('Residuals must be positive finite values')
    if any(a['iteration'] >= b['iteration'] for a,b in zip(tail,tail[1:])):
        raise ValueError('Iterations must increase')
    drop = (values[0]-min(values[1:]))/values[0]
    stalled = drop < fraction
    return {'status':'FAIL' if stalled else 'PASS', 'plateau_alarm':stalled,
            'fractional_drop':drop, 'solver_stopped':False, 'root_cause':'UNKNOWN',
            'scope':'Residual trend only; not a convergence verdict'}

def conservation(payload):
    identity = freshness(payload['identity'])
    if identity['status'] != 'PASS':
        return {'status':'NOT_RUN','reason':'No verified fresh solution identity','identity':identity}
    expected = payload['required_terms']; terms = payload['terms']
    if not expected or len(expected) != len(set(expected)):
        raise ValueError('Declare unique required boundary, source and storage terms')
    if len({t['id'] for t in terms}) != len(terms):
        raise ValueError('Duplicate conservation terms')
    mapping = {t['id']:t for t in terms}
    missing = [k for k in expected if k not in mapping]
    if missing:
        return {'status':'NOT_RUN','missing_terms':missing}
    unexpected = sorted(set(mapping)-set(expected))
    if unexpected:
        raise ValueError('Undeclared conservation terms: ' + ', '.join(unexpected))
    total = 0.0
    for key in expected:
        term = mapping[key]
        if not all(term.get(k) for k in ('expression','selection','evidence','unit')):
            return {'status':'NOT_RUN','reason':'Missing integral definition or evidence'}
        if term['unit'] != payload['unit']:
            raise ValueError('Conservation units differ')
        value = float(term['value']); sign = term['sign']
        if not math.isfinite(value) or sign not in (-1,1):
            raise ValueError('Invalid signed integral')
        total += sign*value
    denominator = float(payload['normalization']); tolerance = float(payload['tolerance'])
    if not math.isfinite(denominator) or denominator <= 0 or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Declare a positive finite denominator and nonnegative tolerance')
    if not payload['normalization_definition']:
        raise ValueError('Declare the normalization definition')
    residual = abs(total)/denominator
    return {'status':'PASS' if residual <= tolerance else 'FAIL','signed_sum':total,
            'relative_residual':residual,'tolerance':tolerance,'unit':payload['unit']}

def comparison(payload):
    runs = payload['runs']
    if len(runs) < 2:
        return {'status':'NOT_RUN','reason':'At least two validated runs required'}
    for run in runs:
        if freshness(run['identity'])['status'] != 'PASS' or any(run.get(k) != 'PASS' for k in ('convergence','conservation','mesh_independence')):
            return {'status':'NOT_RUN','reason':'A run lacks prerequisite validation'}
    fields = ('conditions_hash','materials_hash','metric_definitions_hash','mesh_strategy_hash')
    if any(not runs[0].get(k) or any(r.get(k)!=runs[0][k] for r in runs) for k in fields):
        return {'status':'BLOCKED','reason':'Comparison conditions are missing or different'}
    return {'status':'PASS','scope':'Comparison admission only; not numerical agreement'}

def evaluate(kind, payload):
    functions = {'freshness':freshness,'plateau':plateau,'conservation':conservation,'comparison':comparison}
    try:
        if kind not in functions:
            raise ValueError('Unknown gate kind')
        result = functions[kind](payload)
        return {'success':result['status']=='PASS', **result}
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        return {'success':False,'status':'FAIL','category':'configuration','retryable':False,'error':str(error)}
