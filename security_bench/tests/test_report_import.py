"""Synthetic ZIPs only; no external data or inference."""
import tempfile
import unittest
from pathlib import Path
import zipfile
from scripts.import_experiment_reports import import_bundle


class ImportTests(unittest.TestCase):
    def test_original_bytes_preserved_and_source_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);archive=root/'fixture.zip';payload=b'{"fixture":true}\r\n'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('data/agent-security-study/runs/unit-fixture/events.jsonl',payload)
                z.writestr('scripts/do_not_execute.py','raise RuntimeError("must not execute")')
            result=import_bundle(archive,root,root/'record')
            self.assertEqual((root/'data/agent-security-study/runs/unit-fixture/events.jsonl').read_bytes(),payload)
            self.assertFalse((root/'scripts').exists())
            self.assertEqual(result['imported_files'],1)
            self.assertEqual(result['model_calls'],0)
    def test_collision_rejected_before_any_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);archive=root/'fixture.zip';original=root/'data/agent-security-study/runs/fixture/a'
            original.parent.mkdir(parents=True);original.write_bytes(b'original')
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('data/agent-security-study/runs/fixture/new',b'new')
                z.writestr('data/agent-security-study/runs/fixture/a',b'changed')
            with self.assertRaises(ValueError):import_bundle(archive,root,root/'record')
            self.assertEqual(original.read_bytes(),b'original')
            self.assertFalse((original.parent/'new').exists())
            self.assertFalse((root/'record').exists())
    def test_unsafe_or_duplicate_entries_rejected(self):
        for names in [['../outside'],['C:/outside'],['data/CON.txt'],['data/a','data/A']]:
            with self.subTest(names=names),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);archive=root/'fixture.zip'
                with zipfile.ZipFile(archive,'w') as z:
                    for name in names:z.writestr(name,b'fixture')
                with self.assertRaises(ValueError):import_bundle(archive,root,root/'record')
                self.assertFalse((root/'record').exists())
