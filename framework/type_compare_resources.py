"""Derive timing and list-price cost from saved TypeSafe responses; no API calls."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

from framework.type_compare import ROOT, TYPES

PRICE = {'input_usd_per_million': .042, 'output_usd_per_million': 0,
         'source': 'https://docs.typesafe.ai/models', 'verified_date': '2026-10-27',
         'basis': 'Official Jev 1.14 list price; estimate from reported usage, not a bill'}


def percentile(values, q):
    values = sorted(values)
    position = (len(values) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def aggregate(rows):
    responses = [c['response'] for r in rows for c in r['calls'] if 'response' in c]
    usage = {'input_tokens': 0, 'output_tokens': 0}
    missing_usage_responses = 0
    for response in responses:
        counts = response.get('usage', {})
        if any(not isinstance(counts.get(k), int) or isinstance(counts[k], bool) or counts[k] < 0 for k in usage):
            missing_usage_responses += 1
            continue
        for k in usage:
            usage[k] += counts[k]
    latency = [r['latency_ms'] for r in rows]
    attempts = [a for r in rows for c in r['calls'] for a in c.get('attempts', [])]
    return {'records': len(rows), 'failed_records': sum('error' in r for r in rows),
            'response_count': len(responses), 'attempt_count': len(attempts),
            'failed_attempts': sum('error' in a for a in attempts),
            'missing_usage_responses': missing_usage_responses, **usage,
            'known_estimated_cost_usd': usage['input_tokens'] * PRICE['input_usd_per_million'] / 1e6,
            'latency_ms': {'mean': statistics.mean(latency), 'p50': percentile(latency, .5),
                           'p95': percentile(latency, .95), 'min': min(latency), 'max': max(latency)},
            'cumulative_record_seconds': sum(latency) / 1000}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    manifest_path = out / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    raw_path = ROOT / 'bench/data/scans' / out.name / 'predictions.jsonl'
    raw_bytes = raw_path.read_bytes()
    rows = [json.loads(line) for line in raw_bytes.decode('utf-8').splitlines() if line.strip()]
    repair_path = raw_path.with_name('repairs.jsonl')
    repair_bytes = repair_path.read_bytes() if repair_path.exists() else b''
    repairs = [json.loads(line) for line in repair_bytes.decode('utf-8').splitlines() if line.strip()]
    if not rows:
        raise ValueError('No recorded requests')
    expected = {(r['uid'], t) for r in manifest['records'] for t in TYPES}
    actual = {(r['uid'], r['type']) for r in rows}
    if len(actual) != len(rows) or not actual <= expected:
        raise ValueError('Unexpected or duplicate prediction')
    effective = {(r['uid'], r['type']): r for r in rows}
    for repair in repairs:
        cell = (repair['uid'], repair['type'])
        if cell not in effective or 'error' not in effective[cell]:
            raise ValueError('Repair must follow a failed cell')
        from framework.type_compare import digest
        if repair['repair_of_sha256'] != digest(effective[cell]):
            raise ValueError('Repair lineage mismatch')
        effective[cell] = repair
    rows += repairs
    start = min(datetime.fromisoformat(r['started_at']) for r in rows)
    finish = max(datetime.fromisoformat(r['started_at']) + timedelta(milliseconds=r['latency_ms']) for r in rows)
    wall = (finish - start).total_seconds()
    local = timezone(timedelta(hours=8))
    result = {'status': 'complete' if actual == expected and all('error' not in r for r in effective.values()) else 'partial', 'planned_records': len(expected),
              'effective_failed_cells': sum('error' in r for r in effective.values()), 'repair_evaluations': len(repairs),
              'model': manifest['contract']['model'], 'proxy': manifest['contract'].get('proxy'),
              'pricing': PRICE, 'started_at_shanghai': start.astimezone(local).isoformat(),
              'last_record_finished_at_shanghai': finish.astimezone(local).isoformat(),
              'request_phase_wall_seconds': wall,
              'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              'predictions_sha256': hashlib.sha256(raw_bytes).hexdigest(),
              'repairs_sha256': hashlib.sha256(repair_bytes).hexdigest(),
              'analysis_implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'overall': aggregate(rows),
              'by_type': {t: aggregate([r for r in rows if r['type'] == t]) for t in TYPES if any(r['type'] == t for r in rows)}}
    lines = ['# AgentDojo 三种 type：时间与费用', '',
             f"状态：{result['status']}，计划 {len(expected)} 组判断，实际执行 {len(rows)} 组（含 {len(repairs)} 组补测），最终失败项 {result['effective_failed_cells']}。模型 {result['model']}，代理 {result['proxy']}。", '',
             f"北京时间：{result['started_at_shanghai']} 至 {result['last_record_finished_at_shanghai']}。请求阶段墙钟时间 {wall:.2f} 秒（{wall/60:.2f} 分钟）。", '',
             '| type | 判断组数 | 实际尝试 | 失败尝试 | 输入 token | 输出 token | 估算 USD | 平均 ms | P50 ms | P95 ms |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for t, r in list(result['by_type'].items()) + [('总计', result['overall'])]:
        timing = r['latency_ms']
        lines.append(f"| {t} | {r['records']} | {r['attempt_count']} | {r['failed_attempts']} | {r['input_tokens']:,} | {r['output_tokens']:,} | ${r['known_estimated_cost_usd']:.6f} | {timing['mean']:.1f} | {timing['p50']:.1f} | {timing['p95']:.1f} |")
    lines += ['', '时间按每条样本、每种 type 计，包含该条全部分片、网络、代理、解析及发生时的重试；并非模型纯推理耗时。最多四并发，各 type 交错运行，因此累计耗时不能当成整轮墙钟用时。墙钟起止由首条开始时间与末条完成时间计算，不含启动准备和生成报告。', '',
              '按 [TypeSafe 官方模型价格](https://docs.typesafe.ai/models)（2026-10-27 核实）：Jev 1.14 输入 $0.042／百万 token，输出免费。费用由实际返回 usage 计算，包含长文本分片；未获得账户实际账单。失败请求如没有 usage，其潜在费用无法确认，不按零费用保证。', '',
              '原始记录逐条保留 started_at、latency_ms、每片响应 usage 和各次尝试状态。本报告不调用 API，不修改预测。', '']
    (out / 'resources.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'resources.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'wall_seconds': wall, 'overall': result['overall']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
