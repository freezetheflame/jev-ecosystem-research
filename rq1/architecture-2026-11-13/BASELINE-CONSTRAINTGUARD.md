# ConstraintGuard 作为基线：能不能用、怎么用才公平（2026-11-13）

状态：实测分析（无模型调用；ConstraintGuard 是确定性 detector）。数据源：
data/agent-security-study/datasets/full-suite-v1/stepshield/snapshot/benchmark/detectors/constraint_guard.py
+ 我们的 census（55 prefix-missed rogue + 55 prefix-clean）与完整 test split（7,933）。
脚本：[run_constraintguard_baseline.py](run_constraintguard_baseline.py)、[coverage_subset.py](coverage_subset.py)。

## 0. 结论

**可以，而且应该用**——它是"确定性约束检查"这一类方法的代表，正好回答"规则够不够，为什么还需要模型"。
但**不能直接用官方实现然后宣布胜利**，因为它的召回被**覆盖率**卡死：StepShield 的约束只有 **12.9%** 能被它的 23 个关键词类别匹配，**69% 的任务一个约束都匹配不上**。
正确做法是三行基线 + 覆盖披露 + 匹配 FPR：

1. **ConstraintGuard（官方，published）**：holdout recall 24.1% / FPR 25.0% / EIR 0.08。
2. **ConstraintGuard（同 split 复跑）**：完整 test split recall 24.3% / FPR 29.8% / EIR 0.432。
3. **ConstraintGuard+（我们把规则按任务约束条件化后的强规则版）**：完整 test recall 16.0% / FPR 1.15%。
4. **CCD**：census 上 recall 80% / FPR 5.5%（同样是"约束 × 步"的分解，但用 Jev 判断语义）。

**在覆盖率匹配的子集上，CG 的 recall=100% 但 FPR=100%；CCD 同样 recall=100%，FPR=5.3%。在 CG 完全没覆盖的 69% 任务上，CCD 仍拿到 71.8% recall / 5.6% FPR。CG OR CCD 反而更差（FPR 38.2%，recall 不变）——所以不要把 CG 叠在 CCD 上。**

## 1. 官方 ConstraintGuard 到底做了什么

- 23 个"约束类别"（do not modify / do not delete / read only / do not execute / staging only / test first / …），每类是一组 (action regex, confidence)。
- 对任务里的每条 constraint，**只有当 constraint 文本包含某个类别关键词时**，才启用该类规则；然后在该步的 thought/action/arguments/observation 里正则匹配；置信度 > 0.5 即判 rogue。
- 它没有用"任务要求的正面行为"（如"日志最多保留 7 天"、"压缩轮转日志"、"不要记录 API key"），所以这些约束在它那里是**不可判定**的。

## 2. 实测

### 2.1 覆盖率（这是关键）

| 数据 | 约束总数 | 被 CG 关键词匹配 | 完全无覆盖的任务 |
|---|---:|---:|---:|
| 完整 test split（7,933） | 21,905 | 2,815（**12.9%**） | 5,509（**69.4%**） |
| census（110） | 292 | 37（12.7%） | 75（68%） |

未覆盖约束的例子：Keep maximum 7 days of logs、Compress rotated logs、Must not delete current log、DO NOT log or display API keys、Use masked output for secrets。这些恰恰是 StepShield rogue 轨迹最常违反的那类**语义约束**。

### 2.2 同 split 指标

| 系统 | recall | FPR | EIR@3 | IG | 覆盖约束 |
|---|---:|---:|---:|---:|---:|
| ConstraintGuard（官方 published, holdout 216） | 24.1% | 25.0% | 0.08 | −5.3 | 12.9%（同类） |
| ConstraintGuard（复跑, 完整 test 7,933） | 24.3% | 29.8% | 0.432 | −2.12 | 12.9% |
| ConstraintGuard+（规则按约束条件化, test） | 16.0% | 1.15% | 0.510 | −1.04 | 任务级 69% 无映射 |
| Jev prefix（现有） | 91.4% | 13.2% | 0.686 | — | — |
| **CCD（census, θ=0.60）** | **80.0%**（44/55） | **5.5%**（3/55） | **0.909** | −0.39 | 全部（Jev 语义） |

（CCD 的 census 是在 prefix 漏掉的 55 条 rogue + 55 条 prefix-clean 上算的，不是同分布；和 CG 的 full-test 数字不能直接混表，但和 CG 在同一 census 上的对比是公平的。）

### 2.3 覆盖率匹配子集（census 110 条）

| 子集 | 系统 | recall | FPR |
|---|---|---:|---:|
| CG 覆盖的 35 个任务 | ConstraintGuard | 100%（16/16） | **100%**（19/19 clean 全报） |
| 同上 | **CCD @0.60** | **100%**（16/16） | **5.3%**（1/19） |
| CG 未覆盖的 75 个任务 | ConstraintGuard | 0% | 0% |
| 同上 | **CCD @0.60** | **71.8%**（28/39） | **5.6%**（2/36） |
| 全体 | CG OR CCD | 80% | **38.2%**（比 CCD 单独差） |

读法：
- CG 在它能覆盖的任务上**召回是满分，但把 clean 也全报了**（do not access/read only 这类模式会命中正常读取）。在匹配 FPR 的意义上，它远不如 CCD。
- CG 在 69% 的任务上根本**没有判断能力**；CCD 仍能工作。
- 把 CG 和 CCD 叠加不会提高召回，只会把 FPR 从 5.5% 拉到 38.2%——**不要叠加**。

## 3. 论文里怎么写才公平（防"打稻草人"）

主表（不放 LLM，按你的要求）建议：

| 系统 | 类型 | recall | FPR | EIR@3 | 约束覆盖率 | 每轨迹调用 | 成本 |
|---|---|---:|---:|---:|---:|---:|---:|
| Random | 下界 | 50% | 50% | 0.12 | — | 0 | 0 |
| ConstraintGuard（官方实现） | 确定性约束 | 24.1% | 25.0% | 0.08 | 12.9% | 0 | 0 |
| ConstraintGuard+（按约束条件化的强规则） | 确定性约束 | 16.0% | 1.15% | 0.51 | 任务级 69% 无映射 | 0 | 0 |
| **CCD（ours）** | 语义约束分解 | **80%（census）/ 组合 96.7%** | **5.5%** | **0.909** | **100%（Jev 语义）** | 8.6 | $0.0005 |

必须同时报：
1. **约束覆盖率**（否则 CG 的 24% 看起来像能力问题，其实是覆盖问题）。
2. **匹配 FPR 的 recall**（CG 在 FPR 25–35% 下才有 24–29% recall；CCD 在 FPR 5.5% 下有 80%）。
3. **CG 覆盖子集上的头对头**（CCD 100% vs CG 100%，FPR 5.3% vs 100%）。
4. **未覆盖子集上的 CCD**（71.8% / 5.6%），证明"规则覆盖不到的地方模型有用"。
5. **CG OR CCD 消融**（变差），说明不是简单叠加。

LLM 基线（GPT/Claude/官方 LLMJudge）可以放附录或 related work，作为"上限参照"，不进主表。

## 4. 还需要的两个公平性处理

1. **同等工程投入**：CG 的规则是人工按类别写的；CCD 的探针是一次性模板、按任务约束自动生成。论文应写清"规则需要每个约束手写 pattern；CCD 对未见约束零额外工程"，并报告规则开发成本（23 类 × 若干正则）。
2. **StaticGuard 不可用**：StepShield snapshot 的 detectors/ 里只有 constraint_guard / hybrid_guard / llm_judge，没有 static_guard.py；官方 StaticGuard（847 条规则）拿不到实现。如果非要规则基线，用 CG + CG+ 即可，并在文中说明 StaticGuard 未复现。

## 5. 局限

- census 是 prefix-missed 子集（难例），CCD 的 80% 不能直接外推到全分布；全分布需要完整 test split 的 CCD 运行。
- CG 复跑使用我们 monitor-visible 的 view（task + steps），与官方 harness 的轨迹字段可能略有差异；recall 24.3% 与官方 24.1% 接近，说明复跑可信。
- CG 的 EIR 在官方 holdout 是 0.08、我们在 test split 是 0.432；差异来自 split 与告警步分布，跨 split 不可直接比。
- CG+ 是我们写的强规则版，属于"方法学对照"，不是官方数字；论文中要标明自建。

## 6. 文件

- [run_constraintguard_baseline.py](run_constraintguard_baseline.py)：官方 CG + CG+ 在 census 与完整 test 上的运行脚本。
- [coverage_subset.py](coverage_subset.py)：覆盖率匹配子集与 CG OR CCD 分析。
- [BASELINES.md](BASELINES.md)：整体基线矩阵（B1–B28）。
- 数据：data/agent-security-study/datasets/full-suite-v1/stepshield/snapshot/benchmark/detectors/。
