# 11 个选定模型的推理接入与输出映射

日期：2026-10-28。类型：工程适配。状态：离线实现与合成验收；没有真实模型推理、权重下载、部署或新性能观测。模型名单来自当前第三版 selection；未替换未知 API 型号或未选定尺寸。

代码：[adapters.py](../../security_bench/adapters.py)、[传输与 monitor](../../security_bench/models.py)。运行器按 `evaluation_models` 选择模型、逐项随机交错调度，不再写死 Jev/GPT 两组。旧配置缺少该字段时使用配置中除 `main_agent` 外的所有模型。

| 模型 | 推理服务契约 | 输出到预测的映射 |
|---|---|---|
| Jev 1.14.0 | 原生 System One，`state` + `questions.risk`，choice 的选项按 safe、unsafe 排序 | `answers.risk.choice` safe→0，unsafe→1 |
| D3-Mini | 本地部署其原生 `system_one`，HTTP 桥接同上；不能按普通生成模型加载 | 同上；不从概率重新选择 |
| Laya | 固定 checkpoint 的 `Agent.system_one`，HTTP 桥接同上；不使用自动选模型的 Router | 同上；返回 usage 的 truncated / dropped / truncated_questions 时拒绝判分 |
| SecJev | 官方 adapter、decision head、calibration、tokenizer 和匹配 backbone；桥接其 System One 输入/返回 | 同上；不以普通 base LLM 生成结果替代 decision head |
| Jev-Guard | **保留 System One choice 桥接契约，未验证官方发布接口** | 桥接后的 safe/unsafe；不声称该格式是官方原生格式，也不把二分类桥接当作完整策略树系统 |
| GLiGuard | 自建 HTTP classifier 桥接，调用 GLiNER2 `classify_text(text, schema)` | 顶层 `prompt_safety` safe→0，unsafe→1 |
| Shieldstral | OpenAI Chat 兼容服务；官方固定 system；user 中 Instruct / Query / Document | 精确 yes/no；配置 `yes_means` 决定方向；草案 query 问 unsafe，yes→1，no→0 |
| Qwen3Guard-Gen | OpenAI Chat 兼容服务；仅 user 原文，使用 checkpoint 原生 chat template | 唯一的 `Safety: Safe`→0，`Safety: Unsafe`→1；Controversial→解析失败、预测缺失 |
| Qwen3.5-4B | OpenAI Chat 兼容服务，system 为数据集检查指令，user 为可见输入 | 精确 JSON `{"risk":false}`→0，`{"risk":true}`→1 |
| GPT-6 Luna | OpenAI Responses；API model ID 尚未指定 | 同上 |
| Claude Haiku 5.5 | Anthropic Messages；实际 API model ID 尚未指定 | 同上；只解析最终 text，不解析 thinking |

以上是客户端请求和解析能力。**本地服务端/权重加载由用户部署，本轮没有安装这些推理运行时，也没有验证其权重能加载。** 尤其 Jev-Guard 尚缺可核验的发布制品和接口，不能仅凭名称生成可复现实现。`deployment.interface_verified` 必须在真实部署核验后填写 true；模板保留 null。

## 配置与命令

四数据集全部模型：[security-bench-all-models.template.json](../../configs/security-bench-all-models.template.json)。
独立 AgentHarm 全模型：[agentharm-all-models.template.json](../../configs/agentharm-all-models.template.json)。
这两份配置均为草案。沿用原有科学参数、预算、数据划分未冻结的状态。模型 ID、端点、超时、推理参数、checkpoint revision、运行时版本、精度、硬件、上下文上限、服务启动命令和接口核验状态由实际部署补全；不猜测 SecJev、Shieldstral、Qwen3Guard、Laya 的未指定版本/尺寸。参数中不要重复 model、messages、state、questions 等由适配器控制的字段。Claude 需要显式正整数 `parameters.max_tokens`，也不能用 null 发起请求。

离线查看所有请求，不需要 key、模型文件或数据集：

```powershell
./.venv-benchmark/Scripts/python.exe -m security_bench inspect-models --config configs/agentharm-all-models.template.json --out-dir data/agent-security-study/preparations/model-request-preview-01
```

该命令输出合成文本的请求预览，不是实际样本或实验。固定原生 classifier/guard 在 AgentHarm 配置中直接接收 `user_request` 原文；通用 LLM 和 choice 模型接收该字段的 JSON 表示。四基准模板默认把完整可见结构序列化，保留原数据，不自动选取某一条消息。跨数据集更改 `input_field` 必须先确认各数据集实际字段，并进入冻结配置。

配置补全后的运行入口（新建 config 副本，不覆盖模板）：

```powershell
./.venv-benchmark/Scripts/python.exe -m security_bench doctor --config configs/my-agentharm-all-models.json
./.venv-benchmark/Scripts/python.exe -m security_bench run --config configs/my-agentharm-all-models.json --run-dir data/agent-security-study/runs/my-agentharm-all-models-01
```

运行仍需通过数据、价格、配置和冻结条件检查。尚未确定的 B/C 合同不能由模型适配层自动补成已批准定义。

## 本地服务部署边界

`provider: local` 表示自行运行的推理服务，**不只是 endpoint 的地理位置**。向收费代理调用模型必须填真实 API provider 并提供价格，不应写 local。本地 HTTP 仅允许 loopback（127.0.0.1 / localhost / ::1）；跨机器可用 HTTPS。没有认证的本地服务填 `api_key_env: null`；需要 Bearer token 则填写环境变量名。

- D3-Mini / Laya / SecJev：HTTP JSON 接收 `{model,state,questions,...parameters}`。服务端应把 state/questions 交给各自官方决策运行时，返回完整原始 answers、probabilities 和 usage。原生 Python 库不一定自带此 HTTP 路由，需要部署桥接。Laya 默认长度预算可能截断，必须核验服务端设置；客户端会拒绝服务已报告的截断，不会自动分块补跑。
- GLiGuard：HTTP JSON 接收 `{model,text,schema:{prompt_safety:[safe,unsafe]},...parameters}`；schema 中 safe/unsafe 为 JSON 字符串。服务端对固定部署模型调用 `model.classify_text(body['text'], body['schema'], **inference_parameters)`，直接返回完整原始字典，例如 `{"prompt_safety":"unsafe"}`。这是本仓库的桥接协议，不是声称存在官方 GLiGuard OpenAI 路由。
- Shieldstral / Qwen3Guard / Qwen3.5：HTTP JSON 使用 `/v1/chat/completions` 类协议，返回单个 choices、message.content 和 finish_reason。服务须固定 tokenizer/chat template，不得隐式截断、动态切 checkpoint 或加入未记录的 prompt。Qwen3Guard 不套通用 JSON system 提示。
- SecJev 必须保留官方校准和训练 head。Jev-Guard 的 choice 桥接需要真实制品支持后才能核验。二者不能用同名 base 模型的生成式回答冒充。

原生 guard 使用其训练标签体系；GLiGuard 与 Qwen3Guard 不执行共享任意 rubric。它们输出了 safe/unsafe 不代表与 Mode B/C 的授权/历史目标已经语义等价。适配器提供固定输入下的检测输出；各数据集合同与解释仍需单独确认，不能将此实现描述为所有模型已在四基准获得可比官方成绩。

## 解析、费用与记录

拒绝缺标签、冲突标签、重复 JSON key、额外 JSON 字段、字符串/整数 risk、截断、未完成、拒答和工具调用。没有用字符串包含 `safe` 来判断 Unsafe；没有概率阈值或缺标签默认 safe。未决输出保留 raw，episode 记 failed，降低有效判分覆盖率，而不进入 TP/FP/TN/FN。

Anthropic 草案按本机官方 SDK 2.3.0 的源码使用 Bearer 和 `anthropic-version: 2026-10-21`；如实际接入需要旧式 x-api-key，可显式配置 `auth_scheme: x_api_key`。没有用旧的 2023 版本头冒充当前默认。认证只在发送前加入，不写入 raw。原 monitor 每次实际请求只调用一次；代码和接口未修改。Anthropic 如果出现独立的 cache read/write token，由于旧 monitor 无法完整表示写缓存 TTL 计价，保留原 usage，但计价保持未知并停止下一次 API 请求，避免低估。

本地调用仍记录耗时、原始响应与可用 usage，费用为 null / unpriced；不写 local 价格表项，也不因本地未计价而中止整个矩阵。API 未知费用仍触发原停止策略。报告及断点恢复把本地调用与 API 调用分开；本地-only 分组的 API 费用 null 表示不适用，不是计算成本为零。端到端时间包含 HTTP 与服务执行；不包含服务启动前的模型加载，部署元数据另行保存。

## 来源与验收

原始来源快照及 SHA256：[来源目录](../../data/model-adapter-sources/2026-10-28/)。优先核对官方 [D3-Mini](https://huggingface.co/vllm-sr/d3-mini)、[Laya](https://huggingface.co/convaiinnovations/laya)、[GLiGuard](https://huggingface.co/fastino/gliguard-LLMGuardrails-300M)、[SecJev](https://github.com/UESTC1010/SecJev)、[Shieldstral](https://docs.mistral.ai/models/shieldstral-1-0)、[Qwen3Guard](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B)、[Qwen3.5](https://huggingface.co/Qwen/Qwen3.5-4B)、[OpenAI Responses](https://developers.openai.com/api/docs/guides/text)。Qwen3Guard 0.6B 模型卡只用于查接口，不是替用户确定尺寸。Jev-Guard 参考论文 arXiv:2610.18326v1，未将 Open-Jev 代码误当完整 Jev-Guard 发布。

验收入口：`scripts/verify_security_bench.py`。新增测试涵盖 11 模型的请求和映射、坏格式/第三类/截断、Claude 认证、未知缓存计费、连续本地调用，以及 11×4 个合成输入 episode 的调度、分 split 报告、费用与恢复。所有响应和单价都是测试夹具，测试完成不能视作真实模型连通或安全性能验证。

本轮最终[验收记录](../../data/workspace-evidence/2026-10-28-all-model-adapters/final/verification.json)：40 项单元测试通过，7 个离线检查符合预期；全模型模板预检正确报告 not_ready。真实模型调用 0；原 monitor SHA256 与用户指定值一致。最终[11 模型请求预览](../../data/workspace-evidence/2026-10-28-all-model-adapters/final/request-previews/manifest.json)使用合成文本。根目录的早期验收保留，不覆盖；当前证据以 final/ 对应源码哈希为准。
