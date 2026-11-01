"""Offline input-inspection artifacts for one static dataset.

Usable before credentials, budgets or a frozen protocol exist. Gold is written to a
separate file and never enters the request example.
"""
from collections import Counter
from pathlib import Path
import copy
from .common import append, digest, file_hash, now, write
from .datasets import load_static
from .models import request
from .runner import data_hashes
from .config import inspect


def inspect_inputs(config, out_dir, splits=None, selected=None):
    if selected is not None and selected not in config['datasets']:
        raise ValueError('Selected dataset is absent from the configuration')
    active = set(config['datasets']) if selected is None else {selected}
    if len(active) != 1 or 'agentdojo' in active:
        raise ValueError('Offline input inspection handles exactly one static dataset')
    dataset = next(iter(active))
    effective = copy.deepcopy(config)
    if selected is not None:
        effective['datasets'] = {selected: effective['datasets'][selected]}
    if splits is not None:
        if dataset != 'agentharm':
            raise ValueError('--split applies only to AgentHarm')
        effective['datasets']['agentharm']['splits'] = splits
    unsafe_issues = [x for x in inspect(effective, check_keys=False)['issues']
                     if 'credential' in x or 'unknown fields' in x]
    if unsafe_issues:
        raise ValueError('Offline input configuration must not contain credentials or unknown model fields')
    contract = effective['datasets'][dataset]['contract']
    instructions = effective['contracts'][contract]['instructions']
    if not instructions:
        raise ValueError('A draft safety question is required to export an actual request example')
    items = load_static(effective, dataset)
    if not items:
        raise ValueError('No selected ' + dataset + ' items')
    source_hashes = data_hashes(effective)
    target = Path(out_dir).resolve()
    target.mkdir(parents=True, exist_ok=False)
    counts = Counter()
    gold_sources = Counter()
    for item in items:
        entry = {'item_id': item['item_id'], 'view': item['view'], 'input_sha256': item['input_sha256']}
        if 'source_split' in item:
            entry['split'] = item['source_split']
        append(target/'inputs.jsonl', entry)
        gold = {key: item.get(key) for key in
                ('item_id', 'family_id', 'gold', 'gold_source', 'source_sha256', 'native_score')
                if key in item}
        append(target/'gold.jsonl', gold)
        counts[(item.get('source_split', 'selected'), item.get('source_partition', 'native'))] += 1
        gold_sources[item['gold_source']] += 1
    write(target/'jev-request-example.json', request(effective, 'jev', items[0]['view'], instructions))
    write(target/'effective-input-config.json', effective)
    write(target/'manifest.json', {'record_kind': 'offline_input_preparation_not_experiment',
        'created_at': now(), 'dataset': dataset,
        'mode': effective['datasets'][dataset]['mode_code'], 'contract': contract,
        'items': len(items), 'families': len({item['family_id'] for item in items}),
        'counts': [{'split': s, 'partition': p, 'items': n} for (s, p), n in sorted(counts.items())],
        'gold_sources': dict(sorted(gold_sources.items())),
        'exact_item_ids': [item['item_id'] for item in items],
        'source_hashes': source_hashes, 'config_sha256': digest(effective),
        'artifact_sha256': {p.name: file_hash(p) for p in sorted(target.iterdir()) if p.is_file()},
        'model_calls': 0, 'api_fee': 'not_applicable_no_model_calls',
        'performance_results': 'not_run', 'prompt_status': 'draft_not_frozen',
        'note': 'Gold is evaluation-only metadata and never enters the request view; derived gold is labelled by source.'})
    return {'status': 'prepared_no_model_calls', 'dataset': dataset, 'items': len(items),
            'counts': [{'split': s, 'partition': p, 'items': n} for (s, p), n in sorted(counts.items())],
            'output_dir': str(target)}