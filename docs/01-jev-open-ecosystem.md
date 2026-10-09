# 基于 Jev 的开源模型生态深度调研报告

> **调研时间**：2026 年 10 月 1 日
> **数据基准**：JevBench v1.4.2.2（2026-09-27 冻结，95 个系统 / 91 个已排名）
> **核心结论前置**：Jev 发布 16 天内，社区已产出 **90+ 个开源决策模型/服务**，其中 **3 个开源模型的综合分超过 Jev 官方 1.13.0**。但"超过"几乎全部来自速度与成本轴；一旦题目换成模型从未见过的密封题，**所有 Jev 类模型（含原版）的准确率从 ~86% 崩到 ~35%**，而同期通用大模型仍有 90%+。Jev 类模型打破的是"决策的成本结构"，不是"决策的能力上限"。

---

## 一、Jev 是什么，为什么会在两周内被复刻几十次

### 1.1 模型本身

2026 年 9 月 15 日，前 OpenAI 研究员、RLHF 共同发明者 Diogo Almeida 创办的 **TypeSafe AI** 发布 **Jev**（当前版本 `jev-1.13.0`），并提出一个新类别名：**System One Model（系统一模型）**。

它的形态与 LLM 完全不同：

| 维度 | 通用 LLM | Jev |
|---|---|---|
| 输出 | 逐 token 自回归生成文本 | 一次前向，直接返回**类型化答案 + 每选项概率** |
| 问题类型 | 任意 | 三种原语：`choice`（从你给的选项里选一个）、`noul`（是/否概率）、`score`（有序量表打分） |
| 延迟 | 秒级到分钟级 | 官方称 70–500 ms |
| 计费 | 输入+输出 | 输入 \$0.042 / 百万 token，**输出免费** |
| 幻觉 | 可能编造 | 输出被选项集封死，"不可能编出选项外的答案" |
| 上下文 | — | 32K token 状态，单个 choice 最多 255 个选项 |
| 权重 | — | **闭源，仅托管 API**（未向中国大陆开放） |

名字取自 19 世纪经济学家杰文斯（Jevons），暗合"杰文斯悖论"：智能使用成本暴跌 → 智能用量暴涨。

官方定位不是"用来聊天的模型"，而是程序里的**"聪明的 if-else"**：Agent 循环里最高频的原子判断（这条工单归哪个组、这个工具调用要不要批准、这份草稿过不过审）交给它，昂贵的慢思考留给大模型。负责组装这套"快慢分工"的工程层，业界称为 **Harness**。

### 1.2 为什么复刻潮来得这么快

三个原因叠加：

1. **核心机制极其简单**。把每个候选选项映射成 tokenizer 里的单个 token（A/B/C/D…），组织好 prompt，跑一次前向传播，直接读答案位置上的 logits，在你给的选项集上做 softmax。不做解码循环，不生成任何文本，不解析 JSON。这套"单 token logits 打分"几小时就能写出来。
2. **底座现成**。绝大多数复现都站在 **Qwen3.5**（0.8B / 2B / 4B / 9B / 35B-A3B）或 **ModernBERT / DeBERTa / Gemma 4** 上，Apache-2.0，可直接商用。
3. **训练成本近乎为零**。**Together AI 的 Tev1 训练只花了约 \$17、25 分钟**；个人开发者 mohit67890 的 Imajev-4B 总共 \$1,200、15 天；Jeff 系列在一张家用工作站 GPU 上训练约 2 小时。

Latent Space 当时的统计是"两天出了 6 个 Jev 克隆"。到 9 月底，GitHub 上名字里带 JEV 的仓库已达 **13,000+**，其中 50 star 以上、经过源码评审的精选清单（Awesome JEV）收录 **228 个**，内有 **31 个属于"开源模型/权重"类**。

---

## 二、生态规模：到底有多少个

### 2.1 分层计数（从严格到宽泛）

| 层次 | 数量 | 口径 |
|---|---:|---|
| **进入 JevBench 独立评测的开源决策模型/服务** | **81** | JevBench v1.4.2.2 的 95 个系统中，`open=yes/True/weights` 的条目 |
| 其中：**真正独立训练/微调过的 Jev 复现** | 59 | JevBench 分类 `jev-rebuild` |
| 其中：**开放接口的 System-One 实现** | 5 | `system-one-open`（如 Mapika/decider、blockbrain 系列） |
| 其中：**纯 logits 读出（未训练）** | 4 | `native-logit`（如 Jobe、NInfer） |
| 其中：**小分类器 / 零样本编码器** | 5 | `classifier`（Laya、GLiNER2.5、OpenDecision 等） |
| **JevBench 中的对照组** | 10 | `raw-logit-control` 5（裸 Qwen logits）+ `reranker` 5 |
| **Awesome JEV 精选（50+ star、源码评审）** | 228（Open models 类 31） | 2026-09-28 版 |
| **GitHub 含 JEV 的仓库** | 13,000+ | 含大量应用、SDK、玩具项目 |
| **HF "Jev Decision Index" 追踪的权重条目** | 60+ | multimodalart/jev-decision-index |

**一句话回答"有多少"**：**有可信第三方评测背书的、能真正跑起来的开源 Jev 类模型，约 80 个；其中经过微调/训练的不是几个，而是 60 个以上。** 加上应用层项目，整个生态在两周内膨胀到两百多个有质量的项目、一万三千多个仓库。

### 2.2 时间线：16 天的爆发

| 日期 | 事件 |
|---|---|
| 09-15 | TypeSafe 发布 Jev 1.13.0（闭源 API） |
| 09-17 | browser-use 开源 `jev-ultrafast`（HN 首页，18.2K star） |
| 09-18 | Convai Innovations 发布 **Laya**（ModernBERT 421M）；JevBench v1.0 出现（242 题） |
| 09-19 | **APUS**（麒麟合盛）发布全球首批独立开源复现，封装为 `fast-browser-use` Agent Skill |
| 09-20 | Jared Palmer 发布 **kev** 家族（0.5B/0.8B/4B/9B） |
| 09-21 | 诺基亚应用研究院 + 腾讯混元发布 **AnyJev**（免训练）；JevBench 扩到 534 题 |
| 09-22 | JevBench v1.3.0 首次公开榜单（48 行）；Hanno Labs 发布 **DecisionBench**（43 任务 / 23,900 行）+ **Bosun v3.1** |
| 09-23 | Together AI 发布 **Tev1-4B-experimental**；Mapika 发布 **decider** 家族 |
| 09-24 | JevBench **v1.4.2 引入 308 条密封题**，decider-4b v2 首次登顶；Fastino 发布 GLiNER2.5-Decide |
| 09-25 | **JevK5 v0.3**（Apache-2.0，4B/9B，双教师蒸馏） |
| 09-26 | 上海 AI Lab / 书生·InternLM 发布 **Intern-Decision**（0.8B/2B/4B） |
| 09-27 | JevBench v1.4.2.2，**Imajev-4B 登顶** |
| 09-28 | **Jeff** 系列（0.8B/2B，HN 353 分）；ImageJevBench v0.1.3 发布 |

---

## 三、技术路线：六种复刻方式

社区把"做一次决策"这件事拆出了六条不同路径，成本和能力差异极大。

### A. 冻结基座 + 直接读 logits（**零训练**）
不做任何梯度更新，把选项映射成单 token，读答案位置的 logits。
- 代表：**AnyJev**（诺基亚 + 腾讯混元，Apache-2.0）、**Jobe**、**local-jev**、JevBench 的 `raw-logit-control` 对照组
- 优点：零成本、零数据、任意 LLM 立即可用
- 致命问题：**位置偏置 + 标签偏置**。AnyJev 实测，同一题把选项顺序倒过来，裸 logits 的答案翻转率 **23%**；Qwen3-8B 上不同位置之间的先验 logit 差最大达 **6.81**（≈900 倍权重）；校准误差 ECE **0.240**（嘴上说 90% 把握，实际只有六七成）
- AnyJev 的解法：L0 层做**循环移位边际化**（把选项做 K 种循环移位各读一次，在 log 空间取平均）+ 无标签先验校正 → 翻转率 23% → **7.3%**，一条标签都不用

### B. LoRA / 全参微调 + 选项字母 logits 读出（**主流路线**）
- 代表：**JevK5**、**decider**、**Plumb-4B**、**reflex**、**Hopper**、**Jeff**、**metask-jev-4b**、**Intern-Decision**、**Tev1**、**Bosun v3.1**
- 做法：1 个 epoch，batch 256，对选项字母做交叉熵，训完再拟合**一个温度**做校准
- 成本：Tev1 \$17 / 25 分钟；Jeff 单卡 2 小时；Imajev-4B \$1,200 / 15 天
- 这条路线出了榜单前 10 名里的 8 个

### C. 编码器 + 打分头（**超小、可 CPU、可离线**）
- 代表：**Laya**（ModernBERT-large 421M + 322M 多语言版）、**GLiNER2.5-Decide**（340M，GLiNER 原班人马）、**Von**（395M）、**verdict-small**（118M）、**openJev Verdict**（ModernBERT 151M）、**open-jev-deberta-v3-large**
- 优点：可在 CPU / Apple Silicon / 气隙环境跑；成本极低（Laya 榜上 \$0.0029/千次）
- 缺点：**上下文与选项数受限**（Laya 512–1024 token），泛化最弱，基线 checkpoint 在域外**接近随机**

### D. 离散扩散路径
- 代表：**djev**（Maisa，DiffusionGemma 26B-A4B）、**razorback16/OpenJev**（同一底座 + vLLM PR #57250）
- 思路：不逐 token 生成，而是把答案模板写进"画布"，只留标签槽位做噪声，一次去噪步读出全部分布
- 注意：djev 明确声明**不是独立训练的模型，而是一种推理方法**，无自有权重

### E. 闭式解 head / 提前退出（**免梯度的新方向**）
- **AnyJev L2**：前向只跑到约 2/3 深度，用闭式线性 head 从中间隐状态直接读决策。反直觉结果——**砍掉深度是净赚**：Qwen3-1.7B 只用 64% 深度达 0.730（Jev 公布值 0.727），Qwen3-4B 达 0.786；速度是完整前向的 0.68 倍，100 条标签即可拟合
- **CLM-8B**（Stanford，冻结 Qwen3-8B + 75MB 投影）：JevBench 排 **78/89**，且被三个独立后端复现发现**三种问题类型中有一种恒定返回同一答案**——是重要的负面证据
- **typecastlm**、**Cygnet**（冻结 Gemma-4-12B-it + MIT shim，榜上第 6）

### F. 多模态扩展（Jev 本身做不到）
- **Imajev**（2B/4B/9B）：图 + 记录 + 类型化问题 → 带"unknown"选项的校准概率，**ImageJevBench v0.1.3 第 1 名**
- **decider-2b-vision**、**Jev-Omni**（Gemma-4-12B + 256 路决策头）、**Intern-Decision**（多模态）

---

## 四、效果到底如何：JevBench v1.4.2.2 全量解读

### 4.1 先说评测方法（这决定了分数怎么读）

JevBench 是目前唯一由**独立第三方（Benchmark Heaven）**运行、且**开源权重参赛者一律在断网只读容器里、用评测方自己的 GPU 离线跑完**的榜单。这比各家模型卡的自报数字可信得多。

- **题目**：每系统 842 道决策 = 534 道公开（easy 72 / standard 96 / judge 146 / hard 220）+ **308 道全新密封题**
- **四轴，等权调和平均**（ weakest axis dominates ）：
  `Score = 4 / (1/I + 1/C + 1/S + 1/K)`
  - **I 智能**：机会校正后准确率，tier 权重 hard 30% / judge 28% / standard 28% / easy 14%；混入 20% 密封题；公开→密封差距 >25pp 要扣分
  - **C 校准**：hard tier 上的 ECE + 对 gold 分布的忠实度
  - **S 速度**：`100 − 20·log10(p50/0.1s)`，每慢 10 倍扣 20 分
  - **K 成本**：`100 − 30·log10($/千次 ÷ 0.001)`，每贵 10 倍扣 30 分
- **密封集随机猜测基线 = 29.3%**

### 4.2 榜单前十

| # | 系统 | 开源 | 总分 | I 智能 | C 校准 | S 速度 | K 成本 | 公开% | 密封% | p50 | \$/千次 |
|---:|---|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **Imajev-4B** (mohit67890) | ✅ | **67.37** | 52.2 | 80.4 | 90.6 | 59.7 | 86.1 | 37.0 | 0.229s | \$0.022 |
| 2 | **Plumb-4B** (crh225, JevK5+LoRA) | ✅ | **65.84** | 53.0 | 75.5 | 93.5 | 55.8 | 89.6 | 38.0 | 0.183s | \$0.030 |
| 3 | **decider-4b v2** (Mapika) | ✅ | **64.13** | 49.4 | 75.0 | 92.9 | 60.9 | 83.5 | 34.7 | 0.185s | \$0.020 |
| 4 | **Jev 1.13.0** (TypeSafe，原版) | ❌ | **63.29** | **53.1** | 76.3 | 83.3 | 52.0 | 86.6 | 36.7 | 0.652s | \$0.040 |
| 5 | **JevK5 v0.2.0** (allebee) | ✅ | 62.04 | 48.9 | 74.5 | 91.1 | 59.5 | 85.3 | 33.1 | — | \$0.022 |
| 6 | **Cygnet** (blockbrain, 冻结 Gemma-4-12B) | ✅ | 61.76 | 49.5 | 74.9 | 90.7 | 52.8 | 87.9 | 33.8 | 0.220s | \$0.037 |
| 7 | **Hopper** (HopitAI) | ✅ | 59.43 | 48.0 | **79.1** | 86.8 | 58.7 | 82.3 | 34.1 | 0.408s | \$0.024 |
| 8 | Winnow-12B Q8 (Eldan Ring) | ✅ | 55.58 | 48.3 | 64.8 | 82.3 | 52.9 | 85.7 | 33.1 | 0.600s | \$0.037 |
| 9 | reflex 4B (kshetrajna12) | ✅ | 53.99 | 47.5 | 70.4 | 68.0 | 59.7 | 79.2 | 28.2 | 3.749s | \$0.022 |
| 10 | djev (Maisa, DiffusionGemma) | ✅ | 52.23 | 47.0 | 55.4 | 91.4 | 57.6 | 84.0 | 29.9 | 0.237s | \$0.026 |

**读法**：
- 前 3 名全开源，原版 Jev 掉到第 4。但**第 1 到第 4 只差 4.08 分**，而榜单作者自己声明 **~1 分差距可能是噪声**。说"开源全面超越"是过度解读。
- **开源赢在哪**：速度（S 90+ vs Jev 83.3）和成本（K 55–61 vs Jev 52.0），以及延迟绝对值——Plumb-4B 调整后 p50 **183 ms**，Jev **652 ms**。
- **Jev 仍赢在哪**：智能轴 I=53.1 是所有 Jev 类模型里最高的（Plumb 53.0、Imajev 52.2 紧咬），校准 76.3 也在第一梯队。
- **校准反超**：**Hopper 79.1 > Jev 76.3**；另有实测称 Laya 的 ECE 0.081 vs Jev 0.246。开源在"概率是否可信"这件事上已经不输甚至更好。

### 4.3 最重要的发现：公开 → 密封的坍塌

这是整份报告里最需要记住的一张表。

| 系统 | 公开题准确率 | 密封题准确率 | 落差 |
|---|---:|---:|---:|
| Imajev-4B | 86.1% | **37.0%** | −49.1pp |
| Plumb-4B | 89.6% | **38.0%** | −51.6pp |
| decider-4b v2 | 83.5% | **34.7%** | −48.8pp |
| **Jev 1.13.0** | 86.6% | **36.7%** | **−49.9pp** |
| JevK5 v0.2.0 | 85.3% | 33.1% | −52.2pp |
| Cygnet | 87.9% | 33.8% | −54.1pp |
| — | | | |
| **GPT-6 Luna** | 99.6% | **95.5%** | −4.1pp |
| **DeepSeek V4.1 Flash** | 97.8% | **94.8%** | −3.0pp |
| **GPT-5.6 Luna** | 97.4% | **89.0%** | −8.4pp |
| *（密封集随机猜测）* | — | *29.3%* | — |

**结论非常硬**：

1. **坍塌是普遍的，不是开源的问题**。原版 Jev 自己就塌了 49.9pp，和开源复现塌的幅度完全一致（48–57pp）。这说明它反映的是**这条技术路线的共同上限**，而非"开源没做好"。
2. **最好的 Jev 类系统（Imajev-4B）在密封题上 37.0%，只比随机猜测 29.3% 高 7.7 个百分点**。榜单作者自己的原话是：密封集"非常难"，"大多数系统的分数接近随机"。
3. **同期通用大模型在密封题上是 89%–95.5%**。Jev 类模型在"见过的、同分布的、边界清晰的"任务上高效得惊人，但对**真正没见过的问题几乎没有泛化**。
4. 那为什么大模型总分那么低？因为**四轴等权调和平均下，最弱的轴说了算**：GPT-6 Luna 总分 33.27（I=97.4 但 K=36.0、S=72.6），DeepSeek V4.1 Flash 总分 4.77（I=94.0 但 K=16.8）。它们被打死在成本和速度上，不是能力上。

**换句话说**：Jev 类模型解决的是"**已经知道该怎么判的判据，能否用 1/400 的成本、1/200 的时间执行**"，而不是"**面对新问题时能否判对**"。把两者混为一谈，是当前社区宣传里最大的误导。

### 4.4 其他独立实测（含负面证据）

不能只看一个榜单。以下是**非关联第三方**的实测：

| 来源 | 对比 | 结果 |
|---|---|---|
| 某中文技术团队实测（同语料/同样本/同阈值） | Jev vs openjev vs SemIf | **Jev 92.2% vs openjev 75.9% / SemIf 79.7%**；开源版延迟漂亮（0.71s 最快档），但**校准差一截、放行过多** |
| xyspace 400 道新题 | Jev vs Together 的 Tev1 | **Jev 97.2% vs Tev 90.0%**；难题子集 **95.9% vs 84.1%**；ECE Jev 2.0 vs Tev 3.1；Brier 0.041 vs 0.158 |
| Jeff 的 HN 讨论（569 分） | Jeff vs Jev 在真实分类场景 | 一位实践者报 **70% vs 94%**，原话"unacceptable"；另一位说 0.8B 在职位分类上"completely useless"，2B 仍漏掉核心标签 |
| Milvus / Zilliz 三个真实项目 | Jev 接入 DeepSearcher / MemSearch / Vector Graph RAG | DeepSearcher 100 道多跳题：与 DeepSeek V4 Flash **同为 93.25% Recall@5**，延迟中位数 2.23s→**0.55s**，成本约 **1/7**。MemSearch：Recall@5 74.71%→79.41%，仍落后 Voyage rerank-3 的 81.87% |
| Milvus RAG 重排专项（80 条 SciFact） | Jev vs qwen3.7-text-rerank | Jev nDCG@10 **+0.0778**（最好），但 **P50 重排延迟高 10.2 倍、单次成本 6.7 倍** |
| AnyJev 的运营视角指标 | 校准前后可自动放行流量 | 5% 错误率红线内，可自动决策的流量从 **7.7% → 52.0%**（7 倍）。作者认为这个数字比准确率重要得多 |
| Stanford CLM-8B | 三个独立后端复现 | **三种问题类型中有一种恒定返回同一答案**（与输入无关）；JevBench 排 78/89 |

**规律**：在**有边界、高频、可枚举**的任务上（工单路由、相关性判定、停止搜索、内容过滤），开源复现已经能用，且性价比极高；在**需要规则推理、多跳、数值/日期比较**的任务上，开源与 Jev 的差距是 7–16 个百分点，且两者都不如直接上大模型。

### 4.5 交叉验证：其他榜单

- **DecisionBench**（Hanno Labs，43 任务 / 23,900 行 / 28 域，含 1,200 行推理专项）
  - Bosun v3.1 0.6B：整体 **81.18%**，ECE 0.0659；但**推理专项只有 43.08%**，ECE 0.2019 —— 再次印证"非推理任务强、推理任务崩"
  - Imajev-4B：**第 3 / 56**，79.65，超过 GLM-5.3 Flash(320B)、Jev 1.13、DeepSeek V4.1 Flash(552B)、GPT-5.6 Luna
- **ImageJevBench v0.1.3**（89 张合成图，49 个系统）：Imajev-4B **#1（76.39）**，领先 Jev-Omni 12B（73.10）、NeoHorse Jev 4B（71.94）。跑完前 5 名全榜只花 **\$0.0217**
- **JevBench 子榜 Capability 排名**："在 Jev 2 倍成本与延迟以内的系统中，Imajev-4B 以 66.3 领先 Jev 类系统"

---

## 五、重点模型逐一剖析

### 🥇 Imajev-4B（mohit67890）— 当前综合实力第一
- **底座**：Qwen3.5-4B + LoRA + 小型决策头；**支持图片**（照片 + 记录 + 类型化问题）
- **许可**：Apache-2.0；MLX 可跑 Mac，PyTorch 可跑单 GPU
- **训练**：\$1,200 租金、15 天、 solo 开发者（一位做过财富 500 强流程改进咨询的顾问）
- **关键教训**：第一版用 50 万条短决策样本训 9B，**推理能力反而从 64.9 掉到 42.3**（学会了模式匹配而非思考）。改法是生成真正的难题，并**只保留两个不同 AI 答案一致的样本**，才拉回来
- **特色**：每个答案都带一个 **"unknown"（无法判断）概率**，可主动弃权
- **成绩**：JevBench #1/91（67.37）、ImageJevBench #1/49（76.39）、DecisionBench #3/56（79.65）
- **诚实 caveat**：作者自己说明——第一名是四轴等权的结果，**单看准确率只排第三**

### 🥈 Plumb-4B（crh225）
- JevK5 v0.2 之上再叠 LoRA；Apache-2.0，NOTICE 中署名 JevK5 / Qwen / SemIf
- **I=53.0 是所有开源里最高的**（比 Jev 的 53.1 只低 0.1），S=93.5 速度第一梯队
- 在 H100 上 p50 原始 **16.5 ms**，调整后 183 ms

### 🥉 decider-4b v2（Mapika）— 最早登顶的那个
- 9/24 曾在 v1.4.2 上 **64.13 > Jev 63.29**，是第一个在综合分上压过原版的开源模型
- **完整家族**：decider-0.8b / 2b (v11) / 4b (v2.1) / 35b-a3b / 35b-a3b-nvfp4 / 2b-vision，共享统一接口与读出方式
- 自报数字：regression set 0.831 in-task / 0.784 held-out；JevBench hard 0.649；live browser 93% sampled
- 作者对版本选择很严谨：v2.1 默认、v2 在 hard 多步题上校准更好（0.104 vs）、v1 适合表单填写与网格导航

### JevK5（allebee）— 文档最扎实的一个
- Apache-2.0，4B / 9B / 2B / GGUF 全套；基座 Qwen3.5-4B，LoRA rank 16 合并进权重
- **训练数据可审计**：v0.3 用 17,408 道教师题（Qwen3.6-27B + GPT-6 Luna 双教师）+ 26 个公开数据集 train split 的 30,052 条人工标注做 replay，**明确不用任何数据集的 test/validation split，完全不用 MMLU/MMLU-Pro/BBH**
- **运行时**：每个 padded 长度一个 CUDA graph，H100 上 **~13 ms/决策**
- 9B v0.3.3：hard tier 0.775（v0.3 是 0.730），hard ECE 0.071（v0.3 是 0.126）
- 兼容性：GGUF Q8_0 在 231 道公开题上与 bf16 一致 229 道

### AnyJev（诺基亚应用研究院 + 腾讯混元）— 唯一的"零训练"路线
- Apache-2.0，**一个参数都不动**
- 三档：L0 零标签（循环移位消位置偏置）→ L1 温度缩放（每题 100–500 条标签）→ L2 闭式 head（提前退出到 2/3 深度）
- **效果**：BANKING77 20 分类上，顺序翻转率 23% → 7.3%；准确率 0.747 → 0.807；**ECE 0.240 → 0.095**；5% 错误率红线内可自动决策流量 **7.7% → 52.0%**
- L2 反直觉结论：**Qwen3-1.7B 只用 64% 深度达 0.730 ≈ Jev 公布的 0.727**；Qwen3-4B 0.786 追平微调过的 421M Laya（0.768）
- 自适应早停：18 选 1 时平均只读 4.1 轮，与读满 18 轮结果一致率 98.7%，吞吐 2.2–2.7 倍
- 局限：head 按问题拟合、不能迁移到新问题；目前只发了 Qwen3 系列 head；字母读法上限 26 个选项；官方明确说"迷宫、扫雷这类模型本身就答不出来的任务，校准也救不了"

### Laya（Convai Innovations）— 最"能落地"的小模型
- ModernBERT-large **421M**，另有 322M 多语言版；Apache-2.0；**17.1K star**
- 可在 CPU / Apple Silicon（有 CoreML 移植）跑；榜上成本 **\$0.0029/千次**（全场最低档）
- **重要警告**：作者自己说明**基座 checkpoint 在 typed-decisions 上接近随机**，只有**微调过的 checkpoint 才有 0.766**（vs Jev 0.727）。"下载通用 checkpoint 直接上生产"是最常见的踩坑
- 有实测称其 ECE 0.081 vs Jev 0.246

### Intern-Decision（上海 AI Lab / 书生·InternLM）— 国内最强
- 2026-09-26 上线，**0.8B / 2B / 4B** 三档，Apache-2.0，Qwen3.5 对应尺寸微调
- 机制：选项映射成单 token 符号（A-Z/a-z/0-9）+ prompt 渲染完整 JSON skeleton 与每字段占位 + 占位前 logits 取 softmax + 校准
- **厂商自报（未经第三方复现）**：4B 七套件均分 **90.02**，高于 Jev 的 **88.74**；单卡 RTX 4090 端到端 **44.16 ms**，约为 Jev 109.70 ms 的四成
- 分项：JevBench-Hard 73.87 / Typed Decision 80.55 / ToolACE 96.45 / WildJailBreak 89.86
- **注意**：中间档 2B 在 ECE 校准上偏弱，落地建议自拟合温度；**准确率与延迟均为厂商自报，第三方复现仍在进行**
- 团队还用经典概率题（掷骰子、蒙提霍尔）搭了校准基准，称 Jev 的预测分布偏离 golden 分布较远

### 其他值得记的名字

| 项目 | 作者 | 特点 |
|---|---|---|
| **Tev1-4B / 0.8B** | Together AI | **\$17、25 分钟**训出来的 4B（Qwen3.5-4B LoRA）；Ollama 0.35+ 可直接 `ollama pull tev1`；**保留自回归头**，是"写字母"而非"读 logits"，严格说不还原 Jev 的并行接口 |
| **Jeff** (0.8B/2B/Gemma4-E2B) | Logan Markewich | fork 自 AutoJev 配方，压到笔记本可跑；0.8B 在 RTX PRO 6000 上 **22 ms**、M4 Max 上 28 ms；HN 353 分；**实践者实测不如 Jev**（70% vs 94%） |
| **Hopper** | HopitAI | **校准轴 79.1，全场最高**（超过 Jev 76.3） |
| **Bosun v3.1** (0.6B/1.7B) | Hanno Labs | Qwen3 + rank-16 LoRA + **256 个学习到的决策 token**；DecisionBench 81.18% / ECE 0.0659；推理专项 43.08% |
| **kev** (0.5B/0.8B/4B/9B) | Jared Palmer | 评测透明度最好，有训练代码 + 预注册测试集 |
| **GLiNER2.5-Decide** (340M) | Fastino（GLiNER 原班） | CPU 可跑，含气隙环境 |
| **fast-browser-use** | APUS（麒麟合盛） | MIT，本地 Qwen3.5-9B/35B-A3B；M2 Pro 消费级笔记本上**决策 79 ms**，维基检索中位 **18 秒**、表单填报约 3 秒，**单任务仅 4 次模型打分**，零云端调用 |
| **jev-ultrafast** | browser-use | MIT，18.2K star；Google Flights 苏黎世→伦敦 **7.07 秒**（含页面加载），中位 Jev 延迟 178 ms；协议调用从 1092 → 101 |
| **hoi4-jevai** | zwh20081 | 最有意思的垂直微调：DeBERTa-v3-large + 选项打分头，在《钢铁雄心 4》33 局观测数据（44.6 万状态、240 万问题）上微调，让 AI 国家选战略姿态；Intel NPU 上 233 ms/序列 |

---

## 六、局限、陷阱与风险（务必读完再选型）

### 6.1 模型能力层面

1. **泛化断层**：公开→密封坍塌 48–57pp（含原版）。**不要在"没见过的问题类型"上依赖它**。
2. **选项顺序敏感**：`open-alternative-jev` 在榜上被发现——同一模型、同一题，只把 `A. yes, B. no` 反转为 `A. no, B. yes`，在 answer-judging 项上 **72% → 21%**。小模型对选项顺序极其敏感。**选型时必须做顺序轮换测试**。
3. **长选项列表退化**：多数实现在超过 16–26 个选项时明显退化（Jeff v1.0 曾有"选不出第 26 个之后的选项"的 bug，v1.1 修到 254 个，0.8B 长列表测试从 40.3% → 94.7%）。
4. **推理/多跳/数值/日期弱**：这是所有 Jev 类模型的共同短板，不是开源的短板。
5. **Harness 决定一半表现**：有实测者发现，把三张"防御牌"列成三个独立选项后，概率被拆成三份，Jev 因此选了"结束回合"然后被打死。**哪些动作算一个选项、要不要合并，是工程师的设计责任**。

### 6.2 评测可信度层面

6. **自报数字泛滥**：多数模型卡的分数是作者自己跑的。JevBench 是目前唯一把开源权重拉到断网容器里用评测方硬件重跑的榜单——**优先看它**。
7. **延迟调整是假设不是测量**：JevBench 对自托管/演示端点做了 **×2 + 0.15s** 的调整来近似生产负载，作者明确标注"这是假设"。原始 p50/p95 在结果文件里。
8. **成本多是估算不是账单**：自托管行的成本用基座模型的公开挂牌价 × 实测 token 计算，**不是 GPU 账单**。JevBench 把这类行标为 `estimate`。
9. **只发布聚合密封统计**：v1.4.2.2 起，公开半区可被训练或针对性选择，因此 held-out 部分会随领域变化演进。

### 6.3 法律与工程层面

10. **许可证是三个独立事实**：代码许可证、权重可用性、权重许可证。宽松的仓库许可证 ≠ 基座模型的许可证。必须分别检查：
    - Qwen 系列：Apache-2.0
    - Gemma 4：Apache-2.0 **但附带 Google 的 Prohibited Use Policy**
    - **Malkuth-4B/2B 是 CC-BY-NC-4.0（仅研究用）**，因为训练混合里有 XNLI 和 RACE —— **不能商用**
    - 榜上有 2 个系统"截至评测时仓库中没有许可证文件"
    - `openjev-sglang`（ekzhang）未声明许可证，商用前需确认
11. **英文为主**：JevBench 全英文；Laya 有 322M 多语言版；Jev-Style v3 声称 51 种语言。
12. **项目成熟度**：jev-ultrafast 约两周大、**约 120 个未合并 PR、零 release**；很多模型是一周内的产物。榜单每天都在动。

---

## 七、选型建议

### 7.1 按场景选

| 场景 | 建议 |
|---|---|
| **纯本地 / 数据不出网 / 气隙** | Laya（CPU 可跑）、GLiNER2.5-Decide（340M）、Jeff-0.8B、decider-0.8b |
| **综合最强、要图片** | **Imajev-4B**（Apache-2.0，唯一支持图 + 主动弃权） |
| **纯文本、要最高智能轴** | **Plumb-4B**（I=53.0）或 **decider-4b v2** |
| **要最可信的概率（设阈值做自动放行）** | **Hopper**（校准 79.1 全场最高）、AnyJev L1/L2（ECE 0.240→0.095） |
| **完全不想训练、手头只有现成 LLM** | **AnyJev L0**（零标签，先跑起来再说） |
| **想要自己训、要可审计配方** | **JevK5**（训练数据可审计，不用任何 test split）、**kev**（预注册测试集）、Together 的 Tev1 配方（\$17） |
| **要中文/国产** | **Intern-Decision 4B**（上海 AI Lab，自报 90.02 均分；等第三方复现） |
| **浏览器 Agent** | jev-ultrafast（云端 API 版，最快）、fast-browser-use（本地离线版，数据不出机） |
| **选项超过 26 个** | JevK5-9B（>16 选项更强）、Jeff v1.1（支持到 254）、decider-35b-a3b |
| **多跳推理、数值、日期** | **不要用 Jev 类模型**，直接用大模型 |

### 7.2 落地前必做的六项验收

参考社区实践者的清单：

1. **真实标签准确率**（不是教师模型一致率）
2. **概率校准**（ECE / Brier）—— 这决定了你能不能设阈值
3. **候选项顺序与改写的稳定性** —— 必做顺序轮换
4. **长输入拒绝率**
5. **目标设备上的 P95 延迟、内存、每千次决策成本**
6. **阈值按错误成本设定**，不要因为输出了 0.9 就直接放行

### 7.3 推荐的引入姿势

不要一上来就替换。更稳妥的是**影子运行**：与现有流程并行打分、不执行动作、记录分歧，再由人工或已发生的业务结果核验。AnyJev 的"从 7.7% 到 52.0%"正是这种渐进式路径的收益——它衡量的不是"模型多准"，而是"多少流量可以安全地不用人看"。

---

## 八、三个判断

1. **数量上：生态已经饱和竞争。** 两周 90+ 个开源决策模型进入独立评测，前 3 名被个人开发者的 4B 模型占据。这个赛道的**训练壁垒已经被抹平**（\$17 起），剩下的壁垒是数据质量与校准。

2. **效果上：开源在"成本-速度-校准"三轴上已经追平或超过，在"泛化"上所有人（含原版）都还很差。** 前三名与 Jev 的 4 分差距里，绝大部分来自 S 和 K 轴；智能轴 Jev 仍是 Jev 类模型第一。真正的能力天花板是那个 **37% 的密封准确率**——它同时约束着开源和闭源。

3. **价值上：Jev 真正的产品不是模型，是接口契约。** `/v1/systemone` + choice/noul/score 三原语，让"决策"从提示词工程变成了一个可替换、可压测、可设阈值的工程组件。开源复刻们复制的是这个契约，而不是 Jev 的权重——**而事实证明，在大多数有边界的判断任务上，复制契约就够了。**

---

## 附录 A：JevBench v1.4.2.2 完整榜单（95 个系统）

> 数据源：`fstandhartinger/jevbench` → `results/v1.4.2.2/jevbench-v1.4.2.2-results.json`（生成于 2026-09-27 18:49 UTC，status: final）
> 列说明：**I**=智能（机会校正）| **C**=校准 | **S**=速度 | **K**=成本 | 公开%/密封%=534 公开题 / 308 密封题准确率 | p50 为调整后中位延迟 | \$/千次为每 1000 次决策成本（**不是**每千 token）
> 类别：`jev-rebuild` 独立复现 | `system-one-open` 开放实现 | `native-logit` 原生 logits 读出 | `raw-logit-control` 裸模型对照组 | `classifier` 小分类器 | `reranker` 重排模型 | `llm-baseline` 通用大模型 | `jev` 官方 Jev 及同类

| # | 系统 | 作者 | 类别 | 开源 | 总分 | I | C | S | K | 公开% | 密封% | p50(s) | $/千次 | 链接 |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Imajev-4B | mohit67890 | jev-rebuild | ✅ | 67.37 | 52.2 | 80.4 | 90.6 | 59.7 | 86.1 | 37.0 | 0.229 | 0.022 | [↗](https://github.com/mohit67890/imajev) |
| 2 | Plumb-4B (crh225, JevK5 v0.2 + LoRA) | crh225 | jev-rebuild | ✅ | 65.84 | 53.0 | 75.5 | 93.5 | 55.8 | 89.6 | 38.0 | 0.183 | 0.0298 | [↗](https://github.com/crh225/plumb) |
| 3 | decider-4b v2 (Mapika) | Mapika | system-one-open | ✅ | 64.13 | 49.4 | 75.0 | 92.9 | 60.9 | 83.5 | 34.7 | 0.185 | 0.0201 | [↗](https://github.com/Mapika/decider) |
| 4 | Jev 1.13.0 (TypeSafe AI) | TypeSafe AI | jev | ❌ | 63.29 | 53.1 | 76.3 | 83.3 | 52.0 | 86.6 | 36.7 | 0.652 | 0.0399 | [↗](https://docs.typesafe.ai) |
| 5 | JevK5 v0.2.0 | allebee | jev-rebuild | None | 62.04 | 48.9 | 74.5 | 91.1 | 59.5 | 85.3 | 33.1 | 0 | 0.0224 | [↗](https://github.com/allebee/jevk5) |
| 6 | Cygnet (blockbrain, frozen Gemma-4-12B-it) | blockbrain | system-one-open | ✅ | 61.76 | 49.5 | 74.9 | 90.7 | 52.8 | 87.9 | 33.8 | 0.22 | 0.0374 | [↗](https://github.com/blockbrain-ai/cygnet-recipe) |
| 7 | Hopper | HopitAI | jev-rebuild | ✅ | 59.43 | 48.0 | 79.1 | 86.8 | 58.7 | 82.3 | 34.1 | 0.408 | 0.0238 | [↗](https://huggingface.co/HopitAI/hopper) |
| 8 | Winnow-12B Q8 | Eldan Ring | jev-rebuild | ✅ | 55.58 | 48.3 | 64.8 | 82.3 | 52.9 | 85.7 | 33.1 | 0.6 | 0.0371 | [↗](https://huggingface.co/EldanRing/Winnow-12B) |
| 9 | reflex 4B (kshetrajna12) | kshetrajna12 | jev-rebuild | ✅ | 53.99 | 47.5 | 70.4 | 68.0 | 59.7 | 79.2 | 28.2 | 3.749 | 0.0221 | [↗](https://github.com/kshetrajna12/reflex) |
| 10 | djev (Maisa, diffusion-gemma) | Maisa (David Villalón) | jev-rebuild | ✅ | 52.23 | 47.0 | 55.4 | 91.4 | 57.6 | 84.0 | 29.9 | 0.237 | 0.026 | [↗](https://github.com/Davipar/djev-dev) |
| 11 | Jev-Omni (akhilaaa3, Gemma-4-12B merged) | akhilaaa3 | jev-rebuild | ✅ | 51.34 | 46.8 | 64.1 | 81.5 | 53.0 | 88.7 | 32.1 | 0.584 | 0.0368 | [↗](https://huggingface.co/akhilaaa3/Jev-Omni) |
| 12 | metask-jev-4b | Wayfind (metask-ai) | jev-rebuild | ✅ | 47.78 | 44.7 | 66.9 | 89.1 | 54.5 | 79.7 | 27.6 | 0.281 | 0.0328 | [↗](https://github.com/metask-ai/metask-jev) |
| 13 | SemIf, formerly OpenJev (Qwen3.5-4B, TheoLeeCJ) | Theodore Lee (TheoLeeCJ) | jev-rebuild | ✅ | 47.69 | 44.4 | 66.8 | 83.7 | 59.5 | 81.0 | 26.3 | 0.546 | 0.0224 | [↗](https://github.com/TheoLeeCJ/openjev) |
| 14 | Jobe Qwen3.5-4B (frozen) | MantisShrimpdev | native-logit | ✅ | 46.94 | 44.1 | 66.1 | 85.6 | 59.5 | 81.0 | 25.6 | 0.419 | 0.0224 | [↗](https://github.com/MantisShrimpdev/jobe) |
| 15 | local-jev Qwen3.5-4B | Amith Chandrappa (amithgc) | jev-rebuild | ✅ | 46.8 | 44.4 | 73.3 | 75.0 | 55.8 | 80.5 | 26.0 | 1.565 | 0.0297 | [↗](https://github.com/amithgc/local-jev) |
| 16 | system-one-open (Gemma 4 E2B LoRA on an L4) | mithalouni | jev-rebuild | ✅ | 45.11 | 44.2 | 54.9 | 77.0 | 64.8 | 73.2 | 27.6 | 1.303 | 0.0149 | [↗](https://github.com/mithalouni/system-one-open) |
| 17 | spark-s1-4b-v6 (Open Spark Jev, abhishek085) | Abhishek Rai (abhishek085) | jev-rebuild | ✅ | 44.62 | 45.1 | 47.6 | 81.0 | 57.9 | 79.2 | 26.6 | 0.779 | 0.0253 | [↗](https://github.com/abhishek085/open-spark-jev) |
| 18 | Malkuth-4B (newfull5, Kev post-train) | newfull5 (dhtocks) | jev-rebuild | ✅ | 44.45 | 43.1 | 61.5 | 88.3 | 61.5 | 74.9 | 23.4 | 0.327 | 0.0192 | [↗](https://github.com/newfull5/malkuth) |
| 19 | jqv (Qwen3-32B zero-shot) | hjmurmur (Octalab) | jev-rebuild | ✅ | 44.35 | 46.4 | 71.6 | 74.6 | 47.5 | 80.1 | 28.2 | 1.645 | 0.0564 | [↗](https://github.com/Octalab-Inc/jqv) |
| 20 | Qwen3-Reranker-4B | Qwen | reranker | ✅ | 43.49 | 44.6 | 65.2 | 78.7 | 49.2 | 68.0 | 29.9 | 0.41 | 0.0495 | [↗](https://huggingface.co/Qwen/Qwen3-Reranker-4B) |
| 21 | decider-35b-a3b (Mapika) | Mapika | jev-rebuild | ✅ | 41.18 | 47.2 | 65.3 | 80.8 | 45.3 | 83.1 | 31.5 | 0.734 | 0.0666 | [↗](https://huggingface.co/Mapika/decider-35b-a3b) |
| 22 | Raw Qwen3 4B Instruct 2507 direct logits | Alibaba Qwen / neutral reproduction | raw-logit-control | ✅ | 40.95 | 46.4 | 29.1 | 87.6 | 59.7 | 69.7 | 27.3 | 0.315 | 0.0221 | [↗](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) |
| 23 | OpenSourceJev (Qwen3.5-4B Q4_K_M, native llama.cpp) | sabeel111 | jev-rebuild | None | 40.87 | 41.8 | 60.3 | 82.0 | 64.0 | 78.4 | 26.3 | 0 | 0.0159 | [↗](https://github.com/sabeel111/OpenSourceJev) |
| 24 | ZeroEntropy zerank-2 | ZeroEntropy | reranker | ✅ | 40.21 | 42.1 | 75.8 | 79.0 | 49.8 | 70.1 | 28.6 | 0.403 | 0.0473 | [↗](https://huggingface.co/zeroentropy/zerank-2-reranker) |
| 25 | decision-machine-1 (milliseconds.ai) | milliseconds.ai (Baptiste Laget) | decision-api | ❌ | 39.94 | 41.3 | 68.3 | 92.9 | 53.7 | 67.5 | 25.6 | 0.172 | 0.035 | [↗](https://www.milliseconds.ai) |
| 26 | Malkuth-2B (newfull5, Kev post-train) | newfull5 (dhtocks) | jev-rebuild | ✅ | 38.93 | 41.3 | 53.5 | 91.4 | 61.5 | 69.7 | 24.4 | 0.24 | 0.0192 | [↗](https://github.com/newfull5/malkuth) |
| 27 | Raw Phi-4 mini direct logits | Microsoft / neutral reproduction | raw-logit-control | ✅ | 37.96 | 41.8 | 58.8 | 88.8 | 49.6 | 65.8 | 29.2 | 0.278 | 0.048 | [↗](https://huggingface.co/microsoft/Phi-4-mini-instruct) |
| 28 | JEV Qwen3.5-9B Base NVFP4 | WilfLin | jev-rebuild | ✅ | 37.7 | 46.8 | 67.7 | 93.3 | 43.3 | 75.3 | 29.5 | 0.189 | 0.0775 | [↗](https://huggingface.co/WIlfLin/JEV-Qwen3.5-9B-Base-NVFP4) |
| 29 | OpenJev (DiffusionGemma 26B-A4B NVFP4, razorback16) | razorback16 / Codiv | jev-rebuild | ✅ | 36.85 | 45.4 | 55.0 | 83.2 | 45.5 | 81.8 | 28.6 | 0.633 | 0.0656 | [↗](https://github.com/razorback16/openjev) |
| 30 | kev 4B (research preview) | Jared Palmer | jev-rebuild | ✅ | 36.14 | 42.1 | 39.6 | 75.7 | 61.8 | 66.2 | 22.4 | 1.25 | 0.0188 | [↗](https://github.com/jaredpalmer/kev) |
| 31 | Decision 2B (FlyMy.AI, v59) | FlyMy.AI (@denti) | jev-rebuild | ✅ | 35.8 | 38.8 | 74.1 | 84.3 | 62.5 | 75.3 | 26.0 | 0.528 | 0.0178 | [↗](https://huggingface.co/flymy-ai/decision-2b-preview) |
| 32 | Qwen3.5-9B Jev-like data-mix v2 | jsaurabh | jev-rebuild | None | 35.24 | 47.4 | 61.3 | 82.0 | 42.4 | 78.4 | 29.2 | 0 | 0.0834 | [↗](https://huggingface.co/jsaurabh/qwen3.5-9b-jev-data-mix-v2) |
| 33 | GPT-6 Luna (low reasoning effort) | OpenAI | llm-baseline | None | 35.11 | 95.8 | 92.0 | 73.7 | 36.9 | 99.1 | 92.9 | 1.442 | 0.127 |  |
| 34 | SimpleJev Qwen3.8-27B | Featherless AI | jev-rebuild | ✅ | 34.57 | 51.6 | 74.5 | 71.2 | 39.5 | 86.6 | 35.7 | 2.028 | 0.104 | [↗](https://github.com/featherless-ai/simple-jev) |
| 35 | NInfer Qwen3.8-Flash-Next mixed | Igor L. / NInfer contributors | native-logit | ✅ | 33.98 | 49.5 | 78.6 | 88.2 | 38.9 | 89.6 | 34.1 | 0.308 | 0.1087 | [↗](https://github.com/igorls/ninfer) |
| 36 | swanOne (blockbrain, Qwen3.8-Flash-Next NVFP4) | blockbrain | system-one-open | ✅ | 33.61 | 52.6 | 71.0 | 82.5 | 38.6 | 88.7 | 38.6 | 0.712 | 0.111 | [↗](https://github.com/blockbrain-ai/swanone-recipe) |
| 37 | GPT-6 Luna (default medium reasoning effort) | OpenAI | llm-baseline | None | 33.27 | 97.4 | 93.5 | 72.6 | 36.0 | 99.6 | 95.5 | 1.477 | 0.1354 |  |
| 38 | open-alternative-jev (Qwen3.5-4B, IkerMoel) | IkerMoel | jev-rebuild | ✅ | 33.24 | 38.6 | 58.7 | 83.5 | 59.6 | 74.0 | 24.4 | 0.564 | 0.0222 | [↗](https://github.com/ikermoel/open-alternative-jev) |
| 39 | jev-local (Qwen3.5-9B) | us (GitHub) | jev-rebuild | ✅ | 32.54 | 45.2 | 64.2 | 69.2 | 43.3 | 74.9 | 29.5 | 2.24 | 0.0775 | [↗](https://github.com/us/jev-local) |
| 40 | Decision Fast (FlyMy.AI, v53a) | FlyMy.AI (@denti) | jev-rebuild | ✅ | 32.49 | 37.1 | 65.3 | 81.6 | 76.1 | 63.2 | 25.6 | 0.631 | 0.0063 | [↗](https://huggingface.co/flymy-ai/decision-fast-preview) |
| 41 | decider-2b (Mapika) | Mapika | jev-rebuild | ✅ | 30.74 | 38.5 | 43.5 | 83.2 | 61.0 | 71.0 | 24.7 | 0.672 | 0.02 | [↗](https://huggingface.co/Mapika/decider-2b) |
| 42 | jeff (Logan Markewich, GLiFormer 400M) | Logan Markewich | jev-rebuild | ✅ | 30.58 | 36.8 | 67.9 | 63.5 | 76.6 | 62.8 | 33.1 | 2.026 | 0.006 | [↗](https://github.com/logan-markewich/jeff) |
| 43 | Laya (Convai Innovations, ModernBERT-large 421M) | Convai Innovations | jev-rebuild | ✅ | 30.25 | 36.1 | 63.7 | 71.1 | 86.2 | 58.4 | 30.8 | 1.724 | 0.0029 | [↗](https://huggingface.co/convaiinnovations/laya) |
| 44 | Autoloops – Gemma 4 31B IT | Autoloops | jev | ❌ | 29.96 | 59.8 | 79.2 | 84.0 | 36.0 | 92.8 | 45.8 | 0.604 | 0.1363 |  |
| 45 | Standard One 8B (Standard Thinking) | Standard Thinking (myeongho12) | jev-rebuild | ✅ | 29.07 | 46.2 | 65.9 | 92.0 | 39.4 | 76.6 | 26.6 | 0.198 | 0.1044 | [↗](https://huggingface.co/StandardThinking/StandardOne-8B) |
| 46 | lev-350m (Franck Verrot, LFM2.5-350M) | Franck Verrot (franckverrot) | jev-rebuild | ✅ | 28.5 | 34.8 | 70.6 | 85.3 | 76.1 | 58.4 | 25.0 | 0.494 | 0.0063 | [↗](https://github.com/franckverrot/lev) |
| 47 | openjev-sglang (Qwen3.6-35B-A3B on SGLang) | ekzhang | jev-rebuild | ✅ | 27.65 | 49.4 | 69.2 | 77.1 | 36.5 | 85.3 | 33.1 | 1.355 | 0.1313 | [↗](https://github.com/ekzhang/openjev-sglang) |
| 48 | Von (wfzyx, Option-Marker 395M) | wfzyx (Victor Hugo) | jev-rebuild | None | 27.48 | 34.5 | 75.7 | 70.5 | 77.8 | 57.1 | 27.9 | 0 | 0.0055 | [↗](https://github.com/wfzyx/von) |
| 49 | NInfer Qwen3.8-27B NVFP4 (T=1.5) | Igor L. / NInfer contributors | native-logit | ✅ | 26.92 | 51.5 | 76.0 | 80.1 | 35.2 | 83.1 | 33.1 | 0.886 | 0.1449 | [↗](https://github.com/igorls/ninfer) |
| 50 | NInfer Qwen3.8-27B NVFP4 | Igor L. / NInfer contributors | native-logit | ✅ | 26.3 | 51.5 | 67.2 | 80.1 | 35.2 | 83.1 | 33.1 | 0.886 | 0.1449 | [↗](https://github.com/igorls/ninfer) |
| 51 | kev 8B (research preview) | Jared Palmer | jev-rebuild | ✅ | 25.56 | 41.8 | 40.2 | 74.9 | 44.0 | 71.4 | 21.8 | 1.331 | 0.0733 | [↗](https://github.com/jaredpalmer/kev) |
| 52 | JevOne | Juspay | jev-rebuild | ✅ | 25.51 | 47.6 | 77.6 | 88.5 | 35.9 | 89.6 | 33.8 | 0.323 | 0.1373 | [↗](https://huggingface.co/juspay/jev-one) |
| 53 | typecastlm (Mikhail Gribov, Qwen3.5-4B computed head) | Mikhail Gribov | system-one-open | ✅ | 25.28 | 34.0 | 62.1 | 92.6 | 60.2 | 77.9 | 29.9 | 0.206 | 0.0213 | [↗](https://github.com/mihail-gribov/typecastlm) |
| 54 | SimpleJev Qwen3.6-35B-A3B | Featherless AI | jev-rebuild | ✅ | 24.86 | 45.7 | 59.8 | 75.0 | 38.1 | 81.4 | 28.2 | 1.704 | 0.1156 | [↗](https://github.com/featherless-ai/simple-jev) |
| 55 | kev 0.6B (research preview) | Jared Palmer | jev-rebuild | ✅ | 24.75 | 34.2 | 50.0 | 75.6 | 76.1 | 66.7 | 24.0 | 1.331 | 0.0063 | [↗](https://github.com/jaredpalmer/kev) |
| 56 | Raw Qwen3 8B direct logits | Alibaba Qwen / neutral reproduction | raw-logit-control | ✅ | 23.68 | 45.7 | 24.1 | 86.3 | 41.9 | 68.4 | 26.3 | 0.32 | 0.0866 | [↗](https://huggingface.co/Qwen/Qwen3-8B) |
| 57 | system-one (Qwen3-8B, Sean Goedecke) | Sean Goedecke | jev-rebuild | ✅ | 23.37 | 43.6 | 32.8 | 84.4 | 41.5 | 71.9 | 24.4 | 0.482 | 0.0894 | [↗](https://github.com/sgoedecke/system-one) |
| 58 | OpenDecision (ModernBERT-large zero-shot) | Deepan Wadhwa | classifier | ✅ | 21.64 | 31.8 | 57.1 | 79.9 | 75.3 | 53.2 | 25.6 | 0.826 | 0.0066 | [↗](https://github.com/deepanwadhwa/OpenDecision) |
| 59 | LitJev (Qwen3.8-27B) | Zhengxu Yu | jev-rebuild | ✅ | 19.51 | 46.3 | 76.6 | 66.7 | 33.6 | 86.1 | 30.8 | 4.2 | 0.163 | [↗](https://github.com/zhengxuyu/litjev) |
| 60 | openJev Verdict 1.4 | Hemant (heman10x) | jev-rebuild | ✅ | 19.0 | 29.4 | 72.0 | 78.1 | 82.4 | 57.6 | 27.9 | 0.777 | 0.0039 | [↗](https://huggingface.co/heman10x/rlcd-modernbert-151m) |
| 61 | kev 0.5B | Jared Palmer | jev-rebuild | ✅ | 18.88 | 30.5 | 49.7 | 77.0 | 76.1 | 49.4 | 27.3 | 1.011 | 0.0063 | [↗](https://github.com/jaredpalmer/kev) |
| 62 | Bespoke Nimble 9B (Bespoke Labs) | Bespoke Labs | jev-rebuild | ✅ | 18.66 | 46.3 | 56.4 | 78.7 | 33.4 | 79.7 | 28.9 | 0.928 | 0.1658 | [↗](https://github.com/bespokelabsai/nimble) |
| 63 | GPT-5.6 Luna (low reasoning effort) | OpenAI | llm-baseline | ❌ | 18.51 | 93.1 | 87.4 | 77.5 | 28.5 | 97.4 | 89.0 | 0.968 | 0.2419 |  |
| 64 | openJev Verdict (heman10x, ModernBERT-base 151M) | Hemant (heman10x) | jev-rebuild | ✅ | 18.09 | 30.0 | 47.0 | 76.7 | 83.1 | 55.4 | 24.7 | 0.706 | 0.0037 | [↗](https://github.com/Heman10x-NGU/openJev-verdict-2.0) |
| 65 | Raw Qwen3 1.7B direct logits | Alibaba Qwen / neutral reproduction | raw-logit-control | ✅ | 18.06 | 33.2 | 24.3 | 89.7 | 64.9 | 54.1 | 26.0 | 0.283 | 0.0148 | [↗](https://huggingface.co/Qwen/Qwen3-1.7B) |
| 66 | reflex-27b (Qwen3.8-27B) | kshetrajna12 | jev-rebuild | ✅ | 17.84 | 46.4 | 77.2 | 67.5 | 32.3 | 87.0 | 29.5 | 3.926 | 0.1811 | [↗](https://github.com/kshetrajna12/reflex) |
| 67 | JevAct (einptein, jev1-2b-v2) | einptein | jev-rebuild | ❌ | 16.93 | 29.3 | 55.1 | 76.5 | 64.3 | 61.9 | 23.4 | 0.799 | 0.0155 | [↗](https://github.com/fstandhartinger/jevbench/issues/66) |
| 68 | djev (thinking) | David Villalon / Maisa | jev-rebuild | ✅ | 15.2 | 71.6 | 87.8 | 75.2 | 26.9 | 87.4 | 60.1 | 1.002 | 0.2743 | [↗](https://github.com/Davipar/djev-dev) |
| 69 | GLiNER2 large (Fastino) | Fastino | classifier | ✅ | 15.14 | 31.1 | 24.8 | 61.7 | 73.3 | 56.7 | 28.6 | 2.343 | 0.0077 | [↗](https://huggingface.co/fastino/gliner2-large-v1) |
| 70 | OpenJev (thinking, BF16) | razorback16 | jev-rebuild | ✅ | 14.83 | 58.1 | 58.1 | 76.1 | 27.8 | 88.7 | 42.2 | 1.076 | 0.2546 | [↗](https://github.com/razorback16/openjev) |
| 71 | Qwen3.5-0.8B Decision Model (Mourad Ghafiri) | Mourad Ghafiri | jev-rebuild | ✅ | 14.54 | 28.1 | 68.2 | 49.2 | 75.7 | 59.3 | 34.7 | 14.45 | 0.0065 | [↗](https://huggingface.co/mghafiri/qwen3.5-0.8B-decision-model) |
| 72 | Gemini 3.1 Flash-Lite | Google | llm-baseline | ❌ | 14.26 | 54.5 | 59.3 | 81.8 | 27.4 | 87.0 | 38.6 | 0.756 | 0.2638 |  |
| 73 | open-jev-deberta-v3-large (local CPU) | Kotoba Labs | jev-rebuild | ✅ | 12.65 | 25.6 | 66.6 | 66.0 | 74.0 | 52.4 | 29.5 | 3.685 | 0.0073 | [↗](https://github.com/kotoba-lang/typed-decisions) |
| 74 | smalljev semantic-v9 | Aditya (isHeSatoshi) | jev-rebuild | ✅ | 12.31 | 25.7 | 59.2 | 79.8 | 57.9 | 60.6 | 26.9 | 0.978 | 0.0254 | [↗](https://github.com/isHeSatoshi/smalljev) |
| 75 | GLiNER2 (Fastino, gliner2.5-base) | Fastino | classifier | ✅ | 11.78 | 27.4 | 25.2 | 71.8 | 83.1 | 58.0 | 29.2 | 0.776 | 0.0037 | [↗](https://github.com/fastino-ai/GLiNER2) |
| 76 | Instinct (ZooWork, Qwen3.8-27B) | rayrain-srp (ZooWork) | jev-rebuild | ❌ | 11.45 | 51.1 | 78.7 | 83.9 | 24.6 | 86.6 | 35.1 | 0.517 | 0.3253 | [↗](https://github.com/fstandhartinger/jevbench/issues/69) |
| 77 | Open-Jev 9B (Zefan Cai) | Zefan Cai (@Zefan_Cai) | jev-rebuild | ✅ | 11.2 | 44.2 | 61.8 | 72.0 | 28.1 | 77.5 | 29.9 | 1.66 | 0.2488 | [↗](https://github.com/Zefan-Cai/Open-Jev) |
| 78 | Open-Jev 2B (Zefan Cai) | Zefan Cai (@Zefan_Cai) | jev-rebuild | ✅ | 9.98 | 42.3 | 55.3 | 73.5 | 28.1 | 64.5 | 26.3 | 1.479 | 0.2488 | [↗](https://github.com/Zefan-Cai/Open-Jev) |
| 79 | GLiNER2.5 multi (Fastino, 287M) | Fastino | classifier | ✅ | 9.76 | 23.1 | 57.2 | 67.8 | 82.4 | 48.9 | 32.8 | 1.006 | 0.0039 | [↗](https://huggingface.co/fastino/gliner2.5-multi-v1) |
| 80 | CLM-8B (Contrastive-LM, clm-latest) | Contrastive-LM (Kwok, Kang, Suresh, Saad-Falcon, Pavone, Ré, Mirhoseini) | system-one-open | ✅ | 8.57 | 22.4 | 39.8 | 93.6 | 78.4 | 40.7 | 24.0 | 0.184 | 0.0052 | [↗](https://github.com/Contrastive-LM/CLM) |
| 81 | SimpleJev (Qwen3.5-0.8B, CPU) | sabeel111 / Featherless AI | jev-rebuild | ✅ | 7.46 | 21.5 | 49.1 | 57.5 | 68.3 | 54.5 | 34.7 | 8.138 | 0.0114 | [↗](https://github.com/featherless-ai/simple-jev) |
| 82 | GLiNER2.5 small (Fastino, 74M) | Fastino | classifier | ✅ | 7.19 | 20.5 | 50.7 | 77.8 | 82.4 | 45.9 | 28.6 | 0.378 | 0.0039 | [↗](https://huggingface.co/fastino/gliner2.5-small-v1) |
| 83 | Raw Qwen3 0.6B direct logits | Alibaba Qwen / neutral reproduction | raw-logit-control | ✅ | 7.14 | 22.8 | 20.7 | 89.9 | 73.9 | 48.1 | 25.6 | 0.286 | 0.0074 | [↗](https://huggingface.co/Qwen/Qwen3-0.6B) |
| 84 | verdict-small (Manavarya09, multilingual-e5-small 118M) | Manavarya09 (Manav) | jev-rebuild | ✅ | 5.69 | 18.1 | 66.9 | 85.0 | 96.6 | 53.7 | 28.9 | 0.257 | 0.0013 | [↗](https://github.com/Manavarya09/verdict) |
| 85 | DeepSeek V4.1 Flash (thinking default) | DeepSeek | llm-baseline | ⚠️ | 4.77 | 94.0 | 95.5 | 71.6 | 16.8 | 97.8 | 94.8 | 1.416 | 0.5937 |  |
| 86 | Mirror | Bluusun | jev-rebuild | ✅ | 2.11 | 13.6 | 26.0 | 70.8 | 73.3 | 41.1 | 9.1 | 1.799 | 0.0077 | [↗](https://github.com/Bluusun/Decision-API) |
| 87 | Mixedbread mxbai-rerank-base-v2 | Mixedbread | reranker | ✅ | 0.4 | 6.8 | 84.1 | 87.5 | 67.9 | 37.2 | 34.4 | 0.288 | 0.0117 | [↗](https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v2) |
| 88 | BAAI bge-reranker-v2-m3 | BAAI | reranker | ✅ | 0.17 | 5.0 | 84.2 | 89.5 | 73.4 | 39.4 | 27.9 | 0.219 | 0.0077 | [↗](https://huggingface.co/BAAI/bge-reranker-v2-m3) |
| 89 | Alibaba GTE Reranker ModernBERT-base | Alibaba-NLP | reranker | ✅ | 0.15 | 4.8 | 78.9 | 90.6 | 69.6 | 33.8 | 33.4 | 0.246 | 0.0103 | [↗](https://huggingface.co/Alibaba-NLP/gte-reranker-modernbert-base) |
| 90 | Certo v1 (AltSlate Labs) | AltSlate Labs | jev-rebuild | ✅ | 0.0 | 0.1 | 83.0 | 94.0 | 100.0 | 31.6 | 29.5 | 0.188 | 0.001 | [↗](https://huggingface.co/altslate/certo-decision-model) |
| 91 | Open Jev JSON Canvas (JoshuaSP) | JoshuaSP | jev-rebuild | ✅ | 0 | 48.2 | 0 | 84.1 | 45.6 | 84.4 | 31.2 | 0.599 | 0.065 | [↗](https://github.com/JoshuaSP/open-jev) |
| — | classifier.dev (fast tier) | mrmps (@michael_chomsky) | jev-service | ❌ | 70.82 | 51.6 | 72.4 | 87.6 | 84.3 | 85.3 | 34.4 | 0.386 | 0.0033 | [↗](https://classifier.dev) |
| — | Qwen3.8 27B (Chutes TEE) | Qwen / Chutes | llm-baseline | ⚠️ | 0 | 40.4 | 93.6 | 61.3 | 0 | 71.9 | 21.8 | 5.754 | 2.6691 |  |
| — | Needle 3, options as tools (post-hoc adapter mode) | Cactus Compute | small-tool-model | ✅ | 0 | 0 | 0 | 0 | 0 | 22.1 | 0 | 7.708 | 0.0144 | [↗](https://github.com/cactus-compute/needle) |
| — | Needle 3 (Cactus, 2-bit, local CPU) | Cactus Compute | small-tool-model | ✅ | 0 | 0 | 0 | 0 | 0 | 22.5 | 0 | 3.524 | 0.0238 | [↗](https://github.com/cactus-compute/needle) |

## 附录 B：主要信息来源

| 来源 | 性质 | 用途 |
|---|---|---|
| `github.com/fstandhartinger/jevbench` | 第三方独立基准（MIT harness） | 本报告主数据源，v1.4.2.2 结果 JSON |
| `benchmarkheaven.com/jev-models` | Benchmark Heaven 榜单站 | 交叉核对 |
| `Hanno-Labs/DecisionBench` | 第三方基准（43 任务 / 23,900 行） | 交叉验证 |
| ImageJevBench v0.1.3 | 第三方图像决策基准 | 多模态验证 |
| `BeatAPI/awesome-jev` | 228 项目精选清单（50+ star，源码评审） | 生态规模 |
| `multimodalart/jev-decision-index` (HF) | 60+ 权重条目追踪 | 补充清单 |
| TypeSafe 官方文档 / OpenRouter / Vercel / LangChain | 厂商与集成方 | Jev 本体规格 |
| Milvus / Zilliz 实测、xyspace 实测、HN 讨论、中文社区实测 | 独立第三方实测 | 负面与中性证据 |
| 新华网 / 科技日报 / 央广网 | 国内媒体报道 | APUS、Intern-Decision 等国内项目 |

**声明**：本报告中所有分数均标注了来源与可信度层级。凡标注"厂商自报"的数字（如 Intern-Decision 的 90.02 均分）**未经第三方复现**，请以谨慎态度引用。JevBench 榜单每日变动，引用时请注明版本号与评分日期。
