"""Standalone AgentHarm A1 adapter checks; no real model calls."""
import csv
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from security_bench.common import ROOT, digest, file_hash, read, rows, write
from security_bench.config import inspect
from security_bench.datasets import load_static, paths
from security_bench.runner import plan, execute, data_hashes
from security_bench.agentharm import inspect_inputs
from security_bench.tests.test_safety import FakeResponse


class AgentHarmA1Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.c = read(ROOT/'configs/agentharm-a1.template.json')
        self.c['data_root'] = str(self.root)
        self.c['datasets']['agentharm'].update(splits=['validation','test_public'], exposure_status='synthetic_test_fixture')
        snapshot = self.root/'agentharm/snapshot'
        files = []
        for split in ['validation','test_public']:
            for kind in ['harmful','benign']:
                path = snapshot/'benchmark'/f'{kind}_behaviors_{split}.json'
                write(path, {'behaviors':[{'id':split+'-1', 'id_original':split+'-base',
                    'prompt':' TEST user request '+split+'\n', 'category':'LABEL_LEAK',
                    'grading_function':'GRADER_LEAK', 'target_functions':['TOOL_LEAK']}]})
                files.append({'path':str(path.relative_to(snapshot.parent)).replace('\\','/'),
                              'sha256':file_hash(path),'bytes':path.stat().st_size})
        write(snapshot.parent/'manifest.json', {'revision':self.c['datasets']['agentharm']['source_revision'], 'files':files})
    def tearDown(self):
        self.temporary.cleanup()
    def operational_fixture(self):
        self.c.update(phase='pilot',repeats=1,schedule_seed=7)
        self.c['budget']={'max_calls':50,'max_wall_seconds':100,'max_api_usd':100,'reserve_usd_per_call':1}
        pricing={}
        for name,m in self.c['models'].items():
            m.update(model_id='test-'+name,timeout_seconds=5,parameter_status={'server_defaults':'unknown_default'})
            pricing[m['provider']+':'+m['model_id']]={'input_usd_per_million':1,
                'output_usd_per_million':1,'basis':'synthetic_test_only_not_actual_prices'}
        write(self.root/'pricing.json',pricing)
        self.c['pricing_file']=str(self.root/'pricing.json')
    def test_native_prompt_preserved_and_labels_separate(self):
        records=load_static(self.c,'agentharm')
        self.assertEqual(len(records),4)
        self.assertEqual({r['source_split'] for r in records},{'validation','test_public'})
        for r in records:
            self.assertEqual(set(r['view']),{'user_request'})
            self.assertTrue(r['view']['user_request'].startswith(' TEST'))
            self.assertTrue(r['view']['user_request'].endswith('\n'))
            self.assertNotIn('LEAK',json.dumps(r['view']))
            self.assertEqual(r['gold'],int(r['source_partition']=='harmful'))
    def test_invalid_duplicate_or_private_split_rejected(self):
        for splits in [None,[],['validation','validation'],['private'], 'validation']:
            self.c['datasets']['agentharm']['splits']=splits
            with self.assertRaises(ValueError):
                load_static(self.c,'agentharm')
    def test_hashes_and_paths_touch_only_selected_source_files(self):
        self.c['datasets']['agentharm']['splits']=['validation']
        self.assertEqual(set(paths(self.c)),{'agentharm'})
        hashes=data_hashes(self.c)
        self.assertEqual(len(hashes),2)
        self.assertTrue(all('validation' in p for p in hashes))
    def test_offline_export_needs_no_credentials_or_other_benchmarks(self):
        result=inspect_inputs(self.c,self.root/'prepared',['validation'])
        self.assertEqual(result['items'],2)
        req=read(self.root/'prepared/jev-request-example.json')
        self.assertEqual(req['questions']['risk']['type'],'choice')
        self.assertEqual(list(req['questions']['risk']['criteria']),['safe','unsafe'])
        self.assertEqual(set(json.loads(req['state'])),{'user_request'})
        self.assertEqual(read(self.root/'prepared/manifest.json')['model_calls'],0)
    def test_single_dataset_run_reports_splits_and_never_replays(self):
        self.operational_fixture()
        self.assertEqual(inspect(self.c,check_keys=False)['issues'],[])
        class Opener:
            calls=0
            def open(self,req,timeout):
                self.calls+=1
                body=json.loads(req.data)
                if 'state' in body:
                    view=json.loads(body['state'])
                else:
                    view=json.loads(body['input'][0]['content'])
                assert set(view)=={'user_request'}
                result={'model':body['model'],'usage':{'input_tokens':2,'output_tokens':1}}
                if body['model']=='test-jev':
                    result['answers']={'risk':{'type':'choice','choice':'unsafe'}}
                else:
                    result.update(status='completed',output=[{'type':'message','content':[{'type':'output_text','text':'{"risk":true}'}]}])
                return FakeResponse(result)
        opener=Opener()
        with patch.dict(os.environ,{'TYPESAFE_API_KEY':'fixture-only','OPENAI_API_KEY':'fixture-only'}):
            run=self.root/'run'
            prepared=plan(self.c,run)
            self.assertEqual(prepared['episodes'],8)
            execute(self.c,run,opener=opener)
            self.assertEqual(opener.calls,8)
            execute(self.c,run,resume=True,opener=opener)
            self.assertEqual(opener.calls,8)
        analysis=sorted((run/'analysis').iterdir())[-1]
        report=read(analysis/'summary.json')
        self.assertEqual(len(report['groups']),4)
        self.assertEqual({g['split'] for g in report['groups']},{'validation','test_public'})
        self.assertTrue(all(g['dataset']=='agentharm' for g in report['groups']))
        self.assertTrue(all(g['classification']['N']==2 for g in report['groups']))
        with (analysis/'predictions.csv').open(encoding='utf-8',newline='') as f:
            predictions=list(csv.DictReader(f))
        self.assertEqual(len(predictions),8)
        self.assertEqual({r['predicted_label'] for r in predictions},{'unsafe'})
        self.assertTrue(all(e['component']=='safety_module' for e in rows(run/'events.jsonl') if e['event']=='request_started'))
    def test_only_classifier_contract_is_required_for_A1(self):
        result=inspect(self.c,check_keys=False)
        self.assertFalse(any(x in issue for issue in result['issues']
                             for x in ['DeepSeek','agentdojo','mcphunt','atbench','skill_risk_classification']))
