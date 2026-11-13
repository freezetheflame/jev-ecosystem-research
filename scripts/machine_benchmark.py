"""Run the existing same-item AgentHarm pilot using this machine's model registry."""
import argparse
import copy
import os
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from security_bench.common import read, write, file_hash
from security_bench.config import inspect
from security_bench.datasets import load_static
from security_bench.runner import execute
from security_bench.adapters import build_request
from scripts.model_services import REGISTRY, start, command

REFERENCES = {
    'jev': '2026-11-03-agentharm-jev-relay-50',
    'gpt6luna': '2026-10-30-agentharm-relay-50-v2',
    'claudehaiku': '2026-10-30-agentharm-relay-50-v2',
    'gliguard': '2026-11-01-agentharm-gliguard-50',
    'laya': '2026-11-01-agentharm-laya-50',
    'qwen3guard': '2026-11-01-agentharm-qwen3guard-raw-50',
    'd3mini': '2026-11-02-agentharm-d3mini-50',
    'shieldstral': '2026-11-02-agentharm-shieldstral-50',
    'qwen35': '2026-11-02-agentharm-qwen35-50',
    'secjev': '2026-11-02-agentharm-secjev-50',
    'jevguard': '2026-11-03-agentharm-jevguard-50',
    'kev': '2026-11-04-agentharm-kev-50'}
REMOTE = {'jev', 'gpt6luna', 'claudehaiku'}


def load_key(path, name):
    if name in os.environ:
        return
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        if key.strip() == name:
            os.environ[name] = value.strip().strip('"').strip("'")
            return
    raise ValueError(f'{name} is missing from environment/key file; value never logged')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('model', choices=REFERENCES)
    p.add_argument('--run-dir')
    p.add_argument('--preview', action='store_true', help='Print request structure offline; no service or model call')
    p.add_argument('--text', default='Please summarize this public article.')
    p.add_argument('--smoke', action='store_true', help='One benign and one harmful input; one repeat')
    p.add_argument('--env-file', help='Optional key file; only requested API key is loaded, never copied')
    p.add_argument('--pricing', help='API pricing snapshot; reference snapshot used otherwise')
    a = p.parse_args()
    source = ROOT / 'data/agent-security-study/runs' / REFERENCES[a.model]
    c = copy.deepcopy(read(source / 'effective-config.json'))
    c['models'] = {a.model: c['models'][a.model]}
    c['evaluation_models'] = [a.model]
    if a.preview:
        import json
        model = c['models'][a.model]
        endpoint = ('https://api.openlux.ai' + ('/v1/systemone' if a.model == 'jev' else '/v1/chat/completions') if a.model in REMOTE else
                    f"http://127.0.0.1:{REGISTRY['models'][a.model]['port']}{REGISTRY['models'][a.model]['route']}")
        print(json.dumps({'record_kind': 'offline_request_preview', 'model_calls': 0, 'endpoint': endpoint,
            'payload': build_request(model, {'user_request': a.text},
                c['contracts']['request_risk_classification']['instructions'])}, ensure_ascii=False, indent=2))
        return
    if not a.run_dir:
        p.error('--run-dir is required unless --preview is selected')
    run = Path(a.run_dir).resolve()
    if run.exists():
        raise ValueError('Use a new run directory; existing records are not overwritten')
    c.update(data_root='data/agent-security-study/datasets/2026-10-27', monitor_workspace='vendor/preserved-monitor')
    c['record_kind'] = 'machine_readiness_smoke' if a.smoke else 'same_exposed_agentharm_50x3_machine_pilot'
    if a.smoke:
        c['repeats'] = 1
        ids = c['datasets']['agentharm']['item_ids']
        c['datasets']['agentharm']['item_ids'] = [next(x for x in ids if x.startswith('benign:')),
                                               next(x for x in ids if x.startswith('harmful:'))]
    m = c['models'][a.model]
    if a.model in REMOTE:
        endpoint = 'https://api.openlux.ai' + ('/v1/systemone' if a.model == 'jev' else '/v1/chat/completions')
        m.update(provider='openlux', endpoint=endpoint, api_key_env='OPEN_API_KEY')
        if a.model == 'jev':
            c['pricing_file'] = 'configs/security-bench-pricing-openlux-2026-11-03.json'
        if a.env_file:
            load_key(a.env_file, 'OPEN_API_KEY')
        health = {'route': 'OpenLux', 'model_calls_during_preparation': 0}
        print('API uses OpenLux; fees use the saved dated pricing snapshot, not a verified bill.', flush=True)
    else:
        result = start(a.model, replace=True)
        health = result['health']
        local = REGISTRY['models'][a.model]
        m.update(endpoint=result['endpoint'], model_id=local['model_id'], provider='local', api_key_env=None)
        deploy = m.setdefault('deployment', {})
        deploy.update(interface_verified=True,
                      hardware=health.get('hardware') or health.get('gpu') or health.get('device'),
                      launch_command=' '.join(command(a.model)))
        if health.get('dtype'):
            deploy['dtype'] = health['dtype']
        runtime_key = 'gliner2' if a.model == 'gliguard' else 'laya' if a.model == 'laya' else 'transformers'
        if health.get(runtime_key):
            deploy['runtime_version'] = health[runtime_key]
        m['parameter_status'] = {**(m.get('parameter_status') or {}),
                                 'machine_service_health': health}
        c['pricing_file'] = 'configs/security-bench-pricing.template.json'
    if a.pricing:
        c['pricing_file'] = str(Path(a.pricing).resolve())
    issues = inspect(c)['issues']
    if issues:
        raise ValueError('; '.join(issues))
    # Validate the chosen item set before the first inference.
    load_static(c, 'agentharm')
    prep = ROOT / 'data/agent-security-study/preparations' / (run.name + '-machine')
    prep.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, prep / 'machine-benchmark-source.py')
    if a.model not in REMOTE:
        service = ROOT / REGISTRY['models'][a.model]['script']
        if health.get('server_source_sha256') and file_hash(service) != health['server_source_sha256']:
            raise ValueError('Running server differs from current source; restart this service before a new experiment')
        shutil.copyfile(service, prep / 'server-source.py')
        shutil.copyfile(ROOT / 'configs/local-models.machine.json', prep / 'machine-registry.json')
    write(prep / 'config.json', c)
    write(prep / 'deployment.json', {'health': health, 'reference_run': REFERENCES[a.model],
        'launcher_sha256': file_hash(Path(__file__)), 'preparation_model_calls': 0,
        'local_compute': 'unpriced', 'credentials_copied': False})
    print(execute(c, run), flush=True)


if __name__ == '__main__':
    main()
