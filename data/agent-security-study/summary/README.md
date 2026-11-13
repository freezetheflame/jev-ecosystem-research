# 实验结果汇总

这里集中保存各基准的当前汇总结果。版本化分析和原始实验仍保留原目录；本文件夹用于日常查阅。

## AgentHarm（当前已完成12模型）

- [汇总文档](agentharm/README.md)
- [主比较 CSV](agentharm/comparison.csv)：包括 Kev-4B，参数量、全50项正确完成率、条件准确率、token、耗时和费用。
- [Token 使用量](agentharm/tokens.csv)
- [模型参数量及来源](agentharm/model-sizes.csv)
- [每次重复与共同子集指标](agentharm/metrics.csv)
- [全50项计算明细](agentharm/full-sample.csv)
- [逐输入投票](agentharm/item-predictions.csv)
- [逐次实验记录](agentharm/episodes-all-runs.csv)
- [逐调用用量与费用](agentharm/calls-all-runs.csv)
- [模型完整参数](agentharm/model-parameters.csv)
- [运行索引](agentharm/run-inventory.csv)
- [来源与版本](agentharm/source.json)

当前来源为2026-11-04的12模型版本。主比较统一采用50条 validation 输入，每条3次；公开已暴露样本属于开发pilot。Jev使用OpenLux重测；GPT的未决项保留，token缺失不填零，本地计算未计价。

后续新基准可在本目录下新增对应文件夹。更新当前汇总时从版本化分析产物同步，不手工修改分数或原始记录。
