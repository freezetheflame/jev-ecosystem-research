# Jev 官方长上下文模式：连通与长度 smoke

日期：2026-10-27（Asia/Shanghai）。状态：**已真实调用；单个合成样本、两次请求的 smoke，不是正式安全评测或长上下文准确率研究**。

## 配置与依据

按[官方模型文档](https://docs.typesafe.ai/models#long-context)及 [System One API](https://docs.typesafe.ai/api/system-one)核对：向 `https://api.typesafe.ai/v1/systemone` 发送 `TypeSafe-Danger-Zone-Long-Context: true`，可启用 Jev 1.14 / 1.13 的长上下文，文档标称请求及单问题上限均为 262k tokens；默认分别为 64k / 32k。文档价格为每百万输入 token $0.042，输出免费，长模式单价不变。它并不保证长文本准确率。

本次固定 `model=jev-1.14.0`，直接调用官方端点，使用本地 `.env.local` 中 `TYPESAFE_API_KEY2`；不记录 key 内容，也未修改免费代理配置。最长两次请求、并发 1、超时每次 120 秒、无重试、无模型替换。原有 `jev_skill.monitor` 复用且源码未改，计价表作为本次独立快照传入。

## 数据与请求

一个确定性合成文本：8,000 行数字填充，在中间插入 `TARGET-582401 has decision DENY.`，以单个 Choice 问题读取该记录。三选项为 allow / deny / review。它不含真实隐私或正式测试集样本。

- state 长度：224,102 字符。
- 序列化请求：232,418 字节。
- 两次正文完全一致，先不带长模式 header，再添加 header。
- token 数以服务响应中的 billable `usage.input_tokens` 为准；没有假称使用官方本地 tokenizer 预先计数。
- 数据数量：1 个唯一合成条目，2 次计划请求，2 次实际请求；无重试、无排除。

## 实际结果

| 条件 | HTTP | 服务响应 | 网络调用耗时 | provider 报告输入/输出 token |
|---|---:|---|---:|---:|
| 默认模式，不带长 header | 400 | `max_tokens_exceeded` | 3.003 秒 | 未提供 |
| 长上下文 header=true | 200 | 返回模型 `jev-1.14.0`；选择 deny，与合成记录一致 | 6.311 秒 | 224,375 / 41 |

本地 key 在本次调用时可用于官方 Jev 1.14 长模式。观察到该请求跨过默认长度限制且成功返回；未测满 262k 边界、不同内容/位置、重复波动或一般长文本性能，也未比较两模式的准确率或推理速度（默认组没有完成推理）。

monitor 墙钟时间为 9.478 秒，不包含前期文档核对和编写/离线测试。成功调用的已知费用估算为 `224375 × 0.042 / 1,000,000 = $0.00942375`；这是价格估算，不是账单核验。默认模式拒绝请求未返回 usage，其计费未知，因此 monitor 完整总估价保持 null，未将拒绝调用计为零费用。本地计算未计价。

TP/FP/TN/FN：NA，原因是 API/长度连通 smoke 无安全二分类 gold。单个合成记录的正确读取不能支持安全能力、校准或可替代性结论。

## 原始证据与复现

- [运行报告](../../data/jev-official-long-context/2026-10-27-smoke-01/report.md)
- [结构化结果](../../data/jev-official-long-context/2026-10-27-smoke-01/summary.json)
- [有效配置](../../data/jev-official-long-context/2026-10-27-smoke-01/effective-config.json)
- [完整实际请求](../../data/jev-official-long-context/2026-10-27-smoke-01/raw/request-body.json)
- [默认模式原始响应](../../data/jev-official-long-context/2026-10-27-smoke-01/raw/default-control.response.txt)
- [长模式原始响应](../../data/jev-official-long-context/2026-10-27-smoke-01/raw/long-enabled.response.txt)
- [文件哈希清单](../../data/jev-official-long-context/2026-10-27-smoke-01/manifest.json)
- [复现命令](../../data/jev-official-long-context/2026-10-27-smoke-01/reproduce.txt)
- [脚本](../../scripts/jev_long_context_smoke.py)与[离线测试](../../scripts/test_jev_long_context_smoke.py)；三项离线测试通过。

源码、monitor 快照、环境、完整请求/原始响应、调用开始/结束事件、monitor 分段与价格快照都位于独立运行目录。复现使用新目录、单独提供本地 key；不要覆盖本轮产物。服务端隐藏参数未知，API 服务行为及随机性可能变化。本轮未改写既有结果、未变更 monitor、未启动正式 Agent 安全对比。
