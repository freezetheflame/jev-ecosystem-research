"""Fetch InjecAgent and TS-Bench source files for the A/A/B/D adaptation spike.

This is acquisition only: no model calls, no credentials, no derived labels.
Each dataset gets <out-root>/<name>/snapshot/ plus a manifest recording the exact
source revision, URL, byte count and SHA-256 used by security_bench.data_hashes.
"""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MEDIA = 'https://media.githubusercontent.com/media'
SOURCES = {
    'injecagent': {
        'repo': 'uiuc-kang-lab/InjecAgent',
        'revision': 'f19c9f2c79a41046eb13c03c51a24c567a8ffa07',
        'files': {
            'test_cases_dh_base.json': 'https://raw.githubusercontent.com/uiuc-kang-lab/InjecAgent/main/data/test_cases_dh_base.json',
            'test_cases_ds_base.json': 'https://raw.githubusercontent.com/uiuc-kang-lab/InjecAgent/main/data/test_cases_ds_base.json',
        },
    },
    'tsbench': {
        'repo': 'MurrayTom/ToolSafe',
        'revision': '46358fa424a927a895c6c8322f99032c4eb5155e',
        'files': {
            'agentharm-traj/benign_steps.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/agentharm-traj/benign_steps.json',
            'agentharm-traj/harmful_steps.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/agentharm-traj/harmful_steps.json',
            'agentdojo-traj/banking.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/agentdojo-traj/banking.json',
            'agentdojo-traj/slack.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/agentdojo-traj/slack.json',
            'agentdojo-traj/travel.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/agentdojo-traj/travel.json',
            'agentdojo-traj/workspace.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/agentdojo-traj/workspace.json',
            'asb-traj/DPI_attack_success.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/asb-traj/test/DPI_attack_success.json',
            'asb-traj/OPI_attack_success.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/asb-traj/test/OPI_attack_success.json',
            'asb-traj/attack_failure.json': MEDIA + '/MurrayTom/ToolSafe/main/TS-Bench/asb-traj/test/atttack_failure.json',
        },
    },
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url, attempts=4):
    last = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'jev-ecosystem-research/1.0'})
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError('download failed after retries: ' + str(last))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-root', default=str(Path(__file__).resolve().parents[1] /
        'data/agent-security-study/datasets/2026-10-30'))
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    root = Path(args.out_root).resolve()
    for name, spec in SOURCES.items():
        manifest_path = root / name / 'manifest.json'
        if manifest_path.exists() and not args.force:
            raise SystemExit(str(manifest_path) + ' exists; pass --force to replace')
        records = []
        for relative, url in spec['files'].items():
            data = fetch(url)
            if relative.endswith('.json'):
                json.loads(data.decode('utf-8-sig'))
            destination = root / name / 'snapshot' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            records.append({'path': 'snapshot/' + relative, 'url': url,
                            'sha256': sha256(data), 'bytes': len(data)})
        manifest = {'dataset': name, 'source': 'https://github.com/' + spec['repo'],
                    'revision': spec['revision'],
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'files': records}
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(name, len(records), 'files', sum(r['bytes'] for r in records), 'bytes', '->', manifest_path)


if __name__ == '__main__':
    main()