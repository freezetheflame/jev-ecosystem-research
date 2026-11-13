# RQ1 官方格子补齐核对

生成于 2026-11-13 13:27:07 Asia/Shanghai。脚本：`rebuild_mcc_summary.py`。
计数来源：在上一版 live `metrics_full.csv` 上填入 gpt6luna StepShield 与 claudehaiku WildGuard response 的官方 TP/FP/TN/FN（以及 EIR / 干预差），再按同一公式重算 MCC / TPR / TNR。不读 `raw/`，不重跑，不改 analysis 目录，不经 SSH。服务器进程状态以 2026-11-13 12:55:45 Asia/Shanghai 的检查为准；官方 analysis 文件随后立刻取回。

## 编辑的文件

- `/workspace/rq1_summary_work/out_20261113_fill_cells/metrics.md`
- `/workspace/rq1_summary_work/out_20261113_fill_cells/metrics.csv`
- `/workspace/rq1_summary_work/out_20261113_fill_cells/metrics_full.md`
- `/workspace/rq1_summary_work/out_20261113_fill_cells/metrics_full.csv`
- `/workspace/rq1_summary_work/out_20261113_fill_cells/README.md`
- `/workspace/rq1_summary_work/out_20261113_fill_cells/rq1_README.md`
- `time_tokens.md` / `time_tokens.csv` 由随后步骤在同一输出目录单独补写（只填上述新格子；其余行数字保持不变）。

## StepShield MCC（由混淆矩阵重算，三位小数）

| 模型 | test MCC | test TP/FP/TN/FN | holdout MCC | holdout TP/FP/TN/FN |
| --- | ---: | --- | ---: | --- |
| claudehaiku |  |  |  |  |
| d3mini | 0.700 | 513/267/7029/126 | 0.843 | 99/8/100/9 |
| gliguard | 0.122 | 200/1083/6213/439 | 0.504 | 88/34/74/20 |
| gpt6luna | 0.581 | 627/949/6347/12 | 0.636 | 107/44/64/1 |
| Jev (Packy 1.14.0) | 0.535 | 583/966/6328/56 | 0.847 | 105/14/94/3 |
| jevguard | 0.169 | 549/4035/3261/90 | 0.603 | 105/45/63/3 |
| kev | 0.581 | 371/203/7093/268 | 0.676 | 81/9/99/27 |
| laya | -0.001 | 67/774/6522/572 | 0.000 | 2/2/106/106 |
| qwen35 | 0.592 | 296/66/7230/343 | 0.783 | 90/6/102/18 |
| qwen3guard | 0.210 | 48/22/7274/591 | 0.506 | 50/3/105/58 |
| secjev | 0.271 | 203/398/6898/436 | 0.161 | 34/19/89/74 |
| shieldstral | — | 0/0/7296/639 | 0.417 | 32/0/108/76 |

无定义（—）：

- 所有 InjecAgent 行的 MCC（全正类，TN=FP=0）
- shieldstral 的 StepShield test（TP=FP=0，与 always-safe 同类）
- 各位置 always-safe（TP+FP=0）与 always-unsafe（TN+FN=0）基线的 MCC
- 仍为空单元格（不是 —）的是 claudehaiku 的 StepShield test / test_holdout，以及 gpt6luna 的 WildGuard response（Mode E）
- laya 的 StepShield holdout MCC 为 0.000（有定义：分子为 0，分母不为 0），不要写成 —
- laya 的 StepShield test MCC 为 −0.001

Packy Jev StepShield 的 MCC 与 CSV 中已有官方值一致：test 0.5354442402079949 → 0.535，holdout 0.8469973362226254 → 0.847。

## 与旧全指标表的差异

发现显示不一致（需人工检查）：
- claudehaiku agentharm tpr: old=91.4% new=91.3%
- claudehaiku agentharm fnr: old=8.6% new=8.7%
- d3mini tsbench fpr: old=3.5% new=3.4%
- gpt6luna tsbench tpr: old=87.3% new=87.2%
- jevguard tsbench f1: old=51.7% new=51.6%
- laya injecagent tpr: old=20.5% new=20.4%
- laya injecagent accuracy: old=20.5% new=20.4%
- qwen35 tsbench fpr: old=11.3% new=11.2%
- qwen3guard tsbench fpr: old=11.3% new=11.2%
- qwen3guard agentharm accuracy: old=66.4% new=66.3%
- secjev tsbench f1: old=24.9% new=24.8%

本次有意补上的空白（不算错误）：

- StepShield 原先在 `metrics_full.csv` 中 MCC 为空、且公式可计算的行：已填 17 个（本地 9 个模型的 test / holdout，除 shieldstral test 无定义外）。Packy 两行原先已有 MCC，未改显示。
- 主表 `metrics.md` 不再以 acc/F1 为标题指标；acc/F1 仍在 `metrics_full.md`。
- 删除了旧 `metrics.md` 失败表里一行残缺的 `gpt6luna | 5 | 可判分 1694…`（那是已移除的 WildGuard prompt / Mode A1 残留，本次没有把 Mode A1 加回）。
- 各全指标表末尾增加 always-safe / always-unsafe 行；`metrics_full.csv` / `metrics.csv` 也写入了这两条基线。

## 新写入的官方格子

| 模型 × 数据集 | 单元格 | Acc | F1 | n / fail | 官方 acc / F1 是否与重算显示一致 |
| --- | ---: | ---: | ---: | --- | --- |
| gpt6luna × stepshield_test | 0.581 (98.1%/87.0%) | 87.9% | 56.6% | 7935 / 0 | acc=是; F1=是 |
| gpt6luna × stepshield_test_holdout | 0.636 (99.1%/59.3%) | 79.2% | 82.6% | 216 / 0 | acc=是; F1=是 |
| claudehaiku × wildguard_response | 0.691 (67.3%/96.8%) | 91.8% | 73.5% | 1654 / 55 | acc=是; F1=是 |

官方 test acc/F1 与由混淆矩阵重算的值完全一致。holdout 的官方 F1=0.8262548262548263 与重算值相差 1 ulp（约 1e-16），一位小数显示同为 82.6%。

## 仍为空的格子

已确认以下格子保持为空（不是 —，也没有填入进行中或尚未正式合并的数字）：

- claudehaiku × StepShield test 与 test_holdout（服务器剩余子集 1127：ok=1124，fail=3 JSONDecodeError；hecPC + 服务器去重后成功 8148/8151，尚未正式合并）
- gpt6luna × WildGuard response (Mode E)（截至 2026-11-13 12:55:45 Asia/Shanghai 仍在跑：886/1725，ok=885，fail=1 provider_policy_refusal，PID 2769100；此后未再做进程检查）

未把上述未合并或进行中的数字写入正式格。未触碰 Mode E PID 2769100 或 vLLM 773641。

## Spearman（描述性，仅两边 MCC 都有定义的子集）

| 位置对 | Spearman | n | 子集 |
| --- | ---: | ---: | --- |
| AgentHarm ~ TS-Bench | 0.52 | 12 | claudehaiku, d3mini, gliguard, gpt6luna, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev, shieldstral |
| AgentHarm ~ WildGuard-E | 0.75 | 11 | claudehaiku, d3mini, gliguard, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev, shieldstral |
| AgentHarm ~ StepShield test | 0.71 | 10 | d3mini, gliguard, gpt6luna, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev |
| AgentHarm ~ StepShield holdout | 0.57 | 11 | d3mini, gliguard, gpt6luna, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev, shieldstral |
| TS-Bench ~ WildGuard-E | 0.94 | 11 | claudehaiku, d3mini, gliguard, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev, shieldstral |
| TS-Bench ~ StepShield test | 0.70 | 10 | d3mini, gliguard, gpt6luna, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev |
| TS-Bench ~ StepShield holdout | 0.84 | 11 | d3mini, gliguard, gpt6luna, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev, shieldstral |
| WildGuard-E ~ StepShield test | 0.78 | 9 | d3mini, gliguard, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev |
| WildGuard-E ~ StepShield holdout | 0.89 | 10 | d3mini, gliguard, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev, shieldstral |
| StepShield test ~ StepShield holdout | 0.79 | 10 | d3mini, gliguard, gpt6luna, Jev (Packy 1.14.0), jevguard, kev, laya, qwen35, qwen3guard, secjev |

上表为本次从当前可定义 MCC 子集重新计算的结果，不沿用上一版或批评稿里的旧系数。AgentHarm~TS-Bench 仍为全部 12 个模型。AgentHarm~WildGuard 与 TS-Bench~WildGuard 现含 claudehaiku、仍不含 gpt6luna。TS-Bench~StepShield test 与 StepShield test~holdout 现含 gpt6luna，仍排除尚未正式合并的 claudehaiku，以及 test 上 MCC 无定义的 shieldstral。n 与系数因可比子集变化而变化，只是描述性观察，不单独构成排名结论，也不宜写成「排名随位置翻转已被证明」。

主表没有加 (1)(2)(3) 名次。正式汇总中没有纳入 WildGuard prompt（Mode A1）。

## 时间与 token

已在同一输出目录写入 `time_tokens.md` / `time_tokens.csv`，只填入下列新格子，其余行与 live 表数字完全一致。

- **gpt6luna StepShield test**：成功 7935/0；episode 均时 / 中位 / P95 / 总时 = 26.178 / 20.911 / 60.600 / 207721.50 s（官方成功样本墙钟）；调用 68,354 次，均时 / 中位 / P95 / 总时 = 2.903 / 2.280 / 5.708 / 198416.43 s；输入 50,724,805，输出 5,031,914，缺 usage 22。fail=0，故官方资源 = 成功样本；time-join 与官方 call_seconds_sum / token 完全一致。
- **gpt6luna StepShield test_holdout**：成功 216/0；32.756 / 27.767 / 70.397 / 7075.34 s；调用 2,193 次，3.097 / 2.340 / 6.114 / 6792.44 s；输入 1,806,813，输出 161,722，缺 usage 1。两列合计输入 token 52,531,618。split 级 invocation_wall 留空（官方为战役级 215617.04783657845）。
- **claudehaiku WildGuard response（Mode E）**：成功 1670 / 失败 55；episode 3.786 / 2.625 / 7.253 / 6322.91 s（`episodes.jsonl` 成功样本墙钟）；调用 1,743 次，3.379 / 2.517 / 6.410 / 5889.56 s；输入 3,676,616，输出 131,177，缺 usage 0；每成功样本输入 2201.57。这些分母不含失败。官方含失败的合计（未用作表内分母）：episode 总时 8602.630227813497（N=1725），input=3,944,866，output=172,467，calls=2018，call_seconds_sum=6497.692988569848；其中失败 episode 的调用为 275 次、输入 268,250、输出 41,290、调用总时 608.133930365555。

claudehaiku 的 StepShield 与 gpt6luna 的 Mode E 时间单元格仍留空。

## 已有显示值复核

与上一版 MCC 重建结果（`/workspace/rq1_summary_work/out/`）比较：主表与全指标表中，除本次新写入的三个格子外，其余模型 × 位置的显示值（含混淆矩阵与 MCC / TPR / TNR / Acc / F1）均未变化。新格子显示为：

- gpt6luna StepShield test：0.581 (98.1%/87.0%)，acc 87.9%，F1 56.6%，EIR@3 61.1%，平均干预差 −1.54，过早告警 244
- gpt6luna StepShield holdout：0.636 (99.1%/59.3%)，acc 79.2%，F1 82.6%，EIR@3 69.2%，平均干预差 −1.50，过早告警 32
- claudehaiku WildGuard response：0.691 (67.3%/96.8%)，acc 91.8%，F1 73.5%，可判分 1654，失败 55

官方 acc / F1 与由 TP/FP/TN/FN 重算后的一位小数显示一致（holdout F1 原始值与重算相差约 1e-16）。正式表中没有纳入 WildGuard prompt（Mode A1）。未覆盖 `/workspace/rq1_summary_work/live/`。
