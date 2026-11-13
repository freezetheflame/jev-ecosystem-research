# MCC 对照表（2026-11-13）

由 [mcc_table.py](mcc_table.py) 从各 run/summary 的 TP/FP/TN/FN 计算。MCC 依赖 prevalence，
**不同 split 的 MCC 不能直接比较**；选择性子集（census）只能看同子集内的相对关系。

## 1. 完整 test split（7,933；639 rogue / 7,294 clean，prevalence 8.1%）

| 系统 | TP | FN | FP | TN | MCC |
|---|---:|---:|---:|---:|---:|
| GPT-6 Luna | 627 | 12 | 949 | 6347 | **0.5805** |
| prefix + CCD @0.90（估计） | 601 | 38 | 966 | 6328 | 0.5524 |
| prefix + CCD @0.75（估计） | 618 | 21 | 1081 | 6213 | 0.5432 |
| Jev prefix | 584 | 55 | 966 | 6328 | 0.5364 |
| prefix + CCD @0.60（估计） | 628 | 11 | 1311 | 5983 | 0.5085 |
| Claude Haiku | 615 | 24 | 1868 | 5425 | 0.4145 |
| ConstraintGuard+（自建强规则） | 102 | 537 | 84 | 7210 | 0.2664 |
| ConstraintGuard（官方实现复跑） | 155 | 484 | 2170 | 5124 | **−0.0328** |

读法：
- 确定性基线里 CG 的 MCC 为负（FP 太多），CG+ 0.266；CCD 组合在 0.75/0.90 上比 prefix 略高（+0.007/+0.016）。
- 但 **GPT-6 Luna 的 MCC 仍最高**（0.5805）：CCD 组合没有在 MCC 上超过 GPT。
- @0.90 是"最干净"的增益点：FP 不变（0/55 新增）、只多抓 17 条 rogue，MCC 0.5364→0.5524。

## 2. held-out 216（108 rogue / 108 clean，prevalence 50%）

| 系统 | TP | FN | FP | TN | MCC |
|---|---:|---:|---:|---:|---:|
| 官方 LLMJudge（GPT-4.1-mini） | 103 | 5 | 6 | 102 | **0.8982** |
| Jev prefix | 105 | 3 | 14 | 94 | 0.8470 |
| Claude Haiku | 107 | 1 | 23 | 85 | 0.7944 |
| GPT-6 Luna | 107 | 1 | 44 | 64 | 0.6359 |
| ConstraintGuard（官方 published） | 26 | 82 | 27 | 81 | −0.0108 |

注：这是 balanced split，MCC 普遍比 test split 高；CCD 只在 20/20 随机子集上有数（MCC 0.804），
不能和 216 条整体混比。

## 3. census 110（55 prefix-missed rogue / 55 prefix-clean，选择性子集）

| 系统 | TP | FN | FP | TN | MCC |
|---|---:|---:|---:|---:|---:|
| Jev prefix | 0 | 55 | 0 | 55 | **undefined**（constant-negative） |
| ConstraintGuard | 16 | 39 | 19 | 36 | −0.0586 |
| ConstraintGuard+ | 7 | 48 | 0 | 55 | 0.2607 |
| CCD @0.60 | 44 | 11 | 3 | 52 | **0.7535** |

读法：
- 这个子集里 prefix 的 MCC **无定义**（它没有任何正预测），所以不能用 MCC 评价 prefix——这正是"选择性子集不能外推"的原因。
- 同子集内：CCD 0.754 ≫ CG+ 0.261 ≫ CG −0.059；CCD 在确定性基线面前是明确赢家。
- 但 census 是难例集（prefix 漏掉的 rogue），0.754 不能外推到完整分布。

## 4. 结论（MCC 口径）

- **对 ConstraintGuard：赢。** 完整 test 上 CG −0.033（比随机还差），CG+ 0.266；CCD 组合 0.543–0.552，census 上 0.754 vs −0.059/0.261。
- **对 Claude Haiku：在 test split 上赢**（CCD 组合 0.543–0.552 vs 0.414），但 Claude 是 native 点、无概率，不能做匹配 FPR 的严格比较。
- **对 GPT-6 Luna：没有赢。** test split 上 GPT 0.5805 > CCD 组合 0.552；holdout 上 GPT 0.636 低于 prefix 0.847，说明 split/prevalence 影响很大。
- **对官方 LLMJudge：差得远**（holdout 0.898，FPR 5.6%），而且我们没有同 split 的 CCD 全量数据。

## 5. 方法学提醒

1. MCC 随 prevalence 变化：8.1% 的 test split 与 50% 的 holdout 不能互比；论文按 split 分栏。
2. 常数分类器的 MCC 无定义（census 上的 prefix），不能写成 0。
3. 若以 MCC 为主指标，需在**完整 test** 上跑 CCD（现在组合 MCC 是外推估计），并同时报 matched-FPR recall——否则 MCC 会掩盖 CCD 的召回收益。
4. 组合系统的 MCC 对新增 FP 很敏感：@0.60 时 recall 最高但 MCC 反而低于 prefix；@0.90 是 MCC 最优的保守点。
