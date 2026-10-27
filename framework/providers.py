"""Label-blind request adapters, based on jev-skill-security transports.

The original monitor is invoked by the runner once per transport attempt;
these adapters must not add a second monitor decorator.
"""
import json
import math
import urllib.error
import urllib.parse
import urllib.request


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def validate_backend(backend):
    if backend.get('kind') not in ('jev', 'openai_chat'):
        raise ValueError('Supported backend kinds: jev, openai_chat; no implicit API conversion')
    for key in ('id', 'provider', 'model', 'endpoint', 'key_env'):
        if not isinstance(backend.get(key), str) or not backend[key].strip():
            raise ValueError('Missing backend field: ' + key)
    import re
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', backend['key_env']):
        raise ValueError('key_env must name an environment variable, not contain a key')
    endpoint = urllib.parse.urlsplit(backend['endpoint'])
    local = endpoint.hostname in ('localhost', '127.0.0.1', '::1')
    if (endpoint.scheme != 'https' and not (endpoint.scheme == 'http' and local)) or not endpoint.netloc:
        raise ValueError('Use HTTPS, or explicit HTTP for a loopback model server')
    if endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:
        raise ValueError('Endpoint must not contain credentials, query or fragment')
    if not isinstance(backend.get('parameters'), dict):
        raise ValueError('parameters must explicitly enumerate sent generation parameters')
    if {'model', 'state', 'questions', 'messages'} & backend['parameters'].keys():
        raise ValueError('Parameters cannot override the frozen model, prompt or state')
    if backend['kind'] == 'jev' and backend['parameters']:
        raise ValueError('Jev generation parameters are unsupported here; leave parameters empty')
    if backend['kind'] == 'jev' and backend.get('decision_type') not in ('noul', 'choice', 'score'):
        raise ValueError('Jev decision_type must be noul, choice or binary score')
    timeout = backend.get('timeout_s')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('An explicit positive timeout_s is required')
    headers = backend.get('headers', {})
    if not isinstance(headers, dict) or any(not isinstance(v, str) for v in headers.values()):
        raise ValueError('headers must be a string map')
    if any(key.lower() in ('authorization', 'x-api-key', 'api-key', 'cookie') for key in headers):
        raise ValueError('Credentials must not be embedded in configuration headers')


def request_body(backend, state, question, llm_system):
    """Only state and the trusted question are read; labels/metadata never enter."""
    if backend['kind'] == 'jev':
        kind = backend['decision_type']
        criteria = {'noul': {'false': question['negative_definition'], 'true': question['positive_definition']},
                    'choice': {'safe': question['negative_definition'], 'unsafe': question['positive_definition']},
                    'score': [question['negative_definition'], question['positive_definition']]}[kind]
        return {'model': backend['model'], 'state': state, 'questions': {
            'risk': {'type': kind, 'instructions': question['instructions'], 'criteria': criteria}}}
    # Explicit YES/confidence contract adapted from the source workspace's
    # bench.deepseek_compare.SYSTEM_V2, without assuming a specific cloud model.
    evidence = {'question': {'instructions': question['instructions'],
                'yes_definition': question['positive_definition'],
                'no_definition': question['negative_definition']}, 'state': state}
    return {**backend['parameters'], 'model': backend['model'], 'messages': [
        {'role': 'system', 'content': llm_system},
        {'role': 'user', 'content': encoded(evidence).decode('utf-8')}]}


def probability(value, minimum=0):
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= 1:
        raise ValueError('Invalid probability/confidence value')
    return float(value)


def decision(backend, response, threshold):
    if backend['kind'] == 'jev':
        kind = backend['decision_type']
        answer = response['answers']['risk']
        if answer.get('type') != kind:
            raise ValueError('Response type differs from the frozen question')
        if kind == 'choice':
            chosen = answer['choice']
            if chosen not in ('safe', 'unsafe'):
                raise ValueError('Unknown choice')
            risk = probability(answer['probabilities']['unsafe'])
            safe = probability(answer['probabilities']['safe'])
            if not math.isclose(risk + safe, 1, abs_tol=.02):
                raise ValueError('Invalid choice distribution')
            if answer['probabilities'][chosen] + .02 < max(safe, risk):
                raise ValueError('Choice contradicts its distribution')
            return risk, int(chosen == 'unsafe'), 'native_choice'
        risk = probability(answer[kind])
        return risk, int(risk >= threshold), 'fixed_threshold'
    choice = response['choices'][0]
    if choice.get('finish_reason') != 'stop':
        raise ValueError('LLM generation is incomplete or refused')
    answer = json.loads(choice['message']['content'])
    if type(answer.get('answer_yes')) is not bool:
        raise ValueError('LLM answer_yes must be a boolean')
    confidence = probability(answer['confidence'], minimum=.5)
    yes = answer['answer_yes']
    return confidence if yes else 1 - confidence, int(yes), 'native_yes_no_self_reported_confidence'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def post(backend, body, secret):
    """Return raw response, parsed response and transport error, without retry."""
    request = urllib.request.Request(backend['endpoint'], data=body, method='POST', headers={
        **backend.get('headers', {}), 'Content-Type': 'application/json', 'Accept': 'application/json',
        'Authorization': 'Bearer ' + secret})
    raw, status, error, request_id = b'', None, None, None
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=backend['timeout_s']) as response:
            raw, status = response.read(), response.status
            request_id = response.headers.get('x-request-id') or response.headers.get('request-id')
    except urllib.error.HTTPError as exc:
        raw, status, error = exc.read(), exc.code, exc
        request_id = exc.headers.get('x-request-id') or exc.headers.get('request-id')
    except Exception as exc:
        error = exc
    redacted = secret.encode('utf-8') in raw
    raw = raw.replace(secret.encode('utf-8'), b'[REDACTED]')
    try:
        parsed = json.loads(raw)
        parsed = parsed if isinstance(parsed, dict) else None
    except (ValueError, UnicodeError):
        parsed = None
    if request_id:
        request_id = request_id.replace(secret, '[REDACTED]')
    return raw, parsed, status, error, redacted, request_id
