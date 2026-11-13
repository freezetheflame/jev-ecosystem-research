# 五数据集全集入口准备记录

类型：工程实现与离线预检。没有本轮真实模型请求，没有付费 API。

操作入口与范围：[全集实验操作手册](../../../docs/infrastructure/full-benchmark-operations.md)。机器部署仍见原本地模型手册。

`readiness.json` 由 `scripts/audit_full_suite.py` 从本机原始数据、获取 manifest、版本化模型配置和请求构造器生成，记录实际行数、split、标签数量、ID hash、源码 hash 和每模型预检问题；不是实验分数。WildGuardTest 明确列为 not_ready：用户选择等待作者原库授权，未用镜像替代。

验证命令：

```powershell
.venv-benchmark/Scripts/python.exe -m unittest discover -s security_bench/tests -q
.venv-benchmark/Scripts/python.exe scripts/audit_full_suite.py --out <新的输出路径.json>
```

本次测试为 62 项通过，包括新加的未知标签、未来信息隔离、首次告警停止、保留单条上下文错误遥测检查。单元 fixture 不是基准结果；真实长输入集成与完整矩阵尚未执行。

数据：`data/agent-security-study/datasets/full-suite-v1/`。StepShield 下载的初始含非运行所需上游代码的 manifest 保存在 `manifest-with-unused-upstream-code.json`；活动 manifest 只包含数据/说明/许可。运行器不执行上游 benchmark 脚本，原始轨迹与答案表均按哈希验证。
