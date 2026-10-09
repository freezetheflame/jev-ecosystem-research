# Jev Router 生态：官方服务与社区工具

整理自 2026-10-02 的核查。

---

## 零、先澄清一个常见误解

常听到"x.com 发布了一个使用 Jev 的 router"——**这不是 X（Twitter）公司做的项目**。

它是 **OpenRouter 上线的 `typesafe/jev-router`**（2026-09-25/26 由 @OpenRouter 和 @typesafeai 在 X 上发布，所以容易记成"x.com 发布"），底层跑在 `openrouter.ai/~typesafe/jev-latest` 上。

---

## 一、OpenRouter `typesafe/jev-router`

### 它解决什么

普通 router（含 OpenRouter 自己的 Auto Router）有两个毛病：

1. **按任务类型选模型，不按难度选**——简单的和困难的编码任务拿到同一个模型
2. **每次换模型就丢缓存**——长对话里新模型得把整段聊天记录重读一遍，白花钱

### 核心创新是第二点：缓存感知

Jev Router 只在"换模型收益 > 重读成本"时才换模型；否则沿用同一模型，**只调 reasoning effort**（不丢缓存）。

### 用法

OpenAI 兼容，把 model slug 换成 `typesafe/jev-router` 即可，其余代码不用动。上下文 1M。模型卡上 prompt/completion 价格都是 -1（动态，路由本身似乎是零价格，你只付下游模型的钱）。

### 官方数据，要看清绝对数

- 4 项 agent benchmark、423 个任务：Jev Router 完成 **237**，Auto Router 完成 130，相对提升 82%
- 5 项 benchmark：首 token 中位延迟低于所有被测 router

但 **237/423 的绝对完成率只有 56%**。82% 是相对提升——Auto Router 只有 31%，两个都不算高。而且没公布原始延迟数值，也没公布路由策略细节。

### 三个坑，第一个是硬伤

1. **Jev 调用超时或返回无效输出，请求直接失败，不降级。** OpenRouter 明说了这一点。Jev 从"优化层"变成**硬依赖**——它挂了整个调用链就断。生产环境必须自己 catch 错误并回退到固定模型。
2. **质量降级是隐形的**（Prefactor 的 Matt Doughty）：把请求错配给便宜模型时，返回 HTTP 200，成本遥测上显示为"省钱"，但**答案变蠢这件事逃过了 router 层的所有信号**。你监控完成率和成本，两个指标都在变好，只有用户知道答案变差了。
3. **对比不够透明。** theo 在推文下直接要求公布"没有 router"的基线数据，否则不予评估。另有开发者反映使用量激增后延迟明显上升。

### 隐私做得干净

ZDR 零数据保留，Jev 只读对话文本来选模型和 effort，**附件永不发给 Jev**，支持 `zdr: true`。响应里带 routing metadata 说明为什么这么选。

---

## 二、社区工具：用户常问的两个，恰好是最弱的两个

| 项目 | Star | LICENSE | 更新 | 状态 |
|---|---:|---|---|---|
| `gholtzap/jev-codex-model-and-effort-router` | 3 | **无** | 09-23 停更 | 仅 macOS |
| `miniLV/Jev-Auto-Router` | 8 | — | — | 自称 experimental |

gholtzap 那个设计有想法：Jev 为线程的第一个任务选模型和 effort，然后**把整条线程钉死**（thread pin）以保住缓存；寒暄类消息不触发选路；带菜单栏 App 和配额感知。

但**没有许可证意味着法律上连用都不能用**。

> 提醒：搜索里那几篇讲"Jev Auto Router 可恢复委派、检查点续跑"的中文长文，来自 mhpq.cn / xxmr.cn 这类采集站，内容是 AI 批量生成的软文，别当真。

---

## 三、社区里真正成气候的（GitHub 搜索 "jev router" 共 792 个仓库）

| 项目 | Star | 许可 | 更新 | 定位 |
|---|---:|---|---|---|
| kerpopule/hermes-jev-skills | 991 | MIT | 10-02 | Hermes agent 全套 Jev 能力 |
| **gargpratyush/jev-router** | 518 | MIT | 10-02 | Claude Code + Codex 双 CLI |
| BillionsBobby/JevRouter | 347 | MIT | 10-02 | 模型 / 工具 / 子 agent 路由 |
| **0xNatoshi/jev-codex-router** | 276 | MIT | 10-01 | Codex per-call，工程最严谨 |
| thinkany-ai/autojev | 75 | 无 | 10-02 | Rust，agent 模型路由 |
| yusukebe/hono-jev-router | 51 | MIT | 09-30 | HTTP 语义路由（非 LLM 场景） |
| prismhq/jev-router | 14 | MIT | 09-30 | 基于 LiteLLM |

---

## 四、真正的选型维度：路由粒度

| 粒度 | 代表 | 特点 |
|---|---|---|
| **thread pin** | gholtzap | 一次决策锁死整条线程。缓存最友好，但中途任务变难也换不了 |
| **per-turn** | gargpratyush | 每个用户新轮次决策一次。折中 |
| **per-call** | 0xNatoshi、miniLV | 每次模型调用都决策（含工具调用返回后的续接）。最灵活，缓存代价最高 |

OpenRouter 官方的 cache-aware ≈ **per-turn + 缓存成本核算**，正好卡在中间。

---

## 五、推荐的两个

### 要开箱即用 → `gargpratyush/jev-router`

npm 全局装，`jev-claude` / `jev-codex` 两个命令。它启动的是真实的上游 CLI，**只接管模型选择**——会话、权限、工具、`/compact`、认证全都不动。

状态行显示上一轮用了什么模型和置信度（`⚡ haiku p=0.98`），`/jev-explain` 看路由依据。手动改模型就自动暂停路由。

### 要工程严谨 → `0xNatoshi/jev-codex-router`

它**解决了官方版最大的硬伤**：

- **Fail-open**——Jev 出任何错，本轮继续走安全回退路由。官方版是"失败即失败"，这个是"失败即降级"
- Kill switch：一个哨兵文件立刻停用 Jev
- 双投影：Jev 只看到有界的决策状态，执行模型拿完整上下文——路由判断和执行上下文隔离
- 本地决策日志用于校准，明确写了"从不上传"

而且它很诚实：README 说历史模拟比全 Astra 省约 60%，紧接着标注**"这不是实测的 Codex 配额节省，也不是当前策略的证据"**（见 BACKTEST.md）。这种自我限定在同类项目里少见。

**它的路由策略值得抄**：一次向 Jev 问 4 个独立的 Choice——

1. 是否命中强制 Astra 策略（架构、终审、安全/权限/并发/迁移/公共 API 兼容性/重大性能风险）
2. 最低够用的能力档（Luna → Terra → Sol → Astra）
3. 最低思考深度
4. **路由租期**（one_call / tool_chain / user_turn）

最后那个"租期"概念是巧思——让 Jev 自己决定这个选择管多久。注意第 1 条：那是**用自然语言写的、由决策模型判定的安全策略**，这一点在 `06-security-research-agenda.md` §2 里会再提到。

### 要避开的

gholtzap（无许可证 + 停更）、miniLV（8 星 + 自称 experimental）。

---

## 六、这件事的定性

Jev Router 就是**"把用哪个模型这个判断从 LLM 手里交给决策模型"的工业化版本**。它新加的维度是**缓存成本**，这一点很聪明——多轮长对话里换模型的隐性代价确实容易被忽略。

**值得试**：agent 工作流、长上下文多轮对话、缓存成本占比高的调用。

**别用**：单次短请求（没缓存可省，白加一跳延迟）、对稳定性要求高的生产链路（失败即失败）、数据不能出境的（Jev 是闭源 API，路由决策要过 TypeSafe）。

真要上：并行跑一周 A/B，用固定模型作对照，**监控答案质量而不只是成本和完成率**（比如抽样本让强模型打分）。否则会掉进"质量降级隐形"那个坑。
