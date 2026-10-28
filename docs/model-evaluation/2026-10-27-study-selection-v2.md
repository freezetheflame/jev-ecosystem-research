# Agent 安全实验：调整后的模型与数据集

> 历史选型：2026-10-28 用户已用 MaliciousSkillBench 替换 AgentDojo，当前名单见[第三版选型](2026-10-28-study-selection-v3.md)。以下记录保留供溯源。

日期：2026-10-27（Asia/Shanghai）。状态：**当前选型范围，运行配置尚未冻结；不是实验结果**。

按用户提供的两张表更新。2026-10-28 补充确认：A1/A2 都继承原 Mode A（输入检查），数字仅是序号；B/C 含义仍未确定。机器可读记录：[selection-2026-10-27-v2.json](../../data/agent-security-study/selection-2026-10-27-v2.json)。本记录替代[上一版选型](2026-10-27-study-selection.md)的模型、数据集名单及 Mode 分配，历史资料与实验证据继续保留。

来源：用户附图 `codex-clipboard-c8f2f081-9b72-4aa3-9a1a-94005f630d07.png` 和本轮文字回复。表中年份按用户材料记录，未作独立书目核验。

## 模型与方法（11 项）

| 图中分组 | Method | Backend | Tasks |
|---|---|---|---|
| 第一组 | Jev 1.14.0 | 未指定 | 未指定 |
| 第一组 | D3-Mini | 未指定 | 未指定 |
| 第一组 | Laya | 未指定 | 未指定 |
| 第一组 | SecJev | 未指定 | 未指定 |
| 第一组 | Jev-Guard | 未指定 | 未指定 |
| 第二组 | GLiGuard | 未指定 | 未指定 |
| 第二组 | Shieldstral | 未指定 | 未指定 |
| 第二组 | Qwen3Guard-Gen | 未指定 | 未指定 |
| 第三组 | Qwen3.5-4B | 未指定 | 未指定 |
| 第三组 | GPT-6-Luna | 未指定 | 未指定 |
| 第三组 | Claude-Haiku-5.5 | 未指定 | 未指定 |

保留图中顺序与分组。Backend、Tasks 两列原图为空，不补写推测。Plumb-4B 移出当前名单。Shieldstral 与 Qwen3Guard-Gen 未指定具体版本/尺寸，不自动沿用旧选型的 1.0 / 0.6B。其余名称中显式给出的版本或尺寸按原名保留；具体 checkpoint、服务标识及请求配置仍待确定。

## 数据集（4 项）

| Dataset | Year（用户表格） | Mode（暂存代码） |
|---|---|---|
| AgentDojo | 2024 | A2 |
| AgentHarm | 2025 | A1 |
| MCPHunt | 2026 | B |
| ATBench | 2026 | C |

新增 AgentHarm；InjecAgent、R-Judge、SCR-Bench 移出当前名单。A1/A2 同属原 Mode A，1/2 仅作序号，不另行定义为直接/间接攻击两种 Mode。A 的概念继承不代表具体数据字段、标签合同或 prompt 已冻结。新 B/C 仍未定，不能仅因字母相同而继承旧定义。原定义及用户原文保留在[Mode 文档](agent-security-evaluation-modes.md)。

## 执行边界与未决项

本次只调整选型；此前五类参数因素未被本图替换，保留为历史参考，涉及已移出模型的例子不代表仍选用该模型。运行前仍需固定数据版本、条目数与 ID、划分及暴露审计、模型制品、Backend、Tasks、Mode 语义、prompt、判分、阈值及资源预算。

现有离线报告工具的 A/B/C/D 校验属于旧命名空间，本次未修改其历史行为。新 Mode 定义确认后再更新适配与验证；不能直接提交本版 B/C 给旧工具并认定语义一致。

本轮未下载数据或模型，未运行 API 或实验，未变更 monitor。历史数据与已暴露样本的证据性质不因本次选型变化而改变。

## 后续补充：主 Agent 与工程入口

用户随后暂定主 Agent 使用 DeepSeek，并表示还要确认；这不指定具体型号、端点或预算，也不将 DeepSeek 加入本页的 11 个受测安全模型名单。对应运行模板见 [security-bench.template.json](../../configs/security-bench.template.json)，家族以外的参数保持未定。已补充[统一工程入口](../../security_bench/README.md)，无真实模型实验；此补充不冻结 Mode 含义。

用户进一步指定新框架 Jev 请求采用 `choice`，仅有 `safe`、`unsafe` 两项。按返回选项直接判定，不设置 noul 概率阈值。具体数据集 instructions 和其余实验配置仍未冻结；此前 noul 与三 type 历史记录保留。
