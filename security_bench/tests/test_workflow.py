"""Temporary synthetic transport fixtures, never saved as research observations."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from security_bench.common import ROOT, write, read, rows
from security_bench.runner import plan, execute
from security_bench.tests.test_safety import fixture_config, FakeResponse


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.c = fixture_config()
        try:
            from security_bench.dojo import suites
            suites(self.c)
        except ImportError:
            self.skipTest('Actual upstream AgentDojo dependencies unavailable')
        pricing = {m['provider'] + ':' + m['model_id']: {'input_usd_per_million': 1,
            'output_usd_per_million': 1, 'basis': 'synthetic_test_rates_not_real_prices'}
            for m in self.c['models'].values()}
        write(self.root / 'test-pricing.json', pricing)
        self.c['pricing_file'] = str(self.root / 'test-pricing.json')
        self.env = patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture-only-key',
            'OPENAI_API_KEY': 'fixture-only-key', 'DEEPSEEK_API_KEY': 'fixture-only-key'})
        self.env.start()
    def tearDown(self):
        if hasattr(self, 'env'):
            self.env.stop()
        self.temp.cleanup()
    def static_fixture(self, config, dataset):
        return [{'dataset_id': dataset, 'item_id': 'test', 'family_id': 'test',
            'evaluation_mode': config['datasets'][dataset]['mode_code'], 'view': {'user_request': 'TEST'},
            'input_sha256': 'test-input', 'gold': 1, 'gold_source': 'synthetic_fixture_only'}]
    def test_one_entrypoint_records_all_arms_and_resume_does_not_replay(self):
        class Opener:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                body = json.loads(req.data)
                model = body['model']
                response = {'model': model, 'usage': {'input_tokens': 2, 'output_tokens': 1}}
                if model == 'test-main_agent':
                    response['choices'] = [{'finish_reason':'stop', 'message': {'role': 'assistant', 'content': 'TEST FINAL'}}]
                elif model == 'test-jev':
                    response['answers'] = {'risk': {'type':'choice', 'choice':'unsafe'}}
                else:
                    response.update(status='completed', output=[{'type': 'message',
                        'content': [{'type': 'output_text', 'text': '{"risk":true}'}]}])
                return FakeResponse(response)
        opener = Opener()
        directory = self.root / 'run'
        with patch('security_bench.runner.load_static', self.static_fixture):
            result = plan(self.c, directory)
        self.assertEqual(result['episodes'], 8)
        completed = execute(self.c, directory, opener=opener)
        self.assertEqual(completed['attempted'], 8)
        count = opener.calls
        again = execute(self.c, directory, resume=True, opener=opener)
        self.assertEqual(again['attempted'], 0)
        self.assertEqual(opener.calls, count)
        self.assertEqual(len(rows(directory / 'episodes.jsonl')), 8)
        analyses = sorted((directory / 'analysis').glob('*/summary.json'))
        self.assertEqual(len(analyses), 2)
        report = read(analyses[-1])
        self.assertEqual(report['status'], 'complete')
        self.assertEqual(len(report['groups']), 8)
        self.assertEqual(sum(g['resources']['calls'] for g in report['groups']), count)
    def test_changed_plan_is_rejected_before_transport(self):
        directory = self.root / 'run'
        with patch('security_bench.runner.load_static', self.static_fixture):
            plan(self.c, directory)
        with (directory / 'cases.jsonl').open('a', encoding='utf-8') as f:
            f.write('{}\n')
        with self.assertRaisesRegex(ValueError, 'cases changed'):
            execute(self.c, directory)

    def test_current_four_datasets_run_without_main_agent_or_dojo(self):
        c = read(ROOT/'configs/security-bench.template.json')
        for name in ['phase','repeats','schedule_seed','budget','pricing_file']:
            c[name] = self.c[name]
        for model in ['jev','gpt6luna']:
            c['models'][model] = self.c['models'][model]
        for name, spec in c['datasets'].items():
            spec['mode_definition'] = 'SYNTHETIC TEST CONTRACT ONLY'
            spec['exposure_status'] = 'test_fixture'
            spec['contract'] = ('skill_risk_classification' if name == 'maliciousskillbench' else
                                'request_risk_classification' if name == 'agentharm' else 'full_trace_risk_classification')
        c['datasets']['maliciousskillbench']['withheld_text_policy'] = 'exclude'
        c['datasets']['mcphunt']['gold_field'] = 'any_risk'
        for name in c['contracts']:
            c['contracts'][name] = {'instructions':'TEST ONLY', 'positive_class':'risk', 'label_semantics':'test_only'}
        class Opener:
            def open(self, req, timeout):
                model = json.loads(req.data)['model']
                if model not in ('test-jev','test-gpt6luna'):
                    raise AssertionError('Inactive main agent must never be called')
                response = {'model':model, 'usage':{'input_tokens':2,'output_tokens':1}}
                if model == 'test-jev':
                    response['answers'] = {'risk':{'type':'choice','choice':'unsafe'}}
                else:
                    response.update(status='completed',output=[{'type':'message','content':[{'type':'output_text','text':'{"risk":true}'}]}])
                return FakeResponse(response)
        directory = self.root/'current'
        with patch('security_bench.runner.load_static', self.static_fixture), patch('security_bench.dojo.prepare', side_effect=AssertionError('Legacy Dojo planner called')):
            result = plan(c, directory)
        self.assertEqual(result['episodes'], 8)
        execute(c, directory, opener=Opener())
        self.assertEqual({x['dataset_id'] for x in rows(directory/'episodes.jsonl')},
                         {'maliciousskillbench','agentharm','mcphunt','atbench'})
        self.assertTrue(all(x['component']=='safety_module' for x in rows(directory/'events.jsonl') if x['event']=='request_started'))


if __name__ == '__main__':
    unittest.main()
