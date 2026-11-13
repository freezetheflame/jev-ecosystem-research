"""Package only the new local pilots; never re-score the previously completed models."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security_bench.common import ROOT, file_hash, read, rows, write
from scripts.agentharm_multimodel_metrics import metrics


def package(destination, models=None, date='2026-11-02'):
    models = models or ['shieldstral', 'd3mini', 'qwen35']
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    output = {'record_kind': 'new_local_agentharm_development_pilots_not_confirmatory',
              'date': date, 'hardware': 'RTX 4070 SUPER 12GB',
              'reference_sample_run': '2026-10-30-agentharm-pilot-50',
              'prior_results': 'User completed on another computer; not re-audited or re-run here',
              'interval_note': 'Wilson intervals in derived JSON are unclustered descriptive intervals; no family-cluster correction or confirmatory claim',
              'api_calls': 0, 'local_compute_cost': 'unpriced', 'models': {}}
    selection = None
    for key in models:
        run = ROOT / 'data/agent-security-study/runs' / f'{date}-agentharm-{key}-50'
        cases, episodes = rows(run / 'cases.jsonl'), rows(run / 'episodes.jsonl')
        config = read(run / 'effective-config.json')
        current = {c['item_id']: c['input_sha256'] for c in cases}
        if selection is None:
            selection = current
        if current != selection or len(cases) != 50 or len(episodes) != 150:
            raise ValueError('Pilot is incomplete or uses different inputs')
        if any(e['status'] != 'ok' for e in episodes):
            raise ValueError('Pilot contains non-scorable outcomes; preserve raw and report coverage separately')
        gold = {c['item_id']: c['gold'] for c in cases}
        votes = defaultdict(dict)
        for episode in episodes:
            votes[episode['item_id']][episode['repeat']] = episode['prediction']
        if any(len(v) != 3 for v in votes.values()):
            raise ValueError('Three valid repeats per item are required')
        majority = {i: int(sum(v.values()) >= 2) for i, v in votes.items()}
        group = read(sorted((run / 'analysis').glob('*/summary.json'))[-1])['groups'][0]
        output['models'][key] = {'run': run.name, 'source_items': 50, 'repeats': 3, 'episodes': 150,
            'statuses': dict(Counter(e['status'] for e in episodes)),
            'majority': metrics([(gold[i], majority[i]) for i in sorted(majority)]),
            'per_repeat': {str(r): metrics([(e['gold'], e['prediction']) for e in episodes if e['repeat'] == r]) for r in range(3)},
            'all_three_predictions_agree_items': sum(len(set(v.values())) == 1 for v in votes.values()),
            'time': group['time'], 'resources': group['resources'],
            'effective_model': config['models'][key],
            'label_semantics': config['contracts']['request_risk_classification']['label_semantics']}
        for suffix in ['50', 'smoke']:
            source = ROOT / 'data/agent-security-study/runs' / f'{date}-agentharm-{key}-{suffix}'
            target = destination / 'runs' / source.name
            for name in ['effective-config.json', 'manifest.json', 'environment.json', 'pricing-snapshot.json']:
                (target / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / name, target / name)
            for path in (source / 'analysis').rglob('*'):
                if path.is_file() and path.name != 'artifact-hashes.json':
                    dest = target / path.relative_to(source)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, dest)
        checkpoint = ROOT / 'local-models/nov02' / key
        target = destination / 'checkpoints' / key
        target.mkdir(parents=True)
        for name in ['hf-api.json', 'download-manifest.json', 'config.json', 'generation_config.json',
                     'decision_config.json', 'tokenizer_config.json']:
            if (checkpoint / name).exists():
                shutil.copyfile(checkpoint / name, target / name)
        preparation = ROOT / 'data/agent-security-study/preparations' / f'{date}-agentharm-{key}'
        for name in ['pilot-config.json', 'smoke-config.json', 'deployment.json', 'server-source.py']:
            dest = destination / 'preparations' / key / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(preparation / name, dest)
    runtime = ROOT / 'data/agent-security-study/preparations/2026-11-02-local-services/wsl-runtime.lock.txt'
    shutil.copyfile(runtime, destination / 'wsl-runtime.lock.txt')
    secjev_runtime = runtime.with_name('wsl-runtime-secjev.lock.txt')
    if 'secjev' in models and secjev_runtime.exists():
        shutil.copyfile(secjev_runtime, destination / secjev_runtime.name)
    output['base_families'] = len({c['family_id'] for c in cases})
    write(destination / 'results.json', output)
    lines = [f'# AgentHarm：本机 {len(models)} 个模型的 pilot', '',
             f'{date}；RTX 4070 SUPER 12GB；同一 50 条 validation 输入，harmful/benign 各 25，8 个基础任务族，每项重复 3 次。',
             '只报告本轮新实验；没有复核或重跑另一台电脑完成的模型。', '',
             '| 模型 | 调用成功 | 多数票 N | TP | FP | TN | FN | Accuracy | F1 | p50 秒 | p95 秒 |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for key, result in output['models'].items():
        m, t = result['majority'], result['time']
        lines.append(f'| {key} | 150/150 | 50 | {m["TP"]} | {m["FP"]} | {m["TN"]} | {m["FN"]} | {m["accuracy"]:.3f} | {m["f1"]:.3f} | {t["episode_p50_seconds"]:.3f} | {t["episode_p95_seconds"]:.3f} |')
    lines += ['', '每组另有两条接口 smoke，独立 run 与报告保留；上表不把 smoke 算入 150 次调用。',
              f'共 {150 * len(models)} 次 pilot 调用 + {2 * len(models)} 次 smoke 调用；全部为本地推理，没有本轮 API 调用。本地计算未计价，不代表零成本。',
              '时间是单次 HTTP episode 墙钟；模型加载在其外，pilot 之前已做 smoke。不把与另一张显卡的耗时差归因于模型本身。',
              '多数票以 50 项为分母；150 次重复不是 150 个独立任务。公开 validation 与已暴露样本仅属探索性 pilot，未形成确认性结论。',
              '请求、原始输出、monitor 与事件原件在 data/agent-security-study/runs/ 下，保持本地；此包仅含参数、派生报告和来源哈希，不含权重。',
              '实际模型版本、完整 prompt、safe/unsafe 映射、样本 IDs、参数、来源和复现入口见各 run 的 effective-config.json、manifest.json、报告以及 preparations/。',
              ('SecJev-0.8B 补充使用原进度日志明确列出的 v1.0.0 候选；FP32、未合并 LoRA、保留原 decision head/校准。PyTorch 为 2.11.0，而官方 requirements 为 2.6.0，不声明已验证参考运行时数值一致性。'
               if 'secjev' in models else '此目录是三模型阶段的结果；后续补跑另开 run，不覆盖本记录。'),
              ('Jev-Guard 使用发布的原生 safety head，options=[]，不运行策略树路由。基座 revision 为本轮固定值，原发布未指定；共享运行时版本差异见 deployment.json。' if 'jevguard' in models else '本目录只描述所选模型的当轮记录，后续补跑另行存档。')]
    (destination / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    write(destination / 'SHA256SUMS.json', {p.relative_to(destination).as_posix(): file_hash(p)
        for p in destination.rglob('*') if p.is_file()})
    return {k: {'accuracy': v['majority']['accuracy'], 'f1': v['majority']['f1'],
                'p50_seconds': v['time']['episode_p50_seconds']} for k, v in output['models'].items()}


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--models', nargs='+', choices=['shieldstral','d3mini','qwen35','secjev','jevguard'])
    parser.add_argument('--date', default='2026-11-02')
    args = parser.parse_args()
    print(json.dumps(package(args.out, args.models, args.date), indent=2))


if __name__ == '__main__':
    main()
