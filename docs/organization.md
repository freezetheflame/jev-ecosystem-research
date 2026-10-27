# 材料组织约定

按研究问题确定主归属：模型评测与结果在 `model-evaluation/`，工程经验与接入在 `infrastructure/`，可复用代码在 `framework/`，受控的首方汇总与来源哈希在 `data/workspace-evidence/`。一份报告只有一个主位置，其他材料通过链接引用。

本次增量不移动已有根目录生态报告。新增文件不使用跨全仓库流水号；多轮实验可用 `YYYY-MM-DD-<description>`。类型/状态至少区分文献、计划、离线测试、静态探索、真实闭环与确认性结果。历史已暴露样本不因迁移而成为盲测。

每轮关联精确样本、请求/模型版本、完整参数、统计口径、费用时间、失败与限制。缺失记录标 unknown。原始请求/响应、权限受限数据和凭证保持在授权位置，不能为让GitHub链接完整而复制原文。

完整研究协议见[Agent安全执行规范](model-evaluation/agent-security-experiment-protocol.md)。
