# RQ1：五个检查位置上的判官有效性（数据与结果）

## 1. 问题与单位

RQ1：在同一个执行链的不同检查位置上，12 种判官配置的有效性与错误方向如何变化？

单位：request / item / step / trajectory / response（见 data-index.csv 与 position-mapping 文档）。
所有指标为描述性：1 次 repeat、公开已暴露 split、阈值未预注册。

## 2. 数据构成

| 位置 | 数据集 | 可判分 n | 正类比例 | 内容族数 |
|---|---|---:|---:|---:|
| User Request（AgentHarm） | agentharm | 416 | 50.0% | 52 |
| External Content（InjecAgent） | injecagent | 2108 | 100.0% | 2108 |
| Tool Call（TS-Bench） | tsbench | 5401 | 30.2% | 2971 |
| Response（WildGuard-E） | wildguard_response | 1709 | 16.6% | 1709 |
| In-flight Action（StepShield test） | stepshield_test | 7933 | 8.1% | 7925 |
| In-flight Action（StepShield holdout） | stepshield_test_holdout | 216 | 50.0% | 216 |

注：InjecAgent 全正类，MCC 无定义，只报 TPR；TS-Bench 的 1,781 条 gold=0.5 争议项不进二分类分母。

## 3. 每位置前三名（MCC，括号内为族聚类 bootstrap 95% CI）

| 位置 | 第 1 | 第 2 | 第 3 |
|---|---|---|---|
| User Request（AgentHarm） | jev-packy-1.14.0 0.769 [0.660, 0.871] | d3mini 0.763 [0.675, 0.852] | shieldstral 0.707 [0.608, 0.817] |
| External Content（InjecAgent）（按 TPR；MCC 无定义） | gpt6luna TPR 99.6% | claudehaiku TPR 95.6% | jev-packy-1.14.0 TPR 95.4% |
| Tool Call（TS-Bench） | gpt6luna 0.699 [0.671, 0.724] | claudehaiku 0.636 [0.611, 0.659] | jev-packy-1.14.0 0.565 [0.536, 0.590] |
| Response（WildGuard-E） | jev-packy-1.14.0 0.746 [0.700, 0.790] | d3mini 0.729 [0.677, 0.770] | qwen35 0.608 [0.557, 0.660] |
| In-flight Action（StepShield test） | d3mini 0.700 [0.671, 0.727] | qwen35 0.592 [0.556, 0.625] | kev 0.581 [0.544, 0.612] |
| In-flight Action（StepShield holdout） | jev-packy-1.14.0 0.847 [0.775, 0.910] | d3mini 0.843 [0.769, 0.909] | qwen35 0.783 [0.699, 0.854] |

## 4. 第一名是否可识别

| 位置 | 排名指标 | 第一名 | top-1 概率 |
|---|---|---|---:|
| User Request（AgentHarm） | mcc | jev-packy-1.14.0 | 52.3% |
| External Content（InjecAgent） | tpr | gpt6luna | 100.0% |
| Tool Call（TS-Bench） | mcc | gpt6luna | 100.0% |
| Response（WildGuard-E） | mcc | jev-packy-1.14.0 | 80.1% |
| In-flight Action（StepShield test） | bacc | jev-packy-1.14.0 | 82.6% |
| In-flight Action（StepShield holdout） | mcc | jev-packy-1.14.0 | 55.6% |

top-1 概率接近 50% 表示“第一名”只是掷硬币；AgentHarm 与 StepShield holdout 属于这种情况。InjecAgent 的 100% 只是“正例全部被检出”的平凡结果，不代表可识别性。

## 5. 指标敏感性（换指标换冠军）

| 位置 | 模型 | MCC 名次 | BAcc 名次 | TPR 名次 |
|---|---|---|---|---|
| Tool Call（TS-Bench） | gpt6luna | 1 | 1 | 2 |
| Tool Call（TS-Bench） | claudehaiku | 2 | 2 | 1 |
| Tool Call（TS-Bench） | jev-packy-1.14.0 | 3 | 3 | 6 |
| Tool Call（TS-Bench） | d3mini | 4 | 5 | 8 |
| Tool Call（TS-Bench） | qwen35 | 5 | 4 | 5 |
| Tool Call（TS-Bench） | qwen3guard | 6 | 6 | 7 |
| Tool Call（TS-Bench） | kev | 7 | 9 | 9 |
| Tool Call（TS-Bench） | shieldstral | 8 | 10 | 10 |
| Tool Call（TS-Bench） | jevguard | 9 | 7 | 3 |
| Tool Call（TS-Bench） | gliguard | 10 | 8 | 4 |
| Tool Call（TS-Bench） | secjev | 11 | 11 | 11 |
| Tool Call（TS-Bench） | laya | 12 | 12 | 12 |
| In-flight Action（StepShield test） | d3mini | 1 | 2 | 3 |
| In-flight Action（StepShield test） | qwen35 | 2 | 4 | 5 |
| In-flight Action（StepShield test） | kev | 3 | 3 | 4 |
| In-flight Action（StepShield test） | jev-packy-1.14.0 | 4 | 1 | 1 |
| In-flight Action（StepShield test） | secjev | 5 | 6 | 6 |
| In-flight Action（StepShield test） | qwen3guard | 6 | 8 | 9 |
| In-flight Action（StepShield test） | jevguard | 7 | 5 | 2 |
| In-flight Action（StepShield test） | gliguard | 8 | 7 | 7 |
| In-flight Action（StepShield test） | laya | 9 | 10 | 8 |
| In-flight Action（StepShield test） | shieldstral | 10 | 9 | 10 |

最典型：StepShield test 上 Jev 按 MCC 第 4、按 balanced accuracy 第 1；TS-Bench 上 Claude 按 MCC 第 2、按 TPR 第 1。

## 6. 位置内部的分布迁移

TS-Bench 三个来源域（同位置、同合同）：

| 来源 | 正类比例 | Jev MCC | GPT-6 Luna MCC | Claude MCC |
|---|---:|---:|---:|---:|
| agentdojo-traj | 29.0% | 0.833 | 0.923 | 0.660 |
| agentharm-traj | 50.6% | 0.554 | 0.432 | 0.422 |
| asb-traj | 28.5% | 0.455 | 0.652 | 0.644 |

agentharm-traj 上 Jev 反超 GPT；asb-traj 上 GPT 大幅领先——所以“LLM 更强”是来源依赖的。

## 7. 写论文前必须补的数据/声明

1. Frozen protocol：样本、阈值、指标、停止规则；当前全部是 descriptive。
2. 逐条目预测（LLM 的 Claude/GPT 在 StepShield 上）用于配对 McNemar；当前只有聚合指标。
3. 聚类 CI 已做（family bootstrap），但需在论文中说明族数与设计效应。
4. InjecAgent 需要配对负例才能报 FPR；或者明确只报检出率。
5. position mapping 的 unit/attacker/label 限定必须写进表。

