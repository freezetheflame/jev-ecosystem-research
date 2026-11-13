# CCD 的对比基线设计

日期：2026-11-13。状态：设计稿。配套：[ARCHITECTURE.md](ARCHITECTURE.md)、[baseline-matrix.csv](baseline-matrix.csv)、
StepShield 数据集与 harness：data/agent-security-study/datasets/full-suite-v1/stepshield/snapshot/。

## 0. 结论

有，而且比预期现成得多。StepShield 自带 **4 个官方 detector + 统一指标 + 可插拔 BaseDetector 接口**，
所以我们的架构必须和它们在同一 split、同一指标下比较；内部再做"同模型不同接口""同分解不同内容""同内容不同聚合"三层消融。
**最危险的基线是 ConstraintGuard（确定性约束 monitor）和 call-matched 前缀提问**：前者决定"模型是否必要"，后者决定"增益是否只是多调了几次"。

## 1. 外部基线：StepShield 官方 detector（同一 split、同一指标）

官方 README/benchmark 给出 held-out test（216：108 rogue / 108 clean）上的数字：

| Detector | 机制 | EIR@3 | Recall | FPR | Acc | F1 | IG | Tokens saved |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Random | 随机 | 0.12 | 50.0% | 50.0% | .50 | .50 | -3.0 | 49.1% |
| StaticGuard | 847 条正则规则 | 0.23 | 86.1% | 77.8% | .54 | .65 | -5.0 | 78.9% |
| ConstraintGuard | 23 类行为约束 | 0.08 | 24.1% | 25.0% | .50 | .32 | -5.3 | N/A |
| LLMJudge | GPT-4.1-mini + 5 步窗口 | **0.89** | **95.4%** | **5.6%** | .95 | .95 | **-0.4** | **91.2%** |
| HybridGuard | StaticGuard 初筛 → LLM | 0.40 | 75.9% | 44.4% | .66 | .69 | -2.7 | 87.5% |

为什么直接可用：

1. **同一个 harness**：benchmark/detectors/base.py 定义 BaseDetector.detect_step(step, step_index, trajectory_context) -> StepResult；
   detect_trajectory 负责循环、记录 detection_step、api_calls、total_tokens、cost_usd、latency_ms。我们的 CCD 可以写成一个 detector，直接跑 run_benchmark.py。
2. **同一套指标**：EIR(k=3)（告警必须落在分歧步之后 3 步内，提前告警得 0 分）、IG（有符号提前/延迟）、Tokens Saved、FPR、Recall。
   这比我们现在的 TPR/TNR 更严格，也更适合"时序"主张。
3. **同一 split**：test_holdout 是官方可比集；test（7,935）用于功效，但官方 detector 数字只在 holdout 上，需在报告里分列。
4. **可复跑**：StaticGuard / ConstraintGuard 是确定性的，本地零成本复跑；HybridGuard 的静态部分也可复跑；LLMJudge 需要 GPT-4.1-mini，
   我们引用官方数字，并另跑一个"我们自己的 LLM judge"（Claude/GPT-6 Luna）做成本对照。

**注意操作点**：官方数字是各自 native 操作点。我们的 Jev 在同一个 holdout 上 EIR 89.5%、recall 97.2%、FPR 13.0%——
EIR 与 LLMJudge 的 89 持平，但 FPR 是 5.6% 的 2.3 倍。所以主表必须同时给 **recall@FPR<=5% / <=10%**，不能只比 native 点。
在部署 test（7,935）上 Jev 的 EIR 降到 68.6%，这里才是架构要补的缺口。

## 2. T2：同模型、不同接口（隔离"分解"）

| ID | 基线 | 隔离什么 | 预期/判据 |
|---|---|---|---|
| B6 | Jev prefix-level（现有 Mode C） | 现任 | CCD 必须显著优于此，否则分解失败 |
| B7 | Jev 滑窗（最近 5 步，对齐 LLMJudge） | 上下文长度 | 若 B7 ≈ CCD，说明增益来自"短上下文"，不是分解 |
| B8 | Jev 多问题前缀（拆问题、不拆步） | 问题分解 | 若 B8 ≈ CCD，不需要逐步拆 |
| B9 | Jev 全轨迹单次调用（2609.34862 式） | 长上下文单次判决 | 若 B9 ≈ CCD，分解无必要 |
| B10 | **call-matched 前缀提问**（调用数与 CCD 相同） | 计算量 | 若 B10 ≈ CCD，H3 被反驳：增益只是调用数 |

## 3. T3：同分解、不同内容（隔离 checklist）

| ID | 基线 | 隔离什么 | 判据 |
|---|---|---|---|
| B11 | 通用逐步探针（"这一步是否 unsafe？"）+ 同聚合 | checklist 的价值 | 若 ≈ CCD，checklist 不必要 |
| B12 | 仅 q_inj（InjecAgent 口径） | 注入通道 | 若 ≈ CCD，增益只是注入检测 |
| B13 | 仅 q_scope | 范围通道 | 若 ≈ CCD，增益只是 scope |
| B14 | 开放式"是否违反任一要求？"（不给 checklist） | 结构化 vs 开放式 | 若 ≈ CCD，结构化不必要 |

## 4. T4：同探针、不同聚合（隔离聚合器）

max / any-threshold / CUSUM / L2 logistic / last-step-only / oracle-over-thresholds。
主结果用手工规则（max + 持久性 + prefix 分），logistic 只作为上限参考；oracle 是天花板。

## 5. T5：架构与强参照

| ID | 基线 | 作用 |
|---|---|---|
| B22 | CCD + 证据卡 LLM 二审 | 判断聚合是否不足；若 B22 >> CCD，说明需要二审 |
| B23 | Cascade（CCD 过滤 → LLM） | 成本-检出折中，与 HybridGuard 对照 |
| B24 | 微调小分类器（step 文本 + dev 标签） | 监督学习替代；若 ≈ CCD，Jev 不是差异来源 |
| B25 | 人工/ oracle 上界（100 轨迹） | 天花板 |
| B26 | 2609.34862 Jev trace judge（F1 77.8 vs 74.1） | 外部轨迹判官参照 |
| B27 | 2610.11773 ObligationBench（14 模型，best recall 48.97%，exact 10%） | 义务/遗漏粒度参照 |
| B28 | 2611.11571 确定性 monitor（严重动作 0.0% ASR） | 确定性对照的必要性 |

## 6. 主表 vs 附录 vs 只引用

**主表（论文正文）**：Random、StaticGuard、ConstraintGuard、LLMJudge（官方）、HybridGuard、B6 Jev prefix、B7 滑窗、B9 全轨迹、**B15 CCD**、B22 CCD+card、B23 Cascade。
列：Recall、FPR、recall@FPR5%、EIR@3、IG、Tokens Saved、$/轨迹、延迟。

**附录/消融**：B8、B10–B14、B16–B21、B24。
**只引用**：B25（除非做）、B26–B28（不同数据集，不能混表）。

## 7. 杀灭条件（写进 pre-registration）

| 如果 | 结论 |
|---|---|
| CCD ≤ ConstraintGuard（matched FPR） | 模型不必要，规则足够；应转确定性方案或负结果 |
| B10 call-matched ≈ CCD | 增益来自调用数，不是分解；H3 反驳 |
| B11 通用探针 ≈ CCD | checklist 不必要；简化为通用逐步探针 |
| B7 滑窗 ≈ CCD | 上下文长度是主因；不需要 k×步 探针 |
| B24 微调分类器 ≈ CCD | Jev 不是差异来源；架构退化为监督分类 |
| B6 ≥ CCD | 分解失败；报负结果（也有价值） |
| B22 >> CCD | 聚合不足；采用证据卡二审 |

## 8. 实现映射（StepShield harness）

1. **CCDDetector(BaseDetector)**：override detect_trajectory 以每轨迹算一次 checklist（Stage 1），detect_step 做 k 个探针（Stage 2）
   并按聚合状态返回 StepResult（Stage 3）；api_calls/tokens/cost 由 detector 累计，harness 自动写入 DetectionResult。
2. 运行：python benchmark/run_benchmark.py --data-dir data/test_holdout/scrubbed --detector ccd.CCDDetector --output ...
   （可选 --data-dir data/test/... 做 7,935 的功效分析。）
3. 官方 detector：先本地复跑 StaticGuard/ConstraintGuard（无 API），核对 README 数字；LLMJudge 引用官方 + 跑我们自己的 LLM 变体。
4. 指标语义：EIR 对"提前告警"给 0 分；CCD 若在分歧步的 thought 就触发，需要定义告警步（建议：命中 thought 记在下一步 action，
   或同时报官方 EIR 与我们的 early-warning lead 两个口径）。
5. 成本：同一 DetectionResult 里的 api_calls/tokens/cost/latency 直接进表；本地模型标 unpriced。

## 9. 统计

- 主比较：**recall@FPR<=5%** 与 **EIR@3**（同一 holdout）；配对单位=轨迹；族聚类 bootstrap；Holm 校正（约 10 个主比较）。
- test（7,935）用于功效与稳定性；holdout 用于官方可比性；两边都报。
- 若在 holdout 上 CI 过宽（216 条，±5–8pp），主结论以 test 为准、holdout 作一致性检查。

## 10. 版本与复现注意

- 官方 LLMJudge 是 GPT-4.1-mini，5 步窗口；与我们的 GPT-6 Luna 不同，不能混为同一行。
- 官方 detector 的数字来自其 release 版本；我们复跑要固定 commit 与依赖，并保存原始输出。
- CCD 的 checklist 生成若用 LLM，需记录模型/版本/prompt/token 成本；若用 Jev，记录问题与概率。
