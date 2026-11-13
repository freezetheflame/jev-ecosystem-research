# Jev 与 Agent Security：论文工作稿

创建日期：2026-10-15。状态：动机与 Introduction 初稿，尚未完成实验设计或正式实验。

## 文件

- `main.tex`：英文单栏、自包含 LaTeX 稿件，包含暂定标题、摘要、Introduction 和四条已核对来源。可在 Codex 内直接打开编辑及预览。
- 当前参考文献内置于 `thebibliography`，不依赖额外文件；确定投稿模板后再迁移至 BibTeX，并拆分章节。
- RQ 尚未写入论文正文，续写位置已用 LaTeX 注释标出。
- `build/main.pdf`：本机编译预览，构建目录不进入版本控制。已使用 MiKTeX / latexmk 编译；在本目录运行 `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex` 可重新生成。

## 本轮叙事

Agent 与不可信数据交互 → 快速决策组件的动机 → Jev 的接口与命名 → 动作门控和上下文筛选的直接/间接安全影响 → 现有研究与本研究定位 → 安全、效用约束下的总体成本与延迟。

上下文筛选的初始实验边界：可信用户指令、硬权限约束不可被筛选器删除；研究外部材料、证据及其来源信息的选择。两种接入角色仍是候选范围，并非已验证方案。

## 已讨论的 RQ 工作版本（尚未冻结）

1. 安全效果与适用角色。
2. 鲁棒性与失效机制。
3. 接入与组合策略。
4. 成本与效率：在满足预先指定的安全和任务效用要求时，能否降低整体费用与延迟？作为次要 RQ。

## 写作证据边界

- 摘要明确标为尚无结果的工作稿，实验完成后重写。
- 不把厂商关于性能或校准的主张写成独立实测结论。
- 不声称首次研究 Jev 安全、授权门控或闭环 Agent 防护。
- 不将相邻项目中的静态分类、脚本化模拟器结果写成真实 LLM Agent 的防护效果。
- 全面 related work 和正式新颖性核查尚待完成；当前四项引用用于支持本段动机。
- 本轮未调用模型 API 开展实验。

## 研究材料入口

- [实验资产盘点与公开任务复用](../docs/model-evaluation/empirical-study-assets-and-benchmarks.md)：2026-10-15 整理；主实验优先复用公开任务，新增变体只用于必要的机制对照。
- [研究主题索引](../docs/README.md)
- [安全与鲁棒性证据](../docs/semantic-robustness/2026-10-13-robustness-security-review.md)
- [现有 pilot 协议](../docs/semantic-robustness/robustness-security-pilot-protocol.md)
- [Agent 接入材料](../docs/agent-integration/README.md)

后续优先讨论：标题是否足够准确、两个接入角色是否都保留、Introduction 对近邻工作的定位，以及 RQ 的具体可检验表述。
