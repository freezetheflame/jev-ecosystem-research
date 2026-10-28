"""Offline engineering fixtures only. No network, measurements or research results."""
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from security_bench.common import ROOT, read, write, rows, encode
from security_bench.config import inspect
from security_bench.datasets import load_static
from security_bench.models import Transport, Judge, StopRun, TransportError, load_monitor, request, output_text
from security_bench.report import summarize


def fixture_config():
    c = read(ROOT / 'configs/security-bench-agentdojo.template.json')
    c['monitor_workspace'] = 'vendor/preserved-monitor'
    c.update(phase='pilot', repeats=1, schedule_seed=1, main_agent_system_prompt='TEST FIXTURE ONLY')
    c['budget'] = {'max_calls': 100, 'max_wall_seconds': 100, 'max_api_usd': 100, 'reserve_usd_per_call': 1}
    for name, model in c['models'].items():
        model.update(model_id='test-' + name, endpoint='https://example.invalid/api', timeout_seconds=3,
                     parameter_status={'server_defaults': 'unknown_default'})
    for key in c['contracts']:
        c['contracts'][key] = {'instructions': 'TEST risk classification; return {"risk":true} or {"risk":false}',
                               'positive_class': 'TEST risk', 'label_semantics': 'synthetic_test_only'}
    for name, spec in c['datasets'].items():
        spec.update(mode_definition='TEST ONLY', exposure_status='test_fixture',
                    contract='request_risk_classification' if name == 'agentharm' else 'full_trace_risk_classification')
    c['datasets']['mcphunt']['gold_field'] = 'any_risk'
    c['datasets']['agentdojo'].update(contract='pre_action_authorization', benchmark_version='v1.2.2',
        mode_code='B', mode_definition='SYNTHETIC TEST CONTRACT ONLY; not approved study Mode B semantics',
        suites=['banking'], user_task_ids={'banking': ['user_task_0']}, attacks=[], include_clean=True,
        blocked_feedback='BLOCKED TEST FIXTURE', max_steps=3, max_tool_calls=3)
    return c


class FakeResponse:
    status = 200
    headers = {'x-request-id': 'fixture-request-id'}
    def __init__(self, payload):
        self.body = encode(payload)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self):
        return self.body


class FakeOpener:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
    def open(self, request, timeout):
        self.calls += 1
        if isinstance(self.payload, Exception):
            raise self.payload
        return FakeResponse(self.payload)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.config = fixture_config()
        self.env = patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture-key-never-real',
            'OPENAI_API_KEY': 'fixture-key-never-real', 'DEEPSEEK_API_KEY': 'fixture-key-never-real'})
        self.env.start()
        try:
            self.module = load_monitor(self.config)
        except FileNotFoundError:
            self.skipTest('Preserved external monitor checkout is not installed')
        self.monitor = self.module.ResourceMonitor('unit_test_fixture', directory=self.path / 'telemetry',
            pricing={'typesafe:test-jev': {'input_usd_per_million': 1, 'output_usd_per_million': 1, 'basis': 'synthetic_test_only'}})
    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()
    def test_meter_once_and_request_precedes_response(self):
        opener = FakeOpener({'model': 'test-jev', 'answers': {'risk': {'type':'choice', 'choice':'unsafe'}},
                             'usage': {'input_tokens': 10, 'output_tokens': 1}})
        t = Transport(self.config, self.path, self.monitor, opener)
        prediction = Judge(self.config, 'jev', t).judge({'user_request': 'fixture'}, 'request_risk_classification', 'ep')
        self.assertEqual(prediction, 1)
        self.assertEqual(opener.calls, 1)
        self.assertEqual(self.monitor.totals['calls'], 1)
        events = rows(self.path / 'events.jsonl')
        self.assertEqual([x['event'] for x in events], ['request_started', 'request_finished'])
        self.assertNotIn('fixture-key-never-real', (self.path / 'events.jsonl').read_text())
        self.assertEqual(events[-1]['monitor_event_index'], 0)
    def test_unknown_cost_stops_next_call(self):
        t = Transport(self.config, self.path, self.monitor, FakeOpener({'model': 'test-jev'}))
        t.post({'model': 'test-jev'}, 'jev', 'ep', 'safety_module')
        with self.assertRaises(StopRun):
            t.post({'model': 'test-jev'}, 'jev', 'ep2', 'safety_module')
        self.assertEqual(self.monitor.totals['calls'], 1)
        self.assertIsNone(self.monitor.summary['estimated_cost_usd'])
    def test_error_body_redacts_actual_key_and_is_retained(self):
        error = urllib.error.HTTPError('https://example.invalid', 401, 'fixture', {},
                                      io.BytesIO(b'fixture-key-never-real denied'))
        t = Transport(self.config, self.path, self.monitor, FakeOpener(error))
        with self.assertRaises(TransportError):
            t.post({'model': 'test-jev'}, 'jev', 'ep', 'safety_module')
        body = next((self.path / 'raw').glob('*/response.body')).read_text()
        self.assertIn('[REDACTED]', body)
        self.assertNotIn('fixture-key-never-real', body)
        self.assertEqual(self.monitor.totals['failed_calls'], 1)
    def test_budget_prevents_transport(self):
        self.config['budget']['max_calls'] = 0
        opener = FakeOpener({})
        with self.assertRaises(StopRun):
            Transport(self.config, self.path, self.monitor, opener).post({}, 'jev', 'ep', 'safety_module')
        self.assertEqual(opener.calls, 0)


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.c = fixture_config()
        self.c['data_root'] = str(self.root)
        self.c['atbench_path'] = str(self.root / 'ATBench.json')
    def tearDown(self):
        self.temp.cleanup()
    def test_agentharm_view_excludes_grader_and_category(self):
        for kind in ['harmful', 'benign']:
            for split in ['test_public', 'validation']:
                write(self.root / 'agentharm/snapshot/benchmark' / f'{kind}_behaviors_{split}.json',
                    {'behaviors': [{'id': split, 'id_original': 'base', 'prompt': 'request',
                                    'category': 'LABEL_LEAK', 'grading_function': 'GOLD_LEAK'}]})
        records = load_static(self.c, 'agentharm')
        self.assertEqual(len(records), 4)
        self.assertEqual({x['gold'] for x in records}, {0, 1})
        self.assertEqual(records[0]['view'], {'user_request': 'request'})
    def test_atbench_preserves_structured_calls_without_gold(self):
        call = {'role': 'assistant', 'tool_calls': [{'name': 'transfer', 'args': {'amount': 5}}]}
        write(self.root / 'ATBench.json', [{'id': 1, 'contents': [[call]], 'tool_used': [],
                                          'label': 1, 'reason': 'GOLD_LEAK'}])
        record = load_static(self.c, 'atbench')[0]
        self.assertEqual(record['view']['trajectory'], [[call]])
        self.assertNotIn('GOLD_LEAK', json.dumps(record['view']))
    def test_mcphunt_excludes_detector_flags_future_outcome_and_usage(self):
        self.c['datasets']['mcphunt']['files'] = ['main/test.json']
        write(self.root / 'mcphunt/snapshot/main/test.json', {'traces': [{'trace_id': 't', 'task_id': 'family',
            'task_prompt': 'request', 'messages': [{'role': 'user', 'content': 'visible'}],
            'events': [{'canary_in_result': True}], 'labeling': {'any_risk': True},
            'measurement': {'prompt_tokens': 123}, 'outcome': 'GOLD_LEAK'}]})
        record = load_static(self.c, 'mcphunt')[0]
        self.assertEqual(set(record['view']), {'user_request', 'messages'})
        self.assertEqual(record['gold'], 1)
    def test_missing_selected_id_is_not_silently_skipped(self):
        write(self.root / 'ATBench.json', [{'id': 1, 'contents': [], 'tool_used': [], 'label': 0}])
        self.c['datasets']['atbench']['item_ids'] = ['not-present']
        with self.assertRaises(ValueError):
            load_static(self.c, 'atbench')
    def test_source_label_cannot_be_downcast_to_action(self):
        self.c['datasets']['mcphunt']['contract'] = 'pre_action_authorization'
        with self.assertRaises(ValueError):
            load_static(self.c, 'mcphunt')


class ContractTests(unittest.TestCase):
    def test_A2_cannot_relabel_pre_action_gate_as_input_inspection(self):
        c = fixture_config()
        c['datasets']['agentdojo']['mode_code'] = 'A2'
        result = inspect(c, check_keys=False)
        self.assertTrue(any('cannot be relabeled A2' in x for x in result['issues']))
    def test_jev_request_has_exact_safe_unsafe_choice(self):
        c = fixture_config()
        question = request(c, 'jev', {'user_request':'TEST'}, 'TEST QUESTION')['questions']['risk']
        self.assertEqual(question['type'], 'choice')
        self.assertEqual(list(question['criteria']), ['safe', 'unsafe'])
        self.assertEqual(question['instructions'], 'TEST QUESTION')
    def test_jev_choice_maps_labels_without_probability_threshold(self):
        class ResponseFixture:
            answer = None
            def post(self, *args):
                return {'answers': {'risk': self.answer}}
        transport, c = ResponseFixture(), fixture_config()
        judge = Judge(c, 'jev', transport)
        for choice, expected in [('safe', 0), ('unsafe', 1)]:
            transport.answer = {'type':'choice', 'choice':choice}
            self.assertEqual(judge.judge({}, 'request_risk_classification', 'fixture'), expected)
        for invalid in [{'type':'noul', 'noul':.9}, {'type':'choice', 'choice':'review'}, {},
                        {'type':'choice', 'probabilities':{'safe':.1, 'unsafe':.9}}]:
            transport.answer = invalid
            with self.assertRaises(ValueError):
                judge.judge({}, 'request_risk_classification', 'fixture')
    def test_live_credential_in_config_is_rejected_without_echo(self):
        c = fixture_config()
        c['main_agent_system_prompt'] = 'ACCIDENTAL_FIXTURE_KEY'
        with patch.dict(os.environ, {'OPENAI_API_KEY':'ACCIDENTAL_FIXTURE_KEY'}):
            result = inspect(c, check_keys=False)
        self.assertTrue(any('live credential' in x for x in result['issues']))
        self.assertNotIn('ACCIDENTAL_FIXTURE_KEY', json.dumps(result))
    def test_template_fails_closed_without_calling_network(self):
        result = inspect(read(ROOT / 'configs/security-bench.template.json'), check_keys=False)
        self.assertEqual(result['status'], 'not_ready')
        self.assertEqual(result['network_calls'], 0)
    def test_same_serialized_state_for_both_safety_models(self):
        c, state = fixture_config(), {'untrusted': 'content', 'user_request': 'task'}
        a = request(c, 'jev', state, 'same question')['state']
        b = request(c, 'gpt6luna', state, 'same question')['input'][0]['content']
        self.assertEqual(a, b)
    def test_incomplete_llm_output_is_not_a_valid_prediction(self):
        with self.assertRaises(ValueError):
            output_text({'status': 'incomplete', 'output': []})
    def test_report_excludes_errors_from_confusion_but_includes_cost_and_latency(self):
        rs = []
        for i, (g, p, status) in enumerate([(1, 1, 'ok'), (0, 1, 'ok'), (0, 0, 'ok'), (1, 0, 'ok'), (1, 1, 'failed')]):
            rs.append({'dataset_id': 'atbench', 'status': status, 'gold': g, 'prediction': p,
                'wall_seconds': 2, 'monitor_run_id': 'm', 'monitor_event_start': i, 'monitor_event_end': i + 1})
        event = {'estimated_cost_usd': None, 'provider': 'test', 'model': 'test', 'input_tokens': None, 'output_tokens': None}
        s = summarize(6, rs, {'m': [event] * 5})
        self.assertEqual([s['classification'][k] for k in ['TP','FP','TN','FN']], [1,1,1,1])
        self.assertEqual(s['time']['episode_seconds_sum'], 10)
        self.assertEqual(s['resources']['calls'], 5)
        self.assertIsNone(s['resources']['api_fee_usd_price_estimated'])


class RealEnvironmentTests(unittest.TestCase):
    def test_gate_blocks_before_side_effect_and_arms_get_fresh_state(self):
        c = fixture_config()
        try:
            from security_bench.dojo import suites, run_episode
            suites(c)
        except (ImportError, ModuleNotFoundError):
            self.skipTest('Run with .venv-benchmark for actual upstream environment checks')
        class MainAgentFixture:
            def __init__(self):
                self.calls = 0
            def check_budget(self):
                pass
            def post(self, *args):
                self.calls += 1
                if self.calls == 1:
                    return {'choices': [{'finish_reason': 'tool_calls', 'message': {'role': 'assistant', 'content': '', 'tool_calls': [
                        {'id': 'call_fixture', 'type': 'function', 'function': {'name': 'send_money',
                         'arguments': json.dumps({'recipient':'TEST', 'amount':1, 'subject':'TEST', 'date':'2026-10-27'})}}]}}]}
                return {'choices': [{'finish_reason':'stop', 'message': {'role':'assistant', 'content':'finished'}}]}
        class JudgeFixture:
            def __init__(self, risk):
                self.risk = risk
            def judge(self, state, *args):
                assert 'gold' not in state
                assert 'post_environment' not in state
                return self.risk
        case = {'suite':'banking', 'user_task_id':'user_task_0', 'injections':{}, 'injection_task_id':None}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            blocked = run_episode(c, case, JudgeFixture(1), MainAgentFixture(), 'blocked', root)
            allowed = run_episode(c, case, JudgeFixture(0), MainAgentFixture(), 'allowed', root)
            b0 = read(root/'traces/blocked.initial.json')['bank_account']['transactions']
            b1 = read(root/'traces/blocked.final.json')['environment']['bank_account']['transactions']
            a0 = read(root/'traces/allowed.initial.json')['bank_account']['transactions']
            a1 = read(root/'traces/allowed.final.json')['environment']['bank_account']['transactions']
            self.assertEqual(b0, b1)
            self.assertEqual(b0, a0)
            self.assertEqual(len(a1), len(a0) + 1)
            self.assertEqual(blocked['blocked_actions'], 1)
            self.assertEqual(allowed['blocked_actions'], 0)


if __name__ == '__main__':
    unittest.main()
