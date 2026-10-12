"""Offline scoring; missing evidence has no invented numerical score."""
import argparse
import json
from pathlib import Path
from server.contracts import validate_document


def score(report):
    checked=validate_document(report,'validation-report')
    if not checked['success']:
        return {'status':'FAIL','errors':checked['errors']}
    result={'run_id':report['run_id'],'status':report['status']}
    for layer in ('api','geometry','selection','physics','numerical','scientific','reopen'):
        checks=report['layers'][layer]['checks']
        known=[c for c in checks if c.get('status') in ('PASS','FAIL')]
        result[layer]={'status':report['layers'][layer]['status'],
                       'pass_fraction':sum(c['status']=='PASS' for c in known)/len(known) if known else None,
                       'coverage':len(known)/len(checks) if checks else 0,
                       'unexecuted':sum(c.get('status') in ('NOT_RUN','BLOCKED') for c in checks)}
    claims=report.get('tool_claims',[])
    judged=[c for c in claims if c.get('independent_status') in ('PASS','FAIL')]
    result['false_success_rate']=sum(c.get('success') is True and c['independent_status']=='FAIL' for c in judged)/len(judged) if judged else None
    result['objective_errors']=[c.get('error_value') for c in report['layers']['numerical']['checks'] if 'error_value' in c]
    result['cost']={k:sum(c[k] for c in report['repair_history'] if c['operation']=='repair') for k in ('executions','solves','elapsed_seconds')}
    result['tree_similarity']='diagnostic only; not scored'
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    print(json.dumps(score(json.loads(args.report.read_text(encoding='utf-8-sig'))),indent=2))

if __name__=='__main__':main()
