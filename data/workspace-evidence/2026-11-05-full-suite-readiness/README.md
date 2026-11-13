# 五数据集完整数据离线核验

日期：2026-11-05（Asia/Shanghai）。类型：获取与离线预检；不是实验结果。

WildGuardTest 已从作者 `allenai/wildguardmix` 固定 revision 下载完成。凭证仅从用户授权的本地 `.env.local` 读取到进程环境，未复制到产物。原始 parquet 与作者库 LFS SHA-256 相同，见 `wildguard-source-verification.json`。

`readiness.json` 由 `scripts/audit_full_suite.py` 从本机五集原始字节、获取 manifest 和 12 个部署配置生成。保留 2026-11-04 的缺数据记录，不覆盖历史证据。每集的行数、split、gold 数量、ID hash 和模型预检问题在 JSON 中。

本轮新增数据：WildGuardTest 1,725 条，754 harmful、945 unharmful、26 null；原始 test 全部保留。既有 prompt-only 适配不读取 response/refusal 标签。

模型调用 0；未发起实验推理 API，没有新增 benchmark 成绩。下一步按[全集实验手册](../../../docs/infrastructure/full-benchmark-operations.md)进行真实 smoke，再启动全集；API 预算仍须由用户确定。
