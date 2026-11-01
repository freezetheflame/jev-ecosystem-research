# Smoke 2026-10-30-smoke-01：因地区限制失败

状态：**failed at transport**。计划 8 个 episode，实际尝试 1 个，有效预测 0 个。

## 实际发生

- 计划：8 条（AgentHarm 2、InjecAgent 2、TS-Bench 2、ATBench 2）。
- 调度先到 ATBench 的 `86`（gold=1, unsafe）。
- 请求时间：2026-10-30T05:53:57.549169+00:00 开始，05:53:58.386040+00:00 结束，墙钟 0.828 秒。
- HTTP 451，响应正文：`{"title":"Typesafe is not available in your region.","status":451}`。
- attempt：`8cb30570f8bd44408715ce196d7b74c7`；原始请求与响应在 `raw/8cb30570.../`。
- 收到 451 后调度器停止，未继续其余 7 条；`stop_reason=transport_failure`。

## 时间

| 项 | 值 |
|---|---|
| invocation 开始 | 2026-10-30T05:53:57.546148+00:00 |
| episode 开始 | 2026-10-30T05:53:57.549169+00:00 |
| 调用结束 | 2026-10-30T05:53:58.382480+00:00 |
| episode 结束 | 2026-10-30T05:53:58.386040+00:00 |
| 单次调用墙钟 | 0.828 秒 |
| 有效样本 | 0 |

## 费用

- 响应没有 `usage`；input/output token 均为未知，不是 0。
- monitor 把这次调用记为 `unpriced_calls=1`，API 估价为 null，不是 $0。
- 没有可计费的完成响应；但“没有 usage”不等于“确认免费”，实际账单需以 provider 侧为准。
- 本地计算未计价。
- 结论：**本轮 API 费用未知；没有产生可核对的 token 计费记录。**

## 原因

Typesafe 按出口 IP 地区封锁，451 在鉴权之前返回，因此这次失败**不能用来判断 key 是否有效**。直连与经本机 7890 代理均不可用（直连 451，代理 403）。

## 下一步

1. 需要把出口切到 Typesafe 允许的地区（VPN / 境外主机 / 合规代理）。
2. 不要 `--resume` 本目录：失败 episode 已被记录为完成，resume 会跳过它。
3. 用新的 `run-dir`（如 `2026-10-30-smoke-02`）和同一份计划重新执行；若配置/计划未变，可直接复用同一 config 新建目录。
4. 成功后检查 `analysis/<version>/summary.json` 的 usage、费用与 p50/p95，并确认 8 条都返回了 safe/unsafe。

## 证据

- `episodes.jsonl`、`events.jsonl`、`raw/<attempt>/`、`telemetry/`
- `analysis/2026-10-30T055358.399606_0000-e2ba6d/report.md`
- `manifest.json`、`pricing-snapshot.json`、`effective-config.json`

本记录不修改 runner 自动生成的 report.md，也不把失败算成模型判断。
