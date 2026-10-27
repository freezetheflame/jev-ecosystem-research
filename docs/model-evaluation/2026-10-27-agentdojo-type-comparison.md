# AgentDojo 500 条：Jev 1.14 单问题三种 type 配对

记录日期：2026-10-27。状态：**exploratory / complete**。这是已有 Jev 工作区观测的导出，不是发布时重新运行；证据是静态动作分类，不是完整 AgentDojo agent 执行或防护 ASR。

## 1. 目的、数据与数量

比较相同两端定义下 choice、noul、score 的输出差异。唯一变化是 type、其所需 criteria 结构及对应解析；模型、state、授权 rubric、样本、阈值保持一致。没有在本批标签上选择阈值。未预定最小等效界或统计功效，因此不宣称三者等效或稳定领先。

数据：本地 TS-Bench 收录的 AgentDojo S4 动作片段，共 1,220 条（352 正、868 负）。按 `source_id × label` 比例分层，seed=20261027，抽 500 条。来源文件 SHA、精确 UID/标签、state 分片 hash 和完整 questions 见[公开样本清单](../../data/workspace-evidence/2026-10-27-agentdojo-types/sample-manifest.json)。上游 commit 未由本轮 manifest 固定，记 unknown；本地数据文件 hash 是这次版本锚点。不是官方 train/test 盲测划分；历史暴露未按任务族完整审计，按开发/探索证据处理。

| 套件 | 危险动作 | 安全动作 | 合计 |
|---|---:|---:|---:|
| banking | 11 | 24 | 35 |
| slack | 8 | 34 | 42 |
| travel | 8 | 64 | 72 |
| workspace | 117 | 234 | 351 |
| 合计 | 144 | 356 | 500 |

统计单位是带任务、工具、历史和待执行动作的静态片段，正类=`outcome_unsafe=1`。与本仓库 Mode B 的判断目标相近，但没有执行阻断；主 Agent/episode、clean/attack 变体、utility 与 ASR 均不适用。未继承完整轨迹标签充当前缀标签。

原始文本、完整展开的 state 和原始响应/失败日志保留在来源工作区，不随本仓库再分发：TS-Bench 来源无明确再分发许可。公开的是首方汇总、样本索引/哈希与请求 rubric。不能从本导出单独独立复判原始标签；标签来自上游，没有额外人工金标准审核。

## 2. 模型、请求与有效参数

- 请求与所有成功响应模型均为 `jev-1.14.0`；provider=TypeSafe，endpoint=`https://api.typesafe.ai/v1/systemone`。
- profile=`jev-stage-s4-v2`，完整 instructions/criteria 已保存。state 沿用来源 `wrap_files` 和 serialized builder，不包含 gold。
- 每请求一个 question；choice 为 safe/unsafe，noul 为 false/true，score 为 `[safe,unsafe]` 两级 0..1。noul 增加了 criteria，因此不是历史无 criteria 实验的直接复测。
- choice 判定用原生 choice，排序用 P(unsafe)；noul/score≥0.5 判危险。choice 恰好概率平局时保留返回类别，不强制改判。confidence 不作风险分。
- 分片 48,000 字符、重叠 2,000，风险/判定取 max。495 条单片、5 条两片；全来自 workspace。原始单轮计划 1,515 个分片请求，而非 1,500。
- 密钥通过环境变量选择，值不入日志。成功网络路径为显式本地 HTTP 代理；端口只说明本次部署，不构成通用服务配置。
- 首轮最多四并发、任务顺序用固定本地 seed 打散；补测最多两并发。超时 30 秒，临时网络错误及 429/500/502/503/504/529 最多重试两次，退避 1、2 秒。无单独响应缓存。
- 无 long-context header；未发送 temperature、top_p、sampling seed、max_tokens 等参数，服务端默认 unknown，不将本地 seed 当模型 seed。
- 原环境为 Windows / PowerShell / Python；逐项解释器、依赖锁和硬件版本未保存在本轮 manifest，记未完整记录。服务端算力/能耗 unknown，本地计算未计价。

此前 1.13/1.14 直连出现 451，7892 连接被拒；该轮成功配置与这些失败先导分开保存。费用/时间主表只覆盖 7890 上的成功配置首轮及补测，不含更早连接诊断。

## 3. 分类结果与配对差异

三臂共同成功 500/500。每臂 144 正 / 356 负，阈值固定 0.5：

| type | TP | FN | FP | TN | Accuracy | Recall | FPR | F1 | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| choice | 142 | 2 | 7 | 349 | 98.2% | 98.6% | 2.0% | 0.9693 | 0.9975 |
| noul | 142 | 2 | 8 | 348 | 98.0% | 98.6% | 2.2% | 0.9660 | 0.9986 |
| score | 142 | 2 | 9 | 347 | 97.8% | 98.6% | 2.5% | 0.9627 | 0.9984 |

全部计数满足 TP+FN+FP+TN=500。precision、Wilson recall/FPR 区间及逐套件结果见[机器可读汇总](../../data/workspace-evidence/2026-10-27-agentdojo-types/summary.json)；FNR=FN/144、specificity=TN/356，可直接重算。

| A → B | 判定不一致 | A 错 B 对 | A 对 B 错 | Accuracy(B)−Accuracy(A) | 95% 配对 bootstrap 区间 |
|---|---:|---:|---:|---:|---|
| choice → noul | 3/500 | 1 | 2 | −0.2pp | [−1.0pp, +0.4pp] |
| choice → score | 2/500 | 0 | 2 | −0.4pp | [−1.2pp, 0.0pp] |
| noul → score | 3/500 | 1 | 2 | −0.2pp | [−0.8pp, +0.4pp] |

在这批数据上分类差异小，choice 误报少 1–2 条，noul 的 AUROC 略高。没有同请求重复来分离服务噪声；2,000 次 bootstrap 的单位是片段，不是轨迹/任务族聚类；未做多重比较调整。区间含零不证明等效，且不支持把两级 score 外推到多级 rubric。

## 4. 成功率、时间与 API 费用

| 数量 | 值 |
|---|---:|
| 唯一样本 / 计划 sample-type cell | 500 / 1,500 |
| 首轮成功 / 失败 cell | 1,470 / 30 |
| 单独补测评估 / 最终失败 cell | 30 / 0 |
| 总 cell 评估次数（含补测） | 1,530 |
| 网络尝试 / 成功返回 / 失败尝试 | 1,628 / 1,515 / 113 |
| 首轮 cell 成功率 / 补齐后的完成率 | 98.0% / 100.0% |
| 按网络尝试的成功率 | 93.06% |

北京时间 2026-10-27 **15:22:17.228480 至 15:40:22.384255**，第一条开始到最后补测完成历时 **1,085.155775 秒 / 18.09 分钟**。含网络、代理、分片、解析、退避与补测间隔；不含启动准备和报告生成。它是请求阶段历时，不是服务端推理性能。原历史入口未激活 monitor，无 monitor run ID；不追造遥测。

| type | 执行 cell 次数 | 输入 token | 输出 token | 估算 USD | Mean ms | P50 ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| choice | 510 | 1,555,271 | 17,675 | 0.065321 | 2,660.7 | 2,167.7 | 3,189.3 |
| noul | 510 | 1,547,191 | 12,120 | 0.064982 | 2,655.8 | 2,174.7 | 2,990.0 |
| score | 510 | 1,547,191 | 10,605 | 0.064982 | 2,753.7 | 2,234.7 | 3,492.2 |
| 合计 | 1,530 | 4,649,653 | 40,400 | **0.195285** | 2,690.0 | 2,198.9 | 3,359.3 |

时间分布包含首轮失败评估和补测，N=每臂510；效果汇总中的 latency 只针对最终500个有效 cell，两种口径不能混称。

按[官方 1.14 定价](https://docs.typesafe.ai/models)（2026-10-27 核实）输入 $0.042/M、输出免费，已知 API 估价为 **$0.195285426**。113 次失败尝试没有 usage，可能产生的账单无法核实；实际 API 账单 unknown。没有新主 Agent、攻击生成或模型判分调用；本地计算未计价，不将 API 小计称为完整计算成本。

## 5. 复现、来源与核对

原始执行入口为来源工作区 `bench.type_compare`，后以 `bench.type_compare_repair` 原配置补齐，`bench.type_compare_resources` 离线统计。源实现与导出版本哈希见[源码清单](../../framework/source-manifest.json)，旧 manifest 的实现 SHA 单独保留；新导出代码不与旧 run 混写。

```powershell
# 来源工作区的历史命令形状；已有输出请勿覆盖。
python -m bench.type_compare --model jev-1.14.0 --key-name TYPESAFE_API_KEY2 --proxy http://localhost:7890 --limit 500 --out reports/<new-run-id>
python -m bench.type_compare_repair --out reports/<new-run-id>
python -m bench.type_compare_resources --out reports/<new-run-id>
```

导出入口、依赖准备、未来 monitor 接入与无 API 验证见[框架说明](../../framework/README.md)。本次迁移验证了七项离线测试、外部依赖哈希；没有新增付费验证。

本地已逐条核对：样本/state hash、返回模型、响应重解析、补测父记录、最终1,500个 cell 和独立重算分类指标。证据见[verification](../../data/workspace-evidence/2026-10-27-agentdojo-types/verification.json)、[补测审计](../../data/workspace-evidence/2026-10-27-agentdojo-types/repair-audit.json)、[时间费用](../../data/workspace-evidence/2026-10-27-agentdojo-types/resources.json)、[导出 lineage](../../data/workspace-evidence/2026-10-27-agentdojo-types/export-lineage.json)。这些是结构与计算核对，不是标签真实性、账单或跨机器模型确定性的保证。
