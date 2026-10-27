# Jev 工作区证据导出

2026-10-27 将用户已授权分享的跑测经验、首方汇总与代码整理到本仓库。没有新推理、重新标注、阈值选择或全链路实验。

| 目录 | 类型/状态 | 内容与限制 |
|---|---|---|
| [2026-10-27-agentdojo-types](2026-10-27-agentdojo-types/) | 真实静态、探索性、complete | 500 条同 UID × 3 type；144正356负；包含30失败项补测、资源与样本/state哈希 |
| [2026-10-09-local-models](2026-10-09-local-models/summary.json) | 历史配对 pilot | 100条：MSB30/MCPTox30/AgentDojo40；本地3模型与历史Jev比较，非同时重复 |
| [2026-10-09-deepseek](2026-10-09-deepseek/summary.json) | 历史探索性对照 | 同100条；显式YES/NO版在看到首轮后修改，非预先单一冻结协议 |
| [2026-09-29-question-v2](2026-09-29-question-v2/summary.json) | 历史提示词试验 | wild100，20正80负；低误报伴随召回损失，不能当默认升级证据 |

来源均为 `jev-skill-security` 本地工作区，不是第三方榜单或厂商数字。主要来源路径：

- `reports/2026-10-27/agentdojo-type-500-jev114-key2-proxy7890/`
- `reports/2026-10-09/local-models-paired/`
- `reports/2026-10-09/deepseek-paired/`
- `reports/2026-09-29/maliciousness-v2/`

其余经验参考已存在的[历史方法比较](https://github.com/freezetheflame/jev-skill-security/blob/3cb9758de7e00aeb5c97c7f5b3a729efa0e33445/reports/2026-09-28/method-comparison/README.md)、[历史单问题全量](https://github.com/freezetheflame/jev-skill-security/blob/3cb9758de7e00aeb5c97c7f5b3a729efa0e33445/reports/2026-09-28/full-single-question/README.md)以及来源工作区的 `reports/2026-10-09/static-guard-summary/README.md`、`reports/2026-10-09/threshold-sensitivity/README.md`、`harness/README.md`。后一组有些仍属当时未提交材料，本次只导出必要汇总，不保证全部历史报告已可由远程 HEAD 恢复。

TS-Bench 原始文本无明确再分发许可，数据正文、完整 state/响应、凭证、私人日志、模型权重不发布。样本索引只保留 UID、上游标签与输入/state哈希；这不等同独立公开可复现数据集。完整重判需另行取得授权来源数据。

汇总 JSON 的测量值保持不变，代理 loopback 地址在公开版中写为 localhost 并显式记录清理过程；`sample-manifest.json` 是明确标记的清理版，去除了机器本地工作树状态。原文件哈希保存在 lineage。源 HEAD 不足以描述未提交实现，导出代码与外部依赖各有哈希。

历史先导的用量不纳入成功代理配置的费用小计；失败调用缺失 usage 的部分依旧 unknown。没有为了补模板而编造运行时间、价格、上游 commit、硬件版本或 monitor run ID。
