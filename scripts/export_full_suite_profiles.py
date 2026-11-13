"""Export existing measured deployment configurations without credentials or raw data."""
import copy
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.machine_benchmark import REFERENCES, REMOTE
from scripts.model_services import REGISTRY
from security_bench.common import read, write


def main():
    models = {}
    for key, reference in REFERENCES.items():
        model = copy.deepcopy(read(ROOT / 'data/agent-security-study/runs' / reference / 'effective-config.json')['models'][key])
        model.pop('input_field', None)
        if key in REMOTE:
            model.update(provider='openlux', endpoint='https://api.openlux.ai' + ('/v1/systemone' if key == 'jev' else '/v1/chat/completions'), api_key_env='OPEN_API_KEY')
        else:
            spec = REGISTRY['models'][key]
            model.update(endpoint=f'http://127.0.0.1:{spec["port"]}{spec["route"]}', provider='local', api_key_env=None, model_id=spec['model_id'])
            model['deployment'].update(launch_command=f'python scripts/model_services.py start {key} --replace',
                hardware='execution health recorded separately', runtime_version='execution health recorded separately')
        if key == 'laya':
            model['deployment']['dtype'] = 'float32'
        models[key] = model
    write(ROOT / 'configs/full-suite-models.v1.json', {'record_kind':'versioned_deployment_profiles_not_runtime_measurements','models':models})
    pricing = read(ROOT / 'data/agent-security-study/runs/2026-10-30-agentharm-relay-50-v2/pricing-snapshot.json')
    pricing.update(read(ROOT / 'configs/security-bench-pricing-openlux-2026-11-03.json'))
    write(ROOT / 'configs/full-suite-pricing.v1.json', pricing)


if __name__ == '__main__':
    main()
