"""Reuse locally available official release files only after upstream hash checks."""
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def main():
    original = Path('D:/projects/jev/msb')
    metadata = json.loads((original / 'hf_api_blobs.json').read_text(encoding='utf-8'))
    revision = 'd4b42ce5766a6e0359c987cf59c1007cb3795a90'
    if metadata['sha'] != revision:
        raise ValueError('Unexpected source revision')
    base = ROOT / 'data/agent-security-study/datasets/2026-10-28/maliciousskillbench'
    snapshot = base / 'snapshot'
    snapshot.mkdir(parents=True, exist_ok=True)
    files = []
    for entry in metadata['siblings']:
        name = entry['rfilename']
        source = original / 'hf' / name.replace('/', '__')
        if not source.is_file():
            continue
        content = source.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        if entry.get('lfs'):
            matched = sha == entry['lfs']['sha256']
        else:
            matched = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest() == entry['blobId']
        if not matched:
            raise ValueError('Local official release file hash differs: ' + name)
        target = snapshot / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != content:
            raise FileExistsError('Refusing to overwrite different snapshot')
        if not target.exists():
            shutil.copyfile(source, target)
        files.append({'path':'snapshot/' + name, 'bytes':len(content), 'sha256':sha,
                      'upstream_hash_verified':True})
    if not (snapshot / 'primary.parquet').is_file():
        raise ValueError('Full official primary dataset is missing')
    manifest = {'record_kind':'local_official_dataset_acquisition_not_experiment',
        'created_at':datetime.now(timezone.utc).isoformat(),
        'source':'https://huggingface.co/datasets/ProtectSkills/MaliciousSkillBench',
        'revision':revision, 'status':'download_complete',
        'scope':'Selected official HF release files verified and reused locally; not source-package execution or all HF files.',
        'files':files}
    target = base / 'manifest.json'
    if target.exists():
        raise FileExistsError('Manifest already exists; retain previous record')
    target.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    shutil.copyfile(original/'hf_api_blobs.json',base/'upstream-metadata.json')
    print(json.dumps({'status':'verified_official_files_reused','files':len(files),'revision':revision}))


if __name__=='__main__':
    main()
