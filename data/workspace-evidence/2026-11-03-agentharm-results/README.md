# AgentHarm：已执行 10 个模型的实验汇总

同一批 50 条 validation 输入（25 harmful / 25 benign、8 个 family），每模型计划 3 次重复。只汇总已有逐条预测，不复核原始模型输出、不重跑旧实验。
多数票基于已有有效输出；平票和没有输出的项保持未决。N/50 与有效调用均单列。

| 模型 | 可判项/50 | 有效调用/150 | TP | FP | TN | FN | Accuracy | F1 | p50秒 | p95秒 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| jev | 50/50 | 150/150 | 21 | 0 | 25 | 4 | 0.920 | 0.913 | 7.250 | 7.704 |
| d3mini | 50/50 | 150/150 | 24 | 0 | 25 | 1 | 0.980 | 0.980 | 0.109 | 0.141 |
| laya | 50/50 | 150/150 | 7 | 2 | 23 | 18 | 0.600 | 0.412 | 0.078 | 0.094 |
| secjev | 50/50 | 150/150 | 18 | 0 | 25 | 7 | 0.860 | 0.837 | 0.109 | 0.203 |
| gliguard | 50/50 | 150/150 | 25 | 1 | 24 | 0 | 0.980 | 0.980 | 0.078 | 0.094 |
| shieldstral | 50/50 | 150/150 | 24 | 2 | 23 | 1 | 0.940 | 0.941 | 0.078 | 0.110 |
| qwen3guard | 50/50 | 150/150 | 25 | 8 | 17 | 0 | 0.840 | 0.862 | 0.391 | 0.531 |
| qwen35 | 50/50 | 150/150 | 19 | 0 | 25 | 6 | 0.880 | 0.864 | 0.532 | 0.781 |
| gpt6luna | 47/50 | 139/150 | 21 | 1 | 24 | 1 | 0.957 | 0.955 | 3.484 | 14.063 |
| claudehaiku | 50/50 | 149/150 | 22 | 3 | 22 | 3 | 0.880 | 0.880 | 6.093 | 8.875 |

所有模型都有可判结果的共同子集：47 项；所有模型均有三次有效输出的共同子集：45 项。各模型在这两个共同子集上的分数、IDs 和投票覆盖见 results.json。
共同子集按可用性筛选，不能替代全 50 项表现。GPT 的 provider refusal 不转换为 safe/unsafe；Claude 的非 JSON 输出同样保留为失败。
费用、unknown API calls、token 和完整硬件/接口/参数见 comparison.csv 与 results.json。表中时间包含失败/拒绝，按统一经验分位数口径汇总；不同显卡/API 通道不构成公平速度排名。
Jev-Guard 尚未执行；用户已停止权重下载，没有成绩，不纳入比较。
Public exposed validation pilot, not confirmatory; 50 items from 8 base families.
Wilson fields are descriptive and not family-cluster corrected; no significance/ranking claim.
Common subsets condition on provider response availability; report all-50 bounds and coverage.
Devices, provider routes and native input packaging differ; latency is not a controlled model-only comparison.
Local compute unpriced. Unknown API fees are not zero. Prices use original monitor snapshots.
Qwen3Guard uses the original-text primary run with Controversial=unsafe; JSON-wrapped run remains historical.
