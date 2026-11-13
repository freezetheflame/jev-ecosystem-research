# 可获取性与许可证：能下载 ≠ 能拿到 ≠ 能用

整理自 2026-10-02 的核查。起因是 Cygnet 这个项目——它公开可访问，但你拿到的和"开源模型"通常不是一回事。

---

## 一、Cygnet 本身

`github.com/blockbrain-ai/cygnet-recipe`，公开、MIT、25 star。

但它是**冻结 Gemma-4-12B-it + 一个推理时 shim**：把选项渲染成字母 A/B/C，读模型对每个字母的 logit 概率，再套一个标定温度。**一个权重都不训，也不发。**

所以你拿到的是**配方**，不是模型。要跑起来得自己先有 Gemma-4-12B-it，而那个受 Google Gemma 条款约束（需单独同意，不是标准开源许可证）。门槛倒是很低：11.96B dense、16K ctx、stock vLLM 直接跑、50 ms、4-bit 约 9 GB 显存，一张 RTX 3060 12G 就够。

### 这不是孤例：零微调流派共 9 个

走"冻结基座 + 推理时读出"路线的：Cygnet、SemIf/OpenJev、Jobe、jqv、open-alternative-jev、jev-local、system-one、LitJev、reflex-27b。

它们的**可获取性其实最高**——只要有基座就能复现，不用训练。

---

## 二、链接基本都是活的（实测）

抽检 JevBench 前 30 名的 GitHub 仓库，**全部 200，无一 404 或归档**。

95 个系统中 88 个有链接：GitHub 57 / HuggingFace 28 / 厂商站 3。只有 7 个没链接，基本都是商业 API（Jev 本体、GPT-6 Luna、Gemini Flash-Lite 等）。

但 star 两极分化得厉害：kev 4B 8238、SemIf 4656、decider-4b 1031，而大量项目是 0–10 star（Jobe 2、swanOne 0、jqv 0）。

> **能拿到 ≠ 有人维护。**

---

## 三、三档获取形态

| 你实际能拿到什么 | 大致数量 | 说明 |
|---|---:|---|
| 完整权重，可直接 download | ~28（HF 直链那批） | 如 Imajev-4B、decider-4b、Winnow-12B |
| 只有配方 / shim / LoRA，需自备基座 | ~9 个零微调 + 部分微调制品 | Cygnet 这一档 |
| 只有 endpoint + 评测客户端 | 2 | JevAct、Instinct——repo 链接指向 jevbench 的 issue，等于没开源 |
| 代码有 LICENSE，**权重另算条款** | 绝大多数 | 代码 Apache/MIT，权重走 Gemma / Qwen / LFM 条款 |

---

## 四、三个具体陷阱

### 1. 仓库 LICENSE 和权重条款不一致

**Malkuth-4B/2B** 在 GitHub 上标 Apache-2.0，但 JevBench 记录的实际权重条款是 **CC-BY-NC-4.0、仅限研究**（因为训练混了 XNLI 和 RACE）。

看顶层 LICENSE 会踩雷。**榜单的 `licence` 字段写得比仓库本身诚实，以它为准。**

### 2. 仓库压根没有 LICENSE 文件

法律上等于保留所有权利，不能算开源：**openjev-sglang、system-one、Bespoke Nimble 9B、jev-local、SimpleJev**。

### 3. 权重仅评估用途

FlyMy.AI 的 **Decision 2B / Decision Fast**：代码是 Apache，但权重明确 evaluation-only。

---

## 五、验收顺序

真要落地，按这个顺序查：

1. 有没有 LICENSE 文件
2. 权重的条款是否和代码分离（Gemma / Qwen / LFM 条款需单独同意）
3. 是不是 evaluation-only
4. 基座是哪个、要不要单独同意条款

---

## 六、Cygnet 类复现的额外意义（研究向）

见 `06-security-research-agenda.md` §5：这类"冻结基座 + 读字母 logit"的复现**把读出机制完全暴露**——A/B/C 字母 logit + 标定温度。你可以直接对 letter readout 求梯度，这大概率就是闭源 Jev 内部在做的事，是个**异常强的白盒 surrogate**，而 R2A（ACL 2026）自述的最大局限恰恰是缺少这种代理。
