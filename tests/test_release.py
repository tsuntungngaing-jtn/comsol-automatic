"""Distribution boundary tests; no COMSOL license or network required."""
import importlib.util
import json
import secrets
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_builder', ROOT/'scripts/release.py')
release=importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def fixture(self, root):
        for name in ['SKILL.md','README.md','LICENSE','pyproject.toml','server/main.py',
                     'vendor/installed-mcp/LICENSE','examples/catalog.json']:
            p=root/name
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('{}' if p.suffix=='.json' else 'public source',encoding='utf-8')
        (root/'vendor/installed-mcp/SNAPSHOT.json').write_text(json.dumps({'files':[]}),encoding='utf-8')

    def test_private_named_asset_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.fixture(root)
            (root/'examples'/('D'+'BC_figure.png')).write_bytes(b'not a public asset')
            with self.assertRaisesRegex(ValueError, 'Private filename'):
                release.public_files(root)

    def test_commercial_model_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.fixture(root)
            (root/'examples/tutorial.mph').write_bytes(b'proprietary')
            with self.assertRaisesRegex(ValueError, 'Forbidden file'):
                release.public_files(root)

    def test_zip_is_self_contained_and_excludes_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source'
            root.mkdir()
            self.fixture(root)
            (root/'runs').mkdir()
            (root/'runs/private.log').write_text('user calculation',encoding='utf-8')
            local_token=secrets.token_urlsafe(32)
            (root/'.mcp-token').write_text(local_token,encoding='utf-8')
            output=Path(tmp)/'skill.zip'
            release.build(output,root)
            with zipfile.ZipFile(output) as archive:
                names=archive.namelist()
                self.assertIn('comsol-automatic/server/main.py',names)
                self.assertIn('comsol-automatic/vendor/installed-mcp/LICENSE',names)
                self.assertIn('comsol-automatic/SKILL.md',names)
                self.assertFalse(any('/runs/' in name for name in names))
                self.assertFalse(any('.mcp-token' in name for name in names))
                self.assertFalse(any(local_token.encode() in archive.read(name) for name in names))
                manifest=json.loads(archive.read('comsol-automatic/RELEASE_MANIFEST.json'))
                for record in manifest['files']:
                    data=archive.read('comsol-automatic/'+record['path'])
                    self.assertEqual(release.digest(data),record['sha256'])


if __name__=='__main__':
    unittest.main()
