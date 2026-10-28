"""Build and verify a portable ZIP of the four selected raw benchmarks."""
import hashlib
import json
from pathlib import Path
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/agent-security-study/datasets/2026-10-27'
NAME = 'jev-agent-security-datasets-2026-10-27-v1'
OUT = ROOT / 'artifacts/dataset-bundles'

VERIFY = '''"""Run after extraction: python verify_bundle.py"""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'MANIFEST.json').read_text(encoding='utf-8'))
failed = []
for item in manifest['files']:
    path = root / item['path']
    if not path.is_file():
        failed.append(item['path'] + ': missing')
        continue
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if path.stat().st_size != item['bytes'] or digest.hexdigest() != item['sha256']:
        failed.append(item['path'] + ': size/hash mismatch')
if failed:
    print('FAILED: ' + str(len(failed)) + ' files')
    print('\\n'.join(failed[:30]))
    raise SystemExit(1)
print('PASS: ' + str(len(manifest['files'])) + ' files verified; environment execution not tested.')
'''

README = '''# Jev Agent 安全研究：可迁移原始数据包

打包日期：2026-10-27。只包含当前选定的四个基准及 MCPHunt 配套源码。

## 解压和校验

1. 将整个 ZIP 下载到本机，核对同名 `.sha256` 文件。
2. 用支持 ZIP64 的解压工具完整解压，保留目录结构。
3. 在解压目录运行 `python verify_bundle.py`，需要 Python 3.9+，只使用标准库。
4. 程序显示 PASS 后，可按下面相对路径接入各机器的实验代码。

压缩包 SHA-256：Windows 使用 `Get-FileHash <文件名.zip> -Algorithm SHA256`；
Linux/macOS 使用 `shasum -a 256 <文件名.zip>`。
Windows 建议解压到较短路径，如 `D:/datasets/`；完整官方仓库含多层目录。

## 数据入口

| 数据集 | 相对路径 | 内容 |
|---|---|---|
| AgentDojo | `datasets/agentdojo/` | 完整官方仓库，四个 suite 的环境、任务、攻击与判分源码；不是 TS-Bench 静态派生片段 |
| AgentHarm | `datasets/agentharm/benchmark/` | 全部公开 harmful、benign 和 chat 文件；不含未公开的私有测试集 |
| MCPHunt | `datasets/mcphunt/` | 全部 6,786 条公开轨迹；main 3,615、mitigation 2,706、其余 supplemental 465 分层保留 |
| MCPHunt 源码 | `sources/mcphunt/` | 官方任务、标签规则、说明和发布工具源码 |
| ATBench | `datasets/atbench/ATBench.json` | 既有原始测试集 1,000 条；不是派生截断或分块版本 |

AgentHarm 的 harmful、benign 各有 test_public 176 条和 validation 32 条；
chat 有 test 44 条和 validation 8 条。变体不能相加解释为独立基础任务数。

完整版本、来源 URL、逐文件字节数和 SHA-256 见 `MANIFEST.json`。
原获取 manifest 和公开源元数据保存在 `provenance/`；本包所有数据入口为相对路径。
MANIFEST 不包含其自身的哈希；包外 `.sha256` 校验整个 ZIP。

## 多机使用边界

这是数据与源码分发包，不是可直接运行的 Python 环境或容器。
不包含本机 API 凭据、模型权重、虚拟环境或本项目实验输出。
AgentDojo 官方仓库原本附带的公开 runs 和资料按原样保留。
各机器仍需安装相应依赖并配置自己的凭据；本次未执行环境或模型验收。
使用同一份数据包不会保证不同硬件或 API 的逐位一致结果。

此次固定的是获取快照，不是正式确认实验配置。
Mode A1/A2/B/C 含义、样本划分、主 Agent、预算与判分合同尚待确定。
旧样本暴露状态不因打包而清除。

保留各上游 LICENSE、README 及数据卡。AgentHarm 的额外使用条款见其 LICENSE；
MCPHunt 数据许可见其 README 和 Croissant 元数据，源码许可见源码 LICENSE。
ATBench 本地已有原始文件未附独立许可文件，本包不推定或授予额外使用权；
再分发和使用前按其上游条款核对。本包不改变任何上游许可。
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT / (NAME + '.zip')
    if archive.exists():
        raise FileExistsError('Refusing to overwrite existing package')
    inputs = []
    datasets = {}
    for name, destination in [('agentdojo', 'datasets/agentdojo'),
                               ('agentharm', 'datasets/agentharm'),
                               ('mcphunt', 'datasets/mcphunt'),
                               ('mcphunt-source', 'sources/mcphunt')]:
        base = BASE / name
        record = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
        assert record['status'] == 'download_complete', name
        datasets[name] = {'source': record['source'], 'revision': record['revision'],
                          'path': destination, 'files': len(record['files'])}
        for item in record['files']:
            relative = Path(item['path']).relative_to('snapshot').as_posix()
            inputs.append((base / item['path'], destination + '/' + relative, item['sha256']))
        inputs.append((base / 'manifest.json', f'provenance/{name}/acquisition-manifest.json', None))
        if (base / 'upstream-metadata.json').exists():
            inputs.append((base / 'upstream-metadata.json', f'provenance/{name}/upstream-metadata.json', None))
    historical = Path('D:/projects/jev/data/agent-safety-full-manifest.json')
    old = json.loads(historical.read_text(encoding='utf-8'))
    datasets['atbench'] = {'path': 'datasets/atbench/ATBench.json', 'rows': 1000,
        'source_revision': old['source_revisions']['ATBench_HF'],
        'source_reference': 'provenance/atbench/historical-source-manifest.json'}
    inputs.append((Path('D:/projects/jev/data/atbench-test.json'), 'datasets/atbench/ATBench.json',
                   old['source_sha256']['ATBench/test.json']))
    inputs.append((historical, 'provenance/atbench/historical-source-manifest.json', None))
    inputs.append((ROOT / 'data/agent-security-study/selection-2026-10-27-v2.json',
                   'provenance/study-selection-v2.json', None))
    manifest = {'record_kind': 'portable_dataset_bundle_not_experiment', 'name': NAME,
        'created_at_utc': datetime.now(timezone.utc).isoformat(), 'datasets': datasets,
        'environment_execution_verified': False, 'mode_semantics': 'unresolved', 'files': []}
    names = set()
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as bundle:
        for source, relative, expected in inputs:
            if relative in names or '..' in Path(relative).parts:
                raise ValueError('Duplicate or invalid archive path')
            names.add(relative)
            data = source.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if expected and digest != expected:
                raise ValueError('Source hash mismatch: ' + relative)
            bundle.writestr(NAME + '/' + relative, data)
            manifest['files'].append({'path': relative, 'bytes': len(data), 'sha256': digest})
        for relative, text in [('README.md', README), ('verify_bundle.py', VERIFY)]:
            data = text.encode('utf-8')
            bundle.writestr(NAME + '/' + relative, data)
            manifest['files'].append({'path': relative, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        encoded = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        bundle.writestr(NAME + '/MANIFEST.json', encoded)
    print('ZIP written; verifying every archived file...', flush=True)
    with zipfile.ZipFile(archive) as bundle:
        for item in manifest['files']:
            data = bundle.read(NAME + '/' + item['path'])
            if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Archive verification failed: ' + item['path'])
        assert bundle.read(NAME + '/MANIFEST.json') == encoded
    digest = hashlib.sha256()
    with archive.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    checksum = OUT / (NAME + '.zip.sha256')
    checksum.write_text(digest.hexdigest() + '  ' + archive.name + '\n', encoding='ascii')
    (OUT / (NAME + '-README.md')).write_text(README, encoding='utf-8')
    summary = {'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': digest.hexdigest(),
        'verified_files': len(manifest['files']), 'verification': 'all_archived_payload_hashes_verified',
        'uncompressed_payload_bytes': sum(f['bytes'] for f in manifest['files']),
        'checksum_file': str(checksum), 'environment_execution_verified': False}
    (OUT / (NAME + '-package-report.json')).write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
