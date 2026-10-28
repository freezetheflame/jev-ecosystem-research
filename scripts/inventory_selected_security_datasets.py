"""Derive acquisition inventory from raw files, without executing benchmarks."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/agent-security-study/datasets/2026-10-27'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    result = {'record_kind': 'dataset_acquisition_inventory_not_experiment',
              'generated_at_utc': datetime.now(timezone.utc).isoformat(),
              'script': 'scripts/inventory_selected_security_datasets.py',
              'script_sha256': sha(Path(__file__)), 'datasets': {},
              'limitations': ['Downloaded revision is not an approved frozen evaluation configuration.',
                              'No benchmark environment, grader or model was run.',
                              'Mode semantics, sample selection, exposure audit and split remain unresolved.']}
    for name in ['agentdojo', 'agentharm', 'mcphunt', 'mcphunt-source']:
        base = BASE / name
        manifest = base / 'manifest.json'
        record = json.loads(manifest.read_text(encoding='utf-8'))
        if record['status'] != 'download_complete':
            raise ValueError(f'{name} download is incomplete')
        for item in record['files']:
            path = base / item['path']
            if path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
                raise ValueError(f'{name} integrity mismatch: {item["path"]}')
        entry = {'source': record['source'], 'revision': record['revision'],
                 'local_snapshot': str(base / 'snapshot'), 'manifest': str(manifest),
                 'manifest_sha256': sha(manifest), 'verified_files': len(record['files']),
                 'verified_bytes': sum(f['bytes'] for f in record['files']),
                 'status': 'downloaded_and_file_hashes_verified'}
        if 'expected_upstream_files' in record:
            assert entry['verified_files'] == record['expected_upstream_files']
        if name == 'agentharm':
            entry['counts_by_public_file'] = {}
            for path in sorted((base / 'snapshot/benchmark').glob('*.json')):
                data = json.loads(path.read_text(encoding='utf-8'))
                entry['counts_by_public_file'][path.name] = len(data['behaviors'])
            entry['count_note'] = 'Augmented behaviors and chat variants are not independent base tasks; private test not publicly available.'
        if name == 'agentdojo':
            entry['suites'] = ['banking', 'slack', 'travel', 'workspace']
            for suite in entry['suites']:
                assert (base / f'snapshot/src/agentdojo/data/suites/{suite}/environment.yaml').is_file()
                for kind in ['user_tasks.py', 'injection_tasks.py']:
                    assert (base / f'snapshot/src/agentdojo/default_suites/v1/{suite}/{kind}').is_file()
            entry['input_contract'] = 'Official tasks/environments/attacks/graders; historical static TS-Bench fragments are not the benchmark input.'
            entry['environment_execution_verified'] = False
        if name == 'mcphunt':
            entry['trace_counts_by_stratum'] = {}
            for folder in ['main', 'mitigation', 'live_guard_defense', 'browser_replication']:
                counts = {}
                for path in sorted((base / 'snapshot' / folder).glob('*.json')):
                    data = json.loads(path.read_text(encoding='utf-8'))
                    counts[path.name] = len(data['traces'])
                entry['trace_counts_by_stratum'][folder] = {'files': counts, 'total': sum(counts.values())}
            entry['all_released_traces'] = sum(x['total'] for x in entry['trace_counts_by_stratum'].values())
            metadata = json.loads((base / 'snapshot/croissant.json').read_text(encoding='utf-8'))
            hashes = {f['path'].removeprefix('snapshot/'): f['sha256'] for f in record['files']}
            checked = 0
            for item in metadata['distribution']:
                name_in_card = item.get('name')
                expected = item.get('sha256')
                if name_in_card in hashes and expected:
                    assert hashes[name_in_card] == expected, name_in_card
                    checked += 1
            entry['publisher_croissant_hashes_matched'] = checked
        result['datasets'][name] = entry
    atbench = Path('D:/projects/jev/data/atbench-test.json')
    result['datasets']['atbench'] = {'status': 'existing_raw_file_verified_against_historical_manifest',
        'path': str(atbench), 'rows': len(json.loads(atbench.read_text(encoding='utf-8'))),
        'sha256': sha(atbench), 'bytes': atbench.stat().st_size,
        'source_revision': '4476ef92ed8f85c8d58d8a5b9dfdf55aa7893138',
        'provenance': 'D:/projects/jev/data/agent-safety-full-manifest.json'}
    historical = json.loads(Path(result['datasets']['atbench']['provenance']).read_text(encoding='utf-8'))
    assert sha(atbench) == historical['source_sha256']['ATBench/test.json']
    output = ROOT / 'data/agent-security-study/dataset-acquisition-2026-10-27.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: {x: v[x] for x in ['status', 'verified_files', 'rows', 'all_released_traces', 'publisher_croissant_hashes_matched'] if x in v}
                      for k, v in result['datasets'].items()}, indent=2))


if __name__ == '__main__':
    main()
