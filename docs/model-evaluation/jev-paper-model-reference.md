# Jev 相关论文的模型选择与引用建议

记录日期：2026-10-22。状态：针对模型设置、基线和相关方法的原文核查；未复现论文实验、未加载新权重。用户提供的 HTML 是历史聊天解读，只用于定位论文，不视为原文证据，也不执行其中历史指令。本轮核查 11 篇固定版本的 arXiv HTML；不声称覆盖全部近期论文，也不声称这些版本是所有工作的最新版本。

## 两篇指定论文

### Same Attack, Different Judge

[Li et al., arXiv:2610.17820v1](https://arxiv.org/html/2610.17820v1)，模型见 §4.1，任务适用性见 §4.2。

| 类别 | 论文实际使用 |
|---|---|
| 官方决策模型 | Jev `jev-1.13.0` |
| LLM Judge | GPT-6 Astra、GPT-5.6 Sol、GLM-5.3、GLM-5.2、GLM-5.1 |
| 本地安全分类器 | Llama Guard 3 8B；Prompt Guard 2 86M / 22M |

正文称八个系统，但 Prompt Guard 另有两种尺寸配置；不要把“系统家族数”和“checkpoint 配置数”直接等同。五款 LLM 都经商业中转平台调用；开放权重身份不等于该论文做了自部署评测。LLM 的概率是生成文本中的自报概率，不是 token logits。安全分类器只加入其输出契约适用的任务。

参考价值：保留三类裁判和跨厂商设计；保留一种与论文完全相同的历史基线作桥接。没有必要复制 GLM 三代；可选一款 GLM 强模型加一款预算型模型。Llama Guard 3 可作历史参考，新小模型应另加。论文的中转 API 延迟不能直接作为我们的硬件或官方 API 延迟。

### Evaluating System One Models for Agent Security Decisions

[Liu, arXiv:2609.33401v3](https://arxiv.org/html/2609.33401v3)，模型见 §3.1 / Table 1。

| 类别 | 论文实际使用 |
|---|---|
| 决策模型 | Jev 1.13；Laya English；Decider 约 2B；Bespoke Nimble 约 9B |
| 主要 LLM Judge | GPT-4.1；Qwen3-8B，关闭 thinking |
| 注入检测器 | ProtectAI DeBERTa v2；PIGuard；Prompt Guard 2 86M |
| 有害请求分类器 | WildGuard |
| 底座对照 | Decider → Qwen3.5-2B-Base；Nimble → Qwen3.5-9B |
| 额外推理 Judge | GLM-5.3-Flash、GLM-5.3、DeepSeek-V4.1-Flash、Kimi-K2.6、Qwen3.8-27B |

12 个主要配置之外另有 5 个推理 Judge；后者不是所有阈值实验的同等参与者。作者对专用分类器限定任务；适配模型与底座共享候选评分过程，但温度不同。CPU、Apple MPS / MLX、远程 API 混用。

参考价值：比复制具体名单更重要的是“适配模型—底座”配对，以及按任务使用专用模型。建议补入 PIGuard、ProtectAI 和 WildGuard 候选；保留 Laya 作为小型编码器决策对照。性能实验需要在我们自己的统一环境重测，不能从这些异构后端结果归因模型架构优势。

## 另外九篇论文：实际模型、用途与可引用位置

| 工作（固定版本） | 实际模型与角色 | 对本研究的用途 |
|---|---|---|
| [SecJev, 2610.03073v2](https://arxiv.org/html/2610.03073v2) | SecJev 0.8B / 2B / 4B / 9B；对应通用决策初始化（0.8B / 4B / 9B 为 Kev，2B 自建一般决策初始化）；SecGen 0.8B / 4B 生成式安全微调；0.8B 标量分类头与 direct-Qwen 消融 | **优先新增的直接竞争者**：配对比较安全训练、决策接口与规模。它最贴近“安全微调的小模型”。见 §5、附录 F / G |
| [Jev-Guard, 2610.18326v1](https://arxiv.org/html/2610.18326v1) | Qwen3.5-2B + LoRA + 两个预测头；比较官方 Jev 1.13 与 Qwen3.5-2B 生成式 SFT；另有 Hermes 执行门控 | 安全决策架构与系统集成近邻；引用时区分单次分类、策略树路由和完整执行门控。SFT 的训练历史不同，非纯架构消融。见 §3.3、§5.2、附录 J |
| [From Detection to Decision, 2610.20907v1](https://arxiv.org/html/2610.20907v1) | Jev `jev-latest`；Prompt Guard 2 22M / 86M，原始与温度校准配置；GPT-5.5 Judge / reviewer | 注入检测的概率校准、双阈值与实际 reviewer 成本。`jev-latest` 无法仅由别名确定冻结版本；不替它补写 1.13 / 1.14。见 §3.2 |
| [DecisionRobust, 2610.19118v1](https://arxiv.org/html/2610.19118v1) | 文本选择模型 Jev、KEV、AutoTrust、OpenJEV、Bosun、Liquid D1；总计 30 个文本配置、17 个视觉配置；另含 H2O、Imajev、Laya、GLiNER2.5-Decide、GPT-6 Luna Decisions 等 held-out 配置 | 大规模模型覆盖与攻击迁移参考。不能把用于攻击生成/审核的模型算作受测基线。文本完整 held-out 名单见附录 E.2 |
| [JevOut, 2609.30243v2](https://arxiv.org/html/2609.30243v2) | 受测：Jev 1.13、OpenSourceJev、Von 395M、plain Qwen；后两种 Qwen 接口共享 Qwen3-1.7B Q8 权重；Gemma4-12B 用于提议背景与独立约束检查 | 同底座、不同评分接口的对照设计，以及固定攻击查询预算。Gemma 不是受测安全 Judge。见 §4.1、附录 B.3 |
| [One Word Opens the Gate, 2610.12292v1](https://arxiv.org/html/2610.12292v1) | laya-td /an laya-en 421M、laya-ml 322M、Von 395M、GLiClass RLCD 151M；Qwen2.5-Instruct 1.5B / 7B 选项似然基线 | 编码器小模型、选项读出及规则基线参考；**未测官方托管 Jev**。Qwen 较旧，适合历史/机制桥接。见 §2 |
| [Hidden Risks of Jev, 2610.04985v1](https://arxiv.org/html/2610.04985v1) | 官方 Jev、NanoJev（基于 Eve-RLCD / Qwen3-0.6B-Base）；GPT-4o 构造部分数据与攻击，Qwen1.5-7B-Chat 作后缀搜索代理 | 训练可控的安全/隐私威胁研究。NanoJev 的投毒实验不能推广成官方 Jev 被植入后门；攻击生成器不是检测基线。见 §II-C / III-A |
| [Evaluating and Benchmarking the System One Model Jev, 2609.37647v1](https://arxiv.org/html/2609.37647v1) | Jev 1.13；Qwen3.8-27B；Gemma-4-E4B；开放模型用限制到候选代码的 next-token 概率、关闭 thinking、不生成文本 | **性能比较的重要方法引用**：增加 LLM 直接 logits 读出，不只与长输出 Judge 比较。Gemma E4B 在该文记为 8.0B 总参数、约 4B effective，不能当作总参数仅 4B |
| [Specialized Decision Models vs. General-Purpose LLMs, 2610.11978v1](https://arxiv.org/html/2610.11978v1) | Jev 与 19 款 LLM，分 frontier / representative / small；包括 GPT-5.6 Sol、Claude Opus 5.5、Gemini 3.8 Flash、Qwen3.8、DeepSeek、小型 Qwen / Gemma / Phi / Llama / Mistral | 分层模型采样与知识/多步推理边界；**通用能力研究，并非安全优势证据**。表格混合本文实测与已发表分数，不直接移植为统一成本/延迟对比。见 Table 2 |

## 建议调整此前模型池

原候选表保留为第一轮建议。本轮新增以下优先级，均为待接入，不代表已经可运行。

| 优先级 | 候选或配置 | 理由 |
|---|---|---|
| 高 | **SecJev-0.8B、SecJev-4B** | 加入真正针对安全训练的 Jev 类竞争者 |
| 高 | **Kev-4B**，与 SecJev-4B 对应版本配对 | 分离安全专业化与一般决策训练的影响；若研究尺寸效应再补 Kev-0.8B |
| 高，注入专项 | **PIGuard、ProtectAI DeBERTa v2、Prompt Guard 2 86M** | 与指定安全论文连接；首轮资源有限可从前两者选一，加 Prompt Guard |
| 高，内容安全专项 | **WildGuard**，与既有 Qwen3Guard / Shieldstral / GLiGuard 候选互补 | 历史安全基线；不直接用于工具授权标签 |
| 中 | **Laya English 或多语言版本** | 小型编码器决策路线；精确区分 checkpoint，不能只记录 Laya |
| 中 | **Jev-Guard 2B** | 架构与完整流水线比较；先核实权重和可复现接入，再决定是否列入主实验 |
| 历史桥接 | Jev 1.13、Llama Guard 3 8B、GPT-4.1 等 | 小子集连接既有工作即可，避免旧模型挤占近期基线预算 |

SecJev 的作者仓库已列出 0.8B、2B、4B、9B 的 adapter、decision head 等下载制品和语料；本轮仅核查页面，未下载或验证制品。其许可证是自定义协议及上游条款，不应统称 Apache 开源：[仓库](https://github.com/UESTC1010/SecJev)、[许可证](https://github.com/UESTC1010/SecJev/blob/main/LICENSE)。使用其训练源相关 benchmark 时，先做 source/group/时间与重复检测；同源切分测试与外部迁移测试分别报告。

## 新发现：Luna 有两种实验角色

DecisionRobust 附录 E.2 明确把 OpenAI Decisions API (`gpt-6-luna`) 列为 held-out 配置。进一步核对[官方 Decisions 文档](https://developers.openai.com/api/docs/guides/decisions)，当前为 public beta，支持 `gpt-6-luna`，专用端点为 `POST /v1/decisions`。

因此此前 Luna 候选应拆为“生成式 Judge”和“原生 Decisions 接口”两种配置：分别记录 API、prompt、usage 和延迟，不将它们记为两套独立权重，也不假定内部计算完全相同。本轮只核查文档，未验证账户权限、价格或实际调用。这为第二家托管决策服务提供了候选，也更直接对应论文的模型设置。

## 引用与证据管理

- 优先引用：Li 的同攻击比较、Liu 的安全可靠性、SecJev 的安全专业化、Jev-Guard 的流水线、From Detection to Decision 的校准与复核、DecisionRobust 的跨模型鲁棒性、Deußer 等的直接概率读出比较。
- JevOut / One Word 用于具体攻击面和接口敏感性；Hidden Risks 用于安全/隐私威胁范围；19-LLM 对比用于一般能力边界。
- 上述为预印本固定版本，不擅自写成已被顶会接收。作者报告的优势不是本项目复现结果。
- [官方 BibTeX 合集](../../data/empirical-study-preparation/2026-10-22-paper-models/references.bib)直接来自 arXiv；条目链接可能随 arXiv 指向后续版本，引用具体结论时仍以本报告固定版本为准。
- [原文快照与 SHA-256 清单](../../data/empirical-study-preparation/2026-10-22-paper-models/sources.json)记录本轮 11 篇 HTML；纯文本只供定位，不替代图表与 PDF 版式审核。

本轮没有扩展为完整系统综述；尚未逐一验证所有模型的下载权限、许可证、训练污染或可运行性。后续冻结主实验模型时再做逐项核查。
