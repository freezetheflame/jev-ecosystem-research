"""Audit the old AgentHarm failures offline; optionally run a separate 4-item/model diagnostic smoke."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from security_bench.common import read, rows, write, file_hash
from security_bench.full_suite import configuration, inventory
from security_bench.runner import execute
from scripts.machine_benchmark import load_key


def audit(source):
    result = {}
    for model in ('gpt6luna', 'claudehaiku'):
        directory = source / model / 'agentharm'
        events = rows(directory / 'events.jsonl')
        envelope = Counter()
        for event in events:
            if event['event'] != 'request_finished':
                continue
            import json
            body = (directory / 'raw' / event['attempt_id'] / 'response.body').read_text(encoding='utf-8')
            try:
                response = json.loads(body)
            except ValueError:
                envelope['invalid_envelope'] += 1
                continue
            try:
                text = response['choices'][0]['message']['content']
                json.loads(text)
            except (ValueError, KeyError, TypeError, IndexError):
                envelope['non_json_answer_or_error'] += 1
            else:
                envelope['json_answer'] += 1
        result[model] = {'inventory':inventory(rows(directory/'cases.jsonl')),
            'episode_outcomes':dict(Counter(r.get('error_type') or r['status'] for r in rows(directory/'episodes.jsonl'))),
            'response_kinds':dict(envelope),
            'source_hashes':{name:file_hash(directory/name) for name in ('episodes.jsonl','events.jsonl','cases.jsonl')}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'data/agent-security-study/runs/full-api-agentharm-v2')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--max-api-usd',type=float)
    parser.add_argument('--env-file',type=Path)
    args = parser.parse_args()
    if args.live and (args.max_api_usd is None or args.max_api_usd <= 0):
        parser.error('--live requires an explicit positive --max-api-usd')
    args.out.mkdir(parents=True,exist_ok=False)
    write(args.out/'old-run-audit.json',audit(args.source))
    shutil.copyfile(__file__,args.out/'verify_api_retry_repair.py')
    command = ' '.join([sys.executable, *sys.argv])
    write(args.out/'invocation.json',{'argv':sys.argv,'python':sys.executable,'cwd':str(Path.cwd()),
        'script_sha256':file_hash(Path(__file__)),'kind':'diagnostic_smoke' if args.live else 'offline_audit_no_model_calls'})
    if not args.live:
        print('Offline audit saved; 0 API calls.');return
    if args.env_file:
        load_key(args.env_file,'OPEN_API_KEY')
    for model in ('gpt6luna','claudehaiku'):
        old = args.source/model/'agentharm'
        records = rows(old/'episodes.jsonl')
        # Preselected by recorded failure/success status, never by correctness or gold.
        failed = [r for r in records if r['status'] != 'ok'][:3]
        success = [r for r in records if r['status'] == 'ok'][:1]
        ids = [r['item_id'] for r in failed + success]
        config, _ = configuration(model,'agentharm',max_api_usd=args.max_api_usd/2,max_hours=.25)
        config['datasets']['agentharm']['item_ids'] = ids
        config.update(record_kind='full_suite_integration_smoke')
        config['budget']['max_calls'] = len(ids)*config['retry_policy']['max_attempts']
        directory = args.out/model/'agentharm'
        result = execute(config,directory)
        analysis = sorted((directory/'analysis').glob('*/summary.json'))[-1]
        summary = read(analysis)
        # Report-template fields are supplied by immutable linked artifacts plus this supplement.
        note = [f'# API retry diagnostic smoke: {model}', '',
            'Type: diagnostic smoke on exposed development samples; not confirmation or full benchmark.',
            'Purpose: check classification framing and bounded retries; no minimum accuracy target or model ranking.',
            'Changed: explicit data framing, bounded retries and unknown-fee budget reservations. '
            'Unchanged: native inputs, gold, model IDs, endpoint, decoding parameters, strict boolean parser and pricing snapshot.',
            f'Origin: {old}; selected first 3 non-ok and first 1 ok episodes in recorded order, independent of correctness.',
            'Raw selected IDs: '+', '.join(ids),
            'Dataset revision, splits, model parameters, prompts, retry policy and limits: effective-config.json.',
            'Dataset identity, exact cases, labels and input hashes: cases.jsonl, manifest.json and plan.jsonl.',
            'Gold positive=harmful partition; prediction positive=risk true; unit=one input item.',
            'Counts, TP/FP/TN/FN, coverage and NA metric reasons: '+str(analysis.relative_to(directory))+'.',
            'Native agent task completion, prevention, independent review, sample-power and replacement claims: NA; classification smoke only.',
            'Started/finished timestamps and per-item wall time including retries: episodes.jsonl; invocation time: telemetry/*.run.json.',
            'API fees: original monitor usage × frozen price snapshot; not verified bills. Unknown fees remain null. Local compute unpriced.',
            'Exact requests and raw outputs: raw/; linked attempts, selected result, delays and errors: events.jsonl.',
            'Environment, packages, code snapshot and dirty-state provenance: environment.json, source/, manifest.json.',
            'Hosted hardware/tokenizer/defaults and immutable service version: unknown; no server-side access.',
            'Rerun from repository root using a NEW --out directory; same invocation arguments in ../.. /invocation.json.',
            'Invocation: `'+command+'`',
            'Source launcher and hash: ../../verify_api_retry_repair.py and ../../invocation.json.',
            'Native variant/family counts are in cases.jsonl; one repeat; no additional clean/attack derivation or exclusions.',
            'Budget reservation is a scheduling allowance, not a measured fee or guaranteed provider spending cap.',
            'Generated report: '+str(analysis.parent.relative_to(directory)/'report.md')+'.']
        (directory/'report.md').write_text('\n\n'.join(note)+'\n',encoding='utf-8')
        print(model,result, 'coverage',[(g['split'],g['classification']['N'],g['assigned']) for g in summary['groups']],flush=True)


if __name__ == '__main__':main()
