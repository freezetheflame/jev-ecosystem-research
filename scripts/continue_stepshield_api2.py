#!/usr/bin/env python3
"""Continuation #2 for full-api-stepshield after switching API traffic to direct WLAN.

Completed under the earlier (aTrust VPN) path:
  full-api-stepshield-v1      claudehaiku 4718 ok
  full-api-stepshield-cont-v1 claudehaiku 1510 ok
Remaining: claudehaiku 1923; gpt6luna never started => full 8151.
New campaign: full-api-stepshield-cont2-v1. Same frozen config/prompts, max_hours=72.
"""
import argparse, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _k in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
    os.environ.pop(_k, None)
os.environ['NO_PROXY'] = '*'


def load_key(path, name):
    if name in os.environ:
        return
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        if key.strip() == name:
            os.environ[name] = value.strip().strip('"').strip("'")
            return
    raise ValueError(f'{name} is missing from environment/key file; value never logged')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--env-file', required=True)
    p.add_argument('--max-hours', type=float, default=72.0)
    p.add_argument('--max-api-usd', type=float, default=80.0)
    p.add_argument('--new-campaign', default='full-api-stepshield-cont2-v1')
    p.add_argument('--models', default='claudehaiku,gpt6luna')
    a = p.parse_args()

    load_key(a.env_file, 'OPEN_API_KEY')

    from security_bench.common import rows
    from security_bench.full_suite import configuration
    from security_bench.runner import execute

    runs = ROOT / 'data/agent-security-study/runs'
    sources = [runs / 'full-api-stepshield-v1', runs / 'full-api-stepshield-cont-v1']
    plan = rows(sources[0] / 'claudehaiku' / 'stepshield' / 'plan.jsonl')
    all_ids = list(dict.fromkeys(r['item_id'] for r in plan))
    ok_ids = set()
    for s in sources:
        ep = s / 'claudehaiku' / 'stepshield' / 'episodes.jsonl'
        if ep.exists():
            ok_ids |= {r['item_id'] for r in rows(ep) if r.get('status') == 'ok'}

    models = [m for m in a.models.split(',') if m]
    per_api = a.max_api_usd / len(models)

    for model in models:
        if model == 'claudehaiku':
            ids = [i for i in all_ids if i not in ok_ids]
        elif model == 'gpt6luna':
            ids = all_ids
        else:
            raise ValueError(f'unknown model {model}')

        config, _ = configuration(model, 'stepshield', repeats=1,
                                  max_api_usd=per_api, max_hours=a.max_hours)
        config['datasets']['stepshield']['item_ids'] = ids
        config['record_kind'] = 'full_public_descriptive_evaluation_continuation_v2_direct'

        directory = ROOT / 'data/agent-security-study/runs' / a.new_campaign / model / 'stepshield'
        print(f'[{model}] items={len(ids)} dir={directory} max_hours={a.max_hours} per_api_usd={per_api}', flush=True)
        result = execute(config, directory, resume=False)
        print(f'[{model}] RESULT={result}', flush=True)


if __name__ == '__main__':
    main()
