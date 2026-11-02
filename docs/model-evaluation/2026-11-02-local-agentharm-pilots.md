# 剩余模型的本机 AgentHarm pilot

最新补充：已按原进度日志明确列出的 SecJev-0.8B 候选完成第四组。最终[四模型汇总](../../data/workspace-evidence/2026-11-02-local-agentharm-four-models/README.md)为当前结果；[最初三组包](../../data/workspace-evidence/2026-11-02-local-agentharm-pilots/README.md)保留，不覆盖。

SecJev 使用 [官方 v1.0.0 发布包](https://github.com/UESTC1010/SecJev/releases/tag/v1.0.0)（SHA256 `afb7e216edfbde4bfc19335312e4ae6577e98f29c915545ae2f7284e052e13dc`）、Qwen3.5-0.8B-Base 的 `dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68` 和 Kev `90990a5fac2995b9faa3190f7d437e84f2067768`。记录里的 `UESTC1010/SecJev-0.8B` 是本轮制品显示标签，实际源码仓库是 `UESTC1010/SecJev`，不是一个额外仓库。FP32、未合并 LoRA、原 decision head 和温度 1.3525612043415394；禁用 TF32、flash SDP 和 memory-efficient SDP，未另行测量实际 SDPA 内核选择（元数据 `sdpa_math` 为简写，不是内核测量结论）。PyTorch 2.11.0+cu130 与官方 requirements 2.6.0 不同，记录了此差异，不声称参考运行时数值等价。首次 8016 端口占用的加载日志和会话切换后的服务重启日志保留；这些阶段没有 benchmark 推理请求。

最终四组均 150/150 成功，另有 8 次独立 smoke；每组三次逐项预测均一致。SecJev 多数票 TP18/FP0/TN25/FN7，accuracy 0.86、F1 0.8372。当前留给 3090 的未完成名单仅 Jev-Guard，其制品/接口尚待核验。

日期：2026-11-02（Asia/Shanghai）。类型：真实本地推理 pilot。不是确认性实验，不是 AgentHarm 官方 Agent 有害任务完成率。

用户要求同步另一台机器已完成的实验，然后只在本机测试尚未完成且能运行的模型；沿用同样的 AgentHarm 数据，不复核或重跑已经完成的模型。其余留给 RTX 3090 工作站。

## 实际执行

从远端 main 同步到 `c4890e6`，保留本机原有文档及配置改动。用户提供的 `jev_experiment_reports_2026-11-01.zip` 原件复制到本地 preparations 导入目录，SHA256 为 `d2d6bb6003c9aab112b15562f9a134d17ce278422de06081305a0d001205257e`；导入 2,766 个 runs/preparations 文件，保持原字节，不执行压缩包中的代码、不替换已有不一致文件。按用户后续说明，没有继续复核旧实验。

本机实测硬件为 RTX 4070 SUPER 12GB、Ryzen 5 7500F、约 32GB RAM。使用已有 WSL Ubuntu 运行时：PyTorch 2.11.0+cu130、Transformers 5.17.0，模型逐个加载并在完成后停止服务。未量化；Qwen3.5 和 Shieldstral 为 BF16；D3 为官方 BF16 backbone + FP32 decision readout。

| 模型/检查点 | 固定 revision |
|---|---|
| Qwen/Qwen3.5-4B | `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` |
| vllm-sr/d3-mini | `df99bf4ca4418bc6908ee68e9b7479af1f3b8800` |
| mistralai/Shieldstral-1.0-3B | `003ec7e2b0bab5f0e6307edbaf186fa5822b76f5` |

权重下载按固定 revision 进行，分片和组装后核对官方 SHA256。D3 另用官方完整包校验；`--no-warmup` 禁止服务自动执行预热请求。HF 元数据、完整配置、文件哈希及运行时锁随[报告包](../../data/workspace-evidence/2026-11-02-local-agentharm-pilots/README.md)保存，权重留在本机 `local-models/nov02/`。

沿用 `2026-10-30-agentharm-pilot-50` 的 50 个 validation item，25 harmful / 25 benign、8 个基础任务族。只核对了用于复制实验条件的 item IDs 与输入哈希一致性，没有重新评判原有实验。每项重复 3 次，schedule_seed=20261030。各模型先用既有样本中的两条做接口 smoke，另开 run；然后执行 150 次 pilot 调用。

结果由版本化脚本生成：[完整统计与多数票](../../data/workspace-evidence/2026-11-02-local-agentharm-pilots/results.json)、[结果表](../../data/workspace-evidence/2026-11-02-local-agentharm-pilots/README.md)。三组 pilot 均 150/150 成功，另有 6 次成功 smoke；三次重复的逐项预测均一致。正类是有害请求 unsafe=1，safe=0。

## 推理契约与计时

- D3：官方 System One runtime，safe/unsafe choice；instructions 和 criteria 继承既有 Jev pilot。
- Qwen3.5：沿用既有 GPT/Claude pilot 的严格 JSON 判断问题；greedy、max_tokens=64、`enable_thinking=False`，只解析最终 `{"risk":boolean}`。
- Shieldstral：官方固定 system 和 Instruct/Query/Document 格式，单个 yes/no token，yes 表示 unsafe；max_tokens=1、temperature=0。此协议的 `length` 结束只在明确的一 token yes/no 输出时允许，其他模型的截断仍拒绝判分。没有将单 token 的固定决策错误记成 EOS 终止。

所有新调用仍通过原 monitor 一次计量，原 `monitor.py` 的实现、接口、SHA256 不变。450 次 pilot + 6 次 smoke 都是本地推理，没有本轮收费 API 请求；本地计算未计价。HTTP episode 时间包含请求和推理，模型加载不在其中；pilot 前的 smoke 起到预热作用。不能把另一台显卡上的耗时差直接归因于模型。

完整实际请求/响应、source、事件、monitor、失败/成功状态和六段自动报告分别保存在：

```text
data/agent-security-study/runs/2026-11-02-agentharm-{d3mini,shieldstral,qwen35}-smoke/
data/agent-security-study/runs/2026-11-02-agentharm-{d3mini,shieldstral,qwen35}-50/
```

所有 run 与 preparations 保持本地，不提交 raw 提示词。每次实际请求、完整有效模型设置和提示词可从其 effective-config.json / raw / deployment.json / manifest.json 追溯。报告包保存不含原始请求的派生材料。

## 复现与后续

下载程序 `scripts/fetch_remaining_local_models.py` 支持从报告包的 `checkpoints/` 读取固定 HF 元数据；服务和配置生成分别是 `scripts/local_remaining_server.py`、`scripts/prepare_remaining_agentharm.py`。D3 使用其固定 checkpoint 内的官方 d3_server.py。实际服务启动命令在各 preparations/deployment.json。

```powershell
python scripts/fetch_remaining_local_models.py --root local-models/nov02 --metadata-dir data/workspace-evidence/2026-11-02-local-agentharm-pilots/checkpoints
# 按 deployment.json 启动相应模型服务后，在新 preparations 目录生成配置。
python scripts/prepare_remaining_agentharm.py --model qwen35 --port 8015 --out data/agent-security-study/preparations/my-qwen35-repeat
python -m security_bench run --config data/agent-security-study/preparations/my-qwen35-repeat/pilot-config.json --run-dir data/agent-security-study/runs/my-qwen35-repeat
```

保留给 3090 的 [Jev-Guard 草案](../../configs/agentharm-3090-followup.template.json)沿用相同 50 项和三次重复；可核验制品和桥接接口仍待落实。草案会被 doctor 拒绝，不能误称为已完成部署或推理。SecJev-0.8B 的原生 HTTP 桥接为 `scripts/local_secjev_server.py`，命令和完整配置见其 preparations/deployment.json；本轮不再要求它到另一台机器重跑。

本批数据已用于开发且样本族少，多数票 N=50，150 次重复不是 150 个独立任务。派生 JSON 中 Wilson 区间未做 family 聚类校正，不据此作确认性或显著性结论。
