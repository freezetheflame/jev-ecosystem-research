# RQ1/RQ2 审阅包（2026-11-13）

给学长审阅用：一页结论 + 数据清单 + 补充 insight。全部数字来自仓库内可复现产物；本包不修改正式汇总。

## 1. 三分钟结论

**RQ1（五位置 × 12 判官）**
- 没有通吃的判官：AgentHarm 上 Jev top-1 概率 52%（d3mini 40%），StepShield holdout 56% vs 40%，都是掷硬币。
- 可识别的第一名只有三处：TS-Bench（GPT-6 Luna 100%）、Response（Jev 80%）、StepShield test（Jev 83%，按 balanced accuracy）；InjecAgent 的 100% 是正例检测的平凡结果。
- 换指标就换冠军：StepShield test 上 Jev 按 MCC 第 4、按 balanced accuracy 第 1。
- 位置内部也会翻转：TS-Bench 的 agentharm-traj 上 Jev 反超 GPT，asb-traj 上 GPT 大幅领先。

**RQ2（成本与效率）**
- 成本结构是 O(steps)：StepShield 每轨迹 8.7–10.1 次判断，其他位置 1 次；Jev 6.36 s/episode vs AgentHarm 0.67 s。
- 0.5/argmax 不是中立基准：MCC 最优阈值从 0.01 到 0.95；Jev 在 StepShield 上 0.50→0.77 使 MCC 从 0.535 升到 0.710。
- 成本与检出耦合：从不告警的模型调用最多；跨模型比每 episode 成本会奖励好模型。

**补充 insight（不在 RQ1/RQ2 主表，但决定结论强度）**
- ConstraintGuard 只覆盖 12.9% 的任务约束；覆盖子集上 CG 召回 100% 但 FPR 100%，CCD 同召回 FPR 5.3%。
- CCD（轨迹分解）补回 prefix 漏检的 44/55（80%），新增误报 3/55（5.5%）；TS-Bench 单步口径下分解无显著收益。
- 五位置映射有 unit/attacker/label 三类不可比，必须写进论文表。

## 2. 文件

| 文件 | 内容 |
|---|---|
| RQ1-data.md | RQ1 数据构成、每位置前三、可识别性、指标敏感性、来源迁移、缺口 |
| RQ2-data.md | RQ2 成本结构、O(steps)、操作点成本、检出耦合、缺口 |
| SUPPLEMENTARY-INSIGHTS.md | 其他文件夹里的补充 insight（阈值/MCC/CG/CCD/TS-Bench/位置映射） |
| data/ | 关键表副本（metrics_ci、metrics_full、time_tokens、thresholds、shift、cost、rank_*） |
| data-index.csv | 每个数据文件的路径、口径、状态 |

## 3. 请学长重点把关的五件事

1. RQ1 的主表是否应按位置分栏、用 MCC + matched-FPR recall 双指标（避免 MCC 掩盖召回）。
2. “第一名不可识别”是否足以支撑论文的核心 claim（还需要冻结协议/更多样本？）。
3. InjecAgent 的 positives-only 与位置映射的 unit/attacker 限定，是否按当前写法可接受。
4. RQ2 是否应降级为“成本结构”而非“成本结论”（价格快照、主 Agent/reviewer 成本仍缺）。
5. 补充 insight 是否进正文（CG 基线、CCD、TS-Bench 负结果），还是放附录。

## 4. 已知限制（务必随包转发）

- 全部为 descriptive：1 次 repeat、公开已暴露 split、无 freeze manifest、无预注册。
- 个别人工/自动口径未统一：LLM 判官无概率，只能 native 点；本地模型未计价。
- 部分 cell 仍在补（Claude/GPT 的 WildGuard-E；Claude/GPT 的 StepShield 成本行在 time_tokens/cost 为空）。
- RQ1 的 CI 是按内容族 bootstrap 的（1000 次），跨族设计效应未额外建模。

