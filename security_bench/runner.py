"""Offline planning and serial live scheduling with immutable inputs and resume audit."""
import importlib.metadata
import json
import platform
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path
from .common import ROOT, absolute, append, digest, encode, file_hash, now, read, rows, sources, write
from .config import inspect
from .datasets import load_static, paths, agentharm_files
from .models import Judge, Transport, StopRun, TransportError, load_monitor
from .adapters import selected_models


def environment():
    return {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
            'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}}


def git_provenance():
    def run(arguments):
        p = subprocess.run(['git', *arguments], cwd=ROOT, capture_output=True, encoding='utf-8')
        return p.stdout.strip() if p.returncode == 0 else None
    return {'head': run(['rev-parse', 'HEAD']),
            'relevant_dirty_state': run(['status', '--porcelain', '--', 'security_bench', 'configs', 'requirements']),
            'scope': 'Relevant code/config paths only; actual Python source snapshot and hashes are retained separately.'}


def data_hashes(config):
    result = {}
    locations = paths(config)
    for path in (sorted((locations['agentdojo'] / 'src').rglob('*')) if 'agentdojo' in config['datasets'] else []):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py', '.yaml', '.json', '.txt'):
            result[str(path)] = file_hash(path)
    selected_files = []
    if 'atbench' in config['datasets']:
        selected_files.append(locations['atbench'])
    if 'agentharm' in config['datasets']:
        selected_files.extend(p for _, _, _, p in agentharm_files(config))
    if 'mcphunt' in config['datasets']:
        selected_files.extend(locations['mcphunt'] / p for p in config['datasets']['mcphunt']['files'])
    for path in selected_files:
        result[str(path)] = file_hash(path)
    if 'maliciousskillbench' in config['datasets']:
        path = locations['maliciousskillbench'] / 'primary.parquet'
        result[str(path)] = file_hash(path)
    # Compare active raw files to the acquisition/published snapshot, not just to
    # hashes first observed after a possible local edit. Works with the portable bundle.
    if 'atbench' in config['datasets'] and result[str(locations['atbench'])] != config['datasets']['atbench']['source_sha256']:
        raise ValueError('ATBench raw file differs from acquired source')
    for name in (n for n in config['datasets'] if n != 'atbench'):
        location = locations[name].resolve()
        local_manifest = location.parent / 'manifest.json'
        if location.name == 'snapshot' and local_manifest.is_file():
            m = read(local_manifest)
            expected = {str(location.parent / f['path']): f['sha256'] for f in m['files']}
            revision = m['revision']
        else:
            bundle = location.parents[1]
            m = read(bundle / 'MANIFEST.json')
            expected = {str(bundle / f['path']): f['sha256'] for f in m['files']}
            revision = m['datasets'][name]['revision']
        if revision != config['datasets'][name]['source_revision']:
            raise ValueError(name + ' source revision differs from configuration')
        for filename, hashed in result.items():
            if Path(filename).is_relative_to(location) and expected.get(str(Path(filename))) != hashed:
                raise ValueError(name + ' raw source file differs from acquisition manifest')
    return result


def plan(config, run_dir):
    # Planning is offline: credentials are checked only when run is requested.
    checked = inspect(config, check_keys=False)
    if checked['issues']:
        raise ValueError('Configuration unresolved: ' + '; '.join(checked['issues']))
    directory = Path(run_dir).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    write(directory / 'effective-config.json', config)
    cases, exclusions = [], []
    if 'agentdojo' in config['datasets']:
        from .dojo import prepare
        dojo_cases, exclusions = prepare(config)
        cases.extend(dojo_cases)
    for name in (n for n in config['datasets'] if n != 'agentdojo'):
        cases.extend(load_static(config, name))
    if exclusions:
        write(directory / 'planning-failures.json', exclusions)
        # Never silently turn failed task construction into a smaller benchmark.
        raise ValueError('Planning exclusions require an explicit revised task selection; see planning-failures.json')
    if not cases:
        raise ValueError('Empty benchmark plan')
    cases_by_id = {}
    for case in cases:
        case_id = digest([case['dataset_id'], case['item_id']])
        case['case_id'] = case_id
        cases_by_id[case_id] = case
        append(directory / 'cases.jsonl', case)
    if len(cases_by_id) != len(cases):
        raise ValueError('Duplicate case identity')
    rng = random.Random(config['schedule_seed'])
    rng.shuffle(cases)
    schedule = []
    for case in cases:
        for repeat in range(config['repeats']):
            arms = selected_models(config)
            rng.shuffle(arms)
            for arm in arms:
                row = {'episode_id': digest([case['case_id'], arm, repeat]), 'case_id': case['case_id'],
                       'dataset_id': case['dataset_id'], 'item_id': case['item_id'],
                       'family_id': case['family_id'], 'evaluation_mode': case['evaluation_mode'],
                       'split': case.get('source_split', 'selected_native'),
                       'arm': arm, 'repeat': repeat, 'input_sha256': case['input_sha256']}
                schedule.append(row)
                append(directory / 'plan.jsonl', row)
    write(directory / 'environment.json', environment())
    snapshot = directory / 'source'
    for relative in sources():
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    write(directory / 'manifest.json', {'record_kind': 'offline_plan_not_observation',
        'created_at': now(), 'config_sha256': digest(config), 'source_hashes': sources(),
        'git_provenance': git_provenance(),
        'environment_sha256': file_hash(directory / 'environment.json'),
        'runtime_fingerprint': digest(environment()),
        'data_hashes': data_hashes(config), 'cases_sha256': file_hash(directory / 'cases.jsonl'),
        'plan_sha256': file_hash(directory / 'plan.jsonl'), 'planned_cases': len(cases),
        'planned_episodes': len(schedule), 'pricing_sha256': file_hash(absolute(config['pricing_file']))})
    shutil.copyfile(absolute(config['pricing_file']), directory / 'pricing-snapshot.json')
    return {'status': 'planned_no_model_calls', 'cases': len(cases), 'episodes': len(schedule),
            'run_dir': str(directory)}


def verify_inputs(config, directory):
    manifest = read(directory / 'manifest.json')
    checks = [('config', digest(config), manifest['config_sha256']),
              ('code', sources(), manifest['source_hashes']),
              ('data', data_hashes(config), manifest['data_hashes']),
              ('cases', file_hash(directory / 'cases.jsonl'), manifest['cases_sha256']),
              ('plan', file_hash(directory / 'plan.jsonl'), manifest['plan_sha256']),
              ('pricing', file_hash(directory / 'pricing-snapshot.json'), manifest['pricing_sha256']),
              ('environment', digest(environment()), manifest['runtime_fingerprint'])]
    for name, actual, expected in checks:
        if actual != expected:
            raise ValueError(name + ' changed since planning; use a new plan')
    return manifest


def execute(config, run_dir, resume=False, opener=None):
    checked = inspect(config)
    if checked['issues']:
        raise ValueError('Preflight failed: ' + '; '.join(checked['issues']))
    directory = Path(run_dir).resolve()
    if not directory.exists():
        plan(config, directory)
    verify_inputs(config, directory)
    if config['phase'] == 'confirmatory':
        frozen = read(absolute(config['confirmation_protocol_manifest']))
        manifest = read(directory / 'manifest.json')
        required = {'config_sha256': digest(config), 'cases_sha256': manifest['cases_sha256'],
                    'plan_sha256': manifest['plan_sha256'], 'source_hashes': sources(),
                    'data_hashes': manifest['data_hashes']}
        if frozen.get('status') != 'frozen' or not frozen.get('frozen_at') or any(
                frozen.get(k) != v for k, v in required.items()):
            raise ValueError('Confirmatory protocol does not match frozen configuration/plan/code/data')
        for key in ('exposure_audit', 'primary_metrics', 'sample_size_rationale', 'statistical_analysis', 'stopping_policy'):
            if not frozen.get(key):
                raise ValueError('Confirmatory protocol missing ' + key)
    prior = rows(directory / 'episodes.jsonl')
    if prior and not resume:
        raise ValueError('Prior results exist; use --resume with unchanged inputs')
    completed = {r['episode_id'] for r in prior}
    schedule = rows(directory / 'plan.jsonl')
    if len(completed) != len(prior) or completed - {r['episode_id'] for r in schedule}:
        raise ValueError('Duplicate or unplanned episode results')
    finished_attempts = {r['attempt_id'] for r in rows(directory / 'events.jsonl') if r['event'] == 'request_finished'}
    pending = [r for r in rows(directory / 'events.jsonl')
               if r['event'] == 'request_started' and r['attempt_id'] not in finished_attempts]
    if pending:
        raise ValueError('Unresolved in-flight requests from interruption; audit billing before a new run')
    # A partial dynamic episode cannot be replayed as if it were a free continuation.
    started = {r['episode_id'] for r in rows(directory / 'events.jsonl') if r['event'] == 'episode_started'}
    if started - completed:
        raise ValueError('Interrupted episode needs an explicit recovery decision; prior prefix retained')
    preserved = load_monitor(config)
    monitor = preserved.ResourceMonitor('security_bench.run', directory=directory / 'telemetry',
                                       pricing=read(directory / 'pricing-snapshot.json'))
    transport = Transport(config, directory, monitor, opener=opener)
    old_summaries = list((directory / 'telemetry').glob('*.run.json'))
    old_summaries = [read(p) for p in old_summaries if p.stem != monitor.run_id]
    # Budgets cover all resumed invocations, not only the current process.
    old_cost = sum(s.get('known_estimated_cost_usd', 0) for s in old_summaries)
    old_calls = sum(s.get('calls', 0) for s in old_summaries)
    old_wall = sum(s.get('wall_seconds', 0) for s in old_summaries)
    old_api_unknown = any(e.get('provider') != 'local' and e.get('estimated_cost_usd') is None
        for p in (directory / 'telemetry').glob('*.calls.jsonl') for e in rows(p))
    original_check = transport.check_budget
    def total_budget():
        if old_api_unknown:
            raise StopRun('prior_unknown_cost')
        b = config['budget']
        if old_cost + monitor.totals['known_estimated_cost_usd'] + b['reserve_usd_per_call'] > b['max_api_usd']:
            raise StopRun('cumulative_estimated_cost_budget')
        if old_calls + transport.call_count >= b['max_calls']:
            raise StopRun('cumulative_call_budget')
        if old_wall + time.monotonic() - transport.started >= b['max_wall_seconds']:
            raise StopRun('cumulative_wall_budget')
        original_check()
    transport.check_budget = total_budget
    cases = {r['case_id']: r for r in rows(directory / 'cases.jsonl')}
    stopping, attempted = None, 0
    append(directory / 'events.jsonl', {'event': 'invocation_started', 'time': now(), 'monitor_run_id': monitor.run_id})
    try:
        for entry in schedule:
            if entry['episode_id'] in completed:
                continue
            try:
                transport.check_budget()
            except StopRun as exc:
                stopping = str(exc)
                break
            case = cases[entry['case_id']]
            result = dict(entry, started_at=now(), gold=case['gold'], gold_source=case['gold_source'])
            append(directory / 'events.jsonl', {'event': 'episode_started', 'episode_id': entry['episode_id'], 'time': now()})
            start, call_start = time.monotonic(), len(monitor.events)
            judge = Judge(config, entry['arm'], transport)
            try:
                if case['dataset_id'] == 'agentdojo':
                    from .dojo import run_episode
                    result.update(run_episode(config, case, judge, transport, entry['episode_id'], directory))
                else:
                    prediction = judge.judge(case['view'], config['datasets'][case['dataset_id']]['contract'], entry['episode_id'])
                    result.update(status='ok', prediction=prediction)
            except StopRun as exc:
                result.update(status='partial_budget', error_type='StopRun', prediction=None)
                stopping = str(exc)
            except Exception as exc:
                result.update(status='failed', error_type=type(exc).__name__, prediction=None)
                # Preserve failures; no retry based on prediction quality. Transport failures
                # stop scheduling, including usage-unknown network/auth errors.
                if isinstance(exc, (TransportError, OSError)):
                    stopping = 'transport_failure'
            result.update(finished_at=now(), wall_seconds=time.monotonic() - start,
                          monitor_run_id=monitor.run_id, monitor_event_start=call_start,
                          monitor_event_end=len(monitor.events))
            append(directory / 'episodes.jsonl', result)
            attempted += 1
            if stopping:
                break
    except BaseException as exc:
        monitor.finish(exc)
        raise
    else:
        monitor.finish()
    finally:
        append(directory / 'events.jsonl', {'event': 'invocation_finished', 'time': now(),
            'monitor_run_id': monitor.run_id, 'stop_reason': stopping})
        from .report import report
        report(directory)
    return {'status': 'partial' if stopping else 'finished', 'stop_reason': stopping, 'attempted': attempted}
