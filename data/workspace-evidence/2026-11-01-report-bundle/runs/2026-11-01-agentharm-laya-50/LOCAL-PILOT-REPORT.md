# AgentHarm 50×3：Laya-421M 本地 pilot

类型：**pilot**。150/150 次本地调用成功，0 失败。

## 1. 本地部署

| 项 | 值 |
|---|---|
| 模型 | `convaiinnovations/laya`（根 checkpoint，ModernBERT-large，421M） |
| 权重 | 842,609,210 字节；SHA-256 `891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c` |
| 运行时 | laya 0.4.20，transformers 4.57.1，torch 2.2.1+cu121 |
| 显存 | 约 1.58GB |
| 服务 | `scripts/local_laya_server.py`，POST `http://127.0.0.1:8002/v1/systemone` |
| 接口 | `Agent.system_one(state, questions)`，直接返回 choice/probabilities/usage |
| 参数 | Jev 风格 `choice`，options safe/unsafe；无概率阈值 |

Windows + torch 2.2 下 ModernBert 导入会触发不支持的 `torch.compile`，服务在导入 laya 前把 `torch.compile` 置为恒等函数；推理仍是 eager，未使用编译。

## 2. 执行

- 同一 AgentHarm validation 50 item（25 harmful / 25 benign），seed `20261030`。
- 50 × 3 = 150 次；全部 HTTP 200、解析成功；`usage.truncated=false`，无截断。
- state 是 `{"user_request": ...}` 的 JSON 字符串；questions 的 instructions/criteria 与 Jev 配置相同。
- 输入 22,401 token，输出 0 token（非自回归，不生成）。

## 3. 指标（50 item 多数票）

| N | TP | FP | TN | FN | accuracy | 95% Wilson | precision | recall | F1 | FPR | FNR |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 50 | 7 | 2 | 23 | 18 | **0.600** | [0.462, 0.724] | 0.778 | 0.280 | 0.412 | 0.080 | 0.720 |

- 30/50 个 item 三次全对，20/50 三次全错；没有混合。
- 主要错误是 harmful → safe：25 个 harmful 里只识别出 7 个。

## 4. 时间与费用

| 项 | 值 |
|---|---|
| 单次 p50 / p95 | **0.078 / 0.094 秒** |
| 150 次累计 | **10.88 秒** |
| API 费用 | 不适用（本地） |
| 本地计算 | 未计价 |

## 5. 重要告警

加载时 laya 报告：checkpoint 自带的部分 temperature 值超出 [0.5, 5]，已回退到 0.5，**受影响的 confidence 未校准**。本轮只用 `answers.risk.choice`，不用 confidence 或 probabilities，所以指标不受该告警影响；但后续若要做概率校准，不能直接用这个 checkpoint 的 confidence。

## 6. 证据

- `analysis/<version>-multimodel-metrics/`
- `raw/`：150 次原始返回
- `telemetry/`：逐调用耗时/token
- 配置：`data/agent-security-study/preparations/2026-11-01-agentharm-laya-50-config.json`

## 7. 复现

```powershell
./.venv-local/Scripts/python.exe scripts/local_laya_server.py --port 8002
./.venv-local/Scripts/python.exe -m security_bench run --config data/agent-security-study/preparations/2026-11-01-agentharm-laya-50-config.json --run-dir data/agent-security-study/runs/2026-11-01-agentharm-laya-50 --resume
```

## 8. 限制

- 421M 模型，50 item / 8 family，不能外推总体性能。
- 512 token 上下文；本批未截断，但更长的输入会截断。
- state 以 JSON 字符串传入，而不是 Laya 原生 dict；这是为了让输入与 Jev 组一致，可能不是 Laya 最优格式。
- 没有主 Agent、工具执行或任务效用；这是 A1 输入分类。
- 不是确认性实验。
