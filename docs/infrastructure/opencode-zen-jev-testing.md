# OpenCode Zen 免费 Jev：项目测试入口

本项目新增测试默认使用以下配置，统一保存在 `.pi/pi-jev.json`，同时供 Pi Jev 插件和 `scripts/jev_api.py` 使用：

- endpoint：`https://opencode.ai/zen/v1/systemone`
- model：`jev-1.13-free`
- apiKey：`public`（公开占位值，不是私人密钥）
- timeout：10 秒；无自动重试，不回退到付费服务。

免费供应属于限时活动，没有持续可用性或服务等级保证。请求内容会发送给 OpenCode Zen 及其服务链路；不要提交密钥、个人数据或未授权的代码。这个入口可以用于支持相同 wire schema 的 Jev 测试，不代表所有第三方测试框架会自动读取它，也不替代离线本地模型或 JevBench 下载。

## 测试命令

仓库根目录运行（仅 Python 标准库，无新增依赖）：

```bash
# 合成 smoke test：choice / noul / score
python scripts/jev_api.py --out data/jev-zen-smoke.json

# 调用历史演示请求；发送时替换 model，源文件不变
python scripts/jev_api.py data/jev-request-examples-2026-10-11/03-rag-screen.json --out data/jev-zen-rag-screen.json

# 离线测试：不会调用网络
python -m unittest discover -s scripts -p test_jev_api.py -v
```

也可调用 `scripts/jev_api.py` 的 `evaluate(payload, config)` 供新的实验脚本复用。通过 `--config` 显式选择另一份配置；若需要私人凭据，使用 `JEV_TEST_API_KEY`，不要把私人值写进共享 JSON。

脚本不继承 `TYPESAFE_API_KEY`，避免把其他服务的私钥发往免费端点。HTTP 错误会使实验失败，不会记成“安全”或静默转向付费模型。保存结果包括实际响应模型、请求模型、来源模型、有效请求 SHA-256、HTTP 状态和端到端耗时，不保存鉴权值或完整请求正文。响应内容仍可能含敏感信息，保存前应自行确认。

## Pi 插件

个人配置 `C:/Users/14399/.pi/agent/pi-jev.json` 也已接入该端点。项目配置覆盖个人配置；`@y0usaf/pi-jev` 的 `TYPESAFE_API_KEY` 环境变量又会覆盖 JSON 中的 `apiKey`，使用免费通道前请确认未设置其他服务的私人 key。

运行 `/reload`，再用 `/jev` 检查模型和状态。当前 gate 为 shadow，只评估 bash / write / edit，不拦截；output 检查关闭。工具参数和最新用户请求的有界片段会被发给服务，shadow 并不意味着离线。API 出错时插件 fail-open，不能当作安全边界。

## 验证与实验边界

- 合成三类型请求已返回 HTTP 200，结果在 `data/jev-zen-smoke.json`。
- 使用已安装插件的原始 `client.ts` 副本做独立合成 Noul 调用，成功返回 `jev-1.13-free`；尚未验证交互式 session 的完整 hook 链。
- 旧结果、固定版本请求和第三方源码未改写。重新调用旧样本是新的 hosted-provider 实验，不能覆盖旧记录或声称与 `jev-1.13.0` 官方直连完全等价。
- 批量评测应先做小批验证，记录响应模型，控制并发，并预先固定样本、问句和阈值。
- 相邻 `D:/projects/jev` 的 benchmark 框架及第三方 JevOut / mu 没有在本次变更中自动迁移。它们需显式配置相同 endpoint、model 和 key，且先检查各自的接口适配。
