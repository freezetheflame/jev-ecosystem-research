"""Native Skill input views, with synthetic parquet fixtures only."""
import tempfile
from pathlib import Path
import unittest
from security_bench.common import ROOT, read
from security_bench.datasets import load_static
from security_bench.config import inspect


class SkillInputTests(unittest.TestCase):
    def test_native_skill_text_only_and_explicit_redaction_policy(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pq.write_table(pa.Table.from_pylist([
                {'benchmark_id':'test1', 'structural_family_id':'family', 'label':'1',
                 'original_text_withheld':False, 'skill_text':'TEST skill content', 'public_skill_text':None},
                {'benchmark_id':'test2', 'structural_family_id':'family', 'label':'1',
                 'original_text_withheld':True, 'skill_text':None, 'public_skill_text':'TEST sanitized text'}]),
                root/'primary.parquet')
            c = read(ROOT/'configs/security-bench.template.json')
            c['maliciousskillbench_path'] = str(root)
            c['datasets']['maliciousskillbench']['withheld_text_policy'] = 'exclude'
            records = load_static(c, 'maliciousskillbench')
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]['view'], {'skill_text':'TEST skill content'})
            self.assertEqual(records[0]['gold'], 1)
            c['datasets']['maliciousskillbench']['withheld_text_policy'] = 'public_sanitized'
            records = load_static(c, 'maliciousskillbench')
            self.assertEqual(len(records), 2)
            self.assertEqual(records[1]['text_representation'], 'public_sanitized')
            c['datasets']['maliciousskillbench']['withheld_text_policy'] = None
            with self.assertRaises(ValueError):
                load_static(c, 'maliciousskillbench')

    def test_current_preflight_does_not_require_inactive_main_agent(self):
        c = read(ROOT/'configs/security-bench.template.json')
        result = inspect(c, check_keys=False)
        self.assertNotIn('agentdojo', result['local_sources_available'])
        self.assertTrue(result['local_sources_available']['maliciousskillbench'])
        self.assertFalse(any('main_agent' in x or 'agentdojo' in x.lower() for x in result['issues']))
