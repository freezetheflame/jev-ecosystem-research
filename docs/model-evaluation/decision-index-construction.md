# Jev Decision Index：开放范围与构建方法

核查日期：2026-10-13。材料类型：一手文档与源码调研；附公共指数聚合检查。未重建完整数据集、未调用模型、未独立验证私有测试。

## 结论与版本

**公共 benchmark 的构建器、运行器和评分器开源，完整榜单所用测试并不全部公开。** 项目由 Apolinário Passos / multimodalart 维护，声明与 TypeSafe AI 无关联。

- [复现仓库](https://github.com/apolinario/decision-index)，代码 [MIT License](https://github.com/apolinario/decision-index/blob/main/LICENSE)。
- [榜单](https://huggingface.co/spaces/multimodalart/jev-decision-index)、[方法页源码](https://huggingface.co/spaces/multimodalart/jev-decision-index/blob/main/methodology.html)。本轮在线快照标为 **0.3.2**；复现工具的公共文本套件版本为 **0.3**。
- 公共题目从各上游数据源本地重建，不提供统一可自由再分发的题库；上游许可证继续适用。
- Full score = 20% 公共指数 + 50% 私有同能力测试 + 30% 私有新领域任务。私有题目不发布，工具只计算公共指数。

私有部分按维护者运行的未微调 stock 模型的平均水平与分散程度映射到公共分数尺度，再加权。公开方法只足以解释设计意图，不能让第三方重跑私有题目、审计其标签或证明不存在污染。[榜单说明](https://huggingface.co/spaces/multimodalart/jev-decision-index/blob/main/README.md)

## 公共套件覆盖什么

公共总分纳入 37 个 benchmark；领域、基线和权重可直接读取 [index-0.3.json](https://github.com/apolinario/decision-index/blob/main/decision_index/data/index-0.3.json)。

| 领域 | 数量 | 权重（约） | 代表任务 |
|---|---:|---:|---|
| 知识与推理 | 11 | 25.85% | MMLU-Pro、BBH、GPQA Diamond、GSM8K、HLE、ChessBench |
| 语言理解 | 9 | 25.85% | ANLI、ContractNLI、HellaSwag、ACOS、RAGTruth |
| 检索与分类 | 6 | 20.02% | BANKING77、CLINC150、BRIGHT、ESCI、PhishNChips、HoVer |
| 工具与自动化 | 5 | 18.28% | BFCL、ToolRet、API-Bank、Home appliances、When2Call |
| 艺术与人类偏好 | 6 | 10.00% | 诗歌、幽默、和弦、配色、共识文本、New Yorker caption |

完整公共运行还包含一些仅展示分数、不进入总分的 benchmark。工具文档给出的有效请求数为 `109,759 + 30,419 = 140,178`；这是整个运行套件的请求数，不能直接叫作“37 个任务的独立题数”。一次请求可含多个决策，一个原始案例也可产生多次请求。网页基础套件计数 110,201 不包含额外七项的 30,419 请求。[套件文档](https://github.com/apolinario/decision-index/blob/main/docs/suite.md)

## 构建流程

### 1. 获取既有数据并记录版本

`suite/build/acquire.py` 与 `adapters_added.py` 定义 Git commit、HF revision、文件 URL 和校验值，下载到工作目录；不同来源使用不同固定方式。应同时保留最终 suite 哈希，不能仅依赖“下载了同名数据集”。

新增的七项是 MMLU-Pro、BBH、RAGTruth、HoVer、When2Call、New Yorker、PhishNChips。[新增任务源码](https://github.com/apolinario/decision-index/blob/main/decision_index/suite/build/adapters_added.py)

### 2. 转成统一的决策接口

模型收到 `state` 和 `questions`；每个问题有 `type`、`instructions`、`criteria`。`choice` 在给定选项中选择，并输出各选项概率；`noul` 输出 yes 概率。`expected`、来源元数据和评分信息不送给模型。[格式说明](https://github.com/apolinario/decision-index/blob/main/docs/format.md)

例如下面是接口示意，**不是原始测试题**：

```json
{
  "state": {"message": "I lost my debit card."},
  "questions": {
    "intent": {
      "type": "choice",
      "instructions": "Choose the intent of the message.",
      "criteria": {
        "lost_card": "The customer lost a card.",
        "transfer": "The customer asks about a transfer."
      }
    }
  }
}
```

各任务的转换深度不同：

| 任务 | 转换后的实际问题 | 解读边界 |
|---|---|---|
| MMLU-Pro / BBH | 原题与有限选项映射到 `criteria` | BBH 只保留可用固定选项表达的任务 |
| BFCL | 对每个候选函数回答是否调用 | 不测参数生成、调用顺序或执行 |
| ACOS | 对类别 × 情感组合分别判断是否出现 | 不测完整四元组抽取 |
| FinEntity | 判断已给出的实体跨度的情感 | 不测实体识别 |
| RAGTruth | 根据 prompt 与 response 判断是否存在无依据内容 | 响应级判断，不测幻觉跨度定位 |
| HoVer | 根据 claim 与提供的正确证据文档判断支持与否 | 证据按 supporting facts 给定，不测寻找证据 |
| When2Call | 在直接回答、调用工具、索取信息、无法回答中选择 | 固定选项决策 |

这些边界在 [mechanical adapters](https://github.com/apolinario/decision-index/blob/main/decision_index/suite/build/adapters_mechanical.py) 和 [added adapters](https://github.com/apolinario/decision-index/blob/main/decision_index/suite/build/adapters_added.py) 中明确。因此引用结果时应说明“Decision Index 改编版”，不能将它当作各原版 benchmark 的原生分数。

### 3. 检索任务先生成候选，再用概率重排

ToolRet / BRIGHT 用 SQLite FTS5 BM25，仅根据 query 从公开语料取 top-32，不插入 gold。模型对每个候选给出相关性 `P(yes)`，合并分块结果后计算 nDCG@10。

超长完整文档不截断而被省略；未标注候选不是经验证的分类负例，但计算排序指标时按未判相关处理。0.2.1 起只纳入候选中至少有一个相关项的查询：ToolRet 685 个、BRIGHT 220 个。因此成绩反映固定候选上的重排，不能推出完整语料检索质量。[检索源码](https://github.com/apolinario/decision-index/blob/main/decision_index/suite/build/adapters_retrieval.py)

### 4. 确定性抽样与冻结

初版使用 seed `20260919`，按 `sha256(seed:catalog_id:group_id)` 排序抽样；设案例上限或请求预算，按完整关联案例保留。ESCI 按 locale × relevance 分层；部分后续子集另用固定 seed 和公开名单。

冻结步骤写入 `run_id`、`group_id`、`payload_sha256` 与 manifest；全体模型使用相同排除名单。`suite import` 校验文件，gzip 头可不同，题目文件按解压后的哈希比较。[冻结源码](https://github.com/apolinario/decision-index/blob/main/decision_index/suite/build/freeze.py)

### 5. 构造并修正干扰选项

GSM8K 原本是数值答案题，被转成 4 选 1 和 10 选 1。旧版错误选项由正确答案加减或乘除生成，导致只看选项规律也能高于随机。

0.3 的 `answer-groups-v1` 将数值规模相近的不同题目编组，用其他题目的正确答案作为干扰项；每组共享十个不同答案，再确定性生成四选一子集并打乱顺序。1,319 道原题产生 2,638 请求。[GSM8K 修正源码](https://github.com/apolinario/decision-index/blob/main/decision_index/suite/build/gsm8k_v3.py)

## 怎么评分

先用任务自己的指标：accuracy、macro-F1、case-exact accuracy、nDCG@10 或 per-review F1。缺失、错误、unsupported、弃答计入覆盖惩罚；关联案例缺少必要请求时记零。

然后对有效原始得分做机会水平校正：

```text
skill_b = clip((raw_b - chance_b) / (1 - chance_b), 0, 1)
area_c  = Σ benchmark_weight_b × skill_b / Σ benchmark_weight_b
public  = 100 × Σ area_weight_c × area_c
```

普通任务通常用随机选项基线，但 F1、检索和整案例指标各有专门基线；例如 RAGTruth 用始终判有幻觉的 F1 0.5177。域内 gold ★ 任务权重为 1.2，其余为 1.0。[评分源码](https://github.com/apolinario/decision-index/blob/main/decision_index/scoring/index02.py)

主指数不能单独证明概率校准良好；榜单另外展示 calibration。也不能单独证明安全性、输入扰动鲁棒性或 Agent 完整工作流成功率。这是根据所测任务和评分公式得出的能力边界判断。

## 已披露的构建问题

- RouterBench：提示暴露 GPT-4 是最佳路由，退出指数。
- SGD：构建器曾给出完整对话，包括被分类时点之后的内容，退出指数等待重跑。
- Home appliances：删除测试内重复及与公开 dev 相同的 state，保留 88/160。
- ForecastBench：0.3 退休，不再运行或计入指数。

这些记录说明版本会实质改变评测定义；不同版本总分不能直接混用。[配置与退出理由](https://github.com/apolinario/decision-index/blob/main/decision_index/data/index-0.3.json)、[版本与子集](https://github.com/apolinario/decision-index/blob/main/docs/suite.md)

## 后续 benchmark 转换的参考约定

记录日期：2026-10-13。**用户确认：Decision Index 的适配逻辑可用于我们之后的 benchmark 转换，作为后续设计参考。** 当前记录的是方向，具体任务、转换协议与实现留待后续确定。

优先参考以下方法：

1. 用 `state + questions + criteria` 表达决策输入，将 gold、来源与评分元数据留在评测端。
2. 每类 benchmark 单独编写 adapter，并明确原任务、转换后问题、标签映射与保留/省略的能力；区分直接选项映射、机械改编和需要构造语义选项的改编。
3. 保留原始案例与关联请求的对应关系；记录来源版本、抽样 seed、请求 ID 和 payload 哈希，冻结后供各模型配对比较。
4. 为构造的干扰项检查答案泄露、位置偏差与重复；检查上下文是否包含未来信息或 gold。GSM8K、SGD 与 RouterBench 的问题可作为转换审查案例。
5. 根据转换后的任务语义选择评分器，并保留 coverage 与失败记录。若合成跨任务指数，再单独确定机会基线和权重。

应用到我们的安全 benchmark 时，仍按 MSB、MCPTox、AgentDojo 等原任务分别定义正确动作与评测单位；静态决策改编的结果只支持对应判断能力，完整交互任务的成功率继续单独衡量。Decision Index 的总分权重与私有测试设计不是本次确认的复用内容。

后续启动转换设计时，先回看本节及本报告的任务转换表，再确定各 adapter 的协议；实现参考固定源码版本 `f8552a13b643d39f61185f5951bb5fed16bedf51`。

## 实际复现入口

在源码目录安装 rebuild 依赖，然后：

```powershell
python -m pip install -e ".[rebuild]"
$env:HF_HUB_DISABLE_XET = "1"
python -X utf8 -m decision_index suite rebuild --edition 0.3 --work work

python -X utf8 -m decision_index suite import --edition 0.3 `
  --rows work/artifacts/benchmark-suite/release-v2-rebuilt/selected-rows.jsonl.gz `
  --added-rows work/artifacts/benchmark-suite/release-v2-rebuilt/added-rows.jsonl.gz `
  --gsm8k-rows work/artifacts/benchmark-suite/release-v3-rebuilt/gsm8k-rows.jsonl.gz

python -X utf8 -m decision_index pipeline --edition 0.3 --engine http `
  --option base_url=http://127.0.0.1:8000 --option model=my-model --out runs/my-model
```

HTTP 服务需支持 `/v1/systemone` 格式。文档估计约 7 GB 下载、17 GB 工作空间；HLE 需接受访问条款。此处命令根据 CLI 和 README 整理，**本轮未执行完整重建或推理**。[复现说明](https://github.com/apolinario/decision-index/blob/main/README.md)

## 本轮核查材料与限制

- 源码 checkout：[`data/decision-index-source`](../../data/decision-index-source/README.md)，commit `f8552a13b643d39f61185f5951bb5fed16bedf51`。
- 在线快照：[`data/decision-index-research-2026-10-13`](../../data/decision-index-research-2026-10-13/README.md)，保存榜单 JSON、方法 HTML 与 Space README。
- 公共指数检查：[`public-index-check.json`](../../data/decision-index-research-2026-10-13/public-index-check.json)。直接调用聚合函数，对项目 fixture 的 11 个模型重算，各误差均小于 0.005 指数点。
- 本机未安装 pytest，因此没有运行其完整 pytest 套件；改用直接聚合检查。Windows 默认 GBK 导致源码读取失败，开启 `python -X utf8` 后完成上述检查。

检查只确认这批固定 per-benchmark 值的聚合数学与 fixture 一致，不能证明样本构建正确、模型结果可复现或私有 Full score 有效。私有部分的具体题目构建与标签质量仍无法从公共工具独立核查。
