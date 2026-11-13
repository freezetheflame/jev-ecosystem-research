# Jev-Guard 的 AgentHarm 输入检查适配

2026-11-03。状态：制品来源与离线适配已核验，基座下载中；尚未执行本轮模型推理。

此前未找到可核验制品的记录属于当时检索结论。本次找到作者关联发布 `hubin/jev-guard-v3.2-2b`，固定 revision `70aa1f3e0fc88c98afd88bca830b45b0a772e800`。原生代码、LoRA、分类头和 notice 已下载并记录 SHA-256。原发布未固定基座 commit；本轮选择并记录 `Qwen/Qwen3.5-2B` revision `15852e8c16360a2fea060d615a32b45270f8a8fc`。不得声称复现了未公开的基座版本。

该发布提供 `JevClassifier.predict`，本轮使用 safety-only：`options=[]`、`mode=single`、`safety_applicable=true`。请求 input 是沿用的安全策略与 AgentHarm 原始 user_request。判定只读取原生 `safety` 字段，safe=0、unsafe=1；缺失、未知或截断响应记失败。没有使用类别选择充当安全结论，也没有运行完整策略树路由或 Hermes gate。

计划使用既有 Jev pilot 的相同 50 条 validation 输入，harmful/benign 各 25，8 个 family，3 次重复。另开 2 条接口 smoke。属于已暴露开发 pilot，不是确认性测试或官方有害任务执行评分。

运行准备入口：`scripts/prepare_remaining_agentharm.py --model jevguard --port 8027 --out data/agent-security-study/preparations/2026-11-03-agentharm-jevguard`。服务由 `scripts/local_jevguard_server.py` 薄封装原生分类器。没有自动预热，没有生成 token；BF16 backbone、FP32 native heads、未合并 LoRA。共享环境 torch 2.11.0、transformers 5.17.0、peft 0.21.0 与发布 requirements 不同，须保留实际环境，不声明参考运行时数值一致性。

原 monitor 保持不变，由客户端每次调用记录一次。原始请求、响应、失败、monitor、有效配置和必备报告由统一 runner 存入独立 run；加载时间单列，本地计算未计价。

汇总代码 `scripts/consolidate_agentharm_models.py` 只读已有逐条预测，不重新判读旧输出。缺失和平票保持未决，分别给出覆盖、全 50 项准确率界限和共同可判子集。不同机器/API 通道的时间不能作为受控模型速度排名。

## 本机执行完成（2026-11-03）

本节更新上方准备状态。基座和发布包已完整校验并真实运行。两条 smoke 均成功，首次调用16.438秒、第二次0.078秒；随后50项×3次 pilot 全部成功。多数票 TP25/FP5/TN20/FN0，accuracy90%、F1约0.9091，所有有害输入被识别，有5项无害误报。pilot HTTP episode p50=0.078秒、p95=0.125秒，累计13.591秒；输入17976 token、生成输出0，usage覆盖150/150。本地计算未计价，无本次API调用。

仍为原生 safety-only 判断，不是完整策略树路由。实际环境 torch2.11.0+cu130、transformers5.17.0、peft0.21.0；BF16基座/FP32 heads、未合并LoRA、SDPA，matmul TF32=false、cuDNN TF32=true。运行时缺少causal_conv1d优化内核，按 transformers 提示使用参考PyTorch实现；不为本轮测试临时更换内核。加载24.435秒独立于episode；smoke首调用初始化单列。不能把本机延迟当作所有部署环境的速度。

完整必备报告、raw、telemetry、配置和样本IDs/hash分别在 `data/agent-security-study/runs/2026-11-03-agentharm-jevguard-{smoke,50}/`；原生源码与权重来源、服务快照和rerun入口见 `data/agent-security-study/preparations/2026-11-03-agentharm-jevguard/deployment.json`。共享环境锁和原始服务日志在 `data/agent-security-study/preparations/2026-11-03-local-services/`。公开validation已暴露，仍为pilot，不是确认性结论。没有更改之前任何模型的预测。
