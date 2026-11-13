# Jev 生态调研笔记

围绕 **Jev**（TypeSafe AI 于 2026-09-15 发布的 "System One" 决策模型）的一手调研记录，按研究问题组织为七个主题：模型生态与获取、产品应用与请求设计、模型评测与校准、路由机制与安全、对抗上下文复现、语义鲁棒性，以及 Agent 决策接入。

> **一句前提**：Jev 本身**没有开源**（闭源托管 API，不生成文本，只返回类型化答案 + 概率）。所以所谓"基于 Jev 的开源模型"，全部是**独立复现 + 接口兼容 + 微调制品**。

## 为什么这份记录可能有别于二手文章

核心榜单与项目状态尽量依据**一手原始资料**；新增文献调研区分论文作者报告、公开项目初步证据与本仓库实测，不把综述目录的二手数字当成复现结论：

- 榜单数据直取 **JevBench 原始结果 JSON**（`data/jevbench-v1.4.2.2-results.json`，622 KB，95 个系统全量），脚本见 `scripts/fetch_jevbench.py`
- 项目状态、star 数、许可证用 **GitHub API** 实测，不靠记忆
- 能实测的站点都实测过可达性

---

## 研究主题

完整报告、数据、脚本与推进状态见 [调研主题索引](docs/README.md)，新增材料遵循 [组织约定](docs/organization.md)。

| 主题 | 研究问题 | 当前阶段 |
|---|---|---|
| [模型生态与获取](docs/ecosystem/README.md) | 有哪些模型，怎样获取、调用及选型？ | 生态与许可调研；Microsoft-Decision-1 尚未独立实测 |
| [产品应用与请求设计](docs/applications/README.md) | 如何写 state、criteria、选项边界与操作阈值？ | 产品源码调研、RAG 场景分析与请求示例 |
| [模型评测与校准](docs/model-evaluation/README.md) | 固定任务下，各模型的质量、概率与性能如何？ | 本地 smoke、100 条安全任务配对 pilot |
| [路由机制与安全](docs/routing-security/README.md) | 候选集合、缓存与失败路径如何影响模型路由？ | 机制调研与研究议程 |
| [对抗上下文与 JevOut 复现](docs/adversarial-robustness/README.md) | 保持正确答案时，自适应背景能否诱导定向错误？ | 8 题与 40 题探索；观察翻转的语义有效性未确认 |
| [语义鲁棒性与概率一致性](docs/semantic-robustness/README.md) | 等价变化应稳定、关键变化应敏感，概率与操作是否一致？ | 全文与源码核查、安全研究结论、60 场景 pilot 协议；实验未启动 |
| [Agent 决策接入与 Mu](docs/agent-integration/README.md) | 判断模块接入后，是否改善实际任务与上下文效率？ | 本地源码、历史回测与桌面试用材料 |

[共享实验基础设施](docs/infrastructure/README.md)收录 API 客户端、端点配置与离线测试。每份报告有一个主归属，跨主题通过链接引用；文献、厂商数字、本仓库实测和待做方案分别标明。

报告位于对应主题目录；现有实验数据、脚本、配置和本地工程路径保持原位置，由主题索引关联。完整安全配对报告依赖相邻的 Jev 项目，Mu 和模型权重属于本地可选材料。


---

## 核心结论速览

> 以下为 JevBench v1.4.2.2 历史快照，不覆盖新发布的模型。**Microsoft-Decision-1 已纳入托管决策模型研究范围**，见[增量报告](docs/ecosystem/microsoft-decision-1.md)；其厂商数据不混入旧榜单，“泛化上限”等结论不直接外推到新模型。

**vLLM-SR Decision 3.0 / d3 已加入模型对比列表**，后续优先试 d3-mini（4.54B），d3 全尺寸作为大模型对照；见[模型资料与试跑安排](docs/ecosystem/vllm-sr-decision-models.md)。当前尚未独立试跑。

### 生态规模

| 层次 | 数量 |
|---|---:|
| 进入独立评测的**开源** Jev 类系统 | **81**（95 个入榜系统中） |
| 其中**真正微调/训练过**的复现 | **59** |
| Awesome JEV 精选（50+ star、源码评审） | 228（Open models 类 31） |
| GitHub 含 JEV 的仓库 | 13,000+ |

绝大多数站在 **Qwen3.5** 上。训练成本已被抹平到 **\$17 / 25 分钟**（Together 的 Tev1）到 \$1,200（Imajev-4B）。

### 效果：前三名全是开源，但要先读这张表

JevBench v1.4.2.2 前四：**Imajev-4B 67.37 → Plumb-4B 65.84 → decider-4b v2 64.13 → Jev 1.13.0 63.29**。

分轴看才清楚：开源赢在**速度**（S 90+ vs Jev 83）和**成本**（Plumb p50 183 ms vs Jev 652 ms）；**智能轴 Jev 仍以 53.1 居 Jev 类最高**。

**而最关键的发现是公开 → 密封的坍塌**（密封集随机基线 29.3%）：

| 系统 | 公开题 | 密封题 |
|---|---:|---:|
| Imajev-4B | 86.1% | **37.0%** |
| **Jev 1.13.0（原版）** | 86.6% | **36.7%** |
| GPT-6 Luna | 99.6% | **95.5%** |

**坍塌 48–57pp 是普遍的，原版 Jev 自己就塌 49.9pp。** 这说明它反映的是**整条技术路线的共同上限**——Jev 类模型打破的是决策的**成本结构**，不是**能力上限**。任何"开源已全面超越"的说法都忽略了这点。

### 选型要点

- 综合最强 + 支持图片 → **Imajev-4B**
- 最高智能轴 → **Plumb-4B**
- 可信概率设阈值 → **Hopper**（校准全场第一）
- 完全不想训练 → **AnyJev L0**（诺基亚 + 腾讯混元，一个参数不动，顺序翻转率 23% → 7.3%）
- 纯本地 / 无 GPU → **Laya**（421M，**必须用微调版**，基座 checkpoint 域外接近随机）
- 多跳推理 / 数值 / 日期 → 别用，直接上大模型

国内注意：**Intern-Decision 4B**（上海 AI Lab）自报 90.02 均分，**尚未第三方复现**，谨慎引用。

### 科研切入点

路由问题见[研究议程](docs/routing-security/research-agenda.md)，最新证据与选题判断见[鲁棒性与安全调研](docs/semantic-robustness/2026-10-13-robustness-security-review.md)：

> 已有研究覆盖文本扰动、选项命名与定义绑定、概率门控和授权边界，不能再将这些主题整体视为无人研究。当前建议聚焦**不可信来源声称如何影响安全判断，以及固定门控阈值在扰动下的风险与覆盖率变化**；具体新颖性仍需与最近邻逐项比较。

---

## 新研究主线：语义鲁棒性

**同一含义换一种说法，Jev 的答案、概率和操作决定是否稳定？只改变关键语义，它又能否及时改变判断？**

已发现直接相关工作：JevAdvBench、CITY-Jev / CanITrustU-Jev、Beyond Calibration，以及独立的 metamorphic coherence JevBench（不是现有 Benchmark Heaven 榜单）。因此不能将“做一些改写并测翻转率”宣称为新问题。

2026-10-13 已完成九篇论文全文、三项摘要级材料和部分公开实现核查，形成[鲁棒性与安全研究报告](docs/semantic-robustness/2026-10-13-robustness-security-review.md)。建议以 **state 等价改写 + 伪授权／真实授权对照 + 概率与操作阈值迁移**连接 Jev 与安全；相同请求重跑用于估计噪声，同时测正确率，避免把稳定错误算作鲁棒。配套[60 场景 pilot 协议](docs/semantic-robustness/robustness-security-pilot-protocol.md)尚未执行，来源与固定版本记录见[本轮快照](data/jev-robustness-literature/2026-10-13-review/README.md)。

**本轮完成文献与设计，没有新增模型调用；既有 JevOut 脚本、数据、共享配置与结果保持独立。**

## 免费 Jev 测试入口

已配置 OpenCode Zen 的 `jev-1.13-free`，项目共享配置在 `.pi/pi-jev.json`。

```bash
python scripts/jev_api.py --out data/jev-zen-smoke.json
python scripts/jev_api.py data/jev-request-examples-2026-10-11/03-rag-screen.json
```

运行时会使用配置中的模型，不修改历史请求与结果。免费服务可能结束或限流；请求会发送到外部服务。配置、离线测试与证据边界见 [测试说明](docs/infrastructure/opencode-zen-jev-testing.md)。

## 复现

```bash
# 需要 gh 已登录（主传输走 gh api，因为 raw.githubusercontent.com 常被代理屏蔽）
python scripts/fetch_jevbench.py                  # 默认 v1.4.2.2
python scripts/fetch_jevbench.py --version v1.4.2.1
```

脚本会重试直到 payload 能解析，并打印字节数（**单次下载被代理截断是常见坑**：曾拿到 80 KB 而非 622 KB，JSON 解析静默失败）。

---

## 引用前请注意

- 版本：本仓库数据为 **JevBench v1.4.2.2**（上游仓库最后更新 2026-09-29）。**v1.5.x 已存在**（Autoloops 从 29.96 → 40.53），分数变动很快，引用前请确认。
- Jev 发布于 2026-09-15，调研进行时它**不足一个月**，独立可复现评测仍稀缺。
- 厂商公布的倍数（最高 193.6× 更快、444.6× 更便宜）由厂商自己的团队构建，其自述处在"真实收益的上端"，**不应直接写入采购测算**。

## 许可证

本仓库自有代码与文档为 **MIT**。保存的第三方论文、网页和源码快照保留原有权利与许可证；模型权重也各有独立条款（Gemma / Qwen / LFM 等），**与本文档的许可证无关**，商用前请单独确认（见 `docs/ecosystem/obtainability-and-licensing.md`）。


## 本地 benchmark 首轮

[本地三款 4B 模型配对试验](docs/model-evaluation/local-benchmark-pilot.md)：在 Jev 工作空间各完成 100 条，含 MSB、MCPTox、AgentDojo，与同 UID 的 Jev 历史预测对照。


[各 benchmark 的 Jev、本地模型与 DeepSeek 对比总结](docs/model-evaluation/benchmark-comparison.md)。

## 实用产品与请求设计（2026-10-11）

[基于 Jev 的实用产品与请求设计调研](docs/applications/products-and-request-design.md)：核查 12 个仓库，重点剖析 Winnow、jev-align、DocJev、JevPDF、classifier.dev 等的 state、criteria、批量问题与阈值；附 [四个可复制的 JSON 示例](data/jev-request-examples-2026-10-11/README.md) 和精确源码快照记录。


## 跑测实践与框架代码（2026-10-27）

本地 Jev 安全工作区的已有实践现已整理入仓：

- [实践总结：接口、标签、提示词、阈值、抽样、分片、失败与计费](docs/infrastructure/jev-benchmark-lessons.md)
- [静态评测框架与离线测试](framework/README.md)：三种 type 配对、失败补测、时间/费用统计；复用原 monitor，不复制其实现。
- [AgentDojo 500 条、Jev 1.14 三 type 结果](docs/model-evaluation/2026-10-27-agentdojo-type-comparison.md)：每次单问题、同批样本，三臂准确率97.8%–98.2%，不是完整agent ASR。
- [历史证据索引与受限数据边界](data/workspace-evidence/README.md)。

本次导出只做离线验证，没有再次请求模型。框架依赖另行准备的源工作区、精确版本与授权数据，不能仅凭本仓库克隆恢复付费观测。既有全链路研究协议仍属独立计划，不因静态实验而变成已完成。

## Agent 安全 benchmark

[四基准与 11 模型评测入口](security_bench/README.md)提供请求适配、原始记录、时间/API费用与报告；模型部署及实验配置尚待补全。[换机恢复步骤](docs/infrastructure/2026-10-28-machine-handoff.md)说明依赖、原 monitor 和两个数据包。

本机模型调用见[本机模型使用手册](docs/infrastructure/local-model-operations.md)：9个本地服务、Jev等API中转、请求预览与实验入口。
