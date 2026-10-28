# 当前四个 Agent 安全基准：本地获取记录

日期：2026-10-27（Asia/Shanghai）。材料类型：原始数据与源码获取记录，**不是模型实验或执行环境验收**。当前选型见[第二版清单](2026-10-27-study-selection-v2.md)。

只处理用户当前选定的四个基准；其他试跑语料保持原位。AgentDojo 按用户补充要求采用官方完整基准，不以历史 TS-Bench 静态派生数据作为入口。

| 基准 | 本地入口 | 来源和固定版本 |
|---|---|---|
| AgentDojo | `data/agent-security-study/datasets/2026-10-27/agentdojo/snapshot/` | [官方仓库](https://github.com/ethz-spylab/agentdojo)，`089ed468cf3ed0322acc66b0211f26d9d90dbf60` |
| AgentHarm | `data/agent-security-study/datasets/2026-10-27/agentharm/snapshot/` | [官方公开数据](https://huggingface.co/datasets/ai-safety-institute/AgentHarm)，`e23b3fe60a0da9037314b88e5ee3a0c054970dad` |
| MCPHunt | `data/agent-security-study/datasets/2026-10-27/mcphunt/snapshot/` | [官方轨迹](https://huggingface.co/datasets/lihaonan0716/mcphunt-agent-traces)，`8f05fed6face78aa48b10edcf3357c9aadfe71f5` |
| ATBench | `D:/projects/jev/data/atbench-test.json`；相同原始文件亦保存在 `D:/projects/jev/bench/raw/atbench/ATBench.json` | 复用已有原始文件，SHA-256 与历史 `agent-safety-full-manifest.json` 一致；历史记录的源 revision 为 `4476ef92ed8f85c8d58d8a5b9dfdf55aa7893138` |

MCPHunt 的配套[官方源码](https://github.com/lihaonan0716/MCPHunt)另存于 `mcphunt-source/snapshot/`，固定 commit `48e0f42f0820f15c9e88edb0ba461c615b908ecb`，便于定位任务定义、标签规则及数据说明；未执行其采集或判分程序。

## 获取与完整性

[下载脚本](../../scripts/download_selected_security_datasets.py)只下载固定 revision 的公开文件或源码 ZIP，并保存原件、源码展开目录、来源和逐文件 SHA-256。网络错误会记录并最多尝试三次。失败或未完成的获取明确保存 `failed_or_partial` 状态，不声称成功。

[核对脚本](../../scripts/inventory_selected_security_datasets.py)从原始文件及 manifest 生成[机器可读获取索引](../../data/agent-security-study/dataset-acquisition-2026-10-27.json)。该索引记录实际完成状态、逐文件校验、AgentHarm 各公开文件条目数、MCPHunt 各层轨迹数及发布者 Croissant 哈希核对。ATBench 与既有历史来源哈希核对。源文件没有被清洗或重标注。

```powershell
python scripts/download_selected_security_datasets.py
python scripts/inventory_selected_security_datasets.py
```

下载原件和展开目录属于本地依赖，已从 Git 排除；索引、获取代码和说明保留在仓库中。获取结果不通过编辑生成索引修正，应修改代码后重新派生。未下载的 AgentHarm 私有测试集不冒称可用；其公开 augmented、benign 和 chat 文件保留各自单位，不相加宣称独立基础任务数。

## AgentDojo 的完整性边界

AgentDojo 是动态基准：官方任务、初始环境、工具、攻击和判分源码共同构成可运行入口，而非一个固定的轨迹 CSV。此处下载完整官方仓库，包括 banking、slack、travel、workspace 四个 suite 的环境 YAML、各版本任务定义、攻击实现和判分代码，以及上游仓库随附的资料。

下载所有 suite 不等于必须运行所有版本的任务笛卡尔积；正式运行还要明确 benchmark 版本、可用任务/攻击配对、预算和 gold 契约。当前没有安装环境、启动 Agent、调用 API 或验收执行结果。旧静态片段只作历史开发证据保留。

## 尚未确定

本次固定的是**获取快照版本**，没有替用户冻结最终评测配置、Mode A1/A2/B/C 含义、样本数、ID、划分、前缀或动作标签。MCPHunt 主基准、mitigation 与 supplemental 轨迹必须分层，不能混作独立主测试样本。既有样本暴露和未来确认集独立性仍需审计。

本轮只有网络下载、文件校验和结构计数，无模型/API 实验，不产生 TP/FP/TN/FN 或 API 推理费用；本地计算未计价，未修改现有 monitor。
