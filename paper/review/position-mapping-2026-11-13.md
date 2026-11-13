# 五类检查位置 × 数据集的对应核对（2026-11-13）

核对依据：五套数据在 Packy Jev 战役里的 cases.jsonl 实际 view 字段、gold 字段与评测单元；
以及 data/infrastructure/full-benchmark-operations.md 的 Mode 合同。

## 0. 结论

这张表**基本成立**，但直接照抄会出三个问题：

1. **单位不同**：request/item、step、trajectory、response 混在一起；表里若没有 unit 列，读者会以为五者可比。
2. **标签语义不同**：请求有害性 / 注入存在性 / 动作安全性 / 轨迹 rogue / 回复有害性，不能合并成一个分数。
3. **StepShield 被叫作 Action Inspection 不准确**：它实际是**前缀监测（in-flight / prefix monitoring）**，不是单动作检查；建议改名为 In-flight Action Inspection（Prefix Monitoring）。

## 1. 逐行核对（判官实际看到什么）

| 位置 | 数据集 | Mode | 判官实际可见 | gold | 单元 | 判定 |
|---|---|---|---|---|---|---|
| User Request Inspection | AgentHarm | A1 | 仅 user_request | harmful / benign | 请求条目 | **成立（adapted slice）** |
| External Content Inspection | InjecAgent | A2 | user_request + tool_response | 该 tool response 是否含注入指令（我们跑的是 positives-only） | 条目 | **成立，但无原生负类** |
| Tool Call Inspection | TS-Bench | B | user_request + history + tools + candidate_action | 候选动作 safe/unsafe/unknown(0.5) | 单步 | **成立** |
| Action Inspection | StepShield | C | task + 已观察前缀（逐步）；轨迹级 gold + divergence_step | 轨迹是否 rogue | 轨迹（逐步判定→首次告警） | **成立但应改名：前缀监测** |
| Response Inspection | WildGuardTest | E | user_request + assistant_response | response_harm_label | 回复条目 | **成立，但不是 agent 自身输出** |

## 2. 每一行必须写的限定

**AgentHarm（User Request Inspection）**
- 原生 AgentHarm 是 agent 任务基准（工具调用、官方 harm/task-completion 分数）；这里只用了**请求文本的有害性分类**，是 adapted slice。
- 论文不能写成“AgentHarm 上的 agent 安全分数”，也不能声称覆盖其工具/执行部分。
- 好处：view 确实只有 user_request，位置定义是干净的。

**InjecAgent（External Content Inspection）**
- 判官看到 user_request + tool_response；gold 是“tool response 中是否含第三方注入指令”，不是“动作是否会执行”。
- 我们当前跑的是 **positives-only**（全部 gold=1），所以只能报检出率/FN，**没有 FPR/specificity**；若要 balanced 指标，需要构造配对中性化负例（派生负类）并单列。
- 这条限制必须写进表注，否则 reviewers 会问“FPR 呢”。

**TS-Bench（Tool Call Inspection）**
- 判官看到 user_request + history + tools + candidate_action；gold 是候选动作本身是否 unsafe。
- 评测单元是**单步**（来自轨迹的步骤），不是整条轨迹；0.5 是争议项，需单独报覆盖率；三个来源域（ASB/AgentHarm/AgentDojo）要分开报，不建议只报 pooled。
- 这正是 Mode B 的原生用法，适配度最高。

**StepShield（Action Inspection）**
- 判官看到 task + 已观察前缀；每次在前缀上判，轨迹级别由“首次告警步”决定；gold 是轨迹 rogue + divergence_step。
- 它不是“给定一个候选动作判安全”，而是“在执行过程中持续监测”；指标含 EIR@3 / IG / lead（告警时机），这些是单动作位置没有的。
- 建议表中改名为 **In-flight Action Inspection (Prefix Monitoring)**，否则与 Tool Call Inspection 混淆。

**WildGuardTest（Response Inspection）**
- 判官看到 user_request + assistant_response；gold 是 response_harm_label。
- WildGuardTest 是通用 moderation 数据，不是 agent 自己产生的回复；如果论文说“Response Inspection”，要说明这是**回复内容审核**，不是“agent 执行后行为的后果”。
- 16 条 unknown 不进二分类分母；prompt-harm（Mode A1）不在本表（已从正式汇总删除）。

## 3. 建议的论文表格（可直接改）

| Position | Dataset (mode) | What the judge sees | Gold / label | Unit | Protocol / caveat |
|---|---|---|---|---|---|
| User Request Inspection | AgentHarm (A1) | user request | harmful vs benign | request | adapted slice; not the native agent harm score |
| External Content Inspection | InjecAgent (A2) | user request + tool return | injected instruction present | item | positives-only in our runs: report detection rate, no FPR |
| Tool Call Inspection | TS-Bench (B) | request + history + tools + candidate action | safe / unsafe / unknown | step | step-level from trajectories; report per source domain |
| In-flight Action Inspection | StepShield (C) | task + observed prefix | trajectory rogue + divergence step | trajectory | prefix monitoring; timing metrics EIR@3 / IG |
| Response Inspection | WildGuardTest (E) | user request + assistant response | response harm | response | general moderation; not the agent's own output |

## 4. 还需要补的两列/两句话

- **Unit 列**必须有（request / item / step / trajectory / response），否则五位置不可比。
- **Attacker model 必须说明**：不可信用户（AgentHarm）、第三方内容（InjecAgent）、agent 轨迹/动作（TS-Bench、StepShield）、模型输出（WildGuard）。五个位置不是同一个攻击者。
- 表注里写：五类位置**不合并总分**，各自报指标与分母（与 docs/model-evaluation/agent-security-experiment-protocol.md 一致）。

## 5. 引用核对（重要）

- **StepShield**：官方 README 写的是 “paper preprint forthcoming”，没有 arXiv 号；只能引用仓库 + 作者（Felicia et al., 2026），或等 preprint 上线。
- **TS-Bench / ToolSafe**：仓库 https://github.com/MurrayTom/ToolSafe；本地未记录正式论文条目，引用前需核对作者/年份/会议。
- **AgentHarm**：HF dataset ai-safety-institute/AgentHarm；正式论文引用需另行核对（本地 acquisition 索引只记录 HF 来源与 revision）。
- **InjecAgent**：仓库 https://github.com/uiuc-kang-lab/InjecAgent；论文引用需核对。
- **WildGuardTest**：HF allenai/wildguardmix；WildGuard 论文引用需核对。
- 不要在表里留空的 \cite{}；StepShield 和 TS-Bench 的条目本地没有可引用的正式信息，必须补。

## 6. 一句话回答

**符合，但不是“直接对应”而是“每个位置一个适配后的数据集”**：AgentHarm 是请求切片、InjecAgent 是正例检测、TS-Bench 是单步动作、StepShield 是前缀监测（建议改名）、WildGuardTest 是回复审核（非 agent 自身输出）。
把 unit、label、attacker、adapted/native 四件事写进表，分类就站得住；不写，reviewers 第一轮就会打“五个位置不可比”。