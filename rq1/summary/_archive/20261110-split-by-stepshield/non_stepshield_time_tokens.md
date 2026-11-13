# 非 StepShield 时间与 token 汇总（TS-Bench / AgentHarm / InjecAgent / WildGuard）

> 自动生成于 2026-11-11 11:53 Asia/Shanghai。口径与 `non_stepshield_summary.md` 相同：仅纳入已完成的正式跑测（11 个模型 × 4 个数据集）。StepShield、早期失败的 Jev API 试跑、冒烟测试均未纳入。时间取成功 episode 的客户端墙钟 `wall_seconds`（不是 TTFT）；token 优先取官方 `summary.json` 的 known usage，缺失或官方 analysis 不完整时回退已完成的 `telemetry/*.run.json`（不含未完成的 running 快照）。本地模型的 `output_tokens` 常为 0（推理未上报 usage）；个别模型（如 gliguard）输入 token 也未上报。本地算力未计价。

## 口径说明

- **episode 均时 / 中位 / P95**：成功样本的端到端墙钟（秒）。失败样本不计入时间分母。
- **episode 总时**：成功样本 `wall_seconds` 之和；顺序执行时近似等于推理墙钟。
- **调用均时 / 中位 / P95 / 总时**：safety module 单次调用的 `duration_seconds`。
- **输入 / 输出 token**：已知 usage 合计；`missing_usage_calls` 为未上报 token 的调用数。
- **TS-Bench** 的时间与 token 包含全部成功样本（含 gold=0.5 的争议项）。准确率表里未计入分母的失败样本（claudehaiku 33、secjev 124）同样不计入时间分母。
- 若某本地 TS-Bench 模型有 `full-local-tsbench-repair-v1` 补跑，样本按与准确率表相同的最终结果合并；token 计入实际消耗（含补跑）。

## 总览（成功样本均时 / 已知输入 token）

| 模型          | TS-Bench 均时 / 输入 token | AgentHarm 均时 / 输入 token | InjecAgent 均时 / 输入 token | WildGuard 均时 / 输入 token |
| ----------- | ---------------------- | ----------------------- | ------------------------ | ----------------------- |
| claudehaiku | 3.961 s / 10,015,184   | 2.558 s / 120,155       | 3.170 s / 862,147        | 2.893 s / 1,343,725     |
| d3mini      | 0.460 s / 6,803,870    | 0.100 s / 88,529        | 0.102 s / 660,260        | 0.087 s / 422,512       |
| gliguard    | 0.120 s / 未上报          | 0.055 s / 未上报           | 0.064 s / 未上报            | 0.061 s / 未上报           |
| gpt6luna    | 2.635 s / 6,924,505    | 3.293 s / 90,646        | 3.259 s / 660,592        | 3.062 s / 429,547       |
| jevguard    | 0.323 s / 6,179,036    | 0.078 s / 52,337        | 0.087 s / 476,864        | 0.078 s / 272,437       |
| kev         | 0.483 s / 6,293,948    | 0.112 s / 58,999        | 0.129 s / 510,592        | 0.105 s / 300,039       |
| laya        | 0.172 s / 15,096,467   | 0.059 s / 61,703        | 0.052 s / 530,885        | 0.052 s / 310,892       |
| qwen35      | 0.796 s / 6,394,496    | 0.405 s / 64,817        | 0.451 s / 540,104        | 0.365 s / 324,187       |
| qwen3guard  | 0.350 s / 7,532,120    | 0.380 s / 147,843       | 0.361 s / 889,610        | 0.319 s / 668,558       |
| secjev      | 0.309 s / 4,903,347    | 0.088 s / 58,999        | 0.097 s / 510,592        | 0.084 s / 300,039       |
| shieldstral | 0.181 s / 6,630,159    | 0.070 s / 69,931        | 0.078 s / 579,205        | 0.069 s / 346,294       |

## 时间（秒）

### TS-Bench

| 模型          | 成功 / 失败    | 均时    | 中位    | P95    | episode 总时 | 调用均时  | 调用中位  | 调用 P95 | 调用总时     |
| ----------- | ---------- | ----- | ----- | ------ | ---------- | ----- | ----- | ------ | -------- |
| claudehaiku | 7149 / 33  | 3.961 | 2.453 | 10.222 | 28316.79   | 3.254 | 2.421 | 6.266  | 26269.27 |
| d3mini      | 7182 / 0   | 0.460 | 0.330 | 0.833  | 3301.73    | 0.423 | 0.293 | 0.784  | 3037.86  |
| gliguard    | 7182 / 0   | 0.120 | 0.072 | 0.433  | 861.67     | 0.088 | 0.042 | 0.398  | 673.14   |
| gpt6luna    | 7182 / 0   | 2.635 | 2.250 | 5.000  | 18924.55   | 2.591 | 2.219 | 4.953  | 18644.59 |
| jevguard    | 7182 / 0   | 0.323 | 0.262 | 0.515  | 2320.27    | 0.286 | 0.227 | 0.458  | 2052.84  |
| kev         | 7182 / 0   | 0.483 | 0.355 | 0.884  | 3468.76    | 0.446 | 0.319 | 0.849  | 3211.54  |
| laya        | 7182 / 0   | 0.172 | 0.092 | 0.418  | 1236.86    | 0.111 | 0.053 | 0.286  | 1177.20  |
| qwen35      | 7182 / 0   | 0.796 | 0.677 | 1.154  | 5715.40    | 0.759 | 0.644 | 1.114  | 5451.88  |
| qwen3guard  | 7182 / 0   | 0.350 | 0.308 | 0.492  | 2514.55    | 0.312 | 0.273 | 0.454  | 2240.81  |
| secjev      | 7058 / 124 | 0.309 | 0.269 | 0.536  | 2181.46    | 0.270 | 0.234 | 0.484  | 1911.53  |
| shieldstral | 7182 / 0   | 0.181 | 0.123 | 0.388  | 1299.43    | 0.144 | 0.088 | 0.292  | 1035.59  |

### AgentHarm

| 模型          | 成功 / 失败 | 均时    | 中位    | P95   | episode 总时 | 调用均时  | 调用中位  | 调用 P95 | 调用总时    |
| ----------- | ------- | ----- | ----- | ----- | ---------- | ----- | ----- | ------ | ------- |
| claudehaiku | 416 / 0 | 2.558 | 2.000 | 3.363 | 1064.21    | 2.519 | 1.961 | 3.332  | 1047.74 |
| d3mini      | 416 / 0 | 0.100 | 0.094 | 0.140 | 41.801     | 0.089 | 0.078 | 0.125  | 36.817  |
| gliguard    | 416 / 0 | 0.055 | 0.047 | 0.063 | 22.933     | 0.047 | 0.047 | 0.062  | 19.499  |
| gpt6luna    | 416 / 0 | 3.293 | 2.711 | 6.864 | 1369.80    | 3.177 | 2.657 | 6.770  | 1346.80 |
| jevguard    | 416 / 0 | 0.078 | 0.078 | 0.094 | 32.310     | 0.068 | 0.063 | 0.079  | 28.437  |
| kev         | 416 / 0 | 0.112 | 0.109 | 0.141 | 46.487     | 0.104 | 0.094 | 0.140  | 43.333  |
| laya        | 416 / 0 | 0.059 | 0.062 | 0.078 | 24.501     | 0.046 | 0.047 | 0.063  | 18.955  |
| qwen35      | 416 / 0 | 0.405 | 0.390 | 0.531 | 168.53     | 0.377 | 0.359 | 0.484  | 156.68  |
| qwen3guard  | 416 / 0 | 0.380 | 0.375 | 0.484 | 157.91     | 0.347 | 0.344 | 0.438  | 144.41  |
| secjev      | 416 / 0 | 0.088 | 0.078 | 0.110 | 36.553     | 0.080 | 0.078 | 0.109  | 33.129  |
| shieldstral | 416 / 0 | 0.070 | 0.063 | 0.079 | 29.295     | 0.059 | 0.062 | 0.078  | 24.707  |

### InjecAgent

| 模型          | 成功 / 失败  | 均时    | 中位    | P95   | episode 总时 | 调用均时  | 调用中位  | 调用 P95 | 调用总时    |
| ----------- | -------- | ----- | ----- | ----- | ---------- | ----- | ----- | ------ | ------- |
| claudehaiku | 2108 / 0 | 3.170 | 1.828 | 6.531 | 6683.01    | 3.088 | 1.796 | 6.334  | 6562.21 |
| d3mini      | 2108 / 0 | 0.102 | 0.094 | 0.141 | 215.20     | 0.095 | 0.094 | 0.125  | 199.89  |
| gliguard    | 2108 / 0 | 0.064 | 0.063 | 0.078 | 134.51     | 0.054 | 0.047 | 0.063  | 113.90  |
| gpt6luna    | 2108 / 0 | 3.259 | 2.687 | 5.614 | 6869.01    | 3.220 | 2.656 | 5.593  | 6788.21 |
| jevguard    | 2108 / 0 | 0.087 | 0.078 | 0.125 | 183.75     | 0.077 | 0.078 | 0.110  | 161.36  |
| kev         | 2108 / 0 | 0.129 | 0.125 | 0.187 | 272.13     | 0.118 | 0.109 | 0.172  | 249.52  |
| laya        | 2108 / 0 | 0.052 | 0.047 | 0.078 | 109.92     | 0.044 | 0.047 | 0.063  | 93.467  |
| qwen35      | 2108 / 0 | 0.451 | 0.438 | 0.563 | 951.36     | 0.423 | 0.407 | 0.531  | 890.84  |
| qwen3guard  | 2108 / 0 | 0.361 | 0.359 | 0.469 | 760.75     | 0.332 | 0.328 | 0.438  | 700.15  |
| secjev      | 2108 / 0 | 0.097 | 0.094 | 0.141 | 203.98     | 0.090 | 0.079 | 0.140  | 189.34  |
| shieldstral | 2108 / 0 | 0.078 | 0.078 | 0.094 | 163.97     | 0.070 | 0.063 | 0.093  | 147.01  |

### WildGuard

| 模型          | 成功 / 失败   | 均时    | 中位    | P95   | episode 总时 | 调用均时  | 调用中位  | 调用 P95 | 调用总时    |
| ----------- | --------- | ----- | ----- | ----- | ---------- | ----- | ----- | ------ | ------- |
| claudehaiku | 1725 / 0  | 2.893 | 1.672 | 6.904 | 4989.91    | 2.844 | 1.641 | 6.847  | 4916.96 |
| d3mini      | 1725 / 0  | 0.087 | 0.079 | 0.110 | 150.23     | 0.080 | 0.078 | 0.109  | 138.05  |
| gliguard    | 1725 / 0  | 0.061 | 0.062 | 0.093 | 105.01     | 0.054 | 0.047 | 0.078  | 92.550  |
| gpt6luna    | 1720 / 5  | 3.062 | 2.360 | 5.876 | 5266.44    | 2.929 | 2.328 | 5.812  | 5233.88 |
| jevguard    | 1725 / 0  | 0.078 | 0.078 | 0.106 | 135.17     | 0.066 | 0.063 | 0.093  | 113.32  |
| kev         | 1725 / 0  | 0.105 | 0.094 | 0.140 | 181.04     | 0.098 | 0.094 | 0.125  | 169.74  |
| laya        | 1714 / 11 | 0.052 | 0.047 | 0.078 | 88.928     | 0.045 | 0.047 | 0.063  | 77.987  |
| qwen35      | 1725 / 0  | 0.365 | 0.359 | 0.453 | 630.47     | 0.337 | 0.328 | 0.406  | 581.33  |
| qwen3guard  | 1725 / 0  | 0.319 | 0.297 | 0.437 | 550.00     | 0.290 | 0.266 | 0.391  | 499.55  |
| secjev      | 1725 / 0  | 0.084 | 0.078 | 0.110 | 145.05     | 0.077 | 0.078 | 0.109  | 132.86  |
| shieldstral | 1725 / 0  | 0.069 | 0.063 | 0.094 | 119.88     | 0.063 | 0.062 | 0.079  | 107.82  |

## Token

### TS-Bench

| 模型          | 输入 token   | 输出 token | 缺失 usage 调用 | 调用次数   | 每成功样本输入 token |
| ----------- | ---------- | -------- | ----------- | ------ | ------------- |
| claudehaiku | 10,015,184 | 420,367  | 0           | 8,075  | 1400.92       |
| d3mini      | 6,803,870  | 0        | 0           | 7,182  | 947.35        |
| gliguard    | 未上报        | 未上报      | 7,305       | 7,305  | —             |
| gpt6luna    | 6,924,505  | 883,924  | 6           | 7,188  | 964.15        |
| jevguard    | 6,179,036  | 0        | 272         | 7,454  | 860.35        |
| kev         | 6,293,948  | 0        | 124         | 7,306  | 876.35        |
| laya        | 15,096,467 | 0        | 0           | 10,609 | 2101.99       |
| qwen35      | 6,394,496  | 57,456   | 0           | 7,182  | 890.35        |
| qwen3guard  | 7,532,120  | 62,654   | 7           | 7,189  | 1048.75       |
| secjev      | 4,903,347  | 0        | 124         | 7,182  | 694.72        |
| shieldstral | 6,630,159  | 7,182    | 0           | 7,182  | 923.16        |

### AgentHarm

| 模型          | 输入 token | 输出 token | 缺失 usage 调用 | 调用次数 | 每成功样本输入 token |
| ----------- | -------- | -------- | ----------- | ---- | ------------- |
| claudehaiku | 120,155  | 8,391    | 0           | 416  | 288.83        |
| d3mini      | 88,529   | 0        | 0           | 416  | 212.81        |
| gliguard    | 未上报      | 未上报      | 416         | 416  | —             |
| gpt6luna    | 90,646   | 38,887   | 3           | 419  | 217.90        |
| jevguard    | 52,337   | 0        | 0           | 416  | 125.81        |
| kev         | 58,999   | 0        | 0           | 416  | 141.82        |
| laya        | 61,703   | 0        | 0           | 416  | 148.32        |
| qwen35      | 64,817   | 3,328    | 0           | 416  | 155.81        |
| qwen3guard  | 147,843  | 4,470    | 0           | 416  | 355.39        |
| secjev      | 58,999   | 0        | 0           | 416  | 141.82        |
| shieldstral | 69,931   | 416      | 0           | 416  | 168.10        |

### InjecAgent

| 模型          | 输入 token | 输出 token | 缺失 usage 调用 | 调用次数  | 每成功样本输入 token |
| ----------- | -------- | -------- | ----------- | ----- | ------------- |
| claudehaiku | 862,147  | 53,934   | 0           | 2,125 | 408.99        |
| d3mini      | 660,260  | 0        | 0           | 2,108 | 313.22        |
| gliguard    | 未上报      | 未上报      | 2,108       | 2,108 | —             |
| gpt6luna    | 660,592  | 134,368  | 0           | 2,108 | 313.37        |
| jevguard    | 476,864  | 0        | 0           | 2,108 | 226.22        |
| kev         | 510,592  | 0        | 0           | 2,108 | 242.22        |
| laya        | 530,885  | 0        | 0           | 2,108 | 251.84        |
| qwen35      | 540,104  | 16,864   | 0           | 2,108 | 256.22        |
| qwen3guard  | 889,610  | 20,314   | 0           | 2,108 | 422.02        |
| secjev      | 510,592  | 0        | 0           | 2,108 | 242.22        |
| shieldstral | 579,205  | 2,108    | 0           | 2,108 | 274.77        |

### WildGuard

| 模型          | 输入 token  | 输出 token | 缺失 usage 调用 | 调用次数  | 每成功样本输入 token |
| ----------- | --------- | -------- | ----------- | ----- | ------------- |
| claudehaiku | 1,343,725 | 33,620   | 0           | 1,729 | 778.97        |
| d3mini      | 422,512   | 0        | 0           | 1,725 | 244.93        |
| gliguard    | 未上报       | 未上报      | 1,725       | 1,725 | —             |
| gpt6luna    | 429,547   | 117,544  | 38          | 1,758 | 249.74        |
| jevguard    | 272,437   | 0        | 0           | 1,725 | 157.93        |
| kev         | 300,039   | 0        | 0           | 1,725 | 173.94        |
| laya        | 310,892   | 0        | 0           | 1,725 | 181.38        |
| qwen35      | 324,187   | 13,800   | 0           | 1,725 | 187.93        |
| qwen3guard  | 668,558   | 15,812   | 0           | 1,725 | 387.57        |
| secjev      | 300,039   | 0        | 0           | 1,725 | 173.94        |
| shieldstral | 346,294   | 1,725    | 0           | 1,725 | 200.75        |

## 数据来源

| 模型          | 数据集        | campaign                                                    | 备注                                                                                                                             |
| ----------- | ---------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| claudehaiku | tsbench    | `full-api-tsbench-v1`                                       |                                                                                                                                |
| claudehaiku | agentharm  | `full-api-agentharm-claude-v5`                              |                                                                                                                                |
| claudehaiku | injecagent | `full-api-wg-injec-tsbench-v1`                              |                                                                                                                                |
| claudehaiku | wildguard  | `full-api-wg-injec-tsbench-v1`                              |                                                                                                                                |
| d3mini      | tsbench    | `full-local-tsbench-server-v1`                              |                                                                                                                                |
| d3mini      | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| d3mini      | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| d3mini      | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |
| gliguard    | tsbench    | `full-local-tsbench-server-v1+full-local-tsbench-repair-v1` | merged full-local-tsbench-repair-v1 (replaced=123, added=0)                                                                    |
| gliguard    | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| gliguard    | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| gliguard    | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |
| gpt6luna    | tsbench    | `full-api-tsbench-v1`                                       |                                                                                                                                |
| gpt6luna    | agentharm  | `full-api-agentharm-gpt-v5`                                 |                                                                                                                                |
| gpt6luna    | injecagent | `full-api-wg-injec-tsbench-v1`                              |                                                                                                                                |
| gpt6luna    | wildguard  | `full-api-wg-injec-tsbench-v1`                              |                                                                                                                                |
| jevguard    | tsbench    | `full-local-tsbench-server-v1+full-local-tsbench-repair-v1` | merged full-local-tsbench-repair-v1 (replaced=272, added=0)                                                                    |
| jevguard    | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| jevguard    | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| jevguard    | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |
| kev         | tsbench    | `full-local-tsbench-server-v1+full-local-tsbench-repair-v1` | merged full-local-tsbench-repair-v1 (replaced=124, added=0)                                                                    |
| kev         | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| kev         | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| kev         | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |
| laya        | tsbench    | `full-local-tsbench-server-v1+full-local-tsbench-repair-v1` | merged full-local-tsbench-repair-v1 (replaced=3427, added=0)                                                                   |
| laya        | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| laya        | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| laya        | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |
| qwen35      | tsbench    | `full-local-tsbench-server-v1`                              |                                                                                                                                |
| qwen35      | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| qwen35      | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| qwen35      | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |
| qwen3guard  | tsbench    | `full-local-tsbench-server-v1+full-local-tsbench-repair-v1` | merged full-local-tsbench-repair-v1 (replaced=7, added=0); official analysis incomplete; tokens/calls from completed telemetry |
| qwen3guard  | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| qwen3guard  | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| qwen3guard  | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |
| secjev      | tsbench    | `full-local-tsbench-server-v1`                              | accuracy table n_total=7058 is ok-only; this table uses episodes n=7182 including 124 failed                                   |
| secjev      | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| secjev      | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| secjev      | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |
| shieldstral | tsbench    | `full-local-tsbench-server-v1`                              |                                                                                                                                |
| shieldstral | agentharm  | `full-local-agentharm-v1`                                   |                                                                                                                                |
| shieldstral | injecagent | `full-local-injecagent-v1`                                  |                                                                                                                                |
| shieldstral | wildguard  | `full-local-wildguard-tsbench-v1`                           |                                                                                                                                |

完整数值见同目录 `non_stepshield_time_tokens.csv`。
