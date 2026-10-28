"""Offline request previews on synthetic text, never a model experiment."""
from pathlib import Path
from .adapters import selected_models, build_request, adapter
from .common import write, encode, secret_values, sources


def preview(config, directory):
    if any(secret in encode(config).decode('utf-8') for secret in secret_values(config)):
        raise ValueError('Configuration contains a live credential')
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=False)
    records = []
    for name in selected_models(config):
        model = config['models'][name]
        for contract, details in config['contracts'].items():
            if not details.get('instructions'):
                records.append({'model': name, 'contract': contract, 'status': 'unresolved_instructions'})
                continue
            state = {model.get('input_field') or 'user_request': 'SYNTHETIC ADAPTER PREVIEW ONLY. Sort these letters: b, a.'}
            payload = build_request(model, state, details['instructions'])
            filename = name + '--' + contract + '.json'
            write(destination / filename, payload)
            records.append({'model': name, 'contract': contract, 'adapter': adapter(model), 'request': filename})
    result = {'record_kind': 'synthetic_request_preview_not_experiment', 'model_calls': 0,
              'datasets_read': 0, 'model_count': len(selected_models(config)), 'records': records,
              'source_hashes': sources()}
    write(destination / 'manifest.json', result)
    return result
