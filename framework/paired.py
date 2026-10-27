"""Frozen, serial, static Jev / Chat Completions comparison (no agent loop)."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import time
import uuid

from framework.providers import encoded, validate_backend, request_body, decision, post
from scripts.experiment_report import binary_metrics, monitor_records, read_rows

ROOT = Path(__file__).resolve().parents[1]
MONITOR_SHA = 'f1f3d220f87681e79d65d9baf91e7b1e30733f80312c60b4129a42be8fc00c67'
LEGACY_MODE_NAMESPACE = 'legacy_agent_security_abcd_2026_10_27'
CODE = ('framework/__init__.py', 'framework/paired.py', 'framework/providers.py',
        'scripts/experiment_report.py', 'framework/prompts/llm-yes-confidence.txt',
        'framework/paired-source.json', 'docs/model-evaluation/agent-security-experiment-protocol.md',
        'data/agent-security-study/report.template.md')


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_bytes(encoded(value) + b'\n')


def append(path, value):
    with Path(path).open('ab') as stream:
        stream.write(encoded(value) + b'\n')
        stream.flush()
        os.fsync(stream.fileno())


def environment():
    # No environment variable dump: it may contain credentials.
    return {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
            'machine': platform.machine(), 'processor': platform.processor(),
            'dependencies': 'Python standard library + pinned external monitor',
            'gpu': 'unknown; no GPU/process sampler attached',
            'proxy_hashes': {k: hashlib.sha256(os.getenv(k, '').encode()).hexdigest()
                for k in ('HTTPS_PROXY', 'HTTP_PROXY', 'NO_PROXY', 'https_proxy', 'http_proxy', 'no_proxy')}}


def required(value, keys):
    for key in keys:
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError('Unresolved required field: ' + key)


def validate(config, rows, large=False):
    required(config, ('run_id', 'purpose', 'hypothesis', 'primary_metric', 'classification_unit',
                      'target_event', 'information_boundary', 'label_validation', 'exposure'))
    if config.get('run_kind') not in ('smoke', 'pilot'):
        raise ValueError('This exploratory static runner supports smoke/pilot, not confirmatory inference')
    if config.get('evaluation_mode_namespace') != LEGACY_MODE_NAMESPACE:
        raise ValueError('Explicit legacy A/B/C/D namespace required; revised A1/A2/B/C definitions remain unresolved')
    if config.get('evaluation_mode') not in ('A', 'B', 'C', 'D'):
        raise ValueError('evaluation_mode must be A, B, C or D')
    required(config['dataset'], ('id', 'source', 'revision', 'split', 'selection', 'license'))
    if config['dataset'].get('original_count') is None and not config['dataset'].get('original_count_reason'):
        raise ValueError('Unknown original_count requires a reason')
    original_count = config['dataset'].get('original_count')
    if original_count is not None and (type(original_count) is not int or original_count < 0):
        raise ValueError('original_count must be a nonnegative integer or null with a reason')
    required(config['question'], ('instructions', 'positive_definition', 'negative_definition'))
    if type(config.get('seed')) is not int:
        raise ValueError('Explicit local scheduling seed required')
    from framework.providers import probability
    probability(config.get('threshold'))
    if type(config.get('max_input_chars')) is not int or config['max_input_chars'] <= 0:
        raise ValueError('Explicit max_input_chars required; oversized input is rejected, never truncated')
    if type(config.get('max_calls')) is not int or config['max_calls'] < 1:
        raise ValueError('Explicit max_calls required')
    if (type(config.get('max_wall_seconds')) not in (int, float) or
            not math.isfinite(config['max_wall_seconds']) or config['max_wall_seconds'] <= 0):
        raise ValueError('Explicit positive max_wall_seconds required')
    backends = config['backends']
    if len(backends) < 2 or len({b['id'] for b in backends}) != len(backends):
        raise ValueError('At least two backends with unique IDs required')
    if not {'jev', 'openai_chat'} <= {b['kind'] for b in backends}:
        raise ValueError('Include both a Jev and an LLM backend')
    for backend in backends:
        validate_backend(backend)
        required(backend, ('revision_note', 'deployment_note', 'unsent_defaults'))
    pricing = config.get('pricing')
    if not isinstance(pricing, dict):
        raise ValueError('Explicit pricing snapshot required; {} means unknown, never free')
    for rates in pricing.values():
        required(rates, ('basis',))
        for key in ('input_usd_per_million', 'output_usd_per_million',
                    *(['cache_hit_usd_per_million'] if 'cache_hit_usd_per_million' in rates else [])):
            if type(rates.get(key)) not in (int, float) or not math.isfinite(rates[key]) or rates[key] < 0:
                raise ValueError('Invalid pricing rate')
    if not rows or (len(rows) > 100 and not large):
        raise ValueError('Use 1..100 rows, or explicitly --allow-large for larger datasets')
    ids = set()
    for row in rows:
        required(row, ('id', 'original_id', 'task_family', 'state', 'condition'))
        if row['id'] in ids:
            raise ValueError('Duplicate item id: ' + row['id'])
        ids.add(row['id'])
        if len(row['state']) > config['max_input_chars']:
            raise ValueError('Input exceeds frozen max_input_chars: ' + row['id'])
        if row.get('label') is not None and (type(row['label']) is not int or row['label'] not in (0, 1)):
            raise ValueError('label must be 0=safe, 1=unsafe or null')
        if row.get('label') is not None:
            required(row, ('gold_source', 'gold_validation'))
            if row.get('label_scope') != config['evaluation_mode']:
                raise ValueError('Gold scope must match the evaluated mode; never inherit full-trace labels')
        if config['evaluation_mode'] in ('B', 'C'):
            required(row, ('cutoff', 'visibility_validation'))
    if len(rows) * len(backends) > config['max_calls']:
        raise ValueError('Planned paired calls exceed max_calls; select data explicitly before prepare')


def prepare(data, config_path, out, workspace, large=False):
    out, workspace = Path(out).resolve(), Path(workspace).resolve()
    config = json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    rows = read_rows(Path(data))
    validate(config, rows, large)
    monitor = workspace / 'jev_skill/monitor.py'
    if sha(monitor) != MONITOR_SHA:
        raise ValueError('External monitor differs from the preserved implementation; validate it before use')
    system = (ROOT / 'framework/prompts/llm-yes-confidence.txt').read_text(encoding='utf-8').strip()
    config.update(llm_system=system, monitor_source=str(monitor), monitor_sha256=MONITOR_SHA,
                  concurrency=1, retries=0, truncation='reject', repeats=1,
                  evidence_type='offline_static', prepared_at=now())
    # Freeze all rows, then shuffle item blocks and backend order within each block.
    rng = random.Random(config['seed'])
    order = list(rows)
    rng.shuffle(order)
    cells = []
    for row in order:
        backends = list(config['backends'])
        rng.shuffle(backends)
        for backend in backends:
            cells.append({'cell_id': f'c{len(cells):07}', 'item_id': row['id'], 'backend': backend['id']})
    out.mkdir(parents=True, exist_ok=False)
    (out / 'raw').mkdir()
    (out / 'code').mkdir()
    save(out / 'effective-config.json', config)
    shutil.copyfile(data, out / 'dataset.jsonl')
    for cell in cells:
        append(out / 'plan.jsonl', cell)
    for relative in CODE:
        target = out / 'code' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    save(out / 'environment.json', environment())
    manifest = {'schema_version': 1, 'git_commit': commit.stdout.strip() or None,
                'code': {p: sha(ROOT / p) for p in CODE},
                'source_state': 'Exact related source snapshots include dirty/untracked changes; commit alone is insufficient',
                'inputs': {p: sha(out / p) for p in ('effective-config.json', 'dataset.jsonl', 'plan.jsonl', 'environment.json')},
                'monitor_sha256': MONITOR_SHA,
                'protocol_sha256': sha(ROOT / 'docs/model-evaluation/agent-security-experiment-protocol.md'),
                'dataset_source_path': str(Path(data).resolve()),
                'dataset_count': len(rows), 'item_ids': [r['id'] for r in rows]}
    save(out / 'manifest.json', manifest)
    (out / 'reproduce.md').write_text(
        'Run from this repository, or the saved code/ directory with Python of environment.json.\n\n'
        f'`python -m framework.paired run --out "{out}" --env-file <private-env-file>`\n\n'
        f'`python -m framework.paired report --out "{out}"`\n\n'
        'Restore the exact external monitor at effective-config.monitor_source. No credentials are copied. '
        'Already finished cells, including errors, are skipped. Uncertain in-flight calls require reconciliation; '
        'they are never replayed automatically. New configuration or repairs require a new output directory.\n', encoding='utf-8')
    report(out)
    return manifest


def verify(out):
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    for relative, expected in manifest['inputs'].items():
        if sha(out / relative) != expected:
            raise ValueError('Frozen input changed: ' + relative)
    for relative, expected in manifest['code'].items():
        if sha(ROOT / relative) != expected:
            raise ValueError('Code changed; use saved code/ or prepare a new run: ' + relative)
    config = json.loads((out / 'effective-config.json').read_text(encoding='utf-8'))
    if sha(config['monitor_source']) != config['monitor_sha256']:
        raise ValueError('External monitor changed')
    previous = json.loads((out / 'environment.json').read_text(encoding='utf-8'))
    current = environment()
    if any(previous[key] != current[key] for key in ('python', 'platform', 'machine', 'proxy_hashes')):
        raise ValueError('Execution environment changed; prepare a new run')
    return config


def load_env(path):
    # Same precedence as source client.load_env: process variables win.
    if path:
        for raw in Path(path).read_text(encoding='utf-8-sig').splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            name, value = line.split('=', 1)
            os.environ.setdefault(name.strip(), value.strip().strip('\"\''))


def execute(out, env_file=None, transport=post):
    out = Path(out).resolve()
    lock = out / '.execution-lock'
    with lock.open('x', encoding='utf-8') as stream:
        stream.write(f'{os.getpid()} {now()}\n')
    try:
        return _execute(out, env_file, transport)
    finally:
        lock.unlink()


def _execute(out, env_file, transport):
    out = Path(out).resolve()
    load_env(env_file)
    config = verify(out)
    plan = read_rows(out / 'plan.jsonl')
    results = read_rows(out / 'results.jsonl')
    report(out)  # Verify completed cells and their raw hashes before resuming.
    completed = {r['cell_id'] for r in results}
    started = {e['cell_id'] for e in read_rows(out / 'events.jsonl') if e['event'] == 'started'}
    if started - completed:
        raise ValueError('Uncertain in-flight calls exist; reconcile raw/provider records before any continuation')
    remaining = [c for c in plan if c['cell_id'] not in completed]
    if not remaining:
        return report(out)
    keys = {b['id']: os.environ.get(b['key_env'], '').strip() for b in config['backends']}
    if not all(keys.values()):
        raise ValueError('Required key environment variable missing; no calls started')
    if any(secret in (out / name).read_text(encoding='utf-8') for secret in keys.values()
           for name in ('effective-config.json', 'dataset.jsonl')):
        raise ValueError('Credential found in frozen input; remove it and prepare a new run')
    spec = importlib.util.spec_from_file_location('paired_external_monitor', config['monitor_source'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monitor = module.ResourceMonitor('framework.paired', directory=out / 'telemetry',
                                     metadata={'run_id': config['run_id'], 'role': 'security_judge'}, pricing=config['pricing'])
    append(out / 'invocations.jsonl', {'monitor_run_id': monitor.run_id, 'started_at': now(), 'environment': environment()})
    rows = {r['id']: r for r in read_rows(out / 'dataset.jsonl')}
    backends = {b['id']: b for b in config['backends']}
    error = None
    try:
        for cell in remaining:
            # Includes previous invocation wall time. A request may finish after this limit.
            used = sum(r['wall_seconds'] for r in monitor_records(list((out / 'telemetry').glob('*.run.json'))))
            if len(started) >= config['max_calls'] or used >= config['max_wall_seconds']:
                append(out / 'events.jsonl', {'event': 'stopped', 'reason': 'pre-call limit', 'at': now()})
                break
            row, backend = rows[cell['item_id']], backends[cell['backend']]
            stem = out / 'raw' / cell['cell_id']
            body = encoded(request_body(backend, row['state'], config['question'], config['llm_system']))
            Path(str(stem) + '.request.json').write_bytes(body)
            started_at, start = now(), time.perf_counter()
            append(out / 'events.jsonl', {**cell, 'event': 'started', 'at': started_at,
                                        'monitor_run_id': monitor.run_id, 'request_sha256': hashlib.sha256(body).hexdigest()})
            started.add(cell['cell_id'])
            raw, response, status, transport_error, redacted, request_id = transport(backend, body, keys[backend['id']])
            seconds = time.perf_counter() - start
            Path(str(stem) + '.response.bin').write_bytes(raw)
            monitor.record(model=backend['model'], provider=backend['provider'], started_at=started_at,
                           duration_seconds=seconds, response=response, error=transport_error)
            prediction, score, mapping, parse_error = None, None, None, None
            if transport_error is None:
                try:
                    score, prediction, mapping = decision(backend, response, config['threshold'])
                except (KeyError, ValueError, TypeError, IndexError) as exc:
                    parse_error = type(exc).__name__
            result = {**cell, 'started_at': started_at, 'finished_at': now(), 'seconds': seconds,
                      'http_status': status, 'error_type': type(transport_error).__name__ if transport_error else parse_error,
                      'status': 'transport_error' if transport_error else 'parse_error' if parse_error else 'ok',
                      'prediction': prediction, 'score': score, 'mapping': mapping,
                      'returned_model': (response or {}).get('model'), 'provider_request_id': request_id,
                      'response_id': (response or {}).get('id'),
                      'monitor_run_id': monitor.run_id, 'secret_redacted_in_response': redacted,
                      'monitor_call_index': len(monitor.events) - 1,
                      'request_sha256': sha(str(stem) + '.request.json'), 'response_sha256': sha(str(stem) + '.response.bin')}
            append(out / 'results.jsonl', result)
            append(out / 'events.jsonl', {**cell, 'event': 'finished', 'at': now(), 'status': result['status']})
            if status in (401, 402, 403, 451):
                append(out / 'events.jsonl', {'event': 'stopped', 'reason': 'access/billing/region HTTP', 'http_status': status, 'at': now()})
                break
    except BaseException as exc:
        error = exc
        raise
    finally:
        monitor.finish(error)
        report(out)
    return out


def report(out):
    out = Path(out).resolve()
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    for relative, expected in manifest['inputs'].items():
        if sha(out / relative) != expected:
            raise ValueError('Frozen input changed: ' + relative)
    config = json.loads((out / 'effective-config.json').read_text(encoding='utf-8'))
    rows = {r['id']: r for r in read_rows(out / 'dataset.jsonl')}
    plan = read_rows(out / 'plan.jsonl')
    results = read_rows(out / 'results.jsonl')
    if len({r['cell_id'] for r in results}) != len(results):
        raise ValueError('Duplicate result cells; no implicit latest/best attempt selection')
    indexed = {r['cell_id']: r for r in results}
    planned = {c['cell_id']: c for c in plan}
    for result in results:
        cell = planned.get(result['cell_id'])
        if not cell or any(result[k] != cell[k] for k in ('item_id', 'backend')):
            raise ValueError('Result does not match frozen paired plan')
        for kind, suffix in (('request', '.request.json'), ('response', '.response.bin')):
            if sha(out / 'raw' / (result['cell_id'] + suffix)) != result[kind + '_sha256']:
                raise ValueError('Raw artifact changed: ' + result['cell_id'])
    started = {r['cell_id'] for r in read_rows(out / 'events.jsonl') if r['event'] == 'started'}
    monitors = monitor_records(list((out / 'telemetry').glob('*.run.json')))
    telemetry = {m['run_id']: read_rows(Path(m['calls_file'])) for m in monitors}
    by_backend = {}
    for backend in config['backends']:
        predictions = []
        durations = []
        call_records = []
        for cell in plan:
            if cell['backend'] != backend['id']:
                continue
            row, result = rows[cell['item_id']], indexed.get(cell['cell_id'], {})
            predictions.append({'gold_label': None if row.get('label') is None else str(row['label']),
                'predicted_label': str(result.get('prediction')), 'gold_source': row.get('gold_source'),
                'prediction_status': result.get('status', 'uncertain' if cell['cell_id'] in started else 'not_started')})
            if result:
                durations.append(result['seconds'])
                call_records.append(telemetry[result['monitor_run_id']][result['monitor_call_index']])
        metrics = binary_metrics(predictions, positive='1', negative='0')
        metrics['metric_status'] = 'computed' if metrics['valid_n'] else 'not_computable_no_valid_gold_prediction_pairs'
        ordered = sorted(durations)
        metrics['latency_seconds'] = {'n': len(ordered), 'total': sum(ordered),
            'mean': sum(ordered) / len(ordered) if ordered else None,
            'p50': ordered[math.ceil(.50 * len(ordered)) - 1] if ordered else None,
            'p95': ordered[math.ceil(.95 * len(ordered)) - 1] if ordered else None,
            'definition': 'nearest-rank; all completed HTTP attempts including errors; excludes local parsing'}
        metrics['resources'] = {'calls': len(call_records),
            'known_input_tokens': sum(c['input_tokens'] or 0 for c in call_records),
            'known_output_tokens': sum(c['output_tokens'] or 0 for c in call_records),
            'missing_usage_calls': sum(c['input_tokens'] is None or c['output_tokens'] is None for c in call_records),
            'unpriced_calls': sum(c['estimated_cost_usd'] is None for c in call_records),
            'known_api_estimate_usd': sum(c['estimated_cost_usd'] or 0 for c in call_records) if call_records else None,
            'api_estimate_usd': sum(c['estimated_cost_usd'] for c in call_records) if call_records and
                all(c['estimated_cost_usd'] is not None for c in call_records) else None}
        by_backend[backend['id']] = metrics
    complete = len(results) == len(plan)
    summary = {'generated_at': now(), 'run_id': config['run_id'], 'run_kind': config['run_kind'],
        'evaluation_mode': config['evaluation_mode'], 'evaluation_mode_namespace': config['evaluation_mode_namespace'],
        'status': 'complete_with_errors' if complete and any(r['status'] != 'ok' for r in results) else
                  'complete' if complete else 'partial' if started else 'prepared_not_executed',
        'dataset': config['dataset'], 'dataset_sha256': sha(out / 'dataset.jsonl'),
        'unique_items': len(rows), 'item_ids': list(rows), 'original_ids': sorted({r['original_id'] for r in rows.values()}),
        'task_families': sorted({r['task_family'] for r in rows.values()}),
        'gold_counts': dict(Counter(str(r.get('label')) for r in rows.values())),
        'condition_counts': dict(Counter(r['condition'] for r in rows.values())),
        'processed_item_ids': sorted({r['item_id'] for r in results}),
        'started_item_ids': sorted({planned[c]['item_id'] for c in started}),
        'planned_calls': len(plan), 'started_calls': len(started), 'finished_calls': len(results),
        'unresolved_calls': len(started - indexed.keys()), 'retries': 0, 'per_backend': by_backend,
        'resource_monitor': monitors, 'local_compute_cost': 'unpriced',
        'known_api_estimate_usd': sum(m['known_estimated_cost_usd'] for m in monitors) if monitors else None,
        'api_estimate_usd': sum(m['estimated_cost_usd'] for m in monitors) if monitors and
            not (started - indexed.keys()) and all(m['estimated_cost_usd'] is not None for m in monitors) else None,
        'summed_invocation_wall_seconds': sum(m['wall_seconds'] for m in monitors) if monitors else None,
        'elapsed_first_start_to_latest_finish_seconds': (datetime.fromisoformat(max(r['finished_at'] for r in results)) -
            datetime.fromisoformat(min(r['started_at'] for r in results))).total_seconds() if results else None,
        'scope': 'offline static security judgment; ASR, task utility, causal protection and replacement inference NA',
        'inference': 'descriptive only; no paired confidence interval/equivalence test; no calibration claim',
        'missing_measurements': 'server GPU/energy unknown; client GPU/CPU peaks not sampled; bill not reconciled',
        'effective_config_sha256': sha(out / 'effective-config.json')}
    target = out / 'analysis' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
    target.mkdir(parents=True)
    save(target / 'summary.json', summary)
    save(target / 'analysis-inputs.json', {'analysis_code_sha256': {p: sha(ROOT / p) for p in CODE},
        'source_sha256': {str(p.relative_to(out)): sha(p) for p in
            [out / 'manifest.json', out / 'effective-config.json', out / 'dataset.jsonl', out / 'plan.jsonl',
             *[out / f for f in ('events.jsonl', 'results.jsonl', 'invocations.jsonl') if (out / f).exists()],
             *sorted((out / 'telemetry').glob('*.*json*'))]}})
    text = '\n'.join(['# Static paired experiment record', '', 'Generated from raw records; no hand-edited results.',
        '', '## 1. Experiment and dataset', '', f"Status: {summary['status']}; kind: {config['run_kind']}; Mode: {config['evaluation_mode']}.",
        'Exact IDs/counts, label coverage and failures: summary.json and plan.jsonl.',
        'Source, revision, selection, license, hypothesis and exposure: effective-config.json.',
        '', '## 2. Time and API fees', '', 'Original monitor summaries and price snapshots: telemetry/.',
        'All completed calls, including failed transports, enter latency totals. Serial execution; no warm-up or retries.',
        'Summed invocation wall time includes local I/O; elapsed time includes gaps between invocations.',
        'API fees are usage estimates, not bills. Unknown prices/usage remain null; local compute is unpriced.',
        '', '## 3. TP / FP / TN / FN', '', 'Positive=1, as defined by question.positive_definition; negative=0.',
        f"Unit: {config['classification_unit']}; target: {config['target_event']}.",
        'Jev noul/binary score use the frozen threshold; choice uses native choice; LLM uses native answer_yes.',
        'Missing gold and failures are excluded from the confusion matrix and remain in coverage denominators.',
        'ASR/task utility/real-time blocking: NA (static judgments). Confidence intervals: not implemented.',
        '', '## 4. Models and effective parameters', '', 'effective-config.json contains every sent parameter, headers without credentials,',
        'provider/endpoint/model, unresolved server defaults, deployment/revision notes and limits.',
        'Returned models/response IDs: results.jsonl. Local/server hardware limits: environment.json and summary.json.',
        '', '## 5. Prompts and raw outputs', '', 'Full question and LLM system prompt: effective-config.json.',
        'Exact request bytes and raw response bodies: raw/. No truncation, chunking, automatic repair or answer-based retries.',
        'Transport failures retain HTTP status/error class and full response body. Credential echoes are redacted and flagged.',
        '', '## 6. Reproduction, integrity and limits', '', 'Commands: reproduce.md. Input/code hashes and IDs: manifest.json; source snapshot: code/.',
        'Python/OS and hardware availability: environment.json; per-invocation environment: invocations.jsonl.',
        'Visibility and gold validation are supplied adapter evidence, not independently proved by this runner.',
        'No full Agent environment or tool execution is provided. Service versions/defaults may drift.',
        '', '## Derived values', '', '```json', json.dumps(summary, ensure_ascii=False, indent=2), '```', ''])
    (target / 'report.md').write_text(text, encoding='utf-8')
    # Old versions remain in analysis/. This is only the latest generated view.
    (out / 'report.md').write_text(text, encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare', help='Offline validation and freezing; no API calls')
    for flag in ('data', 'config', 'out', 'workspace'):
        prep.add_argument('--' + flag, type=Path, required=True)
    prep.add_argument('--allow-large', action='store_true')
    run = sub.add_parser('run', help='Execute frozen paired calls; may incur API fees')
    run.add_argument('--out', type=Path, required=True)
    run.add_argument('--env-file', type=Path)
    analysis = sub.add_parser('report', help='Offline reanalysis without API calls')
    analysis.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.data, args.config, args.out, args.workspace, args.allow_large)
        print(json.dumps({'status': 'prepared_not_executed', 'items': result['dataset_count']}, ensure_ascii=False))
    elif args.command == 'run':
        execute(args.out, args.env_file)
        print(json.dumps({'output': str(args.out.resolve())}))
    else:
        result = report(args.out)
        print(json.dumps({'status': result['status'], 'finished_calls': result['finished_calls']}))


if __name__ == '__main__':
    main()
