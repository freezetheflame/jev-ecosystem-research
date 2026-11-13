# rq1/architecture-2026-11-13 - 用 input 级判断提升轨迹级检出（CCD）

状态：设计稿 + 离线诊断（无模型调用）。主文档 **[ARCHITECTURE.md](ARCHITECTURE.md)**。

## 一句话

Jev 在轨迹级弱、在 input 级强；离线诊断显示"重新聚合现有 per-step 分数"救不回来（any-threshold 已最优，CUSUM 更差），
漏检的失败模式是**约束弱化/省略**（"without size check"、"no timeout"、"cache all patterns"）。因此提出
**CCD（Constraint-Checklist Decomposition）**：任务→约束清单→每步×每约束的 Jev 原子探针→校准聚合（+可选证据卡二审）。

## 关键数字

- StepShield test：Jev TPR 91.4% @ TNR 86.5%；把 TNR 提到 95%，TPR 只剩 **80.9%**；GPT-6 Luna 98.1% @ TNR 87.0%（差 10–15pp）。
- 离线规则搜索 69,289 步：any-threshold 最优；CUSUM 最好 MCC 0.586（TPR 68.7% @ TNR 95.4%）。
- 55 条漏检 rogue：35 条 max-p ≥0.3（22 条 0.3–0.4、13 条 0.4–0.5），但良性轨迹同样落在该区间。
- P1 pilot 规模：200 轨迹 × 3 个 Jev 系模型 × 6 探针 ≈ 3.1 万次，Jev 现金 <$2。

## 文件

| 文件 | 内容 |
|---|---|
| ARCHITECTURE.md | 诊断、三种候选架构、CCD 三层设计、实验计划、功效、假设与反驳、风险 |
| **BASELINES.md** | 基线设计：StepShield 官方 4 detector、同模型/同分解/同聚合消融、杀灭条件、BaseDetector 实现映射 |
| baseline-matrix.csv | 28 个基线（B1-B28）的层级、实现、split、指标、隔离对象、判据 |
| **TS-BENCH-RESULT.md** | 负结果：单动作判断上原子探针分解无显著收益；真实杠杆是阈值校准与分来源 |
| **MCC-TABLE.md** | 各 split 下 prefix / CG / CG+ / CCD / GPT / Claude 的 TP-FP-TN-FN 与 MCC（含不可定义说明） |
| **BASELINE-CONSTRAINTGUARD.md** | 把官方 ConstraintGuard 当基线的实测：覆盖率、同 split 指标、覆盖子集头对头、CG+ 强规则版 |
| **RESULTS-PILOT.md** | 第一轮真实 pilot：0 LLM 调用、互补性 census（补回 44/55）、组合曲线、成本/延迟 |
| ccd/ | 可执行 CCD 包（含 run_pilot 与 mock 模式） |
| runs/ | 4 个可复现 run（v1/v2 holdout、dev、prefix-miss census） |
| analyze_step_signal.py | 离线诊断脚本（从 Jev StepShield raw 重算 per-step 概率与聚合规则） |
| offline_step_signal.json | 诊断输出（68 条规则 + CUSUM 网格 + FN 分析） |
| inspect_missed.py | 漏检 vs 检出轨迹的分歧步对比与失败模式抽样 |
| pilot-plan.csv | P1–P4 的模型/轨迹/探针/调用/成本 |

## 下一步

1. 拍板 A（CCD）还是 A+B（证据卡二审）。
2. P1 先跑 40 条 feasibility，看探针在分歧步 ±1 的命中率；≥50% 再扩到 200。
3. 冻结约束抽取 prompt、探针文本、聚合器与阈值程序，预注册 H2（TPR@TNR95 从 80.9% → ≥90%）。