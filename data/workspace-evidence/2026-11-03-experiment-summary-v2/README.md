# AgentHarm：已执行 10 个模型的实验汇总

同一批 50 条 validation 输入（25 harmful / 25 benign、8 个 family），每模型计划 3 次重复。只汇总已有逐条预测，不复核原始模型输出、不重跑旧实验。
多数票基于已有有效输出；平票和没有输出的项保持未决。N/50 与有效调用均单列。

| 模型 | 可判项/50 | 有效调用/150 | TP | FP | TN | FN | Accuracy | F1 | p50秒 | p95秒 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jev 1.14.0 (OpenLux relay) | 50/50 | 150/150 | 22 | 0 | 25 | 3 | 0.940 | 0.936 | 1.766 | 2.485 |
| vllm-sr/d3-mini (local BF16) | 50/50 | 150/150 | 24 | 0 | 25 | 1 | 0.980 | 0.980 | 0.109 | 0.141 |
| Laya-421M (local) | 50/50 | 150/150 | 7 | 2 | 23 | 18 | 0.600 | 0.412 | 0.078 | 0.094 |
| UESTC1010/SecJev-0.8B (local BF16) | 50/50 | 150/150 | 18 | 0 | 25 | 7 | 0.860 | 0.837 | 0.109 | 0.203 |
| GLiGuard-300M (local) | 50/50 | 150/150 | 25 | 1 | 24 | 0 | 0.980 | 0.980 | 0.078 | 0.094 |
| mistralai/Shieldstral-1.0-3B (local BF16) | 50/50 | 150/150 | 24 | 2 | 23 | 1 | 0.940 | 0.941 | 0.078 | 0.110 |
| Qwen3Guard-Gen-0.6B (local bf16) | 50/50 | 150/150 | 25 | 8 | 17 | 0 | 0.840 | 0.862 | 0.391 | 0.531 |
| Qwen/Qwen3.5-4B (local BF16) | 50/50 | 150/150 | 19 | 0 | 25 | 6 | 0.880 | 0.864 | 0.532 | 0.781 |
| GPT-6 Luna (OpenLux relay) | 47/50 | 139/150 | 21 | 1 | 24 | 1 | 0.957 | 0.955 | 3.484 | 14.063 |
| Claude Haiku 5.5 (OpenLux gptrelay) | 50/50 | 149/150 | 22 | 3 | 22 | 3 | 0.880 | 0.880 | 6.093 | 8.875 |

所有模型都有可判结果的共同子集：47 项；所有模型均有三次有效输出的共同子集：45 项。各模型在这两个共同子集上的分数、IDs 和投票覆盖见 results.json。
共同子集按可用性筛选，不能替代全 50 项表现。GPT 的 provider refusal 不转换为 safe/unsafe；Claude 的非 JSON 输出同样保留为失败。
费用、unknown API calls、token 和完整硬件/接口/参数见 comparison.csv 与 results.json。表中时间包含失败/拒绝，按统一经验分位数口径汇总；不同显卡/API 通道不构成公平速度排名。
Jev 主结果已按用户要求切换到 2026-11-03 OpenLux 中转重测；旧官方通道 run 保留在历史 CSV 中，不混入主比较。qwen35 对应 Qwen/Qwen3.5-4B，BF16 本地推理。
Jev-Guard 尚未执行；用户已停止权重下载，没有成绩，不纳入比较。
Public exposed validation pilot, not confirmatory; 50 items from 8 base families.
Wilson fields are descriptive and not family-cluster corrected; no significance/ranking claim.
Common subsets condition on provider response availability; report all-50 bounds and coverage.
Devices, provider routes and native input packaging differ; latency is not a controlled model-only comparison.
Local compute unpriced. Unknown API fees are not zero. Prices use original monitor snapshots.
Qwen3Guard uses the original-text primary run with Controversial=unsafe; JSON-wrapped run remains historical.

## 时间与费用

时间为各组全部 episode 的 HTTP 墙钟时间，包含失败和拒绝，不包含模型加载；本机 pilot 前另有 smoke。API 费用是原 monitor 价格快照估算，并非已核验账单。本地计算未计价。

| 模型 | episode 累计秒 | 已知 API 估价 USD | 未知费用 API 调用 | 全部 API 费用是否完整 |
|---|---:|---:|---:|---|
| jev | 279.955 | 0.00108310 | 0 | 是 |
| d3mini | 16.712 | 0.00000000 | 0 | 不适用（本地） |
| laya | 10.881 | 0.00000000 | 0 | 不适用（本地） |
| secjev | 17.442 | 0.00000000 | 0 | 不适用（本地） |
| gliguard | 12.159 | 0.00000000 | 0 | 不适用（本地） |
| shieldstral | 12.268 | 0.00000000 | 0 | 不适用（本地） |
| qwen3guard | 61.945 | 0.00000000 | 0 | 不适用（本地） |
| qwen35 | 83.779 | 0.00000000 | 0 | 不适用（本地） |
| gpt6luna | 797.719 | 0.00408188 | 11 | 否 |
| claudehaiku | 866.565 | 0.00336379 | 0 | 是 |

## 数据与统计口径

正类为 unsafe/harmful=1：TP 为正确识别有害输入，FP 为误报无害输入，TN 为正确放行无害输入，FN 为漏报有害输入。表中准确率分母为可判的唯一输入数，三次重复不当作三个独立任务。GPT 有 3 项完全缺预测，全 50 项准确率界限为 90%–96%；其 47 项有效分母上的 95.7% 不能直接视为全 50 项成绩。Claude 有一次非 JSON 输出失败，仍有 50 项可判结果。

这是 AgentHarm 输入检查（Mode A1），不是官方 Agent 有害任务执行成功率。当前结果来自公开 validation 的已暴露开发样本；8 个 family 内存在相关性，不据此作显著性或确认性结论。Qwen3Guard 采用原文输入、Controversial=unsafe 的主版本；JSON 包装旧版本保留在历史清单。不同模型的原生请求包装及机器不同，不能把时间差单独归因于模型。

## CSV 文件与复现

- comparison.csv：10 模型主比较，含覆盖、混淆矩阵、准确率/F1、耗时与费用。
- metrics.csv：逐次重复、可用多数票、共同 47 项和共同 45 项的完整指标。
- item-predictions.csv：主比较 500 个模型×输入的投票、标签、状态和输入 hash。
- episodes-all-runs.csv：所有已索引 run 的逐 episode 记录，包括历史版本、smoke、部分及失败记录；is_primary 区分主比较，不能混合计分。
- calls-all-runs.csv：所有已索引 run 的原 monitor 逐调用记录，含用量、价格与调用耗时。
- model-parameters.csv：主比较的有效模型配置；参数值为 JSON 时保留结构。完整 prompt 在原 effective-config.json，展开请求和原输出保留在原 run/raw，不复制或改写。
- run-inventory.csv：全部 run 的阶段、计划/实际数量、状态及主比较归属。

CSV 使用 UTF-8 BOM，空数值表示未知或不适用，不能填成零；具体原因见 results.json 和原始报告。所有 CSV 保留来源 run/monitor ID，原始文件未改动。其他旧测试只做历史索引，不冒充当前选型的完整基准结果。

复现命令：`./.venv-benchmark/Scripts/python.exe scripts/consolidate_agentharm_models.py --out <新的输出目录>`。该命令只汇总本地证据，不调用模型。来源内容 hash 见 results.json，输出 hash 见 SHA256SUMS.json。
