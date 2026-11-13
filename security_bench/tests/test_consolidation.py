"""Synthetic aggregation fixtures only; never calls inference or regrades model text."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.consolidate_agentharm_models import majority, model_data, token_summary, full_sample_performance


class ConsolidationTests(unittest.TestCase):
    def test_missing_and_tied_votes_stay_unresolved(self):
        self.assertIsNone(majority([]))
        self.assertIsNone(majority([0,1]))
        self.assertEqual(majority([1]),1)
        self.assertEqual(majority([0,1,1]),1)

    def test_call_costs_follow_monitor_identity_and_include_failed_episodes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'telemetry').mkdir()
            config={'phase':'pilot','repeats':3,'models':{'fixture':{'display_name':'Fixture','provider':'fixture_api'}},
                    'contracts':{'request_risk_classification':{'label_semantics':'SYNTHETIC ONLY'}}}
            (root/'effective-config.json').write_text(json.dumps(config))
            cases=[{'item_id':'a','gold':0,'input_sha256':'fixture-a','family_id':'family'},
                   {'item_id':'b','gold':1,'input_sha256':'fixture-b','family_id':'family'}]
            episodes=[{'arm':'fixture','item_id':'a','gold':0,'prediction':0,'status':'ok','repeat':0,
                       'monitor_run_id':'z','monitor_event_start':0,'monitor_event_end':1,'wall_seconds':.2},
                      {'arm':'fixture','item_id':'b','gold':1,'prediction':None,'status':'failed','repeat':0,
                       'monitor_run_id':'a','monitor_event_start':0,'monitor_event_end':1,'wall_seconds':.8}]
            for name,data in [('cases.jsonl',cases),('episodes.jsonl',episodes),('plan.jsonl',episodes)]:
                (root/name).write_text('\n'.join(json.dumps(x) for x in data)+'\n')
            for identity,cost in [('z',.2),('a',.5)]:
                (root/'telemetry'/f'{identity}.calls.jsonl').write_text(json.dumps({'provider':'fixture_api',
                    'estimated_cost_usd':cost,'input_tokens':1,'output_tokens':1})+'\n')
            result,*_=model_data(root,'fixture')
            self.assertAlmostEqual(result['resources']['known_api_fee_usd_price_estimated'],.7)
            self.assertEqual(result['scorable_items'],1)
            self.assertEqual(result['missing_or_tied_items'],['b'])
            self.assertEqual(result['all_50_accuracy_bounds'],[.5,1.0])


class TokenSummaryTests(unittest.TestCase):
    def test_missing_usage_is_not_zero_and_zero_generation_is_valid(self):
        missing=token_summary([{'input_tokens':None,'output_tokens':None}],'fixture')
        self.assertIsNone(missing['input_tokens_known'])
        self.assertIsNone(missing['total_tokens_all_calls'])
        self.assertEqual(missing['coverage_status'],'unavailable')
        partial=token_summary([{'input_tokens':5,'output_tokens':0},{'input_tokens':None,'output_tokens':None}],'fixture')
        self.assertEqual(partial['output_tokens_known'],0)
        self.assertEqual(partial['total_tokens_known_complete_calls'],5)
        self.assertIsNone(partial['total_tokens_all_calls'])
        self.assertEqual(partial['complete_usage_calls'],1)
        full=token_summary([{'input_tokens':5,'output_tokens':0}],'fixture')
        self.assertEqual(full['total_tokens_all_calls'],5)
        self.assertEqual(full['coverage_status'],'complete')


class FullSampleTests(unittest.TestCase):
    def test_abstention_is_unsuccessful_without_class_imputation(self):
        gold={'a':0,'b':1,'c':1,'d':0}
        result=full_sample_performance(gold,{'a':0,'b':0})
        self.assertEqual(result['full_sample_correct_completion_rate'],.25)
        self.assertEqual(result['prediction_coverage'],.5)
        self.assertEqual(result['unresolved_items'],2)
        self.assertEqual(result['unresolved_positive_items'],1)
        self.assertEqual(result['unresolved_negative_items'],1)
        complete=full_sample_performance(gold,gold)
        self.assertEqual(complete['full_sample_correct_completion_rate'],1)
