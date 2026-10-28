# Jev security empirical study：模型候选与选型依据

记录日期：2026-10-22。状态：官方资料核查与实验设计建议，尚未执行新模型下载、部署或付费调用。本文中的“核心”是建议，不代表最终冻结；现有实验状态来自仓库历史记录。

后续文献核查增量：见[论文模型与引用参考](jev-paper-model-reference.md)。新增优先考虑 SecJev-0.8B / 4B 及 Kev 配对、PIGuard / ProtectAI / WildGuard；Luna 的生成式 Judge 与 Decisions API 分别记为独立运行配置。下文 14 款是原始建议，不是最终冻结名单。

## 研究目标与分组

比较专用决策模型、通用 LLM、安全判别器在安全任务上的质量、运行成本和延迟。优势应作为待检验假设，以固定误报率下的检出率、质量约束下的成本和延迟来判断。不能提前假定 Jev 胜出，也不能仅选择昂贵的大模型作为对照。

官方 Jev 是闭源托管模型；开放权重的 Jev 类模型是独立实现。本文的安全模型主要指输入/输出安全判别器，不是仅经过安全对齐、会拒绝有害请求的聊天模型。开放权重与开源许可分别核查。

## A. 专用决策模型

| 候选 | 方式 / 规模口径 | 安排 | 选择理由与状态 |
|---|---|---|---|
| TypeSafe `jev-1.14.0` | 官方 API；参数未公开 | 核心 | 当前新版本，2026-10-14 发布；需新建结果组，不能混入历史 1.13 结果 |
| TypeSafe `jev-1.13.0` | 官方 API；参数未公开 | 历史桥接 | 项目已有历史数据；新旧版在同一新样本子集配对，避免把不同数据差异解释为版本提升 |
| `vllm-sr/d3-mini` | 自部署；模型卡约 4.54B | 核心 | 新系列；与 Qwen3.5-4B 做底座对照；此前已纳入待测，尚未试跑 |
| `vllm-sr/d3-nano` | 自部署；模型卡约 2.21B | 核心 | 同系列尺寸与资源对照；12 GB 显存环境的优先备选 |
| `crh225/plumb-4b` | 自部署；4B 命名档位 | 核心 | 已有本地 smoke 和安全 pilot；需固定历史权重及 readout，不能将新版服务代码与旧结果混用 |
| `Mapika/decider-4b` | 自部署；4B 命名档位 | 核心 | 已有本地 smoke 和安全 pilot；与 Plumb 比较不同训练/读出方案 |
| Microsoft-Decision-1 | 微软官方 Foundry API | 扩展优先 | 第二家托管专用决策模型；已有专题，未独立运行；不是 Jev 的微软端点 |
| `mohit67890/imajev-4b` | 自部署；LoRA 与其指定基座 | 扩展 | 增加独立实现；不按旧通用榜单名次预断安全表现 |
| H2O-Lightning-4B v1.1 | 自部署；4B 命名档位 | 历史复用 | 已有本地 smoke 和 pilot；官方 shim 与 stock vLLM 不能预设等价 |

Jev 官方文档当前同时列出 1.14 与 1.13，输入单价均为 $0.042 / 百万 token，默认 64k / request、32k / question；`jev-latest` 仍指向 1.13，`jev-preview` 指向 1.14。正式实验显式填写版本 ID，保存响应版本和日期。API 可用性、账户权限及实际账单尚未验证。

来源：[Jev 模型页](https://docs.typesafe.ai/models)、[d3-mini](https://huggingface.co/vllm-sr/d3-mini)、[d3-nano](https://huggingface.co/vllm-sr/d3-nano)、[Plumb](https://huggingface.co/crh225/plumb-4b)、[decider](https://huggingface.co/Mapika/decider-4b)、[Microsoft 部署文档](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision)、[Imajev](https://huggingface.co/mohit67890/imajev-4b)。

## B. 通用 LLM

| 候选 | 方式 | 安排 | 实验作用 |
|---|---|---|---|
| `Qwen/Qwen3.5-4B` | 自部署 | 核心 | 必须保留的底座对照：比较通用生成判断与 Jev 类微调模型 |
| `Qwen/Qwen3.5-9B` | 自部署 | 核心 | 同家族规模对照；本机 12 GB 卡不能预设 BF16 可容纳，必要时单列量化轨道 |
| `google/gemma-4-E4B-it` | 自部署 | 核心 | 新一代、另一模型家族，避免结论只覆盖 Qwen；E4B 命名不能直接当作总驻留参数量 |
| OpenAI `gpt-6-luna` | 官方 API | 核心 | 当前高吞吐、预算导向的通用模型，直接挑战 Jev 的成本与延迟优势 |
| Anthropic `claude-haiku-5-5` | 官方 API | 核心 | 第二家厂商的快速小模型；2026 年 10 月的新候选 |
| OpenAI `gpt-6.1-sol` | 官方 API | 扩展优先 | 较强质量参考；质量上限仍是实验问题，不作为 gold 标注器 |
| Anthropic `claude-sonnet-5-5` | 官方 API | 扩展 | 跨厂商较强参考，与 Haiku 构成能力档位对照 |
| `Qwen/Qwen3.8-27B` | 自部署 | 扩展 | 较新开放权重强模型；需要额外算力，不能用激活规模替代驻留成本 |

Qwen3.5-4B 的保留理由是配对底座，而非声称它是最新 Qwen。主选型同时包含近期发布的 Gemma、OpenAI、Claude。正式运行前冻结 HF revision、API 模型 ID、可用的 snapshot 与推理配置；无不可变 API snapshot 时记录日期、响应版本和漂移探针。

来源：[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B)、[Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B)、[Gemma 4 E4B IT](https://huggingface.co/google/gemma-4-E4B-it)、[OpenAI 模型文档](https://developers.openai.com/api/docs/models)、[Claude 模型文档](https://platform.claude.com/docs/en/models/overview)、[Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B)。

## C. 专用安全判别器

| 候选 | 规模 | 安排 | 实验作用与边界 |
|---|---|---|---|
| `Qwen/Qwen3Guard-Gen-0.6B` | 0.6B | 核心 | 低预算、多语言安全判别器；保留 safe / controversial / unsafe 原始输出 |
| `Qwen/Qwen3Guard-Gen-4B` | 4B | 核心 | 同系列规模对照，与 4B 决策模型作近似规模比较；不同底座，不能作纯微调因果归因 |
| Shieldstral 1.0 | 官方文档 3.8B | 核心 | 2026-08-04 发布；自然语言政策问题、yes/no 分类；适合检验可配置安全判别竞争力 |
| `fastino/gliguard-LLMGuardrails-300M` | 作者约 0.3B | 核心 | 非自回归小型安全判别对照，覆盖安全、毒性、越狱和拒答；模型页摘要另显示 0.2B，冻结前按 config/权重核对实际参数 |
| `nvidia/Nemotron-3.5-Content-Safety` | 4B | 扩展优先 | 2026 年模型，Gemma-3-4B-it 经 LoRA 微调；多语言、多模态，增加另一训练路线 |
| `meta-llama/Llama-Guard-4-12B` | 12B | 扩展 | 广泛使用的安全判别参考；规模较大且较旧，不作为唯一小模型安全基线 |
| `meta-llama/Llama-Prompt-Guard-2-86M` | 86M | 注入/越狱专项必选 | 专用攻击检测；不等同于通用有害内容、工具授权或任务遵循判别器 |

Prompt Guard 2 的上下文是 512 token，官方不再提供第一代那样的独立 injection 子标签。长输入分段与聚合必须计入成本、延迟和误报率；不得只取前 512 token 并当作完整样本测试。其在 AgentDojo 等间接注入上的泛化能力需要实测。

Qwen3Guard 的 controversial 如何映射为二分类，应在开发集预先决定并记录；不能查看测试集结果后选择更好的映射。Guard 原生政策与项目自定义政策可能不一致，分别报告原生能力与可配置任务适配；不能把“不支持该任务”一律当成识别错误。

来源：[Qwen3Guard 0.6B](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B)、[4B](https://huggingface.co/Qwen/Qwen3Guard-Gen-4B)、[Shieldstral](https://docs.mistral.ai/models/shieldstral-1-0)、[GLiGuard](https://huggingface.co/fastino/gliguard-LLMGuardrails-300M)、[Nemotron](https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety)、[Llama Guard 4](https://huggingface.co/meta-llama/Llama-Guard-4-12B)、[Prompt Guard 2](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M)。

## 建议起步范围

完整核心组为 14 款：5 款决策模型（Jev 1.14、d3-mini、d3-nano、Plumb、decider），5 款通用 LLM（Qwen 4B / 9B、Gemma E4B、Luna、Haiku），4 款安全判别器（Qwen3Guard 0.6B / 4B、Shieldstral、GLiGuard）。另在注入/越狱专项增加 Prompt Guard 2，共 15 款。Jev 1.13 作历史版本桥接，独立计为额外配置。

资源受限时，首轮缩至 10 款：Jev 1.14、Plumb、d3-mini、Qwen3.5-4B、Gemma E4B、Luna、Haiku、Qwen3Guard-0.6B、Shieldstral、GLiGuard。若 d3-mini 显存不够，用 d3-nano 并记录替换原因。首轮用于检验接口与资源，不据此调优测试集或只保留有利于 Jev 的模型。

## 为后续数据与参数设计保留的约束

1. 内容安全、提示注入/越狱、工具授权/行为安全至少分开报告。各模型支持的任务不同，先做适配资格表。
2. 在同一任务内统一目标政策、原始信息、标签与样本 UID；允许官方聊天模板和适配器，保存最终请求。标签输出的拒答、解析失败、超时单独计数，不从准确率分母删除。
3. 通用 LLM 主轨道输出最短判决；推理能力按文档支持的最小配置固定。可选 reasoning 另建轨道，隐藏推理 token 也记账。未支持关闭推理时如实记录。
4. Qwen3.5-4B 增加受限选项 logits 读出作为消融；它是同 checkpoint 的推理配置，不算另一独立模型。多 token 标签不能简单只取第一个 token。比较其与生成判决、微调决策模型的差异。
5. 延迟统计到可用判决返回的 p50 / p95，含解析和网络；本地另报模型计算时间，区分冷启动、预热、batch、并发和吞吐。单次 API 多问题不等于单次前向。
6. API 成本使用实际 usage 和账单口径，含输出、推理、重试；自部署报告 GPU 时长、租金、利用率及部署摊销假设。不可把本地零 API 账单写成零成本。
7. 报告 F1 / AUPRC、固定 FPR 下的 TPR、业务风险与质量约束下的成本-延迟 Pareto 前沿；概率可得时再作 Brier / 校准分析。口头自报置信度与原生概率不能直接等同。
8. 相同精度下的硬件比较与现实部署比较分轨。量化不是只影响显存，也可能影响安全判决和概率；量化配置须单列。现有 12 GB GPU 的可运行性不能由权重大小直接保证。

所有模型的官方速度和榜单数据只能作为选型线索。本文未新增任何实测优势结论。
