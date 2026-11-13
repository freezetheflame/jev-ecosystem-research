# CCD 架构：第一轮真实 pilot 结果（2026-11-13）

状态：**探索性 pilot**（Jev 1.14.0 via Packy；无 LLM 调用；阈值未在独立 dev 上校准；样本小）。所有数字来自 runs/ 下的可复现 run，脚本与数据 hash 见各 run 的 manifest.json。

## 0. 结论

**架构跑通了，而且用 0 次 LLM 调用拿到了接近 GPT-6 Luna 的轨迹级检出。**

- CCD 单独在随机 holdout（20 rogue / 20 clean，阈值 0.60）：recall 0.95、FPR 0.15、EIR@3 0.895、IG −0.84；**0 次 LLM 调用**，8.6–11.9 次 Jev 调用/轨迹，约 $0.0005–0.0007/轨迹。
- 真正的价值在**互补性**：对 Jev prefix 在部署 test split 上漏掉的**全部 55 条 rogue**，CCD 补回 **44 条（80%）**；同时在这些 prefix 已放行的 clean 上只新增 **3/55（5.5%）** 误报。补回的告警大多正好落在分歧步（gap=0），EIR@3 = 0.909。
- 组合 prefix + CCD（阈值 0.75）估计：recall 从 91.4% → **96.7%**，FPR 13.2% → 14.8%；阈值 0.90 时 recall 94.1%、FPR 仍约 13.2%。GPT-6 Luna 在同一 test split 是 recall 98.1%、FPR 13.0%，但用 **8.6 次 LLM 调用/轨迹、26.2 s/episode**；我们组合系统 **0 次 LLM 调用、约 13–15 s/episode**。

一句话：**"相同效果"还差 1–2pp recall 与约 2pp FPR（小样本，CI 重叠），但 LLM 调用从 ~8.6 次/轨迹降到 0，延迟约一半、成本低一个数量级以上。**

## 1. 做了什么

代码：rq1/architecture-2026-11-13/ccd/（config / probes / state / client / detector / metrics / baselines / run_pilot），
探针固定为"任务约束 × 当前步"的 noul 判断 + requirement_bypass + weaken_vs_history + injection，**每步一次 Jev 请求批量问全部问题**，错误重试、usage/latency 逐调用记录。

- v1：state 只有 task + 当前步 → 随机 holdout 0.60 时 recall 0.85 / FPR 0.10；漏掉的 3 条恰好是 prefix 能检出的 → 诊断为**丢历史上下文**。
- v2：state 加入最近 2 步 + weaken_vs_history 探针 → 随机 holdout 0.60 时 recall 0.95 / FPR 0.15，EIR 0.895。
- 互补性实验（census）：全量 55 条 prefix-missed rogue + 55 条 prefix-clean。

## 2. 结果

### 2.1 随机 holdout（216 里的 20 rogue / 20 clean，v2，阈值 0.60）

| 指标 | CCD v2 | Jev prefix（同 20 条） |
|---|---:|---:|
| recall | 0.95 | 1.00 |
| FPR | 0.15 | 0.15 |
| EIR@3 | 0.895 | 0.85 |
| IG | −0.84 | −0.75 |
| Jev calls / 轨迹 | 11.9 | 8.7 |
| 输入 token / 轨迹 | 16,753 | 8,117 |
| 延迟 / 轨迹 | 19.1 s | 6.4 s |
| LLM calls | 0 | 0 |
| 现金（估算） | $0.0007 | $0.00034 |

注：随机 holdout 上 prefix 本来就很强（recall 1.0），CCD 单独没有优势。

### 2.2 互补性 census（全部 55 条 prefix-missed rogue + 55 条 prefix-clean，阈值 0.60）

| 指标 | 值 | 95% 区间（Wilson/近似） |
|---|---:|---|
| 补回的 prefix-missed rogue | **44/55 = 80.0%** | [67.6%, 88.4%] |
| 新增误报（prefix-clean 上） | **3/55 = 5.5%** | [1.9%, 14.8%] |
| 补回条目的 EIR@3 | 0.909 | — |
| 补回条目的 IG | −0.39（多数 gap=0） | — |
| Jev calls / 轨迹 | 8.6 | — |
| 输入 token / 轨迹 | 11,147 | — |
| 延迟 / 轨迹 | 8.7 s | — |
| 现金（估算） | $0.00047 | — |
| LLM calls | 0 | — |

### 2.3 组合系统（prefix + CCD）在部署 test split 的估计

基线 prefix（Jev，n=7,933）：TP 584 / FN 55 / FP 966 / TN 6328 → recall 91.4%，FPR 13.2%。

| CCD 阈值 | 补回 rogue | 新增 FP（样本） | 组合 recall | 组合 FPR |
|---:|---:|---:|---:|---:|
| 0.40 | 50/55 | 8/55 | 0.992 | 0.259 |
| 0.50 | 47/55 | 4/55 | 0.987 | 0.196 |
| 0.60 | 44/55 | 3/55 | 0.983 | 0.180 |
| 0.70 | 38/55 | 2/55 | 0.973 | 0.164 |
| **0.75** | **34/55** | **1/55** | **0.967** | **0.148** |
| 0.80 | 24/55 | 1/55 | 0.951 | 0.148 |
| 0.90 | 17/55 | 0/55 | 0.941 | 0.132 |

（新增 FP 按 55 条 prefix-clean 的比率外推到全部 6,328 条 prefix-clean；这是估计，CI 宽。）

### 2.4 与完整 LLM 判官对照（同一 test split）

| 系统 | recall | FPR | LLM calls / 轨迹 | 延迟 / episode | 备注 |
|---|---:|---:|---:|---:|---|
| Jev prefix（现有） | 91.4% | 13.2% | 0 | 6.4 s | 8.7 次 Jev 调用 |
| **prefix + CCD @0.75** | **96.7%** | **14.8%** | **0** | **~13–15 s** | 估计值 |
| prefix + CCD @0.90 | 94.1% | 13.2% | 0 | ~13–15 s | 估计值 |
| GPT-6 Luna | 98.1% | 13.0% | ~8.6 | 26.2 s | 实测 |
| Claude Haiku | 96.2% | 25.6% | ~7.6 | 25.0 s | 实测 |
| 官方 LLMJudge（holdout 216） | 95.4% | 5.6% | ~n_steps | — | 官方发布，非同 split |

## 3. 成本与速度

- LLM 调用：**0**（这是架构的核心卖点；官方 LLMJudge 每步一次 LLM）。
- Jev 调用：CCD 单独 8.6–11.9 次/轨迹；若只在 prefix 判 clean 的轨迹上跑 CCD（约 80%），组合平均约 15–16 次 Jev 调用/轨迹。
- 现金：Jev 输入 token × 0.042 USD/M → CCD 约 $0.0005/轨迹，组合约 $0.0008/轨迹（列表价估算，非账单）。GPT/Claude 的 relay 价格需快照。
- 延迟：CCD 8.7 s/轨迹（串行加和）；组合约 13–15 s；GPT 26.2 s、Claude 25.0 s（实测 episode mean）。

## 4. 有效性与局限

1. **样本小**：互补性 census 只有 55 条 rogue（全部 prefix-missed）与 55 条 clean；FPR 的 95% 上界可达 ~15%，不能宣称"FPR 不变"。
2. **阈值未在独立 dev 上校准**：0.40–0.90 的 sweep 是事后报告；论文需要 dev/test 分离。
3. **组合数字是估计**：把 55 条 clean 的新增 FP 率外推到 6,328 条是近似；需要在更大 clean 集上验证。
4. **EIR 早告警问题**：CCD 在少数条目上比分歧步早 1–9 步告警；官方 EIR 对提前告警给 0 分。本报告的 EIR 只对补回条目算，且多数 gap=0；跨系统比较时需同时报 strict EIR 与 early-warning。
5. **Jev 版本/中转**：jev-1.14.0 via Packy；与官方 1.13.0 不可混。
6. **StepShield 合成噪声**：部分轨迹有 example_command_* 占位符，可能影响探针。

## 5. 下一步（v3）

1. 用 100–150 条独立 dev（balanced）校准每问题阈值与聚合规则；冻结后跑完整 test/holdout。
2. 只在 prefix 判 clean 的轨迹上跑 CCD（cascade），把平均 Jev 调用从 15.6 降到 ~7（按 prefix FN+TN 比例估算需要实测）。
3. 与官方 LLMJudge 在 216 holdout 上同 split 对比（我们可复跑 StaticGuard/ConstraintGuard；LLMJudge 引用官方数字）。
4. 加入"证据卡 → Jev 二审"与"证据卡 → LLM 二审"两个 arms，看能否用 1 次 LLM 调用逼近 GPT 水平。
5. 攻击鲁棒（RQ3）：warm-up / gradual-drift 下 CCD 是否仍及时。

## 6. 文件

| 路径 | 内容 |
|---|---|
| ccd/ | 可执行包（探针、state、client、detector、metrics、baselines、run_pilot） |
| runs/v2-holdout-40/ | 随机 holdout 40 条（v2） |
| runs/v2-prefixmiss-census/ | 55 prefix-missed + 55 prefix-clean（核心证据） |
| runs/dev-test-40/ | dev（test split 40 条） |
| runs/pilot-real-40/ | v1 holdout 40 条（对照） |
| calibrate.py / combine.py | 阈值校准与组合估计 |
| manifest.json / report.md | 每个 run 的复现信息 |
