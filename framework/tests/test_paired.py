"""Offline engineering checks. Synthetic fixtures are not benchmark observations."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from framework import paired
from framework.providers import encoded, decision, request_body, validate_backend, post


def backend(kind):
    return {'id': kind, 'kind': kind, 'provider': 'test', 'model': 'fixture-' + kind,
            'endpoint': 'https://example.invalid/test', 'key_env': 'PAIRED_TEST_SECRET',
            'decision_type': 'noul', 'parameters': {}, 'headers': {}, 'timeout_s': 1,
            'revision_note': 'synthetic fixture only', 'deployment_note': 'mock transport',
            'unsent_defaults': 'unknown test defaults'}


def config():
    return {'run_id': 'unit-test-not-research', 'run_kind': 'pilot', 'purpose': 'offline test',
        'hypothesis': 'test fixture', 'primary_metric': 'test-only coverage', 'evaluation_mode': 'B',
        'evaluation_mode_namespace': paired.LEGACY_MODE_NAMESPACE,
        'classification_unit': 'fixture_action', 'target_event': 'fixture violation',
        'information_boundary': 'state only, no gold', 'label_validation': 'synthetic fixture',
        'exposure': 'development unit tests', 'question': {'instructions': 'Is this unsafe?',
            'positive_definition': 'Unsafe', 'negative_definition': 'Safe'},
        'dataset': {'id': 'synthetic-not-benchmark', 'source': 'unit test', 'revision': '1',
            'split': 'unit', 'selection': 'all two fixtures', 'license': 'synthetic', 'original_count': 2},
        'seed': 17, 'threshold': .5, 'max_input_chars': 1000, 'max_calls': 4, 'max_wall_seconds': 60,
        'pricing': {'test:fixture-jev': {'input_usd_per_million': 1, 'output_usd_per_million': 2,
            'basis': 'synthetic test rate; not actual pricing'}},
        'backends': [backend('jev'), backend('openai_chat')]}


def rows():
    return [{'id': str(i), 'original_id': 'trace-' + str(i), 'task_family': 'family-' + str(i),
             'state': 'Evidence ' + str(i), 'label': i, 'label_scope': 'B',
             'gold_source': 'synthetic', 'gold_validation': 'unit fixture', 'condition': 'fixture',
             'cutoff': 'before action', 'visibility_validation': 'unit fixture'} for i in (0, 1)]


def mock_post(selected, body, secret):
    payload = json.loads(body)
    state = payload['state'] if selected['kind'] == 'jev' else json.loads(payload['messages'][1]['content'])['state']
    positive = state.endswith('1')
    response = {'model': selected['model'], 'usage': {'input_tokens': 10, 'output_tokens': 1}}
    if selected['kind'] == 'jev':
        response['answers'] = {'risk': {'type': 'noul', 'noul': .9 if positive else .1}}
    else:
        response['choices'] = [{'finish_reason': 'stop', 'message': {'content': json.dumps(
            {'answer_yes': positive, 'confidence': .9, 'reason': 'synthetic'})}}]
    return encoded(response), response, 200, None, False, 'synthetic-request-id'


class AdapterTests(unittest.TestCase):
    def test_revised_modes_cannot_inherit_legacy_meanings(self):
        for mode in ('A1', 'A2', 'B', 'C'):
            selected = config()
            selected['evaluation_mode_namespace'] = 'selection_2026_10_27_v2_pending_definition'
            selected['evaluation_mode'] = mode
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'definitions remain unresolved'):
                paired.validate(selected, rows())
        selected = config()
        del selected['evaluation_mode_namespace']
        with self.assertRaisesRegex(ValueError, 'namespace required'):
            paired.validate(selected, rows())

    def test_http_boundary_long_header_error_body_and_credential_redaction(self):
        seen = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append((self.headers.get('Authorization'), self.headers.get('TypeSafe-Danger-Zone-Long-Context')))
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(403)
                self.send_header('x-request-id', 'local-http-fixture')
                self.end_headers()
                self.wfile.write(b'{"error":"echo private-unit-key"}')

            def log_message(self, *args):
                pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            selected = backend('jev')
            selected['endpoint'] = f'http://127.0.0.1:{server.server_port}/test'
            selected['headers'] = {'TypeSafe-Danger-Zone-Long-Context': 'true'}
            validate_backend(selected)
            # Do not route a loopback unit-test server through a machine proxy.
            with patch.dict(os.environ, {'NO_PROXY': '127.0.0.1', 'no_proxy': '127.0.0.1'}):
                raw, parsed, status, error, redacted, request_id = post(selected, b'{}', 'private-unit-key')
            self.assertEqual(status, 403)
            self.assertIsNotNone(error)
            self.assertEqual(request_id, 'local-http-fixture')
            self.assertTrue(redacted)
            self.assertNotIn(b'private-unit-key', raw)
            self.assertEqual(seen, [('Bearer private-unit-key', 'true')])
            self.assertIn('[REDACTED]', parsed['error'])
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_label_blind_projection(self):
        cfg = config()
        row = rows()[0]
        for selected in cfg['backends']:
            first = request_body(selected, row['state'], cfg['question'], 'system')
            row.update(label=1, gold_source='SECRET_GOLD_CANARY')
            self.assertEqual(first, request_body(selected, row['state'], cfg['question'], 'system'))
            self.assertNotIn('SECRET_GOLD_CANARY', json.dumps(first))

    def test_bad_gold_scope_cutoff_and_length_are_rejected(self):
        for field, value in [('label_scope', 'D'), ('cutoff', ''), ('state', 'x' * 1001), ('label', True)]:
            data = rows()
            data[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                paired.validate(config(), data)

    def test_wrong_endpoint_and_prompt_override_rejected(self):
        for field, value in [('endpoint', 'https://user:key@example.invalid/test'),
                             ('parameters', {'messages': []}), ('headers', {'Authorization': 'secret'})]:
            selected = backend('openai_chat')
            selected[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_backend(selected)

    def test_native_yes_no_is_not_thresholded_as_calibrated_risk(self):
        response = {'choices': [{'finish_reason': 'stop', 'message': {'content':
            '{"answer_yes": true, "confidence": 0.6}'}}]}
        risk, prediction, mapping = decision(backend('openai_chat'), response, .99)
        self.assertEqual((risk, prediction), (.6, 1))
        self.assertIn('self_reported', mapping)
        response['choices'][0]['finish_reason'] = 'length'
        with self.assertRaises(ValueError):
            decision(backend('openai_chat'), response, .5)

    def test_choice_tie_uses_native_choice(self):
        selected = backend('jev')
        selected['decision_type'] = 'choice'
        response = {'answers': {'risk': {'type': 'choice', 'choice': 'safe',
            'probabilities': {'safe': .5, 'unsafe': .5}}}}
        self.assertEqual(decision(selected, response, .5)[:2], (.5, 0))


@unittest.skipUnless((Path(os.getenv('JEV_WORKSPACE_ROOT', 'D:/projects/jev')) / 'jev_skill/monitor.py').is_file(),
                     'Pinned external monitor workspace required for integration tests')
class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data.jsonl'
        self.data.write_bytes(b''.join(encoded(r) + b'\n' for r in rows()))
        self.config = self.root / 'config.json'
        paired.save(self.config, config())
        self.out = self.root / 'run'
        self.workspace = Path(os.getenv('JEV_WORKSPACE_ROOT', 'D:/projects/jev'))
        self.env = patch.dict(os.environ, {'PAIRED_TEST_SECRET': 'test-key-is-never-real-840192'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def prepare(self):
        return paired.prepare(self.data, self.config, self.out, self.workspace)

    def test_full_pair_records_costs_unknowns_and_no_duplicate_resume(self):
        self.prepare()
        self.assertEqual(paired.report(self.out)['status'], 'prepared_not_executed')
        calls = []
        def transport(*args):
            calls.append(args[0]['id'])
            return mock_post(*args)
        paired.execute(self.out, transport=transport)
        report = paired.report(self.out)
        self.assertEqual((report['planned_calls'], report['finished_calls']), (4, 4))
        self.assertEqual(report['status'], 'complete')
        for metrics in report['per_backend'].values():
            self.assertEqual((metrics['TP'], metrics['TN'], metrics['FP'], metrics['FN']), (1, 1, 0, 0))
        self.assertAlmostEqual(report['per_backend']['jev']['resources']['api_estimate_usd'], .000024)
        self.assertIsNone(report['api_estimate_usd'])
        self.assertEqual(sum(m['calls'] for m in report['resource_monitor']), 4)
        paired.execute(self.out, transport=transport)
        self.assertEqual(len(calls), 4)
        self.assertNotIn(os.environ['PAIRED_TEST_SECRET'], (self.out / 'report.md').read_text())

    def test_http_access_failure_is_partial_and_not_a_safe_prediction(self):
        self.prepare()
        def denied(*args):
            return b'{"error":"denied"}', {'error': 'denied'}, 403, RuntimeError('denied'), False, None
        paired.execute(self.out, transport=denied)
        report = paired.report(self.out)
        self.assertEqual(report['status'], 'partial')
        self.assertEqual(report['finished_calls'], 1)
        self.assertEqual(sum(m['valid_n'] for m in report['per_backend'].values()), 0)
        self.assertIsNone(report['api_estimate_usd'])

    def test_parse_failure_retains_usage_and_raw_response(self):
        self.prepare()
        def malformed(*args):
            response = {'model': args[0]['model'], 'usage': {'input_tokens': 10, 'output_tokens': 1}}
            return encoded(response), response, 200, None, False, None
        paired.execute(self.out, transport=malformed)
        report = paired.report(self.out)
        self.assertEqual(report['status'], 'complete_with_errors')
        self.assertEqual(report['per_backend']['jev']['excluded']['parse_error'], 2)
        self.assertAlmostEqual(report['per_backend']['jev']['resources']['api_estimate_usd'], .000024)
        self.assertEqual(len(list((self.out / 'raw').glob('*.response.bin'))), 4)

    def test_uncertain_interrupted_call_is_never_replayed(self):
        self.prepare()
        def interrupted(*args):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            paired.execute(self.out, transport=interrupted)
        self.assertEqual(paired.report(self.out)['unresolved_calls'], 1)
        with self.assertRaisesRegex(ValueError, 'Uncertain'):
            paired.execute(self.out, transport=mock_post)

    def test_resume_rejects_frozen_input_or_raw_modification(self):
        self.prepare()
        paired.execute(self.out, transport=mock_post)
        first = next((self.out / 'raw').glob('*.response.bin'))
        original = first.read_bytes()
        first.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Raw artifact changed'):
            paired.execute(self.out, transport=mock_post)
        first.write_bytes(original)
        (self.out / 'dataset.jsonl').write_bytes(b'{}\n')
        with self.assertRaisesRegex(ValueError, 'Frozen input changed'):
            paired.execute(self.out, transport=mock_post)

    def test_active_runner_lock_prevents_duplicate_calls(self):
        self.prepare()
        (self.out / '.execution-lock').write_text('another process')
        with self.assertRaises(FileExistsError):
            paired.execute(self.out, transport=mock_post)

    def test_saved_code_can_reproduce_offline_report_without_original_imports(self):
        self.prepare()
        result = subprocess.run([sys.executable, '-m', 'framework.paired', 'report', '--out', str(self.out)],
            cwd=self.out / 'code', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'prepared_not_executed')
        self.assertTrue((self.out / 'code/docs/model-evaluation/agent-security-experiment-protocol.md').is_file())


if __name__ == '__main__':
    unittest.main()
