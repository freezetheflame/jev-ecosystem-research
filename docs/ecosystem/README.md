# 模型生态与获取

研究问题：有哪些 Jev 类决策模型，它们采用什么技术路线，如何获取、调用及遵守许可？

| 文档 | 类型 | 证据与状态 |
|---|---|---|
| [开放模型生态主报告](open-ecosystem.md) · [历史 HTML](open-ecosystem.html) | 生态综述 | 项目资料与 JevBench v1.4.2.2 历史快照；HTML 未包含后续增量 |
| [可获取性与许可证](obtainability-and-licensing.md) | 获取核查 | 区分源码、权重、托管服务及许可条件 |
| [托管 API 调研](hosted-api-survey.md) | 服务调研 | 历史可达性记录；不保证当前服务可用 |
| [Microsoft-Decision-1](microsoft-decision-1.md) | 增量模型调研 | 官方文档与厂商比较；未做独立模型实测 |
| [vLLM-SR Decision 3.0 / d3](vllm-sr-decision-models.md) | 增量模型调研与待测安排 | 六款公开 checkpoint 已纳入比较；优先 d3-mini，尚未试跑 |

## 数据与工具

- [JevBench 原始 JSON](../../data/jevbench-v1.4.2.2-results.json) 与 [榜单](../../data/jevbench-v1.4.2.2-leaderboard.md)：冻结版本的通用评测资料。
- [微软来源快照](../../data/microsoft-decision-1-research/)：公告、部署说明、来源哈希与厂商比较。
- [vLLM-SR 来源与候选清单](../../data/vllm-sr-decision-research-2026-10-13/models.json)：六款模型 revision、许可和后续优先级。
- [榜单获取脚本](../../scripts/fetch_jevbench.py)：下载指定版本的上游榜单。

## 关联与下一步

模型进入比较前，先核对接口和版本，再进入 [模型评测](../model-evaluation/README.md)。微软的厂商数字保持独立，不追加到旧榜单；其实际契约与配对评测仍是待做事项。

[全部主题](../README.md)
