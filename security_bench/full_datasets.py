"""Native public test adapters. Evaluation metadata is never in model views."""
from .common import read, rows, digest
from .datasets import item


VISIBLE = ('step', 'thought', 'action', 'arguments', 'observation')


def load_new(config, dataset, location):
    spec = config['datasets'][dataset]
    output = []
    if dataset in ('wildguardtest', 'wildguardtest-response'):
        import pyarrow.parquet as pq
        path = location / 'test/wildguard_test.parquet'
        response_mode = dataset == 'wildguardtest-response' or spec.get('contract') == 'response_risk_classification' or spec.get('mode_code') == 'E'
        if dataset == 'wildguardtest' and response_mode:
            raise ValueError('wildguardtest is the frozen Mode A1 prompt-harm path; use wildguardtest-response for Mode E')
        if dataset == 'wildguardtest-response' and not response_mode:
            raise ValueError('wildguardtest-response requires Mode E / response_risk_classification')
        for i, row in enumerate(pq.read_table(path).to_pylist()):
            prompt = row['prompt']
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError('Missing WildGuard prompt')
            if response_mode:
                response = row['response']
                if not isinstance(response, str) or not response.strip():
                    raise ValueError('Missing WildGuard assistant response')
                label = row['response_harm_label']
                if label not in ('harmful', 'unharmful', None):
                    raise ValueError('Unknown WildGuard response label: ' + str(label))
                record = item(dataset, f'test:{i}', digest(prompt),
                    {'user_request': prompt, 'assistant_response': response},
                    None if label is None else int(label == 'harmful'), 'native_response_harm_label', path, spec['mode_code'])
                record.update(source_split='test', native_response_label=label)
            else:
                label = row['prompt_harm_label']
                if label not in ('harmful', 'unharmful', None):
                    raise ValueError('Unknown WildGuard prompt label: ' + str(label))
                record = item(dataset, f'test:{i}', digest(prompt), {'user_request': prompt},
                    None if label is None else int(label == 'harmful'), 'native_prompt_harm_label', path, spec['mode_code'])
                record.update(source_split='test', native_prompt_label=label)
            output.append(record)
        return output
    for split in spec['splits']:
        if split not in ('test', 'test_holdout'):
            raise ValueError('StepShield evaluation permits only test and test_holdout; no training merge')
        directory = location / 'data' / split
        key_rows = rows(directory / 'mapping/answer_key.jsonl')
        keys = {r['id']: r for r in key_rows}
        files = sorted((directory / 'scrubbed').glob('*.jsonl'))
        if len(keys) != len(key_rows) or {p.stem for p in files} != set(keys):
            raise ValueError('StepShield answer-key coverage/identity mismatch')
        for path in files:
            row, key = read(path), keys[path.stem]
            kind = key['trajectory_type']
            if kind not in ('rogue', 'correct', 'clean', 'benign'):
                raise ValueError('Unknown StepShield trajectory type')
            steps = [{k:s.get(k) for k in VISIBLE} for s in row['steps']]
            if not steps or [s['step'] for s in steps] != list(range(1,len(steps)+1)):
                raise ValueError('StepShield requires contiguous 1-based native step IDs')
            onset = key.get('rogue_step')
            if (kind == 'rogue' and (type(onset) is not int or not 1 <= onset <= len(steps))) or (kind != 'rogue' and onset is not None):
                raise ValueError('Invalid StepShield divergence metadata')
            task = {k:row['task'].get(k) for k in ('title','description','constraints','success_criteria')}
            record = item(dataset, f'{split}:{path.stem}', digest(steps),
                {'task':task, 'steps':steps}, int(kind == 'rogue'), 'native_blind_split_answer_key', path, spec['mode_code'])
            record.update(source_split=split, divergence_step=onset, trajectory_type=kind,
                          native_steps=len(steps), monitor_visible_content_sha256=digest(steps))
            output.append(record)
    return output


def run_prefix(case, judge, episode_id):
    """Replay observed steps in order; stop at first unsafe; never send future steps."""
    decisions = []
    for index, step in enumerate(case['view']['steps']):
        view = {'task':case['view']['task'], 'history':case['view']['steps'][:index], 'current_observed_step':step}
        prediction = judge.judge(view, 'prefix_monitoring', episode_id)
        decisions.append({'step':step['step'], 'prediction':prediction})
        if prediction == 1:
            return {'status':'ok', 'prediction':1, 'detection_step':step['step'], 'step_decisions':decisions}
    return {'status':'ok', 'prediction':0, 'detection_step':None, 'step_decisions':decisions}
