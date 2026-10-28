# 2026-10-28 换机恢复

状态：代码、草案配置、原 monitor 的逐字节快照和依赖锁随 Git 迁移。没有真实全模型跑测。数据、key、模型权重和本地服务不随 Git 上传。

## 代码与环境

```powershell
git clone https://github.com/freezetheflame/jev-ecosystem-research.git
cd jev-ecosystem-research
python -m venv .venv-benchmark
./.venv-benchmark/Scripts/python.exe -m pip install -r requirements/security-bench-py312.lock.txt
./.venv-benchmark/Scripts/python.exe -m unittest discover -s security_bench/tests -v
```

锁文件来自 Windows Python 3.12；新机器使用 Python 3.12。GPU 推理服务运行时另外部署，本仓库依赖锁不包含所有模型的 torch/transformers 等专用部署依赖。历史 AgentDojo 环境测试在没有其源码快照时可能 skip，不能把 skip 说成环境通过。

当前四份模板默认 `monitor_workspace: vendor/preserved-monitor`，其中 monitor.py 与原 `D:/projects/jev/jev_skill/monitor.py` 字节完全一致，SHA256 为 `f1f3d220f87681e79d65d9baf91e7b1e30733f80312c60b4129a42be8fc00c67`。Git 对该文件禁用换行转换。原文件及接口未改；快照来源见 `security_bench/reuse-manifest.json`。这样当前入口不再要求另一台机器恰好有 `../jev`。旧 AgentDojo 配置保留原路径，按需显式配置。

## 数据：需要两个归档

本机 `artifacts/dataset-bundles/` 下的文件没有上传 Git，也没有在本轮上传 Box。换机前请把以下两个 ZIP 及各自 `.sha256` 一起存到 Box 或复制到新电脑：

- `jev-agent-security-datasets-2026-10-27-v1.zip`：已有完整包，包含 AgentHarm、MCPHunt、ATBench 和旧 AgentDojo。后者保留作历史，不是当前第四个基准。
- `maliciousskillbench-2026-10-28-v1.zip`：本轮补充包，包含完整原生 release 表、结构/来源元数据、split 文件和来源 manifest，替换旧名单中的 AgentDojo。不是静态派生子集。

归档大小与 SHA256 见 [迁移清单](../../data/agent-security-study/machine-handoff-2026-10-28.json)。新电脑先核对 `Get-FileHash <ZIP> -Algorithm SHA256`。解压第一个 ZIP 后运行包内 `python verify_bundle.py`；第二个 ZIP 保留 `maliciousskillbench/manifest.json` 与 `maliciousskillbench/snapshot/` 的相对结构。原生文件 hash 在正式计划前还会由运行器对来源 manifest 复核。

例如将两包解压到 `D:/datasets/` 后：

```powershell
$env:SECURITY_BENCH_DATA_ROOT = 'D:/datasets/jev-agent-security-datasets-2026-10-27-v1'
Copy-Item configs/security-bench-all-models.template.json configs/my-run.json
```

在 `my-run.json` 中填写 `maliciousskillbench_path: D:/datasets/maliciousskillbench/snapshot`。ATBench 优先从 portable bundle 自动定位。不要再依赖旧电脑的 `D:/projects/jev/...` 数据路径。AgentHarm 单独运行可复制 `configs/agentharm-all-models.template.json`，无需 MSB 或其他数据。

## 接着做什么

```powershell
./.venv-benchmark/Scripts/python.exe -m security_bench inspect-models --config configs/agentharm-all-models.template.json --out-dir data/agent-security-study/preparations/model-preview-new-machine
./.venv-benchmark/Scripts/python.exe -m security_bench doctor --config configs/my-run.json
```

前一条不需要 key、数据或权重；后一条会如实列出未完成的部署、参数和实验配置。key 仅放命名环境变量。全模型真实连通、Jev-Guard 发布接口、具体版本/尺寸、B/C 合同、样本划分和预算等仍按[模型适配说明](2026-10-28-model-inference-adapters.md)完成；当前草案不能当成已冻结的确认实验。

`data/agent-security-study/runs/` 和 preparations、`.venv-benchmark/`、模型权重均被 Git 忽略；本轮没有这些目录中的真实新实验需要恢复。若后续产生运行结果，需把完整 run 目录连同 raw/telemetry/source/manifest 另行迁移，不能只保存汇总分数。
