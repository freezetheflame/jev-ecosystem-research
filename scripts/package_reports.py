"""Assemble the tracked report bundle and its checksum list."""
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'data/agent-security-study/runs'
DEST = ROOT / 'data/workspace-evidence/2026-11-01-report-bundle'


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


def main():
    if DEST.exists():
        shutil.rmtree(DEST)
    copied = []
    for run in sorted(p for p in RUNS.iterdir() if p.is_dir()):
        target = DEST / 'runs' / run.name
        for path in sorted(run.glob('*.md')):
            copied.append(copy(path, target / path.name))
        analysis = run / 'analysis'
        if analysis.is_dir():
            for path in sorted(analysis.rglob('*')):
                if path.is_file() and path.suffix.lower() in ('.md', '.json'):
                    copied.append(copy(path, target / 'analysis' / path.relative_to(analysis)))
        for name in ('effective-config.json', 'pricing-snapshot.json'):
            path = run / name
            if path.is_file():
                copied.append(copy(path, target / name))
    for path in sorted((ROOT / 'configs').glob('*.json')):
        if path.name.startswith('security-bench-aabd') or path.name.startswith('security-bench-pricing'):
            copied.append(copy(path, DEST / 'configs' / path.name))
    for relative in ('data/agent-security-study/selection-2026-10-30-v4.json',
                     'data/workspace-evidence/2026-10-30-dataset-acquisition/verification.json',
                     'data/workspace-evidence/2026-11-01-merged-table/merged-table.md',
                     'data/workspace-evidence/2026-11-01-merged-table/merged-table.csv',
                     'data/workspace-evidence/2026-11-01-merged-table/merged-table.json'):
        path = ROOT / relative
        if path.is_file():
            copied.append(copy(path, DEST / relative))
    lines = ['# 2026-11-01 实验报告包', '',
             '本目录是进入 Git 的报告与派生指标集合；原始请求/响应、数据集和模型权重不在此处。', '',
             '## 内容', '']
    for path in copied:
        lines.append('- ' + path.relative_to(DEST).as_posix())
    lines += ['', '## 未包含', '',
              '- data/agent-security-study/runs/*/raw/：第三方提示词和原始响应，只放本地。',
              '- data/agent-security-study/datasets/：上游数据快照，体积大且有独立许可。',
              '- D:/models/：本地权重（Qwen3Guard、GLiGuard、Laya）。',
              '- .env、.venv-local/。']
    (DEST / 'README.md').write_text(chr(10).join(lines) + chr(10), encoding='utf-8')
    checks = []
    for path in sorted(p for p in DEST.rglob('*') if p.is_file()):
        checks.append(sha256(path) + '  ' + path.relative_to(DEST).as_posix())
    (DEST / 'SHA256SUMS.txt').write_text(chr(10).join(checks) + chr(10), encoding='utf-8')
    print('files', len(copied) + 2, 'bytes', sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()))


if __name__ == '__main__':
    main()
