# Agent 安全实验：调整后的模型与数据集

日期：2026-10-27（Asia/Shanghai）。状态：**当前选型范围，运行配置尚未冻结；不是实验结果**。

按用户本轮提供的两张表更新。用户随后明确 Mode 含义尚不确定，先按表保存，之后可能调整。因此不将新代码映射到旧 A/B/C/D 定义。机器可读记录：[selection-2026-10-27-v2.json](../../data/agent-security-study/selection-2026-10-27-v2.json)。本记录替代[上一版选型](2026-10-27-study-selection.md)的模型、数据集名单及 Mode 分配，历史资料与实验证据继续保留。

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

新增 AgentHarm；InjecAgent、R-Judge、SCR-Bench 移出当前名单。Mode A1/A2/B/C 的语义、可见信息、判断目标及标签契约全部暂留未定。特别是新 B/C 与旧 B/C 字母相同，也不能据此继承旧定义。旧定义及用户原文保留在[历史 Mode 文档](agent-security-evaluation-modes.md)。

## 执行边界与未决项

本次只调整选型；此前五类参数因素未被本图替换，保留为历史参考，涉及已移出模型的例子不代表仍选用该模型。运行前仍需固定数据版本、条目数与 ID、划分及暴露审计、模型制品、Backend、Tasks、Mode 语义、prompt、判分、阈值及资源预算。

现有离线报告工具的 A/B/C/D 校验属于旧命名空间，本次未修改其历史行为。新 Mode 定义确认后再更新适配与验证；不能直接提交本版 B/C 给旧工具并认定语义一致。

本轮未下载数据或模型，未运行 API 或实验，未变更 monitor。历史数据与已暴露样本的证据性质不因本次选型变化而改变。
