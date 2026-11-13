# vLLM-SR Decision 3.0：加入对比与后续试跑

记录日期：2026-10-13。**用户要求：将 vLLM-SR 的 decision model 加入我们的模型对比列表，之后试跑。** 状态：已核查公开资料并纳入待测；未下载权重、未部署、未推理。

## 模型与获取

当前新系列是 **Decision 3.0 / d3**，由 vLLM Semantic Router 团队发布。公开权重与推理代码，Apache-2.0；支持文本 / JSON、图片和视频，输出 choice、noul、score 类型的答案与概率，不生成自由文本。

| 模型 ID | 模型卡参数量（含视觉编码器） | 上游底座 | 本项目安排 |
|---|---:|---|---|
| [vllm-sr/d3](https://huggingface.co/vllm-sr/d3) | 26.09B | Qwen3.8-27B | 大模型对照，待具备相应算力 |
| [vllm-sr/d3-flash](https://huggingface.co/vllm-sr/d3-flash) | 8.39B | Qwen3.5-9B | 可选中间规模对照 |
| [vllm-sr/d3-mini](https://huggingface.co/vllm-sr/d3-mini) | 4.54B | Qwen3.5-4B | **优先本地试跑**，与现有 4B 模型配对 |
| [vllm-sr/d3-nano](https://huggingface.co/vllm-sr/d3-nano) | 2.21B | Qwen3.5-2B | 较小尺寸备选与资源对照 |
| [vllm-sr/d3-lite](https://huggingface.co/vllm-sr/d3-lite) | 0.85B | Qwen3.5-0.8B | 可选轻量对照 |
| [vllm-sr/d3-edge](https://huggingface.co/vllm-sr/d3-edge) | 0.59B | 从 d3-lite 剪枝，card base 为 Qwen3.5-0.8B | 可选更小尺寸对照 |

系列命名中的 27B / 9B / 4B 等与模型卡实际参数统计不同；比较时同时记录确切 checkpoint 和参数量。旧 Decision 1.0 / 2.0 是独立版本，本次优先试 3.0。[官方模型选择文档](https://vllm-sr.ai/docs/next/model-runtime/choose-a-model/)

## 榜单证据

本轮与已保存的 Decision Index 0.3.2 榜单 JSON 交叉核对：d3 Full **66.26**、Public **65.45**；d3-mini Full **52.61**、Public **54.90**。这些是公开榜单结果，不是本项目实测；Full 含私有测试，不能由公共 kit 独立复现。厂商在 AMD MI325X 上的速度数据也不能当成本机延迟。

数据见 [`models.json`](../../data/vllm-sr-decision-research-2026-10-13/models.json)，原始榜单见 [`data-index.json`](../../data/decision-index-research-2026-10-13/data-index.json)。榜单评估 d3 v3.1.0；本轮模型卡声明当前版本使用相同权重，但仍应固定下载 revision，避免后续推理代码变化。

## 接入路径与试跑计划

官方路径包含 Transformers `AutoModel(..., trust_remote_code=True).system_one(state=..., questions=...)`、模型包的 `d3_runtime.D3`、`d3_engine.D3Engine`，以及 vLLM Semantic Router Engine mode 的 `/v1/systemone`。多问题可在一次 API 调用中提交，源码按问题准备前向并可批处理，不能把“一次调用”理解为全部问题共用一次前向。

优先采用官方模型运行代码接入现有配对流程。Engine mode 当前在 dev channel，实际兼容性留待试跑核查，不因模型来自 vLLM-SR 就假设现有 stock vLLM 可以直接服务它。[模型卡](https://huggingface.co/vllm-sr/d3-mini)、[已保存的 engine 源码](../../data/vllm-sr-decision-research-2026-10-13/d3-mini-d3_engine.py)

后续执行顺序：

1. **版本与运行环境**：d3-mini 优先固定 `6d8971f464d6f9d4c5af7d9a8d75f3aa03be4f59`，包括推理代码、config、readout 与权重。沿用本地 WSL / RTX 4070 SUPER 12 GB 环境评估是否可运行；实际显存尚未测。先用短文本和小问题 batch；若资源不足，再试 d3-nano。
2. **接口 smoke**：复用现有英文分类、退款政策、中文、score 样例，确认 choice / noul / score 输出、概率和失败处理；区分冷启动与预热延迟。
3. **同题对比**：与 Jev、Plumb-4B、decider-4b、H2O-Lightning-4B 使用相同 UID、state、criteria 和 gold，按 MSB、MCPTox、AgentDojo 分别报告；延续已有 100 条配对 pilot 的口径。
4. **概率与鲁棒性**：记录正确率、置信度、覆盖率及选项轮换 / 等价改写的翻转。官方 `permutation_average` 默认为关闭，主对比先保留默认；若另开反序平均，作为单独变体记录其额外计算量。
5. **扩展对照**：本地 pilot 后，再按资源安排 d3 全尺寸和多模态任务。校准阈值与正式盲测另设数据，不在同一 pilot 上调参并宣称泛化提升。

## 固定来源

六款模型的完整 HF revision、基础模型、许可、来源文件哈希及榜单值保存在 [`models.json`](../../data/vllm-sr-decision-research-2026-10-13/models.json)。本轮只保存模型卡、metadata 及 d3-mini 的少量配置 / 推理源码，作为后续实验的起点；运行状态统一为 `planned_not_tested`。

关联：[模型评测对比列表](../model-evaluation/README.md)、[现有本机环境](../model-evaluation/local-model-smoke-test.md)、[Decision Index 转换参考](../model-evaluation/decision-index-construction.md)。
