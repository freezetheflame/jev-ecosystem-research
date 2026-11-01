"""Per-arm, per-repeat metrics for the AgentHarm relay pilot (GPT/Claude)."""
import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security_bench.common import read, rows, write


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [None, None]
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, centre - half), min(1.0, centre + half)]


def metrics(pairs):
    tp = sum(1 for g, p in pairs if g == 1 and p == 1)
    fp = sum(1 for g, p in pairs if g == 0 and p == 1)
    tn = sum(1 for g, p in pairs if g == 0 and p == 0)
    fn = sum(1 for g, p in pairs if g == 1 and p == 0)
    n = tp + fp + tn + fn

    def div(a, b):
        return None if b == 0 else a / b

    return {'N': n, 'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn,
            'accuracy': div(tp + tn, n), 'accuracy_wilson95': wilson(tp + tn, n),
            'precision': div(tp, tp + fp), 'recall': div(tp, tp + fn),
            'f1': div(2 * tp, 2 * tp + fp + fn), 'fpr': div(fp, fp + tn),
            'fnr': div(fn, fn + tp), 'specificity': div(tn, tn + fp)}


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', required=True)
    args = parser.parse_args()
    run = Path(args.run_dir).resolve()
    config = read(run / 'effective-config.json')
    arms = config.get('evaluation_models') or [k for k in config['models']]
    cases = {r['case_id']: r for r in rows(run / 'cases.jsonl')}
    plan = rows(run / 'plan.jsonl')
    episodes = rows(run / 'episodes.jsonl')
    valid = [e for e in episodes if e.get('status') == 'ok' and e.get('prediction') is not None]
    calls = []
    for p in sorted((run / 'telemetry').glob('*.calls.jsonl')):
        calls.extend(rows(p))

    result = {'record_kind': 'derived_multimodel_pilot_metrics_not_confirmatory',
              'created_at': datetime.now(timezone.utc).isoformat(), 'run_dir': str(run),
              'planned': len(plan), 'recorded': len(episodes), 'valid': len(valid),
              'failed_or_partial': len(episodes) - len(valid), 'arms': {}}
    item_votes = {}
    for arm in arms:
        arm_valid = [e for e in valid if e['arm'] == arm]
        per_repeat = {}
        for repeat in sorted({e['repeat'] for e in arm_valid}):
            pairs = [(e['gold'], e['prediction']) for e in arm_valid if e['repeat'] == repeat]
            m = metrics(pairs)
            m['assigned'] = sum(1 for p in plan if p['arm'] == arm and p['repeat'] == repeat)
            m['valid'] = len(pairs)
            eps = [e for e in arm_valid if e['repeat'] == repeat]
            m['seconds_sum'] = sum(e['wall_seconds'] for e in eps)
            m['seconds_p50'] = statistics.median([e['wall_seconds'] for e in eps]) if eps else None
            per_repeat[str(repeat)] = m
        by_item = defaultdict(dict)
        for e in arm_valid:
            by_item[e['item_id']][e['repeat']] = e['prediction']
        agreement = Counter()
        golds = {}
        majority = {}
        for item_id, votes in by_item.items():
            values = [votes[r] for r in sorted(votes)]
            gold = next(e['gold'] for e in arm_valid if e['item_id'] == item_id)
            golds[item_id] = gold
            correct = sum(1 for v in values if v == gold)
            agreement[f'{correct}/{len(values)}'] += 1
            maj = 1 if sum(values) > len(values) / 2 else 0
            majority[item_id] = maj
        item_votes[arm] = majority
        arm_calls = []
        for e in arm_valid:
            start, end = e.get('monitor_event_start'), e.get('monitor_event_end')
            if isinstance(start, int) and isinstance(end, int):
                arm_calls.extend(calls[start:end])
        durations = [e['wall_seconds'] for e in arm_valid]
        result['arms'][arm] = {
            'per_repeat': per_repeat,
            'majority': metrics([(golds[i], majority[i]) for i in sorted(majority)]),
            'agreement': dict(sorted(agreement.items())),
            'unanimous_rate': (sum(1 for i in majority if len(set(by_item[i].values())) == 1) / len(majority)) if majority else None,
            'seconds': {'p50': statistics.median(durations) if durations else None,
                        'p95': sorted(durations)[max(0, math.ceil(0.95 * len(durations)) - 1)] if durations else None,
                        'sum': sum(durations), 'n': len(durations)},
            'resources': {'calls': len(arm_calls),
                          'input_tokens': sum(c.get('input_tokens') or 0 for c in arm_calls),
                          'output_tokens': sum(c.get('output_tokens') or 0 for c in arm_calls),
                          'api_fee_usd_price_estimated': sum(c.get('estimated_cost_usd') or 0 for c in arm_calls),
                          'unpriced_calls': sum(1 for c in arm_calls if c.get('estimated_cost_usd') is None),
                          'local_compute': 'unpriced'}}

    comparison = None
    if len(item_votes) == 2:
        a, b = arms
        both = only_a = only_b = neither = 0
        rows_out = []
        for item in sorted(set(item_votes[a]) & set(item_votes[b])):
            gold = next(e['gold'] for e in valid if e['item_id'] == item)
            ca = item_votes[a][item] == gold
            cb = item_votes[b][item] == gold
            both += ca and cb
            only_a += ca and not cb
            only_b += cb and not ca
            neither += (not ca) and (not cb)
            rows_out.append({'item_id': item, 'gold': gold, a: item_votes[a][item], b: item_votes[b][item]})
        comparison = {'both_correct': both, 'only_' + a: only_a, 'only_' + b: only_b,
                      'both_wrong': neither, 'mcnemar_exact_p': mcnemar_exact(only_a, only_b),
                      'items': rows_out}
    result['paired_comparison'] = comparison

    out = run / 'analysis' / (datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%S_%f_0000') + '-multimodel-metrics')
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'multimodel-metrics.json', result)

    lines = ['# AgentHarm relay pilot：GPT-6 Luna vs Claude Haiku 5.5', '',
             f"计划 {len(plan)}，记录 {len(episodes)}，有效 {len(valid)}，失败/部分 {len(episodes)-len(valid)}。", '']
    for arm in arms:
        d = result['arms'][arm]
        lines += [f"## {arm}", '', '| repeat | N | TP | FP | TN | FN | accuracy | 95% CI | precision | recall | F1 | FPR |',
                  '|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|']
        for repeat, m in d['per_repeat'].items():
            ci = m['accuracy_wilson95']
            lines.append(f"| {repeat} | {m['N']} | {m['TP']} | {m['FP']} | {m['TN']} | {m['FN']} | {m['accuracy']:.3f} | [{ci[0]:.3f}, {ci[1]:.3f}] | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['fpr']:.3f} |")
        mm = d['majority']
        lines += ['', f"多数票：N={mm['N']} TP={mm['TP']} FP={mm['FP']} TN={mm['TN']} FN={mm['FN']} accuracy={mm['accuracy']:.3f} precision={mm['precision']:.3f} recall={mm['recall']:.3f} F1={mm['f1']:.3f}；一致率 {d['unanimous_rate']:.3f}。", '',
                  f"时间 p50 {d['seconds']['p50']:.3f}s，p95 {d['seconds']['p95']:.3f}s，合计 {d['seconds']['sum']:.1f}s。", '',
                  f"费用：{d['resources']['calls']} 次，输入 {d['resources']['input_tokens']}，输出 {d['resources']['output_tokens']}，API 估价 {d['resources']['api_fee_usd_price_estimated']:.6f} USD，unpriced {d['resources']['unpriced_calls']}。", '']
    if comparison:
        lines += ['## 配对比较（item 多数票）', '',
                  f"both correct={comparison['both_correct']}, only_{arms[0]}={comparison['only_'+arms[0]]}, only_{arms[1]}={comparison['only_'+arms[1]]}, both wrong={comparison['both_wrong']}, McNemar exact p={comparison['mcnemar_exact_p']:.4f}。", '']
    lines += ['重复不是独立样本；这是 pilot，不是确认性结论。']
    (out / 'multimodel-metrics.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(out), 'arms': {a: {'majority': result['arms'][a]['majority'],
        'resources': result['arms'][a]['resources'], 'seconds': result['arms'][a]['seconds'],
        'agreement': result['arms'][a]['agreement']} for a in arms},
        'paired': comparison and {k: v for k, v in comparison.items() if k != 'items'}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
