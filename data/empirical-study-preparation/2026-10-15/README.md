# 本地实验资产快照与审计候选

这是 2026-10-15 的只读盘点输出，不是新实验结果或人工审核后的 gold 数据。

- `inventory.json`：读取相邻 `D:/projects/jev` 的静态数据、预测及模拟 harness，记录计数、字段、模型标识与 SHA-256。`rows_with_numeric_score` 仅表示 score 字段为数值，不保证输出语义或概率有效；JSONL 子目录还含 disagreements 等辅助文件，不能把所有行相加当预测总数。
- `review-candidates.json`：从本地已有 AgentDojo 用户任务中确定性选择 24 个待审核入口（每 suite 6 个）。没有复制攻击载荷、生成场景、构造动作标签或调用模型。
- `sources.json`：本轮核对的公开一手来源与访问范围。

报告：[已有资产与公开任务复用](../../../docs/model-evaluation/empirical-study-assets-and-benchmarks.md)。

从仓库根目录重跑（若需保留本次快照，请改用新的输出目录）：

```powershell
python -X utf8 scripts/inventory_empirical_assets.py --source D:/projects/jev --out data/empirical-study-preparation/2026-10-15
```

脚本不导入 benchmark 实现，不执行 raw Python 任务，不重建统一集，也不发出网络请求。文件完整性哈希用于识别本轮实际读取的本地版本，不代替上游 commit 或标签真实性审核。

审计候选中 `local_patch_version` 只表示该抽取条目的来源 patch；执行原环境时必须恢复整个固定版本，不能逐条混装这些 patch。正式测试集要与开发任务族隔离。
