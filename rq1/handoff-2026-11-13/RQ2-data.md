# RQ2：成本与效率（数据与结果）

## 1. 问题与口径

RQ2：在满足既定安全/效用要求时，引入判官组件的现金成本、延迟与调用量是多少？何时值得？

口径：API 费用为 list-price 估算（非账单）；本地计算未计价；延迟取成功 episode 的客户端墙钟；
分别报每判定（per decision）与每 episode（per trajectory），因为 StepShield 是 O(steps)。

## 2. 每位置成本结构（选 4 个代表模型）

| 模型 | 位置 | 调用/条目 | 单次调用均时 | episode 均时 | 输入 token/条目 |
|---|---|---:|---:|---:|---:|
| jev-packy-1.14.0 | User Request（AgentHarm） | 1.000 | 0.632 s | 0.667 s | 430 |
| jev-packy-1.14.0 | Tool Call（TS-Bench） | 1.000 | 0.711 s | 0.748 s | 1188 |
| jev-packy-1.14.0 | In-flight Action（StepShield test） | 8.735 | 0.683 s | 6.358 s | 8116 |
| d3mini | User Request（AgentHarm） | 1.000 | 0.089 s | 0.100 s | 212 |
| d3mini | Tool Call（TS-Bench） | 1.000 | 0.423 s | 0.460 s | 947 |
| d3mini | In-flight Action（StepShield test） | 9.380 | 0.348 s | 3.807 s | 6795 |
| gpt6luna | User Request（AgentHarm） | 1.007 | 3.177 s | 3.293 s | 217 |
| gpt6luna | Tool Call（TS-Bench） | 1.001 | 2.591 s | 2.635 s | 964 |
| claudehaiku | User Request（AgentHarm） | 1.000 | 2.519 s | 2.558 s | 288 |
| claudehaiku | Tool Call（TS-Bench） | 1.130 | 3.254 s | 3.961 s | 1400 |

关键：StepShield 每轨迹 8.7–10.1 次判断（cost.csv；部分旧 run 到 12.3），其他位置 1 次；O(steps) 是成本结构的主因。

缺口：Claude/GPT 的 StepShield 行在 cost.csv 与 time_tokens.csv 为空，未列入；需要补跑或标 N/A，不能用别的行替代。

## 3. 成本与检出耦合

“每轨迹首个 unsafe 后停止”意味着检出越好调用越少：

| 模型 | StepShield test 调用/轨迹 | TPR |
|---|---:|---:|
| shieldstral | 10.099 | 0.0% |
| qwen3guard | 10.017 | 7.5% |
| qwen35 | 9.746 | 46.3% |
| kev | 9.483 | 58.1% |
| d3mini | 9.380 | 80.3% |
| laya | 9.322 | 10.5% |
| secjev | 9.312 | 31.8% |
| gliguard | 8.879 | 31.3% |
| jev-packy-1.14.0 | 8.735 | 91.2% |
| jevguard | 5.860 | 85.9% |

读法：从不告警的 shieldstral 调用最多（10.1/轨迹），Jev 8.74；跨模型比每 episode 成本会奖励好模型。

## 4. 操作点也是成本（同一模型不同阈值）

| 模型 | 位置 | 默认阈值 MCC | MCC 最优阈值 | 最优阈值下 MCC | TPR@FPR=5% | AUC |
|---|---|---|---:|---|---:|---:|
| d3mini | tsbench | 0.470 | 0.143 | 0.557 | 47.1% | 0.878 |
| d3mini | agentharm | 0.763 | 0.889 | 0.809 | 80.8% | 0.972 |
| jev-packy-1.14.0 | tsbench | 0.565 | 0.300 | 0.619 | 59.6% | 0.906 |
| jev-packy-1.14.0 | agentharm | 0.769 | 0.640 | 0.785 | 72.6% | 0.958 |
| jev-packy-1.14.0 | wildguard_response | 0.746 | 0.590 | 0.768 | 82.4% | 0.946 |
| jevguard | tsbench | 0.252 | 0.302 | 0.268 | 3.7% | 0.668 |
| jevguard | agentharm | 0.580 | 0.954 | 0.630 | 25.5% | 0.875 |
| kev | tsbench | 0.315 | 0.270 | 0.495 | 29.0% | 0.831 |
| kev | agentharm | 0.688 | 0.661 | 0.744 | 77.4% | 0.931 |
| laya | tsbench | 0.052 | 0.448 | 0.064 | 4.3% | 0.460 |
| laya | agentharm | 0.449 | 0.344 | 0.517 | 20.2% | 0.797 |
| secjev | tsbench | 0.127 | 0.010 | 0.298 | 8.0% | 0.660 |
| secjev | agentharm | 0.658 | 0.700 | 0.684 | 71.2% | 0.892 |
| jev-packy-1.14.0（逐前缀） | stepshield_test | TPR 91.4% / TNR 86.5% | 0.770 | 0.710 | — | — |
| jev-packy-1.14.0（逐前缀） | stepshield_test_holdout | TPR 97.2% / TNR 87.0% | 0.630 | 0.880 | — | — |

StepShield 上 Jev 0.50→0.77：MCC 0.535→0.710——同一模型、同一数据，只换操作点。

## 5. 写论文前必须补的数据

1. 价格快照：Jev 列表价 0.042 USD/M 输入；GPT/Claude 的 relay 价目表未记录；本地计算未计价。
2. 主 Agent 与 reviewer 的成本/延迟需分列；当前只有判官组件。
3. 等调用数对照（Jev vs LLM judge）与等成本对照。
4. 真实账单 vs 估算：当前全部是估算。
5. 延迟来源（网络/队列/推理）未拆分。

