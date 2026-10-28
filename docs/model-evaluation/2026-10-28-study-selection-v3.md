# 当前选型：以 MaliciousSkillBench 替换 AgentDojo

日期：2026-10-28（Asia/Shanghai）。类型：用户选型变更与数据适配记录；运行配置未冻结，无新模型成绩。

本版取代[第二版](2026-10-27-study-selection-v2.md)的数据集名单；11 个受测模型/方法不变。机器可读记录见[selection-2026-10-28-v3.json](../../data/agent-security-study/selection-2026-10-28-v3.json)。

| 数据集 | Mode | 当前判断对象 |
|---|---|---|
| AgentHarm | A1 | 输入的用户请求是否有害；属于本研究的输入分类适配，不等同官方 Agent 任务完成评分 |
| MaliciousSkillBench | A2 | 输入的 Skill 文本是否恶意；在加载/使用前检查文本，不执行 Skill |
| MCPHunt | B | B 的操作定义仍待确认；已有完整轨迹判断代码不自动成为已批准的 B 合同 |
| ATBench | C | C 的操作定义仍待确认；已有完整轨迹判断代码不自动成为已批准的 C 合同 |

A1/A2 的数字仅为序号，二者均继承原 Mode A（Input Inspection，输入检查）。它们不另定义为直接/间接攻击两个 Mode。

## 更换依据及准确边界

用户要求移出 AgentDojo，改用 MaliciousSkillBench。这里应区别：AgentDojo 本身可以适配输入检查；本仓库先前实现的是执行前动作授权 gate，不能标成 A2。这一工程差异不证明 AgentDojo 天生不属于 Mode A。旧数据、动态代码、配置与验收证据继续保留。

[MaliciousSkillBench 官方数据卡](https://huggingface.co/datasets/ProtectSkills/MaliciousSkillBench)将任务定义为恶意 Agent Skill 检测，公开 primary 表含 9,740 个身份。其 Skill 文本可作为输入检查对象，与原 Mode A 的位置和可见信息匹配。原始二分类标签用于独立判分，benchmark_id、source、类别及标签不进入模型输入。不得将结果称为执行安全或任意环境中的运行时攻击阻断率。

AgentHarm 的 harmful/benign 原始请求也可以作为输入检查对象，因此能对应 A1 的位置。但这是本研究利用请求及来源分区构造的分类任务；[官方 AgentHarm](https://arxiv.org/html/2410.09024v3)主要让 Agent 使用合成工具完成任务，以有害任务完成程度和拒绝等指标评分。输入分类分数不得冒称官方 harm score。

## 本地数据和代码

已核对相邻工作区的完整官方 `primary.parquet`，没有使用历史 2,137 条子集。固定来源 revision `d4b42ce5766a6e0359c987cf59c1007cb3795a90`，primary SHA-256 `1d6382017f259bde0b699d402318f3c03f16b2e8ed2363a346b77a5465f06a06` 与官方 LFS 元数据一致。连同可取得的原始元数据/划分等 13 个文件，按源哈希核对后复用到 `data/agent-security-study/datasets/2026-10-28/maliciousskillbench/`，获取脚本为 `scripts/prepare_maliciousskillbench.py`。

原始表结构核对为 9,740 条，标签 1 有 7,505 条、标签 0 有 2,235 条；9,735 条提供完整冻结文本，5 条原文 withheld、提供公开脱敏表示。`withheld_text_policy` 仍需明确选 exclude 或 public_sanitized，不能静默将脱敏文本等同原文。样本数、ID、划分及暴露审计尚未冻结；HF 的单一 train 容器也不等于本研究已经确定训练/测试划分。

新适配器只向 Jev/GPT-6 Luna 发送 `{"skill_text":"<原始可用文本>"}`，沿用 choice safe/unsafe。`instructions` 和标签语义仍待确定。当前四基准都采用已有输入/轨迹数据进行判断时，不需要 DeepSeek 主 Agent；其暂定选型保留供后续闭环研究。旧 AgentDojo 配置另存 `configs/security-bench-agentdojo.template.json`。

旧数据 ZIP `jev-agent-security-datasets-2026-10-27-v1.zip` 保持原样，仍含 AgentDojo，不代表本版四基准包；本轮未覆盖或重新上传该包。
