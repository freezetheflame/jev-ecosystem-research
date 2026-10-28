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

