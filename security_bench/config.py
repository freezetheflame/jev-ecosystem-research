"""Preflight is offline and never silently fills unresolved study choices."""
import os
import math
from pathlib import Path
from urllib.parse import urlsplit
from .common import absolute, file_hash, read, encode, secret_values
from .datasets import paths, agentharm_files
from .adapters import selected_models, build_request, adapter

DATASETS = {'maliciousskillbench', 'agentharm', 'mcphunt', 'atbench'}
LEGACY_DATASETS = {'agentdojo', 'agentharm', 'mcphunt', 'atbench'}
STATIC_CONTRACTS = {'agentharm': 'request_risk_classification',
                    'maliciousskillbench': 'skill_risk_classification',
                    'mcphunt': 'full_trace_risk_classification', 'atbench': 'full_trace_risk_classification'}


def inspect(config, check_keys=True):
    issues, available = [], {}
    active = set(config.get('datasets', {}))
    has_dojo = 'agentdojo' in active
    try:
        selected = selected_models(config)
    except (ValueError, KeyError) as exc:
        selected = []
        issues.append(str(exc))
    active_models = {k:v for k,v in config.get('models', {}).items() if k in selected or (k == 'main_agent' and has_dojo)}
    serialized = encode(config).decode('utf-8')
    if any(value in serialized for value in secret_values(config)):
        issues.append('Configuration contains a live credential; move it to the named environment variable')
    def need(value, name):
        if value is None or value == '':
            issues.append(name + ' is unresolved')
            return False
        return True
    if config.get('phase') not in ('pilot', 'confirmatory'):
        issues.append('phase must be explicitly pilot or confirmatory')
    if config.get('concurrency') != 1:
        issues.append('Only serial concurrency=1 is implemented for unambiguous call accounting')
    if config.get('execution_policy') != {'retry': 'none', 'overflow': 'provider_error_no_truncation',
            'client_cache': 'disabled', 'unknown_cost': 'stop_before_next_request',
            'context': 'full_native_input_no_automatic_chunking'}:
        issues.append('execution_policy must match implemented no-retry/no-truncation policy')
    if type(config.get('repeats')) is not int or config['repeats'] < 1:
        issues.append('repeats must be an explicit positive integer')
    if type(config.get('schedule_seed')) is not int:
        issues.append('schedule_seed must be explicit (local scheduling only, not a model seed)')
    for field in ('max_calls', 'max_wall_seconds', 'max_api_usd', 'reserve_usd_per_call'):
        value = config.get('budget', {}).get(field)
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            issues.append('budget.' + field + ' must be an explicit positive value')
    need(config.get('pricing_file'), 'pricing_file')
    if config.get('pricing_file') and not absolute(config['pricing_file']).is_file():
        issues.append('pricing_file not found')
    monitor = absolute(config['monitor_workspace']) / 'jev_skill/monitor.py'
    available['preserved_monitor'] = monitor.is_file()
    if not monitor.is_file() or file_hash(monitor) != config.get('monitor_sha256'):
        issues.append('monitor is missing or hash differs')
    for name, model in active_models.items():
        allowed = {'display_name', 'model_id', 'api', 'provider', 'endpoint', 'api_key_env', 'headers',
                   'parameters', 'parameter_status', 'timeout_seconds', 'decision_type', 'choice_criteria',
                   'adapter', 'input_field', 'yes_means', 'query', 'deployment', 'auth_scheme'}
        if set(model) - allowed:
            issues.append(name + ' has unknown fields; credentials must only be in named environment variables')
        for field in ('model_id', 'endpoint', 'api', 'timeout_seconds', 'parameter_status'):
            need(model.get(field), f'models.{name}.{field}')
        endpoint = model.get('endpoint')
        if endpoint:
            url = urlsplit(endpoint)
            local_http = (model.get('provider') == 'local' and url.scheme == 'http'
                          and url.hostname in ('localhost', '127.0.0.1', '::1'))
            if (url.scheme != 'https' and not local_http) or url.username or url.password or url.query or url.fragment:
                issues.append(name + ' endpoint must be HTTPS (or local-provider loopback HTTP), without credentials/query/fragment')
        if model.get('api') not in ('jev', 'openai_responses', 'openai_chat', 'anthropic_messages', 'gliguard'):
            issues.append(name + ' has no supported API selected')
        if type(model.get('parameters')) is not dict:
            issues.append(name + ' parameters must be explicit object, not an unspecified default')
        else:
            forbidden = {'model', 'messages', 'input', 'instructions', 'state', 'questions', 'tools',
                         'api_key', 'authorization', 'stream', 'previous_response_id', 'system', 'text', 'schema'}
            if forbidden.intersection(model['parameters']):
                issues.append(name + ' parameters override controlled fields')
        if type(model.get('timeout_seconds')) not in (int, float) or model['timeout_seconds'] <= 0:
            issues.append(name + '.timeout_seconds must be positive')
        if type(model.get('headers')) is not dict or any(k.lower() not in (
                'typesafe-danger-zone-long-context', 'anthropic-version') for k in model.get('headers', {})):
            issues.append(name + ' has unsupported or credential-bearing headers')
        key_var = model.get('api_key_env')
        if model.get('auth_scheme', 'bearer') not in ('bearer', 'x_api_key'):
            issues.append(name + ' auth_scheme must be bearer or x_api_key')
        if (not key_var and model.get('provider') != 'local') or (key_var and check_keys and not os.environ.get(key_var)):
            issues.append(name + ' credential environment variable is absent (value never displayed)')
        if model.get('provider') == 'local':
            deployment = model.get('deployment') or {}
            for field in ('artifact_revision', 'runtime', 'runtime_version', 'dtype', 'hardware', 'context_limit', 'launch_command', 'interface_verified'):
                need(deployment.get(field), name + '.deployment.' + field)
            if deployment.get('interface_verified') is not True:
                issues.append(name + ' local deployment interface is not verified')
        if model.get('api') == 'anthropic_messages':
            if not model.get('headers', {}).get('anthropic-version'):
                issues.append(name + ' requires anthropic-version')
            if type(model.get('parameters', {}).get('max_tokens')) is not int or model['parameters']['max_tokens'] <= 0:
                issues.append(name + ' requires explicit positive max_tokens')
        if name != 'main_agent':
            try:
                build_request(model, {model.get('input_field') or 'user_request': 'OFFLINE PREFLIGHT FIXTURE'}, 'OFFLINE PREFLIGHT')
            except (ValueError, TypeError, KeyError) as exc:
                issues.append(name + ' request contract: ' + str(exc))
        if model.get('api') == 'jev':
            criteria = model.get('choice_criteria')
            if model.get('decision_type') != 'choice':
                issues.append(name + '.decision_type must be choice')
            if not isinstance(criteria, dict) or list(criteria) != ['safe', 'unsafe'] or any(
                    not isinstance(v, str) or not v.strip() for v in criteria.values()):
                issues.append(name + '.choice_criteria must define safe then unsafe with nonempty descriptions')
    if has_dojo and 'main_agent' not in config.get('models', {}):
        issues.append('Missing active safety/main-agent model configurations')
    if config.get('pricing_file') and absolute(config['pricing_file']).is_file():
        pricing = read(absolute(config['pricing_file']))
        for name, m in active_models.items():
            if m.get('provider') == 'local':
                if str(m.get('provider')) + ':' + str(m.get('model_id')) in pricing:
                    issues.append(name + ' local compute must remain unpriced; keep estimates separate')
                continue
            rate = pricing.get(str(m.get('provider')) + ':' + str(m.get('model_id')))
            if not rate or not rate.get('basis') or any(type(rate.get(k)) not in (int, float)
                    or not math.isfinite(rate[k]) or rate[k] < 0
                    for k in ('input_usd_per_million', 'output_usd_per_million')):
                issues.append(name + ' needs explicit USD token rates and dated pricing basis; missing is not zero')
    if not active or not (active <= DATASETS or active == LEGACY_DATASETS):
        issues.append('Select a nonempty subset of current datasets, or the preserved legacy four-dataset config')
    locations = paths(config)
    for name in active:
        spec = config.get('datasets', {}).get(name, {})
        available[name] = locations[name].exists()
        if not available[name]:
            issues.append(name + ' source path is missing')
        for field in ('mode_code', 'mode_definition', 'contract', 'source_revision', 'exposure_status'):
            need(spec.get(field), 'datasets.' + name + '.' + field)
        if spec.get('mode_code') not in ('A1', 'A2', 'B', 'C'):
            issues.append(name + ' must use an explicit current Mode code')
        if spec.get('mode_code') in ('A1', 'A2') and spec.get('contract') not in (None, 'request_risk_classification', 'skill_risk_classification', 'input_inspection'):
            issues.append(name + ' A1/A2 inherit Mode A input inspection; action authorization or full-trace auditing is not this mode')
        if name in STATIC_CONTRACTS and spec.get('contract') != STATIC_CONTRACTS[name]:
            issues.append(name + ' contract is unresolved or unsupported; native execution score is not implemented here')
        if name == 'agentharm':
            try:
                agentharm_files(config)
            except ValueError as exc:
                issues.append(str(exc))
        if name == 'mcphunt' and (not spec.get('files') or not spec.get('gold_field')):
            issues.append('MCPHunt explicit files and gold_field are required')
        if name == 'maliciousskillbench' and spec.get('withheld_text_policy') not in ('exclude', 'public_sanitized'):
            issues.append('MaliciousSkillBench withheld_text_policy must be explicitly selected')
    dojo = config['datasets'].get('agentdojo', {})
    if has_dojo and dojo.get('contract') != 'pre_action_authorization':
        issues.append('AgentDojo dynamic adapter requires explicit pre_action_authorization contract')
    if dojo.get('mode_code') == 'A2':
        issues.append('AgentDojo A2 input-inspection adapter is not implemented; existing pre-action gate cannot be relabeled A2')
    for field in (('benchmark_version', 'suites', 'attacks', 'blocked_feedback', 'max_steps', 'max_tool_calls') if has_dojo else ()):
        need(dojo.get(field), 'agentdojo.' + field)
    for field in (('max_steps', 'max_tool_calls') if has_dojo else ()):
        if type(dojo.get(field)) is not int or dojo[field] <= 0:
            issues.append('agentdojo.' + field + ' must be a positive integer')
    if has_dojo and type(dojo.get('include_clean')) is not bool:
        issues.append('agentdojo.include_clean is unresolved')
    if has_dojo:
        need(config.get('main_agent_system_prompt'), 'main_agent_system_prompt')
    required_contracts = {STATIC_CONTRACTS[n] for n in active if n in STATIC_CONTRACTS}
    if has_dojo:
        required_contracts.add('pre_action_authorization')
    for contract in required_contracts:
        details = config.get('contracts', {}).get(contract, {})
        for field in ('instructions', 'positive_class', 'label_semantics'):
            need(details.get(field), contract + '.' + field)
    if config.get('phase') == 'confirmatory':
        frozen = config.get('confirmation_protocol_manifest')
        if not frozen or not absolute(frozen).is_file():
            issues.append('Confirmatory execution needs a separately frozen scientific protocol manifest')
    return {'status': 'ready' if not issues else 'not_ready', 'issues': issues,
            'local_sources_available': available, 'network_calls': 0}
