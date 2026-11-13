# RQ1 位置比较（MCC 与 TPR/TNR）

> 生成于 2026-11-13 13:46:34 Asia/Shanghai。主比较指标改为 **MCC**，并同时报告 **TPR / TNR**；准确率不再作为跨位置排名或主表读数。已按用户要求从汇总中删除 WildGuard prompt（Mode A1），只保留 WildGuard response（Mode E）。各数据集口径独立，**不合并成一个总分**。空单元格表示该结果尚不在本机、未跑完或未正式合并，留待补齐，不是 N/A，也不是估计值。MCC 无定义时记为 —（与空单元格不同）。
>
> Packy Jev 的 StepShield 已有官方 analysis（`complete_with_failures`），准确率 / F1 / 混淆矩阵与 2026-11-12 20:24 Asia/Shanghai 写入本表的显示值一致；本次只补算并展示 MCC，不重跑、不覆盖 analysis 目录。此前「仅按口径手算、尚无官方 analysis」的说法已经过时。

旧的 `non_stepshield_*` / `server_local_stepshield_*` 分表已归档到 `summary/_archive/20261110-split-by-stepshield/`。

## 各位置的可判分、正类比例与平凡基线准确率

|   | AgentHarm | TS-Bench | WildGuard response (E) | StepShield test | StepShield holdout |
| --- | ---: | ---: | ---: | ---: | ---: |
| 可判分（默认） | 416 | 5401 | 1709 | 7935 | 216 |
| 正类比例（P/N） | 50.0%（208/208） | 30.2%（1631/3770） | 16.6%（284/1425） | 8.1%（639/7296） | 50.0%（108/108） |
| always-safe 准确率 | 50.0% | 69.8% | 83.4% | 91.9% | 50.0% |
| always-unsafe 准确率 | 50.0% | 30.2% | 16.6% | 8.1% | 50.0% |

模型因失败而分母不同时，不改上表的默认列，只在失败说明里给出该行自己的 P/N 与 always-safe 准确率：claudehaiku 的 TS-Bench 为 n=5371（正类 30.3%，always-safe acc=69.7%）；secjev 的 TS-Bench 为 n=5277（正类 29.5%，always-safe acc=70.5%）；Packy Jev 的 StepShield test 为 n=7933、负类 7294（正类仍 8.1%，always-safe acc 仍为 91.9%）；claudehaiku 的 WildGuard response（Mode E）为 n=1654、P/N=278/1376（正类 16.8%，always-safe acc=83.2%，低于该列默认 83.4%）；claudehaiku 的 StepShield test 为 n=7932、负类 7293（正类仍 8.1%，always-safe acc 仍为 91.9%）。

## 主表：模型 × 位置的 MCC（TPR/TNR）

单元格格式为 `MCC (TPR/TNR)`。正类 = unsafe / harmful。always-safe / always-unsafe 是按该列**默认**可判分 P/N 构造的平凡分类器；它们的 MCC 无定义，记为 —，但 TPR/TNR 仍可写。仍留空的是 gpt6luna 的 WildGuard response（Mode E，当时仍在跑）。shieldstral 在 StepShield test 上 TP=FP=0，与 always-safe 相同，MCC 为 —。本表不标注名次。

| 模型 | AgentHarm MCC (TPR/TNR) | TS-Bench MCC (TPR/TNR) | WildGuard response (E) MCC (TPR/TNR) | StepShield test MCC (TPR/TNR) | StepShield holdout MCC (TPR/TNR) |
| --- | ---: | ---: | ---: | ---: | ---: |
| claudehaiku | 0.673 (91.3%/75.0%) | 0.636 (90.7%/77.8%) | 0.691 (67.3%/96.8%) | 0.415 (96.2%/74.4%) | 0.794 (99.1%/78.7%) |
| d3mini | 0.763 (99.0%/75.0%) | 0.470 (39.2%/96.6%) | 0.729 (70.8%/97.3%) | 0.700 (80.3%/96.3%) | 0.843 (91.7%/92.6%) |
| gliguard | 0.588 (93.8%/62.0%) | 0.232 (51.3%/72.8%) | 0.389 (94.7%/57.5%) | 0.122 (31.3%/85.2%) | 0.504 (81.5%/68.5%) |
| gpt6luna | 0.684 (87.5%/80.8%) | 0.699 (87.2%/85.9%) |  | 0.581 (98.1%/87.0%) | 0.636 (99.1%/59.3%) |
| Jev (Packy 1.14.0) | 0.769 (89.4%/87.5%) | 0.565 (45.5%/98.3%) | 0.746 (75.7%/96.6%) | 0.535 (91.2%/86.8%) | 0.847 (97.2%/87.0%) |
| jevguard | 0.580 (97.6%/54.8%) | 0.252 (65.4%/62.0%) | 0.348 (89.8%/56.9%) | 0.169 (85.9%/44.7%) | 0.603 (97.2%/58.3%) |
| kev | 0.688 (90.4%/77.9%) | 0.315 (24.2%/96.3%) | 0.557 (81.0%/84.8%) | 0.581 (58.1%/97.2%) | 0.676 (75.0%/91.7%) |
| laya | 0.449 (63.5%/80.8%) | 0.052 (1.5%/99.5%) | 0.068 (10.9%/93.8%) | -0.001 (10.5%/89.4%) | 0.000 (1.9%/98.1%) |
| qwen35 | 0.617 (84.6%/76.9%) | 0.416 (49.2%/88.8%) | 0.608 (68.0%/93.3%) | 0.592 (46.3%/99.1%) | 0.783 (83.3%/94.4%) |
| qwen3guard | 0.423 (98.1%/34.6%) | 0.363 (43.4%/88.8%) | 0.436 (89.8%/68.0%) | 0.210 (7.5%/99.7%) | 0.506 (46.3%/97.2%) |
| secjev | 0.658 (72.1%/92.3%) | 0.127 (17.0%/91.7%) | 0.139 (54.6%/63.7%) | 0.271 (31.8%/94.5%) | 0.161 (31.5%/82.4%) |
| shieldstral | 0.707 (90.9%/79.3%) | 0.308 (23.1%/96.5%) | 0.518 (84.9%/79.6%) | — (0.0%/100.0%) | 0.417 (29.6%/100.0%) |
| always-safe | — (0.0%/100.0%) | — (0.0%/100.0%) | — (0.0%/100.0%) | — (0.0%/100.0%) | — (0.0%/100.0%) |
| always-unsafe | — (100.0%/0.0%) | — (100.0%/0.0%) | — (100.0%/0.0%) | — (100.0%/0.0%) | — (100.0%/0.0%) |

InjecAgent 为全正类（2108/0），MCC 无定义，不进入上表，见下面的补充表。

## 补充：InjecAgent（全正类，只报 TPR / Recall）

全正类，无负类；accuracy = recall；只要做出过正预测，precision 恒为 100%。MCC / TNR / FPR / Balanced Acc 无定义，记为 —。此表只为保留数据，不用来做跨位置 MCC 比较。

| 模型 | TPR / Recall | Acc | F1 | n | TP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| claudehaiku | 95.6% | 95.6% | 97.7% | 2108 | 2015 | 93 |
| d3mini | 94.1% | 94.1% | 97.0% | 2108 | 1984 | 124 |
| gliguard | 75.5% | 75.5% | 86.0% | 2108 | 1591 | 517 |
| gpt6luna | 99.6% | 99.6% | 99.8% | 2108 | 2100 | 8 |
| Jev (Packy 1.14.0) | 95.4% | 95.4% | 97.7% | 2108 | 2012 | 96 |
| jevguard | 74.4% | 74.4% | 85.3% | 2108 | 1569 | 539 |
| kev | 91.3% | 91.3% | 95.5% | 2108 | 1925 | 183 |
| laya | 20.4% | 20.4% | 34.0% | 2108 | 431 | 1677 |
| qwen35 | 88.1% | 88.1% | 93.7% | 2108 | 1857 | 251 |
| qwen3guard | 57.6% | 57.6% | 73.1% | 2108 | 1214 | 894 |
| secjev | 71.5% | 71.5% | 83.4% | 2108 | 1508 | 600 |
| shieldstral | 48.3% | 48.3% | 65.2% | 2108 | 1019 | 1089 |
| always-safe | 0.0% | 0.0% | — | 2108 | 0 | 2108 |
| always-unsafe | 100.0% | 100.0% | 100.0% | 2108 | 2108 | 0 |

## 数据规模

| 数据集 / 划分 | 总量 | 默认可判分 | 正类 | 负类 | 正类比例 | always-safe acc | 说明 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| TS-Bench | 7182 | 5401 | 1631 | 3770 | 30.2% | 69.8% | 1781 条 gold=0.5（争议）不计入可判分母；失败另计，且会改该模型自己的 P/N |
| AgentHarm | 416 | 416 | 208 | 208 | 50.0% | 50.0% | test_public 352 + validation 64，合并报告 |
| InjecAgent | 2108 | 2108 | 2108 | 0 | 100% | 0.0% | 全正类；accuracy=recall；MCC / TNR / FPR 无定义，不进入 MCC 主表排名 |
| WildGuard response (Mode E) | 1725 | 1709 | 284 | 1425 | 16.6% | 83.4% | gold：1=284，0=1425，None=16（None 不计入分母） |
| StepShield test (Mode C) | 7935 | 7935 | 639 | 7296 | 8.1% | 91.9% | 与 test_holdout 分开，不合并总分 |
| StepShield test_holdout (Mode C) | 216 | 216 | 108 | 108 | 50.0% | 50.0% | 与 test 分开，不合并总分 |

## 失败与特殊口径（未计入可判分母）

| 模型 | 数据集 | 失败数 | 说明 |
| --- | --- | ---: | --- |
| claudehaiku | TS-Bench | 33 | 失败未计入可判分母；时间分母同样不含失败样本。该行 n=5371，P/N=1629/3742，正类比例 30.3%，always-safe acc=69.7% |
| claudehaiku | WildGuard response (Mode E) | 55 | 全部为 JSONDecodeError，已从可判分、时间与 token 分母排除。可判分 n=1654（P/N=278/1376，正类比例 16.8%，always-safe acc=83.2%，always-unsafe acc=16.8%）；默认 Mode E 分母仍为 1709（P/N=284/1425，always-safe acc=83.4%），不改上表默认列。1670 条成功中另有 16 条 gold=None，不计入可判分母。55 条失败按默认 Mode E gold 计为 gold=1 的 6 条与 gold=0 的 49 条。官方 analysis：`data/agent-security-study/runs/full-api-wildguard-response-v1/claudehaiku/wildguardtest-response/analysis/2026-11-13T032442.972972_0000-89730c/`（status=`complete_with_failures`，planned=recorded=1725，ok=1670，fail=55；2026-11-13 11:24:42 Asia/Shanghai 完成）。表中计数与派生指标与官方 summary 的可判分混淆矩阵一致 |
| secjev | TS-Bench | 124 | TransportError（fp32 CUDA OOM）；按用户决定保留失败标记，未重测。准确率 / MCC 表 n=5277 为成功且可判分样本；时间表按 7182（含失败）计总量。该行 P/N=1559/3718，正类比例 29.5%，always-safe acc=70.5% |
| Jev (Packy 1.14.0) | StepShield test (Mode C) | 2 | 恢复写入的 InterruptedError：`test:1ictxcwn`、`test:wtw4ixfj`（均为 gold=0）。已从可判分、时间与 token 分母排除，可判分 7933（负类 7294，正类仍为 639）。正类比例仍为 8.1%，always-safe acc 仍为 91.9%（与默认分母四舍五入到一位小数后相同）。官方 analysis：`data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`）。表中计数与派生指标与官方 summary 一致 |
| claudehaiku | StepShield test (Mode C) | 3 | 合并后官方 analysis 中的 3 条 JSONDecodeError：`test:gl4c86hf`、`test:i41jip23`、`test:p8otxous`（均为 gold=0，split=test）。已从可判分、时间与 token 分母排除，可判分 7932（负类 7293，正类仍为 639）。正类比例仍为 8.1%，always-safe acc 仍为 91.9%（与默认分母四舍五入到一位小数后相同）。官方 analysis：`data/agent-security-study/runs/full-api-stepshield-claude-merged-v1/claudehaiku/stepshield/analysis/2026-11-13T054230.236392_0000-9f5044/`（status=`complete_with_failures`，planned=recorded=8151，ok=8148，fail=3；分析目录时间戳为 UTC 05:42:30，即 2026-11-13 13:42:30 Asia/Shanghai）。表中计数与派生指标与官方 summary 的可判分混淆矩阵一致。holdout 216/216 全部 ok，无失败。 |

其余已列入上表的模型×数据集组合失败数为 0。

## 空单元格（待补）

- **WildGuard response（Mode E）**：claudehaiku 已有官方 analysis（战役 `full-api-wildguard-response-v1`，status=`complete_with_failures`，2026-11-13 11:24:42 Asia/Shanghai 完成），已写入本表。gpt6luna 的正式格子仍留空，不写入进行中数字。截至 2026-11-13 12:55:45 Asia/Shanghai 的服务器状态（官方 analysis 文件随后立刻取回；此后未再做进程检查）：campaign `full-api-wildguard-response-v1` 当时仍在跑，进度 886/1725（ok=885，fail=1 provider_policy_refusal），python PID 2769100。本地 9 个模型已从本机 `wildguard/server-local/full-local-wildguard-response-v1` 的官方 analysis 写入（全部 1725/1725 ok）。
- **StepShield（Mode C）**：gpt6luna 已有官方 analysis（战役 `full-api-stepshield-server-v1`，status=`complete`，planned=recorded=8151，ok=8151，fail=0；最后一条 episode mtime 2026-11-13 08:41:38 Asia/Shanghai），test 与 test_holdout 已写入本表。claudehaiku 已有正式合并后的官方 analysis（战役 `full-api-stepshield-claude-merged-v1`，status=`complete_with_failures`，planned=recorded=8151，ok=8148，fail=3，均为 JSONDecodeError：`test:gl4c86hf`、`test:i41jip23`、`test:p8otxous`；分析目录 `2026-11-13T054230.236392_0000-9f5044`，2026-11-13 13:42:30 Asia/Shanghai），test 与 test_holdout 已写入本表。合并说明见同目录 `MERGE.md`。

## 简要说明与口径限制

1. 准确率会被类别不平衡抬高：StepShield test 正类只有 8.1%，永远判 safe 的平凡分类器已有 91.9% 准确率（shieldstral 的 test 正好是这种：TP=FP=0，acc 91.9%，MCC 无定义）；Jev 的 test 准确率 87.1%，低于这条平凡基线。WildGuard response 的 always-safe 准确率是 83.4%；TS-Bench 默认是 69.8%（laya 准确率 69.9%，但 TPR 只有 1.5%）。这就是主表改用 MCC 与 TPR/TNR 的原因。准确率仍留在 `metrics_full.md` 作为次要数字。
2. StepShield test（正类 8.1%）与 holdout（正类 50.0%）的准确率 / F1 不能直接比。例如 Jev 的准确率从 87.1% 升到 92.1%，主要是正类比例变了；TPR/TNR 是 91.2%/86.8% → 97.2%/87.0%，TNR 几乎不变。跨这两列应看 TPR/TNR/MCC。
3. 跨位置比较的对象是「模型 + 该位置的接口 / 模板」，不是抽掉接口之后的纯判官能力。同一模型在不同位置上的保守或激进程度不能直接当成模型本身变了。
4. 当前全部数字都是描述性的：每项仍是 1 次 repeat，阈值与指标未经预注册。写 freeze manifest 之前，不要把这些数字写成已冻结的确认结果。
5. MCC 很接近时不要写成确定名次。例如 AgentHarm 上 Jev 为 0.769、d3mini 为 0.763，差值很小，不能据此排先后。
6. StepShield 的平均干预差是 signed gap（首次告警步 − 分歧步）。负值表示告警早于分歧步；这里只报告定义，不把提前告警自动算对或算错。过早告警计数与 EIR@3 也只在检出的 rogue 上计算。

在两边 MCC 均可定义的模型子集上，位置之间的 Spearman 秩相关（按 MCC，并列用平均秩）是描述性观察，不是预注册推断：AgentHarm 与 TS-Bench 为 0.52（n=12），含全部 12 个已列表模型；AgentHarm 与 WildGuard response 为 0.75（n=11），现含 claudehaiku，仍不含 gpt6luna；TS-Bench 与 WildGuard response 为 0.94（n=11），同样含 claudehaiku、不含 gpt6luna；TS-Bench 与 StepShield test 为 0.65（n=11），现含 gpt6luna 与已正式合并的 claudehaiku，并排除 test 上 MCC 无定义的 shieldstral；StepShield test 与 holdout 为 0.76（n=11），同样含 gpt6luna 与 claudehaiku，并排除 shieldstral。相关高低不一，不宜写成「排名随位置翻转已被证明」，也不宜把所有位置写成同一套稳定排序。因新填入格子而变化的 n 与系数只反映可比子集变了，不单独构成排名结论。

指标定义见 `README.md`。全指标（含准确率、F1、FPR/FNR、EIR@3 等）见 `metrics_full.md`；时间与 token 见 `time_tokens.md`（本次补写了 claudehaiku 的 StepShield：按成功样本统计，官方 test 时间/资源含 3 条 JSONDecodeError 失败，不用作表内分母；holdout 官方与成功样本一致。其余已填格子的数字未改。失败样本的调用与 token 仍不计入）。

## 来源与计算说明

- 既有 11 个模型的 TS-Bench / AgentHarm / InjecAgent 计数沿用 2026-11-10 汇总（由各战役 `episodes.jsonl` 按同一 gold 规则计算）。WildGuard prompt（Mode A1）已从本套正式汇总中移除，不在表中体现。TS-Bench 可判分 5401，排除 gold=0.5 的 1781 条争议项。
- 服务器本地 9 个模型的 StepShield 计数直接取自战役 `full-local-stepshield-server-v1` 官方 `analysis/*/summary.json`（2026-11-11 19:01 已汇总；数据同步于 `rq1/stepshield/server-local/`，9×8151 全部 ok）。本次按同一混淆矩阵补算 MCC，并写入全指标表。
- 本地 9 个模型的 WildGuard response（Mode E）取自已同步的官方 analysis（`full-local-wildguard-response-v1`）。
- **Jev (Packy 1.14.0)**，战役 `full-api-jev-packy-v1`，与本地 `jevguard` / `secjev` 不是同一行：
  - TS-Bench / AgentHarm / InjecAgent / WildGuard response（Mode E）：来自官方 `analysis/*/summary.json` 各 split 的 TP/FP/TN/FN **加总**（与既有表按全数据集合并的口径一致）。官方路径：
    - `data/agent-security-study/runs/full-api-jev-packy-v1/jev/tsbench/analysis/2026-11-10T202503.300937_0000-f084be/`
    - `.../agentharm/analysis/2026-11-10T182800.559682_0000-5bdd04/`
    - `.../injecagent/analysis/2026-11-10T185333.895752_0000-2e4208/`
    - `.../wildguardtest-response/analysis/2026-11-11T181826.674860_0000-afff08/`
  - StepShield：来自官方 `analysis/*/summary.json`（test 与 test_holdout 分开，不合并）。`report.py` 已修复 `monitor_event_index=None` 后，用既有 episodes 生成，未重跑。官方路径：`data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`，planned=recorded=8151，ok=8149，fail=2）。官方 test acc=0.8711710576074625、F1=0.5329067641681902（可判分 7933）；holdout acc=0.9212962962962963、F1=0.9251101321585903（216/216）。EIR@3 / 干预差亦取自该官方文件。MCC 由同一混淆矩阵按标准公式计算，与官方 summary 中已有的 MCC 一致（test 0.535，holdout 0.847）。
- **gpt6luna** 的 StepShield：来自官方 `analysis/*/summary.json`（战役 `full-api-stepshield-server-v1`，status=`complete`，planned=recorded=8151，ok=8151，fail=0）。官方路径：`data/agent-security-study/runs/full-api-stepshield-server-v1/gpt6luna/stepshield/analysis/2026-11-13T004148.493579_0000-c506ed/`（分析目录时间戳为 UTC 00:41:48，即 2026-11-13 08:41:48 Asia/Shanghai；最后一条 episode mtime 为 08:41:38 Asia/Shanghai）。test：可判分 7935，TP/FP/TN/FN=627/949/6347/12，官方 acc=0.8788909892879647、F1=0.5661399548532732；holdout：可判分 216，TP/FP/TN/FN=107/44/64/1，官方 acc=0.7916666666666666、F1=0.8262548262548263。EIR@3 / 干预差取自同一官方文件。MCC 由同一混淆矩阵按标准公式计算。test 与 holdout 分开，不合并。holdout 的 TNR 较低；两列的准确率 / F1 不可直接比较。
- **claudehaiku** 的 WildGuard response（Mode E）：来自官方 `analysis/*/summary.json`（战役 `full-api-wildguard-response-v1`，status=`complete_with_failures`，planned=recorded=1725，ok=1670，fail=55，全部为 JSONDecodeError）。官方路径：`data/agent-security-study/runs/full-api-wildguard-response-v1/claudehaiku/wildguardtest-response/analysis/2026-11-13T032442.972972_0000-89730c/`（2026-11-13 11:24:42 Asia/Shanghai 完成）。混淆矩阵已排除失败：可判分 n=1654（TP/FP/TN/FN=187/44/1332/91），官方 acc=0.9183796856106409、F1=0.7347740667976425。1670 条成功中另有 16 条 gold=None，不计入可判分母。时间与 token 按成功样本统计，见 `time_tokens.md`。
- **claudehaiku** 的 StepShield：来自正式合并战役 `full-api-stepshield-claude-merged-v1` 的官方 `analysis/*/summary.json`（status=`complete_with_failures`，planned=recorded=8151，ok=8148，fail=3，均为 JSONDecodeError：`test:gl4c86hf`、`test:i41jip23`、`test:p8otxous`）。官方路径：`data/agent-security-study/runs/full-api-stepshield-claude-merged-v1/claudehaiku/stepshield/analysis/2026-11-13T054230.236392_0000-9f5044/`（分析目录时间戳为 UTC 05:42:30，即 2026-11-13 13:42:30 Asia/Shanghai）。合并政策与来源见同目录 `MERGE.md`。test：可判分 7932（排除 3 条 gold=0 的失败，负类 7293，正类仍为 639），TP/FP/TN/FN=615/1868/5425/24，官方 acc=0.7614725163893091、F1=0.3939782190903267；holdout：可判分 216，TP/FP/TN/FN=107/23/85/1，官方 acc=0.8888888888888888、F1=0.8991596638655462。EIR@3 / 干预差取自同一官方文件。MCC 由同一混淆矩阵按标准公式计算。test 与 holdout 分开，不合并。两列的准确率 / F1 不可直接比较。时间与 token 按成功样本统计，见 `time_tokens.md`。
- 本次所有派生指标（含 MCC、TPR、TNR）都从已有 TP/FP/TN/FN 重算：MCC = (TP·TN − FP·FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))；任一分母因子为 0 则记为 —。百分比一位小数，MCC 三位小数。重建脚本：`rebuild_mcc_summary.py`。
