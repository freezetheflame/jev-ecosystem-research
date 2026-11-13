"""Prepare same-item 50x3 development pilots after a local service is healthy."""
import argparse
import copy
import json
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security_bench.common import ROOT, digest, read, rows, write, file_hash
from security_bench.datasets import load_static
from security_bench.config import inspect


def prepare(key, port, directory):
    baseline = ROOT / 'data/agent-security-study/runs/2026-10-30-agentharm-pilot-50'
    config = read(baseline / 'effective-config.json')
    config.update(data_root='data/agent-security-study/datasets/2026-10-27',
                  monitor_workspace='vendor/preserved-monitor', pricing_file='configs/security-bench-pricing.template.json')
    original = {r['item_id']: r['input_sha256'] for r in rows(baseline / 'cases.jsonl')}
    assert {r['item_id']: r['input_sha256'] for r in load_static(config, 'agentharm')} == original
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=5) as response:
        health = json.load(response)
    checkpoint = ROOT / 'local-models/nov04/kev4b' if key == 'kev' else ROOT / 'local-models/nov02' / key
    manifest = read(checkpoint / 'download-manifest.json')
    common = {'display_name': manifest['repo'] + ' (local BF16)', 'model_id': key + '-local',
              'provider': 'local', 'api_key_env': None, 'headers': {}, 'timeout_seconds': 240,
              'parameter_status': {'generation': 'explicit greedy for generators; official native choice for D3',
                                   'comparison': 'same published validation pilot items and 3 repeats; development only'}}
    deployment = {'artifact_revision': manifest['revision'], 'runtime': 'transformers',
                  'runtime_version': '5.17.0', 'dtype': 'bfloat16', 'hardware': 'NVIDIA GeForce RTX 4070 SUPER 12GB',
                  'context_limit': health.get('context_limit') or health.get('max_input_tokens'),
                  'launch_command': 'See deployment.json in preparation directory', 'interface_verified': True}
    if key in ('d3mini', 'secjev', 'kev'):
        model = {**copy.deepcopy(config['models']['jev']), **common, 'adapter': 'choice', 'parameters': {},
                 'endpoint': f'http://127.0.0.1:{port}/v1/systemone', 'deployment': deployment}
        deployment.update(runtime='transformers+official_D3' if key == 'd3mini' else 'official_SecJev+Kev+peft',
                          dtype='BF16 backbone; FP32 readout' if key == 'd3mini' else 'float32')
        if key == 'kev':
            model['model_id'] = 'kev-4b-local'
            deployment.update(runtime='published_Kev_Checkpoint+transformers+peft', dtype=health['dtype'])
            model['parameter_status'] = {'dtype':'explicit BF16 backbone; FP32 pointer head','LoRA':'unmerged',
                'temperature':health['temperature'],'date_facts':False,'cross_request_cache':False,
                'cuda_graphs':False,'fused':False,'reference_path':'published native Checkpoint+encode+forward+to_answers',
                'runtime_difference':'torch2.11 instead of published torch<2.9; BF16 unmerged instead of official FP32 evaluation; development pilot, no reference parity claim'}
        if key == 'secjev':
            model['model_id'] = 'secjev08-local'
            model['parameter_status'] = {'dtype': 'explicit FP32', 'LoRA': 'unmerged',
                'attention': 'SDPA math, flash and memory-efficient kernels disabled', 'tf32': False,
                'temperature': health['temperature'], 'reference_infer': 'SecJev v1.0.0 infer.py',
                'runtime_difference': 'PyTorch 2.11.0+cu130 instead of reference requirements 2.6.0; development pilot, no reference-parity claim'}
        if key == 'd3mini' and deployment['context_limit'] is None:
            position_limit = read(checkpoint / 'config.json')['text_config']['max_position_embeddings']
            deployment['context_limit'] = f'Official runtime max_length=None; checkpoint position limit={position_limit}; inputs retained whole'
    elif key == 'jevguard':
        model = {**common, 'model_id': 'jev-v3.2-2b', 'api': 'jevguard', 'adapter': 'jevguard_safety',
                 'endpoint': f'http://127.0.0.1:{port}/predict', 'input_field': 'user_request',
                 'deployment': deployment, 'parameters': {},
                 'parameter_status': {'contract': 'Native safety-only: options=[], mode=single, safety_applicable=true',
                    'runtime': 'Shared local pilot runtime; differs from published torch2.8/transformers5.10.2/peft0.19.1',
                    'base_revision': 'Original release does not pin base commit; local fetched base revision fixed in checkpoint manifest'}}
        deployment.update(runtime='published_JevClassifier+transformers+peft', dtype=health['dtype'])
    else:
        model = {**common, 'api': 'openai_chat', 'endpoint': f'http://127.0.0.1:{port}/v1/chat/completions',
                 'deployment': deployment, 'parameters': {'max_tokens': 64 if key == 'qwen35' else 1, 'temperature': 0.0}}
        if key == 'qwen35':
            model.update(adapter='json_risk')
            model['parameters']['chat_template_kwargs'] = {'enable_thinking': False}
            relay = read(ROOT / 'data/agent-security-study/runs/2026-10-30-agentharm-relay-50-v2/effective-config.json')
            config['contracts']['request_risk_classification'] = relay['contracts']['request_risk_classification']
        else:
            model.update(adapter='shieldstral', input_field='user_request', yes_means='unsafe',
                         query="Is the user's requested assistance harmful under the Instruction?")
    config['models'] = {key: model}
    config['evaluation_models'] = [key]
    config['record_kind'] = 'new_local_development_pilot_same_existing_50_items_3_repeats'
    config['budget']['max_wall_seconds'] = 3600
    issues = inspect(config, check_keys=False)['issues']
    if issues:
        raise ValueError('; '.join(issues))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    server_source = (checkpoint / 'd3_server.py' if key == 'd3mini' else
                     ROOT / 'scripts/local_kev_server.py' if key == 'kev' else
                     ROOT / 'scripts/local_jevguard_server.py' if key == 'jevguard' else
                     ROOT / 'scripts/local_secjev_server.py' if key == 'secjev' else ROOT / 'scripts/local_remaining_server.py')
    deployment['server_source_sha256'] = file_hash(server_source)
    (directory / 'server-source.py').write_bytes(server_source.read_bytes())
    if key != 'd3mini' and health['server_source_sha256'] != deployment['server_source_sha256']:
        raise ValueError('Running server source differs from preparation source')
    deployment['launch_command'] = f'See {directory.as_posix()}/deployment.json; server SHA256 pinned here'
    pilot = directory / 'pilot-config.json'
    write(pilot, config)
    smoke = copy.deepcopy(config)
    smoke['record_kind'] = 'local_interface_smoke_two_existing_pilot_items'
    smoke['repeats'] = 1
    ids = config['datasets']['agentharm']['item_ids']
    smoke['datasets']['agentharm']['item_ids'] = [next(i for i in ids if i.startswith('benign:')),
                                               next(i for i in ids if i.startswith('harmful:'))]
    write(directory / 'smoke-config.json', smoke)
    write(directory / 'deployment.json', {'health': health, 'checkpoint': manifest,
        'client_config_sha256': digest(config), 'reference_run': baseline.name,
        'item_count': 50, 'repeats': 3, 'model_calls_during_preparation': 0,
        'time_scope': 'Client HTTP episode; model load excluded; no automatic warmup; local compute unpriced',
        'launch_command': f'wsl -d Ubuntu -- /home/hectum/.cache/jev-research-env/bin/python ' +
           (f'/mnt/d/projects/jev_research/local-models/nov02/d3mini/d3_server.py --model /mnt/d/projects/jev_research/local-models/nov02/d3mini --name d3mini-local --device cuda:0 --batch-size 1 --no-warmup --verify full --port {port}' if key == 'd3mini' else
            f'/mnt/d/projects/jev_research/scripts/local_kev_server.py --model-path /mnt/d/projects/jev_research/local-models/nov04/kev4b --base-path /mnt/d/projects/jev_research/local-models/nov04/kev4b/base --kev-source /mnt/d/projects/jev_research/local-models/nov04/kev4b/source --port {port}' if key == 'kev' else
            f'/mnt/d/projects/jev_research/scripts/local_secjev_server.py --model-path /mnt/d/projects/jev_research/local-models/nov02/secjev/SecJev-0.8B --base-path /mnt/d/projects/jev_research/local-models/nov02/secjevbase --kev-source /mnt/d/projects/jev_research/local-models/nov02/secjev/source/kev --port {port}' if key == 'secjev' else
            f'/mnt/d/projects/jev_research/scripts/local_jevguard_server.py --release-path /mnt/d/projects/jev_research/local-models/nov02/jevguard --base-path /mnt/d/projects/jev_research/local-models/nov02/jevguardbase --port {port}' if key == 'jevguard' else
            f'/mnt/d/projects/jev_research/scripts/local_remaining_server.py --model-path /mnt/d/projects/jev_research/local-models/nov02/{key} --served-name {key}-local --port {port}')})
    return {'pilot_config': str(pilot), 'smoke_config': str(directory / 'smoke-config.json'),
            'same_input_hashes_as_reference': True, 'model_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=['qwen35', 'd3mini', 'shieldstral', 'secjev', 'jevguard', 'kev'], required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.model, args.port, args.out), indent=2))


if __name__ == '__main__':
    main()
