# 补充 insight（来自其他文件夹，按相关性排序）

这些分析不属于 RQ1/RQ2 主表，但决定了主表结论能不能站住；每条给出处。本包 insights/ 下附了原文副本，仓库路径一并保留。

| # | Insight | 一句话结论 | 出处 |
|---|---|---|---|
| 1 | 操作点敏感性 | 0.5/argmax 不是中立基准；MCC 最优阈值 0.01–0.95；Jev StepShield 0.50→0.77 使 MCC 0.535→0.710 | rq1/ext-2026-11-13/thresholds.csv, thresholds_stepshield.csv |
| 2 | 排名不可识别性 | 多数位置 top-1 概率 52–56%，是掷硬币；只有 TS-Bench 与 StepShield test 可识别 | rq1/ext-2026-11-13/rank_top1.csv, rank_stability.csv |
| 3 | 指标敏感性 | MCC / BAcc / TPR 给出不同冠军；单指标排名不可用 | rq1/ext-2026-11-13/rank_by_metric.csv |
| 4 | 来源迁移 | TS-Bench 三来源排名翻转；StepShield test vs holdout 是 8.1% vs 50% prevalence，acc/F1 不可比 | rq1/ext-2026-11-13/shift.csv |
| 5 | MCC 对照 | 全 test：GPT .5805 > CCD 组合 .543–.552 > prefix .536 > Claude .414 > CG+ .266 > CG −.033 | rq1/architecture-2026-11-13/MCC-TABLE.md |
| 6 | ConstraintGuard 基线 | 覆盖率 12.9%，69% 任务零覆盖；覆盖子集 CG 100%/100% vs CCD 100%/5.3%；CG 叠加 CCD 只增 FP | rq1/architecture-2026-11-13/BASELINE-CONSTRAINTGUARD.md |
| 7 | CCD 轨迹分解 | 补回 prefix 漏检 44/55（80%），新增 FP 3/55（5.5%）；组合 recall 91.4%→96.7%（@.75），FPR 13.2%→14.8% | rq1/architecture-2026-11-13/RESULTS-PILOT.md |
| 8 | TS-Bench 诊断 | Jev 的原始差距一半是操作点；剩余集中在 ASB 合成轨迹；AgentHarm-traj 上 Jev 赢 GPT | rq1/architecture-2026-11-13/TS-BENCH-RESULT.md |
| 9 | TS-CCD 负结果 | 单步口径下探针分解无显著收益（AUC CI 含 0，McNemar p=0.54）；轨迹口径尚未测 | rq1/architecture-2026-11-13/TS-BENCH-RESULT.md |
| 10 | 位置映射限定 | 五位置是五类适配数据，unit/attacker/label 不同；StepShield 应改名 In-flight/Prefix monitoring | paper/review/position-mapping-2026-11-13.md |

## 与 RQ3 的关系

CCD、ConstraintGuard、TS-CCD 这些属于 RQ3（攻击/架构），不在 RQ1/RQ2 主表；但 CG 基线是 RQ1 的必要对照，CCD 是 RQ3 的主线。

