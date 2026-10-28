# 离线模型适配验收

当前实现的验收位于 [final/verification.json](final/verification.json)：40 项单元测试通过，7 个检查符合预期，零真实模型调用。合成 workflow/单价不是 benchmark 成绩或实际费用。部署、checkpoint 加载、key、API 型号和真实接口仍未验证。

根目录先前的 verification.json 与日志保留为首轮工程证据。之后核对本机官方 anthropic 2.3.0 源码，发现其默认 API 版本和鉴权已变化，因此更新草案为显式 Bearer / 2026-10-21，并在 final/ 新建验收记录。早期 mock 通过只证明当时的代码路径，不证明其头部已被实际服务接受。两版各自保存源码哈希，未改写旧验收。
