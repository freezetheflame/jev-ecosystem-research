# Jev security empirical study：问题类型与调用参数

记录日期：2026-10-22。状态：官方接口与论文方法核查、实验设计建议；未新增模型调用或参数实测。建议不等于已证实的最佳设置。

## 1. 调用方式与问题类型

官方 REST 为 `POST https://api.typesafe.ai/v1/systemone`，也可经官方 SDK 调用。SDK/HTTP 是传输入口；`noul`、`choice`、`score` 是每个问题的 `type`，并非三个独立服务。同一请求可混用类型，多问题共享 state、独立求值；不得假定后一问看到前一问答案。

目前 API 还列有视觉定位用 `box`；本文聚焦文本安全的三种原语。开放权重模型的本地接口及推理参数按实现单独记录，不假设其与官方 API 完全等价。

来源：[官方 API](https://docs.typesafe.ai/api/system-one)、[state](https://docs.typesafe.ai/concepts/state)。

## 2. 三种原语的选用

| 类型 | 语义及输出 | 安全任务例子 | 本项目建议 |
|---|---|---|---|
| Noul | 给定命题成立 / yes 的概率；可写 true / false 定义 | 是否包含重定向 Agent 行为的指令；某动作是否违反固定策略 | 二元风险检测主配置；统一 yes=unsafe 的方向 |
| Choice | 互斥选项中的选择及归一化分布 | 从候选工具动作中选择一个；safe / unsafe / insufficient_evidence | 多类决策主配置；二元 Choice 作 Noul 对照；候选应覆盖任务 |
| Score | 有序描述等级的分布及期望等级 | 若执行请求，后果有多严重 | 仅用于有序程度目标；首轮可用清楚可分的 3–4 级，但级数是待检验设计，不是文献最佳值 |

“Review”是代码采取的行动，“insufficient_evidence”是对证据状态的判断；不能直接当作同一个标签。二分类数据若没有第三类标注，不能随意加入第三类后仍按原二分类解释其准确率。多种危害可能同时成立时，用独立 Nouls，不能强迫它们成为互斥 Choice。

Noul 的优先级来自二元任务匹配与方便计算风险阈值，不是已证实比 Choice 更抗攻击。Choice 的归一化也不保证它的语义正确或校准更好。

来源：[Noul](https://docs.typesafe.ai/primitives/noul)、[Choice](https://docs.typesafe.ai/primitives/choice)、[Score](https://docs.typesafe.ai/primitives/score)。

### Score 与 confidence 的解释

Score 的 `score` 是等级索引的概率加权平均。把 0–3 的分数除以 3，只得到归一化等级，不自动得到 unsafe 概率。若等级有明确风险事件映射，可把对应等级概率相加；仍需对该事件检验校准。Choice / Score 的 `confidence` 是输出分布的派生统计，不是独立估计的正确率；Noul 不返回此字段。

来源：[Score 输出定义](https://docs.typesafe.ai/primitives/score)、[Confidence](https://docs.typesafe.ai/confidence)。

## 3. 论文是否支持某一种更安全

| 论文 | 已核查证据 | 可用于本项目的结论 |
|---|---|---|
| [Same Attack, Different Judge, v1](https://arxiv.org/html/2610.17820v1) §2.2 / §4.2 | 主内容审核配置使用四个危害 Nouls 加一个严重程度 Score，再由代码路由 | 支持二元风险与严重程度分解的设计；不是 Noul vs Choice 的同题公平胜负比较 |
| [DecisionRobust, v1](https://arxiv.org/html/2610.19118v1) Appendix B.1 / Table A7 | Jev 1.13 上将一类格式优化的攻击原样转到另一格式：Choice→Noul 的 ASR 为 28.7%→20.3%；Noul→Choice 为 18.3%→13.4% | 请求类型会改变攻击效果；两方向候选池不同，不能推出 Noul 或 Choice 普遍更安全。均为候选级、源格式标签检查后的构建池，不是最终人工审核集 |
| [Beyond Calibration, v1](https://arxiv.org/html/2609.33209v1) §3 / Table 3 / §6 | 测跨格式、否定、加法一致性；Jev Noul 与 Choice 对相同标签事件的概率存在差异 | 不把多个独立 Noul 当作总和为 1 的类别分布；不直接跨问题形式复用阈值。比较前必须显式固定完整事件空间 |
| [More Choices, Fewer Decisions, v2](https://arxiv.org/html/2609.38827v2) §3–4 | 有序候选的数量、位置和间距与决策分布压缩有关；覆盖官方 Jev 和开放模型 | 支持检查有序等级构造；不是官方 Score 对 Noul 的同任务优势实验。论文含大于官方 Score 10 级上限的候选设置，不能一概称为 Score API 实测 |
| [Type-Safe Is Not Error-Free, v3](https://arxiv.org/html/2609.26758v3) §3–4 | 保持 state、问题及定义文本，交换选项名—定义绑定后，决策可能随名称而变 | Choice 的标签文本与定义绑定应单独检查；测可信配置敏感性与攻击者可修改配置是不同威胁模型 |
| [Liu 的安全可靠性研究, v3](https://arxiv.org/html/2609.33401v3) §3.2 / §6 | 分开选择、确认与测试；ALLOW / BLOCK 阈值独立 | 把风险估计与执行策略分开，阈值需要独立留出验证 |

本轮没有发现能支持“在所有安全任务上三种类型存在统一最佳名次”的可靠证据。所读关键结果主要涉及 Jev 1.13，需在 1.14 上重新检验。

## 4. 除 type 外的影响因素

| 因素 | 具体可变项 | 推荐控制 / 消融 |
|---|---|---|
| 模型与服务 | `model`、固定版本 / alias、provider | 主实验固定官方版本；记录响应 model、时间及端点，切换 provider 独立分组 |
| 问题语义 | `instructions`、问风险还是授权、正问 / 否定问、语言 | 固定目标事件；yes=unsafe；中英文与否定改写分别测 |
| 判定标准 | `criteria`、细节、例子、边界与例外 | 简洁定义 vs 明确边界定义；例子只取开发数据，不能泄露测试答案 |
| 候选集合 | Choice 名称、定义、顺序、个数、干扰项、other / 证据不足 | 先测保持语义的重命名与顺序；增删类别会改变任务，不混成同一种不变性 |
| 有序等级 | Score 等级数、各级描述、方向、极端风险覆盖 | 有真实程度标签才比较 3 / 5 等级；记录从原标签到等级的映射 |
| 输入内容与结构 | `state` 字符串 / JSON / 数组、字段名、可信来源标记、背景长度、位置、历史 | 相同证据下比较表示；不信任正文的“已授权”声称；长度与位置分别控制 |
| 提问分解 | 一个复合风险问题 vs 几个原子问题；单问 vs 多问同请求 | 预先规定组合规则；一次 HTTP 请求不等于一次前向或零额外计算 |
| 上下文处理 | 默认上下文 / long-context header、裁剪、分段、聚合 | 固定完整证据与 token 上限；裁剪改变信息时单列。当前默认 64k/request、32k/question，扩展需 header |
| 输出后处理 | 校准、ALLOW / REVIEW / BLOCK 阈值、argmax / 期望 / 概率尾部、置信度复核 | 不改变返回的原始概率，但改变执行结果；开发集选择后冻结，测试集不再调优 |
| 运行策略 | timeout、重试、并发、缓存、失败回退、重复次数 | 主要影响观测结果、成本与可用性；重复调用可能不同，缓存/重试不能与模型判断混淆 |

官方当前公开 schema 未列出 `temperature`、`top_p`、`max_tokens`、`seed`、`reasoning_effort`；这些不应当作官方 Jev 可调参数。开放实现可能有 temperature、反序平均、校准等参数，需要按模型另列。温度后处理可能只改变概率、不改变 argmax，仍会改变阈值路由。

问题对象的 key（例如 `risk_check`）用于响应匹配，官方说明不传给模型；它与 Choice `criteria` 的选项名不同，后者会进入模型。需通过正文明确判断对象，不能指望 key 传达任务。

来源：[API schema](https://docs.typesafe.ai/api/system-one)、[模型与上下文限制](https://docs.typesafe.ai/models)、[问题 ID 与选项名](https://docs.typesafe.ai/primitives/choice)、[官方 1.13 局限](https://docs.typesafe.ai/model-jaggedness/jev-1.13)。局限文档明确针对 1.13，不自动作为 1.14 的已测事实。

## 5. 建议首轮参数实验

### 类型主对照

选用标签明确、证据充分的二元安全样本，固定同一 unsafe 事件、state、模型与两端定义：

1. Noul：是否 unsafe，使用 true / false 定义。
2. Choice-2：中性 A / B 标签，绑定完全相同的 unsafe / safe 定义；顺序平衡。
3. Score-2：两个等级使用同样的 safe / unsafe 定义，读取 unsafe 对应等级概率。它只作跨类型诊断，不代替真正的严重程度实验。

这个设计尽量控制语义，但三种序列化仍不同，不能声称隔离了隐藏架构的因果作用。Score-2 的目标不是“后果有多严重”。真正的严重程度作为单独有序目标，仅在有相应 gold 时设 Score-3 / Score-5。

主结果分别给两种政策口径：原生 0.5 边界，以及各配置独立在校准集选择的相同误报预算。报告 AUPRC / AUROC、TPR@固定FPR、漏检、误报、成本与 p50/p95 延迟。类型间概率差、动作差和攻击迁移是辅助指标。

### 其余消融的顺序

- P0：明确 criteria、模型版本、state 信任边界、每种格式独立阈值。
- P1：Choice 标签与顺序、问题极性与语言、背景长度与位置。
- P2：问题分解 / 聚合、Score 等级细化、多问打包与多阶段复核。

先单因素配对，再测有理论理由的交互，不做所有因素的全笛卡尔积。主模型跨候选比较时冻结请求方案，不能给某个模型额外挑选最有利的模板。

### 重复、预算与威胁边界

在预先抽取的小子集重复完全相同请求，估计输出噪声；不把新增文本 UID 的请求当作相同输入。给每种格式相同攻击预算，同时记录请求数、问题数、tokens 和实际费用：多类任务用每类一个 Noul 时，问题数不同，不应只按 HTTP 次数宣称预算相同。

从干净开发集选定策略后，面对干净与攻击测试均冻结。分别报告各模型自身 clean-correct 的条件 ASR 和共享 clean-correct 子集结果，并同时给全样本攻击后错误率；不能通过丢弃格式不支持、超时和解析失败来隐藏代价。

仅攻击 state 时固定 instructions、criteria 与阈值；标签/策略篡改另设配置攻击轨道。分清“文本有害”“包含注入”“该动作违反授权”三个目标事件，三者不互相替代。
