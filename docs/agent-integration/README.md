# Agent 决策接入与 Mu

研究问题：将小模型接入任务归类、技能披露、工具结果准入和上下文取舍后，是否实际提高任务成功率、关键约束保留与整体效率？

该主题目前主要材料在本机 Mu 源码和试用目录中。本页提供索引，未将上游文档或实现复制为本仓库自己的成果。

| 材料 | 类型 | 证据与状态 |
|---|---|---|
| [JevAgentHarness 精读](2026-10-19-jevagentharness-critical-reading.md) | 文献与方法评估 | 正文、相关附录与固定源码核查；逐任务汇总算术核对；未重跑模型与安全攻击 |
| [本地试用记录](../../local-apps/mu/README.md) | 安装与环境核查 | 桌面安装、哈希、doctor 与 help 检查；记录中尚未提交模型任务 |
| [现状与交接](../../data/mu/kyrn/docs/06-project-status-and-handoff.md) | 上游工程快照 | 2026-09-22 历史状态；其中其他机器路径不表示本机已具备相同环境 |
| [决策接入构想](../../data/mu/kyrn/docs/01-jev-integration-brainstorm.md) | 架构设计 | 决策点、主模型与判断模型分工 |
| [历史收益回测](../../data/mu/kyrn/docs/08-jev-retrospective.md) | 上游历史分析 | 2026-09-21 留存样本；局部作用不等于整体净收益已证明 |
| [工具输出准入](../../data/mu/kyrn/docs/09-test-log-admission.md) | 工程专题 | 工具结果如何进入上下文及测试日志处理 |

## 本地工程与关联

- `data/mu/` 是本地源码检出；`local-apps/mu/` 包含本地应用、启动器与试用工作区。两者目前由本机 Git exclude 排除，不随本仓库克隆分发。
- 通用请求结构归 [应用设计](../applications/README.md)，固定任务的模型质量归 [模型评测](../model-evaluation/README.md)，路由操纵归 [路由安全](../routing-security/README.md)。
- 下一步若继续此线，应记录具体决策点、实际采取的操作和端到端任务结果，并与关闭判断模块的基线配对；不能只以少 tokens 或判断调用次数宣称收益。

[全部主题](../README.md)
