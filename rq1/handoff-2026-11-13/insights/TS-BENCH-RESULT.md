# TS-Bench 上的 CCD 尝试：负结果与真实杠杆（2026-11-13）

问题：TS-Bench（执行前动作安全）上 LLM 比 Jev 系强，CCD 的分解思路能不能提升它？

结论：**不能（至少当前设计不行）。** 单动作输入的 TS-Bench 与长轨迹的 StepShield 不同：Jev 的单问题问法本来就匹配；
把判断拆成 6 个原子探针再用 max 聚合会显著变差；用校准的 logistic 组合只有 +0.018 AUC（95% CI 含 0），
不是统计显著的提升。TS-Bench 的真正杠杆是**操作点校准 + 分来源报告**，不是分解。

## 1. 先看差距到底在哪

Jev 单问题（TS-Bench，5,401 可判分）：TPR 45.5% / TNR 98.3% / MCC 0.565。
按来源拆：

| 来源 | n | Jev TPR | Jev TNR | Jev MCC | GPT-6 MCC | Claude MCC |
|---|---:|---:|---:|---:|---:|---:|
| asb-traj | 3,765 | 0.323 | 0.984 | 0.455 | **0.652** | 0.644 |
| agentdojo-traj | 1,220 | 0.790 | 0.990 | 0.833 | **0.923** | 0.660 |
| agentharm-traj | 416 | 0.567 | 0.947 | **0.554** | 0.432 | 0.422 |

- 差距主要集中在 **ASB（合成轨迹，占 70% 可判分）**；在 AgentHarm-traj 上 Jev 反而赢 GPT。
- Jev 的操作点极保守：原生 FPR 只有 1.7%；到 FPR 14.1%（GPT 的原生 FPR）时 TPR = 75.5%，与 GPT 的 87.2% 差 **11.7pp**，不是表面上的 42pp。
- 单独校准阈值（全 split）就能把 MCC 从 0.565 提到 **0.619**（thr≈0.30）——这是免费的、真实的增益，但仍低于 GPT 的 0.699。

## 2. 试过的三种"提升"

### 2.1 多模型概率组合（离线，零调用）

| 组合 | AUC | MCC（最优阈值） | TPR@FPR14.1% |
|---|---:|---:|---:|
| Jev 单问题 | 0.906 | 0.619 | 0.755 |
| d3mini | 0.878 | 0.557 | 0.696 |
| kev | 0.831 | 0.495 | 0.544 |
| mean(Jev,d3mini) | 0.902 | 0.621 | 0.754 |
| rank-mean(Jev,d3,kev) | 0.899 | 0.609 | 0.757 |

→ 组合几乎不涨：三个模型的错误高度相关，瓶颈不在模型随机性。

### 2.2 工具名/关键词规则（离线）

"工具名含 attack/tamper/exfiltrat/... 就判 unsafe"：全 split MCC 0.341（ASB 0.431），只解释 **172/889** 的 Jev 漏检。
→ TS-Bench 不是单纯工具命名捷径；恶意动作也会用正常工具 + 恶意参数。

### 2.3 TS-CCD：6 个原子探针（真实调用，600 条 pilot）

探针：history_injection（历史是否含改目标的指令）、goal_hijack（动作是否服务注入指令）、tool_purpose（工具是否恶意用途）、
argument_risk（参数是否触敏感数据/目标）、direct_harm（执行是否直接造成伤害）、not_justified（是否超出用户请求）。

| 方法（test n=280） | recall | FPR | MCC |
|---|---:|---:|---:|
| 单问题（dev 校准阈值） | 0.565 | 0.069 | **0.552** |
| TS-CCD max 聚合 | 0.609 | 0.309 | **0.287** |
| 单问题 + 6 探针 logistic 组合 | 0.576 | 0.053 | **0.588** |

统计：
- max 聚合：明显更差（FPR 0.309），因为每个原子探针都是高召回弱判断，OR 逻辑把误报放大。
- logistic 组合：AUC 0.886→0.903，但 **AUC 差的 95% CI = [−0.009, 0.044]（含 0）**；McNemar **p=0.54**。
- 分来源：ASB MCC .479→.509（TPR 降、FPR 降）；AgentDojo .889→.960；AgentHarm .397→.498，都是小样本、不显著。

## 3. 为什么分解在 StepShield 有用、在 TS-Bench 的单步口径下没用（轨迹口径见 §6）

- StepShield 的输入是**长前缀**（8–12 步、几千 token），一个复合问题必须把多步证据压成一句；逐步分解能恢复被丢的证据。
- TS-Bench 的输入已经是**压缩好的单动作视图**（user_request + history + tools + candidate_action），单问题与这个接口天然匹配；
  再加 6 个原子判断只是增加误报，没有新增信息。
- 换句话说：**CCD 的适用条件是"判断单元跨越了太多证据"**；TS-Bench 不满足这个条件。

## 4. 对论文的建议

TS-Bench 上可以写的是：
1. **操作点修正**：Jev 在匹配 FPR 下与 GPT 差约 12pp，而不是原始 TPR 的 42pp；MCC 校准后 0.565→0.619。
2. **分来源**：差距集中在 ASB 合成轨迹；AgentHarm-traj 上 Jev 赢 GPT，AgentDojo 差距较小。这是重要的 construct-validity 结论。
3. **负结果**：原子探针分解在单动作判断上无显著收益（AUC CI 含 0，McNemar p=0.54），说明"分解"不是通用药；它依赖判断单元的长度/复合程度。
4. 不要把"TS-CCD"写成方法贡献；如果坚持要试，下一步只能是**任务特定的数据流/授权探针**（例如 tool schema + 参数目标分析），而不是通用 6 问。


## 6. 口径更正：TS-Bench 是“轨迹来源、单步评测”

前面第 1–5 节的结论只适用于**单步 Mode B 口径**。需要澄清两件事：

- **数据来源是轨迹**：TS-Bench 从 AgentHarm / AgentDojo / ASB 的轨迹里抽步骤，item_id 编码为 文件:轨迹号:步号:全局号（例如 asb-traj/OPI_attack_success.json:0:1:1）。原始轨迹结构**可恢复**。
- **评测单元是单步**：每个 item 是“用户请求 + 前缀历史 + 工具说明 + 一个候选动作”，标签是“这个候选动作是否 unsafe”（Mode B，执行前动作安全）。StepShield 才是轨迹级（每个前缀判一次、到首次告警步），ATBench 是完整轨迹审计。

按 item_id 重新分组后的实际结构（7,182 步）：

| 来源 | 轨迹组 | 多步组(>=2) | 多步且含 unsafe | 多步且全 safe | 步数 |
|---|---:|---:|---:|---:|---:|
| ASB OPI | 1,105 | 1,080 | 373 | 0 | 2,509 |
| ASB DPI | 1,228 | 448 | 147 | 0 | 2,293 |
| AgentDojo workspace | 474 | 256 | 185 | 71 | 855 |
| AgentHarm harmful | 72 | 71 | 56 | 0 | 525 |
| AgentHarm benign | 125 | 56 | 0 | 56 | 206 |
| AgentDojo banking/travel/slack | 115 | 87 | 56 | 31 | 365 |
| ASB attack_failure | 257 | 95 | 0 | 95 | 429 |
| **合计** | **3,376** | **2,093** | **817** | 253 | 7,182 |

所以：

1. 之前“TS-CCD 在 TS-Bench 上无显著收益”的结论，**只说明单步 Mode B 口径下分解不划算**；它**不能**推出“轨迹口径下也不行”。
2. 正确的做法是把 TS-Bench **重聚合成轨迹级 episode**：按（文件, 轨迹号）分组、按步号排序、去重、定义派生轨迹标签，再做逐步扫描 + 首次告警。
3. 这才是检验“CCD 是否适用于 TS-Bench”的正确实验；之前的单步负结果应改写成“单步口径下的负结果”，而不是“TS-Bench 不适用”。

### 6.1 轨迹级重评测设计（待做）

- **分组**：item_id 前缀（文件, 轨迹号）；步号排序；同一步的多个变体按动作文本去重（保留一个或取平均，预注册规则）。
- **标签**：轨迹 rogue = 组内存在 gold=1 的步；全 gold=0 的组为 safe；含 unknown(0.5) 的组按预注册规则排除或单列。**这是派生标签，必须声明。**
- **检测**：逐步扫描；首次 score >= theta 即告警；theta 在 dev 组上校准。
- **指标**：轨迹级 recall/FPR、告警步与首个 unsafe 步的关系（提前/正好/滞后）、平均 lead。
- **对比**：单问题逐步扫描 vs CCD 逐步扫描；同轨迹配对；按来源分层。
- **样本**：817 个含 unsafe 的多步组 + 253 个多步全 safe 组；pilot 取 150–200 组（约 400–600 步），成本约 $0.05。
- **风险**：TS-Bench 的“轨迹”中位只有 2 步，且每个 item 的 history 已含前缀；CCD 在 StepShield 上的优势来自 8–12 步长前缀，这里可能有限。必须用 pilot 判断，不能先验假设。

### 6.2 文件

- [tsbench_groups2.py](tsbench_groups2.py)：按 item_id 重建轨迹组的统计（3,376 组 / 817 组含 unsafe）。
## 5. 文件

- [run_ts_pilot.py](run_ts_pilot.py)：TS-CCD 600 条 pilot（真实 Jev 调用，6 探针）。
- [tsccd_analysis.py](tsccd_analysis.py)：max/mean/logistic 组合与分来源评估。
- [tsccd_stats.py](tsccd_stats.py)：McNemar 与配对 bootstrap。
- [tsbench_diag2.py](tsbench_diag2.py)：分来源、工具名规则、Jev ROC。
- 结果：runs/tsccd-pilot-600/results.json。
