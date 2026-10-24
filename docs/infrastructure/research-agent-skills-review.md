# 实验代理 skill 候选核查

日期：2026-10-25。范围：公开一手仓库、skill 入口与相关规范核查；不是所有脚本的安全/功能审计，也不是 skill 效果评测。

| 候选 | 核查内容 | 判断与当前操作 |
|---|---|---|
| [research-rigor](https://github.com/bsq415/research-rigor-skill/tree/4c28423a14f5cc53c6e5e80571ba5452ccf3bafa/skills/research-rigor) | README、SKILL.md、experiment-and-evidence、integrity-and-privacy；固定 commit 4c28423a14f5cc53c6e5e80571ba5452ccf3bafa | 最贴近研究全流程；已固定版本安装并采用实验规范，不代表功能/科研效果已独立验证 |
| [experimental-design](https://github.com/K-Dense-AI/scientific-agent-skills/blob/a92663a0214b3b9fa1ba6b958284ffd919c00a0c/skills/experimental-design/SKILL.md) | 在线入口，随机化、分块、重复和伪重复相关内容；API 确认该文件最近提交 a92663a0214b3b9fa1ba6b958284ffd919c00a0c | 可作设计补充；未安装、未运行脚本，未完整审核附带参考文件 |
| [experiment-tracking](https://github.com/selvarajmurugesan90/ops-engineering-skills/blob/110eb8804ca274d5d5ce677e990c287691686a20/plugins/mlops/skills/experiment-tracking/SKILL.md) | 在线入口中的参数、指标和代码/数据版本记录流程；API 确认该文件最近提交 110eb8804ca274d5d5ce677e990c287691686a20 | 偏 ML 训练追踪，可补记录；未安装，不取代科学设计和判分审计 |
| scientific-critical-thinking（已在本机） | 本地 SKILL.md：独立单元、偏差、统计和证据范围审核 | 本轮用于检查设计；不负责实际执行与不可篡改留存 |

官方 openai/skills curated 列表已通过 skill-installer 的 list-skills.py 成功读取，本次未见覆盖这套科研执行要求的专用条目。该判断只适用于本次列表，不声称不存在其他 skill。

安装命令（已成功执行）：

```powershell
python C:/Users/14399/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo bsq415/research-rigor-skill --path skills/research-rigor --ref 4c28423a14f5cc53c6e5e80571ba5452ccf3bafa
```

安装位置：`C:/Users/14399/.codex/skills/research-rigor`。从下一轮起进入可用 skill 列表。本轮直接读取安装内容后应用。没有执行第三方初始化器、控制器或实验脚本。

选择理由：该 skill 提出证据先于结论，保留不利结果和失败，冻结后不静默修改比较，区分工程通过与科学支持。其 README 自述的评测未显示相对无辅助模型的收益，不能把文档要求当成已验证的能力增益。

skill 是工作指令，不能保证真实数据或正确结论。应结合实际运行器、原始请求/响应、轨迹、判分与用量核对。先使用本地 JSONL/JSON 与版本化分析满足审计，再按规模考虑 [MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/)；本轮未安装 MLflow 或开通外部追踪账户。

用户选定的方向与操作约定见[全链路实验规范](../model-evaluation/agent-security-experiment-protocol.md)。
