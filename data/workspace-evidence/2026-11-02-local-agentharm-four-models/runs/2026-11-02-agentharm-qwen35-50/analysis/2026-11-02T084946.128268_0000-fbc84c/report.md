# 实验报告：2026-11-02-agentharm-qwen35-50

类型：pilot；状态：complete。

本报告由原始结果和既有 monitor 派生；不是独立标签审核或账单核验。

## 1. 数据集与数量

计划 episodes：150；已记录：150。
确切数据项、任务族、输入 hash 与 gold：`cases.jsonl`；配对/重复及顺序：`plan.jsonl`。
来源版本及暴露：`effective-config.json`；文件 hash：`manifest.json`。

## 2. 时间与费用

逐 episode 墙钟含该任务的主 Agent、安全模块和工具；逐调用耗时及失败计费见 `events.jsonl` 与 `telemetry/`。
各段 invocation 墙钟包含报告前的运行开销，不包括计划生成；暂停间隔不纳入累计墙钟。
API 费用按 monitor 价格快照估算，本地计算未计价；未知费用保持 null。

## 3. 分数、基础计数与覆盖率

| 数据集 | split | Mode | 模型 | 计划 | 有效分类 | accuracy | F1 | API估价 USD | p50秒 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| agentharm | validation | A1 | qwen35 | 150 | 150 | 0.88 | 0.8636363636363636 | None | 0.5319999999992433 |

TP/FP/TN/FN、precision/recall/FPR/FNR、覆盖率、失败及原生 episode 成绩见同目录 summary.json。
AgentDojo 无动作 gold，混淆矩阵标为不适用；仅统计官方任务效用与攻击成功。

## 4. 模型和完整有效配置

`effective-config.json` 保存所有实际配置及参数状态；每次实际请求、返回模型与 usage 另存 `raw/`。
服务端隐藏默认值无法查明，按配置 parameter_status 明确记录；没有伪造 Jev 的采样温度或 seed。

## 5. Prompt、请求与原始记录

实际发送 JSON 字节：`raw/<attempt>/request.json`；原始响应正文：`response.body`。
请求前事件和对应 monitor event 索引：`events.jsonl`；动态状态与工具调用：`traces/`。

## 6. 复现、验收和限制

`source/`、`environment.json`、`pricing-snapshot.json`、`manifest.json` 固定代码、包版本、价格与输入。
入口：`python -m security_bench run --config <相同配置文件> --run-dir <本目录> --resume`。
恢复遇到未决调用、代码/环境/数据变化时拒绝；失败 episode 不自动挑选最好重试。
Per-dataset contracts have different target events; no pooled benchmark score.
API fees are provider-usage price estimates, not verified bills; local compute unpriced.
No calibration, confidence interval or replacement/noninferiority claim is produced.
AgentHarm request classification is not its official agent task-completion benchmark.
Full-trace gold is not action/prefix gold.
