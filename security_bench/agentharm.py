"""Offline A1 inspection artifacts, usable before credentials or run budgets are set."""
from collections import Counter
from pathlib import Path
import copy
from .common import append, digest, file_hash, now, write
from .datasets import load_static
from .models import request
from .runner import data_hashes
from .config import inspect


def inspect_inputs(config, out_dir, splits=None):
    if set(config['datasets']) != {'agentharm'}:
        raise ValueError('Use the AgentHarm-only config for standalone A1 input inspection')
    effective = copy.deepcopy(config)
    if splits is not None:
        effective['datasets']['agentharm']['splits'] = splits
    unsafe_issues = [x for x in inspect(effective, check_keys=False)['issues']
                     if 'credential' in x or 'unknown fields' in x]
    if unsafe_issues:
        raise ValueError('Offline input configuration must not contain credentials or unknown model fields')
    instructions = effective['contracts']['request_risk_classification']['instructions']
    if not instructions:
        raise ValueError('A draft safety question is required to export an actual request example')
    items = load_static(effective, 'agentharm')
    if not items:
        raise ValueError('No selected AgentHarm items')
    source_hashes = data_hashes(effective)
    target = Path(out_dir).resolve()
    target.mkdir(parents=True, exist_ok=False)
    counts = Counter()
    for item in items:
        append(target/'inputs.jsonl', {'item_id':item['item_id'], 'split':item['source_split'],
            'view':item['view'], 'input_sha256':item['input_sha256']})
        append(target/'gold.jsonl', {k:item[k] for k in ['item_id', 'family_id', 'source_split',
            'source_partition', 'source_item_id', 'gold', 'gold_source', 'source_sha256']})
        counts[(item['source_split'], item['source_partition'])] += 1
    write(target/'jev-request-example.json', request(effective, 'jev', items[0]['view'], instructions))
    write(target/'effective-input-config.json', effective)
    write(target/'manifest.json', {'record_kind':'offline_input_preparation_not_experiment',
        'created_at':now(), 'dataset':'agentharm', 'mode':'A1',
        'contract':'request_risk_classification', 'items':len(items),
        'families':len({item['family_id'] for item in items}),
        'counts':[{'split':s, 'partition':p, 'items':n} for (s,p),n in sorted(counts.items())],
        'exact_item_ids':[item['item_id'] for item in items],
        'source_hashes':source_hashes, 'config_sha256':digest(effective),
        'artifact_sha256':{p.name:file_hash(p) for p in sorted(target.iterdir()) if p.is_file()},
        'model_calls':0, 'api_fee':'not_applicable_no_model_calls',
        'performance_results':'not_run', 'prompt_status':'draft_not_frozen',
        'note':'Native partition labels are independent evaluation metadata, not model inputs or official harm scores.'})
    return {'status':'prepared_no_model_calls', 'items':len(items),
            'counts':[{'split':s,'partition':p,'items':n} for (s,p),n in sorted(counts.items())],
            'output_dir':str(target)}
