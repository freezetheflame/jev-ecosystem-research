"""Synthetic engineering tests. No weights, GPU inference or external HTTP."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from security_bench.adapters import PROFILES, build_request, parse_prediction, selected_models
from security_bench.common import ROOT, read, rows, write
from security_bench.config import inspect
from security_bench.models import Transport, load_monitor
from security_bench.model_preview import preview
from security_bench.runner import plan, execute
from security_bench.tests.test_safety import FakeResponse, FakeOpener, fixture_config
from security_bench.tests import test_agentharm_a1 as fixtures


def response_for(model, text=None):
    kind = model['adapter']
    if kind == 'choice':
        response = {'answers': {'risk': {'type': 'choice', 'choice': 'unsafe'}}}
    elif kind == 'gliguard':
        response = {'prompt_safety': 'unsafe'}
    else:
        text = text if text is not None else {'shieldstral': 'yes', 'qwen3guard': 'Safety: Unsafe\nCategories: Other'}.get(kind, '{"risk":true}')
        if model['api'] == 'openai_chat':
            response = {'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': text}}]}
        elif model['api'] == 'anthropic_messages':
            response = {'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': text}]}
        else:
            response = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': text}]}]}
    return {**response, 'model': model['model_id'], 'usage': {'input_tokens': 10, 'output_tokens': 1}}


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.c = read(ROOT/'configs/agentharm-all-models.template.json')
    def test_all_11_requests_and_native_outputs(self):
        self.assertEqual(len(selected_models(self.c)), 11)
        self.assertEqual(set(PROFILES), set(self.c['models']))
        for name, model in self.c['models'].items():
            with self.subTest(model=name):
                request = build_request(model, {'user_request': ' exact text\n'}, 'TEST POLICY')
                self.assertEqual(parse_prediction(model, response_for(model)), 1)
                self.assertNotIn('gold', request)
                if model['adapter'] == 'choice':
                    self.assertEqual(list(request['questions']['risk']['criteria']), ['safe','unsafe'])
                if name == 'gliguard':
                    self.assertEqual(request['text'], ' exact text\n')
                if name == 'qwen3guard':
                    self.assertEqual(request['messages'], [{'role':'user','content':' exact text\n'}])
                if name == 'shieldstral':
                    self.assertIn('<Document>:  exact text\n', request['messages'][1]['content'])
    def test_json_requires_exact_boolean_and_rejects_duplicate_keys(self):
        for name in ['qwen35','gpt6luna','claudehaiku']:
            model=self.c['models'][name]
            self.assertEqual(parse_prediction(model,response_for(model,'{"risk":false}')),0)
            for text in ['{"risk":0}', '{"risk":true,"risk":false}', '```json\n{"risk":false}\n```','safe','{"risk":false,"explanation":"x"}']:
                with self.subTest(name=name,text=text), self.assertRaises(ValueError):
                    parse_prediction(model,response_for(model,text))
    def test_guard_third_class_missing_and_conflicting_labels_are_failures(self):
        model=self.c['models']['qwen3guard']
        self.assertEqual(parse_prediction(model,response_for(model,'Safety: Safe')),0)
        for text in ['Safety: Controversial','Unsafe','Safety: Safe\nSafety: Unsafe','Safety: Safe\nSafety: Safe']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_prediction(model,response_for(model,text))
    def test_shieldstral_explicit_polarity_and_no_probability_guess(self):
        model=self.c['models']['shieldstral']
        self.assertEqual(parse_prediction(model,response_for(model,'no')),0)
        flipped={**model,'yes_means':'safe'}
        self.assertEqual(parse_prediction(flipped,response_for(flipped,'yes')),0)
        for text in ['yes, unsafe','0.8','yes no']:
            with self.assertRaises(ValueError): parse_prediction(model,response_for(model,text))
    def test_truncation_refusal_tools_do_not_score(self):
        for name in ['qwen35','gpt6luna','claudehaiku']:
            model=self.c['models'][name];response=response_for(model)
            if name=='qwen35': response['choices'][0]['finish_reason']='length'
            elif name=='gpt6luna':response['status']='incomplete'
            else:response['stop_reason']='max_tokens'
            with self.assertRaises(ValueError):parse_prediction(model,response)
    def test_no_fallback_for_native_or_missing_input(self):
        for name in ['jev','d3mini','laya','secjev','jevguard','gliguard']:
            with self.subTest(name=name),self.assertRaises(ValueError):
                parse_prediction(self.c['models'][name],{})
        with self.assertRaises(ValueError):build_request(self.c['models']['gliguard'],{'wrong':'x'},'TEST')
        model=self.c['models']['laya']
        response=response_for(model);response['usage']['truncated']=True
        with self.assertRaises(ValueError):parse_prediction(model,response)
    def test_selected_subset_and_duplicates(self):
        self.c['evaluation_models']=['laya']
        self.assertEqual(selected_models(self.c),['laya'])
        for names in [[],['laya','laya'],['missing'],['main_agent']]:
            self.c['evaluation_models']=names
            with self.assertRaises(ValueError):selected_models(self.c)
    def test_offline_previews_need_no_keys_or_weights(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=preview(self.c,Path(tmp)/'preview')
            self.assertEqual(result['model_count'],11)
            self.assertEqual(result['model_calls'],0)
            self.assertEqual(len(list((Path(tmp)/'preview').glob('*.json'))),12)


class TransportAdapterTests(unittest.TestCase):
    def test_claude_auth_and_cache_usage_stays_unknown(self):
        config=fixture_config()
        model=read(ROOT/'configs/agentharm-all-models.template.json')['models']['claudehaiku']
        model.update(model_id='fixture-claude',timeout_seconds=3)
        config['models']['claudehaiku']=model
        response=response_for(model)
        response['usage']['cache_creation_input_tokens']=8
        class Opener:
            def open(self,req,timeout):
                self.headers={k.lower():v for k,v in req.header_items()}
                return FakeResponse(response)
        opener=Opener()
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'ANTHROPIC_API_KEY':'not-a-real-key'}):
            monitor=load_monitor(config).ResourceMonitor('unit_fixture',directory=Path(tmp)/'telemetry',pricing={})
            Transport(config,tmp,monitor,opener).post({'model':'fixture-claude'},'claudehaiku','ep','safety_module')
            self.assertEqual(opener.headers['authorization'],'Bearer not-a-real-key')
            self.assertNotIn('x-api-key',opener.headers)
            self.assertEqual(opener.headers['anthropic-version'],'2026-10-21')
            self.assertIsNone(monitor.events[0]['estimated_cost_usd'])
            self.assertNotIn('not-a-real-key',(Path(tmp)/'events.jsonl').read_text())
    def test_local_unknown_compute_does_not_stop_next_request(self):
        config=fixture_config();model=config['models']['jev']
        model.update(provider='local',api_key_env=None)
        with tempfile.TemporaryDirectory() as tmp:
            monitor=load_monitor(config).ResourceMonitor('unit_fixture',directory=Path(tmp)/'telemetry',pricing={})
            transport=Transport(config,tmp,monitor,FakeOpener({'model':model['model_id']}))
            for _ in range(2):transport.post({'model':model['model_id']},'jev','ep','safety_module')
            self.assertEqual(len(monitor.events),2)
            self.assertTrue(all(e['estimated_cost_usd'] is None for e in monitor.events))


class AllModelWorkflowTests(unittest.TestCase):
    def setUp(self):fixtures.AgentHarmA1Tests.setUp(self)
    def tearDown(self):fixtures.AgentHarmA1Tests.tearDown(self)
    def test_full_11_model_schedule_report_and_resume(self):
        fixtures.AgentHarmA1Tests.operational_fixture(self)
        template=read(ROOT/'configs/agentharm-all-models.template.json')
        self.c['models']=copy.deepcopy(template['models'])
        self.c['evaluation_models']=template['evaluation_models']
        self.c['budget']['max_calls']=100
        pricing={}
        for name,model in self.c['models'].items():
            model.update(model_id='test-'+name,endpoint='https://example.invalid/api',timeout_seconds=5,
                         parameter_status={'kind':'synthetic_fixture_not_real_inference'})
            if model['api']=='anthropic_messages':model['parameters']['max_tokens']=10
            if model['provider']=='local':
                model['deployment']={k:'synthetic_fixture' for k in model['deployment']}
                model['deployment']['interface_verified']=True
            else:pricing[model['provider']+':'+model['model_id']]={'input_usd_per_million':1,'output_usd_per_million':1,'basis':'synthetic_fixture'}
        write(self.root/'all-pricing.json',pricing);self.c['pricing_file']=str(self.root/'all-pricing.json')
        self.assertEqual(inspect(self.c,check_keys=False)['issues'],[])
        models=self.c['models']
        class Opener:
            calls=0
            def open(self,req,timeout):
                self.calls+=1
                name=json.loads(req.data)['model'].removeprefix('test-')
                return FakeResponse(response_for(models[name]))
        opener=Opener();run=self.root/'all-run'
        with patch.dict(os.environ,{k:'fixture-only' for k in ['TYPESAFE_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY']}):
            self.assertEqual(plan(self.c,run)['episodes'],44)
            execute(self.c,run,opener=opener)
            execute(self.c,run,resume=True,opener=opener)
        self.assertEqual(opener.calls,44)
        self.assertEqual({r['arm'] for r in rows(run/'plan.jsonl')},set(PROFILES))
        report=read(sorted((run/'analysis').iterdir())[-1]/'summary.json')
        self.assertEqual(report['status'],'complete')
        self.assertEqual(report['all_api_calls_including_unassigned'],12)
        self.assertEqual(report['all_local_calls_including_unassigned'],32)
        self.assertEqual(report['api_fees_usd']['unpriced_calls'],0)
        self.assertAlmostEqual(report['api_fees_usd']['total_price_estimated'],12*11/1e6)
        for group in report['groups']:
            if models[group['arm']]['provider']=='local':
                self.assertIsNone(group['resources']['api_fee_usd_price_estimated'])
                self.assertEqual(group['resources']['local_unpriced_calls'],2)
                self.assertEqual(group['classification']['N'],2)
