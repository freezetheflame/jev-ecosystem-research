# 服务器本地 StepShield 汇总（9 个本地模型）

> 自动生成于 2026-11-11 19:01 Asia/Shanghai。数据来自服务器战役 `full-local-stepshield-server-v1` 各模型官方 `analysis/*/summary.json`（Mode C，prefix monitoring）。test 与 test_holdout 分开报告，不合并打一个总分。全部 9×8151 均成功，失败 0。本地算力未计价；token usage 大多未上报。

## 准确率与 F1

| 模型          | test acc / F1 | test_holdout acc / F1 |
| ----------- | ------------- | --------------------- |
| d3mini      | 95.0% / 72.3% | 92.1% / 92.1%         |
| gliguard    | 80.8% / 20.8% | 75.0% / 76.5%         |
| jevguard    | 48.0% / 21.0% | 77.8% / 81.4%         |
| kev         | 94.1% / 61.2% | 83.3% / 81.8%         |
| laya        | 83.0% / 9.1%  | 50.0% / 3.6%          |
| qwen35      | 94.8% / 59.1% | 88.9% / 88.2%         |
| qwen3guard  | 92.3% / 13.5% | 71.8% / 62.1%         |
| secjev      | 89.5% / 32.7% | 56.9% / 42.2%         |
| shieldstral | 91.9% / 0.0%  | 64.8% / 45.7%         |

## 数据规模

| 划分           | 总量   | 可判分  | 正类（rogue） | 负类   | 失败  |
| ------------ | ----:| ----:| ---------:| ----:| ---:|
| test         | 7935 | 7935 | 639       | 7296 | 0   |
| test_holdout | 216  | 216  | 108       | 108  | 0   |

战役合计每模型 8151 条（test 7935 + test_holdout 216），9 个模型全部 `ok`。

口径：gold 来自原生轨迹答案；预测是观察到的前缀上第一次 unsafe 告警。官方 temporal 指标（仅在检出的 rogue 上计算）见 `server_local_stepshield_metrics_full.md`；时间见 `server_local_stepshield_time_tokens.md`。shieldstral 在 test 上 TP=FP=0，precision 与 EIR 官方记为缺省。
