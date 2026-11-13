# 本地模型 benchmark 首轮（2026-10-09）

已在 Jev 工作空间接入 Plumb-4B、decider-4B v2.1 和 H2O-Lightning-4B v1.1，三款各完成 100 条静态评测，零运行错误。全程复用本地权重离线运行。

[完整配对报告](../../../jev/reports/2026-10-09/local-models-paired/README.md) · [机器可读指标](../../../jev/reports/2026-10-09/local-models-paired/summary.json) · [运行环境和显存](../../../jev/reports/2026-10-09/local-models-paired/runtime.json)

评测实现位于 Jev 仓库的 `bench/local_models.py`、`bench/local_compare.py`，通过 `bench/engines.py` 复用现有问句、包装、分块和风险分方向。MSB 30 条、MCPTox 30 条、AgentDojo 40 条；按 UID 固定抽样，正负平衡，原文不超过 12,000 字符且完整保留。与同 UID 已保存的 Jev 预测对照，不调用 Jev API。

默认 0.5 阈值下，Plumb 误报较多、decider 漏检较多。H2O 在 AgentDojo 原始概率的 AUROC 为 1.000，但只识别 13/20 个危险动作；该观察应通过独立校准集与盲测集验证，不能在当前测试样本上选阈值后视为部署效果。H2O 官方 floor 会损失排序信息，因此逐条保留 raw_score 和处理后的 score。本轮 H2O 使用 Transformers 与官方 shim，尚未验证 stock vLLM 的结果一致性。

GPU 分配峰值：Plumb 8.35 GiB、decider 8.61 GiB、H2O 8.33 GiB；这是 PyTorch 分配量，不含桌面等其他显存占用。跑完已退出模型进程。

这是长度受限的小样本静态评测，不能替代全量结果或 Agent 闭环攻击成功率评测。接入代码 94 项本地 unittest 通过，三款 300 条实际 CUDA 推理全部成功，模型间对应请求哈希一致。
