"""Write an offline readiness artifact, including missing datasets; no model calls."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from security_bench.full_suite import configuration, inventory, DATASETS
from security_bench.common import read,write,now,sources,file_hash
from security_bench.config import inspect
from security_bench.runner import data_hashes
from security_bench.adapters import build_request


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    models=list(read(ROOT/'configs/full-suite-models.v1.json')['models'])
    results={}
    for d in DATASETS:
        try:
            c,cases=configuration('jev',d)
            hashes=data_hashes(c)
            checks={}
            for m in models:
                cm,_=configuration(m,d,cached_cases=cases)
                problems=inspect(cm,check_keys=False)['issues']
                state=cases[0]['view']
                if d=='stepshield':state={'task':state['task'],'history':[],'current_observed_step':state['steps'][0]}
                build_request(cm['models'][m],state,cm['contracts'][cm['datasets'][d]['contract']]['instructions'])
                checks[m]=problems
            results[d]={'status':'offline_ready' if not any(checks.values()) else 'not_ready',
                **inventory(cases),'revision':c['datasets'][d]['source_revision'],'source_file_count':len(hashes),'model_issues':checks}
        except (ValueError,FileNotFoundError) as e:
            results[d]={'status':'not_ready','reason':str(e)}
        print(d,results[d]['status'],flush=True)
    limitations=['No live integration or full run performed.']
    if results['wildguardtest']['status']!='offline_ready':
        limitations.append('WildGuard official data is not ready; see its dataset reason and authorized HF_TOKEN configuration.')
    write(a.out,{'record_kind':'offline_readiness_not_experiment','created_at':now(),'model_calls':0,'api_calls':0,
        'datasets':results,'source_hashes':sources(),
        'preserved_monitor_sha256':file_hash(ROOT/'vendor/preserved-monitor/jev_skill/monitor.py'),
        'limitations':limitations})


if __name__=='__main__':main()
