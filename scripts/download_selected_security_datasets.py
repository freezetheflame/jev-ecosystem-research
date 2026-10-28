"""Acquire selected benchmark snapshots only; never import or execute upstream code."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def fetch(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    partial = path.with_name(path.name + '.partial')
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'jev-research-dataset-acquisition/1.0'})
            with urllib.request.urlopen(request, timeout=90) as response, partial.open('wb') as output:
                shutil.copyfileobj(response, output, 1024 * 1024)
            partial.rename(path)
            return
        except Exception as exc:
            print(json.dumps({'event': 'download_error', 'url': url, 'attempt': attempt + 1,
                              'error_type': type(exc).__name__, 'time': stamp()}), flush=True)
            if attempt == 2:
                raise
            time.sleep(2)


def file_record(path, base):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    record = {'path': path.relative_to(base).as_posix(), 'bytes': path.stat().st_size,
              'sha256': digest.hexdigest()}
    if path.suffix == '.json':
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if isinstance(data, list):
            record['top_level_list_count'] = len(data)
        elif isinstance(data, dict):
            record['top_level_list_counts'] = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    return record


def hf(dataset_id, revision, base):
    endpoint = f'https://huggingface.co/api/datasets/{dataset_id}/revision/{revision}'
    fetch(endpoint, base / 'upstream-metadata.json')
    metadata = json.loads((base / 'upstream-metadata.json').read_text(encoding='utf-8'))
    if metadata['sha'] != revision:
        raise ValueError('Revision mismatch')
    names = [x['rfilename'] for x in metadata['siblings']]
    def download(name):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid upstream path')
        url = f'https://huggingface.co/datasets/{dataset_id}/resolve/{revision}/{urllib.parse.quote(name)}'
        fetch(url, base / 'snapshot' / relative)
        print(json.dumps({'event': 'downloaded', 'dataset': dataset_id, 'file': name}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(download, names))
    return {'source': f'https://huggingface.co/datasets/{dataset_id}', 'revision': revision,
            'expected_upstream_files': len(names), 'scope': 'all_public_repository_files',
            'files': [file_record(p, base) for p in sorted((base / 'snapshot').rglob('*')) if p.is_file()]}


def github(repo, revision, base):
    url = f'https://codeload.github.com/{repo}/zip/{revision}'
    archive = base / 'source.zip'
    fetch(url, archive)
    snapshot = base / 'snapshot'
    snapshot.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            relative = Path(*Path(member.filename).parts[1:])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Invalid archive path')
            if member.is_dir() or not relative.parts:
                continue
            destination = snapshot / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                with bundle.open(member) as source, destination.open('wb') as output:
                    shutil.copyfileobj(source, output)
    return {'source': f'https://github.com/{repo}', 'revision': revision, 'download_url': url,
            'scope': 'official_source_and_bundled_tasks_not_installed_or_executed',
            'archive': file_record(archive, base),
            'files': [file_record(p, base) for p in sorted(snapshot.rglob('*')) if p.is_file()]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='data/agent-security-study/datasets/2026-10-27')
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    jobs = [
        ('agentharm', hf, 'ai-safety-institute/AgentHarm', 'e23b3fe60a0da9037314b88e5ee3a0c054970dad'),
        ('mcphunt', hf, 'lihaonan0716/mcphunt-agent-traces', '8f05fed6face78aa48b10edcf3357c9aadfe71f5'),
        ('agentdojo', github, 'ethz-spylab/agentdojo', '089ed468cf3ed0322acc66b0211f26d9d90dbf60'),
        ('mcphunt-source', github, 'lihaonan0716/MCPHunt', '48e0f42f0820f15c9e88edb0ba461c615b908ecb'),
    ]
    def acquire(job):
        name, method, repo, revision = job
        base = output / name
        base.mkdir(exist_ok=True)
        record = {'record_kind': 'dataset_acquisition_not_experiment', 'started_at_utc': stamp(),
                  'dataset': name, 'status': 'in_progress', 'mode_semantics': 'unresolved',
                  'confirmation_selection': 'not_frozen', 'source': repo, 'revision': revision}
        manifest = base / 'manifest.json'
        if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8')).get('status') == 'download_complete':
            print(json.dumps({'event': 'already_complete', 'dataset': name}), flush=True)
            return
        manifest.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        try:
            record.update(method(repo, revision, base))
            record['status'] = 'download_complete'
        except Exception as exc:
            record.update(status='failed_or_partial', error_type=type(exc).__name__)
        record['finished_at_utc'] = stamp()
        manifest.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'event': 'acquisition_finished', 'dataset': name, 'status': record['status']}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(acquire, jobs))


if __name__ == '__main__':
    main()
