# H2O-Lightning-4B v1.1：本地检查与试跑

2026-10-09：已下载并在 RTX 4070 SUPER 12 GB / WSL Ubuntu 上跑通原始 BF16 权重。没有量化；推理使用 Transformers 后端与官方 v1.1 shim 的提示和概率读出函数，尚未复现官方 vLLM 服务。

## 版本区别

用户指定的 v1.1 是文本决策模型，基于 Qwen/Qwen3.5-4B，Apache-2.0，支持 choice、noul、score。当前主页已经介绍后续多模态版本，不能把其中的图像能力算到 v1.1 上。

- 官方 tag：`v1.1`，对应 commit `193ad740925b176a3b70a5a13a7cff2f2fadd01e`。
- 完整权重：8,411,558,400 字节，SHA-256 `c65443b1d28891ffc4b6f7d90028c542d6ccb24c2f9cd6a46a8294a44ab0ffae`，已校验。
- 本地路径：`local-models/weights/h2o-lightning-4b-v1.1`；推理代码、配置、tokenizer 与权重均按 v1.1 下载。
- 下载使用 hf-mirror，curl 关闭显式代理并通过真实 IP 绕过本地 Fake-IP DNS；没有修改全局代理或 DNS。

v1.1 模型卡报告在 H100 80 GB 上运行官方 JevBench CLI 的公开集：205/231（88.7%），easy 48/48、standard 71/72、hard 86/111，串行全体题目 p50 33 ms。**这是厂商运行评测工具得到的报告，本机没有复现该评测。** 当前主页的综合排名对应 JevBench v1.6.1，也不能与本仓库 v1.4.2.2 榜单分数直接比较。

## 本机结果

环境沿用 `07-local-model-smoke-test.md`：PyTorch 2.11.0+cu130、Transformers 5.17.0、fla-core 0.5.2。每例运行 4 次，首遍单列，后 3 遍取中位数。

| 样例 | 判断 | 预热后中位延迟 |
|---|---|---:|
| 英文重复扣款分类 | billing，概率 0.933 | 83.7 ms |
| 包裹投错门牌 | misdelivered，概率 0.938 | 78.1 ms |
| 退款要求收据，客户没有收据 | 不允许；P(允许)=0.0767 | 90.6 ms |
| 中文重复扣款分类 | 账单与退款，概率 0.952 | 84.5 ms |
| 完全停机的严重程度 | 最高等级，概率 0.939 | 85.8 ms |

加载耗时 70.5 秒，首例第一次推理 1.11 秒，PyTorch 显存分配峰值 7.86 GiB。其他模型的内核缓存已经存在，不能拿首次推理耗时与此前冷启动直接比较。显存统计不含桌面和驱动。

五个简单样例都符合预期，仅说明本机可以运行，不代表准确率、泛化能力或正式榜单排名。各模型提示格式、输入 token 数不同，延迟仅作本地体验参考。未验证图像、长上下文、并发或 HTTP 服务。

## 推理方式与官方方式的差异

官方 v1.1 要求 stock vLLM 0.30.0 + 标准库 shim，配置 `head_dtype=float32`，默认服务上下文 40960。现有本机 vLLM 为 0.22.1。本次没有下载另一套大型 CUDA / vLLM 依赖，而是用已有 Transformers 环境完成本地验证：

- 直接调用官方 `Contract.question_prompt()`、`render_state()`、`format_answer()`。
- 验证全部 255 个 label 在官方答案槽位处各追加一个独立 token，使用这些 token 的真实 ID。
- BF16 主干运行一次前向，再将最后隐状态和选项对应输出权重转为 fp32，计算选项 logits；无需生成文本或分配全词表 logits。
- 保留官方温度 0.8 和 yes/no floor 0.801。
- 原始 logits 与全词表 log-probabilities 相差同一个归一化常数，选项内 softmax 对该常数不变；但不同推理后端、内核与数值仍可能产生差异，不声称与 vLLM 完全等价。

官方 `test_shim.py` 的 10 项无 GPU 测试全部通过。必须取消本地请求的代理或设置 `NO_PROXY=localhost,127.0.0.1`，否则测试请求会被显式 HTTP 代理转发并返回 502。

## 概率研究要注意的变换

`noul_floor=0.801` 会把不够确定的 yes/no 概率提交到其原本判断的一侧，例如 0.55 → 0.801，0.45 → 0.199；它保留 argmax，但改变概率值。用于校准、阈值或漂移研究时，应另外查看原始概率。

本地测试输出同时保存 `noul` 和 `raw_noul_before_floor`。本次退款样例原始值已经低于 0.199，所以未被改变。

## 重跑

在仓库根目录：

```powershell
.\scripts\test-local-model.ps1 -Model h2o
```

该命令采用上述 Transformers 路径，读取本地权重，结果写到 `local-models/results-h2o.json`。首次结果快照在 `data/h2o-local-smoke-2026-10-09.json`。

官方资料：[v1.1 模型卡](https://huggingface.co/h2oai/h2o-lightning-4b/blob/v1.1/README.md)、[v1.1 推理配置](https://huggingface.co/h2oai/h2o-lightning-4b/blob/v1.1/serve_config.json)。
