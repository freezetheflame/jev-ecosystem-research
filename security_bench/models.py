"""Request adapters and a single metered transport; gold never enters this module."""
import importlib.util
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from .common import encode, now, append, redact, absolute, file_hash, secret_values
from .adapters import build_request, parse_prediction


class StopRun(RuntimeError):
    pass


class TransportError(RuntimeError):
    def __init__(self, status):
        super().__init__('Transport failed; see redacted raw response')
        self.status = status


def load_monitor(config):
    path = absolute(config['monitor_workspace']) / 'jev_skill/monitor.py'
    if file_hash(path) != config['monitor_sha256']:
        raise ValueError('Preserved monitor differs from configured revision')
    spec = importlib.util.spec_from_file_location('security_bench_preserved_monitor', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class Transport:
    def __init__(self, config, run_dir, monitor, opener=None):
        self.config, self.directory, self.monitor = config, Path(run_dir), monitor
        self.opener = opener or urllib.request.build_opener(NoRedirect)
        self.started = time.monotonic()
        self.secrets = secret_values(config)
        self.call_count = 0

    def check_budget(self):
        budget = self.config['budget']
        if time.monotonic() - self.started >= budget['max_wall_seconds']:
            raise StopRun('wall_time_budget')
        if self.call_count >= budget['max_calls']:
            raise StopRun('call_budget')
        if any(e.get('provider') != 'local' and e.get('estimated_cost_usd') is None for e in self.monitor.events):
            raise StopRun('unknown_cost_stop')
        if self.monitor.totals['known_estimated_cost_usd'] + budget['reserve_usd_per_call'] > budget['max_api_usd']:
            raise StopRun('estimated_cost_budget')

    def post(self, payload, model_key, episode_id, component):
        self.check_budget()
        model = self.config['models'][model_key]
        key = os.environ[model['api_key_env']] if model.get('api_key_env') else None
        attempt = uuid.uuid4().hex
        raw = self.directory / 'raw' / attempt
        raw.mkdir(parents=True)
        request_bytes = encode(payload)
        safe_bytes = redact(request_bytes.decode('utf-8'), self.secrets).encode('utf-8')
        if safe_bytes != request_bytes:
            raise ValueError('Configured credential appears in request body')
        (raw / 'request.json').write_bytes(request_bytes)
        headers = {'Content-Type': 'application/json', **model['headers']}
        append(self.directory / 'events.jsonl', {'event': 'request_started', 'attempt_id': attempt,
            'episode_id': episode_id, 'component': component, 'model_key': model_key,
            'endpoint': model['endpoint'], 'headers': headers, 'time': now(),
            'request_path': str(raw.relative_to(self.directory) / 'request.json'),
            'request_sha256': __import__('hashlib').sha256(request_bytes).hexdigest()})
        # Credentials are added only after request persistence and are never written to artifacts.
        if key:
            if model.get('auth_scheme', 'bearer') == 'x_api_key':
                headers['x-api-key'] = key
            else:
                headers['Authorization'] = 'Bearer ' + key
        req = urllib.request.Request(model['endpoint'], data=request_bytes, headers=headers, method='POST')
        start, started_at = time.monotonic(), now()
        remaining = self.config['budget']['max_wall_seconds'] - (start - self.started)
        status, body, parsed, error, response_headers = None, b'', None, None, {}
        self.call_count += 1
        try:
            with self.opener.open(req, timeout=min(model['timeout_seconds'], remaining)) as response:
                status, body = response.status, response.read()
                response_headers = {k: v for k, v in response.headers.items()
                                    if k.lower() in ('x-request-id', 'request-id', 'content-type')}
            parsed = json.loads(body)
            if not isinstance(parsed, dict):
                raise ValueError('Response must be an object')
            if parsed.get('error'):
                raise ValueError('Provider returned an error object')
            return parsed
        except urllib.error.HTTPError as exc:
            status, body = exc.code, exc.read()
            error = TransportError(status)
            raise error from None
        except Exception as exc:
            error = exc
            raise
        finally:
            latency = time.monotonic() - start
            (raw / 'response.body').write_bytes(redact(body.decode('utf-8', errors='replace'), self.secrets).encode('utf-8'))
            # Original monitor is the only pricing implementation. Normalize cached-token
            # spelling for telemetry only; the raw response is preserved above.
            telemetry = dict(parsed or {})
            usage = dict(telemetry.get('usage') or {})
            details = usage.get('input_tokens_details') or usage.get('prompt_tokens_details') or {}
            if 'cached_tokens' in details:
                usage['cache_hit_tokens'] = details['cached_tokens']
            if model['api'] == 'anthropic_messages':
                # Anthropic separates uncached input, cache reads and cache writes.
                # The preserved monitor cannot price all creation TTL classes.
                # Keep such calls unpriced rather than under-report their fees.
                cache_write = usage.get('cache_creation_input_tokens', 0)
                cache_read = usage.get('cache_read_input_tokens', 0)
                if cache_write or cache_read:
                    usage = {}  # Raw usage above remains intact; unknown fees stop the next API call.
            telemetry['usage'] = usage
            self.monitor.record(model=model['model_id'], provider=model['provider'], started_at=started_at,
                duration_seconds=latency, response=telemetry, error=error)
            event = self.monitor.events[-1]
            append(self.directory / 'events.jsonl', {'event': 'request_finished', 'attempt_id': attempt,
                'episode_id': episode_id, 'component': component, 'time': now(), 'http_status': status,
                'response_headers': response_headers, 'error_type': type(error).__name__ if error else None,
                'monitor_run_id': self.monitor.run_id, 'monitor_event_index': len(self.monitor.events) - 1,
                'telemetry': event})


def request(config, model_key, state, instructions):
    return build_request(config['models'][model_key], state, instructions)


def output_text(response):
    if response.get('status') not in (None, 'completed'):
        raise ValueError('Response is not completed')
    pieces = [part['text'] for entry in response.get('output', []) if entry.get('type') == 'message'
              for part in entry.get('content', []) if part.get('type') == 'output_text']
    return ''.join(pieces)


class Judge:
    def __init__(self, config, model_key, transport):
        self.config, self.key, self.transport = config, model_key, transport

    def judge(self, state, contract, episode_id):
        prompt = self.config['contracts'][contract]['instructions']
        model = self.config['models'][self.key]
        response = self.transport.post(request(self.config, self.key, state, prompt), self.key, episode_id, 'safety_module')
        return parse_prediction(model, response)
