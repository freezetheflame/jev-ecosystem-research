"""Request adapters and a single metered transport; gold never enters this module."""
import importlib.util
import json
import os
import time
import urllib.error
import urllib.request
import uuid
import http.client
from pathlib import Path
from .common import encode, now, append, redact, absolute, file_hash, secret_values
from .adapters import build_request, parse_prediction, ModelRefusal
from .retries import reservation, unknown_calls


class StopRun(RuntimeError):
    pass


class PolicyRefusal(RuntimeError):
    """Provider-side content policy rejected the request before inference."""

    def __init__(self, status, detail=''):
        super().__init__('Provider policy refusal')
        self.status = status
        self.detail = detail


class TransportError(RuntimeError):
    def __init__(self, status):
        super().__init__('Transport failed; see redacted raw response')
        self.status = status


class ContextRejected(RuntimeError):
    """Known local context rejection: retain failed item, continue the frozen schedule."""


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
        base = opener or urllib.request.build_opener(NoRedirect)
        self.opener = base
        self.last_attempt_id = None
        self.retry_after_seconds = 0
        self.started = time.monotonic()
        self.secrets = secret_values(config)
        self.call_count = 0

    def check_budget(self):
        budget = self.config['budget']
        if time.monotonic() - self.started >= budget['max_wall_seconds']:
            raise StopRun('wall_time_budget')
        if self.call_count >= budget['max_calls']:
            raise StopRun('call_budget')
        reserve_unknown = self.config['execution_policy']['unknown_cost'] == 'reserve_per_unknown_attempt'
        if unknown_calls(self.monitor.events) and not reserve_unknown:
            raise StopRun('unknown_cost_stop')
        allowance = reservation(self.config, self.monitor.events) if reserve_unknown else 0
        if self.monitor.totals['known_estimated_cost_usd'] + allowance + budget['reserve_usd_per_call'] > budget['max_api_usd']:
            raise StopRun('estimated_cost_budget')

    def post(self, payload, model_key, episode_id, component, *, logical_call_id=None, attempt_index=1, retry_of=None):
        self.check_budget()
        model = self.config['models'][model_key]
        key = os.environ[model['api_key_env']] if model.get('api_key_env') else None
        attempt = uuid.uuid4().hex
        self.last_attempt_id = attempt
        self.retry_after_seconds = 0
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
            'logical_call_id': logical_call_id, 'attempt_index': attempt_index, 'retry_of': retry_of,
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
            response_headers = {k: v for k, v in (exc.headers or {}).items()
                                if k.lower() in ('x-request-id', 'request-id', 'content-type', 'retry-after')}
            try:
                self.retry_after_seconds = max(0, float(exc.headers.get('Retry-After', 0)))
            except (ValueError, TypeError, AttributeError):
                pass
            text = body.decode('utf-8', 'replace')
            if (self.config.get('record_kind') in ('full_public_descriptive_evaluation_v1','full_suite_integration_smoke')
                    and model.get('provider')=='local' and status==400
                    and any(marker in text for marker in ('no truncation','input is not truncated'))
                    and 'exceeds' in text):
                error = ContextRejected('Full input exceeds local context; no truncation')
                raise error from None
            if status in (400, 403) and any(marker in text for marker in
                    ('cyber_policy', 'content was flagged', 'content_policy', 'safety_policy',
                     'content_filter', 'content management policy', 'content filtering')):
                # The provider rejected the input before inference. Keep it distinct from a
                # transport failure so one policy refusal does not abort the whole schedule.
                error = PolicyRefusal(status, text[:500])
                raise error from None
            error = TransportError(status)
            raise error from None
        except Exception as exc:
            if isinstance(exc, http.client.IncompleteRead):
                body = exc.partial
            error = exc
            raise
        finally:
            latency = time.monotonic() - start
            (raw / 'response.body').write_bytes(redact(body.decode('utf-8', errors='replace'), self.secrets).encode('utf-8'))
            # Original monitor is the only pricing implementation. Normalize cached-token
            # spelling for telemetry only; the raw response is preserved above.
            telemetry = dict(parsed) if isinstance(parsed, dict) else {}
            usage = telemetry.get('usage') or {}
            usage = dict(usage) if isinstance(usage, dict) else {}
            details = usage.get('input_tokens_details') or usage.get('prompt_tokens_details') or {}
            details = details if isinstance(details, dict) else {}
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
        payload = request(self.config, self.key, state, prompt)
        policy = self.config.get('retry_policy') if model.get('provider') != 'local' else None
        if not policy:
            response = self.transport.post(payload, self.key, episode_id, 'safety_module')
            return parse_prediction(model, response)
        logical = uuid.uuid4().hex
        previous = None
        for index in range(1, (policy['max_attempts'] if policy else 1) + 1):
            category = None
            try:
                response = self.transport.post(payload, self.key, episode_id, 'safety_module',
                    logical_call_id=logical, attempt_index=index, retry_of=previous)
            except PolicyRefusal:
                category = 'refusal'
                if not policy or not policy[category] or index == policy['max_attempts']:
                    raise
            except TransportError as exc:
                category = 'http'
                if not policy or exc.status not in policy['http_statuses'] or index == policy['max_attempts']:
                    raise
            except (OSError, http.client.HTTPException):
                category = 'network'
                if not policy or not policy[category] or index == policy['max_attempts']:
                    raise
            except (ValueError, UnicodeError):
                category = 'decode'
                if not policy or not policy[category] or index == policy['max_attempts']:
                    raise
            else:
                try:
                    prediction = parse_prediction(model, response)
                except (ValueError, TypeError, KeyError, IndexError) as exc:
                    category = 'refusal' if isinstance(exc, ModelRefusal) else 'format'
                    append(self.transport.directory / 'events.jsonl', {'event': 'prediction_parse_failed',
                        'time': now(), 'episode_id': episode_id, 'logical_call_id': logical,
                        'attempt_id': self.transport.last_attempt_id, 'error_type': type(exc).__name__})
                    if not policy or not policy[category] or index == policy['max_attempts']:
                        raise
                else:
                    append(self.transport.directory / 'events.jsonl', {'event': 'prediction_selected',
                        'time': now(), 'episode_id': episode_id, 'logical_call_id': logical,
                        'attempt_id': self.transport.last_attempt_id, 'attempt_index': index})
                    return prediction
            previous = self.transport.last_attempt_id
            delay = min(policy['max_delay_seconds'], max(
                policy['base_delay_seconds'] * 2 ** (index - 1), self.transport.retry_after_seconds))
            self.transport.check_budget()
            append(self.transport.directory / 'events.jsonl', {'event': 'retry_scheduled',
                'time': now(), 'episode_id': episode_id, 'logical_call_id': logical,
                'retry_of': previous, 'next_attempt_index': index + 1, 'category': category,
                'delay_seconds': delay})
            remaining = self.config['budget']['max_wall_seconds'] - (time.monotonic() - self.transport.started)
            time.sleep(max(0, min(delay, remaining)))
