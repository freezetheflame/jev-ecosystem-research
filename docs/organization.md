# 仓库组织约定

整理日期：2026-10-13。主题总览见 [调研索引](README.md)。

## 归属与命名

1. 以研究问题决定主主题。模型名、数据集名和文件日期是次级信息，不单独成为同级研究主题。
2. 一份报告只有一个主位置，跨主题通过链接引用。`ecosystem` 等稳定主题名不使用全仓库流水号，解决两份 `15-*` 并存的问题。
3. 在主题 README 记录材料类型（文献、设计、协议、实验记录、结果分析、工程）和状态（待做、已试跑、探索性结果、已独立验证）。执行完一次实验不自动等于独立验证。
4. 新报告用描述问题的英文文件名；多轮实验可使用 `YYYY-MM-DD-<description>.md`。日期代表该轮记录，不覆盖旧结果。
5. 结果说明至少关联固定样本、请求/模型版本、协议与预算、原始结果、指标口径和限制；缺少材料时显式注明。
6. 厂商自报、公开研究作者报告、本仓库实测分别标注，不混为同一证据来源。全文未读与摘要级筛选也应区分。

## 数据与代码

此次按主题迁移第一方报告，数据、脚本、第三方源码、配置与本地运行环境保持原路径。现有脚本有固定输出目录，manifest 与历史日志也记录了路径、版本和哈希；主题 README 将报告与这些材料关联。

后续新实验使用明确且独立的 `data/<study>/<run-id>/` 目录；一轮研究可在主题下维护协议、结果分析和运行索引。不要为统一外观重写历史轨迹或来源快照。

`data/mu/`、`local-apps/mu/` 和 `local-models/` 当前在本机 `.git/info/exclude` 中排除；它们是本地可选依赖。安全配对完整报告位于相邻 `../jev/`。这些材料的链接在本机可读，但干净克隆未必具备，应按主题索引中的环境说明准备。

## 旧路径对照

旧路径仅用于定位迁移前材料；新链接均指向当前报告。

| 原 `docs/` 文件名 | 当前报告 |
|---|---|
| `01-jev-open-ecosystem.md` | [ecosystem/open-ecosystem.md](ecosystem/open-ecosystem.md) |
| `01-jev-open-ecosystem.html` | [ecosystem/open-ecosystem.html](ecosystem/open-ecosystem.html) |
| `02-rag-security-and-jev.md` | [applications/rag-security-and-jev.md](applications/rag-security-and-jev.md) |
| `03-obtainability-and-licensing.md` | [ecosystem/obtainability-and-licensing.md](ecosystem/obtainability-and-licensing.md) |
| `04-hosted-api-survey.md` | [ecosystem/hosted-api-survey.md](ecosystem/hosted-api-survey.md) |
| `05-jev-router-ecosystem.md` | [routing-security/router-ecosystem.md](routing-security/router-ecosystem.md) |
| `06-security-research-agenda.md` | [routing-security/research-agenda.md](routing-security/research-agenda.md) |
| `07-local-model-smoke-test.md` | [model-evaluation/local-model-smoke-test.md](model-evaluation/local-model-smoke-test.md) |
| `08-h2o-lightning-local-test.md` | [model-evaluation/h2o-lightning-local-test.md](model-evaluation/h2o-lightning-local-test.md) |
| `09-local-benchmark-pilot.md` | [model-evaluation/local-benchmark-pilot.md](model-evaluation/local-benchmark-pilot.md) |
| `10-benchmark-comparison.md` | [model-evaluation/benchmark-comparison.md](model-evaluation/benchmark-comparison.md) |
| `11-jev-products-and-request-design.md` | [applications/products-and-request-design.md](applications/products-and-request-design.md) |
| `12-opencode-zen-jev-testing.md` | [infrastructure/opencode-zen-jev-testing.md](infrastructure/opencode-zen-jev-testing.md) |
| `13-jevout-subset-pilot.md` | [adversarial-robustness/jevout-subset-pilot.md](adversarial-robustness/jevout-subset-pilot.md) |
| `14-microsoft-decision-1.md` | [ecosystem/microsoft-decision-1.md](ecosystem/microsoft-decision-1.md) |
| `15-jevout-40-results.md` | [adversarial-robustness/jevout-40-results.md](adversarial-robustness/jevout-40-results.md) |
| `15-jev-semantic-robustness.md` | [semantic-robustness/semantic-robustness.md](semantic-robustness/semantic-robustness.md) |


## 2026-10-27 PR #1 导入增量约定

按研究问题确定主归属：模型评测与结果在 `model-evaluation/`，工程经验与接入在 `infrastructure/`，可复用代码在 `framework/`，受控的首方汇总与来源哈希在 `data/workspace-evidence/`。一份报告只有一个主位置，其他材料通过链接引用。

本次增量不移动已有根目录生态报告。新增文件不使用跨全仓库流水号；多轮实验可用 `YYYY-MM-DD-<description>`。类型/状态至少区分文献、计划、离线测试、静态探索、真实闭环与确认性结果。历史已暴露样本不因迁移而成为盲测。

每轮关联精确样本、请求/模型版本、完整参数、统计口径、费用时间、失败与限制。缺失记录标 unknown。原始请求/响应、权限受限数据和凭证保持在授权位置，不能为让GitHub链接完整而复制原文。

完整研究协议见[Agent安全执行规范](model-evaluation/agent-security-experiment-protocol.md)。
