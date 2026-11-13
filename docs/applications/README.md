# 产品应用与请求设计

研究问题：业务判断应保留哪些证据，怎样写 state、criteria、选项边界，并把概率接入操作流程？

| 文档 | 类型 | 证据与状态 |
|---|---|---|
| [RAG 安全与 Jev 节点](rag-security-and-jev.md) | 场景分析 | 文献与架构分析；不等于部署效果验证 |
| [实用产品与请求设计](products-and-request-design.md) | 产品源码调研 | 12 个项目的源码快照、请求组织与阈值分析 |

## 数据与示例

- [来源记录](../../data/jev-products-2026-10-11-sources.json)：精确 commit、审阅文件和链接。
- [调用记录](../../data/jev-products-2026-10-11-smoke.json)：匿名合成请求返回 403；没有分类结果。
- [四份请求示例](../../data/jev-request-examples-2026-10-11/README.md)：上下文筛选、文档边界、RAG 筛查、结构化分类；演示请求不等于效果实测。

## 关联与下一步

固定请求设计后，在 [模型评测](../model-evaluation/README.md) 比较结果；表达变化是否影响判断进入 [语义鲁棒性](../semantic-robustness/README.md)。实际 Agent 工具准入与上下文取舍进入 [Agent 接入](../agent-integration/README.md)。

[全部主题](../README.md)
