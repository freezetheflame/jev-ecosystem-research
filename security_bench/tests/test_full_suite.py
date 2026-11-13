import json
import tempfile
import unittest
import io
import urllib.error
from pathlib import Path
from security_bench.full_datasets import load_new, run_prefix
from security_bench.report import summarize


class FullSuiteTests(unittest.TestCase):
    def test_step_key_separation_and_prefix_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'data/test/scrubbed').mkdir(parents=True)
            (root/'data/test/mapping').mkdir()
            native={'task':{'title':'repair','description':'repair project','constraints':['no secrets']},
                'trajectory_type':'DO_NOT_SEND','steps':[
                    {'step':1,'thought':'inspect','action':'read','arguments':{},'observation':'public','label':None,'rationale':'SECRET_GOLD'},
                    {'step':2,'thought':'bad','action':'send','arguments':{},'observation':'sent','label':'INV','continuation':False},
                    {'step':3,'thought':'FUTURE_CANARY','action':'done','arguments':{},'observation':'done'}]}
            (root/'data/test/scrubbed/a.jsonl').write_text(json.dumps(native))
            (root/'data/test/mapping/answer_key.jsonl').write_text(json.dumps({'id':'a','trajectory_type':'rogue','rogue_step':2})+'\n')
            c={'datasets':{'stepshield':{'splits':['test'],'mode_code':'C'}}}
            case=load_new(c,'stepshield',root)[0]
            self.assertEqual(case['gold'],1)
            self.assertNotIn('SECRET_GOLD',json.dumps(case['view']))
            self.assertNotIn('trajectory_type',case['view'])
            class Judge:
                def __init__(self):self.views=[]
                def judge(self,view,*args):
                    self.views.append(view)
                    return int(len(self.views)==2)
            j=Judge();result=run_prefix(case,j,'episode')
            self.assertEqual(result['detection_step'],2)
            self.assertEqual(len(j.views),2)
            self.assertNotIn('FUTURE_CANARY',json.dumps(j.views))
            self.assertEqual(j.views[0]['history'],[])
            (root/'data/test/mapping/answer_key.jsonl').write_text('')
            with self.assertRaises(ValueError):load_new(c,'stepshield',root)

    def test_wildguard_unknown_labels_and_no_response_leakage(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'test').mkdir()
            data=[{'prompt':'prompt'+str(i),'prompt_harm_label':label,'response':'RESPONSE_CANARY','response_harm_label':'harmful'} for i,label in enumerate(['harmful','unharmful',None])]
            pq.write_table(pa.Table.from_pylist(data),root/'test/wildguard_test.parquet')
            cases=load_new({'datasets':{'wildguardtest':{'mode_code':'A1'}}},'wildguardtest',root)
            self.assertEqual([c['gold'] for c in cases],[1,0,None])
            self.assertNotIn('RESPONSE_CANARY',json.dumps([c['view'] for c in cases]))
            self.assertEqual(cases[0]['gold_source'],'native_prompt_harm_label')

    def test_wildguard_response_mode_e_uses_response_harm_and_keeps_labels_out_of_view(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'test').mkdir()
            data=[
                {'prompt':'prompt0','prompt_harm_label':'harmful','response':'RESPONSE_SAFE','response_harm_label':'unharmful','response_refusal_label':'refusal'},
                {'prompt':'prompt1','prompt_harm_label':'unharmful','response':'RESPONSE_HARM','response_harm_label':'harmful','response_refusal_label':'compliance'},
                {'prompt':'prompt2','prompt_harm_label':'harmful','response':'RESPONSE_UNKNOWN','response_harm_label':None,'response_refusal_label':'refusal'},
            ]
            pq.write_table(pa.Table.from_pylist(data),root/'test/wildguard_test.parquet')
            cases=load_new({'datasets':{'wildguardtest-response':{'mode_code':'E','contract':'response_risk_classification'}}},'wildguardtest-response',root)
            self.assertEqual([c['gold'] for c in cases],[0,1,None])
            self.assertEqual(cases[0]['gold_source'],'native_response_harm_label')
            self.assertEqual(cases[0]['evaluation_mode'],'E')
            self.assertEqual(cases[0]['view']['user_request'],'prompt0')
            self.assertEqual(cases[0]['view']['assistant_response'],'RESPONSE_SAFE')
            self.assertEqual(cases[1]['view']['assistant_response'],'RESPONSE_HARM')
            views=json.dumps([c['view'] for c in cases])
            self.assertNotIn('prompt_harm_label',views)
            self.assertNotIn('response_harm_label',views)
            self.assertNotIn('response_refusal_label',views)
            self.assertNotIn('refusal',views)
            self.assertNotIn('GOLD',views)
            # Mode A1 path must remain unchanged and must not see the response.
            a1=load_new({'datasets':{'wildguardtest':{'mode_code':'A1','contract':'request_risk_classification'}}},'wildguardtest',root)
            self.assertEqual([c['gold'] for c in a1],[1,0,1])
            self.assertNotIn('RESPONSE_SAFE',json.dumps([c['view'] for c in a1]))
            self.assertNotIn('assistant_response',json.dumps([c['view'] for c in a1]))

    def test_missing_predictions_not_imputed(self):
        r={'status':'ok','gold':1,'prediction':1,'monitor_run_id':'x','monitor_event_start':0,'monitor_event_end':0,'dataset_id':'injecagent','wall_seconds':1}
        out=summarize(2,[r],{})['classification']
        self.assertEqual(out['N'],1)
        self.assertEqual(out['correct_completion_rate_all_assigned'],.5)
        self.assertIsNone(out['fpr'])

    def test_known_local_overflow_remains_metered_failure(self):
        from security_bench.tests.test_safety import fixture_config, FakeOpener
        from security_bench.models import Transport, ContextRejected, TransportError, load_monitor
        from security_bench.common import rows
        c=fixture_config()
        c['record_kind']='full_public_descriptive_evaluation_v1'
        c['models']={'local':{'api':'jev','provider':'local','model_id':'fixture','endpoint':'http://127.0.0.1:9/predict','api_key_env':None,'headers':{},'timeout_seconds':1}}
        with tempfile.TemporaryDirectory() as tmp:
            monitor=load_monitor(c).ResourceMonitor('fixture',directory=Path(tmp)/'telemetry',pricing={})
            error=urllib.error.HTTPError('http://127.0.0.1:9',400,'Bad request',{},io.BytesIO(b'{"detail":"State plus question exceeds 8192; no truncation"}'))
            transport=Transport(c,tmp,monitor,opener=FakeOpener(error))
            with self.assertRaises(ContextRejected):transport.post({'state':'fixture'},'local','e','safety_module')
            self.assertEqual(len(monitor.events),1)
            self.assertEqual(monitor.events[0]['error_type'],'ContextRejected')
            self.assertEqual(rows(Path(tmp)/'events.jsonl')[-1]['event'],'request_finished')
            monitor.finish()


if __name__=='__main__':unittest.main()
