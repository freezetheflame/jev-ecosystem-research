# AgentHarm A1：独立输入检查适配器

日期：2026-10-28（Asia/Shanghai）。类型：工程实现、原始输入准备与离线测试；不是模型性能实验。

本适配器按用户当前目标，把 AgentHarm 的原始用户请求作为 Mode A 输入检查对象，比较 Jev 与 GPT-6 Luna 的有害请求识别、时间和 API 费用。它不执行请求，不加载 AgentHarm 工具，不调用 DeepSeek，不生成或声称官方 harm score。

## 数据与判断合同

- 模型输入只有 `{"user_request":"<原始 prompt>"}`；保留原始文本，不自动截断、改写、拼入类别、来源、目标函数或判分说明。
- gold 来自公开 harmful/benign 文件分区：harmful=1=unsafe，benign=0=safe。它是本研究的输入分类 gold，未经过新的独立标签审核。
- source item ID、base behavior ID、split 和 partition 保留在判分记录中，不进入模型输入。变体沿用原始 base ID，不计成新的独立基础行为。
- 只允许显式选择 `validation` 和/或 `test_public`。私有集与 chat 不由本合同隐式代替；空值、重复或未知 split 会报错。每个 split 单独报告，不把 validation 与 test_public 混成一个成绩。
- Jev 固定 choice，候选按 safe、unsafe 排列，直接使用返回选择。GPT-6 Luna 继续采用既有 `{"risk":boolean}` 解析，两边得到同一 user_request 和同一判断问题，risk=true 对应 unsafe。

[独立配置模板](../../configs/agentharm-a1.template.json)仅含 AgentHarm 与两个安全模型，无其他基准路径或主 Agent 依赖。它提供了一份可审阅的英文判断问题草稿和标签语义，标为 draft_not_frozen；phase、划分选择、暴露、模型有效参数、价格与预算仍待明确，模板不能直接启动收费调用。

## 先离线查看实际输入和请求

从仓库根目录执行，输出目录必须不存在：

```powershell
python -m security_bench inspect-inputs --config configs/agentharm-a1.template.json --split validation --out-dir data/agent-security-study/preparations/my-agentharm-validation
```

不需要 API key，也不发送网络请求。输出：

| 文件 | 内容 |
|---|---|
| `inputs.jsonl` | ID、split、纯输入 view 与 hash；实际发送的 state 只使用 view |
| `gold.jsonl` | 独立标签、来源分区、原始 ID 和基础行为 ID |
| `jev-request-example.json` | 第一条输入展开后的完整 Jev 请求；type=choice、safe/unsafe，无 Authorization |
| `effective-input-config.json` | 本次输入准备配置，包括显式覆盖的 split |
| `manifest.json` | 全部确切 ID、数量、来源/产物 hash、draft 状态与零模型调用记录 |

实际已在 `data/agent-security-study/preparations/2026-10-28-agentharm-a1-validation/` 完成 validation 准备：64 条请求，harmful/benign 各 32 条，原始文件 hash 与获取快照一致。这个数量是准备的数据，不是已判分样本；没有模型输出、准确率或调用费用。该目录包含第三方原文，作为本地准备材料排除于 Git。

## 配置后运行与输出

复制模板为本轮配置，明确 split、样本 ID（null 表示所选 split 的全部项）、phase、重复/调度 seed、GPT-6 Luna 实际模型 ID、两模型参数/超时、价格依据、预算及暴露状态。先检查：

```powershell
python -m security_bench doctor --config configs/agentharm-a1.local.json
python -m security_bench run --config configs/agentharm-a1.local.json --run-dir data/agent-security-study/runs/my-agentharm-a1-pilot
```

这两个配置名/目录名是使用示例，不表示已有一份获准付费运行的配置。正式比较前须先完成真实 pilot；确认性运行仍遵守独立冻结协议。

每次调用先保存实际请求、attempt 和来源关联，再保存原始响应及既有 monitor 的计量事件。运行输出继承完整框架的 `raw/`、`events.jsonl`、`cases.jsonl`、`plan.jsonl`、`episodes.jsonl`、环境/代码/价格快照。报告生成新 `analysis/<version>/`，包含：

- `report.md`、`summary.json`：按 split 和模型分组的 TP/FP/TN/FN、accuracy/precision/recall/F1、FPR/FNR、覆盖与失败、时间分布、token、API 估价及未知费用。
- `predictions.csv`：逐项 safe/unsafe 标签、状态、耗时和可估算费用，不把失败解析成 safe。
- `artifact-hashes.json`：原始事实文件校验清单。

费用来自原 monitor，缺失用量或单价不当作零。本地计算未计价。重复执行只在 unchanged 输入/环境下 `--resume`，已完成项不会再次调用；旧请求/失败记录不覆盖。

本轮验收使用临时合成响应及费率，验证单数据集完整计划→调用→报告→恢复流程，以及原始 prompt 保留、无标签泄漏、split 分组和逐项导出。无真实模型 API 实验，不能把这些测试当成 AgentHarm 模型成绩。

29 项离线测试及环境、依赖、模板预检的实际输出见[验收记录](../../data/workspace-evidence/2026-10-28-agentharm-a1-adapter/verification.json)；原始 validation 输入的数量与哈希核对另见同目录 input-preparation-audit.json。
