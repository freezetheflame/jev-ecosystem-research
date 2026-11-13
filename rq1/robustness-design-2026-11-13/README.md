# rq1/robustness-design-2026-11-13 - 鲁棒性实验设计

状态：**设计稿，未执行**（无模型调用、无新结果）。

主文档：**[PROTOCOL.md](PROTOCOL.md)** - Same Attack, Different Position：借 2610.17820 的三个控制（同一 payload / 同一策略 / 同一套指标），把因变量换成"判官 x 检查位置"。

## 文件

| 文件 | 内容 |
|---|---|
| PROTOCOL.md | 完整设计：抄/改/加、威胁模型、五位置攻击面、操作点协议、指标、功效、分层与预算、有效性审计、执行计划、假设与反驳条件 |
| RQ3-SCOPE-AND-SCHEMES.md | **RQ3 子集版范围与方案**：5 个方向、S/M/L 三种方案、子集抽样规则、M 方案确切矩阵与功效 |
| scheme-comparison.csv | S/M/L x 位置 的调用量预算 |
| attack-matrix.csv | 机器可读攻击矩阵：家族、机制、carrier、适用位置、变体数、生成方式、校验、目标、层级、来源 |
| paper-2610.17820-extract.md | 对源论文的逐节抽取（威胁模型、系统、任务、13 家族/50 变体、ASR/GBR 定义、全部结果数字、五个 gap、内部不一致） |
| repo-robustness-assets.md | 仓库内可复用的攻击/校验/记录资产清单（21 项、5 问答案、8 项待建；security_bench 不能直接注入变体，framework/paired.py 只能跑 pilot） |

## 三条最关键的设计决定

1. **同一 payload 走五个位置**（A 层），只有这样才能说"位置改变鲁棒性"；接口型与位置原生攻击只做深度层（C 层）。
2. **matched-FPR 操作点**：每个 模型 x 位置 在 dev 上把 block 阈值选到 benign FPR <= 5%，冻结后再攻击；同时报默认 0.5/argmax 作对照。否则比较的是阈值，不是鲁棒性。
3. **G4（benign 误报）与 G5（时序延迟）升为一等指标**：该文的 ASR/GBR 只测失败方向；部署代价在误报，prefix 的代价在"告警太晚"。

## 规模与成本（planning estimates）

约 20 万次判官调用（A 9.8 万 + B 1.4 万 + C 6.7 万 + D 2.7 万）；Jev 约 7.5 万次，~3-4 美元（按 0.042 USD/M 输入、~1k tokens/次，非账单）；GPT 单价需先取价格快照。墙面时间预留 4-6 天。MVP 约 3-4 万次调用，1 周。

## 与现有工作的关系

- 2610.17820：提供控制设计与 attack 家族模板；它明确没做执行链、操作点、预算曲线、跨粒度、防御臂。
- JevAdvBench / JevOut / JevBreak / DecisionRobust / FlipJev：单判官、单位置的攻击与鲁棒性；本设计的差异是"位置"与"matched-FPR"。
- rq1/ext-2026-11-13：提供 clean 操作点、MCC/CI、O(steps) 成本，作为本设计的基线。

## 实现现实（详见 PROTOCOL.md §9.5）

- security_bench 的 cases 是 loader 生成 + 哈希冻结，**不能直接注入"同 item 的变体视图"**；主实验需要加变体注册表（2-3 人日），pilot 可用 framework/paired.py（任意行、同 gold，但仅 smoke/pilot、repeats=1）。
- JevOut 引擎可跑（optimize_context / independent / retest / checker），但默认指向官方 jev-1.13.0，没有 OpenLux 适配器；主数据是 Packy 1.14.0，adaptive 前必须做版本桥接。
- 语义校验只有单 LLM checker；人工盲审表与一致性代码需要新建。
- 需新建模块总计约 12-15 人日（变体注册、payload 编译、逐项预算、adaptive 桥、配对分析、审计工具、pilot）。

## 下一步

0. 先选方案（推荐 M，约 2.9 万次调用）：见 RQ3-SCOPE-AND-SCHEMES.md。
1. 拍板 PROTOCOL.md 第 13 节的五个开放项（judge-level vs replay、guard 选择、位置优先级、adaptive 披露策略、预算）。
2. 先做 MVP pilot（30 例 x 2 位置 x 3 判官 x 2 家族），估方差后再冻结主实验。
3. 冻结 manifest 前不要跑 test 集。