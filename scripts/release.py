"""Build a self-contained skill ZIP from an explicit public-source allowlist.

Run from any directory: python scripts/release.py --output ../Comsol-Automatic-v0.1.0.zip
No network access, repository-wide glob upload, credentials, or model files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {'SKILL.md','README.md','LICENSE','NOTICE.md','.gitignore','pyproject.toml'}
DIRECTORIES = {'server','vendor','examples','docs','scripts','tests'}
EXTENSIONS = {'.py','.md','.toml','.json','.csv','.png','.cff','.ps1'}
SKIP_PARTS = {'.git','.venv','__pycache__','.pytest_cache','runs','runtime','dist','build'}
FORBIDDEN_EXTENSIONS = {'.mph','.mphbin','.log','.pdf','.step','.stp','.pem','.key','.pfx','.zip','.pyc','.pyo'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def public_files(root=ROOT):
    root=Path(root).resolve()
    result=[]
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if any(part in SKIP_PARTS or part.endswith('.egg-info') for part in rel.parts):
            continue
        if not p.is_file():
            continue
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError(f'Symlinks are not published: {rel}')
        if len(rel.parts)==1:
            if p.name not in ROOT_FILES:
                continue
        elif rel.parts[0] not in DIRECTORIES:
            continue
        if p.suffix.lower() in FORBIDDEN_EXTENSIONS or p.name.startswith('.env'):
            raise ValueError(f'Forbidden file in a publication directory: {rel}')
        if p.suffix.lower() not in EXTENSIONS and p.name not in ROOT_FILES:
            raise ValueError(f'Unreviewed file type in publication directory: {rel}')
        data=p.read_bytes()
        # Match file-name/word markers, not accidental substrings in SHA digests.
        private_terms=['D'+'BC', 'codex'+'-clipboard', 'AppData'+'\\Local\\Temp']
        marker_patterns=[re.compile(r'(?<![A-Za-z0-9])'+re.escape(term)+r'(?![A-Za-z0-9])', re.I) for term in private_terms]
        if any(pattern.search(rel.as_posix()) for pattern in marker_patterns):
            raise ValueError(f'Private filename marker in {rel}')
        if p.suffix != '.png':
            content=data.decode('utf-8-sig')
            # Private marker strings are intentionally assembled to avoid a
            # scanner matching its own source. Add project-specific terms locally.
            if any(pattern.search(content) for pattern in marker_patterns):
                raise ValueError(f'Private project/path marker in {rel}')
            if re.search(r'(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s<>"\']+', content):
                raise ValueError(f'Personal Windows home path in {rel}')
            if re.search(r'\bsk-[A-Za-z0-9_-]{20,}', content):
                raise ValueError(f'Possible API credential in {rel}')
            if ('-----BEGIN ' + 'PRIVATE KEY-----') in content:
                raise ValueError(f'Private key in {rel}')
        result.append((rel.as_posix(), data))
    present={name for name,_ in result}
    for required in ['SKILL.md','README.md','LICENSE','pyproject.toml','server/main.py',
                     'vendor/installed-mcp/LICENSE','examples/catalog.json']:
        if required not in present:
            raise ValueError(f'Missing required distribution file: {required}')
    snapshot_path=root/'vendor/installed-mcp/SNAPSHOT.json'
    snapshot=json.loads(snapshot_path.read_text(encoding='utf-8'))
    for record in snapshot['files']:
        source=root/'vendor/installed-mcp'/record['path']
        if digest(source.read_bytes()) != record['sha256']:
            raise ValueError(f'Vendor provenance mismatch: {record["path"]}')
    return result


def build(output, root=ROOT):
    output=Path(output).resolve()
    if output.is_relative_to(Path(root).resolve()):
        raise ValueError('Release ZIP must be outside the skill directory')
    files=public_files(root)
    manifest={'format':1,'skill_name':'comsol-automatic','display_name':'Comsol-Automatic','author':'抖音 萌猪过河','files':[
        {'path':name,'bytes':len(data),'sha256':digest(data)} for name,data in files]}
    files.append(('RELEASE_MANIFEST.json',(json.dumps(manifest,indent=2)+'\n').encode()))
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in files:
            info=zipfile.ZipInfo('comsol-automatic/'+name, date_time=(2026,9,5,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644 << 16
            archive.writestr(info,data)
    output.with_suffix(output.suffix+'.sha256').write_text(digest(output.read_bytes())+'  '+output.name+'\n',encoding='ascii')
    return {'file':str(output),'files':len(files),'bytes':output.stat().st_size,'sha256':digest(output.read_bytes())}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.output),indent=2))
