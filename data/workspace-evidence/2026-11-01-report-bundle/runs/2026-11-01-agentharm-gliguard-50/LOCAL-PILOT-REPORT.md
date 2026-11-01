# AgentHarm 50×3：GLiGuard-300M 本地 pilot

类型：**pilot**。150/150 次本地调用成功，0 失败。

## 1. 本地部署

| 项 | 值 |
|---|---|
| 模型 | `fastino/gliguard-LLMGuardrails-300M` |
| 架构 | DeBERTa-v3-base 编码器 + GLiNER2 分类头，约 0.3B |
| 硬件 | RTX 3050 Ti Laptop，4GB；bf16/float32 加载后显存约 0.79GB |
| 权重 | 833,938,108 字节；SHA-256 `03132cef1def4bb172b586e662ffc3c30f76034411fc21cd309dd8f1b627c466` |
| 运行时 | gliner2 2.1.0，transformers 4.57.1，torch 2.2.1+cu121 |
| 服务 | `scripts/local_gliguard_server.py`，POST `http://127.0.0.1:8001/classify` |
| 输入 | AgentHarm 的 `user_request` 原文，不包 JSON、不加 system |
| 参数 | `prompt_safety: [safe, unsafe]`，threshold 0.5 |

## 2. 执行与标签

- 同一 AgentHarm validation 50 item（25 harmful / 25 benign），seed `20261030`。
- 50 × 3 = 150 次；150 次 HTTP 200、解析成功。
- GLiGuard 输出 `prompt_safety` 二分类，没有 controversial 第三类。
- 输入长度：max 145 token、p95 84 token，全部低于 DeBERTa 的 512 上限，未发生截断。

## 3. 指标（50 item 多数票）

| N | TP | FP | TN | FN | accuracy | 95% Wilson | precision | recall | F1 | FPR | FNR |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 50 | 25 | 1 | 24 | 0 | **0.980** | [0.895, 0.996] | 0.962 | 1.000 | 0.980 | 0.040 | 0.000 |

- 49/50 个 item 三次预测完全一致且正确；1 个 benign item 三次都误报。
- 只有一个误报，没有漏检。

## 4. 时间与费用

| 项 | 值 |
|---|---|
| 单次 p50 / p95 | **0.078 / 0.094 秒** |
| 150 次累计 | **12.16 秒** |
| 输入/输出 token | 0 / 0（编码器分类，不生成 token） |
| API 费用 | 不适用（本地） |
| 本地计算 | 未计价 |

GLiGuard 是本次唯一真正“输入输出 token 都为 0”的模型；它不做自回归生成，单次只是一次前向。

## 5. 证据

- `analysis/<version>-multimodel-metrics/`
- `raw/`：150 次原始分类结果
- `telemetry/`：逐调用耗时和 unpriced 状态
- 配置：`data/agent-security-study/preparations/2026-11-01-agentharm-gliguard-50-config.json`

## 6. 复现

```powershell
./.venv-local/Scripts/python.exe scripts/local_gliguard_server.py --port 8001
./.venv-local/Scripts/python.exe -m security_bench run --config data/agent-security-study/preparations/2026-11-01-agentharm-gliguard-50-config.json --run-dir data/agent-security-study/runs/2026-11-01-agentharm-gliguard-50 --resume
```

## 7. 限制

- 0.3B 编码器，50 item / 8 family，不能外推总体性能。
- 512 token 上下文；本批未截断，但更长的输入会静默截断，后续数据集必须检查。
- 只在 AgentHarm 用户请求上测；它不做 AgentHarm 官方 agent 任务评分。
- 本地费用未计价；GPU 电费/折旧未计。
- 不是确认性实验。
