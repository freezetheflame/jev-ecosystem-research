# Agent 安全实验：用户暂定模型、数据集与参数清单

记录日期：2026-10-27（Asia/Shanghai）。状态：**用户暂定选型，尚未冻结具体运行配置；不是实验结果**。

本页整理用户当日提供的表格，作为当前选型记录；早前选型报告继续作为历史背景，不自动扩大本轮名单。共 **12 个模型/方法、6 个数据集、5 类参数因素**。日期、特点和研究用途除特别说明外均来自用户材料，不表示本轮已独立验证。条目数量、固定 revision、具体数值、预算及 prompt 尚待确定。

机器可读记录：[selection-2026-10-27.json](../../data/agent-security-study/selection-2026-10-27.json)。实验执行继续遵循[执行规范](agent-security-experiment-protocol.md)；时间与费用沿用已有 monitor，不因此次整理更改。

## 1. 模型与方法

以下分类用于整理角色，不表示所有模型都已通过每种任务/接口的适配验收。“发布日期”保留用户口径；论文首发、修订日期和权重发布时间后续分别核实。

| 类别 | 模型/方法 | 日期（用户提供） | 来源 | 特征与选型备注 | 待明确 |
|---|---|---|---|---|---|
| 决策模型 | Jev 1.14.0 | 2026-10-14 | TypeSafe 官方 API；[模型文档](https://docs.typesafe.ai/models) | 闭源托管决策模型；用户列为代表性 Jev 基准 | 实际 API 版本、端点、可用性和请求契约 |
| 决策模型 | D3-mini | 2026-10-17 | [vllm-sr/d3-mini](https://huggingface.co/vllm-sr/d3-mini) | 用户列为开放决策模型；保留其模型卡 BibTeX | 固定 revision、依赖、推理实现和精度 |
| 决策模型 | Plumb-4B | 未提供 | 用户来源栏空缺；历史资料指向 [crh225/plumb-4b](https://huggingface.co/crh225/plumb-4b) / [实现](https://github.com/crh225/plumb) | 纳入本轮暂定名单；历史已有本地试跑 | 正式采用的权重和服务/readout 版本；不自动沿用旧温度 |
| 安全专门化决策模型 | SecJev | 2026-10-14 | [SecJev，2610.03073v2](https://arxiv.org/html/2610.03073v2) | 用户列为安全领域微调决策模型 | 尺寸、checkpoint/adapter、head、温度、可用性及许可证 |
| 路由/审计方法与执行防护系统 | Jev-Guard | 2026-10-13（用户标为论文首发） | [Jev-Guard，2610.18326v1](https://arxiv.org/html/2610.18326v1) | Qwen3.5-2B + LoRA + 预测头，结合可编辑策略树；用户希望用于完整流水线比较 | 权重接入；单判别器、策略树和执行 gate 分别定义配置 |
| 小型决策模型 | Laya | 未提供 | 用户来源栏空缺；历史资料指向 [convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya) | 小型编码器决策路线；具体模型元数据待补 | English / 多语言 / typed-decisions 具体 checkpoint，不以家族名代替版本 |
| 通用 LLM | Qwen3.5-4B | 2026-03（仅月份） | [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | 开放权重通用模型，支持本地部署 | revision、精度、生成式判决和推理设置 |
| 通用 LLM | GPT-6 Luna | 2026-09（仅月份） | [OpenAI 模型目录](https://developers.openai.com/api/docs/models) | 用户选作快速闭源 LLM | 精确模型/snapshot、普通 LLM Judge 请求方式；Decisions API 不自动纳入 |
| 通用 LLM | Claude Haiku 5.5 | 2026-10-07 | [Haiku 5.5 文档](https://platform.claude.com/docs/en/models/haiku-5-5/overview) | 用户选作面向分类、提取、路由的低延迟闭源 LLM | 精确模型/snapshot、端点、推理与输出预算 |
| 专用安全模型 | GLiGuard | 2026-05-08（用户标为论文首发） | [fastino/gliguard-LLMGuardrails-300M](https://huggingface.co/fastino/gliguard-LLMGuardrails-300M) | 用户列为 300M 非自回归安全分类器，优先候选、低资源效率对照 | 实际参数量、标签契约、任务适用性与 revision |
| 专用安全模型 | Shieldstral 1.0 | 2026-08-04 | [官方模型文档](https://docs.mistral.ai/models/shieldstral-1-0) | 用户列为 3.8B，可接受自然语言政策问题并做 yes/no 判断；优先候选 | 实际部署标识、政策/标签适配、权重/端点与配置 |
| 专用安全模型 | Qwen3Guard-Gen-0.6B | 2026-10-16 | [Qwen/Qwen3Guard-Gen-0.6B](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B) | 安全判别对照 | 输出标签映射、任务适用性、revision 和推理配置 |

补充边界：

- Plumb 与 Laya 的链接来自本地既有研究记录，补作定位入口，未据此替用户选择具体制品；日期仍保留空缺。参见[历史模型选型](empirical-study-model-selection.md)、[论文模型核查](jev-paper-model-reference.md)。
- 用户对 SecJev、Jev-Guard 使用了“open source”表述，先记录该说法；具体权重许可、上游条款和开源资格待核验。既有 SecJev 资料提示自定义许可，不能默认为 Apache/MIT。
- SecJev 的“安全微调”不表示拿闭源 TypeSafe Jev 权重继续训练；基座和训练来源按实际发布制品核对。
- Jev-Guard 是包含策略结构的方法：整套系统效果和单模型效果分开，不把结构收益全归给模型。
- 用户原备注“最知名的 jev 模型”作为选型意见保留在 JSON 中，不当作已证明的知名度排名。

### 用户提供的 D3-mini 引用

以下是用户提供的模型卡引用，做了 BibTeX/URL 格式清理，书目信息尚未单独核验：

```bibtex
@misc{d3_mini_2026,
  title        = {{d3-mini}: A Multimodal Foundation Decision Model},
  author       = {{vLLM Semantic Router Team}},
  year         = {2026},
  howpublished = {\url{https://huggingface.co/vllm-sr/d3-mini}}
}
```

## 2. 数据集与用户指定 Mode

| 数据集 | 用户指定主要 Mode | 选择理由（用户提供） | 核心参考文献 | 当前未冻结 |
|---|---|---|---|---|
| InjecAgent | A | 不可信工具返回与攻击者目标；用于输入端间接提示注入检测 | [Zhan et al., ACL 2024](https://aclanthology.org/2024.findings-acl.624/) | 版本、条目数、标签适配、划分 |
| AgentDojo | A、B | 真实 Agent 工具环境；连接输入判断、执行前防护与攻击结果 | [Debenedetti et al., NeurIPS 2024](https://arxiv.org/abs/2406.13352) | commit、任务/攻击集合、初始状态、环境及判分 |
| R-Judge | D | 多类别 Agent 交互风险及原生轨迹级标签；行为安全基线 | [Yuan et al., EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.79/) | 版本、条目数、标签范围、去重及划分 |
| ATBench | C、D | 长轨迹与延迟触发风险；比较历史信息与完整轨迹 | [Li et al., COLM 2026（用户署名/会议口径）](https://arxiv.org/abs/2604.02022) | 论文/制品元数据、轨迹切点及标签继承规则 |
| MCPHunt | B、C、D | 跨 MCP 服务器信息传播；区分正常执行与违规数据传输 | [Li et al., 2026（用户署名口径）](https://arxiv.org/abs/2604.27819) | 制品版本、任务/轨迹可用性、标签和环境 |
| SCR-Bench | B、C、D | 单独安全、组合后危险的 Skill 路径；能力传递、信任转移、授权混淆 | [Xie et al., 2026（用户署名口径）](https://arxiv.org/abs/2606.15242) | 制品版本、路径/动作标签、组合单位及切分 |

**Mode A/B/C/D 的概念定义已由用户于 2026-10-27 补充**：A Input Inspection；B Pre-action Authorization；C Prefix-based Monitoring；D Full-trace Auditing。按决策位置、可见信息和判断目标划分，非攻击类型分类。具体定义、输入边界与派生标签规则见[Mode 定义](agent-security-evaluation-modes.md)。它们属于 `evaluation_mode_codes`，与比较组 A（无新增模块）、J、L、R 分属不同维度；数据集适配合同仍待冻结。

“列入数据集”不表示所有数据集都能直接运行闭环 Agent。静态输入、执行前动作、历史前缀、完整轨迹必须分别核对可见信息与 gold；完整轨迹风险标签不能直接下放到每个前缀/动作。数据集来源、作者、年份/会议、许可、原始条目数及训练暴露后续逐一核验。

## 3. 参数与消融因素

这些是用户希望考察的**参数因素**，还不是已固定的运行值。主实验每次固定具体配置；参数消融单列，避免把所有因素做未经预算的全组合。

| 参数因素 | 用户给出的含义 | 用户列举的适用对象 | 参考研究 | 记录与冻结要求 |
|---|---|---|---|---|
| `type`: `noul` / `choice` / `score` | 二元概率、互斥选择或有序评分 | Jev、Plumb、decider、d3、SecJev | [DecisionRobust](https://arxiv.org/html/2610.19118v1) | 目标事件/证据尽量一致；各实现支持情况逐项验收；尚未选定主 type |
| `instructions` | 定义模型回答的问题 | 上述模型 | [Beyond Calibration](https://arxiv.org/html/2609.33209v1) | 极性、否定、语言、措辞可消融；保存完整原文及 hash |
| `questions` 数量/分解方式 | 复合判断拆成原子问题 | 支持多问题请求的模型 | [Same Attack, Different Judge](https://arxiv.org/html/2610.17820v1) | 先规定组合规则；HTTP 请求数、问题数、实际调用/前向及费用分别记录 |
| 校准温度 | 调整候选概率分布尖锐程度 | Plumb、decider；用户称 SecJev 发布包含温度 | [SecJev](https://arxiv.org/html/2610.03073v2)、[Liu 的安全可靠性研究](https://arxiv.org/html/2609.33401v3) | 与生成采样 temperature 分开命名；固定温度值和来源，若拟合仅使用校准集 |
| 输入长度上限/截断策略 | 上下文可接收范围及超长处理 | 自部署模型；官方 Jev 有限制/扩展选项 | 用户未提供对应论文 | 按真实 tokenizer/接口记录；截断、分段/聚合、报错分别处理，记录内容损失 |

对于有限候选 logits、固定候选集、相同正数标量温度的标准 softmax，排序不变，但概率、阈值动作和 Score 期望值可能改变；这不是生成采样温度的一般保证。发布包附带校准温度也不表示我们已经确认其值或适用版本。

**decider 只出现在用户的参数适用例子中，没有进入本次 12 项模型名单，因此不自动添加为受测模型。** Jev-Guard、Laya 与三类专用安全模型也不自动假定支持同样的 Jev 请求字段。参数名相同不代表语义或计算开销相同。

## 4. 下一步需明确的最小信息

1. 将已明确的 Mode A–D 定义落实到各数据集：固定输入字段/前缀切点、输出类别、原生或派生 gold 及标注验证规则。
2. SecJev 尺寸、Laya checkpoint、Plumb revision/readout、Jev-Guard 可接入制品。
3. 六个数据集的固定版本、选取数量与 ID、开发/校准/确认划分及暴露审计。
4. 各受测配置的 type、完整 instructions/请求、分解数与组合规则、校准温度/阈值、长度及超长策略；LLM 生成参数另外冻结。
5. 主 Agent、硬件/端点、重复、并发、步骤与费用/时间预算。

当前 JSON 的对应空值保持 null，不编造样本数、参数、审核或执行状态。本轮未运行模型、未下载新权重、未变更 monitor，也未将此清单标为正式冻结实验。

## 5. 本轮来源检查范围

成功打开 D3-mini、Qwen3.5-4B 模型卡以及 SecJev v2、Jev-Guard v1 论文页面，属于链接/页面级抽查；未逐项核验全部发布日期、性能、接口和许可证。其后对其他来源的批量访问遇到 HTTP 403，未完成全面核查；这不表示对应模型或链接不存在。本文按用户材料记录并保留待核实状态，不能称为完整资料审计。
