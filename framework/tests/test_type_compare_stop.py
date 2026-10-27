"""No live calls: permission stops must still persist in-flight responses."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from framework import type_compare


@dataclass
class ConfigFixture:
    model: str = "jev-1.14.0"
    instructions: str = "Synthetic offline authorization question"
    sha256: str = "offline-profile"
    chunk_size: int = 48000
    chunk_overlap: int = 2000
    question_name: str = "unauthorized_action"


class PermissionStopTests(unittest.TestCase):
    def test_completed_inflight_calls_are_saved_after_permission_stop(self):
        second_started, stop_requested = threading.Event(), threading.Event()
        lock = threading.Lock()
        successful, bulk_count = [], [0]

        class ObservedPool(ThreadPoolExecutor):
            def submit(self, *args, **kwargs):
                future = super().submit(*args, **kwargs)
                original_cancel = future.cancel

                def cancel():
                    stop_requested.set()
                    return original_cancel()

                future.cancel = cancel
                return future

        def transport(payload, **kwargs):
            kind = payload['questions']['unauthorized_action']['type']
            if payload['state'] != 'u0':
                with lock:
                    bulk_count[0] += 1
                    index = bulk_count[0]
                if index == 1:
                    if not second_started.wait(5):
                        raise RuntimeError('Offline test did not start the second worker')
                    raise RuntimeError('TypeSafe HTTP 401: offline fixture')
                second_started.set()
                if not stop_requested.wait(5):
                    raise RuntimeError('Offline test did not observe cancellation')
            answer = {'type': kind, 'noul': .1, 'score': .1, 'choice': 'safe',
                      'probabilities': {'safe': .9, 'unsafe': .1}}
            with lock:
                successful.append((payload['state'], kind))
            return {'model': 'jev-1.14.0', 'answers': {'unauthorized_action': answer},
                    'usage': {'input_tokens': 10, 'output_tokens': 1}}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / 'bench/data/ts_bench.jsonl'
            dataset.parent.mkdir(parents=True)
            records = [{'uid': f'u{i}', 'label': 0, 'source_id': 'fixture', 'corpus': 'fixture',
                        'text_stage': 'S4_action', 'label_semantics': 'outcome_unsafe',
                        'meta': {'tsbench_group': 'AgentDojo'}} for i in range(3)]
            dataset.write_text('\n'.join(json.dumps(row) for row in records), encoding='utf-8')
            argv = ['type_compare', '--limit', '3', '--workers', '2',
                    '--out', str(root / 'reports/permission-stop-fixture')]
            with patch.object(type_compare, 'ROOT', root), \
                 patch.object(type_compare, 'configure_transport'), \
                 patch.object(type_compare, 'load_config', return_value=ConfigFixture()), \
                 patch.object(type_compare, 'select', side_effect=lambda rows, n, seed: rows), \
                 patch.object(type_compare, 'wrap_files', side_effect=lambda row: row['uid']), \
                 patch.object(type_compare, 'build_states', side_effect=lambda uid, *args: [uid]), \
                 patch.object(type_compare, 'load_env'), \
                 patch.object(type_compare, 'api_key', return_value='offline-not-a-key'), \
                 patch.object(type_compare, 'post_json', side_effect=transport), \
                 patch.object(type_compare, 'ThreadPoolExecutor', ObservedPool), \
                 patch.object(type_compare, 'report'), \
                 patch.object(type_compare.subprocess, 'check_output', return_value='offline-fixture'), \
                 patch('sys.argv', argv):
                type_compare.main()
            rows = type_compare.read(root / 'bench/data/scans/permission-stop-fixture/predictions.jsonl')
            saved = {(row['uid'], row['type']) for row in rows if 'error' not in row}
            self.assertTrue(stop_requested.is_set())
            self.assertTrue(second_started.is_set())
            self.assertGreater(len(successful), 3)
            self.assertEqual(saved, set(successful))
            self.assertEqual(sum('HTTP 401' in row.get('error', '') for row in rows), 1)


if __name__ == '__main__':
    unittest.main()
