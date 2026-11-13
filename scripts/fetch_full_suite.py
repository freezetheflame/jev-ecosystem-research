"""Acquire pinned public evaluation data; never execute upstream code or call models."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request
import zipfile
import subprocess
import os
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from security_bench.common import file_hash, read, write, now
from scripts.fetch_ab_datasets import SOURCES

DATA_ROOT = ROOT / 'data/agent-security-study/datasets/full-suite-v1'
STEP_REV = '031aa88219f78cda987c2b9d034112e360afda7e'
WILD_REV = 'd29c47f41c8b51348b5c8e8c81c039b3132b66d1'


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirected and urlsplit(req.full_url).netloc!=urlsplit(newurl).netloc:
            redirected.remove_header('Authorization')
        return redirected


def acquire(root=DATA_ROOT, proxy=None, datasets=None):
    opener = urllib.request.build_opener(SafeRedirect,urllib.request.ProxyHandler({'https': proxy, 'http': proxy} if proxy else {}))
    def get(url):
        cache = Path(root) / '_download-cache' / hashlib.sha256(url.encode()).hexdigest()
        cache.parent.mkdir(parents=True, exist_ok=True)
        if not cache.exists():
            partial = cache.with_suffix('.partial')
            if 'huggingface.co/datasets/allenai/wildguardmix/' in url:
                token = os.environ.get('HF_TOKEN')
                if not token:
                    raise ValueError('Official WildGuardMix is gated. Configure an authorized HF_TOKEN locally; no mirror substitution.')
                req = urllib.request.Request(url, headers={'Authorization':'Bearer '+token})
                with opener.open(req, timeout=180) as response:
                    partial.write_bytes(response.read())
                partial.rename(cache)
                return cache.read_bytes()
            subprocess.run(['curl.exe', '--fail', '--location', '--retry', '3', '--connect-timeout', '20',
                '--max-time', '300', '--silent', '--show-error', *(['--proxy',proxy] if proxy else ['--noproxy','*']),
                '--output',str(partial),url],check=True)
            partial.rename(cache)
        return cache.read_bytes()
    for name in (datasets or ['agentharm', 'injecagent', 'tsbench', 'stepshield', 'wildguardtest']):
        dest = Path(root) / name
        if (dest / 'manifest.json').exists():
            m = read(dest / 'manifest.json')
            if name=='stepshield' and any(f['path'].startswith('snapshot/benchmark/') for f in m['files']):
                # Evaluation uses our reviewed adapter, not upstream executable code.
                # Preserve the first acquisition record; scope the active manifest to data.
                (dest/'manifest.json').rename(dest/'manifest-with-unused-upstream-code.json')
                m['files']=[f for f in m['files'] if not f['path'].startswith('snapshot/benchmark/')]
                m['scope_note']='Data-only acquisition; unused upstream executable files excluded. Initial acquisition manifest preserved.'
                write(dest/'manifest.json',m)
            if any(file_hash(dest / f['path']) != f['sha256'] for f in m['files']):
                raise ValueError('Acquired data changed: ' + name)
            print(name, 'verified existing', flush=True)
            continue
        files = {}
        if name == 'agentharm':
            old = ROOT / 'data/agent-security-study/datasets/2026-10-27/agentharm'
            m = read(old / 'manifest.json')
            rev, source = m['revision'], m.get('source')
            for f in m['files']:
                p = old / f['path']
                if file_hash(p) != f['sha256']:
                    raise ValueError('Old AgentHarm source hash differs')
                files[str(Path(f['path']).relative_to('snapshot')).replace('\\','/')] = (p.read_bytes(), 'preserved:' + str(p))
        elif name in SOURCES:
            spec = SOURCES[name]
            rev, source = spec['revision'], 'https://github.com/' + spec['repo']
            urls = {p: u.replace('/main/', '/' + rev + '/') for p,u in spec['files'].items()}
            if name == 'injecagent':
                for kind in ['dh','ds']:
                    p = f'test_cases_{kind}_enhanced.json'
                    urls[p] = f'https://raw.githubusercontent.com/{spec["repo"]}/{rev}/data/{p}'
            for p,u in urls.items():
                print('fetch', name, p, flush=True)
                files[p] = (get(u), u)
        elif name == 'wildguardtest':
            rev, source = WILD_REV, 'https://huggingface.co/datasets/allenai/wildguardmix'
            for p in ['README.md', 'test/wildguard_test.parquet']:
                u = f'{source}/resolve/{rev}/{p}'
                files[p] = (get(u), u)
        else:
            rev, source = STEP_REV, 'https://github.com/glo26/stepshield'
            u = f'https://codeload.github.com/glo26/stepshield/zip/{rev}'
            print('fetch StepShield pinned archive', flush=True)
            archive = get(u)
            with zipfile.ZipFile(io.BytesIO(archive)) as z:
                for f in z.infolist():
                    p = '/'.join(f.filename.split('/')[1:])
                    if not f.is_dir() and (p.startswith('data/') or p in ['README.md','LICENSE']):
                        if '..' in Path(p).parts or Path(p).is_absolute():
                            raise ValueError('Unsafe archive path')
                        files[p] = (z.read(f), u + '#' + p)
        manifest = []
        for p,(b,u) in files.items():
            target = dest / 'snapshot' / p
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != b:
                raise ValueError('Never overwrite differing partial acquisition: ' + str(target))
            target.write_bytes(b)
            manifest.append({'path':'snapshot/'+p, 'sha256':hashlib.sha256(b).hexdigest(), 'bytes':len(b), 'url':u})
        write(dest / 'manifest.json', {'dataset':name,'source':source,'revision':rev,'retrieved_at':now(),'files':manifest})
        print(name, len(files), 'files acquired', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=DATA_ROOT)
    p.add_argument('--proxy')
    p.add_argument('--datasets', nargs='+',choices=['agentharm','injecagent','tsbench','stepshield','wildguardtest'])
    a = p.parse_args()
    acquire(a.root, a.proxy,a.datasets)
