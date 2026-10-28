import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def append(path, value):
    with Path(path).open('ab') as f:
        f.write(encode(value) + b'\n')
        f.flush()
        os.fsync(f.fileno())


def rows(path):
    if not Path(path).exists():
        return []
    with Path(path).open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def absolute(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def sources():
    return {str(p.relative_to(ROOT)).replace('\\', '/'): file_hash(p)
            for p in sorted((ROOT / 'security_bench').rglob('*.py'))}


def secret_values(config):
    return [os.environ[m['api_key_env']] for m in config['models'].values()
            if m.get('api_key_env') and os.environ.get(m['api_key_env'])]


def redact(value, secrets):
    # Redact actual configured credentials, not synthetic canaries in benchmark data.
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, '[REDACTED]')
        return value
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, dict):
        return {k: redact(v, secrets) for k, v in value.items()}
    return value
