"""Include the runtime's non-package resources in wheels and source builds."""
from pathlib import Path
from shutil import copy2
from setuptools import setup
from setuptools.command.build_py import build_py

class BuildWithResources(build_py):
    def run(self):
        super().run()
        root = Path(__file__).parent
        dest = Path(self.build_lib) / 'server' / 'resources'
        for folder in ['vendor', 'examples']:
            for source in (root/folder).rglob('*'):
                if not source.is_file() or any(p in {'__pycache__', '.venv', 'validation'} for p in source.parts):
                    continue
                if source.suffix not in {'.py', '.md', '.json', '.toml'} and source.name != 'LICENSE':
                    continue
                target = dest/source.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                copy2(source,target)

setup(cmdclass={'build_py':BuildWithResources})
