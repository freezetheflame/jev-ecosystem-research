# Jev 官方长上下文 smoke

状态：completed。合成数据 1 条，计划 2 次调用，实际 2 次。

模型：jev-1.14.0；官方端点：https://api.typesafe.ai/v1/systemone；timeout=120.0s，无重试，并发 1。
完整请求见 raw/request-body.json，参数见 effective-config.json，价格来源见 sources.json。

| 请求 | HTTP | 耗时 s | 实际返回模型 | 结果 | 输入 token |
|---|---:|---:|---|---|---:|
| default-control | 400 | 3.003 | None | None | None |
| long-enabled | 200 | 6.311 | jev-1.14.0 | deny | 224375 |

monitor 墙钟时间：9.478s。已知费用估算：$0.00942375；完整估价：None；未计价调用：1。
估算不等于账单；错误调用缺少 usage 时费用未知。本地计算未计价。

TP/FP/TN/FN：NA（仅 API/长度连通测试，无安全分类 gold）；合成记录读取结果另列，不作为安全能力结论。
复现命令见 reproduce.txt；源码、monitor 快照与环境已保存；服务端隐藏参数未知，模型随机性不可消除。
本测试只验证此请求是否被服务接受及返回，不证明长文本一般准确率或完整 262k 边界。
