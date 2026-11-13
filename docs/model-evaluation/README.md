# 模型评测与校准

研究问题：在固定任务、样本、标签与请求下，各决策模型的准确性、风险排序、校准、延迟和成本如何？

| 文档 | 类型 | 证据与状态 |
|---|---|---|
| [AgentHarm A1 独立适配器](2026-10-28-agentharm-a1-adapter.md) | 输入检查工程与离线验收 | 只用原始请求；独立两模型比较、split 分表、逐项分数/时间/费用；尚未真实 API 试跑 |
| [AgentDojo 500 条三 type 比较](2026-10-27-agentdojo-type-comparison.md) | 历史静态探索实验 | 500 条配对及补测/时间费用，不是完整 Agent 防护 ASR |
| [Mode 定义与适配边界](agent-security-evaluation-modes.md) | 用户定义与执行约定 | 2026-10-28 确认 A1/A2 继承原 A 输入检查，数字仅为序号；B/C 待确认，旧定义及原文保留 |
| [当前实验选型（第三版）](2026-10-28-study-selection-v3.md) | 用户更换数据集及 Mode 确认 | AgentHarm=A1、MaliciousSkillBench=A2、MCPHunt=B、ATBench=C；11 项模型不变，未冻结运行配置 |
| [当前四个基准的本地获取记录](2026-10-27-selected-dataset-acquisition.md) | 原始数据/源码获取与文件校验 | 完整官方 AgentDojo、AgentHarm 公开数据、MCPHunt 轨迹与已有 ATBench；不代表已跑通环境或完成实验 |
| [四基准统一运行入口](../../security_bench/README.md) | 工程实现与离线验收 | 官方 AgentDojo 动态 gate、原始请求/轨迹分类、Jev/Responses/Chat 适配、原 monitor、预算/恢复/报告；无真实模型 pilot，AgentHarm 原生闭环未实现 |
| [历史实验选型（第一版）](2026-10-27-study-selection.md) | 历史用户选型记录 | 保留此前 12 项模型/方法、6 个数据集和五类参数因素供溯源 |
| [Agent 安全全链路对比执行规范](agent-security-experiment-protocol.md) | 2026-10-25 工作规范与准备模板 | 主 Agent 固定、Jev / LLM 安全模块配对；真实执行与资源记录要求已落盘，具体参数未冻结，尚未新增实验 |
| [Empirical study 参数与问题类型](empirical-study-parameter-selection.md) | 2026-10-22 官方接口与论文核查、设计建议 | Noul / Choice / Score 选用、影响因素与配对消融；尚未新增模型调用 |
| [Jev 论文模型与引用参考](jev-paper-model-reference.md) | 2026-10-22 原文设置核查 | 两篇指定安全论文及另外九篇；SecJev 等新增优先级、模型角色、11 篇官方 BibTeX |
| [Empirical study 模型选型](empirical-study-model-selection.md) | 2026-10-22 官方资料核查与设计建议 | 决策模型、近期通用 LLM、安全判别器；14 款核心候选与注入专项，尚未新增模型运行 |
| [Gate / selector 收益比较计划](agent-role-benefit-comparison-plan.md) | 2026-10-18 实验设计草案 | 四配置配对、已有数据复用、收益定义、基线与分阶段验证；尚未新增模型运行 |
| [Empirical study 资产与公开任务复用](empirical-study-assets-and-benchmarks.md) | 2026-10-15 本地盘点与选型 | 实际核对静态文件与预测；建议复用 AgentDojo 环境；24 个原任务待审核候选，未新增模型调用 |
| [Plumb 与 decider 本地试跑](local-model-smoke-test.md) | 连通与推理 smoke | 本地环境、模型版本、输出与重跑说明 |
| [H2O-Lightning 本地试跑](h2o-lightning-local-test.md) | 后端核查与 smoke | Transformers / 官方 shim 路径；stock vLLM 一致性未验证 |
| [本地 benchmark 首轮](local-benchmark-pilot.md) | 配对 pilot | 三款模型各 100 条静态安全任务；小样本探索 |
| [Jev、本地模型与 DeepSeek 比较](benchmark-comparison.md) | 结果分析 | 同 UID 历史 Jev 对照；DeepSeek 第二版属于探索性调整 |
| [Decision Index 的开放范围与构建方法](decision-index-construction.md) | 一手文档与源码调研 | 公共构建、任务改编、抽样与评分核查；11 个 fixture 聚合值通过检查，未重建全套或验证私有测试 |

## 对比模型与新增待测候选

| 模型 | 当前状态 | 后续安排 |
|---|---|---|
| Jev | 已有历史同 UID 安全任务结果 | 保留请求版本，作为托管决策基线 |
| Plumb-4B / decider-4b / H2O-Lightning-4B | 已有本地 smoke 与 100 条安全 pilot | 后续新模型沿用同题配对口径 |
| Microsoft-Decision-1 | 已纳入研究，尚未独立试跑 | 获取接口后做 smoke 与配对评测 |
| **vLLM-SR d3-mini（4.54B）** | **2026-10-13 新增，待试跑** | **优先本地接入，与现有 4B 模型比较** |
| vLLM-SR d3-nano（2.21B） | 新增尺寸备选，待试跑 | 较低资源与尺寸对照 |
| vLLM-SR d3（26.09B） | 新增大模型对照，待试跑 | 具备相应算力后比较 |
| vLLM-SR d3-flash / d3-lite / d3-edge | 纳入系列候选，尚未安排优先试跑 | 根据 pilot 与资源选择扩展 |

用户已确认之后试 vLLM-SR 模型。固定版本、接入路径与后续步骤见 [Decision 3.0 专题](../ecosystem/vllm-sr-decision-models.md)；本轮只核查资料，未执行模型实验。

## 数据、脚本与外部依赖

- [本地 smoke 快照](../../data/local-model-smoke-2026-10-09.json)、[H2O 快照](../../data/h2o-local-smoke-2026-10-09.json)。
- [推理脚本](../../scripts/local_model_smoke.py)、[PowerShell 入口](../../scripts/test-local-model.ps1)；本地权重与环境在 `local-models/`，该目录仅在本机保留。
- 完整安全配对数据与实现位于相邻 `D:/projects/jev`；[本地配对报告](../../../jev/reports/2026-10-09/local-models-paired/README.md)、[DeepSeek 配对报告](../../../jev/reports/2026-10-09/deepseek-paired/README.md)。这些链接需要本地同时存在相邻项目。
- [历史通用榜单](../../data/jevbench-v1.4.2.2-results.json)由 [生态主题](../ecosystem/README.md)维护，不与安全任务比例合成总排名。

## 关联与下一步

按 MSB、MCPTox、AgentDojo 分别报告，不把三者的标签语义混为一类。独立校准、盲测和严格的性能比较尚待补充。[Microsoft-Decision-1](../ecosystem/microsoft-decision-1.md) 当前只有厂商资料，配对实测列为待做。

2026-10-13 用户确认：后续 benchmark 转换参考 [Decision Index 的适配逻辑](decision-index-construction.md#后续-benchmark-转换的参考约定)，包括统一决策接口、逐任务 adapter、任务边界说明、确定性冻结与泄露检查。该方向已记录，具体转换协议与实现待后续确定。

[全部主题](../README.md)

历史本地/DeepSeek配对与提示词对照见[证据索引](../../data/workspace-evidence/README.md)；复用代码见[framework](../../framework/README.md)。
