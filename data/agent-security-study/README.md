# Agent 安全替代研究：准备区

日期：2026-10-25。状态：准备阶段；本目录没有新增实验观测。

- [执行规范](../../docs/model-evaluation/agent-security-experiment-protocol.md)：研究对象、固定项、指标、失败和数据完整性规则。
- `protocol.template.json`：未冻结模板；所有 null 均需在对应阶段解决或有依据地标记不适用。模型配置需包含准确标识、provider、实际支持参数、模板与预算。
- `decisions.md`：范围、已定约定、未决参数及下一步。
- [report.template.md](report.template.md)：每次实验必须完成的报告；数据集与数量、时间/费用、基础计数、模型完整配置、prompt/请求和复现入口。
- `episode-columns.csv`、`call-columns.csv`、`prediction-columns.csv`：后续分析导出列约定；只有表头，无模拟数据。prediction 表为适用的逐条分类记录，支持从 gold 与预测重算 TP/FP/TN/FN。JSONL 原始账本及嵌套 usage / 错误详情仍是事实来源。

新全链路运行器尚未实现。现有相邻项目的 `jev_skill.monitor` 保留；[离线报告工具](../../scripts/experiment_report.py)已实现并通过八个离线测试，读取事实记录与原 monitor 汇总，不调用模型。职责与用法见[框架说明](../../docs/infrastructure/experiment-framework.md)。正式开跑前需做真实 pilot、冻结配置及验收；模板本身不会阻止错误执行。确认 run 进入独立的 `runs/<run-id>/`，禁止覆盖历史结果。

`unknown`/空值必须附原因，不能转成 0；费用要注明 measured / provider_reported / price_estimated / unknown。每个派生表关联原始记录与分析版本。人工复核和 AI 审核分别记录。

费用默认报告“API 费用（本地计算未计价）”。本地估价另列公式与费率，不自动与 API 费用混成实际总成本。模型完整参数须保存实际有效配置并注明未知默认值，不能只写“其余默认”。
