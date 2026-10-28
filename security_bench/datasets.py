"""Only native source fields enter model views; labels stay in separate records."""
from pathlib import Path
from functools import lru_cache
from .common import absolute, read, digest, file_hash


@lru_cache(maxsize=256)
def _source_hash(path, size, modified_ns):
    return file_hash(path)


def paths(config):
    import os
    base = absolute(os.environ.get('SECURITY_BENCH_DATA_ROOT') or config['data_root'])
    bundle = (base / 'datasets').is_dir()
    result = {}
    for name in config['datasets']:
        if bundle and (base / 'datasets' / name).exists():
            result[name] = base / 'datasets' / name / 'ATBench.json' if name == 'atbench' else base / 'datasets' / name
        elif name == 'atbench':
            result[name] = absolute(config['atbench_path'])
        elif name == 'maliciousskillbench':
            result[name] = absolute(config['maliciousskillbench_path'])
        else:
            result[name] = base / name / 'snapshot'
    return result


def agentharm_files(config):
    splits = config['datasets']['agentharm'].get('splits')
    if not isinstance(splits, list) or not splits or len(splits) != len(set(splits)) or any(
            s not in ('validation', 'test_public') for s in splits):
        raise ValueError('AgentHarm needs distinct explicit validation/test_public splits; private/chat are not this contract')
    root = paths(config)['agentharm'] / 'benchmark'
    return [(split, kind, label, root / f'{kind}_behaviors_{split}.json')
            for split in splits for kind, label in [('harmful', 1), ('benign', 0)]]


def item(dataset, uid, family, view, label, source, source_path, mode):
    if label is not None and type(label) not in (bool, int):
        raise ValueError('Non-binary gold requires an explicit mapping')
    if label is not None and label not in (0, 1):
        raise ValueError('Non-binary gold requires an explicit mapping')
    return {'dataset_id': dataset, 'item_id': uid, 'family_id': family,
            'evaluation_mode': mode, 'view': view, 'input_sha256': digest(view),
            'gold': None if label is None else int(label), 'gold_source': source,
            'source_file': str(source_path), 'source_sha256': _source_hash(str(source_path),
                source_path.stat().st_size, source_path.stat().st_mtime_ns)}


def load_static(config, dataset):
    spec = config['datasets'][dataset]
    mode = spec.get('mode_code')
    location = paths(config)[dataset]
    output = []
    if dataset == 'maliciousskillbench':
        if spec['contract'] != 'skill_risk_classification':
            raise ValueError('MaliciousSkillBench requires skill_risk_classification')
        policy = spec.get('withheld_text_policy')
        if policy not in ('exclude', 'public_sanitized'):
            raise ValueError('Explicit withheld_text_policy must be exclude or public_sanitized')
        import pyarrow.parquet as pq
        path = location / 'primary.parquet'
        for row in pq.read_table(path).to_pylist():
            withheld = bool(row['original_text_withheld'])
            if withheld and policy == 'exclude':
                continue
            text = row['public_skill_text'] if withheld else row['skill_text']
            if not isinstance(text, str) or not text.strip():
                raise ValueError('Missing selected MSB text; never silently skip a source item')
            label = {'0':0, '1':1}.get(str(row['label']))
            if label is None:
                raise ValueError('Unknown native MaliciousSkillBench label')
            record = item(dataset, row['benchmark_id'], row['structural_family_id'] or row['benchmark_id'],
                {'skill_text':text}, label, 'native_MaliciousSkillBench_label', path, mode)
            record['text_representation'] = 'public_sanitized' if withheld else 'exact_frozen_text'
            output.append(record)
    elif dataset == 'agentharm':
        if spec['contract'] != 'request_risk_classification':
            raise ValueError('AgentHarm adapter requires request_risk_classification contract')
        for split, kind, label, path in agentharm_files(config):
            for row in read(path)['behaviors']:
                prompt = row.get('prompt')
                if not isinstance(prompt, str) or not prompt.strip():
                    raise ValueError('Missing AgentHarm request; never silently skip an item')
                if row.get('id') is None or row.get('id_original') is None:
                    raise ValueError('AgentHarm requires native item and base-behavior IDs')
                uid = f'{kind}:{split}:{row["id"]}'
                # These fields are provenance only; the model view is exactly one native prompt.
                record = item(dataset, uid, str(row['id_original']),
                    {'user_request': prompt}, label, 'published_harmful_or_benign_partition', path, mode)
                record.update(source_split=split, source_partition=kind, source_item_id=str(row['id']),
                              base_behavior_id=str(row['id_original']))
                output.append(record)
    elif dataset == 'atbench':
        if spec['contract'] != 'full_trace_risk_classification':
            raise ValueError('ATBench adapter requires full_trace_risk_classification contract')
        for index, row in enumerate(read(location)):
            uid = str(row.get('id') if row.get('id') is not None else index)
            # Preserve structured tool calls and content. Old serialize() flattened message
            # lists but lost non-text fields; this adapter keeps the complete native contents.
            output.append(item(dataset, uid, uid,
                {'tools': row['tool_used'], 'trajectory': row['contents']},
                row.get('label'), 'native_ATBench_label', location, mode))
    elif dataset == 'mcphunt':
        if spec['contract'] != 'full_trace_risk_classification':
            raise ValueError('No action/prefix gold is inherited from a full-trace MCPHunt label')
        gold_field = spec['gold_field']
        if gold_field not in ('any_risk', 'data_flow_risk', 'intrinsic_risk'):
            raise ValueError('Explicit supported MCPHunt gold_field is required')
        for relative in spec['files']:
            path = (location / relative).resolve()
            if not path.is_relative_to(location.resolve()):
                raise ValueError('MCPHunt file escapes data root')
            for row in read(path)['traces']:
                # Events contain detector canary flags; use only native agent-visible messages.
                # Exclude events, labeling, outcomes, turn usage, env_snapshot and canary detector metadata.
                view = {'user_request': row['task_prompt'], 'messages': row['messages']}
                output.append(item(dataset, f'{relative}:{row["trace_id"]}', str(row['task_id']),
                    view, row['labeling'].get(gold_field), 'native_labeling.' + gold_field, path, mode))
    else:
        raise ValueError('AgentDojo must use the official dynamic environment adapter')
    wanted = spec.get('item_ids')
    if wanted is not None:
        selected = {r['item_id']: r for r in output}
        if len(wanted) != len(set(wanted)) or set(wanted) - selected.keys():
            raise ValueError('Duplicate or missing requested item IDs')
        output = [selected[k] for k in wanted]
    if len({x['item_id'] for x in output}) != len(output):
        raise ValueError('Duplicate native item IDs')
    return output
