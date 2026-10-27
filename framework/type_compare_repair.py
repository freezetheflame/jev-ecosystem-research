"""Retry failed transport cells without changing the frozen experiment or original log."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import time

from framework.type_compare import ROOT, configure_transport, digest, parse_answer, read, report
from bench.engines import wrap_files
from jev_skill.client import load_env, api_key, post_json
from jev_skill.config import load_config
from jev_skill.input import build_states


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    contract = manifest['contract']
    configure_transport(contract.get('proxy'))
    load_env(ROOT / '.env')
    import os
    os.environ['TYPESAFE_KEY_NAME'] = contract['key_name']
    key = api_key()
    raw = ROOT / 'bench/data/scans' / out.name
    original = read(raw / 'predictions.jsonl')
    previous = read(raw / 'repairs.jsonl')
    effective = {(r['uid'], r['type']): r for r in original + previous}
    jobs = [r for r in effective.values() if 'error' in r]
    dataset = {r['uid']: r for r in read(ROOT / 'bench/data/ts_bench.jsonl')}
    cfg = load_config(ROOT / 'config/jev-stage-s4-v2.json')
    assert cfg.sha256 == contract['profile_sha256']
    chosen = {r['uid']: r for r in contract['records']}

    def work(old):
        rec = dataset[old['uid']]
        assert digest(rec) == chosen[rec['uid']]['record_sha256']
        states = build_states(wrap_files(rec), 'serialized', cfg.chunk_size, cfg.chunk_overlap)
        assert [digest(s) for s in states] == chosen[rec['uid']]['state_sha256']
        row = {k: old[k] for k in ('uid', 'type', 'label', 'source_id', 'corpus', 'text_stage', 'label_semantics', 'contract_sha256', 'record_sha256')}
        row.update(started_at=datetime.now(timezone.utc).isoformat(), calls=[], repair_of_sha256=digest(old))
        start = time.perf_counter()
        try:
            scores, preds = [], []
            for state in states:
                payload = {'model': contract['model'], 'state': state,
                           'questions': {cfg.question_name: contract['questions'][row['type']]}}
                call = {'request_sha256': digest(payload), 'state_sha256': digest(state), 'attempts': []}
                row['calls'].append(call)
                for attempt in range(3):
                    try:
                        response = post_json(payload, key=key, timeout=30)
                        call['attempts'].append({'attempt': attempt + 1, 'status': 'success'})
                        break
                    except Exception as error:
                        message = str(error).replace(key, '[REDACTED]')
                        call['attempts'].append({'attempt': attempt + 1, 'error': message})
                        transient = 'TypeSafe HTTP' not in message or any(f'HTTP {n}' in message for n in (429, 500, 502, 503, 504, 529))
                        if not transient or attempt == 2:
                            raise
                        time.sleep(1 + attempt)
                call['response'] = response
                score, pred = parse_answer(row['type'], response['answers'][cfg.question_name])
                scores.append(score)
                preds.append(pred)
            row.update(score=max(scores), pred=max(preds), chunks=len(scores),
                       usage={k: sum(c['response'].get('usage', {}).get(k, 0) or 0 for c in row['calls']) for k in ('input_tokens', 'output_tokens')})
        except Exception as error:
            row['error'] = str(error).replace(key, '[REDACTED]')
        row['latency_ms'] = (time.perf_counter() - start) * 1000
        return row

    print(f'failed_cells_to_repair={len(jobs)}', flush=True)
    with (raw / 'repairs.jsonl').open('a', encoding='utf-8') as stream:
        # One unchanged failed cell checks restored transport before the rest.
        if jobs:
            first = work(jobs.pop(0))
            stream.write(json.dumps(first, ensure_ascii=False) + '\n'); stream.flush()
            previous.append(first)
            print('repair_probe', first['type'], first.get('error', 'OK'), flush=True)
            if 'error' in first:
                jobs = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            for row in pool.map(work, jobs):
                stream.write(json.dumps(row, ensure_ascii=False) + '\n'); stream.flush()
                previous.append(row)
                print('repair', len(previous), row['type'], row.get('error', 'OK'), flush=True)
    effective = {(r['uid'], r['type']): r for r in original + previous}
    report(out, manifest, list(effective.values()))
    audit = {'reason': 'Retry all failed transport cells with unchanged model, question, state, proxy and key selector',
             'original_failed_cells': sum('error' in r for r in original), 'repair_evaluations': len(previous),
             'remaining_failed_cells': sum('error' in r for r in effective.values()),
             'repair_implementation_sha256': hashlib.sha256(__file__.encode()).hexdigest(),
             'original_predictions_sha256': hashlib.sha256((raw / 'predictions.jsonl').read_bytes()).hexdigest(),
             'repairs_sha256': hashlib.sha256((raw / 'repairs.jsonl').read_bytes()).hexdigest()}
    audit['repair_implementation_sha256'] = hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest()
    (out / 'repair-audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    with (out / 'README.md').open('a', encoding='utf-8') as stream:
        stream.write(f"\n首轮有 {audit['original_failed_cells']} 个失败项；保留 predictions.jsonl，并执行 {len(previous)} 组原配置补测（repairs.jsonl）。最终指标采用同一样本/type 的最后记录，剩余失败 {audit['remaining_failed_cells']}；费用和时间统计包含首轮及补测。\n")


if __name__ == '__main__':
    main()
