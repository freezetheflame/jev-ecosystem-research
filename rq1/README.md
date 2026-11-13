# rq1 — 已收集实验数据汇总

整理时间：2026-11-08 (Asia/Shanghai)。时间与 token 汇总补于 2026-11-11。服务器本地 StepShield 结果同步于 2026-11-11。统一汇总表重写于 2026-11-12 02:31 Asia/Shanghai，并于 2026-11-12 02:38 Asia/Shanghai 从正式汇总中删除 WildGuard prompt（Mode A1）。Packy Jev 的 StepShield 官方 analysis 于 2026-11-12 20:24 Asia/Shanghai 写入汇总来源说明。服务器本地 Mode E（`full-local-wildguard-response-v1`）于 2026-11-12 02:44:52 Asia/Shanghai 同步到 `wildguard/server-local/`（压缩包 `_ingest/rq1-wildguard-response-local-download.tar.gz`，29.7 MB，sha256 `a382288e5fccfb69a199a59a46ef794f0adf85f7e791a8d67fb3cca15fd835ca`，打包时排除 raw/），并写入正式汇总。MCC 主表重建于 2026-11-13 13:27:07 Asia/Shanghai：`summary/metrics.md` 现以 MCC 与 TPR/TNR 为跨位置主比较，准确率不再作为排名指标；指标含义见 `summary/README.md`。本目录存放数据副本/快照；原始 runs 仍在 `data/agent-security-study/runs`（未删除、未改动生成结果）。

## 目录结构

- `tsbench/server-local/` — 服务器本地模型 TS-Bench（已跑完，从 172.17.210.135 下载）
  - `full-local-tsbench-server-v1/` 9 个模型 × 7182
  - `full-local-tsbench-repair-v1/` 失败项重测（laya / kev / gliguard / jevguard / qwen3guard；secjev 124 条按决定保留失败）
- `tsbench/api/` — API TS-Bench
  - `full-api-tsbench-v1/`（claudehaiku, gpt6luna）
- `stepshield/api/` — 本机 API StepShield 快照目录（战役 `full-api-stepshield-v1`）。汇总表中 gpt6luna StepShield 来自服务器战役 `full-api-stepshield-server-v1`；claudehaiku StepShield 来自正式合并战役 `full-api-stepshield-claude-merged-v1`，都不是此目录。
  - `full-api-stepshield-v1/`（claudehaiku 部分完成，gpt6luna 当时未开始）
- `stepshield/server-local/` — 服务器本地模型 StepShield（已跑完，从 172.17.210.135 下载）
  - `full-local-stepshield-server-v1/` 9 个模型 × 8151，全部成功
  - 完整含 raw 的压缩包：`_ingest/rq1-stepshield-local-download.tar.gz`（解压时未展开 raw/，避免约 135 万个小文件）
- `agentharm/` — AgentHarm（api: claude / gpt / jev 系列；local: full-local-agentharm-v1）
- `injecagent/` — InjecAgent（local: full-local-injecagent-v1）
- `wildguard/` — 既有战役副本仍在（含旧的 prompt-harm / Mode A1 数据，正式汇总不纳入）。服务器本地 Mode E 在 `wildguard/server-local/`。
- 另外，Jev (Packy 1.14.0) 的正式战役 `full-api-jev-packy-v1` 目前只保留在 `data/agent-security-study/runs/full-api-jev-packy-v1/`（TS-Bench、AgentHarm、InjecAgent、StepShield、WildGuard response / Mode E）。汇总表已纳入这些官方结果。

## 汇总表

位于 `summary/`，现在是一套统一文件，不再按「非 StepShield / StepShield」分文件名：

- `summary/README.md` — 表目录、计分说明，以及各指标（MCC、TPR/TNR、准确率、F1、EIR@3、干预差、平凡基线等）的含义
- `summary/metrics.md` / `.csv` — 主表：模型 × 位置的 MCC 与 TPR/TNR（含 always-safe / always-unsafe 与正类比例）；InjecAgent 因全正类、MCC 无定义，作为补充 TPR 表
- `summary/metrics_full.md` / `.csv` — 全指标（准确率作为次要数字保留；含 FPR/FNR/TNR/MCC，以及 StepShield 的 EIR@3、干预差）。StepShield 可计算的 MCC 已补齐
- `summary/time_tokens.md` / `.csv` — 时间与 token（成功样本墙钟、调用延迟、已知输入/输出 token；本次补写了 gpt6luna 的 WildGuard Mode E，其余已填行未改）
- `summary/rebuild_mcc_summary.py` — 从已有混淆矩阵计数重建指标表，不读 `raw/`，不重跑

2026-11-10 / 2026-11-11 的旧分表已移到 `summary/_archive/20261110-split-by-stepshield/`。根目录的 `rq1_non_stepshield_bundle_20261110.zip` 仍保留，但是过期快照，请以 `summary/` 新表为准。

空单元格表示该结果还不在本机、尚未完成或尚未正式合并，不是估计值，也不写入进行中数字。现已写入 gpt6luna 的 StepShield、claudehaiku 的 WildGuard Mode E、claudehaiku 的 StepShield（正式合并战役 `full-api-stepshield-claude-merged-v1`），以及 gpt6luna 的 WildGuard Mode E（战役 `full-api-wildguard-response-v1`，官方 analysis `2026-11-13T061430.606753_0000-9d3a76`，2026-11-13 14:14:30 Asia/Shanghai 完成）。列入本套正式汇总的官方格子现已全部写入。

## 主指标（简要）

正类 = unsafe / 有害。跨位置主比较用 MCC，并同时看 TPR（=Recall）和 TNR（=Specificity）。准确率会被正类比例抬高（例如 StepShield test 正类 8.1% 时，永远判 safe 已有 91.9% 准确率），只留在全指标表里备查。MCC 在分母任一因子为 0 时无定义，记为 —，不能写成 0（InjecAgent 全正类、常数分类器、shieldstral 的 StepShield test 都属于这种情况）。完整定义、平凡基线、可判分母与干预差的含义见 `summary/README.md`。当前数字都是描述性的（1 次 repeat，阈值未经预注册）；MCC 很接近时不要写成确定名次。

## 主指标（简要）

正类 = unsafe / 有害。跨位置主比较用 MCC，并同时看 TPR（=Recall）和 TNR（=Specificity）。准确率会被正类比例抬高（例如 StepShield test 正类 8.1% 时，永远判 safe 已有 91.9% 准确率），只留在全指标表里备查。MCC 在分母任一因子为 0 时无定义，记为 —，不能写成 0（InjecAgent 全正类、常数分类器、shieldstral 的 StepShield test 都属于这种情况）。完整定义、平凡基线、可判分母与干预差的含义见 `summary/README.md`。当前数字都是描述性的（1 次 repeat，阈值未经预注册）；MCC 很接近时不要写成确定名次。

## 主指标（简要）

正类 = unsafe / 有害。跨位置主比较用 MCC，并同时看 TPR（=Recall）和 TNR（=Specificity）。准确率会被正类比例抬高（例如 StepShield test 正类 8.1% 时，永远判 safe 已有 91.9% 准确率），只留在全指标表里备查。MCC 在分母任一因子为 0 时无定义，记为 —，不能写成 0（InjecAgent 全正类、常数分类器、shieldstral 的 StepShield test 都属于这种情况）。完整定义、平凡基线、可判分母与干预差的含义见 `summary/README.md`。当前数字都是描述性的（1 次 repeat，阈值未经预注册）；MCC 很接近时不要写成确定名次。

## 关键说明

- 服务器 TS-Bench 由 `172.17.210.135` 打包下载（`rq1-tsbench-download.tar.gz`，333MB），解压到 `tsbench/server-local/`。
- secjev 的 TS-Bench 124 条超长输入因 fp32 CUDA OOM，按用户决定保留 `TransportError` 失败标记，未重测。
- 服务器本地 StepShield（`full-local-stepshield-server-v1`）已于 2026-11-11 07:56 Asia/Shanghai 全部完成，2026-11-11 同步到 `stepshield/server-local/`。完整压缩包 `_ingest/rq1-stepshield-local-download.tar.gz`（约 812 MB，sha256 `1271a0542c051782dd955cef0150dad614a646b8cc472034a1c99557f26250cd`）含 raw/；目录中展开了 analysis / episodes / events / telemetry 等，未展开 raw/。
- Jev (Packy 1.14.0) 的 StepShield episodes 已完整（8151，ok=8149，fail=2）。官方 analysis 已用修复后的 `report.py` 从既有文件生成（未重跑）：`data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`）。汇总表该行现引用该官方文件；准确率 / F1 与原先按同一口径手算的显示值一致。
- 服务器本地 WildGuard response（Mode E，full-local-wildguard-response-v1）已同步到 wildguard/server-local/，并写入 summary/。
- 汇总表中的 gpt6luna StepShield 来自服务器战役 `full-api-stepshield-server-v1` 的官方 analysis；claudehaiku 的 StepShield 来自正式合并战役 `full-api-stepshield-claude-merged-v1` 的官方 analysis（`2026-11-13T054230.236392_0000-9f5044`）。claudehaiku 与 gpt6luna 的 WildGuard Mode E 均已写入（gpt6luna 官方 analysis `2026-11-13T061430.606753_0000-9d3a76`，2026-11-13 14:14:30 Asia/Shanghai 完成）。
- 除 StepShield raw/ 按上条说明留在压缩包外，每个已同步 campaign 内的 `effective-config.json` / `manifest.json` / `plan.jsonl` / `cases.jsonl` / `episodes.jsonl` / `events.jsonl` / `telemetry/` / `raw/` 均按原结构原样保留。

## 未纳入（仍可在原 runs 目录找到）

各 50 条/2 条的 pilot、smoke、relay 等开发期小规模记录。
