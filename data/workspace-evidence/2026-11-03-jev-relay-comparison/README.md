# Jev 1.14.0：OpenLux 中转重测

2026-11-03；探索性 pilot；AgentHarm Mode A1 输入检查。
沿用原 50 条 validation 输入（25 harmful、25 benign，8 个 family），每条 3 次，串行，无重试。输入 hash、策略、choice safe/unsafe、seed 和判分方式保持一致。旧结果原样保留。本次服务为 GPT 使用的 OpenLux，同一凭证来源，Jev 使用原生 /v1/systemone。

| 通道 | 有效调用 | TP | FP | TN | FN | 多数票准确率 | p50 秒 | p95 秒 | episode 累计秒 | API 估价 USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| official_previous | 150/150 | 21 | 0 | 25 | 4 | 0.920 | 7.250 | 7.704 | 998.326 | 0.00270774 |
| openlux_rerun | 150/150 | 22 | 0 | 25 | 3 | 0.940 | 1.766 | 2.485 | 279.955 | 0.00108310 |

本轮观测 p50 相比旧轮下降 75.6%。这是不同日期、机器和网络条件下的端到端 HTTP 延迟，不能把差值全部归因于中转本身，也不是模型推理耗时。
另有独立 2 条 smoke，均成功，耗时约 1.72–1.76 秒；不计入上表 150 次。共新发起 152 次 API 调用。
费用是原 monitor 价格快照估算，不是实际账单，也不代表总计算成本。OpenLux 快照 model_ratio=0.021、completion_ratio=0、唯一支持组 jev-1 的 group_ratio=0.4，按平台现有计价公式折算输入 0.0168 USD/M，输出 0 USD/M；实际后台路由/账单未独立核验。
完整请求为原模型请求：model=jev-1.14.0，state=原 user_request 状态 JSON，questions.risk.type=choice，criteria 按 safe/unsafe 顺序；instructions 沿用原 AgentHarm 有害请求判定。无附加生成参数，服务端未知默认值仍未知。
TP/FP/TN/FN 按唯一输入多数票计算，正类 unsafe=1。公开且已暴露 validation 仅作开发证据，不是官方 AgentHarm 有害任务执行分数。

## 证据与复现

- 新 pilot：data/agent-security-study/runs/2026-11-03-agentharm-jev-relay-50/
- 独立 smoke：data/agent-security-study/runs/2026-11-03-agentharm-jev-relay-smoke/
- 准备和价格来源：data/agent-security-study/preparations/2026-11-03-jev-relay/
- 各 run 保存原始请求/响应、telemetry、完整 effective-config、环境、必备报告与数据 IDs/hash。
- comparison.csv 为两通道汇总，episodes.csv 为原 300 条逐次记录；results.json 含完整有效模型配置及来源 hash。
- 重跑：在环境中提供 OPEN_API_KEY 后，运行 `python -m security_bench run --config data/agent-security-study/preparations/2026-11-03-jev-relay/pilot-config.json --run-dir <新目录>`。
- 重新汇总：`python scripts/compare_jev_routes.py --out <新目录>`，不会调用模型。
