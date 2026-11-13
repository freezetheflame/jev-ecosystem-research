# Jev 语义鲁棒性：公开研究与延伸路线

> **后续更新（2026-10-13）：** 已完成关键论文全文与部分源码核查，新增选项通道及授权门控近邻。最新结论与优先级见[鲁棒性与安全报告](2026-10-13-robustness-security-review.md)，具体方案见[pilot 协议](robustness-security-pilot-protocol.md)。本篇保留为前一轮初筛记录，其中“尚未核验”等状态只描述当时进度。

> 调研日期：2026-10-12。状态：文献与研究设计，**未启动模型实验**。与正在进行的 JevOut 实验独立：不改它的脚本、数据、配置或结果。本篇的论文数字均为作者报告，不是本仓库复现结果。

## 1. 问题定义：相似文本是否应产生相似判断？

不能只用文本相似度定义正确行为。应区分：

1. **语义不变**：同义改写、语序变化、可读格式变化，在判断相关事实与判据不变时，决策应稳定。
2. **语义改变**：增加否定、改变授权、执行主体、目标地址、数量或时间，即使只改几个字，也可能应改变判断。
3. **外观自然但可能诱导**：加入背景、意见或权威声称；须核查是否真正改变任务证据，不能默认所有新增上下文都应被忽略。
4. **请求自身波动**：完全相同请求也可能产生不同概率，必须测重复调用噪声，才能归因改写效应。

因此目标不是“让模型永远给同一答案”，而是：**对判断无关的表达变化保持稳定，对判断相关的语义变化保持敏感。**

## 2. 已有研究：不是空白领域

### 2.1 直接相关的 arXiv 预印本

已获取下面前四项的 arXiv 页面及摘要；这里只做摘要级初筛，尚未完成全文、实现与原始预测审计。arXiv 上线不等于同行评审通过。

| 工作与一手入口 | 已公开内容 | 与本研究的关系 / 限定 |
|---|---|---|
| [JevAdvBench: A Benchmark and Black-Box Attacks for Reinforcement Learning for Calibrated Decisions Models](https://arxiv.org/abs/2609.31142) | 812 个类型化问题、66 个场景、9,744 个单编辑变体。以干净决策及相同请求重跑作参照。Jev 1.13.0 的改写效应距重跑基线在 1.2pp 内；追加未经证实意见翻转 12.1% 决策。 | **最近邻工作**：已经研究改写、单输入面扰动与重复噪声。其参照主要是模型原答案，不等于有独立 gold 的正确性评测。不能把“1.2pp 内”写成任意改写都鲁棒。 |
| [JevOut: Natural Context Can Flip Decision Models](https://arxiv.org/abs/2609.30243) | 四个系统、七个数据集；每个决策至多 64 次接受的目标评估，定向优化自然背景，使最初正确的决策转向预定错误选项，报告 61.4%–73.2%。对 250 条成功上下文做盲评，91.6% 获多数评审认可为自然、答案保持且无决定性新证据。 | 属于**自适应上下文攻击**，不是随机同义改写翻转率。数据条件、攻击预算与人工审核比例不能省略；也不能与 JevAdvBench 的单编辑 12.1% 直接比较。现有实验保持不动。 |
| [Fast Models, Slow Evidence: A Paired and Self-Audited Evaluation of System-1 Decision Models for LLM Agent Harnesses](https://arxiv.org/abs/2610.02267) | Jev 与 Laya 在 11 类决策点、7,283 个基础样本及 6,640 个鲁棒性变体上的配对评测，并做跨日复测及流水线自审。摘要报告 Laya 选项逆序翻转 30%。 | 可借鉴输入严格配对、跨日复测与自审。**30% 是 Laya，不是 Jev**；同硬件跨模型延迟公平性与最终任务质量仍需单独分析。 |
| [Beyond Calibration: Do a Typed-Decision Model's Probabilities Obey the Probability Axioms?](https://arxiv.org/abs/2609.33209) | ChaosNLI / PubMedQA 的 160 个样本、480 个否定对。Jev 的 P(X)+P(not X) 与 1 的平均绝对偏差为 0.064，95% CI 0.055–0.072；约为重复调用噪声五倍。 | 测**逻辑概率一致性**，并非仅改写一致性。校准、正确率和概率公理是不同属性。 |

还检索到以下直接相关论文，但本轮仅通过公共目录发现，**未核验它们的原文与数字**，列为下一轮全文筛选候选：

- [Type-Safe Is Not Error-Free: A Constrained Decision Head Follows the Option Name, Not the Rubric Bound to It](https://arxiv.org/abs/2609.26758)：选项名称与判据绑定。
- [Same Scores, Different Decisions: Evaluating JEV and Language Models for Legal Document Understanding](https://arxiv.org/abs/2609.27678)：重复条件下的个体决策一致性。
- [Evaluating and Benchmarking the System One Model Jev](https://arxiv.org/abs/2609.37647)：通用评测及选项旋转诊断。
- [Evaluating System One Models for Agent Security Decisions: Reliability, Calibration, and Selective Automation](https://arxiv.org/abs/2609.33401)：安全判断、校准与选择性自动化。

### 2.2 公开平台上的直接相关项目

#### CITY-Jev / CanITrustU-Jev

一手入口：[GitHub](https://github.com/JiaQiSJTU/CanITrustU-Jev) · [Hugging Face 数据](https://huggingface.co/datasets/KikiNLP/CanITrustYou-Jev)。已读取 README 快照。

- `test-v1`：13 个来源，2,437 个基础问题，每题原始输入 + 五个变体，总计 14,622 个评估记录。
- 五种变化：选项逆序、标识替换、state 格式、无关上下文、**instructions 改写**。不能将它的 instruction 改写结果误称为完整 state 语义改写评测。
- 报告 mean accuracy 与所有六版本均正确的 strict accuracy，并提供弃权相关指标。
- 当前 Jev 报告 mean 66.88%、strict 61.70%，实际计分为 **2,428 个问题 / 14,568 个决策**：10 个保留的验证失败影响 9 题，整组排除。不能把模型行当作完全相同计分样本。
- 限制：项目明确声明大量使用自动化工具、仅部分人工审查；没有穷尽等价性审核，单次运行无重复不确定性估计；存在截断、修复和历史预测复用。旧 2,000 题版本不可与新版本直接比较。
- AAA 将“正确或低置信度”计为通过，不等于普通 accuracy；须一起报告弃权率和有效覆盖。

这是用户问题的另一项**最近邻工作**，因此仅新增五种扰动并报平均翻转率，不足以构成明确新意。

#### JevBench — Metamorphic Coherence Testing

一手入口：[项目站](https://jevbench.github.io/)；已读取静态页面。

- 自称技术报告 / Python 包；页面引用为 Chen Feng、2026 年的技术报告。本轮**未确认有效 arXiv 编号**，不将页面的 alphaXiv 文本标识当成 arXiv 论文号。
- 50 条关系，五个维度：表达、batch 独立性、概率测度、逻辑顺序、候选集合条件化。
- mini 集为 240 个案例、12 个领域、1,200 个测试；变换只作用于问题侧，不改 state。
- 采用概率差异容差 0.05；这是该项目规则，不自动成为本研究的生产门槛。
- 项目强调：不看输入、永远输出均匀分布也可能取得高一致性，故必须并列测正确率。页面实际数值部分动态加载，本轮不引用未获取的排行榜数字。

**同名消歧：**它不是原仓库研究的 [Benchmark Heaven / fstandhartinger JevBench](https://github.com/fstandhartinger/jevbench)。后者测准确率、校准、速度和成本；不能合并两者分数、版本和样本。

#### Awesome Jev Robustness 与独立审计

入口：[Yifan-Lan/awesome-jev-robustness](https://github.com/Yifan-Lan/awesome-jev-robustness)。已读取 README；其自报快照 2026-10-07、146 项，主要针对 `jev-1.13.0`。

目录覆盖表达、选项、重复请求、语言、批量、注入、校准与弃权，可作为**检索线索，不能替代原研究证据**。目录本身提醒，多数是小预算、短周期独立试验，不应把条目数量视为成熟证据数量。

优先追踪的公开项目（未审计实现，不引用目录二手数字）：

- [jujumilk3/jev-calibration-audit](https://github.com/jujumilk3/jev-calibration-audit)：重复噪声、否定、原语、选项、语言与批量审计。
- [RastislavDujava/jev-classification-prompting](https://github.com/RastislavDujava/jev-classification-prompting)：criteria 表达与分类结果。
- [willkelly/jev-evaluation](https://github.com/willkelly/jev-evaluation)：预注册评测与任务间校准差异。

### 2.3 可借鉴的通用方法

已取得原始 arXiv 摘要：

- [CheckList: Beyond Accuracy: Behavioral Testing of NLP Models（2020）](https://arxiv.org/abs/2005.04118)：最小功能、不变性、方向性测试；适合组织“应稳定 / 应改变”的行为矩阵。
- [TextFlint（2021）](https://arxiv.org/abs/2103.11441)：通用与任务相关变换、对抗样本、子群与多语言评估。可以借鉴变换生成与审核，但不是 Jev 鲁棒性已经被证明的证据。

## 3. 我们的可辨识延伸

### 暂定主题

**Jev 的决策边界鲁棒性：语义不变性、关键变化敏感性与操作阈值稳定性。**

这是一项拟议路线，尚未穷尽文献确认新颖性；不能宣称首次。

与既有工作的区别应落在：

1. **从问题侧改写到 state 本身**：固定判据与选项，分别测陈述改写、证据顺序、格式和背景；再单独改变 instructions / criteria，避免多个输入面混杂。
2. **等价对 + 关键变化对**：同一基础案例既生成保留含义的版本，也生成明确改变授权 / 行为 / 风险的最小对照。稳定但迟钝不算鲁棒。
3. **跨操作阈值**：即使 argmax 不变，风险概率从 0.79 到 0.81 也可能触发不同复核策略；同时检查自动放行、拒绝和升级的变化。
4. **独立标签与重复噪声**：原版正确与错误均保留，分别统计对→错、错→对、错→错；不把稳定错误奖励为安全。
5. **中文安全判断**：将中英文、人类自然改写、术语与主体指代纳入分层分析，但中文本身不是自动的新颖性证据。

## 4. 后续 pilot 设计（待确认，不执行）

### 4.1 请求与数据隔离

- 只新建未来的 `data/jev-semantic-robustness/` 与独立评测脚本；当前不创建实验结果或修改共享配置。
- 不读取正在写入的 JevOut 日志作为统计输入，不复用其结果文件名、UID 命名空间或运行队列。
- 将固定版本的许可允许数据复制为独立快照再使用；不原地加工 JevOut 数据。实验执行时另确认 API 授权、预算、外发许可及与现有任务的限流协调。

### 4.2 初步矩阵

建议先构建 **60 个基础案例**，覆盖工具动作、RAG 证据、安全内容三类，每类 20 个；合理平衡正负标签，并另设模糊 / 信息不足组，不混作确定 gold。

每题：原始请求 3 次完全相同重跑，4 个独立等价变体，2 个有明确预期变化的最小对照，共 **540 个初始单问题请求**。这只是预算估计，不保证统计功效；若噪声较大，应按预定规则提高重跑次数。

- 等价变体：同义改写、语序 / 主被动变化、格式 / 分段、判断无关的背景。
- 最小变化：否定 / 授权主体、行为对象 / 目标域名等；按具体判据确定是否应翻转或仅方向变化。
- 一次只变一个因素；选项集合、映射与阈值保持固定。
- `noul` 与 `choice` 首轮分组，不因二者原语表达看似等价就合并概率；`score` 后续单独处理量表。
- 对选项顺序 / 名称变换，先映射回语义类别再比较概率与答案。

### 4.3 变体审核

LLM 可辅助生成，但不能独自判定所有等价性。建议冻结：原文本、变换类型、改动位置、gold、预期关系、独立审查意见及置信程度。

审核至少检查：否定与数量、时间、主体、权限、指代、因果、引语与指令身份、是否添加能决定答案的新证据。双审分歧进入争议组；报告过滤比例，不能事后按模型表现挑样本。

### 4.4 指标

设原请求为 x、等价变体为 T(x)，概率向量先对齐语义标签。

| 指标 | 定义 / 注意事项 |
|---|---|
| 完全相同请求噪声 | 重跑间类别翻转、概率绝对差与阈值跨越；相同 API 标识不保证后台 checkpoint 不变。 |
| 等价变体翻转率 | `mean[decision(x) != decision(T(x))]`，与重跑基线并列。不要机械减法后就称为纯因果效应。 |
| 概率漂移 | 二元 `abs(p(x)-p(T(x)))`；多类 `0.5 * sum(abs(p_i(x)-p_i(T(x))))`（总变差）。 |
| 准确率与严格正确率 | 每版正确率，以及一题所有等价版本均正确的比例；原版错误也应纳入。 |
| 关键变化敏感性 | 在预先定义“应改变 / 应方向移动”的最小对照上评估，不强制任何词变化都应翻转。 |
| 操作一致性 | 固定决策策略后，自动放行 / 拦截 / 升级是否改变；同时报告误放行与误拦。 |
| 选择性风险 | 已接受样本错误率与 coverage 联合报告；不以全部弃权取得的高分代表高能力。 |
| 成本与错误覆盖 | 实付 / token / 延迟、失败与重试；缺失不能按安全或正确处理。 |

阈值及变换策略在独立校准样本确定，评估集冻结；按基础案例分组 bootstrap，不能把同题多个变体当作独立样本夸大置信度。随机化原版与变体调用次序，记录时间、精确请求 hash、原始答案、返回模型标识、端点、截断与重试；初步估计之后再决定规模。

## 5. 结论与下一步

**已有直接研究，尤其 JevAdvBench、CITY-Jev 与 metamorphic JevBench。** 下一步应先精读它们的变换实现、标签 / 等价性审核、重复基线与公开预测，确定哪些输入面和操作风险仍未充分覆盖，再启动独立 pilot。

已有证据不能简单概括为“Jev 改写鲁棒”或“Jev 很容易翻转”：无预算改写、自适应上下文优化、选项修改与逻辑关系检验，是不同条件下的问题。

## 6. 来源与复现边界

本轮主要检索 `Jev robustness/paraphrase/consistency`、`JevOut arxiv`、`Jev robustness site:arxiv.org`、`JevBench coherence`；使用 arXiv、项目 README、项目站与公共目录筛选，不是系统综述。

原始取证目录：[`data/jev-robustness-literature/`](../../data/jev-robustness-literature)。

- `sources.json`：首批 arXiv / GitHub 来源、UTC 时间、URL、字节与 SHA-256。
- `supplemental-sources.json`：概率公理、coherence 项目站、CheckList、TextFlint 的同类记录。
- `*-abstract.txt` / `.html` 与项目 `.md`：摘要、原始页面、README 快照。
- `extra-paper.html` / `extra-paper-abstract.txt`：检索碰到的 PixelJev 视觉模型论文（2609.29283），不是托管 Jev 文本改写鲁棒性直接证据，未纳入核心表。

网页提取工具受本机代理地址安全检查阻挡后，用普通 HTTPS 下载公开页面取证；未修改工具安全设置。外部来源内容权利仍归来源方，不自动适用本仓库 MIT 许可。本轮未调用 Jev、未产生新模型预测、未复现论文 headline。
