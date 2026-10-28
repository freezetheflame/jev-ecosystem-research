"""Persistent, thread-safe resource telemetry, independent of benchmark scores.

No prompts, credentials, response bodies or exception messages are collected.
"""
from __future__ import annotations

import argparse
import functools
import inspect
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_active = None
_guard = threading.RLock()
_owner = None


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def annotate_run(**metadata):
    """Attach non-sensitive benchmark provenance once its configuration is resolved."""
    if _active is not None:
        with _active.lock:
            _active.summary['metadata'].update(metadata)
            _active._save()


class ResourceMonitor:
    def __init__(self, name, *, directory=None, metadata=None, pricing=None):
        self.run_id = uuid.uuid4().hex
        self.directory = Path(directory or os.getenv('JEV_MONITOR_DIR', ROOT / 'monitor/data'))
        self.directory.mkdir(parents=True, exist_ok=True)
        self.events_path = self.directory / (self.run_id + '.calls.jsonl')
        self.summary_path = self.directory / (self.run_id + '.run.json')
        pricing_path = Path(os.getenv('JEV_MONITOR_PRICING', ROOT / 'config/resource-pricing.json'))
        self.pricing = pricing if pricing is not None else json.loads(pricing_path.read_text(encoding='utf-8'))
        self.lock = threading.Lock()
        self.events = []
        self.totals = dict(calls=0, failed_calls=0, call_seconds=0.0, input_tokens=0,
                           output_tokens=0, missing_usage_calls=0, known_estimated_cost_usd=0.0,
                           unpriced_calls=0)
        self.summary = {'schema_version': 1, 'run_id': self.run_id, 'name': name,
                        'started_at': utc_now(), 'status': 'running', 'metadata': metadata or {},
                        'pricing_snapshot': self.pricing, 'calls_file': str(self.events_path.resolve())}
        self.start = time.perf_counter()
        self._save()

    def _save(self):
        self.summary.update(self.totals, wall_seconds=time.perf_counter() - self.start,
            estimated_cost_usd=self.totals['known_estimated_cost_usd'] if not self.totals['unpriced_calls'] else None)
        temporary = self.summary_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporary.replace(self.summary_path)

    def record(self, *, model, provider, started_at, duration_seconds, response=None, error=None):
        usage = (response or {}).get('usage') or {}
        def count(*keys):
            for key in keys:
                value = usage.get(key)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    return value
            return None
        inp, out = count('input_tokens', 'prompt_tokens'), count('output_tokens', 'completion_tokens')
        model = (response or {}).get('model') or model or 'unknown'
        rates = self.pricing.get(provider + ':' + model)
        cost = None
        if rates and inp is not None and out is not None:
            hit = count('prompt_cache_hit_tokens', 'cache_hit_tokens')
            if 'cache_hit_usd_per_million' in rates:
                if hit is not None and hit <= inp:
                    cost = ((inp-hit)*rates['input_usd_per_million'] + hit*rates['cache_hit_usd_per_million'] + out*rates['output_usd_per_million']) / 1_000_000
            else:
                cost = (inp*rates['input_usd_per_million'] + out*rates['output_usd_per_million']) / 1_000_000
        event = {'run_id': self.run_id, 'started_at': started_at, 'finished_at': utc_now(),
                 'duration_seconds': duration_seconds, 'provider': provider, 'model': model,
                 'status': 'error' if error else 'ok', 'error_type': type(error).__name__ if error else None,
                 'input_tokens': inp, 'output_tokens': out,
                 'cache_hit_tokens': count('prompt_cache_hit_tokens', 'cache_hit_tokens'),
                 'cache_miss_tokens': count('prompt_cache_miss_tokens', 'cache_miss_tokens'),
                 'estimated_cost_usd': cost, 'cost_basis': rates.get('basis') if rates else None}
        with self.lock:
            with self.events_path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + '\n')
                stream.flush()
            self.events.append(event)
            self.totals['calls'] += 1
            self.totals['failed_calls'] += int(error is not None)
            self.totals['call_seconds'] += duration_seconds
            self.totals['input_tokens'] += inp or 0
            self.totals['output_tokens'] += out or 0
            self.totals['missing_usage_calls'] += int(inp is None or out is None)
            self.totals['known_estimated_cost_usd'] += cost or 0
            self.totals['unpriced_calls'] += int(cost is None)
            self._save()

    def finish(self, error=None):
        with self.lock:
            self.summary.update(status='error' if error else 'completed', finished_at=utc_now())
            self._save()


def monitored_call(provider, model=None):
    """Instrument actual transport/inference, so successful calls before errors survive."""
    def decorate(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            monitor = _active
            if monitor is None:
                return fn(*args, **kwargs)
            payload = args[0] if args and isinstance(args[0], dict) else kwargs.get('payload', {})
            selected = model or payload.get('model')
            started_at, start = utc_now(), time.perf_counter()
            response, error = None, None
            try:
                response = fn(*args, **kwargs)
                return response
            except BaseException as exc:
                error = exc
                raise
            finally:
                monitor.record(model=selected, provider=provider, started_at=started_at,
                               duration_seconds=time.perf_counter()-start, response=response, error=error)
        return wrapped
    return decorate


def monitored_run(fn):
    """One invocation = one run, including resumed and empty runs. Worker calls share it."""
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        global _active, _owner
        with _guard:
            if _active is not None:
                if _owner != threading.get_ident():
                    raise RuntimeError('Concurrent benchmark runs in one process require separate processes')
                return fn(*args, **kwargs)
            bound = inspect.signature(fn).bind(*args, **kwargs)
            bound.apply_defaults()
            metadata = {k: str(v) for k, v in bound.arguments.items()
                        if k in ('dataset_path', 'output_path', 'data_path', 'out_path', 'engine', 'workers', 'state_format', 'name', 'variant')}
            config = bound.arguments.get('config') or bound.arguments.get('profile')
            if config is not None:
                metadata.update(model=getattr(config, 'model', None), profile_hash=getattr(config, 'sha256', None))
            namespace = bound.arguments.get('args')
            if namespace is not None:
                metadata.update({k: str(v) for k, v in vars(namespace).items()
                                 if k in ('out', 'backend', 'guards', 'gate', 'tasks', 'seed')})
            monitor = ResourceMonitor(fn.__module__ + '.' + fn.__name__, metadata=metadata)
            _active = monitor
            _owner = threading.get_ident()
        error = None
        try:
            result = fn(*args, **kwargs)
            if isinstance(result, dict):
                monitor.summary['result_counts'] = {k: result[k] for k in ('planned', 'attempted', 'errors', 'remaining') if k in result}
                result['resourceMonitor'] = {'runId': monitor.run_id, 'summary': str(monitor.summary_path.resolve())}
            return result
        except BaseException as exc:
            error = exc
            raise
        finally:
            try:
                monitor.finish(error)
            finally:
                with _guard:
                    _active = None
                    _owner = None
    return wrapped


def main():
    parser = argparse.ArgumentParser(description='List resource usage for benchmark invocations')
    parser.add_argument('--directory', default=os.getenv('JEV_MONITOR_DIR', str(ROOT / 'monitor/data')))
    args = parser.parse_args()
    rows = [json.loads(p.read_text(encoding='utf-8')) for p in Path(args.directory).glob('*.run.json')]
    print(json.dumps(sorted(rows, key=lambda r: r['started_at']), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
