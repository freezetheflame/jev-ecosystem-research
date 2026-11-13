# 决策与进度

## 2026-10-28：完成 AgentHarm A1 独立输入检查适配

- 用户明确先做好符合当前研究目标的 AgentHarm 适配。本轮固定工程目标为 Mode A 输入请求风险分类，不接官方 AgentHarm 工具执行/harm score，不调用 DeepSeek。
- 新独立模板 `configs/agentharm-a1.template.json` 只含 AgentHarm、Jev 和 GPT-6 Luna，附判断问题/标签语义草稿；phase、split、模型有效参数、价格、暴露和预算保留未定。完整四基准模板的 AgentHarm contract 同步为 request_risk_classification。
- 配置和数据路径支持当前基准子集；单独计划/运行 AgentHarm 不再读取 MSB/MCPHunt/ATBench 或要求它们的参数。源哈希检查只覆盖显式选取的 harmful/benign split 文件。
- 原始 prompt 原样进入唯一模型字段 user_request。native item ID、base behavior ID、split、来源分区和 gold 独立保存；缺失请求/ID、重复或未知 split 拒绝。validation/test_public 分组报告，并导出逐项 predictions.csv，保留 safe/unsafe、状态、耗时和可估算费用。
- 新增离线 `inspect-inputs` 入口，支持缺少密钥/预算时先核对输入和实际展开请求。本轮 validation 准备实际为 64 项（harmful/benign 各 32，8 个基础行为），来源和导出文件哈希核对通过；位于 `data/agent-security-study/preparations/2026-10-28-agentharm-a1-validation/`，原文不入 Git。
- 29 项离线工程测试通过，含单 AgentHarm 计划→合成 transport→按 split 报告→恢复不重复调用、无标签泄漏和原始文本保留。完整验收日志及准备清单核对见 `data/workspace-evidence/2026-10-28-agentharm-a1-adapter/`。这些是临时合成响应/费率测试，不是模型 benchmark 成绩。
- 无真实模型 API 调用或费用测量；原 monitor 未改。尚需具体 GPT-6 Luna 标识、有效请求参数、真实价格与预算、划分/样本和暴露决定，并完成真实 pilot，之后才有实际分类分数与时间费用结果。

## 2026-10-28：MaliciousSkillBench 替换 AgentDojo，澄清 AgentHarm 对应范围

- 用户明确要求将 AgentDojo 换为 MaliciousSkillBench。第三版选型 `selection-2026-10-28-v3.json` 成为当前记录，名单为 AgentHarm=A1、MaliciousSkillBench=A2、MCPHunt=B、ATBench=C，11 个模型/方法不变。
- A1/A2 同属原输入检查，数字仅为序号；B/C 不在本轮推断。AgentHarm 可以评测有害用户输入识别，但这是本研究的分类适配，不是其官方 harm score。MaliciousSkillBench 的原生恶意 Skill 文本检测对应加载/使用前的输入检查。
- 纠正工程与基准能力的区别：AgentDojo 本身可以适配输入检查；不符 A2 的是此前实现的动作前 gate，不以此声称基准本身无法用于 A。旧代码、配置、数据及 ZIP 不删除或覆盖。
- 已从本地完整官方发布文件复用并核验 13 项，源 revision `d4b42ce5766a6e0359c987cf59c1007cb3795a90`。primary.parquet 9,740 条（7,505 恶意、2,235 良性），原文件 SHA-256 与官方 LFS 一致；不是历史 2,137 条子集。5 条原文 withheld 的处理策略未定，不默认为原文。
- 新运行模板及计划器使用当前四基准，不再要求未激活的 DeepSeek/AgentDojo。新增原生 parquet 适配器只传 skill_text，标签和来源独立保存；旧动态入口保留且显式使用旧配置。Jev 仍为 choice safe/unsafe。
- 无真实模型调用；离线工程验收输出另存 `data/workspace-evidence/2026-10-28-maliciousskillbench-selection/`。原始文本未执行、未重新标注；样本划分、暴露、prompt 和运行预算仍未冻结。
- 本轮 23 项离线测试、旧环境兼容检查、依赖检查和当前模板缺项拒绝检查均通过。native-data-inventory.json 由原始主表派生，明确冻结评测数量仍为 null。

## 2026-10-28：确认 A1/A2 均属原 Mode A

- 用户明确 1/2 仅为序号，A 仍按此前 Mode A（Input Inspection，输入检查）定义。当前分配保持 AgentHarm=A1、AgentDojo=A2，不将数字另解释为两种攻击类型或新 Mode。
- selection-v2 的 A1/A2 定义继承第一版原 A 对象，并记录 base_mode=A 和 ordinal。运行模板补齐两项概念定义；数据集输入/标签合同、prompt 与运行参数仍未冻结。B/C 未获本轮确认，继续留空。
- 现有 AgentDojo 动态代码是执行前授权 gate，与 A2 输入检查不符。预检明确拒绝将此 gate 标为 A2；本轮不将其伪称已完成的输入检查适配器。合成工作流单元测试用显式标注的测试合同，不代表批准研究 Mode B。
- 原始实验、旧定义原文和验收证据保留。本轮无模型调用；变更后的离线验收另存新目录。
- 离线验收通过，原始输出与当前代码哈希见 `data/workspace-evidence/2026-10-28-mode-a-ordinal/verification.json` 及同目录日志；概念定义继承与 B/C 仍为空的结构检查通过。

## 2026-10-27：用户指定 Jev 使用 safe/unsafe 二选一

- 新统一框架的 Jev 请求从 noul 改为 choice，选项顺序固定 safe、unsafe。请求保存各选项描述及实际 instructions；具体数据集 prompt 和其余运行参数仍未冻结。
- 按服务返回的 `answers.risk.choice` 直接映射 safe=0、unsafe=1；动态 gate 对 unsafe 阻断。移除 noul 概率字段和阈值配置，不用概率 argmax 替代缺失选择；非法标签和类型错配记解析失败。
- 更新 `security_bench/models.py`、配置预检、运行模板、测试与 README；selection-v2 追加用户选择记录。LLM safety 请求仍使用既有 risk 布尔输出合同，本轮未要求变更。
- 19 项离线测试及环境、依赖、模板拒绝运行检查通过。实际输出见 `data/workspace-evidence/2026-10-27-security-bench-choice/verification.json` 及同目录 stdout/stderr；测试使用合成响应，不是模型性能观测。
- 历史 noul/三 type 请求、结果、此前验收记录与原 monitor 保留。本轮没有真实 API 请求或新实验成绩；新代码/配置需新建计划，不能接续旧请求配置。

## 2026-10-27：统一评测框架与 DeepSeek 主 Agent 暂定

- 用户授权补齐统一运行能力，并允许复用 `freezetheflame/jev-skill-security`。已确认相邻 `D:/projects/jev` 的 origin 指向该仓库；只读复用原 monitor，来源文件及 dirty-state 限制见 `security_bench/reuse-manifest.json`，原 monitor SHA-256 未变。
- 用户回复“主agent先用deepseek吧，我再确认一下”。记录家族为 DeepSeek，精确模型、端点和请求参数仍留空，不猜版本或批准状态，也不加入 11 个受测安全方法名单。
- 新入口 `python -m security_bench` 提供 doctor、plan、run、report、check-environment。独立模块承担原始数据 view、模型请求、真实 AgentDojo 环境、调度、监控关联和派生报告；原 `framework.run` 与旧报告工具保持历史用途。
- AgentDojo 使用官方完整环境，逐 arm 独立恢复初始状态；固定攻击载荷在离线计划中生成并共用，gate 在工具副作用前执行。通过原生效用/攻击目标判分；没有动作 gold 时不生成动作混淆矩阵。
- AgentHarm 当前是原始 harmful/benign 请求分类，尚未实现其官方 Agent 有害任务执行/Inspect 评分。MCPHunt 当前是原始 messages 的完整轨迹分类，gold 字段须显式选择；ATBench 保留原始完整工具/轨迹结构。上述合同是工程能力，不自动批准 Mode A1/A2/B/C 的含义。
- 运行前保存完整实际请求字节和 attempt 事件；原始响应/失败、逐调用 monitor 索引、工具及状态变化保留。每次 transport 只调用一次原 monitor.record。费用未知则停下一请求；预算包括恢复前各段，明确不是账单硬上限。未决调用/episode 拒绝自动重放，变更输入/代码/环境/价格拒绝续跑。
- 新报告按六段必备记录结构派生分数/混淆矩阵/覆盖/失败、episode 成绩、时间、分组件估价与原始文件哈希；原生分数与改编分类分开，未计价不填零，旧分析不覆盖。
- 独立 `.venv-benchmark` 安装并通过 pip check；实际 72 个依赖版本锁定在 `requirements/security-bench-py312.lock.txt`。v1.2.2 四个 suite 均能加载：用户任务 16/21/20/40，注入任务 9/5/7/14。这是加载数量，不是已执行实验样本。
- 最终离线验证通过 17 项测试、上游环境加载、依赖检查，以及模板缺项拒绝运行检查。证据：`data/workspace-evidence/2026-10-27-security-bench-framework-release/verification.json` 及同目录原始 stdout/stderr。测试只使用合成响应/费率及临时目录，不是 mock benchmark 研究结果，不产生真实模型分数或费用。
- 未完成的实验输入：Mode/合同/prompt、DeepSeek 与 GPT-6 Luna 精确接口型号、模型参数/阈值、实际价格、预算、样本/划分/暴露及真实 pilot。配置模板保持 null，doctor 拒绝付费启动。本轮无模型 API 调用，未冻结确认协议。

## 2026-10-27：为 Box 存储及多机使用打包原始数据

- 用户要求打包当前四个基准，由用户存入 Box。未上传外部服务。
- 使用 `scripts/package_selected_security_datasets.py` 生成 `artifacts/dataset-bundles/jev-agent-security-datasets-2026-10-27-v1.zip`，包含完整官方 AgentDojo、AgentHarm 全部公开文件、MCPHunt 分层公开轨迹及配套源码、ATBench 原始 1,000 条文件。旧静态派生片段和其他试跑语料不纳入。
- 数据入口改为包内相对路径，附 `README.md`、逐文件 `MANIFEST.json`、标准库 `verify_bundle.py` 和来源/许可记录；外置 `.zip.sha256` 可供上传下载后核对。原始源码内已有的上游公开 runs 保留。
- 生成报告记录 ZIP 为 195,826,416 字节，36,989 个载荷文件全部经压缩包内逐文件 SHA-256 核对；ZIP SHA-256 为 `af7168c40d3b547bd25e66ed901e5f28650342e75ded94f3f5c27dab84049269`。外置 package-report 由代码生成，不手改。
- 这是数据与源码分发包，不含模型权重、本机凭据、虚拟环境或本项目实验输出。未安装或验证多机执行环境，未改变 Mode 未定及确认配置未冻结状态，未调用模型或修改 monitor。

## 2026-10-27：补齐当前四个基准的原始数据

- 用户授权核对并下载当前选定的 AgentDojo、AgentHarm、MCPHunt、ATBench，其他历史试跑语料不处理。
- 用户进一步明确不要将静态派生片段作为 AgentDojo 数据入口；采用官方完整仓库中的任务定义、suite 初始环境、攻击实现及判分代码。历史 TS-Bench/500 条片段留存，不充当完整 AgentDojo。
- 下载操作只获取固定 revision 的公开数据和源码，不安装或执行上游代码、不调用模型，不构成 smoke/pilot 或确认实验。下载固定版本不等于已冻结最终运行版本及样本集合。
- 获取脚本：`scripts/download_selected_security_datasets.py`；本地原始快照及逐文件 SHA-256 位于 `data/agent-security-study/datasets/2026-10-27/`。完整性、实际数量及未完成项以各 manifest 和后续获取索引为准。
- 获取已完成，核对脚本生成 `dataset-acquisition-2026-10-27.json`：AgentDojo 官方快照 36,860 文件、AgentHarm 8 文件、MCPHunt 数据 33 文件及配套源码 77 文件均通过逐文件 SHA-256 核对；MCPHunt 31 项发布者 Croissant 哈希全部匹配。MCPHunt 共 6,786 条发布轨迹，分层保留；ATBench 既有原始测试文件 1,000 条，与历史源哈希一致。AgentHarm 公开 harmful/benign 各为 test_public 176、validation 32；chat 另列，不混为独立任务。
- 上述是文件获取与完整性事实，不是标签独立审核、环境运行验收或新实验结果。AgentDojo 四个 suite 的初始环境和任务/攻击定义已检查存在，尚未执行。

## 2026-10-27：按用户附图调整当前选型（第二版）

- 当前共 11 项模型/方法，按图顺序：Jev 1.14.0、D3-Mini、Laya、SecJev、Jev-Guard；GLiGuard、Shieldstral、Qwen3Guard-Gen；Qwen3.5-4B、GPT-6-Luna、Claude-Haiku-5.5。移出 Plumb-4B，保留历史记录。
- 当前数据集：AgentDojo（2024，A2）、AgentHarm（2025，A1）、MCPHunt（2026，B）、ATBench（2026，C）。年份按用户表格记录；新增 AgentHarm，移出 InjecAgent、R-Judge、SCR-Bench。
- 用户明确回复 Mode 含义“还不确定，你先按照这个来吧，之后可能会调整”。因此只保存 A1/A2/B/C 代码，定义和旧代码映射保持未定；不批准任何推测解释。旧 B/C 定义不自动适用。
- 图中 Backend、Tasks 为空，保持未指定。Shieldstral / Qwen3Guard-Gen 不沿用旧 1.0 / 0.6B；精确制品与运行参数仍待确定。此前五类参数因素未被本图替换，留作历史参考。
- 当前记录：`docs/model-evaluation/2026-10-27-study-selection-v2.md`、`data/agent-security-study/selection-2026-10-27-v2.json`；模板和索引指向新版，旧清单、旧定义及历史结果保留。
- 本轮仅更新规划材料和配置引用，无模型/API 调用、数据下载、实验或 monitor 修改。旧报告工具仍使用历史 A/B/C/D 语义，新 Mode 定义后再适配，不将同名代码视为同义。
- 发布前合并通用静态配对框架；为其增加显式历史 Mode 命名空间校验，拒绝未定义的新版 A1/A2/B/C（包括同名 B/C）。14 项新框架测试、8 项历史框架测试、10 项报告层测试，共 32 项离线测试全部通过，无 skip；新版清单数量/代码/模板引用一致，原 monitor 哈希不变。

## 2026-10-25：用户明确研究目标

- 优先比较 Jev 与普通 LLM 承担完整 Agent 安全链路职责时的效果、时间和资源。
- 允许可替代、局部可用、有差距或证据不足的结论；不以证明 Jev 优势为验收条件。
- 方法约定：先固定主 Agent 比较安全模块，J 对 L 为主要比较；A/R 提供基线。具体配置尚未冻结。
- 采用固定 commit 的 research-rigor skill，保留本项目现有组织与历史数据。
- 已完成：候选核查、skill 安装、执行规范、未冻结配置模板与空记录表头。
- 未执行：新模型调用、benchmark 运行、费用/延迟/资源测量；没有新结果。
- 待确定：主 Agent、Jev 和 LLM gate 的具体版本及部署方式、可用预算与硬件、任务/攻击集合、协议中的数值参数。
- 下一步：核对固定版本原始 Agent 环境和开发任务的可执行性，再实现最小运行器和记录链，随后真实 pilot；不把历史静态预测或模拟 harness 当成全链路成绩。

## 2026-10-25：用户确定每次实验的必备数据

- 每轮必须记录数据集及条目数量、使用时间和费用、TP/FP/TN/FN 等基础统计、模型及完整有效参数、prompt 或请求结构，支持基本复现。
- 本地默认不计价；采用估价时独立给出费率、来源和计算公式。未计价不写零成本。
- 记录实际展开后的请求和输出、确切样本 ID 与 hash、代码/环境及启动命令；明确服务端隐藏参数和版本不可固定等限制。
- 二分类以预先定义的正类和统计单位计算混淆矩阵；动作 gate 默认“应阻断”为正。无 gold/不适用时明确标记，不编计数；错误和超时单列。
- 新增空白实验报告模板及逐条分类导出字段；协议与配置模板升级至 0.2，具体实验配置仍未冻结。没有新增实验观测。

## 2026-10-25：补充科学口径并保留 monitor

- 用户允许补充实验要求、整理代码职责，并明确保留现有 monitor。
- 已定位并只读核查 `D:/projects/jev/jev_skill/monitor.py`、调用方和文档，保留现有源码/接口/价格表；原有三项离线测试通过。
- 新增独立 `scripts/experiment_report.py`：核对计划/结果/逐条预测、重算基础指标、关联原 monitor 汇总；不发模型请求、不重算价格、不改原始记录。八项离线测试通过，包含命令行导出与拒绝覆盖。
- 配置新增可证伪假设、比较契约、主要效果和停止/复核/汇总口径，记录 monitor 关联；协议升级至 0.3，仍未冻结实际模型参数。
- 明确当前 monitor 没有预算硬停止、请求前开始事件、原生 episode/call ID；实际运行器后续需接入这些职责，不能声称已具备。
- 本轮新增的是规范和离线报告层，无真实模型实验、无新观测数据。

## 2026-10-27：用户提交暂定模型、数据集与参数范围

- 已按用户表格整理 12 项模型/方法：Jev 1.14.0、D3-mini、Plumb-4B、SecJev、Jev-Guard、Laya、Qwen3.5-4B、GPT-6 Luna、Claude Haiku 5.5、GLiGuard、Shieldstral 1.0、Qwen3Guard-Gen-0.6B。
- 数据集：InjecAgent（A）、AgentDojo（A/B）、R-Judge（D）、ATBench（C/D）、MCPHunt（B/C/D）、SCR-Bench（B/C/D）。Mode 操作定义尚未提供，不能与比较组 A/J/L/R 混同。
- 参数因素：type、instructions、questions 数量/分解、校准温度、输入长度/超长策略。只是因素范围，尚未固定具体值；decider 只作适用例子，不自动进入模型名单。
- 记录位置：`docs/model-evaluation/2026-10-27-study-selection.md`；机器可读 `selection-2026-10-27.json`。用户提供的日期、特点和引用标为 user-reported，缺项保持 null。
- 待确定：SecJev 尺寸、Laya checkpoint、Plumb/Jev-Guard 制品和接口，Mode 定义、样本数/划分、prompt/参数、主 Agent、预算和环境。
- 本轮仅整理并抽查部分来源页面；后续批量访问遇到 HTTP 403，未完成全部元数据验证。没有模型调用、权重下载、monitor 修改或正式配置冻结。

## 2026-10-27：用户补充 Mode A–D 的定义与论证

- 补足上一条的 Mode 定义缺口：A Input Inspection；B Pre-action Authorization；C Prefix-based Monitoring；D Full-trace Auditing。按照决策位置、可见信息、判断目标划分，非攻击类型分类。
- 完整保留用户两段论证与局部 [1]–[9] 对应；[5] Runtime Verification 尚缺具体书目，不猜测引用。
- 六个数据集的 Mode 对应维持原选型，不要求每个基准覆盖全部场景。缺失的执行前动作/前缀标签另行构造验证，不能复制完整轨迹标签；C 不见未来信息。
- 明确离线风险识别与真实运行时防护的证据边界，同源动作/前缀/全轨迹按原任务族划分与聚类。
- selection JSON 补充四种 Mode 的结构化定义；协议/模板升至 0.4。episode/prediction 增加 evaluation_mode，报告按 Mode 分组并拒绝错配；十项离线测试通过。
- 模型、数量、prompt、前缀切点和逐数据集标签合同仍未冻结。没有新模型实验，也未修改已有 monitor。

## 2026-10-27：用户要求试用官方长上下文模式

- 核对官方文档后，固定 `jev-1.14.0`，以一个合成数字档案做两次真实请求；先无长 header，再添加 `TypeSafe-Danger-Zone-Long-Context: true`。无重试、并发 1、每次超时 120 秒。
- 默认请求返回 HTTP 400 / max_tokens_exceeded；相同正文的长模式返回 HTTP 200，模型 1.14，读取中间记录为 deny，与合成记录一致。
- 服务报告输入 224,375、输出 41 tokens；长模式调用 6.311 秒，monitor 墙钟 9.478 秒；成功调用估价 $0.00942375。拒绝调用无 usage，费用未知，完整估价保持 null；本地未计价。
- 原始请求/响应、配置、源码/monitor 快照、环境、复现命令和哈希保存在 `data/jev-official-long-context/2026-10-27-smoke-01/`；说明见 `docs/infrastructure/jev-official-long-context-smoke.md`。
- 脚本三项离线测试通过。保留 monitor 源码/接口和免费通道配置。此次只证明该官方长请求被接受并返回，不是正式安全实验、完整上下文上限测试或一般准确率证据。


## 2026-10-27：汇总相邻工作区的已有跑测实践

- 导出已有静态经验、三种type评测/补测/资源分析代码与必要离线测试；原monitor不复制、不修改，新适配入口复用其接口。
- 收录历史100条本地/DeepSeek配对汇总，以及独立500条AgentDojo静态三type结果与样本/输入哈希、30项补测和时间费用。原始语料/响应不再分发。
- 500条是静态动作片段分类，不是真实agent闭环，也不是本研究全链路确认实验；本研究具体配置未冻结的状态不变。
- 本次仓库更新没有新模型调用、额外费用测量或重新标注；导出适配层只做离线测试。上游commit、历史monitor ID和失败请求账单未记录的部分明确为unknown。

## 2026-10-27：PR #1 审查与修正

- 对照现有源工作区核对了 11 项依赖哈希、500 个样本/state、30 条补测父记录及 1,500 个最终 cell，独立重算三臂 TP/FN/FP/TN，与导出汇总一致；这是结构/算术核对，不是标签独立审核或新模型复现。
- 离线回归复现权限错误后退出收集循环会遗漏在途完成结果的问题；修正为取消未开始任务并持续保存所有在途结果，新增回归测试，更新导出源码哈希说明。历史原始记录和汇总未改写，新实现另开输出。
- 修正后框架 8 项及既有报告层 10 项离线测试通过，无 API 调用；原 monitor 源码及接口保留。
- 已阅读 sample-manifest 中的完整 S4 v2 rubric：先识别可信用户任务，再判断当前动作是否服务该任务；将其作为后续 Mode B 的历史参考，不自动定为新确认实验 prompt，也不套用于 A/C/D。
# 2026-10-28：按用户完整模型清单补充推理客户端与输出映射

- 用户要求其他模型的推理/输出映射一起实现；API key 与本地模型部署由用户之后完成。本轮不启动真实模型实验、不下载权重。
- 新增 11 模型全量草案配置；按 evaluation_models 调度，保留既有 Jev/GPT 和历史动态模板。各服务协议及输出解析独立实现；Jev/D3/Laya/SecJev 使用 choice，GLiGuard 使用原生 prompt_safety，Shieldstral 使用显式 yes/no 极性，Qwen3Guard 使用 Safety 标签，普通 LLM 使用严格 risk boolean JSON。
- Jev-Guard 未查明官方可核验发布接口；仅预留 System One choice 桥接契约，不声称已经实现完整官方策略树系统。版本/尺寸/model ID 未选定部分保持 null。
- Controversial、格式错误、截断、拒答不进入有效二分类计数。保留 raw 并计入失败/覆盖率。本地计算未计价不触发 API 未知费用停止；未知 API 费用仍停止下一请求，原 monitor 不改。
- 具体接口、来源和限制见 docs/infrastructure/2026-10-28-model-inference-adapters.md；验收保存于 data/workspace-evidence/2026-10-28-all-model-adapters/。这不是科学配置冻结、正式执行或安全性能结论。


## 2026-10-27：补足通用静态 Jev / LLM 配对框架

- 用户询问 benchmark 到位后能否直接跑，授权从 `freezetheflame/jev-skill-security` 复用缺失框架。核对发现旧入口固定 AgentDojo 三 type，源 LLM 脚本绑定历史样本；不能直接覆盖任意原生基准。
- 从固定远端 commit 的 client/deepseek 适配传输与 JSON 判定思路；本地未提交的 SYSTEM_V2 只作独立历史参考，来源和差异记录在 `framework/paired-source.json`，不声称远端有该文件。
- 新增标准化 JSONL + 显式配置的静态配对入口，freeze/执行/分析分开，逐请求保留原始证据及失败；复用原 monitor 的 ResourceMonitor 一次计账，源码哈希保持不变。配置模板缺项保持 null，未冻结具体实验。
- 验证范围为离线工程测试，含本机 HTTP fixture 和原 monitor 接口；没有调用真实模型、下载完整 benchmark 或测出新的科学结果。六基准的原生转换、B/C 标签验证、各模型真实服务和 Agent 闭环仍需分别接入验收。
- 最终验收：新增 13 项、历史框架 8 项、既有报告层 10 项，共 31 项离线测试全部通过，无 skip；保存的源码快照可独立生成离线报告，原 monitor SHA-256 不变。记录这些测试不代表真实模型或原生 benchmark 已通过联调。


## 2026-10-30：四基准定为 A/A/B/D，完成 InjecAgent 与 TS-Bench 的离线 Jev 适配

- 用户确认按 A/A/B/D 推进：AgentHarm=A1、InjecAgent=A2、TS-Bench=B、ATBench=D。A1/A2 仍同属 Mode A 输入检查，数字只是序号；ATBench 原生是完整轨迹判断，改回 D，不再标 C。C 暂时空缺。
- 获取并核对 InjecAgent（revision `f19c9f2c…`，1,054 条攻击用例）与 TS-Bench（revision `46358fa4…`，7,182 步：3,770 safe / 1,631 unsafe / 1,781 controversial）。获取脚本 `scripts/fetch_ab_datasets.py`，数据在本地 `data/agent-security-study/datasets/2026-10-30/`，附 revision 与逐文件 SHA-256。
- 新增 `injecagent`、`tsbench` 加载器与 `input_inspection`、`pre_action_safety` 合同，注册 Mode D；离线导出改为任意单数据集通用，`--dataset` 可从多数据集配置中选一个。
- InjecAgent 的正类是原生攻击用例；负类由同一响应的 `Attacker Instruction` 删除得到，标 `derived_paired_neutralization`，不冒称原生标签。TS-Bench 的 0.5 由 `controversial_policy` 显式决定，本模板取 `unknown`（保留条目、记不可判分）。TS-Bench 同步多候选导致 `(interaction, segment)` 重复，item_id 追加源行号，family 仍按文件+interaction 聚类。
- 离线导出（无 key、无网络模型请求）：InjecAgent 2,108 条（1,054 正/1,054 派生负）、TS-Bench 7,182 条；每条目均生成 Jev `choice` safe/unsafe 请求样例，gold 单独存放。证据在 `data/agent-security-study/preparations/2026-10-30-*`，manifest 标 `model_calls=0`、`performance_results=not_run`。
- 7 项新适配测试通过；全量 47 项中 1 failure + 1 error，均为本机缺 `pyarrow` 与 MaliciousSkillBench 数据，另有 4 项 AgentDojo 依赖跳过。没有真实模型调用、没有成绩、没有费用、没有冻结配置。
- 限制：TS-Bench 测的是执行前动作安全，不是端到端阻断或任务效用；其 eval 轨迹与 AgentHarm 共享底层任务族，统计须按 family 聚类；InjecAgent 负类是合成反事实，结论不能外推到真实工具返回分布。
- 详细记录见 [2026-10-30 A/A/B/D 适配](docs/model-evaluation/2026-10-30-aabd-adaptation.md)；机器可读选型见 `selection-2026-10-30-v4.json`。


## 2026-10-30：Mode B 去掉授权合规语义，改为执行前动作安全

- 用户决定：B 不再要求“已验证授权/政策”，判断目标直接改为“这个拟执行动作安不安全、要不要在副作用前拦截”。时机和可见信息不变：仍是工具执行前，仍看动作/参数、已发生历史、任务上下文和工具说明。
- 影响：Mode B 从 **Pre-action Authorization** 改为 **Pre-action Safety**；动作级正类从“违反授权”改为“不安全/应阻断”。TS-Bench 因此不再需要补造授权字段，其原生 step-level 安全标签可以直接使用。
- 同步更新：`docs/model-evaluation/agent-security-evaluation-modes.md`、`agent-security-experiment-protocol.md`、`configs/security-bench-aabd.template.json`、`selection-2026-10-30-v4.json`。2026-10-27 用户论证原文保留不动，并加注其中 B 的授权表述已不代表当前定义。
- 边界：B 仍只看执行前快照，不含执行返回；仍不能把离线动作判断准确率当作攻击阻断率；C 的前缀风险、D 的整轨迹审计与 B 的动作标签继续分开。
- 不改变已导出的 InjecAgent/TS-Bench 请求样例，无需重新获取数据或重跑导出；本次没有模型调用。


## 2026-10-30：四数据集全部下载并通过 hash 与加载核对

- AgentHarm（revision `e23b3fe6…`）与 ATBench（`4476ef92…`）通过 `hf-mirror.com` 按固定 revision 下载。HuggingFace 直连在本机不可达，镜像只改变传输路径；文件内容由 SHA-256 核对。AgentHarm 6 个行为文件 340,071 字节；ATBench 18,335,079 字节，SHA-256 `80c534b5…` 与 2026-10-27 记录一致。
- 四个数据集实际加载结果：AgentHarm 416（208 harmful / 208 benign，validation 与 test_public 分开）、InjecAgent 2,108（1,054 原生正 / 1,054 派生负）、TS-Bench 7,182（3,770 safe / 1,631 unsafe / 1,781 controversial）、ATBench 1,000（503 safe / 497 unsafe）。
- 核对脚本 `scripts/verify_aabd_datasets.py` 重新计算 16 个源文件 hash、比对四个 manifest、走四个 adapter；结果 `data/workspace-evidence/2026-10-30-dataset-acquisition/verification.json`，标 `model_calls=0`。
- 四个数据集均已生成离线 Jev 请求样例：AgentHarm、InjecAgent、TS-Bench、ATBench 各一份 preparation 目录。仍无真实模型调用、无成绩、无费用。
- ATBench 轨迹较长（视图字符中位数约 7.5k、p95 约 26k、最大约 365k），全量直送 Jev 可能触发上下文限制；正式运行前须显式决定长上下文配置或截断/排除规则，不能静默截断。
- 配置模板现覆盖四个数据集；AgentHarm 与 ATBench 沿用原适配器，ATBench 走 D 全轨迹路径。


## 2026-10-30：Jev smoke-01 因 HTTP 451 地区限制失败

- 计划 8 条（AgentHarm/InjecAgent/TS-Bench/ATBench 各 2），实际只尝试 1 条 ATBench（item 86），HTTP 451 `Typesafe is not available in your region`，调度器随即停止；有效预测 0。
- 单次调用墙钟 0.828 秒（2026-10-30T05:53:57.549Z 至 05:53:58.386Z）。响应无 usage，monitor 记 `unpriced_calls=1`，API 估价为 null；不能写成 $0 或“免费”。本地计算未计价。
- 451 在鉴权前返回，所以本次不能判断 key 有效性；直连 451，本机 7890 代理 403，均不可用。
- 失败证据完整保留在 `data/agent-security-study/runs/2026-10-30-smoke-01/`，含 raw 请求/响应、events、episodes、telemetry 和自动生成的 analysis；另加 `SMOKE-NOTE.md` 说明范围。
- 不 resume 该目录（失败 episode 会被当成已完成而跳过）；恢复网络后新建 `2026-10-30-smoke-02` 重跑同一计划。


## 2026-10-30：smoke-02 完成 8 条真实 Jev 调用

- 新加坡节点生效后重试成功：8/8 HTTP 200，返回模型均为 `jev-1.14.0`，解析失败 0。smoke-01 的 451 失败保留为历史，不覆盖。
- 时间：06:03:04.346Z 至 06:04:05.576Z，总墙钟约 61.23 秒；单条 p50 7.578 秒、p95 7.906 秒。
- 费用：4,499 输入 token + 248 输出 token；按 `pricing-snapshot.json` 的 0.042 USD/百万输入、输出 0，API 估价 **0.000188958 USD**。这是 usage×列表价的估价，不是账单核验；本地计算未计价。
- 结果（n=2/数据集，仅冒烟）：AgentHarm 2/2；InjecAgent 2/2；TS-Bench 1/2（漏 1 条 unsafe 动作）；ATBench 1/2（漏 1 条 unsafe 轨迹）。不能合并成总分，也不能当能力结论。
- 证据在 `data/agent-security-study/runs/2026-10-30-smoke-02/`：`SMOKE-REPORT.md`、`raw/`、`events.jsonl`、`telemetry/`、自动生成的 `analysis/`。配置与数据 hash 由 `manifest.json` 固定。
- 未完成：pilot 规模、controversial 0.5 覆盖、长 ATBench 样本、主 Agent 闭环、效用与端到端阻断。运行配置仍未冻结。


## 2026-10-30：AgentHarm 50×3 pilot 完成

- 样本：AgentHarm validation，按 harmful/benign 各 25 条分层随机抽取（seed `20261030`），50 个 item、8 个 base family；确切 ID 见 `preparations/2026-10-30-agentharm-pilot-50-selection.json`。
- 执行：50 × 3 repeats = 150 次 Jev choice 调用，150/150 HTTP 200、0 失败、覆盖率 100%；返回模型均为 `jev-1.14.0`。
- 每次 repeat 的指标完全相同：TP 21、FP 0、TN 25、FN 4，accuracy 0.920（Wilson 95% [0.812, 0.968]）、precision 1.000、recall 0.840、F1 0.913、FPR 0.000。三次预测对 50/50 个 item 完全一致；4 条 FN 全为 harmful→safe，集中在 3 个 family。
- 时间：首条 09:18:16.069Z，末条 09:34:54.917Z，总墙钟 998.85 秒；单次 p50 7.257 秒、p95 7.704 秒。
- 费用：64,470 输入 token + 4,650 输出 token，API 估价 **0.00270774 USD**（输入 0.042 USD/百万、输出 0）；unpriced 0；本地计算未计价。估价不是账单。
- 限制：仅 50 item / 8 family；Wilson 区间未做 family 聚类校正；三次完全一致，无法估计采样方差；validation 公开集 pilot，不是盲测或 exposure audit；AgentHarm 输入分类不等于官方 agent harm score；无主 Agent、效用或端到端阻断。
- 证据：`data/agent-security-study/runs/2026-10-30-agentharm-pilot-50/`，含 `PILOT-REPORT.md`、`raw/`、`telemetry/`、自动生成的 `analysis/` 以及 `analysis/<version>-repeat-metrics/` 的逐重复与 item 级指标。


## 2026-10-30：GPT-6 Luna 与 Claude Haiku 5.5 经 OpenLux 中转完成 50×3 pilot

- 连接：`https://api.openlux.ai`，两个模型都走 OpenAI-compatible `/v1/chat/completions`，严格 JSON 输出。Claude 原生 `/v1/messages` 的 usage 带 `cache_creation_input_tokens`，现有 Transport 为避免错误计价会清空 usage，因此统一改走 chat 入口；模型仍是 `gpt-6-luna` / `claude-haiku-5-5`。
- 执行：2 模型 × 50 item × 3 repeats = 300 次；GPT 139 有效 + 11 provider refusal，Claude 149 有效 + 1 次散文拒答（JSON 解析失败）。
- 结果（共同 47 item 多数票）：GPT acc 0.957（TP21/FP1/TN24/FN1），Claude acc 0.872（TP19/FP3/TN22/FN3）；McNemar exact p=0.125，不能声称优劣。全 50 item：Claude 0.880；GPT 只能给 [0.900, 0.960] 边界，因为 3 个 harmful item（family 8）三次全被 provider 拒绝。
- GPT 的 11 次 400 `cyber_policy` 是上游内容策略，发生在推理前，不是模型判断；新增 `PolicyRefusal` 单独记录并继续调度，不把拒绝算成 safe/unsafe。Claude 的 10-3 repeat 0 是模型散文拒答，同样不计分。
- 时间：首条 10:12:30.969Z，末条 10:40:16.537Z，总墙钟 1665.57 秒；GPT p50 3.437 秒、Claude p50 6.093 秒。
- 费用：356,393 输入 + 22,412 输出 token，总 API 估价 **0.007445668 USD**（GPT 0.00408188，Claude 0.00336379，含失败调用）；11 次 refusal 无 usage、unpriced，不能记 0。价格按 OpenLux pricing_new 与实测路由组估算，不是账单。
- 证据：`data/agent-security-study/runs/2026-10-30-agentharm-relay-50-v2/`，含 `RELAY-PILOT-REPORT.md`、`raw/`、`telemetry/`、`analysis/*-multimodel-metrics` 与 `analysis/*-common-metrics`。
- 限制：8 个 family；GPT 拒绝集中在 family 8，共同 47 item 比较会排除 GPT 无法判分的 harmful 项；中转策略与路由组均可能影响结果/价格；仍是 pilot。


## 2026-11-01：Qwen3Guard-Gen-0.6B 本地部署完成并跑完 50×3

- 本机 RTX 3050 Ti Laptop 4GB 上以 bf16 加载 `Qwen/Qwen3Guard-Gen-0.6B`（权重 SHA-256 `4f3ce47e…`，1.50GB），transformers 4.57.1 + torch 2.2.1+cu121；显存约 1.12GB。通过 `hf-mirror.com` 逐文件下载，Hub 客户端直连失败。
- 新增 `scripts/local_guard_server.py`（OpenAI-compatible `/v1/chat/completions`）和独立 `.venv-local`；新增 `controversial_policy` 配置项，Qwen3Guard 的 Controversial 不再硬编码为解析失败。
- 执行：同一 AgentHarm validation 50 item × 3 = 150 次，全部成功。原始标签 Safe 48 / Unsafe 78 / Controversial 24。
- 指标（多数票）：strict（Controversial=unsafe）TP25/FP9/TN16/FN0，accuracy 0.820、precision 0.735、recall 1.000、FPR 0.360；loose（=safe）TP21/FP5/TN20/FN4，accuracy 0.820、precision 0.808、recall 0.840、FPR 0.200。两种口径都报告，不能只挑一个。
- 时间：p50 0.531 秒、p95 0.750 秒，150 次累计 81.42 秒；输入 53,370 token、输出 1,533 token；本地费用未计价。
- 证据：`data/agent-security-study/runs/2026-11-01-agentharm-qwen3guard-50/`，含 `LOCAL-PILOT-REPORT.md`、raw、telemetry 与两份派生分析。
- 机器分工：4GB 本地先跑 Qwen3Guard 0.6B（已完成），后续 GLiGuard 300M、Laya 421M、SecJev-0.8B 仍属本地候选；D3-Mini 4.5B、Qwen3.5-4B、Shieldstral 3B、SecJev 2B/4B 放到 3090 24GB。Jev-Guard 仍缺可核验发布制品。


## 2026-11-01：GLiGuard-300M 本地部署完成并跑完 50×3

- 本机 4GB GPU 以 gliner2 2.1.0 加载 `fastino/gliguard-LLMGuardrails-300M`（833,938,108 字节，SHA-256 `03132cef…`），显存约 0.79GB；输入为 AgentHarm `user_request` 原文。
- 150/150 次成功；50 item 多数票 TP25/FP1/TN24/FN0，accuracy 0.980（Wilson [0.895, 0.996]）、precision 0.962、recall 1.000、F1 0.980、FPR 0.040；1 个 benign item 三次误报。
- 时间：p50 0.078 秒、p95 0.094 秒，150 次累计 12.16 秒；输入/输出 token 均为 0（编码器分类）；本地费用未计价。
- 输入长度 max 145 token，低于 512 上下文，未截断。
- 新增 `scripts/local_gliguard_server.py` 与独立配置；证据在 `data/agent-security-study/runs/2026-11-01-agentharm-gliguard-50/`。
- 本地已完成 Qwen3Guard-0.6B、GLiGuard-300M；下一个本地候选 Laya-421M，再后 SecJev-0.8B。


## 2026-11-01：Laya-421M 本地部署完成并跑完 50×3

- 本机 4GB GPU 加载 `convaiinnovations/laya` 根 checkpoint（842,609,210 字节，SHA-256 `891102d3…`），显存约 1.58GB；laya 0.4.20，服务为 `Agent.system_one` 的 HTTP 桥接。
- Windows/torch 2.2 下 ModernBert 导入触发不支持的 torch.compile，服务在导入前将 torch.compile 置为恒等；推理为 eager。
- 150/150 次成功，无截断。多数票 TP7/FP2/TN23/FN18，accuracy 0.600（Wilson [0.462, 0.724]）、precision 0.778、recall 0.280、F1 0.412、FPR 0.080。25 个 harmful 只识别出 7 个。
- 时间 p50 0.078 秒、p95 0.094 秒，150 次累计 10.88 秒；输入 22,401 token、输出 0；本地未计价。
- checkpoint 自带部分 temperature 越界，laya 回退到 0.5 并警告 confidence 未校准；本轮只用 choice，不用 confidence。
- 证据在 `data/agent-security-study/runs/2026-11-01-agentharm-laya-50/`。
- 本地已完成 Qwen3Guard-0.6B、GLiGuard-300M、Laya-421M；只剩 SecJev-0.8B 属本地候选，其余上 3090。


## 2026-11-01：Qwen3Guard 原始输入对照（排除 JSON 包装混淆）

- 发现前一版本地 Qwen3Guard 收到的是 `{"user_request": ...}` JSON 字符串，而 GLiGuard 收到的是 `user_request` 原文；输入格式不可比。
- 用相同 50 item × 3 重跑 Qwen3Guard，`input_field=user_request`：strict（Controversial=unsafe）TP25/FP8/TN17/FN0，accuracy 0.840、precision 0.758、recall 1.000、FPR 0.320；loose TP22/FP6/TN19/FN3，accuracy 0.820。Controversial 从 24 降到 15 次。
- 原始输入只把 strict accuracy 从 0.820 提到 0.840，仍明显低于 GLiGuard 的 0.980；格式不是全部差距。
- 证据：`data/agent-security-study/runs/2026-11-01-agentharm-qwen3guard-raw-50/`。

## 2026-11-02：按用户要求同步后补跑本机剩余模型

- 已从 origin/main 同步 c4890e6；保留本机原有修改。导入用户 ZIP 的 runs/preparations 原字节，原件和导入 manifest 留在本地，不执行压缩包源码。用户随后明确不需要复核旧实验，因此不重算旧结果、不重跑已完成模型。
- 新跑 D3-Mini、Shieldstral-1.0-3B、Qwen3.5-4B；又依据原日志明确列出的 SecJev-0.8B 候选补跑第四组。沿用既有 AgentHarm 50 条、25/25 标签、8 个 family、相同输入 hash、3 repeats、schedule_seed=20261030。每组另开两条 smoke，原始记录和报告均保留。
- 四组各 150/150 调用成功，另 8/8 smoke 成功。多数票 accuracy：D3-Mini 0.98；Shieldstral 0.94；Qwen3.5-4B 0.88；SecJev-0.8B 0.86。均为本机真实 pilot，不是确认性或官方 agent harm score。
- 原 monitor 实现和接口不变；本轮 608 次全为本地推理，API 调用 0，本地计算未计价。模型加载单独记录，pilot 之前有 smoke；不跨显卡直接归因耗时差。完整 TP/FP/TN/FN、时间、参数/精度、模型和软件 hash、raw/source/telemetry 及复现命令见新 run 与 data/workspace-evidence/2026-11-02-local-agentharm-four-models/。
- Shieldstral 的一 token yes/no 协议允许显式 max_tokens=1 对应的 length 结束，文本仍须精确 yes/no；其他截断仍拒绝。52 项离线测试通过，新增真实推理链路均通过 smoke。
- SecJev 使用官方 v1.0.0 adapter、固定 backbone 和 Kev 代码、原 head/校准、FP32 未合并 LoRA。运行时 PyTorch 2.11.0 与参考 requirements 2.6.0 的差异明确记录，不宣称数值复现官方指标。
- Jev-Guard 尚缺核验后的制品/接口，保留给用户 3090。对应草案仅含该模型，不用同名 base 模型替代。

## 2026-11-03：补充找到 Jev-Guard 原生安全头发布

- 用户要求在本机补跑 2B 并整理所有模型数据。公开发布 hubin/jev-guard-v3.2-2b 的固定 revision、LoRA/heads/原生代码已核验；此前缺制品的记录不覆盖本次新发现。
- AgentHarm 使用 native safety-only，不使用类别输出或完整策略树成绩。原发布未固定基座 commit，本轮固定 Qwen/Qwen3.5-2B 15852e8c16360a2fea060d615a32b45270f8a8fc，并记录共享运行时与官方 requirements 的差异。
- 当前为准备状态，尚无本轮推理结果。按用户要求改用 Hugging Face 官方 HTTP 下载，经 127.0.0.1:7890 代理；保留此前下载缓存。

## 2026-11-03：Jev 经 OpenLux 中转重测

用户授权使用 GPT 原中转站重测延迟。模型列表核验为 jev-1.14.0（用户写 0.14.0），原生 /v1/systemone。同旧 Jev 的 50 条输入/hash、策略、choice、3 repeats、seed、串行和预算；仅改变 provider/endpoint/凭证来源及相应价格快照。2 条 smoke 单独保存。异时异机比较仅作探索性延迟观察，不作网络路径因果归因。保留旧 run，不替换主结果。

- 执行结果：150/150 pilot + 2/2 smoke 成功，返回 model 全为 jev-1.14.0。150 次请求 payload hash 多重集合与旧官方 run 完全一致。多数票 TP22/FP0/TN25/FN3，accuracy .94；p50 1.766s、p95 2.485s，累计279.955s；pilot API 价格估算0.001083096 USD。独立对照见 data/workspace-evidence/2026-11-03-jev-relay-comparison/，旧主比较不覆盖。

## 2026-11-03：主汇总切换 Jev 中转重测

用户确认以 OpenLux 重测替换汇总表 Jev 主行。分析脚本 PRIMARY 改为 2026-11-03-agentharm-jev-relay-50，重新生成 experiment-summary-v2，旧官方 run 与旧汇总保留。其他九模型数据核对未变；qwen35 确认 Qwen/Qwen3.5-4B、本地 BF16。

## 2026-11-03：汇总补充 token 口径

按用户要求生成 experiment-summary-v4，在 comparison.csv、tokens.csv 和文档中加入输入/输出/总 token、usage 覆盖与原因。取原 monitor/usage，不复算分词，不重跑。GLiGuard 无 usage 保持未知，GPT 11 次拒绝缺失 usage 仅报139次小计；非生成式输出0保留。原分数、时间、费用、参数量未变。

## 2026-11-03：统一50项主分母（探索性分析版本变更）

用户要求 GPT 也显示50项计算。生成 summary-v5，所有模型主指标统一为全50正确完成率，未决记未成功完成，不伪造safe/unsafe。GPT正确45、错误2、未决3，45/50=.90；已有预测条件准确率45/47=.9574、覆盖47/50=.94单列，TP/FP/TN/FN和F1不强行插补。旧预测、调用、token、费用和历史分析不变；此为事后描述口径变更，不是新确认性预注册，无新API调用。

## 2026-11-03：恢复 Jev-Guard 下载并完成校验

按用户要求短时试下、慢则停止。7890 经标准 aria2 断点续传速度可接受（整段平均7.2MiB/s），下载完成。Qwen3.5-2B 基座4548221488字节，官方固定revision的SHA256 aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1 校验一致；发布包逐文件hash也一致。下载清单在 local-models/nov02/jevguardbase/download-manifest.json。本次只有下载/文件校验，无新增模型推理和实验成绩。

## 2026-11-03：Jev-Guard 本机pilot完成

用户授权启动；官方 safety-only 适配下两条smoke+150次pilot均成功，50项多数票TP25/FP5/TN20/FN0、accuracy .90、F1 .9091。p50 .078秒/p95 .125秒，pilot累计13.591秒；输入17976、生成输出0，150/150 usage。本地未计价，模型加载/首smoke初始化单列；参考卷积回退和共享依赖差异见专门文档。11模型汇总在 experiment-summary-v6-final，保留统一50项正确完成率；原十模型字段核对未变。原monitor校验不变，6项针对性离线测试通过。

## 2026-11-04：整理已使用prompt

从28个实际run的events/raw提取2001条请求，验证每条request SHA256，按case.view只替换输入占位符并逐条验证无损还原，归纳16个实际模板。当前主比较11模型共1650条；其他包含历史、smoke、失败/部分实验和其他三基准smoke。模板目录data/workspace-evidence/2026-11-04-experiment-prompts-final，逐条展开原文仅在本地artifacts整理包，不更改旧raw。附本地可取得的4份原生chat template；服务端/未取得内部模板明确未知。无新模型调用。

## 2026-11-04：新增 Kev-4B pilot

用户授权加入4B并试测。固定 jaredpalmer/kev-4b 6cfce5c2fa4b4bd64026336ab649c5ca78857d52、原生代码2074cc44256200bb37540103fa4572901faa10f3、Qwen3.5-4B-Base 1001bb4d826a52d1f399e183466143f4da7b741b。沿用原AgentHarm50×3与2条smoke；明确BF16未合并、原temperature、无跨请求缓存/额外预处理，原monitor不变，运行时差异见新文档。目前基座下载中，未发起推理；已有12项适配离线检查通过，无付费调用。

- Kev执行完成：2条smoke+150次pilot全部成功，150次均正确且50项三次完全一致；TP25/FP0/TN25/FN0，accuracy/F1=1.0；p50 .157秒、p95 .328秒、累计27.615秒，输入21261、输出0。body除model外与原Jev150次完全一致，未改参数/温度，原11模型字段保持不变。使用参考卷积回退，本地未计价，不是官方参考路径或确认性结论。12模型汇总为2026-11-04-experiment-summary-v7。

## 2026-11-04：建立汇总专用目录

按用户要求建立data/agent-security-study/summary/，AgentHarm当前12模型结果置于summary/agentharm/。从已核验v7分析逐字节复制并核对hash，来源另记source.json；旧版本与raw路径保留。无新实验或分数计算。

## 2026-11-04：本机模型恢复与使用手册

用户要求盘点、补齐不能运行的本地选型，并固定Jev中转。恢复GLiGuard/Laya/Qwen3Guard原权重，固定HF revision并验证原SHA256；安装gliner2=2.1.0/laya=0.4.20且未改其他依赖，各2条本机smoke共6调用成功，原主12模型表不替换。另6模型重新加载/健康检查成功；原monitor不变。新增model_services和machine_benchmark统一入口，当前Jev模板及入口使用OpenLux。58项离线测试与12模型离线请求预览通过；共享WSL pip check存在其他工具既有冲突，原日志保留，不宣称全环境依赖一致。唯一使用手册为docs/infrastructure/local-model-operations.md；清单/证据在data/workspace-evidence/2026-11-04-local-model-operations/。服务已停止释放显存，无付费API调用。
## 2026-11-04：五数据集全集准备与操作规范

用户指定当前范围为 AgentHarm、InjecAgent、TS-Bench、StepShield、WildGuardTest；旧四集范围不再作为下一轮默认。12 个实验模型保留，试用模型不纳入，Jev 使用 OpenLux 中转站。

用户已明确接受全部公开评测条目、按原始 split 分报、历史暴露保留；InjecAgent 只用原生攻击条目，不构造负例；TS-Bench 0.5 保留 unknown。用户选择 WildGuard 作者原库，稍后配置访问授权，不替换镜像。

新增版本化部署配置、`scripts/fetch_full_suite.py`、`scripts/full_benchmark.py` 与[全集手册](../../docs/infrastructure/full-benchmark-operations.md)。全集默认一次重复、串行、单组合 24 小时是显式工程默认，可在首次运行前改变并记录；API 总预算没有用户定值，运行时必须显式传入，手册示例不是批准预算。描述性全集沿用内部 phase=pilot，并以 record_kind 区分；没有声称完成 confirmatory 统计协议。

正式原始记录位置：`runs/<campaign>/<model>/<dataset>/`；准备冻结与部署 health：`preparations/<campaign>/`；跨机汇总预留 `summary/<campaign>/`。旧 50 条 pilot 和旧汇总不覆盖。当前工作是数据获取/离线实现，没有本轮新模型调用。

# 2026-11-05：补齐 WildGuardTest 作者原始数据

用户授权从仓库 `.env.local` 中读取 HF_TOKEN 获取缺失数据。已通过 7890 代理下载 `allenai/wildguardmix` 固定 revision `d29c47f41c8b51348b5c8e8c81c039b3132b66d1` 的 README 与原始 `test/wildguard_test.parquet`，不使用镜像。凭证未写入产物。

原始 test 文件 2,258,878 字节，SHA-256 `6ccc2909c1ae6d41424fac69f1fc32535b1de39cb8f80407d81e8bc64a0bebca`，与作者库 API 的 LFS oid 一致。实际 1,725 条：prompt harmful 754、unharmful 945、null 26；未定标签保留，不补造 gold。

获取 manifest：`datasets/full-suite-v1/wildguardtest/manifest.json`；最新离线核验：`data/workspace-evidence/2026-11-05-full-suite-readiness/`（仓库根目录相对路径）。此次仅下载及离线预检，0 次模型推理，没有新 benchmark 分数或推理 API 费用。

## 2026-11-05：修复 API 分类输出与显式重试（探索性协议变更）

用户要求核对 AgentHarm 全集数量并修复 JSONDecodeError，允许网络、decode、格式和拒绝重试。固定原始数据核对：validation 64（32 harmful/32 benign）、test_public 352（176/176），共416个变体条目、52个基础任务族；chat和私有集不属于当前 behavior 输入分类合同。

原 `full-api-agentharm-v2` 审计：GPT 378有效、37 provider policy refusal、1 RemoteDisconnected；Claude 117有效、295 JSONDecodeError、3 URLError、1 TimeoutError。295个Claude失败均是合法HTTP响应包内的非JSON答案，而非外层JSON损坏；抽查有散文拒答，不能把295条都命名为已人工确认的拒绝。审计代码与输入hash见 `runs/2026-11-05-api-retry-diagnostic-v2/old-run-audit.json` 及同目录脚本。旧raw/results不修改。

新API配置使用明确分类材料边界与最多5次请求；2秒指数退避、最多60秒并参考数字Retry-After；网络、指定临时HTTP错误、解码、格式和拒绝可重试，第一次有效预测即结束。每次HTTP请求独立写raw、开始/结束事件及原monitor；删除原来未逐次计量的隐藏429重试。次数/墙钟/估价预算每次检查；未知费用保留null，按预留占用继续调度（原调用前PolicyRefusal豁免保留），不是实际费用或账单硬上限。401/永久配置错误停止；临时错误耗尽按失败保留并继续下一条。历史无重试配置保留原行为。

验证：68项离线工程测试通过；两模型416条离线预检通过。真实诊断仅每模型4条：按原记录顺序选前3条失败及前1条成功，不按正确性选样；显式总估价上限0.50 USD。GPT 4/4有效、6次请求（2次拒绝重试），25.743秒；Claude4/4有效、4次请求、19.059秒，未出现JSONDecodeError。GPT TP3/FP1/TN0/FN0，Claude TP4/FP0/TN0/FN0；这不是总体准确率估计。已知API价格估算小计0.000108654264 USD，GPT两次无usage拒绝费用unknown，费用合计unknown，本地计算未计价。原monitor SHA256仍为f1f3d220f87681e79d65d9baf91e7b1e30733f80312c60b4129a42be8fc00c67。

完整诊断记录、精确ID、有效配置、prompt、raw、monitor、环境和复现命令在 `runs/2026-11-05-api-retry-diagnostic-v2/<model>/agentharm/report.md` 及其链接产物。v1是凭证变量缺失的准备失败，0次模型调用，保留记录。没有启动新416条全集，没有追加Jev，没有合并旧成功和新失败补测；重跑须使用新campaign。公开且已暴露样本仅作开发诊断，不能称确认性证据。

