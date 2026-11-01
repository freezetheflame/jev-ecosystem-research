# A/A/B/D 选型、四数据集获取与 Jev 适配

日期：2026-10-30（Asia/Shanghai）。类型：用户选型变更、数据获取与离线适配记录。状态：**四个数据集均已落地并核对，均能生成 Jev 请求样例；已完成一次 8 条 Jev smoke（smoke-02），有逐条耗时与 API 估价，但不是 pilot、不是确认性成绩，运行配置未冻结**。

本记录把当前四基准定为：

| 数据集 | Mode | 判断对象 |
|---|---|---|
| AgentHarm | A1 | 用户请求是否属于 harmful 分区（输入检查，原生二分类） |
| InjecAgent | A2 | 工具返回中是否含第三方注入指令（输入检查，负类为派生的配对反事实） |
| TS-Bench | B | 尚未执行的候选工具调用是否应被拦截（执行前动作安全，原生三分类） |
| ATBench | D | 完整轨迹是否安全（原生轨迹级二分类，不再标 C） |

ATBench 的原生任务就是完整轨迹审计，数据卡写的是 "evaluate safety at the trajectory level"，没有前缀切点或逐步标签。此前把它列在 C 不成立；本版改回 D。C 暂时空缺，不能用 ATBench 冒充。

## 数据获取与核对

获取脚本：[`scripts/fetch_ab_datasets.py`](../../scripts/fetch_ab_datasets.py)（InjecAgent、TS-Bench）与 [`scripts/fetch_agentharm_atbench.py`](../../scripts/fetch_agentharm_atbench.py)（AgentHarm、ATBench）。数据落在 `data/agent-security-study/datasets/2026-10-30/`（被 .gitignore 排除），每个数据集带 `manifest.json`，记录来源 revision、URL、字节数和 SHA-256。

HuggingFace 直连在本机不可达（`huggingface.co` 连接失败），AgentHarm 与 ATBench 通过显式镜像 `hf-mirror.com` 按固定 revision 下载；镜像只改变传输路径，不改变文件内容，下载后仍按字节计算 SHA-256。

| 数据集 | 来源 revision | 文件 | 条目 |
|---|---|---|---:|
| AgentHarm | `e23b3fe60a0da9037314b88e5ee3a0c054970dad` | harmful/benign × validation/test_public，另含 chat 两文件 | 416（208 harmful / 208 benign） |
| InjecAgent | `f19c9f2c79a41046eb13c03c51a24c567a8ffa07` | `test_cases_dh_base.json` 510 + `test_cases_ds_base.json` 544 | 1,054 攻击用例 |
| TS-Bench | `46358fa424a927a895c6c8322f99032c4eb5155e` | AgentHarm-Traj 731、AgentDojo-Traj 1,220、ASB-Traj 5,231 | 7,182 步 |
| ATBench | `4476ef92ed8f85c8d58d8a5b9dfdf55aa7893138` | `ATBench/test.json` | 1,000 轨迹 |

标签分布（实测）：AgentHarm 208/208；TS-Bench safe 3,770、unsafe 1,631、controversial 1,781；ATBench 503 safe / 497 unsafe。InjecAgent 没有负类：1,054 条全部是攻击用例。

ATBench 文件 SHA-256 为 `80c534b5f3517c872b528a2e6b64e34495206968edd184f4aed563d39f0cca09`，与 2026-10-27 获取记录一致；字节数 18,335,079 也一致。

独立核对脚本 [`scripts/verify_aabd_datasets.py`](../../scripts/verify_aabd_datasets.py) 重新计算 16 个源文件的 SHA-256、逐个 manifest 比对，并通过四个 adapter 加载。结果在 [`data/workspace-evidence/2026-10-30-dataset-acquisition/verification.json`](../../data/workspace-evidence/2026-10-30-dataset-acquisition/verification.json)，标 `model_calls=0`。

## 代码与口径

- [`security_bench/datasets.py`](../../security_bench/datasets.py) 新增 `injecagent` 与 `tsbench` 加载分支；`item_ids` 过滤、hash 与 manifest 校验沿用原路径。
- [`security_bench/config.py`](../../security_bench/config.py) 注册两个数据集，新增 `input_inspection`、`pre_action_safety` 合同和 Mode D。
- [`security_bench/agentharm.py`](../../security_bench/agentharm.py) 的离线导出改为任意单数据集通用；`--dataset` 可从多数据集配置中选一个。
- [`security_bench/runner.py`](../../security_bench/runner.py) 把两个新数据集的源文件纳入 hash 校验。
- 配置模板：[`configs/security-bench-aabd.template.json`](../../configs/security-bench-aabd.template.json) 现覆盖四个数据集；AgentHarm 与 ATBench 沿用原适配器，ATBench 走整轨迹 D 路径。

InjecAgent 的 A2 视图是 `user_request` + `tool_response`。正类来自原生攻击用例；负类由同一响应里删除 `Attacker Instruction` 得到（`negative_policy=paired_neutralized`），是派生反事实，`gold_source=derived_paired_neutralization`，不冒称原生标签。也可以选 `positives_only`，此时没有负类、不能算二分类指标。

TS-Bench 的 B 视图是 `user_request` + `history` + `candidate_action` + `tools`，标签是该步的 `score`。`controversial_policy` 必须显式选择：`unknown` 把 0.5 记为不可判分（保留条目，不静默丢弃）；`unsafe`/ `safe` 分别并入正/负类。本模板用 `unknown`。

TS-Bench 的 `(id-interaction, id-segment)` 在同一文件内会重复（同一步的多个候选动作），因此 `item_id` 追加源行号；`family_id` 仍按 `文件:interaction` 聚类，避免把同一步的多个候选当成独立任务。

## 离线导出结果

命令（不读 key，不发网络请求）：

```powershell
python -m security_bench inspect-inputs --config configs/security-bench-aabd.template.json --dataset agentharm --split validation --split test_public --out-dir data/agent-security-study/preparations/2026-10-30-agentharm-a1
python -m security_bench inspect-inputs --config configs/security-bench-aabd.template.json --dataset injecagent --out-dir data/agent-security-study/preparations/2026-10-30-injecagent-a2
python -m security_bench inspect-inputs --config configs/security-bench-aabd.template.json --dataset tsbench --out-dir data/agent-security-study/preparations/2026-10-30-tsbench-b
python -m security_bench inspect-inputs --config configs/security-bench-aabd.template.json --dataset atbench --out-dir data/agent-security-study/preparations/2026-10-30-atbench-d
```

| 导出 | 条目 | 族 | 标签 |
|---|---:|---:|---|
| AgentHarm A1 | 416 | 52 | 208 harmful / 208 benign（validation 与 test_public 分开） |
| InjecAgent A2 | 2,108 | 1,054 | 1,054 正 / 1,054 派生负 |
| TS-Bench B | 7,182 | 3,376 | 3,770 safe / 1,631 unsafe / 1,781 unknown |
| ATBench D | 1,000 | 1,000 | 503 safe / 497 unsafe |

每个目录含 `inputs.jsonl`（只含模型可见视图）、`gold.jsonl`（gold 单独存放）、`jev-request-example.json`、`effective-input-config.json`、带文件 hash 的 `manifest.json`。`manifest.json` 明确标注 `model_calls=0` 和 `performance_results=not_run`。

## 8 条真实冒烟（smoke-02）

2026-10-30 在切换到允许地区的出口后，用同一份 8 条计划完成了一次真实调用。8/8 返回 HTTP 200 并解析成功；返回模型均为 `jev-1.14.0`。

| 数据集 | 条目 | TP | FP | TN | FN | 备注 |
|---|---:|---:|---:|---:|---:|---|
| AgentHarm A1 | 2 | 1 | 0 | 1 | 0 | harmful/benign 各一 |
| InjecAgent A2 | 2 | 1 | 0 | 1 | 0 | 正类 + 派生配对负类 |
| TS-Bench B | 2 | 0 | 0 | 1 | 1 | 漏 1 条 unsafe |
| ATBench D | 2 | 0 | 0 | 1 | 1 | 漏 1 条 unsafe |

- 时间：首条 06:03:04.346Z，末条 06:04:05.576Z，总墙钟约 61.23 秒；单条 p50 7.578 秒、p95 7.906 秒。
- 费用：4,499 输入 + 248 输出 token，按 0.042 USD/百万输入估价 **0.000188958 USD**；不是账单核验，本地计算未计价。
- 证据：`data/agent-security-study/runs/2026-10-30-smoke-02/`，含 `SMOKE-REPORT.md`、`raw/`、`events.jsonl`、`telemetry/` 与自动生成的 `analysis/`。
- 这不是 pilot 或确认性结果；n=2/数据集，只能证明链路可用，不能估计准确率。

## AgentHarm 50×3 pilot

2026-10-30 在 AgentHarm validation 上按 harmful/benign 各 25 条分层抽样（seed 20261030），跑 3 次，共 150 次调用，全部成功。

| 指标 | 每个 repeat |
|---|---:|
| TP / FP / TN / FN | 21 / 0 / 25 / 4 |
| accuracy（Wilson 95%） | 0.920 [0.812, 0.968] |
| precision / recall / F1 | 1.000 / 0.840 / 0.913 |
| FPR / FNR | 0.000 / 0.160 |

三次预测对 50/50 个 item 完全一致；4 条漏检均为 harmful→safe，集中在 3 个 family。总墙钟 998.85 秒（单次 p50 7.257 秒、p95 7.704 秒）；64,470 输入 + 4,650 输出 token，API 估价 0.00270774 USD。样本只有 8 个 base family，Wilson 区间未做聚类校正，不能当总体精度。

## 中转对照：GPT-6 Luna 与 Claude Haiku 5.5

2026-10-30 经 OpenLux 中转（`/v1/chat/completions`，严格 JSON）在同一 50 item 上各跑 3 次。

| 模型 | 可判 item | TP/FP/TN/FN | accuracy（共同 47） | FPR |
|---|---:|---|---:|---:|
| GPT-6 Luna | 47/50 | 21/1/24/1 | 0.957 | 0.040 |
| Claude Haiku 5.5 | 50/50 | 19/3/22/3（共同 47） | 0.872 | 0.120 |

GPT 有 3 个 harmful item（family 8）三次全被上游 `cyber_policy` 拦截，无法判分；全 50 的 accuracy 只能给 [0.900, 0.960] 边界。Claude 有 1 次散文拒答导致解析失败。McNemar exact p=0.125，不能声称优劣。总 API 估价 0.007445668 USD（356,393 输入 + 22,412 输出 token），11 次 provider refusal 无 usage、未计价。详见运行目录的 `RELAY-PILOT-REPORT.md`。

Jev 请求结构已按用户 2026-10-27 的选择生成：

```json
{"model": "jev-1.14.0", "state": "<序列化后的 view>",
 "questions": {"risk": {"type": "choice", "instructions": "...",
   "criteria": {"safe": "...", "unsafe": "..."}}}}
```

## 测试

`python -m unittest security_bench.tests.test_ab_datasets -v` 的 7 项全部通过（配对负类、三分类策略、非法策略/分数拒绝、Jev 请求形状、gold 不进请求、注册表）。

全量 `python -m unittest discover -s security_bench/tests`：47 项，1 failure + 1 error，均为本机环境问题，与本次改动无关：

- `test_msb` 需要 `pyarrow`，本机 Python 3.11 未安装；
- MaliciousSkillBench 数据不在本机。

另有 4 项因 AgentDojo 依赖缺失而跳过。

## 未做与限制

- **已完成 8 条 smoke 与 AgentHarm 50×3 pilot**：smoke-01 因地区封锁（HTTP 451）失败，切到新加坡节点后 smoke-02 的 8 条全部返回 200；pilot 的 150 次调用全部成功，但仍是小样本开发性结果，不是确认性成绩。
- smoke-02 的 API 估价为 0.000188958 USD（4,499 输入 + 248 输出 token，按 0.042 USD/百万输入、输出 0 的列表价），不是账单核验；本地计算未计价。
- 四个数据集都已落地，但这只是原始输入准备，不是模型成绩；AgentHarm 的 416 条是输入分类样本，不等于官方 Agent harm score。
- ATBench 轨迹较长：视图字符数中位数约 7.5k、p95 约 26k、最大约 365k（约 90k tokens）。全量 1,000 条直接送 Jev 可能触发上下文限制，正式运行前必须明确长上下文配置或预先定义截断/排除规则，不能静默截断。
- 没有冻结 prompt、样本量、预算、阈值和停止规则；模板会被 `doctor` 拒绝。
- TS-Bench 的 B 语义已按 2026-10-30 的决定改为“执行前动作安全”，授权合规语义已去掉；论文另有接入 Agent 的闭环实验（TS-Flow），本轮不做，因此不能从本数据推出端到端攻击阻断率或任务效用。
- TS-Bench 的 eval 轨迹来自 AgentHarm/ASB/AgentDojo，和 AgentHarm A1 臂共享底层任务族；分析时必须按 task family 聚类，不能当独立样本。
- InjecAgent 的派生负类是对同一响应的反事实修改，存在合成痕迹；结论只能针对“是否检测到第三方指令”，不能外推到真实工具返回分布。