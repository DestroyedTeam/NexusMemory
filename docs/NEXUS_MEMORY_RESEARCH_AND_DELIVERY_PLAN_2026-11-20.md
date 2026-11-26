# Nexus Memory：跨 Harness 研究与交付计划（v0.1）

日期：2026-11-20  
状态：研究计划与可验证原型阶段；不是完成报告，也不代表已迁移 Destruction Era。

用户于 2026-11-20 说明：此前语音转写中的 “destraction error” 是识别错误，规范名称为 **Destruction Era**；后续研究、搜索和迁移范围均以此名称为准。

用户于 2026-11-20 澄清目标端：第一阶段包含本地/自托管 Claude Code（API Key 或第三方网关）以及 Claude Desktop 客户端管理的会话，并研究其 Developer → Configure Third-Party Inference 网关模式。用户随后确认 Claude Desktop 的 Chat、Cowork、Code 三种 mode 全部纳入，并于 2026-11-24 的最新回复再次确认三种均纳入。Anthropic 托管的 Claude Code Cloud session/Projects 不是本阶段目标；它们仍作为单独的产品面和边界记录。CLI、Desktop 各 mode 与托管 Cloud 的 session 存储/导入能力必须分别验证，不可因共用网关或品牌而假定兼容。Claude Desktop 的具体版本和操作系统仍待锁定。

## 1. 目标与原则

Nexus Memory 旨在让用户在不同 AI Harness 之间迁移项目上下文、会话历史、层级关系、附件、记忆、Skills、MCP、插件、权限提示和自动化。产品目标是把“已研究过、版本已确认”的适配路线做成确定性工具，使后续转换无需 AI 临场重新猜测；对于新版本、未公开云端数据和不兼容状态，必须显式报告未知/损失，不能承诺市面上所有 Harness 无条件完美兼容。

核心验收标准不是“文本看起来相似”，而是：来源对象有可追溯身份；项目/Section/会话/分支/子任务关系不被扁平化；消息事件及附件有校验；目标端可恢复的状态经目标运行时实测；无法恢复的字段逐项说明；API Key、OAuth token、MCP 凭据、权限授权记录永不随包迁移。

## 2. 当前证据与未决边界

- 当前原型已解析 ChatGPT 导出 JSON 树和 Codex rollout JSONL，并保留分支关系、原始记录和工作区归属；对 Claude Code 的本地 JSONL 投影做过隔离测试，但仅对 Claude Code 2.1.172 + localhost 模拟 Messages API 验证，未访问 Anthropic。
- Anthropic 托管的 Claude Code Cloud/Projects 要求 claude.ai 账号认证；API Key/Console-only 不可用于该 Cloud/teleport 工作流。用户将第一阶段目标明确为本地/自托管 Claude Code 与 Claude Desktop 客户端管理的 session，并确认 Desktop Chat、Cowork、Code 全部纳入；Desktop 的 Third-Party Inference 配置属于单独网关/客户端路径，不等于 Anthropic 托管 Cloud session。官方 Microsoft Foundry 指引称其 Desktop 配置可将模型请求路由至 Foundry、由 Azure 计费且会话留在用户设备；Cloudflare 也记录了 Claude Desktop 经 Gateway 请求的配置流程。以上只证明这两种特定网关路径的文档化配置，不证明 ChatGPT/Codex 历史可以原生导入，也不证明 Desktop 各 mode/版本/OS 之间有相同 session 结构。见 `docs/research/evidence/target-scope-clarification-2026-11-20.txt`。
- First-party Codex app snapshot 暴露本地 Projects 与带 source-qualified item keys 的 sidebar Sections；Sections 的 membership 与 Project/Thread 的 containment 是不同关系。此本地快照没有暴露名为 “Destruction Era” 的 Project；ChatGPT 历史索引中也没有标题/摘要匹配，但这不证明对象在帐号中不存在。当前没有用户导出的真实 ChatGPT/Codex 数据，因此不声称实际迁移。
- 2026-11-22 官方文档复核进一步确认：Claude Desktop on 3P 可覆盖 Chat、Cowork、Code 三种界面，gateway 模型请求与本机/SSH 会话存储分离；Desktop 通过自身 Third-Party Inference 配置读取 gateway，开启后不提供 Anthropic-hosted cloud environment/Remote Control。Chat/Cowork 与 Code 有不同的本机 session/transcript store；官方 importer 仅承诺导入 Claude.ai 与本机早期 Cowork/Code 数据，不是 ChatGPT/Codex 通用 writer。仍需锁定 Desktop 版本/OS，并以授权副本逐 mode 做 list/resume/附件/hash 验证。详情见 `docs/research/evidence/claude-desktop-3p-current-review-2026-11-22.txt`。
- 截至本计划，GitHub 元数据筛选共有 303 个独立候选；深度源码/测试审查仍只是小样本。已检查 session-migrate、OpenCode、DSH 等代表性项目，以及 HarnessKit、Bridle 等相邻工具；该样本远不足以宣称全市场覆盖。
- 新增第 11 个手工补充候选 `Chang-Tong/dsh-unified-context`（前 repo alias `dsh-import-agents`，MIT，package 0.5.0，pinned commit `108a5f09a151754220f66e5e9a0214f98551d802`）：本地 build 和 74 项测试通过，但不是 ChatGPT Project/Section 或 Claude API-Key/Cloud 迁移器；静态/合成审查发现分支与工具结果丢失、Skill 路径逃逸规划，以及 partial append 后 retry 按 ID 跳过。详情见 RESEARCH.md。
- 原 303 项语料中高星候选 `jazzyalex/agent-sessions`（MIT，6.6，pinned `3dfa0405d204279b7581d85218ea04fa218af8a7`）已做源码/测试深审：适合本机搜索、子任务展示和原 CLI 恢复，不是 ChatGPT Projects/Sections 或 Claude Cloud/API-Key 迁移器。全量 Xcode suite 4,586 passed / 9 skipped / 1 host-locale 金额断言失败；该断言在 en-US 单测通过。详见 RESEARCH.md。
- 2026-11-20 的增量人工发现新增了 a2migrate、sessionport、zen 与 baton 深审记录：a2migrate 实现 Claude Code/OpenCode 双向会话与配置迁移但没有 ChatGPT/Codex parser，且 MCP writer 会写入原始凭据值；sessionport 的 122 项测试/构建通过，但 Claude writer 将分支父指针线性化；zen 利用 Codex 原生 importer 做 Claude→Codex，反向生成 Claude JSONL 时明确丢弃侧链/图片/文件历史并有大小上限；baton 有 9 种读取格式、6 种写入格式及 35 项 Rust 测试，但其 canonical session 没有 fork/branch/project 关系，Codex writer 会把附件降为占位文本。手工发现不计入原 303 个 API 搜索元数据记录；市场筛选与真实目标 Harness 恢复验证仍未完成。
- 对原始候选 `shenysun/skills-manager` 完成源码与测试审查（MIT，固定 commit `948db52fa5dcfdae994073cf9d8c1fd05ab89205`）：它是共享 Skill hub/分发工具，不是 ChatGPT/Codex Projects/Session 迁移器。全套测试首次运行 1,048/1,052 通过、4 项失败；复测将 2 项 Git identity 测试确认是缺少 Git `user.useConfigOnly` 的 host-fallback 假设，另有 1 项受本机 `/Applications/ZCode.app` 的绝对路径探测影响，1 项固定 2026-08-20 的“fresh”测试已老于 90 天阈值。其内置 catalog 来源日期 2026-08-18，实际也已过期；一次隔离 `catalog refresh` 收到 GitHub API 403，未完成刷新。详情见 RESEARCH.md / COMPATIBILITY.md / ARCHITECTURE.md。
- 对原始候选 `shuqinlee/ConvFlow` 做了源码可用性筛选：仓库说明声称支持 ChatGPT/Claude 对话迁移，但固定浅克隆 `b78dfeb521dcdc2de3ca51a81b9b4f43056e2f70` 只有 Apache-2.0 LICENSE，CodeGraph 找到 0 个可索引源文件，GitHub 当前页面显示 1 个 commit、无 release、0 stars。没有可运行实现、测试或 README 功能细节，故标记为 `screened_no_implementation_only_license`，不据其简介推断迁移能力。
- 对 `Sai-Nitin123/ContextBridge` 完成固定版本源码/测试审查（commit `2a4b9b460387679c9dcced9b7cad3b6afa0aa6d8`）：它是浏览器里的 `.aicx` 上下文与 continuation-prompt bridge，不是 Claude Code API-Key/Cloud session writer，也不恢复 Project/Section/branch。干净隔离安装后 53 项测试和生产构建通过，但三个合成对抗探针证实消息脱敏后 secrets 仍泄漏到派生摘要/附件元数据，且标题可关闭 `<historical_context>` 安全围栏；manifest 使用 `<all_urls>`。README/package 声称 MIT，但克隆无 LICENSE 文件、候选 SPDX 仍为空。详见 RESEARCH.md。
- 2026-11-22 更新 OpenAI Codex 的 first-party importer 研究：固定 source `8653ca9e99b2c805107bde7b7d6f57a634c643d0` 的 `MigrationDetails` 包含 Skills、MCP、Memory、Plugins、Hooks、Subagents、Commands 和 Session `{path,cwd,title}`，但源适配器是 Claude Code/Cursor，不含 ChatGPT Project/Section。实际 exporter 将 session 映射成用户/助手文本的 Codex rollout，不会重建原生工具调用和项目/分支图。OpenAI `codex-plugin-cc` 对外调用同一协议实现 Claude Code→Codex transfer；不能倒推成 ChatGPT→Claude 或 Desktop 3P importer。已有更新/重导入问题仍需按版本实测。
- 对原始 GitHub 候选 #136 `rbutera/harness-bridge` 完成固定源码/测试/CI审查（MIT，HEAD `31559c93be61fa6adec584b728f843e2f92330f3`）：它是 Claude Code CLI↔Codex CLI 的实时 MCP 委派，不迁移 Projects/Sections/Session graph，也不调用 Codex external-agent import API。Codex exec 默认无条件绕过审批和 sandbox；app-server 用 `danger-full-access`，故不作为 Nexus 迁移依赖。17 个测试文件 127 项通过；格式、lint/typecheck、构建及固定 CI 通过；pnpm frozen install 因 esbuild 安装脚本被 pnpm 11 拒绝而退出 1，未批准该脚本。详见 `docs/research/evidence/rbutera-harness-bridge-review-2026-11-22.txt`。

## 3. 领域模型与项目结构

Nexus 的 Canonical Bundle 必须拆成相互引用但不互相冒充的对象图：

1. **Account / Workspace / Host**：账户域、运行端、远程/本地执行环境。
2. **Sidebar Section**：侧边栏展示分组，可对 Session/Thread 建 source-qualified membership；不默认是 Project 的父节点。
3. **Project / Location / Repository / Worktree**：目标工作区和存储位置，保留路径、repo、host、默认分支等字段及其 provenance。
4. **Session / Conversation / Thread**：一条会话主干；保存会话 ID、标题、模型/Agent 元数据、时间和当前状态。
5. **Message / Event / Turn / Tool Call / Result / Compaction**：序列事件和投影视图分开；用户补充、停止/改向、失败工具调用、重试、摘要压缩均应有独立事件类型。
6. **Fork / Branch / Parent / Child / Subagent / Workflow Task**：区别聊天分叉边界、Codex 任务父子关系、并行 Agent、工作流步骤和工具派生会话。只有来源明确提供边界时才声称准确保留 fork point。
7. **Asset / Attachment / Artifact / Link / Changed File / Snapshot**：文件内容入内容寻址存储，保留 MIME、原始名称、来源引用、SHA-256、尺寸和缺失原因；URL 不是附件本体。工作区 patch/checkpoint 与会话 transcript 独立。
8. **Skill / MCP Server / Plugin / Instruction / Memory / Permission / Secret Reference / Schedule**：每类资源都有独立 scope、版本、依赖、启用方式与权限；迁移配置不等于复用凭据或授权。

实现上保留两份并列视图：A) 版本化原始源记录与事件账本；B) 面向目标 Harness 的投影。任何删改都生成 machine-readable loss report（field, source evidence, target capability, transform, loss reason, confidence）。

## 4. 研究矩阵与证据分级

### Harness 覆盖范围

按执行形态而非品牌名去重，至少持续覆盖：ChatGPT/Codex；Claude Desktop/Claude Code 本地与 Cloud；Gemini CLI/Antigravity；Cursor；Windsurf；Cline/Roo Code；OpenCode；Continue；Zed/ACP；Kiro IDE/CLI/Web；Warp Terminal/Agent/Oz；Goose；Aider；Pi；OpenClaw/Clawdbot；DeepSeek Harness；各类云端 IDE/Agent 平台；以及用户确认的 “Walkie Talkie / Kura / Tree / DS Harness”等具体产品/项目名。每个项目先做存在性、版本、许可和功能定位核验，再决定深审；品牌近似/语音转写名称必须在报告里标为待确认，不凭名字扩写事实。

### 项目数量与筛选

初始语料是 303 个 GitHub 搜索结果，另有 11 个经人工发现、未命中初始查询的补充项目；两类均不等同于合格项目。下一轮继续完成去重/许可证/维护状态/代码可运行性分类，至少形成：
- 100+ 初筛记录（项目名称、URL、Harness 类型、许可、活跃度、搜索匹配、初筛结论）；
- 30+ 二次筛选记录（源码与测试入口、导入导出/存储格式、分支/附件/配置 coverage、维护风险）；
- 12–20 个深审对象（源码调用链、schema、测试、版本、实测门槛、缺陷/限制）；
- 每个优质候选公开证据与每个淘汰类别的淘汰理由。

数量只是目标，不代替质量。项目得分维度：版本化接口、真实格式/fixture、分支/媒体覆盖、Round-trip测试、明确许可、维护质量、安全模型、跨平台行为、与用户 API-Key 模式的契合度。Stars/README 描述不计作实现证据。

### 证据等级

E0 名称/发现；E1 官方文档；E2 源码/Schema；E3 官方 fixture/unit tests；E4 沙盒原生 CLI/API 导入导出；E5 带代表性真实导出的端到端恢复；E6 用户确认的目标数据迁移及回滚演练。README claim、issues 报告与我们亲自复现需分别标注；搜索不到仅表示“当前未找到”，不代表功能不存在。

## 5. 研究与实现阶段

### Phase 0 — 锁定范围与数据授权（当前）

目标端类别已确认：本地/自托管 Claude Code 与 Claude Desktop 第三方推理网关模式；Desktop 的 Chat、Cowork、Code 全部纳入，Anthropic 托管 Cloud 另列而不作为本阶段迁移目的地。继续锁定 Desktop 客户端版本与 OS；获取用户自助导出的 ChatGPT 数据或可达的 Project/Section 清单；确认 Codex app/CLI 具体来源、平台和版本。只在用户选择的副本/导出上操作；不读取任何未授权账号数据。

**Gate 0**：目标类型、认证模式、输入对象路径/格式、保护边界、成功/回滚标准具备明确值。未确认目标时只做研究/预览，不连接实际服务。

### Phase 1 — Source adapters 与内容盘点

ChatGPT ZIP/JSON：识别 conversations、mapping 节点、parent/children/current node、项目元数据、导出附件与链接；统计缺失的 Project/Section index、memory、scheduled task 等字段。Codex：分别读取 local rollout JSONL、remote/workspace thread 和 project/task metadata；用正式导出或本机 app database API 而非推测，校验 parent thread、fork/side chats、uploads/artifacts、tokens/cost、任务状态。

**Gate 1**：只读 inspect 命令能输出机器可读清单、哈希、敏感信息告警、关系图及未知字段，不写目标文件。

### Phase 2 — Canonical Archive v1

发布 schema version、事件类型表、实体边、Asset Manifest、未知字段扩展槽、source adapter provenance、目标 loss/capability report、去重与冲突规则。未知数据原样保存在加密/受限本地包中；secret-like 内容默认标记/隔离，不自动带入目标端。准备 golden fixtures：线性对话、修改/再生分支、用户补充/中断、图片/文件、工具失败/重试、子任务、MCP/Skill、token/cost、归档、定时任务。

**Gate 2**：任意源字段可映射为保留/投影/sidecar/损失/未知之一，并经 round-trip 断言；Attachment hash 端到端一致。

### Phase 3 — Target adapters（由 Gate 0 选定后排序）

先做目标本地 dry-run projector，再做原生导入/API adapter；优先利用正式公开接口，其次只在版本固定并经隔离回归的非公开格式上建立兼容层。Cloud 执行环境单独建 auth adapter；不复制 API Key、OAuth token、MCP secret 或权限 grant。每个目标定义“可创建 Project/Session”、“可恢复 transcript”、“可恢复 branch/subtask”、“可挂载附件”、“可激活 Skill/MCP/plugin”、“可配置 schedule”独立能力。

**Gate 3**：真实目标客户端能看到并续写会话；线程层级、工具调用、附件、任务输出各自通过明确的人工+自动断言；不满足时降级为可用 handoff bundle，不能标“原生迁移成功”。

### Phase 4 — Fidelity / 安全 / 可恢复性试验

按来源×目标×版本生成矩阵；比较实体计数、边数、消息序列、分支点、时间戳、usage、asset hash、native resume、skills/MCP activation、schedule semantics。准确率用分项覆盖率报告，不给单一“迁移准确率”掩盖丢失项。失败注入：重复运行、部分写入、路径冲突、ID 冲突、无父节点、坏媒体、API timeout、目标权限不足；验证 rollback 到目标 pristine hash。

**Gate 4**：preview/apply/verify/rollback 四个阶段均可复现、审计；失败报告含原始异常和恢复建议。

### Phase 5 — 发行形态与 Harness 自动发现

先交付 CLI + 可阅读 Bundle/报告，保证 macOS/Windows/Linux；随后评估 Codex Skill、Claude Code Skill/Plugin、macOS `.app` 与 Windows `.exe`。安装器仅负责发现 Harness 版本/路径/目录，执行已验证规则；未知版本应进入“unsupported/manual review”，不能用 AI 临时猜测后写入。工具本身可以不调用模型，但新 Harness 新版本适配仍需维护者研究/规则更新。

**Gate 5**：跨平台 package smoke tests、签名/供应链/升级/回滚策略、卸载不删除用户数据、运行日志不记录凭据。

## 6. 衡量指标与成功定义

- **结构保真**：已知实体与边保留率，分开统计 parent/child、fork boundary、Section membership、Project containment、workflow/automation。
- **消息保真**：role、顺序、可见文本、tool call/result、失败/中断、compaction summary、token/cost 各自统计。隐藏 reasoning/system prompt 只在合法/明确导出时处理，不能假设可读取。
- **资产保真**：有效载荷数、hash、MIME、inline/reference 状态、缺失/不可访问/损坏原因。
- **原生恢复**：目标客户端找到 Project/Session、resume、正确工作区/父链、附件可读取、MCP/Skills 可按用户授权启用。
- **安全**：secret 检出/误报、默认拒绝共享凭据、rollback 后 pristine hash 相等、用户对每个写入目标有确认。
- **覆盖**：每个 Harness/版本/路线的 evidence level、last verified、known loss、automated test count；不拿搜索数量或 README claims 冒充支持率。

只有 E5/E6 端到端证据才能声称“在该版本/该数据样本上已验证恢复”；“所有 harness”“完美迁移”不作为无条件宣传语。

## 7. 当前阻塞与用户输入

1. Claude Desktop 的 Chat、Cowork、Code 三种 mode 均已确认纳入。官方 3P 文档已说明其 per-mode 数据目录和 Claude-origin import 边界；仍需锁定客户端版本和 OS，并对授权副本实测 ChatGPT-origin 对象的 native listing/resume、附件及回滚。
2. 提供 ChatGPT 自助导出 ZIP（可本地副本），或打开/指出具体 ChatGPT Project/Section/Conversation。当前本机 app API 快照未显示 “Destruction Era”，没有真实源数据可迁移。
3. 确认是否只做自己帐号、是否包含附件/媒体、以及是否允许目标端创建新 Project/Session；凭据仍需在目标产品单独输入。Anthropic Cloud session 不会因第三方 gateway 或 API Key 而自动成为可写目标。

没有这些输入时，Nexus 可继续完善 schema、研究矩阵和 synthetic tests，但不会声称项目层级已精准迁移，也不会对任何 Cloud 服务发起实际写入。

### 增量深审：Agent Connect（2026-11-20）

在原始 303 个 GitHub 元数据候选中固定审查 `1naruto-1/agent-connect`（MIT，commit `42287c14a8fd381bc7ef7a96076a5cba5b4d75f6`）。本地源码/测试支持 Cursor、Claude Code、Codex CLI、Pi 的部分本地会话互转，但 canonical event 只有五类，不携带完整分支/项目/Section/附件字节/token-cost/权限/自动化图。故将其作为格式与安全模式参考，不视为 ChatGPT Project/Section 或 Claude Cloud/API Key 迁移器；122 项测试通过也不等于 12 条路线均已完成原生恢复验收。详见 RESEARCH.md。

### 增量深审：AI Workspace Manager / AIW（2026-11-20）

原始候选中的 `neosun100/aiw`（MIT，固定 commit `a9e4221aa39e20aa7c041528805f8a763c035158`）属于 tmux 实时工作区管理器，而非会话迁移器：`sessions.json` 记录工具与目录等工作区元数据，日志来自当前 tmux pane，未发现消息树/附件/Project Section 导入导出。66 项单测通过但均以 mock 覆盖为主。静态源码还发现全网卡默认、API 无认证及 shell 命令字符串插值风险；分类为“迁移低相关，仅作编排对照”，不建议直接用于有敏感上下文的网络环境。详情见 RESEARCH.md。

### 增量深审：DSH 升级修复 Skill 与官方导入器（2026-11-20）

`Fabian-698/dsh-update-guide`（MIT，固定 commit `0fcb77d2a9abf8c28da32119a243a568bd9c3824`）是特定 DeepSeek Harness 0.1.2–0.1.7 版本升级/恢复工具，不是跨 Harness 导入器；本地合成测试发现它在目录同时有 V4 权威后继、V2 旧日志时仍把 V2 列为可修复，且 `--apply` 能改写 V2。官方 DSH 当前已到 0.2.2-rc.5。官方实验性 DeepSeek website 导入器只读该站 ZIP、每个对话写一个 Session、仅保留导出 active branch；rc.5 又有用户报告的合法 data-descriptor ZIP 读取失败（尚未由我们用真实导出复现）。因此仅作 DSH 格式/恢复边界参考。详见 RESEARCH.md。

### 增量深审：DSH Unified Context 社区导入器（2026-11-20）

对 `Chang-Tong/dsh-unified-context`（former `dsh-import-agents`）固定 commit `108a5f09a151754220f66e5e9a0214f98551d802` 深审：五种本地 session adapter 入 DSH，加上部分 Skills/context/memory/automation 路径；不含 ChatGPT reader、Claude Cloud/API-key writer、Section/Project mapping 或通用 MCP/provider/permission 迁移。`pnpm run build` 与 13 文件/74 tests 通过，但 synthetic fault injection 证明 append 中途留存两事件后，重跑按 stable ID 跳过；另有 `../escaped` Skill 名称会把规划目标放到 skills root 外（未执行恶意写入）。该项目适合作为 DSH 目标格式/adapter 参考，不能作为本目标迁移成功证据。其 findings 更新了 Nexus 对部分提交恢复、路径 containment 与完成回执的架构要求；见 RESEARCH.md / ARCHITECTURE.md。

### 许可证筛选：coding_agent_session_search（2026-11-20）

该高星项目仍留在原 303 项 GitHub 元数据清单，但已标记 `license_restricted_excluded`。仓库许可证的 OpenAI/Anthropic rider 将源码分析、索引、测试也列为受限使用；未取得书面许可前不做依赖或 benchmark，不声称其兼容性。发现 rider 后删除了临时克隆与 CodeGraph 索引，未运行构建或测试；不计入 11 个手工补充候选。


### 增量深审：AI Config Sync Manager（2026-11-20）

已完成对原始 303 条 GitHub 候选中的 slash9494/ai-config-sync-manager 的源码与测试审查。固定版本为 MIT、npm 0.1.13、commit 3ac0566032807acabc79405245777edcc780d347；它是 Claude Code 与 Codex 的本地配置双向同步器，不是一次性会话迁移器。测试在先执行安全的 build:dist:no-sync 后，445 项中 443 通过、2 跳过、0 失败；未连接真实 Claude/Codex 服务，也未写入 Cloud。

结论：可借鉴本地配置的 diff-first、selector、备份及逐项哈希记录；不能用于 ChatGPT Project/Section/Session 到 Claude Cloud/API-Key 的迁移。它没有会话图、ChatGPT reader、Cloud writer、附件/Token/定时任务导入；memory 明确 out of scope，plugins 只显示状态。默认 MCP env 会复制密钥，开启环境变量才做基于名称的过滤，与 Nexus “凭据默认绝不随包迁移”相冲突；hooks/permissions 的 manual 标签也不是强制确认门。保留为相邻配置同步参考，拒绝作为核心迁移依赖。完整证据与测试前置构建差异见 RESEARCH.md。


### 增量深审：memory-harness-kit 跨 Harness 记忆系统（2026-11-20）

已完成原始候选 pgrigorr/memory-harness-kit 的源码和运行验证，固定 commit 3374ead82060868b2398acffb40f945402bb4cac；顶层 LICENSE/pyproject 声明 Apache-2.0，GitHub API 的许可证字段仍为 NOASSERTION。它值得参考的是“原始来源—规范化记录—事实/检索—审核队列”的分层记忆管线，以及可选 Claude Code Stop/SessionStart 捕获与索引钩子；但 config adapter 仅 generic/OpenClaw，不能导入 ChatGPT/Codex Projects/Sections/Session 或写入 Claude Cloud/API-Key 会话。

安全与保真门未满足 Nexus 要求：合成测试发现 credential-shaped marker 同时留在 raw 和 normalized search record；source filename sanitize 把 a/b 与 a_b 映射到同一路径并覆盖；Claude JSONL normalize 只输出用户/助手文本，project_slug=null，不建立 branch/project/section typed edges。make ci-smoke 289 项通过，make ci-artifact-proof 通过，但 OpenClaw live workspace 和任何真实 Harness/Cloud 导入均未验证。结论：仅作为低星但有架构价值的记忆层参考；不作为迁移依赖，需先补秘密过滤、稳定身份/冲突检测、跨 Harness 源/目标 adapter 与关系保真测试。


### 增量深审：agent-cli-session-TUI 会话目录/续接工具（2026-11-20）

已完成 yeelam-gordon/agent-cli-session-TUI 的固定版本源码与测试审查（MIT，v0.3.3，commit f81a993aa94071fd2150bd9cf4fd6710547b196e，0-star 快照）。它支持六种 CLI 本地会话目录的搜索与源端续接，但不做会话转格式/导入/导出；Enter 按原 provider、原 session ID、原 cwd 调用其 CLI。其 SessionView 元数据和 groups.json 是目录/平面分组，不包含 Projects/Sections/branch/task 图或附件恢复。

隐私门：默认 remote grouping 会在初次发现后自动发送代表性 session 的标题和工作目录 URI 到 Microsoft-hosted endpoint；它不发送 transcript/summary/provider session ID，现有 group name 需另外 opt-in。若只作本地源端发现，首次扫描前必须把 engine 配为 wordmatch，并且这不是本地 AI 模型。cargo +stable test --lib：220 passed、1 ignored（live remote test）；cargo +stable test --no-run 编译六个生命周期集成测试，但没有用真实 session 运行。结论：可作为只读发现/续接 UX 参考，不是本项目的迁移目标或跨 Harness writer。

### Candidate-screen result — MethodoxTech history browser
Reviewed as a useful local catalog/export UX reference, not a cross-Harness migrator or Cloud/API-Key writer. Its local-only design is useful for offline inspection, but the Markdown output is not a lossless session transfer; keep parent graph, image, token, Project/Section, and restore-writer gaps in the adapter matrix.

### Candidate-screen result — ai-agent-skills
Adopt as a partial reference for a standalone Skill-library/target-path adapter only. The 12 explicit agent-root mappings and global/project scopes are useful; --all writes only both generic scopes. It does not address ChatGPT/Codex Projects, session graphs, MCP/plugins, memory, artifacts, or scheduled tasks. Keep its 225/228 test result and 4.3.2 release-doc/catalog drift visible in the candidate scorecard.

### Candidate-screen result — purple MCP server
Keep as an adjacent security-pattern reference for the separate MCP-adapter layer, not as a cross-Harness migration engine. Its default stdio client config and read-only/audit options inform policy mapping, but it has no Projects/Sections/Session import; direct CLI MCP is writable unless --read-only is supplied, and its documented provider token files are plaintext.

### Candidate-screen result — Dutis MCP transaction design
Use as a high-value security pattern for any Nexus write adapter: deny writes by default, require a fresh plan digest plus explicit approval, persist rollback state and audit, and verify after mutation. Do not classify the repository as a chat/session importer. MIT metadata is declared but there is no standalone LICENSE file; do not adopt as a dependency until license evidence is clarified.

### 增量深审：MaazzAlii/context-saver-extension（2026-11-20）

已固定审查原始 303 个 GitHub 候选中的 `MaazzAlii/context-saver-extension`（commit `2e46bc79b266089a67ccc0c61d32f6cfce5a8f7e`）。它是 DOM 抓取 + 本地保存 + 手动复制 prompt 的 Chrome 扩展，不是 ChatGPT/Codex Project/Section/Session 导入器，也不是 Cloud/API-Key 原生 writer。可选总结会把捕获文本发往 Mistral；代码目前只见 Mistral 请求，manifest 的 Anthropic host 权限未在请求路径使用。抓取受 150 步上限约束，但有消息时无论是否到顶都会报告成功；保存结构最多 20 条，且摘要未实际写回保存记录。无独立 LICENSE、测试或构建流程；3 个 JavaScript 语法检查和 manifest JSON 解析通过。结论：仅作低价值的手动交接 UX 对照，不作为依赖或迁移适配器。详见 `RESEARCH.md`。

### 增量深审：laohu-aiskills/agent-session-vault（2026-11-20）

固定审查 MIT 项目 laohu-aiskills/agent-session-vault，commit 8f46611c7a6b6ae2fc916f45888ca69f15fc4157。它是本地多 Agent 会话目录、原始文件备份与恢复工具，解析器覆盖 Codex CLI 等本地格式，但没有 ChatGPT parser/Projects/Sections，也没有 Claude Cloud/API-Key writer；跨 Agent 默认只迁文本消息并报告 loss，不保留分支关系或更新目标索引。其 provider registry、WAL/SHM + hash 原始备份和显式 dry-run/apply/overwrite 门值得参考。合成路径审计则证实篡改 manifest 中的 ../escaped.txt 可在 --apply --yes --verify 下写到当前工作目录父层，且 --target 不会把此相对路径限制在目标家目录；未读取真实本地会话。README 的 verify 测试会索引调用者 HOME 的真实会话，故没有运行；静态解析 22 个 JS 文件通过。Nexus Phase 4 必须增加非可信 manifest 路径穿越、symlink、路径别名和 target-root containment 的反例测试；SQLite 活库快照还需验证 WAL/SHM 一致性，不能只检验归档内哈希。详见 RESEARCH.md。

### 增量深审：llxgdtop/Agent-Session-Migration（2026-11-20）

固定审查 Apache-2.0 项目 llxgdtop/Agent-Session-Migration（commit 72263bfbcbf3a010c99ad8f1ed3242fd3a66add5）。它支持 Claude Code、Codex CLI、ZCode 三者间本地文件/数据库互迁，适合作为目标 writer、schema guard、确定性测试和人工可读 resume 命令参考；但没有 ChatGPT 源、Projects/Sections、Cloud/API-Key writer 或 Skills/MCP/plugins/memory/schedules。其 IR 是扁平消息序列，分支/sidechain 被丢弃，reasoning/tool calls/results 被压成有截断上限的文本，图片/文件与 token/cost 不在 IR。两项隔离合成测试分别复现了 ZCode 第二个数据库写失败后 CLI 库仍已提交，以及活跃 WAL 中的已提交行未出现在单文件备份中。cargo test --workspace：95 项通过；标准 clippy 有 2 个 warning，开启 -D warnings 退出 101。详见 RESEARCH.md；Nexus 必须将跨库原子性、WAL-aware rollback、模型/权限 provenance、结构化事件损失与 branch/asset completeness 纳入验收。


### 增量深审：YURIBEDRAN/rubi 跨 Harness 记忆层（2026-11-20）

固定审查 MIT 项目 YURIBEDRAN/rubi，main 与本次 checkout 均为 commit `6780b453a1f8587b42bec318e55b912e13b4ca5e`（版本 0.6.0；Node >=18），本机 `npm test` 17 项全过。它是高价值的共享 Markdown 项目记忆/MCP/hooks 参考，但不是会话迁移器：没有 ChatGPT Projects/Sections 源或 Claude Cloud/API-Key 会话 writer；PreCompact 仅保存截断的 Claude Code 文字摘录，忽略 sidechain 与非文本内容，没有 session/fork/subagent 图。大多数目标 harness 依赖 MCP + 模型遵循说明，不等于原生自动迁移；claude.ai/mobile 仍被标为实验且未验证。仅用临时合成数据复现：假 token 无自动脱敏写入 Markdown，以及 `.rubi` 内 symlink 可读到 memory root 外文件。保留为 memory-plane/adapter-wiring 参考；Nexus 的记忆导入/读取必须先有确定性脱敏、realpath containment、显式损失报告，且必须与可回放原始会话分离。完整源码/测试/安全结论见 `RESEARCH.md`。

### 增量深审：luckeyfaraday/athena-code 跨 Agent 会话搜索（2026-11-20）

固定审查 MIT 项目 luckeyfaraday/athena-code，当前 main 与本次干净 checkout 均为 63e5143d8122343fda0130e728ddd4215bd4edb1；GitHub 页面显示 27 stars / 3 forks，最新可见 release 为 v0.5.0（2026-06-24）。本机使用隔离 HOME/TMPDIR 运行 README 测试：98 passed、1 个可选 sessions-search oracle skipped、0 failed。它是 OpenCode fork，提供全局/项目 Markdown-like 记忆、局部 SQLite FTS 会话检索、Claude Code/Codex/OpenCode/Hermes 的原生 CLI resume；但不是会话转换器：执行 scanner 未找到 ChatGPT parser，更没有 Projects/Sections、父子/分支图、附件/结构化工具调用或 Claude Cloud/API-Key writer。临时合成测试确认 sessions.db 会原样保存假 token；session_index 也没有源会话删除/保留周期机制。另有默认 permissionless 工具授权，需视为高风险产品默认。保留为本机历史搜索、source-native resume 和 memory/index 分层参考；Nexus 不得将 FTS row 当规范档案或将 CLI resume 当迁移。完整 source/test 与兼容性细节见 RESEARCH.md。

### 增量深审：xtermium 跨平台桌面 session manager（2026-11-20）

固定审查 Apache-2.0 项目 xtermium/xtermium，main 当前 commit f7c55e017128615676573716ab66bac5b56f9902（2026-11-18），GitHub 最新可见 release v0.10.0（2026-11-14），另有 11-15 nightly。它是 Windows/Linux/macOS 的 Tauri 终端和连接会话管理器，包含 Claude Code、Codex、omp 的本地历史列表、source-native resume、MCP 控制与 Xtermium 自身 workspace/folder/config。其连接 Session/workspace 与 AI Transcript history 是两套概念：MobaXterm/OpenSSH 导入导出仅涉及 SSH/RDP/VNC 等连接配置；AI history 仅展示元数据并重新运行原 CLI，不解析/转写完整对话，也没有 ChatGPT Projects/Sections 或 Claude Cloud/API-Key writer。Agent history 删除会删掉源工具 transcript；MCP 可操作已认证终端，因此是高权限远程控制面。目标用户仍可借鉴本机多 agent workspace/历史浏览 UX，但不能作为迁移引擎。针对 Claude/Codex 两项 Rust 单测通过；omp 没有对等历史解析测试，完整桌面测试未运行。详见 RESEARCH.md。


### 增量深审：leox255/termem（2026-11-20）

固定审查 main commit a7901bc3a3fed1bcaac4860002e9b31531a5e594（v0.6.3）。termem 将 Claude Code、Codex CLI、Gemini CLI、OpenCode 与 shell history 做本地 SQLite 搜索/MCP recall，并用原 CLI resume；它不是转换器，没有 ChatGPT Project/Section parser，也没有 Claude Cloud/API-Key writer。规范对象只有本地 session 元数据与按提供方提取的 role/text/optional timestamp；图像/文件、结构化 tool call/result、usage/cost、task/fork/subagent 关系与用户编辑/打断事件不能由它恢复。OpenCode 列表仅取 parent_id IS NULL。SQLite FTS 会保存每个 session 首批最多 400 条、总计最多 200,000 字符的 transcript text；应按敏感副本处理，不可与规范档案混为一体。隔离 cargo test --locked 为 56 passed、0 failed；测试没有扫描真实 HOME。仅作为本地记忆检索、MCP 分页和跨 harness wrapper 的设计参考，不纳入迁移依赖。Cargo/README 声称 MIT，但固定 checkout 缺少 LICENSE 文件，源代码复用前还须核实授权。完整审查见 RESEARCH.md。


### 增量深审：zavudev/leon（2026-11-20）

固定审查 Apache-2.0 项目 zavudev/leon，main commit 1fe87724d62a5d29f40982daecd13392a977872b，GitHub 最新 release 页面为 0.16.2（2026-11-05）。它是带机器/项目/worktree/会话树的跨平台桌面 Agent 编排器，本地历史 importer 只覆盖 Claude Code、Codex CLI、OpenCode；其“统一聊天界面”实验不等于 ChatGPT/Claude Cloud session 迁移。规范 history row 保存 agent/external id/machine/account/cwd/project/title/model/times/text messages 及 per-model/day token counts，但无成本字段、附件引用或通用 session 父子/fork/subagent graph。Claude 图片、tool result、sidechain/meta 和 subagent transcript text 会丢；Codex tool results 丢且 fork parent link 不进 IR；OpenCode children/non-text parts 不进顶层 history。优点是 provider-specific HistorySource、幂等指纹/cursor、OpenCode read-only、诊断 skip/error 和 workspace UX，可作为本机导入器/项目树的设计参考，不能作为规范迁移档案或 Cloud/API-Key writer。Focused cargo test --locked -p leon-history 为 217 passed、0 failed；全桌面应用测试未运行，测试仅用 fixture/temp store。Windows/Linux 构建虽在 README 中列出，但 README 说明尚未由人验证。详情见 RESEARCH.md。


### 增量深审：itaywol/adeptability（2026-11-20）

固定审查 MIT 项目 itaywol/adeptability，main 与本次 checkout 同为 c5b1b81b2e0ae71bd8afeeade28eaea6f8fd1bf5；GitHub 页面显示 9 stars / 0 forks，最新可见 release 为 v1.10.0（2026-07-24）。其 CLI 的 harness list 验证出 56 个 renderer registry 项：Claude Code、Cursor、OpenCode、Codex、Copilot 具专门 renderer，其余主要走通用 per-skill 文件适配。它是 Skills 与 subagent portable schema 的强参考，特别是 canonical sidecars、hash drift、sync-from、library 与 agent lint；但不是 session/project migration 工具，也没有 ChatGPT Projects/Sections、MCP/plugin 配置 writer 或 API-Key Cloud conversation target。Sidecar、activation、model hint、harness override 和大小预算存在明确损失：Codex/Copilot 聚合、超限截断/丢弃；Copilot跳过 agent/manual skill；Cursor/Codex/Copilot 不带 canonical sidecar；OpenCode不表达 activation；import 不恢复 harness overrides。loop add 只是生成 discovery skill、reviewer agent 和可选 GitHub Actions cron skeleton，不迁移既有定时任务。全仓库 go test -count=1 ./... 在临时 Go 1.25.14 环境通过；另有隔离 symlink probe 证实项目 .claude 指向仓库外时 sync 可在仓库外创建/替换输出路径。它适合作为 Nexus Skills/Agents 适配器参考，安全落地前需要 realpath containment；不应作为跨世纪会话/项目记忆图的中心引擎。完整兼容矩阵、loss ledger 与 probe 记录见 RESEARCH.md。


### 增量深审：AblazeGHR/pan（2026-11-20）

固定审查 AGPL-3.0 项目 AblazeGHR/pan，main commit 74f475250b54959aaab13ffa83be820cada68a32，GitHub 页面显示 8 stars / 1 fork。它是有参考价值的本地 Session/Workspace/Jobs/MCP 多 Agent 管理器，并提供 CBC/Kimi/OpenCode/Codex CLI/DSH native-history import；Claude provider 已注册，但当前 ImportModal 未列出。它把外部日志导入 Pan 自己的 Session，而不是导入 ChatGPT web/Codex Projects 或 Cloud/API-Key会话。Pan 有 Workspace membership 与 managed_by/managed 子会话关系，但导入路由不会保留通用源 fork/parent/task 图；Workspace 只对 Pan 组织 Sessions，不移动工作目录。DSH adapter 读压缩事件日志，筛出提交的 user/assistant 文本、reasoning、tool-call 摘要与 raw usage；运行时 context/skill reminder、未提交 retry attempt、tool/result事件及二进制 assets 未作为完整规范记录保留。Reimport 使用 native snapshot、稳定 Pan message IDs、HMAC 确认和冲突报告，值得借鉴。Pan Jobs/MCP/插件是 Pan 自身配置，不代表能迁移 ChatGPT schedules 或源 MCP。README 明确 Memory/Character 当前暂停；API 默认无认证且仅默认绑定 loopback，修改 PAN_HOST 会对外暴露无认证 API，需严格隔离；AGPL-3.0 仅作研究参考。测试：4 个 import/DSH/reimport 文件 82 项通过；包含独立 terminal-native-control 测试的宽集合有 18 项因本机 Darwin 不支持 terminal.native 而返回 501，故不宣称全仓库通过。详见 RESEARCH.md。

### 增量候选审查：termide/termide（本地 Agent Harness；非迁移器，2026-11-20）

固定审查 MIT 项目 `termide/termide`：干净 main HEAD `5c3eec4915380da479c2bb03f6843342e7a9e17d`，与当时远端 main 一致；GitHub 页面为 189 stars / 10 forks，v0.50.0 于 2026-11-16 发布。本轮隔离执行 Termide session 41 项、project 41 项、Markdown exporter 4 项测试，均通过；未运行全 workspace suite，未访问真实会话、API Key 或 provider。

它是终端 IDE + 本地/托管模型 Agent workbench，并可用 ACP 运行 Claude Code、Codex、Gemini CLI；不是 ChatGPT 导入器。项目按本地根路径和哈希组织，`project.toml` 保存布局与 panel groups；AI session JSONL 存在独立 `ai/sessions/<panel directory>` 路径，没有 ChatGPT Section Group。原生 append-only JSONL 含 24 种事件、entry `parent_id` 链、typed message/tool/result/token/timing 数据；会话 fork 复制当前分支并记录 copied count，但不保留明确的 fork source session ID。Delegated task 使用独立 SessionParent，ACP native session 使用 external session reference，三者不可合并成单一父子边。

Termide 的 “Save chat as Markdown” 只输出当前分支用户/助手文本，丢弃 reasoning、tool calls/results 和 notices。Skills 可沿用 `SKILL.md`，MCP 可读 `mcp.toml` 与一部分 `.mcp.json`；OAuth/API secrets 保留在目标本地，不随包迁移。`/loop`/`/goal` 是绑定 session 的循环工作，不是通用、可直接迁移的定时任务。分类为 `reviewed_local_event_log_harness_not_migrator`：借鉴其事件日志、Project/layout 分离、ACP resume 与资源适配边界，不作为 Nexus canonical archive 或 ChatGPT/Codex→Claude Cloud API-Key writer。完整证据见 `RESEARCH.md` / `COMPATIBILITY.md`。

### 增量候选审查：bobmatnyc/claude-mpm（Claude Code 会话控制/分析工具；非跨 Harness 迁移器，2026-11-20）

固定审查 main `25203d34f20982c5871574b5059949ab85ab5a6b`。它是 Claude Code CLI 的多 Agent 编排器，支持 Skills/MCP、resume/fork、一个 MCP 会话控制服务器、checkpoint、resume summary 和可选 transcript 分析。重要结论是“session”在其代码中并非一个统一产物：`active_sessions.json` 主要是 Session ID/上下文/时间/agent-use 元数据；`session pause --export` 写 project-local JSON/Markdown 检查点；ResumeLogGenerator 写结构化摘要；可选 EventAggregator 只保存它捕获到的事件投影；另一套 parser 读取 Claude Code native JSONL 及 subagent JSONL 生成报告。只有底层 Claude Code 的原生 Session ID 可用于 `--resume`/`--fork-session`，这不是导入 ChatGPT/Codex 历史，也不生成 Claude.ai Cloud session。

Transcript parser 默认脱敏，可恢复文本/部分 tool usage、token/cost 并按时间近似关联 subagent；但忽略 image/non-text 和 sidechain，tool-result output 在 report 中截断为 500 字符，父子关联可能 ambiguous。人工暂停快照的默认 conversation summary 是占位/人工 message，token usage 默认值为 0。MCP `aggregate export` 可导出 MPM 自己捕获的 JSON/summary/events，但依赖本地 monitor 已在采集，且不是原生 transcript 的逐记录副本。合成 probe 还复现 EventAggregator 的 50-session 内存上限会不落盘地驱逐最旧未完成记录。

Skills、MCP、插件属于 Claude Code 专有接入面；`claude-mpm migrate` 是内部配置/二进制重命名升级，Huey cron 只做通知/队列 housekeeping。Cloud Sled 是 README 的未来路线，SDK 模式仍标为实验。HTTP MCP Session Server 默认 loopback，但 ngrok 可暴露、当前审查的 route 中无认证。根 LICENSE/pyproject 为 Elastic-2.0，NPM wrapper metadata 却称 MIT；Github API 也标记 Other，因此保持 `NOASSERTION` 并排除代码依赖。两组隔离定向测试合计 407 passed、1 skipped、3 warnings；未运行全仓测试、真实 Claude CLI 或任何 provider。详见 `RESEARCH.md`。

### 增量候选审查：rolecraft-sh/rolecraft（Skills/MCP 资源层，不是 Session 迁移器，2026-11-20）

- 固定审查快照：MIT，v2.6.2，commit `edfd87eed27288fa9e29521eb90e946130075842`；manifest 计算为 90 个 agent（65 verified）与 9 个 MCP target。
- 结论：可作为 Nexus 的 Skills/MCP/config adapter 参考；不能承载 ChatGPT/Codex Project、Section 或 Session 的层级与时间线，也不能当作会话迁移方案。
- 安全/保真闸门：RoleCraft `install` 会扫描技能声明的 MCP；`setup` 只把声明随结果返回。无可扫描内容时当前代码将 MCP 标为 `unscanned_source`/REVIEW，install 需 `--yes`，CI 拒绝；README 仍写成 SAFE，须记录为文档漂移。Profile export 未脱敏环境变量；profile serializer 丢弃它验证过的 `projectOverrides` 和 `localOverrides`。实际合成探针仅使用假 token。
- Nexus 用途：只接入资源/配置映射；规范 session graph、events、附件、schedule 和 provenance 继续由 Nexus 自己维护。API Key/env 字段默认 redacted，未经用户授权不得写入目标。
- 验证：安全/安装/setup/CI/profile 定向 Node 测试 195 pass / 0 fail；同一仓库此前完整 npm suite 1535 + release-prep 4 均通过。审查证据与 synthetic probe 记录见 `docs/research/evidence/rolecraft-codegraph-review-2026-11-20.txt`。
### 增量候选审查：vanillagreencom/kendex（资源适配器强，Session 迁移不是其边界，2026-11-20）

- 审查快照：MIT，版本 1.22.2；release tag v1.22.2 于 2026-11-18，主分支在 2026-11-20 已到 260b6492363b47d84ba1f893c5223120ad6a9f4a。
- 资源覆盖：8 个 coding harness；按 harness × 资源类型 × global/project scope 的 capability table 区分 managed/read-only/unsupported，适合作为 Nexus 资源 adapter 和 provenance/diff-preview 的参考。
- Session 边界：项目核心并非跨 Harness transcript importer。Pi 附属扩展可浏览原生 Pi sessions 并列相关树；Pi bridge 只读取 live/recent event stream；Pi QOL 将 scheduled prompts 写入 Pi session branch；Pi-Claude bridge 只在 Pi 与已有 Claude Code session 间核验并恢复一个 cursor/fingerprint marker。
- 目标差距：没有证据表明它能导入 ChatGPT/Codex 的 Project/Section/Session graph、附件或 token traces；Pi Claude bridge 要求 Claude Code 登录账号，不是用户要求的 standalone Cloud API Key workflow。
- Nexus 决策：借鉴 capability matrix 和 resource package adapter；Session/Project/Section/Event/Artifact/Schedule canonical graph 仍由 Nexus 管理，Pi state adapter 作为可选单一 harness adapter。
- 测试状态：本轮源代码/文档审查；Bun 缺失，Rust toolchain 1.95.0 低于 Cargo 声明的 1.96，未执行 Kendex/extension 测试。不要把未执行描述成通过。
### 增量候选审查：lasoons/AgentSkillsManager（Skills-only VS Code 插件；非 Session 迁移器，2026-11-20）

- 固定审查快照：MIT，package 0.6.0，main SHA f603f685e46d53bbf538f0c3014545255ee50e4c，最后提交日期为 2026-01-17；GitHub 当时未列出 releases。
- 能力：浏览 Git skill repositories 与 claude-plugins.dev 的 Skills catalog，并装入当前 workspace 的 IDE-specific skills 目录；另可显示部分本地/个人 Skills 目录。
- 不支持：ChatGPT/Codex Project/Section/Session 图、会话消息/修改/打断、附件、token 记录、MCP/插件迁移或通用 schedule。
- 安全闸门：cloud ZIP 使用 adm-zip 0.5.16。npm audit 对生产依赖给出 high；GitHub Advisory 记录 crafted ZIP 可导致多 GB 内存分配/进程 DoS。代码还没有应用级下载大小、超时、完整性校验；替换时先删旧目录再拷贝。没有发现自动化测试。
- 决策：仅作为 IDE Skills 目录识别的低优先级参考，不作为 Nexus source/target adapter。Nexus 应对任何云端 skill ZIP 做隔离、配额、哈希与扫描，再原子写入。

### 增量候选审查：skills-compat-manager（资源兼容检查，不是 Session 迁移器，2026-11-20）

- 审查快照：MIT、Python >=3.11、包元数据 0.1.0/Alpha；commit `8be1357e06a350cf13eb670b4d7ff24e4fc54bae` 与远端 HEAD 一致，检出干净。GitHub 页面当日快照 84 stars/0 forks/45 commits（仅作时点元数据）。
- 价值：用 `COMPAT.yaml` 表达 packages/system tools/external services/runtime capabilities 并以 MCP 注入 preflight 状态；只可作为 Nexus 资源兼容 adapter 的设计参考。它不迁移 ChatGPT/Codex Project/Section/Session、分支/子任务、附件、token/tool timeline 或 schedules；不能当作本项目所需的会话转换器。
- 闸门：Python 3.12 隔离环境解析为 `fastmcp 4.2.3` + `mcp 2.3.0` 后，MCP server import 退出 1；全测试在 `test_mcp_server.py` 收集阶段退出 2，排除该文件后的 39 项测试通过。官方 SDK v2 已将 `FastMCP` 改名并移动为 `MCPServer`。另有 shell=True repair gate 误收 arbitrary command chaining 的隔离 AST 测试；未执行命令。重复 basename 的两个合成技能只枚举出一个。
- 当前决定：列为 `RESOURCE_COMPAT_REFERENCE_ONLY`；不要直接依赖或开放自动修复。后续设计可以借鉴四维 Delta，但必须有 source-qualified identity、只读预览、可验证 API-key validity、版本锁定/兼容矩阵、shell-free argv execution 及 lossless round-trip tests。完整证据见 `docs/research/evidence/skills-compat-manager-review-2026-11-20.txt`；截至此增量审查，GitHub 候选库 303 个中已人工复核 32 个，271 个仍待复核。

### 增量候选审查：itlackey/akm（有本地 Session 读取/记忆提取；不是会话迁移器，2026-11-20）

- 当前审查快照：main `ec8318eabc6f15b912b3fe4f86b17130c0e3746f`（0.10.261129）；最新开发/发布线 `release/0.11.0` `fce58373e7cf373cd07f57ec854c31268697e4d9`（0.11.0-beta.0，合并 0.10.261130-beta.6）；MPL-2.0。GitHub release 页面 2026-11-20 列出 `0.10.261130-beta.6` 为 prerelease；与 `0.11.0` release branch 不混称。
- 价值：跨 harness 的本地知识/能力库；读 Claude Code、Codex、OpenCode 三种 Session logs；可用 path-based Projects 和本机 Tasks scheduler；适合做 Nexus 的 source-adapter、content-hash 抽取幂等、read-only DB snapshot 与 pre-filter 参考。
- 保真边界：`proposal extract` 是 LLM 提取 insights 并形成 AKM proposal；`sessions/**` 只有总结/主题和原始本机 `log_path`，不是原 transcript。SessionEvent 无 Project/SectionGroup/parent/fork/interrupt/media/token 字段；Claude 子任务合并，Codex 内部 rollout 忽略，OpenCode v2 只列 top-level。ChatGPT Session/Projects/Section Group importer 和 Claude Cloud API-Key 对话 writer 未发现。
- Cloud / resource 边界：AKM connections 可用于请求 OpenAI-compatible LLM endpoint（API key 是 env reference），但其用途为 AKM 推理，不是云端会话目标存储。文档明确将 AKM 定位为 MCP/native Skills 的补充；`akm-plugins` 是独立 repo，需单独评审。Task v4/cron/launchd/schtasks 仅解决本机排程，不迁移 ChatGPT Scheduled Tasks。
- 质量闸门：最新 `release/0.11.0` 分支 Bun 1.4.5 定向 reader/pre-filter/summary/SQLite 测试 81 pass；但项目路径集成测试 0/3 pass。`resolveProposalQueueTarget` 对 `/var/folders/...` 与 `safeRealpath` 后 `/private/var/folders/...` 的路径未规范化比较；直接合成探针和项目测试均复现 `No bundle owns proposal queue`。不要在修复/回归前信任此 Apple-host extraction path。完整来源、退出码和 literal outputs 见 `docs/research/evidence/akm-review-2026-11-20.txt`。
- 结论：分类 `HIGH_VALUE_LOCAL_SESSION_INGESTION_REFERENCE_NOT_MIGRATOR`; 303 项清单中人工复核 33 项，270 项待审。正确用户目标名仍为 **Destruction Era**，并未因 AKM 支持 Claude Code logs 而证明其 Cloud 历史可迁移。

### 增量候选审查：beautyfree/skiller（跨 Agent Skills 桌面管理器，非 Session 迁移器，2026-11-20）

- 审查快照：main `019d1ab13ecbb194dc4b6052f22e1db249f9d932`，版本 0.3.8；GitHub 最新 release 2026-10-23。Electron 应用支持 macOS/Windows/Linux；本地有 49 份 agent TOML target 配置。
- 价值：共享 `~/.agents/skills`、项目级 `.agents/skills`、跨 agent installation、dotagents sync manifest、版本/来源 hash、冲突预览、Skills CLI v3 lock 的只读兼容，可参考 Nexus 的 Skills adapter/UI。
- 范围边界：`ProjectEntryJson` 只含 path/name/group，`ProjectSkillJson` 只含技能 metadata/path；SyncManifest 仅含 profile、agent policy 与 Skills。未找到 ChatGPT Session/Section/附件/分支/Token/MCP/plugin/schedule 迁移模型或目标会话 writer。项目分组是技能目录的 UI 组织，不是 ChatGPT 的 Project / Section Group。
- 法律闸门：LICENSE 是 SUL-1.0，限定内部商业用途或个人/非商业使用，向外分发仅限免费非商业；不适合直接派生为付费/商业发行的 Nexus 产品，除非另获授权。
- 验证：在隔离 Bun 1.4.5 下 `bun install --frozen-lockfile --ignore-scripts` 成功；选定 Project/sync/Skills CLI 测试 45 pass / 0 fail / 206 assertions。测试不覆盖 Session 迁移。证据：`docs/research/evidence/skiller-review-2026-11-20.txt`。
- 结论：`SKILLS_PLANE_REFERENCE_ONLY_SUL_REUSE_RESTRICTED_NO_SESSION_MIGRATION`；当前 303 项候选库中人工复核 34 项，269 项待审。标准迁移目标仍是 **Destruction Era**。

### 增量候选审查：jacopobonomi/venv_manager（MCP/Python 环境状态，非会话迁移，2026-11-20）

- 固定 `HEAD=fd561c3501cf031aba0b589bde05dd147fe22f30`，与远端 HEAD 匹配；MIT；Go 1.24.2。官方 GitHub Actions 的该 commit CI #22 于 2026-08-24 成功。当前 Mac 没有 Go，`go version` 返回 `No such file or directory`，所以没有本地 Go 测试结论。
- 可用能力：本地 Python venv 的跨 Agent 共享 CLI/TUI/MCP；包清单、pip-freeze snapshot/diff/rollback；环境登记表包含路径/tag/创建/最后使用 metadata。它的 Project 只是 venv 到文件系统路径的可选关联，不是 ChatGPT Project / Section Group / Session。
- 不包含：会话/消息图、聊天树/子任务/分支、附件、token/tool 历史、Cloud API-Key 会话写入、Skills/MCP 配置导入或定时任务迁移。
- 代码策略复核：MCP 默认 `safe`；危险/执行工具需调用方传 `confirm: true`（不是独立的人类确认渠道）；`exec_ephemeral` 带 `sandbox: true` 虽通过 policy，但 handler 当前拒绝该 MCP 沙箱路径。故仅适合作为可选“依赖环境”子资源参考，不计作 session 迁移能力。
- 证据：`docs/research/evidence/venv-manager-review-2026-11-20.txt`。本轮后 303 个候选中已复核 35 个，268 个未复核；更正后的具体目标名称仍是 **Destruction Era**。

### 增量候选审查：kirodotdev-labs/config-control-kiro（Kiro 本地配置与会话元数据，不是跨平台迁移器，2026-11-20）

- 固定 `HEAD=580d2df3f2edafe4d7b979fbd249901cc5ddf346`，远端 HEAD 匹配；`v3.0.0`，Apache-2.0。官方 Build and Test #41 对该 commit 成功；CodeQL #67 于 2026-11-13 成功。
- 可借鉴：Kiro Global / Workspace 的资源分层；本地 Session 元数据包含 workspace、engine、agent/model、user-message count、usage/context、subagent `parentSessionId` 与 tangent/rewind `createdReason` / `BranchOf`。项目也能在 Kiro ACP 上管理其专属 Memory type/scope。
- 关键损失：session reader 不读取 prompts、replies、tool results 或 attachments；resume 只是执行 `kiro-cli --resume-id`。Kiro 自带本地 V3 `/chat save` 与 `/chat load`，但 Config Control 本身没有跨 harness session 导入导出。官方文档说 Cloud session archive 不支持 save/load；它是否能列出所有 Cloud 会话没有在本轮实时账户上验证，因此 Cloud 覆盖仍标未验证。
- 本地验证：`go test -race ./internal/... ./tools/...` 全部列出的包通过；前端 51/51；Vite build 通过但主 JS chunk 702 KB；通过官方 npm registry 的 audit 为 0 vulnerabilities。默认 npm 镜像的 audit endpoint 不支持请求，换 registry 后成功。
- 决策：保留为 Kiro source/config/memory/session-metadata 建模参考，不计入 ChatGPT Projects/Sections 或 Claude Cloud 会话迁移覆盖。证据：`docs/research/evidence/config-control-kiro-review-2026-11-20.txt`。候选库已审 **36/303**，待审 **267**；用户目标名称仍规范为 **Destruction Era**。


### 增量候选审查：danieljustus/symaira-vault（API 凭据保险库与 MCP 安全，不是会话记忆库，2026-11-20）

- 固定 main `HEAD=3ae37916b834e3fb81caddc038f4022967411ef8`，远端 HEAD 匹配；该 commit 仅更新 `docs/product-boundaries.md`。最新发布版为 `v0.25.0`（Apache-2.0，2026-11-16），main 有 10 个后续提交；项目仍 pre-1.0。
- 实际可借鉴的范围：加密 API 凭据/密码/TOTP/通行密钥存储、OnePassword/Bitwarden/pass/CSV/CXF 凭据导入、按 MCP agent 的路径/工具 allowlist 与 scoped token、人类审批、服务端 API key 解析。
- 不具备：聊天 Session transcript/event、Project/Section Group、分支/子任务关系、图像/附件、token usage 历史或 Cloud session API-Key 导入。README 的 Session 指的是 vault unlock 缓存；文件夹路径只是 secret namespace。
- 本地全 workspace `cargo test --workspace --all-features --locked`（memory keyring + `/tmp` target）退出 0；`cargo fmt --all -- --check` 与 strict Clippy 全 targets 退出 0。GitHub Actions 对父 commit 的最新失败来自 macOS ARM runner 无法分配，非源码断言；main HEAD 是其 docs-only 子 commit。
- 决策：保留为可选安全/密钥 provider 参考，不纳入 session importer 核心。迁移载荷默认只能承载 secret reference，不能把解密值、bearer token 或账户认证复制过去。证据：`docs/research/evidence/symaira-vault-review-2026-11-20.txt`。总候选已审 **37/303**，待审 **266**；标准对象名仍为 **Destruction Era**。


### Incremental candidate review: pwnera/artbucket (2026-11-20)

- Classification: **adjacent MCP/project-scope and reversible asset-import reference; not a session migrator**. Pinned main `84e34122c7eff9d401bef48edd20d21000464087`; AGPL-3.0; v2.8.0 (2026-10-15). The upstream commit notes Artbucket Cloud has closed; self-hosted app remains.
- Useful pattern: frozen API/MCP schemas, project-bound consent/scopes, explicit `project` selector, migration preview → human review → apply → undo; name losses for custom metadata, links and rights.
- Exclusion: organization/Project/Collections/brand-page sections are DAM hierarchy, not ChatGPT Project/Section Group. Assistant chat list/turn UI delegates to external `ASSISTANT_URL`; app only stores current chat ID in browser sessionStorage, and this repository has no chat database, transcript import/export or Cloud session writer. Artbucket API keys are not Cloud model API keys.
- Local checks: `pnpm test` 734 pass/0 fail; typecheck, lint, `contract:check` exit 0. DB tests not run because Docker is unavailable and the harness needs a Postgres `DATABASE_URL`. Evidence: `docs/research/evidence/artbucket-review-2026-11-20.txt`.
- Candidate inventory now **38/303 reviewed / 265 unreviewed**. Exact next unreviewed registry row is `yeasy/ask`. The working project remains **Nexus Memory**, with the requested product name corrected to **Destruction Era**.


### Incremental candidate review: yeasy/ask (2026-11-20)

- Classification: **high-value Skills-plane package-manager reference; not a session/Cloud migrator**. MIT; main HEAD `987829750053dd5589b32f301d992d6fc8147b1a` (Aug 31), 27 stars / 4 forks capture; latest published v1.11.0 (July 12).
- Useful: 19 explicit agent skill paths; global/project scope; `ask.lock` pins source commit; HTTPS sparse clone; symlink/copy fallback; 12+ rule static skill scanner; local Wails/web app with desktop packages for Mac/Windows/Linux.
- Gaps: no MCP config / plugin / session, Project / Section Group / transcript, attachment, memory or schedule importer; file copy is not semantic conversion. Its Cloud/model API key behavior is nonexistent.
- Quality/caveat: exact-head upstream tests pass on Linux+macOS and separate Lint/Format workflows pass. Combined CI workflow fails on golangci action v6 vs requested v2.1 config. A previous-head security workflow found Go standard-library and dependency advisories; current main still declares Go 1.26.5, and a current-head govulncheck was not observed. No local Go test due missing Go toolchain. Evidence: `docs/research/evidence/yeasy-ask-review-2026-11-20.txt`.
- Candidate inventory: **39/303 reviewed / 264 unreviewed**, next `seed-forge/harness-ai-kit`. Canonical target name remains **Destruction Era**.


### Incremental candidate review: seed-forge/harness-ai-kit (2026-11-20)

- Classification: **strong adjacent Skills/asset-manifest/runtime materialization reference; not a session migrator**. Apache-2.0; main HEAD `43d6a659cb0d1b3409f8b0a98166f964bc067e7a` (Aug 28); 26 stars / 2 forks snapshot. Latest published GitHub/PyPI release observed: v0.2.0 (Aug 12), while main advertises 0.18.18.
- Useful: typed project manifest/lock for Skills, CLIs, plugins, hooks, subagents, MCPs and loops; checksummed source resolution; stage/sync; runtime profiles and scope-based installs. Main supports eight code runtimes; Skills are materialized in runtime-specific formats. DSH plugin installation is a separate DSH-only route.
- Gaps: manifest describes assets, not ChatGPT Project/Section/Session hierarchy; no messages/turns, branch/child graph, attachments, token/usage, schedules, or Cloud API-key chat writer. Workflow `LoopState` is not a chat transcript. Generic `.agents` asset placement is not proof that the target harness registers or activates that asset.
- Distribution check: PyPI 0.2.0 official wheel hash verified locally (`1fd3289...f765f`); static wheel scan found no conversation transcript importer/exporter. The exact-main CI public-release gate passed, but v0.18.18 PyPI publish run #33101008389 failed because its OIDC-scoped token was invalid for the project. Local release-gate tests passed 30/30; no full suite claimed.
- Evidence and exact outputs: `docs/research/evidence/harness-ai-kit-review-2026-11-20.txt`. Inventory now **40/303 reviewed / 263 unreviewed**; next exact unreviewed row is `24KaratAu/openhub`. The end-user scope still names **Destruction Era**.


### Incremental candidate review: 24KaratAu/openhub (2026-11-20)

- Classification: **adjacent Skills catalog/exporter; not a Projects/Sessions migrator**. MIT; pinned `eb8a50b01fea5b88d8e028dcd03cfe6ac7880d66`, latest release v0.2.0; GitHub snapshot 21 stars / 4 forks.
- Useful: local/global `SKILL.md` and OpenCode agent export targets; scans installed skills, checks source release versions, backs up old skill folders and rolls back failed updates. Action history only records repo install/export/update operations.
- Gaps: no chat/Project/Section/session model, conversation turns/branches/attachments, memory, scheduled tasks, MCP configuration or Claude/Cloud API-Key conversation writer. README host matrix is not backed by per-host discovery tests; “MCP server” is just a catalog tag/type and install delegates to `opencode get`.
- Quality: exact-HEAD upstream CI and release succeeded on Sep 27, but the local official `run_all_tests.py` command now fails one `test_quality_scorer` assertion because pushed-at freshness is computed against current UTC time. Tests delete `~/.cache/opencode-hub/repos.db`; this review set HOME to `/tmp`. Export overwrites same-slug files; installer uses a shell string from catalog slug; no exploit demonstrated.
- Evidence: `docs/research/evidence/24karatau-openhub-review-2026-11-20.txt`. Inventory now **41/303 reviewed / 262 unreviewed**; next exact unreviewed row is `xiaode-ai/nanofile-connector`. Canonical target remains **Destruction Era**.
- Evidence: `docs/research/evidence/nanofile-connector-review-2026-11-20.txt`. Inventory now **42/303 reviewed / 261 unreviewed**; next exact unreviewed row is `cbruyndoncx/obsidian-skills-manager`. `xiaode-ai/nanofile-connector` is retained as a Windows-local MCP/Skills/plugin-manifest reference only, not a session migrator.
- Evidence: `docs/research/evidence/obsidian-skills-manager-review-2026-11-20.txt`. Inventory now **43/303 reviewed / 260 unreviewed**; next exact unreviewed row is `superradcompany/tool-cli`. The Obsidian plugin is a lossy Skill library/export surface, not a project/session migrator; no license was identified.
- Evidence: `docs/research/evidence/tool-cli-review-2026-11-20.txt`. Inventory now **44/303 reviewed / 259 unreviewed**; next exact unreviewed row is `andrader/jup`. `superradcompany/tool-cli` is retained as an MCP package/host-adapter reference, not a session migrator.

### 增量深审：andrader/jup（2026-11-20）

- 定位：本地/GitHub Agent Skills 安装与同步器，属资源面参考，不是会话迁移器。审查了 `main` commit `2019ba873fb316d685d09c29bfe30b8c281af8bf`、Python 源码、测试与隔离运行；GitHub 元数据为 17 stars / 3 forks、`archived=false`、license `null`，仓库无 LICENSE 文件（更正上一次 dispatch 中“archived”的误标）。
- 可借鉴：source/layout/category/skill 名称/version 等 Skills lock 元数据，本地/全局 harness 目录映射，以及 link/copy sync。其 `skills_lock_session` 只管理 SkillsLock 文件读写，不是对话 Session。路径校验/遍历与符号链接测试有参考价值；但 sync 可能删除同名目标目录，Nexus 应加入冲突预览、备份与确认。
- 边界：无 Projects、Sections、对话 turns/events、父子/分叉、attachments、tokens、MCP/plugin 转移、memory/schedules、ChatGPT reader 或 Claude Desktop Chat/Cowork/Code、本地 Claude Code、托管 Cloud 的会话 writer。未发现 Skills lock 内容摘要；装入目录也不证明目标 Harness 已激活 Skill。
- 质量：隔离测试 95 passed；合成 local-source CLI 演示 3 个命令均为 exit 0，生成 `.agents/skills/demo-skill` 符号链接和 `skills.lock`，只覆盖 Skill 文件投影。
- Evidence：`docs/research/evidence/jup-review-2026-11-20.txt`。Inventory now **45/303 reviewed / 258 unreviewed**; next `ktreharrison/tkmd`。本轮目标端仍按用户确认纳入 Claude Desktop Chat、Cowork、Code 三种 mode，另含本地/自托管 Claude Code；Anthropic-hosted Cloud 仍分开记录。

### 增量深审：ktreharrison/tkmd（2026-11-20）

- 定位：本地 Markdown task manager + MCP server，包含**任务到 agent session ID 的引用/续接**，不包含会话 transcript 导入/导出。审查 main `14db41f865c2fd7c894d4b02638a24878c4e47a8`；Cargo v0.4.0，dual MIT OR Apache-2.0；GitHub snapshot 16 stars / 3 forks；最新 release v0.4.0 落后 main 3 commits。
- 可借鉴： task DAG、显式 local/global scope、Task 上的 latest session ID 与 agent→session 列表、任务事件日志、`tk u` 调回原生 agent CLI 的机制、人类 sign-off 和 eval 输入 hash pinning。session ID 只是来源 Harness 的引用，不是可跨 Harness 续接的会话内容。
- 边界：`project` 是字符串标签，`blocked_by`/`blocks` 是任务依赖；无 Project/Section/SectionGroup、主控/被控 Session 树、对话消息、工具输出、attachments、token 成本、ChatGPT reader、Claude Desktop Chat/Cowork/Code / 本地 Claude Code / hosted Cloud writer。MCP API 管理 task，不是 session transfer。
- 验证：隔离 `cargo test --locked` 126 passed / 0 failed / 2 ignored；`cargo check` 和 `cargo fmt --check` 通过；`cargo clippy -- -D warnings` 在 Rust 1.95 对 `src/store/doctor.rs:85` 报一个 lint 并以 101 退出。stub CLI 演示证明了 ID 的存储与 argv 派发，不证明真实 provider 可恢复。
- 安全边界：task eval 与用户配置的 on-done hook 可执行命令；迁移包应将其保留为 inert data，明确列出并经用户确认后才执行。不要自动运行导入的 session command。
- Evidence：`docs/research/evidence/tkmd-review-2026-11-20.txt`。本轮目标范围仍覆盖 Claude Desktop Chat、Cowork、Code 全部三种 mode，并单独研究本地/自托管 Claude Code 与 Anthropic-hosted Cloud。

### 增量深审：grimoire-rs/grimoire（2026-11-20）

- 定位：当前最强的 **Skills/Rules/Agents/MCP/plugin 资源资产面**候选之一：OCI digest 或 local-path hash、lockfile、每 Harness 格式化、冲突拒绝与 drift 状态、项目锁定资产导出 Claude/Codex plugin。Apache-2.0；main `5676c2c`，高于最新 v0.16.1 tag 一提交。
- 可借鉴：把“源资产、摘要/版本、目标 client serializer、实际落盘证据、拒绝/降级原因”做成独立资源适配器；不要把这些锁条目伪装为聊天 Session。官方文档另有 ChatGPT/Codex 与 Claude Desktop Chat/Cowork plugin marketplace 分发路径，可作为资产分发研究输入。
- 缺口：无 ChatGPT/Codex Projects/Sections、对话 transcript/turn/branch/child Session、附件/token/记忆/定时任务导入或 Claude Desktop/Code Session writer。官方 Anthropic 帮助明确 API-key/cloud-provider 的 Claude Code 不接收 Claude-account plugin sync；Desktop Chat/Cowork plugin support 不是 Session 迁移，也不证明 Code mode 或第三方推理兼容。
- MCP/安全：canonical MCP artifact 可转成 client config，但本地 MCP descriptor path 被 CLI 拒绝（exit 64），并未发现把现有客户端 MCP 配置反向导入为锁定 artifact 的路径。MCP command 和 hooks 是可执行资源；迁移需按非可信输入展示、摘要、拒绝/需人工批准，不能自动启动。
- 验证：隔离测试 7,563 passed / 0 failed；fmt/check通过；Clippy 在 launcher test helper 的 dead-code warning 上 exit 101。临时本地 Skill → Claude/Codex 插件导出成功；这验证 asset projector，不是历史会话准确率。
- Evidence：`docs/research/evidence/grimoire-review-2026-11-20.txt`。范围仍完整保留用户确认的 Claude Desktop Chat、Cowork、Code 三 mode、本地/自托管 Claude Code，并把 Anthropic-hosted Cloud 单列。At this checkpoint, inventory stood at **47/303 reviewed / 256 unreviewed**; next was `yuvalsuede/claudia`.


### 增量深审：yuvalsuede/claudia（2026-11-20）

- **定位：** AI Agent 的本地 Bun/SQLite 任务管理器，适合作为 Nexus Memory 的 workflow/task plane 参考；不是对话 Session/Project/Section 迁移器。审核 main snapshot commit `8898fa8c255470119a6634e699857f666f398b93`（2026-02-28），GPL-3.0，仓库 snapshot 15 stars / 5 forks；无 Releases 页面条目。`package.json` 为 0.1.3，Claude plugin manifest 为 0.1.2。
- **结构：** Project、Sprint、Task；Task 的 `parent_id` 是任务父子树，依赖另存 edge；Task 保存不超过 65,536 serialized characters 的 JSON context、images/metadata/acceptance criteria。MCP `session_agent_id` 是服务进程启动时生成的 task owner，不是 Claude provider session ID；当前 Project 选择只在进程内存里。
- **兼容边界：** 可参考显式任务树、依赖、SQLite 持久化与任务级结构化上下文；不可把 Task 树映射成对话 Session/turn parentage。没有 ChatGPT Projects/Sections/Section Groups、Claude Chat/Cowork/Code 的会话/转录读写、Claude Code 本地/自托管 session 导入、托管 Cloud session 接口、工具输出/中断历史/多模态消息/Token 成本/定时任务。Task 图片字段不是消息附件事件。插件/Skill/MCP 示例仅说明 Claudia 自身 Claude 集成，不构成跨 Harness 迁移。
- **质量边界：** 仓库 CI workflow 声明 Bun typecheck/test/build；未独立验证具体 CI run。本地 `bun test` 因 Bun 不在环境而 exit 1；没有声称测试通过。`package`/plugin 版本不一致、没有 Releases，作为维护与分发成熟度风险记录，不据 stars 单独判质。
- **证据：** `docs/research/evidence/claudia-review-2026-11-20.txt`。研究台账当前 **48/303 reviewed / 255 unreviewed**；ChatGPT Projects/Sections 与 Claude Desktop Chat、Cowork、Code 三模式继续分别评估，本地/自托管 Claude Code 与 Anthropic-hosted Cloud 继续分开。


### 增量深审：sbroenne/skillpm（2026-11-20）

- **定位：** npm 原生 Agent Skill 包管理器；适合做 Skills 资源资产面参考，不是 Nexus Memory 的 Session/Project/Section 迁移器。MIT，package 0.0.9，Node >=22.20.0；审核 main `1dadf71398242ef9f0186b5af052082400f21c5d`（2026-10-23）。网站 Getting Started 仍写 Node 18，和当前源码/README 的 22.20 要求不同。
- **实现：** `npm install` → 递归扫描 `node_modules`（含嵌套依赖/工作区 symlink）→ 检查 Skill frontmatter 名称冲突 → `npx --yes skills@1.7.0 add <path> -y --json`。每个 npm package 约定一个 `skills/<name>/SKILL.md`；当前上游 `skills` 是独立版本，skillpm 未传 `--all` 或 `--agent`，安装目标由上游 CLI 自动检测决定。
- **实测：** 隔离 synthetic npm package 在 Codex 上被检测，skill 内容同 SHA 复制到 `.agents/skills/demo-skill`；`list --json` 返回 package；`uninstall` 移除 npm dependency，却留下复制的 Skill 和 `skills-lock.json`，并打印 stale-copy warning。Nexus 应将卸载设计成预览+显式清理+可回滚事务。
- **局限：** 无项目/Section/会话/Transcript/turn/branch/附件/token/cost/MCP迁移；不具跨 Harness 语义准确率指标。Agent Skills 目录可移植不等于各宿主 frontmatter、权限、发现行为一致；上游支持表有 Claude Code，但没有证明 Desktop Chat/Cowork/Code 的 session 兼容。repo 明确把全项目 Agent 配置引向 Microsoft APM，后续单独评审。
- **质量：** Node 26 环境 `npm ci`、lint、build、65 tests 全部通过；8 Vitest 文件。CI 配置含 Node 22.20/24/26 与官方 `skills-ref` 验证，但未核实某次 upstream CI run。未声称任何会话迁移通过。
- **证据：** `docs/research/evidence/skillpm-review-2026-11-20.txt`。研究台账当前 **49/303 reviewed / 254 unreviewed**，下一候选由当前 registry/dispatcher 选取。Claude Desktop Chat、Cowork、Code 三 mode 均单独保留；本地/自托管 Claude Code 与托管 Cloud 分开。


### 增量深审：tigu77/tiguclaw（2026-11-20）

- **定位：** 本地自托管多 LLM agent runtime；是目前最强的一类 **Session/branch graph 架构参考**，不是跨 Harness Session 迁移器。Apache-2.0；main/release v0.86.0 commit `6ac04e92c38d8d990865641822c8032d9e2892b0`（2026-11-20）。
- **会话数据：** SQLite `threads` 保存 channel/thread 与当前 provider sid；`transcript_index` 将 thread 映射到多份 provider SID/JSONL 路径；`transcripts` 存文字投影，`turn_items` 存一部分结构化工具项。`thread_lineage` 记录 parent key 与 transcript/chat/time 截止点；Claude 分支会调用 SDK fork，并校验复制件是否恰好止于选定回复后再提交 lineage。
- **项目/记忆：** Project 以绝对路径为 key，`PROJECT.md` 是真源，数据库为索引；Project 可连到会话并带入 Skills/MCP/子代理/命令。没有 Section/Section Group/嵌套项目；memory 是 user/feedback/project/reference 分类；schedule/worker job 也属于本地 runtime。
- **迁移边界：** 未发现 ChatGPT Projects/Sections 导入、外部 Session/Transcript import/export 或 Claude Desktop Chat/Cowork/Code 适配。Claude SDK JSONL 是 TiguClaw 自己管理的会话索引，不等于外部 Claude Code JSONL 导入工具；Codex/OpenAI 自有记录可共享文字连续性，但没有 Claude SDK 原生 fork checkpoint。JSONL 内容索引只取文字块，不能宣称完整多模态迁移。
- **质量/安全：** typecheck/build/build:prod 通过。Node 26 本地 8,429 assertions 中 21 项集中于 `plugin-fetch-redirect` 的 Undici 测试夹具（夹具仍 patch dispatcher `.1`，本机 Node 26 当前 dispatcher `.2`）；`better-sqlite3` 也警告 Node 26 不在其 engine list。相同 commit 的官方 Node 22 CI #784 通过，16m11s。插件/MCP 是可执行信任边界；屏幕控制不可逆，Dashboard 默认 loopback 且自身无登录，远程开放需 ACL/auth proxy。
- **证据：** `docs/research/evidence/tiguclaw-review-2026-11-20.txt`。台账当前 **50/303 reviewed / 253 unreviewed**；下一候选由 registry/dispatcher 选定。Claude Desktop Chat、Cowork、Code 仍分别评估，本地/自托管 Claude Code 与托管 Cloud 分开。


### 候选筛查：forest6511/secretctl（2026-11-20）

- **定位：** 本地密钥保险库（CLI/桌面/MCP），不是 Harness 会话迁移器。Apache-2.0；最新 release v0.8.8（2026-01-22），main commit `2de7b68d61dae81988ca96161e2a65b11badc618`（2026-01-23），GitHub snapshot 12 stars / 8 forks。
- **能力与边界：** MCP 返回密钥元数据/脱敏字段；`secret_run` 通过 default-deny 策略把选定的 vault 值注入被允许的子进程环境并清洗输出。没有 Project/Section/Session/Transcript、branch、memory、MCP 配置转换、导入/导出。**不能把密钥管理当作会话迁移或 MCP importer。**
- **可借鉴：** Nexus 的迁移清单应保存目标端 secret alias/ref，不携带原始 API Key；在目标端经用户确认后由安全 vault 解析。
- **质量边界：** Go 1.24+ 本机未安装，未运行 `go test`/build；仅作代码/文档筛查，不声称加密实现通过审计，也不把它列为核心候选。
- **证据：** `docs/research/evidence/secretctl-review-2026-11-20.txt`。台账目前 **51/303 reviewed / 252 unreviewed**；Claude Desktop Chat、Cowork、Code 三 mode 仍分别纳入，本地 Claude Code 与托管 Cloud 分开记录。


### 候选筛查：Brattlof/skillet（2026-11-20）

- **定位：** MIT Go 包管理器，能安装 Agent Skills、MCP 和 Claude Code 专属 commands/hooks/subagents/output-styles；不是 Session 迁移器。`main` HEAD `7f3b43cc80873a665ecc188f675f1dec0cb2718f` 与 remote main 相同；该 commit 的 GitHub CI #77 通过。
- **实现可借鉴：** 明确的 MCP 客户端配置渲染器、commit/checksum lock、frozen 检验、只清理由本工具登记的文件、原子写入和保留无关 JSON。`~/.agents/skills` 只证明 Skill 文件投影，不代表目标端实际加载/权限/触发一致。
- **不支持/不应推断：** 无 ChatGPT Projects/Sections/Session、Claude Desktop Chat/Cowork/Code 的会话存储、转录/附件/分支/子任务/Token/Memory/Schedule 导入，也没有 Claude hosted Cloud 或 API-Key 的 Session writer；它的 `claude` MCP writer 目标是 Claude Code 项目 `.mcp.json`。
- **工程结论：** 只留作资源层安装器、manifest、校验与 rollback 的设计参考，不列为核心 Session 引擎；资产传输成功与 Session fidelity 分开测量。Go 本机未安装，`rtk proxy go test ./...` exit 1（命令无法启动），无本地 Go 测试结论；官方 exact-head CI 通过。详细证据：`docs/research/evidence/skillet-review-2026-11-20.txt`。台账 **52/303 reviewed / 251 unreviewed**；Chat/Cowork/Code 三 mode 全覆盖，本地/自托管 Code 与 hosted Cloud 分开。


### 候选筛查：harperreed/toki（2026-11-21）

- **定位：** 任务管理 CLI + MCP，Project 只包含 Todo，不是会话或对话层级。没有 ChatGPT Projects/Sections、Claude Desktop Chat/Cowork/Code 会话，亦无本地 Claude Code transcript 或 Cloud/API-Key Session 迁移。
- **可借鉴范围：** 小型 MCP task CRUD / resources / prompts 的工作流平面；其 project path 与 session 身份必须分开。导出格式有 YAML/JSON/Markdown/SQLite，**导入只接受 YAML**。
- **完整性风险：** Project 创建时间不导出，导入时重置；`runImport` 每条记录错误只打印、不回传失败状态，允许部分导入却 exit success；backend migration 无事务，`--force` 只跳过非空目录检查而不清空目标；SQLite backup 仅复制 `.db`，测试先关闭 DB，WAL 活跃时的快照一致性未验证。
- **质量/许可：** exact-main CI #75 状态 Success，但本机 Go 不存在，`go test ./...` exit 1；`go.mod` Go 1.24.9 与 CI 1.21–1.23 矩阵有需查明的工具链差异。README 声称 MIT，但 checkout 无 LICENSE 且 SPDX null，许可未核实。
- **结论：** 不列为核心 Session 引擎或保真证据；只保留低优先级 task/MCP 参考。证据：`docs/research/evidence/toki-review-2026-11-21.txt`。台账 **53/303 reviewed / 250 unreviewed**；Claude Desktop Chat/Cowork/Code 均纳入，本地/自托管 Claude Code 与 hosted Cloud 仍分开。


### 高价值候选：greenfield-inc/agent-farm（2026-11-21）

- **定位：** 当前候选中较强的 Claude Code CLI/Codex CLI 配置与本地 Session telemetry 参考，但不是跨 Harness Session 迁移器。没有 Claude Desktop Chat/Cowork/Code 或 hosted Cloud Session 的适配。
- **可迁移设计：** 分开记录 Agent Farm Session ID、native provider Session ID、launch ID、trace/span ID 与 parent-child 边；用本机 OTel 收集子会话/工具事件；Project path 与工作区、MCP 连接独立；API key 只记录环境变量名。
- **局限：** telemetry 导出只留下 session metadata、过滤后的 logs 与 metrics，明确省略 traces.jsonl；因此不是可回放的完整 transcript archive。它没有 importer，不会写入另一 Harness 的 session。会话内容默认关闭，导出内容要显式同意。
- **Gateway 适配：** 支持 Claude Code/Codex CLI 通过 provider base URL 和环境变量 key 接入代理，已用 localhost fake gateway 验证；这不能外推到 Claude Desktop developer-mode 或 Cloud API-key Session。
- **安全边界：** 每次启动 Claude 用 `--dangerously-skip-permissions`，Codex 用 `--yolo`，没有关闭/沙箱选项；仅在独立 worktree 测试。许可证缺少 LICENSE/元数据，未核实。
- **结论：** 高价值 session-observation 与 CLI gateway 架构参考，非迁移引擎。Node 26 本机 typecheck 通过、361/370 tests 通过，9 个 Windows/PowerShell相关 skip；本地 fake provider smoke 通过；exact main CI #330 通过。证据：`docs/research/evidence/agent-farm-review-2026-11-21.txt`。台账 **54/303 reviewed / 249 unreviewed**，下一项由 registry 选择。


### 高价值候选：greenfield-inc/agent-farm（2026-11-21）

- **定位：** 当前候选中较强的 Claude Code CLI/Codex CLI 配置与本地 Session telemetry 参考，但不是跨 Harness Session 迁移器。没有 Claude Desktop Chat/Cowork/Code 或 hosted Cloud Session 的适配。
- **可迁移设计：** 分开记录 Agent Farm Session ID、native provider Session ID、launch ID、trace/span ID 与 parent-child 边；用本机 OTel 收集子会话/工具事件；Project path 与工作区、MCP 连接独立；API key 只记录环境变量名。
- **局限：** telemetry 导出只留下 session metadata、过滤后的 logs 与 metrics，明确省略 traces.jsonl；因此不是可回放的完整 transcript archive。它没有 importer，不会写入另一 Harness 的 session。会话内容默认关闭，导出内容要显式同意。
- **Gateway 适配：** 支持 Claude Code/Codex CLI 通过 provider base URL 和环境变量 key 接入代理，已用 localhost fake gateway 验证；这不能外推到 Claude Desktop developer-mode 或 Cloud API-key Session。
- **安全边界：** 每次启动 Claude 用 `--dangerously-skip-permissions`，Codex 用 `--yolo`，没有关闭/沙箱选项；仅在独立 worktree 测试。许可证缺少 LICENSE/元数据，未核实。
- **结论：** 高价值 session-observation 与 CLI gateway 架构参考，非迁移引擎。Node 26 本机 typecheck 通过、361/370 tests 通过，9 个 Windows/PowerShell相关 skip；本地 fake provider smoke 通过；exact main CI #330 通过。证据：`docs/research/evidence/agent-farm-review-2026-11-21.txt`。台账 **54/303 reviewed / 249 unreviewed**，下一项由 registry 选择。


## 2026-11-21 research checkpoint — LocalVault

The 55th of 303 GitHub-corpus candidates is reviewed: `inventlist/localvault` is retained as an adjacent encrypted-secret/MCP security reference only, not a session/project migration candidate. Its vault `SessionCache` stores an unlocked vault key, and its groups contain credential names—not ChatGPT Projects/Sections or conversation sessions. Upstream exact-main CI passed; local tests were not run because this host has only Ruby 2.6.10/Bundler 1.17.2 versus Ruby >=3.2/Bundler 2.6.9. README/LICENSE vs gemspec/RubyGems license conflict remains unresolved. Current next unreviewed candidate: `opencue/cuecards`. Detailed source evidence: `docs/research/evidence/localvault-review-2026-11-21.txt`.


## 2026-11-21 research checkpoint — CueCards

The 56th of 303 GitHub corpus candidates is reviewed: `opencue/cuecards` is retained as a high-value project-profile/asset-adapter reference, not a session importer. Its full runtimes cover Claude Code CLI and Codex; external adapters provide partial Skill/MCP/rules writes, not Claude Desktop modes or session state. Local analytics and repo-only text importers do not create a portable conversation graph. Exact-head main is `6c81ebd`; latest visible CI #653 fails with a repeated grader-sandbox output error. Isolated local profile tests passed 171, while the same targeted eval test failed; no full-suite pass claimed. Current next unreviewed candidate: `Phoobobo/herdr-agent-config-manager`. [Evidence](docs/research/evidence/cuecards-review-2026-11-21.txt).


## 2026-11-21 research checkpoint — Herdr Agent Config Manager

The 57th of 303 corpus candidates is reviewed: `Phoobobo/herdr-agent-config-manager` is a narrow Skills inventory/central-symlink tool, not an MCP/config or Session migrator. Its 25 Python tests pass and synthetic organize works; synthetic probes reveal raw MCP argument/URL and hook-command values leak into `detect --json`, while TUI selection can remove a divergent real skill copy without conflict warning. Do not pass its raw JSON to AI or centralize divergent copies blindly. Current next unreviewed candidate: `smartsheet/cli-agent-power-tools`. [Evidence](docs/research/evidence/herdr-agent-config-manager-review-2026-11-21.txt).


### 2026-11-21 candidate update — Smartsheet CLI Agent Power Tools

`smartsheet/cli-agent-power-tools` is reviewed as an adjacent resource-adapter fixture only: paired Claude Code/Gemini agent manifests and structured tool allowlists, no transcript/session import/export or Project/Section graph. The user confirmed Claude Desktop coverage means Chat, Cowork and Code; this candidate demonstrates Code Tab reuse only and must not count as evidence for the other two. Its Gemini automated-chain instructions conflict with the explicit write-approval rule, and both setup scripts remove an existing MCP before validating credentials and pass the token in process args. Add per-host semantic and approval-gate tests to the Nexus resource-adapter validation plan; do not adopt the setup scripts. Evidence: `docs/research/evidence/cli-agent-power-tools-review-2026-11-21.txt`. Candidate inventory: 58/303 reviewed, 245 unreviewed; next selection remains registry-driven.


### 2026-11-21 candidate update — Lokalite credential references

`RubenGlez/lokalite` is a useful local secret-vault/security reference (AES-GCM + macOS Keychain, project/environment scopes, `lokalite://` placeholders, brokered MCP handoff) but it is **not** a Session or API-key gateway migration tool. Preserve credentials as unresolved secret references and require destination-specific human re-binding; never bundle secret values. Add tests for MCP permission semantics, project/env re-resolution, malformed config fail-closed behavior, and vault-reference provenance. Claude Desktop config registration does not prove Chat/Cowork/Code session transfer; the confirmed three-mode scope remains unchanged. Candidate evidence: `docs/research/evidence/lokalite-review-2026-11-21.txt`. Inventory 59/303 reviewed, 244 unreviewed; next registry action `bunhine0452/Ocul-PM`.

## Research checkpoint — Claude Desktop 3P and Ocul-PM (2026-11-21)

The user's clarification is now reflected as a hard scope: Claude Desktop Chat, Cowork and Code all included, plus local/self-hosted Claude Code. The destination meant here is Claude Desktop on third-party inference/gateway, not Anthropic-hosted Claude Code Cloud. First-party docs confirm a static API-key gateway path, but that only supplies model inference; it is not a portable-history API. The 3P app stores Chat/Cowork sessions locally and uses Claude Code's own local transcript store for Code. The built-in import is source-specific to Claude.ai plus local earlier-install Cowork/Code, not a ChatGPT export import. Current product rollout also unifies Chat and Cowork for some users, so version/mode must be recorded and tested rather than assumed. See [`claude-desktop-3p-chat-cowork-code-2026-11-21.txt`](research/evidence/claude-desktop-3p-chat-cowork-code-2026-11-21.txt).

Deep source review of candidate `bunhine0452/Ocul-PM` at `9dd0f85` adds a useful project-journal/activity-observation reference, but no cross-Harness conversation importer. Its watcher session groups work activity and a list of provider session IDs; its transcript parser is for file-verdict evidence. Local source tests are strong but Windows Portability CI has two spawn-budget failures. Synthetic hook events show raw prompt/assistant payloads can remain as plaintext owner-umask files. It remains adjacent-only, with privacy caveat; see [`ocul-pm-review-2026-11-21.txt`](research/evidence/ocul-pm-review-2026-11-21.txt).

Candidate registry now records **60/303 reviewed, 243 unreviewed**; next: `compilando/norte. This is one more candidate review, not a full market survey or target compatibility result. Next work: validate ChatGPT export/session source shapes, probe documented Claude Desktop 3P import/export using a versioned disposable app, then test Chat/Cowork/Code projections separately. Do not use any undocumented app-state writer until an authorized target-native resume succeeds.

## Research checkpoint — Norte session/audit distinctions (2026-11-21)

Reviewed `compilando/norte` at `52256ccb816999705fb681a5336d39839497d099`. Its persistent UI session (`session.json`), ephemeral assistant chat, MCP agent actor ID, and hash-chained filesystem-operation journal are four different concepts. The operation journal and approval/undo design are useful adjacent reference patterns, but they are not transcript history; no ChatGPT Project/Section/thread importer or general conversation writer was found. The local Mac workspace compile gate failed on Linux-oriented `O_PATH`/`st_dev` code despite source/README Mac claims; a selected test subset had 2,058/2,061 passing, and remaining failures are recorded. It is not a core migration dependency. Details: [`compilando-norte-review-2026-11-21.txt`](research/evidence/compilando-norte-review-2026-11-21.txt).

Candidate inventory is now **61/303 reviewed**, with 242 unreviewed; next candidate: `hyper-swe/mtix`. This increments source-code review breadth only; Claude Desktop Chat/Cowork/Code and local Claude Code target routes still need versioned native restore tests, and the broad Harness inventory remains incomplete.


## Research checkpoint — MTIX task context vs. provider conversation (2026-11-21)

Reviewed hyper-swe/mtix at 12c6a41582f3639f0438f92bf74ba0749429dfeb. Its task hierarchy, MCP context assembly, checksummed task-board transfer and agent-run Session metadata are useful adjacent capabilities; the Session record is only lifecycle/summary/task counts, not conversation messages. No ChatGPT Project/Section import, conversation fork graph, multimodal turn store or target-native session writer was found. Keep separate TaskGraph/AgentRun/ConversationThread records; do not promise transcript fidelity via MTIX. Local targeted service/MCP/SQLite package tests passed after fetching required historical tags; upstream CI #1356 passed. Details: [hyper-swe-mtix-review-2026-11-21.txt](research/evidence/hyper-swe-mtix-review-2026-11-21.txt).

Candidate inventory is now **62/303 reviewed**, 241 unreviewed; next: JoeyWangTW/todo-cli. This adds repository-code review breadth only; all three Claude Desktop modes are in research scope, but their native resume/import paths still need separate live, versioned verification.


## Research checkpoint — task-process handle versus Gemini native chat session (2026-11-21)

Reviewed JoeyWangTW/todo-cli at 22caf3182d01d321264f1ee189e8ce457b25c190. It persists a flat todo and tmux session name while Gemini CLI stores its own project-scoped resumable conversations; todo-cli never records the Gemini session UUID or reads/exports its transcript. It is not cross-Harness migration support. Keep Task, HarnessProcess and NativeConversationSession distinct. Seven JS syntax checks and a synthetic task store round-trip passed, but no automated test or release gate is defined; Gemini/tmux/MCP were not launched. [Evidence](research/evidence/todo-cli-review-2026-11-21.txt).


Candidate inventory status: 66/303 reviewed, 237 unreviewed; next: evoerax/awesome-harness-engineering. All three Claude Desktop modes (Chat, Cowork, Code) remain in scope. Conus is an adjacent task/session activity ledger; CData Google Ad Manager MCP is an archived provider connector. Neither is a native session migrator; no live native-session restore test was performed this turn.

## Incremental GitHub candidate review — evoerax/awesome-harness-engineering (2026-11-21)

Reviewed the next unreviewed search result at pinned main `0569df715fed9c42cb5ab3658655a2b55cf1c6b9`. It is a low-adoption Markdown index, not a transfer implementation; the feature matrix contains material inaccuracies against current first-party Codex, OpenClaw, and Gemini docs, with no reproducible migration benchmark. No tracked LICENSE exists despite the README MIT claim. Disposition: pass as an engine, retain only as an unverified discovery lead; use vendor documentation and native tests as the compatibility source of truth. Candidate inventory is now **67/303 reviewed, 236 unreviewed**; next unreviewed: **`sboorlagadda/artmark`**. Research is still ongoing and this is not a completeness or accuracy claim. All three Claude Desktop modes remain in scope. Full evidence: `docs/research/evidence/evoerax-awesome-harness-engineering-review-2026-11-21.txt`.

## Incremental GitHub candidate review — sboorlagadda/artmark (2026-11-21)

Reviewed pinned main `231313e914be18a17c3bb4a028fe6bd9698acf66` and v0.2.3. Disposition: retain as an Apache-2.0 **artifact memory/catalog** reference, not a Session/Project migration engine. Local code, tests and a synthetic CLI workflow were exercised; two recent upstream scheduled dependency-audit runs failed with unknown public-log cause, so security status remains a follow-up. Candidate inventory is now **68/303 reviewed, 235 unreviewed**; next: **`t59688/skillpack-manager`**. All three Claude Desktop modes remain in scope. This is incremental research, not completeness or live-import proof. Full evidence: `docs/research/evidence/artmark-review-2026-11-21.txt`.

## Incremental GitHub candidate review — t59688/skillpack-manager (2026-11-21)

Reviewed pinned main `2d8f5507c4926fccb776c121879b5bed449d7f9d`. It is a MIT-licensed SkillPack/ResourceInstaller, not a Session or Project migration implementation. Local 37 tests, typecheck, lint and build pass, but two isolated malicious-manifest probes show a confirmed path traversal and the static audit misses it; do not install untrusted packs or use on real skill directories until fixed. npm v0.1.3 last published May 27; GitHub main last pushed May 28 and the repo has no Releases. Keep as a resource-plane design lead only. Candidate inventory is now **69/303 reviewed, 234 unreviewed**; next: **`travelhawk/agentpm`**. All three Claude Desktop modes remain in scope; research is ongoing. Full evidence: `docs/research/evidence/skillpack-manager-review-2026-11-21.txt`.


## Candidate review checkpoint — 2026-11-21

`travelhawk/agentpm` has been screened at pinned source `8738e024df1356c802b50440ebe4820a986bf2ab`: retain as an adjacent Skills/resource-plane reference; reject as a ChatGPT/Codex-to-Claude project/session migration engine. The exact-SHA upstream CI succeeds, but the local Node 26 / pnpm 11 test run has a reproducible two-suite `@agentpm/shared` package-resolution issue; reproduction with CI's declared Node 24 / pnpm 10.32.1 remains open. The inventory is now **70/303 reviewed, 233 pending**; next candidate: `walidboulanouar/ay-claude-templates`. User-confirmed scope remains Claude Desktop Chat, Cowork, and Code separately, plus local/self-hosted Claude Code. This checkpoint is incremental, not a completion claim.


## Candidate review checkpoint — 2026-11-21

`walidboulanouar/ay-claude-templates` reviewed at `634b2742dcde12445b45b59f097b70553247707b`. Exclude as migration engine: it installs Claude Code resources through an AY OAuth marketplace, offers no project/session conversation importer, lacks the three Claude Desktop mode adapters, and ignores `CLAUDE_CONFIG_DIR`. Synthetic source probes demonstrate destination-root escape by API package slug and a Windows backslash ZIP path projection; its built-in hook template is rejected by its verifier. No tests/CI evidence. **Do not use against user data or untrusted packages.** Remaining inventory: **71/303 reviewed, 232 pending**; next `zavora-ai/macos-zlaunch-manager`. User scope remains ChatGPT/Codex source migration to local/self-hosted Claude Code plus Claude Desktop Chat/Cowork/Code separately.


## Candidate review checkpoint — 2026-11-21

`zavora-ai/macos-zlaunch-manager` at `639640e1f7cf643536a16a8e9270e8d5bc8c3df9` is screened out as an unrelated launchd-management MCP, not a session or project migrator. It exposes 19 OS-mutating tools, has no Session/Message/Project model, lacks current Desktop `.mcpb` packaging, and a sandboxed source POC confirms path escape in `launchd_create`. Keep tool-approval and OS-resource risks distinct from Harness portability. Inventory now **72/303 reviewed, 231 pending**; next `ai-agent-manager/agent-manager`. Preserve all three Desktop modes as separate target surfaces.


## Candidate review checkpoint — 2026-11-21

`ai-agent-manager/agent-manager` at `c2be46db0be58c653cd285044fe598b4a63c2fb2` is shortlisted as a **resource-plane architecture reference only**. Borrow discovery/version/source provenance, safe cache extraction, repo/system scope and explicit target provisioners. Do not infer conversation semantics from the product's `Session` or `Project`: they are local bundle/auth/membership state and Atlassian team projects. No transcript/section/session import, memory, token ledger, schedule, MCP config or Claude Desktop Chat/Cowork/Code restoration exists. Inventory **73/303 reviewed, 230 pending**; next `omarmfouad25/google-marketing-agent`; research remains active.


## Candidate review checkpoint — 2026-11-21

`omarmfouad25/google-marketing-agent` is screened out as a migration engine. Its Google marketing MCP is a useful secondary tool-safety reference; released v0.3.0 is less protected than its docs imply when a profile allows writes, while an open but unmerged v0.4.0 PR adds Preview-ID/hash confirmation and drift-aware rollback. This establishes the requirement that Nexus approvals be server-enforced, bound to the exact planned mutation and relevant external state, with rollback records; it does **not** provide chat/session transfer. Current main dependency audit also reports 17 production and 20 total advisories. Inventory **74/303 reviewed, 229 pending**; next `SoonIter/skills-package-manager`.


## Candidate review checkpoint — 2026-11-21

`SoonIter/skills-package-manager` at `4d3d216144c493ba4ad4ea2f8fa581304bef3f71` is screened out as a Session migration engine and retained only as a narrow Skill asset/source-linking reference. Its 45 skill directory mappings do not represent support for ChatGPT/Codex Project/Section/session trees, memory, MCP/plugins, attachments, schedules, or Claude Desktop Chat/Cowork/Code modes. Direct schema/core/plugin build gates and 134/134 tests pass; the package-manager install gate exited 1 because unapproved dependency lifecycle scripts were blocked. Inventory now **75/303 reviewed, 228 pending**; next `AI-Colleagues/skill-mgr`. Full evidence: `docs/research/evidence/skills-package-manager-review-2026-11-21.txt`. Research remains active; this is not a completeness claim.


## Candidate review checkpoint — 2026-11-21

`AI-Colleagues/skill-mgr` at `12beaffd08dedad72a3a673f47569993bd856c69` is a narrow AgentSkills installer, not a conversation migrator. Keep its adapter boundaries as a small reference only; do not reuse its target writes unchanged because two disposable tests confirmed local symlink dereference and destructive replacement of a same-name unmanaged directory. The local test/lint gates and PyPI provenance are strong, but do not prove migration fidelity. Inventory now **76/303 reviewed, 227 pending**; next `bl1nk-bot/skills-cli`. Claude Desktop Chat, Cowork, and Code remain separate included target modes; local/self-hosted Claude Code remains distinct. Full source/test/probe evidence: `docs/research/evidence/skill-mgr-review-2026-11-21.txt`. Research remains active.


## Candidate review checkpoint — 2026-11-21

`bl1nk-bot/skills-cli` at `5c62e991ffa94818a747fbe3badca92e178ecbd3` is rejected as a session migration engine. It is an advertised Skill overlay/path installer, but source commands do not match the README; the root crate fails to build at `src/lib.rs`, the registry stub fails separately, and the Claude/Gemini converter code is not wired in. It contains no conversation Project/Section/Session importer or writer. Keep at most a weak Skill ResourcePlane idea, not code. User has clarified scope: local/self-hosted Claude Code plus Claude Desktop client-managed sessions configured through a third-party gateway; include Chat, Cowork and Code as distinct Desktop modes and do not conflate with Anthropic-hosted Claude Code Cloud. Inventory **77/303 reviewed, 226 pending**; next `CassianFlorin/skill-hub`. Detailed ledger: `docs/research/evidence/skills-cli-review-2026-11-21.txt`. Research remains active; not a completeness claim.


## Candidate review checkpoint — 2026-11-21

`CassianFlorin/skill-hub` at `19b764bce362a172b23e8db6f7394ff4e15f3ea2` is retained as a strong adjacent Skills `ResourcePlane` and native SwiftUI-on-JSON-CLI reference, but excluded as a conversation migration engine. It has clear managed/project/runtime skill scopes and source/checksum/rollback records, yet no ChatGPT Project/Section/session graph or Claude Desktop Chat/Cowork/Code / third-party gateway session adapter. Exact-head GitHub CI #77 passed three OS jobs; the local Go toolchain is absent, so local Go test/build were not run; npm wrapper tests were 3/3. Record the static symlink-copy caution without claiming a reproduced exploit. Inventory now **78/303 reviewed, 225 pending**; next `Heretyc/subagent-mcp`. Full ledger: `docs/research/evidence/skill-hub-review-2026-11-21.txt`. User-confirmed target remains local/self-hosted Claude Code plus Desktop client-managed third-party gateway, with Chat/Cowork/Code separate. Research remains active.


## Candidate review checkpoint — 2026-11-21

`Heretyc/subagent-mcp` at `aa8f421186d93a4cc2608b0ae0314569a0e08fef` is kept as a strong adjacent sub-agent OrchestrationPlane reference, not a cross-harness session migration engine. It offers managed local child processes, permissions, output polling, compact handoffs and a latest per-session context/token sample; it has no durable parent-child transcript tree, ChatGPT Project/Section reader, attachment converter, or Claude Desktop Chat/Cowork/Code writer. Its direct API adapter is a single task-call integration, not a Claude Desktop gateway session API. Local build passed; local npm test 147/150 with three reproducible failures, while an earlier PR gate passed before merge on Ubuntu Node20; the exact current-main push workflow was not a test gate. Do not treat an MCP tool server as a data importer. Inventory now **79/303 reviewed, 224 pending**; next `hiadamhere/spm`. Full ledger: `docs/research/evidence/subagent-mcp-review-2026-11-21.txt`. All three Claude Desktop modes remain separate and in scope. Research remains active.


## Candidate review checkpoint — 2026-11-21

`hiadamhere/spm` at public `main` SHA `ca8d684e546b510ccae7fe2e966df2679f86df92` is a Skill catalog/deployer only, not a Project/Section/Session converter. The public repo has no CLI source/tests; the published 0.4.0 NuGet PDB points to an unavailable private-source commit `742a52d...`. Limited static decompilation found a possible destructive replacement of real same-name target directories; this is not a runtime-reproduced exploit. Keep only as a weak ResourcePlane/path-discovery idea, not an implementation dependency. Inventory **80/303 reviewed, 223 pending**; next `keynv-labs/keynv`. Claude Desktop Chat/Cowork/Code remain independently in scope; no session migration has been tested. Research remains active. Full ledger: `docs/research/evidence/hiadamhere-spm-review-2026-11-21.txt`.

## Candidate review checkpoint — keynv-labs/keynv (2026-11-21)

keynv-labs/keynv at pinned SHA d179d30e4131b2198f272d5b3712d8aaa9582927 is not a migration engine. Keep only as an adjacent opt-in privacy/redaction-plane idea for text surfaces; it lacks the source/target adapters and structured Project/Section/Session/event graph needed for Nexus Memory, and does not support the confirmed Claude Desktop Chat, Cowork, or Code destinations. Its watcher’s whole-file rewrite of an actively appended JSONL/log has a source-documented lost-append race; avoid real user transcripts. Local Node 22 build/typecheck and full tests passed (824 passed, 1 skipped, 10 TODO), while lint failed on two Biome formatting findings and the official npm audit reported 88 occurrences including 4 critical dependency findings. Latest GitHub release was v0.1.0-rc.25 (pre-release, July 13); exact-main CI later in July failed lint. Inventory now 81/303 reviewed, 222 pending; next KRISH-exe-29/ai-agent-skill-router. The user reaffirmed all Claude Desktop modes—Chat, Cowork and Code—are in scope; exact app version and OS remain open. Full evidence: docs/research/evidence/keynv-labs-keynv-review-2026-11-21.txt. Research remains active, not complete.

## Candidate review checkpoint — KRISH-exe-29/ai-agent-skill-router (2026-11-21)

The candidate at SHA 50bd7bbdde14ceca5f2ed0db255497d6e6ccaa13 is an AI-mediated Skill router and inventory/approved cleanup tool, not the requested no-AI universal data migration engine. It is useful only for ResourcePlane discovery, names-only MCP inventory, per-item preview/approval, hashes and undo. Its opt-in Claude Code JSONL scan summarizes usage metadata; it does not preserve or replay sessions. It has no Projects/Section Groups, message/event graph, attachments, memory/schedule or Claude Desktop Chat/Cowork/Code support. Local selftests/schema validation pass and exact-head CI passes, but disposable macOS installation reproduced a script-entrypoint silent no-op through the generated Claude skill symlink (exit 0, empty stdout); canonical realpath passes. Tests do not cover cross-Harness fidelity. Inventory advances to 82/303 reviewed, 221 pending; next candidate is selected from the registry. Claude Desktop Chat, Cowork and Code remain independently in scope. Details: docs/research/evidence/ai-agent-skill-router-review-2026-11-21.txt.

## Candidate review checkpoint — nemesiscodex/pulse-tm (2026-11-21)

Pulse at SHA aa76ba14baa8d3e3115e91cb7447ed3889b7116e is a low-adoption, early-development local task manager and MCP server, not a Harness session migrator. It provides tag-grouped Tasks and one-level Subtasks in .pulse YAML and can help a user resume work by manually authored descriptions. It does not model provider Project/Section/session/message/branch/event graphs, media, memory, schedule or arbitrary import/export, and it has no Claude Desktop Chat/Cowork/Code adapter. In a synthetic CLI test, a malformed YAML file was logged as a parse error, treated as empty, then overwritten by a newly created task. Bun 1.3.0 test suite passes 21/21 and build passes; the CI-defined lint/typecheck gate exits 2 at Modal.tsx TS2322 after dependency resolution, and GitHub Actions currently shows 0 runs; no GitHub release exists. Inventory advances to 83/303 reviewed, 220 pending; user-confirmed Desktop scope remains Chat, Cowork and Code separately. Full evidence: docs/research/evidence/pulse-tm-review-2026-11-21.txt. Research remains active.

## Candidate review checkpoint — rtaparay/Open-Skills-Manager (2026-11-21)

The candidate at exact SHA 2541c9df6f1f20fad774a38d5b3dbda6f5c1c78d is a VS Code extension for Agent Skills discovery/deployment, not the requested universal session/project migration product. It supports skill repository and local folder inventory across several VS Code forks; it does not serialize ChatGPT/Codex Projects, Section Groups, session/message/branch graphs, Claude Desktop Chat/Cowork/Code, tool events, attachments, MCP/plugin configs, memories or schedules. Source checks found destructive overwrite behavior for existing skill destinations and a static remote-name path escape; the ZIP dependency adm-zip 0.5.16 has high advisories reported by the official registry audit. Build/typecheck pass in a disposable copy, but no tests or CI were found. Inventory advances to 84/303 reviewed, 219 pending; all three Desktop modes remain in scope. Full evidence: docs/research/evidence/open-skills-manager-review-2026-11-21.txt.


## Incremental candidate review — Spaztazim/lucid-context-engine (2026-11-21)

Screened exact upstream HEAD 2dbfa1e8faa612278307cd9d30f51b6b6d637861. It is an OpenClaw-only retrieval plugin, not a Project/Section/Session migrator. Its ingest() returns false; retrieval is delegated to a local QMD shim; it has no source/target adapters, transcript graph, Claude Code or Desktop Chat/Cowork/Code/3P gateway support. Do not shortlist as a migration dependency; preserve only as a limited optional retrieval-plane comparison. No tests/CI/releases/lockfile were found; build/typecheck were not runnable because dependencies were not installed. Evidence: docs/research/evidence/lucid-context-engine-review-2026-11-21.txt.

Corpus status: **85/303 reviewed, 218 unreviewed**; next candidate: stefafafan/skm. The inventory and repository triage remain incomplete; this is not proof of market-wide or Harness-wide coverage.


## Incremental candidate review — stefafafan/skm (2026-11-21)

Reviewed archived/deprecated MIT package @stefafafan/skm 0.3.3 at exact HEAD 9cd248d2857f38d3d937606f82d54f52151ab7f8. Useful only as a ResourcePlane manifest/lock/cache reference; it has no ChatGPT/Codex Project/Section/Session or Claude Code/Desktop Chat/Cowork/Code/API-key destination adapter. Local tests passed 131/131 and lint passed, but format check has five issues; the official-registry production audit flags ws 8.19.0 (1 high, 1 moderate). A disposable symlink-output probe reproduced writing outside the project and deleting an external same-name canary. Do not adopt as dependency. Full evidence: docs/research/evidence/stefafafan-skm-review-2026-11-21.txt.

Corpus status: **86/303 reviewed, 217 unreviewed**; next candidate: asm-cli/asm-cli. Repository and Harness research remain incomplete.


## Incremental candidate review — asm-cli/asm-cli (2026-11-21)

Reviewed exact latest-release HEAD 2537ee2ba8941ace891dfced324f2b411a5c0ba9. This is a local Skills/MCP/Plugin store and projection CLI, not a Project/Section/Session migrator. It offers useful resource-plane seams, but GitHub shows no license and the repository has no LICENSE. Official release build exists for Linux amd64, macOS arm64 and Windows amd64; local Go test/vet/build pass with a checksum-verified temporary Go toolchain. No tests cover migrator/MCP/plugin operations. Temporary exact-binary probes confirm unvalidated package ID path escape and MCP binary path-prefix deletion; config contains plaintext environment values. Do not adopt unchanged. Evidence: docs/research/evidence/asm-cli-asm-cli-review-2026-11-21.txt.

Corpus status: **87/303 reviewed, 216 unreviewed**; next: b2amedina/omaset. Research remains incomplete.


## Candidate review checkpoint — b2amedina/omaset (2026-11-21)

Omaset at exact HEAD `5548b2789706a950f3d954fd234190ee4d9d367d` is a local Omarchy settings UI/CLI/MCP server, not a generic Harness migrator. Keep only the shared schema/control-plane, atomic setting write and undo patterns; do not count its night-light schedule as an agent schedule. It has no ChatGPT/Codex Project/Section/Session import, attachments, transcript graph, memory, or Claude Desktop Chat/Cowork/Code/API-gateway session writer. A disposable macOS-compatible test copy reported 23/29 passing, with six failures involving BSD `wc`, absent Omarchy locale data and unavailable `setsid`; no clean cross-platform test claim. Full evidence: `docs/research/evidence/omaset-review-2026-11-21.txt`.

Candidate inventory: **96/303 reviewed, 207 pending**; next `nathfavour/anyisland`. Survey remains active and not exhaustive. The user's confirmed Claude Desktop scope remains all three modes: Chat, Cowork and Code.


## Candidate review checkpoint — dougrn/MCP-MegaBrain (2026-11-21)

At pinned HEAD `2b8fd6b6e05fd74ea5ca4cf085b120815e4fb14e`, this is a local record-based MCP memory sidecar (rules/specs/experiences/patterns), not the requested universal no-AI migrator. Local locked tests pass 17/17 and a temporary stdio MCP record→consult test passes. However, a disposable POC reproduces cross-project leakage when unrelated project names share a final path segment; a separate temporary probe observed default SQLite mode 0644 and data directory mode 0755 under umask 022. No ChatGPT/Codex Project/Section/session import or Claude Desktop Chat/Cowork/Code gateway-session writer exists. Retain only as an adjacent memory-plane pattern; harden scope identity and storage before considering reuse. Full evidence: `docs/research/evidence/dougrn-mcp-megabrain-review-2026-11-21.txt`.

Candidate inventory: **96/303 reviewed, 207 pending**; next `nathfavour/anyisland`. The survey is active and not exhaustive; Claude Desktop Chat, Cowork and Code remain in scope.

 
## Candidate review checkpoint — eddieran/skillpm (2026-11-21)

At pinned HEAD 26fb1c66b274b8729f5bcca0c2e31d2013cf3141, skillpm is a strong deterministic Agent Skills ResourcePlane CLI, not the requested universal no-AI migrator. Its seven “verified” plus three best-effort targets are filesystem discovery/validation contracts. Project manifests and lockfiles describe Skills, not ChatGPT Projects/Sections or Session trees. It has no MCP/plugin/memory/schedule or Claude Desktop Chat/Cowork/Code/API-gateway session adapter. Exact-HEAD CI, nightly E2E and local tests pass, but the security workflow fails at govulncheck. Disposable POCs reproduce manifest symlink overwrite, external symlink read and scanner gap, same-basename Skill overwrite, crafted adapter path escape and rollback/state inconsistency. Do not adopt its filesystem code unchanged. Detailed evidence: docs/research/evidence/eddieran-skillpm-review-2026-11-21.txt.

Candidate inventory: **90/303 reviewed, 213 pending**; next Elixion-ai/claudepass. The survey remains active and not exhaustive; all three Claude Desktop modes remain in scope.


## Candidate review checkpoint — Elixion-ai/claudepass (2026-11-21)

At pinned HEAD a18b332b8bbfe6661eab2841ec169d3b1f878da3, ClaudePass is a local secret-reference/handling tool, not a session transfer project. It is valuable to the security plane only: store secret handles separately from content/session artifacts, do not put raw API keys in export bundles by default, and enforce explicit project/session scope because this project deliberately shares a user Vault across local agents and has no cloud relay. Its Claude Code plugin directory is not an account-backed Desktop Chat/Cowork installer; official component support differs across all three modes (Chat ignores hooks, while skills load). Cloud sessions, relay, sync and practical Windows Broker support are explicitly out of scope. Detailed tested evidence: `docs/research/evidence/claudepass-review-2026-11-21.txt`.

Candidate inventory: **96/303 reviewed, 207 pending**; next `nathfavour/anyisland`. The survey is active and not exhaustive; Claude Desktop Chat, Cowork and Code remain separately in scope.


## Candidate review checkpoint — higherorderfunctor/nix-agentic-tools (2026-11-21)

At pinned HEAD b68c1e93af91e64e919d3cf792d51b6b0b1aa95e, the repository is a serious Nix-based declarative config/resource manager, not a universal migrator. Keep its typed runtime capability matrix, scope-aware Home Manager/devenv emitters, managed MCP/Skills/agents/hooks, and CPA inference-route patterns as references for deterministic ResourcePlacement. It does not import ChatGPT/Codex Projects, Sections, conversation/session graphs, attachments, or Desktop account state.

Kiro session knowledge is unusually rich but version-bounded: the raw KAS 2.15.1/2.15.2 research maps 23 message payload kinds, sub-executions, snapshots, usage and workflow state; the same repo now packages Kiro CLI 3.5.0. Use current Kiro's official local V3 ZIP or save/load script boundary; keep cloud sessions and local archives separate; use advertised ACP export/history APIs rather than direct-writing server-owned V3 storage. Re-probe current version before implementing. Detailed evidence: `docs/research/evidence/higherorderfunctor-nix-agentic-tools-review-2026-11-21.txt`.

Candidate inventory: **96/303 reviewed, 207 pending**; next `nathfavour/anyisland`. Claude Desktop Chat, Cowork and Code remain separately in scope; architecture/prototype work remains outstanding.


## Candidate review checkpoint — interrupted-sh/murk (2026-11-21)

At pinned HEAD 8e884703eceb63bf6f1102535ff60da20ddbcc23, murk is a local encrypted credential vault with MCP and expiring scoped agent grants, not a conversation/session importer. Use it as a SecretPlane reference: store secrets separately, avoid raw values in exported bundles, and tie credential grants to explicit per-run/session scope. Do not treat `MURK_AGENT`/`MURK_STRICT`, output masking or grant TTL as a sandbox; require separate OS user/container if a local agent must not reach the operator key. Its MCP `murk_get` returns the value to model context. Full local tests and exact-HEAD CI are recorded in `docs/research/evidence/interrupted-sh-murk-review-2026-11-21.txt`.

Candidate inventory: **96/303 reviewed, 207 pending**; next `nathfavour/anyisland`. Cross-Harness research and safe migration prototype remain outstanding.


## 2026-11-21 research checkpoint — Claude Desktop 3P source-specific import + AnyIsland #97

The user reconfirmed that all Claude Desktop modes (Chat, Cowork, Code) are in scope for the third-party inference/API-key client path, alongside local/self-hosted Claude Code; Anthropic-hosted Cloud Code remains a separate non-target. Rechecked current first-party Desktop docs: a static API-key gateway powers inference and does not authorize history import. The native wizard imports Claude.ai chats/projects and same-machine earlier-install Cowork/Code sessions, not ChatGPT export ZIPs; the Chat/Cowork local audit/state and Claude Code transcript/workspace remain distinct. Keep exact Desktop version/OS and a disposable profile as Gate 0/target-runtime requirements; no target app or user session was opened in this research pass.

Candidate #97, `nathfavour/anyisland`, is a package manager with no ConversationGraph or Project/Section/session contract. Local tests/vet pass, but explicit mock encryption exposes command text/key prefix, shell history lacks a production hook, and manifest shell steps execute without the documented approval gate. Reject it as a migration dependency. Registry progress is **97/303 reviewed, 206 pending**; next `omer-ayhan/skillspp`. Detailed evidence and error statuses are in `docs/research/evidence/anyisland-review-2026-11-21.txt`. Research remains active and non-exhaustive.


## 2026-11-21 user scope confirmation and Desktop gateway check + candidate #98

The user selected all three Claude Desktop modes—Chat, Cowork, Code—as destination adapters, alongside local/self-hosted Claude Code. The named target path is Claude Desktop Developer → Configure Third-Party Inference, not Anthropic-hosted Claude Code Cloud. Current first-party docs confirm the Desktop gateway config and specify Messages API requirements; Chat/Cowork/Code are supported surfaces, but provider routing alone does not move Sessions. The Desktop import wizard can one-time copy Claude.ai chats/projects and local earlier Cowork/Code sessions into a local store; it is not a ChatGPT ZIP importer. Keep Desktop mode, OS, exact app version, gateway provider/auth mode, import state and per-field fidelity in the test matrix. Current import docs identify 5.11492.0 (most automatic copy items) and 5.1231.0 (additional project/folder/pin completeness) as material version cutoffs. Preserve the gateway API key only as an OS-protected secret reference, never in portable conversation content.

Source-side OpenAI docs currently describe a Project as chats/files/instructions with project memory and branching, and an export as conversation JSON plus other account data/files. That does not prove sidebar Section Groups will export or that importing an archive can rehydrate native projects. Keep the user's canonical project label **Destruction Era**; as recorded earlier, no accessible local/source account export has yet confirmed this item. Need user-provided data export/copy before testing real object conversion.

Candidate #98 `omer-ayhan/skillspp` is only a Skill installer/manager, not a SessionGraph migrator. Typecheck/lint/build, unit/integration/contract/e2e and CI tests pass, but harmless isolated probes reproduced GitHub-source installer hook execution by default and a symlink containment escape. Reject as dependency; retain only as a small ResourcePlane schema reference. Inventory now **98/303 reviewed, 205 pending**; next `patterson-agents/cli`. Full ledger and official documentation URLs are in `docs/research/evidence/skillspp-review-2026-11-21.txt`. Research is active; this is not a completion claim.


## 2026-11-21 research checkpoint — candidate #99 patterson-agents/cli

Reviewed main HEAD `fca318f1dc775c017129cbf1856b96b7d1cfbcf4`. Patterson is a strong adjacent configuration/resource manager: strict typed IR, target-specific emitters, explicit reachability gaps, and a single provenance/drift-safe writer. It is not a conversation/session interchange product: project `init --import` lifts local config assets only, and the core model contains no transcript/event/attachment/usage graph. It does not cover the confirmed Claude Desktop Chat, Cowork, Code third-party gateway, or ChatGPT/Codex Project/Section hierarchy.

The exact-HEAD upstream Gate succeeded (typecheck/test/lint), but local test execution was not attempted: Bun and Socket CLI are absent, and the repository requires Socket scoring before dependency installation. The custom `LicenseRef-Patterson-Internal` license prohibits copying/redistribution outside Patterson without written permission. Retain only independent architectural lessons, not source/assets/dependency. Candidate inventory **99/303 reviewed, 204 pending**, next `rcdelfin/agentkit`; research remains incomplete. Detailed source/CI/error evidence: `docs/research/evidence/patterson-agents-cli-review-2026-11-21.txt`.


## 2026-11-21 research checkpoint — candidate #100 rcdelfin/agentkit

Reviewed `f5bb34e7e09799ca3a5191970e66864a96517583`. AgentKit links shared instructions and a 15-entry Markdown-only Skill allowlist for a few local harness roots; it is a narrow asset/resource linker, not cross-Harness session migration. It has no Projects/Section Groups, conversation/message/fork/subagent model, attachments, token history, independent memory or schedules, and no Claude Desktop Chat/Cowork/Code third-party gateway adapter. Isolated temp-HOME tests exposed that `--unlink` removes foreign instruction symlinks and leaves a generated Claude import wrapper after a fresh install/unlink; existing regular-file backup/restore works. Use only as a limited resource-layer comparison, never as evidence of session fidelity. The repo is MIT but each bundled Skill keeps its own license. Inventory **100/303 reviewed, 203 pending**, next `rolecraft-sh/.github`; survey remains active. Full details: `docs/research/evidence/agentkit-review-2026-11-21.txt`.


## 2026-11-21 registry hygiene — rolecraft-sh/.github (#101)

The candidate is only a GitHub organization profile README. Its links identify the distinct RoleCraft CLI and sibling repos; the CLI is already separately reviewed, so do not count this profile as a product implementation or as another harness/adapter. Inventory **101/303 reviewed, 202 pending**, next `rolecraft-sh/skills`. Full evidence: `docs/research/evidence/rolecraft-github-profile-review-2026-11-21.txt`.


## 2026-11-21 research checkpoint — candidate #102 rolecraft-sh/skills

Reviewed `12b10bccadd7348235ee49bf4b18bc6729616e01`: archived MIT Skills corpus with 52 markdown instructions, not a Project/Section/Session importer. Its Node script validates basic frontmatter only; no Harness loading, migrations, adapters, session event fidelity, attachments or Claude Desktop Chat/Cowork/Code gateway writer is present. The linked RoleCraft core CLI is a separate previously reviewed asset/config manager. The pinned Skills repo also has a stale README link to a nonexistent `skills/core/skill-orchestration` directory. Per-skill license metadata is self-declared and upstream provenance remains unverified. Inventory **102/303 reviewed, 201 pending**, next `sergionoodles/skillshard`. Research is active. Full ledger: `docs/research/evidence/rolecraft-skills-review-2026-11-21.txt`.


## Follow-up checkpoint — confirmed three Claude Desktop modes and candidate #103 (2026-11-21)

The user explicitly confirmed that destination evaluation must include **Chat, Cowork, and Code**, not only an undifferentiated “Claude Desktop” adapter. Keep these as separate mode/runtime axes alongside local/self-hosted Claude Code; third-party inference/API-key client behavior stays separate from Anthropic-hosted Cloud. Fresh first-party Help Center pages describe Claude Desktop on a cloud provider as a local-device history/project/memory store using configured provider inference, with a one-time source-specific import for that user's Claude.ai history plus local Cowork/Code sessions, not a generic ChatGPT export importer. Desktop session export is an unencrypted ZIP for same-OS/org Desktop-to-Desktop transfer, excludes Claude Code CLI sessions, and must be treated only as a backup interoperability test surface. Current Cowork help pages also distinguish cloud-executed consumer tasks from Desktop-on-3P local history; Project availability is Cowork-oriented and not yet a Claude Code Project API. These are version-volatile product facts; verify again against the user's target app version/OS before writing any adapter. Sources and full evidence: `docs/research/evidence/claude-desktop-3p-chat-cowork-code-2026-11-21.txt`.

Candidate #103 `sergionoodles/skillshard` (`05345c60ba4506add81eda1e3d97f0091738121c`, `v0.6.0`) is an adjacent Skills GUI, not a Project/Section/Session migrator. Its project scope is a path for `.agents/skills`; there is no ConversationGraph, attachment, token, subtask, schedule, or Desktop Chat/Cowork/Code writer. Partner audits fail open; license metadata is absent. Exact-HEAD Release build/package is green but no CI test workflow exists; local offline test run stopped at missing `gpui-kit` (exit 101). Do not copy its source. Registry now **103/303 reviewed, 200 pending**, next `stefanvo78/cross-agent-memory`; survey remains incomplete. Full ledger: `docs/research/evidence/skillshard-review-2026-11-21.txt`.

## Research checkpoint — candidate #104 cross-agent-memory (2026-11-21)

Cross-Agent Memory is an adjacent local-memory/Handoff product, not the requested lossless Project/Section/Session migration layer. It ingests Copilot CLI, local Claude Code and Gemini CLI through local hooks, runs deterministic heuristic summaries, stores a reduced session/knowledge model in SQLite/FTS/vector tables, and exposes MCP tools plus optional Git-shared summary bundles. ChatGPT/Codex is planned, not implemented; it has no Claude Desktop Chat/Cowork/Code third-party-provider support. The model and sync bundle omit branches/subtasks/Sections, attachments/media, token usage, tool event lineage, schedules, skills/plugins, and native session restoration. Keep as a high-relevance derived-memory pattern, separate from the canonical lossless archive.

Exact-head GitHub Actions CI run 22786695786 passed; local tests were not run because the checkout has no dependencies and no package install was performed. package.json says MIT but no LICENSE file/GitHub license metadata was found. Source review recorded a Claude MEMORY.md persistence bug, Gemini project-identity fallback, hook configuration clobbering, and likely orphan-vector risk on upsert; these remain source-level findings rather than runtime repros. Dashboard listener/auth must be rechecked before any deployment. Detailed ledger: docs/research/evidence/cross-agent-memory-review-2026-11-21.txt.

Registry is now **104/303 reviewed, 199 pending**; next candidate is thesmart/install. User scope remains all three Claude Desktop modes via third-party inference plus local/self-hosted Claude Code, with Anthropic-hosted Cloud separate. Research is still incremental; no real ChatGPT export or target restore has been performed.

## Research checkpoint — candidate #105 thesmart/install (2026-11-21)

The candidate is a package-manager Agent Skill, not a Harness migration system: it has no Project/Section/Session graph, source import, or Claude Desktop mode adapter. Its explicit user-consent gate is a helpful safety principle to independently apply to any future tool-install feature. However, a harmless temporary-directory probe reproduced arbitrary shell command execution through the documented eval of bin/detect-platform output when the caller-controlled SHELL contains an unescaped quote/command substitution; no user/system package was touched. Its package reference also lists go search, which is absent from current official Go command documentation. There is no test suite or CI, and its PolyForm Internal Use license prohibits redistribution/sublicensing. Reject reuse and preserve only the consent design idea. Full evidence: docs/research/evidence/thesmart-install-review-2026-11-21.txt.

Candidate inventory: **105/303 reviewed, 198 pending**; next weiox/skm. The project remains non-complete and no user ChatGPT/Codex export or Claude Desktop restore has been tested.

## Research checkpoint — candidate #106 weiox/skm (2026-11-21)

SKM is an adjacent Skills ResourcePlane manager for Codex and Claude Code, using a source-of-truth tree plus generated shared symlink entrypoints. The README explicitly excludes chat history and tool-internal state; there is no Project/Section/session/branch/attachment importer and no Claude Desktop Chat/Cowork/Code mode support. Its six fake-home shell tests pass, but the same output reports removal of an unmanaged skill; a separate disposable fake-home probe confirmed bootstrap --force deletes existing regular skill directories under ~/.agents/skills and ~/.claude/skills before replacing the entrypoint roots. Doctor inspects symlinks only. The scripts do not enforce the README's requested per-operation destructive confirmation, and no CI or root license metadata is present. Retain only the independent source/export-view design idea; reject as migration dependency.

Candidate ledger and full probe details: docs/research/evidence/weiox-skm-review-2026-11-21.txt. Inventory now **106/303 reviewed, 197 pending**, next wess/loom. Research remains incomplete; no user skill directory or session data was touched.

## Research checkpoint — candidate #107 wess/loom (2026-11-21)

Loom is a narrow MIT Skill package manager, not a Projects/Sections/session migration tool. Its YAML manifests, source refs/archive checksums, and per-agent directory projection are possible ResourcePlane references only; no messages, branches, event provenance, attachments, usage, MCP/plugins, schedules, or Claude Desktop mode session writer exist. Local `cargo test --all-targets` passed 15 tests; exact-HEAD CI and Pages succeeded, but install/path logic has no covering tests. Isolated `/tmp` probes reproduced both an unconditional foreign-directory replacement and an accepted `../outside` skill name that installed outside the configured skills root and deleted a foreign marker. No actual user data was accessed. Reject as a migration dependency; independently implement strict path validation, immutable digest provenance, managed-target checks, dry-run/approval, staged write and rollback if building Skill projection. Full source/test/POC evidence: `docs/research/evidence/wess-loom-review-2026-11-21.txt`.

Candidate inventory: **107/303 reviewed, 196 pending**; next `yearzen1/LocalSkillManager`. User-confirmed scope remains local/self-hosted Claude Code plus all Claude Desktop modes (Chat, Cowork, Code) over third-party inference as separate mode/runtime axes. Research remains incomplete; no user ChatGPT export or target restore has been performed.

## Research checkpoint — candidate #108 yearzen1/LocalSkillManager (2026-11-22)

LocalSkillManager is a narrow local Skills manager with global/project directory scopes, copy-based `pull`/`push`, and nested global groups. These groups are lists of Skill IDs, not Project sections; project scope is `<cwd>/.agents/skills`, and no Session or host-mode adapter exists. Retain only its strict Skill-name validation, explicit no-overwrite default, symlink refusal, and staged atomic replacement/rollback as independent Skills ResourcePlane design references.

Verification is mixed: local add → group → pull into temporary project succeeded, `cargo fmt` and release build passed, while full `cargo test --all-targets` exits 101 on one read-only upgrade-permission test whose expectation does not match the earlier staging-download failure. Strict Clippy also exits 101 on an un-gated Windows-only helper on macOS; no upstream CI run is available. The candidate is MIT but HEAD 0.11.0 is ahead of latest observed v0.9.1 tag. Do not treat it as migration fidelity evidence. Full record: `docs/research/evidence/yearzen-localskillmanager-review-2026-11-22.txt`.

Candidate inventory: **108/303 reviewed, 195 pending**; next `zhuyansen/awesome-agent-skills-managers`. User-confirmed scope remains local/self-hosted Claude Code plus Claude Desktop Chat/Cowork/Code via third-party inference as separate runtimes. Research remains incomplete; no actual user export or session was accessed.

## 2026-11-22 scope reaffirmation and catalog expansion

The user reconfirmed that Claude Desktop Chat, Cowork, and Code all remain in scope as separate runtime/mode adapters, in addition to local/self-hosted Claude Code. Keep the third-party inference/API-key path separate from server-hosted Claude Code Cloud and do not conflate inference routing with Session import. Source target remains ChatGPT Projects, Section Groups, and the user-named Destruction Era hierarchy; no real export/session has been touched.

Candidate #109 screening added the pinned zhuyansen/awesome-agent-skills-managers static directory as a discovery input, not a product/dependency. Importing its 192 rows after deduplication adds 177 net-new Skills/resource-plane candidates; the primary API query set is now 109/303 reviewed / 194 pending and the supplemental queue has 177 unreviewed rows. The README-based external grades are not code audit or behavioral compatibility evidence. The external benchmark checks Skills install/remove/sync, not chat/session migration. Research remains incomplete; next primary candidate is zongwu233/skillctl.

Detailed data, benchmark limitations, and provenance are in docs/research/evidence/awesome-agent-skills-managers-review-2026-11-22.txt and docs/research/awesome-agent-skills-managers-supplemental-2026-11-22.json.

## 2026-11-22 research checkpoint — candidate #110 skillctl

Candidate #110 is a local Skills/resource manager, not a ChatGPT-to-Claude session migrator. Its directory inventory and profile layer may inform a separate AssetPlane adapter; its chars/4 description budget is not per-session usage. Local tests pass 57/57 but no upstream CI/release was observed. Isolated tests show user/project scope leakage for Codex, whole-block config replacement, malformed-settings overwrite, scanner fail-open parsing, source-symlink dereferencing, and delete-before-copy force behavior. Do not adopt unchanged; implement independently with transactional writes and fail-closed/versioned checks.

The target scope remains ChatGPT Projects / Section Groups / Session tree for Destruction Era and Claude Desktop Chat, Cowork, Code as distinct modes, plus local/self-hosted Claude Code. No real user export or target restore was performed. Inventory is 110/303 primary reviewed, 193 primary pending, plus 177 supplemental pending; next primary candidate is zzj1965186613/agentforge. Research remains incomplete. Full evidence: docs/research/evidence/zongwu233-skillctl-review-2026-11-22.txt.

## 2026-11-22 research checkpoint — candidate #111 AgentForge

AgentForge is a local Markdown-Skill installer plus bundled content, not a Session/Project migrator. Its marketplace API is stubbed; its Claude Code adapter emits slash commands, not native Skills; it does not represent Codex, Claude Desktop Chat/Cowork/Code, Projects, Section Groups, Session branches, attachments, memory, or schedules. Local tests pass 226/226, Ruff/format pass, and the visible CI run #6 is successful, but isolated POCs expose name-validation/path-containment gaps, symlink overwrite, and false update status. The PyPI slug shown in README belongs to an unrelated GPL project, creating a blocking install/distribution name collision. Do not adopt source or recommend the README pip command unchanged.

User scope is unchanged: ChatGPT Projects/Section Groups and Session hierarchy for Destruction Era to Claude Desktop's three separate modes plus local/self-hosted Claude Code. No account export or session was accessed. Inventory now 111/303 primary reviewed, 192 primary pending, plus 177 supplemental pending; next primary candidate is AidarKhusainov/agent-skills-manager. Research remains incomplete. Full evidence: docs/research/evidence/agentforge-review-2026-11-22.txt.

## 2026-11-22 research checkpoint — candidate #112 Agent Skills Manager

The user's current reply reconfirms that Claude Desktop Chat, Cowork, and Code are all required as separate destination modes; the existing plan/evidence already recorded this, and a scope check passed. Candidate #112 `AidarKhusainov/agent-skills-manager` is not a migration product: one stateless skill manages GitHub `SKILL.md` resources, with no ChatGPT Project/Section/session parser or Claude Desktop/Claude Code adapter. Local unit tests passed 26/26 and package validation passed; default-branch and PR CI passed, while runtime routing E2E and all external-write scenarios are explicitly not run. Use only its consent/provenance/edit-preservation patterns for a future ResourcePlane.

Inventory: 112/303 primary candidates reviewed, 191 primary pending; plus 177 supplemental pending. Next primary candidate: akhenda/inline-commenting-convention. Research remains incomplete. Full evidence: `docs/research/evidence/agent-skills-manager-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #113 inline-commenting-convention

The user's target scope remains ChatGPT Projects/Section Groups/Session hierarchy for Destruction Era, into Claude Desktop's Chat, Cowork, and Code modes under the third-party gateway/API-key setup, plus local/self-hosted Claude Code. Candidate #113 is a static coding-convention Skill; it has no session importer, target adapter, or automatic cross-Harness execution. The phrase “cross-harness” means manually copying instruction snippets. Keep it as a narrow optional InstructionPlane resource, not migration capability. Frontmatter parse passed; automated product tests are not applicable, and no CI/releases were observed.

Inventory: 113/303 primary candidates reviewed, 190 primary pending; 177 supplemental pending. Next: All-The-Vibes/ATV-PaperBoard. Research remains incomplete. Full evidence: `docs/research/evidence/akhenda-inline-commenting-convention-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #114 ATV-PaperBoard

The confirmed target remains ChatGPT Projects/Section Groups/Session hierarchy for Destruction Era to Claude Desktop Chat, Cowork and Code via a third-party gateway/API key, plus local/self-hosted Claude Code. Candidate #114 is a visual report-artifact tool, not a session importer: “sections” describe HTML layout; its per-harness gallery has no ChatGPT/Claude Desktop session graph, source IDs, attachments, memory, token usage or schedules. Local validation: 212/215 tests pass (3 skipped), Ruff, wheel/Twine, wheel smoke render and Claude/Copilot distribution parity pass. Treat unsanitized raw HTML as untrusted and do not rely on its lossy `.meta.yaml` for provenance. Keep only optional report presentation / shared-core adapter patterns.

Inventory: 114/303 primary candidates reviewed, 189 primary pending; 177 supplemental pending. Next candidate: BANCUNXUEBI/reno. Research remains incomplete. Full evidence: `docs/research/evidence/atv-paperboard-review-2026-11-22.txt`.



## 2026-11-22 research checkpoint — candidate #115 Reno

The user reconfirmed Claude Desktop Chat, Cowork and Code are all required as separate destination modes; local/self-hosted Claude Code remains separate. Candidate #115 BANCUNXUEBI/reno is a Windows-first Skills manager with 15-tool detection, not a ChatGPT Project/Section/Session importer. Its own README conflicts on MCP/Plugin readiness; source install lifecycle is Skills-only. Four isolated synthetic probes exposed ZIP path traversal, symlink scanner/copy mismatch, max-file truncation that still yields low, and nested-file loss during rollback. Native macOS tests had 23 %USERPROFILE% platform-expansion failures; with a process-local Windows-variable compatibility shim, 495/495 tests passed. Treat it only as an adjacent resource-inventory concept; do not adopt its code or claim migration support. No user export/session/key/account data was accessed.

Primary inventory: 115/303 reviewed, 188 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 365. Next primary candidate: Beicxxxx/cross-harness-sync. Research remains active and incomplete. Evidence: docs/research/evidence/reno-review-2026-11-22.txt.



## 2026-11-22 research checkpoint — candidate #116 cross-harness-sync

The user-confirmed destinations remain local/self-hosted Claude Code plus separate Claude Desktop Chat, Cowork and Code modes. Candidate #116 is a high-value narrow reference for project-level narrative continuity (git-backed CURRENT/TASK/BLOCKERS, decisions index, layered retrieval and handoff), but not a ChatGPT Projects/Section Groups/Session importer or fidelity adapter. It does not preserve source message trees, attachments, usage, memory stores or scheduled tasks; it explicitly says the verifier proves omission, not truth, and the lock is advisory.

Pinned main review found reproducible defects: force refresh overwrites partially filled state while preserving the placeholder; a negated .env gitignore rule is falsely reported as safely ignored; and on this macOS host the verifier exits before checks with AttributeError at st_file_attributes. Local main suite: 555 collected, 298 passed, 252 failed, 5 skipped. Open draft PR #7 proposes fixes to preserve state, check ignore negation, validate paths and recover failed migrations, but is not merged/released and does not fix the observed POSIX runtime crash. Keep only its state-plane architecture; do not adopt current main for actual memory state.

Primary inventory: 116/303 reviewed, 187 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 364. Next primary candidate: cagedbird-org/skills. Research remains active and incomplete. No user export/session/key/account data was accessed. Evidence: docs/research/evidence/cross-harness-sync-review-2026-11-22.txt.

## 2026-11-22 research checkpoint — candidate #117 cagedbird-org/skills

The scope remains ChatGPT Projects/Section Groups and Destruction Era session hierarchy to local/self-hosted Claude Code plus Claude Desktop Chat, Cowork and Code as separate modes. Candidate #117 is a pinned Go Skill installer/synchronizer, not a session migrator. The CLI separates manifest, lock, installed assets and symlink mirrors; this can inform a separate ResourcePlane only. It contains no Project/Section/EventGraph mapping, session import/export, media, usage, schedule, memory or Desktop mode adapters. Its `sync` restores files changed from the lock hash.

Pinned main `7e39209b5eb705714d2988f92ac35ca0b7334ba3`; Go vet, race tests and build/version succeeded. A synthetic `..` manifest name escaped the configured target and removed a sibling sentinel in a disposable temp directory; no user data was accessed. The GitHub owner repo is archived, latest listed release v0.5.31 predates the archive, and README's `cagedbird043` URL redirects to the archived page. Do not adopt the implementation as-is.

Primary inventory: 117/303 reviewed, 186 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 363. Next primary candidate: Dark-Ohm/pz-mod-manager. Research remains active and incomplete. No ChatGPT export/session/key/account data was accessed. Evidence: `docs/research/evidence/cagedbird-skills-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #118 PZ Mod Manager

Scope remains ChatGPT Projects / Section Groups / Destruction Era session hierarchy to local/self-hosted Claude Code and Claude Desktop Chat/Cowork/Code as separate modes. Candidate #118 is an MIT Project Zomboid manager, not a memory or Harness migration tool. Its code does provide an MCP stdio server over a shared CLI command table; a live isolated handshake exposed 50 domain-specific game tools and zero session/migration-named tools. `.pzpack` tracks PZ mod packs and server connection settings. Keep only the generic command-schema/mutation-hint integration pattern; exclude product state and binaries.

Pinned master `e04311449785d27b866c2993d27f6681302326b6`. Release workspace tests passed 62 with 4 ignored; build passed with 26 warnings. No game data or user config was accessed. Primary inventory: 118/303 reviewed, 185 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 362. Next primary candidate: ebenhzr1/agent-smith. Research remains active and incomplete. Evidence: `docs/research/evidence/dark-ohm-pz-mod-manager-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #119 Agent Smith

Target scope remains ChatGPT Projects / Section Groups / Destruction Era Session hierarchy to local/self-hosted Claude Code and three distinct Claude Desktop modes: Chat, Cowork and Code. Candidate #119 is a Skill catalog/CLI prototype, not a Session migration tool. Its format uses `skill.json` + `SKILL.md`, but the installer writes only to `~/.agent-smith/skills`; it ignores platform tags and configured installDir and has no destination adapter.

Behavioral probes against temporary fixtures found: (1) remote install fetches only registry.json and writes a generated stub instead of downloading the repository; (2) publish creates local metadata only; (3) a symlink at the destination lets installation write outside the advertised sandbox. README’s npm install name currently resolves to an unrelated LynxAI package; version 0.2.1 is not published under that name. Unit suite passes 28, but does not cover the installer; ESLint reports 120 errors/22 warnings and Prettier flags 14 files, with both CI checks masked by `|| true`. Reject as an implementation dependency; retain only generic versioned Skill metadata ideas after building real Harness destinations and symlink-safe writes.

Primary inventory: 119/303 reviewed, 184 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 361. Next primary candidate: erdemtuna/craft. Research remains active and incomplete. No user export/session/key/account data was accessed. Evidence: `docs/research/evidence/ebenhzr1-agent-smith-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #120 craft

The user goal remains the full ChatGPT Projects / Section Groups / Destruction Era Session structure and applicable Skills/MCP/plugin/memory/context/schedule resources to local/self-hosted Claude Code and Claude Desktop Chat/Cowork/Code as separate modes. Candidate #120 is only a Skill dependency manager. Its declarative `craft.yaml` plus `craft.pin.yaml`, MVS, subpath selection, immutable commits/content integrity, agent prompt and project-vs-global store are the best package-manager patterns encountered so far; they can inform a future ResourcePlane. It has no SessionGraph or Project/Section/transcript importer, media, token-use, memory/schedule, MCP/plugin or Desktop Chat/Cowork/Code adapters. Agent detection currently covers only Claude Code and Copilot; `--target` is manual.

Pinned signed v0.5.0/main commit `38a686ac308616ab2b6e7647b6ce3d50881fa18a`. All 13 packages pass race tests; vet/build/gofmt pass; statement coverage 60.2%. However current go-git/go-billy/x-crypto versions produce 20 symbol-reachable govulncheck advisories (additional package/module-only findings also reported), several directly concerning remote refs/tree/path handling and SSH credentials. The only open PR #34 also confirms a 201-vs-200 dependency-boundary defect. Do not deploy the pinned version against untrusted Skills until dependencies are updated and the advisory scan is clean. Primary inventory: 120/303 reviewed, 183 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 360. Next primary candidate: eugen1408/skill-sync. Research remains active and incomplete. Evidence: `docs/research/evidence/erdemtuna-craft-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #121 Skill Sync

Target scope remains ChatGPT Projects/Section Groups/Destruction Era session structure and applicable Skills/MCP/plugins/memory/context/schedules to local/self-hosted Claude Code and Claude Desktop Chat/Cowork/Code as distinct modes. Skill Sync is the strongest desktop-style Skill organizer in this reviewed slice: official/ Git/local sources, a canonical `.agents/skills` library, per-agent links, and a 72-ID static path table. It supports Skill distribution only; the table has Claude Code but not Desktop Chat/Cowork/Code, and no SessionGraph, Project/Section importer, MCP/plugin/memory transfer or conversation fidelity function.

Pinned release v0.9.0 (`fc78bf37f5531daef373031c732fe57f6a2f5abb`), 41 test files/274 pass, typecheck/lint/build pass, and packaged release exists. `npm audit --omit=dev` reports two high-severity production dependencies. A temp-only failure probe showed canonical `SKILL.md` removed when a reinstall’s source was missing, since copy logic removes destination before copying. Keep the UI/resource adapter concept, not the replacement semantics; a lossless importer must stage, validate and rollback all user content. Research status: 121/303 primary reviewed, 182 pending; supplemental net-new 177 pending; combined pending excluding manual additions 359. Next primary candidate: Hardt-LLC/AgentPack. Research remains active and incomplete. No user session/export/key/account data accessed. Evidence: `docs/research/evidence/eugen1408-skill-sync-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #122 AgentPack

Scope remains ChatGPT Projects/Section Groups/Destruction Era session structure and related Skills/MCP/plugins/memory/context/schedules to local/self-hosted Claude Code plus Claude Desktop Chat, Cowork and Code as separate modes. AgentPack is an adjacent high-value ResourcePlane reference, not a session migrator: its pack/workspace schemas and runtime handle Skills, MCP servers, instructions, hooks, plugin metadata, target profiles, gateway and config collection, but no Session/Project/Section graph, chat transcript/events/media/token ledger or schedule model. It maps `claude` to Claude Code and has no distinct Claude Desktop Chat/Cowork/Code projections.

Pinned v0.3.0/commit `b76f0e49ef39bbf4c32535c94e5ad08105416d29` (MIT, 1 GitHub star at review). Local install with lifecycle scripts disabled, all 65 test files/487 tests pass, and typecheck/lint/build pass. npmjs audit reports 2 high + 1 moderate production dependency advisories (smol-toml 1.7.0 and zod 3.25.76); treat these as dependency risk and require remediation before untrusted input reuse. Keep capability negotiation, reversible write ownership/adoption and review-inbox concepts. No user application/session/key data accessed. Primary inventory: 122/303 reviewed, 181 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 358. Next primary candidate: harsha-pyla/skillhub. Research remains active and incomplete. Evidence: `docs/research/evidence/hardt-llc-agentpack-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #123 SkillHub

Scope remains ChatGPT Projects/Section Groups/Destruction Era sessions and related assets to local/self-hosted Claude Code plus Claude Desktop Chat, Cowork and Code as separate modes. `harsha-pyla/skillhub` is only a four-path Skills CLI: it stores `SKILL.md` folders and a URL/commit/date lock record. It has no Project, Section, Session, transcript, MCP/plugin, memory, schedule or token model and cannot satisfy session migration.

Pinned `b48b55844ee5ac9de60933a7e164761f543c4b8e`; checkout package 1.2.0, latest GitHub release displayed v1.1.0; GitHub repository says MIT while published npm metadata says ISC and includes a self-dependency. Tests: 5 files/15 pass, build pass, npm production audit 0 vulnerabilities. Disposable mock/path probes confirmed URL-fed shell command construction, removal outside the Skills root via `../../victim`, and loss of an existing Skill on a failed replacement copy. Do not reuse its install/remove logic. Current vendor path docs also disagree with at least its Copilot/Gemini destinations; the separate Claude Desktop modes are unsupported. Keep only the high-level catalog/lock UX concept.

Primary inventory: 123/303 reviewed, 180 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 357. Next primary candidate: Hayatelin/skillhub. Research remains active and incomplete; no user app/account/session/key/global skill store accessed. Evidence: `docs/research/evidence/harsha-pyla-skillhub-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #124 Hayatelin/skillhub

The agreed scope remains ChatGPT Projects/Section Groups/Destruction Era sessions and related Skills/MCP/plugins/memory/context/schedules to local/self-hosted Claude Code plus Claude Desktop Chat, Cowork and Code as separate targets. Hayatelin/skillhub contributes a Python standard-library linter, scaffold, curated offline Skill registry and four project-local path adapters. It is an adjacent Skill ResourcePlane tool only: no Session/Project/Section graph or transcript, MCP, plugin, memory or schedule migration exists.

Pinned v1.0.0 initial commit `945a938bcf74a2c53a1444973eaa5aef6f0dbc68` (MIT, Python 3.8+). The 40-test standard-library suite passes, but its direct `../` tar test missed a reproduced symlink escape: on CPython 3.12.10, the exact `safe_extract_tar()` wrote a tar member outside its extraction root into a sibling disposable folder. The README claims traversal protection, but extraction uses `tar.extractall()` without link validation/filter; supported Python 3.8–3.13 do not default to the 3.14 `data` filter. Also no branch pin/commit lock and `--force` removes old skill before copy. Do not use its installer on untrusted packs; keep only lint/scaffold/catalog UX concepts.

Primary inventory: 124/303 reviewed, 179 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 356. Next primary candidate: jniltinho/ad-manager. Research remains active and incomplete. No user app/account/session/key data accessed. Evidence: `docs/research/evidence/hayatelin-skillhub-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #125 false positive

Scope remains cross-Harness transfer of ChatGPT Projects/Section Groups/Destruction Era sessions and related resources to local/self-hosted Claude Code plus Claude Desktop Chat/Cowork/Code separately. `jniltinho/ad-manager` (MIT, v0.30.0) is Active Directory/Samba administration, despite matching an “MCP manager” search. Its MCP endpoints operate AD users/groups/OUs/computers/DNS/policies; its signed-in operator sessions and SMB connection sessions are not LLM conversation state; its “migration” is AD/Samba data movement. No ChatGPT, Codex, Claude, Project, Section or conversation adapter exists. Pass from shortlist; no admin service, test environment, credentials or user data was accessed.

Primary inventory: 125/303 reviewed, 178 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 355. Next primary candidate: Juliusolsson05/agent-manager. Research remains active and incomplete. Evidence: `docs/research/evidence/jniltinho-ad-manager-review-2026-11-22.txt`.

## 2026-11-22 research checkpoint — candidate #126 Agent Manager

Scope remains ChatGPT Projects/Section Groups/Destruction Era sessions and related Skills/MCP/plugins/memory/context/schedules to local/self-hosted Claude Code plus Claude Desktop Chat/Cowork/Code separately. `Juliusolsson05/agent-manager` is a narrow project/global Markdown command and stdio-MCP manager for Claude Code, Cursor, Codex and OpenCode. It has no Skills or Session/Project/Section migration model, transcript/media/token data, plugin/session conversion, or Claude Desktop target modes.

Pinned v0.2.3, MIT, 51-commit/1-star snapshot. Build and typecheck pass; `npm audit --omit=dev` reports zero dependency advisories. Its `npm test` script is a TODO that exits 0 and no tests directory exists. Disposable temp probes reproduced `add ../../outside` writing outside the project command directory, Codex `mcp remove` JSON-parsing TOML and leaving the server entry, and an OpenCode MCP file/schema mismatch; MCP env values are stored plaintext. Keep only profile/adapter UX ideas, not security or compatibility semantics.

Primary inventory: 126/303 reviewed, 177 pending; supplemental net-new catalog: 177 pending; combined pending excluding manual additions: 354. Next primary candidate: KAFKA2306/agent-resources. Research remains active and incomplete; no user app/config/credential/session data accessed. Evidence: `docs/research/evidence/juliusolsson05-agent-manager-review-2026-11-22.txt`.


## 2026-11-22 follow-up — user reconfirmed all Claude Desktop modes; candidate #127

The user reconfirmed that **Chat, Cowork, and Code** are all in scope for Claude Desktop configured for third-party inference, in addition to local/self-hosted Claude Code. This is now a locked scope field, not a request to collapse the three target semantics into one writer. Fresh first-party documentation review adds an implementation constraint: Chat/Cowork UI selection is being rolled out as a unified conversation; account-based Cowork now runs new consumer-plan tasks in Anthropic's cloud by default, while older local tasks persist. The 3P gateway route uses a static API key or OIDC to call streaming `/v1/messages`; the gateway key is not an import credential. Claude Desktop 3P stores Chat/Cowork event/audit/session data under `local-agent-mode-sessions` and Code session metadata/transcripts in separate Claude Code stores. Project memory and local/hosted execution locality are additional scopes. Version and OS remain unresolved. See `docs/research/evidence/claude-desktop-3p-chat-cowork-code-2026-11-21.txt` (2026-11-22 addendum).

Candidate #127, `KAFKA2306/agent-resources`, is MIT and pinned at `b461929bd7138afa8211f8492662e972ff0776e1`. The `agr`/`agrx` package is useful only as a narrow Skills ResourcePlane reference: it has no source session reader, SessionGraph, ChatGPT Project/Section support, MCP/plugin/memory/schedule migration, or Claude Desktop target. Focused tests: 136 passed; CLI tests: 188 passed / 5 skipped; `ty` passes, Ruff reports 47 diagnostics, and the repository-wide offline suite has 19 unrelated contract/docs/dashboard failures. See `docs/research/evidence/kafka2306-agent-resources-review-2026-11-22.txt`.

Primary inventory: **127/303 reviewed, 176 pending**; supplemental net-new catalog: **177 pending**; combined pending excluding manual additions: **353**. Next primary candidate: `kayaman/agentskills`. Research remains active/incomplete. No user app, data, session, API key or global Skill store accessed.


## 2026-11-22 research checkpoint — candidate #128 kayaman/agentskills

Scope remains all Claude Desktop logical surfaces (Chat, Cowork, Code) plus local/self-hosted Claude Code, with Destruction Era as the corrected ChatGPT project name. `kayaman/agentskills` is a Rust Skill package manager, not a Projects/Sections/session/resource-plane migration system. Its eight detected agent markers do not correspond to eight adapters: the installed layout is always `.agents/skills`; official vendor docs validate that for Codex, Cursor, Copilot and OpenCode, whereas Claude Code documents `.claude/skills`, and Desktop Chat/Cowork skills use separate account/client behavior.

Pinned `a5093afcb84a27dbbd7a816f8e92bd5058313cf2`, Apache-2.0, v0.1.3. `cargo test --locked`: 58 passed; locked release build passed; rustfmt check failed and strict Clippy failed on 3 lints. Isolated `/tmp` probes reproduced remove-path traversal beyond `.agents/skills`, data loss on a failed overwrite with stale lock, omitted dotfile coverage, and an ambiguous tree-hash collision. Keep only Skills-format/registry concepts; reject its mutating implementation as a dependency. Evidence: `docs/research/evidence/kayaman-agentskills-review-2026-11-22.txt`.

Inventory: **128/303 primary reviewed, 175 pending**; 177 supplemental candidates pending; combined primary + supplemental pending: **352** excluding manual additions. Research is active and incomplete; next primary candidate is `kayaman/skillz`. No user app/session/key/data was accessed.


Current Skills-plane note: as of 2026-11-22, GitHub CLI `gh skill` documents a public-preview route for preview-first, target/scope-specific Skill installation, explicit tag/SHA pins and source/ref/tree-SHA provenance (CLI v2.90+). Evaluate it as a possible native ResourcePlane helper, without confusing Skills handling with session/project migration. `kayaman/agentskills` remains a reference only: its PR #6 is open/unmerged and contains a Copilot review warning about a missing advertised skill.


Candidate #128 additional verification: a temp project with a fake failing `git` executable made `agentskills update demo` log `Failed to update 'demo'` yet exit 0 and print `All skills are up to date.` Treat this as a machine-readable per-item error-reporting failure, separate from the tested path traversal, destructive replacement, and hash collisions. Full evidence: `docs/research/evidence/kayaman-agentskills-review-2026-11-22.txt`.


## 2026-11-22 research checkpoint — candidate #129 kayaman/skillz

`kayaman/skillz` is an Apache-2.0, one-commit Python parallel to the Rust `kayaman/agentskills` package. It still writes only `.agents/skills` and a v3 skill lock; it has no ChatGPT Project/Section/session model or Claude Desktop Chat/Cowork/Code adapter. 32 pytest tests, Ruff and Ruff format passed; mypy has one HTTPX typing error; no release/tag or CI workflow appeared in the checkout. Temporary probes reproduced traversal deletion, partial-destructive reinstall with stale lock, hash omissions/collision, false-success update status, and temp-dir leak after lock-write failure. Do not adopt as migration code. Full evidence: `docs/research/evidence/kayaman-skillz-review-2026-11-22.txt`.

Inventory: **129/303 reviewed, 174 primary pending**; 177 supplemental net-new pending; combined pending: **351** excluding manual additions. Next candidate: `MaNongJSZ/SkillHub`. Research remains active/incomplete; no user app, key, session or global skill path was accessed.


## 2026-11-22 research checkpoint — candidate #130

Primary review count: **130/303** (173 pending); 177 supplemental net-new candidates remain. `MaNongJSZ/SkillHub` is only an adjacent local Skills ResourcePlane; it does not migrate Project/Section/Session history. Its Windows-only, undocumented Claude Desktop 3P Skill path and three reproduced data-integrity/security failures make it unsuitable as a migration engine. Next primary candidate: `michaelmjhhhh/agent-skill-manager. Full pinned-source, test, build, and probe findings are in `docs/research/evidence/manongjsz-skillhub-review-2026-11-22.txt`.


## 2026-11-22 research checkpoint — candidate #131

Primary review count: **131/303** (172 pending); 177 supplemental net-new candidates remain. `michaelmjhhhh/agent-skill-manager` is a macOS Skill catalog with a local JSON bookmark collection, not a Project/Section/Session migrator or Claude Desktop 3P adapter. Its UX and safe removal patterns are adjacent references only; license remains unresolved. Next primary candidate: `msking18/cognitive-personas. Detailed pinned-source/test findings: `docs/research/evidence/michaelmjhhhh-agent-skill-manager-review-2026-11-22.txt`.


## 2026-11-22 research checkpoint — candidate #131

Primary review count: **131/303** (172 pending); 177 supplemental net-new remain. `michaelmjhhhh/agent-skill-manager` is a macOS local Skill browser and JSON bookmark catalog, not a Project/Section/Session migrator or Claude Desktop 3P adapter. Safe local removal and review-before-run UX are adjacent references; license is unresolved. Next primary candidate: `msking18/cognitive-personas. Full evidence: `docs/research/evidence/michaelmjhhhh-agent-skill-manager-review-2026-11-22.txt`.


## 2026-11-22 research checkpoint — candidate #132 and scope reconfirmation

The user reconfirmed that all three Claude Desktop surfaces—Chat, Cowork, and Code—remain in scope alongside local/self-hosted Claude Code; keep each as a distinct target adapter. The ChatGPT source remains Projects / Section Groups / full Session hierarchy for the project `Destruction Era` (not “Destruction error”).

Candidate #132 `msking18/cognitive-personas` at `1b4afc67b17020571f4c1db569f5ff666ad2d237` is an adjacent persona framework, not a migration engine. Its Claude Code adapter is `.claude/` output styles and its other documented targets are Cursor, Roo Code, GitHub Copilot, and Antigravity; there is no Claude Desktop Chat/Cowork/Code writer or ChatGPT Project/Section/Session graph. The `agent-memory-mcp` v3.2 tables/tools are a proposed RFC; implementation only reads a small amount of legacy pedagogy memory at SessionStart. Local Node v26.7.0: `rtk npm test` passed 30/30 and `rtk npm run lint-structure` passed 4/4. A disposable hook repro observed first same-category native decision `ask`, second `allow`: the marker is written before the prompt and the hook has no approval/denial feedback. Official Antigravity docs distinguish `ask` (respects Always Allow) from `force_ask` (ignores cached permissions); the plugin uses only `ask`. The installer force-copies without backup. Retain persona protocol/read-only hydration as optional design references; reject its gating/installer as a safe migration foundation. No app/user data, API key, installed plugin, or session store was accessed. Full pinned-source and test evidence: `docs/research/evidence/msking18-cognitive-personas-review-2026-11-22.txt`.

Inventory: **132/303 primary reviewed, 171 primary pending**; 177 supplemental net-new pending; combined primary + supplemental pending **348**, excluding manual additions. Next primary candidate: `ngmkhoi/tavily-mcp-manager`. The research is not complete; no accuracy claim is made for any migration mapping until export/runtime fixtures are tested.


## 2026-11-22 research checkpoint — candidate #133

The locked scope is unchanged: ChatGPT Projects / Section Groups / full Sessions (including `Destruction Era`) must be evaluated against local/self-hosted Claude Code and Claude Desktop third-party-inference Chat, Cowork, and Code as distinct targets. No general MCP/Plugin compatibility is inferred from matching one server's config format.

Candidate #133 `ngmkhoi/tavily-mcp-manager` (`5a4fb410288422f73d186dd11faae6b7bd4a782f`) is a Tavily-specific key store and launcher for one local MCP server, with Codex / Claude Code CLI / Gemini CLI / OpenCode config helpers. It is not an Anthropic/provider gateway credential tool, a Claude Desktop adapter, or a Project/Section/Session importer. Local `npm test` passed 64; `npm run check` passed; both pinned GitHub CI runs succeeded. Preserve only the separated secret-file, shell-safe serialization, atomic key-store and config-preview ideas for optional MCP ResourcePlane design. Disposable tests found that the Claude CLI-unavailable fallback silently replaces an existing Tavily entry without `--force`, changes 0600 config permissions to 0644 and creates a 0644 backup containing the old fixture secret; `mcp install all` also exits 0 with one failed/manual target. Do not adopt its config writer wholesale. Full evidence: `docs/research/evidence/ngmkhoi-tavily-mcp-manager-review-2026-11-22.txt`.

Inventory: **133/303 primary reviewed, 170 primary pending**; 177 supplemental net-new pending; combined pending **347**, excluding manual additions. Next primary candidate: `nicolavalenti/mem`. Research remains active and incomplete; no user key, Claude Desktop state, app data or session was touched.


## 2026-11-22 research checkpoint — candidate #134

The active user scope remains ChatGPT Projects / Section Groups / complete Destruction Era Sessions and their context/resources, mapped separately to local/self-hosted Claude Code and Claude Desktop 3P Chat, Cowork, and Code. A shared memory store does not constitute a session migration or native restore.

Candidate #134 `nicolavalenti/mem` (`24bab43df29181cb4dcdd50b26f7466b3e9dfd66`) is an adjacent local Context/Handoff tool: SQLite/vector recall shared across Claude Code, Codex and Pi, plus text-only transcript ingestion and idle summaries. It has no Project/Section/Session graph, parent-child branches, attachments/tools/token usage, ChatGPT export reader, Claude Desktop 3P mode adapter, or generic plugin/MCP/schedule migration. Python AST and shell syntax checks passed; the synthetic dry-run found 3 stale Claude/Pi/Codex transcripts without model calls; a synthetic Pi handoff emitted `claude --resume pi-synthetic-123`. The selected excerpt is summarized through the installed Claude CLI, so the local database does not guarantee that summary requests remain local. No formal tests, CI workflow, tag or release was found. Keep its explicit source/kind, incremental ingestion and handoff-freshness concepts; reject it as a native session-migration dependency. Evidence: `docs/research/evidence/nicolavalenti-mem-review-2026-11-22.txt`.

Inventory: **134/303 primary reviewed, 169 primary pending**; 177 supplemental net-new pending; combined pending **346**, excluding manual additions. Next candidate: `Primuez/skill-installer`. Research remains active/incomplete.


## 2026-11-22 research checkpoint — candidate #135

The requested scope is unchanged: migrate ChatGPT Projects / Section Groups / full Destruction Era Sessions and related resources to local/self-hosted Claude Code and Claude Desktop 3P Chat/Cowork/Code as separate targets. A Skill installer is not a session-graph adapter.

Candidate #135 `Primuez/skill-installer` (`7fa1548d16cc184a96806cc622133dd4c746b6d4`) only installs individual Skills to one directory and backs them up; it does not migrate projects, sessions, tools, attachments, memory or schedules. Its actual LICENSE is proprietary/non-commercial, while README text contradicts it by claiming MIT/commercial permission. There are no tests, CI workflows, releases or tags. Isolated no-network probes found: scanner exit 42/empty output marked SAFE; documented GitHub `/tree/` URL installed as HTML `SKILL.md`; and `../escaped` frontmatter name wrote outside the requested skills directory. The program can also create/push to GitHub and upload to GWS automatically; no such external side effect was exercised. Do not adopt this code. Full evidence: `docs/research/evidence/primuez-skill-installer-review-2026-11-22.txt`.

Inventory: **135/303 primary reviewed, 168 pending**; 177 supplemental net-new pending; combined pending **345**, excluding manual additions. Next candidate: `rbutera/harness-bridge`. Research remains active and incomplete.


## 2026-11-22 research checkpoint — candidate #136

用户已明确将 Claude Desktop 的 Chat、Cowork、Code 三种 mode 全部纳入；每种 mode 和本地/self-hosted Claude Code 仍必须是独立 target adapter。ChatGPT source scope 仍为 Projects、Section Groups 与 Destruction Era 的完整 Session/event/hierarchy/resources。

候选 #136 `rbutera/harness-bridge` 固定在 `31559c93be61fa6adec584b728f843e2f92330f3`（MIT，npm v1.0.0）。它只把 Claude Code CLI 与 Codex CLI 通过 MCP 做在线委派，不是 session importer；Claude `threadKey` 由内存 Map 映射到 session ID，bridge 重启后此映射不保留。源码无 `externalAgentConfig/detect` / `externalAgentConfig/import` 运行调用；出现相似生成类型不等于迁移功能。其 Codex CLI 默认总是带 `--dangerously-bypass-approvals-and-sandbox`，app-server 会请求 `danger-full-access`，不能直接给不受信任的 Harness/agent 调用。可保留 native thread ID 和实时委派概念，不采用其安全默认或作为项目/会话迁移依赖。

检查：直接运行已安装 Vitest entrypoint 为 17 文件、127 tests 通过；Oxfmt、Oxlint type-check、`tsdown` 生产构建及 publint 检查通过。冻结安装退出 1 的原因是本机 pnpm 11.25.0 拒绝执行未批准的 `esbuild@0.27.3` build script，尚未调用 `approve-builds`。固定 GitHub CI matrix 通过，npm/GitHub 最新 release 为 1.0.0。完整证据与原始 stdout/stderr 见 `docs/research/evidence/rbutera-harness-bridge-review-2026-11-22.txt`。

OpenAI Codex first-party source commit `8653ca9e99b2c805107bde7b7d6f57a634c643d0` 证实 `externalAgentConfig` 是一个定向的外部源→Codex importer：类型有 Skills/MCP/Memory/Plugins/Hooks/Subagents/Commands/Session path-cwd-title，但没有 Project/Section entity；session exporter 写入 Codex-native rollout/thread，不过主要以 user/assistant text records 投影，并生成 approximate token count 与 import marker，不重建 source tool calls / Project / Section / fork graph。官方 `openai/codex-plugin-cc` 调用该 API 是 Claude Code→Codex 方向。这个实现适合作为目标适配器和 loss-report 的对照，不是本项目 source/target 组合的通用迁移器。

原始 303 项语料当前 **136/303 primary reviewed、167 pending**；另有 **177** supplemental net-new pending；primary+supplemental combined pending **344**（不含手工补充项）。下一条 primary candidate：`rogue-dev-studio/rogue-skill-pack-managers-skill`。研究仍未完成；没有访问用户账号数据、导出或本机 Desktop store，也未执行任何真实凭据或远端写入。


## 2026-11-22 research checkpoint — candidate #137

候选 #137 `rogue-dev-studio/rogue-skill-pack-managers-skill` 固定 HEAD `ba9ff33055418484cb984136ee888c8dc1ace471`。这是一个只含 `SKILL.md` 文本的 marketplace 管理提示，README 提到 OpenSkills、agent-skills-cli 和 Claude marketplace；仓库没有可运行的 installer、session parser、测试或 CI。它要求读取 `TEAM.yaml` / `ALIASES.md`，但这两个文件不在候选仓库中；它也不处理 ChatGPT Projects/Sections/Sessions 或 Claude Desktop 3P 三种 mode。保留为低相关 Skill-workflow 样例，不作为 Nexus 迁移依赖。

本地 YAML frontmatter 检查确认必需字段、name 语法和 description 长度符合 Agent Skills spec；但 spec 还要求 Skill 安装目录名与 frontmatter `name` 一致。该候选元数据名为 `skill-pack-managers`，而 Git checkout 目录为 `rogue-skill-pack-managers-skill`；README 的 copy 指引没有给出如何建成规范目录的操作。许可证文本看似 MIT 且 README 声称 MIT，但 GitHub API 报告 `Other`，`NOTICE` 另要求发行时保留作者归属；商业复用前应核验许可与归属义务。官方 `skills-ref` 工具未安装；其上游说明它是 demonstration reference library，因此本次不把“未运行官方 validator”伪装成通过。

版本信号：1 star / 0 forks，4 commits，tag/release `v1.0.0`，最近 commit 2026-09-26；GitHub Actions 无 runs。固定代码树仅 5 个文件；CodeGraph status 0 source files / 0 nodes / 0 edges，索引为空但 up-to-date。完整记录见 `docs/research/evidence/rogue-dev-studio-skill-pack-managers-skill-review-2026-11-22.txt`。

当前候选计数 **137/303 primary reviewed、166 pending**；另有 **177 supplemental net-new pending**，总待审 **343**（不含 manual additions）。下一条 primary candidate：`safebuffer/cli-manager-mcp`。研究仍在进行，没有访问用户安装目录、会话数据或账号凭据。


## 2026-11-22 research checkpoint — candidate #138

候选 #138 `safebuffer/cli-manager-mcp` 固定 HEAD `92fd151a239994cbf8c94e723c2c7b59d5ca8d68`（Apache-2.0，1 star / 0 forks）。它是一个单文件 Python MCP server，提供后台 shell 执行、结果读取、列出与清理进程 4 个 tool；不是 Session/Project/Section 导入器，也不提供跨 Harness 的 MCP 配置/凭据迁移。MCP 输入只有 `cmd: str`，服务端 `subprocess.Popen(..., shell=True)` 以服务器用户权限直接执行；未实现 allowlist、sandbox、按调用审批、cwd 或执行超时。单实例全局内存 registry 会返回原始命令及完整 stdout/stderr，并记录命令日志；README 虽提醒仅与可信 Agent 或 sandbox 一起使用，但源码没有强制这一限制。作为安全边界反例记录，不作为 Nexus 插件/资源依赖。

检查：CodeGraph 索引 1 个 Python 文件、44 nodes、86 edges；Python AST parse 通过。tracked tree 无依赖清单、test、CI 或 release/tag，故没有正式测试/构建可运行。没有启动 MCP server 或执行 shell 输入。完整审查见 `docs/research/evidence/safebuffer-cli-manager-mcp-review-2026-11-22.txt`。

原始 303 项语料当前 **138/303 primary reviewed、165 pending**；另有 **177 supplemental net-new pending**；合计待审 **342**（不含 manual additions）。下一候选：`SebghatYusuf/skills-manager`。研究仍在进行，没有访问用户应用、账号或会话数据。


## 2026-11-22 research checkpoint — candidate #139

候选 #139 `SebghatYusuf/skills-manager` 固定 HEAD `980da978cc7d7ff27cd7cca74eb328baf95a738e`，是桌面 Skill 文件管理器，目标为 VS Code、OpenCode、Codex、Antigravity、Cursor、Claude Code；其 Claude target 只读写 `~/.claude/skills` 和项目 `.claude/skills`，不是 Claude Desktop 3P Chat/Cowork/Code，也不迁移 Projects/Sections/Sessions/MCP/plugins/memory/schedules。它可以作为 ResourcePlane UI 的邻接样例，不是 Nexus session migration engine。

固定源码检查发现：用户指定 `skillName` 找不到时会 fallback 到全量 discovered skills；多 Skill 安装中途冲突可能留下先前已写入目录；`deleteSkillAll` 依据 basename 清除所有目标根目录下同名路径，未逐项证明内容身份；README 所述 VS Code Copilot “symlink” 实际由 `copyDir` 复制。SkillsMP key 写入 `app.getPath("userData")/settings.json` 普通 JSON，没有应用层加密；它是搜索目录用的 key，不是 LLM/model key。Codex target 还包括 `/etc/codex/skills`，删除范围需谨慎审查。

许可证与质量：package.json 写 MIT，但固定 checkout 没有 LICENSE 文件且 GitHub license metadata 为 null；1 star / 0 fork，0.1.0 release/tag，最近推送 2026-02-12；GitHub Actions runs 为空且无 tests。缺少 node_modules，当前无 Yarn 4.11.0，故未运行 build/typecheck。CodeGraph 已索引 20 files / 240 nodes / 629 edges；保留 per-target skill discovery/enablement 作为 UX 参考，不复用代码或声称已验证运行。证据：`docs/research/evidence/sebghatyusuf-skills-manager-review-2026-11-22.txt`。

原始主语料当前 **139/303 reviewed、164 pending**；另有 **177 supplemental** 待审，主+补充合计 **341**（不含 manual additions）。下一候选 `sirrobot01/mnemo`。研究仍未完成；没有访问用户安装目录、API key 或会话数据。


## 2026-11-22 research checkpoint — candidate #140

候选 #140 `sirrobot01/mnemo` 固定 HEAD `6474642dbf02c6c1dc5858a9bce16888e041f1b8`。它是本地 coding-session catalog 与 Task/handoff 工具，不是 ChatGPT/Claude 通用迁移器。Domain 有 Session/Event/Task/WorkingState，但没有 Project、Section、附件、schedule、Session parent/fork/subtask/event-parent 实体。Task 与 Session 是 many-to-many；自动 thread 使用 repo + branch + 45 分钟 idle window，pinned Task 可覆盖 branch，这属于 continuity heuristic，不是原生会话树。WorkingState 是派生摘要/决策等状态，不能替代逐条 ConversationEvent。

源码审查发现 Claude reader 只拼接嵌套文本块，示例中嵌套 `tool_use` 未保存；Codex reader 虽映射 tool-call/result 类型，但结构体不接收 arguments/output；Continue reader 只保留文本并将事件时间写成 ingest time。它没有 ChatGPT export/project/section reader，也不支持 Claude Desktop 3P Chat/Cowork/Code。可借鉴 fingerprint 幂等导入、显式 derived-handoff 层、PostgreSQL 清除 raw event content/绝对路径的隐私边界；不可把搜索/摘要/handoff 当成源档案迁移。

本地 `rtk go test ./...` 因环境没有 Go executable 而无法启动（exit 1）；GitHub v0.1 release CI run `26256191646` 于固定 `b3f7c6d69854bee68cd4f39ced9989bb15e04f4e` 成功。`v0.1..HEAD` 仅文档/网站与 `.gitignore` 变化、不含 Go source，因此“测试覆盖相同 Go 实现”是由 diff 得出的推断，不代表当前 HEAD 本地重跑通过。CodeGraph status 为 99 files / 1,664 nodes / 4,294 edges，up-to-date。详细 source/test limitation 见 `docs/research/evidence/sirrobot01-mnemo-review-2026-11-22.txt`。

原始主语料当前 **140/303 reviewed、163 pending**；另有 **177 supplemental net-new pending**；主+补充合计待审 **340**（不含 manual additions）。下一候选 `timonwong/skimi`。研究仍未完成；没有读取用户本机 session store、访问模型凭据或执行目标端写入。


## 2026-11-22 research checkpoint — candidate #141

候选 #141 timonwong/skimi 固定在 HEAD 8814b0f64b5afd492999cab6766931e4f7285f03（v0.3.1，MIT）。它是相对完整的 Skill ResourcePlane CLI：skills.yaml、skills-lock.yaml、来源/commit/linked path 记录、5 个 user-home target（Claude Code、.agents、Codex、OpenClaw、Pi）、name/path selector、agent include/exclude、last-wins collision report，以及 link/lock 写入失败后的 rollback。它不是 SessionGraph 或 Project/Section 迁移器，也没有 Claude Desktop 3P Chat/Cowork/Code 目标 adapter，因此只作为架构参考，不作为会话迁移依赖。

源码边界：repo subdirectory 被拼到 clone path 时没有 containment 校验，source-level 推断为潜在 path-confinement 风险；没有执行 exploit。更重要的是 Run 先 pull source repo，再发现 Skill 并提交链接/lock；target 是指向 mutable checkout 的 symlink，所以后续 planning/lock 失败无法恢复已更新的 Skill 内容。应借鉴事务与 ownership 校验，但 Nexus 写入需采用 staging、内容 hash/immutable snapshot 和 atomic publish。默认配置安装是 full desired-state sync，可能 prune 不在配置中的 managed Skills；集成 UI 应显式呈现 destructive scope。

GitHub CI / Release runs 31807172874 / 31807172997 在 pinned HEAD 成功；CI 定义 build、vet、race test、lint。15 个 Go test 文件共 66 个顶层 Test 函数；本地 rtk go test ./... 因当前没有 Go executable 而无法启动（exit 1，不是代码测试失败）。CodeGraph index 为 41 files / 519 nodes / 1,249 edges，up-to-date。完整证据见 docs/research/evidence/timonwong-skimi-review-2026-11-22.txt。

原始主语料当前 **141/303 reviewed、162 pending**；另有 **177 supplemental net-new pending**；主+补充合计待审 **339**（不含 manual additions）。下一候选 xpera-ch/goodboy。研究仍未完成；没有安装 Skill、扫描用户目录、访问凭据或写入真实 target。


## 2026-11-22 research checkpoint — candidate #142

候选 #142 xpera-ch/goodboy 固定 HEAD 5e3620c87eb80fc32ff0176caa85f556615a097d，MIT，GitHub CI 在该提交通过。GoodBoy 是本地 Skill registry / integrity checker：project install 只到 .claude/skills，global links 目标为 Claude Code、Codex、Gemini 和共享 .agents。它没有 ChatGPT Project/Section/Session importer，也不支持 Claude Desktop 3P 的 Chat/Cowork/Code；Phase 1 的 RegistryClient 仍是 stub，不存在 remote registry sync。

实测本机 Node 26.7 的 CI 路径：generated-types verify、CLI build、E2E 5/5、registry-client build 和 coverage 36 files / 776 passed / 3 skipped 均通过；覆盖率 100% statements/functions/lines、99.83% branches。第一次 coverage 失败原因是仓库扫描器把本次 CodeGraph 生成的 .codegraph/codegraph.db 当普通文件扫描；临时移走索引后通过，再恢复原 DB，SHA 未变、CodeGraph status up-to-date。

关键不兼容：goodboy.json 与 goodboy.lock 看似可复现，但真实 restore 调用只按 skill name 解析 registry latest；临时 HOME 的 synthetic fixture 有 manifest range ^1.0.0 和 lock 1.0.0，而本地 registry 有 1.0.0/2.0.0，执行 installFromManifest 后装入 2.0.0 且把 range 改写成 ^2.0.0。另两项隔离 probe：global link 会覆盖同名但指向别处的 symlink；Codex 的 shared .agents symlink 先创建后，遇到 .codex 同名真实目录冲突时留下未记录的 partial link。没有触及用户目录或真实凭据。GoodBoy 适合借鉴 local content hash / versioned store 与 consent UX，不可原样采用其锁恢复与多目标写入语义。

详细 evidence：docs/research/evidence/xpera-ch-goodboy-review-2026-11-22.txt。原始语料当前 **142/303 reviewed、161 pending**；另有 177 supplemental net-new pending，合计待审 **338**（不含 manual additions）。下一候选 ylz201/keyvault。研究仍未完成；未访问用户 session、Desktop store 或 credentials。


## 2026-11-22 research checkpoint — candidate #143 and refreshed Claude Desktop 3P model

用户已确认目标端包含 Claude Desktop 的 Chat、Cowork、Code 全部三种 mode，另含本地/自托管 Claude Code；这里的第三方 inference gateway 不是 Anthropic 托管 Cloud session。对官方文档的当日复核发现 Claude Desktop 3P 已提供 Claude 自有数据的跨设备 import/export：ZIP 可含 session、Projects/files、memory、scheduled tasks、Skills、uploaded plugins、部分 preferences 和 local MCP commands，并可能含密码/API Key，必须作为敏感档案处理。该原生导入面接受 Claude.ai history 和受支持的旧版 Claude Desktop/Cowork/Code data，不是 ChatGPT/Codex 的通用 importer。目标侧按 mode 与 version 保存清晰 loss ledger；不要将私有磁盘结构等同稳定公开写入 API。

官方数据边界：Chat/Cowork 的会话文件、transcript、uploads/outputs、audit、memory 位于 `local-agent-mode-sessions/`；Code metadata 位于 `claude-code-sessions/`，而 transcript JSONL 仍在 `~/.claude/projects/`。audit 会记录 prompts、responses、tool inputs/results、thinking、permission decisions、model 与 token usage；该文件未加密。Chat/Cowork Project memory 是独立目录层。Unified Claude 会改变 home-screen 对话落到 Chat 还是 Cowork，故 canonical graph 必须分别保存稳定 surface/deployment 与 UI label。证据：`docs/research/evidence/claude-desktop-3p-current-review-2026-11-22.txt`。

本轮候选 #143 `ylz201/keyvault` 固定 main HEAD `b6ac537c511f5670ab07a0c7334bf49e8fe9274e`（MIT）。当前 main 是本机加密 secrets vault + CLI/MCP/SDK，没有 ChatGPT parser、Project/Section/Session graph、transcript/media/token codec 或 Claude Desktop 3P writer。MCP policy 默认 deny，但允许 `secrets_get` 后会把 plaintext secret 交给 MCP tool context；应只借鉴 SecretPlane 的本机加密和 deny-by-default 原则，Nexus archive 只保存 opaque credential reference/relink requirement。

Open PR #1 的独立 Agent Credential Gateway (`a515e4fbb3d83f7815c9fe21acd0f8b93e8a0956`) 目前仍 unmerged。它有独立 Unix RPC、固定 HTTPS GET/grant、期限/用量限制、revision-bound credential、atomic no-retry reservations、allowlisted output projection 与 secret-free error/audit，方向值得抽取为架构原则；但它是 POSIX alpha、非通用模型推理网关，不写 Desktop inference config，也不迁移会话。PR CI 对 PR synthetic merge commit 报告 Python 3.10/3.12/3.13 各 95 passed；current main 隔离本地 suite 11/11 passed（file backend，未启用 host keyring 或可选 MCP SDK）。完整审查：`docs/research/evidence/ylz201-keyvault-review-2026-11-22.txt`。

当前原始候选语料 **143/303 reviewed、160 pending**；177 supplemental net-new pending；主+补充待审 **337**（不含 manual additions）。下一 primary candidate：`agents-mcp/cli`。研究未完成；没有访问用户聊天导出、密钥、Claude Desktop store 或做目标写入。


## 2026-11-22 research checkpoint — candidate #144 agents-mcp/cli

候选 #144 固定在 `agents-mcp/cli` HEAD `cbf03ff339f876dbb3d7792a806c1c30bf3d4c6e`。它是 MCP 配置的项目/全局 compiler，不是 Projects/Sections/Session 转换器。运行时 adapter 覆盖 Claude Code CLI、Cursor、VS Code、OpenCode、Windsurf、Zed、Antigravity；不覆盖 Codex 或 Claude Desktop 的 Chat/Cowork/Code、第三方 gateway 设置、会话历史、附件、记忆、Skills/定时任务图。Antigravity 输出为 per-plugin 文件，而 import 只扫描有单一配置路径的 adapter。字段矩阵记录了 cwd 丢失、fallback placeholder 丢失、HTTP/SSE 推断等降级。

可借鉴纯 adapter、loss warning、JSONC 局部修改、managed-name ownership 与单文件 atomic write；但不能把 `.agents/mcp.json` 宣称为被广泛 Harness 原生采用的现行标准。它引用 Agent Plugins MCP 1.0.0 schema，却扩展到项目/全局目录和 URL/header placeholder。Agent Plugins 上游标准则规定 `mcp.json` 位于插件根，未定义 portable credentials，并要求远端 header 不含密钥。

临时合成验证发现：默认 `import` 对已识别的伪 `ghp_...` key 发出警告却仍把明文写入 canonical 与生成的插件 mcp.json；未识别的伪 `CUSTOM_SETTING` secret 未告警也保留。显式 `--extract-secrets` 会转成 placeholder、将 `.env` 写为 0600、只在 `.env.example` 写 key，并更新 gitignore。`import --no-sync` 实际仍执行 sync；同名不同配置静默取第一个 adapter；canonical server 名 `../../../escape` 可通过 Zod 并使 sync 在项目根外写入 `.agents/plugins` 文件。所有 POC 都使用 `/tmp` 合成目录/伪凭据，未接触用户项目。

验证：干净 checkout 的 `npm run verify` 因先跑 packaging test、后 build，缺 `dist/index.js` 而失败；CI 在 Node 22/24/26 重现。Windows path 测试另因断言 POSIX `/` 而失败。手动 build 后 `npm test` 为 332/332、`npm run verify` 通过，但这不能证明干净 CI gate 通过。项目无 GitHub release，页面显示 0 stars / 0 forks。结论：仅作为 MCP ResourcePlane 架构参考；不作为 Nexus 迁移依赖。详见 `docs/research/evidence/agents-mcp-cli-review-2026-11-22.txt`。

原始候选语料现为 **144/303 reviewed、159 pending**；177 supplemental net-new pending；主+补充待审 **336**（不含 manual additions）。下一候选 `1naruto-1/agent-connect`。研究未完成；没有访问用户会话、密钥或写入用户目标。


## 2026-11-22 research checkpoint — candidate #144 agents-mcp/cli

候选 #144 固定在 `agents-mcp/cli` HEAD `cbf03ff339f876dbb3d7792a806c1c30bf3d4c6e`。它是 MCP 配置的项目/全局 compiler，不是 Projects/Sections/Session 转换器。运行时 adapter 覆盖 Claude Code CLI、Cursor、VS Code、OpenCode、Windsurf、Zed、Antigravity；不覆盖 Codex 或 Claude Desktop 的 Chat/Cowork/Code、第三方 gateway 设置、会话历史、附件、记忆、Skills/定时任务图。Antigravity 输出为 per-plugin 文件，而 import 只扫描有单一配置路径的 adapter。字段矩阵记录了 cwd 丢失、fallback placeholder 丢失、HTTP/SSE 推断等降级。

可借鉴纯 adapter、loss warning、JSONC 局部修改、managed-name ownership 与单文件 atomic write；但不能把 `.agents/mcp.json` 宣称为被广泛 Harness 原生采用的现行标准。它引用 Agent Plugins MCP 1.0.0 schema，却扩展到项目/全局目录和 URL/header placeholder。Agent Plugins 上游标准则规定 `mcp.json` 位于插件根，未定义 portable credentials，并要求远端 header 不含密钥。

临时合成验证发现：默认 `import` 对已识别的伪 `ghp_...` key 发出警告却仍把明文写入 canonical 与生成的插件 mcp.json；未识别的伪 `CUSTOM_SETTING` secret 未告警也保留。显式 `--extract-secrets` 会转成 placeholder、将 `.env` 写为 0600、只在 `.env.example` 写 key，并更新 gitignore。`import --no-sync` 实际仍执行 sync；同名不同配置静默取第一个 adapter；canonical server 名 `../../../escape` 可通过 Zod 并使 sync 在项目根外写入 `.agents/plugins` 文件。所有 POC 都使用 `/tmp` 合成目录/伪凭据，未接触用户项目。

验证：干净 checkout 的 `npm run verify` 因先跑 packaging test、后 build，缺 `dist/index.js` 而失败；CI 在 Node 22/24/26 重现。Windows path 测试另因断言 POSIX `/` 而失败。手动 build 后 `npm test` 为 332/332、`npm run verify` 通过，但这不能证明干净 CI gate 通过。项目无 GitHub release，页面显示 0 stars / 0 forks。结论：仅作为 MCP ResourcePlane 架构参考；不作为 Nexus 迁移依赖。详见 `docs/research/evidence/agents-mcp-cli-review-2026-11-22.txt`。

原始候选语料现为 **144/303 reviewed、159 pending**；177 supplemental net-new pending；主+补充待审 **336**（不含 manual additions）。下一候选 `LKCY23/agent-session-migration`。研究未完成；没有访问用户会话、密钥或写入用户目标。


## 2026-11-22 research checkpoint — candidate #145 LKCY23/agent-session-migration; Claude Desktop scope

用户确认 Claude Desktop 3P 的目标范围是全部三种模式：Chat、Cowork、Code；其中包括本地/自托管 Claude Code 与可由开发者模式配置第三方网关的 Desktop session。官方 3P 文档将其定义为完整桌面体验，Chat/Cowork 对话位于 `local-agent-mode-sessions/`，Code 元数据在 `claude-code-sessions/`，可续接 transcript 仍在 `~/.claude/projects/`。官方导入流程是 Claude 来源历史/应用数据的迁移，不能据此推断存在通用 ChatGPT Project/Section importer。Code-only JSONL writer 仍是部分支持，不能当作满足全部目标。

候选 #145 `LKCY23/agent-session-migration` 固定于 clone HEAD `5d2c56b1662a4c5da1c95949ad17643a7d304b19`。它是 Skill + 四个已有 CLI/插件的安装与编排说明，不是 session graph converter；矩阵仅列 Codex、Claude Code、Pi、DSH 与 Antigravity，无 ChatGPT Web、Projects/Sections、Claude Desktop 3P Chat/Cowork、API-key gateway、portable MCP/plugin/skills/memory/schedule graph。无检测到 license/许可证文件，GitHub 0 stars/0 forks；不要作为 Nexus 实现依赖。保留其 preview-first、源会话不删除、显式损失和目标 session reopen/resume 的流程提示即可。

真实 pinned-upstream 交叉核对暴露明显文档漂移：候选锁定 `session-migrate 0.12.0`、`harnext 0.8.2`、`dsh-chat-import 0.26.2`、`ccx 0.1.7`；截至本次核验，上游为 0.13.0、0.9.0、0.26.8、0.1.7。尤其上游 dsh-chat-import `v0.26.2` 已可从 ChatGPT `conversations.json` 导入会话；`branch:"all"` 把 conversation DAG 的每个 root→leaf branch 导成独立 DSH session，并可保留结构化 tool call/result。其文档还列出 preview、图像 attachment、token usage/time、compaction 与更广泛来源。候选自己的 `references/dsh-chat-import.md` 却把输入源缩减为 Codex/Claude/Pi，且未呈现 ChatGPT 及分支能力。此项让 DSH 成为下一步值得深审的**中间桥**，但它不是 Claude Desktop 3P writer；尚未从 parser 源码确认 ChatGPT Projects/Section membership 会如何处理，也未验证 ChatGPT → DSH → Claude Code 链的全链路恢复质量。

安全/质量检查：`scripts/tools.py install ccx --force` 对固定安装目录递归删除，并无条件 unlink `~/.local/bin/ccx`；只运行 `--dry-run`，没有实际安装。更新查询只读执行 exit 0，但本机四个 TLS lookup 全失败后仍报告 `has_updates:false`（JSON 里带每项错误）；没有把版本自动应用。冒烟脚本缺少 DSH 验证，缺命令时记作 skip 且所有 skip 仍 exit 0；默认 `ccx ls` 未隔离 `ANTIGRAVITY_HOME`，`--allow-ag-write` 会向真实 Antigravity Desktop 写入、清理 return code 被忽略，因此均未运行。完整来源、命令/边界和记录见 `docs/research/evidence/LKCY23-agent-session-migration-review-2026-11-22.txt`。

候选主语料本轮为 **145/303 reviewed、158 pending**；177 supplemental net-new pending；主+补充待审 **335**（不含 manual additions）。既有 `1naruto-1/agent-connect` deep-review 记录仍不重做；下一 executable action 选为 clone 并 source-audit pinned `Nwflower/dsh-chat-import v0.26.2`，重点检查 ChatGPT export parser 是否保存 Projects/Sections/thread DAG/工具/图像/附件，以及它导出至 Claude Code JSONL 时的实际损失。研究未完成；没有访问用户会话、密钥、Claude Desktop store，或向目标应用写入。


## 2026-11-22 supplemental source review #146 — Nwflower/dsh-chat-import v0.26.2

为核对候选 #145 所依赖、且可能承接 ChatGPT archive 的 DSH 中间桥，固定审阅 `Nwflower/dsh-chat-import` tag `v0.26.2` / HEAD `1e3e63e533abd709e646f49eca08e8a5c6de9176`（MIT）。上游最新 release 页面为 `v0.26.8`（2026-11-18）；本轮暂审的是候选所 pin 的旧版源码，下一步需比对最新版本的 ChatGPT parser/transfer 变化。

这是现有项目里最有价值的源格式桥之一：它能从 ChatGPT `conversations.json` 还原 `mapping` 图；`branch:"all"` 会把 root-to-leaf 各路径写成独立 DSH session，并有 FIFO 结构化工具 call/result 配对。ChatGPT 形状测试覆盖无 `children` 的 slim export、占位 root、浮点时间、安全 preview/output schema，以及 fake-host 真实 import。版本化 interchange v1 有 turns/steps、tool blocks、attachments、timestamps、provider usage、compaction 的表达；这些是 DSH 目标侧能力，不能倒推出 ChatGPT 源数据具备每个字段。

synthetic parser probe 发现这些边界：只使用 conversation id/title/create_time/mapping 与文本/已知 tool carrier，不读取 Project/Section、`current_node`、model 或 usage 字段；分支 session 只加 `sourceId` 后缀/标题，不保留 session 间显式边。默认“主”分支按最后 child 链选取（即使合成 `current_node` 指向另一个叶子）。非文本 `content.parts` 被忽略：合成 image-only user turn 被跳过，后续 assistant answer 被挂进上一个文本 prompt 的同一轮；工具结果 FIFO 配对，`isError` 固定 false。所有这些 probe 都只用合成数据。

ChatGPT official export 文档说 ZIP 里有 conversations JSON 及其他账户数据/资源；官方 Projects 文档描述了 chats、上传文件、instructions、project memory、branched chats 等完整工作区关系。当前 DSH ChatGPT importer 只消费指定 `conversations.json`，没有 ChatGPT Project/Section membership 或资源侧车适配器。此判断基于 importer 实现与官方描述之差异；在用户提供一个已脱敏、明确授权的真实导出前，不声称 Project 归属在某个隐藏字段里一定存在或不存在。

DSH 会话可另行 `export_chat({format:"claude"})` 写出 Claude Code JSONL，但必须有 cwd；ChatGPT 源本身不带 cwd，v0.26.2 guide 说明默认会落到专用 `dsh-chat-import-workspace`（或 per-project 模式 ungrouped）。另一个确切 drift：同版 Usage Guide 说 `import_chat` 的 `target` 参数可直接转投，然而 pin 中 `makeImportChatTool` 的 schema/`COMMON_PARAMS`/`EXTRA_PARAMS` 没有 `target`，`runImportSpec` 总是执行 DSH import。fake-host synthetic 调用附加 `target:"claude"`、cwd 和 outputDir，实测仍是 `mode=batch`, `imported=1`, DSH persistence 增一会话、没有 Claude 输出路径。Panel 有独立 `transferDiscoveryItem`，但这不能当作 tool-level API 支持。Claude Desktop 3P 的 Chat/Cowork `local-agent-mode-sessions/` 与 Code 的 `claude-code-sessions/`、`~/.claude/projects/` 结构不同；任何 Claude JSONL 输出只覆盖 Code transcript 路径，且需验证 Desktop 是否要通过 “Import Claude Code CLI Sessions…” 注册元数据。

质量门禁：ChatGPT 专项 `node --test test/chatgpt-shape.test.mjs` 9/9 pass；全套 `npm test` 在 macOS 1490/1491，唯一失败是无关 Goose 路径测试把 `process.platform` 传入实现却硬断言 Linux `.local/share` 路径（当前 `darwin` 实际为 `Library/Application Support/Block/goose`）。`check:coverage` 因同一失败退出 1；它显示全局行覆盖 95.58%、分支 82.68%、函数 92.16%。lint、check:linux、check:leaks、check:links、check:tests、build 都 exit 0。v0.26.2 精确 tag 的 GitHub release workflow 在 Ubuntu 上成功；其 release.yml 明确先跑 coverage、lint、cross-platform guard、leak/link/test-discipline、build，再发布。完整日志与 synthetic output 见 `docs/research/evidence/Nwflower-dsh-chat-import-review-2026-11-22.txt`。

结论：可借鉴其 per-source adapters、canonical turn/step IR、branch-all 选择、显式 degradation ledger、idempotent source fingerprints、preview 与 DSH 事件级 bundle 保护。它**不能单独完成** ChatGPT Project/Section → Claude Desktop 3P 的 Chat/Cowork/Code 全量迁移；至多验证一条 ChatGPT text/history → DSH → Claude Code local transcript 的受限 route。primary corpus 仍 **145/303 reviewed、158 pending**；supplemental net-new pending **177**；manual review additions 增至 **12**（本项 #146 已审 pinned v0.26.2，latest v0.26.8 source comparison 待做）。下一 executable action：clone `v0.26.8` 并 diff/复验当前 ChatGPT path。研究未完成；没有访问真实 ChatGPT 导出、API key、DSH profile、Claude Desktop store 或外部推理端点。

## 2026-11-22 current-release and destination-contract update — #146 Nwflower/dsh-chat-import

The earlier pinned v0.26.2 review is now compared with upstream latest v0.26.8 (`4b946717d67ee8f41919913f50f7571a4bd44945`). The release adds jcode and Cherry Studio support and broader maintenance, but the ChatGPT converter has no source diff between these tags. Focused ChatGPT/transfer/index tests pass 16/16; the full suite is 1,861/1,862 on this Mac with the sole failure an unrelated Goose path assertion. Local lint, Linux compatibility, leak, link, test-discipline and build gates pass. Exact v0.26.8 upstream release#9 is green. Full evidence: `docs/research/evidence/Nwflower-dsh-chat-import-review-2026-11-22.txt`.

**Target finding:** current v0.26.8 has two distinct paths. `import_chat` does not define a `target` field; a synthetic v0.26.8 fake-host call with `target:"claude"`, `cwd`, and `outputDir` still returns one DSH imported session with no output file. The separate sidebar transfer pipeline supports Claude Code, Codex, Kimi and OpenCode, and serializes Claude Code JSONL under `~/.claude/projects`; it neither models ChatGPT Project/Section membership nor writes Claude Desktop 3P Chat/Cowork session state or Code app registration metadata. Keep it as an adapter/IR and branch-preservation reference, not as the requested end-to-end migration backend.

**User-confirmed destination scope:** Claude Desktop on third-party inference in Chat, Cowork, and Code, plus local/self-hosted Claude Code. Official 3P setup's Developer Mode configuration and static gateway API key (`inferenceGatewayApiKey`) are compatible with this intended local client-managed flow. The gateway must speak Anthropic Messages API (`POST /v1/messages`, streaming/tool use; optional `/v1/models`); a plain OpenAI-compatible endpoint requires a translation layer. Do not confuse this with Anthropic-hosted Claude Code Cloud: hosted Cloud sessions use a different claude.ai login/deployment and are not launched/resumed by a 3P API key. The 3P importer is documented for Claude.ai archives and local earlier Cowork/Code sessions, not ChatGPT exports.

Architecture implication: preserve stable `deployment` + `surface` (Chat/Cowork/Code) and version-specific native object graph independently from mutable unified UI labels. Chat/Cowork state (`local-agent-mode-sessions`, uploads, outputs, audit, memory) and Code app metadata (`claude-code-sessions`) / transcript (`~/.claude/projects`) are separate. A Code-only JSONL exporter is not equivalent to all three modes. API credentials must never be copied into the Nexus archive; use credential relink references. Details and links: `docs/research/evidence/claude-desktop-3p-current-review-2026-11-22.txt`.

Inventory reconciliation: primary `repositories` records contain **145 reviewed / 158 unreviewed out of 303**; their JSON summary fields and `next_unreviewed` had lagged behind these statuses (139/164, incorrectly pointing at an already-reviewed record). This update recalculates those metadata fields from the record states and sets the next primary candidate to `ai-agent-manager/github-dispatcher-action`. Supplemental net-new catalog remains 177 pending, and manual additions are 12 after this supplemental Nwflower review. Primary+supplemental pending = 335; counts are screening progress, not a completeness claim. The current manual-addition status and exact test evidence are in `docs/research/github-candidates.json` and the evidence file. Research remains incomplete.

## 2026-11-22 primary candidate #146 — ai-agent-manager/github-dispatcher-action

Reviewed current `main` at `dc81e8a6ebfd4814b94d7b2d8fe353c03679441d` (package v2.1.1; latest release tag v2.1.1). It is a well-engineered GitHub CI skill dispatcher for PR/comment events, not a transcript or Project migration engine. Its config and output/autonomy surface is useful for Nexus Memory's future resource-plane / workflow-trigger module, but it does not carry ChatGPT/Codex session trees, Projects/Sections, attachments, memories, MCP/plugins, schedules, token ledgers, or Claude Desktop 3P native state. Tool adapters cover Claude Code CLI, GitHub Copilot CLI and pi only; Claude Desktop Chat/Cowork/Code are not target adapters.

Local `npm run validate` passed: typecheck + 90/90 tests + bundled build + lint. Upstream CI#259 is green on this exact main SHA. Important deployment risk: execution is approval-bypassed (`--dangerously-skip-permissions`, Copilot `--yolo`, pi `-a`); `act` does `git add -A` and pushes; the action does not enforce comment-author association itself. README warns against untrusted fork PRs and recommends consumer workflow gating. Runtime skill installer defaults to `agent-manager-ref: latest`, so production workflows should pin it. Full evidence: `docs/research/evidence/ai-agent-manager-github-dispatcher-action-review-2026-11-22.txt`.

Primary inventory is **146/303 reviewed, 157 pending**; supplemental net-new catalog remains **177 pending**; manual additions remain 12. Primary+supplemental pending: **334**, excluding manual additions. Next primary candidate: `AJV009/ddev-drupal-devkit`. This is incremental screening progress, not a completeness claim.

## 2026-11-22 primary candidate #147 — AJV009/ddev-drupal-devkit

Reviewed default branch `main` at `c9c6ccd0d9d2e17851f5a9e8a695c4a2ea2aa84c`. Disposition: **exclude as migration engine**. This is a DDEV wrapper around the separate Drupal Devkit skills installer, not a ChatGPT/Codex conversation/Project/Section importer or a Claude Desktop 3P Chat/Cowork/Code adapter. The underlying Drupal Devkit's 8-harness skill/plugin emitter is a useful but separate resource-plane lead; it is not evidence of session continuity.

Static manifest audit found three missing `global_files` source paths and two post-install script references to files not installed by any `project_files`/`global_files` entry. `prompt-api-keys.sh` writes Anthropic API keys through `ddev config --web-environment-add`, while official DDEV docs place `web_environment` in `.ddev/config.yaml` and recommend gitignored `.ddev/.env.web.local` for secrets (supported from DDEV 1.25.4); this add-on claims minimum DDEV 1.24.10. The wrapper has six tracked files and no README/LICENSE/tests/CI/release; no DDEV runtime was executed. Shell syntax alone passes and is not an install check. Full evidence: `docs/research/evidence/AJV009-ddev-drupal-devkit-review-2026-11-22.txt`.

Primary inventory: **147/303 reviewed, 156 pending**; supplemental net-new catalog **177 pending**; primary+supplemental pending **333**, excluding manual additions (12). Next primary candidate: `ansonTGN/skills-hub-rs`. Research remains incomplete.


## 2026-11-22 scope confirmation and primary candidate #148

The user explicitly confirmed the Claude Desktop target covers **Chat + Cowork + Code**, using third-party gateway inference from the local Desktop client, plus **local/self-hosted Claude Code**. Model these as separate native targets: `desktop-3p/chat`, `desktop-3p/cowork`, `desktop-3p/code`, and `claude-code-local`. Do not call this hosted Claude Code Cloud, and do not equate the API-key/gateway route with a Claude.ai-account migration. The current official Desktop configuration reference exposes the 3P `gateway` provider, URL/key/auth-scheme fields, and distinct Chat/Cowork/Code surfaces; the official migration guide lists these app features and warns that its unencrypted session ZIP excludes Claude Code CLI sessions. This confirms the requested surface exists, not that ChatGPT/Codex archives can be imported losslessly. Preserve source lineage, native storage differences, and per-field degradation reports. Detailed source capture: `docs/research/evidence/claude-desktop-3p-scope-confirmation-2026-11-22.txt`.

Primary candidate #148 `ansonTGN/skills-hub-rs` was reviewed at main HEAD `085e986288ae212f1845834c9ee06282ece2e157`. It is a Rust Skills library/sync manager with 47 static Skills path adapters, not a Project/Section/session graph migrator; Claude Code `.claude/skills` is only a Skills target and MCPJam is only another Skills adapter. Core `cargo fmt`, 6/6 tests, strict Clippy, release build and isolated CLI Skill sync all passed. The repo remains useful only as a ResourcePlane reference. Source audit identified shallow Git refs stored without resolved commit SHA and a destructive `overwrite=true` path that removes a target before replacement without restoring it on later failure. No Tauri build or real user-target write was performed. Full review: `docs/research/evidence/ansonTGN-skills-hub-rs-review-2026-11-22.txt`.

Inventory: **148/303 primary reviewed, 155 pending**; supplemental net-new catalog **177 pending**; primary+supplemental pending **332** (excluding 12 manual additions). Next primary candidate: `anverse/agentskills-manager`. This is screening progress, not completion; the requested breadth/depth survey and universal loss-accounted migration design remain in progress.


## 2026-11-22 primary candidate #149 — anverse/agentskills-manager

Pinned default branch main at fbfa1dca5612dd4a348d85e05f6b02aff6065e64 (Apache-2.0). This is an early package-manager design for Agent Skills, not a session/project migrator. Despite the detailed README/spec, the actual CLI only implements help and version; there are no install/config/lockfile/Git/target mutation commands yet. Its latest release shown on GitHub is v0.0.1; README labels the repository concept/development phase, and the v0.1 production release remains a future milestone. Exact main CI #2 is green, but it exercises only this skeleton and its help/version scripts.

The spec is unusually useful for the Skills ResourcePlane: deterministic tree hashing, immutable content-addressed store, resolved commit/content pins, copy-vs-symlink strategy, and ownership-safe deletion/conflict behavior. These remain design-only. It has no ChatGPT/Codex Projects/Sections/sessions/transcripts/attachments/token records, MCP/plugins/memory/schedules, Desktop 3P Chat/Cowork/Code, or local Claude Code session adapter. Full source/spec/runtime evidence: docs/research/evidence/anverse-agentskills-manager-review-2026-11-22.txt.

Local temporary Go 1.26.11 checks: test, coverage, vet, gofmt, build, and the actual binary help/version passed. The full test suite is only help/version coverage; cmd/asm has 0% statements. No Skills install was attempted because the binary has no installer command. Upstream CI uses Go 1.26.2. No user directories or credentials were accessed.

Inventory: 149/303 primary reviewed, 154 pending; supplemental net-new catalog 177 pending; primary+supplemental pending 331 (excluding 12 manual additions). Next primary candidate, from the first remaining unreviewed index record: arthamegayasa/nam-stack. Research remains incomplete.


## 2026-11-22 primary candidate #150 — arthamegayasa/nam-stack

Reviewed isolated default-branch `main` at exact HEAD `d645ff1438f90f6d19e5ded3cecf3f51f35dfc49` (MIT; GitHub snapshot: 0 stars/0 forks; no releases). This is a personal five-Skill content repository for Claude Code, Codex, and Grok Build, not a Skills manager or a project/session migrator. It has no Projects, Sections, conversation trees, MCP/plugin manifest, memory, schedules, or cross-harness import/export. Repository validation and self-test pass; 13 fake-HTTP tests pass with local socket ResourceWarnings. A temporary-only `--name ../escaped` probe reproduced output path traversal in `openai_image.py`; the same unchecked path join exists in `openrouter_image.py`. No real provider request, key, or user path was used. Preserve it only as a Skill-content and portability/security fixture. Full evidence: `docs/research/evidence/arthamegayasa-nam-stack-review-2026-11-22.txt`.

The README's unpinned direct dependency `xingkongliang/skills-manager` is recorded as a separate **manual pending source audit**, not credited with functionality until its implementation is reviewed. Candidate #150 reinforces that raw `SKILL.md` presence is not equivalent to a working target deployment: tool assumptions, API credentials, scripts, grants, and the required Desktop plugin/marketplace packaging must be represented independently.

### Target confirmation — all Claude Desktop modes

The user explicitly confirmed that Claude Desktop third-party-inference coverage must include **Chat, Cowork, and Code**, all three, plus local/self-hosted Claude Code. Each Desktop mode is a separate adapter/acceptance track; a successful Chat or Cowork test does not establish Code support. Current official docs continue to say Claude-account-synced Skills do not sync into Claude Code when API-key or third-party/cloud-provider auth is used; use locally provisioned plugin/marketplace routes and verify per surface instead of assuming account sync. Vendor source map and limitations: `docs/research/evidence/claude-desktop-3p-skills-routing-2026-11-22.txt`.

Inventory: **150/303 primary reviewed, 153 pending**; supplemental catalog **177 pending**; combined primary+supplemental pending **330**; manual additions **13**, of which **1 pending** (the direct Skills Manager dependency); total unresolved including manual: **331**. Next primary candidate from the updated index: `arynull/skillden`. Research and platform verification remain in progress.


## 2026-11-22 primary candidate #151 — arynull/skillden

Reviewed isolated `main` at exact HEAD `23104d439ccfc169ad310076f73c46443125e47c` (MIT; GitHub snapshot 0 stars/0 forks; latest release v0.5.1; upstream CI #10 on this commit green). This is a local packaged-Skill manager, not a conversation/project migrator. The actual adapter list is only `claude-code` (`~/.claude/skills`), Cursor, and generic. It has no Claude Desktop 3P Chat/Cowork/Code, Codex, DeepSeek, ChatGPT Project/Section/session, MCP/plugin, memory, or schedule transport.

Isolated Python 3.12.4 installation, Ruff, and 12 local CI-style registry/install/uninstall/project pin/sync smoke commands passed. Source/runtime review found: CLI `--version` prints 0.4.0 despite package 0.5.1; `info` omits description/author/license; installing `acme/demo` then `other/demo` silently overwrites the same basename path without `--force`; and crafted project pins `author/..` caused `unpin` to remove project sentinel/pin/installed Skill files inside a temporary project before exit 1. Existing replacement is delete-then-rename without rollback (static risk). No user files, credentials, or provider endpoints were touched. Full source, logs and limitations: `docs/research/evidence/arynull-skillden-review-2026-11-22.txt`.

Disposition: retain only as a low-priority local Skill ResourcePlane/lockfile concept reference; do not treat its scanner or installer as a secure cross-Harness transfer layer without redesign. The user-confirmed Claude Desktop 3P scope remains **Chat, Cowork, and Code, all three**, plus local/self-hosted Claude Code; Skill package support in one local adapter is not evidence for any Desktop mode.

Inventory: **151/303 primary reviewed, 152 pending**; supplemental catalog **177 pending**; combined primary+supplemental pending **329**; manual additions **13**, of which **1 pending** (the unpinned `xingkongliang/skills-manager` dependency); total unresolved including manual: **330**. Next primary candidate from the updated index: `brainpower168/skill-manager`. Research remains incomplete.


## 2026-11-22 primary candidate #152 — brainpower168/skill-manager

Reviewed isolated `main` at exact HEAD `830ca5d91818969088bde3b38c21ba9f60c2eaad` (MIT; 0 stars/0 forks; five commits; no releases or Actions runs). It is a 336-line Windows directory-junction linker for one global copy of Skills, verified in its README on Windows 10/11 + ZCode only; macOS/Linux support is roadmap. It has no ChatGPT Project/Section/Session import/export, history graph, MCP/plugin, memory, schedule, project-scope or Claude Desktop 3P Chat/Cowork/Code packaging. Its Claude path is `~/.claude/skills`, only.

Source/runtime audit: the checked-in JSON config contains machine-specific Windows paths and `CONFIG_PATH` is next to the script. In isolated TemporaryDirectories, `remove ../victim` deleted a directory outside the configured Skill library and returned 0; `install --force` with a simulated `mklink` failure deleted an existing real agent Skill, falsely printed “replaced”, and returned 0 without a link. An ordinary path under macOS `/var` was misclassified as a link because `realpath != abspath` detects symlinked ancestors. A same-name library entry also blocks importing updated source content. Python compile and CLI help pass; no tests, CI workflow, or releases exist. Detailed source/test evidence: `docs/research/evidence/brainpower168-skill-manager-review-2026-11-22.txt`.

Disposition: retain only as a low-priority Windows ResourcePlane/junction concept; do not use its current destructive mutation logic as an installer or migration backend. It contributes no evidence for the fixed Claude Desktop 3P targets Chat, Cowork, or Code, nor local/self-hosted Claude Code session migration.

Inventory: **152/303 primary reviewed, 151 pending**; supplemental catalog **177 pending**; combined primary+supplemental pending **328**; manual additions **13**, of which **1 pending** (the unpinned `xingkongliang/skills-manager` dependency); total unresolved including manual: **329**. Next primary candidate from the updated index: `CDataSoftware/google-campaign-manager-360-mcp-server-by-cdata`. Research remains incomplete.


## 2026-11-22 primary candidate #153 — CDataSoftware/google-campaign-manager-360-mcp-server-by-cdata

Reviewed archived `main` at exact HEAD `1dc44b6c99367a5c503b73488ba561999aa4ea85`. GitHub archived the repository read-only on 2026-11-17; README calls it deprecated. MIT, 0 stars/0 forks, 4 commits, no release and no CI runs. It is a local stdio MCP adapter for one Google Campaign Manager 360 data source through a separately supplied CData JDBC driver and `.prp` config. README shows a Claude Desktop `mcpServers` snippet; source registers only `get_tables`, `get_columns`, `run_query` (`Statement.executeQuery`) and table metadata resources. It does not import or serialize MCP configuration, ChatGPT Projects/Section Groups/Sessions, message branches, files, memory or schedules. It does not test Claude Desktop 3P API-key mode or Chat/Cowork/Code.

`mvn test` passed 11/11 utility tests; `mvn package` passed and assembled the jars. Tests cover only table parsing/URI and JSON schema construction—no MCP transport handshake, actual CData driver, OAuth account, SQL permissions, or harness runtime. The CData driver is external. The README labels the adapter read-only and describes `SELECT`, but one generic usage paragraph claims read/write/update/delete; source has no write tool, while it also does not set JDBC read-only mode or restrict query tables. Treat read-only as an intended tool/driver permissions contract, not a proven security boundary. Detailed evidence: `docs/research/evidence/cdatasoftware-google-campaign-manager-360-mcp-review-2026-11-22.txt`.

Disposition: preserve as a narrow MCP stdio/config/driver dependency fixture only; do not use as a Nexus migration engine. It demonstrates what an MCP transport adapter needs to record (server command/args, environment placeholder names, transport, platform, driver version/hash, auth reference and scopes) without copying secret values or live data.

Inventory: **153/303 primary reviewed, 150 pending**; supplemental catalog **177 pending**; primary+supplemental pending **327**; manual additions **13**, of which **1 pending**; total unresolved including manual: **328**. Next primary candidate from the updated index: `clictl/cli`. The user-confirmed Claude Desktop target remains all three modes—Chat, Cowork, Code—plus local/self-hosted Claude Code. Research remains incomplete.


## 2026-11-22 primary candidate #154 — clictl/cli

Reviewed isolated `main` at exact HEAD `80a83a81c8978b883adbf7b7b67af70e0b0e7a61` (Apache-2.0; GitHub snapshot 0 stars/0 forks; latest visible release v0.1.2). The Go package manager offers a useful adjacent ResourcePlane model—typed API/CLI/MCP/Skill specs, target-specific Skill/MCP configuration writers, a local vault, tool-scoped note memory, and sandbox metadata. It is not a ChatGPT/Codex Projects/Sections/Session importer, session graph, transcript or attachment transport, or schedule migrator. Its Claude Desktop writer is a local MCP JSON path only, not evidence of third-party-inference session support.

`go test ./...` and `go vet ./...` both passed using temporary caches and Go 1.26.11. Source review plus isolated temporary probes reproduced three concrete defects: a `source.files[].path` traversal overwrites a sibling Skill because containment uses a string prefix; Codex target install writes the source `SKILL.md` despite its `AGENTS.md` adapter filename; and `forget ../config --all` removes a disposable sibling config through unvalidated tool-name path joining. Sandbox source defaults to host network and forwards SSH-agent/Git/npm config unless denied; an empty command allowlist becomes `[Bash, Read, Write]`. Treat specs/permissions as explicit ResourcePlane metadata, pin source revisions and hashes, and do not adopt these mutators unchanged. No live service, credentials, user directories, or Claude Desktop modes were used. Full evidence: `docs/research/evidence/clictl-cli-review-2026-11-22.txt`.

The user-confirmed Claude target remains Desktop 3P **Chat, Cowork, and Code, all three**, each a separate acceptance track, plus local/self-hosted Claude Code. This candidate supplies no mode-level acceptance evidence.

Inventory: **154/303 primary reviewed, 149 pending**; supplemental catalog **177 pending**; primary+supplemental pending **326**; 13 manual additions with 1 pending; total unresolved including manual **327**. Next primary candidate: `CTOUT/agentsmith`. Research remains active and incomplete.


## 2026-11-22 primary candidate #155 — CTOUT/agentsmith

Reviewed isolated `main` at exact HEAD `fded2989b580230e43467e36369964ef3cbc5e60` (MIT; 0-star snapshot; current main has 13 commits; only visible release is v0.1.0 at `44f3204`). This is a local source/asset sync and installer for the `awesome-copilot` catalogue, targeting only VS Code, Kiro, and Antigravity with repo/user scopes. It uses explicit native/adapted/unsupported asset outcomes, hash-backed subscriptions, dry-run, and local-edit checks—useful ResourcePlane design ideas. It has no ChatGPT/Codex Projects, Sections, Session/event/message/fork graph, attachment, token/cost, MCP, plugin transfer, or schedule migration. Claude Code is only a future roadmap item; no Claude Desktop 3P Chat/Cowork/Code or API-gateway runtime support exists in this pinned source.

Node 26.7 isolated build, lint, Prettier, and CI-order test suite passed (9 files / 72 tests; build before test). Running `npm test` before build on a clean copy failed 7 CLI tests because generated `dist/cli.cjs` was absent; CI explicitly runs build first. Two synthetic, disposable probes found important correctness/rollback gaps: the removal guard allows exactly 25% removal while docs promise ≥25% protection, and `force` directory update deletes the existing target before `cpSync`; an induced copy failure left the old Skill gone while the subscription kept its old hash. GitHub Actions shows the latest visible CI is a Dependabot PR run, not proof for the captured main HEAD. Detailed primary-source and runtime record: `docs/research/evidence/ctout-agentsmith-review-2026-11-22.txt`.

The confirmed target remains Claude Desktop third-party-gateway **Chat, Cowork, Code—all three**, each with a separate adapter acceptance test, plus local/self-hosted Claude Code. This asset manager supplies no evidence for those targets or for Anthropic-hosted Cloud.

Inventory: **155/303 primary reviewed, 148 pending**; supplemental catalog **177 pending**; primary+supplemental pending **325**; 13 manual additions with 1 pending; total unresolved including manual **326**. Next primary candidate: `DaveGerson/aiskills`. Research remains active/incomplete.


## 2026-11-22 primary candidate #156 — DaveGerson/aiskills

Reviewed isolated `master` at exact HEAD `7e238306d47507bf6e63032d76b862a54d05a06d` (MIT; GitHub snapshot 0 stars/forks, 2 commits, no release and no Actions workflow/run). This is primarily a skill/config repository: `program-docs` gives agents a dated Markdown brief/map/status/append-only decisions/tracks structure; `build-status-artifact` uses Claude Artifact/ArtifactData to publish a project-specific status page and answer loop; setup snippets cover Claude Code, Codex and Antigravity. These are useful **authored program-context sidecars** and resource-plane packaging examples, not parsers/writers for ChatGPT/Codex Project, Section, Session, messages, branches, subagents, attachments or usage. They require an agent/owner to create and update the docs; they are not deterministic session migration.

The example seed validator passed 59 writes across two batches (50+9). Local Claude Code CLI 2.1.76 `claude plugin validate .` failed because the marketplace root `description` key was rejected. Codex CLI 0.154.0 accepted local marketplace registration, but no plugin installation was run. Dynamic temporary probes found path traversal in both build-status scripts: a crafted seed manifest made `make_batches.py` emit an ArtifactData `file_path` outside the seed; `make_harness.py` embedded sibling JSON into generated HTML. Only synthetic sentinel files were used and no ArtifactData call or user file was touched. Full source/runtime evidence: `docs/research/evidence/davegerson-aiskills-review-2026-11-22.txt`.

The user-confirmed Claude Desktop 3P scope remains **Chat, Cowork, and Code, all three as distinct acceptance tracks**, plus local/self-hosted Claude Code. This candidate provides no native Desktop mode/session-store integration.

Inventory: **156/303 primary reviewed, 147 pending**; supplemental catalog **177 pending**; primary+supplemental pending **324**; 13 manual additions with 1 pending; total unresolved including manual **325**. Next primary candidate: `David-Sat/agpx`. Research remains active/incomplete.


## 2026-11-22 primary candidate #157 — David-Sat/agpx; Claude Desktop target reaffirmed

The user selected **all three** Claude Desktop third-party-inference surfaces—Chat, Cowork, and Code—plus local/self-hosted Claude Code. Keep provider/deployment identity separate from surface/mode. Current official documentation confirms Desktop 3P routes inference to a configured provider or LLM gateway while the app stores conversations, projects, and memory on the device. Its one-time importer is Claude-source-specific: the user's Claude.ai chats/projects and local Cowork/Code sessions; cloud Cowork/Code sessions, project knowledge-file contents, and uploaded file bytes have exclusions. Desktop session export is an **unencrypted ZIP** that can contain sessions, projects/files, memory, scheduled tasks, Skills, plugins, preferences, local MCP commands, and passwords/API keys; it excludes Claude Code CLI sessions. Treat it as sensitive source material, not a ChatGPT importer or credential-safe interchange format. Claude Code CLI provider setup and local transcripts (`~/.claude/projects/`) are separate; an API-key gateway does not make Anthropic-hosted Cloud sessions available. Product acceptance remains four independent tracks: `desktop-3p/chat`, `desktop-3p/cowork`, `desktop-3p/code`, and `claude-code-local`; no Code-only check can stand in for Chat or Cowork. See the current official [Desktop migration/export guide](https://support.claude.com/en/articles/18426225-move-from-claude-enterprise-to-claude-desktop-on-a-cloud-provider), [gateway configuration](https://claude.com/docs/third-party/claude-desktop/configuration), [CLI migration guide](https://support.claude.com/en/articles/18466061-move-claude-code-cli-users), and [MCP storage scopes](https://code.claude.com/docs/en/mcp).

Candidate #157, pinned to `David-Sat/agpx` main HEAD `61b51e587422738c8735011eedb30308cd1c8890` (MIT, TypeScript, 0-star snapshot; latest visible package v0.3.1), is a Skills/MCP/environment-config installer for 19 Harness IDs, not session migration. Its Claude Desktop adapter only writes MCP config and returns no Skills target; it has no mode-specific Desktop sessions or Chat/Cowork/Code data import. No Codex-native adapter exists; `workspace` is a generic `.mcp.json` / `skills/` route. The Claude Code adapter writes `~/.claude/mcp.json`, whereas current first-party docs place user/local MCP in `~/.claude.json` and project MCP in `.mcp.json`. No Projects/Sections/session/event/branch/attachment/token/cost/schedule data model or importer was found.

Node 26.7 build then test passed (6 files, 27/27 tests); a clean unbuilt `npm test` previously failed 3 CLI tests because `dist/cli.js` did not yet exist, while CI explicitly builds first. The built CLI reported `0.1.0` although package/banner says `0.3.1`. Four disposable synthetic probes reproduced: manifest `mcpConfig` can read a sibling file; update silently opts into command trust (`yes ?? true`) even under TTY; non-TTY add bypasses command trust even without `--yes`; and uninstall recursively deletes manually added files inside its Skill directory. No real MCP command, harness, credentials, user data, or target profile was used. Keep only per-Harness resource-adapter / dry-run concepts; do not use the current writer/remover as a transactional migration backend. Detailed pinned-source and synthetic runtime evidence: `docs/research/evidence/david-sat-agpx-review-2026-11-22.txt`.

Inventory: **157/303 primary reviewed, 146 pending**; supplemental catalog **177 pending**; primary+supplemental pending **323**; 13 manual additions with 1 pending; total unresolved including manual **324**. Next primary candidate: `davidjamesshelley-netizen/skillpack`. Research remains active/incomplete.


## 2026-11-23 primary candidate #158 — davidjamesshelley-netizen/skillpack (README-only proposal)

Candidate #158 is pinned to main HEAD `bfe9f5407a100f75e6c4dcb66b5fe9f8a8e4c151` (one commit, 2026-03-28). The repository contains only `README.md`; it describes a proposed Skill package manager/registry, an illustrative `skillpack.json` with dependency/version/compatibility/input/output fields, and future CLI/registry roadmap. There is no implementation, package manifest, tests, CI, LICENSE file, native Skill/MCP adapter, or session/project/Section/session graph. The README claims Apache-2.0 but the candidate inventory has no SPDX and the repo has no license text, so license remains unverified. No tests can be run against absent software.

The README tells users to install `skillpack` from npm, but a non-installing `rtk npm view skillpack ... --json` query returned version 0.1.3 whose repository is `joventuraz/skillpack`, not this proposal repository. Do not assume the package implements this README or install it as its counterpart. Disposition: `screened_readme_only_spec_no_implementation`; retain its manifest fields only as unvalidated design ideas. It offers no evidence for ChatGPT/Codex Projects, Sections, Sessions, API-key Claude Desktop Chat/Cowork/Code, local Claude Code, attachments, schedules, or migrations. Full evidence: `docs/research/evidence/davidjamesshelley-netizen-skillpack-review-2026-11-23.txt`.

Claude Desktop's three 3P surfaces remain individually in scope—Chat, Cowork, Code—plus local/self-hosted Claude Code; this candidate does not satisfy any target adapter acceptance.

Inventory: **158/303 primary reviewed, 145 pending**; supplemental catalog **177 pending**; primary+supplemental pending **322**; 13 manual additions with 1 pending; total unresolved including manual **323**. Next primary candidate: `devansh0703/skill-router`. Research remains active/incomplete.


## 2026-11-23 primary candidate #159 — devansh0703/skill-router (Skill shelf tools, no session migration)

Pinned main HEAD `f545fe5aff9abb7a0362bf16403ac299ac3de14e` (MIT, shell project). The repo supplies two Agent Skills and Bash helpers to route against a live Skill shelf and list/search/validate/install/disable/enable Skills. This is useful adjacent ResourcePlane UX, not a session/project portability engine: there is no ChatGPT/Codex Project/Section/Session, event/fork graph, transcript, attachment, MCP/plugin, memory, schedule, or Claude Desktop 3P/local Claude Code writer.

On the actual review host (GNU Bash 3.2.57 on arm64 macOS), `catalog.sh` emits associative-array errors and returns exit 0 with no results; manager `search` with a no-match query exits 1 on unsupported `${desc,,}`. `list`, `validate --all` (2/2), and `doctor` pass. Three synthetic-only probes reproduced path escape from `SKILLS_HOME` using `disable ../outside/victim`, and silent overwrite/data loss when disabling with a pre-existing `SKILL.md.disabled` or enabling with a pre-existing active `SKILL.md`. All POCs used disposable `/tmp` content; no user Skill home or live skill was touched. Full source/runtime evidence: `docs/research/evidence/devansh0703-skill-router-review-2026-11-23.txt`.
+
+The user-confirmed Claude Desktop 3P destination remains **Chat, Cowork, and Code separately**, plus local/self-hosted Claude Code; this project implements none of those four targets.

Inventory: **159/303 primary reviewed, 144 pending**; supplemental catalog **177 pending**; primary+supplemental pending **321**; 13 manual additions with 1 pending; total unresolved including manual **322**. Next primary candidate: `DoryZi/token-efficient-lifecycle`. Research remains active/incomplete.


## 2026-11-23 primary candidate #160 — DoryZi/token-efficient-lifecycle (workflow delegation, not session transfer)

Pinned main HEAD `e3ef5437767b1cec77e1c2969d86ed391dc7709c` (MIT, early 0.1.0 release) includes a Claude Code/Codex subscription task orchestrator and a bounded Playwright browser worker, plus skills. It is relevant to token-efficient work handoffs, but not to importing or translating chat/project/session state: it has no ChatGPT/Codex Projects/Sections/Session/branch/attachment/memory/MCP/schedule migration. The CLI deliberately accepts Claude.ai/OAuth and ChatGPT subscription login only; it explicitly rejects API-key billing and does not target Claude Desktop 3P Chat/Cowork/Code.

Useful workflow ideas include task-attempt logs, lock/budget/retry limits, a narrow worker result, and explicit verification. Safety boundaries differ by component: the browser worker confines model actions and Codex read-only tool use but inherits all parent environment variables for its Playwright CLI; its attachment paths may resolve outside the task directory. The separate Claude orchestrator launches Claude Code in `auto` permission mode with prompts suppressed and Bash/Read/Write/Edit tools, and explicitly is not a filesystem sandbox. Do not run it on sensitive/untrusted projects as an isolated worker; its subscription-only design is not the user's API-Key target.

Validation on the actual macOS host: orchestrator fake-CLI unit suite **13/14 passed**; the one test failure compares lexical `/var/folders` with canonical `/private/var/folders` from `Path.resolve()`. Browser fake tests **54 passed** after installing exact lockfile packages in a disposable venv using hash verification; no real browser, model, subscription login, or network page was used. Synthetic probes accepted a `../outside-sentinel.txt` attachment path and confirmed a synthetic parent env marker reaches the Playwright child env; no data was uploaded. Full source/test evidence: `docs/research/evidence/doryzi-token-efficient-lifecycle-review-2026-11-23.txt`.

The confirmed destination remains Claude Desktop 3P Chat, Cowork and Code as independent acceptance tracks, plus local/self-hosted Claude Code. This candidate meets none of the data portability acceptance paths.

Inventory: **160/303 primary reviewed, 143 pending**; supplemental catalog **177 pending**; primary+supplemental pending **320**; 13 manual additions with 1 pending; total unresolved including manual **321**. Next primary candidate: `Dual-Forge/skills-manager`. Research remains active/incomplete.


## 2026-11-23 primary candidate #161 — Dual-Forge/skills-manager (Skills resource manager, not session transfer)

Pinned main HEAD `9bff2528ce7cdfe7e39bedbebf6b8e35029547b0` (MIT root license; package `@dual-forge/skills-manager` v0.1.1; third-party Skill notices remain). This is a local SQLite-backed Skills catalog/dashboard, bundle builder, API, and provider-root installer for `.agents`, `.claude`, `.cursor`, `.codex`, and `.hermes` Skills. It does not implement ChatGPT/Codex Project, Section/Section Group, Session/event/turn/branch/child graph, transcript/attachment/usage, MCP/plugin, memory, schedule, or Claude Desktop/Claude Code session migration. Its Anthropic/OpenAI API-key paths generate/update Skill files only; they are not a conversation-transfer endpoint.

The actual source and synthetic probes expose three important installer limits: (1) `--skills` accepts arbitrary values and the bundle manifest is parsed without schema/slug validation; `installSkillsFromBundle()` joins the slug under bundle and target roots without containment checks, and a disposable `../../escape` fixture wrote outside `.agents/skills`. (2) `copySkillDir()` recursively removes an existing destination before copying, so a synthetic user-added sidecar file disappeared on overwrite, with no backup/rollback; sequential targets can partially apply. (3) skip detection compares only normalized `SKILL.md`, so a matching main file hid a changed helper sidecar. The default launcher binds loopback, but permits `--host`; reviewed dashboard API routes have no auth, so non-loopback exposure requires an external access-control boundary. Keep only the local inventory/bundle and explicit provider-root concepts; do not use this writer transactionally until it has containment checks, whole-tree drift detection, atomic backup/rollback, and tests.

Validation: isolated `npm ci --ignore-scripts --no-audit --no-fund` exited 0 (800 packages); `npm test` exited 0 (9 files, 41/41 tests). Three actual-function synthetic probes reproduced path escape from the selected skills root, recursive overwrite loss, and stale sidecar skip; no user directories, credentials, API requests, or Claude session data were used. Full evidence: `docs/research/evidence/dual-forge-skills-manager-review-2026-11-23.txt`.

The user's latest clarification reconfirms the four separate target acceptance tracks: Claude Desktop 3P Chat, Cowork, and Code, plus local/self-hosted Claude Code. Inventory: **161/303 primary reviewed, 142 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **319**; manual additions **13** with **1** pending; total unresolved including manual **320**. Next primary candidate: `ducconit/gvm`. Research remains active and incomplete.


## 2026-11-23 primary candidate #162 — ducconit/gvm (Go manager + Skill/MCP, not session migration)

Pinned main HEAD `c6407df8614ce312cce0de455aa4e1533e17e82a` (MIT). This is a cross-platform Go-version manager with an MCP stdio control server and one embedded Skill installer for eight local Harness/IDE directories. It offers no ChatGPT/Codex Projects, Sections/Section Groups, Session/event/turn/branch/subagent graph, transcript/files/attachments, usage, memory, schedule, or Claude Desktop Chat/Cowork/Code session importer/writer. The Claude Skills destination is a local Skill directory; it does not establish compatibility with the three Desktop session stores.

Review retained useful positive controls: Go toolchain archives are checked against go.dev SHA-256 values, traversal and symlink targets are checked during tar/zip extraction, and installs stage before final rename. However, the self-updater treats the `sha256` field as optional and accepts an empty checksum; a fake-server test against the actual updater replaced a synthetic target executable with an arbitrary synthetic release payload when the field was absent. GitHub’s REST asset schema documents `digest` while this code decodes `sha256`; this mismatch is an inference about default release responses, not a fetched observation (the host’s direct API query was blocked). The uploaded `checksums.txt` is not read by the updater. One-line shell/PowerShell installers also do not verify a checksum. MCP tools directly expose installation, switching, uninstall and clean operations without server-side confirmation/annotations; a synthetic `g_uninstall_version` RPC removed only a temporary fake Go version. The MCP host may separately ask for approval. Embedded Skill installation overwrote a synthetic existing `SKILL.md` without prompt or backup.

Quality: main CI run #5 on the pinned commit is green; latest GitHub release was v1.0.1 (2026-10-28), while main Makefile advertises 1.1.0. A temporary official Go 1.27.4 toolchain was SHA-verified against go.dev. `go vet` passed; the first local race-test run hit a macOS `/var/folders` vs `/private/var/folders` path expectation mismatch, then the full suite passed with canonical `TMPDIR`; six cross-build targets passed. No real MCP host, Skill home, API key, Go installation, or Harness session was used. Full evidence: `docs/research/evidence/ducconit-gvm-review-2026-11-23.txt`.

Disposition: keep only the explicit Skill path map, stdio MCP wiring, and verified archive-extraction patterns as adjacent ResourcePlane/security references. Do not count it as a SessionGraph importer. The user's confirmed targets remain separate Desktop 3P Chat/Cowork/Code plus local/self-hosted Claude Code. Inventory: **162/303 primary reviewed, 141 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **318**; manual additions **13** with **1** pending; total unresolved including manual **319**. Next primary candidate: `EfanWang/skills-manager`. Research remains active and incomplete.


## 2026-11-23 primary candidate #163 — EfanWang/skills-manager (single-root Skill provenance manager)

Pinned main HEAD `1f0482bf822835d19552487a2a6345735cdffa0d` (MIT; commit date 2026-05-19). This small Python tool inventories and tracks GitHub-backed `SKILL.md` siblings for one installed skills-root at a time, with source records, update checks, backups, rename-based replacement, and an agent-facing SKILL.md. It explicitly does not aggregate across Claude Code, Cursor, and Codex CLI, and it provides no ChatGPT/Codex Projects, Sections/Section Groups, Session graph, transcript, attachment, MCP/plugin, memory, schedule, or Claude Desktop Chat/Cowork/Code session transfer.

The 80-test contract suite passed. Useful adjacent file-safety patterns include path-constrained clone subpaths, backup-before-replacement, atomic directory rename, atomic JSON writes, and rollback tests. However, inventory follows a sibling-directory symlink and read a synthetic SKILL.md outside the lexical skills root. The offline provenance gate auto-claims any GitHub-looking `.git/config` origin with the local commit hash without fetching/validating remote content; a dry-run on synthetic unrelated content and a fake GitHub origin produced an `auto_claim` record. This is an explicit-evidence heuristic, not proof of upstream identity. The skill instructions also invoke agent WebSearch for unresolved origins, so source tracing is not autonomous/AI-free. README’s default inventory mode may auto-write registry claims after that heuristic.

GitHub landing page shows 0 stars, 1 fork, 15 commits; no releases or Actions workflows were found, and the shallow default-branch HEAD is the May 2026 documentation refresh. No session/project importer or cross-Harness adapter is present. Keep only scoped Skill provenance and transactional replacement ideas; reject as a SessionGraph migration candidate. Full source, test output, probes, and tool-correction ledger: `docs/research/evidence/efanwang-skills-manager-review-2026-11-23.txt`.

The confirmed target remains Claude Desktop 3P Chat/Cowork/Code as independent acceptance tracks plus local/self-hosted Claude Code. Inventory: **163/303 primary reviewed, 140 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **317**; manual additions **13** with **1** pending; total unresolved including manual **318**. Next primary candidate: `ekupekuAI/agenthub`. Research remains active and incomplete.


## Candidate #164 — ekupekuAI/agenthub: transactional Skills supply chain, no session migration

Pinned main HEAD `bc74259f22ab2c043aaed3f5abb3e1e29e72dbb4` (MIT; created 2026-10-05; GitHub snapshot 0 stars/0 forks). It installs capability-gated `SKILL.md` packages to Claude Code, Codex, Cursor, and VS Code/Copilot. Source review found careful archive validation, SHA-256 lock integrity, policy/capability rechecks, journaled multi-target transactions and rollback. These are valuable **resource-plane** references only: no ChatGPT/Codex Project, Section/Section Group, Session event/fork/parent-child graph, transcript/attachment/token state, MCP/plugin, memory, schedule, or native Claude Desktop 3P Chat/Cowork/Code/local Claude Code conversation import/export. Its TUI `Session` is internal UI state, not a model session. Security docs correctly caution that static scanning is not a safety verdict; no sandbox is supplied.

Node 24.22.3: `npm ci`, full suite (1,166 passed / 8 skipped), lint, typecheck and root build passed. On declared-compatible Node 26.7.0, the full source/test suite fails (46 failed / 1,103 passed / 25 skipped) because `scan-runner.ts` still passes `--experimental-transform-types`, removed in Node 26.0; CI covers Node 22/24 only. In contrast, the Node 26 web production build passed and the isolated bundled worker test passed 3/3, because the built JavaScript worker does not use that flag. GitHub CI #15 is green on the pinned commit; there are no GitHub Releases; npm latest is 0.1.0. Keep only the package integrity, capability declarations, transactional write/recovery, and rollback patterns; reject as a SessionGraph migration dependency. Full evidence: `docs/research/evidence/ekupekuai-agenthub-review-2026-11-23.txt`.

The confirmed destination scope remains separate Claude Desktop third-party-gateway acceptance tracks for **Chat**, **Cowork**, and **Code**, plus local/self-hosted Claude Code. Inventory **164/303 primary reviewed, 139 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **316**; manual additions **13**, with **1** pending; unresolved including manual **317**. Next primary candidate: `emanuelet/skill-manager`. Research remains active and incomplete.


## Candidate #165 — emanuelet/skill-manager: Skills/MCP helper, not SessionGraph migration

Pinned `master` HEAD `5fbf417e9ae30cbcbcf20515f83239dde1c142d4` (MIT, 2026-10-07). The CLI manages a canonical Skills store, Claude Code/Codex CLI/OpenCode Skill paths, `.skills.json` project resource manifests, profiles/dependencies, a Claude Code SessionStart Skill-activation hook, a Skill-operation MCP server, and Bifrost Skill synchronization. This is a resource plane, not migration of ChatGPT/Codex Projects, Sections/Section Groups, Session event/fork graphs, transcripts/attachments/token state, MCP configurations, plugins, memory or schedules. The MCP setup installs its own service rather than transferring other MCPs; `SessionStart` is only a trigger to activate Skills. It does not target Claude Desktop 3P Chat/Cowork/Code or local Claude Code conversation files.

Local Node 26.7 review with pinned pnpm 12.9.0: typecheck/lint, oxlint and build passed; 870/870 tests passed after setting canonical macOS `TMPDIR`. First test run had one `/var` vs `/private/var` expected-path assertion mismatch. Upstream validation is not established: GitHub Actions has zero runs, no Releases, workflow's `npm ci` fails because the repo has pnpm-lock only and no npm lock, the CI matrix Node 20/22 conflicts with `engines.node >=24`, and `npm view skill-manager-plus` returned E404.

Two temporary, synthetic POCs are material: actual CLI auto-adopt deleted two same-slug Skill directories with identical SKILL.md but distinct reference files, then retained only the first directory's reference in the canonical store (the second asset disappeared without backup). A nested `SKILL.md` symlink was followed, causing an outside-root synthetic sentinel to be imported into the canonical store. The code also calls auto-adopt on ordinary CLI actions and silently before each MCP tool invocation by default. Keep the manifest/profile, atomic symlink, dependency, session-start-activation and MCP discovery patterns only; reject as a migration dependency and do not run auto-adopt against user data until the duplicate-asset loss and nested-symlink read are fixed. Full source/test/probe record: `docs/research/evidence/emanuelet-skill-manager-review-2026-11-23.txt`.

Confirmed target remains separate Claude Desktop third-party-gateway **Chat**, **Cowork**, and **Code** tracks plus local/self-hosted Claude Code. Inventory **165/303 primary reviewed, 138 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **315**; manual additions **13**, with **1** pending; unresolved including manual **316**. Next primary candidate: `fabiomartino/shroud-layer`. Research remains active and incomplete.


## Candidate #166 — fabiomartino/shroud-layer: empty repository; no source to assess

The discovery catalog describes an AI-agent overlay lifecycle CLI/API/TUI and tags it Rust/MCP, but the exact GitHub checkout is empty. `rtk git clone --depth 1` exited 0 with Git's empty-repository warning; the `main` checkout contains only `.git/`, has no `HEAD`, and `git rev-parse HEAD` exits 128. The official GitHub page confirms “This repository is empty”; no README, LICENSE, code, tests, build, workflow, or release exists. Do not infer capabilities from description/topics. Disposition: `EMPTY_REPOSITORY_NO_SOURCE_REVIEW_POSSIBLE`; exclude until implementation is published and reviewed. Evidence: `docs/research/evidence/fabiomartino-shroud-layer-review-2026-11-23.txt`.

The user's target remains separate Claude Desktop API-key third-party-gateway **Chat**, **Cowork**, **Code** tracks plus local/self-hosted Claude Code. Inventory **166/303 primary reviewed, 137 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **314**; manual additions **13**, with **1** pending; unresolved including manual **315**. Next primary candidate: `facundoPri/agent-config-manager`. Research remains active and incomplete.


## Candidate #167 — facundoPri/agent-config-manager: resource archive + live-session observability, not historical migration

Pinned main HEAD `a6f6af755edfd0edb338e5032761822fabc9e566` (MIT, package v0.2.0, Bun >=1.1; 0-star/0-fork snapshot, 6 commits; no CI/release). A useful local UI inventories Skills across Claude Code/Codex/Cursor/Copilot/Gemini/OpenCode, MCP configs across five harnesses, hooks across three, and Claude Code plugins. It archives/restores those resources in place with backups. Its optional proxy records **new live API requests** for Claude Code and beta Codex, including full request bodies, responses, session IDs and main/subagent displays.

This is not an importer/exporter for existing ChatGPT/Codex Projects, Section Groups, historical session files, event/fork graphs, attachments, or Claude Desktop 3P Chat/Cowork/Code. It cannot write or initialize target sessions. The logger is useful source-observability reference, not a migration channel: session IDs are header-derived (or Codex falls back to a daily bucket), Codex analysis is beta, and parent-child links are inferred from prompt prefixes rather than stable parent event IDs. One synthetic `sessionDetail` probe with two spawn prompts sharing the first 120 characters linked both children to the first spawn.

Official Bun 1.4.5 macOS ARM64 binary verified by SHA-256; fake-home/fake-Anthropic-server suite passes **10 tests / 70 assertions**. Temp-only probes confirmed that `skillDetail()`'s string-prefix path check accepts `../` and returned an outside-root synthetic SKILL.md; that logger auth headers are omitted but a secret sentinel in the user request body persists in plaintext logs; that two Codex requests lacking session identifiers collapse into one date-based session; and that an MCP API-key sentinel is copied unredacted into local backup (`0644` under the test's default umask). The server binds loopback and checks Host/Origin, so these results are local-code/data-boundary findings, not internet exploitability claims. Keep the resource inventory/archive UX and request-observability record model as design references, but do not adopt its tree as authoritative or its logs as a portable session format. Full source and probe report: `docs/research/evidence/facundopri-agent-config-manager-review-2026-11-23.txt`.

The user-confirmed destination remains separate Desktop 3P API-key tracks **Chat**, **Cowork**, **Code**, plus local/self-hosted Claude Code. Inventory **167/303 primary reviewed, 136 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **313**; manual additions **13**, one pending; unresolved including manual **314**. Next primary candidate: `fei-bai-inc/sine-kits-skills`. Research remains active and incomplete.


## Candidate #168 — fei-bai-inc/sine-kits-skills: host-neutral Skills for a separate Kit platform

Pinned `main` HEAD `c450388630135adc5cfc2e48491df66c252fadbe` (2026-10-05). This repository is a two-Skill Markdown pack plus one Reading List sample Kit and author-supplied evidence JSON; no implementation of a Harness migrator, no top-level LICENSE, tests, CI workflow or GitHub release. The Skills teach generic Sine Kits publisher/installer CLI use with operation discovery, JSON Schema inputs/outputs, owner-approved capability grants, durable run IDs and idempotent retries. Those are useful **tool-invocation protocol** ideas but Sine Kits' `Project`/`Installation`/`Run` are not ChatGPT/Codex Projects or chat Sessions. It neither imports/moves conversation history, Section Groups, forks, attachments, MCP/plugin configs, memories or schedules, nor targets Claude Desktop 3P Chat/Cowork/Code/local Claude Code.

Public registry check found latest `@sine-kits/kit-cli`, `kit-sdk`, and `kit-contracts` at 0.2.0; the exact CLI and contracts 0.3.0 versions called for by the Skills both return npm E404. The README itself says those commands require separate future public npm publication. Therefore its example-evidence JSON remains author-reported local/archived release-candidate proof, not an independently reproducible public workflow. License is unconfirmed; do not copy/repackage the Skills until clarified. Keep operation-schema discovery, explicit grants, one-intent/idempotency discipline and same-run polling as conceptual references only. Full evidence: `docs/research/evidence/fei-bai-inc-sine-kits-skills-review-2026-11-23.txt`.

The confirmed target remains separate Claude Desktop third-party-gateway **Chat**, **Cowork**, and **Code** tracks plus local/self-hosted Claude Code. Inventory **168/303 primary reviewed, 135 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **312**; manual additions **13**, one pending; unresolved including manual **313**. Next primary candidate: `FutureHax/openclaw-skill-manager`. Research remains active and incomplete.


## 2026-11-23 progress — candidate #175 and updated queue

Candidate #175 (`harry-leon/ai-agent-skills-registry`, pinned HEAD `11d3972c118b44c91e3ad37e15de45c77486014c`) is now source-reviewed and classified as an adjacent Skills registry/security reference, not a ChatGPT/Codex/Claude session migrator. Actual unit/lint/format/build checks are recorded in the candidate evidence. Integration tests remain unverified without a local PostgreSQL service. Important finding: the repo README advertises `npx skillary add`, while the repository is private and exposes no `bin`, the UI copies a different `skillvault` command, and npm `skillary@0.0.3` resolves to a different yurtsever/skillary local instruction browser. No session or Project/Section data model was found.

Primary inventory: 175/303 reviewed, 128 pending; supplemental net-new pending 177 (305 primary+supplemental pending); manual additions 14, with 2 pending; 307 total unresolved including manual items. A new manual lead, `nikships/skills-registry`, is queued for source/tests review from GitHub page screening only. Next primary source audit: `Heverton-web/skill-manager` (not yet reviewed). User scope remains Claude Desktop third-party-gateway Chat, Cowork, and Code as separate targets plus local/self-hosted Claude Code. The user-corrected project label is “Destruction Era.” The overall research remains active/incomplete; no completion email has been sent.


## 2026-11-23 progress — candidate #176 and native OpenCode transfer

Candidate #176 Heverton-web/skill-manager is reviewed at HEAD `4c9acccad4644b62896dcb63e794f0d936b35d94`. Reject as a direct migration product; do not run its dashboard unmodified because the localhost Skills API has a reproduced shell-injection primitive and wildcard-CORS access. The separate OpenCode Monitor is telemetry only, lacks session export/import, and also exposes synthetic event-log content through wildcard CORS. The OpenCode Monitor subproject tests pass 23/23 only with its upstream URL pointed to a refused local port; there are no automated tests for the Skills Manager package.

The official OpenCode API cross-check is a key discovery: native session export/import (HTTP routes marked experimental), parent/fork/project links, cursor-paginated typed messages, base64/MIME attachments, tool content, costs/tokens, permissions and revert state. Import parents before children; live event streams are volatile and can miss events during disconnect. Build a version-pinned native OpenCode adapter around complete export snapshots, not the reviewed monitor. See `docs/research/evidence/opencode-native-session-transfer-api-2026-11-23.txt`.

Current counts: primary 176/303 reviewed, 127 pending; supplemental net-new pending 177; combined pending 304; manual additions 14, 2 pending; unresolved including manual 306. Next primary candidate: Hitesh-Sisara/agentic-keyvault. Claude Desktop third-party-gateway Chat/Cowork/Code remain distinct; local/self-hosted Claude Code remains separate. “Destruction Era” retained. Research active/incomplete; no completion email sent.


## 2026-11-23 progress — candidate #177: separate credential plane from migration

Pinned and source-reviewed Hitesh-Sisara/agentic-keyvault. It is a self-hosted, versioned API-key/env secret vault, not a chat/project/session or cross-Harness migrator; treat “Project” as credential namespace. Retain only a SecretPlane boundary: canonical bundles may carry opaque credential locators and scope/provider metadata, never plaintext values; require destination-side relinking/reauthorization. The Worker can decrypt by design for MCP reads. A synthetic test confirmed project-A writer can attach an A secret to project-B repoId; this is a demonstrated association-integrity gap, not a cross-project read bypass. Worker 28/28 tests, temporary synthetic extension 29/29, typecheck and dry-run build pass. CLI environments were unavailable (Go/Bun not installed), MCP package has no tests. Full evidence: `docs/research/evidence/hitesh-sisara-agentic-keyvault-review-2026-11-23.txt`.

Counts: primary 177/303 reviewed, 126 pending; supplemental net-new pending 177; primary + supplemental pending 303; manual additions 14, 2 pending; unresolved including manual 305. Next primary audit: `huqiwei123/agentkit`. Claude Desktop third-party-gateway Chat/Cowork/Code stay separate; local/self-hosted Claude Code remains separate; “Destruction Era” retained. Overall research active/incomplete; no completion email sent.


## 2026-11-23 progress — candidate #178 agentkit: resource-plane reference, reject current installer

Pinned-source review plus a 16-test run and two disposable filesystem POCs. The project manages resource files/profiles for two adapters (Codex and generic Claude); it does not migrate projects, Sections, sessions, transcript graphs, attachments, schedules or memory, nor does it write the Claude Desktop third-party gateway in its three modes. Keep the manifest/profile concept only. Do not reuse the current install mechanism: a synthetic `../../outside` resource ID escaped the selected target, a second-action failure left an earlier file in place, and the built-in bootstrap profile references a missing sample-skill while validation still says OK. Codex receives a TOML MCP template; Claude skips MCP. Full review and literal outcomes: `docs/research/evidence/huqiwei123-agentkit-review-2026-11-23.txt`.

Counts: primary 178/303 reviewed, 125 pending; supplemental net-new pending 177; primary + supplemental pending 302; manual additions 14, 2 pending; unresolved including manual 304. Next primary audit `Jaxz714/skills-hub`. Chat/Cowork/Code third-party gateway tracks stay separate from local/self-hosted Claude Code; “Destruction Era” retained. Research active/incomplete; no completion email sent.


## 2026-11-23 progress — candidate #179 Skills Hub is discovery/install only

Pinned source review of `2670bbb911b0182ba42cd243eed113fda1c5210e` plus isolated CLI smoke, compile check and local-only Git update POC. It searches GitHub and clones Skills into local platform folders; it does not transfer Projects/Sections/Sessions, transcripts, attachments, usage, schedules or memory, and has no Claude Desktop Chat/Cowork/Code third-party gateway adapter. Keep only as a narrow ResourcePlane discovery reference. Reproduced an update metadata bug (`codex` becomes `unknown`); no tests directory exists. The publish helper hardcodes `gh repo create --public` (not executed), and uninstall trusts the recorded path (source-only risk). Evidence: `docs/research/evidence/jaxz714-skills-hub-review-2026-11-23.txt`.

Counts: primary 179/303 reviewed, 124 pending; supplemental pending 177; primary + supplemental pending 301; manual additions 14, two pending; unresolved 303. Next source audit: `jondwillis/privacy-rights-plugin`. Claude Desktop third-party gateway Chat/Cowork/Code remain separate from local/self-hosted Claude Code; “Destruction Era” retained. Overall research active/incomplete; no completion email sent.


## 2026-11-23 progress — candidate #180 privacy-rights-plugin is asset packaging, not state migration

Pinned source shows a five-Harness target/fallback map (Claude Code, OpenCode, Codex, Cursor, OpenClaw) for Skills/agents/instructions. It has no project/session/transcript/attachment/token/schedule/memory transfer and no Claude Desktop third-party gateway Chat/Cowork/Code target. Retain only as ResourcePlane packaging inspiration. Distribution audit: all generated target Skills still reference shared/email-templates absent from each dist; README claims Discover/Dashboard missing from source/dist. Jacq is an unpinned external tool and unavailable, with no test suite. Human approval/privacy guardrails are prompt-level; consumer personal data is stored in local files. Legal claims not independently validated. Full evidence: `docs/research/evidence/jondwillis-privacy-rights-plugin-review-2026-11-23.txt`.

Counts: primary 180/303 reviewed, 123 pending; supplemental 177; primary + supplemental 300; manual 14 (2 pending); unresolved 302. Next primary audit `jp-999/dev-team`. Claude Desktop gateway modes remain separate from local/self-hosted Claude Code. “Destruction Era” retained; research active/incomplete; no completion email.

## 2026-11-23 research continuation — candidate #181

Reviewed `jp-999/dev-team` at `d4b132ea32ccdafec64c7bfa6aa0de8e4aa081e4`. It offers a canonical-role-to-Cursor/Claude Code/CrewAI pattern and `.devteam/` project task blackboard, but no ChatGPT/Codex Project or Section migration, SessionGraph, transcript/media/token preservation, or Claude Desktop third-party-gateway Chat/Cowork/Code adapter. It is an adjacent resource/task-workflow example, not a Nexus Memory migrator. `--plan` exited 0 and listed 11 roles; disposable resource-sync smoke passed; there is no test suite; synthetic offline upskill probes showed static cycle-selected adoption independent of findings. No credential, user data, full LLM run, or networked scraper was used. Evidence: `docs/research/evidence/jp-999-dev-team-review-2026-11-23.txt`.

Current inventory: primary **181/303 reviewed, 122 pending**; supplemental net-new pending **177**; primary + supplemental pending **299**; manual additions **14**, **2 pending**; unresolved including manual **301**. Next primary repository: `kamalsrini17/mcp-client`. User-confirmed Claude Desktop Chat, Cowork, and Code remain separate adapters under the third-party gateway path; local/self-hosted Claude Code and Anthropic-hosted Cloud remain distinct. “Destruction Era” is the corrected target name. Research remains in progress; this is not the completion report and no completion email has been sent.

## 2026-11-23 research continuation — candidate #182

Reviewed `kamalsrini17/mcp-client` at `98c224e6bb3dadc307ee9368ef2733c42195c0ec`. It is a generic Axios REST PM workflow, not an MCP protocol client, Harness adapter, or session/project migration implementation. A loopback-only synthetic workflow probe confirmed six ordinary REST requests; TypeScript no-emit passed. The real localhost writer was not run and no tests are supplied. Reject as a migration candidate. Evidence: `docs/research/evidence/kamalsrini17-mcp-client-review-2026-11-23.txt`.

Current inventory: primary **182/303 reviewed, 121 pending**; supplemental net-new pending **177**; primary + supplemental pending **298**; manual additions **14**, **2 pending**; unresolved including manual **300**. Next primary repository: `kelegele/cli-butler`. Claude Desktop Chat, Cowork, and Code remain separate user-confirmed 3P gateway targets; local/self-hosted Claude Code and Anthropic-hosted Cloud are distinct. “Destruction Era” is the corrected target. Research remains active; this is not the completion report and no completion email has been sent.

## 2026-11-23 research continuation — candidate #183

Reviewed `kelegele/cli-butler` at `2a44cb76ec357ec9b9d99002045fd55052536c56`. It is a standalone local CLI management Skill and not a Projects/Sections/SessionGraph migrator. The 184-test Bash suite passed in a faithful disposable copy; ShellCheck could not run locally because its binary is absent, although the repository CI file calls it. Source-driven temp probes confirmed package-name shell injection through `bash -c` and `.app` symlink removal without the required `.bak`. Retain only its provenance/channel adapter and fixture testing patterns; do not reuse its destructive writer without redesign. Evidence: `docs/research/evidence/kelegele-cli-butler-review-2026-11-23.txt`.

Current inventory: primary **183/303 reviewed, 120 pending**; supplemental net-new pending **177**; primary + supplemental pending **297**; manual additions **14**, **2 pending**; unresolved including manual **299**. Next primary repository: `KingImperio/ctx`. Claude Desktop Chat, Cowork, and Code remain separate 3P gateway targets; local/self-hosted Claude Code and Anthropic-hosted Cloud remain separate. “Destruction Era” remains the corrected target. Research is not complete; this is not the completion report and no completion email has been sent.

## 2026-11-23 research continuation — candidate #184

Reviewed `KingImperio/ctx` at `16ad7a730d57bb3a78e5531d3a6bcc3aeece365e`. It is a broad shared Skills/MCP/CLI ResourcePlane with CLI and MCP façades, but not a Projects/Sections/SessionGraph/history migrator. Source review plus disposable tests showed nested Claude Skills are missed; malicious Skill frontmatter can write outside the skills registry; auto-discover can leave partial output before ENOENT; MCP env secrets are written in plaintext; and git sync init fails because `execFileSync` receives a string instead of argv. 13 JS files passed syntax checks, but no test suite/lockfile exists. Git-based secret exposure is inferred from code, not a tested push. Keep only as a design reference; do not use current writers on real user data. Evidence: `docs/research/evidence/kingimperio-ctx-review-2026-11-23.txt`.

Current inventory: primary **184/303 reviewed, 119 pending**; supplemental net-new pending **177**; primary + supplemental pending **296**; manual additions **14**, **2 pending**; unresolved including manual **298**. Next primary repository: `Kizuno18/dora-explores-binaries`. Claude Desktop Chat, Cowork and Code remain separate third-party-gateway targets; local/self-hosted Claude Code and Anthropic-hosted Cloud remain separate. “Destruction Era” remains the corrected target. Research remains active; no completion email has been sent.

## 2026-11-23 research continuation — candidate #185

Reviewed `Kizuno18/dora-explores-binaries` at `9af34d9f8246613064e1bcf9b74289a2b101301d`. It is a prompt-only reverse-engineering Skill with one canonical `SKILL.md` and human installation recipes across Claude Code, Codex, Cursor/Windsurf, generic LLM/API and instruction fields. This can inform the Skills/content plane only; it does not migrate Projects/Sections/Sessions/transcripts/attachments or Claude Desktop third-party-gateway modes. Plugin JSON parses, but no runtime tests exist and CI is Markdown lint/link checking. Evidence: `docs/research/evidence/kizuno18-dora-explores-binaries-review-2026-11-23.txt`.

Current inventory: primary **185/303 reviewed, 118 pending**; supplemental net-new pending **177**; primary + supplemental pending **295**; manual additions **14**, **2 pending**; unresolved including manual **297**. Next primary repository: `Knaackee/linxmd`. Claude Desktop Chat, Cowork and Code remain separate 3P gateway targets; local/self-hosted Claude Code and Anthropic-hosted Cloud are separate. “Destruction Era” remains the corrected target. Research remains active; this is not the completion report and no completion email has been sent.

## 2026-11-23 research continuation — candidate #186: `Knaackee/linxmd`

Pinned source reviewed at `d831a3ac078bfd6322e87ba10bd860a52be2001f` (2026-04-02T10:48:12Z), isolated shallow clone with clean source tree. Linxmd is an MIT .NET CLI package manager for local/GitHub agents, Skills, workflows and templates, with dependency/version metadata and generated agent wrappers for GitHub Copilot, Claude Code and OpenCode. Its `SyncEngine` sends Skills only to `.claude/skills`; no Project/Section or conversation/Session graph, turn/task-parent relationships, transcript/attachment/token import, schedules, memory, or Claude Desktop Chat/Cowork/Code third-party-gateway adapter was found.

A disposable .NET 8 compatibility copy (only copied project target frameworks changed from `net10.0` to `net8.0`) passed **152/152 tests**. The unmodified candidate could not run against the installed .NET SDK 8.0.129: `dotnet test Linxmd.sln --verbosity quiet` exited 1 with `NETSDK1045` for both projects targeting .NET 10; no upstream .NET 10 CI result is claimed. Synthetic local-library probes reproduced two concrete gaps: after removing a generated agent, Copilot/Claude Code/OpenCode wrapper files all remain; and a skill named `../../../escaped-skill` caused a payload to be written outside the disposable project and expected `.linxmd/skills` root, while remaining inside the disposable probe parent. Neither probe touched user paths or credentials.

Decision: keep only as an adjacent ResourcePlane reference for artifact manifests, dependency metadata and host-specific rendering. Do not recommend it as a Project/Section/Session migrator or trust unverified source paths without containment checks; stale generated wrappers need ownership/cleanup semantics. Detailed evidence: `docs/research/evidence/knaackee-linxmd-review-2026-11-23.txt`.

Primary **186/303 reviewed, 117 pending**; supplemental net-new pending **177**; primary + supplemental pending **294**; manual additions **14, 2 pending**; unresolved including manual **296**. Next primary candidate: `korakotlee/koharness`. Claude Desktop's third-party gateway modes Chat, Cowork and Code remain separately tracked from local/self-hosted Claude Code and Anthropic-hosted Cloud. Product scope continues to use the canonical name **Destruction Era**. Research remains active/incomplete; no completion email sent.

## 2026-11-23 research continuation — candidate #187: korakotlee/koharness

Pinned source reviewed at ada356b058f3b84b6abe54f0b17a1367031e038a (2026-08-05T22:11:52-04:00); CodeGraph indexed 88 files, 907 nodes and 2,137 edges. KoHarness centralizes local/GitHub capability files in a version-controlled dotfiles repository: Skills, MCP configs, and Antigravity workflows; it also documents a raw/wiki/AGENTS.md memory-navigation convention. It has no ChatGPT/Codex Project or Section Group transfer, conversation SessionGraph, turn/branch/subtask relation import, transcript/media/token/schedule migration, or persistent cross-harness session serializer. Here “Project” is a shared dotfiles repository, not a ChatGPT Project.

The README mentions Claude CoWork as a steering-file consumer, but the implemented adapter is explicitly Claude Code; there are no Claude Desktop Chat/Cowork/Code mode adapters. Static and disposable CLI probes show that sync injects memory-navigation stubs rather than importing session history. On an empty fake HOME it created .claude/.gemini/.codex AGENTS.md files even though those harness directories did not exist before. A separate init fixture failed to link Claude MCP because it treated ~/.claude.json (a file) as a directory. A synthetic MCP environment-token probe further showed sync can write the expanded value through a harness symlink back into tracked mcp/mcp.json, leaving the shared repository modified; this used only a fake test value, not a credential.

The full Go suite passed under an isolated, checksum-verified Go 1.24.0 toolchain: 15 packages, exit 0. However, the workflow selects Go 1.23 while go.mod says 1.24.0, and CI only builds/runs lint rather than tests. The checkout has no LICENSE file and the inventory has no SPDX license, so code reuse is not cleared. Decision: retain only as a high-value ResourcePlane and human-readable memory-layout reference; do not adopt as a session migrator or copy its code until licensing, MCP file mapping, secret isolation, and installed-harness gating are addressed. Detailed results: docs/research/evidence/korakotlee-koharness-review-2026-11-23.txt.

Primary **187/303 reviewed, 116 pending**; supplemental net-new pending **177**; primary + supplemental pending **293**; manual additions **14, 2 pending**; unresolved including manual **295**. Next primary candidate: krishna-kudari/agent-skills-manager. Claude Desktop Chat, Cowork and Code remain separately tracked from local/self-hosted Claude Code and Anthropic-hosted Cloud. Canonical name remains Destruction Era. Research remains active/incomplete; no completion email sent.

## 2026-11-23 research continuation — candidate #188: krishna-kudari/agent-skills-manager

Pinned source reviewed at 9b11ae223bad40510b1cb9a81bea39c95521cd66 (2026-02-01T20:01:41+05:30), an MIT Raycast extension for installing Skills discovered from skills.sh/GitHub into 40+ coding-assistant skill directories using symlink or copy mode, with a global skill lock and Git commit-hash update detection. It is a narrow Skills/ResourcePlane tool: no Projects, Section Groups, conversation SessionGraph, turn/branch/subtask hierarchy, transcript/media/token/scheduler/MCP/plugin or durable memory import/export. Claude Code is one skill target; there is no Claude Desktop Chat/Cowork/Code mode adapter or Claude API-Key gateway flow.

README describes global or per-project scope, but the pinned InstallFlow sets scope to the literal global value, comments out the scope-selection step and calls the installer with global=true. Type-check, lint and Raycast build all pass after isolated npm ci (238 packages; install scripts disabled); no test script or test files exist. A source-module runtime probe in an isolated temp harness confirmed that copy mode dereferences a symlink in the fetched skill to copy a synthetic file from outside the skill directory, and recursively deletes an existing unmanaged target file without backup. Skill-name traversal sanitization succeeded; this did not access user files or secrets.

Decision: retain as a useful per-agent Skills path registry and single-source-of-truth reference only. Do not treat it as project/session migration or as support for the three Claude Desktop modes. Before adopting code, require symlink containment/no-follow checks, ownership-aware replacement with backup, and align README claims with actual project-scope behavior. Detailed source and probe evidence: docs/research/evidence/krishna-kudari-agent-skills-manager-review-2026-11-23.txt.

Primary **188/303 reviewed, 115 pending**; supplemental net-new pending **177**; primary + supplemental pending **292**; manual additions **14, 2 pending**; unresolved including manual **294**. Next primary candidate: lakshay2395/employee-management-mcp-server-client-demo. Claude Desktop Chat, Cowork and Code remain separately tracked from local/self-hosted Claude Code and Anthropic-hosted Cloud. Canonical name remains Destruction Era. Research remains active/incomplete; no completion email sent.

## 2026-11-23 research continuation — candidate #189: lakshay2395/employee-management-mcp-server-client-demo

Pinned source review at 7bc698c446d0167eb49f3144490b62fbe96a2ad7 (2025-12-21T20:47:00+05:30). This is a small, genuine MCP example: a FastMCP HR/MySQL server exposing employee CRUD tools, a profile resource and promotion prompt; a LangChain/Gemini agent discovers and calls those capabilities over SSE. Its MCP ClientSession is the protocol connection, not a persistent conversation Session. It contains no ChatGPT/Codex Project/Section or SessionGraph import, turn/branch/subtask/transcript/media/token/schedule migration, Skills/plugin transfer, memory synchronization or Claude API-Key/Claude Desktop mode adapter.

The code is tightly bound to a demo employee database and Gemini client. It binds the SSE server to 0.0.0.0:8000, sets MySQL root with an empty password in source, and hardcodes a placeholder Gemini key. I did not start it, expose a port, connect a database or call a model. The two Python files passed py_compile, but no tests, dependency lock/manifest, CI workflow or LICENSE file were present; README “educational/demo” wording is not a license.

Decision: retain only as a concept-level reference for MCP Resources/Tools/Prompts and SSE handshake. Not a cross-Harness migration candidate and unsafe to run as written against real HR data. Detailed review: docs/research/evidence/lakshay2395-employee-management-mcp-server-client-demo-review-2026-11-23.txt.

Primary **189/303 reviewed, 114 pending**; supplemental net-new pending **177**; primary + supplemental pending **291**; manual additions **14, 2 pending**; unresolved including manual **293**. Next primary candidate: Lartweib/dotai. Claude Desktop Chat, Cowork and Code remain separately tracked from local/self-hosted Claude Code and Anthropic-hosted Cloud. Canonical name remains Destruction Era. Research remains active/incomplete; no completion email sent.


## 2026-11-23 continuation — candidate #190 and Claude Desktop target confirmation

Pinned candidate #190 `Lartweib/dotai` at `36eabaec4d4a1d2e840d37c873f3054767be3860` (MIT) was fully inspected and tested. Dotai is an excellent resource/config pack pattern for Claude Code CLI, Google Antigravity CLI and OpenCode, with dry-run/plan, backup, journal, isolated config and restore behavior. Its `run claudecode` can pass an API key and custom base URL through to a local command; a synthetic fake-HOME/fake-CLI probe verified pass-through and restoration without a real API request. Its reach stops at configuration resources: no ChatGPT/Codex Projects, Section Groups, conversation hierarchy, turn/branch/task relations, attachments/media/tokens, durable conversation memory or scheduled-task migration. Keep as an architecture/reference, not the session migrator. Evidence: `docs/research/evidence/lartweib-dotai-review-2026-11-23.txt`.

### Target clarification: all three Claude Desktop capabilities through provider gateway

The target now explicitly includes **Chat, Cowork and Code** in Claude Desktop configured for third-party inference, in addition to local/self-hosted Claude Code via API key. Current Anthropic documentation calls this **Claude Desktop on 3P** and describes routing all model inference through a configured cloud provider or organization's LLM gateway. This is a separate deployment/data plane from Anthropic-hosted claude.ai and Anthropic-hosted Claude Code Cloud.

The three-mode requirement is correct for feature coverage, but not three forever-independent target roots: **Unified Claude is rolling out and merges Chat and Cowork into one conversation experience; Code remains separately organized.** Model both the selected/realized mode and shared Project/context links, and preserve source-mode provenance, thread/branch/subtask relations, files and side effects.

Official Claude-to-Claude move is instructive but not a ChatGPT/Codex importer: the vendor importer copies the user's own Claude chats/projects and local Cowork/Code sessions; it omits Cowork/Code cloud sessions and file bytes from personal export; memory, instructions, connectors, API keys, and some attachments/artifacts need manual handling. It is a one-time copy with repeat import/idempotence rules, not live sync. Thus Nexus needs its own source parsers and must emit a loss ledger, safe archive, mapped target artifacts and resumable handoff.

Target adapter facts that should shape the canonical schema and tests: Desktop 3P has a separate local application-data namespace (`Claude-3p`); Chat/Cowork session state and working directory include transcript, uploads, outputs and audit log; per-project memory lives under project IDs. Code has a separate Desktop session-index record but its actual transcript uses Claude Code's own `~/.claude/projects/` store; settings/Skills/plugins/hooks/MCP and trust state may also be shared with the CLI. Model the Code `session_record` distinct from `transcript`. An unencrypted Desktop export may contain conversation content/secrets written into files or MCP args, while provider keys, connector sign-ins and environment values are intentionally not migrated. Nexus should default to redaction/encryption and require re-consent for credentials, MCP, connectors, permissions and hooks.

Plan implication: implement three target capability adapters (Chat, Cowork/Unified, Code) behind one Claude Desktop 3P target profile, plus a separate local Claude Code CLI adapter and explicit Anthropic Cloud session profile. For each source object, report native round-trip support, transform loss, unsupported topology, missing attachments, token/cost accounting fidelity and whether it is only an archive or resumable target. See the official-source evidence in `docs/research/evidence/lartweib-dotai-review-2026-11-23.txt`.

Primary **190/303 reviewed, 113 pending**; supplemental net-new pending **177**; primary + supplemental pending **290**; manual additions **14, 2 pending**; unresolved including manual **292**. Next primary candidate: `lazyworkshop-create/skills-manager. Canonical product name: **Destruction Era**. Research remains active/incomplete; no completion email sent.


## 2026-11-23 continuation — candidate #191: lazyworkshop-create/skills-manager

Pinned candidate `lazyworkshop-create/skills-manager` at `9d794f6491444b9705e0d0914092dd8552a972a1`. It is a small cross-platform Python downloader/updater for Skills from wshobson/agents. It adds no Projects, Sections, SessionGraph, conversation records, attachments, tokens, MCP/plugins, memory, schedules, API-key setup or gateway target; its only plausible relevance is Skills discovery/copy UX. It has no tests, CI, dependency lock or license file. `py_compile` and `--help` passed; a DeprecationWarning is emitted by `locale.getdefaultlocale`. The `--claude-install` path is a generic legacy `Claude/skills` directory, not the documented Claude Desktop 3P extension mechanism or Claude Code filesystem Skills path. A fake-only isolated probe reproduced an install key `../../escape` writing outside the selected target, deleting an unmanaged preexisting destination, and dereferencing a Skill symlink to copy an external synthetic marker. Its normal updater also deletes existing destinations before copy and runs pip on remote Skill requirements through `shell=True`. Do not reuse its source or target mapping; retain only as a narrow discovery UX reference. Full evidence: `docs/research/evidence/lazyworkshop-create-skills-manager-review-2026-11-23.txt`.

### Target implications from current official Anthropic documentation

Claude Desktop on 3P supports Skills, but stores user extensions in its app-local data model; in-app user-added skills are per-device. Organization-wide content is delivered through plugins/marketplaces or a system-wide plugin directory. In the distinct Code mode, filesystem Skills use `~/.claude/skills/` (personal) or `.claude/skills/` (project). Claude account Skills do not sync into Claude Code sessions authenticated with an API key or third-party cloud provider. For this task, Nexus must model separate target adapters for Desktop 3P Chat/Cowork user extensions, Desktop Code/CLI filesystem Skills and team-distributed plugin marketplaces; never assume copying a `Claude/skills` folder achieves all three. The official sources are linked in the candidate evidence file.

Primary **191/303 reviewed, 112 pending**; supplemental net-new pending **177**; primary + supplemental pending **289**; manual additions **14, 2 pending**; unresolved including manual **291**. Next primary candidate: `learnrudi/cli. Research remains active; no completion email sent.

## 2026-11-23 continuation — candidate #192 + confirmed Claude Desktop 3P scope

User confirmed that the target covers **Chat, Cowork and Code**, all in Claude Desktop on third-party inference/API-key gateway mode. This means the local 3P Desktop application, not merely standalone Claude Code CLI; Anthropic-hosted Claude Code Cloud remains separate. Official 3P docs confirm provider-routed inference, local conversation storage, Chat/Cowork/Code, and a Claude-native importer for Claude.ai/local Claude sessions, not a documented ChatGPT/Codex source adapter. Chat and Cowork may be Unified Claude in the UI; Code remains separate. Model source surface and effective target mode explicitly.

Target storage differs by mode: Chat/Cowork use local-agent-mode session state, transcript/audit, uploads/outputs and memory; Code has a Desktop session index plus its transcript in `~/.claude/projects/`. App-managed Skills/plugins/MCP, Code filesystem configuration, local/project memory, scheduled tasks and project/group structures need distinct adapters. The official import wizard is one-time and has its own omissions; 3P scheduled tasks run locally and require an awake app/device. Do not directly mutate private target stores or call them officially supported. Current primary-source details: `docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`.

### Candidate #192 — `learnrudi/cli`, pinned `797980b5a906e258c54d54c49ad3cfbb367e5279` (MIT)

Detailed review: `docs/research/evidence/learnrudi-cli-review-2026-11-23.txt`. High-value ResourcePlane/host-control architecture: multi-harness Skills projection with digest/ownership/drift/rollback; MCP secrets and native CLI runtime management; isolated provider launch and native resume pointers. It is not a cross-Harness session importer. Current CLI retires `sessions`/`projects`/`import`; historical DB conversion is internal RUDI data and lossy; resume only works from a stored launch record with a native provider session ID; groups are parallel launches, not conversation branches. Isolated frozen install, documented unit tests (953 pass, 0 fail, 10 skipped), build and package dry-run pass; no live provider E2E.

Counts: primary **192/303 reviewed, 111 pending**; supplemental net-new pending **177**; primary + supplemental pending **288**; manual additions **14, 2 pending**; unresolved including manual **290**. Next primary candidate: `liangquanzhou/agentctl`. Research remains active/incomplete; no completion email sent.

## 2026-11-23 continuation — candidate #193 and a higher-priority session-migration lead

### Candidate #193 — `liangquanzhou/agentctl`

Pinned `master` / `refs/remotes/origin/master` at `006d5c3b3c604e938fef93f65a0ccca1d75a7d6c` (release `v0.6.0`, 2026-09-01). It is a genuinely capable cross-harness ResourcePlane/control plane for MCP, rules/hooks/commands/files/ignore, Skills and static subagent role definitions, with plan/apply/status/rollback and solid Go quality (553 tests pass; race, vet and build pass). It is not a user-conversation session or Project/Section importer: no transcript store/import/session graph/ChatGPT mapping or model API-key/gateway setup.

The explicit Claude 3P/Cowork Skill support writes to an internal macOS `Claude-3p/.../skills-plugin/<org>/<account>/skills` path and synthesizes plugin/manifest JSON. The path is hardcoded to macOS, not supported on the official Windows/Linux data roots. With no existing plugin cache, target discovery is empty and `skills sync --dry-run --target claude-3p` returns exit 0 with `targets:null`/`actions:0`; with several profiles it picks the lexicographically first, not an explicit active profile. A fake-HOME test confirms the writer/idempotence only; no live Desktop accepted the output. The official Anthropic extension docs describe user UI and admin marketplaces/system-wide directory, not a supported external `skills-plugin` writer. Treat this as experimental implementation-dependent resource integration, not a verified production adapter. Detailed evidence: `docs/research/evidence/liangquanzhou-agentctl-review-2026-11-23.txt`.

### New high-priority manual lead — `leofmarciano/agentctl` (not yet reviewed)

GitHub search found a project whose README claims a canonical conversation/event store, Codex thread import via the public history API, Claude Code attach/resume, and portable export/import. It has not yet been pinned or source/test audited, so it is only a **queued research lead**, not a validated capability. Review checklist/evidence: `docs/research/evidence/leofmarciano-agentctl-queue-2026-11-23.txt`.

Counts: primary **193/303 reviewed, 110 pending**; supplemental net-new pending **177**; primary + supplemental pending **287**; manual additions **15, 3 pending**; unresolved including manual **290**. Next primary candidate: `lidorshimoni/agentic-coding-design-patterns`. Research remains active/incomplete; no completion email sent.

## 2026-11-23 continuation — candidate #194 `lidorshimoni/agentic-coding-design-patterns`

Pinned `main` at `fb84be7a64ec600252b8653babe2b7111ff79901` (MIT; no GitHub release). This is a prompt/skill-content library with a zero-dependency compiler that emits Claude Code commands, Antigravity skills, Cursor rules, Windsurf/Roo/Cline instructions, and Copilot/AGENTS.md. It has no Codex/ChatGPT or Claude Desktop 3P target and no Projects/Sections, conversation/session graph, transcript, attachment/token or native schedule importer. Its “multi-session” `/teach` means user-maintained files in a learning workspace, not migrated vendor sessions.

The Claude Code writer targets legacy `.claude/commands`, whereas Anthropic recommends `.claude/skills/<name>/SKILL.md`; it flattens other formats as text. It has no tests, CI, dry-run, ownership, diff, backup or rollback. A disposable fake project demonstrated that its Copilot exporter overwrites both existing `AGENTS.md` and `.github/copilot-instructions.md` without preserving unrelated content. Keep the curated prompt content only after review; reject the writer for safe Nexus migration. Evidence: `docs/research/evidence/lidorshimoni-agentic-coding-design-patterns-review-2026-11-23.txt`.

Primary **194/303 reviewed, 109 pending**; supplemental net-new pending **177**; primary + supplemental pending **286**; manual additions **15, 3 pending**; unresolved including manual **289**. The high-priority `leofmarciano/agentctl` session-import lead remains queued and unaudited. Next primary candidate: `LMPrado-DZ23/awesome-agent-plugins`. Research remains active/incomplete; no completion email sent.

## 2026-11-23 continuation — candidate #195 `LMPrado-DZ23/awesome-agent-plugins`

Pinned `main` / `refs/remotes/origin/main` at `163484b3aa54d0c048868e499310b49719dbafae` (2026-11-16). This is a high-value discovery/resource catalog (589 entries, 945 projects, 13 clients) with typed MCP/Skill/native-plugin records, source/license metadata, alternatives, per-client install renderers, a validator, health workflow and a safety-gated CLI. Its “Sessions & Messages” category (10 entries + 7 alternatives) is a list of tools, predominantly DeepSeek Harness plugins—not an import API or SessionGraph. It does not include ChatGPT/Claude Desktop 3P session import or project hierarchy conversion. Treat its 589 rows as an external lead source requiring dedup/provenance, not as 589 new reviewed repositories. Candidate #195 source review, exact tests/e2e and session-catalog leads: `docs/research/evidence/LMPrado-DZ23-awesome-agent-plugins-review-2026-11-23.txt`.

Counts: primary **195/303 reviewed, 108 pending**; supplemental net-new pending **177**; primary + supplemental pending **285**; manual additions **15, 3 pending**; unresolved including manual **288**. Existing primary queue includes the `vshulcz/deja-vu` session-reader lead found in this catalog. The high-priority manual `leofmarciano/agentctl` lead remains unaudited. Next primary candidate: `mabyko/AgentHarnessManager`. Research remains active/incomplete; no completion email sent.


## 2026-11-23 范围确认与官方文档复核

用户已明确：目标是本地 Claude Desktop 的第三方推理/网关模式，Chat、Cowork、Code 三种均纳入；不是 Anthropic 托管的 Claude Code Cloud session，也不只是独立 Claude Code CLI。当前官方文档把它描述成“推理可路由至用户配置的云 provider/gateway、对话数据保存在设备”的产品面。Chat/Cowork 与 Code 使用不同 session/data store；Unified Claude 还会随设备 Cowork VM 能力把首页消息路由到 Cowork 或 Chat。仅凭同一个 API Key、网关或 App 名称，不可合并 session writer。

本次官方文档核对发现：`local-agent-mode-sessions/` 保存 Chat/Cowork session 状态、工作目录、附件副本、输出、审计记录及分层 memory；`claude-code-sessions/` 保存 Code 元数据，Code transcript 则在共享 `~/.claude/projects/`。Chat/Cowork 的 `audit.jsonl` 可含提示、回答、工具输入/结果、权限决策及 token/model 等细节；官方明确它未加密且 Code 不写该 audit 文件。内置 import wizard 面向 Claude.ai 历史/项目及本机早期 Cowork/Code session；这是 Claude 来源的专用导入，并不是 ChatGPT/Codex 的通用 importer。详细的 OS 路径、附件/项目/memory/schedule、恢复约束及官方来源记录在 `docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`。仍需锁定你的 Desktop 版本、OS 和具体 provider，待用副本验证每种 mode 的 session discovery/resume 前不得写入 app 私有存储。

## 2026-11-23 GitHub 深审 #196：AgentHarnessManager

`mabyko/AgentHarnessManager` 固定于 `e64249777df41377e93d5ce12a259d6fd264e4c5`，MIT，当前 GitHub Releases 页面没有 release。它是具有实测审查/审批/journal/rollback 的 macOS Skills、全局指令与 CLI/MCP 管理器，而不是 SessionGraph adapter。其 `SkillGroup` 的 `skillIDs` 只组织/激活已安装 Skills，`WorkProfile` 保存本地 Skill/path 快照；二者均不是 ChatGPT Project、Codex Section、会话或主从/分支关系。未找到聊天、转录、attachment 或会话导入/导出模型；MCP 的 `request` 只入队待人审查的本地 Skill 开关请求。Swift 93 项测试、Xcode app build、合成 CLI/MCP 与 app-state 检查通过，但这不代表 Claude Desktop 3P 的目标端兼容。保留为 ResourcePlane 安全/UX 参考，排除为会话迁移器。完整证据见 `docs/research/evidence/mabyko-agentharnessmanager-review-2026-11-23.txt`。

主 GitHub 语料 **196/303 已审、107 待审**；补充 catalog net-new 177 待审；两队列合计待审 284；人工补充 15 项中 3 项待审；总未解决（计入手工待审）287。下一个主队列候选 `madshn/ai-playbooks`。研究仍在进行中，尚未发完成邮件或声称满足最终覆盖要求。


## 2026-11-23 GitHub 深审 #197：AI Playbooks / 1p-creds

madshn/ai-playbooks 以 MIT 发布一份 Claude Code 专用的 1Password 凭据管理 Skill；README 中 Codex/Gemini 仍是 TBD。它可作为狭义 credential hygiene / ResourcePlane 参考，但“跨 Harness”只是 shell 环境变量继承，不提供 Projects、Section Group、Session/分支/消息/附件迁移，也不支持 Claude Desktop 3P Chat/Cowork/Code 写入。此 repo 是 Prompt/Markdown，没有可执行迁移引擎、自动化测试或 CI，不适合作为无需 AI 的确定性转换器。

静态安全审查记录了关键风险和正向防护：Phase C 把真实凭据暂写入 0600 /tmp 文件；Layer 5 的 rg -Fn 匹配后会打印包含 secret 的整行；rotate 流程要求把新 secret 粘贴进 assistant 对话；可选销毁 1Password 项目前只用长度差异阻断，等长不证明内容相同；工具授权包含 Edit/Write/Bash，并可自动执行文件清理和 commit。保护侧有明确 GUI/用户确认、legacy_source 与 vault_reference 区分、SSH key 文件级排除等。没有访问真实凭据、调用 op、改动用户项目或删除 vault item。详细审查见 docs/research/evidence/madshn-ai-playbooks-review-2026-11-23.txt。

官方 1Password 文档当前确认 Environments 和 Mac/Linux 本地 .env mount，但未在所核对页面确认 FIFO 实现；文档列有 op environment read 的 deprecation/removal 计划，而 AI Playbooks README 仍指向该命令。技能本身也保留“Environments still in beta”的旧说明；具体版本/API 状态需在真实用户环境中重新确认，不能据此自动迁移。Claude Code 官方 Skills 文档说明 allowed-tools 是本次调用的预授权，默认可自动调用的 Skill 应先审其权限；见 evidence 中官方链接。

主 GitHub 语料 197/303 已审、106 待审；补充 catalog net-new 177 待审；两队列合计待审 283；人工补充 15 项中 3 项待审；总未解决（计入手工待审）286。下一个主队列候选 magnumquest39-cloud/AntoSkills。研究仍在进行中，尚未完成或发完成邮件。


## 2026-11-23 用户范围确认与候选 #198 AntoSkills

用户已明确：Claude Desktop 的目标包含第三方推理 / Gateway 配置下的 Chat、Cowork、Code 全部三种模式；另包含本地或自托管 Claude Code。它们需与 Anthropic 托管 Cloud sessions 分开建模。最新一手文档显示 3P Desktop 的 Chat、Cowork、Code 共用可配置的推理提供方，但各模式的 session、project、memory、workspace 与本地数据布局仍不同；Code 使用嵌入式 Claude Code 引擎。3P 会话保存在设备上，远端 SSH 会话另有远端落盘。Claude 官方导入器的范围是 Claude.ai 历史/项目以及既有本地 Cowork/Code 会话，并非 ChatGPT/Codex 通用会话写入器。来源与字段级差异见 docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt。

候选 #198 magnumquest39-cloud/AntoSkills 固定于 main d87ad2628e0f2840e25895f2af11cf064b47a3a7。它在 Claude Code/Codex Skill 文件发现、审核、固定版本与同步上是可复用的 ResourcePlane 参考，但无 ChatGPT/Codex Projects、Sections、sessions、消息、分支、附件、Usage、Memory、Schedules 的导入/导出模型，也没有已验证的 Claude Desktop 3P Chat/Cowork/Code 适配。Code 模式兼容性尚未测试，不能仅凭 .claude/skills 路径推断。npm 0.2.0 与 pinned source 的产物、SHA-512、51 个构建文件均交叉核验。18 个测试文件 121 passed / 6 skipped；typecheck、lint、build、离线 smoke 与 MCP handshake 均通过，仅代表该 Skill package 的自身生命周期，不代表 session fidelity。安全审查发现目录名碰撞只检查 skills.lock，而实际链接函数会递归清理目标下已有的真实目录；Nexus 若实现 Skill 落地，应另外要求资源归属校验、预览、人类确认和可回滚写入。完整复核、来源和执行结果见 docs/research/evidence/magnumquest39-cloud-antoskills-review-2026-11-23.txt。

当前语料状态：主 GitHub 候选 198/303 已审、105 待审；补充 catalog net-new 177 待审；两队列合计待审 282；人工补充 15 项中 3 项待审；计入人工待审后未解决 285。下一项主队列候选为 marcm8793/skill-forger。研究持续进行中，未宣称覆盖完成，未发送完成邮件。


## 2026-11-23 GitHub 深审 #199：skill-forger

候选 #199 marcm8793/skill-forger 固定于 main 与 v0.1.10 tag peeled commit 0cd67497e3dc9b92729ae8dcbf26514d9560f96e。它是基于 Vercel Skills CLI 的 repo 级 skills.json 声明和安装包装器，默认 Claude Code，可将 Codex、Cursor、GitHub Copilot 目标交给依赖处理；没有 ChatGPT/Codex Project、Section、session/message/branch/attachment、Usage、Memory、Schedule 的读取或写入，也没有 3P Desktop Chat/Cowork 适配。通过 Claude Code 目标推断 Desktop Code 兼容性未有实测，不能视为支持。

隔离检查通过 36 个测试、typecheck、静态 check 与 build；测试主要覆盖 source parsing、配置/lock 条目、路径发现及 gitignore，不覆盖外部 Skills CLI 或目标 Harness session fidelity。对临时合成项目执行 all-skills uninstall 后，skills.json 与 skills-lock.json 条目被删，但 .claude/skills/demo/SKILL.md 仍在，CLI 仅打印 warning。安装包装器向底层 CLI 传入 yes=true，config/lock 文件直接重写，无原子 journal/rollback。npm 0.1.10 tarball integrity 与官方 registry 匹配，v0.1.10 tag 指向同一 source commit；本地使用 lock 中 obuild 版本重建后的 dist 与发布 bundle 字节不完全一致，完整 Bun lock 环境不可用，因此 release build reproducibility 仍未证实。完整执行记录见 docs/research/evidence/marcm8793-skill-forger-review-2026-11-23.txt。

当前主队列 199/303 已审、104 待审；补充 catalog net-new 177 待审；两队列合计 281；人工补充 15 项中 3 项待审；计入人工待审后未解决 284。下一个主队列候选 mazen160/skills-manager。Chat、Cowork、Code 三个 Claude Desktop 3P mode 与本地/自托管 Claude Code 保持独立 adapter scope；研究仍在继续，未完成，未发送完成邮件。


## 2026-11-23 GitHub 深审 #200：mazen160/skills-manager

候选 #200 固定于 main commit 9bb8d40f77701ceb02dd15f49430c45dd04b8166，MIT；PyPI 当前 1.0.4。它是跨 Claude/Cursor/Codex/OpenCode 的全局 Agent Skill 安全扫描器与安装/更新 CLI，不是 SessionGraph、ChatGPT/Codex Project、Section 或 Claude Desktop 3P Chat/Cowork/Code 迁移器。主分支包含 155 项通过的标准库测试；静态扫描运行前不执行 Skill 源码，可作为 Nexus ResourcePlane 安全门、机器可读 findings、路径/资源上限与策略分层参考。AI review 为可选；调用用户本地 agent CLI 时，应按 source 可能流向模型 provider 的边界单独处理。

分发证据：PyPI 1.0.4 wheel SHA-256 与官方页面相符，其唯一生产模块 skills_manager.py 与 pinned Git main 逐字节一致（166,402 bytes）。但 PyPI 没有 provenance attestation；当前 README/GitHub Releases 仍显示 1.0.2，PyPI/pyproject/main 为 1.0.4，远端 tag 也没有 v1.0.3/v1.0.4。记录为发布元数据漂移，不能将 PyPI 发布视为可追溯 CI 构建。

重要版本边界：scanner 扩展功能位于未合并的 draft PR #1（85d982038f0e4fc4a896c408bbbbd4326a76cd2b），不是当前 main/PyPI 行为。PR 试验性新增 analyzer registry、Unicode/pipeline/行为检测、policy、SARIF、递归 ZIP/TAR 等，GitHub CI 与本地 176 项测试均通过。但合成 1,001 member TAR 表明它切片到前 1,000 项却没有产生截断 finding：将目录排在前、恶意脚本排在第 1,001 项时没有扫描尾项；整个 TAR 只有 generic high finding，默认 medium 门会挡住它，但显式放宽到 high 时策略接受该结果。另 TarFile.getmembers() 在应用限额前会物化全部头部；需预先限制流式解析。主分支只把 archive 标成 high、默认阻挡，并未递归查 TAR 内容。

另一个一致适用于 main 与 PR 的 rollback 边界由合成探针复现：若新目录 rename 失败且随后备份恢复 rename 也失败，copy_skill_tree 的 finally 会删掉唯一 backup；测试后 destination 不存在、原内容丢失。正常路径的同文件系统替换通过 155/176 测试，但失败恢复路径应保留备份供人工恢复。完整审计和逐字输出见 docs/research/evidence/mazen160-skills-manager-review-2026-11-23.txt。

当前状态：主队列 200/303 已审、103 待审；补充 catalog net-new 177 待审；合计待审 280；人工补充 15 项中 3 项待审；计入人工待审后未解决 283。下一项主候选 mejbaurbahar/awesome-qa-agent-skills。所有 Claude Desktop 3P mode（Chat/Cowork/Code）与本地/自托管 Claude Code 仍各自保持 adapter scope；研究未完成，未发完成邮件。

## 2026-11-23 GitHub 深审 #201：mejbaurbahar/awesome-qa-agent-skills

当前 main 固定为 1665963f605ceecb2ee14aea140a704c2046cae8（MIT）。这是 194 个 QA/PM Agent Skills 的内容目录，分 21 类，README 记录 14 个 vendored 上游的 commit 和 license，静态校验、目录生成和 fake-home 安装/卸载 smoke 均通过。范围是 Claude Code 与 Antigravity 的 Skill 内容部署，不是 ChatGPT/Codex Projects、Section/Section Group、嵌套 Session、分支/附件/记忆/定时任务迁移，也不实现 Claude Desktop 第三方网关下 Chat、Cowork、Code 任一 mode 的 session writer。只保留为低优先级 ResourcePlane 内容/来源追踪参考。

安全边界：隔离临时目录中，替换 manifest 已记录 symlink 为含哨兵文件的用户目录后执行卸载，哨兵被删除；向 .installed 追加 Skills 根目录之外的临时目录后，卸载同样递归删除。说明卸载的所有权判定只相信路径字符串；本地 manifest 被替换/污染时不能安全区分用户内容。sync_vendor.py 在校验/复制新源之前先删旧 Skill 目录，copy_skill() 也先 rmtree 目标再复制，更新并非事务性。可选 77 个 Product-Manager-Skills 属 CC-BY-NC-SA-4.0，并在运行时 shallow clone/pull 最新上游，但 installer 不记录解析出的 commit，重现性较弱。完整源证据和隔离执行输出：docs/research/evidence/mejbaurbahar-awesome-qa-agent-skills-review-2026-11-23.txt。

状态：主队列 201/303 已审、102 待审；补充 catalog net-new 177 待审；两队列合计 279；人工补充 15 项中 3 项待审；计入人工后未解决 282。下一个主队列候选 miles990/skillpkg。Claude Desktop 3P Chat/Cowork/Code 仍各自为验收轨道，并与本地/自托管 Claude Code 分开；研究未完成，未发送完成邮件。

## 2026-11-23 GitHub 深审 #202：miles990/skillpkg

当前 main 固定于 8ec9655e8267e1fe9b37a4edc488c16f591233e7（2026-01-15）。README 明确标记项目 Archived，并说明其 Skill 安装/同步功能已被 Claude Code Plugin Marketplace 取代。它的历史价值在 ResourcePlane：Skill 元数据/依赖树、项目本地 skillpkg.json、安装状态、MCP 配置模型，以及 Claude Code/Cursor/Codex/Copilot 的 Skill 目录投影。它不是会话移植器：没有 ChatGPT/Codex Projects、Section Groups、嵌套 Session、主从/分叉消息图、附件、token usage、持久记忆或定时任务的数据模型；也没有 Claude Desktop 第三方网关下 Chat、Cowork、Code 的会话数据库适配器。README 的 v1→v2 migrate 指项目自己 skillpkg.json/state 格式，不是跨 Harness。

功能边界：新 Syncer 可以写多个 Skill 目录，核心 syncMcpConfig 方法也能写 MCP 配置；但 CodeGraph 只找到 syncAll 的测试调用点，当前 CLI auto-sync 与 MCP sync_skills 都走 syncToTarget，因此 MCP 配置写入没有接到正常用户侧流程。旧 AdapterManager/Importer 使用另一套 Claude Code、旧 Codex Agent markdown、Copilot instruction block、Cline 适配。CLI README 虽写 skillpkg sync，但 CLI 注册表没有 sync；migrate 也被注释掉，构建后的 CLI 分别返回 unknown command。Codex 原生 .codex/skills/SKILL.md 经自动检测被误标成 Claude Code，显式 platform=codex 导入则拒绝；Importer 的 Skill 返回值不含文件资产，reference 文件丢失。导出器只写 SKILL.md。即便同步目录，SKILL.md 内容相同且附加文件数量相同但内容不同时，也会误报 unchanged，保留旧 asset。

验证：使用 lockfile 声明的 pnpm 8.15.0 安装 frozen dependencies 成功；build、typecheck 通过；测试 259/261，两个失败断言和当前 schema 的 required/additionalProperties 定义不一致；lint 有 7 个 error/7 个 warning。GitHub 没有工作流运行/本地 .github 目录。npm CLI/core/MCP 包 latest 为 0.5.7，2026-01-12 发布；官方 registry integrity 与下载 tarball 匹配，当前源码 build 的共同 entrypoint 字节匹配，但 tarball 另含旧 dist 遗留文件。

隔离 POC：空输入的 cleanupOrphans 删除了未由 skillpkg 管理的 .claude/skills 子目录；syncMcpConfig 覆写并丢弃了原有 user_server；parseSkillMd 接受 ../../store-escape，StoreManager 随即在 .skillpkg root 外创建 SKILL.md；Exporter 也接受 ../export-escape 并越出输出目录写文件。以上只触碰临时目录，但表明不可直接复用其写入/卸载逻辑。完整源、输出与限制：docs/research/evidence/miles990-skillpkg-review-2026-11-23.txt。

结论：不纳入 Nexus Memory 核心迁移器 shortlist。仅保留为历史性 Skill/MCP ResourcePlane 参考；重新实现时必须加入名称规范化与路径 containment、文件所有权 manifest、资产逐项 hash、对现有 MCP 配置的 review/merge、事务暂存及 rollback。主队列 202/303 已审、101 待审；补充 net-new 177；合计 278；人工补充 15 项中 3 项待审；含人工待审总计 281。下一项主队列候选 MlsMoon/moon-game-dev-tool-manager。研究未完成，未发送完成邮件。

## 2026-11-23 GitHub 深审 #203：MlsMoon/moon-game-dev-tool-manager

候选 #203 固定于 `develop` 的 `f204cb9271954895200a92c282f71ffdb963997b`（MIT，Windows WPF；最新 Release v0.2.5）。它是 MlsMoon Agent Skills 与 Unity Plugin/Package 的目录和安装管理器，不包含 ChatGPT/Codex Project、Section Group、SessionGraph、turn/task/fork 层级、transcript、附件、token、memory、schedule 的读写，也没有 Claude Desktop 第三方网关 Chat/Cowork/Code adapter。仅保留为低优先级 ResourcePlane/catalog UX 参考，不列为核心迁移引擎。

源码链路显示普通 Skill 的 `id`/`installName` 直接参与 `.agents/skills/<id>` 路径组合，未做工作区 containment；`SkillCopy.Replace` 遇到已存在的非 Git 目标目录会递归删除，不要求该目录有 MlsMoon ownership marker。临时合成 Core POC 证实：无 marker 的碰撞目录中的 sentinel 被删除；`id=../../../escaped-skill` 可落到 disposable workspace 外，并删除那里无 marker 的 sentinel 后写入合成 `SKILL.md`。所有数据均在唯一 `/tmp` 临时根内。Plugin/Package 路径另有 workspace containment 校验。原始 SDK 8.0.129 的测试在编译时遇到八处 C# 12 `string.Split` overload ambiguity；只在临时兼容副本改成等价 char-array overload 后得到 21 pass / 3 个 macOS 下 Windows-path 假设失败。锁定 commit 的官方 Windows CI #18 为绿色；这些本地差异不等于 upstream Windows CI 失败。完整源码链路、输出和限制见 `docs/research/evidence/mlsmoon-moon-game-dev-tool-manager-review-2026-11-23.txt`。

主队列 **203/303 已审、100 待审**；补充 catalog net-new 177 待审；合计待审 277；人工追加 15 项中 3 项待审；计入人工待审后未解决 280。下一个主队列候选 `mocikadev/mocika-samsara`。Claude Desktop 仍分开覆盖第三方网关 Chat、Cowork、Code，并包括本地/自托管 Claude Code；Anthropic 托管 Cloud 不混为同一目标。研究仍在继续，尚未完成，未发完成邮件。

## 2026-11-23 GitHub 深审 #204：mocikadev/mocika-samsara

固定于 `main` commit `4de9564444e235164ea3e1b4443b4478866627a1`（2026-05-30；samsara v1.0.0；MIT OR Apache-2.0）。它是本地优先的 Markdown 知识/经验管理器：记录 error/skill/pattern/insight，重复后晋升规则，提供 Git 同步、六个 stdio MCP 工具和 OpenCode 会话启动/压缩时读取注入。可作为 Memory/ResourcePlane 参考，但不是 Projects/Sections/SessionGraph 迁移器：源码无 session、task/主从/分支、message/transcript、attachment、usage、schedule 的导入/导出模型；README 所称迁移是 AI 批量写 lesson 或逐条 CLI 写入。MCP `write_lesson` 是经验记录接口，不是会话导入；未发现 Claude Desktop 第三方网关/Chat、Cowork、Code 的 session writer。

验证：锁定版本 46 个测试（8 suites）通过；fmt、clippy `-D warnings`、release build 通过；官方 CI #20 和 v1.0.0 release 已核对。隔离 POC 发现未经校验的 lesson domain/keyword 可使实际 CLI 在知识库根外创建文件；fake HOME 下 `--dry-run init` 仍创建目录。普通 fake-home init 会保留已有 MCP server 并可幂等重跑，但不证明 live Desktop/3P mode 兼容。代码的自动提交/远端 push 使用 `git add -A`，未见 secret filtering；API key 不应放入此知识库。完整源码、实测 stdout/stderr、输出和限制见 `docs/research/evidence/mocikadev-mocika-samsara-review-2026-11-23.txt`。

主队列 **204/303 已审、99 待审**；补充 catalog net-new 177 待审；合计待审 276；人工追加 15 项中 3 项待审；计入人工待审后未解决 279。下一个主队列候选 `pewpewgogo/agentcrew`。Claude Desktop 仍分别覆盖第三方网关 Chat、Cowork、Code，并纳入本地/自托管 Claude Code；Anthropic 托管 Cloud 单独建模。研究仍在继续，未宣称完成，未发完成邮件。

## 2026-11-23 GitHub 深审 #205：pewpewgogo/agentcrew

固定于 `main` commit `5af3a362fc1c37834ad0c60c8d3d2d6bb84c65e5`（2026-06-01；MIT；npm v0.1.0）。AgentCrew 是团队 Project → Milestone → Task 管理器，带项目知识库（repo/URL/技术栈/notes）和 human/agent append-only context log，可经 REST、MCP、CLI 访问。它适合作为共享工作上下文参考，不是 ChatGPT/Codex Project/Section 或 Claude Desktop Chat/Cowork/Code 的 SessionGraph importer。Context 记录只有 target type/id、author kind、时间和纯文本 note；无 conversation/session/message ID、分支/主从关系、附件、token usage 或 schedule 导入。`cs_s_` 是应用登录 bearer，不是对话 session；`cs_k_` 是 AgentCrew API key，不是模型 provider key。

构建与 lint 通过；6 个明确不依赖数据库的测试文件共 16 项通过。全量 29-file Vitest 中 23 个数据库 suite 因 Docker/Postgres 不可用、`localhost:54329` 拒绝连接而未初始化，不能称全量测试通过。只在临时目录用假 token 测得：Claude Code MCP API key 写入新建 `~/.claude.json` 时为明文、POSIX mode 0644；而 `~/.agentcrew/config.json` 另有 chmod 0600。未用真实 token、服务端或用户配置。checkout 无 GitHub workflow/release。完整源和限制见 `docs/research/evidence/pewpewgogo-agentcrew-review-2026-11-23.txt`。

结论：只保留为项目/任务/append-only 共享 context 参考，不列为会话迁移器。若未来映射到 Nexus，需要保留 `harness`、source Project/Session/Message ID、父子/分支 provenance 与附件，不能把 transcript 扁平化成 note。主队列 **205/303 已审、98 待审**；补充 catalog net-new 177 待审；合计待审 275；人工追加 15 项中 3 项待审；计入人工后未解决 278。下一个候选 `Predator404/aiToolManager`。Claude Desktop 仍分开覆盖第三方网关 Chat、Cowork、Code 与本地/自托管 Claude Code；Anthropic 托管 Cloud 另行建模。研究未完成，未发完成邮件。

## 2026-11-23 GitHub 深审 #206：Predator404/aiToolManager

固定于 `main` commit `1d331d49ddc6e83b27fa521ace1a59ee4dd7ff2d`（2026-08-22；Node CLI/TUI v0.1.0）。它是 OMP（oh-my-pi）、Claude Code、Prime Agent 三个 Harness 的资源/config 管理器，含 `.agents` canonical Skills/Commands、原生路径 symlink mirror、MCP、扩展、Hooks 和 sidecar metadata。它的 project scope 指磁盘项目目录，不是 ChatGPT Project/Section；没有会话/消息/转录/附件/token/schedule 的导入导出模型，未支持 ChatGPT、Codex 或 Claude Desktop 3P Chat/Cowork/Code。package 标 `private: true`，无许可证字段，仓库也无 README/LICENSE 文件；不可默认复用代码。

100 个测试（10 files）及 TypeScript typecheck 通过，CLI help 只显示资源/config 分类。临时 POC 发现：启用 mirror 会删掉同名未托管真实目录；同名 Skill 导入会无确认覆盖 canonical 文件夹；提升只比 `SKILL.md`，文件相同却会丢失 global-only assets；MCP JSON 原子替换把 `.claude.json` 的 0600 改为 0644，并保留明文 synthetic bearer。POSIX 上还接受反斜杠 `..`；`path.win32` 模拟显示 Windows 目标可逃出 `.agents/skills`（未在 Windows 实机运行）。完整源码、输出及限制：`docs/research/evidence/predator404-aitoolmanager-review-2026-11-23.txt`。

结论：仅保留 per-harness 原生资源适配/sidecar 架构参考；不列为 SessionGraph 迁移器。复用写入器前需加 ownership、整棵资源树冲突比对、Windows path containment、事务备份回滚和权限保留。主队列 **206/303 已审、97 待审**；补充 net-new 177；合计待审 274；人工追加 15 项中 3 项待审；计入人工待审后未解决 277。下一候选 `pyhu26-public/agent-moringgroove`。研究未完成，未发完成邮件。


## 2026-11-23 — Candidate #207 review and SessionGraph disposition

`pyhu26-public/agent-moringgroove` at `65a43f1307a4449ab5a566822d8b3d0e4a01bc82` is a credible local **Claude Code session-resume UI**, not a migration/interchange tool. It models filesystem folder → application Agent (`id`, `sessionId`) and delegates actual transcript storage to Claude Code `~/.claude/projects`. Web chat and a PTY pane resume the same native session. Its history endpoint is only a capped 200-message screen projection; it drops non-text user blocks, command/system records, tool results, and historical parent/fork edges, and cannot load WSL transcripts from native Windows. It cannot restore a ChatGPT Project, Section Group, nested/parent-child Sessions, or a Claude Desktop third-party-gateway Chat/Cowork/Code session. Project names map to disk folders; Markdown docs are local knowledge context, not a portable conversation memory graph.

**Architecture takeaway:** keep a migration product's SessionGraph independent of target runtime UIs. A target writer may optionally create a local Claude Code folder/agent plus a resumable native session, but must store the canonical source IDs, parent/branch edges, full message/event order, attachments, usage and loss report outside the target's display-history projection. Treat Chat/Cowork/Code as distinct Claude Desktop surfaces and local CLI Code as a separate runtime axis. Never claim fidelity from the same-session web/terminal resume feature.

**Safety/build caveats:** the actual temporary HTTP API test shows lexical `docs` path checks can follow a project `docs/` symlink and read/write outside the registered folder. MCP env secrets are plain in new mode-0644 `.mcp.json`; Skill delete recursively removes a same-name directory without a confirmation marker. Host/Origin and folder-root checks exist, but do not fix nested symlink paths. `npm ci` rejects the checked-in package lock; only a `--package-lock=false` install reached the 30 passing tests/build, and the real Agent SDK path is not covered by the fake-Claude E2E suite. Public GitHub metadata conflicts with README's “private” claim; package is private and no license/release/workflow was found. Do not reuse its code. Full evidence: `docs/research/evidence/pyhu26-public-agent-moringgroove-review-2026-11-23.txt`.

Inventory after this source review: 207/303 primary repositories reviewed, 96 pending; 177 supplemental net-new candidates pending; 15 manual additions with 3 pending. Next primary review: `qingyunk/skill-manager`. Scope remains ChatGPT Projects/Section Groups/Destruction Era Sessions, plus all three Claude Desktop 3P modes and local/self-hosted Claude Code as separate target axes. Research is ongoing; no completion notification has been sent.


## 2026-11-23 — Candidate #208 and current Kimi native interoperability baseline

The audited `qingyunk/skill-manager` repository is just a Kimi Code Agent Skills plugin/CLI, not Kimi's native session importer. Do not confuse Skill discovery/validation/install/disable with chat migration. Its `name: ..` acceptance plus `--force` deleted the entire temporary `KIMI_CODE_HOME`; a malicious managed-plugin `skills: ./../../../../../outside` path let `show --json` read a temp file outside the plugin root. The official Kimi plugin security model requires every path to remain within the plugin root after symlink resolution. Do not reuse its installer until it validates path segments and realpath containment and stages backups. Full pinned source and outputs: `docs/research/evidence/qingyunk-skill-manager-review-2026-11-23.txt`.

**New first-party Kimi baseline to add to the harness matrix:** Kimi Code Desktop and CLI share `$KIMI_CODE_HOME` configuration/sessions. Sessions group by working directory and have per-session `state.json` plus `agents/main/wire.jsonl` and subagent `wire.jsonl`; those wire streams support recovery/replay and record request/MCP traces. The native `/fork`, session ZIP/Markdown export, and diagnostic log default inclusion require their own fidelity and secret-review gates. Official import is currently narrowly documented for Claude Code/Codex only: one message contains a bounded/recent conversation representation and text tool notes, with full source history and original files separately preserved. The separate `/import-from-cc-codex` brings selected instructions, Skills and MCP settings. Kimi Plugin Builder can convert Claude/Codex plugin manifests, MCP registry entries, marketplaces and Skill-only repos to native Kimi plugins. These are separate resource plane and session plane features; none establishes ChatGPT Projects/Section Groups import or all-Harness semantic parity. Test exact CLI/Desktop versions, candidate counts/age caps, existing project folders, duplicate handling, attachments, child-agent streams, fork behavior and export privacy before any fidelity claims. Official documentation links and evidence freshness are recorded in the candidate evidence file.

Inventory: primary 208/303 reviewed, 95 pending; supplemental net-new 177 pending; manual 15 additions / 3 pending; research ongoing and no completion email sent. The confirmed target still includes Destruction Era ChatGPT Projects/Section Groups/session tree, Claude Desktop 3P Chat/Cowork/Code as separate modes, and local/self-hosted Claude Code; Anthropic-hosted Cloud is separately scoped.


## 2026-11-23 continuation — candidate #209 and user-confirmed Claude Desktop 3P coverage

用户对澄清问题已确认：Claude Desktop 的 **Chat、Cowork、Code 三种 mode 全部纳入**；目标是由第三方 provider/API gateway 提供推理的桌面客户端 session，而不是 Anthropic 托管 Claude Code Cloud，也不只是本地 Claude Code CLI。由于 Unified Claude 正在合并 Chat/Cowork 的 UI 入口，仍要按数据面/实际 session mode 记录，而不能将二者永久硬编码成一个 source adapter。

当前 Anthropic Help Center 官方说明进一步收窄了可移植边界：Claude Desktop on 3P 的 prompts/responses 通过配置的 provider/gateway，conversation history 保存在本机；同厂迁移向导可复制用户自己的 Claude chats/projects 和已在本机的 Cowork/Code sessions，但不复制 Cowork/Code cloud sessions。个人数据导出不含上传文件原件，也不可导入另一个个人 Claude 账号；memory、personal instructions、Skills、connectors 要分别处理。帮助中心目前明确不支持从其他 AI provider 导入 conversation history；Cowork 项目从 Chat 导入目前一次一个、非 bulk，Claude Code 目前不是 Cowork Projects 的项目目标。相关原始链接与行级研究说明见 `docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`。这证明有源头/目标内部的窄迁移路径，不证明 ChatGPT/Codex 可通过该路径恢复。

### GitHub candidate #209 — `Rafa-Innerchispa/inneros-personal-brain`

固定 `main` at `c0f899bdde77eb25b555878a44f1764861199308`。这是 Cognee-backed shared long-term memory / personal brain：三种 API models 是 `Evidence`、`BrainRequest`、`BrainResponse`，没有原始会话消息、session IDs、fork/parent graph、Project/Section relation、附件索引或 tokens/cost ledger；其 web retrieval/orchestration/local artifact 路径也不是 session import/export。23 个离线/隔离 pytest 全部通过，但两个 deprecation warnings；synthetic fake-client POC 显示 `cognee_remember`/`CogneeMemoryStore.add` 有绕过 curation 的写路径，测试 credential/macOS 文件路径可进入请求体，curator 示例仍漏掉 email、AWS-like credential 与 `/Users` 路径。PR #5 尚 open；其作者报告的 48 条 memory seed 与 5/5/live recall 不属于 pinned `main` 验证，本次未独立审计该 PR 的源码差异。结论：只留作 MemoryPlane 对照；不复用为 Nexus SessionGraph/migrator。完整记录：`docs/research/evidence/rafa-innerchispa-inneros-personal-brain-review-2026-11-23.txt`。

计数推进：primary **209/303 reviewed，94 pending**；supplemental net-new **177 pending**；manual additions **15 个、3 pending**；primary+supplemental 剩 271，含 manual 共 274 个未解决项。下一个 primary 候选：`RafaelQSantos-RQS/MyAgentControl`。Nexus Memory 仍处于研究阶段：未访问用户 ChatGPT export / 私有 session store、未写入 Claude Desktop 私有目录、未验证端到端迁移准确率；不向用户声称兼容率或完成。


## 2026-11-23 continuation — GitHub candidate #210 MyAgentControl

本轮按前次继续状态核验并修正候选身份：primary registry 中 #210 的准确仓库是 `RafaelQSantos-RQS/MyAgentControl`（前一控制元数据省略了 `-RQS`，已从机器可读候选清单解析纠正）。主分支固定提交 `92b3fd6bffcf6b2d255cd26052d1b53e190d8889`，日期 2026-08-30。项目是一个 MIT / Rust 2024 / pre-v1 的 OpenCode-compatible `.opencode/` 静态资源安装器；不是 OpenCode runtime，不调用模型 API。它维护 embedded registry 与 profile，`add/remove/status/validate/wizard/list` 命令作用于资源文件和 `.mac/manifest.json`。Registry schema v2.0.0 有 5 个配置档、248 个 entries（8 agents、19 subagents、17 commands、2 tools、1 plugin、4 Skills、194 contexts、3 configs），这些 profile 和 context 不能等同 ChatGPT Project、Section Group 或会话分支结构。

本地固定提交验证：`cargo test --locked` 120 passed（7 suites），`cargo fmt --check`、`cargo clippy -- -D warnings`、release build 均 exit 0；GitHub 该固定提交 CI 也成功。CLI 的临时 `add → status → remove` happy path 正常，`list` 实际可用，而 README Status 对 list 未实现的描述已过时。Repository 页面显示 0 stars/forks、31 commits；无 Releases、无 PRs；MIT。

安全反例比基础安装测试更重要。目标目录 `managed/config` 是指向同级 `outside` 的 symlink 时，`add config:agent-metadata --dir managed` 成功在选定树外创建文件（10,292 bytes）。另一个仅含 synthetic sentinel 的树显示：不带 `--force` 的 add 报告 1 collision，但仍把 symlink 指向的外部文件 SHA 写进 manifest；后续 remove 删除了该外部 sentinel，然后在 symlink 目录 prune 时 exit 1 (`Not a directory`)。源码位置为 unchecked `plan_files` path join / `copy_bytes` 写入 / add 对所有 planned targets 记 manifest / remove 信任 manifest 路径。详细命令输出、hash、exit codes 见 `docs/research/evidence/rafaelqsantos-rqs-myagentcontrol-review-2026-11-23.txt`。结论：仅保留 ResourcePlane 的 static registry/profile 与哈希 manifest 思路；拒绝复用其 writer/remover，除非真实路径 containment、碰撞所有权和事务回滚都修复并验证。它没有 ChatGPT/Codex Projects、Section Groups、session graph 或 Claude Desktop 3P Chat/Cowork/Code adapter。

计数推进到 primary **210/303 reviewed，93 pending**；supplemental net-new 177 pending；manual additions 15 个、3 pending；primary+supplemental 270 项，含 manual 共 273 项待解决。下一个 primary candidate 为 `ramon-sg/agent-skills`。全目标仍包含 ChatGPT/Codex 项目与 `Destruction Era` 会话树、Claude Desktop 3P Chat/Cowork/Code、独立本地/self-hosted Claude Code；候选筛选仍只是旁证，不能替代目标格式解析/恢复验证。


## 2026-11-23 continuation — candidate #211 and Agent Skills runtime contracts

固定 `ramon-sg/agent-skills` 主分支 `f0d7da8867dc9939b647d5d9c428adff77b81a18`（2026-11-21，合并 PR #11）。这是 MIT 的 5 个西班牙语 Agent Skills 内容目录，分别为 planning、narrative-summary、visual-preview、code-audit、test-audit；`skills-catalog.json` 维护依赖边，另有 per-repo editable `project.md` overlay。它是高质量 ResourcePlane 样例，不含 ChatGPT/Codex 对话 import/export、Project/Section identifiers、SessionGraph、attachments、tokens 或 MCP server；不能作为迁移工具。

本地固定检验：`npm ci` exit 0；一次在 inherited `CODEX_CI=1` 环境下的 `npm test` 因 `visual-preview` 脚本把服务切到 foreground，而测试用 `spawnSync` 等待该脚本退出，形成挂起；我中断该 run（exit 130），确认 CODEX_CI 变量触发原因并以 `rtk proxy env -u CODEX_CI npm test` 重新运行，得到 20 passed、0 failed、0 skipped。GitHub 对固定 HEAD 的最新 Actions run 通过，v0.5.0 release 于 11 月 21 日发布。初步源审核未发现本仓库自己的 target project/session importer；仅对 HTML preview server、plan checker 和其集成测试做了源审阅，不把这等同于全面审计第三方 `skills-manager`。

**新增关键边界（官方标准/平台文档核对）：** Agent Skills 标准规定 `SKILL.md` + 可选 scripts/references/assets，是内容格式；不自动规定所有 harness 的发现位置、激活语义、permission、cloud sync 或目标 API。OpenAI/Codex 项目技能为 `.agents/skills/`；Anthropic Claude Code 本地/项目技能文档为 `.claude/skills/`；Cowork/Claude 托管 cloud session 使用 Claude 帐户已启用并同步的 Skills，本机 personal `~/.claude/skills/` 不会进入这些 session。OpenAI API 还另外支持有 version id 的上传 Skill bundle，这又不是本地 `.agents/skills`。因此该 repo README 的“复制到 `.agents/skills` 就能覆盖 Claude cloud”没有被它自己的测试验证，也不符合当前公开 Anthropic 所列路径；作为通用套件可留在 Codex/OpenAI Skills adapter 后续实测，但 Desktop 3P 的 Chat/Cowork/Code 必须分别测试，不能直接推断 cloud SaaS 与 3P 客户端相同。官方对照和精确链接见 `docs/research/evidence/agent-skills-standard-runtime-paths-2026-11-23.txt`。

该 Skill pack 的 `code-audit` / `test-audit` 使用 Claude Code 特有 `context: fork`、`argument-hint`、`/slash` 和 `project.md` overlay；原始文本可以保留，但各 harness 的 invocation、side effects、external runner/manager、权限和状态效果应单列能力/损失报告。其 README install 命令引用 `@ramon-sg/skills-manager@1`，E2E 测试使用 lockfile 精确固定的 `1.1.0`；该依赖是独立产品，未在本轮做完整代码/安全审计。候选完整记录：`docs/research/evidence/ramon-sg-agent-skills-review-2026-11-23.txt`。

进度：primary **211/303 reviewed，92 pending**；supplemental net-new 177 pending；15 manual candidates 中3 pending；primary+supplemental 269项，含manual共272项待解决。下一个 primary candidate：`ricardosalcedo/agentpack`（#212）。研究仍在进行；未读取真实 ChatGPT export 或 Claude Desktop 私有 session，也未做任何恢复/迁移准确率声明。


## 2026-11-23 continuation — candidate #212, scope confirmation and next research gate

用户已确认目标不是 Anthropic 托管的 Claude Code Cloud session，而是 Claude Desktop 使用第三方 provider/API gateway 时的全部三种 surface：Chat、Cowork、Code；同时覆盖本地或自托管 Claude Code。各 mode 的存储、事件、工具权限和入口不同，必须独立 adapter/reader/writer 与独立 fidelity report。Claude Desktop 3P 的推理经配置的 provider/gateway；官方迁移指导称 history/project/memory 保存在设备本地，gateway 的模型请求/响应日志不能代表本机 permission 决策等 session event。官方 Claude-to-Claude 导入/导出只证明 Claude 自身格式的路径：设备上 session export 为未加密 ZIP，可含 sessions/projects/memory/scheduled tasks/skills/plugins，但不含 Claude Code CLI sessions；普通用户 history export 不含 project knowledge 和 chat attachment 文件内容。该路径不能证明 ChatGPT/Codex→Claude 的结构转换。另须区分 Claude Code CLI 的 gateway 模式与 Claude Desktop Code mode；在第三方 provider 配置下，CLI 的 `--cloud` sessions 不可用。

本轮固定审核 primary candidate #212 `ricardosalcedo/agentpack`，commit `07b11d6bd182c533ac5a9c7093fb594670c7759b`。它适合作为 MCP/agent dependency ResourcePlane 的声明式 manifest、lock、profile 和 capability reference；不含 Projects/Section Groups、session tree、branches/subtasks、messages、attachments/files、tokens 或 mode-specific session import/export。Claude Desktop export 实际生成 cwd 下的 `claude_desktop_config.json`，属于窄 MCP 配置输出，不是 Desktop 3P 配置部署或 session migration。

可重复质量结果：`cargo test --locked` 默认并行 exit 101（19 passed / 4 failed；测试用例争用进程全局 working directory）；README 推荐的串行 `cargo test --locked -- --test-threads=1` exit 0（23 passed）。Rust fmt、Clippy `-D warnings`、release build 均成功。隔离 POC 已确认 `import --command` 的原始字符串插值可执行注入 JavaScript；`fetch ..` 可写入并覆盖临时项目的 `packages/../agentpack.json`。POC 仅触及临时目录、synthetic manifest 与 fake local MCP SDK。将 importer 与 fetch writer 视作安全 blocker，除非上游修复并新增回归测试；其余的 dependency manifest ideas 仅作为架构参考。完整审计证据见 `docs/research/evidence/ricardosalcedo-agentpack-review-2026-11-23.txt`。

计数推进到 primary **212/303 reviewed，91 pending**；supplemental net-new **177 pending**；manual additions **15 项、3 pending**；primary+supplemental 待审核 268 项，含 manual 共271项。下一项 primary candidate `roedyrustam/ctxbridge`（#213）。研究仍未完成；没有访问真实 ChatGPT archive、Claude 私有会话数据库、账号或真实 API key。


## 2026-11-23 continuation — candidate #213, cross-agent memory bridge

固定 primary candidate `roedyrustam/ctxbridge` 的 `main` commit `9c03ce2da94ac38eaec2beef964d16e0c3cbf534`。它是 MIT、local-first 的 memory + MCP 工具：SQLite project/global memory、instruction files adapters、JSONL、handoff capsules。作为 Nexus Memory 的 **MemoryPlane/ResourcePlane 参考**有价值，但 project scope 只是 repo directory；没有 ChatGPT/Codex 的 Project/Section Group ID、Session graph、消息/工具事件、分支、子任务、附件、token usage、恢复 ID 或 mode-specific Cloud/Desktop import/export。Claude 的目标仍按用户确认覆盖 Claude Desktop 3P 的 Chat、Cowork、Code，以及本地/自托管 Claude Code，不能把本 repo 的 `CLAUDE.md` 文件同步误当成覆盖 Chat/Cowork/Code 的 Session adapter。

本地 release binary 的合成 JSONL 导入验证：传入指定 ID、创建/更新时间、hash 与 token estimate 后，文本、scope、kind、title、source_agent、priority、tags 保留；ID 被重建，timestamps 变成导入时刻，hash 与 token estimate 重算。`export_jsonl` 仅选择 `memories` 表，不导出 `capsules` / `capsule_items`。因此它的 memory interchange 适合作为 baseline，不是 provenance-preserving import。另有 symlink safety boundary：`AGENTS.md` 在 temp project 内链接到外部 sentinel 时，`ctxbridge sync` exit 0 并把 managed markers 写到了外部文件；需为 Nexus writer 增加 realpath containment、symlink 明确拒绝/交互授权、原子多文件提交及 rollback。此次所有文件都在 `/tmp/nm-ctxbridge-followup213-poc/`，未改用户文件。

质量：`cargo test --locked` exit 0，19 tests / 7 suites；fmt、clippy `-D warnings`、release build exit 0。`cargo audit` 提示 `libsqlite3-sys v0.30.1` + bundled SQLite CVE-2026-119375（RustSec 6.8 medium，需打开不可信 crafted DB/WAL pair；修复版本 `libsqlite3-sys >=0.39.0`）和 unmaintained `chrono`。这是可验证依赖风险，不等于已远程利用；在导入任意第三方本机存储时必须作为 gate。`rtk cargo audit --locked` 误用了不支持的参数，exit 2；改为 `rtk cargo audit` 执行扫描，exit 1 并报告上述 advisories。

GitHub 页面：0 stars/forks，5 commits，MIT；latest release v0.2.0；CI#3 与 Release#1 成功，Metadata run #2 失败；无 open issues / PRs。完整代码路径、测试、POC 输出、上游链接和 advisory 原文见 `docs/research/evidence/roedyrustam-ctxbridge-review-2026-11-23.txt`。

primary 计数更新为 **213/303 reviewed，90 pending**；supplemental net-new 177 pending；manual additions 15 项、3 pending；primary+supplemental 267 pending，含 manual 共270。下一候选 `Saber5656/skillet` (#214)。这一阶段没有处理任何真实 ChatGPT export、Claude Desktop 私有数据、provider API key 或真实项目文件。


## 2026-11-23 continuation — candidate #214, Skill manager design-only

本轮审核 `Saber5656/skillet` 的固定 `main` commit `4d42851c5281a5604e32befb16fa8dfadd584d94`。它是一份完整度很高的 Agent Skills package-manager **设计**，不是可安装/可运行产品：主仓库只有 README 与 docs，没有源代码、tests、`package.json`/lock、CI workflows、release 或 LICENSE。GitHub 目前显示 40 个 open issues 与 0 个 workflow runs/releases；本地逐项检查有 40 个 issue drafts，209 个 acceptance checkbox 全未勾选。故不能把里面设计的 pinning、SHA-256、consent、safe staging、copy-only writes、receipt-based rollback 当成已验证安全行为，也不能推断可合法复用代码。

规划范围是 Claude Code 与 Codex 的本地 Skill 文件包：`SKILL.md`、版本索引、lockfile、目录物化和缓存。没有项目/Section/Session identity、主从会话关系、tool events、历史/文件附件/ token accounting/ scheduling 等模型；对 Claude plugins、MCP servers、agent configs 也明确 Out of Scope。因此它最多作为 Nexus Memory ResourcePlane 的设计审查清单，不是用户要求的 Session/Project transfer tool。

新的兼容性风险：Skillet 文档将 Codex skill 路径定为 `.codex/skills/`/`~/.codex/skills/`；当前官方 OpenAI CLI 安装参考的 Codex 表格却列 `.agents/skills/`/`~/.agents/skills/`，另一个 OpenAI 官方 Codex skills 示例又出现 `.codex/skills/`。Agent Skills 标准只定义 `SKILL.md` 及 payload 结构，不统一本地路径、插件包路径、Cloud discovery 或权限/调用语义。需要按 Codex host/version 建立 profile，并以干净环境的安装/发现 smoke test 解决差异，不接受文档互抄作为兼容性证据。

Skillet 计划里的安全设计本身有借鉴价值：Git `ls-tree` 枚举，不解压 tar；symlink/gitlink/traversal/path collisions/超限拒绝；不执行技能代码；首次显式同意；复制安装并记录 receipts；仅允许有 receipt 的目录被覆盖/删除；hash drift 可检测；security suite 与 e2e 检查都列为门禁。但由于本项目还没有实现/测试，这些是规范性意图，而非已证明行为。它也把指数/包签名、prompt-injection scanning 等延后，且其 prior-art 摘要只回顾少量项目（日期 2026-07-07），不足以满足本项目要求的广泛市场调研；该文的“none provide”应视为作者假设，待和本研究 corpus 核验。

证据：`docs/research/evidence/saber5656-skillet-review-2026-11-23.txt`; 官方路径补充：`docs/research/evidence/agent-skills-standard-runtime-paths-2026-11-23.txt`。primary **214/303 reviewed，89 pending**；supplemental net-new 177 pending；manual additions 15 个、3 pending；primary+supplemental 266 pending，含 manual 共269。下一候选 `saturnarians/ctx-manager` (#215)。用户目标仍覆盖 Claude Desktop 3P 的 Chat、Cowork、Code 和本地/自托管 Claude Code，未运行任何真实迁移。

## 2026-11-23 continuation — candidate #215 and scope reaffirmation

The user reconfirmed the destination scope: local/self-hosted Claude Code and the Claude Desktop client on a third-party inference provider/API gateway, with **Chat, Cowork, and Code all in scope**. This reiterates the current architecture; it does not include Anthropic-hosted Claude Code Cloud. Desktop version, OS and gateway still need to be pinned before any target write or native-resume claim. Preserve each Desktop mode as a separate adapter/data profile.

Candidate #215 `saturnarians/ctx-manager`, pinned `0112b8c94cd5020fd64a8bc638499f66f4fddc28` (MIT), is a local Markdown slicer + MCP/CLI phase ledger, not a Project/Section/session migrator. On isolated synthetic fixtures it passed 21 tests under CPython 3.14.3 and 3.12.4 and built 0.2.0. Source review plus actual MCP stdio probes showed caller-controlled Docs path escape, project config ledger path escape, MCP/CLI phase mismatch, “Verified” based only on dirty file count, and a forced concurrent lost-update race. PyPI 0.2.0 predates the same-version upstream phase fix; dependency audit found 25 advisory records, with transport-specific reachability unproven for the stdio path. Retain only the context-ledger concept, pending strong containment/concurrency/claim verification; do not reuse the writer.

Candidate evidence: `docs/research/evidence/saturnarians-ctx-manager-review-2026-11-23.txt`. Primary count **215/303 reviewed, 88 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**. Primary+supplemental pending **265**, plus pending manual **268**. Next primary candidate: `sefas-labs/ai-skills-manager` (#216), cloned at `95fad6764918a639b52c9cc1ef810f27cf5b7d12` on `main`; source review is the next gate. No real user export, API key, account or private Desktop store was accessed. Research remains active/incomplete; no completion notification sent.

## 2026-11-23 continuation — candidate #216 `sefas-labs/ai-skills-manager`

Candidate #216 is pinned at `main` commit `95fad6764918a639b52c9cc1ef810f27cf5b7d12` (MIT). It is a robust-looking VS Code/Cursor Skill inventory and install/update extension with four provider path adapters: Claude Code, Cursor, Codex and Copilot. Local tests (57/57), typecheck, build and smoke pass after a scripts-disabled dependency install. Source supplies useful ResourcePlane patterns—path validation, exact commit/tree provenance, bounded staging, consent, non-executable writes, diff, backup and rollback. `npm audit` reports 7 affected dev/publishing package records (2 high, 5 moderate), while the production-only audit is clean; no lockfile fixes were applied.

This candidate does not model ChatGPT/Codex Projects, Section Groups, session ancestry, branches, subtasks, media, tools, token usage, schedules, MCP/plugins or any conversation restore/resume. Its Claude support is Claude Code Skills directories; it has no Claude Desktop 3P Chat/Cowork/Code session adapter. Keep it as a ResourcePlane reference only, not the requested migrator. Live editor E2E was not re-run because its script inspects real home Skills and live GitHub; upstream docs also note manual modal coverage remains incomplete. GitHub showed 1 open PR / no issues or releases; the PR CI failure is attributed to hosted runner capacity/internal GitHub error, not a source-test failure. Review: `docs/research/evidence/sefas-labs-ai-skills-manager-review-2026-11-23.txt`.

Primary inventory **216/303 reviewed, 87 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**. Primary+supplemental pending **264**, including manual pending **267**. Next primary candidate: `shqear93/mcp-manager` (#217). The user-confirmed target remains Claude Desktop 3P Chat/Cowork/Code plus local/self-hosted Claude Code; no real user data or provider was accessed. Research remains active/incomplete; no completion email sent.

## 2026-11-23 continuation — candidate #217 `shqear93/mcp-manager`

Pinned main `8f077dd615d74e4b29eba0e4b5ab47f48acdd9be` (MIT, Node 0.1.0). A small CLI registers MCP definitions and projects them into config files; it is not a SessionGraph, Project/Section, transcript, attachment, token, schedule or resume importer. No test script/tests beyond fixtures, no release/workflow/PR/issues; local syntax check and CLI help smoke pass.

**Reject its current writers.** Temp-only adversarial probes proved registry `name` traversal can write outside the configured registry and replace a sentinel; `remove` can recursively delete an outside registry path; same-name replacement deletes existing registry data without backup/consent; `--copy` has the same delete-first behavior. Project registry mode still writes into the user's global agent config. A synthetic API key was persisted in cleartext to a mode-0644 config. A remote HTTP URL disappeared from the generated agent config. `experimental_restore` only lists missing paths. Current official paths show the Claude/Cursor/Kimi/Cline adapters are wrong or stale; Aider native MCP config is unverified/not supported by the official Aider CLI. Codex's basic config path is the only obvious partial match.

Full evidence and POCs: `docs/research/evidence/shqear93-mcp-manager-review-2026-11-23.txt`. Primary count **217/303 reviewed, 86 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**; primary+supplemental pending **263**, including manual pending **266**. Next primary candidate: `simonwu53/agent-skills` (#218). User's scope remains Claude Desktop 3P Chat/Cowork/Code plus local/self-hosted Claude Code. No real user config or session was read. Research remains active/incomplete; no completion notification sent.


## 2026-11-23 continuation — candidate #218 `simonwu53/agent-skills` and scope reconfirmation

The user again selected all three Claude Desktop on 3P modes—**Chat, Cowork, Code**—and local/self-hosted Claude Code. This scope excludes Anthropic-hosted Claude Code Cloud. The current official overview/feature matrix says Desktop 3P routes inference to a configured provider but stores conversation history on device and has no Anthropic-cloud sessions. The local-data map separates Chat/Cowork session state/workdirs from Code session metadata and Claude Code transcript files. Unified Claude can merge Chat/Cowork UI while Code stays separate. Desktop app-managed Skills/marketplaces and Code filesystem Skills are also separate delivery paths. Keep three distinct mode profiles and one CLI profile; no live target data was opened.

Pinned `simonwu53/agent-skills` main `0a7e4569fab0f40011b74a6a4e7781aecc3a1ae4`. This is a Shell/Bash Skill-library manager (source Git repos/local folders/ZIP, categories, pins, copy/symlink installs and submodule refresh), not a Project/Section/session importer. It has one generic `~/.claude/skills`/`.claude/skills` adapter and no ChatGPT/Codex source-session graph, messages, branches, attachments, token/cost/memory/schedule/MCP/plugin migration, native restore or resume. Offline smoke is 47/47; GitHub has v3.0.1 but no configured workflow. A synthetic `--skill ../../../../../outside` probe escaped its cloned repository and later copied an outside `/tmp` SKILL.md into a scratch project target. Its default target clear and `--update` overwrite lack a rollback receipt. Keep only as a low-priority ResourcePlane reference; reject its path/overwrite behavior for a Nexus writer. Full evidence: `docs/research/evidence/simonwu53-agent-skills-review-2026-11-23.txt`.

Primary inventory: **218/303 reviewed, 85 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**. Primary + supplemental pending **262**, including manual pending **265**. Next primary candidate: `sjmgarnier/skill-manager` (#219). Research remains active/incomplete; no user session, account, credential, or Desktop profile was accessed; no completion email sent.


## 2026-11-23 continuation — candidate #219 `sjmgarnier/skill-manager`

The user-confirmed target remains Claude Desktop on a third-party inference provider/API gateway, all three modes **Chat, Cowork, Code**, plus local/self-hosted Claude Code. Current official Claude Help Center docs now explicitly describe account-level Skills/Plugins available in Chat, Cowork and Code when signed into the same Claude account, while Desktop 3P separately documents device-local and org-managed extensions. Treat account-backed sharing as conditional on identity/configuration; it is not proof every API-key/gateway deployment syncs those objects. Store account/local/org provenance and per-mode discovery separately.

Pinned `sjmgarnier/skill-manager` main `7ab49b0735a6a50082222cb1b93b5ba13ba7d8f9`. It is an AI-invoked Agent Skill that orchestrates `gh skill` / `npx skills` installs and writes a repo-keyed registry. It has no ChatGPT/Codex Projects, Section Groups, SessionGraph, messages, branches, attachments, token/cost, MCP/plugin auth history, schedules or resume IDs. 23 Bats tests are declared but the runner was absent; Bash syntax and isolated registry/update checks passed. A synthetic detector fixture at official Codex user Skill path `~/.agents/skills/...` returned `warp`, while its own path table lists Codex as `~/.codex/skills`. Current OpenAI CLI docs specify Codex `~/.agents/skills`; the user-confirmation prompt avoids an unconditional wrong write but this breaks unattended platform detection. A 32-writer `/tmp` stress test did not reproduce registry row loss. Keep as a low-priority Skill ResourcePlane reference, not a migrator. Full source, tests and outputs: `docs/research/evidence/sjmgarnier-skill-manager-review-2026-11-23.txt`.

Primary inventory: **219/303 reviewed, 84 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**. Primary+supplemental pending **261**, including manual pending **264**. Next primary candidate: `stevengonsalvez/reflect-kb` (#220). No private user data, account or gateway credential was read; research remains active/incomplete and no completion email sent.


## 2026-11-23 continuation — candidate #220 `stevengonsalvez/reflect-kb`

Pinned `main` `d3375adb9fb403c4f8c657ca5001322d13fd0826` is the owner-archived (May 18, 2026) source-removal commit. The checkout retains only README, docs, MIT license and CI workflow; it has no package source, tests or runnable CLI. README directs users to a different monorepo, which was not opened during this bound-object review. The remaining `docs/usage.md` describes a Markdown learning KB with content-hash note IDs, entity sidecars, GraphRAG/QMD index and search. It is useful as a derived MemoryPlane design reference, not a full session archive or migration adapter.

The custom default store `~/.claude/global-learnings/` differs from current Claude Code native Auto Memory under `~/.claude/projects/<project>/memory/` and from resume-capable transcript JSONL at `~/.claude/projects/<project>/<session-id>.jsonl`. Auto Memory is per repository and machine-local; it is not shared across machines/cloud. Reflect KB has no project/section/session/message provenance, parent/fork graph, interruption lineage, attachments, tokens/cost or resume IDs. It also has a docs-only path discrepancy (`~/.learnings/` vs `~/.claude/global-learnings/`). Keep SessionGraph immutable and attach any future derived memories to source event IDs. Official source comparison and scope consequence: `docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`; complete candidate note: `docs/research/evidence/stevengonsalvez-reflect-kb-review-2026-11-23.txt`.

GitHub reports MIT, 22 commits, 0 stars/forks, 0 issues, one open Renovate PR, no release, and 16 workflow runs. The archive/removal CI run was cancelled; earlier source-commit CI runs shown failed. Current archived tree still has a CI workflow expecting `pip install -e .[dev]` and tests, but no package manifest/source remains. No code test or runtime migration was claimed.

Primary inventory: **220/303 reviewed, 83 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**. Primary+supplemental pending **260**, including manual pending **263**. Next primary candidate: `summer-via/skill-package-manager` (#221). Target scope remains Desktop 3P Chat/Cowork/Code plus local/self-hosted Claude Code. Research remains active/incomplete; no user data or credential was accessed.


## 2026-11-24 scope confirmation and current evidence delta

The user confirmed Claude Desktop on a third-party inference provider/API gateway must cover Chat, Cowork, and Code, in addition to local/self-hosted Claude Code. Keep a separate mode adapter for each; a common API credential does not collapse their local history stores into one session type. Current official Anthropic migration materials say Desktop on 3P may route inference through a customer LLM gateway and locally stores work; its built-in importer is Claude-origin-only, has mode- and locality-dependent coverage, and is not a ChatGPT/Codex importer. Imported project knowledge/file bytes, memory, instructions, Skills, connectors, cloud Cowork/Code sessions and several other records require separate handling. Preserve source payloads/events and validate per-mode target discovery/resume, including app version/OS and provider identity. No live target or user session was read.

Candidate #221 summer-via/skill-package-manager passed its TypeScript build but has no test suite and is not a session migrator. Disposable fixtures reproduced path-traversal deletion and destructive overwrite of an unmanaged Skill directory; reject current writers and keep only ResourcePlane package-ref terminology. Evidence: docs/research/evidence/summer-via-skill-package-manager-review-2026-11-24.txt.

Primary inventory: 221/303 reviewed, 82 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Next candidate: sunven/skills-box (#222). The plan remains research-first and active/incomplete.


## 2026-11-24 continuation — candidate #222 fit and disposition

All three Claude Desktop 3P modes remain in scope, plus local/self-hosted Claude Code. sunven/skills-box is a useful adjacent ResourcePlane/UI study: it provides global and locally registered project Skill scopes, agent discovery, CLI previews, backups, a native plugin manager for Claude/Codex CLIs, and 79 coding-agent definitions. It does not parse or write ChatGPT/Codex Project/Section/session hierarchies, event transcripts, attachments, token/cost, memories, schedules, MCP history or target resume identifiers. Its project concept is a local path; its “session” is operation lifecycle state, not AI dialogue. Do not use this candidate to claim any migration fidelity.

At pinned HEAD 9ab4b1e15ba99fb7297423266d4b409dc4f931ce, frontend tests/build and Rust tests pass on repeat with one earlier transient Rust failure preserved. Production JS audit is clean via the official registry; dev dependencies and Cargo lockfile have advisories. No license is declared; release assets are only macOS Apple Silicon. Disposition: keep design/reference patterns only and do not reuse source code. Full review: docs/research/evidence/sunven-skills-box-review-2026-11-24.txt.

Primary count 222/303 reviewed, 81 pending; supplemental pending 177; manual additions 15 total / 3 pending. Next candidate: suqiangqiang2012-dot/agent-skill-manager (#223). Research remains active/incomplete; no real user session or credential was accessed.


## 2026-11-24 continuation — candidate #223 fit and disposition

The candidate supplies a useful Skill ResourcePlane/release lifecycle: stable published versions, typed Agent/OS targets, package integrity hashes, strict ZIP checks, explicit per-skill approvals, staged install, retained backup, rollback, and independently authorized release Draft/publish/catalog operations. It does not model ChatGPT/Codex Projects, Section Groups, sessions, event trees, attachments, tool calls, tokens, MCP/plugins, memory, scheduled work or destination resume IDs. Do not treat a versioned Skill package as a session archive.

Its declared adapter set is only Codex Windows/macOS plus WorkBuddy Windows. Its default Codex path is CODEX_HOME/skills or ~/.codex/skills, while current official OpenAI documentation lists .agents/skills and ~/.agents/skills. A temp-only path probe reproduced the difference. The explicit root option exists, but native discovery compatibility still needs a host test. The published v0.3.0 package has limited scope and the source is unlicensed; keep patterns only, do not reuse code. Full review: docs/research/evidence/suqiangqiang2012-dot-agent-skill-manager-review-2026-11-24.txt.

Primary count 223/303 reviewed, 80 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Next candidate: theonepichael/agent-toolkit (#224). Research remains active/incomplete.


## 2026-11-24 continuation — user scope confirmation and candidate #224

The user reconfirmed that Claude Desktop configured for a third-party inference provider/API gateway includes **all three modes: Chat, Cowork and Code**, as well as local/self-hosted Claude Code. Current official Anthropic documentation now calls the Desktop deployment `Claude Desktop on 3P`, names compatible LLM gateways, says the app stores conversation content on-device, and documents a separate Desktop provider-configuration path from the Claude Code CLI environment (`ANTHROPIC_BASE_URL`/`settings.json`). This confirms the requested target as a real supported product path, but does not merge the modes' native stores. Keep `desktop-chat`, `desktop-cowork`, `desktop-code`, and `claude-code-cli` as separate versioned profiles and test each independently. Sources/limits: `docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`.

Primary candidate #224 `theonepichael/agent-toolkit` is MIT, pinned to `main` commit `5daf67975c8ffac3241b49341edbc76f3350820f`. It is a strong adjacent multi-harness workflow kit; its six local transcript readers provide useful text, usage/cost, timestamp, cwd, and query patterns. They normalize to lossy `SessionRecord` rows, omit raw event identity, tool/result/permission payloads, attachments and actual parent/fork edges, and have no reviewed Project/Section/session migration writer or native target resume. Keep as SessionObservability parser prior art only, not a migrator or canonical interchange schema.

Validation from the pinned checkout: `test_analyze_sessions.py` 135 passed; `test_worker_invariant_audit.py` 45 passed; `test_worker_run_metrics.py` 24 passed; `test_herdr_queue_runner.py` ran 130 and had two failures plus one error caused by this macOS host resolving `/tmp` as `/private/tmp`, where tests compare literal paths. The source uses `Path.resolve`; an explicit check returned `/private/tmp`. The configured CI is Ubuntu-only. Full `uv run pytest` was not run because uv/pytest was unavailable; do not describe this as a complete green suite. Full review: `docs/research/evidence/theonepichael-agent-toolkit-review-2026-11-24.txt`.

Primary count **224/303 reviewed, 79 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**. Primary+supplemental pending **256**, including manual pending **259**. Next primary candidate: `timianmalloo/x-harness-x-model-bench` (#225). No real user export, desktop profile, credential or private session was accessed; research remains active/incomplete and no completion notice was sent.


## 2026-11-24 continuation — Claude Desktop scope retained; candidate #225

The user-confirmed target remains Claude Desktop on a configured third-party provider/API gateway across Chat, Cowork and Code, plus local/self-hosted Claude Code. Keep each as a separate versioned profile. Candidate #225 `timianmalloo/x-harness-x-model-bench` is an Apache-2.0 benchmark pinned at `main`/`origin/main` commit `560d2fae9eaebb6450ab33b752df6ca288b5de6e`.

This candidate is not a session migrator, but is high-value adjacent prior art: per-harness native readers produce measured model/tool/error/usage/reasoning/prompt/harness-event projections, and the benchmark uses a hash-chained ledger plus SHA-256-verified cell archives. The normalized `Extraction` intentionally omits complete conversation messages, media bytes, Projects/Section membership, actual parent/fork/subtask relations and target resume handles. Its `resume.py` recovers benchmark runs and cells, not native harness conversations. CLI `--help` exposes no conversation import/export/restore. Retain the reader/archive patterns; never use the projection as Nexus's canonical archive.

Local focused tests in a disposable Python 3.12 environment: reader/telemetry group 187 passed, 1 failed; archive/resume/view group 331 passed, 1 skipped. Exact total 518 passed, 1 failed, 1 skipped. The failure is `test_grok_served_model.py::test_observed_layout_is_found_by_tree`: macOS path normalizers do not equate a Windows backslash key with its forward-slash `--tree` form; observed exit 2 `not recorded: no session store for this tree`. The pinned CI defines Windows, macOS and Ubuntu jobs, but the Actions page's latest visible run is #163 from 2026-10-04, before the pinned commit dated 2026-10-19, so a green hosted result for this revision was not established. Full source/test/fit evidence: `docs/research/evidence/timianmalloo-x-harness-x-model-bench-review-2026-11-24.txt`.

Primary inventory **225/303 reviewed, 78 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**. Primary+supplemental pending **255**, including manual pending **258**. Next primary candidate: `toshon-jennings/agent-advisor` (#226). No real user export, app session, provider key or private profile was accessed; research remains active/incomplete.

## 2026-11-24 continuation — candidate #226 and current Claude Desktop 3P topology

The user confirmed the Claude Desktop third-party inference provider/API gateway target includes Chat, Cowork and Code, plus local/self-hosted Claude Code. Current Anthropic documentation describes the supported Desktop-on-3P deployment: the configured customer provider/gateway processes inference while the Desktop app stores conversation state locally. This is not an Anthropic-hosted Claude Code Cloud session and not a standalone CLI configured only through ANTHROPIC_BASE_URL.

As checked against current primary sources, Chat and Cowork share a local state family under local-agent-mode-sessions/: session state + working directory; uploads, outputs and audit.jsonl; project-scoped memory under spaces/<projectId>/memory/. The audit contains prompts/responses/tool I/O, returned thinking, permission decisions, model and usage metadata, but is unencrypted and does not establish completeness. Code's Desktop session metadata lives in claude-code-sessions/, but its native conversation transcript is in the Claude Code store at ~/.claude/projects/. ~/.claude/ and ~/.claude.json contain Skills/plugins/hooks/permissions/MCP setup shared with Code and standalone Claude Code CLI. Cowork VM state, ~/Claude/ artifacts/project files, schedules, connector credentials, trusted working folders and SSH remote copies are companion resources with their own portability/identity limits. Therefore implement and validate distinct claude-desktop-chat, claude-desktop-cowork, claude-desktop-code, and claude-code-cli profiles, record actual provider/auth mode and OS/app build, and test each destination's discovery, attachments, project linkage, schedule behavior and native resume. The vendor's Claude-origin import/copy is not a ChatGPT/Codex source adapter.

Candidate #226, toshon-jennings/agent-advisor, is a selective routing and plugin/config synchronization hub for Codex, Claude Code and Antigravity, pinned at main 02d8c757f04e00a3d8f9da51507ba9a23b9b350f. It contains no ChatGPT/Codex Project/Section/session/event import/export or destination resume writer. Its large manifest-driven spoke-sync script has useful ResourcePlane safety patterns (destination identity, path/symlink/dirty/ignored-file checks, preflight/revalidation, target validators, post-write drift comparison and scoped compensation), but acknowledges a TOCTOU window and can produce mixed results after writes begin: rollback is per spoke, not a global transaction. No tests/ directory exists; latest visible hosted validator workflow #16 passed, and local shell syntax/help passed. Do not claim a full behavioral suite or run against live spoke repos. Full review: docs/research/evidence/toshon-jennings-agent-advisor-review-2026-11-24.txt.

Primary corpus 226/303 reviewed, 77 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 254, including manual pending 257. Next primary candidate: weixuanteo/skills-manager (#227). Research remains active/incomplete; no private user export/store, app profile, session or key was accessed.

## 2026-11-24 continuation — candidate #227 weixuanteo/skills-manager

The pinned repository 3aa4419870ca2a73fc90aea919042d606736ea9c is an unlicensed local web application for managing SKILL.md folders, not a Nexus Memory session migrator. It scans conventional Skills directories for Claude Code, Codex, Cursor, Gemini CLI, Copilot, Windsurf, Kiro, OpenCode, Amp, Goose, Cline, Roo Code and a universal .agents/skills resource; it also discovers Skill directories inside Claude Code plugin installs. It models filesystem path/frontmatter/content, installing agent and scope, symlink groups, install method and provenance, version/update state and command log. Project roots are local directories, not ChatGPT/Codex Projects, Sections or conversation hierarchy.

What Nexus can learn: show exact planned and completed asset operations; preserve upstream identity and observed commit/version; deduplicate symlinked Skill replicas without pretending they are independent; separate global and workspace-local scope; require explicit per-target confirmation; persist command output and status. Boundaries: no MCP/Plugins-as-whole, memories, schedules, sessions, messages, images, tool logs, Section Groups, parent/fork/child relations or native resume. The tool previews at a SHA and checks the remote ref again before calling the skills CLI, but the invocation still names the ref rather than immutable SHA; a ref move after that check can change fetched bytes. Do not claim preview-to-install integrity is race-free.

Tests and quality from the disposable pinned checkout: using exact pnpm 12.3.4, install with frozen lockfile and scripts disabled passed the package manager's supply-chain policy check (273 entries), 184 packages installed to temporary store, and 35/35 Node tests passed. TypeScript/Vite build passed with 2,372 modules and a nonfatal 782.38 kB bundle warning. A temp HOME/project API smoke scanned four fixtures (global universal, global Claude, project Codex, project Claude) and returned the expected names/scopes; path traversal and arbitrary command posts returned 400, a cross-origin post returned 403. App was bound to 127.0.0.1, all fixtures/config lived under /tmp, and the process was stopped afterward.

Caveats: no .github workflows, releases, or LICENSE; GitHub showed 0 stars/forks and 14 commits. A production audit against registry.npmjs.org returned 9 advisories (8 moderate, 1 low) for locked Hono 4.13.7 and @hono/node-server 2.1.1. Several reviewed advisories affect request-path or wildcard middleware handling; the project uses app.use('/api/*') for its local command endpoints. This is a package-level security finding, not an exploit demonstrated against the app. The configured npmmirror audit endpoint initially failed; the official registry retry produced the result. Full source/test/audit evidence: docs/research/evidence/weixuanteo-skills-manager-review-2026-11-24.txt.

Disposition: keep only adjacent ResourcePlane discovery/provenance/confirmation UI patterns; do not reuse unlicensed code or classify it as a migrator. Primary inventory 227/303 reviewed, 76 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 253, including manual pending 256. Next candidate: WoodSettler/CyberGuild (#228). Research remains active/incomplete; no private session, credential or installed Skill was accessed.

## 2026-11-24 continuation — confirmed Desktop scope, candidate #228, and DSH state model

The user answered the open scope question: include **all Claude Desktop third-party-provider/API-gateway modes—Chat, Cowork, and Code**. Local or self-hosted Claude Code remains a separate target; Anthropic-hosted Claude Code Cloud is not added. Keep four versioned profiles (`claude-desktop-chat`, `claude-desktop-cowork`, `claude-desktop-code`, `claude-code-cli`) and record Desktop build, OS, provider/auth topology, data roots, and live native discovery/resume per profile.

Candidate #228 `WoodSettler/CyberGuild` is pinned at `main`/`origin/main` `a199c207087e99217cae2d456fa4b915b10e8fba` (2026-10-21). It is an explicit appointment Skill and manual QuestBoard for Claude Code, Codex and DSH. Package checker passed completeness/internal references only; README says native discovery and live-session behavior are unverified. Windows-only DSH junction links the shared global Skill into `~/.dsh/skills`; it does not integrate project DSH Skill roots, Workspace registry, Session storage, or resumption. No license/release/CI; retain opt-in/minimal context only and reuse no code. Details: `docs/research/evidence/woodsettler-cyberguild-review-2026-11-24.txt`.

Official DSH docs at observed remote HEAD `4b399c39a6d1479cd84ca591b4d7c88e24d38a96` document an optional **flat, host-side Workspace registry** (canonical directory, stable ID/title, ordered Session membership) validated against each SessionHeader.cwd, not an event-log field or nested Section Group tree. Removing the Workspace registration does not delete its folder or Session log; archive/hide and ungrouped state are distinct. A Session itself is an append-only typed event log from which model messages are derived. Durable distinctions include turn/step order, streamed assistant output and usage, failed/retried/cancelled attempts, tool args/results/errors, interruption, request context and plugin records. Header records ID/version/time/cwd and selected lineage/composition fields; inherited fork prefix length is exact and paired with the log. Ordinary forks need not set `parentSession`; that field names a subagent creator, with `origin: subagent` separately classifying the child. Preserve `fork-prefix`, `subagent-parent`, `workspace-membership`, and sequential/user-follow-up as different typed edges.

DSH persistence is per-Session versioned JSONL (checksummed Zstandard frames by default, raw lines configurable); header stays separate, per-session handles serialize writers, `flush` is durability barrier, and crash repair preserves committed events while closing incomplete turns. Skills are discovered through distinct project `.dsh/skills` / `.agents/skills` and user `$DSH_HOME/skills` / `.agents/skills` roots and loaded on demand. Host Schedule records persist separately and can target existing/new Sessions; delivery receipt means inbox write, not model completion, and historical schedule-like Session events do not auto-create an active task. Non-session Storage is another plane. Keep Skills, MCP/plugins, schedule, attachments/media, outputs, credentials and memory as independent resources with dependency/provenance links. DSH attachment/config/plugin layouts and real imported-session usability remain an explicit source/test work item.

This is official documentation/source-contract review, not a live DSH install or session restore. See `docs/research/evidence/deepseek-harness-session-project-profile-2026-11-24.txt`; this turn's Desktop scope answer is also appended to the Claude Desktop scope evidence.

Primary inventory **228/303 reviewed, 75 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**; primary+supplemental pending **252**, including manual pending **255**. Next primary candidate: `xdlkc/SkillHub` (#229). No private Session, provider credential, Desktop profile, or export was accessed; research remains active/incomplete.

## 2026-11-24 continuation — candidate #229 xdlkc/SkillHub

The current user-confirmed destination remains Claude Desktop using a third-party provider/API gateway in three distinct modes—Chat, Cowork and Code—plus local/self-hosted Claude Code as another adapter. Candidate #229 does not address that transfer problem.

Pinned `xdlkc/SkillHub` main/origin-main `a5e955012307b59ba47a49f6366d45c662b04f77`, commit date 2026-11-17. GitHub page snapshot: 44 commits, 0 stars/forks, no release, no license or CI. The app is a local Skill repo catalog and static-path copier: it offers metadata, shallow clones, skill scanning, install/update/diff to 73 global agent IDs, and optional metadata-only Git sync. The `skills.json` file contains 115 metadata rows and cloned flags, not pinned SKILL content, source Project/Section trees, conversation archives, session branches/edits, output/media, token/cost, MCP/plugin configuration, schedules, memory, or target continuation. Its repository clone marker downloads current branch state, so a sync does not make Skill bytes reproducible across machines. It models no project-local roots and does not implement Claude Desktop 3P Chat/Cowork/Code stores.

Source-level review and isolated disposable runtime probes materially downgraded its fit. The server omits the listen host and was observed on `*:18787`; it returns wildcard CORS for read and mutation methods and has no auth. A synthetic cross-origin JSON creation returned 201. A cloned SKILL.md symlink to a synthetic file outside the clone root bypassed the lexical traversal check and was returned by the content API (direct `../` returned 400). Two valid repos `a-b/c` and `a/b-c` collided at `a-b-c`. Copy-update reports deleted source files but leaves those files in the destination; there is no staged replacement/rollback. These findings were demonstrated only with `/tmp` data, not user data or a real hostile network origin. Therefore reject for use against real agent profiles until local-only binding, auth/origin checks, canonical symlink containment, collision-free origin-bound clone identities, and atomic write/rollback are implemented.

The adjacent positive pattern is separation of shared repo metadata from machine-local clone paths; the implementation also has strong tests around metadata-only Git commit safety. But there is no license for source reuse. The current suite passed 27 Vitest and 43 Node tests, and production build passed; tests do not exercise install/update/uninstall, path boundary, clone-origin, CORS or 73 native discovery. Full npm audit from registry.npmjs.org reported 6 dev-tree vulnerabilities (2 moderate, 2 high, 2 critical); `--omit=dev` reported 0 production vulnerabilities. Review evidence, exact commands, outputs and limitations: `docs/research/evidence/xdlkc-skillhub-review-2026-11-24.txt`.

Primary corpus **229/303 reviewed, 74 pending**; supplemental net-new **177 pending**; manual additions **15 total / 3 pending**; primary+supplemental pending **251**, including manual pending **254**. Next candidate: `xfan3696-collab/skillpkg` (#230). No user session, profile, credential or installed Skill was accessed; research remains active/incomplete.

## 2026-11-24 continuation — candidate #230 skillpkg and separate PyPI lead

The user-confirmed target is unchanged: Claude Desktop via a third-party provider/API gateway in Chat, Cowork and Code, plus local/self-hosted Claude Code. Candidate #230 does not implement those readers or writers.

`xfan3696-collab/skillpkg` is pinned at main/origin-main `ba406e139f12a0db6abcd1da232e5273e057b05f` (2026-03-13), a MIT 8-commit repository with 0 stars/forks and no releases, GitHub Actions workflow or test suite. The architecture is CLI → HTTP index/server → S3/MinIO, storing one versioned SKILL.md tarball plus JSON manifest. The generic package home is `~/.skillpkg/skills`; it does not write native profiles or model harness-specific Project/Session structure. Good ResourcePlane concepts include separation of S3 credentials, per-version bundle hashes and a machine-readable index; the hash is not a publisher signature. Local Git “source” is only a directory copy; `version` is ignored there; `requires` has no resolver; `update` is not implemented; string comparison can leave version 0.9.0 latest after 0.10.0 publishes.

Isolated safety probes showed why not to reuse or deploy this implementation: remove/install names can escape the configured skill directory; an HTTP index's `file` member can escape the client's TemporaryDirectory and overwrite a synthetic outside file; publish succeeds with no token when the optional `SKILLPKG_PUBLISH_TOKEN` is unset (also the docker-compose default); a plaintext publish token is stored in mode-0644 config under umask 022. All data was synthetic and under `/tmp`; no real S3, profile, token, Skill or session was used. A tar extraction `filter="data"` is a useful defense but does not prevent the preceding download-path write. Full source, exact commands and outputs: `docs/research/evidence/xfan3696-collab-skillpkg-review-2026-11-24.txt`.

The README's `pip install skillpkg` is ambiguous: current PyPI `skillpkg` belongs to a different maintainer/project (0.0.6). The separate `skillpkg-cli`/GitHub `Exaggarate/skillpkg` project is a new manual-review lead, not part of this #230 review; its public claims include runtime discovery and security checks but are unverified here. Added it as manual pending so the name collision and stronger alternative aren't lost.

Primary inventory 230/303 reviewed, 73 pending; supplemental net-new 177 pending; manual additions 16 total/4 pending; primary+supplemental pending 250, manual-inclusive 254. Next primary candidate: `Xichun123/dsh-skills-manager` (#231). No email or completion notice has been sent; research remains active/incomplete.


## 2026-11-24 continuation — candidate #231 and updated next gate

The user confirmed the Claude Desktop local/third-party-provider/API-gateway scope includes **all three modes: Chat, Cowork and Code**. Keep those as separately versioned profiles alongside local/self-hosted Claude Code; do not conflate this with Anthropic-hosted Claude Code Cloud. This candidate review changes no target scope.

Candidate #231 `Xichun123/dsh-skills-manager` is a DSH-only Skill ResourcePlane adapter, not a cross-Harness Project/Section/Session migrator. It provides a private Skill library, provenance lockfile, workspace/global scope and manual-only policy state; it cannot migrate session messages/events, lineage, media, MCP/plugins, schedules, memory or resume state. Pin `13004c2e00c90e68d383ae63a31932dfb12a172a`; `UNLICENSED`; repo CI and 24 local tests pass, but the README's `pnpm validate` is not a package script. The public open issue #1 reports that the published plugin fails activation and browser RPC on DSH 0.2.0-rc.2, and that peer bounds block clean install. Source confirms the custom `/skill-manager` RPC and older peer ranges, while the runtime failures remain issue-author-reported rather than independently reproduced. Full dependency audit finds one high Zod and one low KaTeX advisory; production-only audit reports none. Retain only abstract adapter patterns; no source reuse. Full evidence: `docs/research/evidence/xichun123-dsh-skills-manager-review-2026-11-24.txt`.

Primary corpus **231/303 reviewed, 72 pending**; supplemental net-new **177 pending**; manual additions **16 total / 4 pending**; primary+supplemental pending **249**, including manual pending **253**. Next primary review is `yyeret/ai-threads-kanban` (#232), a cross-Harness in-flight work/thread board; inspect its actual schemas and source to distinguish task-board cards from durable Session/branch lineage. Research remains active/incomplete; no user data, credentials, private profiles or sessions were used.


## 2026-11-24 continuation — candidate #232 and next gate

The confirmed local Claude Desktop third-party-provider/API-gateway destination remains three separate modes (Chat, Cowork, Code), plus a distinct local/self-hosted Claude Code profile. Candidate #232 does not connect to ChatGPT Projects or any Desktop mode.

`yyeret/ai-threads-kanban` is stronger adjacent prior art than an asset-only Skill catalog because it reads local Claude Code, Codex, Gemini CLI and Antigravity session histories and maintains a reviewed workflow overlay with native continue/archive affordances. It does not provide migration. Its durable identity is a repo-basename/first-prompt hash plus same-repo fuzzy Jaccard merge, with no message event archive, branch/fork/parent/subagent edges or Project/Section hierarchy. It has no ChatGPT/Claude Desktop modes, file attachments, portable bundle, field loss report or target import/resume. It is MIT, but source-level and synthetic testing found an unauthenticated GET mutation route accepted with a synthetic external Origin, and an unquoted shell resume string from fabricated Codex metadata (not executed). The Codex archive path also rewrites `session_index.jsonl` and moves rollouts; no user installer or real profile was touched. Keep as a high-value local SessionInventory/UI reference only; require identity and security hardening before reuse. Full evidence is in `docs/research/evidence/yyeret-ai-threads-kanban-review-2026-11-24.txt`.

Primary corpus **232/303 reviewed, 71 pending**; supplemental net-new **177 pending**; manual additions **16 total / 4 pending**; primary+supplemental pending **248**, including manual pending **252**. Next primary candidate is `zuhabul/yo-code` (#233); inspect source and license rather than assuming “cross-harness workflows” means session migration. Nexus research/prototype remains active and incomplete; no target data was accessed.


## 2026-11-24 continuation — candidate #233 legal stop gate

The target remains local/self-hosted Claude Code using an API key plus Claude Desktop through a third-party gateway in three distinct modes: Chat, Cowork and Code. `zuhabul/yo-code` appears relevant because public docs describe local API-key account storage, but its own LICENSE/SOURCE_PROVENANCE claim the imported source is leaked proprietary Anthropic Claude Code and expressly prohibit a competing product based on it. Stop source analysis at this boundary: do not use implementation code or code-derived architecture for Nexus. The repo also states its runtime is not provider-agnostic and its recovered full CLI cannot boot due to missing modules. Public docs do not describe migration or ChatGPT/Codex Project/Session import. Bun checks could not run because Bun is absent; no install/runtime/user data/key access occurred. Full evidence: `docs/research/evidence/zuhabul-yo-code-review-2026-11-24.txt`.

Add a **provenance/license gate before deep source work** to the candidate workflow: require a clear, compatible license and origin statement; if source is marked leaked/proprietary or use in a competing product is prohibited, stop source-level analysis, mark as documentation-screened rather than code-reviewed, exclude code and code-derived design, and seek only lawful independent sources for the same product requirement. This does not reduce the original research breadth; it prevents tainted implementation reuse while continuing through the candidate queue.

Primary corpus **233/303 reviewed or screened, 70 pending**; supplemental net-new **177 pending**; manual additions **16 total / 4 pending**; primary+supplemental pending **247**, including manual pending **251**. Next primary candidate: `zxu756/AgentVM` (#234), an APFS snapshot/lineage manager; review its actual public license/provenance before source analysis. Nexus research and prototype remain active/incomplete.
### 增量深审：agent-history（primary #235，2026-11-24）

在已确认的平台范围内继续：ChatGPT `Destruction Era` Project、Section Group 与完整 Session/资源关系；Claude Desktop 第三方网关下 Chat、Cowork、Code 三种独立模式；以及本地/自托管 Claude Code API-Key 工作流。`lvtd-dgtl/agent-history` 在指定浅克隆中解析为 MIT 项目，HEAD `fefe2d1833af2c93f0cf3048d5e2fcf5787b35d6`（2026-11-21）；GitHub 页面重定向到 `d3layd/agent-history`。其定位是本地会话转录的统一检索/索引，不是源到目标迁移器。

有价值的实现方向：按 Harness 维护独立、只读的文件/SQLite source adapter；记录 session aliases、Claude Code subagent/部分 fork 提示、远程会话 bridge IDs；报告 torn JSONL 和索引覆盖；以只读命名列访问可能同时保存 OAuth tokens/system prompts 的 SQLite；把 local Project memory 记录进索引；将 MCP、Claude Code plugin hooks、cron/Task Scheduler 看作索引更新与召回接口。这些都不能替代 canonical event/session graph 或目标端 writer。

已核实的边界：Claude.ai 必须先下载并显式导入官方数据导出；Projects/docs/instructions、memory、design chats 和 extracted attachment text 是独立 searchable records。当前 adapter 明确说 export 不把 chats link 到 Projects。它按顺序提取可读文本，不重建完整 branch/event graph；thinking/tool-use/tool-result、图片字节、用量/token 计数等未迁移，附件抽取文本截断为 100,000 字符。`doctor --coverage` 将 live claude.ai Chat、claude.ai/code Cloud session 和 Claude Desktop Cowork 列为无 adapter 可见的 surface；没有 Claude Desktop Chat/Cowork/Code 或 Claude Code API-Key target-native writer。Plugin、MCP、cron、Windows Scheduled Task 更新的是该工具索引，不是移植来源端 schedules/resources。

关键安全教训：本机 SQLite index 默认保留完整消息文本，redaction 默认关闭且无 at-rest encryption，作者明确要求按 credential store 对待。Nexus 不应照搬该默认；应 preview-first、将 API keys 留在 OS secret store、禁止未经允许的远端 embedding/索引、在任何 egress 之前做 secret scrub、把原始导出和派生索引分层并可审计删除。

本地校验：MIT 文件/来源检查后才进行代码阅读。CodeGraph 102 files / 2,605 nodes / 8,507 edges。聚焦 parser/identity 105 passed/56 skipped；pytest 全量 434 passed/410 skipped；其中 409 项因本机 Python 3.12 无 SQLite extension loading 而 skip，1 项 Windows-only。不能据此声称本机 SQLite 集成或跨平台全通过。无私人 profile/export/API key/Ollama/provider API 被使用；测试依赖安装在临时 venv。详见 `docs/research/evidence/lvtd-dgtl-agent-history-review-2026-11-24.txt`。

产品决策：收录为高价值的**本地历史归档/搜索/覆盖检测**邻接先例；不计为跨 Harness migration success，不以 chunk index 替代 `SessionGraph`。数据层维持不可变 source events → canonical graph/hierarchy → target-native projection → optional search index 四层独立。明确保存每条转换边的证据/丢失项，ChatGPT Sections/Projects 与 Claude Desktop 三模式分别验证，不依据 workspace path 或 session title 猜关系。

Primary corpus **235/303 reviewed, 68 pending**；supplemental net-new **177 pending**；manual additions **21 total / 9 pending**；primary+supplemental pending **245**，manual-inclusive **254**。下一 primary candidate：`neosun100/aiw` (#236)。Nexus 调研与原型仍 active/incomplete。


### 增量深审：neosun100/aiw（primary #236，2026-11-24）及证据完整性修正

`neosun100/aiw` 在 main HEAD `a9e4221aa39e20aa7c041528805f8a763c035158`（2026-01-08）为 MIT tmux 工作空间管理器。它在目录绑定的 tmux 会话中启动/管理 CLI agent，保存的只是 workspace name、tool、model、dir、desc、created 元数据；不是聊天 transcript、Project/Section/Session lineage 或 session importer/exporter。它无法证明会将 ChatGPT `Destruction Era`、Section Group、Sessions/子任务/产物/媒体导入 Claude Desktop 第三方网关的 Chat、Cowork、Code 三模式，也不是本地/自托管 Claude Code API-Key provider adapter。Skills/MCP/plugin/memory/task schedule 的迁移也未实现。

当前不应把它当安全后端：HTTP 默认监听 `0.0.0.0`、没有内建认证/授权；接口可向 agent 发送命令、关闭 session、连接交互终端。`tmux.py::_run` 以 `shell=True` 拼命令；README 建议用带认证与 HTTPS 的反向代理保护暴露服务。另 `rename_workspace` 使用未定义 `SESSION_PREFIX`（隔离的安全探测得到 NameError）；`mcp>=1.0.0` 无上界，当前解析到 2.3.0 后 14 个 MCP 测试因旧 Server decorator API 失效而失败；使用 1.0.0 时 66 tests 全通过。没有真实 tmux/网络服务器/用户配置/秘钥参与测试。只保留为邻接的本地 workspace orchestration prior art，不作为 migration target 或 Nexus 网络服务依赖。

#### 审计修正：#234 AgentVM 证据与 inventory 行

续审 #236 时重新打开 #235 的 MODIFIED_FILE.zip，发现 #234 的 `zxu756-agentvm-review-2026-11-24.txt` 虽然被 followup234 verification ledger 列为新增路径，却并未在 ZIP 内；主清单对应记录也仍标记 `unreviewed`，与累计 235/303 计数矛盾。已依据可重开的 followup234 ledger 及同一 pinned MIT checkout恢复证据文件，并把记录状态与已执行测试结果对齐；VM 测试是先前观察的结果，本轮没有声称重跑。现在 236/303 reviewed，67 pending，且 `review_status=unreviewed` 的行数也恰为67。

最新研究边界仍明确包括 ChatGPT **Destruction Era**、Section Group、完整 Session/资源；Claude Desktop 第三方网关 Chat/Cowork/Code 独立适配；及本地/自托管 Claude Code API-Key workflow。AIW 与 AgentVM 均不构成 migration success。主清单 236/303、67 pending；补充目录177 pending；人工补充21总数/9待审；primary+supplemental pending244，manual-inclusive253。下一 primary candidate `i3T4AN/Archivist-MCP` (#237)。

详细审查：`docs/research/evidence/neosun100-aiw-review-2026-11-24.txt`、恢复的 `docs/research/evidence/zxu756-agentvm-review-2026-11-24.txt`。


### 增量深审：i3T4AN/Archivist-MCP（primary #237，2026-11-24）

`i3T4AN/Archivist-MCP`（MIT，HEAD `54fcaca4b25f1452ce5ced55a878199d8b285bec`）是目前最相关的**独立记忆图谱/召回**先例之一：按 Project 存储 Decisions、Rules、Incidents、Entities、Observations、Artifact 引用、typed edges 和审计事件；MCP 暴露结构化读写、冲突解决、memory promotion/invalidation，WebUI供人工回顾；`core_memory.md/.json`把部分资料压缩为预算内上下文。可作为未来可选的 target memory adapter 参考；与 user 目标所要求的源 SessionGraph/Project/Section migration 是不同平面。

会话数据的实际边界：schema虽有 `sessions(session_id, project_id, user_id, client_type, started_at, ended_at)`，`observations.session_id` 可选引用；但 MCP tool list 中无创建/导入 session 的工具，Quickstart 只 seed project/user。通用的 `Session` graph node 不能替代 relational session row，也没有消息事件、轮次顺序、active branch、父子/子任务/委派边、token/usage、typed image/audio 或 transcript archive。真实 `store_observation` 关联到未种入的 session ID 的合成临时库探测返回 `INTERNAL_STORAGE_ERROR: FOREIGN KEY constraint failed`。memory 的 `scope=branch` 是知识记录晋升生命周期，不是对话 fork。

出口与删除：`export_audit_log` 仅导出有限审计事件和 digest，不导出图节点/关系内容；snapshot/restore 是本地 SQLite 整库恢复，不是跨 Harness 可移植 bundle。默认 core memory 预算12KiB并允许截断，属于派生投影。Observations purge 仅清理老旧 Observation（高置信/长文本移交 triage）；不会处理 Nodes、Artifacts 或审计历史。

安全：`encryption_required` 默认 false，普通 SQLite 默认未加密；SQLCipher可选，配置要求加密时库不可用会 fail closed。合成 fake `sk-...` 值在 create_entity 的临时 DB探测中以原文写入，说明 secret redaction 不在内容入库路径；日志与 audit export 的 redaction 不等于数据消毒。默认 HTTP 是 loopback，但 `ARCHIVIST_SSE_TOKENS` 为空时 MCP HTTP tools/list/call 无需 Bearer token；若改绑非本机地址必须显式配 token 与 TLS。Team SSE 才强制 bearer token + role/project scope。`--require-user-id`只检查 caller 提交的字段，不验证身份。Hash-local embedding 是当前真实实现，配置中其它名称未落地 provider。

本地验证：CodeGraph 86 files / 979 nodes / 2,462 edges；全量测试 `rtk test /tmp/nm-aiw-review-236-venv/bin/python -m pytest` exit 0，79 passed / 5.89s。临时 SQLite 仅含 synthetic fixtures；未访问用户 `.archivist`、ChatGPT export、API key、provider/model endpoint 或远端服务。完整代码和探测结果见 `docs/research/evidence/i3T4AN-archivist-mcp-review-2026-11-24.txt`。

架构决策：保留为**后迁移的可选记忆图谱 target adapter** prior art，不将其视为 source history 或 Session hierarchy 的权威档案。Nexus仍应先保存不可变源数据和 canonical Event/SessionGraph，再按显式 loss-report 决定是否把选定决策/规则/项目记忆映射到该类图；将 Portable Archive、Source adapter、Target writer、派生 Search/Memory 层分开。上线前要求为其补齐 session import/session lifecycle、跨平台图谱bundle、全量数据删除/保留策略、默认加密和入库 secret redaction、非 loopback 强制认证，以及真实 Chat/Cowork/Code/API-key fixture tests。

主清单 237/303 reviewed、66 pending；supplemental net-new177 pending；manual additions21 total/9 pending；primary+supplemental pending243、manual-inclusive252。下一主清单候选 `maideps/ai-harness-framework` (#238)。研究仍 active/incomplete。


## 2026-11-24 continuation — user-confirmed Claude Desktop scope and candidate #238

The user confirmed that Claude Desktop configured for third-party inference/gateway includes **Chat, Cowork, and Code**. First-party Claude Desktop documentation directly confirms all three modes route requests through the selected gateway using Claude Code, and documents a Gateway endpoint with static API key or OIDC authentication. The gateway must implement Messages API streaming and tool use; model discovery is optional, and cache/usage fields should be preserved. This is inference-plane evidence only: app-level gateway configuration is distinct from Claude Code CLI API-key variables/settings, and an active gateway removes Anthropic-hosted cloud environment choices and Remote Control. Continue to treat native resume/import, session stores, local/cloud execution, and gateway routing as separate dimensions. Updated Cowork cloud/local behavior is version-sensitive; capture app version and session locality in the target adapter tests. Sources: https://claude.com/docs/third-party/claude-desktop/gateway ; https://code.claude.com/docs/en/llm-gateway-connect ; https://code.claude.com/docs/en/sessions ; https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile ; https://support.claude.com/en/articles/16761823-claude-cowork-and-chat-are-one-claude .

Candidate #238 `maideps/ai-harness-framework`, MIT at pinned `e0de706a240892ea2d3a66e5d7a56ec59d75d48e`, is an adjacent coding workflow framework for Claude Code/Codex/Gemini CLI, not a cross-Harness session migrator. Its persistent “sessions” are feature/workflow state and git/verification traces; no native turn/event/lineage/media/token/session archive, ChatGPT Project/Section importer or Claude Desktop 3P writer was found. Safe adoption/upgrades with pre-overwrite backups, skill packaging, WIP=1 lanes, and verification summaries are useful, separate patterns. Full check `rtk test npm run check` exited 0; RTK-visible terminal showed 74.93% coverage against ≥65; no test count surfaced. CodeGraph 44 files/656 nodes/2,511 edges; `sessionTrace` one caller/no direct unit test. Full record: `docs/research/evidence/maideps-ai-harness-framework-review-2026-11-24.txt`.

Primary corpus 238/303 reviewed, 65 pending; supplemental net-new 177 pending; manual additions 21 total/9 pending; primary+supplemental pending 242, manual-inclusive 251. Nexus remains in active research/prototype phase; no Destruction Era migration or research-completion notice is claimed.


## 2026-11-24 continuation — candidate #239 and definitive Claude Desktop 3P store map

User scope remains: ChatGPT Project **Destruction Era**, Section Group and full Session/subtask/fork/resources; target Claude Desktop third-party inference in Chat/Cowork/Code, plus separate local/self-hosted Claude Code API-Key/gateway support. Latest first-party Desktop 3P docs make the storage model more precise: `local-agent-mode-sessions/` holds Chat/Cowork conversation history, workdirs/uploads/outputs, memory and `audit.jsonl`; `claude-code-sessions/` holds Code session metadata (working folder/settings/title/summary), while the transcript JSONL is in shared `~/.claude/projects/`. Chat/Cowork are now unified in the home interface where the Cowork VM is available, and Code remains separate. The official import wizard copies claude.ai exports and supported prior Desktop Cowork/Code folders, but is one-time and source-specific; no generic ChatGPT JSON import contract is described. It carries some resource layers, with explicit losses such as connector sign-ins, Code attachments, permissions, project links, and project knowledge/attached file contents in personal exports. Record mode, locality, version, store roots, and tested native-resume behavior separately. Sources: https://claude.com/docs/third-party/claude-desktop/data-storage ; https://claude.com/docs/third-party/claude-desktop/import ; https://claude.com/docs/third-party/claude-desktop/unified-claude ; https://claude.com/docs/third-party/claude-desktop/code .

### Primary #239 — `1naruto-1/agent-connect`

Pinned MIT main `42287c14a8fd381bc7ef7a96076a5cba5b4d75f6`, 2026-08-09. This is genuine coding-CLI session continuity for Cursor, Claude Code CLI, Codex CLI and Pi: 122 tests/386 assertions pass in Bun 1.3.14; host build, smoke and checksum checks pass. Its event projection does not preserve chat/project/section graphs, full fork trees, images/attachments, usage/model/provider settings, memory, schedules or skill/MCP/plugin config. Its Claude target writer writes CLI transcript JSONL but not Claude Desktop 3P local-agent Code metadata or Chat/Cowork stores; only target-app/native-list tests can prove full support. It should be retained as adapter prior art, not reused as an already-solved migration system.

A safe synthetic Codex-profile probe found `configTemplate()` copies the newest other local Codex session's `base_instructions` and `turn_context` into a new session. Fake canaries placed only in a temporary HOME reappeared in the target rollout; no real profile/credential was touched. Any prototype must avoid implicit cross-project context inheritance and must keep source config/resource dependencies explicit. Detailed candidate evidence: `docs/research/evidence/1naruto-1-agent-connect-review-2026-11-24.txt`.

Primary inventory 239/303 reviewed, 64 pending; supplemental net-new 177 pending; manual additions 21 total/9 pending; primary+supplemental pending 241, manual-inclusive 250. The user's source data has not been migrated; research and implementation remain active.


## 2026-11-24 continuation — candidate #240 AgentHoard

The target remains ChatGPT Project **Destruction Era**, Section Group and full Session/subtask/fork/resources; Claude Desktop via third-party inference in Chat, Cowork and Code separately; and local/self-hosted Claude Code via API key/gateway. Candidate #240 is MIT AgentHoard (dawnnnnnnnnnnnnnnnn/agent-hoard, HEAD e3b43df1898e9c0af3db38ac226fc3ce9f15eeca), a local disk scanner/cleanup UI, not a migration system. It does not preserve Project/Section/session lineage, message events, attachments, Skills/MCP/plugins, memory, schedules or provider credentials, and it has no ChatGPT source or Claude Desktop 3P target writer.

A disposable-HOME full test exited 0: 5 passed, 0 failed, 1 skipped in 121 seconds. The MCP verifier's dangling 120-second timers cause the delay; its space_plan request returned a no-cache error while the wrapper still passed. Isolated synthetic HTTP probes confirmed /api/trash can move arbitrary out-of-root files without confirm and /api/trash/purge can permanently delete a named batch without confirm; server default is loopback, configurable HOST, with no observed auth/origin guard. This is a security finding on the candidate, not a browser exploit claim. Keep it as low-fit inventory prior art only; do not adopt it against real user state. Full evidence: docs/research/evidence/dawnnnnnnnnnnnnnnnn-agent-hoard-review-2026-11-24.txt.

Primary corpus **240/303 reviewed, 63 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **240**, manual-inclusive **249**. Nexus research/prototype remains active and incomplete; no Destruction Era migration or research-completion notice is claimed. Next primary candidate: NeoHsu/mnemark (#241), selected from the remaining unreviewed primary corpus. Research remains active/incomplete.


## 2026-11-24 continuation — candidate #241 NeoHsu/mnemark

Candidate #241 is MIT NeoHsu/mnemark v0.10.1 at exact main/release commit 12d6656b4511d161e83c091e40b313ac25be062e. It offers portable, local-first curated memory for five coding CLIs, plus Mnemark-specific JSON and bundle store transfer; it is not a conversation/session importer. Synthetic raw ChatGPT conversation JSON failed its memory importer with missing field name. Mnemark's project scope is project:owner/repo and is not a nested ChatGPT Project/Section graph; there are no session/message/branch/attachment records. The Claude Code SessionStart hook performs contract-gated read-only prime only; no transcript ingestion and no Claude Desktop 3P modes or gateway/API-key configuration.

Positive prior art: explicit trust/provenance, memory record lifecycle, scope, graph context, store bundle checksum validation, isolated agent wiring, source validation and explicit memory transfer. Important boundary: no SQLCipher/at-rest encryption; bundles are plaintext and hashes do not authenticate publishers. Treat this as an optional user-curated memory adapter, never the canonical archive or migration success. Full review: docs/research/evidence/neohsu-mnemark-review-2026-11-24.txt.

Rust 1.97.1 local checks on the exact release commit: 273 workspace tests passed, format and Clippy passed, doc-drift 10/10 passed, and isolated Mnemark memory import/export/bundle roundtrip passed. The full mise PR gate was not run because mise is unavailable; full audit/gitleaks/nextest are not claimed.

Primary corpus **241/303 reviewed, 62 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **239**, manual-inclusive **248**. Nexus research and prototype remain active/incomplete; no Destruction Era migration or completion notice is claimed. Next primary candidate: slonana-labs/agichan (#242). Research remains active/incomplete.


## 2026-11-24 continuation — candidate #242 agichan provenance stop

Candidate #242 slonana-labs/agichan is a README-documented multi-machine task swarm with manager/worker messages, per-worker branches, MCP/Skill/CLI/Claude Code hooks and a claimed encrypted channel. This is live coordination, not ChatGPT Project/Section/Session archive migration. No LICENSE/COPYING file or explicit grant was found in the clone; GitHub license metadata is absent. Per the provenance gate, source-level review, install, tests and reuse were stopped. Do not treat readme-level encryption or coordination claims as verified migration/security support. Documentation-only report: docs/research/evidence/slonana-labs-agichan-review-2026-11-24.txt.

Primary corpus **242/303 reviewed or screened, 61 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **238**, manual-inclusive **247**. Nexus research remains active/incomplete; no migration or completion notice is claimed. Next primary: chrisreedbates/a2a-dms (#243). Research remains active/incomplete.


## 2026-11-24 continuation — candidate #243 chrisreedbates/a2a-dms
The first-phase target remains ChatGPT Destruction Era Project/Section Group/full Session, lineage and resources; Claude Desktop third-party-inference Chat/Cowork/Code separately; and local/self-hosted Claude Code via API key/gateway. All three Desktop modes remain confirmed scope; this candidate does not implement any of them.
A2A DMs (MIT, main HEAD `31b96830fbdd7ef5d3a8a2c702e5e2b99695c2c2`) is a local tmux wake/coordination utility, not migration: no ChatGPT reader, canonical session graph, native importer, transcript export, resource transfer, or Claude Desktop/local Claude Code target writer. It has no formal test suite or release. Isolated syntax/install checks passed; synthetic tests found an unvalidated lease path escape and a duplicate wake caused by independent CLI/watchdog cooldowns. Retain only as low-fit orchestration prior art, not as a Nexus dependency. Review: `research/evidence/chrisreedbates-a2a-dms-review-2026-11-24.txt`.
Primary corpus 243/303 reviewed; 60 pending; supplemental net-new 177; manual additions 21 total / 9 pending; primary+supplemental pending 237; manual-inclusive 246. Next primary: benvenker/agent-session-search (#244). Research/prototype remains active and incomplete; no migration or completion notice is claimed.


## 2026-11-24 continuation — candidate #244 benvenker/agent-session-search
The confirmed target remains ChatGPT Destruction Era Project/Section Group/full Session graph/resources; Claude Desktop third-party-inference Chat, Cowork and Code separately; and local/self-hosted Claude Code via API Key/gateway. Candidate #244 is useful for local lexical session discovery only. It does not ingest ChatGPT exports into a canonical graph, preserve hierarchy or write any of the three Claude Desktop modes or local Claude Code.
MIT v0.9.1. Main session search is a local read/search layer over FFF; a custom root can search a JSON export as text but returns only bounded paths/snippets. The optional cm compatibility shim can render a known session file to stdout but is capped and format-specific; a synthetic ChatGPT mapping export was rejected. Keep as high-value retrieval prior art, never as migration fidelity evidence.
On Node 26.7/npm 11.19 with isolated HOME/TMPDIR, npm check and build passed. Full suite: 370/370 passed with checksum-verified FFF 0.9.6. With current official FFF 0.11.0, managed grep remains functional but the strict native policy blocks changed `grep`/`multi_grep` schema fingerprints; 2 native lane tests fail, and the doctor smoke checks only the capabilities tool. Both versions failed the multi_grep recall-equivalence probe, so managed search explicitly uses sequential fallback. See the full evidence ledger in `research/evidence/benvenker-agent-session-search-review-2026-11-24.txt`.
Primary corpus 244/303 reviewed; 59 pending; supplemental 177; manual additions 21 total / 9 pending; primary+supplemental pending 236; manual-inclusive 245. Next primary: rore/Pallium (#245). Research remains active/incomplete; no migration or completion notice is claimed.

## Candidate #245 — rore/Pallium (2026-11-24)
The user reconfirmed that Claude Desktop scope covers all three third-party-inference surfaces: Chat, Cowork, and Code. The source remains ChatGPT Destruction Era Project/Section Group/full Session graph/resources; also include local/self-hosted Claude Code via API key/gateway. Official Anthropic docs distinguish the client 3P deployment from Anthropic-hosted Cloud sessions and document different local stores for Chat/Cowork versus Code.

Pallium (MIT, main HEAD `e2b55fbc8f5ed8f23ac242d1a29be2aa173e7efd`) is local selected-turn history search plus cross-session plain-text Relay for Claude Code, Codex, OpenCode, and Hermes Desktop/TUI. It has no ChatGPT export importer, no first-class Project/Section/Session/Fork graph, no attachment/event/token migration layer, and no Claude Desktop 3P Chat/Cowork/Code or local Claude Code target writer. Source schema `SourceItemRecord` records per-turn/source text, role, scope/thread refs, artifact kind, visibility, ordering/attribution metadata; arbitrary metadata is not a migration mapper. Relay is message delivery, not a hierarchy/task engine. History docs explicitly exclude full audit-log and external-state guarantees. Disposition: high-value local searchable-memory/security prior art only; not migration compatibility and not a Nexus dependency recommendation.

Focused disposable test run: after installing the declared optional vector extra, 8 history/visibility/relay test files passed **258/258 with 1 skipped**. The initial run without the vector extra had 257 passed, 1 skipped, 1 failed because the optional `usearch` backend was absent; the corrected run is the qualifying result. Full suite, other OSes, real service, private sessions, and live providers were not tested. Full evidence and commands: `research/evidence/rore-pallium-review-2026-11-24.txt`.

Primary corpus **245/303 reviewed, 58 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **235**, manual-inclusive **244**. Nexus research/prototype remains active/incomplete; no Destruction Era migration or research-completion notice is claimed. Next primary: `zen-solutions-dev/zen-agent-skills` (#246).

## Candidate #246: zen-solutions-dev/zen-agent-skills (2026-11-24)
The user's confirmed source and destination remain unchanged: ChatGPT **Destruction Era** Project/Section Group/full Session graph/resources to Claude Desktop 3P Chat, Cowork, and Code separately, plus local/self-hosted Claude Code via API key/gateway. Candidate #246 is a Skills/distribution prior-art review only.

`zen-solutions-dev/zen-agent-skills` is an MIT, cross-Harness **skills library**, not an agent runtime or session migrator. Main HEAD `b61dab8b1ede6ece42e950e70e820b1a7ee68590` (2026-10-21). Local `git ls-remote` showed the same `main` commit at the README's `hams-ollo/zen-agent-skills` quick-start URL; treat those as aliases of one snapshot. GitHub at review: 2 stars, 0 forks, 0 open issues, 3 open PRs, 348 commits; no release/tag observed. Canonical `SKILL.md` bodies distribute globally to Claude Code/OpenCode, with project adapters for Cursor and VS Code/Copilot and an optional Claude Code plugin tree. The integration table does not list Codex as a first-class install target; other Harnesses are directed to read the canonical skill or use a local adapter.

Useful Skills-plane prior art: single-source skill instructions, generated adapters, description budgets and closed-over sibling dependencies, ownership manifests and non-destructive install/uninstall. No ChatGPT project or Section Group importer, session/transcript/hierarchy export, attachment or tool-event preservation, MCP/gateway configuration, or Claude Desktop 3P target writer.

The repo also contains a maintainer-only, unshipped `agent-observatory` draft. Its separate observatory scans local Claude Code JSONL under `~/.claude/projects`; the SQLite schema models message parent UUIDs, replay occurrences, tool calls, subagent sidecars, token metrics and context samples. It stores derived analytics, not raw message bodies/attachments, and does not migrate or resume sessions. Keep this as narrow Claude Code parsing/schema prior art, not shipped product support.

`rtk proxy python3 scripts/run-checks.py` exited 0: **9 passed, 0 failed, 0 could not run** on Darwin/Python 3.12.10 (one of six CI matrix cells). Adapter/install dry-runs and an isolated temporary install cycle passed; tests had 2 skips. No real target client was invoked and no user session or provider credentials were touched. Full evidence: `research/evidence/zen-agent-skills-review-2026-11-24.txt`.

Primary corpus **246/303 reviewed, 57 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **234**, manual-inclusive **243**. Research remains active/incomplete; no Destruction Era migration or completion notice is claimed. Next primary candidate: `AndySze/session-seek` (#247), which is directly session-search/MCP-oriented and should receive the same license and source gate.



## Candidate #247 — AndySze/session-seek (2026-11-24)

`AndySze/session-seek` (MIT, main HEAD `da27a2632c7941afc8d8335bdd42a3ea8b8c7ade`) is an MCP search/index utility for local Claude Code and Codex CLI JSONL, not a ChatGPT Destruction Era Project/Section/Session migrator. Claude Desktop remains in scope for third-party-inference Chat, Cowork, and Code separately, alongside local/self-hosted Claude Code via API key/gateway. Its five search/index/context/stats tools have no target writer, graph importer, attachment/event transfer, or skills/MCP/plugin/schedule dependency migration. Its small text schema is session-id/project/role/text/time/cwd/slug/line/content type, without parent/fork/session-lineage or first-class project/Section records.

The synthetic MCP smoke passed and confirmed local discovery/search over both providers. A separate fake-local-embedding probe indexed synthetic Claude/Codex records, then dynamically demonstrated stale sensitive text after deleting its source file: reindex processed zero, semantic search still returned the deleted Codex answer, and stats retained two files/four chunks. Treat as moderate adjacent retrieval prior art only, not a migration dependency; the deletion/forget and source-fingerprint controls are especially important Nexus requirements. Full source and run evidence: `research/evidence/andy-session-seek-review-2026-11-24.txt`.

Primary corpus **247/303 reviewed, 56 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **233**, manual-inclusive **242**. Research remains active/incomplete; no migration or completion notice is claimed. Next primary candidate: `Burney-Web-Services/Best-Foot-Forward` (#248).


## Candidate #248 — Burney-Web-Services/Best-Foot-Forward (2026-11-24)

BFF is a strong **adjacent structured-memory, Skills, and MCP reference**: a local SQLite career-memory model, generated JSON caches/Logseq pipeline, shared agent workflows, and an MCP `get_profile_bundle` for a narrowly defined offline job-sourcing profile. Synthetic stdio testing confirmed that bundle contains selected career caches and one Claude Code `user_profile.md`; it does not contain transcript/session graphs, story database, applications, binary attachments, or tool history. BFF's “projects” and Logseq pipeline are job-search concepts, not ChatGPT Projects or Section Groups. It does not import ChatGPT **Destruction Era** sessions or create Claude Desktop third-party-inference Chat, Cowork, or Code sessions, nor local/self-hosted Claude Code API-key/gateway sessions. The user-confirmed three Desktop modes remain in scope.

Cross-Harness cleanup Skills do offer good selective artifact capture and user-vs-agent provenance rules, but they rely on an agent deciding what to summarize and are not lossless/reversible. An isolated MCP bundle smoke passed. The full suite passed **519 tests with 14 UAT skips** on each of Python 3.11/3.12/3.13. The skips require an isolated data DB; running the optional UAT would invoke a live `claude -p` model call, so it was not run. No real credentials, model provider, or user data were used. Disposition: **high-value narrow architecture prior art; no direct migration code or dependency recommendation**. Full evidence: `research/evidence/burney-best-foot-forward-review-2026-11-24.txt`.

Primary corpus **248/303 reviewed, 55 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **232**, manual-inclusive **241**. Research remains active/incomplete; no migration or completion notice is claimed. Next primary candidate: `chazhyseni/ai-skillweave` (#249).


## Candidate #249 — chazhyseni/ai-skillweave (2026-11-24; license/provenance screen only)

README claims describe local Claude correction capture, session-history-to-Skills extraction, and ownership-aware Skill delivery across several Harnesses. This is a high-relevance **Skills-plane discovery lead**, not evidence of importing ChatGPT Destruction Era Projects/Section Groups/full Sessions or creating Claude Desktop 3P Chat/Cowork/Code sessions. Its Claude Desktop note refers to separate snapshots that must be rebuilt/re-imported; no conversation/session import contract is documented. The README also says Claude/Copilot Skill delivery does not configure their provider APIs.

**Gate stop:** no LICENSE/COPYING/grant found; GitHub metadata has no license and `/blob/main/LICENSE` returned 404. Per the established provenance rule, no source, tests, installer, hooks, or runtime were inspected or run; no code or code-derived design is recommended. README claims remain unverified. Full screen evidence: `research/evidence/chazhyseni-ai-skillweave-screen-2026-11-24.txt`.

Primary corpus **249/303 reviewed or screened, 54 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **231**, manual-inclusive **240**. Research remains active/incomplete. Next primary candidate: `DevExpGbb/swampup-skills` (#250); apply the license/provenance gate before deeper review.


## Candidate #250 — DevExpGbb/swampup-skills (2026-11-24)

Small, APM-packaged catalog of three developer Skills (OpenTelemetry tracing, changelog generation, release notes); the latter declares a dependency on `changelog-writer`. MIT is declared in README and APM manifests, but there is no canonical LICENSE file and GitHub SPDX is null; APM docs clarify its `license:` value is the author's assertion, not a verified license-file conclusion. The repo has no conversation importer, session graph, memory store, MCP server, or Claude Desktop Chat/Cowork/Code resume support. APM's broader target matrix is a separate project and covers artifact deployment rather than conversations.

This is a narrow Skills-plane example, not a migration engine. README's unittest command fails because `tests/` is absent (exit 1); APM/native target installation was not run. Source checkout remains clean. Detailed scope, license caveat, commands, and citations: `research/evidence/devexgbb-swampup-skills-review-2026-11-24.txt`.

Primary corpus **250/303 reviewed, 53 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **230**, manual-inclusive **239**. Research remains active/incomplete; no Destruction Era migration or completion notice is claimed. Next primary candidate: `dexmaddy/ai-agent-harness` (#251).


## Candidate #251 — dexmaddy/ai-agent-harness (2026-11-24)

This MIT-licensed Claude Code/coding-agent workflow harness is **adjacent session-continuity prior art, not a cross-Harness migrator**. At pinned `main` HEAD `75ddb762e1392b448a2bf41d3c865e745fc243fd` (matching remote HEAD), it builds startup manifests/sentinels and hooks, and documents JSON/SQLite backlog plus end-of-session summaries. The DB model stores summary fields only (`topic`, completed/next items, date, duration, prompt count); it has no session ID, ordered turn/event archive, Project/Section, branch/subtask graph, attachments, or import/export adapter. The transcript option is only a filename check. The wizard lists Claude Code, Cursor, Windsurf, Aider, and custom—not Claude Desktop Chat/Cowork/Code or a third-party gateway/session writer. Keep its handoff concept separate from Nexus's lossless SessionGraph; do not reuse its session-gate implementation as-is.

Validation: README smoke command exited 0 (**37 passed, 0 failed**). A synthetic SQLite probe exposed a session identity gap: no same-session summary made `on_stop.py` exit 2, while an unrelated same-day summary allowed the synthetic new session to exit 0. Only disposable test data was used. Full mode/API/provider matrix and setup installation were not run. Evidence: `docs/research/evidence/dexmaddy-ai-agent-harness-review-2026-11-24.txt`.

Primary inventory **251/303 reviewed, 52 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **229**, manual-inclusive **238**. Research remains active/incomplete; no Destruction Era migration or completion notice is claimed. Next primary candidate: `Fabian-698/dsh-update-guide` (#252). Latest user reply reconfirmed all three Claude Desktop modes—Chat, Cowork, Code.


## Current research checkpoint — candidate #252 safety/version follow-up (2026-11-24)

This follow-up completes the primary-list review for `Fabian-698/dsh-update-guide` while preserving its earlier 2026-11-20 deep-review record. It remains a DSH-specific upgrade/recovery Skill, not a ChatGPT/Codex → Claude importer. The user's confirmed destination remains Claude Desktop third-party-gateway **Chat, Cowork, and Code separately**, plus local/self-hosted Claude Code via API key/gateway.

The pinned MIT repo (`0fcb77d2a9abf8c28da32119a243a568bd9c3824`) has 1 star / 0 forks in the captured GitHub page and only claims DSH 0.1.2-rc.1 through 0.1.7-rc.1. The official DSH release page now lists **0.2.3-alpha.2 (2026-11-22)**. Default selftest passed **24 checks, 0 failed**, with one explicit skip for a missing owner Skill; its `--full` mode was not run because it scans a real DSH home.

New disposable probes found: `verify-session` prints `SKIP S9` then `ALL PASS` and exits 0 when zstd is absent; `repair-v0-sessions --apply` checks a matching backup only for the first item but rewrites all fixable items; and a workspace symlink can direct the repair outside the configured DSH_HOME. The tests used a fake format catalog and temporary session files; they do not prove official DSH conversion success. Keep only versioned DSH schema/recovery observations; do not reuse the mutator or gate as-is. Full evidence: `docs/research/evidence/fabian-698-dsh-update-guide-followup-audit-2026-11-24.txt`.

Primary corpus **252/303 reviewed, 51 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **228**, manual-inclusive **237**. Research remains active/incomplete; no Destruction Era migration or completion notice is claimed. Next primary candidate: `henryyu333/CLUE` (#253).


## Current research checkpoint — candidate #253 CLUE (2026-11-24)

Candidate #253, `henryyu333/CLUE`, is a valuable **adjacent local-memory/text-recall reference**, not a ChatGPT Destruction Era Projects/Section Groups/full Sessions migrator. Its MIT v0.7.0 snapshot (`3b7a74533e4b1f455c38ced5dbe0cbf30f6eae80`, main and remote HEAD) indexes local text history from seven coding harnesses—Antigravity, Claude Code, Codex, OMP, pi, OpenCode and Hermes—into SQLite FTS. It has no ChatGPT source adapter, Project/Section or session-lineage graph, target writer, multimodal/tool/token transfer or measured conversion fidelity. `clue export` is a selected-memory plain-text context pack. The Claude target installs local Claude Code hooks, not Claude Desktop 3P Chat/Cowork/Code.

The durable-memory pattern (human-readable source files, explicit approval, one Git receipt/undo) is the narrow reusable concept. The searchable transcript cache is text-only, loses event and parent/child semantics, caps messages at 8,000 chars and redacts known secret patterns; OpenCode/Hermes parent IDs become an `isNoise` flag. Disposition: keep as adjacent memory/retrieval prior art only; no direct code/dependency recommendation. Detailed source and evidence: `docs/research/evidence/henryyu333-clue-review-2026-11-24.txt`.

Validation is **not run**: `rtk bun test && rtk bun x tsc --noEmit` exited 127 (`[rtk: No such file or directory (os error 2)]`), so the chained typecheck did not start. A separate typecheck invocation also exited 127; Bun was not on PATH or at the inspected install paths. Existing recall-test fixtures were source-inspected but not executed. No client, user profile, credential or user transcript was accessed.

### First-party Claude Desktop 3P contract correction (2026-11-24)

The current Anthropic guide documents Claude Desktop on a third-party provider, including an organization's own LLM gateway, for Chat, Cowork and Code. Its built-in import is specifically an **Enterprise-admin/source-account migration**: it brings each user's own Chats and Projects plus local Cowork/Code sessions. It excludes cloud Cowork sessions and uploaded/project-knowledge files; other users' data is excluded; memory, personal instructions, Skills and connectors require manual/reconfiguration work, and artifact/file movement is partial. A separate Desktop session ZIP includes Desktop sessions, projects, memory, scheduled tasks, Skills and uploaded plugins but not Claude Code CLI sessions. Consumer export cannot be imported into another personal Claude account. Do not misstate these built-in paths as generic API-key or ChatGPT migration support. Revalidate exact source and client-version behavior in each mode.

Primary references checked 2026-11-24: [provider migration guide](https://support.claude.com/en/articles/18426225-move-from-claude-enterprise-to-claude-desktop-on-a-cloud-provider), [consumer data export](https://support.claude.com/en/articles/9450526-export-your-claude-data), [Cowork surfaces and local/cloud behavior](https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile), [Claude Code CLI migration](https://support.claude.com/en/articles/18466061-move-claude-code-cli-users).

Primary corpus **253/303 reviewed, 50 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **227**, manual-inclusive **236**. Research remains active/incomplete; no migration or full-market coverage is claimed. Next primary candidate: `Hrishikesh2512/Smyrti` (#254), a README-claimed browser-based ChatGPT/Claude/Gemini conversation-transfer project; apply provenance and source gates before treating its claims as evidence. The requested scope remains ChatGPT **Destruction Era** Projects/Section Groups/full Session graph/resources to Claude Desktop 3P Chat, Cowork and Code separately, plus local/self-hosted Claude Code via API key/gateway.


## Candidate #254 — Hrishikesh2512/Smyrti (2026-11-24; provenance screen only)

Smyrti's README claims a local Chrome extension that transfers working memory between ChatGPT, Claude and Gemini web UIs by extracting current state and injecting a continuation prompt rather than moving raw chat logs. This is not evidence of ChatGPT Destruction Era Project/Section/full Session export or Claude Desktop 3P/Claude Code target support.

**Provenance gate stop:** GitHub API reports `license: null`; no LICENSE/COPYING/grant is in the tracked tree. Pinned `master` HEAD `3e91debdbf3350af68eae65cb1ebb4533681c7b3` matches remote HEAD; snapshot has 1 star/0 forks. Per the established gate, no source, tests, manifest permissions, installer or runtime was inspected or run; no code or code-derived design is recommended. Keep as a high-relevance discovery lead with README claims explicitly unverified. Evidence: `docs/research/evidence/hrishikesh2512-smyrti-screen-2026-11-24.txt`.

Primary corpus **254/303 reviewed or screened, 49 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **226**, manual-inclusive **235**. Research remains active/incomplete; no migration, source-level validation or completion notice is claimed. Next primary candidate: `Lain-in-coding/agent-session-grep` (#255), a Rust local-search project; apply license and provenance gate before source review. The user-confirmed destination remains Claude Desktop third-party-provider Chat, Cowork and Code separately, plus local/self-hosted Claude Code by API key/gateway; source remains ChatGPT Destruction Era Projects/Section Groups/full Session graph/resources.


## Candidate #255 — Lain-in-coding/agent-session-grep (2026-11-24)

This is the strongest **adjacent local SessionGraph/search architecture** in the primary list so far, but it is not a ChatGPT → Claude migrator. At pinned `main`/remote HEAD `de2c95d2c93f7453ce5b5ccc169614d3aa7892ee` (Oct 14; GitHub pushed the unchanged ref Nov 8), it has 14 Experimental local coding-agent adapters and two deferred formats; no ChatGPT adapter. The README warns current `main` has unreleased work beyond tagged 0.1.0 and no downloadable binaries. Dual MIT/Apache-2.0 grant and NOTICE are present.

Useful graph model: one stable Session identity with canonical text Messages, source-document fingerprint/length, document/session `MessagePlacement` occurrences, source ordinals/spans/sidechains, and parent `MessageEdge`s for Reply/Retry/Fork/Continuation/Subagent/ToolResult. This captures message-level forks and mainlines only when native parent pointers are exposed; it has no first-class Project/Section or cross-session parent graph. The canonical Message body is plain text; full `ContentBlob`/`ContentOccurrence`/`attachment_ref` appears only in Draft RFC-0001, not current implementation. Tool activity and usage are separate bounded facts but capability support is provider-specific; only Claude Code has native context support in the matrix.

Operationally it is read-only local indexing/search, evidence-aware context retrieval and a deterministic/redacted handoff pack. The pack suggests a target but does not inject/write to it. `asg resume` reconstructs a same-provider native CLI resume command for a supported source session; it is not target-session import. It does not migrate ChatGPT Projects/Sections, Claude Desktop 3P Chat/Cowork/Code, Skills/MCP/plugins/schedules, credentials or files. Session IDs remain path-dependent across machines unless explicit alias relocation is performed. Disposition: **high-value conceptual prior art for Nexus's canonical graph/search, not a direct product dependency or migration-fidelity reference**. Full evidence: `docs/research/evidence/lain-in-coding-agent-session-grep-review-2026-11-24.txt`.

Validation on the pinned source: full workspace `cargo test` exit 0 (including after an online dependency fetch; isolated HOME/XDG), subsequent offline quiet rerun exit 0, `cargo fmt --all --check` exit 0, and workspace Clippy with `-D warnings` exit 0. Initial offline test attempt exit 101 because locked `dyn-stack-macros` was missing; after fetching lockfile dependencies the full suite ran successfully. No user sessions, live provider, app or cross-mode transfer was exercised. Green tests validate this repository, not ChatGPT/Desktop interoperability.

Primary corpus **255/303 reviewed, 48 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **225**, manual-inclusive **234**. Research remains active/incomplete; no migration or completion notice is claimed. Next primary candidate: `Lain-in-coding/AgentSessions` (#256), a separate Rust local-search project; review as a distinct repository rather than assuming it is an alias or duplicate. User-confirmed destination remains Claude Desktop third-party-provider Chat, Cowork and Code separately, plus local/self-hosted Claude Code via API key/gateway; source remains ChatGPT Destruction Era Projects/Section Groups/full Session graph/resources.


## Candidate #256 — Lain-in-coding/AgentSessions (2026-11-24)

`Lain-in-coding/AgentSessions` is a separate public repo but a close code-family snapshot of #255 `Lain-in-coding/agent-session-grep`, not an independent migration system. Pinned `main`/remote HEAD `b1216c976e3cd25661b4dd2f871b7832ef0fb818` (2026-10-07), dual MIT/Apache-2.0 with NOTICE; GitHub reports 1 star, 0 forks and 12 open issues; no tags (`git ls-remote --tags` empty). Its README says 0.1.0 is planned. Comparing the two clones: all 199 AgentSessions crate files exist in #255, 160 are byte-identical, 39 differ, and #255 adds 8 crate files. Both report `fork:false`; common Git ancestry was not asserted. Count this pair as one close product family in market tallies, but keep their per-repository/version evidence distinct.

AgentSessions has a `skills/agent-session-grep/SKILL.md`, but it is a client usage Skill for querying local `asg` through MCP/Robot, not a Skills importer. `.agents/`, `.codex/`, `.codebuddy/` and `.trellis/` are explicitly development workflow assets under the repo's own AGENTS.md. The product remains a local coding-session search/catalog with 14 Experimental provider parsers. Its model is message-level SessionContextGraph, not Project/Section or cross-Session parent hierarchy; current Messages are plain text; there is no ChatGPT provider, Claude Desktop 3P writer, or migration/import/export pipeline.

Documentation discrepancy: README claims community adapters follow a versioned external-process Provider Adapter Protocol, but its contributor guide says RFC-0002 is Draft and the process boundary is planned; current code has only an in-process Rust `ProviderAdapter`, and the schemas directory contains Robot/handoff schemas, not a provider plugin manifest/loader. Do not count it as an existing generic plug-in bridge. Disposition: close sibling to #255 and adjacent local search/Skill example only, no migration code or compatibility claim. Evidence: `docs/research/evidence/lain-in-coding-agent-sessions-review-2026-11-24.txt`.

Validation on the pinned snapshot: `cargo test --workspace --offline --quiet`, `cargo fmt --all --check`, and `cargo clippy --workspace --all-targets --offline -- -D warnings` all exit 0 in an isolated HOME/XDG environment. No real source history or target client was tested. Research scope remains ChatGPT Destruction Era Projects/Section Groups/full Sessions/resources → Claude Desktop third-party-provider Chat/Cowork/Code separately, plus local/self-hosted Claude Code via API key/gateway.

Primary corpus **256/303 reviewed, 47 pending**; supplemental 177; manual additions 21 total/9 pending; combined pending 224; manual-inclusive 233. Next primary candidate: `landywei/my-ex` (#257), described as a local Codex-session MCP memory; apply license/source gate and keep distinct from this Rust family.


## Candidate #260 — NomaDamas/wombat (2026-11-24)

Reviewed at pinned MIT commit `f51431a818bfd9b3f33fc9d26f850d18d52197cf` (`main` remote HEAD and peeled `v0.1.4` match). Wombat advances the breadth survey: 20 local coding-agent readers across JSONL/zstd, SQLite and provider-specific stores, with a normalized user/assistant text mirror, source offsets, local catalog and MinSync search. It is a useful source-inventory/parser and trace-pointer reference, but its canonical model is not adequate for the requested fidelity: `Turn` contains only role/text/time/source offset, while `ParsedSession` has a limited optional subagent parent link and cwd rather than Projects, Section Groups, typed assets, token/usage/tool/event records, schedule/resource/config transfer or target adapters. CLI help confirms no import/export/restore surface. It reads local Claude Code CLI logs, not ChatGPT Projects or Claude Desktop Chat/Cowork/Code, and cannot create Claude Code API-key/gateway sessions. The mirror intentionally filters much provider-specific content; raw trace still requires source logs.

Verification: **74/74 tests passed** (including 15 CLI fixture/e2e, 7 mirror/catalog/MinSync, 51 parser and 1 scoped-sync test; two zero-test harness groups); `cargo fmt --all -- --check` passed; strict Clippy failed only at `src/parsers/pi.rs:177` (`collapsible_match`). No real user sessions, provider app or destination was tested. Treat this as a local ReaderAdapter/search reference, not code adoption or migration-accuracy evidence. Privacy design should distinguish local plaintext mirrors/source paths from any external index endpoint. Full evidence: `docs/research/evidence/nomadamas-wombat-review-2026-11-24.txt`.

Current primary registry: **260/303 reviewed, 43 pending**; next `Rylaispirit/grok-build-manager`. Supplemental net-new queue remains 177 pending; manual candidates 21 total/9 pending; combined unresolved 220 excluding manual and 229 including manual. Research remains active and incomplete; no user ChatGPT export or target restore was performed.


## Candidate #261 — Rylaispirit/grok-build-manager (2026-11-24)

This MIT Grok Build CLI manager contributes UI references for project switching, run controls, Git/worktree review and Harness-scoped MCP/plugin permissions, but does not move data between Harnesses. Its session-list schema is id/date/status/summary; native resume/fork and Markdown export remain Grok CLI operations. No ChatGPT Projects/Section Groups, session graph, typed attachments/events, Claude Desktop Chat/Cowork/Code or Claude Code API-key gateway target is present. Do not count this as migration coverage.

Security finding: despite loopback bind and `shell:false`, `server.mjs` has no auth/Origin/CSRF validation. A synthetic HTTP `text/plain` request carrying `Origin: https://attacker.example` returned 200 and caused a temporary fake `grok` executable to receive `--permission-mode bypassPermissions`. This is server-side CSRF hardening evidence; no browser-specific network-policy test or real Grok execution occurred. The two repository tests do not exercise routes. Treat the app as UI prior art only; the Nexus Memory local daemon needs launch-scoped authorization tokens, strict Host/Origin checks and explicit action confirmations independent of UI.

Validation: 2/2 npm tests pass; official-registry `npm audit --omit=dev` reports zero advisories for one production dependency; `npm ci --ignore-scripts` preserved the lockfile. No actual target app or data transfer tested. Full pinned-source review: `docs/research/evidence/rylaispirit-grok-build-manager-review-2026-11-24.txt`.

Current primary inventory **261/303 reviewed, 42 pending**; next `uniStark/pi-session-find`. Supplemental net-new 177 pending; manual 21 total/9 pending; 219 unresolved primary+supplemental, 228 including manual. Research remains active/incomplete; full cross-Harness research and a real safe migration prototype are not complete.


## Candidate #262 — uniStark/pi-session-find (2026-11-25)

This small MIT Pi extension is adjacent source-reader/UI prior art. It accesses the active Pi branch or all session entries, identifies whether each result belongs to the active branch, and separates user text, assistant text, thinking, tool calls/results and metadata. This makes it a useful clue for keeping branch membership and typed content distinct in the Nexus canonical model. It does not retain branch parent graph, provider metadata, usage, media assets, Project/Section Group, cross-session parent relations or a portable export; `--all` broadens the current session search only. It has no ChatGPT or Claude Desktop/Claude Code adapter. The `meta` category is currently inaccessible in the UI, and NPM package has no test script/test suite. Published code matches GitHub source, although NPM `gitHead` predates the current tag and README differs by badge lines only. Full evidence: `docs/research/evidence/unistark-pi-session-find-review-2026-11-25.txt`.

Disposition: conceptual Pi adapter/event-category reference; no code adoption or migration-accuracy claim. Current primary registry **262/303 reviewed, 41 pending**; next `uwings/session-migration-prompt`. Supplemental net-new 177 pending; manual 21 total/9 pending; combined pending 218 excluding manual / 227 including manual. Research remains active/incomplete.


## Candidate #263 — uwings/session-migration-prompt (2026-11-25)

A manual source-AI prompt and Hermes-style Skill can generate a human-readable six-section handoff (goal, decisions, rejected approaches, progress, constraints, concrete values). Retain this as an optional, explicitly lossy summary fallback when a destination cannot accept native history; separate it from the canonical SessionGraph and include a loss manifest/preview. It does not parse/export existing user or assistant events, projects/sections, parent branches, attachments, tool traces, tokens, Skills/MCP/plugins, schedules or memory state, and does not create a target session. Its “any AI” statement is copy/paste prompt flexibility, not a supported adapter matrix. README's claimed three-session scoring is not reproducible from the repo. License inconsistency (README Apache-2.0 vs LICENSE/GitHub MIT) blocks assuming reuse rights. Full evidence: `docs/research/evidence/uwings-session-migration-prompt-review-2026-11-25.txt`.

Primary registry **263/303 reviewed, 40 pending**; next `windviki/sessiondex`. Supplemental net-new 177 pending; manual 21 total/9 pending; unresolved 217 excluding manual / 226 including manual. Research remains active/incomplete.


## Candidate #264 — windviki/sessiondex (2026-11-25)

SessionDex is a significant adjacent retrieval/service reference: six local readers, incremental parsing, CJK-aware search, original-source locators, REST/MCP and a reusable query Skill. Its normalized model remains a search projection (SessionMeta + role/text/reasoning/tool summary) rather than a portable conversation object; it lacks ChatGPT Projects/Section Groups, parent-session graph, full typed assets/events, usage, resource configuration and any target writer. Its contentless FTS reduces full-text persistence, but metadata/paths and capped excerpts remain in SQLite and full readback depends on original logs.

Security boundary must not be copied blindly. Default token is unset; `POST /api/messages/read` trusts a supplied locator path. Synthetic TestClient evidence read a temporary JSONL file outside configured roots (200); setting token blocks unauthenticated requests, but path provenance is still unbound. If adopting a local retrieval service, require opaque index-issued locators and strict source-root validation; require auth when exposed beyond loopback. `pytest` ran 61 synthetic tests; no arbitrary-locator test exists. Full evidence: `docs/research/evidence/windviki-sessiondex-review-2026-11-25.txt`.

Primary **264/303 reviewed, 39 pending**; next `yoyooyooo/pi-session-history`. Supplemental net-new 177 pending; manual 21 total/9 pending; combined unresolved 216 excluding manual / 225 including manual. Research remains active/incomplete.

## Scope confirmation update (2026-11-25)

The user confirmed Claude Desktop **Chat, Cowork, and Code** are all target surfaces, in addition to local/self-hosted Claude Code via API key or third-party gateway. Treat each as a versioned adapter target and keep account-hosted Cloud sessions separate from local 3P inference sessions: Anthropic documents distinct session stores and differing auth/lifecycle. The Claude Desktop 3P gateway requires Anthropic Messages API streaming and tool-use behavior; a static gateway API key is supported, but the credential must never be written into the portable bundle. The current Desktop docs identify local 3P app data roots and split Chat/Cowork audit logs and attachments from Code session metadata plus transcript files under Claude Code's own store. A Claude-specific first-party importer exists for Claude.ai/local Claude sources only; it is not a ChatGPT import path. Read this as evidence for future adapter design, not an invitation to mutate undocumented app-private files.

Cloud Cowork today runs on Anthropic's servers and stores its sessions/files with the Claude account; scheduled tasks run without the device. Local file access bridges through Desktop while it is open. Claude Code Cloud requires Claude-account sign-in; API-key-only local sessions and Cloud sessions are not interchangeable. Exact source-system inventories, loss ledgers, native writer capabilities, and test fixtures must be validated separately for each mode and version.

Candidate #265 (`yoyooyooo/pi-session-history`, MIT, pinned `334d1e7`) is a Pi-only local reader with bounded JSONL search/read, safe path resolution and native Pi resume. Its 10 unit tests and package check pass, but it has no import/export, session graph, Project/Section structure, typed attachment fidelity, or Claude/ChatGPT adapter. Retain only as a local reader/path-security reference. Primary review progress is 265/303 (38 pending); next primary `Abhiram-Vengala/Continuum`. Research/implementation remain incomplete.

## Candidate #266 disposition — Abhiram-Vengala/Continuum (2026-11-25)

Do not treat this repository as a session importer. It captures visible web-chat text and asks Groq to distill only recent messages into generic decision/fact/constraint/question/assumption MemoryUnit notes; the original transcript and source graph are discarded. It has no ChatGPT Project/Section Groups, section membership, session tree, source attachments/token/model data, schedules, Skills/MCP/plugin resource packs, or Claude Desktop 3P/local Claude Code writer. The UI copies a generated prompt for the user to paste manually.

Quality/security review found a `project_id` schema field with no downstream use; global `get_recent()` SQL and unscoped semantic retrieval can mix sessions; Qdrant is configured as in-memory; the frontend canary exposes no session import. The REST API is unauthenticated with wildcard CORS; direct script launch binds all interfaces. The Claude content script references an undefined helper. The manifest omits `http://localhost:8000` despite a popup fetch, which Chrome's host-permission documentation indicates is likely blocked. The repo has no license file or tests and tracks bytecode plus one SQLite row; row content was not inspected. Static syntax checks pass only; no runtime/browser or import test is claimed. Use only as vocabulary/extraction-flow prior art; do not reuse its code or count it as transfer coverage.

Primary inventory now **266/303 reviewed, 37 pending**, next `Aixand/manager-suite`; supplemental net-new 177 pending; manual additions 21 total/9 pending; combined unresolved 214 excluding manual / 223 including manual. User-confirmed Claude Desktop Chat/Cowork/Code plus local Claude Code API-key/gateway scope is unchanged. Research and a verified migration prototype remain incomplete.

## Candidate #267 — Aixand/manager-suite: adjacent manager architecture, not a cross-Harness importer (2026-11-25)

Pinned Apache-2.0 main `7be93efc46eb1068745904b0764ae77c54aaafe4`. The suite provides five components, but none ingests ChatGPT archive data or writes a Claude Desktop third-party-gateway Chat/Cowork/Code session. Agent Manager's native continuation is same-provider only; OpenCode's native copy path has explicit revision ancestry and branch heads, while retaining limitations around unfinished work, child-session trees, runtime state and external artifacts. Conversation Manager owns new locally retained conversations rather than discovering all provider histories. Resource Managers import Skills/MCP/Prompts into owned stores; actual application delivery remains separate. The published beta notes state stateful rollback is blocked pending a migration-aware adapter.

Prior-art to retain: logical conversation identity separate from native provider IDs; explicit copy/reference lineage; observed revision digests and branch heads rather than implicit merging; operation receipts/idempotency/recovery; strict version/platform adapter checks; and provenance/acceptance/delivery separation for resource planes. Do not reuse the suite as Nexus's migration backend or count it as an import. No Project/Section Group model, ChatGPT reader, Destruction Era transfer, Claude Desktop 3P adapter, plugin/schedule/memory conversion or gateway transfer is established. Claude Code local continuation is a constrained same-provider CLI route, not the requested cross-provider import.

Validation at pinned source: all five component static checks passed. Conversation Manager tests pass 278 with 59 optional skips after correcting macOS temporary-path aliasing (`TMPDIR=/private/tmp`); its first raw run had 7 lexical `/var` vs `/private/var` failures. Prompt Manager: 215 pass. Agent Manager: 862 tests, 1 failure/44 errors/80 skips. MCP Manager: 84 tests, 1 failure/1 skip (temporary Python 3.11 `ensurepip` child `SIGABRT`). Skill Manager: 134 tests, 2 errors/1 skip (mocked `Popen` is not a context manager). See `docs/research/evidence/aixand-manager-suite-review-2026-11-25.txt`; no live provider, account, credential, user session, or cross-Harness transfer was tested.

Primary inventory **267/303 reviewed, 36 pending**, next #268 `Alot1z/agents-handoff`; supplemental net-new 177 pending; manual 21 total/9 pending; unresolved 213 primary+supplemental / 222 including manual. User-confirmed target remains the three separate Claude Desktop 3P modes (Chat, Cowork, Code) plus local/self-hosted Claude Code via API key/gateway. Research is still active/incomplete; no completion notice or real migration is claimed.

## Candidate #268 — Alot1z/agents-handoff: portable handoff Skill, not native session migration (2026-11-25)

Pinned MIT main `bef94b269f5f8353005a536417607b627d22946f` / package `agents-handoff@2.0.7` (npm latest 2.0.7). This is the closest candidate so far to a reusable cross-Harness *handoff Skill*, but the actual engine is a generic JSONL/text parser plus file writer; standard ChatGPT `conversations.json` mapping export fails with exit 4. It writes a linear project/session folder. The transcript itself is not included—only selected text, timestamps/sequence, source path and a raw-file digest—so the output is not a lossless archive or native session restoration. It has no Section Groups, session parent/fork/branch edges, Claude Desktop 3P Chat/Cowork/Code adapter, local Claude Code gateway writer, or resource dependency migration. The documented DSH/SQLite/Claude routes use an external `conversation-vault`; that source adapter is not in this checkout or package. The `federated-merge` command only copies this tool's own handoff format between compatible stores.

Keep limited design ideas: explicit machine-readable/human-readable handoff artifacts; a separate timeline and tool-call text view; source-path/hash provenance; append-by-watermark updates; explicit verification gates; opt-in Skill installation across Claude Code/Codex/generic skill directories. Treat these as a **manual, lossy fallback** only, not as source/target interoperability or cross-Harness migration success.

Local validation: Node 26.7.0/npm 11.19.0. `npm test` 53/53, demo tests 6/6, docs check (18 pages / 103 links) and sample index check (2 sessions) pass. No real app, account, provider, session store, or credential was accessed. Security findings from disposable synthetic inputs contradict broad safety claims: `--project .. --session ..` escaped `HANDOFFS_ROOT`, wrote the handoff files to its parent, and overwrote a sibling sentinel (exit 0 when `<root>/projects` existed; first run with a missing `projects` directory still wrote then exited 1). The writer uses direct non-atomic writes and is outside the runtime permission gate. No secret scanning/redaction exists; a synthetic key marker appeared verbatim in four output files. A same-line-count edit to `timeline.jsonl` still passed `verify` because the content is not hashed/signed. A nested image block, `parentUuid`, message IDs and token usage were omitted from generated payload, while text/tool name remained. Full report: `docs/research/evidence/alotz-agents-handoff-review-2026-11-25.txt`.

Disposition: retain as **handoff UX/schema prior art**, no code reuse and zero native migration coverage until root containment, transactional writes, sensitive-data safeguards, content-authenticated integrity, typed asset/event preservation and real per-target adapters exist. Primary inventory **268/303 reviewed, 35 pending**, next #269 `Aryan-sourcee/context-capsule`; supplemental net-new 177 pending; manual 21 total/9 pending; unresolved 212 primary+supplemental / 221 including manual. User-confirmed scope remains separate Claude Desktop third-party-gateway Chat, Cowork and Code targets plus local/self-hosted Claude Code via API key/gateway; research and prototype remain incomplete.


## Candidate #269 — Aryan-sourcee/context-capsule (2026-11-25)

Pinned `ccad87e557c0787f7ccc1e7f3822d169e4fda79c`. This MV3 Chrome extension is a local, lossy DOM-text capture and prompt-paste handoff—not a session/project migrator. It reads selected currently open web chat pages, emits a linear `context-capsule` messages array with synthetic positional IDs, and does not read ChatGPT exports or native app stores. It has no Project/Section/Destruction Era branch graph; no Claude Desktop 3P Chat/Cowork/Code or local Claude Code gateway writer; no skills/MCP/plugins/memory/schedules transfer. Attachments, tool/usage/model data and original turn IDs/times are not preserved. The viewer displays a capsule; its restore path pastes a formatted transcript into a web chat composer, which is a new prompt rather than historical-session import.

Synthetic source execution: redaction helper detects/replaces a dummy key when called directly, but it is not wired into capture/build/save/export; the dummy marker survives capsule serialization. Native IDs, parent/branch IDs, usage, tool calls and attachment payload were dropped; a provided timestamp is retained by the builder although the real DOM extractor stamps current time. Output flags state context/files/attachments are false. Seven JavaScript files pass `node --check`; there is no automated test package/suite and the pre-release checklist is unchecked. No user data, app, account, API key, live browser or provider was used. No network/runtime privacy claim tested. README says MIT, but the pinned `LICENSE` path returns 404 and SPDX metadata is null, so reuse rights are unverified. Full source/probe evidence: `docs/research/evidence/aryan-sourcee-context-capsule-review-2026-11-25.txt`.

Disposition: low-confidence text-handoff prior art only; do not reuse as a migrator or report it as a session restore. Primary registry **269/303 reviewed, 34 pending**, next #270 `Barmagloth/Joiny-Mnemonic`. Supplemental net-new: 177 pending; manual additions: 21 total / 9 pending; primary+supplemental pending: 211; including manual pending: 220. User scope remains all three Claude Desktop gateway modes plus local/self-hosted Claude Code using API key/gateway. Research remains active and incomplete.


## Candidate #270 — Barmagloth/Joiny-Mnemonic (2026-11-25)

Pinned `0d3ad140563b5ea60e2b7ae14b78e0e1384d7f0b`, package 0.8.0, MIT. This is substantial architecture prior art for a local agent-neutral **memory layer**: SQLite append-only event/artifact ledger with hashes and origin provenance, redaction, internal branch/fork cursors, tasks, snapshots, resume packets, MCP and four live-hook adapters (`claude-code`, `codex`, `opencode`, `openhands`). However, it is not a historical migration engine. The adapters ingest future individual hook/native events; `ingest_native()` accepts one event object and hooks bind external session IDs to Joiny-generated IDs. CLI help has no archive import/export or migration command. It has no ChatGPT archive reader, Project/Section Group mapper, Claude Desktop 3P Chat/Cowork/Code local-store support, or native session writer. Its branch/task hierarchy is Joiny-owned, not recovered from source conversations; its 1,500-estimated-token resume packet is a bounded context handoff, not exact historical replay. Skills/MCP/plugin/schedule transfer is also absent (the MCP server is for Joiny memory itself).

The strongest reusable patterns are canonical event provenance, immutable hash-chained storage, explicit branch fork cursors, idempotent receipts, typed artifact hashes, and separating live hooks from historical adapters. Do not adopt it wholesale or count it as a migration. The project does not launch external agent binaries in its suite. On Python 3.12.4/Pytest 9.2.0, the pinned CI install (`-e . pytest`) reproduced a collection failure because the test imports `joiny_mnemonic_local_llm` but the workflow does not install that plugin. With the optional local-LLM package installed in a disposable venv, full suite result: 486 passed, 8 failed, 1 skipped, 1 xfailed, 314 subtests; failures were a 1,089-line complexity-gate violation, six stale diagnostic-artifact hashes, and a telemetry exception that bubbles through search. Focused ingress/integration tests passed with one xfail. No transcript, API key, provider, or agent binary used. A capabilities check briefly checked only host-level Joiny hook-registration markers in default-home Claude Code/Codex/OpenCode configs (no Joiny hooks found); no transcript or credential content was accessed. The subsequent probe used isolated HOME and the test-generated store/cache/runtime fixtures were removed. Full source and exact outputs: `docs/research/evidence/barmagloth-joiny-mnemonic-review-2026-11-25.txt`.

Disposition: **keep as strong memory-substrate architecture reference; reject as a cross-Harness archive/project/session migrator and do not count a hook integration as restore.** Primary inventory **270/303 reviewed, 33 pending**, next #271 `bhavikkaul/ChatPort`. Supplemental net-new: 177 pending; manual additions 21 total / 9 pending; primary+supplemental pending: 210; including manual pending: 219. User-confirmed scope remains all three Claude Desktop gateway modes plus local/self-hosted Claude Code via API key/gateway. Research remains active/incomplete.


## Candidate #271 — bhavikkaul/ChatPort (2026-11-25)

Pinned `cf8bb7cc3c6cf0202083f99d34a86fa3e61442a0`, Chrome MV3 extension 2.0.0. It performs visible-page text handoff between eight web AI destinations (ChatGPT, Claude, Gemini, Perplexity, DeepSeek, Grok, Copilot, Mistral Le Chat) and lets other webpages serve as generic sources. The site reader covers Gemini/ChatGPT/Claude; other pages rely on heuristic DOM inference, and the README says selectors were not live-tested and older turns must first be loaded by scrolling. Extracted messages are `{role,text}`; synthetic source execution showed IDs, timestamps, project/session/branch IDs and attachment names disappear. The destination gets one continuation prompt in a new chat composer (optionally auto-sent), not imported historical turns. There is no native Project/Section/session graph, Claude Desktop 3P Chat/Cowork/Code or local Claude Code adapter, and no Skills/MCP/plugin/memory/schedule transfer. It is text-only; images/uploads/cards and hidden instructions are not carried.

Five JS syntax checks pass; no automated tests, test directory, package manifest, CI, live-site tests, or LICENSE file are present. GitHub's pinned LICENSE path returns 404 (SPDX null), so code reuse is not cleared. Synthetic `buildPrompt` probe confirms a 401-character text prompt, not structured restore. `pendingTransfer` uses local extension storage and is cleaned on successful fill or a later expired-transfer check; if no matching destination page runs, residual prompt retention is possible (source-based inference). No account, transcript, API key, provider, or live browser was used. Full evidence: `docs/research/evidence/bhavikkaul-chatport-review-2026-11-25.txt`.

Disposition: low-value text-only handoff prototype, not a migration candidate; no code reuse. Primary inventory **271/303 reviewed, 32 pending**, next #272 `ccclucky/session-state`. Supplemental net-new 177 pending; manual 21 total / 9 pending; primary+supplemental pending 209; including manual pending 218. User-confirmed scope remains the three separate Claude Desktop gateway modes plus local/self-hosted Claude Code via API key/gateway. Research remains active/incomplete.


## Candidate #272 — ccclucky/session-state (2026-11-25)

Pinned `0b19c40d8e79f3871dc5d915d1e32192107b75b5`, npm 1.0.0, MIT. It manages `[wip]`/`[pending]`/`[done]` title prefixes by directly updating Antigravity title metadata, DSH title JSON/cache, or appending a Claude Code `ai-title` JSONL event. This is title/state governance, not session content transfer: no ChatGPT/Codex Project/Section reader, Destruction Era conversation tree, attachment or memory migration, Claude Desktop third-party-gateway Chat/Cowork/Code adapter, or API-key/gateway historical session restore. The DSH native tool described in documentation is provided by an external plugin, not shipped here.

The actual adapters were inspected and tested only with disposable fixtures. `npm test` passes 30 assertions, but covers only happy-path fixture writes and invalid CLI arguments; no CI/coverage/live-host tests. Three important gaps were reproduced in a temporary copy: (1) Claude adapter accepts `../../outside` as a session ID and appends outside the configured project directory; (2) DSH fallback renames the globally newest shard despite an unrelated cwd; (3) Antigravity mirror writes swallow errors after the SQLite row has changed, allowing split state. The test script also mutates three tracked fixture files, so it was run on an isolated `git archive` copy. Full evidence: `docs/research/evidence/ccclucky-session-state-review-2026-11-25.txt`.

Disposition: low migration fit; retain only the status-label vocabulary, not its auto-detection or host-storage writers. Primary inventory **272/303 reviewed, 31 pending**, next #273 `cmxau/ai-shelf`. Supplemental net-new 177 pending; manual additions 21 total / 9 pending; primary+supplemental pending 208; including manual pending 217. All three Claude Desktop gateway modes and local/self-hosted Claude Code via API key/gateway remain in scope. Research remains active/incomplete.

## Candidate #273 — cmxau/ai-shelf

Pinned SwiftUI/macOS 26 app `1.0.0` at `cd752daef4220e22edf48f70d0deb5aad61b9b03` (MIT). It browses, previews, searches and resumes local Claude Code, Antigravity, Codex CLI and Gemini CLI histories; OpenCode/Aider/Goose/Amp/Cursor Agent/Copilot are launch-only. Its hierarchy is a local `cwd` folder with flat session rows. There is no ChatGPT/Codex App Project or Section reader, Claude Desktop third-party-gateway Chat/Cowork/Code adapter, local gateway restore contract, cross-Harness archive, branch/parent task model, native session writer, or import of skills/MCP/plugins/memory/schedules. Markdown export is a text projection; stats JSON transfers usage ledger only; Antigravity payload DBs are not decoded.

Build/lint passed on macOS 27.3 / Swift 6.4. Docs say no automated test suite, CI is lint/build only, and Codex/Gemini readers have not been real-session tested. No app was launched and no real user session or provider credential was touched. Disposition: not a migration candidate; retain only as local session-browser UX and host-path reference. Full source review: `docs/research/evidence/cmxau-ai-shelf-review-2026-11-25.txt`.

## Candidate #274 — Codeenk/Skill-Forge

Pinned MIT v1.2.0 `86e61e176b0a19324d0cf16a19bccff511f7f7d5`. A local Skills inventory/composite-Skill orchestration tool: scans known `SKILL.md` roots, has an AI agent select/compose phases, writes a team Skill and `.forge` sidecar, mirrors locally, and hashes roster drift. It is not a historical session/project importer. No ChatGPT/Codex App Project/Section Group or Destruction Era hierarchy, Claude Desktop Chat/Cowork/Code gateway, local API-key session restore, native history format conversion, or MCP/plugin/memory/attachment/schedule transfer. Generated bundles point at source Skills by path rather than shipping those dependencies.

Synthetic POCs showed `install --force` with `name: ../victim` deletes a sibling sentinel outside `--into` after lint rejects the bundle; `audit` reports a curl pattern but exits 0 and misses an `npx` subprocess; `eval` passes a `{}` fixture for a declared JSON shape, with `phases: []`; and `resolve` stages a placeholder while its promised rescan leaves the manifest absent. Six tests pass after installing pytest 9.2.0 in an isolated venv, but several assertions are hard-coded/no-op. Root CI lint fails in an exact-case `Skill-Forge` checkout due to the lowercase frontmatter-name/dirname comparison; actual remote Actions status was not queried. Details and evidence: `docs/research/evidence/codeenk-skill-forge-review-2026-11-25.txt`.

Disposition: reject as a migration engine; retain only Skills inventory, hash/provenance, and filesystem contract ideas for a safer native implementation. Inventory is 274/303, next #275 `DanDavD/Universal-AI-Sync`. Research remains active/incomplete.

## Candidate #275 — DanDavD/Universal-AI-Sync

Pinned `cc143db94405e56f1764135caa9c106c4347c355`: MV3 extension for the ChatGPT web page, Claude.ai, Gemini and Copilot. It scrapes DOM text and either replays it as synthetic prompts in a new destination chat or attaches a simple Markdown role/text transcript. This is a browser context handoff, not a native conversation/session migration. It does not preserve ChatGPT Projects/Section Groups, Destruction Era ancestry/branches, source message IDs/timestamps, tools, attachments, token usage, local Claude Code API-key sessions or Claude Desktop Chat/Cowork/Code. The extension has no skills/MCP/plugin/memory/schedule transfer.

`npm ci` and extension `npm run build` pass, but no test suite or CI workflow is present; no live web session was exercised. README claims MIT, but neither source checkout nor v1.0.1 ZIP has a LICENSE file and the registry SPDX is null, so code reuse is not cleared. Mirror-related worker handlers have no sender in the extension client code. Full evidence: `docs/research/evidence/dandavd-universal-ai-sync-review-2026-11-25.txt`.

Disposition: retain only as browser handoff UX prior art; never claim it restores native sessions or projects. Primary inventory 275/303 reviewed; next #276 `danielrosehill/Rclone-Manager`. Research remains active/incomplete.

## Candidate #276 — danielrosehill/Rclone-Manager

Pinned MIT Rclone manager/plugin `c6074c3690b8f7867ea21e503f8bfdafa171524b`: it creates, backs up, edits and migrates `rclone.conf` remotes, with optional path-prefix rewrites. This is cloud-storage configuration movement, not AI context/history transfer. It has no ChatGPT/Codex App Project/Section, Destruction Era tree, Claude Desktop Chat/Cowork/Code, local Claude Code API-key session, attachment, MCP, plugin, or memory migration. A future Nexus transport adapter could optionally store already-exported files via Rclone, but it would not restore native conversations.

The synthetic config test (dummy token only) confirmed dry-run leaves target bytes unchanged and `--write` creates an exact target backup before applying a path mapping. MIT license is present; no test suite/CI found; Linux/systemd tested, macOS notes untested. Full evidence: `docs/research/evidence/danielrosehill-rclone-manager-review-2026-11-25.txt`.

Disposition: reject as a Harness migrator; keep only explicit preview/consent/backup and optional encrypted transport patterns. Inventory is 276/303; next #277 `darshil2032007/AI-Bridge`.



## Candidate #277 — darshil2032007/AI-Bridge (2026-11-25)

Pinned to `86b73bb4eb6b8b728331c482ba3127d87cbe4976` (2026-06-04; TypeScript/React MV3 Chrome extension). AI Bridge extracts visible browser-DOM text from ChatGPT, Claude.ai, Gemini, Perplexity, and Grok, asks Groq Llama 3.3 70B to produce a short `ContextPackage`, then opens a new target web chat and inserts a continuation prompt. It is context handoff, not a native archive importer. The ChatGPT adapter returns only role/content strings; it does not capture project IDs, Project/Section/“Destruction Era” grouping, conversation IDs, turn IDs, branch/parent/subtask relationships, timestamps, edits, images/files, tool calls, schedules, or usage records. The declared `Message.timestamp?` is not populated by the DOM adapter. Context generation keeps only the first plus the latest 49 messages when longer, caps each message to 2,000 characters for the Groq prompt, and emits a generated summary instead of preserving the source transcript. `executeTransfer` opens a platform homepage and injects text; it does not create/restore an existing target project or session.

Privacy wording needs a caveat: settings/API key are stored in Chrome local storage and there is no AI Bridge backend, but the implementation sends conversation text to `https://api.groq.com/openai/v1/chat/completions`; “100% Local” must not be interpreted as local inference or zero third-party disclosure. The README claims MIT, but no `LICENSE*` file was found in the checkout and the candidate registry SPDX remains null; do not assume code-reuse permission. `package.json` has no test script. On the review host, `npm ci` succeeded; `npm run build` exited 2 at `tsc --noEmit` with widespread `@types/chrome` namespace/redeclaration diagnostics including `src/chrome.d.ts`. The separate bundler path `npm run build:fast` exited 0 and produced popup/background/content bundles, while warning that the CSS `@import` follows Tailwind statements. No browser, account, user transcript, Groq API key, or remote inference request was used.

Disposition: reject as a Nexus migration engine. Retain only the UI handoff concept and clear separation between source-side text extraction and target prompt insertion. It supplies no evidence for Codex/ChatGPT Project or Section restore, Destruction Era hierarchy, Claude Desktop third-party-gateway Chat/Cowork/Code, or local/self-hosted Claude Code API-key session restore. Detailed pinned-source report: `docs/research/evidence/darshil2032007-ai-bridge-review-2026-11-25.txt`.

Inventory: **277/303 primary repositories reviewed, 26 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 203; total pending including manual additions 212. Next primary candidate: `datawithdanny/cache-manager-mcp`. Research remains active/incomplete.


## Nexus Memory — scope lock and staged delivery plan (updated 2026-11-25)

### Confirmed outcome and naming

The user confirmed that Claude Desktop's third-party inference/gateway configuration is in scope for **all three independent surfaces: Chat, Cowork, and Code**. Also in scope: **local or self-hosted Claude Code** configured with an API key or compatible gateway. These are four separately accepted routes: `claude-desktop-3p/chat`, `claude-desktop-3p/cowork`, `claude-desktop-3p/code`, and `claude-code-local`. Do not substitute Anthropic-hosted Claude.ai/Claude Code Cloud for a gateway-configured desktop or local CLI, and do not claim that an API key can restore hosted cloud sessions. The corrected project label is **Destruction Era** (not “Destruction error”); treat it as the user's named project/session until source artifacts prove whether it is a product-native object, a project title, or a workspace/section label. The user has not supplied a personal export, so no account data has been inspected.

Official documentation currently supports this important boundary: Claude Desktop on a configured provider routes inference through that provider and stores its conversation history, projects, and memory on the device; its published Enterprise migration workflow covers Chat, Cowork, and Code but is a Claude-to-Claude one-time import, not a ChatGPT/Codex importer. The Claude Code CLI has separate provider configuration and local session storage; third-party-provider configuration does not expose Anthropic-hosted `--cloud` sessions through `--resume`. Source anchors: [Claude Desktop gateway configuration](https://claude.com/docs/third-party/claude-desktop/configuration), [Claude Enterprise-to-Desktop-on-3P migration guide](https://support.claude.com/en/articles/18426225-move-from-claude-enterprise-to-claude-desktop-on-a-cloud-provider), [Claude Code CLI migration guide](https://support.claude.com/en/articles/18466061-move-claude-code-cli-users), [Claude Code MCP/scopes](https://code.claude.com/docs/en/mcp). OpenAI's current consumer export documents a ZIP with conversations JSON plus other account data, with business-workspace export restrictions; Projects organizes chats, files, instructions, sources and memory, but public docs do not promise a cross-product native import API. Source anchors: [ChatGPT export](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data), [ChatGPT Projects](https://help.openai.com/en/articles/10169521-projects-in-chatgpt).

### Research work plan (the present corpus is not complete)

1. **Freeze the source/target inventory.** Separate ChatGPT web projects, Codex app Projects/threads, local Codex CLI, and other OpenAI surfaces rather than assuming they share an export or persistence contract. Determine exactly what the user's “Section Group” means and whether it is explicit source metadata or a derived taxonomy. Keep Projects, saved sources, files, chats, branches, subagents/tasks, memory, instructions, Skills, MCP servers, plugins, scheduled tasks, artifacts, model/provider settings, usage and credentials as separate record classes. Keep Claude Desktop Chat, Cowork, and Code separate in every matrix and test report; separately model local Claude Code's filesystem sessions and gateway profile. Distinguish direct-documented APIs/imports from private/on-disk reverse engineering and browser UI behavior.
2. **Broad discovery, then deep triage.** Finish the pinned-source review of the 303-repository primary GitHub corpus (277 reviewed; 26 remain), inspect the 177 net-new supplemental leads and 9 unresolved manual additions, and extend searches outside GitHub to official product docs, API/schema references, exporters, issue trackers, releases, package registries and relevant academic/industry work. Deduplicate by canonical repo/package, repository owner and lineage; pin commit/version/date. For high-fit projects inspect implementation, tests, CI, changelog/issues, license, data flows, security boundaries and reproducible behavior—not README-only. Record why strong/weak/unsafe candidates are kept or rejected, and never treat star counts or marketing claims as fidelity evidence.
3. **Publish a capability and loss matrix.** Per source → target surface × data type, classify `native-exact`, `native-transformed`, `sidecar-only`, `prompt-handoff`, `unsupported`, or `not-yet-tested`; link each claim to a pinned test or official source. Include object identity/hierarchy, event order, parent/fork/subtask edges, timestamps/edit/branch state, text/multimodal attachments, tool/MCP/plugin traces, source files/artifacts, token/cost/limits, schedules, memory, Skills, policies, OAuth/API-key references and ownership/workspace boundaries. State per-route measured coverage and unknowns instead of one vague “accuracy” percentage.
4. **Define a versioned canonical archive before expanding writers.** Candidate direction: a local-first, content-addressed bundle (versioned manifest + ordered event records + asset blobs + source/transform/loss ledger). Model harness, product surface, provider/deployment, workspace, project, section/group, chat/session, event/message node, parent/fork/task relation, tool invocation/result, attachment/artifact, memory/instruction/resource/automation, usage observation and provenance as typed entities. Preserve source IDs and raw source fragments when licensing/privacy permit; never invent absent parents, metadata, branch edges, timestamps, token counts, or filenames. Each adapter declares schema/version coverage and deterministic transforms. Keep an untouched source archive and lossless sidecar even when target-native projection cannot represent something.
5. **Implement read-only discovery first, then reversible writers.** CLI/library core before GUI; inspect, validate, diff and dry-run are safe defaults. Source connectors should ingest documented exports/backups first (for example ChatGPT account export), with browser/local-store acquisition gated by an explicit user-controlled profile, visible selection, minimum scope and no cloud upload by default. Target writers must be isolated per profile/mode, version-gated and backup/rollback capable; never edit the original history store. Keep API keys out of the portable bundle and use OS keychain/credential helpers or target-owned secret references. Skill/MCP adapters transfer manifests and configuration references, not secret values or assumptions that providers support an identical protocol.
6. **Prototype a small, honest route set.** First build a synthetic/fixture-backed ChatGPT and Codex reader plus canonical project/session graph; then test each Claude Desktop 3P mode separately and local Claude Code separately. If no supported native session importer exists for a target, deliver a clearly labelled portable project package/sidecar or new-session handoff—not a false claim of native historical restore. Do not write into undocumented Desktop/CLI databases until a disposable-profile test proves the schema, reopen/resume behavior, migration safety and user consent path.
7. **Measure and harden.** Use synthetic edge fixtures and user-supplied sanitized exports only; compare counts, IDs, ordering, graph edges, attachment hashes, references, timestamps, usage fields and loss records before/after. Measure structural coverage by field/object and target reopen success, idempotence, duplicate behavior and rollback. Run parsers on hostile ZIP/JSONL/SQLite fixtures (traversal, symlinks, duplicate IDs, malformed records, large media, truncation), secrets scans, privacy checks, cross-platform tests and a disposable desktop/CLI smoke test. Acceptance: zero silent losses; every unrepresentable field is surfaced; every write has a preview, backup and tested rollback; results and claims are reproducible and version-scoped.
8. **Ship in stages.** A Python/Rust/TypeScript library and CLI plus an open, documented archive format is the first deliverable; platform Skills are thin wrappers around deterministic adapters, not independent implementations. A GUI can follow once core fidelity and rollback are proven. Decide packaging after capability research: macOS `.app`, Windows `.exe`, portable CLI and optional self-hosted service should share one schema and test corpus. Network sync/encryption is an opt-in transport layer, never a dependency for local conversion. README must state for every route exactly what moves, what changes, what is omitted, validation coverage, provider/account requirements, and supported app versions.

### Milestones and gates

- **R0 / research baseline:** finish primary, supplemental, manual and non-GitHub source inventories; provide a dated source index and evidence-backed shortlist with keep/reject rationale.
- **R1 / schema & capability contract:** publish canonical graph/archive draft, taxonomy, threat model, compatibility matrix and fixture/test specification; resolve native-vs-sidecar feasibility per four Claude targets.
- **R2 / read-only prototype:** source importers, graph validator, audit/loss report, redacted dry-run; no target-store mutation.
- **R3 / disposable target trials:** mode-by-mode Claude Desktop gateway and local Claude Code writes only where supported, each with test profile, reopen/resume, backup, rollback and failure injection.
- **R4 / MVP:** stable CLI/library, transparent route guarantees, fixture corpus and docs; no GUI claim until all regression gates pass.
- **R5 / productization:** Skills wrappers and GUI/app packaging, signed releases, migrations/upgrade tests and opt-in encrypted transport.

**Current gate:** R0 remains in progress. The just-reviewed #277 AI Bridge is a lossy prompt-handoff tool and cannot satisfy native project/session migration. No broad compatibility, accuracy rate, or “research complete” claim is made.


### Claude Desktop third-party-mode control surface checked 2026-11-25

The live official Configuration Reference exposes a gateway provider selector (`inferenceProvider: gateway`), gateway base URL and gateway API-key fields, and independent Chat, Cowork, and Code capability settings. It also defines separate retention controls for Chat, Cowork, and Code. `scheduledTasksEnabled` is documented for Cowork and Code, not as a generic Chat transcript feature. This confirms the three Desktop modes have distinct settings/lifecycle surfaces and must be validated independently. **These are deployment/configuration controls, not a public cross-Harness history-import API.** The reference says `chatTabEnabled` and `coworkTabEnabled` are deprecated after 2026-12-17 in favor of `desktopHome`; exact setting names and version gates must be rechecked at implementation time. Source: [Claude Desktop Configuration Reference](https://claude.com/docs/third-party/claude-desktop/configuration) (gateway keys and surface toggles; session-retention and scheduled-task entries). Do not write gateway secrets into a portable archive or copy an API key as ordinary JSON.


## Candidate #278 — datawithdanny/cache-manager-mcp (2026-11-25)

Pinned default-branch HEAD `1609df1e075746e7c5556a2fdd46d38679302781` (2026-06-26, `Add value-explainer SVG to README`), package `@dannyma/cache-manager-mcp@0.1.4`, MIT. It is a local stdio MCP server with a small Zed extension wrapper. Its useful adjacent capability is an agent-authored Markdown checkpoint with an alias/session key and optional flat `project_group`, returned to an agent on a later `resume_or_start`; it also supplies heartbeat/TTL dashboards and Claude Code token/cache cost estimates. It is not a native transcript importer: README explicitly says most MCP clients do not expose stable native thread IDs, exact thread restore is not automatic, and the notifier cannot observe host-client messages, create a chat, prefill it, or know its native ID. Its restart path is “read summary, start a fresh client conversation,” not restoration of the old chat.

The stored “session” is timer metadata (ID, label, cwd, timestamps, a bounded heartbeat/action tail and optional Claude transcript IDs) in `sessions.json`; aliases, titles and one free-form project group are in `aliases.json`; checkpoint content is an agent-supplied Markdown summary. There is no source Project/Section/branch/subtask graph, message/event sequence, image/file bytes, tool trace, MCP/plugin/Skill inventory, schedule import, or target-native writer. The group is a sticky dashboard label, defaulting to the working-directory basename; README lists project-scoped memory stores as future work. Usage/cost collection is a separate Claude Code JSONL reader, not transcript transfer; hard-coded prices are documented as a June-2026 snapshot and may be stale. Its instruction protocol relies on the model calling `resume_or_start`, `heartbeat`, and `checkpoint`; the server itself cannot clear or prefill a client conversation. Generic MCP interoperability is not proof of support across Claude Desktop Chat/Cowork/Code or local Claude Code gateway configurations.

`npm test` passed all 10 chained smoke scripts (including 30 web-dashboard checks, 4 failover checks, MCP, notifier, timers, attribution and project-group behavior). The root Zed Rust shim compiles with `cargo test --manifest-path Cargo.toml`, but reports **0 tests**. No authenticated desktop, transcript, external gateway, or real user data was exercised. Two disposable `/tmp` probes exposed security/integrity caveats: `save_memory` wrote the synthetic summary as a plain Markdown file with mode `0644` and the store directory as `0755` under this review host's inherited umask; and after a deliberately malformed synthetic `sessions.json`, `start_session` returned `ok: true` and rewrote the index from an empty fallback, replacing the malformed bytes without a warning. Source also uses direct, non-atomic JSON writes and no locking while README describes multiple MCP clients sharing a store; concurrent-update loss is a source-level risk, not dynamically reproduced. Startup pruning defaults to 30 days while preserving only the newest checkpoint per session/alias, so it is unsuitable as an archive of all historical checkpoints.

Disposition: **not a Harness migration engine and not an AI-independent universal transfer tool**. Retain only the local, cross-chat checkpoint-memory pattern, alias naming, and project-label UX as optional adjacent MemoryPlane ideas; a Nexus implementation should add explicit graph IDs, backup/atomic writes, encryption/permissions, retention audit, and target-specific validation rather than adopting this persistence layer unchanged. It supplies no verified adapter for ChatGPT/Codex Projects/Section Groups/“Destruction Era” or the four user-confirmed Claude tracks. Detailed evidence: `docs/research/evidence/datawithdanny-cache-manager-mcp-review-2026-11-25.txt`.

Inventory: **278/303 primary repositories reviewed, 25 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 202; total pending including manual additions 211. Next primary candidate: `digiogithub/agentd`. Research remains active/incomplete.


### Cross-Harness fit of candidate #278 (2026-11-25)

`datawithdanny/cache-manager-mcp` is a useful reminder that MCP “memory” is not equivalent to session portability: it stores agent-authored summaries and heartbeat metadata, not source transcript graphs or target-native histories. Its flat `project_group` is a dashboard label, and exact thread restore is explicitly not automatic. It can inform a separate optional checkpoint/MemoryPlane component, but it does not move the user's ChatGPT/Codex project or section hierarchy and cannot replace the four mode-specific Claude acceptance tracks. The source+tests review also found plain-text 0644 handoffs under this host's default umask and silent replacement of a malformed session index in a synthetic probe; treat those as design lessons, not a recommendation to adopt its writer.


## Candidate #279 — digiogithub/agentd (2026-11-25)

Pinned `main` HEAD `0ad5e5f64d5be56f97c82e7e7baf2d97505bd58a` (2026-11-24, `docs: backlog notes plan, mobile phase done in agentd-app`), MIT. This is an active terminal/runtime manager: it launches arbitrary CLI Harnesses (Claude Code, Codex, Pando and other binaries) in PTYs, supports detach/reattach, screen viewing, terminal input, queues/mailbox, per-session task/status views, and a Linux/macOS native desktop client. It can organize running processes with flat project-path aliases and default names such as `codex@webapp`; it does **not** read or restore native ChatGPT/Codex/Claude session archives. Claude CLI/Code inside a managed PTY is a process boundary, not an importer for the tool's native transcript/session format.

Persistence is nuanced: the daemon's live session registry, screen emulator, screen-history/chat view, task list and up-to-100 turn summaries live in memory; the README says daemon restart kills all agent processes and marks session persistence/replay as future work. However, each launched session is assigned a **local raw PTY-output log** at `<state>/logs/<session>.log` (session input may be echoed by the terminal, but this is not a structured conversation transcript, and there is no importer/replay contract). Default cap is 50 MB with one `.1` rollover. The semantic Chat tab reconstructs display items from the live session's bounded `proto.View.Lines`; it is available only for agentd sessions, while zellij/tmux/plain-shell sessions show terminal-only UI. Turn records retain only turn number/outcome/origin/status/timing, bounded to 100 and held in memory; they are not message histories. A per-host versioned `docs.json` document store and SQLite backlog/mailbox are persistent adjacent memory/work-queue features, not cross-Harness conversation archives. Project alias is one path label, not a parent/child Project/Section hierarchy.

The current GitHub Releases page shows **v0.9.0**, released 2026-11-24 from abbreviated commit `0ad5e5f`, matching this checkout. The current README still labels the software “prototype (v0.1, pre-release),” so release-status wording is stale. GitHub CI run #37 passed for this same latest commit on Linux; workflow tests/vets on Linux and only builds/vets on macOS. On this macOS arm64 review host, Go was absent from PATH, so the official Go 1.27.4 darwin-arm64 archive was downloaded to `/tmp`, checksum-verified against go.dev and used without installing globally. `go build ./...` and `go vet ./...` passed. `go test ./...` exited 1 with reproducible Mac test failures: `cmd/agentd/TestShimConflicts` (the own-symlink re-link is rejected; source compares `EvalSymlinks(link)` to a non-canonical executable string), `internal/daemon/TestReviewPromptBeforeSubmitRecheck` (expected a `conflict` guard when a menu appears after paste, got nil), `internal/desktopui/core/TestLaunchFirstPrompt` (first prompt was not executed; Bash displayed `00~echo first-$((2+3))01~` then `00~echo: command not found`), and provision tests that see Homebrew executables appended from `SystemBinDirs` despite their temporary PATH. Each was rerun individually and reproduced. The provision failures are host/test isolation sensitivity; the guard and prompt failures are potential macOS-specific behavior gaps. Do not infer the Linux CI run covers them: the macOS job does not run tests.

Security/portability positives from code and docs: the daemon uses a user-only Unix socket (0700 directory, 0600 socket), session log directory/files use 0700/0600, process identity and ACL checks, and optional SSH/Noise relay with view/operate/admin scopes. The README warns same-user hostile code can inspect process environments/ptrace; session tokens are passed to child environments. Default mode is local; only mailbox message bodies are sent to recipient agents/model providers. Windows is unsupported. The desktop/mobile clients are operational manager frontends (mobile is a separate repository), not history migrators.

Disposition: **strong adjacent multi-agent terminal orchestration prior art, but not a Nexus Memory migration engine**. Retain its alias/path naming, live-session UX, bounded turn/event stream, task/mailbox and permission/relay ideas for a separate OrchestrationPlane. Do not treat its PTY logs or chat-shaped live view as lossless source history, and do not claim Project/Section/branch hierarchy, attachments, token accounting, Skills/MCP/plugin transfer or native ChatGPT/Codex → Claude Desktop/local Claude Code restore. Candidate source: [pinned README](https://github.com/digiogithub/agentd/blob/0ad5e5f64d5be56f97c82e7e7baf2d97505bd58a/README.md); release and CI evidence is recorded in the review ledger.

Inventory: **279/303 primary repositories reviewed, 24 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 201; total pending including manual additions 210. Next primary candidate: `ekpootu/ai-agents-document-os`. Research remains active/incomplete.


### Candidate #279: orchestration versus history portability

`agentd` is useful for keeping **live CLI processes** and peer coordination organized, but it should occupy a different OrchestrationPlane row from Nexus's portable archive/importer. Its session logs are raw terminal output; the live view/turn metadata is in memory; names/project aliases are not native project trees; there is no history import/export. Preserve the distinction between “resume a still-running process,” “replay a local PTY log,” and “restore a target-native conversation”—these are different fidelity levels. The repo's MIT license and recent Linux CI/release make it credible adjacent prior art, but Mac test failures and stale README status need to stay in the evidence ledger.


## Candidate #280 — ekpootu/ai-agents-document-os (2026-11-25)

This MIT document-processing plugin is **not a Harness session migrator**. The pinned implementation copies document Skills between a small set of local Harness folders; it does not import/export ChatGPT/Codex/Claude transcripts, Project/Section trees, branches, attachments, tools, MCPs, schedules, or memory. Static review found an advertised `Universal` target with no dispatch branch, unpinned installer dependencies, and no test/CI paths. Keep only as a low-relevance document-skill/resource-plane reference; do not count its portability claim as session fidelity. Evidence: `docs/research/evidence/ekpootu-ai-agents-document-os-review-2026-11-25.txt`.

Inventory: **280/303 primary repositories reviewed, 23 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 200; total pending including manual additions 209. Next primary candidate: `fishinggoing/agent-continue`. User-confirmed destination scope remains Claude Desktop third-party gateway **Chat, Cowork and Code as separate modes**, plus **local/self-hosted Claude Code**. Research remains active/incomplete.


## Candidate #281 — fishinggoing/agent-continue (2026-11-25)

This is the highest technical-value native migration implementation reviewed so far: deterministic Codex ↔ DeepSeek Harness conversion, separate parsers/writers, explicit lossy mapping/tallies, pending-operation reporting, preview and target-native resume validation. It is **not a universal transfer tool** and does not cover ChatGPT/Codex Projects or Section Groups, Claude Desktop Chat/Cowork/Code, Claude Code sessions, Skills, MCP, plugins, schedules, or independent memory. It rejects DSH child/subagent sessions rather than carrying the hierarchy. It documents concrete fidelity losses instead of claiming a perfect round trip.

Important gate: GitHub reports no license metadata and the pinned tree has no license file. Do not reuse or depend on its code without permission/licensing resolution. The current Node test suite does not pass on this Mac (the local CLI is Windows-centered and its path fixtures are Windows-specific); two contract tests also fail because `docs/HANDOFF.md` is referenced but missing. Isolated Go tests, `go vet`, and the documented race packages pass with a physical macOS temp root. Native harness acceptance is gated and was not run here. Retain as a research/architecture reference only. Evidence: `docs/research/evidence/fishinggoing-agent-continue-review-2026-11-25.txt`.

Inventory: **281/303 primary repositories reviewed, 22 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 199; total pending including manual additions 208. Next primary candidate: `goodappsstore/sessions-box`. User-confirmed scope remains Claude Desktop third-party-gateway **Chat, Cowork and Code as three tracks**, plus **local/self-hosted Claude Code**; `Destruction Era` remains the source target name. Research remains active/incomplete.


## Candidate #282 — goodappsstore/sessions-box (2026-11-25)

Sessions Box is a multi-Harness **local history hub**, not a transcript migrator. The latest v0.1.1 release imports read-only local histories for Codex, Claude Code, OpenCode, Pi, Command Code, Muse, Hermes, Cline and Antigravity into its own SQLite library; it supports search, token/tool analytics, source-native resume, Markdown/JSON transcript export, and atomic backup/restore of its own SQLite database. It has no target-native writer, no ChatGPT Projects/Section Groups, and no Claude Desktop Chat/Cowork/Code adapter. The local Claude Code path is not the Claude Desktop Code surface. The database groups by agent/workspace and flat sessions; it does not preserve a parent/child session graph or Section Group hierarchy.

Latest release v0.1.1 is three commits ahead of the default `main` branch and includes OpenCode v2 schema support; the branch still identifies itself as 0.1.0. Both snapshots build on macOS, but there is no test suite and CI runs only on release tags; successful release packaging is not runtime-ingestion verification. Retain as a high-value local Archive/Inventory/Analytics UX reference, not the migration engine. Evidence: `docs/research/evidence/goodappsstore-sessions-box-review-2026-11-25.txt`.

Inventory: **282/303 primary repositories reviewed, 21 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 198; total pending including manual additions 207. Next primary candidate: `hpeliuhan/agent-session-management`. User-confirmed scope remains Claude Desktop third-party-gateway **Chat, Cowork and Code as three separate modes**, plus **local/self-hosted Claude Code**; source target remains **Destruction Era**. Research remains active/incomplete.


## Candidate #283 — hpeliuhan/agent-session-management (2026-11-25)

GitHub’s description (“Manage Session migration from host to cloud”) is relevant, but the repository currently has no branch commit or source files. The public clone contains only `.git`; GitHub reports an empty public repository, with no license, release, or Actions runs. **Screened out as unavailable—not evidence of working migration functionality.** Reassess only if implementation and license are published. Evidence: `docs/research/evidence/hpeliuhan-agent-session-management-review-2026-11-25.txt`.

Inventory: **283/303 primary repositories reviewed, 20 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 197; total pending including manual additions 206. Next primary candidate: `ironbabatekkral/context-bridge`. User-confirmed target remains Claude Desktop third-party-gateway **Chat, Cowork and Code separately**, plus **local/self-hosted Claude Code**; source project remains **Destruction Era**. Research remains active/incomplete.


## Candidate #284 — ironbabatekkral/context-bridge (2026-11-25)

`context-bridge` is a tiny, MIT, file-based OMP ↔ Antigravity context-pack experiment: read a local session, redact selected secrets, keep a summary and recent user/assistant text within an approximate token budget, then dry-run/optionally inject Markdown into a project rule path. It does not write native sessions and carries neither tool activity, images, full hierarchy nor OMP memory/skills. Its README explicitly says **NOT WORKING END-TO-END**: neither Harness's load of the injected file is verified, and Antigravity target-rule docs conflict.

Two synthetic checks exposed important limits: long metadata can push pack output far beyond the token budget; and a symlinked `.omp` parent let injection write outside the selected project (POSIX test, isolated temp directory). Unit tests pass but test only redaction/pack shaping, not Harness loading or path containment. Keep solely as a design experiment for possible closed-Harness file handoff; do not represent it as a working migrator. Evidence: `docs/research/evidence/ironbabatekkral-context-bridge-review-2026-11-25.txt`.

Inventory: **284/303 primary repositories reviewed, 19 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 196; total pending including manual additions 205. Next primary candidate: `JaekunE2/agent-cli-hub`. User-confirmed target remains Claude Desktop third-party-gateway **Chat, Cowork and Code separately**, plus **local/self-hosted Claude Code**; source target remains **Destruction Era**. Research remains active/incomplete.


## Candidate #285 — JaekunE2/agent-cli-hub (2026-11-25)

Agent CLI Hub is a Windows-local terminal dashboard for Claude Code/Codex CLI/Cursor and shells. It searches flat local CLI histories, previews outputs and resumes a hit in its original workspace; it is not a session/project migrator. `hub/searchindex.js` indexes only Claude Code CLI JSONL plus Codex CLI rollout JSONL; filters tool/attachment content and truncates each message; no ChatGPT Projects/Sections or Claude Desktop 3P Chat/Cowork/Code reader/writer, cross-Harness archive, branch/parent graph, or native destination writer. The gzip search cache is locally ignored by Git but not encrypted. MIT; pinned main `427656e329133ba600e1991b2b6d60971e0ae950`; Windows 10/11; no test files/workflows or test script (`npm --prefix hub test` reports missing script). Keep only as an adjacent local session-search/operations UX reference. Evidence: `docs/research/evidence/jaekune2-agent-cli-hub-review-2026-11-25.txt`.

Inventory: **285/303 primary repositories reviewed, 18 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 195; total pending including manual additions 204. Next primary candidate: `joesnason/Zeppeli`. User again confirmed all three Claude Desktop third-party-gateway modes (Chat, Cowork, Code) as distinct acceptance tracks, plus local/self-hosted Claude Code; source target remains **Destruction Era**. Research remains active/incomplete.

## Claude Desktop third-party gateway scope refresh — 2026-11-25

Current Anthropic configuration docs list the gateway inference provider and separately describe Chat, Cowork, and Code surfaces. The currently documented Claude Enterprise -> Claude Desktop on 3P import is Claude-origin only: it copies a user's own chats/projects and locally stored Cowork/Code sessions, while project file contents, cloud Cowork/Code sessions, connectors and some other data do not automatically move; memory, personal instructions and Skills require manual work. Its session ZIP is unencrypted and does not include Claude Code CLI sessions. The separate CLI guide says local CLI sessions/settings use their own store/configuration. Unified Claude may combine the Chat/Cowork UI, but acceptance remains per mode. This source-native import is not a ChatGPT/Codex importer. Full scoped source notes: `docs/research/evidence/claude-desktop-3p-scope-confirmation-2026-11-25.txt`. Official sources: https://claude.com/docs/third-party/claude-desktop/configuration ; https://support.claude.com/en/articles/18426225-move-from-claude-enterprise-to-claude-desktop-on-a-cloud-provider ; https://support.claude.com/en/articles/18466061-move-claude-code-cli-users.


## Candidate #286 — joesnason/Zeppeli (2026-11-25)

Zeppeli is a local-first AI coding-agent CLI (Ollama, or cloud/self-hosted models via LiteLLM) that records its own sessions. It is a useful single-Harness history/event-log format reference, not a migration tool: one process starts one UUID, persists version-1 session JSON plus a separate event JSONL, and cannot resume the saved context after process restart. The record has cwd/title, flat history and flat runs; there is no Project/Section/Section Group, parent/child/branch graph, external importer/exporter, target writer, or ChatGPT/Claude Desktop adapter. System instructions/Skills and multimodal image payloads are not preserved in session history. The provider field stays "ollama" even for LiteLLM cloud endpoints and omits base URL/key. The separate event log can contain prompt preview, full tool results, and local-model reasoning text; it is plain local JSONL with no observed encryption or retention/redaction. Keep only as a native session/event design reference. Evidence: docs/research/evidence/joesnason-zeppeli-review-2026-11-25.txt.

Pinned eb191939e96dec774a2caaf865388f9d83b42a94, MIT. Full declared-dependency suite in an isolated venv: 328 passed, 2 skipped because direnv is not installed; this validates internal persistence, not cross-Harness transfer. No live model/provider/account or user session was exercised. Primary inventory: 286/303 reviewed, 17 pending; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 194; total pending including manual additions 203. Next primary candidate: Luodian/tmux-autoname-agent-sessions. Scope remains Claude Desktop third-party gateway Chat/Cowork/Code as distinct tracks, plus local/self-hosted Claude Code; source target remains Destruction Era. Research remains active/incomplete.



## Candidate #287 — Luodian/tmux-autoname-agent-sessions (2026-11-25)

This small MIT tmux plugin detects interactive Claude Code/Codex processes, reads only the first user prompt (up to 400 characters) from their local session files, optionally sends that excerpt to OpenRouter for a short window title, and caches the title. It changes tmux window names; it does not transfer or restore session history, Projects/Sections, branch/task ancestry, attachments or tools. The Claude Desktop stream-json helper is explicitly excluded. The GitHub About text mentions history search/status summaries, but the pinned source tree only implements window renaming. Keep only as adjacent process-detection/session-label UX prior art. Review: docs/research/evidence/luodian-tmux-autoname-agent-sessions-review-2026-11-25.txt.

Pinned 13c13a880b3630b0e6d7644173692ba2d25fbb48, MIT, 0 stars/forks, no releases or workflow runs. Makefile lint passes both Bash syntax checks; no automated test suite exists. Isolated fake-process probe confirmed the first-prompt-only title fallback and no API call without a key. Primary inventory: 287/303 reviewed, 16 pending; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 193; total pending including manual additions 202. Next primary candidate: lweiss01/holistic. Scope remains Claude Desktop third-party Gateway Chat/Cowork/Code as separate tracks plus local/self-hosted Claude Code; source target remains Destruction Era. Research remains active/incomplete.

## Candidate #288 — lweiss01/holistic (2026-11-25)

Holistic v0.7.2 (MIT; pinned release commit `e698632106e40bc2c75f35592b6e5694eafe34e1`) is a valuable repo-scoped cross-agent memory/handoff and optional observability reference, not a native session migration engine. Its `SessionRecord` stores summarized work/checkpoints; `HolisticState` has one active session, flat pending work and a last handoff, with archived Holistic JSON records and simple `relatedSessions` identifiers—not raw messages/tool/attachment/token payloads or a parent/child session DAG. It has no ChatGPT Projects/Sections/Section Group importer, Claude Desktop third-party-gateway Chat/Cowork/Code session reader/writer, or local Claude Code transcript exporter. Claude Desktop is represented by a combined Claude/Cowork MCP adapter; Claude Code uses separate lifecycle hooks. Opt-in `refs/holistic/state` sync moves Holistic state, not destination-native sessions. Retain as architecture/reference prior art; do not claim migration fidelity.

The user-confirmed Claude Desktop 3P Chat, Cowork and Code modes remain separate acceptance lanes, in addition to local/self-hosted Claude Code; unified UI does not merge acceptance. Candidate test suite: one macOS temp-path canonicalization failure under default `/var/folders` vs Git `/private/var/folders` paths (329 passed, 1 failed); with canonical `TMPDIR`, all 330 pass. Tests are internal fixtures, not live Harness transfer. Full source/security/test evidence: `docs/research/evidence/lweiss01-holistic-review-2026-11-25.txt`.

Inventory: **288/303 primary repositories reviewed, 15 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 192; total pending including manual additions 201. Next primary candidate: `NodeJSmith/cass`. Research remains active/incomplete.

## Candidate #289 — NodeJSmith/cass license-screen exclusion (2026-11-25)

Stopped at the license gate. The repository's “MIT License (with OpenAI/Anthropic Rider)” expressly withholds rights from OpenAI/Anthropic and their representatives and defines use to include analysis, indexing, execution and testing. It is not approved for source review, testing, integration, or reuse without the copyright holder's express prior written permission. GitHub marks the repository archived (2026-07-05); the repository page reports zero stars/forks and no releases. This is **not a source-code or product-functionality verdict**. A clone and CodeGraph index had been started before the license was checked; after discovery, the checkout and index were deleted. No build/tests or user session/API data were used. License-only evidence: `docs/research/evidence/nodejsmith-cass-license-screen-2026-11-25.txt`.

Process correction: screen license before cloning/CodeGraph/source inspection; for explicit OpenAI/Anthropic exclusions, record only the license screen, remove checkout/index, and proceed to the next eligible candidate unless written permission is provided. The user-confirmed scope remains Claude Desktop third-party-gateway Chat, Cowork and Code as separate acceptance tracks, plus local/self-hosted Claude Code; source target remains **Destruction Era**.

Inventory: **289/303 primary entries screened, 14 pending source/review decisions**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 191; total pending including manual additions 200. Next primary candidate: `obakeng-develops/better-agent`. Research remains active/incomplete.

## Candidate #290 — obakeng-develops/better-agent (2026-11-25)

Better Agent (`bta`) is a high-value **narrow** local history / pairwise handoff reference: it imports local Claude Code and OpenCode histories into a local SQLite/FTS index and creates deterministic, previewable prompt packs to start the other native CLI. It does not rehydrate a native session in the destination; it starts a new CLI session with a pack (default max 8,000 chars). `bta resume` reopens a session only in its original CLI. Its typed related/continuation/handoff/fork/subagent links are useful lineage metadata, but are not a strict parent-controlled tree. Source normalization drops or truncates some content; `--full` remains character-capped and the rendered transcript omits thinking/full tool results. It has no ChatGPT/Codex source, no Claude Desktop third-party-gateway Chat/Cowork/Code support, and no Skills/MCP/plugins/memory/schedule/API-key migration. The `project` field is a path, not a Project/Section hierarchy.

Current checkout HEAD `95c42d65e7b273d27855ecab9447c168fc755196` (2026-11-20), project version 0.8.0; tag v0.8.0 exists though GitHub Releases shows no release assets. The repo has no `LICENSE` file/license metadata (`NOASSERTION`); do not reuse source pending permission. Candidate unit tests: initial uninstalled-source invocation 44 passed/1 package-metadata failure; after installing into an isolated venv with isolated HOME/BTA_HOME, 45 passed (0.64s); `bta --version` output `bta 0.8.0`. No real session or CLI was used. Full evidence: `docs/research/evidence/obakeng-develops-better-agent-review-2026-11-25.txt`.

User-confirmed Claude Desktop 3P Chat, Cowork and Code remain separate acceptance tracks, plus local/self-hosted Claude Code; source target remains **Destruction Era**. Inventory: **290/303 primary candidates reviewed, 13 pending**; supplemental net-new 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 190; total pending including manual 199. Next primary candidate: `oreid-zd/pi-search`. Research remains active/incomplete.


## Confirmed target coverage and current research status — 2026-11-25

The user explicitly confirmed all three Claude Desktop third-party-gateway surfaces are in scope: **Chat, Cowork, and Code**, each kept as a separate compatibility/acceptance lane. **Local or self-hosted Claude Code** remains a fourth, separate lane. This is confirmation of desired coverage, not proof that arbitrary gateway inference is supported equally in each mode; mode-specific behavior, local/cloud session storage, credentials, and product features must be verified independently. The source project name remains **Destruction Era**.

Candidate #291 `oreid-zd/pi-search` is a single-Harness Pi local session search/export/view/resume utility, not a cross-Harness migrator. It searches Pi JSONL-derived Markdown and resumes by invoking Pi against its original JSONL; it does not preserve a transferable session graph or Projects/Section Groups and has no ChatGPT/Codex or Claude target adapter. Its regression suite has 21/22 passing tests; a same-second mtime incremental-export assertion fails reproducibly on this macOS/Bash environment. License is `NOASSERTION`; source reuse is gated. Review: `docs/research/evidence/oreid-zd-pi-search-review-2026-11-25.txt`.

Inventory: **291/303 primary candidates reviewed, 12 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 189; total pending including manual additions 198. Next primary candidate: `outerarc-ai/agent-sweep`. Research remains active/incomplete.


## Candidate #292 — outerarc-ai/agent-sweep (2026-11-25)

`agent-sweep` is an Apache-2.0, zero-dependency local residue inventory/cleanup tool, not a cross-Harness session or project migrator. Its eight registry descriptors cover Claude Code CLI, Codex CLI, Cursor, Windsurf/Devin, Trae, Copilot CLI, Aider, and Goose/OpenCode. It enumerates path-shaped units, reports filesystem metadata, and offers a guarded scan → plan → reverify → trash/restore workflow. It does not parse or export/import conversations, preserve session graphs/Sections, or move Skills/MCP/plugins/memory/schedules/keys. Claude Code CLI paths are not Claude Desktop Chat/Cowork/Code; Codex CLI state is not ChatGPT Project/Section Group state.

Review found a critical safety defect in `src/core/trash.js`: `restore` records destination conflicts but deletes the entire batch whenever there are no missing sources, even with conflicts. A synthetic-temp reproduction confirmed the existing replacement survives but the only original trashed payload is deleted. The 112-test suite, lint, 24-check selfcheck, and package check all pass, but existing conflict tests fail to assert that the source copy remains. Keep only as safety-UX/registry design reference; do not use as a destructive foundation until corrected. Full evidence and captured outputs: `docs/research/evidence/outerarc-ai-agent-sweep-review-2026-11-25.txt`.

Inventory: **292/303 primary candidates reviewed, 11 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 188; total pending including manual additions 197. Next primary candidate: `ozankasikci/agent-browser-manager`. User-confirmed scope remains Claude Desktop third-party-gateway Chat, Cowork, and Code as three separate tracks, plus local/self-hosted Claude Code; source target remains **Destruction Era**. Research remains active/incomplete.


## Candidate #293 — ozankasikci/agent-browser-manager (2026-11-25)

This MIT macOS Rust CLI/MCP tool is a high-value **adjacent browser-identity transfer** reference, not a Harness conversation or project migrator. Its explicit profile export/import moves one ABM-managed Chrome identity between Macs in authenticated age-encrypted archives, including available cookies, site storage, IndexedDB and extension data; it never imports a user's normal Chrome profile. Tests use synthetic profiles/credentials only. `cargo fmt`, clippy, the default test suite, and the opt-in `scripts/verify.sh --chrome` completed successfully here; the opt-in integration passed real headless Chrome round trips for synthetic cookies/storage with no listeners left afterward. No physical second-Mac transfer or real-site login was tested. The export does not move MCP/agent config, API keys, Skills, memory, Projects/Sections, transcripts or session trees; device-bound and OS-protected credentials may require reauthentication. Keep browser context as a separate, explicitly sensitive data plane. Review: `docs/research/evidence/ozankasikci-agent-browser-manager-review-2026-11-25.txt`.

Inventory: **293/303 primary candidates reviewed, 10 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 187; total pending including manual additions 196. Next primary candidate: `pixle-codes/scrollback`. User-confirmed scope remains Claude Desktop third-party-gateway Chat, Cowork and Code as three separate tracks, plus local/self-hosted Claude Code; source target remains **Destruction Era**. Research remains active/incomplete.


## Candidate #293 — ozankasikci/agent-browser-manager (2026-11-25)

This MIT, macOS-only Rust CLI/MCP tool is a high-value **adjacent browser-identity transfer** reference, not a Harness conversation/project migrator. It explicitly exports/imports an ABM-managed Chrome profile between Macs in authenticated age-encrypted archives, including available cookies, local storage, IndexedDB and extension data; it does not read the user's regular Chrome profile. The opt-in live Chrome tests passed here using temporary signed-out profiles and synthetic cookies/storage; no real account or physical second-Mac transfer was tested. Device-bound cookies, Keychain passwords, passkeys and MFA may require reauthentication. Its MCP/agent config is generated for manual merge, not transferred; Projects/Section Groups, conversation graphs, Skills, API keys, memory and schedules are out of scope. Keep browser identity as a separate sensitive data plane from chat/session migration. Review: `docs/research/evidence/ozankasikci-agent-browser-manager-review-2026-11-25.txt`.

Inventory: **293/303 primary candidates reviewed, 10 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 187; total pending including manual additions 196. Next primary candidate: `pixle-codes/scrollback`. User-confirmed scope remains Claude Desktop third-party-gateway Chat, Cowork, Code as three separate tracks, plus local/self-hosted Claude Code; source remains **Destruction Era**. Research remains active/incomplete.


## Candidate #294 — pixle-codes/scrollback (2026-11-25)

This MIT, zero-dependency Python CLI builds a local SQLite FTS5 index across OpenCode, Claude Code CLI and Codex CLI history. It is a read-only source/index/search tool, not an importer/exporter or destination-native session migrator. Its flat session/doc rows omit Project/Section hierarchy and parent/child/branch edges, and it does not transfer Skills, MCPs, API keys, attachments or scheduled work.

Important privacy finding: the index includes reasoning and tool inputs, but `index_path()` relies on umask/default SQLite modes instead of enforcing private permissions. In a synthetic-only test with a 0755 HOME and umask 022, `~/.local/share/scrollback` was mode 0755 and `index.db` 0644; a fabricated private marker appeared in the database. This demonstrates conditional local-account disclosure risk, not exposure of this user's actual data (which was not accessed). The 32-test suite passes, with two ResourceWarnings; no live history was read. Retain as parser/FTS search prior art only, and require explicit permission/redaction plus enforced owner-only storage before adopting this pattern. Review: `docs/research/evidence/pixle-codes-scrollback-review-2026-11-25.txt`.

Inventory: **294/303 primary candidates reviewed, 9 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 186; total pending including manual additions 195. Next primary candidate: `rengaryang/agent-bridge`. User-confirmed scope remains Claude Desktop third-party-gateway Chat, Cowork and Code as three separate tracks, plus local/self-hosted Claude Code; source target remains **Destruction Era**. Research remains active/incomplete.


## User scope confirmation and official gateway check — 2026-11-25

The user confirmed Claude Desktop third-party inference must cover **Chat, Cowork, and Code as three independent acceptance lanes**, plus **local/self-hosted Claude Code** as a fourth. Current official Claude docs say Desktop third-party inference is configured inside the app (Developer → Configure Third-Party Inference) or deployed by an administrator, while local Claude Code uses its own gateway settings. Official Desktop 3P docs explicitly place Chat, Cowork, and Code requests on the configured gateway; Anthropic-hosted cloud sessions are not part of that gateway deployment. This confirms the requested scope is technically plausible, not that cross-Harness session/project migration exists. No account, API key, or real session was accessed.

The gateway contract requires Anthropic Messages API `POST /v1/messages` with streaming and tool use; model discovery is optional. Tool/system/cache fields must be preserved or translated. Keep Chat, Cowork, Code, local CLI, and hosted-cloud sessions separate in compatibility and acceptance records. Source evidence: `docs/research/evidence/claude-desktop-third-party-mode-scope-2026-11-25.txt`; official docs: https://code.claude.com/docs/en/llm-gateway-connect and https://claude.com/docs/third-party/claude-desktop/gateway.


## Candidate #295 — rengaryang/agent-bridge (2026-11-25)

Local-first preview CLI reads Pi, OMP and Codex CLI session history, builds a canonical event graph and loss-aware `.acx` archive, supports a review-required semantic context-only profile, and writes version-pinned Pi/OMP native storage sessions. Codex remains handoff-only. It does not read ChatGPT exports/Projects/Sections, and it has no Claude Desktop Chat/Cowork/Code or Claude Code adapter; it does not migrate Skills/MCP/plugins/memory/schedules/attachments. Archive mode is not lossless: selected branches are projected to a linear native context; tools become inert history; provider/runtime state is not resumed. Native verification proves storage cold-open/context projection, not a real model/TUI next turn. The label-based no-LLM checkpoint extraction can miss unlabelled prose and requires human review.

High-value design prior art: canonical source graph plus loss report, selected-leaf handling, read-only snapshots, fail-closed unknown semantics, conservative context-only profile, and exact native storage cold-open proof. Important security caveats: best-effort redaction is explicitly not a guarantee; `.acx` and native sidecars are unencrypted and can contain paths/code/custom content; attachments are not bundled; the macOS sandbox denies network and external writes but still allows reads. Source is v0.3.0 preview, 0 stars/forks and one commit in the official repository; no root LICENSE or package license metadata was found, so SPDX remains `NOASSERTION` and source reuse is gated. Full source/test review: `docs/research/evidence/rengaryang-agent-bridge-review-2026-11-25.txt`.

Observed on macOS arm64: `npm run setup:native` exit 0; `npm run check` exit 0 (6 files, 73/73 tests); `npm run format:check` exit 0; three `npm audit` checks against registry.npmjs.org exit 0 with 0 advisories at review time. All fixtures were synthetic, no model/API key or user session was touched. Root registry mirror returned 404 for audit; verification was repeated successfully against the official npm registry.

Inventory: **295/303 primary candidates reviewed, 8 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 185; total pending including manual additions 194. Next primary candidate: `rucnyz/agents-sesame`. User-confirmed destination scope remains Claude Desktop third-party-gateway Chat/Cowork/Code as three separate lanes, plus local/self-hosted Claude Code; official docs confirm Desktop gateway inference but not cross-Harness migration. The source project name remains **Destruction Era**. Research remains active/incomplete.


## User confirmation — all Claude Desktop modes included (2026-11-25)

The user answered that the scope includes **all three Claude Desktop modes: Chat, Cowork, and Code**. Treat them as distinct acceptance lanes; test each mode's third-party gateway path, session store/discoverability, import/write capability, assets, resume behavior, and cloud/local boundary independently. A shared client or gateway does not imply shared session semantics. Local/self-hosted Claude Code is a separate fourth lane. Anthropic-hosted Cloud remains outside the API-key/gateway objective absent separate authorization. The source project is **Destruction Era**.

## Candidate #296 — rucnyz/agents-sesame (2026-11-25)

Disposition: a narrow local search/preview/resume TUI, **not a cross-Harness migration engine**. The Rust/Tantivy index holds flat session rows and returns control to each source CLI. It has no ChatGPT export/Project/Section importer; no Claude Desktop third-party-gateway Chat/Cowork/Code reader/writer; no local Claude Code output writer; and no Skills/MCP/plugin/memory/schedule/attachment/API-key transfer. `ase relocate` moves Claude Code local storage between project path encodings and is not a harness converter.

Pinned snapshot `3d3ab396a08a96c0a8a9f063eb2ba31c17069fcb` (v0.1.2); MIT declared by Cargo metadata/README, but no license text file. Source review identifies flat/partial content extraction and no Project/Section/branch/subagent graph. Synthetic-only repros: relocation to a missing target exits 0 and writes cwd to a nonexistent directory; with fake HOME 0755 and umask 022, local index 0755 and Tantivy segment files 0644 contain a fabricated marker. No real session/HOME was read. `cargo test --locked` passed 75; build/fmt passed; strict Clippy `-D warnings` failed with 12 style lints (exit 101). Retain as search UX prior art only; fix permission enforcement/transactional relocation before recommendation; verify license text before reuse. Evidence: `docs/research/evidence/rucnyz-agents-sesame-review-2026-11-25.txt`.

Inventory: **296/303 primary repositories reviewed, 7 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 184; total pending including manual 193. Next primary candidate: `sabaiway/agent-workflow-kit`. Research remains active/incomplete.


## Candidate #297 — sabaiway/agent-workflow-kit (2026-11-25)

Disposition: **adjacent curated-project-memory and portable-Skill reference; not a session/project-hierarchy migrator**. The MIT v1.3.0 kit installs a Claude Code Skill and launcher glue, then asks an AI agent to inspect a repository and populate `AGENTS.md` + `docs/ai/` handover, plan, state, decisions, issues, changelog/history and enforcement files. Its project continuity is a narrative memory projection, not a lossless transcript/event archive. No ChatGPT Project/Section or session graph, parent/child/fork/subtask, attachments, tool/usage, MCP/plugin/API key/schedule, Claude Desktop third-party-inference Chat/Cowork/Code writer, or Claude Code transcript import. Codex gets a symlink; Devin Desktop gets a workflow; other `AGENTS.md` readers require manual integration. It is AI-driven, not the user's requested no-AI automatic transfer engine.

Pinned checkout `0037c39a44d5aca692bf2d231c4c4637d6365c6e` (2026-11-24), version 1.3.0; local MIT LICENSE verified. Candidate helper tests pass 44/44 and syntax/isolated installer checks pass. The suite does not test `bin/install.mjs`, launchers, bootstrap, or Harness integrations. A fake-HOME synthetic reproduction showed `install-launchers.sh` replaces a user-owned Codex skills symlink without `--force` or backup, although its regular-file branch leaves a user file alone. Keep as curated-memory design reference; do not adopt launcher unmodified. Full review: `docs/research/evidence/sabaiway-agent-workflow-kit-review-2026-11-25.txt`.

Inventory: **297/303 primary candidates reviewed, 6 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 183; total pending including manual 192. Next primary candidate: `SamiAhmadBeg/Continuity`. Research remains active/incomplete.


## Candidate #298 — SamiAhmadBeg/Continuity (2026-11-25)

Disposition: **lossy browser context handoff reference only; not a migration engine**. The MIT v1.0.0 MV3 extension scrapes rendered text from ChatGPT/Claude/Perplexity/Gemini/Copilot browser pages and injects a last-Q/A handoff into a target input. It does not import/export full conversation records, ChatGPT Project/Section data, stable session IDs or branch/parent/subtask graphs, tool calls/results, usage, assets, MCPs/Skills/plugins, API-key gateways, schedules, or native target sessions. A `claude.ai` browser match does not provide Claude Desktop Chat/Cowork/Code or local Claude Code adapters. No AI-free complete transfer; optional summarization is direct OpenAI/Anthropic only.

Pinned `9ffd4e3538ae569d5433ef3911ba069d259d12a1` (2025-07-30); GitHub lists 3 commits, 0 stars/forks and no releases; root MIT LICENSE verified. No upstream automated test suite; its `test.html` reports simulated success. Three JavaScript syntax checks passed. Synthetic-only VM evidence: popup initialization fails because code expects a missing `status` DOM id; API key input ids mismatch; clear-all removes storage but the live background Map still returns the deleted context; the LLM-summary toggle writes `usellm-summary`, and background never reads settings. Mocked fetch (no network) showed the background attempts a hardcoded OpenAI summary request containing a synthetic marker even when settings say disabled. Manifest does not grant the API host permissions; Chrome requires host permissions for service-worker cross-origin fetch. `chrome.storage.local` is used for contexts and keys, without retention/encryption layer. Review: `docs/research/evidence/samiahmadbeg-continuity-review-2026-11-25.txt`.

Inventory: **298/303 primary repositories reviewed, 5 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 182; total pending including manual 191. Next primary candidate: `Seroliya/session-history`. Research remains active/incomplete.


## Candidate #299 — Seroliya/session-history (2026-11-25)

Disposition: **high-value read-side transcript/lineage prior art; not a migration engine**. The MIT v1.1.0 Skill/Node CLI reads DeepSeek Harness, Codex and local Claude Code sessions into a typed turn/item view, with refs, tool calls/results, compaction, lineage, subagents, and bounded output. It has no ChatGPT adapter, Projects/Sections, Claude Desktop third-party-gateway modes, destination writer/import, asset bytes, schedules, credentials/MCP/plugin transfer or full target resume. It does not move Destruction Era into Claude.

Pinned commit `83ca41a9cdfa9778aac7536f4e466e9c2faa201d` (2026-11-02), local MIT license. `npm test` exits 1: the synthetic Claude suite passes 21/21; installer sandbox tests pass 10/11, with idempotence assertion failure caused by macOS `/var` vs `/private/var` canonicalization. Additional synthetic DSH multi-frame and Codex parent/fork smoke probes pass. Most important: default cache writes raw, unredacted text into `index.json` and gzip digests (fake HOME 0755, umask 022 yielded cache dirs 0755/files 0644), even though CLI stdout is redacted. `--no-cache` avoids it. Also, installer and uninstaller treat any symlink in a reserved skill slot as installer-owned; a fake-home test showed a user symlink replaced/removed without backup or `--force`. No real sessions, homes, or API/network data used. Full review: `docs/research/evidence/seroliya-session-history-review-2026-11-25.txt`.

Inventory: **299/303 primary candidates reviewed, 4 pending**; supplemental 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 181; total pending including manual 190. Next primary candidate: `Shivala-08/contex-landing-page`. Research remains active/incomplete.


## Candidate #300 — Shivala-08/contex-landing-page (2026-11-25)

Disposition: **local-first context-card handoff prior art; not a session/project migrator**. The catalog repo is a static landing page. Its explicit product link leads to the separate MIT `context-shifter` macOS app + Node CLI. The app captures selected/pasted text, asks a model to synthesize one six-section card and leaves target insertion to copy/paste. The CLI recognizes ChatGPT and Claude official `conversations.json` exports, but projects both into flat speaker-labeled text and then a model-generated card.

Fidelity boundary: ChatGPT parsing follows only `current_node` ancestry; images/files/audio become `[non-text part]`, and branch graph, message IDs, timestamps and metadata are not serialized. Claude export parsing keeps only sender/text textual blocks, omitting IDs/timestamps and non-text. The card's local capture date is not the original session chronology. Neither repo contains ChatGPT Project/Section migration, Claude Desktop third-party gateway Chat/Cowork/Code session import/write, local Claude Code native session import/write, MCP/Skill/plugin/memory/schedule transfer, attachment bundling or native target resume. Model-based extraction is required; the app's Anthropic endpoint is hardcoded to `api.anthropic.com`. This is not the user's no-AI exact transfer requirement.

Pinned sources: landing `1153db84921a420acf61512b0079a613b4ad4cfc`; linked app `cc78f2bfaeb84732cc9932fb176785d29651180b` (MIT verified). Linked app `rtk npm test --prefix cli` passed **142/142**, no real exports, keys or model calls. The fixture/unit tests do not measure round-trip/semantic accuracy. Full source-level notes: `docs/research/evidence/shivala-08-contex-landing-page-review-2026-11-25.txt`.

Inventory: **300/303 primary candidates reviewed, 3 pending**; supplemental net-new catalog 177 pending; manual additions 22 total / 9 pending; primary + supplemental pending 180; total pending including manual additions 189. Next primary candidate: `steam-soda/skill-manager`. Research remains active/incomplete.


## Candidate #301 — steam-soda/skill-manager (2026-11-25)

Disposition: **prompt-only Skills inventory/update helper; not a migration adapter**. The repository contains a single `SKILL.md`, with no `LICENSE` (GitHub `licenseInfo` is null), code, or upstream test suite. Its static frontmatter check passed. The prompt claims to check `~/.claude/skills/` and `~/.agents/skills/` on session start, but contains no hook or executable guarantee; it misses other Harness-specific roots and cannot migrate Projects/Sections, sessions, MCPs, plugin configuration, memory or schedules. Reuse is license-gated.

The prompt delegates to `npx skills check`, `npx skills update -y`, and `npx skills add ... -g -y`. `-y` skips confirmations; its update path has no prescribed diff/backup review. The referenced CLI's check is currently read-only at v1.9.0 (4/4 targeted tests pass), after a real upstream `check`-mutates-skills regression was fixed in PR #2605; the candidate pins no minimum version, and `skills check` still reports anonymous telemetry by default.

The linked `vercel-labs/skills` CLI was separately reviewed as manual addition #23: MIT v1.9.0; supports Skills file placement across 79 advertised agents with project/global scope, source/commit/hash lock metadata, and symlink/copy fan-out. It is valuable Skills-plane prior art, not session or MCP/plugin migration. Full unit suite: **1,421 passed, 4 failed / 1,425 tests** under Node 26.7.0 and exact pnpm 12.18.0; typecheck, format check, and isolated check test pass. Full evidence: `docs/research/evidence/steam-soda-skill-manager-and-vercel-skills-review-2026-11-25.txt`.

Inventory: **301/303 primary candidates reviewed, 2 pending**; supplemental net-new catalog 177 pending; manual additions 23 total / 9 pending; primary + supplemental pending 179; total pending including manual additions 188. Next primary candidate: `Thespaceblade/Fantasy-Basketball-Manager`. Research remains active/incomplete.


## Candidate #302 — Thespaceblade/Fantasy-Basketball-Manager (2026-11-25)

Disposition: **adjacent MCP/Skill and side-effect-safety pattern; not a Harness migrator**. The unlicensed, domain-specific ESPN CLI exposes 15 operations, an optional MCP server, and one Agent Skill. It calls API Anything's local saved browser session (no ESPN API key), not Claude Desktop third-party inference or native session storage. No license metadata; code reuse is gated.

Useful design reference: MCP writes are disabled unless the server starts with `--allow-writes`; preview uses a dry run and validates the exact host/path/body; the write manager checks fresh state and constraints, records intent before one send, reads back state, and never retries an ambiguous send. The gate is server-wide rather than per-call human consent. Synthetic unit tests pass 45/45 with the optional MCP extra installed. A synthetic fake-HOME probe also found `transactions.local.jsonl` mode 0644 under mode-0755 directories/umask 022 and persisted a fake player ID: the journal needs explicit private permissions. No live ESPN session/data used.

It has no Project/Section/session import, cross-Harness adapters, MCP server config transfer, memory/schedule migration, or API-Key gateway. Its best contribution is a design pattern for a **separately authorized, previewed, journaled, readback-verified mutation**. Full source/test notes: `docs/research/evidence/thespaceblade-fantasy-basketball-manager-review-2026-11-25.txt`.

Inventory: **302/303 primary candidates reviewed, 1 pending**; supplemental net-new catalog 177 pending; manual additions 23 total / 9 pending; primary + supplemental pending 178; total pending including manual additions 187. Next primary candidate: `Yybe/Agent-Janitor`. Research remains active/incomplete.


## Follow-up 303 (2026-11-25): Candidate #303 and Claude Desktop scope

Primary GitHub search rows are now 303/303 source-reviewed; the 177 net-new supplemental rows and 9 manually queued source reviews remain open, so overall research is not complete. See `docs/research/evidence/yybe-agent-janitor-review-2026-11-25.txt` and `claude-desktop-scope-confirmation-followup-2026-11-25.txt`.

Yybe/Agent-Janitor is an adjacent storage-hygiene reference, not a migration tool. Its read-only scan, dry-run, trash/restore and DB proof patterns are useful; its Codex GC runs `git gc --prune=now`. In an isolated synthetic repo, that command removed an unrelated pre-existing unreachable blob while preserving the main branch. The tool's ref filter does not bound the objects Git GC may prune; make this whole-repository side effect explicit and require an unreachable-object safety check/backup before any real `--apply`.

The user confirmed Claude Desktop Chat, Cowork and Code all belong in scope. Preserve these as three acceptance lanes plus a fourth local/self-hosted Claude Code lane. Current Anthropic docs support all three Desktop modes routing through a third-party gateway, but they do not establish cross-Harness import/resume compatibility. Cloud Cowork/session execution is distinct from gateway-backed local Desktop Code and cannot be inferred from an API key.


## Follow-up 304 (2026-11-25): Current Claude Desktop 3P model + candidate #304

User scope remains three distinct Desktop lanes (Chat, Cowork, Code) plus local/self-hosted Claude Code CLI. New current Anthropic docs materially refine the earlier legacy model: 3P Desktop stores Chat/Cowork local session state under a separate `Claude-3p` app root, scoped by device `ant-did` and organization rather than an Anthropic account UUID; Code session records and `~/.claude/projects` transcripts remain a separate store. Unified Claude may hide the Chat/Cowork selector, so use capability/session type rather than UI labels. See `docs/research/evidence/claude-desktop-3p-storage-import-current-2026-11-25.txt`.

A first-party 3P import/export baseline now exists, but is managed-feature gated and not cross-Harness: it can import claude.ai chats/projects and local Cowork/Code sessions, or move a Desktop archive to another device under same-OS/same-organization constraints. It leaves out secrets, connector sign-ins, tool permissions, some Code attachments/environment values and other state. The archive is unencrypted. Third-party API-key Code sessions are not exposed by the Enterprise Compliance API; do not claim that API gives a full migration source.

Candidate #304 `XDUwt/claude-desktop-history` is a MIT-licensed legacy macOS account-switching helper, not the 3P gateway adapter. Its source assumes standard `Claude` paths and account UUID folders; its README's Chat-cloud-only statement is false for current 3P Desktop Chat. Its direct value is historical metadata/body separation and safety workflow. Synthetic fake-HOME review confirmed happy paths but also reproduced collision overwrite/merge, false-positive resume verification, missing backup-directory failure, `--full` success with exit 1, and world-readable plaintext backup under umask 022. Full result: `docs/research/evidence/xduwt-claude-desktop-history-review-2026-11-25.txt`.

Research remains active: 303 primary rows reviewed, 177 supplemental pending, 8 manual source reviews pending (185 total).
## Follow-up 305 (2026-11-25): Candidate #305 `rpeck/claude-explorer`

Candidate #305 `rpeck/claude-explorer` (Apache-2.0, `CLA.md`, pinned commit `bdb6434731de39b63b4adbdbc27e120cb1228dbe`, 26 stars / 3 forks on 2026-11-25) is a high-value **read-only local archive, search/viewer, Markdown/PDF exporter, and 5-tool FastMCP server** (`list_sessions`, `list_projects`, `get_session_outline`, `get_messages`, `export_session`), not a cross-Harness session/project migrator or Claude Desktop 3P writer. Its four source adapters cover `CLAUDE_AI` (fetched from `claude.ai` via browser-captured session cookies into `~/.claude-explorer/credentials.json` `0o600`, not API-key/3P local Chat), live `CLAUDE_CODE` (`~/.claude/projects`), live local/remote `CLAUDE_COWORK` (defaulting to standard `platformdirs.user_data_path("Claude")`, not `Claude-3p`; zero `Claude-3p`/`ant-did` references in code), and archive-copied `CODEX` (`~/.codex`, supporting `.jsonl.zst` and home-path redaction).

Critical boundaries for Nexus: zero ChatGPT export/Projects/Sections/Skills/MCP/plugin/memory/schedule support; zero destination writers; both `CLAUDE_CODE` and `CLAUDE_COWORK` return `None` from `archive_sync()` (live-read only, so upstream pruning removes sessions); and `backend/cowork_reader.py` truncates single content payloads above 1 MB (`_CONTENT_BYTE_LIMIT`) while `CoworkAdapter` disables projects and branching (`has_projects=False`, `branch_flag=False`). High-value Apache-2.0 patterns worth adopting: `SourceDescriptor` capability flags, Cowork `audit.jsonl` + sibling sidecar parsing caveats, two-stage `backend/write_gate.py` (corrupt-config safe mode + cloud-sync folder write block bound to resolved `data_dir`), Codex read-only source isolation with atomic archive copies, and `SECURITY.md` / `TESTING.md §0` verification discipline.

Automated suite verification (`scripts/check.py` via `/Users/vincentadamnemessis/.local/bin/uv` after `npm ci` in `frontend/`) exited 0: `ruff`, sources JSON, `compileall`, parallel `pytest` (3,983 passed, 12 skipped), serial `pytest` (5 passed, 1 skipped; 248 disk test files = 247 default-collected + 1 serial benchmark), `tsc`, `eslint`, `vitest` (103 files / 1,002 tests passed), and `react-doctor` (66/100, 261 warnings, 0 gating errors). Raw stderr still emitted 215 unhandled MSW request errors (`GET /api/bookmarks`: 111, `GET /api/preferences`: 104) and 504 React `act(...)` warnings; Playwright E2E (137 files) was not run, and no live account, local user profile, or gateway was accessed. Full report: `docs/research/evidence/rpeck-claude-explorer-review-2026-11-25.txt`.

Research remains active: 303 primary rows reviewed, 177 supplemental pending, 7 manual source reviews pending (184 total).
## Follow-up 306 (2026-11-25): Candidate #306 `ericblue/cowork-explorer`

Candidate #306 `ericblue/cowork-explorer` (MIT, pinned commit `293e35da4fa5bc9ba41e804e6ce513fda279dcad`, 2026-03-05, 3 stars / 1 fork, no upstream tests/CI) is a narrow, macOS-only, zero-dependency Python CLI (`cowork`) and stdlib HTTP viewer (`cowork_web.py`) for early standard Claude Desktop Cowork sessions — not a cross-Harness migrator and not safe for Claude Desktop 3P. It hard-codes `~/Library/Application Support/Claude` (`claude-code-sessions` and `local-agent-mode-sessions`) with zero `Claude-3p`, `ant-did`, Windows/Linux, ChatGPT, Codex, Projects/Sections, Skills/MCP/plugins/memory/schedules, or target-writer support.

Source audit and isolated synthetic fake-HOME + ephemeral `127.0.0.1` probes (no real user profile, credentials, or gateway accessed; logged in `.verified306/logs/candidate-synthetic-tests.json`) confirmed `py_compile` passes on both Python files and happy-path CLI/web reads work, while reproducing seven concrete defects/security issues: (1) `parse_audit` silently drops `tool_result` blocks, `parent_tool_use_id` subagent turns, user image blocks, and non-`success` results; (2) `stats --format json` ignores `--format` and prints plain text; (3) `cmd_serve` passes only `claude-code-sessions` (`DEFAULT_DATA_PATH`), raising `FileNotFoundError` when sessions live solely in `local-agent-mode-sessions`; (4) `cmd_migrate` symlinks `claude-code-sessions -> local-agent-mode-sessions`, conflating current Desktop Code and Cowork/3P-Chat roots; (5) `unarchive`/`unarchive-all` rewrite `local_<uuid>.json` in place without backup, confirmation, or atomic writes; (6) `/api/file/<sid>` adds `os.path.dirname(f)` for every `userSelectedFolders` entry and checks `real_path.startswith(os.path.realpath(d))` without a path separator, reproducing both HTTP 200 sibling-file exposure in the parent directory and HTTP 200 prefix-collision directory escape (`.../home-evil/prefix-escape.txt`); and (7) `/api/file/<sid>` serves `.html` with `Content-Type: text/html`, `Content-Disposition: inline`, and no CSP (same-origin XSS vector). Full report: `docs/research/evidence/ericblue-cowork-explorer-review-2026-11-25.txt`.

Research remains active: 303 primary rows reviewed, 177 supplemental pending, 6 manual source reviews pending (183 total).
