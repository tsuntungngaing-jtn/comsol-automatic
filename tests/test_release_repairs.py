import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit_versioning', ROOT/'vendor/installed-mcp/src/utils/versioning.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class SaveRepairTests(unittest.TestCase):
    def test_same_second_versions_are_unique(self):
        class Frozen:
            @staticmethod
            def now(): return datetime(2026,10,12,12,0,0)
        with TemporaryDirectory() as tmp, patch.object(v,'MODELS_BASE_DIR',Path(tmp)), patch.object(v,'datetime',Frozen):
            a=v.generate_version_path('model')
            b=v.generate_version_path('model')
            self.assertNotEqual(a,b)

    def test_parent_name_rejected_before_writing(self):
        with TemporaryDirectory() as tmp, patch.object(v,'MODELS_BASE_DIR',Path(tmp)/'versions'):
            with self.assertRaises(ValueError): v.generate_version_path('..')
            self.assertFalse((Path(tmp)/'versions').exists())

    def test_escape_name_rejected(self):
        with TemporaryDirectory() as tmp, patch.object(v,'MODELS_BASE_DIR',Path(tmp)):
            for name in ['../bad','nested/name','C:\\outside\\name.mph','CON','']:
                with self.subTest(name=name),self.assertRaises(ValueError):v.generate_version_path(name)

if __name__=='__main__':unittest.main()
