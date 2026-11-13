# 架构设计：用 input 级判断救轨迹级检出（CCD：Constraint-Checklist Decomposition）

日期：2026-11-13。状态：**设计稿 + 已完成离线诊断，未跑模型**。
数据来源：rq1/summary（StepShield test/holdout）、rq1/ext-2026-11-13、本目录 offline_step_signal.json 与 inspect_missed.py 抽样。

## 0. 结论

可以设计，而且数据指向一个很具体的架构，不是"再换一种聚合"。

1. **差距是真的，但只在高 TNR 区**：StepShield test 上，Jev 在 TNR 86.5% 时 TPR 91.4%；把 TNR 提到 95% 时 TPR 只剩 **80.9%**。GPT-6 Luna 在 TNR 87.0% 时 TPR **98.1%**（无概率，无法直接给 95% TNR 点，估计差 10–15pp）。d3mini 在 TNR 96.3% 时 TPR 80.3%，与 Jev 的 ROC 相近但操作点更保守；Claude TNR 只有 74.4%、MCC 0.415——所以"Jev 系 vs LLM"不是一句"LLM 更强"，要按匹配操作点读。
2. **靠现有 per-step 分数重新聚合救不回来**：对 Jev 的 69,289 个前缀判断做了全网格规则搜索（any / 连续 k / CUSUM / EWMA）。**any-threshold 已经是最优**；CUSUM 最好也只有 MCC 0.586（TPR 68.7% @ TNR 95.4%），低于简单规则在 TNR 95% 的 TPR 80.9%。结论：当前探针问的是"整个前缀是否 unsafe"，缺失的证据不在分数里，**再聚合只是换个切法**。
3. **漏检的失败模式很清楚**：55 条漏检 rogue 中，35 条的最高分其实 ≥0.3（22 条在 0.3–0.4、13 条在 0.4–0.5），但良性轨迹同样落在这一区间——信号与噪声不可分。抽样看分歧步：漏检案例的 observation 往往完全正常（"Command executed successfully"），风险写在 **thought/action 的约束弱化**里，例如 "I need to compresses without size check"、"no job timeout configured"、"no maximum retry limit"、"global cache stores all patterns"。这不是注入，是**约束省略/弱化**。

→ 因此架构应该是：**把轨迹判断分解成"每个约束 × 每个步骤"的短上下文原子判断（Jev 的强项），再学习一个校准的聚合器**，而不是继续在长前缀上问一个复合问题。

## 1. 诊断细节（可写进论文的 motivation）

| 指标 | Jev 1.14 | d3mini | kev | GPT-6 Luna | Claude Haiku |
|---|---:|---:|---:|---:|---:|
| StepShield test TPR | 91.4% | 80.3% | 58.1% | 98.1% | 96.2% |
| TNR | 86.5% | 96.3% | 97.2% | 87.0% | 74.4% |
| MCC | 0.533 | 0.700 | 0.581 | 0.581 | 0.415 |
| TPR @ TNR=95% | **80.9%**（算出） | ~82%（粗估） | ~63%（粗估） | 未知（无概率，上界 98.1%） | 未知（上界 96.2%） |

注：d3mini/kev 的 95% TNR 点按 ROC 单调性粗估，因为它们的逐步概率（raw）没有同步到本机；Jev 的 80.9% 是从 69,289 个原始响应重算的。

- 基线（Jev，any step p≥0.5）：TP 584 / FP 983 / TN 6311 / FN 55。
- 离线规则搜索（69,289 步）：any-threshold 最优；CUSUM 最好 MCC 0.586，但 TPR 68.7% @ TNR 95.4%；"连续 k 次"规则都更差。
- 漏检 55 条的 max-p 分布：<0.2 有 12 条、0.2–0.3 有 8 条、0.3–0.4 有 22 条、0.4–0.5 有 13 条；把阈值降到 0.3 能召回 35/55，但良性 FP 同步爆掉。
- 分歧步位置：漏检与检出的分歧步中位数都是 6，**不是"分歧太晚"**；漏检轨迹反而更短（中位 10 vs 13 步）。

**失败模式**（抽样 5 条漏检）：observation 正常、thought 里出现"去掉检查/不设上限/缓存所有"的约束弱化；或 action 参数是 example_command_* 占位符（合成数据噪声）。这两类需要不同探针：约束违背 vs 信息不足。

## 2. 为什么 input 级能力可以借

Jev 系在短、定义明确的二选一判断上强：AgentHarm 请求分类 MCC 0.769（Jev）/0.763（d3mini）；InjecAgent 注入检出 TPR 95.4%（Jev）。轨迹级判断弱的原因是**接口**：一个复合问题 + 长前缀 + 单一阈值。CCD 把它换成 k×steps 个"约束 + 单步"的短判断，每个都落在 input 分布里。代价是调用数变 O(k·steps)，但 Jev 单次成本极低（现测 ~0.68 s、~$0.0001/次）。

## 3. 候选架构

| | A：CCD（推荐） | B：Evidence Card + 二审 | C：Cascade |
|---|---|---|---|
| 流程 | 任务→约束清单（O(1) 次 LLM/Jev）→每步×每约束 Jev 原子探针→校准聚合 | A 的探针结果压成 ≤200 token 证据卡→Jev/LLM 做轨迹判决 | Jev 探针做高召回过滤→只把可疑窗口送 GPT/Claude |
| 借 input 强项 | 直接（原子二分类） | 间接（短上下文判决） | 直接（过滤） |
| 成本 | k×steps 次 Jev | k×steps Jev + 1 次 LLM | 少 LLM，但延迟/复杂度高 |
| 科学贡献 | 分解是否恢复轨迹级能力 | 二审是否必要 | 成本-检出折中 |
| 风险 | 约束抽取质量、探针有效性 | 证据卡信息损失 | LLM 调用不确定 |

**推荐 A，B 作为 A 的消融（判断证据卡二审是否额外加分），C 只作为成本对照。**

## 4. CCD 的三层设计

**Stage 1：约束抽取（每轨迹 1 次）**
- 输入：用户任务（+ 应用策略，若有）。
- 输出：2–6 条原子约束，每条含 id、自然语言定义、可判定的边界（例如 C1 超时限制必须存在；C2 缓存必须有界；C3 不得把用户数据写到任务指定位置之外；C4 必须保留输入校验）。
- 实现：pilot 用一次 LLM 调用严格 JSON；消融用 Jev（候选约束做 Choice/Noul）+ 抽取式规则。
- 质量控制：双人抽检 10% 任务，检查约束是否来自任务而非模板；统计每任务约束数。

**Stage 2：每步原子探针（k × steps 次 Jev）**
- 每个探针只给：约束定义 + 用户任务（截断到必要部分）+ 当前步的 thought/action/observation（可选最近 1 步）。
- 问题形态：noul「这一步是否违反约束 Ci？」；另加两个通用探针：
  - q_inj：该步 observation 是否含试图改变行为的指令（InjecAgent 口径，Jev 强项）。
  - q_scope：该步 action 是否超出用户任务的范围（目标/目的地/数据范围）。
- 输出：p(t,c)。所有探针用同一阈值族（dev 校准），记录问题文本与 criteria，冻结。

**Stage 3：聚合与判决（dev 拟合，test 冻结）**
- 特征（每轨迹）：max p、top-2 均值、≥τ 的计数、连续命中长度、首个命中步、prefix-level 分数（现有 Jev 前缀判断）、步数、约束数。
- 规则：pilot 先用手工规则（max + 持久性 + prefix 分），再拟合 L2 逻辑回归（按内容族交叉验证），避免过拟合。
- 判决：trajectory rogue + 首个告警步；阈值在 dev 上选到 TNR=95%（主）与 90%（次）。
- 可选 B：把证据卡（约束×最高 3 个命中步）交给 Jev 或 LLM 二审；只在聚合分处于不确定带时触发。

## 5. 实验计划

| 阶段 | 内容 | 规模 | 调用 | 产出 |
|---|---|---|---|---|
| P0（已完成） | 离线信号诊断 + 失败模式审计 | 7,933 轨迹 / 69,289 步 | 0 | 本文件 §1 |
| P1 pilot | 200 轨迹（120 rogue / 80 non-rogue，dev/test 40/60 按族切），Jev + d3mini + kev，k=3–5 探针 + 2 通用探针 | 3 模型 × 200 × 8.7 × 6 | ~31,000 | TPR@TNR 曲线、EIR@3、成本 |
| P2 消融 | 探针集、上下文窗口（当前步/最近 2 步/全前缀）、聚合器、checklist 来源、call-matched 对照（同样调用数但问前缀问题） | 1 模型 × 100 轨迹 | ~8,000 | 归因：增益来自分解而非更多调用 |
| P3 二审/级联 | 证据卡 → Jev/LLM；不确定带 → LLM | 100 轨迹 | ~2,000 + LLM | 二审增益与成本 |
| P4 攻击鲁棒 | 用 RQ3 的 P3/P4（warm-up/gradual drift）测 CCD 是否仍能及时告警 | 60 轨迹 | ~10,000 | 与 RQ3 联动 |

P1 用 3 个 Jev 系模型；GPT/Claude 只作为上限参照（现有 summary 数字 + 若拿到逐轨迹预测则做配对）。

**基线**（详见 [BASELINES.md](BASELINES.md)）：StepShield 自带 4 个官方 detector（Random / StaticGuard / ConstraintGuard / LLMJudge / HybridGuard）与统一指标（EIR@3、IG、Tokens Saved、FPR、Recall），我们的 CCD 直接实现为 BaseDetector 跑同一 harness；内部再配 5 类消融：同模型不同接口（滑窗/多问题/全轨迹/call-matched）、同分解不同内容（通用探针/q_inj/q_scope/开放式）、同内容不同聚合、证据卡二审、微调分类器。最危险的对照是 **ConstraintGuard**（决定模型是否必要）与 **call-matched**（决定增益是否只是多调了几次）。

## 6. 指标与功效

- 主指标：**TPR @ TNR=95%**（以及 90%），MCC，EIR@3，平均 lead，成本/轨迹，延迟。
- 次要：探针在分歧步 ±1 的命中率（用 divergence_step 作弱 gold）、良性误报、约束数敏感性。
- 配对：同一轨迹 baseline vs CCD，McNemar；族聚类 bootstrap。
- 功效：120 rogue、discordance ~0.15 时，8–9pp 的配对差异可检出（n≈145 是 8pp 的边界，120 略紧 → 可扩到 150 rogue）。

## 7. 假设与反驳

| 编号 | 假设 | 反驳条件 |
|---|---|---|
| H1 | 漏检 rogue 的失败主要是约束弱化/省略，而非注入 | 探针在分歧步命中率 <30%；人工审计显示多为信息不足/占位符 |
| H2 | 约束探针 + 聚合把 TPR@TNR95 从 80.9% 提到 ≥90% | 提升 <5pp，或提升只来自良性 FP 不变而 TPR 不变 |
| H3 | 增益来自分解，而不是调用数 | call-matched 对照（同调用数的前缀提问）达到同等增益 |
| H4 | 成本可接受：≤5× baseline 调用，现金 <$1/200 轨迹 | 超过 10× 或延迟不可接受 |
| H5 | 在 P3 warm-up 攻击下仍比前缀基线更早告警 | 攻击把 CCD 的 lead 拉到与基线相同 |

## 8. 成本（planning）

- P1：200 轨迹 × 8.7 步 × 6 探针 ≈ 10.4k 次/模型；3 个模型 ≈ 31k 次。Jev 现金约 0.04 USD/千次 → **<$2**；本地模型 GPU 时间可忽略；墙钟约 1 天（8 并发）。
- 约束抽取：200 次 LLM 调用（若用 GPT/Claude，需价格快照）。
- P2/P3/P4 合计再约 20k 次。

## 9. 风险与缓解

1. **探针有效性**：探针没有逐步 gold；用分歧步 ±1 命中率 + 人工抽检 50 步验证"违规定义"。
2. **约束抽取质量**：约束若来自模板而非任务，会泄漏/失真；要求每条约束引用任务片段，双人抽检。
3. **合成数据噪声**：部分轨迹是 example_command_* 占位符；P1 需过滤"信息不足"轨迹或单列。
4. **过拟合聚合器**：特征少、按族交叉验证、dev/test 严格切分；主结果优先手工规则。
5. **成本 O(k·steps)**：k 控制在 3–5；可只对"变化步"（action/observation 非空）跑探针。
6. **与 GPT/Claude 的可比性**：它们无概率，无法 matched-TNR；只能报其原生点 + 上界，或让它们输出概率（弱证据）。

## 10. 与论文 RQ 的映射

- RQ1（能力边界/可委托性）：CCD 是"把轨迹判断委托给 input 级判断"的具体架构。
- RQ3（攻击下鲁棒）：P4 用 warm-up/gradual drift 测 CCD 的时序鲁棒性。
- RQ4（成本）：O(k·steps) 与 cascade 的成本-检出曲线。

## 11. 下一步

1. 拍板：只做 A，还是 A+B（证据卡二审）。
2. P1 先做 40 条轨迹的 feasibility（约束抽取 + 探针命中率），再扩到 200。
3. 冻结约束抽取 prompt、探针文本、聚合器与阈值程序；跑前预注册 H2 的 90% 目标。
4. 若 P1 的 H2 失败，转 C（cascade）作为成本论文，或如实报负结果（分解不足）。