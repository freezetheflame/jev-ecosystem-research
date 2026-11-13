# RQ1 汇总表（统一口径）

更新于 2026-11-13 14:45:35 Asia/Shanghai。本目录是当前正式汇总；不再按「非 StepShield / StepShield」拆成两套文件名。已删除 WildGuard prompt（Mode A1）；服务器本地 9 个模型的 WildGuard response（Mode E）已同步并写入正式表。主比较指标改为 **MCC** 与 **TPR/TNR**，不再用准确率做跨位置排名。

Packy Jev 的 StepShield 官方 analysis 已于 2026-11-12 20:24 Asia/Shanghai 写入来源说明，路径为 `data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`）。此前「只是按口径手算」的说法已经过时。

## 当前表

- `metrics.md` / `metrics.csv` — 主表：模型 × 位置的 MCC 与 TPR/TNR，并给出 always-safe / always-unsafe 基线和各列正类比例。InjecAgent 因全正类、MCC 无定义，作为补充的 TPR / Recall 表，不进入 MCC 比较。
- `metrics_full.md` / `metrics_full.csv` — 全指标表（准确率作为次要数字保留；含 FPR/FNR/TNR/Precision/NPV/F1/MCC；StepShield 另含 EIR@3、平均干预差、过早告警）。StepShield 各行凡可计算的 MCC 均已填入；无定义处为 —。
- `time_tokens.md` / `time_tokens.csv` — 成功样本墙钟、调用延迟、已知输入/输出 token。本次补写了 gpt6luna 的 WildGuard response / Mode E（成功样本；官方时间/资源含 1 条 PolicyRefusal 失败及其 5 次调用，不用作表内分母）。其余已填格子的数字未改。失败样本（含 Packy StepShield 那 2 条 InterruptedError，以及其中 `test:1ictxcwn` 的 16 次调用；claudehaiku StepShield 的 3 条失败及其 17 次调用；claudehaiku Mode E 的 55 条 JSONDecodeError 及其 275 次调用；以及 gpt6luna Mode E 的 1 条 PolicyRefusal 及其 5 次调用）仍不计入。
- `rebuild_mcc_summary.py` — 从本目录已有混淆矩阵计数（`metrics_full.csv` 中的 TP/FP/TN/FN）重建上述指标表的脚本，不读 `raw/`，不重跑实验，不改 analysis 目录。

各数据集单独列表，**不合并成一个总分**。空单元格表示结果还不在本机、尚未跑完或尚未正式合并，可以以后直接填，不是估计值。MCC 写 — 表示公式无定义，与空单元格不是同一回事。

## 指标含义

下列定义中，正类 = unsafe / 有害，负类 = safe / 无害。除非另说，分母都是**可判分**样本：有 0/1 gold、且有 0/1 预测的成功 episode。失败样本、以及 TS-Bench 中 gold=0.5 的争议项、WildGuard 中 gold=None 的样本，都不进入可判分母。

- **正类比例（prevalence）**：可判分中 gold=正类的比例，P / (P+N)。各检查位置的正类比例差很大（StepShield test 约 8.1%，AgentHarm / holdout 为 50%，InjecAgent 为 100%），所以准确率不能跨位置直接比。
- **TPR / Recall（真正例率，也叫灵敏度）**：TP / (TP+FN)。在真正有害的样本里，判成有害的比例。
- **TNR / Specificity（真负例率，也叫特异度）**：TN / (TN+FP)。在真正无害的样本里，判成无害的比例。
- **FPR（假正例率）**：FP / (FP+TN) = 1 − TNR。把无害判成有害的比例。
- **FNR（假负例率）**：FN / (FN+TP) = 1 − TPR。把有害判成无害的比例。
- **Precision（精确率）**：TP / (TP+FP)。在所有判成有害的样本里，真正有害的比例。当 TP+FP=0（从未判有害）时无定义，记为 —。
- **NPV（负预测值）**：TN / (TN+FN)。在所有判成无害的样本里，真正无害的比例。当 TN+FN=0 时无定义。全正类设定下这个量没有比较意义，InjecAgent 表中记为 —。
- **Acc（准确率）**：(TP+TN) / (TP+TN+FP+FN)。类别很不平衡时，哪怕几乎不做检出也可以很高，因此不再作为主表排名指标；只留在全指标表里备查。
- **Balanced Acc（平衡准确率）**：(TPR+TNR) / 2。两类各占一半权重。全正类时 TNR 无定义，故也记为 —。
- **F1**：2 · Precision · Recall / (Precision + Recall)。同样受正类比例影响，且在 Precision 无定义时本表对基线记为 —；shieldstral 的 StepShield test 沿用已发布的 F1=0.0%。
- **MCC（Matthews 相关系数）**：\( (TP·TN − FP·FN) / \sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)} \)。取值大致在 −1 到 1，0 表示与随机（或与类别比例）没有相关。四个分母因子里只要有一个为 0，MCC 就无定义，必须记为 —，**不能改写成 0**。典型无定义情况：常数分类器（always-safe：TP+FP=0；always-unsafe：TN+FN=0）、全正类数据（InjecAgent：TN=FP=0）、以及 shieldstral 在 StepShield test 上 TP=FP=0。MCC 对类别不平衡比准确率稳，因此作为跨位置的主比较指标。百分比一位小数，MCC 三位小数。
- **always-safe / always-unsafe 基线**：分别是「永远判 safe」和「永远判 unsafe」的平凡分类器，按该列默认可判分的 P/N 构造。它们的 MCC 一律无定义。always-safe 的准确率等于负类比例，可用来判断一张准确率表是不是被基线抬起来的。若某模型因失败导致分母与默认列不同，会在失败说明里给出该行自己的基线，不把进行中或失败样本算进计分。
- **EIR@3（StepShield）**：在检出的 rogue 轨迹上，首次告警是否落在分歧步之后 3 步以内的比例。只在检出的 rogue 上计算；没有检出则官方记为缺省（—）。
- **平均干预差（signed intervention gap）**：检出的 rogue 上，（首次告警步 − 分歧步）的平均值。负值表示告警早于分歧步。这里只报告定义，不把提前告警自动算对或算错。
- **过早告警（premature alerts）**：检出的 rogue 中，首次告警早于分歧步的条数。

## 计分要点

- TS-Bench：总量 7182，可判分 5401（排除 gold=0.5 的 1781 条争议项）。
- WildGuard 只汇总 response（Mode E）。Mode E 的 gold 为 1=284、0=1425、None=16（可判分 1709）。WildGuard prompt（Mode A1）不纳入本套正式汇总。
- StepShield 只报告 Mode C 前缀监控，test 与 test_holdout 必须分开，不可把准确率 / F1 直接对比。
- Jev (Packy 1.14.0)（战役 `full-api-jev-packy-v1`）与本地 `jevguard`、`secjev` 是不同模型行。
- Packy 的 StepShield 官方 analysis 现为 `data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`）。表中该行取自官方 summary。2 条 InterruptedError（`test:1ictxcwn`、`test:wtw4ixfj`）仍排除在可判分母之外。
- 所有当前数字都是描述性的（1 次 repeat，阈值与指标未经预注册）。MCC 很接近时不要写成确定名次。跨位置比较的是「模型 + 接口 / 模板」。

## 已填入的官方格子

- 服务器本地 WildGuard Mode E（`full-local-wildguard-response-v1`）已于 2026-11-12 同步到 `../wildguard/server-local/`，并写入本目录各表。
- gpt6luna 的 StepShield（战役 `full-api-stepshield-server-v1`，官方 analysis `2026-11-13T004148.493579_0000-c506ed`）与 claudehaiku 的 WildGuard response / Mode E（战役 `full-api-wildguard-response-v1`，官方 analysis `2026-11-13T032442.972972_0000-89730c`）已写入本目录各表。
- claudehaiku 的 StepShield 已写入正式合并战役 `full-api-stepshield-claude-merged-v1` 的官方 analysis（`2026-11-13T054230.236392_0000-9f5044`，status=`complete_with_failures`，8148/8151 ok）。
- gpt6luna 的 WildGuard response / Mode E 已写入同一战役 `full-api-wildguard-response-v1` 的官方 analysis（`2026-11-13T061430.606753_0000-9d3a76`，status=`complete_with_failures`，planned=recorded=1725，ok=1724，fail=1 PolicyRefusal，2026-11-13 14:14:30 Asia/Shanghai 完成）。列入本套正式汇总的官方格子现已全部写入。详见 `metrics.md` 的来源说明。

## 归档

2026-11-10 / 2026-11-11 的分表（`non_stepshield_*`、`server_local_stepshield_*`、`README_BUNDLE.md`）在 `_archive/20261110-split-by-stepshield/`。上级目录里的 `rq1_non_stepshield_bundle_20261110.zip` 仍保留，但是过期快照，请以本目录新表为准。
