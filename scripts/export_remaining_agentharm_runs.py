"""Export the four new local runs and original validation sources; no weights or credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security_bench.common import ROOT, file_hash


def export(archive, inventory):
    archive, inventory = Path(archive), Path(inventory)
    if archive.exists() or inventory.exists():
        raise FileExistsError('Export destination already exists')
    roots = []
    for key in ['shieldstral', 'd3mini', 'qwen35', 'secjev']:
        roots.extend(ROOT / 'data/agent-security-study/runs' / f'2026-11-02-agentharm-{key}-{suffix}'
                     for suffix in ['50', 'smoke'])
        roots.append(ROOT / 'data/agent-security-study/preparations' / f'2026-11-02-agentharm-{key}')
    roots.extend([ROOT / 'data/agent-security-study/preparations/2026-11-02-local-services',
                  ROOT / 'data/workspace-evidence/2026-11-02-local-agentharm-four-models'])
    files = [p for root in roots for p in root.rglob('*') if p.is_file()]
    native = ROOT / 'data/agent-security-study/datasets/2026-10-27/agentharm'
    files.extend([native / 'manifest.json', native / 'snapshot/benchmark/harmful_behaviors_validation.json',
                  native / 'snapshot/benchmark/benign_behaviors_validation.json'])
    manifest = {'record_kind': 'portable_original_new_run_archive_not_new_experiment', 'model_calls': 0,
        'scope': 'Only 2026-11-02 four local models; original complete validation source files, not a derived dataset',
        'excludes': ['model weights', 'API keys', 'previously completed models'], 'files': []}
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in sorted(set(files)):
            name = path.relative_to(ROOT).as_posix()
            if path.suffix in ('.safetensors', '.pt') or path.name.startswith('.env'):
                raise ValueError('Weights/credential file is not an exportable report')
            data = path.read_bytes()
            manifest['files'].append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            bundle.writestr(name, data)
        bundle.writestr('EXPORT-MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8'))
    with zipfile.ZipFile(archive) as bundle:
        for item in manifest['files']:
            if hashlib.sha256(bundle.read(item['path'])).hexdigest() != item['sha256']:
                raise ValueError('Export verification failed')
    result = {'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': file_hash(archive),
              'verified_payload_files': len(files), 'contains_raw_requests': True, 'uploaded': False}
    archive.with_suffix('.zip.sha256').write_text(result['sha256'] + '  ' + archive.name + '\n', encoding='ascii')
    inventory.parent.mkdir(parents=True, exist_ok=True)
    with inventory.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--inventory', required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.archive, args.inventory), indent=2))


if __name__ == '__main__':
    main()
