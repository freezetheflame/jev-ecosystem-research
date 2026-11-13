"""One-command full public suite: preflight, run, resume, or status. No paid calls by default."""
import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from security_bench.common import read, write, file_hash, now, rows, digest, sources
from security_bench.config import inspect
from security_bench.runner import execute, data_hashes, verify_inputs
from security_bench.full_suite import configuration, inventory, DATASETS, KNOWN_DATASETS
from scripts.model_services import start, stop, REGISTRY
from scripts.machine_benchmark import load_key

BASE = ROOT / 'data/agent-security-study'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['preflight','run','status'])
    p.add_argument('--models',default='all',help='all, local, api, or comma-separated model keys')
    p.add_argument('--datasets',default='all',help='all or comma-separated dataset keys')
    p.add_argument('--campaign',default='full-suite-v1')
    p.add_argument('--repeats',type=int,default=1)
    p.add_argument('--max-api-usd',type=float,help='Total estimated API ceiling across selected cells; explicit for API execution')
    p.add_argument('--max-hours-per-cell',type=float,default=24)
    p.add_argument('--env-file')
    p.add_argument('--resume',action='store_true')
    p.add_argument('--smoke',action='store_true',help='First two native items per dataset; separate smoke campaign, never full results')
    a=p.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*',a.campaign):p.error('Invalid campaign name')
    all_models=list(read(ROOT/'configs/full-suite-models.v1.json')['models'])
    models=all_models if a.models=='all' else list(REGISTRY['models']) if a.models=='local' else ['jev','gpt6luna','claudehaiku'] if a.models=='api' else a.models.split(',')
    datasets=DATASETS if a.datasets=='all' else a.datasets.split(',')
    if len(set(models))!=len(models) or set(models)-set(all_models) or len(set(datasets))!=len(datasets) or set(datasets)-set(KNOWN_DATASETS):p.error('Unknown or repeated model/dataset')
    runroot=BASE/'runs'/a.campaign
    if a.action=='status':
        print(json.dumps([{'model':m,'dataset':d,'planned':(runroot/m/d/'manifest.json').exists(),
            'completed_episodes':len(rows(runroot/m/d/'episodes.jsonl')),
            'assigned_episodes':len(rows(runroot/m/d/'plan.jsonl'))} for m in models for d in datasets],indent=2));return
    remote=[m for m in models if m not in REGISTRY['models']]
    if a.action=='run' and remote and (a.max_api_usd is None or a.max_api_usd<=0):p.error('API execution requires explicit --max-api-usd total ceiling')
    if a.repeats<1 or a.max_hours_per_cell<=0:p.error('repeats/hours must be positive')
    if a.env_file and a.action=='run' and remote:load_key(a.env_file,'OPEN_API_KEY')
    per_api=(a.max_api_usd or 1)/(len(remote)*len(datasets) or 1)
    cells=[]
    fingerprints={}
    # Validate ALL selected sources/contracts before launching any service or API request.
    for d in datasets:
        stats=None
        native_cases=None
        for m in models:
            c,cases=configuration(m,d,a.repeats,per_api if m in remote else 1,a.max_hours_per_cell,cached_cases=native_cases)
            native_cases=cases
            if a.smoke:
                cases=cases[:2]
                c['datasets'][d]['item_ids']=[x['item_id'] for x in cases]
                c.update(record_kind='full_suite_integration_smoke',repeats=1)
                c['budget']['max_calls']=sum(x.get('native_steps',1) for x in cases)*c.get('retry_policy',{}).get('max_attempts',1)
            checked=inspect(c,check_keys=a.action=='run')
            if checked['issues']:raise ValueError('; '.join(checked['issues']))
            if d not in fingerprints:fingerprints[d]=data_hashes(c)
            if stats is None:stats=inventory(cases)
            cells.append((m,d,c))
        print(json.dumps({'dataset':d,**stats,'models':len(models),'repeats':a.repeats},ensure_ascii=False),flush=True)
    if a.action=='preflight':
        print('OFFLINE PREFLIGHT PASSED; 0 model/API calls. Live long-input behavior still requires smoke.');return
    prep=BASE/'preparations'/a.campaign
    signature={'models':models,'datasets':datasets,'repeats':a.repeats,'smoke':a.smoke,'api_ceiling_usd':a.max_api_usd,
        'hours_per_cell':a.max_hours_per_cell,'configs':{m+'/'+d:digest(c) for m,d,c in cells},
        'launcher_sha256':file_hash(Path(__file__)),'registry_sha256':file_hash(ROOT/'configs/local-models.machine.json'),
        'source_hashes':sources(),'data_hashes':fingerprints,
        'server_hashes':{m:file_hash(ROOT/REGISTRY['models'][m]['script']) for m in models if m in REGISTRY['models']}}
    if (prep/'campaign.json').exists():
        if not a.resume or read(prep/'campaign.json')!=signature:raise ValueError('Campaign already exists or frozen inputs changed; use exact --resume or a new campaign ID')
    else:
        if a.resume:raise ValueError('Cannot resume a nonexistent campaign')
        write(prep/'campaign.json',signature)
        for path in [Path(__file__),ROOT/'scripts/model_services.py',ROOT/'scripts/machine_benchmark.py',
                     ROOT/'configs/full-suite-models.v1.json',ROOT/'configs/full-suite-pricing.v1.json',
                     ROOT/'configs/local-models.machine.json',
                     *[ROOT/REGISTRY['models'][m]['script'] for m in models if m in REGISTRY['models']]]:
            target=prep/'source'/path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
    for m,d,c in cells:
        directory=runroot/m/d
        if directory.exists():
            verify_inputs(c,directory)
            if len(rows(directory/'episodes.jsonl'))==len(rows(directory/'plan.jsonl')):
                print(m,d,'already complete; not rerun',flush=True);continue
        health=None
        try:
            if m in REGISTRY['models']:
                health=start(m,replace=True)['health']
                if health.get('server_source_sha256') and health['server_source_sha256']!=signature['server_hashes'][m]:
                    raise ValueError('Service source differs from frozen source; restart it')
            write(prep/'deployments'/f'{m}-{d}-{now().replace(":","-")}.json',{'time':now(),'health':health,'route':c['models'][m]['endpoint']})
            result=execute(c,directory,resume=a.resume)
            print(m,d,result,flush=True)
            if result['status']!='finished':raise RuntimeError('Partial cell retained; inspect report before resume. Campaign stopped.')
        finally:
            if m in REGISTRY['models']:stop(m)


if __name__=='__main__':
    main()
