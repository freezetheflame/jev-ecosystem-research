# 实验代码职责与 monitor 接入

日期：2026-10-25。状态：既有实现核查、独立离线报告工具已验证；新全链路模型运行器尚未接入。

## 1. 保留的现有代码

| 职责 | 现有位置 | 当前处理 |
|---|---|---|
| 时间、token、失败与费用估算 | [jev_skill/monitor.py](../../../jev/jev_skill/monitor.py) | 保留原实现和接口，不复制到本仓库 |
| monitor 用法 | [monitor/README.md](../../../jev/monitor/README.md) | 作为接入依据 |
| 价格表 | [config/resource-pricing.json](../../../jev/config/resource-pricing.json) | 保留；历史价格不是当前报价，运行时另固定该轮价格文件 |
| 静态扫描与对照 | 相邻项目的 bench / jev_skill | 保留历史入口及结果，不当作完整 Agent 闭环 |
| 模拟门控 | 相邻项目的 harness/agb | 仅作已有模拟骨架，不改称真实自主 Agent 实验 |
| 本项目审计与统计 | [scripts/experiment_report.py](../../scripts/experiment_report.py) | 消费已有记录与 monitor 汇总，不调用模型，不改原始记录 |

monitor 原有三个测试已在本次核查中通过，没有修改 monitor、价格表、旧扫描或 harness 源码。核对时 monitor 源码 SHA-256 为 `f1f3d220f87681e79d65d9baf91e7b1e30733f80312c60b4129a42be8fc00c67`；正式实验需重新锁定实际版本。

## 2. 接入约定和能力边界

选定实际运行器后，复用 `@monitored_run` 记录每次进程调用，实际 transport/inference 处复用 `@monitored_call`。已覆盖的调用不得再手工 record 一次。同一进程并发独立实验使用不同进程；嵌套入口沿用同一活动 monitor。

每个实验保存对应 monitor run ID 和原始汇总路径。运行前可通过 `JEV_MONITOR_DIR` 将遥测放到该 run 的 `telemetry/`，通过 `JEV_MONITOR_PRICING` 指定该轮冻结价格表。原始 monitor 文件纳入产物清单；续跑分段按 run ID 去重，不重复计费。

monitor 不保存 prompt/响应正文，它们由实验记录层保存。当前 monitor 原生调用事件没有 episode/call ID；正式运行器接入时需补外围关联记录或小幅扩展元数据并测试，在此之前不声称能精确回溯每个 gate 调用费用。

`wall_seconds` 是单次 invocation 墙钟时间，`call_seconds` 是并发调用耗时之和，不能充当全链路时延。各续跑分段运行时间之和与首次启动到最终结束的历时分别报告，后者可能包含暂停。

monitor 保存的是价格快照估算，不是已核验账单。`known_estimated_cost_usd` 是已知部分；`estimated_cost_usd=null` 表示有未计价调用，不得改为零。本地调用或缺失 usage 也可能导致未计价。API-only 小计需先明确调用归属；无法分离时保持未知。

当前 monitor 不实施预算硬停止，不在请求发出前写开始事件，强杀进程可能遗漏最后一个未返回调用。实际运行器负责开始事件、调度与停止，并考虑在途调用和未知费用。预算停止记 partial。此次未增加硬停止调度器。

## 3. 框架分工

1. 配置与清单：版本、样本 ID、split、重复、配对和科学假设；正式 run 前冻结。
2. 模型适配器：构建请求、调用、保存原始返回；不读取 gold、不算指标、不自行更换模型。
3. 环境运行器：还原初始环境，独立执行 episode，保存轨迹；管理步骤、重试、续跑及停止。
4. monitor：沿用既有计时、用量和估价。
5. 判分与分析：读取事实记录和独立标签；指标代码修改后生成新分析版本。

不为每轮实验复制修改整个脚本。科学变量来自显式配置；adapter、grader 或协议实质变化另开版本。若客户端会覆盖请求 model，记录实际生效 model 与实际请求。gold 不能进入请求构造链。

## 4. 离线报告工具

从本仓库根目录运行，替换实际路径：

```powershell
python scripts/experiment_report.py --run-dir data/agent-security-study/runs/<run-id> --monitor-summary D:/projects/jev/monitor/data/<monitor-run-id>.run.json
```

续跑可重复传 `--monitor-summary`，每个 run ID 只能传一次。工具读取 effective-config、plan、episodes、可选 predictions 与 monitor 原始汇总，生成新的 `analysis/<version>/summary.json` 和 `audit-report.md`。`--out-dir` 必须是新目录，不覆盖旧数据。

plan 每个 episode 必须有 dataset_id、split、evaluation_mode、arm、condition、task_id；结果匹配计划。evaluation_mode 为 A/B/C/D，与 arm 分开；统计分别按 Mode 分组，模式错配或未知 Mode 报错。predictions 额外包含 prediction_id、classification_unit、target_event、gold_label、gold_source、predicted_label、prediction_status。二分类配置给出不同的 positive_label / negative_label。非法输出 status 不能写 ok；错误回退不算模型预测。前缀/动作输入边界和 gold 合同仍需独立验证，新增分组检查本身不验证未来信息泄漏。

工具重算二分类计数和派生指标，检查重复 ID、未知 episode、组别/语义错配、部分覆盖、零分母和 monitor 重复引用。多分类拒绝混入二分类路径。完整模型配置、统计功效、gold 正确性、调用真实性和账单仍需对应验收。结构检查通过不等于科学验证。

2026-10-27 更新后十个离线测试通过，包含命令行导出、拒绝覆盖和 Mode 分组/错配检查；fixture 仅存临时目录，不是实验数据。当前新增的是报告层，不能称新全链路运行器已完成。
