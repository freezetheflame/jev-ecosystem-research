# 非 StepShield 数据汇总（TS-Bench / AgentHarm / InjecAgent / WildGuard）

> 自动生成；数据来源 rq1 下各 campaign 的 episodes.jsonl。StepShield 未纳入。时间与 token 见同目录 `non_stepshield_time_tokens.md` / `non_stepshield_time_tokens.csv`（2026-11-11 补）。

| 模型          | TS-Bench acc / F1 | AgentHarm acc / F1 | InjecAgent acc / F1 | WildGuard acc / F1 |
| ----------- | ----------------- | ------------------ | ------------------- | ------------------ |
| claudehaiku | 81.7% / 75.1%     | 83.2% / 84.4%      | 95.6% / 97.7%       | 84.3% / 79.7%      |
| d3mini      | 79.2% / 53.3%     | 87.0% / 88.4%      | 94.1% / 97.0%       | 90.1% / 88.3%      |
| gliguard    | 66.3% / 47.9%     | 77.9% / 80.9%      | 75.5% / 86.0%       | 87.6% / 86.0%      |
| gpt6luna    | 86.3% / 79.4%     | 84.1% / 84.7%      | 99.6% / 99.8%       | 87.2% / 84.3%      |
| jevguard    | 63.0% / 51.6%     | 76.2% / 80.4%      | 74.4% / 85.3%       | 78.3% / 78.9%      |
| kev         | 74.5% / 36.5%     | 84.1% / 85.1%      | 91.3% / 95.5%       | 87.5% / 86.0%      |
| laya        | 69.9% / 2.9%      | 72.1% / 69.5%      | 20.4% / 34.0%       | 63.9% / 43.0%      |
| qwen35      | 76.8% / 56.2%     | 80.8% / 81.5%      | 88.1% / 93.7%       | 79.9% / 71.5%      |
| qwen3guard  | 75.1% / 51.2%     | 66.3% / 74.5%      | 57.6% / 73.1%       | 90.2% / 88.7%      |
| secjev      | 69.6% / 24.8%     | 82.2% / 80.2%      | 71.5% / 83.4%       | 74.0% / 67.9%      |
| shieldstral | 74.3% / 35.2%     | 85.1% / 85.9%      | 48.3% / 65.2%       | 90.0% / 88.1%      |

## 数据规模与失败

| 数据集        | 总量   | 可判分  | 正类   | 失败（未计入分母）                                                             |
| ---------- | ---- | ---- | ---- | --------------------------------------------------------------------- |
| tsbench    | 7182 | 5401 | 1631 | 见各模型（TS-Bench secjev 124、claudehaiku 33；WildGuard laya 11、gpt6luna 5） |
| agentharm  | 416  | 416  | 208  | 见各模型（TS-Bench secjev 124、claudehaiku 33；WildGuard laya 11、gpt6luna 5） |
| injecagent | 2108 | 2108 | 2108 | 见各模型（TS-Bench secjev 124、claudehaiku 33；WildGuard laya 11、gpt6luna 5） |
| wildguard  | 1725 | 1699 | 754  | 见各模型（TS-Bench secjev 124、claudehaiku 33；WildGuard laya 11、gpt6luna 5） |
