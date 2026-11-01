"""Per-repeat metrics for a completed AgentHarm pilot.

The runner pools episodes; this script keeps repeats separate and reports item-level
agreement, so three calls of one item are never counted as three independent items.
"""
import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security_bench.common import append, read, rows, write


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

    acc = div(tp + tn, n)
    return {'N': n, 'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn,
            'accuracy': acc,
            'accuracy_wilson95': wilson(tp + tn, n),
            'precision': div(tp, tp + fp),
            'recall': div(tp, tp + fn),
            'f1': div(2 * tp, 2 * tp + fp + fn),
            'fpr': div(fp, fp + tn),
            'fnr': div(fn, fn + tp),
            'specificity': div(tn, tn + fp),
            'coverage': div(n, n)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--out')
    args = parser.parse_args()
    run = Path(args.run_dir).resolve()
    cases = {r['case_id']: r for r in rows(run / 'cases.jsonl')}
    episodes = rows(run / 'episodes.jsonl')
    plan = rows(run / 'plan.jsonl')
    planned = len(plan)
    valid = [e for e in episodes if e.get('status') == 'ok' and e.get('prediction') is not None]
    by_repeat = defaultdict(list)
    for e in valid:
        by_repeat[e['repeat']].append((e['gold'], e['prediction']))
    repeat_metrics = {}
    for repeat in sorted(by_repeat):
        pairs = by_repeat[repeat]
        m = metrics(pairs)
        m['assigned'] = sum(1 for p in plan if p['repeat'] == repeat)
        m['valid'] = len(pairs)
        eps = [e for e in valid if e['repeat'] == repeat]
        m['seconds_sum'] = sum(e['wall_seconds'] for e in eps)
        m['seconds_p50'] = statistics.median([e['wall_seconds'] for e in eps]) if eps else None
        repeat_metrics[str(repeat)] = m

    # Item-level agreement: one item is one unit, never three.
    by_item = defaultdict(dict)
    for e in valid:
        by_item[e['item_id']][e['repeat']] = e['prediction']
    gold = {e['item_id']: e['gold'] for e in valid}
    families = {e['item_id']: e['family_id'] for e in valid}
    agreement = Counter()
    majority_pairs = []
    item_rows = []
    for item_id, votes in sorted(by_item.items()):
        values = [votes[r] for r in sorted(votes)]
        correct = sum(1 for v in values if v == gold[item_id])
        agreement[f'{correct}/{len(values)}'] += 1
        unanimous = len(set(values)) == 1
        if values:
            majority = 1 if sum(values) > len(values) / 2 else 0
            majority_pairs.append((gold[item_id], majority))
        item_rows.append({'item_id': item_id, 'family_id': families[item_id],
                          'gold': gold[item_id], 'votes': values,
                          'correct_votes': correct, 'unanimous': unanimous,
                          'majority': majority, 'majority_correct': majority == gold[item_id]})
    majority_metrics = metrics(majority_pairs)
    unanimous_rate = (sum(1 for r in item_rows if r['unanimous']) / len(item_rows)) if item_rows else None
    flip_rate = (1 - unanimous_rate) if unanimous_rate is not None else None

    # Telemetry: per-call usage/cost, attributed by episode monitor event range.
    calls = []
    for p in sorted((run / 'telemetry').glob('*.calls.jsonl')):
        calls.extend(rows(p))
    total_in = sum(c.get('input_tokens') or 0 for c in calls)
    total_out = sum(c.get('output_tokens') or 0 for c in calls)
    total_cost = sum(c.get('estimated_cost_usd') or 0 for c in calls)
    unpriced = sum(1 for c in calls if c.get('estimated_cost_usd') is None)
    durations = [e['wall_seconds'] for e in valid]
    result = {
        'record_kind': 'derived_repeat_metrics_not_confirmatory',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'run_dir': str(run),
        'phase': read(run / 'effective-config.json').get('phase'),
        'planned_episodes': planned,
        'recorded_episodes': len(episodes),
        'valid_episodes': len(valid),
        'failed_or_partial': len(episodes) - len(valid),
        'items': len(by_item),
        'families': len(set(families.values())),
        'repeat_metrics': repeat_metrics,
        'majority_vote_metrics': majority_metrics,
        'item_agreement': dict(sorted(agreement.items())),
        'unanimous_rate': unanimous_rate,
        'flip_rate': flip_rate,
        'seconds': {'p50': statistics.median(durations), 'p95': sorted(durations)[max(0, math.ceil(0.95 * len(durations)) - 1)],
                    'sum': sum(durations), 'n': len(durations)},
        'resources': {'calls': len(calls), 'input_tokens': total_in, 'output_tokens': total_out,
                      'api_fee_usd_price_estimated': total_cost, 'unpriced_calls': unpriced,
                      'local_compute': 'unpriced'},
        'item_rows': item_rows,
        'note': 'Repeats are not independent samples. Per-repeat metrics are descriptive; item-level majority and agreement are the primary summaries for this pilot.'
    }
    out = Path(args.out) if args.out else run / 'analysis' / (datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%S_%f_0000') + '-repeat-metrics')
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'repeat-metrics.json', result)
    lines = ['# AgentHarm pilot：逐重复指标', '',
             f"运行目录：`{run}`", '',
             f"计划 {planned}，记录 {len(episodes)}，有效 {len(valid)}，失败/部分 {len(episodes)-len(valid)}；"
             f"独立 item {len(by_item)}，family {len(set(families.values()))}。", '',
             '| repeat | N | TP | FP | TN | FN | accuracy | 95% CI | precision | recall | F1 | FPR |',
             '|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|']
    for repeat, m in repeat_metrics.items():
        ci = m['accuracy_wilson95']
        lines.append(f"| {repeat} | {m['N']} | {m['TP']} | {m['FP']} | {m['TN']} | {m['FN']} | "
                     f"{m['accuracy']:.3f} | [{ci[0]:.3f}, {ci[1]:.3f}] | "
                     f"{m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['fpr']:.3f} |")
    mm = majority_metrics
    lines += ['', '逐 item 多数票（每个 item 一个单位，不把 3 次重复当 3 个独立样本）：', '',
              '| N | TP | FP | TN | FN | accuracy | precision | recall | F1 | FPR |',
              '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
              f"| {mm['N']} | {mm['TP']} | {mm['FP']} | {mm['TN']} | {mm['FN']} | {mm['accuracy']:.3f} | "
              f"{mm['precision']:.3f} | {mm['recall']:.3f} | {mm['f1']:.3f} | {mm['fpr']:.3f} |", '',
              f"三次全对/两次/一次/零次：{dict(sorted(agreement.items()))}；完全一致率 {unanimous_rate:.3f}；翻转率 {flip_rate:.3f}。", '',
              f"时间：p50 {result['seconds']['p50']:.3f}s，p95 {result['seconds']['p95']:.3f}s，合计 {result['seconds']['sum']:.1f}s（n={len(durations)}）。", '',
              f"费用：{len(calls)} 次调用，输入 {total_in}，输出 {total_out}，API 估价 {total_cost:.6f} USD；unpriced {unpriced}；本地计算未计价。", '',
              '重复不是独立样本；本报告不提供确认性结论。']
    (out / 'repeat-metrics.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(out), 'repeat_metrics': repeat_metrics,
                      'majority': majority_metrics, 'agreement': dict(sorted(agreement.items())),
                      'unanimous_rate': unanimous_rate, 'resources': result['resources']},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
