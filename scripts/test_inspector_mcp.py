"""Opt-in real-MPH acceptance through MCP only; no solve, build or save.

Usage: python scripts/test_inspector_mcp.py --model PATH --output OUTSIDE_SKILL
The report contains private model facts. Keep the output outside the release tree.
"""
import argparse
import asyncio
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


async def run(args):
    root = Path(__file__).resolve().parents[1]
    source, output = Path(args.model).resolve(), Path(args.output).resolve()
    if output == root or root in output.parents:
        raise ValueError('Private acceptance output must be outside the skill directory')
    output.mkdir(parents=True, exist_ok=True)
    before = digest(source)
    env = dict(os.environ, COMSOL_ALLOW_CODE='0', COMSOL_CORES='4',
               COMSOL_OUTPUT_ROOT=str(output / 'runtime'), PYTHONIOENCODING='utf-8')
    params = StdioServerParameters(command=sys.executable,
        args=['-m', 'server.main', 'serve', '--transport', 'stdio'], cwd=str(root), env=env)
    calls = []
    with (output / 'mcp_server.log').open('w', encoding='utf-8') as err:
        async with stdio_client(params, errlog=err) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=600)) as session:
                await session.initialize()
                listing = await session.list_tools()
                (output / 'tools.json').write_text(listing.model_dump_json(indent=2), encoding='utf-8')
                async def call(name, arguments=None, filename=None):
                    print('CALL', name, flush=True)
                    response = await session.call_tool(name, arguments or {})
                    calls.append(name)
                    (output / ((filename or name) + '.json')).write_text(response.model_dump_json(indent=2), encoding='utf-8')
                    if response.isError: raise RuntimeError(str(response))
                    data = response.structuredContent
                    if data is None:
                        data = json.loads(next(c.text for c in response.content if c.type == 'text'))
                    if data.get('success') is False: raise RuntimeError(str(data))
                    print('DONE', name, flush=True)
                    return data
                await call('comsol_doctor')
                await call('comsol_start')
                loaded = await call('model_load', {'file_path': str(source)})
                model_name = loaded['model']['name']
                arguments = {'model_name': model_name, 'max_nodes': 1500, 'max_properties': 256}
                first = await call('inspect_current_model', arguments, 'inspection_first')
                second = await call('inspect_current_model', arguments, 'inspection_second')
                for data in (first, second): data.pop('captured_at', None)
                after = digest(source)
                evidence = {'source_sha256_before': before, 'source_sha256_after': after,
                    'source_unchanged': before == after, 'repeated_read_identical': first == second,
                    'node_count': len(first['nodes']), 'limitations_count': len(first['limitations']),
                    'completeness': first['completeness'], 'mcp_calls': calls,
                    'arbitrary_code_enabled': False,
                    'limit': 'No claim of solve validity or exhaustive in-memory immutability proof.'}
                (output / 'acceptance.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
                print(json.dumps(evidence, ensure_ascii=False), flush=True)
                if before != after or first != second: raise AssertionError('Read-only/repeatability acceptance failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', required=True)
    asyncio.run(run(parser.parse_args()))
