"""Manage this machine's registered local model services; health checks never infer."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / 'configs/local-models.machine.json').read_text(encoding='utf-8'))
STATE = ROOT / 'local-models/.services'


def linux_path(path):
    path = Path(path).resolve()
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


def command(key):
    m = REGISTRY['models'][key]
    substitutions = {'root': linux_path(ROOT), 'weights': linux_path(ROOT / m['weights'])}
    return [REGISTRY['python'], '-u', linux_path(ROOT / m['script'])] + [a.format(**substitutions) for a in m['args']]


def health(key):
    m = REGISTRY['models'][key]
    result = {'key': key, 'model_id': m['model_id'], 'weights': m['weights'],
              'files_present': (ROOT / m['weights']).is_dir(),
              'endpoint': f"http://127.0.0.1:{m['port']}{m['route']}"}
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                f"http://127.0.0.1:{m['port']}/health", timeout=1) as r:
            result['health'] = json.load(r)
        result['running'] = True
    except Exception:
        result['running'] = False
    return result


def stop(key):
    state = STATE / f'{key}.json'
    if not state.exists():
        return {'key': key, 'stopped': False, 'reason': 'No managed process; external service left alone'}
    record = json.loads(state.read_text(encoding='utf-8'))
    # Match the complete saved argv, never kill a whole distribution or unrelated Python processes.
    script = """import os,json,signal,sys
expected=json.loads(sys.argv[1]);stopped=[]
for name in os.listdir('/proc'):
 if not name.isdigit():continue
 try:
  args=open('/proc/'+name+'/cmdline','rb').read().decode().rstrip('\\0').split('\\0')
  if args==expected:os.kill(int(name),signal.SIGTERM);stopped.append(int(name))
 except (OSError,UnicodeError):pass
print(json.dumps(stopped))
"""
    r = subprocess.run(['wsl', '-d', REGISTRY['wsl_distribution'], '--', '/usr/bin/python3', '-c',
                        script, json.dumps(record['linux_argv'])], capture_output=True, text=True, check=True)
    state.unlink()
    return {'key': key, 'stopped_linux_pids': json.loads(r.stdout)}


def start(key, replace=False, timeout=300):
    existing = health(key)
    if existing['running']:
        return existing
    if not existing['files_present']:
        raise RuntimeError('Missing weights: ' + existing['weights'])
    if replace:
        for other in REGISTRY['models']:
            if other != key and (STATE / f'{other}.json').exists():
                stop(other)
        time.sleep(2)
    STATE.mkdir(parents=True, exist_ok=True)
    argv = command(key)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    logfile = STATE / f'{key}-{stamp}.log'
    env_args = [f'{k}={v}' for k, v in REGISTRY['models'][key].get('environment', {}).items()]
    with logfile.open('wb') as log:
        process = subprocess.Popen(['wsl', '-d', REGISTRY['wsl_distribution'], '--', 'env',
            'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1', 'TOKENIZERS_PARALLELISM=false', *env_args, *argv],
            cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    record = {'key': key, 'windows_pid': process.pid, 'linux_argv': argv, 'log': str(logfile)}
    (STATE / f'{key}.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = health(key)
        if status['running']:
            return {**status, 'log': str(logfile)}
        if process.poll() is not None:
            raise RuntimeError('Server exited; inspect ' + str(logfile))
        time.sleep(2)
    stop(key)
    raise RuntimeError('Startup timed out; inspect ' + str(logfile))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['list', 'status', 'start', 'stop', 'command'])
    p.add_argument('model', nargs='?', choices=[*REGISTRY['models'], 'all'])
    p.add_argument('--replace', action='store_true', help='Stop other services managed by this script first')
    p.add_argument('--timeout', type=int, default=300)
    a = p.parse_args()
    if a.action in ('list', 'status'):
        keys = [a.model] if a.model and a.model != 'all' else list(REGISTRY['models'])
        with ThreadPoolExecutor(max_workers=9) as pool:
            print(json.dumps(list(pool.map(health, keys)), ensure_ascii=False, indent=2))
    elif a.action == 'stop' and a.model == 'all':
        print(json.dumps([stop(k) for k in REGISTRY['models']], indent=2))
    else:
        if a.model in (None, 'all'):
            p.error('Select one local model')
        result = command(a.model) if a.action == 'command' else stop(a.model) if a.action == 'stop' else start(a.model, a.replace, a.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
