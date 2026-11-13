# Kev-4B：AgentHarm 输入检查 pilot

2026-11-04。类型：已授权的新模型开发pilot。当前为下载/准备状态，尚未执行真实推理。

用户要求加入 Kev 4B。采用作者发布 `jaredpalmer/kev-4b`，固定 revision `6cfce5c2fa4b4bd64026336ab649c5ca78857d52`；基座为 `Qwen/Qwen3.5-4B-Base` revision `1001bb4d826a52d1f399e183466143f4da7b741b`。这与已测的 Qwen3.5-4B、SecJev-0.8B 都是不同模型。原生 Kev 代码固定至 `2074cc44256200bb37540103fa4572901faa10f3`，以源码只读副本调用 Checkpoint、SystemOneRequest、to_record、encode、forward 和 to_answers；不修改第三方权重、head或原 monitor。

## 本轮方案

- 沿用 Jev 主实验的50条 AgentHarm validation：harmful/benign各25，8个family，每项3次，同 seed=20261030，串行，无重试、无客户端缓存、无截断；另开2条smoke。
- 请求与 Jev/D3-Mini/SecJev 的 state/questions.risk choice 相同，仅 model 标识改为 kev-4b-local。state 为原状态JSON字符串；策略、safe/unsafe准则和顺序不变，不输入gold。
- 输出使用官方to_answers的原生choice，safe=0、unsafe=1；未知输出记失败，不回退到默认safe。
- 本机RTX4070 SUPER 12GB：BF16基座、FP32 pointer head、未合并LoRA，torch后端、SDPA、TF32关闭、cuda_graphs=false、fused=false，无跨请求prefix缓存，无date_facts额外预处理。context上限8192且严格拒绝溢出；本轮短输入全保留。
- 保留 checkpoint 的temperature=2.406050072164233，不重新拟合。本地内存限制下采用BF16未合并路径，区别于作者FP32评测及其优化部署，不声明参考指标数值复现。共享环境torch2.11.0+cu130、transformers5.17.0、peft0.21.0，torch版本超出发布声明<2.9范围；接口检查通过后才发起完整pilot。
- 使用 scripts/local_kev_server.py 提供薄HTTP封装；客户端统一runner复用原monitor且每次调用只计一次。使用prompt内部实际编码state+branch ids长度记录输入token；输出0为非生成式决策，计算费用未计价。

## 证据与复现

制品/代码在 local-models/nov04/kev4b/；下载日志在 data/agent-security-study/preparations/2026-11-04-kev-services/。基座各分片用固定官方LFS SHA256校验；adapter/head同样验证。模型加载、smoke首调用初始化和pilot分别记录，禁止把smoke混入150次pilot。

服务启动：`wsl -d Ubuntu -- env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false /home/hectum/.cache/jev-research-env/bin/python -u /mnt/d/projects/jev_research/scripts/local_kev_server.py --model-path /mnt/d/projects/jev_research/local-models/nov04/kev4b --base-path /mnt/d/projects/jev_research/local-models/nov04/kev4b/base --kev-source /mnt/d/projects/jev_research/local-models/nov04/kev4b/source --port 8028`。

准备入口：`python scripts/prepare_remaining_agentharm.py --model kev --port 8028 --out data/agent-security-study/preparations/2026-11-04-agentharm-kev`。随后分别用生成的smoke/pilot-config经 `python -m security_bench run` 写入独立新run目录。正式发出前核对effective配置与样本hash。报告严格区分接口smoke、公开已暴露validation pilot和确认性研究；本轮不运行主Agent或官方AgentHarm有害任务执行评分。

## 执行完成

本节更新上方准备状态。真实跑完2条smoke+50×3 pilot，152次均成功。pilot三次预测全部一致且150次均正确，50项多数票TP25/FP0/TN25/FN0，accuracy、precision、recall、F1均为1.0；有效覆盖50/50。pilot单次HTTP episode p50=0.157秒、p95=0.328秒，累计27.615秒；输入21261 token、输出0，usage覆盖150/150。本地计算未计价，无API推理调用。独立smoke耗时2.453秒与0.109秒，模型加载52.654秒，均不混入pilot耗时。

已核对：150次请求body除model字段外与原Jev pilot的多重集合完全一致；返回choice均与原概率argmax相同，无截断，原monitor hash不变，原11模型汇总字段未改变。离线58项测试通过。没有据本轮结果更改模型、问题、选项、温度或样本。

实际使用SDPA、BF16未合并LoRA、原生FP32 head、temperature=2.406050072164233。缺少causal_conv1d优化库，日志显示使用参考PyTorch卷积回退；未在测试中途更换内核。CUDA graphs和fused projections关闭，无跨请求prefix缓存。该路径与作者FP32评测/优化部署有差异；不声明数值或速度复现官方结果。

这只是公开、已暴露的50项开发pilot（8个family）；预训练/微调数据与这些公开样本是否重叠尚未核验。100%不能外推为全AgentHarm或未见数据的准确率。

完整原始请求/响应、telemetry、effective-config、环境和必备报告：`data/agent-security-study/runs/2026-11-04-agentharm-kev-{smoke,50}/`。部署/配置/服务源码快照：`data/agent-security-study/preparations/2026-11-04-agentharm-kev/`；软件锁和原始启动/下载日志：`data/agent-security-study/preparations/2026-11-04-kev-services/`。最新12模型汇总：`data/workspace-evidence/2026-11-04-experiment-summary-v7/`，包含参数量、统一50项主分母、token覆盖、时间和费用。
