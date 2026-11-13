# Plumb-4B 与 decider-4b 本地试跑

测试日期：2026-10-09。结论：两份原始 BF16 权重均可在本机的 WSL Ubuntu + RTX 4070 SUPER 上运行，不需要量化。

## 环境与版本

- Windows 主机：Ryzen 5 7500F（6 核 / 12 线程），32 GB 内存，RTX 4070 SUPER 12 GB。
- WSL Ubuntu：约 15 GB 可用总内存；NVIDIA 驱动 610.57.01，CUDA 驱动接口 13.3。
- Python 3.12.7；PyTorch 2.11.0+cu130；Transformers 5.17.0；Accelerate 1.15.0；flash-linear-attention / fla-core 0.5.2；Triton 3.6.0。
- 虚拟环境：`/home/hectum/.cache/jev-research-env`，复用已有 Anaconda 的 PyTorch，通过 system-site-packages 使用；新增组件安装在虚拟环境内。不是完全独立、可移植的环境。
- Plumb 的官方服务说明测试环境为 PyTorch 2.14 / CUDA 13。本次复用本机 PyTorch 2.11；实际前向运行成功。

| 模型 | 权重版本 / revision | 官方推理代码 |
|---|---|---|
| crh225/plumb-4b | v5，`55de037801a8a9b9de3db5c0e16cef86210c2186` | crh225/plumb，`fe73067682729221bc61aac1db6c1e08f2f7d7f8` |
| Mapika/decider-4b | v2.1，`eb5fbdfc9448473ec25e399882912863afbdb70e` | Mapika/decider，`e50e549b47e2da69223734fee4efa1ddd4528e93`（1.9.0） |

版本与本仓库旧 JevBench 榜单里的模型不完全相同，不能据此声称复现了旧榜单分数。

## 下载与完整性

权重保存在 `local-models/weights/plumb-4b` 和 `local-models/weights/decider-4b`；各自的 safetensors 文件为 8,411,558,400 字节。代码仓库在 `local-models/plumb` 和 `local-models/decider`。本机 `.git/info/exclude` 已排除整个 `local-models/`，权重不会进入 Git。

下载先经过 Hugging Face，后根据用户要求改走 hf-mirror。由于本机 DNS 返回代理的 Fake-IP，镜像下载通过 curl 的 `--resolve` 使用真实地址，且 `--noproxy '*'` 关闭显式代理。没有修改全局 DNS 或代理设置。下载脚本中的 IP 是当时的解析结果，未来重用需要重新解析。

最终完整文件均与镜像返回的 LFS SHA-256 匹配：

- Plumb：`89e119ea07f4c5b4b6715560c7de6694ec3b777dfd0e62351da0b33986d2e1e1`
- decider：`ee8ce585b3cedd93206dd149b09b4bdd683174874211f85c77a36090b90c9fdd`

## 实测

每例运行 4 次，第一遍单独记录，后 3 遍取中位数。单进程、单 GPU、batch 1，逐个加载模型，计时包含同步后的 Python 接口调用。测试为英文账单分类、错投包裹、退款政策判断、中文分类、故障严重程度，共 5 个简单样例。两模型均给出预期类别、拒绝无收据退款，并把完全停机评为最高严重程度。

| 模型 | 加载耗时 | 首例第一次推理 | 各例预热后中位延迟范围 | PyTorch 显存分配峰值 |
|---|---:|---:|---:|---:|
| Plumb-4B v5 | 102.9 秒 | 39.1 秒 | 70–111 ms | 8.11 GiB |
| decider-4b v2.1 | 68.3 秒 | 7.56 秒 | 66–97 ms | 8.20 GiB |

加载耗时受磁盘缓存影响，不适合用来比较模型。第一次推理包含内核准备/编译，常驻进程后续请求无需重复支付。显存数字是 `torch.cuda.max_memory_allocated()`，不含桌面、驱动及其他程序占用。

推理配置：

- Plumb 使用官方 `Plumb51` 的 one-read 路径、温度 2.07；不启用 v5.2 为 JevBench v1.5 提供的 noul-commit，也不启用 score-temperature 1.2，保留 v5 的原始校准概率。
- decider 使用官方 `Decider.system_one()`，显式 `use_graphs=False`。CUDA graphs / torch.compile 加速路径尚未验证。
- 未安装 causal_conv1d 加速扩展；框架使用 PyTorch 回退实现，实际可运行且短输入延迟已低于约 0.12 秒。
- 两模型的 `confidence` 定义不同，跨模型比较应查看 `probabilities` 或 decider 的 `x_p_max`。

这只是可运行性验证。没有测试长上下文、并发、HTTP 服务、正式基准或攻击样例；五个简单样例不能证明准确率或泛化能力。12 GB 卡在桌面占用存在时显存余量有限，建议一次只加载一份模型，先从短输入开始。

## 重跑

在当前仓库根目录执行：

```powershell
.\scripts\test-local-model.ps1 -Model plumb
.\scripts\test-local-model.ps1 -Model decider
```

脚本只读取本地权重，结果写入 `local-models/results-plumb.json` / `results-decider.json`。修改 `scripts/local_model_smoke.py` 中的 cases 可试自己的文本、选项和问题。

首次实测结果已保存到 `data/local-model-smoke-2026-10-09.json`。迁移机器时需调整 PowerShell 脚本中的 WSL 名称和 Python 路径，并重新搭建依赖。

官方说明：[Plumb](https://github.com/crh225/plumb)、[decider](https://github.com/Mapika/decider)。
