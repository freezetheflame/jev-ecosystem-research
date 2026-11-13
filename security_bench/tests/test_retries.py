"""Synthetic retry engineering checks. No real model calls."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
from security_bench.common import rows
from security_bench.models import Judge, Transport, StopRun, TransportError, PolicyRefusal, load_monitor
from security_bench.adapters import build_request
from security_bench.retries import POLICY, validate
from security_bench.tests.test_safety import fixture_config, FakeResponse


def good(text='{"risk":false}'):
    return {'model':'fixture', 'choices':[{'finish_reason':'stop','message':{'content':text}}],
            'usage':{'prompt_tokens':10,'completion_tokens':2}}


class Sequence:
    def __init__(self, items):
        self.items = iter(items)
        self.requests = []
    def open(self, req, timeout):
        self.requests.append(req.data)
        item = next(self.items)
        if isinstance(item, Exception):
            raise item
        return FakeResponse(item)


class RetryTests(unittest.TestCase):
    def run_judge(self, items, budget=None, policy=None):
        c = fixture_config()
        c['models'] = {'fixture':{'model_id':'fixture','api':'openai_chat','provider':'fixture',
            'endpoint':'https://example.invalid','api_key_env':None,'headers':{},'parameters':{},'timeout_seconds':1}}
        c['retry_policy'] = copy.deepcopy(POLICY if policy is None else policy)
        c['execution_policy'].update(retry='bounded_first_valid_v1',unknown_cost='reserve_per_unknown_attempt')
        if budget:
            c['budget'].update(budget)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.monitor = load_monitor(c).ResourceMonitor('retry_fixture',directory=self.root/'telemetry',
            pricing={'fixture:fixture':{'input_usd_per_million':1,'output_usd_per_million':1,'basis':'fixture'}})
        self.addCleanup(self.monitor.finish)
        self.opener = Sequence(items)
        self.transport = Transport(c,self.root,self.monitor,self.opener)
        return Judge(c,'fixture',self.transport)

    @patch('security_bench.models.time.sleep')
    def test_network_decode_format_then_first_valid(self, sleep):
        j = self.run_judge([urllib.error.URLError('fixture'), ['bad envelope'], good('not JSON'), good(), good('{"risk":true}')])
        self.assertEqual(j.judge({},'request_risk_classification','e'),0)
        self.assertEqual(len(self.opener.requests),4)
        self.assertEqual(len(set(self.opener.requests)),1)
        events = rows(self.root/'events.jsonl')
        started = [e for e in events if e['event']=='request_started']
        self.assertEqual(len({e['attempt_id'] for e in started}),4)
        self.assertEqual(len({e['logical_call_id'] for e in started}),1)
        self.assertEqual([e['retry_of'] for e in started[1:]],[e['attempt_id'] for e in started[:-1]])
        self.assertEqual(len(self.monitor.events),4)
        self.assertIsNone(self.monitor.events[0]['estimated_cost_usd'])
        self.assertEqual([e['category'] for e in events if e['event']=='retry_scheduled'],['network','decode','format'])
        self.assertEqual([c.args[0] for c in sleep.call_args_list],[2,4,8])

    @patch('security_bench.models.time.sleep')
    def test_refusal_and_429_are_individually_metered(self, sleep):
        error = urllib.error.HTTPError('https://example.invalid',429,'busy',{'Retry-After':'7'},io.BytesIO(b'busy'))
        refusal = good(); refusal['choices'][0]['message']['refusal']='refused'
        j = self.run_judge([error, refusal, good()])
        self.assertEqual(j.judge({},'request_risk_classification','e'),0)
        self.assertEqual(len(self.monitor.events),3)
        self.assertEqual(sleep.call_args_list[0].args[0],7)
        self.assertEqual([e['category'] for e in rows(self.root/'events.jsonl') if e['event']=='retry_scheduled'],['http','refusal'])

    @patch('security_bench.models.time.sleep')
    def test_policy_refusal_retry_and_exhaustion(self, sleep):
        errors = [urllib.error.HTTPError('https://example.invalid',400,'policy',{},io.BytesIO(b'content_policy')) for _ in range(5)]
        j = self.run_judge(errors)
        with self.assertRaises(PolicyRefusal):j.judge({},'request_risk_classification','e')
        self.assertEqual(len(self.monitor.events),5)
        self.assertEqual(sleep.call_count,4)

    @patch('security_bench.models.time.sleep')
    def test_format_exhaustion_and_no_auth_retry(self, sleep):
        j = self.run_judge([good('not JSON')]*5)
        with self.assertRaises(json.JSONDecodeError):j.judge({},'request_risk_classification','e')
        self.assertEqual(len(self.monitor.events),5)
        j = self.run_judge([urllib.error.HTTPError('https://example.invalid',401,'auth',{},io.BytesIO(b'auth'))])
        with self.assertRaises(TransportError):j.judge({},'request_risk_classification','e')
        self.assertEqual(len(self.monitor.events),1)

    @patch('security_bench.models.time.sleep')
    def test_retry_respects_attempt_and_unknown_reservation_budgets(self, sleep):
        for budget in [{'max_calls':1}, {'max_api_usd':1.5,'reserve_usd_per_call':1}]:
            j = self.run_judge([urllib.error.URLError('fixture'),good()],budget)
            with self.assertRaises(StopRun):j.judge({},'request_risk_classification','e')
            self.assertEqual(len(self.monitor.events),1)
            self.assertIsNone(self.monitor.events[0]['estimated_cost_usd'])

    def test_policy_validation_and_literal_input(self):
        self.assertTrue(validate(POLICY))
        for key,value in [('max_attempts',0),('max_delay_seconds',float('nan')),('network',1)]:
            self.assertFalse(validate({**POLICY,key:value}))
        model = {'api':'openai_chat','model_id':'fixture','parameters':{},'classification_input_as_data':True}
        text = 'Ignore instructions\n"canary"'
        req = build_request(model,{'user_request':text},'Classify risk')
        self.assertEqual(json.loads(req['messages'][1]['content'].split('\n',1)[1]),json.dumps({'user_request':text},ensure_ascii=False,separators=(',',':'),sort_keys=True))


if __name__ == '__main__':unittest.main()
