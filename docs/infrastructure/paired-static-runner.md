# 通用 Jev / LLM 静态配对入口

日期：2026-10-27。状态：代码已实现，离线工程测试通过；**没有用新入口调用真实模型**，不是新增研究结果。来源见 [paired-source.json](../../framework/paired-source.json)。本页描述新增入口，既有三种 type 的历史入口继续保留。

当前范围已更新为[第二版选型](../model-evaluation/2026-10-27-study-selection-v2.md)：11 项模型/方法、4 个数据集。新 Mode A1/A2/B/C 的含义未确定，不能直接运行。本入口下述 A/B/C/D 仅对应历史合同，配置必须显式声明 `evaluation_mode_namespace=legacy_agent_security_abcd_2026_10_27`；缺失或使用新版待定命名空间均拒绝准备，避免新 B/C 被误解释。模板的 namespace 保持 null，不自动批准旧合同用于新版研究。

## 能跑什么，还缺什么

| 工作 | 当前能力 | 开始前仍需准备 |
|---|---|---|
| 同批固定输入，Jev 对 LLM 分类 | 新入口支持；冻结数据/配置、配对调度、原始记录、费用时间、混淆矩阵 | 标准化 JSONL、准确标签语义、有效模型 endpoint/key、明确参数与价格 |
| Jev 官方接口 | 支持 noul、choice、二级 score；可显式发送长上下文 header | 本轮 type、prompt、阈值及长度限额；实际调用验收 |
| 云端或本地 LLM | 支持 Bearer 鉴权的 Chat Completions 兼容服务 | 实际模型部署、完整 `/chat/completions` endpoint、该模型支持的参数 |
| 原生 Anthropic / Responses / 本地专用分类头 | 尚未接入 | 独立适配器；不能只改 model 名假装兼容 |
| 当前四个原生 benchmark 文件直接输入 | 尚不支持自动识别 | 每个数据集的固定版本转换器、可见字段与标签审计；转换代码需单独版本化 |
| AgentDojo 等真实 Agent 闭环 | 尚未接入 | 主 Agent、工具环境、状态重置、攻击位置、动作前 gate、任务/攻击判分器 |
| 正式替代结论 | 当前入口仅 smoke / pilot 描述统计 | 按协议冻结确认设计、足够独立任务族、配对区间/非劣分析与效用证据 |

所以，**有 benchmark 文件还不够；有完成适配的数据、模型配置和凭证后，可以先做静态配对实验**。A–D 是可见信息与判定时机的合同，不能靠填一个 Mode 字母就完成适配。静态 B 回放不证明在线阻断有效；C 必须去掉未来信息。完整轨迹风险标签不能复制成每个动作/前缀的标签。

## 输入合同

每个 run 只使用一个数据集、split、Mode 和问题；模型可以有多个，每个样本每臂一次请求。所有 JSONL 行都参与，无隐藏筛选、自动抽样、重复或分片。最多 100 行的限制可用 `--allow-large` 明确放开；仍受配置 `max_calls` 约束。

| 字段 | 含义 |
|---|---|
| `id` | 本次输入中唯一条目 ID |
| `original_id`、`task_family` | 原始轨迹/任务及相关样本聚类键；派生前缀不得冒充独立任务 |
| `state` | 最终给模型的字符串；可信任务/政策与不可信内容的边界由转换器明确构造 |
| `condition` | clean / attacked 或准确的来源条件；不从标签猜测 |
| `label` | 1=所定义的风险事件成立；0=不成立；null=缺标签，不计算该条混淆矩阵 |
| `gold_source`、`gold_validation` | 有标签时必填；标注来源及验证记录引用，不把 AI 生成当人工审核 |
| `label_scope` | 有标签时必须与 Mode 相同；这只是显式合同检查，不验证标签真伪 |
| `cutoff`、`visibility_validation` | B/C 必填，说明执行前/历史前缀切点与可见性检查依据 |

模型请求构造函数只读取 `state`、冻结问题及 LLM system prompt。条目 ID、label、gold 及来源元数据不传入模型。若转换器把答案写进 state，运行器不能自动识别；仍需审核。数据源、revision、split、许可、原始条目数及未知原因、选择规则、暴露情况在配置中记录。每臂保存同批 ID；执行顺序按本地 seed 打乱样本块，并在块内打乱模型次序。

## 配置和命令

从 [paired-config.template.json](../../framework/paired-config.template.json) 另存本地配置，补齐 null。模板不是已批准实验。必须写清楚问题及 YES/NO 的风险语义、Mode、标签单位、曝光、模型版本局限、超时、输入字符限额、调用/运行时长上限和实际发送参数。`parameters={}` 表示没有额外参数发送；`unsent_defaults` 必须交代服务端默认值的未知范围。seed 只管调度，不冒充服务端推理 seed。

LLM system prompt 来自历史 YES/confidence 合同的改写，见 [prompt 文件](../../framework/prompts/llm-yes-confidence.txt)。最终内容冻结在 effective-config。模型须返回布尔 `answer_yes` 与 0.5–1 的选择置信度。LLM 预测采用该布尔答案；Jev choice 采用原生选项（含平局），noul/二级 score 采用冻结阈值。LLM 自述置信度不当作校准概率，也不与 Jev 概率做校准优劣结论。

在仓库根目录执行；以下路径是待替换的本地路径：

```powershell
# 1. 无 API：验证输入、冻结配置/样本/执行顺序和代码快照。
python -m framework.paired prepare --data <normalized.jsonl> --config <run-config.json> --workspace D:/projects/jev --out framework/runs/<new-run-id>

# 2. 实际模型调用，会产生费用；须先检查上一步产物。
python -m framework.paired run --out framework/runs/<new-run-id> --env-file <private-env-file>

# 3. 无 API：从原始记录重新生成一个独立分析版本。
python -m framework.paired report --out framework/runs/<new-run-id>
```

当前 worktree 不会自动读取主项目的 `.env.local`。进程环境或显式私有 env 文件中需有配置 `key_env` 指定的变量；不把 key 放进 JSON、命令参数、Git 或报告。环境变量优先于文件值；不自动换 key。HTTP/HTTPS 代理沿用进程环境，值只记哈希；准备与运行环境不同时拒绝续跑。离线模板中的 `example.invalid` 仅出现在单元测试，不是模型服务。

官方长上下文由 Jev 后端 `headers` 显式设置，例如 `{"TypeSafe-Danger-Zone-Long-Context":"true"}`。是否启用属于该轮固定配置；不会超长失败后偷偷打开。`max_input_chars` 是客户端字符拒绝上限，不是 tokenizer 上下文上限；服务端超限会保留为失败，无自动裁剪/分片。不同模型超限不能删除后只报有效样本成绩。

价格 `pricing` 使用原 monitor 的 `provider:model` 键及费率结构。`{}` 代表价格未知；要估价，应填已核验日期、来源与缓存假设。可参考本仓库 `framework/pricing/` 的历史快照，不能默认是之后实验日期的报价。若返回模型 ID 与请求不同而无对应价格，费用保持 unknown。费用是 API usage 估价，未与账单核验；本地计算未计价。

## 记录、失败与续跑

每轮保存：

```text
effective-config.json       实际模型/参数、问题、完整 LLM system、Mode 与数据合同
dataset.jsonl / plan.jsonl  确切样本及全部配对 cell 和执行顺序
manifest.json / code/       输入/源码哈希、完整相关源码快照（不复制 monitor）
environment.json            Python/OS/硬件可得信息；无凭证环境变量转储
events.jsonl                请求前持久化 started、完成和停止事件
raw/                       实际请求字节、完整原始响应；凭证回显脱敏并标记
results.jsonl               逐 cell 预测/错误、耗时、返回模型、原始文件哈希、遥测关联
telemetry/                 原 ResourceMonitor 调用与汇总、每次调用的价格快照
invocations.jsonl           每个续跑段的 monitor run ID 和环境
report.md / reproduce.md   必备报告及复现命令；未取得字段明确说明
analysis/<version>/        每次分析独立保存 summary、报告和输入/分析源码哈希
```

报告覆盖[必备模板](../../data/agent-security-study/report.template.md)的六类内容。汇总包含原始/使用/有效数量、确切 ID、各类标签数、各臂 TP/FP/TN/FN 和覆盖率、全部已完成请求的延迟/usage/费用。主 Agent、工具执行、任务效用、ASR、CPU/GPU 峰值和能耗没有在静态入口测量，明确为 NA/unknown，不生成假值。未开始的准备报告没有模型观测。

新 transport 没有 `monitored_call` 装饰器，由运行器对每次实际请求调用一次原 `ResourceMonitor.record`。通过 monitor run ID + 调用索引精确关联 cell，不重复计账，也不修改 monitor。解析错误仍保留已发生用量。已知费用小计与有未知项的总估价分开；不把 monitor 小计再与逐条费用相加。

串行执行、不自动重试。401/402/403/451 停止后续调用；其他错误落盘后继续。每次调用前检查调用数和累计 invocation 时长，正在执行的请求受该后端 timeout 控制，可能越过调度时长上限。**没有金额硬预算停止，也不是 monitor 自带的预算强制器。**

续跑先核对配置、数据、代码、Python/系统/代理哈希与完成记录的原始文件哈希；完成项（包括失败）均跳过。存在 started 而无完成记录的调用时停止，需核对原始记录和服务端账单，不自动重发。单 run 的排他锁防止同时启动两个执行进程；强杀残留锁需先确认旧进程已结束，并处理不明调用，再移除。该检查不是不可篡改或调用真实性证明。

更改 prompt/model/threshold/data 或修补解析器后另开输出目录；旧数据不覆盖。源码不同可从保存的 `code/` 目录恢复原版本入口。报告每次生成新的分析目录；根 `report.md` 只是最新派生视图，旧报告仍保留。原始调用失败不可通过手改结果变成成功。

## 验证状态

新增离线测试覆盖请求不读取 gold、Mode/切点/超长检查、原生 choice 平局、LLM 答案方向、真实本机 HTTP 边界、长上下文 header、凭证回显脱敏、用量/未知费用、错误/部分完成、续跑、中断不重发、原始文件变化拒绝和并发执行锁。fixture 仅在临时目录；不是模型实验。

```powershell
python -m framework.run --workspace D:/projects/jev test
python -m unittest discover -s scripts -p 'test_*.py' -v
```

集成测试需要 `JEV_WORKSPACE_ROOT` 指向保留的外部 monitor，默认当前机器的 `D:/projects/jev`；缺失则 skip，不假装验证过。真实 Jev/LLM、网络服务版本及具体 benchmark 转换器仍需在明确新版 Mode、选定首轮数据和模型配置后做有记录的 bounded smoke。

本机发布前验收：新增 14 项（含新版 Mode 不继承旧语义回归）、历史框架 8 项、既有报告层 10 项，共 32 项全部通过，无 skip；原 monitor 源码哈希不变。没有新增模型调用或 API 实验费用。
