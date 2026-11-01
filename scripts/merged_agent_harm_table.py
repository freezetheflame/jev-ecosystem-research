"""Merge the Jev pilot and the GPT/Claude relay pilot into one item-level table."""
import argparse, csv, json, math, statistics, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security_bench.common import rows, write


def pctl(values, q):
    if not values: return None
    s = sorted(values)
    return s[max(0, math.ceil(q * len(s)) - 1)]


def metrics(pairs):
    tp = sum(1 for g, p in pairs if g == 1 and p == 1)
    fp = sum(1 for g, p in pairs if g == 0 and p == 1)
    tn = sum(1 for g, p in pairs if g == 0 and p == 0)
    fn = sum(1 for g, p in pairs if g == 1 and p == 0)
    n = tp + fp + tn + fn
    div = lambda a, b: None if b == 0 else a / b
    return {'N': n, 'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn,
            'accuracy': div(tp + tn, n), 'precision': div(tp, tp + fp),
            'recall': div(tp, tp + fn), 'f1': div(2 * tp, 2 * tp + fp + fn),
            'fpr': div(fp, fp + tn), 'fnr': div(fn, fn + tp),
            'specificity': div(tn, tn + fp)}


def run_data(path):
    run = Path(path).resolve()
    ep = rows(run / 'episodes.jsonl')
    calls = []
    for f in sorted((run / 'telemetry').glob('*.calls.jsonl')):
        calls.extend(rows(f))
    return run, ep, calls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jev', default='data/agent-security-study/runs/2026-10-30-agentharm-pilot-50')
    ap.add_argument('--relay', default='data/agent-security-study/runs/2026-10-30-agentharm-relay-50-v2')
    ap.add_argument('--out', default='data/workspace-evidence/2026-11-01-merged-table')
    args = ap.parse_args()
    runs = {'jev': run_data(args.jev), 'relay': run_data(args.relay)}
    arms = {}
    for label, (run, ep, calls) in runs.items():
        arm_names = sorted({e['arm'] for e in ep})
        for arm in arm_names:
            ev = [e for e in ep if e['arm'] == arm]
            valid = [e for e in ev if e['status'] == 'ok' and e.get('prediction') is not None]
            votes = defaultdict(dict); gold = {}
            for e in valid:
                votes[e['item_id']][e['repeat']] = e['prediction']; gold[e['item_id']] = e['gold']
            majority = {i: (1 if sum(v.values()) > len(v) / 2 else 0) for i, v in votes.items()}
            slices = []
            for e in ev:
                s, t = e.get('monitor_event_start'), e.get('monitor_event_end')
                if isinstance(s, int) and isinstance(t, int): slices.extend(calls[s:t])
            valid_slices = []
            for e in valid:
                s, t = e.get('monitor_event_start'), e.get('monitor_event_end')
                if isinstance(s, int) and isinstance(t, int): valid_slices.extend(calls[s:t])
            arms[arm] = {
                'run': str(run), 'episodes': len(ev), 'ok': len(valid),
                'non_ok': len(ev) - len(valid), 'gold': gold, 'votes': votes,
                'majority': majority,
                'seconds_all': [e['wall_seconds'] for e in ev],
                'seconds_valid': [e['wall_seconds'] for e in valid],
                'calls_all': slices, 'calls_valid': valid_slices,
                'statuses': dict(Counter(e['status'] for e in ev))}
    common = sorted(set.intersection(*[set(a['majority']) for a in arms.values()]))
    out = {'record_kind': 'merged_pilot_table_not_confirmatory',
           'created_at': datetime.now(timezone.utc).isoformat(),
           'common_items': len(common), 'arms': {}}
    for arm, a in arms.items():
        pairs = [(a['gold'][i], a['majority'][i]) for i in common]
        m = metrics(pairs)
        calls_all, calls_valid = a['calls_all'], a['calls_valid']
        out['arms'][arm] = {
            'common': m, 'common_n': len(common),
            'full_scorable': len(a['majority']), 'all_items': len(a['gold']),
            'full_metrics': metrics([(a['gold'][i], a['majority'][i]) for i in a['majority']]),
            'episodes': a['episodes'], 'ok': a['ok'], 'non_ok': a['non_ok'],
            'statuses': a['statuses'],
            'time_all': {'p50': pctl(a['seconds_all'], .5), 'p95': pctl(a['seconds_all'], .95),
                         'sum': sum(a['seconds_all']), 'n': len(a['seconds_all'])},
            'time_valid': {'p50': pctl(a['seconds_valid'], .5), 'p95': pctl(a['seconds_valid'], .95),
                           'sum': sum(a['seconds_valid']), 'n': len(a['seconds_valid'])},
            'tokens_all': {'input': sum(c.get('input_tokens') or 0 for c in calls_all),
                           'output': sum(c.get('output_tokens') or 0 for c in calls_all),
                           'unpriced': sum(1 for c in calls_all if c.get('estimated_cost_usd') is None),
                           'api_usd': sum(c.get('estimated_cost_usd') or 0 for c in calls_all)},
            'tokens_valid': {'input': sum(c.get('input_tokens') or 0 for c in calls_valid),
                             'output': sum(c.get('output_tokens') or 0 for c in calls_valid),
                             'unpriced': sum(1 for c in calls_valid if c.get('estimated_cost_usd') is None),
                             'api_usd': sum(c.get('estimated_cost_usd') or 0 for c in calls_valid)},
        }
    outdir = Path(args.out).resolve(); outdir.mkdir(parents=True, exist_ok=False)
    write(outdir / 'merged-table.json', out)

    def fmt(v, p=3):
        return 'NA' if v is None else f'{v:.{p}f}'

    lines = ['# AgentHarm 50×3：Jev / GPT-6 Luna / Claude Haiku 5.5 合并表', '',
             f"共同 item = {len(common)}（三模型都有多数票）；全 50 item 的覆盖另列。", '',
             '| 模型 | N | TP | FP | TN | FN | accuracy | precision | recall | F1 | FPR | FNR | p50 s | p95 s | 总墙钟 s | 输入 token | 输出 token | API 估价 USD | 全 50 可判 |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    order = [a for a in ('jev', 'gpt6luna', 'claudehaiku') if a in arms]
    for arm in order:
        d = out['arms'][arm]; m = d['common']; t = d['time_all']; k = d['tokens_all']
        lines.append(f"| {arm} | {m['N']} | {m['TP']} | {m['FP']} | {m['TN']} | {m['FN']} | {fmt(m['accuracy'])} | {fmt(m['precision'])} | {fmt(m['recall'])} | {fmt(m['f1'])} | {fmt(m['fpr'])} | {fmt(m['fnr'])} | {fmt(t['p50'])} | {fmt(t['p95'])} | {fmt(t['sum'], 1)} | {k['input']:,} | {k['output']:,} | {k['api_usd']:.6f} | {d['full_scorable']}/50 |")
    lines += ['', '全 50 item（各自可判子集，分母不同，不能直接横向比较）：', '',
              '| 模型 | 可判 | TP | FP | TN | FN | accuracy | 备注 |', '|---|---:|---:|---:|---:|---:|---:|---|']
    for arm in order:
        d = out['arms'][arm]; f = d['full_metrics']
        note = d['statuses']
        lines.append(f"| {arm} | {d['full_scorable']}/50 | {f['TP']} | {f['FP']} | {f['TN']} | {f['FN']} | {fmt(f['accuracy'])} | {note} |")
    lines += ['', '时间与 token 为**该模型全部调用**（含 refusal/失败）的统计；p50/p95 为单次调用墙钟。',
              'API 估价使用各次运行的价格快照，不是账单。',
              '**Jev 的 token 口径**：官方价格快照是 input 0.042 USD/M、output 0；实测 usage 为 input 64,470、output 4,650。也就是说 output 不收费（单价 0），但 input 仍按 token 计费，并非“输入不耗 token”。若你的口径不同，需要重新确认价格表。',
              '共同 47 item 中，GPT 的 8-4 只有 1 次有效投票（另两次被 provider 拒绝）；其余 item 至少有 2 次。', '']
    (outdir / 'merged-table.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    with (outdir / 'merged-table.csv').open('w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['model', 'N', 'TP', 'FP', 'TN', 'FN', 'accuracy', 'precision', 'recall', 'f1',
                    'fpr', 'fnr', 'p50_s', 'p95_s', 'total_s', 'input_tokens', 'output_tokens', 'api_usd', 'full_scorable'])
        for arm in order:
            d = out['arms'][arm]; m = d['common']; t = d['time_all']; k = d['tokens_all']
            w.writerow([arm, m['N'], m['TP'], m['FP'], m['TN'], m['FN'], m['accuracy'], m['precision'],
                        m['recall'], m['f1'], m['fpr'], m['fnr'], t['p50'], t['p95'], t['sum'], k['input'],
                        k['output'], k['api_usd'], d['full_scorable']])
    print(json.dumps({'out': str(outdir), 'common': len(common),
                      'arms': {a: {'common': out['arms'][a]['common'], 'time_all': out['arms'][a]['time_all'],
                                   'tokens_all': out['arms'][a]['tokens_all'],
                                   'full_scorable': out['arms'][a]['full_scorable'],
                                   'statuses': out['arms'][a]['statuses']} for a in order}},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()