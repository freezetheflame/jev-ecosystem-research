# Agent 安全替代研究：准备区

日期：2026-10-25。状态：准备阶段；本目录没有新增实验观测。

- [执行规范](../../docs/model-evaluation/agent-security-experiment-protocol.md)：研究对象、固定项、指标、失败和数据完整性规则。
- `protocol.template.json`：未冻结模板；所有 null 均需在对应阶段解决或有依据地标记不适用。模型配置需包含准确标识、provider、实际支持参数、模板与预算。
- `decisions.md`：范围、已定约定、未决参数及下一步。
- [AgentHarm A1 独立适配器](../../docs/model-evaluation/2026-10-28-agentharm-a1-adapter.md)：原始请求输入检查，独立配置、离线请求预览、按 split 的分类/时间/费用报告；无主 Agent 依赖，不是官方 harm score。
- [四基准统一入口](../../security_bench/README.md)、[运行配置模板](../../configs/security-bench.template.json)：当前为 AgentHarm/MSB 输入分类与 MCPHunt/ATBench 原始轨迹判断，复用原 monitor；AgentDojo 动态入口保留作历史配置。真实 pilot 和科学配置仍待确定。AgentHarm 官方有害任务执行评分尚未接入。
- [当前四个基准的获取记录](../../docs/model-evaluation/2026-10-27-selected-dataset-acquisition.md)及 [机器可读索引](dataset-acquisition-2026-10-27.json)：原始快照、来源版本、文件哈希与实际条目数；AgentDojo 使用完整官方基准入口，不采用历史静态派生片段。
- [当前选型（第四版，A/A/B/D）](../../docs/model-evaluation/2026-10-30-aabd-adaptation.md)及 [JSON 清单](selection-2026-10-30-v4.json)：AgentHarm=A1、InjecAgent=A2、TS-Bench=B、ATBench=D；11 个模型/方法不变，A1/A2 同属输入检查，B 为执行前动作安全，D 为完整轨迹审计，C 暂时空缺。第三版及旧数据包保留为历史。
- [历史选型](../../docs/model-evaluation/2026-10-27-study-selection.md)及 [原 JSON](selection-2026-10-27.json)：保留此前 12 项模型/方法、6 个数据集和五类参数因素供溯源。
- [历史 Mode A–D 定义](../../docs/model-evaluation/agent-security-evaluation-modes.md)：保留旧定义、用户论证原文和待核验引用；新代码不自动继承旧定义，现有报告工具仍按旧命名空间验证。
- [report.template.md](report.template.md)：每次实验必须完成的报告；数据集与数量、时间/费用、基础计数、模型完整配置、prompt/请求和复现入口。
- `episode-columns.csv`、`call-columns.csv`、`prediction-columns.csv`：后续分析导出列约定；只有表头，无模拟数据。prediction 表为适用的逐条分类记录，支持从 gold 与预测重算 TP/FP/TN/FN。JSONL 原始账本及嵌套 usage / 错误详情仍是事实来源。

新增 `security_bench` 负责计划、动态/离线适配、逐调用落盘、原 monitor 关联、预算停止及版本化报告；当前仅完成离线工程验证，尚无真实模型 pilot。原 `scripts/experiment_report.py` 及其历史 Mode A/B/C/D 合同保持独立。新运行模板保留未定参数，doctor 会拒绝缺项；确认 run 进入独立的 `runs/<run-id>/`，禁止覆盖历史结果。职责与用法见[框架说明](../../docs/infrastructure/experiment-framework.md)。

`unknown`/空值必须附原因，不能转成 0；费用要注明 measured / provider_reported / price_estimated / unknown。每个派生表关联原始记录与分析版本。人工复核和 AI 审核分别记录。

费用默认报告“API 费用（本地计算未计价）”。本地估价另列公式与费率，不自动与 API 费用混成实际总成本。模型完整参数须保存实际有效配置并注明未知默认值，不能只写“其余默认”。

2026-10-27 单独执行了[官方 Jev 长上下文连通 smoke](../../docs/infrastructure/jev-official-long-context-smoke.md)，原始数据放在独立 `data/jev-official-long-context/`。它不是 Mode A–D 安全分类数据，不进入本研究混淆矩阵或正式对比结果。
## 2026-11-02：本机补跑完成

已同步另一台机器的原始记录；按用户要求未复核或重跑其已完成模型。在 RTX 4070 SUPER 12GB 上新完成 D3-Mini、Shieldstral-1.0-3B、Qwen3.5-4B、SecJev-0.8B，同一 50 条 validation × 3 repeats，共 600 次 pilot + 8 次 smoke，全成功。本地计算未计价，无本轮 API 调用。[四模型结果](../workspace-evidence/2026-11-02-local-agentharm-four-models/README.md)和[完整说明](../../docs/model-evaluation/2026-11-02-local-agentharm-pilots.md)。Jev-Guard 制品/接口待落实，留给 3090；科学确认配置仍未冻结。上文早期“尚无真实 pilot”保留为当时状态。

## 2026-11-03：11模型AgentHarm pilot已齐

Jev-Guard原生安全头补跑完成，150+2次本地推理成功。最新[11模型汇总](../workspace-evidence/2026-11-03-experiment-summary-v6-final/README.md)包括参数量、全50项正确完成率、条件准确率、token覆盖和耗时/费用。[Jev-Guard执行说明](../../docs/model-evaluation/2026-11-03-jevguard-agentharm.md)记录接口与运行时限制。仅指当前AgentHarm 50×3开发pilot，不代表其他基准或确认性矩阵已完成。

## 2026-11-04：Kev-4B补充pilot完成

[Kev执行说明](../../docs/model-evaluation/2026-11-04-kev-agentharm.md)；同一AgentHarm50×3全部正确，另2条smoke成功，均为本地BF16未合并的探索性测试。最新[12模型汇总](../workspace-evidence/2026-11-04-experiment-summary-v7/README.md)包括参数量、统一50项主指标、token、耗时与费用，原11模型记录保留。

## 汇总结果固定入口

日常查阅统一进入[summary/](summary/README.md)。当前[AgentHarm 12模型汇总](summary/agentharm/README.md)包含Kev-4B；来源版本和hash在同目录source.json及SHA256SUMS.json。
