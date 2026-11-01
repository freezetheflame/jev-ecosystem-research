"""Fetch AgentHarm and ATBench source files for the A/A/B/D study.

HuggingFace is reached through an explicit mirror because direct access is blocked
on this machine. The pinned revision and per-file SHA-256 are recorded; this is
acquisition only, with no model calls.
"""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HF = 'https://hf-mirror.com/datasets'
SOURCES = {
    'agentharm': {
        'repo': 'ai-safety-institute/AgentHarm',
        'revision': 'e23b3fe60a0da9037314b88e5ee3a0c054970dad',
        'directory': 'agentharm',
        'files': {
            'benchmark/benign_behaviors_test_public.json': 'benchmark/benign_behaviors_test_public.json',
            'benchmark/benign_behaviors_validation.json': 'benchmark/benign_behaviors_validation.json',
            'benchmark/harmful_behaviors_test_public.json': 'benchmark/harmful_behaviors_test_public.json',
            'benchmark/harmful_behaviors_validation.json': 'benchmark/harmful_behaviors_validation.json',
            'benchmark/chat_public_test.json': 'benchmark/chat_public_test.json',
            'benchmark/chat_validation.json': 'benchmark/chat_validation.json',
        },
        'prefix': 'snapshot/',
    },
    'atbench': {
        'repo': 'AI45Research/ATBench',
        'revision': '4476ef92ed8f85c8d58d8a5b9dfdf55aa7893138',
        'directory': 'atbench',
        'files': {'ATBench.json': 'ATBench/test.json'},
        'prefix': '',
        'expected_sha256': '80c534b5f3517c872b528a2e6b64e34495206968edd184f4aed563d39f0cca09',
        'expected_bytes': 18335079,
    },
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url, attempts=4):
    last = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'jev-ecosystem-research/1.0'})
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError('download failed after retries: ' + str(last))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-root', default=str(Path(__file__).resolve().parents[1] /
        'data/agent-security-study/datasets/2026-10-30'))
    parser.add_argument('--datasets', nargs='+', choices=sorted(SOURCES), default=sorted(SOURCES))
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    root = Path(args.out_root).resolve()
    for name in args.datasets:
        spec = SOURCES[name]
        manifest_path = root / spec['directory'] / 'manifest.json'
        if manifest_path.exists() and not args.force:
            print(name, 'skipped; manifest exists (use --force to replace)')
            continue
        records = []
        for local, remote in spec['files'].items():
            url = f"{HF}/{spec['repo']}/resolve/{spec['revision']}/{remote}"
            data = fetch(url)
            json.loads(data.decode('utf-8-sig'))
            destination = root / spec['directory'] / spec['prefix'] / local
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            digest = sha256(data)
            if 'expected_sha256' in spec and digest != spec['expected_sha256']:
                raise RuntimeError(f'{local} sha256 {digest} differs from the acquired snapshot')
            if 'expected_bytes' in spec and len(data) != spec['expected_bytes']:
                raise RuntimeError(f'{local} size {len(data)} differs from the acquired snapshot')
            records.append({'path': spec['prefix'] + local, 'url': url,
                            'sha256': digest, 'bytes': len(data)})
        manifest = {'dataset': name, 'source': 'https://huggingface.co/datasets/' + spec['repo'],
                    'mirror': HF, 'revision': spec['revision'],
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'files': records}
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(name, len(records), 'files', sum(r['bytes'] for r in records), 'bytes', '->', manifest_path)


if __name__ == '__main__':
    main()
