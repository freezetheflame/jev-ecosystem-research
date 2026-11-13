# 共享实验基础设施

这里放跨主题复用的端点、客户端与配置说明，研究主题索引直接引用这些工具。

| 材料 | 用途 | 状态 |
|---|---|---|
| [Jev 跑测实践](jev-benchmark-lessons.md) | 历史 prompt、标签与跑测经验 | 已有静态/探索性证据，非闭环结论 |
| [静态评测代码](../../framework/README.md) | 三种 type、补测、资源分析 | 复用原 monitor；框架八项离线测试通过 |
| [四基准统一入口](../../security_bench/README.md) | 配置预检、真实 AgentDojo 环境、三类原始数据判断、资源及报告 | 离线工程实现；未执行真实模型 pilot，Mode/精确模型与预算待明确 |
| [Jev 官方长上下文 smoke](jev-official-long-context-smoke.md) | 官方 1.14，默认/长 header 使用相同长请求 | 2026-10-27 实测：默认长度拒绝，长模式接受 224,375 个 provider 报告输入 token；单样本连通证据 |
| [实验代码职责与 monitor 接入](experiment-framework.md) | 保留既有资源监控，分离运行、判分和分析 | 原 monitor 三项及报告层十项离线测试通过；报告已分 Mode，新全链路运行器待接入 |
| [实验代理 skill 核查](research-agent-skills-review.md) | 候选、固定版本、安装与使用边界 | research-rigor 已安装；不是自动保证科学有效性或数据真实性 |
| [OpenCode Zen 测试入口](opencode-zen-jev-testing.md) | 测试配置、调用命令与实验边界 | 历史合成调用记录；不保证当前免费通道持续可用 |
| [jev_api.py](../../scripts/jev_api.py) | 类型化请求客户端 | 支持共享配置与有效请求哈希记录 |
| [test_jev_api.py](../../scripts/test_jev_api.py) | 离线客户端测试 | 不调用外部服务 |
| [项目配置](../../.pi/pi-jev.json) | 共享 endpoint / model / timeout | 运行配置保持原位置 |
| [smoke 结果](../../data/jev-zen-smoke.json) · [RAG 示例结果](../../data/jev-zen-rag-screen.json) | 端点验证记录 | 单次测试证据，不是安全能力 benchmark |

模型下载与本地推理入口关联 [模型评测](../model-evaluation/README.md)，榜单下载关联 [模型生态](../ecosystem/README.md)，JevOut 专用适配关联 [对抗复现](../adversarial-robustness/README.md)。

[全部主题](../README.md)

新实验继续遵循[Agent 安全执行规范](../model-evaluation/agent-security-experiment-protocol.md)。
# 模型接入补充

- [2026-10-28：11 模型推理接入、输出映射和部署契约](2026-10-28-model-inference-adapters.md)：工程适配；仅合成验收，尚未真实部署或跑分。


- [本机模型使用手册](local-model-operations.md)：当前机器9个本地服务与3个API模型；原缺失3模型已恢复并真实smoke，Jev默认OpenLux中转。
# 五数据集全集操作

- [全集实验操作手册](full-benchmark-operations.md)：12 模型、API 中转、单命令预检/运行/续跑、原始结果目录与报告边界。工程准备；WildGuard 原始数据待授权，尚未执行新全集。

