# AgentHarm 50×3：Qwen3Guard-Gen-0.6B 本地 pilot

类型：**pilot**，不是确认性实验。状态：150/150 次本地调用成功，0 失败。

## 1. 本地部署

| 项 | 值 |
|---|---|
| 硬件 | NVIDIA RTX 3050 Ti Laptop，4GB VRAM；i7-12700H；23.7GB RAM |
| 模型 | `Qwen/Qwen3Guard-Gen-0.6B`，bf16 |
| 权重 | `D:/models/qwen3guard-0.6b/model.safetensors`，1,503,300,328 字节 |
| SHA-256 | `4f3ce47ebd968cddb67de08d8764f8ede7c410a7d1fb9e08145a4c7a2f2e5c0f` |
| 运行时 | Python 3.11.1，torch 2.2.1+cu121，transformers 4.57.1 |
| 服务 | `scripts/local_guard_server.py`，OpenAI-compatible `/v1/chat/completions`，端口 8000 |
| 显存占用 | 约 1.12GB |
| 上下文上限 | 32,768（config `max_position_embeddings`） |

模型通过 `hf-mirror.com` 下载；Hub 客户端在本机直连失败，改用逐文件 HTTPS 下载。服务端使用 checkpoint 自己的 chat template，输出保持原文，由客户端解析 `Safety:` 行。

## 2. 样本与执行

- 同一 AgentHarm validation 50 item（25 harmful / 25 benign），seed `20261030`，8 个 base family。
- 50 × 3 repeats = 150 次调用，全部 HTTP 200、解析成功。
- 输入是 `{"user_request": ...}` 的 JSON 序列化；没有 system prompt；`max_tokens=64`，`do_sample=False`。

## 3. 原始标签分布

| 标签 | 次数 |
|---|---:|
| Safe | 48 |
| Unsafe | 78 |
| Controversial | 24 |

Qwen3Guard 是三类模型，必须显式决定 Controversial 的二分类映射。本轮在 2 条 smoke 后、正式 150 次前固定为 **strict：Controversial = unsafe**，并在配置里记录 `controversial_policy=unsafe`。这不是预注册决策，属于 pilot 期间的显式口径选择。

## 4. 指标（50 item 多数票）

| 策略 | N | TP | FP | TN | FN | accuracy | 95% Wilson | precision | recall | F1 | FPR | FNR |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| strict（Controversial=unsafe） | 50 | 25 | 9 | 16 | 0 | 0.820 | [0.692, 0.902] | 0.735 | 1.000 | 0.847 | 0.360 | 0.000 |
| loose（Controversial=safe） | 50 | 21 | 5 | 20 | 4 | 0.820 | [0.692, 0.902] | 0.808 | 0.840 | 0.824 | 0.200 | 0.160 |

两种策略 accuracy 相同，但错误结构相反：strict 一个不漏、9 个 benign 误报；loose 把 4 个 harmful 放走、误报降到 5。三次重复完全一致（41 个 item 三次全对，9 个三次全错）。

## 5. 时间与费用

| 项 | 值 |
|---|---|
| 单次 p50 / p95 | **0.531 / 0.750 秒** |
| 150 次累计 | **81.42 秒** |
| 输入 token | 53,370 |
| 输出 token | 1,533 |
| API 费用 | 不适用（本地） |
| 本地计算 | 未计价 |

本地调用没有 API 账单；GPU 电费/折旧未计。token 数是服务端 chat template 展开后的实际计数。

## 6. 证据

- `analysis/<version>-multimodel-metrics/`：逐 repeat 与多数票指标
- `analysis/<version>-qwen3guard-sensitivity/`：strict/loose 重打分
- `raw/`：150 次实际响应与 usage
- `telemetry/`：逐调用耗时、token、unpriced 状态
- 配置：`data/agent-security-study/preparations/2026-11-01-agentharm-qwen3guard-50-config.json`

## 7. 复现

```powershell
./.venv-local/Scripts/python.exe scripts/local_guard_server.py --port 8000
./.venv-local/Scripts/python.exe -m security_bench run --config data/agent-security-study/preparations/2026-11-01-agentharm-qwen3guard-50-config.json --run-dir data/agent-security-study/runs/2026-11-01-agentharm-qwen3guard-50 --resume
```

## 8. 限制

- 0.6B 模型，50 item / 8 family，不能外推总体性能。
- Controversial 映射显著影响 FPR/FNR；两个策略都报告，不能只挑一个。
- 本地 bf16，无量化；GPU 4GB，batch=1，延迟不代表服务吞吐。
- 没有主 Agent、工具执行或任务效用；这是输入分类 A1。
- 不是确认性实验。
