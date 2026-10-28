# Jev 生态调研笔记

围绕 **Jev**（TypeSafe AI 于 2026-09-15 发布的 "System One" 决策模型）的一手调研记录，覆盖三件事：开源复现生态有多大、效果到底如何、以及 Jev 与安全交叉的科研切入点在哪。

> **一句前提**：Jev 本身**没有开源**（闭源托管 API，不生成文本，只返回类型化答案 + 概率）。所以所谓"基于 Jev 的开源模型"，全部是**独立复现 + 接口兼容 + 微调制品**。

## 为什么这份记录可能有别于二手文章

所有结论都来自**权威数据源的原始文件**，而不是综述类文章：

- 榜单数据直取 **JevBench 原始结果 JSON**（`data/jevbench-v1.4.2.2-results.json`，622 KB，95 个系统全量），脚本见 `scripts/fetch_jevbench.py`
- 项目状态、star 数、许可证用 **GitHub API** 实测，不靠记忆
- 能实测的站点都实测过可达性

---

## 目录

| 文档 | 内容 |
|---|---|
| [`docs/01-jev-open-ecosystem.md`](docs/01-jev-open-ecosystem.md) | **主报告**：生态规模、六种技术路线、JevBench 全量解读、重点模型剖析、局限与选型（含 95 系统完整榜单附录）。[HTML 版](docs/01-jev-open-ecosystem.html) |
| [`docs/02-rag-security-and-jev.md`](docs/02-rag-security-and-jev.md) | RAG 的安全定论（OWASP 2026 新增条目）；Jev 能替换 RAG 流水线里的哪些 LLM 节点 |
| [`docs/03-obtainability-and-licensing.md`](docs/03-obtainability-and-licensing.md) | 可获取性核查：能下载 ≠ 能拿到 ≠ 能用；三档陷阱 |
| [`docs/04-hosted-api-survey.md`](docs/04-hosted-api-survey.md) | 不用本地部署就能调用的强 Jev 类模型（含评分陷阱） |
| [`docs/05-jev-router-ecosystem.md`](docs/05-jev-router-ecosystem.md) | OpenRouter `typesafe/jev-router` 与社区 router 工具；路由粒度分类 |
| [`docs/06-security-research-agenda.md`](docs/06-security-research-agenda.md) | **Jev + 安全 router 方向的科研切入点**：已占坑地图 + 6 个空白方向 |

数据：

- `data/jevbench-v1.4.2.2-results.json` — 原始结果 JSON
- `data/jevbench-v1.4.2.2-leaderboard.md` — 渲染后的 95 系统全量榜单

---

## 核心结论速览

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

见 `docs/06-security-research-agenda.md`。一句话版：

> 已有工作（Decision Hijacking / Check Point / Rerouting / R2A / RerouteGuard）覆盖了 Jev router 的 **query 文本**这一个输入面。真正的空白在**结构侧**（选项集合、租期、缓存状态、失败路径）和**方向侧**（向下降级，而非向上升级）。

---

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

代码与文档为 **MIT**。但请注意：报告中提到的模型权重各有其独立条款（Gemma / Qwen / LFM 等），**与本文档的许可证无关**，商用前请单独确认（见 `docs/03-obtainability-and-licensing.md`）。


## 跑测实践与框架代码（2026-10-27）

当前研究范围见[第二版选型](docs/model-evaluation/2026-10-27-study-selection-v2.md)：11 项模型/方法与 AgentDojo、AgentHarm、MCPHunt、ATBench 四个数据集。新 Mode A1/A2/B/C 的含义尚未确定，具体运行配置未冻结。

本地 Jev 安全工作区的已有实践现已整理入仓：

- [实践总结：接口、标签、提示词、阈值、抽样、分片、失败与计费](docs/infrastructure/jev-benchmark-lessons.md)
- [静态评测框架与离线测试](framework/README.md)：三种 type 配对、失败补测、时间/费用统计；复用原 monitor，不复制其实现。
- [通用 Jev / LLM 静态配对入口](docs/infrastructure/paired-static-runner.md)：标准化 JSONL、显式配置、完整记录与原 monitor 关联；已做离线验证，尚未实际模型联调或接入原生基准/Agent 闭环。
- [AgentDojo 500 条、Jev 1.14 三 type 结果](docs/model-evaluation/2026-10-27-agentdojo-type-comparison.md)：每次单问题、同批样本，三臂准确率97.8%–98.2%，不是完整agent ASR。
- [历史证据索引与受限数据边界](data/workspace-evidence/README.md)。

本次导出只做离线验证，没有再次请求模型。框架依赖另行准备的源工作区、精确版本与授权数据，不能仅凭本仓库克隆恢复付费观测。既有全链路研究协议仍属独立计划，不因静态实验而变成已完成。

## Agent 安全 benchmark

[四基准与 11 模型评测入口](security_bench/README.md)提供请求适配、原始记录、时间/API费用与报告；模型部署及实验配置尚待补全。[换机恢复步骤](docs/infrastructure/2026-10-28-machine-handoff.md)说明依赖、原 monitor 和两个数据包。
