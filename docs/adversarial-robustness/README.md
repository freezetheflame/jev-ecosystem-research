# 对抗上下文与 JevOut 复现

研究问题：在不改变 gold answer 的条件下，自适应加入自然背景是否能让最初正确的模型选择预先固定的错误选项？

| 文档 | 类型 | 证据与状态 |
|---|---|---|
| [小子集方法复现](jevout-subset-pilot.md) | 方法 pilot | 冻结 8 题、6 题 eligible；观察到可重复翻转，答案保持性未确认 |
| [40 题探索结果](jevout-40-results.md) | 扩展探索 | 冻结 40 题、32 题 eligible；迭代观察 2/32 翻转，存在语义风险与 provider 差异 |

## 数据与运行器

| 材料 | 位置 | 用途 |
|---|---|---|
| 上游源码与协议 | [JevOut](../../data/JevOut/) · `data/JevOut-main.zip` | 第三方发布包；不是论文原始攻击轨迹 |
| 8 题 pilot | [jevout-pilot](../../data/jevout-pilot/) | 冻结样本、基线、生成与检查、重复性、无效版本归档 |
| 40 题组 | [jevout-40](../../data/jevout-40/) | 冻结题目、两组单次生成、探索性合并摘要 |
| 官方端点组 | [jevout-typesafe](../../data/jevout-typesafe/) | 迭代轨迹与摘要；不默认为与免费端点严格配对 |
| 端点诊断 | [jevout-gateway](../../data/jevout-gateway/) | 连通性记录 |
| 本仓库运行器 | [jevout_pilot.py](../../scripts/jevout_pilot.py) · [prepare_jevout40.py](../../scripts/prepare_jevout40.py) | 适配、子集准备与恢复逻辑 |
| 离线适配测试 | [test_jevout_pilot.py](../../scripts/test_jevout_pilot.py) | 验证客户端行为，不证明攻击有效 |

## 关联与下一步

优先独立盲审答案保持性，再考虑预算匹配对照、更多类别和 seeds。观察翻转、检查器通过、重复翻转和有效攻击率是不同证据层次。

[语义鲁棒性](../semantic-robustness/README.md)引用本主题的方法与问题，但独立设计等价对、关键变化对和重复噪声基线。现有结果、日志、manifest、缓存路径及共享配置均按原位置使用。

[全部主题](../README.md)
