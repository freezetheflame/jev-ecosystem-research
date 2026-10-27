# Jev 静态评测框架导出

2026-10-27 增补：[通用 Jev / LLM 静态配对入口](../docs/infrastructure/paired-static-runner.md)已实现，使用标准化 JSONL 与显式模型配置，独立保存完整实验记录，保留原 monitor。入口为 `python -m framework.paired`；不再绑定下面历史入口的 AgentDojo 数据路径。新入口只做了离线测试；原生数据集转换、各模型真实调用及完整 Agent 闭环尚未验收。

当前[第二版选型](../docs/model-evaluation/2026-10-27-study-selection-v2.md)的 Mode A1/A2/B/C 语义未定。paired 入口仅接受显式历史 A/B/C/D 命名空间，不把新 B/C 视为旧 B/C；模板保留 null，待新定义确定后再适配。

2026-10-27：从已有 Jev 工作区导出三种 type 配对、故障补测与时间/费用统计代码；导出及 PR 审查后的验证是离线测试，**没有为发布再次调用模型**。审查后框架八项、既有报告层十项测试通过。真实观测见[500 条结果](../docs/model-evaluation/2026-10-27-agentdojo-type-comparison.md)。

## 职责与依赖

| 模块 | 职责 |
|---|---|
| `type_compare.py` | 套件 × 标签比例抽样、冻结 manifest、逐片单问题请求、原始响应、配对指标 |
| `type_compare_repair.py` | 只补测失败项，另写 append-only repairs，保存前一记录哈希 |
| `type_compare_resources.py` | 离线统计全部首轮/补测、尝试、usage、延迟分布与公开单价估算 |
| `run.py` | 校验外部依赖版本，加载原工作区，接入原 monitor，处理 UTF-8 控制台 |
| `tests/` | 概率/方向/choice 平局、抽样、分片用量/重试计数和费用计算的离线测试 |
| `source-manifest.json` | 原文件与导出文件哈希、改动说明、外部依赖精确哈希 |

这不是独立 wheel，也不是完整 AgentDojo 环境。需要另行准备 `jev-skill-security` 工作区及其 `jev_skill`、`bench`、S4 profile；调用端复用该工作区的 `client.post_json` 和 `monitor`。本仓库不复制 monitor 实现；使用装饰器一次计账，不对同一请求重复 `record`。

**只克隆本仓库不能复现付费观测。** 来源包含当时未提交的实现，仅 source HEAD 不足以恢复环境。`check` 会逐项比对依赖哈希；缺失或版本不同将拒绝 live 运行。原始数据、付费响应、权重和凭证也不随仓库提供。要在另一台机器运行，应先恢复匹配的授权数据和源工作区，或独立验证新版本后创建新的 source manifest 与 run；不要为通过检查直接删除断言。

## 本地验证（无 API）

在本仓库根目录执行，`<jev-workspace>` 是已有源工作区的路径：

```powershell
python -m framework.run --workspace <jev-workspace> check
python -m framework.run --workspace <jev-workspace> test
python -m unittest discover -s scripts -p 'test_*.py' -v
```

前三种 type 的真实先导与全部 500 条由来源工作区执行；本导出只验证了适配层、解析、抽样和资源分析，尚未额外做 live 重测。不要把离线测试标为新模型结果。

## 新实验示例（实际收费，发布验证未执行）

新实验默认 `--limit 100`，模型默认 `jev-1.14.0`，必须指定新的输出目录。`--limit 500` 仅在明确扩大样本时使用。默认固定 seed=20261027，三臂匹配描述、相同 state，score 为两级 0..1；不是任意多级 score 实验器。

```powershell
# 密钥放源工作区 .env 或当前进程环境，参数只传变量名。
# 7890 是本次成功路径的示例；按自己的网络配置显式指定。
$env:JEV_MONITOR_DIR = '<jev-workspace>/reports/new-type-run/telemetry'
$env:JEV_MONITOR_PRICING = '<this-repo>/framework/pricing/jev-1.14-2026-10-27.json'

python -m framework.run --workspace <jev-workspace> compare --model jev-1.14.0 --key-name TYPESAFE_API_KEY2 --proxy http://localhost:7890 --limit 100 --out reports/new-type-run
```

数据固定读取源工作区 `bench/data/ts_bench.jsonl`，仅使用 `meta.tsbench_group=AgentDojo`。输出目录位于源工作区；原始逐条记录在 `bench/data/scans/<out-name>/`，因此 **out 的末级名称必须唯一**。不要对不同父目录复用同一末级名称。运行前检查数据许可与获取来源，不上传原始样本。

先导会对第一条样本分别调用三种 type，失败就不启动批量请求。完整运行最多四并发。模型输入不包含标签；标签只用于离线统计。长输入沿用 48,000 字符 / 2,000 重叠的分片，风险取 max。这会影响任务与动作的完整性，不等于语义无损处理。

没有将 Jev 的 temperature/seed 等未发送参数伪装成固定参数。seed 只控制本地抽样与调度。服务端默认值未知；请求只含 model、state、questions。默认超时 30 秒，每个分片临时失败最多重试两次；401/402/403/451 触发停止。已在途的调用可能先完成，故停止不等于零额外成本。

## 故障恢复和分析

权限/余额/地区错误停止批量任务时，取消尚未开始的任务，并继续收集所有已在途调用的结果；不能在首次错误后退出结果循环而丢失已完成响应。PR 审查增加了这一修复及离线回归；已有历史观测不重算、不改写，新代码必须使用新输出目录。

```powershell
python -m framework.run --workspace <jev-workspace> repair --out reports/new-type-run
python -m framework.run --workspace <jev-workspace> resources --out reports/new-type-run
```

`repair` 使用被冻结的模型、问句、state 和代理，先验证一条失败项，再以两并发补齐。原 predictions 不改写；重试记录另存 repairs，最终指标使用该 cell 的最新记录，失败不能当作安全。完整保留费用和失败次数。

`compare --report-only` 的历史实现只读首轮 predictions；存在 repairs 时不要用它替代最终合并分析，应使用 `repair` 的合并报告和 `resources`。无剩余错误时再次执行 repair 不请求模型，但会重算报告。更改代码/问题/数据后新开输出，旧 manifest 禁止混用。

原 monitor 覆盖新的 compare/repair invocation；`post_json` 已经有调用装饰器。监控是遥测，不是预算硬停止器，也没有强杀前的请求开始日志。将本轮 telemetry 的 run ID 与价格快照一并保留。`resources` 是对既有响应的离线核算，不把它与 monitor 小计再相加。

## 历史运行的记录缺口

2026-10-27 来源 type 比较入口没有激活 `@monitored_run`，因此没有该轮 monitor run ID。历史时间来自每条 `started_at` / `latency_ms`，费用来自实际返回 usage；不能事后编造 monitor 文件或失败请求用量。导出入口为未来运行增加了原 monitor 包装，并未追改历史数据。

请求阶段墙钟时间是第一条开始到最后补测完成的历时，包含中间间隔；并发累计耗时不是墙钟。逐条耗时含全部分片、代理、解析和重试，不是服务端纯推理时间。失败没有 usage 时费用未知；公开单价估算不等于实际账单。

当前代码仍是研究脚本：固定数据路径、固定 seed、固定两端描述，未封装通用数据注册器；不提供预算强制器、进程强杀恢复或完整 agent 环境。相关经验和后续边界见[实践总结](../docs/infrastructure/jev-benchmark-lessons.md)。
