# Jev 请求设计示例

本次自行编写的演示请求，对应 [调研报告](../../docs/applications/products-and-request-design.md)。它们借鉴产品的组织方式，未复制作者完整请求，也没有提交到 Jev API。文件中不含预测结果、真实用户数据或 API key。

| 文件 | 演示的设计 |
|---|---|
| `01-context-filter.json` | task / tool / blocks，逐块 Noul，独立工具错误门限 |
| `02-document-boundary.json` | 页类别 Choice 与文档边界 Noul 分开；同类别仍可切分 |
| `03-rag-screen.json` | 相关性、答案证据、嵌入指令分别判断 |
| `04-structured-choice.json` | 类别的覆盖范围、排除边界、案例、other 与证据不足 |

请求入口为 `POST https://api.typesafe.ai/v1/systemone`，鉴权使用调用者自己的 Bearer key。这里仅做离线 JSON、类型、criteria 数量和显式 state 引用检查，不代表已验证模型能力或服务端接受结果。阈值、重试和缓存策略见报告，未放入 wire payload。
