"""Fetch the three explicit pilot checkpoints from saved HF metadata; verify every file."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request


def hashes(path):
    digest = hashlib.sha256()
    blob = hashlib.sha1(('blob ' + str(path.stat().st_size) + '\0').encode())
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
            blob.update(block)
    return digest.hexdigest(), blob.hexdigest()


def fetch_ranges(key, repo, revision, item, destination, block_size=32 * 1024 * 1024, workers=8):
    size, name = item['size'], item['rfilename']
    parts = destination.parent / 'range-parts' / name
    if block_size != 32 * 1024 * 1024:
        parts = parts / ('chunks_' + str(block_size))
    parts.mkdir(parents=True, exist_ok=True)
    count = (size + block_size - 1) // block_size
    def part(index):
        start, end = index * block_size, min(size, (index + 1) * block_size) - 1
        target = parts / str(index)
        if target.is_file() and target.stat().st_size == end - start + 1:
            return index
        for host in ('https://huggingface.co', 'https://hf-mirror.com'):
            for attempt in range(3):
                try:
                    url = host + '/' + repo + '/resolve/' + revision + '/' + name + '?download=true&range_start=' + str(start) + '&range_end=' + str(end)
                    req = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}'})
                    with urllib.request.urlopen(req, timeout=45) as response:
                        if response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{size}':
                            raise ValueError('Server did not honor requested range')
                        data = response.read(end - start + 2)
                    if len(data) != end - start + 1:
                        raise ValueError('Incomplete download range')
                    target.write_bytes(data)
                    return index
                except Exception:
                    time.sleep(1)
        raise RuntimeError('Failed checkpoint range: ' + key + '/' + name + '/' + str(index))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(part, i) for i in range(count)]
        for completed, future in enumerate(as_completed(futures), 1):
            future.result()
            if completed % 10 == 0 or completed == count:
                print(json.dumps({'model': key, 'file': name, 'ranges_done': completed, 'ranges_total': count}), flush=True)
    partial = destination.with_name(destination.name + '.partial')
    with partial.open('wb') as stream:
        for index in range(count):
            with (parts / str(index)).open('rb') as source:
                shutil.copyfileobj(source, stream, 8 * 1024 * 1024)
    actual, _ = hashes(partial)
    if actual != item['lfs']['sha256']:
        raise ValueError('Assembled checkpoint hash mismatch')
    partial.rename(destination)


def fetch(key, root, metadata_dir=None):
    directory = root / key
    directory.mkdir(parents=True, exist_ok=True)
    metadata_path = (metadata_dir or root) / key / 'hf-api.json'
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    repo, revision = metadata['id'], metadata['sha']
    selected = [f for f in metadata['siblings'] if '/' not in f['rfilename']
                and f['rfilename'] not in ('.gitattributes', 'consolidated.safetensors')]
    files = []
    for item in selected:
        name = item['rfilename']
        destination = directory / name
        expected = item.get('lfs', {}).get('sha256')
        expected_blob = item.get('blobId') if not expected else None
        if not destination.is_file() and item.get('size', 0) > 64 * 1024 * 1024:
            fetch_ranges(key, repo, revision, item, destination)
        if not destination.is_file():
            partial = destination.with_name(name + '.partial')
            complete = False
            for host in ('https://huggingface.co', 'https://hf-mirror.com'):
                for attempt in range(3):
                    try:
                        offset = partial.stat().st_size if partial.exists() else 0
                        headers = {'User-Agent': 'jev-research-pinned-checkpoint-fetch/1'}
                        if offset:
                            headers['Range'] = 'bytes=' + str(offset) + '-'
                        request = urllib.request.Request(host + '/' + repo + '/resolve/' + revision + '/' + name + '?download=true', headers=headers)
                        with urllib.request.urlopen(request, timeout=60) as response:
                            if offset and response.status != 206:
                                offset = 0
                            with partial.open('ab' if offset else 'wb') as stream:
                                for block in iter(lambda: response.read(8 * 1024 * 1024), b''):
                                    stream.write(block)
                        if item.get('size') is not None and partial.stat().st_size != item['size']:
                            raise ValueError('Incomplete checkpoint file')
                        actual, blob = hashes(partial)
                        if (expected and actual != expected) or (expected_blob and blob != expected_blob):
                            raise ValueError('Checkpoint hash mismatch')
                        partial.rename(destination)
                        complete = True
                        break
                    except Exception as exc:
                        print(json.dumps({'model': key, 'file': name, 'attempt': attempt + 1,
                                          'error_type': type(exc).__name__}), flush=True)
                        time.sleep(1)
                if complete:
                    break
            if not complete:
                raise RuntimeError('Failed checkpoint download: ' + key + '/' + name)
        actual, blob = hashes(destination)
        if (expected and actual != expected) or (expected_blob and blob != expected_blob):
            raise ValueError('Existing checkpoint file hash mismatch')
        files.append({'path': name, 'bytes': destination.stat().st_size, 'sha256': actual,
                      'upstream_verified': bool(expected or expected_blob)})
        print(json.dumps({'model': key, 'file': name, 'bytes': destination.stat().st_size, 'verified': True}), flush=True)
    manifest = {'repo': repo, 'revision': revision, 'files': files, 'model_calls': 0,
                'download_source': 'HF resolve URL at fixed revision; mirror fallback uses identical revision'}
    manifest_path = directory / 'download-manifest.json'
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding='utf-8')) != manifest:
            raise ValueError('Existing acquisition manifest differs; preserve it and use a new destination')
    else:
        with manifest_path.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(manifest, stream, indent=2)
    return {'model': key, 'revision': revision, 'complete': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--metadata-dir', type=Path, help='Directory of pinned <model>/hf-api.json records')
    parser.add_argument('--models', nargs='+', default=['qwen35', 'd3mini', 'shieldstral'])
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=3) as executor:
        for result in executor.map(lambda key: fetch(key, args.root, args.metadata_dir), args.models):
            print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
