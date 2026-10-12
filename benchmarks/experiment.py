"""Generate a fixed-condition experiment manifest; never invent outcomes."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',required=True)
    parser.add_argument('--tool-environment-sha256',required=True)
    parser.add_argument('--seed',type=int,default=20261012)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--max-tool-calls',type=int,default=100)
    parser.add_argument('--max-solves',type=int,default=4)
    parser.add_argument('--seconds',type=int,default=1800)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if min(args.repeats,args.max_tool_calls,args.max_solves,args.seconds)<=0: parser.error('Budgets/repeats must be positive')
    if len(args.tool_environment_sha256)!=64 or any(c not in '0123456789abcdef' for c in args.tool_environment_sha256): parser.error('Expected SHA-256')
    root=Path(__file__).parent
    tasks={p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'tasks').glob('*.json')}
    result={'model':args.model,'environment_sha256':args.tool_environment_sha256,'seed':args.seed,
            'repeats':args.repeats,'budget':{'tool_calls':args.max_tool_calls,'solves':args.max_solves,'seconds':args.seconds},
            'tasks':tasks,'conditions':['tools_only','tools_skill','tools_skill_tutorials','tools_skill_tutorials_acceptance'],
            'protocol':'Same model, tools, tasks and budgets. Fresh model and session context per trial; seeded randomized condition order. Log all calls, mandatory builds and repairs separately. Score independently with score.py.',
            'status':'NOT_RUN','results':[]}
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')

if __name__=='__main__':main()
