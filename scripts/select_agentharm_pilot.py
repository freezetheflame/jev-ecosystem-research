"""Select a stratified AgentHarm validation pilot sample with a recorded seed."""
import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security_bench.common import digest, file_hash, now, write
from security_bench.config import read as read_config
from security_bench.datasets import load_static, paths
from security_bench.runner import data_hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/security-bench-aabd.template.json')
    parser.add_argument('--split', default='validation')
    parser.add_argument('--per-class', type=int, default=25)
    parser.add_argument('--seed', type=int, default=20261030)
    parser.add_argument('--out', default='data/agent-security-study/preparations/'
        '2026-10-30-agentharm-pilot-50-selection.json')
    args = parser.parse_args()
    config = read_config(args.config)
    config['datasets'] = {'agentharm': config['datasets']['agentharm']}
    config['datasets']['agentharm']['splits'] = [args.split]
    items = load_static(config, 'agentharm')
    by_gold = {0: [], 1: []}
    for item in items:
        by_gold[item['gold']].append(item)
    rng = random.Random(args.seed)
    chosen = []
    for gold in (1, 0):
        pool = sorted(by_gold[gold], key=lambda x: x['item_id'])
        if len(pool) < args.per_class:
            raise SystemExit(f'not enough items for gold={gold}: {len(pool)}')
        chosen.extend(rng.sample(pool, args.per_class))
    chosen.sort(key=lambda x: (x['gold'], x['item_id']))
    record = {
        'record_kind': 'pilot_sample_selection_not_observation',
        'created_at': now(),
        'config': args.config,
        'config_sha256': digest(config),
        'split': args.split,
        'seed': args.seed,
        'per_class': args.per_class,
        'counts': dict(sorted(Counter(str(x['gold']) for x in chosen).items())),
        'item_ids': [x['item_id'] for x in chosen],
        'families': len({x['family_id'] for x in chosen}),
        'source_hashes': data_hashes(config),
        'selected': [{'item_id': x['item_id'], 'family_id': x['family_id'],
                      'gold': x['gold'], 'input_sha256': x['input_sha256']} for x in chosen],
        'note': 'Random stratified sample of the public validation split; not an exposure audit.'
    }
    write(args.out, record)
    print(json.dumps({'out': args.out, 'items': len(chosen), 'counts': record['counts'],
                      'families': record['families'], 'seed': args.seed}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
