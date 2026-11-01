"""Verify the four acquired source datasets without any model call.

Recomputes every configured source hash, loads each dataset through its adapter and
writes a machine-readable evidence record. It does not judge model behaviour.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
import sys
import platform

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security_bench.common import ROOT, absolute, file_hash, now, read, write
from security_bench.config import read as read_config
from security_bench.datasets import load_static, paths
from security_bench.runner import data_hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/security-bench-aabd.template.json')
    parser.add_argument('--out', default='data/workspace-evidence/2026-10-30-dataset-acquisition/verification.json')
    args = parser.parse_args()
    config = read_config(args.config)
    locations = paths(config)
    hashes = data_hashes(config)
    datasets = {}
    for name in config['datasets']:
        items = load_static(config, name)
        counts = Counter(str(item.get('gold')) for item in items)
        manifest_path = locations[name].parent / 'manifest.json'
        manifest = read(manifest_path) if manifest_path.is_file() else None
        datasets[name] = {
            'mode': config['datasets'][name]['mode_code'],
            'contract': config['datasets'][name]['contract'],
            'items': len(items),
            'families': len({item['family_id'] for item in items}),
            'gold_counts': dict(sorted(counts.items())),
            'gold_sources': dict(sorted(Counter(item['gold_source'] for item in items).items())),
            'view_keys': sorted(items[0]['view']),
            'max_view_chars': max(len(json.dumps(item['view'], ensure_ascii=False)) for item in items),
            'source_revision': config['datasets'][name]['source_revision'],
            'manifest_file_count': len(manifest['files']) if manifest else None,
            'manifest_hashes_match': all(
                file_hash(locations[name].parent / f['path']) == f['sha256'] for f in manifest['files']
            ) if manifest else None,
        }
        if name == 'atbench':
            datasets[name]['source_sha256'] = file_hash(locations[name])
    result = {
        'record_kind': 'dataset_acquisition_verification_not_experiment',
        'created_at': now(),
        'config': str(absolute(args.config)),
        'data_root': str(absolute(config['data_root'])),
        'python': sys.version,
        'platform': platform.platform(),
        'model_calls': 0,
        'network_model_requests': 0,
        'datasets': datasets,
        'hashed_files': len(hashes),
        'hash_manifest': hashes,
        'note': 'Counts and hashes only. No model output, metric or fee is produced by this check.',
    }
    write(args.out, result)
    print(json.dumps({'status': 'verified', 'datasets': {
        name: {'items': d['items'], 'gold': d['gold_counts'],
               'families': d['families'], 'hashes_match': d['manifest_hashes_match']}
        for name, d in datasets.items()}, 'hashed_files': len(hashes), 'out': str(absolute(args.out))},
        ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()