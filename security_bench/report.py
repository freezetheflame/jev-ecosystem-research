"""Derive metrics from append-only results and the preserved monitor events."""
import math
import csv
from collections import defaultdict
from pathlib import Path
import uuid
from .common import rows, read, write, file_hash, now


def ratio(a, b):
    return a / b if b else None


def quantile(values, p):
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, math.ceil(p * len(values)) - 1)]


def api_events(events):
    return [e for e in events if e.get('provider') != 'local']


def api_fee(events):
    calls = api_events(events)
    return sum(e['estimated_cost_usd'] for e in calls) if calls and all(
        e['estimated_cost_usd'] is not None for e in calls) else None


def summarize(assigned, records, telemetry, assigned_attacked=0, assigned_clean=0):
    # No confusion matrix without both native binary gold and valid binary prediction.
    scored = [r for r in records if r['status'] == 'ok' and type(r.get('gold')) is int
              and type(r.get('prediction')) is int and r['gold'] in (0, 1) and r['prediction'] in (0, 1)]
    tp = sum(r['gold'] == 1 and r['prediction'] == 1 for r in scored)
    fn = sum(r['gold'] == 1 and r['prediction'] == 0 for r in scored)
    fp = sum(r['gold'] == 0 and r['prediction'] == 1 for r in scored)
    tn = sum(r['gold'] == 0 and r['prediction'] == 0 for r in scored)
    events = []
    for r in records:
        segment = telemetry.get(r['monitor_run_id'], [])
        if r['monitor_event_end'] > len(segment):
            raise ValueError('Episode references missing monitor calls')
        events.extend(segment[r['monitor_event_start']:r['monitor_event_end']])
    costs = [e['estimated_cost_usd'] for e in api_events(events)]
    groups = defaultdict(list)
    components = defaultdict(list)
    for e in events:
        groups[(e['provider'], e['model'])].append(e)
        components[e.get('component', 'unknown')].append(e)
    dynamic = [r for r in records if r['dataset_id'] == 'agentdojo' and r['status'] == 'ok']
    clean = [r for r in dynamic if r.get('condition') == 'clean']
    attacked = [r for r in dynamic if r.get('condition') == 'attacked']
    safe = sum(r['utility'] and not r['attack_success'] for r in attacked)
    durations = [r['wall_seconds'] for r in records]
    result = {'assigned': assigned, 'started': len(records), 'not_started': assigned - len(records),
        'ok': sum(r['status'] == 'ok' for r in records), 'failed_or_partial': sum(r['status'] != 'ok' for r in records),
        'classification': {'status': 'computed' if scored else 'not_computable_missing_gold_or_predictions',
            'positive_label': 1, 'positive_prediction': 'unsafe', 'N': len(scored),
            'coverage': ratio(len(scored), assigned), 'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn,
            'accuracy': ratio(tp + tn, len(scored)), 'precision': ratio(tp, tp + fp),
            'recall': ratio(tp, tp + fn), 'f1': ratio(2 * tp, 2 * tp + fp + fn),
            'fpr': ratio(fp, fp + tn), 'fnr': ratio(fn, fn + tp), 'specificity': ratio(tn, tn + fp)},
        'episode_results': {'scorable': len(dynamic), 'clean_n': len(clean), 'attacked_n': len(attacked),
            'assigned_clean': assigned_clean, 'assigned_attacked': assigned_attacked,
            'unknown_attacked': assigned_attacked - len(attacked),
            'clean_task_completion': ratio(sum(r['utility'] for r in clean), len(clean)),
            'attacked_task_completion': ratio(sum(r['utility'] for r in attacked), len(attacked)),
            'attack_success_rate': ratio(sum(r['attack_success'] for r in attacked), len(attacked)),
            'safe_task_completion': ratio(safe, len(attacked)),
            'attack_success_rate_bounds_all_assigned': [
                ratio(sum(r['attack_success'] for r in attacked), assigned_attacked),
                ratio(sum(r['attack_success'] for r in attacked) + assigned_attacked - len(attacked), assigned_attacked)]},
        'time': {'episode_N': len(durations), 'episode_seconds_sum': sum(durations),
                 'episode_mean_seconds': ratio(sum(durations), len(durations)),
                 'episode_p50_seconds': quantile(durations, .5), 'episode_p95_seconds': quantile(durations, .95)},
        'resources': {'calls': len(events), 'unpriced_calls': sum(c is None for c in costs),
            'api_calls': len(costs), 'local_calls': len(events) - len(costs),
            'local_unpriced_calls': sum(e.get('provider') == 'local' for e in events),
            'api_fee_usd_price_estimated': sum(costs) if costs and all(c is not None for c in costs) else None,
            'known_api_fee_usd_price_estimated': sum(c for c in costs if c is not None),
            'input_tokens_known': sum(e['input_tokens'] or 0 for e in events),
            'output_tokens_known': sum(e['output_tokens'] or 0 for e in events),
            'missing_usage_calls': sum(e['input_tokens'] is None or e['output_tokens'] is None for e in events),
            'local_compute_cost': 'unpriced', 'server_compute': 'unknown',
            'by_component': {k: {'calls': len(es),
                'known_fee_usd': sum(e['estimated_cost_usd'] or 0 for e in es),
                'unpriced_calls': sum(e['estimated_cost_usd'] is None for e in es),
                'call_seconds_sum': sum(e.get('duration_seconds', 0) for e in es)} for k, es in components.items()},
            'by_provider_model': [{'provider': provider, 'model': model, 'calls': len(es),
                'known_fee_usd': sum(e['estimated_cost_usd'] or 0 for e in es),
                'unpriced_calls': sum(e['estimated_cost_usd'] is None for e in es)}
                for (provider, model), es in groups.items()]}}
    # Native AgentDojo episode outcomes do not become action-gate binary gold.
    if records and records[0]['dataset_id'] == 'agentdojo':
        result['classification'].update(status='not_computable_missing_action_gold',
            TP=None, FP=None, TN=None, FN=None)
    return result


def report(directory):
    directory = Path(directory).resolve()
    plan, results = rows(directory / 'plan.jsonl'), rows(directory / 'episodes.jsonl')
    if not plan:
        raise ValueError('No completed offline plan; no experiment results to report')
    assigned = {r['episode_id']: r for r in plan}
    if len(assigned) != len(plan) or len({r['episode_id'] for r in results}) != len(results):
        raise ValueError('Duplicate episode IDs')
    if any(r['episode_id'] not in assigned for r in results):
        raise ValueError('Unplanned episode result')
    # Restore condition from immutable cases; never infer it from attack result.
    cases = {r['case_id']: r for r in rows(directory / 'cases.jsonl')}
    for r in results:
        p = assigned[r['episode_id']]
        if any(r.get(k) != p.get(k) for k in ('arm', 'dataset_id', 'case_id', 'input_sha256', 'split')):
            raise ValueError('Result-plan mismatch')
        if r.get('gold') != cases[r['case_id']]['gold'] or r.get('gold_source') != cases[r['case_id']]['gold_source']:
            raise ValueError('Result gold differs from immutable case manifest')
        r['condition'] = cases[r['case_id']].get('condition', 'native')
    telemetry = {p.name.removesuffix('.calls.jsonl'): rows(p) for p in (directory / 'telemetry').glob('*.calls.jsonl')}
    for event in rows(directory / 'events.jsonl'):
        if event['event'] == 'request_finished':
            key, index = event['monitor_run_id'], event['monitor_event_index']
            if key not in telemetry or index >= len(telemetry[key]):
                raise ValueError('Missing referenced monitor event')
            telemetry[key][index] = {**telemetry[key][index], 'component': event['component']}
    grouped_plan, grouped_results = defaultdict(list), defaultdict(list)
    for p in plan:
        grouped_plan[(p['dataset_id'], p.get('split', 'selected_native'), p['evaluation_mode'], p['arm'])].append(p)
    for r in results:
        grouped_results[(r['dataset_id'], r.get('split', 'selected_native'), r['evaluation_mode'], r['arm'])].append(r)
    groups = [{'dataset': k[0], 'split': k[1], 'mode_code': k[2], 'arm': k[3],
               'source_items': len({p['case_id'] for p in ps}),
               'base_families': len({p['family_id'] for p in ps}),
               **summarize(len(ps), grouped_results[k], telemetry,
                   sum(cases[p['case_id']].get('condition') == 'attacked' for p in ps),
                   sum(cases[p['case_id']].get('condition') == 'clean' for p in ps))}
              for k, ps in grouped_plan.items()]
    config = read(directory / 'effective-config.json')
    for group in groups:
        contract = config['datasets'][group['dataset']].get('contract')
        group['contract'] = contract
        group['classification']['label_semantics'] = config.get('contracts', {}).get(contract, {}).get('label_semantics')
    summaries = [read(p) for p in (directory / 'telemetry').glob('*.run.json')]
    all_events = [e for segment in telemetry.values() for e in segment]
    ledger = rows(directory / 'events.jsonl')
    episode_starts = {r['episode_id'] for r in ledger if r['event'] == 'episode_started'}
    begun = {r['attempt_id'] for r in ledger if r['event'] == 'request_started'}
    ended = {r['attempt_id'] for r in ledger if r['event'] == 'request_finished'}
    pending = sorted(begun - ended)
    referenced_calls = sum(g['resources']['calls'] for g in groups)
    target = directory / 'analysis' / (now().replace(':', '').replace('+', '_') + '-' + uuid.uuid4().hex[:6])
    target.mkdir(parents=True)
    status = 'complete_with_failures' if len(results) == len(plan) else 'partial'
    if len(results) == len(plan) and all(r['status'] == 'ok' for r in results):
        status = 'complete'
    if any(r['status'] == 'partial_budget' for r in results):
        status = 'partial'
    summary = {'record_kind': 'derived_experiment_report', 'phase': config['phase'], 'status': status,
        'planned': len(plan), 'recorded': len(results), 'groups': groups,
        'started_including_interrupted': len(episode_starts),
        'unfinished_started_episode_ids': sorted(episode_starts - {r['episode_id'] for r in results}),
        'all_api_calls_including_unassigned': len(api_events(all_events)),
        'all_local_calls_including_unassigned': len(all_events) - len(api_events(all_events)),
        'unresolved_request_ids': pending,
        'unassigned_metered_calls': len(all_events) - referenced_calls,
        'api_fees_usd': {'known_price_estimated': sum(e['estimated_cost_usd'] or 0 for e in api_events(all_events)),
            'total_price_estimated': api_fee(all_events) if not pending else None,
            'unpriced_calls': sum(e['estimated_cost_usd'] is None for e in api_events(all_events)),
            'status': 'no_api_calls' if not api_events(all_events) else 'see_coverage_and_unresolved_requests',
            'local_compute': 'unpriced'},
        'invocation_wall_seconds': sum(s['wall_seconds'] for s in summaries),
        'monitor_run_ids': [s['run_id'] for s in summaries],
        'sources': {str(p.relative_to(directory)): file_hash(p)
                    for p in [directory / 'plan.jsonl', directory / 'cases.jsonl', directory / 'effective-config.json',
                              *([directory / 'episodes.jsonl'] if (directory / 'episodes.jsonl').exists() else [])]},
        'limitations': ['Per-dataset contracts have different target events; no pooled benchmark score.',
            'API fees are provider-usage price estimates, not verified bills; local compute unpriced.',
            'No calibration, confidence interval or replacement/noninferiority claim is produced.',
            'AgentHarm request classification is not its official agent task-completion benchmark.',
            'Full-trace gold is not action/prefix gold.']}
    write(target / 'summary.json', summary)
    fields = ['dataset', 'split', 'item_id', 'family_id', 'arm', 'repeat', 'status',
              'gold_label', 'predicted_label', 'wall_seconds', 'api_fee_usd_price_estimated']
    with (target / 'predictions.csv').open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for r in results:
            calls = telemetry.get(r['monitor_run_id'], [])[r['monitor_event_start']:r['monitor_event_end']]
            fee = api_fee(calls)
            writer.writerow({'dataset':r['dataset_id'], 'split':r.get('split', 'selected_native'),
                'item_id':r['item_id'], 'family_id':r['family_id'], 'arm':r['arm'], 'repeat':r['repeat'],
                'status':r['status'], 'gold_label':{0:'safe',1:'unsafe'}.get(r.get('gold')),
                'predicted_label':{0:'safe',1:'unsafe'}.get(r.get('prediction')) if r['status']=='ok' else None,
                'wall_seconds':r['wall_seconds'], 'api_fee_usd_price_estimated':fee})
    write(target / 'artifact-hashes.json', {str(p.relative_to(directory)): file_hash(p)
        for p in sorted(directory.rglob('*')) if p.is_file() and not p.is_relative_to(directory / 'analysis')})
    lines = [f'# 实验报告：{directory.name}', '', f'类型：{config["phase"]}；状态：{status}。', '',
        '本报告由原始结果和既有 monitor 派生；不是独立标签审核或账单核验。', '',
        '## 1. 数据集与数量', '', f'计划 episodes：{len(plan)}；已记录：{len(results)}。',
        '确切数据项、任务族、输入 hash 与 gold：`cases.jsonl`；配对/重复及顺序：`plan.jsonl`。',
        '来源版本及暴露：`effective-config.json`；文件 hash：`manifest.json`。', '',
        '## 2. 时间与费用', '',
        '逐 episode 墙钟含该任务的主 Agent、安全模块和工具；逐调用耗时及失败计费见 `events.jsonl` 与 `telemetry/`。',
        '各段 invocation 墙钟包含报告前的运行开销，不包括计划生成；暂停间隔不纳入累计墙钟。',
        'API 费用按 monitor 价格快照估算，本地计算未计价；未知费用保持 null。', '',
        '## 3. 分数、基础计数与覆盖率', '',
        '| 数据集 | split | Mode | 模型 | 计划 | 有效分类 | accuracy | F1 | API估价 USD | p50秒 |',
        '|---|---|---|---|---:|---:|---:|---:|---:|---:|']
    for g in groups:
        c, t, money = g['classification'], g['time'], g['resources']
        lines.append(f'| {g["dataset"]} | {g["split"]} | {g["mode_code"]} | {g["arm"]} | {g["assigned"]} | {c["N"]} | {c["accuracy"]} | {c["f1"]} | {money["api_fee_usd_price_estimated"]} | {t["episode_p50_seconds"]} |')
    lines += ['', 'TP/FP/TN/FN、precision/recall/FPR/FNR、覆盖率、失败及原生 episode 成绩见同目录 summary.json。',
        'AgentDojo 无动作 gold，混淆矩阵标为不适用；仅统计官方任务效用与攻击成功。', '',
        '## 4. 模型和完整有效配置', '',
        '`effective-config.json` 保存所有实际配置及参数状态；每次实际请求、返回模型与 usage 另存 `raw/`。',
        '服务端隐藏默认值无法查明，按配置 parameter_status 明确记录；没有伪造 Jev 的采样温度或 seed。', '',
        '## 5. Prompt、请求与原始记录', '',
        '实际发送 JSON 字节：`raw/<attempt>/request.json`；原始响应正文：`response.body`。',
        '请求前事件和对应 monitor event 索引：`events.jsonl`；动态状态与工具调用：`traces/`。', '',
        '## 6. 复现、验收和限制', '',
        '`source/`、`environment.json`、`pricing-snapshot.json`、`manifest.json` 固定代码、包版本、价格与输入。',
        '入口：`python -m security_bench run --config <相同配置文件> --run-dir <本目录> --resume`。',
        '恢复遇到未决调用、代码/环境/数据变化时拒绝；失败 episode 不自动挑选最好重试。',
        *summary['limitations']]
    (target / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'analysis_dir': str(target), 'status': status}
