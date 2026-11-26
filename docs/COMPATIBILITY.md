# Cross-harness capability map (evidence snapshot: 2026-11-23)

This is an initial vendor-doc matrix, not the completed 50–100 harness survey. “Project,” “session,” “memory,” and “cloud” are product-specific nouns; treat them as separate object types until an adapter proves the mapping. User-confirmed first-phase Claude destinations are local/self-hosted Claude Code and Claude Desktop client-managed sessions in third-party inference mode; Anthropic-hosted Claude Code Cloud remains a distinct non-target surface unless separately requested.

## Product structures that must not be conflated

| Harness/surface | Native organization evidenced | Migration implication |
|---|---|---|
| **ChatGPT Projects** | Hosted project workspaces with project-scoped chats/files/instructions and selectable memory behavior; branched chats can coexist with their source chat. Account export provides chat history in JSON and other data. [Projects](https://help.openai.com/en/articles/10169521-projects-in-chatgpt) · [Export](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data) | Parse export graphs, but do not assume the export is a restorable Project or contains its full sidebar/section index. Project and memory metadata need a separate source adapter or must be marked unavailable. |
| **Codex app/CLI** | Projects bind threads to a host/workspace; tasks, side chats and subagents are separate work streams. A first-party app snapshot (`schemaVersion: 2`) exposed Project records (ID/path/host) separately from sidebar `sections` records (`sectionId`, name, `itemKeys`); item keys were source-qualified (`codex` vs `chatgpt`). [Codex platform](https://developers.openai.com/blog/codex-as-a-platform) · [Goals](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) · [Plugin architecture](https://developers.openai.com/plugins/concepts/plugins) | Model project containment and sidebar Section membership as independent edges, not `Project → SectionGroup → Session`. Current account snapshot exposed only local Project records; that is runtime evidence for this desktop view, not proof hosted ChatGPT Projects are absent. |
| **Claude.ai Projects** | Legacy/current Projects group project chats, knowledge and instructions. The 2026 Claude Code Projects beta changes the shape: one coordinator conversation routes work to parallel cloud-session threads; it has a Library, project instructions/memory, repositories/files and scheduled tasks. Anthropic says its own eligible legacy-project move can carry instructions, files, full chat history and scheduled tasks; this is not an external importer. [Projects](https://support.claude.com/en/articles/9517075-what-are-projects) · [Claude Code Projects](https://code.claude.com/docs/en/claude-projects) | Keep classic Projects and the new Code Projects beta as separate versioned types. Do not flatten the coordinator, worker-thread/session, Library, project memory and scheduled-task relations into one transcript. No general ChatGPT/Codex-to-Project import is documented; beta access is account/plan gated. |
| **Claude Code local CLI** | Local sessions are saved continuously per working directory in JSONL under `~/.claude/projects/`; records include messages, tool calls/results, request data and metadata, with adjacent subagent/tool-result/file-history data. The format is explicitly internal and version-unstable; `/export` is a rendered text export. [Sessions](https://code.claude.com/docs/en/sessions) · [.claude directory](https://code.claude.com/docs/en/claude-directory) | Current prototype writes a local, version-tagged session bundle. Treat JSONL as a tested implementation projection, not a supported import API; preserve full source events/attachments and check token/cost data separately. API-key auth is appropriate for local CLI operation, not hosted Cloud sessions. |
| **Claude Desktop on third-party inference (3P)** | Current official docs explicitly describe the full Chat/Cowork/Code experience on a configured inference provider and local conversation storage. Chat/Cowork state, transcripts, uploads/outputs, audit logs and project memory live in `local-agent-mode-sessions/`; Code session metadata is in `claude-code-sessions/`, while Code transcripts are in Claude Code’s `~/.claude/projects/`. Developer → Configure Third-Party Inference reads Desktop’s own provider configuration, not `ANTHROPIC_BASE_URL`/`settings.json`; an active gateway removes Anthropic-hosted cloud environments and Remote Control. The 3P importer copies Claude.ai history/projects and local earlier Cowork/Code sessions, not arbitrary ChatGPT JSON. [3P overview](https://claude.com/docs/third-party/claude-desktop/overview) · [local data](https://claude.com/docs/third-party/claude-desktop/data-storage) · [gateway](https://code.claude.com/docs/en/llm-gateway-connect) · [import](https://claude.com/docs/third-party/claude-desktop/import) | Treat Chat, Cowork, Code, local/self-hosted CLI and Anthropic-hosted Cloud as separate, versioned surfaces. The docs now provide mode-specific storage and source-specific import facts, but no generic ChatGPT/Codex writer. Require exact Desktop version/OS plus a disposable native-discovery/resume test before direct writes. Gateway/API credentials are connection secrets, never portable history. See `docs/research/evidence/claude-desktop-3p-current-review-2026-11-22.txt`. |
| **Claude Code Cloud** | Hosted sessions run in isolated cloud environments; sessions can be opened, archived, shared, or teleported back to a matching local checkout. CLI handoff is one-way (Cloud → local); creating a new `--cloud` session does not import a local transcript. Cloud scheduled tasks are separate saved configurations with schedule/API/GitHub triggers. Cloud sessions/Projects require claude.ai account authentication; API-key/Console authentication alone is not sufficient. [Cloud sessions](https://code.claude.com/docs/en/claude-code-on-the-web) · [Scheduled tasks](https://code.claude.com/docs/en/routines) | Do not promise migration into Anthropic-hosted Cloud under API-Key auth. A desktop-local-session handoff or Remote Control continuation is a narrower, native Anthropic path, not an external archive importer. Keep account auth, Cloud Project, session, environment, and scheduled-task adapters separate. |
| **Gemini CLI** | Session history is project-hash-scoped and records conversation/tool calls/token usage; it has session resume, manual chat checkpoints, configurable retention, and optional file-system checkpoints. [Sessions](https://geminicli.com/docs/cli/session-management/) · [Checkpointing](https://geminicli.com/docs/cli/checkpointing/) | Project hash, retention policy, snapshot chain and session contents are separate data. A transcript alone does not restore the Git shadow checkpoint. |
| **Cursor** | Local Agent rules/skills/MCP/plugins coexist with Cloud Projects that have coordinator chats, delegated/side chats, task boards, project context store and personal store. Plugin formats have portable Agent Plugins components and Cursor-specific rules/agents/commands/hooks. [Projects](https://prod.cursor.com/docs/agent/projects) · [Plugins](https://cursor.com/docs/plugins) · [Skills](https://prod.cursor.com/docs/skills) | Separate local IDE sessions from Cloud Projects; preserve store scope and side-chat links. Skills are more portable than project stores or lifecycle hooks. |
| **Cline** | A task is a self-contained session with conversation, code changes, tool runs, costs/tokens/time and Git-based checkpoints; tasks can be resumed across editor sessions. [Task management](https://docs.cline.bot/core-workflows/task-management) | Capture both transcript and checkpoint metadata; replaying text cannot reconstruct the original file snapshots or tool execution state. |
| **GitHub Copilot CLI** | Local sessions can sync to the user’s GitHub account and resume with full history; session sidebars, checkpoints, skills, MCP, agents and hooks are distinct. [Session data](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/chronicle) · [Configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) | Account-synced sessions differ from purely local files. Respect opt-out and organization policy; do not migrate authentication state. |
| **OpenCode** | Project/location-scoped Sessions expose `parentID`, fork metadata, paginated typed messages, user file attachments (base64 + MIME + source), agent/skill attachments, tool input/content/metadata, costs/tokens, permissions, time and revert. Official API documents complete projected transcript export/import; child imports require existing parent. HTTP transfer routes are experimental; live event stream is volatile across disconnects. [API](https://opencode.ai/docs/api) · [CLI commands](https://opencode.ai/docs/cli/commands) · [pinned transfer implementation](https://github.com/anomalyco/opencode/blob/011f9043e8a90dc9a1ac42fb1181486dd4d13b71/packages/core/src/session/transfer.ts) | High-value harness-native adapter; not universal schema. Export snapshot should anchor fidelity/reconciliation; test version-pinned API, file bytes, branch/fork metadata and sanitization before relying on destination import. Preserve source IDs and separately report fork-boundary/time normalization loss. |
| **Zed Agent / External Agents / Terminal Threads** | Zed groups threads by project and maintains a restorable Thread History. External-agent sessions can be imported through ACP from configured agents; imported threads are archived, sessions without a working directory are skipped, and support is integration-dependent (the docs currently call out Cursor and Gemini CLI as unsupported). Zed Agent, ACP External Agents, and Terminal Threads have distinct config/auth ownership. [Agents](https://zed.dev/docs/ai/agents) · [Thread history/import](https://zed.dev/docs/ai/parallel-agents) · [External Agents](https://zed.dev/docs/ai/external-agents) | Treat Zed as a possible bridge/container for specific ACP integrations, not a universal session converter. Preserve provider/runtime ownership and source session IDs; do not infer that ACP imports reproduce arbitrary transcript graphs, checkpoints, media, tool state, or hosted Projects. |
| **Kiro IDE / CLI / Web / Mobile** | Kiro documents one shared harness exposed through several clients. Project `.kiro/` data includes Specs, Steering, agents, hooks, MCP, skills and workflows; local CLI sessions are per-directory in a local database, with V3 ZIP and 2.x JSON archives plus JSON save/load scripts. Cloud sessions live in an account-side store and cannot use local `/chat save`/`load`. The CLI dashboard groups/sorts sessions and distinguishes derived child sessions; Web supports repo groups, workflows, cloud sessions and scheduled automations. [Architecture](https://kiro.dev/docs/how-kiro-works/) · [Session management](https://kiro.dev/docs/cli/chat/session-management/) · [Configuration scopes](https://kiro.dev/docs/cli/chat/configuration/) · [Kiro Web](https://kiro.dev/docs/web/using-the-agent/) | One of the strongest documented native import/export candidates in this survey, but archive schema and cross-harness fidelity still require an actual versioned client test. Keep local V3 archives, CLI 2.x JSON, cloud sessions, workflow-step trees and Web automations as separate transfer types; a Markdown conversation export is not a full session/project backup. |
| **Warp Agent / Warp Terminal / Oz Automation Platform** | Local Warp conversations can optionally sync as snapshots; cloud-agent runs are separately stored and expose run/session links. Handoff carries transcript, attachments and tracked/untracked workspace changes for supported directions; cloud Claude Code/Codex runs can use provider API credentials stored as managed secrets. Oz APIs expose run IDs, status, resolved config, session link, follow-ups and cancellation; `parent-run-id` creates cloud orchestration lineage. Scheduled runs start fresh sessions. [Cloud conversations](https://docs.warp.dev/agents/local-agents/cloud-conversations/) · [Handoff](https://docs.warp.dev/platform/handoff/) · [API](https://docs.warp.dev/factories/api-and-sdk/) · [Claude Code harness](https://docs.warp.dev/factories/harnesses/claude-code/) · [Scheduled agents](https://docs.warp.dev/platform/triggers/scheduled-agents) | A strong candidate for a cloud-run target/bridge, not an arbitrary session importer. Local-to-cloud handoff is for Warp Agent sessions, not third-party local CLI sessions; Cloud-to-local forks without applying workspace patches. Warp Agent Memory is a gated research preview, not an open universal memory migration API. Distinguish Warp-hosted Claude Code from Anthropic Claude Code Cloud. |
| **Continue IDE extensions / Continue CLI (`cn`)** | IDE Chat treats history as session context and starting a new session clears it. The CLI autosaves local JSON sessions under `~/.continue/sessions/`, has a `sessions.json` index, supports `cn --resume`, `cn ls --json`, and full-history forks. Current `main` source writes UUID/title/workspace/history plus optional usage/mode/model fields; the separate index has title, date, workspace and message count. The source's remote-session provider currently returns an empty list because the Hub integration was removed. Config uses global/workspace rules and MCP; MCP works in Agent mode. [IDE Chat](https://docs.continue.dev/ide-extensions/chat/how-it-works) · [CLI TUI](https://docs.continue.dev/cli/tui-mode) · [MCP](https://docs.continue.dev/customize/deep-dives/mcp) · [session source](https://github.com/continuedev/continue/blob/main/extensions/cli/src/session.ts) · [history source](https://github.com/continuedev/continue/blob/main/core/util/history.ts) | The CLI's local JSON session store is a concrete adapter candidate, but the storage/schema evidence is version-specific source, not a promised stable import format. The reviewed fork path creates a new session from copied history; preserve parent/fork lineage explicitly in Nexus sidecar. The current code path is local-only; IDE export/import, attachments, schedules, and portable Skills remain unverified. |
| **DeepSeek Harness (DSH)** | The MIT-licensed TypeScript harness uses an append-only typed Session event log; model messages are projections. Durability is a separate plugin seam (JSONL/Zstandard or SQLite), and Workspace records group Session IDs. Fork captures a prefix/inherited count but the general `fork()` API does not guarantee a source-session parent edge; `parentSession` is principally a subagent creator relation, so ancestry requires origin-aware interpretation. An optional experimental plugin imports **DeepSeek website** export ZIPs into a chosen Workspace. [Session model](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/session.md) · [Session fork semantics](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/core/session/README.md) · [Persistence](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/session/session-persistence/README.md) · [Workspace](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/workspace/workspace/src/entity.ts) · [DeepSeek importer](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/experimental/deepseek-chat-import) | Valuable architecture and importer reference, not a general external-harness importer. Its own exporter adapter accepts DeepSeek format v3, selects one displayed branch (discarding other branches), and has explicit file/token/tool-state losses. A same-day, unanswered report alleges a valid official export ZIP fails; local synthetic descriptor ZIPs passed, so status is unresolved and must be tested with a real export. |
| **Google Antigravity App / CLI** | Projects associate conversations; CLI can resume by ID or workspace cache and fork a conversation into another project. CLI can import App-originated threads, cloning history, context and tool trajectories. App side panels expose subagents, background tasks, goals, artifacts, documents, links and uploads. Skills, rules, MCP and plugins are supported; App Automations and in-conversation `/schedule` are distinct. [Resume/import](https://antigravity.google/docs/cli/commands/resume/) · [Projects](https://antigravity.google/docs/cli/projects/) · [Side panel](https://antigravity.google/docs/side-panel/) · [Automations](https://antigravity.google/docs/commands/automation) | Strong native App→CLI continuity, but this is not evidence of arbitrary ChatGPT/Codex import or a portable session archive. Preserve the project ID, workspace-keyed recent-session cache, fork edges, subagent/task/artifact relations and automation definitions separately; each automation run starts a fresh conversation. |
| **Pi coding agent** | Session JSONL v3 tree under ~/.pi/agent/sessions/, grouped by working directory; per-project configuration is carried separately in .pi resources. Reviewed core docs/source do not evidence a native Project or Section object. | Preserve the event tree, active branch, parent-session provenance, compaction/context edits, usage, media, and extension state separately from cwd, Skills, MCP, settings, and extensions. Do not claim schedule or project restoration without a target-specific test. |

## Portable capability layers

### Third-party adapter evidence (not a vendor contract)

The pinned `skillsynchq/txcript` implementation can read ChatGPT's live account through Codex-managed OAuth credentials and private ChatGPT endpoints, but only with `auth_mode: "chatgpt"`; its format guide says a ChatGPT API-key login and the official `conversations.json` export are not accepted. It maps the active branch into its common transcript model, refuses writes back to ChatGPT, and writes to local harness stores such as Claude Code. Its `cowork_remote` adapter is also read-only. This is useful source-adapter evidence, not a supported OpenAI export API or a Claude Cloud importer. The separate Skillsync CLI exposes additional hosted sync behavior; do not conflate that product with the open-source `txcript` library. [Pinned ChatGPT adapter docs](https://github.com/skillsynchq/txcript/blob/2bf712eb76dd733ccea97997947265f5e4f1f9cb/docs/formats/chatgpt.md) · [Skillsync sync semantics](https://api.skillsync.com/docs/session-sync)

`wookat/agentmove` covers a broad set of local configuration/resource files (including MCP, skills, instructions, agents and selected memory/persona layers), but its canonical bundle is not a session or workspace graph. `z2z23n0/agent-capsule` has a separate Codex-to-Codex profile-transfer path and Codex/Claude Code session handoff; neither path writes imported content into Anthropic-hosted Cloud Projects. Similar feature labels therefore need separate source/target edges and evidence grades.

`nrzz/claude-chat-ferry` provides a direct static-export edge from ChatGPT JSON into a local Claude Code session. Its writer is a useful local/API-key workflow reference, but its ChatGPT reader follows only `current_node`; it projects images/attachments to labels, does not import ChatGPT project/section membership or token usage, and records tools as summaries. Its optional resume test must be pinned to the Claude Code version and user/system context used for the assertion. [Pinned Chat Ferry sources and tests](https://github.com/nrzz/claude-chat-ferry/tree/1f637d7be4ec1fd5cba1dca379e95c407e485031)

### Codex first-party external-agent import (source snapshot checked 2026-11-22)

OpenAI Codex commit `8653ca9e99b2c805107bde7b7d6f57a634c643d0` has app-server `externalAgentConfig/detect` and `externalAgentConfig/import`; source adapters are Claude Code and Cursor. `MigrationDetails` has named categories for Skills, MCP servers, Plugins, Memory, Hooks, Subagents, Commands, and Sessions (`path`, `cwd`, optional `title`), but does not define ChatGPT Projects or Section membership. The session importer builds a Codex-native rollout/thread projection from parsed user/assistant text, writes estimated usage and an import marker, and does not recreate source tool calls as native Codex calls or restore a Project/Section/fork graph. OpenAI's `codex-plugin-cc` calls the importer to transfer Claude Code → Codex; this is not an outbound ChatGPT → Claude adapter. The implementation is versioned and its detection/import history has reported edge cases, including bounded discovery and silent no-op behavior for already-imported growing sessions; verify exact installed versions and per-item results. [Pinned protocol types](https://github.com/openai/codex/blob/8653ca9e99b2c805107bde7b7d6f57a634c643d0/codex-rs/app-server-protocol/src/protocol/v2/config.rs) · [Pinned session exporter](https://github.com/openai/codex/blob/8653ca9e99b2c805107bde7b7d6f57a634c643d0/codex-rs/external-agent-migration/src/sessions/export.rs) · [Migration source adapters](https://github.com/openai/codex/blob/8653ca9e99b2c805107bde7b7d6f57a634c643d0/codex-rs/external-agent-migration/src/migration_source.rs) · [Official transfer caller](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/scripts/lib/codex.mjs) · [Open import-update issue](https://github.com/openai/codex/issues/53403)

`rbutera/harness-bridge` is a separate live Claude Code ↔ Codex MCP delegation server. Its README and runtime do not invoke the external-agent import protocol; its generated `MigrationDetails`-like types are not an implemented importer. The default Codex execution path unconditionally bypasses approval and sandbox restrictions, while the app-server path requests `danger-full-access`; Claude-side session-key mapping lives in an in-memory registry. These properties make it a useful warning/reference for cross-harness delegation and session-ID mapping, not a safe Nexus migration dependency. [Pinned repository](https://github.com/rbutera/harness-bridge/tree/31559c93be61fa6adec584b728f843e2f92330f3) · [Pinned runtime](https://github.com/rbutera/harness-bridge/blob/31559c93be61fa6adec584b728f843e2f92330f3/src/lib/app-server.ts)

### Agent Skills

The open Agent Skills format (`SKILL.md` plus optional scripts/references/assets) is a realistic portability layer where both runtimes support it. OpenAI’s plugin architecture separates skills (workflow instructions/resources) from MCP (live data/tools); Cursor supports both the open Agent Plugins format and its own richer plugin format; Zed and Antigravity consume `SKILL.md`-style skills; Warp scans standard per-harness skill directories and can publish selected skills into native Claude Code/Codex directories for cloud runs. Zed’s discovery is flat (no nested skill folders), project skills require a trusted worktree, and skills apply to Zed Agent rather than automatically to ACP External Agents or Terminal Threads. [OpenAI skills](https://developers.openai.com/plugins/concepts/skills) · [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins) · [Cursor plugins](https://cursor.com/docs/plugins) · [Zed Skills](https://zed.dev/docs/ai/skills) · [Warp Skills](https://docs.warp.dev/agents/capabilities/skills) · [Antigravity features](https://antigravity.google/docs/features) · [Agent Skills specification](https://agentskills.io/specification)

Candidate #137 `rogue-dev-studio/rogue-skill-pack-managers-skill` illustrates a package-vs-skill distinction: it is an instruction-only `SKILL.md` for skill/marketplace housekeeping, not an installer implementation or session migrator. The Agent Skills spec requires the skill's parent directory name to equal its frontmatter `name`; this candidate's metadata name is `skill-pack-managers`, while the repo root is `rogue-skill-pack-managers-skill`, and its README's copy instruction does not specify the required package folder. A Nexus resource adapter should validate the installed folder/metadata pair and host support, not infer portability from a file named `SKILL.md`. [Pinned candidate](https://github.com/rogue-dev-studio/rogue-skill-pack-managers-skill/tree/ba9ff33055418484cb984136ee888c8dc1ace471) · [Agent Skills directory/frontmatter rules](https://agentskills.io/specification)

The reviewed CLI-first `shenysun/skills-manager` is a resource-plane reference: it imports skills into a canonical hub and distributes to harness-specific roots (user scope defaults to symlinks, project scope to copies), with restore points and provenance. Its README claims a 70+ agent catalog, but that catalog/path inventory is not per-agent runtime certification and does not establish Project/Section/session/branch, MCP/plugin, memory, attachment, token, or schedule migration. The pinned bundled catalog is dated 2026-08-18 and the tested refresh attempt returned GitHub API 403. [Pinned README](https://github.com/shenysun/skills-manager/blob/948db52fa5dcfdae994073cf9d8c1fd05ab89205/README.md) · [pinned source](https://github.com/shenysun/skills-manager/tree/948db52fa5dcfdae994073cf9d8c1fd05ab89205)

Portability is not automatic equivalence: discovery directories, trust/policy, scripts, plugin UI, hook lifecycle and secret configuration vary by host. Always-on instructions are a separate capability from callable Skills: Zed uses personal/project instruction files (including compatible `AGENTS.md`, `CLAUDE.md`, and other named files), while its Skills are reusable on-demand workflows. [Zed Instructions](https://zed.dev/docs/ai/instructions)

Nexus Memory should inventory a skill's files and dependencies, validate the portable core, and emit host-specific installation records without copying secrets. It should separately map always-on instructions, tool profiles/permissions, and host-specific lifecycle configuration rather than folding them into `SKILL.md`.

Candidate #139 `SebghatYusuf/skills-manager` is an adjacent Electron skill-catalog/installer: its Claude target uses `~/.claude/skills` and workspace `.claude/skills`, not Claude Desktop's third-party-inference Chat/Cowork/Code stores. It installs/toggles skill directories only and has no Project/Section/Session or MCP/plugin migration. Source review found no exact-name match causes a selected install to fall back to every discovered skill; multi-skill conflicts can leave earlier copies in place; and the “VS Code Copilot symlink” path copies files rather than creating a symlink. Its SkillsMP key is serialized into the app's `userData/settings.json`; that is a marketplace credential, not the model API key. The package claims MIT but has no LICENSE file and GitHub reports no license, so do not reuse code pending clearance. [Pinned README](https://github.com/SebghatYusuf/skills-manager/blob/980da978cc7d7ff27cd7cca74eb328baf95a738e/README.md) · [Pinned install/target source](https://github.com/SebghatYusuf/skills-manager/blob/980da978cc7d7ff27cd7cca74eb328baf95a738e/src/main/skillsService.ts) · [settings persistence](https://github.com/SebghatYusuf/skills-manager/blob/980da978cc7d7ff27cd7cca74eb328baf95a738e/src/main/settingsStore.ts)

### MCP

MCP standardizes capability discovery/invocation surfaces, not user identity, credentials, authorization policy, server installation state, or approval history. Its specification distinguishes server-provided resources/prompts/tools from client-provided capabilities. [MCP specification](https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/specification)

Candidate #138 `safebuffer/cli-manager-mcp` is a concrete warning for MCP capability transfer: one exposed tool accepts a free-form command string and `subprocess.Popen(..., shell=True)` executes it; the MCP inputs carry no per-call sandbox, approval, working-directory, or timeout policy. A global in-memory process registry returns command text and full stdout/stderr, and the code logs commands without redaction. Its README warns users to trust the caller or sandbox the server, but the server itself does not enforce that boundary. Treat it only as an adjacent background-process feature example; do not install or bundle it as a generic portable MCP resource. [Pinned source](https://github.com/safebuffer/cli-manager-mcp/blob/92fd151a239994cbf8c94e723c2c7b59d5ca8d68/server.py) · [Pinned README](https://github.com/safebuffer/cli-manager-mcp/blob/92fd151a239994cbf8c94e723c2c7b59d5ca8d68/README.md)

The adapter must treat an MCP server URL/command, tool schemas, environment-variable names, auth mechanism, grants and secrets as separate fields. Transfer configuration with credentials redacted; require re-authentication and review of target permissions.

Zed Agent reads Zed-managed MCP configuration; ACP External Agents may receive forwarded Zed MCP servers or use their own native MCP configuration. This is an integration boundary, not proof of identical credentials, grants, or approval history. [Zed External Agents](https://zed.dev/docs/ai/external-agents) · [Zed settings](https://zed.dev/docs/reference/all-settings)

Kiro similarly scopes MCP settings across global, project and agent configuration, with workspace configuration merged over user configuration; Web/Mobile support differs from local IDE/CLI and personal global files are not simply copied into the cloud sandbox. Model server identity, transport, auth, permissions/auto-approval, and surface availability as separate fields. [Kiro configuration scopes](https://kiro.dev/docs/cli/chat/configuration/) · [Kiro MCP configuration](https://kiro.dev/docs/mcp/configuration/)

Continue can reuse MCP JSON configs by placing them in `.continue/mcpServers/`, although its standalone config blocks have their own YAML metadata and MCP tools are Agent-mode-only. Warp's project-scoped file configuration can be shared with Claude Code and Codex, but cloned project servers require approval and cloud runs need managed secrets or environment-provided credentials. Reuse the transport/schema where compatible, never credentials or grants. [Continue MCP](https://docs.continue.dev/customize/deep-dives/mcp) · [Warp MCP](https://docs.warp.dev/guides/external-tools/using-mcp-servers-with-warp)

## Transfer grades

- **Native verified:** target accepts the object, can rediscover/resume it, and a same-version CLI/UI test confirms the intended state.
- **Portable sidecar:** complete source graph and bytes are retained, but the target consumes a projection or handoff document.
- **Semantic continuation:** target receives a summary/transcript; original event graph/tool state cannot be resumed.
- **Unsupported/unknown:** no safe source reader or target writer is verified. Preserve the original and report the reason.

Every feature row must also carry source/target versions, evidence URL or fixture/test ID, date checked, loss reasons and whether validation was a fixture, exact-client, live-provider, or UI test.

### Agent Connect — local session adapter (pinned review)

`1naruto-1/agent-connect` supports Cursor, Claude Code, Codex CLI, and Pi local stores. It is useful as a source-format and safety reference, not a complete Nexus interchange layer: its canonical event schema omits hierarchy, media bytes, usage/cost and provider-resource configuration, and source readers intentionally follow active branches. Target writers create linear histories; Claude usage is zeroed, and Cursor requires a closed client plus an already-opened project. It has no ChatGPT Projects/Sections or Claude-hosted Cloud/API-key writer. Do not label its advertised 12 directions “lossless” without per-pair native resume tests. Evidence is pinned in [RESEARCH.md](RESEARCH.md).

### AIW — live workspace manager, not session migration

`neosun100/aiw` binds configured CLI processes to persistent tmux workspaces and exposes workspace control through CLI, web/API and an AIW-specific MCP server. Its JSON tracks workspace metadata and its logs are tmux pane captures; it has no conversation transcript import/export or parent/branch/project graph. Exclude as a migration engine; keep only as an adjacent orchestration example. Static security review found an unauthenticated API with an all-interface default and shell-interpolated tmux calls; do not expose it to untrusted networks. See [RESEARCH.md](RESEARCH.md#deep-review-neosun100aiw).

### DSH versioned-repair guide (adjacent tooling; not a migrator)

`Fabian-698/dsh-update-guide` offers a version-specific DSH 0.1.2→0.1.7 upgrade/recovery Skill, not an external-harness importer. It has useful staged/backup-gated recovery patterns, but its pinned repair script detects V3 successors and misses V4-only successors; a synthetic `--apply` reproduced modification of an old V2 file beside V4. As of 2026-11-20 official DSH has advanced to v0.2.2-rc.5. Its first-party experimental importer is DeepSeek-web-export-only, active-branch-only, and has an unanswered rc.5 ZIP-layout failure report. Do not treat either as cross-Harness fidelity proof; see [RESEARCH.md](RESEARCH.md#deep-review-fabian-698dsh-update-guide-2026-11-20). Follow-up (2026-11-24): official DSH is now at v0.2.3-alpha.2; isolated probes found a zstd-missing `ALL PASS`, a first-target-only backup gate, and repair through a symlink outside DSH_HOME. Keep as schema/recovery context only; do not use its checker or mutator as a migration safety gate. See `fabian-698-dsh-update-guide-followup-audit-2026-11-24.txt`.

### DSH Unified Context — community importer into DSH

The MIT `Chang-Tong/dsh-unified-context` package (v0.5.0, former repo alias `dsh-import-agents`) is a useful one-way adapter into DeepSeek Harness, not a general source/target matrix. It reads Pi, OpenCode, Codex, Claude Code and WorkBuddy; selected agent prompts/skills, shared instructions/memory and Codex/WorkBuddy schedules are separate pathways. It has no ChatGPT reader, Claude Cloud/API-key writer or ChatGPT Project/Section mapping. MCP definitions, provider/model and permission settings remain native. Source review found lost Codex function-call records/fork topology and Claude/Pi branch selection, call/result pairing degradation (placeholders or unpaired text outside WorkBuddy's real-result path), and a potentially escaping Skill name. A fake persistence diagnostic showed partial appends can remain behind a stable session ID that retries skip. Local build and 74 tests passed; no real DSH GUI resume was performed. Treat as a high-value adapter reference only until path validation, durable completion state and version-specific target resume are proven. See [deep review](RESEARCH.md#deep-review-chang-tongdsh-unified-context-former-dsh-import-agents-2026-11-20).

### License-excluded candidate: coding_agent_session_search

`Dicklesworthstone/coding_agent_session_search` is retained as an original-corpus record but excluded from Nexus implementation/benchmark use because its LICENSE rider expressly restricts OpenAI/Anthropic and related parties, including analysis/indexing/testing absent written permission. No compatibility or source-level fidelity claims are made; the local clone/index were removed after discovering the rider. See [RESEARCH.md](RESEARCH.md#license-exclusion-dicklesworthstonecoding_agent_session_search-2026-11-20).

### Agent Sessions (macOS) — catalog/resume, not migration

`jazzyalex/agent-sessions` is a polished local multi-agent session catalog with provider-specific native resume, a local source-file archive and Markdown transcript export. Its model includes local cwd/repo identity and a limited subagent/side-chat tree, but the reviewed `SessionSource` registry has no ChatGPT source and there is no ChatGPT Project/Section or Claude Cloud/API-key writer. It is a UX/source-discovery reference, not evidence that a transcript can be recreated in another harness. Full review and test evidence: [RESEARCH.md](RESEARCH.md#deep-review-jazzyalexagent-sessions-2026-11-20).


### AI Config Sync Manager — adjacent local config sync, not session migration

Reviewed at pinned commit 3ac0566032807acabc79405245777edcc780d347 (MIT; npm 0.1.13). The actual host pair is Claude Code ↔ Codex, with global/current-project configuration scopes. The implemented surfaces are instructions, Skills, Agents, MCP, hooks and permissions; plugins are reported as status-only. Its source command surface contains no ChatGPT reader, conversation/session graph, Project/Section adapter, hosted Claude Cloud/API-Key session writer, attachment/token/schedule migration, or memory transfer.

This candidate is relevant to the configuration layer of Nexus Memory, but not to the requested ChatGPT/Codex → Claude target migration. It demonstrates useful local dry-run/selector/backup/hash-ledger patterns. Do not reuse its default MCP secret pass-through: credentials are copied unless a redaction environment variable is enabled. Also do not interpret the manual-risk label as an enforced approval gate for hooks/permissions; the apply code sets approvalRequired=false for those operations. The 445-test suite passed after the documented no-sync bundle build (443 passed, 2 skipped); the fixtures do not prove live Cloud/session restoration. See the pinned source-level review in RESEARCH.md.

Source implementation reviewed: [slash9494/ai-config-sync-manager at pinned commit 3ac0566032807acabc79405245777edcc780d347](https://github.com/slash9494/ai-config-sync-manager/tree/3ac0566032807acabc79405245777edcc780d347).


### pgrigorr/memory-harness-kit — memory sidecar, not a migrator

Pinned at 3374ead82060868b2398acffb40f945402bb4cac. The kit can store raw session transcripts and turn them into searchable memory; an optional Claude Code Stop hook captures a local transcript when configured. The typed normalized session record is a single dialogue-text record with no Project/Section/branch graph, and the only config adapter kinds are generic and OpenClaw. No ChatGPT/Codex reader, Claude Cloud/API-Key session writer, or schedule-object importer was found. Its local maintenance schedule is not user-schedule migration.

Evidence quality is useful: canonical make ci-smoke passed all 289 tests on macOS/Python 3.12.10; wheel/sdist proof also passed. Limits remain explicit: OpenClaw smoke skipped without an external workspace, and no account/provider import was tested. Important blocker for reuse: a synthetic credential-shaped string survived both raw capture and normalized search; the source safety filter is not a secret redactor. A synthetic pair of distinct IDs also reproduced a sanitized-filename collision and overwrite. Treat as a memory-architecture reference only, not a Nexus transfer dependency. Repository link: [pgrigorr/memory-harness-kit at pinned commit](https://github.com/pgrigorr/memory-harness-kit/tree/3374ead82060868b2398acffb40f945402bb4cac).


### yeelam-gordon/agent-cli-session-TUI — local session catalog/resumer

Reviewed at pinned commit f81a993aa94071fd2150bd9cf4fd6710547b196e (MIT, version 0.3.3, 0-star snapshot). It reads local histories for six CLI providers, searches them, keeps flat local group/archive metadata, and resumes through the original provider CLI using the original session ID and cwd. It is not an importer/exporter, has no ChatGPT or hosted Claude Project/Section/Cloud adapter, and does not reconstitute the transcript in another harness.

Important limitation: default remote grouping can automatically send session titles and working-directory file URIs to a Microsoft-hosted service. The full transcript and summary are not sent; existing group names are opt-in. Use wordmatch before any scan if this connector is evaluated for privacy-sensitive discovery. cargo +stable test --lib: 220 passed, 1 ignored; lifecycle integration tests compiled but were not run against real histories. See the pinned source review in RESEARCH.md.

### MethodoxTech coding-agent-sessions-history-vscode (reviewed 2026-11-20)
Local Claude Code/Codex history browser with date/project-path grouping, Markdown export, and original-CLI resume only. README describes local-only/no telemetry/no account connection; source review found no remote history/grouping client or Cloud/API-Key writer. Does not preserve the ChatGPT Project/Section hierarchy or provide a machine-readable restore package. See docs/RESEARCH.md for evidence and limits.

### CassianFlorin/skill-hub (reviewed 2026-11-20)
Partial Skill adapter reference: curated SKILL.md library, provenance metadata, CLI/TUI, local/GitHub install, and explicit paths for 12 legacy agents plus global/project scopes. It does not migrate sessions, Projects/Sections, MCP/plugin configs, memories, or schedules. --all means only Claude global + .agents project scope, not all 12 agent paths. Test suite: 225 passed, 3 catalog/release-doc drift failures; detailed findings are in docs/RESEARCH.md.

### erickochen/purple (reviewed 2026-11-20)
Adjacent MCP reference only: stdio server for SSH hosts/commands/containers, optional read-only allowlist and JSONL audit. Claude Desktop bundle sets read-only explicitly; direct CLI mode does not. Provides no session/project import or harness-state migration. Documented provider-token storage is plaintext TOML. See docs/RESEARCH.md for tested evidence.

### tsonglew/dutis (reviewed 2026-11-20)
Adjacent MCP/transaction-pattern reference: local stdio server, 17 read-only tools, two write tools disabled by default; writes require opt-in token, fresh plan digest, requester, policy, snapshot, audit, and verification. No AI session/project/memory migration or Cloud/API-Key endpoint. MIT is declared in Cargo/README but standalone LICENSE text is absent, so dependency adoption needs license confirmation.


### Browser prompt handoff: Sai-Nitin123/ContextBridge

The pinned browser extension extracts a conversation-shaped DOM snapshot into `.aicx`, then targets a browser composer by injecting a generated `continuationPrompt`; it does not recreate individual messages as a native destination session. The canonical schema has a flat message list without Project/Section/branch/subagent edges, and the API-Key/Cloud session surface is absent. Although the repo describes a “complete context” bridge, attachment handling is metadata/visible-preview based and the synthetic redaction probe found secret leakage through derived summary and attachment metadata. Treat it as prompt-handoff UX only, not a faithful ChatGPT-to-Claude session adapter. See the pinned review in [RESEARCH.md](RESEARCH.md#deep-review-sai-nitin123contextbridge-2026-11-20).


### Browser prompt handoff: Sai-Nitin123/ContextBridge

This pinned extension reads the currently accessible page DOM into a flat `.aicx` conversation projection and injects one generated continuation prompt into the destination composer. It does not recreate each message as a native turn or restore Projects/Sections/branch/session identity, and it does not use a Claude API Key or hosted Cloud import API. Its attachment representation is metadata/visible preview, not binary restoration. A synthetic review also found message-body redaction does not cover derived summaries or attachment metadata, so it is not a safe transfer pipeline without substantial fixes. Details: [RESEARCH.md](RESEARCH.md#deep-review-sai-nitin123contextbridge-2026-11-20).

### Browser prompt handoff: MaazzAlii/context-saver-extension

The pinned extension is a DOM text scraper and local prompt catalog, not a native conversation importer/exporter. It can generate a text continuation prompt for manual pasting, but does not map Project/Section/Session identity, message ancestry, forks, tasks, assets, or provider-specific session state. Its optional summary path sends captured text to Mistral; the declared Anthropic host permission does not correspond to an inspected Claude API request. It therefore does not satisfy the ChatGPT/Codex-to-Cloud/API-Key route. Capture may terminate at fixed scroll bounds and still report success; treat this as E2 source evidence only, with no behavioral browser test. See the [pinned review](RESEARCH.md#deep-review-maazzalii-context-saver-extension-2026-11-20).

### Local session archive reference: laohu-aiskills/agent-session-vault

This MIT project is a strong read-only local source-catalog/raw-backup pattern and a useful example of an explicit loss note. Its parsers cover several local coding-agent formats, including Codex CLI, but not ChatGPT exports or ChatGPT Project/Section state. Its migration writer creates new local Claude Code/WorkBuddy/Qwen Work/CodeBuddy-format files; default conversion is text-only and does not update target indexes, preserve branches, or write to hosted Cloud/API-Key sessions. Backup can preserve original files and SQLite sidecars, but a synthetic malicious manifest with rel=../escaped.txt escaped the caller's target/home remapping when explicit apply flags were used. Keep only as an architecture reference until restore path containment is enforced. Detailed pinned review: [RESEARCH.md](RESEARCH.md#deep-review-laohu-aiskillsagent-session-vault-2026-11-20).

### Native local coding-session bridge: llxgdtop/Agent-Session-Migration

This is the closest reviewed candidate to a native local session writer: it reads Claude Code, Codex CLI and ZCode and emits files/rows in all three local formats. It has no ChatGPT source or Claude Cloud/API-Key target. Its flat IR has no branch/parent graph; Claude sidechains are skipped, and tools/reasoning are rendered into capped text rather than replayable native events. ZCode writes span two databases; a temp-only failure probe left the CLI session committed while the task row rolled back, and a live-WAL probe showed the main-file-only backup omitted a committed WAL row. Treat it as a useful adapter/test-pattern reference, not a lossless or transaction-safe dependency. Full pinned review: [RESEARCH.md](RESEARCH.md#deep-review-llxgdtopagent-session-migration-2026-11-20).


### Cross-harness memory sidecar: YURIBEDRAN/rubi

Rubi is a useful *memory plane*, not a conversation-migration plane. It shares a Markdown knowledge graph/code map across clients through MCP and adds hooks where available. Its project/module/knowledge hierarchy and compact handoffs can preserve selected durable facts, but its Claude Code `PreCompact` record is a bounded text extraction, not full event history or a session parent/fork/subtask graph. It has no ChatGPT Project/Section source, no arbitrary Skills/MCP/plugin/scheduler transfer, and no Claude Cloud/API-Key chat writer; the repository explicitly marks claude.ai/mobile integration experimental and unvalidated.

| Requested layer | Rubi evidence | Nexus interpretation |
|---|---|---|
| Shared project memory | `.rubi/` Markdown graph + module summaries + personal vault; hybrid retrieval | Valuable optional sidecar; keep separate from immutable source archives and session IR |
| Project/Section hierarchy | One memory root per code project or app-topic slug; no ChatGPT/Codex Section membership edges | No Section migration coverage |
| Session/branch/subtask hierarchy | One bounded Claude pre-compaction note; sidechains skipped; no event-parent graph | Not a session adapter; no fidelity claim |
| Skills/MCP/plugins | Installs Rubi's own MCP and instruction/hooks; does not map arbitrary user resources | Adapter bootstrap reference only |
| Attachments, links, token/cost, tool events | Non-text transcript parts and event/usage structure are not in the record | Explicit losses; never claim “full context” from a handoff |
| Cloud/API-Key target | Loopback HTTP MCP with a Rubi token; no Cloud session create/import API | Does not meet ChatGPT/Codex-to-Cloud migration target |
| Safety | Documentation says not to store secrets; synthetic secret was persisted, and synthetic symlink read escaped lexical containment | Require deterministic redaction and realpath confinement before any Nexus memory import/read path |

Test evidence is 17/17 local tests passing; it does not validate live Cloud imports, cross-harness session resume or redaction. Full pinned source/security review: [RESEARCH.md](RESEARCH.md#deep-review-yuribedranrubi-cross-harness-memory-sidecar-2026-11-20).

### Local cross-agent session search: luckeyfaraday/athena-code

Athena Code adds a local FTS index and can resume an existing local CLI session. It is useful as a source-discovery and source-native-continuation reference, but it does not import/export portable conversation archives. The current implementation enumerates only Claude Code, Codex, Hermes and OpenCode stores plus Athena's own live sessions; a source grep found no ChatGPT parser. It neither recreates Cloud sessions nor translates Project/Section/fork/task structure.

| Layer | Athena Code evidence | Nexus disposition |
|---|---|---|
| Global/project memory | Separate global and repository memory, frozen snapshots, prompt-based recall | Optional memory-plane pattern; keep separate from raw source records |
| Session index | Local SQLite FTS5 rows: agent/session/workspace/role/time/text | Search projection only; never use as canonical archive |
| Session hierarchy | Flat session key and workspace; no parent/fork/subagent graph | No hierarchy-transfer coverage |
| Source support | Claude Code, Codex, Hermes, OpenCode; no executable ChatGPT adapter found | Useful subset for local-source reconnaissance only |
| Resume | Runs each source's native CLI resume command in the indexed workspace | Resume preserves source-side identity; it is not a target import |
| Cloud/API-Key | No Claude Cloud/API-Key session writer | Does not meet the requested destination |
| Attachments/tools/usage | Image/tool/result payloads, event IDs, model/cost/permission data not in the search row | Lossy recall only; explicit loss report required |
| Safety | Synthetic fake token persisted to the session index; no source-session retention/deletion path found; tool prompts are permissionless by default unless overridden | Require opt-in scanning, deterministic redaction, bounded retention, user rules and explicit workspace confirmation |

The suite passed 98 tests with one optional oracle skipped, but used temporary fixtures/stub commands and did not exercise a real provider. Full review: [RESEARCH.md](RESEARCH.md).

### xtermium — desktop session manager, not AI history migrator

xtermium is a cross-platform terminal/connection manager with an AI-agent tab bridge. Distinguish its saved network Connection Sessions from its separate UI listing of local Claude Code/Codex/omp transcript files. Its workspace/folder hierarchy, layouts and encrypted sync are for xtermium Store data; the AI history list only shows source metadata and resumes the original CLI.

| Requested layer | xtermium evidence | Nexus interpretation |
|---|---|---|
| Workspace/folder groups | Xtermium Store has workspaces, folders and saved connection sessions/layouts | UI-structure reference only; not ChatGPT Project/Section membership |
| AI session history | Local Claude Code, Codex and omp files listed per working directory | Local history browser/source locator; no portable conversation payload |
| Resume | Invokes original CLI with source session ID in a new terminal tab | Source-native continuation, not target import |
| Branches/subagents | Claude agent-* files and Codex thread_source=subagent are excluded; flat Conversation rows have no parent edges | No task/fork/session graph coverage |
| ChatGPT / Cloud | No ChatGPT parser, no Claude Cloud/API-Key session writer | Does not meet target migration requirements |
| Import/export | Xtermium encrypted config backup, MobaXterm and OpenSSH connection settings | Connection-profile transfer only |
| MCP | Xtermium connection/session and terminal-control tools; no AI transcript-import API | Privileged automation surface, not a session adapter |
| Safety | Agent-history delete removes the original transcript; protected by canonical-root check; remote MCP can be enabled with a bearer token | Require explicit export/backup and destination-scoped authorization |

Pinned source and focused test evidence are in [RESEARCH.md](RESEARCH.md).


### termem — local memory/search plane, not a migrator

| Requested layer | termem evidence | Nexus interpretation |
|---|---|---|
| Source adapters | Local Claude Code, Codex CLI, Gemini CLI, OpenCode and shell-log scanners | Useful local input adapters; no ChatGPT source or ChatGPT Project/Section hierarchy |
| Session graph | Grouping by cwd/subtree; OpenCode listing filters to parent_id NULL; no cross-session parent/fork/subagent edges | Keep workspace/project containment, branching, subagents and task edges explicit in Nexus; cwd grouping is not a substitute |
| Transcript fidelity | Role/text/optional timestamp pages; provider-specific text extraction | Lossy search view only; attachments, structured tools/results, usage/cost, edits, interruption/continuation and other event types require separate evidence |
| Destination | Native CLI resume only; no Cloud/API-Key session writer or import/export converter | Not a migration route; destination writers must be separately capability- and loss-tested |
| Skills/MCP | MCP search/recall/get_session plus summary/board tools and generated per-harness wrappers | Useful memory-plane and adapter-wiring pattern; not proof that native sessions, Skills, plugins or scheduled tasks transfer |
| Privacy | SQLite FTS contains initial transcript text (up to 400 messages / 200,000 chars); no deterministic redaction found in the reviewed path | Treat indexed text as sensitive; enforce local-only storage, redaction, retention, access scope and export consent in Nexus |

The repository is MIT-declared in Cargo metadata and README but the pinned source has no root LICENSE file; legal provenance must be verified before source reuse. See the pinned source review in RESEARCH.md.


### Leon — native local history importer and desktop browser, not a Cloud migration target

| Requested layer | Leon evidence | Nexus interpretation |
|---|---|---|
| Source adapters | Local Claude Code, Codex CLI and OpenCode; extra account roots for Claude/Codex | Strong provider-reader seam, but no ChatGPT web/Projects/Sections source |
| Workspace hierarchy | Machine > project > worktree > sessions; cwd can associate history to a project/worktree; direct-project/folder/pinned scopes | Useful shell for Nexus navigation, but not a general cross-harness identity or parent/fork graph |
| Session graph | Unified session row and sequenced messages; Codex parent/fork identity is not retained; Claude subagents are counted for tokens but not stored as sessions; OpenCode child sessions omitted from top-level import | Explicitly store source-qualified fork/subagent edges and report when not reconstructible |
| Transcript events | Role/text/time rows; tool events are textified, results omitted; images and other non-text content omitted; malformed/oversized data is skipped or clipped | Lossy projection only; preserve raw source records and attachment references separately |
| Usage | Token counts aggregated per model/day, including provider-specific cache/reasoning parsing; no cost field in the history model | Good usage parser reference, not a cost/accounting ledger or full event graph |
| Destination | Opens stored transcript or resumes the original CLI; no Cloud/API-Key writer or cross-provider conversion in the reviewed history subsystem | Not a migration route; target writer must be separately proved against a real API-key-compatible target |

Leon is a strong local UX/importer reference (idempotent cursors, account roots, read-only OpenCode access and privacy-conscious diagnostics). See RESEARCH.md for source-level losses and tests.


### Adeptability — strong Skills/subagent portability, not whole-session portability

| Resource | Adeptability evidence | Nexus interpretation |
|---|---|---|
| Skills | Canonical Skill schema and 56 harness registry entries; five specialized renderers, generic per-skill formats for others | Strong adapter/catalog reference for Skills, but not equivalent activation across every target |
| Sidecars | Canonical sidecars include scripts/references/assets; Claude/OpenCode/generic per-skill targets can carry them | Codex AGENTS.md, Cursor .mdc and Copilot buckets drop sidecars; report each loss explicitly |
| Metadata/agents | Canonical subagent definitions; model hint currently emitted only by Claude; per-harness overrides survive canonical storage but import does not rebuild them | Preserve provenance and harness-specific overrides outside the lossy normalized common fields |
| Sessions/projects | No transcript/history import or session graph; project means local repository root | No ChatGPT Project/Section Group or conversation hierarchy portability |
| MCP/plugins | Skill body may describe instructions, but CLI has no MCP/plugin config importer or target writer | Keep MCP servers, plugins and permission/auth scopes as separate resource types |
| Schedules | Loop add scaffolds discovery Skill + evaluator agent + optional GitHub Actions cron YAML | Not a schedule migrator or runtime; preserve trigger, recurrence, timezone, auth and run/session behavior separately |
| Safety | Static content scanner plus optional LLM review; no sync sandbox/root containment | Treat skills as executable instructions, and add canonical-path protection before writing into harness trees |

Full source/test and the temporary symlink-boundary probe are documented in RESEARCH.md.


### Pan — useful local session/workspace/MCP orchestrator, not a Cloud migration target

| Requested layer | Pan evidence | Nexus interpretation |
|---|---|---|
| Source histories | Import providers for CBC, Kimi, OpenCode, Codex CLI, DSH; backend also registers Claude while current modal omits it | Strong source-adapter prototype, but no ChatGPT web/Projects/Sections source |
| Session hierarchy | Pan manager/worker links, child Sessions and branches; source import creates Pan Sessions without general source parent/fork graph | Preserve source-qualified tree edges separately; do not assume Pan-managed hierarchy reconstructs ChatGPT/DSh lineage |
| Workspaces | Pan Workspace groups Sessions and optional shared-directory metadata; source-specific cwd remains the workdir | Useful UI grouping, not a movable folder or exact ChatGPT Section Group importer |
| Transcript fidelity | DSH/CBC/Kimi/OpenCode/Codex parsers convert native events to Pan role/content blocks plus separate raw usage | Text projection; source-specific configs, timestamps/edges, binary attachments and some tool results are lost or simplified |
| MCP/plugins | Pan supports per-Session MCP configuration and app plugins | Manual Pan setup only; no source MCP/plugin config importer or normalized permission/auth transfer |
| Schedules | Jobs UI can schedule Session messages and background work | No ChatGPT scheduled-task importer; preserve trigger, recurrence, timezone, auth and semantics independently |
| API/security | Local service unauthenticated by default; default loopback, but external PAN_HOST lacks authentication | Do not expose on an untrusted network; require explicit deployment/auth boundary |
| Memory | README says Memory/Character is paused | Not a ready-made persistent memory migration layer |

See RESEARCH.md for per-adapter losses, reimport conflict protection, test boundary and AGPL caveat.

### Termide (termide/termide; local event-log harness, not a migration adapter)

| Resource | Observed Termide capability | Nexus mapping / loss boundary |
|---|---|---|
| Project / grouping | Local path-rooted projects; `project.toml` contains panel layout and vertical `panel_groups`; project store contains trust, logs and buffers. | Map root and layout separately. No ChatGPT sidebar Section Group or section-membership importer; a panel column is not a project parent. |
| Sessions / hierarchy | Append-only typed JSONL per session; event `parent_id` chain, rewind leaf, copied fork prefix; delegated tasks have explicit `SessionParent`; ACP sessions have external IDs. | Excellent source-adapter fixture/reference. Keep event edges, copied-fork provenance, subagent relation and ACP native-session reference as distinct edge types. Fork header keeps copied-count but not explicit source-session id. |
| Content / tokens / media | Internal messages support user images, assistant text/thinking/tool calls, tool results, timing, provider call metadata and token accounting; 24 typed event kinds. | Preserve raw events/unknown kinds in Nexus. Do not assume Termide's internal codec is a public canonical format. |
| Export | “Save chat as Markdown” exports current-branch user/assistant text. | Loses reasoning, tool calls/results, panel notices and event/control data; no structured lossless import/export found. |
| Skills | Loads `SKILL.md` skills from app `ai` layers, `.agents/skills` (panel/project) and user `~/.agents/skills`. | Strong shared-resource candidate; retain scope/precedence/activation metadata and revalidate target discovery. |
| MCP / plugins / secrets | `mcp.toml` plus documented subset of `.mcp.json`; supports environment expansion and OAuth, with local OAuth auth file. External process plugins are Termide-specific. | Map server configuration with capability report; never migrate auth tokens/API keys/permission grants. Do not claim generic plugin interoperability. |
| Scheduled work / Cloud | Session-bound `/loop` and `/goal`; built-in agent may call compatible hosted APIs; Claude Code/Codex/Gemini CLI can run over ACP. | Not a general cross-harness scheduler or a Claude.ai/Claude Code Cloud session writer. API endpoint access is not session-store portability. |

Evidence at pinned `main` `5c3eec4915380da479c2bb03f6843342e7a9e17d` (MIT). Targeted tests: session 41/41, project 41/41, Markdown export 4/4; full workspace suite and native target import were not tested. Sources: [https://github.com/termide/termide](https://github.com/termide/termide); [release 0.50.0](https://github.com/termide/termide/releases/tag/0.50.0); [session schema](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/agent-core/src/session.rs); [message schema](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/agent-core/src/message.rs); [project layout](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/project/src/lib.rs); [project store](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/project/src/store.rs); [Agent docs](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/doc/en/agent.md); [architecture docs](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/doc/en/architecture.md); [Markdown exporter](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/panel-agent/src/export.rs).

### bobmatnyc/claude-mpm (Claude Code control plane; restricted license; not cross-harness migration)

| Resource | Observed implementation | Nexus compatibility/loss boundary |
|---|---|---|
| Project/Section | Project cwd and `.claude-mpm/configuration.yaml` override; pause state is under project-local `.claude-mpm/sessions/`. | No ChatGPT/Codex Project or Section Group importer; map cwd/project config separately from transcript. |
| Session identity/resume | Stores Claude session IDs and limited metadata in active_sessions.json; `run --resume`/AgentRuntime resume delegates to Claude Code native ID; MCP server manages live process/status in memory. | Native continuation only for an existing Claude Code ID. It does not ingest ChatGPT/Codex transcript files or create Cloud sessions from them. |
| Export / history | `session pause --export` emits a checkpoint snapshot; optional `aggregate export` emits MPM's captured event projection; a separate analyzer reads Claude Code JSONL and subagents into a report. | These are three different artifacts. Pause JSON is not the transcript; aggregate JSON is monitor-capture-specific; transcript report is a lossy projection with images omitted, tool-result text capped at 500 characters and timestamp-based subagent correlation. No cross-harness import/writer. |
| Branch / subagent relations | CLI can `--resume` and `--fork-session`; captured event analysis may correlate Agent tool calls and subagent files. | Metadata list truncates task text and does not store universal parent session IDs; analyzer correlation may be ambiguous. Preserve source parent/fork IDs and evidence in Nexus instead of inferring. |
| Skills/MCP/plugin | Claude Code plugin supplies hooks, slash commands, Skills and MCP; `.mcp.json` migration upgrades internal command names. | Claude-specific resource/rendering layer, not a universal plugin or project-resource importer. Migrate config with explicit capability mapping; never copy OAuth/API credentials. |
| Attachments/tokens | Transcript report extracts text/tool activity, usage/cost; raw Claude JSONL remains the underlying source. | Images/non-text blocks and full tool outputs are not represented in the report; it is not a binary-asset archive. Keep encrypted source export separately. |
| Scheduling / Cloud | Reviewed cron jobs clean notifications/queues; Cloud Sled is a README roadmap. | No user-scheduled task transfer or shipped Cloud-session writer observed. Claude Code CLI requirement is not Claude.ai Cloud compatibility. |
| License / security | Root license and Python metadata say Elastic-2.0; npm wrapper says MIT. HTTP MCP binds loopback by default; ngrok tunnel is optional. | License remains `NOASSERTION` pending legal clearance; do not use as Nexus dependency. Do not expose HTTP Session Server remotely without an authenticated boundary. |

Evidence: pinned main `25203d34f20982c5871574b5059949ab85ab5a6b`; focused session/export/pause/transcript test bundles 407 passed / 1 skipped; full repository suite and live provider behavior untested. Sources: [https://github.com/bobmatnyc/claude-mpm](https://github.com/bobmatnyc/claude-mpm); [release v6.5.83](https://github.com/bobmatnyc/claude-mpm/releases/tag/v6.5.83); [license](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/LICENSE); [README](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/README.md); [core session metadata](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/core/session_manager.py); [project-local pause export](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/cli/session_pause_manager.py); [resume-log generator](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/infrastructure/resume_log_generator.py); [MCP session server](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/mcp/session_manager.py); [HTTP MCP transport](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/mcp/session_server_http.py); [event capture/export](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/event_aggregator.py); [captured-session model](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/models/agent_session.py); [aggregate export CLI](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/cli/commands/aggregate.py); [Claude transcript reader](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/session_analysis/transcript_parser.py); [session-analysis report writer](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/session_analysis/markdown_writer.py); [channel-session registry](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/channels/session_registry.py); [internal periodic jobs](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/communication/message_bus.py).

### RoleCraft (`rolecraft-sh/rolecraft`) — resource-plane bridge only (2026-11-20)

- **Portable subset:** Skills can be copied/symlinked to manifest-defined agent directories; MCP server config is handled for 9 of the 90 agents. Profiles can carry static per-agent config/instructions/skills/MCP and can be exported/imported. Manifest maps capability/support level, instruction format, path, and MCP config format.
- **Loss / unsupported:** RoleCraft's `.agents/skills` project target is not a project/section hierarchy. Profiles/lockfiles contain no session ancestry, message event history, follow-up/interrupt semantics, files/images/link attachments, token usage, or scheduled tasks. This candidate cannot satisfy the requested ChatGPT/Codex Project → Cloud session-tree migration by itself.
- **Security/fidelity caveats:** `setup` does not scan or install a skill-declared MCP server; `install` does resolve and scan it. Unscannable MCP sources are marked `unscanned_source` and require explicit approval in install (CI fails closed); the README's “report as SAFE” sentence is stale at pinned v2.6.2. Profile export does not redact fake/real env secrets; profile import/write loses `projectOverrides` and `localOverrides`.
- **Use in Nexus:** Treat as a source/target adapter reference for Skills, MCP, and agent config only. Keep Nexus's typed session/project graph and loss ledger authoritative; scrub secrets and test export/import projections before applying any profile. See the [pinned install path](https://github.com/rolecraft-sh/rolecraft/blob/edfd87eed27288fa9e29521eb90e946130075842/src/api/install.js), [setup path](https://github.com/rolecraft-sh/rolecraft/blob/edfd87eed27288fa9e29521eb90e946130075842/src/api/setup.js), [CI path](https://github.com/rolecraft-sh/rolecraft/blob/edfd87eed27288fa9e29521eb90e946130075842/src/api/ci.js), and [profile serializer](https://github.com/rolecraft-sh/rolecraft/blob/edfd87eed27288fa9e29521eb90e946130075842/src/utils/profile.js).
### Kendex — strong resource adapter manager; Pi-only session helpers (reviewed 2026-11-20)

- **Supported resource plane:** Claude Code, Codex, OpenCode, Cursor, Pi, Gemini CLI, GitHub Copilot, and Antigravity. The capability matrix distinguishes managed, read-only, and unsupported operations for agents, skills, hooks, commands, MCP, plugins, and Pi extensions, with personal and per-local-project scopes.
- **Session-adjacent subset:** Pi's session-manager can browse/resume/fork/rename/delete native Pi session files and show related sessions as a tree; Pi's session-bridge reads live/recent Pi events; Pi QOL schedules prompts by appending Pi-session events; Pi Claude Bridge resumes a Claude Code conversation across Pi turns when its persisted cursor/fingerprint still matches.
- **Not compatible as a full-history importer:** none of the reviewed Kendex core surfaces converts ChatGPT/Codex conversation trees, Section Groups, attachments, token usage, or session parent/fork history into another harness. Local folder configuration is not cloud Project/Section hierarchy.
- **Target constraint:** Pi Claude Bridge requires a logged-in Claude Code account and drives the Claude Agent SDK; it does not provide the requested standalone Cloud API-Key migration path.
- **Use in Nexus:** high-value reference / optional resource-setup adapter; do not make it the canonical session archive. Its Pi session facilities can be an opt-in Pi source adapter only. See the [capability table](https://github.com/vanillagreencom/kendex/blob/260b6492363b47d84ba1f893c5223120ad6a9f4a/docs/architecture/harnesses.md), [Pi session manager](https://github.com/vanillagreencom/kendex/blob/260b6492363b47d84ba1f893c5223120ad6a9f4a/pi-extensions/pi-session-manager/README.md), and [Pi Claude bridge](https://github.com/vanillagreencom/kendex/blob/260b6492363b47d84ba1f893c5223120ad6a9f4a/pi-extensions/pi-claude-bridge/README.md).
### AgentSkillsManager — Skills-only VS Code extension; not a migration target (reviewed 2026-11-20)

- **Available subset:** browses local Git skill repositories and a cloud SKILL.md catalog; installs a selected skill into the active workspace skills directory for VS Code and several VS Code-based IDEs. It also displays local skill directories, including Claude/Codex personal locations.
- **Not covered:** no Session, Project/Section Group, message graph, attachment, token/cost, MCP/plugin, or cross-harness schedule migration. Its core record carries a skill path and repository URL, not source commit/content hash or a session identity.
- **Security/continuity:** cloud install downloads a ZIP and uses adm-zip 0.5.16; official npm audit flags that direct runtime dependency high, including a crafted-ZIP memory-exhaustion advisory. The downloader has no app-level response-size/timeout cap, and replacement deletes the old directory before copying. No automated tests were found in the 12-file checkout.
- **Decision:** de-prioritize as a source/target adapter. Its active-IDE skill-folder mapping is a minor reference only; do not use it to transfer user sessions or to import untrusted catalog payloads into Nexus.

### Skills Compat Manager review — import declarations, not migration fidelity

`skills-compat-manager` is a useful design reference for a preflight compatibility plane: four declared requirement categories, per-harness capability profiles, and an MCP interface for detecting gaps before skill execution. Treat its `COMPAT.yaml` as a lossy declaration/assessment artifact, not as a source session or project. It does not serialize Session events, Project/Section containment, attachments, MCP invocation history, token accounting, or schedules. Its own README says it does not validate API-key validity/quota or runtime-test declared platform capabilities.

Nexus should adopt the *idea* of explicit per-adapter capability and loss reports, but use stable source-qualified skill identity and independently validate installed package/API-key/capability state. This candidate currently fails MCP-server import on the observed unconstrained dependency resolution (`fastmcp 4.2.3`, `mcp 2.3.0`), and its `apply_fix` string gate accepted shell-chained commands in a non-executing probe. Do not deploy it as an automatic repair agent until the SDK range and shell execution boundary are fixed and tested. See `docs/research/evidence/skills-compat-manager-review-2026-11-20.txt`.

### AKM candidate review — broad local adapters, narrow/lossy session extraction

AKM is useful evidence for resource/knowledge adapter design: it reads native agent folders and several knowledge formats, models project paths as retrieval/write scopes, extracts session insights from Claude Code/Codex/OpenCode logs, and syncs Task v4 schedules to OS schedulers. Its reader contracts do **not** preserve conversation semantics: `SessionEvent` is a timestamped text projection; child session relations, multimedia, interrupts, tokens, and native continuation identifiers are absent or flattened. Output is an AKM memory/session summary proposal pointing back to a local log, not a Claude Cloud conversation. No ChatGPT Project/SectionGroup reader or MCP server-config migration was found.

The model connection is an API-key-backed endpoint for AKM model work, not a Cloud history destination. The separate platform plugins add AKM-specific UX; they do not establish native project/session conversion. Keep AKM as a valuable adapter/ingestion reference, while Nexus maintains its canonical session graph and loss accounting. macOS path aliasing currently causes proposal queue ownership to fail for `/var/folders` temporary roots even on the latest 0.11 beta branch; see the pinned evidence.

### Skiller review — installable Skills portability, not Session portability

Skiller offers a polished cross-agent Skills plane: a shared `.agents/skills` library, project-local `.agents/skills`, 49 native agent definitions, portable sync profiles, provenance/hash/conflict checks and a skills marketplace. It does not synchronize all harness state: the manifest only describes Skills and agent-selection policy; the Project type is a filesystem path/name/group for skills. No ChatGPT history reader, Section Group graph, session transcript writer, MCP-server config migration or scheduled-task importer was found.

Use only as a product and adapter pattern. Its SUL-1.0 terms constrain code reuse/distribution; any Nexus product that will be shared or sold needs independent implementation or a separate license. The repository's current app tests passed for the focused skill/project/sync area, not for session conversion.

### venv-manager — portable Python environment metadata, no conversation/project graph

- **Available subset:** shared local Python venv registry; project path and tags; package inventory/snapshots/diffs/rollback; MCP tools and CLI/TUI for dependency setup across coding agents.
- **Safety boundary:** MCP defaults to `safe`; destructive/package/code-execution operations require a `confirm: true` argument, and read-only mode is available. The MCP safe-mode confirmation is a caller-controlled boolean rather than a separate human-approval channel. The MCP ephemeral-run `sandbox: true` branch is rejected by the handler at the reviewed commit, even though the CLI has an OS sandbox option.
- **Not covered:** no ChatGPT/Codex history reader, cloud destination, Project/Section hierarchy, session/turn/subtask/fork records, attachment graph, message/tool/token history, skill/plugin/config migration, or scheduled-task importer.
- **Decision:** useful only as an optional dependency-environment subresource adapter/reference. Do not count it as project/session migration coverage or let its environment association imply that conversation context moved. Tests were not run locally because Go is absent; the upstream CI page shows a successful run on the reviewed commit. Evidence: `docs/research/evidence/venv-manager-review-2026-11-20.txt`.

### Config Control for Kiro — rich Kiro-specific metadata view, not a portable transcript converter

- **Available subset:** Global and workspace Kiro CLI configuration for agents, MCP, skills, powers, permissions/sandbox, hooks, steering, prompts, specs/workflows and Kiro Memory. Session dashboard surfaces local chat metadata, run state, credits/context use, Kiro dashboard bookmarks/tags/titles, app-local tags, subagent parent relations and tangent/rewind branch relations.
- **Transcript fidelity:** the V3 reader deliberately counts user messages and reads usage/context events only; prompts, assistant responses, tool results and attachments are not surfaced. Resume is a Kiro CLI command, not session serialization.
- **Cloud boundary:** local V3 files are read from `~/.kiro/sessions`; remote dashboard metadata is not applied by the local V3 adapter. Kiro's official docs say Cloud archives cannot use `/chat save` or `/chat load`. Whether Kiro CLI's list command exposes every remote session to this app was not tested; there is no explicit cloud-import/export path here.
- **Not covered:** no cross-harness ChatGPT/Codex Project/Section importer, portable project-group graph, full transcript/attachment transfer or target Cloud archive writer. Kiro workspace scopes and dashboard grouping are not a ChatGPT Section Group.
- **Decision:** good Kiro adapter/data-model reference only. Record `parentSessionId` and `createdReason` as distinct subagent vs branch relations; preserve Kiro-native memory scopes separately; keep Cloud as unsupported until tested against documented export/import behavior. Review evidence: `docs/research/evidence/config-control-kiro-review-2026-11-20.txt`.


### Symaira Vault — scoped credential/MCP service, not a chat-memory transfer engine

- **Available subset:** encrypted path-based secret entries; password-manager/CXF/CSV import; MCP install for a handful of agent clients; per-agent path/tool allowlists and expiring scoped tokens; optional API templates and egress broker that resolve secrets server-side.
- **Useful security pattern:** let Nexus retain opaque secret references and resolve them only through an explicit, target-aware, authorized provider. Do not export decrypted values alongside session history.
- **Not covered:** no ChatGPT/Codex transcript, Project/Section, parent/fork or attachment graph; no arbitrary Skill/Plugin/MCP-configuration import/export; no Cloud API-key validation/migration. The app's “session” cache is for vault unlock, not chat history.
- **Decision:** adjacent credential layer only. The vault's nested folder path is a namespace for credentials, not a Project/Session hierarchy. Current platform support excludes Windows; pre-1.0 and latest main's upstream CI was blocked by a macOS runner acquisition failure, though local all-features tests/format/Clippy passed. Evidence: `docs/research/evidence/symaira-vault-review-2026-11-20.txt`.


## pwnera/artbucket — adjacent project/API reference, no chat/session adapter

| Surface | What the pinned source actually provides | Nexus compatibility result |
|---|---|---|
| Project scope | Organization → Project DAM library; project selector in MCP; scoped grants | **Conceptual partial only.** Not a ChatGPT Project/session hierarchy or import mapping.
| Section/group | Collections group assets; brand pages contain nested content sections | **Non-equivalent.** Collections/pages are domain-specific. Do not map to Section Groups.
| MCP / API | Stateless Streamable HTTP `/api/v1/mcp`, stable tool contract; project-bound OAuth/consent scopes; Artbucket `ab_...` bearer keys | **Reusable integration pattern only.** Its key authenticates to Artbucket, not to Claude/Cloud.
| Skill / plugin | Artbucket Claude Code plugin teaches asset and brand governance workflows | **Domain-specific Skill.** No general cross-harness Skill, MCP-config or plugin converter.
| Assistant chat | UI keeps selected chat ID in browser sessionStorage; calls external `ASSISTANT_URL` for chat list, turns, streaming and actions | **Do not count as a source adapter.** External assistant store is out of repo; no export/import or destination writer.
| Assets/brand migration | Manual asset ZIP/PDF plan, review/apply/undo; omissions documented | **Adjacent migration UX reference.** Not transcript, attachments, branches, token, tools or schedule migration.

Overall disposition: `ADJACENT_PROJECT_MCP_AND_REVERSIBLE_ASSET_IMPORT_REFERENCE_NOT_SESSION_MIGRATOR`. Evidence and source scope: `docs/research/evidence/artbucket-review-2026-11-20.txt`.


## yeasy/ask — Skills package installation, not harness/session conversion

| Surface | Evidence in pinned source | Nexus compatibility result |
|---|---|---|
| Skills | 19 agent directories, project/global scopes, Git sparse clone, folder copy/symlink fallback, lock pins source commits | **High Skills-plane reference.** Full semantics/harness support still vary; same file is not full compatibility.
| MCP/plugins/settings | `mcp-builder` is only an example Skill; no `mcpServers`/plugin/hook converter found | **Unsupported by this candidate.**
| Project/Session hierarchy | `ask.yaml` is a local Skill-manager config; `.agent/skills` is a destination folder | **Not equivalent** to ChatGPT Project / Section Group / Session.
| Cloud API key | no model key, chat API or transcript writer | **No Cloud Session capability.**
| Desktop/web | Local loopback Wails/web UI; v1.11.0 release has macOS, Windows EXE, Linux assets | **Useful packaging reference, not a migration application.**
| Safety | `ask.lock`, HTTPS source validation, 12+ rule scanner, loopback Host check | **Good local defense-in-depth reference, not sandboxing.** Security scan report must be reviewed; exact-head security scan is unverified and prior scan failed.

Overall: `SKILLS_RESOURCE_PLANE_REFERENCE_NOT_SESSION_OR_CLOUD_MIGRATOR`; full evidence and exact-head workflow IDs in `docs/research/evidence/yeasy-ask-review-2026-11-20.txt`.


## seed-forge/harness-ai-kit — manifest and asset materialization, not conversation conversion

| Surface | Evidence in pinned/current source and released wheel | Nexus compatibility result |
|---|---|---|
| Skills / tools | Typed manifest and lock cover skills, CLIs, plugins, hooks, subagents, MCPs, loops; pin sources, versions/checksums, stage and sync files | **Strong adjacent asset-plane reference.** Require per-target capability checks and report registration/semantic loss; copying an MCP/plugin file does not prove its host has been configured. |
| Runtime profiles | Main source lists Codex, DSH, Pi, Claude Code, Kiro, Cursor, OpenCode and Qoder; skill materialization varies (directory, Kiro steering `.md`, Cursor rule `.mdc`) | Useful adapter-profile idea, but do not rely on current-main features through pip: public PyPI 0.2.0 differs from main's 0.18.18. |
| Project asset structure | `harness-ai-kit.yml` is a local manifest with roots/features/sync targets and typed asset lists; lock records resolved sources | Not equivalent to ChatGPT Project/Section Group/parent-child session graph; it declares dependencies, not conversation containment. |
| Chat/session fidelity | No chat transcript/turn importer/exporter, child/branch graph, attachments, token accounting or conversation-session storage in the focused source and verified 0.2.0 wheel scan | **No session-migration capability found.** Do not infer parity from its word “loop” or its related Dify API's own conversations. |
| Cloud/API-key session | No Cloud model-session create/write route; generic runtime configuration or a DSH plugin command does not create Claude/Cloud conversations | **Unsupported.** Keep account API keys in secret-reference storage; never imply asset install moves an authenticated conversation. |
| Published state | PyPI lists 0.2.0 (Aug 12); exact 0.18.18 release workflow on main HEAD failed at PyPI OIDC token validation | Use exact wheel hash/version as adapter evidence and show source-vs-distribution mismatch. |

Overall: `CROSS_HARNESS_SKILLS_AND_ASSET_LOCK_REFERENCE_NOT_CHAT_SESSION_MIGRATOR`; full local/static and release evidence in `docs/research/evidence/harness-ai-kit-review-2026-11-20.txt`.


## 24KaratAu/openhub — Skill catalog/export, not harness state transfer

| Surface | Evidence in pinned source | Nexus compatibility result |
|---|---|---|
| Skills | Exports generated SKILL.md and OpenCode agent Markdown from a selected GitHub repo/README into local/global `.opencode`, `.agents` and `.claude` paths; scans and updates installed SKILL.md trees | **Useful adjacent Skills UX.** Exporting the same file into multiple folders does not prove that every advertised harness discovers/loads it. Add conflict preview, native discovery validation and explicit copy-loss report. |
| MCP/plugins | Catalog includes implementation labels such as “MCP Servers” / “Plugins”; install command calls `opencode get <slug>` | **No MCP config or plugin migration.** A catalog label is not a runtime adapter or host registration. |
| Session/project hierarchy | Local SQLite tracks repo catalog, installed package locations and operation action logs | **Not equivalent** to ChatGPT Project/Section Group/session tree; no turn, branch, child-task, attachment or conversation schema found. |
| Memory/schedule/API key | no conversation memory, scheduled task import, provider configuration or Claude/Cloud Session writer | **Unsupported.** GitHub API token (`GITHUB_TOKEN`) is for GitHub request limits, not Claude/Cloud model sessions. |
| Safety/quality | Update path backs up and rolls back Skill trees and tests tar path traversal; simple export writes to destination with `open(..., "w")`; install builds a shell command from catalog slug; official runner deletes its HOME cache DB | Reuse only the update rollback pattern. Require argv execution, HOME-safe tests, output conflict confirmation, and never run tests under user HOME. |
| Validation | Upstream exact-HEAD CI/release succeeded Sep 27; current isolated `run_all_tests.py` has a time-dependent rating failure on Nov 20. CI config runs on Ubuntu only despite README's 3-OS claim. | Recent historical CI is not current quality proof; pin the run date and clock-dependent fixture. |

Overall: `ADJACENT_SKILL_CATALOG_AND_EXPORTER_ONLY_NOT_PROJECT_SESSION_OR_CLOUD_MIGRATOR`; see `docs/research/evidence/24karatau-openhub-review-2026-11-20.txt`.

## xiaode-ai/nanofile-connector — Windows file-system tools, not session transfer

| Surface | Current evidence | Nexus decision |
|---|---|---|
| Skills | Seven NanoFile task-guide folders, advertised for file-manager operations. | Adjacent content-package example only; no conversation semantics. A copied `SKILL.md` still needs target-native discovery/activation checks. |
| MCP | 27 unique file/app/tag/favorite tool declarations; wrapper invokes NanoFile's local Windows app/CLI. | Capability/config transfer may be inventoried independently of history. No MCP invocation-history or session graph import found. |
| Plugin manifests | Root Antigravity manifest; separate `.claude-plugin` and `.codex-plugin`; root `mcp.json` is not the portable Agent Plugins schema+typed-transport shape. Local Claude Code 2.1.76 validation reports `skills: Invalid input`; current docs require `./` path prefixes. | Treat each host format as a separate adapter; current target-version runtime validation remains unverified. Do not infer a single portable plugin format from co-located manifests. |
| Project/session/memory/attachment/schedule | Scoped source scan found no conversation/transcript/session/chat-history strings and no ChatGPT/Codex Project/Section or conversation writer. | **Not a session migrator.** It cannot satisfy ChatGPT/Codex Project/Section/session hierarchy, attachments, branch/child-task, memory, schedule or Claude Desktop client-managed history migration. |
| Protocol and integrity | Legacy MCP handshake omits `notifications/initialized`; stdout parser is chunk-based instead of newline-buffered. Installer verifies only PE magic/size, not a digest/signature. | Synthetic stdio probe reproduced chunk-fragment timeout; live NanoFile runtime unavailable on macOS. Do not execute the installer; retain only as an adjacent reference. |
| Tests/release | `npm test` has no script; only `bump`/`release` scripts and a Release-only workflow. | No test-suite claim. The release script performs Git push/tag/release side effects and was intentionally not executed. |

Review: `docs/research/evidence/nanofile-connector-review-2026-11-20.txt`. Inventory now 42/303 reviewed / 261 unreviewed; next `cbruyndoncx/obsidian-skills-manager`.

## cbruyndoncx/obsidian-skills-manager — vault Skill library, lossy fixed-file exporter

| Surface | Current evidence | Nexus decision |
|---|---|---|
| Skill collection | Stores/organizes `SKILL.md` folders in an Obsidian vault (default `.claude/skills`); supports GitHub, monorepo, ZIP and local registration. | Adjacent Skill-plane UX only; do not equate Obsidian vault membership with target Harness project/session hierarchy. |
| Cross-tool export | Strips YAML frontmatter, concatenates all enabled bodies and writes fixed Cursor/Copilot/Windsurf/Cline Markdown files. | **Lossy projection.** It overwrites those files, does not retain per-skill metadata or verify native target discovery, and has no merge/backup confirmation. Do not treat as portable Skill activation. |
| State/credentials | Obsidian plugin data stores per-Skill source/version plus `githubPat` and registry `apiKey` in settings. | State is local plugin configuration, not a portable session store. Re-authenticate credentials; never copy keys into migration bundles. |
| Sessions/projects | Scoped source and README scan found no conversation/transcript/session/chat-history or Project/Section model. | **Not a session migrator.** No turns, branches, attachments, token history, MCP/plugin configuration transfer or schedule model. |
| Quality/license | GitHub license field null; no LICENSE file. No `test` script, tests directory, or GitHub workflow; scratch build passed after clean dependency install with lifecycle scripts disabled. | No code dependency without license permission. Use only as a behavioral reference for catalogue UX, staged install/rollback, and the lossy-export counterexample. |

Review: `docs/research/evidence/obsidian-skills-manager-review-2026-11-20.txt`. Inventory now 43/303 reviewed / 260 unreviewed; next `superradcompany/tool-cli`.

## superradcompany/tool-cli — MCP package/config manager, not conversation migration

| Surface | Current evidence | Nexus decision |
|---|---|---|
| MCP host config | Eleven named host adapters with different config paths/schema keys; tool registration supports dry-run, explicit overwrite, confirmation and config backup. A Claude Code host-add dry-run was executed under a temporary HOME and made no host-config write. | High-value **MCP configuration plane** reference. Model host, transport, process, args/env, OAuth and managed-entry metadata separately; run per-host schema tests. It does not carry chat context. |
| MCPB packages/tools | CLI can detect/init/validate/pack/publish MCP bundles and install/run/inspect MCP tools. | Adjacent resource/package adapter only. MCPB package and server instructions do not imply Agent Skills or Plugins compatibility. |
| Credentials | OAuth credentials are encrypted with AES-256-GCM and stored separately from host config; an application-managed local key file is used. | Do not copy secret stores/keys as session data; re-authenticate or reference a separately authorized secret manager. |
| Projects/sessions/attachments/schedules | Core CLI has no conversation/session transcript store or ChatGPT/Codex project graph. A separate example LangChain agent maintains only in-memory turns/token totals. | **Not a session migrator.** No event archive, branch/subtask, image/file/link import, context memory, or schedule transfer. |
| Quality | Local `cargo test`: 148 passed; `cargo fmt --check` passed; latest exact-HEAD GitHub Rust Tests workflow succeeded. Host add/remove/preview do not have direct covering tests per CodeGraph. | Useful adjacent implementation and tests, but host mutation correctness is only partially established; do not infer live cross-harness restoration. |

Review: `docs/research/evidence/tool-cli-review-2026-11-20.txt`. Inventory now 44/303 reviewed / 259 unreviewed; next `andrader/jup`.

## andrader/jup — Agent Skills installer/sync CLI, not session migration

| Surface | Current evidence | Nexus decision |
|---|---|---|
| Skills | Installs local/GitHub `SKILL.md` directories, records source/layout/category/skill/version metadata in `skills.lock`, then links/copies to configured local/global harness folders. Custom providers are filesystem paths. | Adjacent **Skill resource-plane** reference; verify native host activation separately. Lock metadata is not an AI session archive or a content-addressed snapshot. |
| Projects / Sections / sessions | Scoped source and test review found no Project/Section graph, conversation turns/events, parent/fork/child-task links, attachments, token history, MCP/plugin transfer, memory, schedule, ChatGPT reader, or Claude Desktop/Code/Cloud session writer. `skills_lock_session` is only a lockfile load/save context manager. | **Not a session migrator.** It cannot transfer ChatGPT/Codex Projects/Sections/Destruction Era history into Claude Desktop Chat/Cowork/Code, local Claude Code, or hosted Cloud. |
| Safety | Path containment checks resolve paths and test traversal/symlink escape. Static sync review shows existing same-slug destination paths can be removed before link/copy. | Borrow containment validation, but implement Nexus-side conflict preview, backup and approval before any write. |
| Quality / license | Python 3.12+, package 0.20.0; local isolated suite: 95 passed. GitHub metadata had license `null` and no root LICENSE. | Keep as a behavioral reference only; no dependency adoption without license clarification. Evidence: `docs/research/evidence/jup-review-2026-11-20.txt`. |

Review: `docs/research/evidence/jup-review-2026-11-20.txt`. Inventory now 45/303 reviewed / 258 unreviewed; next `ktreharrison/tkmd`.

## ktreharrison/tkmd — task DAG and session-ID handoff, not a conversation migrator

| Surface | Current evidence | Nexus decision |
|---|---|---|
| Task/project structure | Local Markdown task cards with YAML fields, optional string `project`, `blocked_by` / `blocks` dependency graph, and local/global task scopes. | Useful task orchestration model; **not** ChatGPT Project/Section/Section Group hierarchy or primary/controlled Session relationships. Keep dependency edges and Section membership as separate graph types. |
| Agent sessions | Stores one latest `session_id` and a per-task agent `sessions[]` list; records task-level session IDs in `.events.jsonl`; `tk u` maps IDs to local CLI resume/continue commands. Synthetic probe proved card serialization and stub argv dispatch only. | Strong adjacent `TaskSessionReference` / handoff pattern. No transcript, turn/event tree, tool history, attachment, token or portable resume payload; actual continuation depends on the source CLI's local account/store. |
| MCP / Skills | Nine stdio MCP task tools and one bundled `skills/tkmd` operational Skill. MCP config is documented for manual registration. | A tool server and one Skill are assets, not a migration API. No MCP-host config importer, Session MCP tool, general Skills bridge or ChatGPT/Claude history writer. |
| Safety / quality | Task `eval` executes shell; user `on_done` hooks are opt-in and board hooks are ignored. `cargo test --locked`: 126 passed, 0 failed, 2 ignored; `cargo check` and fmt passed; strict Clippy failed on one Rust 1.95 warning at `src/store/doctor.rs:85`. | Borrow explicit human approval and check-pinning patterns, but treat imported eval/commands as inert and require approval. Session-resume helpers lack direct tests; no real provider resume was tested. MIT OR Apache-2.0; latest release v0.4.0, reviewed main 3 commits ahead. |

Review: `docs/research/evidence/tkmd-review-2026-11-20.txt`. Inventory now 46/303 reviewed / 257 unreviewed; next `grimoire-rs/grimoire`.

## grimoire-rs/grimoire — cross-client asset package manager, not session migration

| Surface | Current evidence | Nexus decision |
|---|---|---|
| Skills / Rules / Agents / MCP / plugins | Apache-2.0 CLI stores typed assets with registry digest or local path+SHA-256 in `grimoire.lock`; renders per-client native files/config, reports unsupported/degraded surfaces, and can export a locked project as separate Claude/Codex plugins. Synthetic local Skill install/export succeeded. | High-value **resource-plane** reference. Keep asset manifests, dependency/provenance edges and output proofs independent from Project/Section/Session. Local MCP path input was refused; registry MCP artifacts can be rendered, but no arbitrary client-config importer was found. |
| ChatGPT and Claude Desktop | The native matrix targets Claude Code and Codex among other coding clients. A separate marketplace guide documents ChatGPT/Codex plugin marketplaces and Claude Desktop Chat/Cowork distribution. This packages Skills/connectors/MCP under supported plugin surfaces; it does not migrate Projects or conversations. | Useful marketplace/asset adapter, not a conversation source/target adapter. Do not infer ChatGPT Desktop or Claude Desktop session import from plugin market support. Claude Code plugin account sync is unavailable with API-key or cloud-provider auth. |
| Project / Section / Session | `grimoire.toml`/`grimoire.lock` scopes configuration and an asset set; no transcript, turn graph, branch/child Session, attachment, token, Session memory or schedule importer/exporter found. | **Not a Session migrator.** Do not map a Grimoire project plugin to ChatGPT/Codex Projects or Section Groups. |
| Safety / quality | Pinned content hashes, staged writes, conflict refusal/`--force`, output-drift state and explicit hook consent. Full workspace `cargo test`: 7,563 passed; fmt/check passed; strict Clippy failed on an unused test helper; full Taskfile verify not run. | Borrow digest/preview/drift patterns. MCP commands and hook artifacts are executable; import inertly, audit provenance and require approval. Evidence: `docs/research/evidence/grimoire-review-2026-11-20.txt`. |

Review: `docs/research/evidence/grimoire-review-2026-11-20.txt`. At this checkpoint, inventory stood at 47/303 reviewed / 256 unreviewed; next was `yuvalsuede/claudia`.


### Claudia (`yuvalsuede/claudia`) — workflow/task hierarchy only

| Source object | Source meaning | Nexus Memory disposition |
|---|---|---|
| Project | SQLite name/path/description namespace | Candidate for an explicitly typed project/workspace mapping; not equivalent to chat Projects/Sections |
| Sprint | Date/status timebox | Optional workflow metadata, no automatic Section conversion |
| Task `parent_id` / dependencies | Parent-child task tree plus separate prerequisite edges | Preserve only in a task/work-item extension; never infer session/turn hierarchy |
| Task `context` | Bounded JSON per task, 65,536 serialized characters | Opaque, provenance-tagged task memory; not transcript |
| MCP `session_agent_id` | Random process-level agent ownership label | Do not map to provider Session ID |
| Task `images` | URL/path/base64 attachment metadata | Not a message attachment event without a parent message and ordering |

**Session migration compatibility: none demonstrated.** The implementation is a task manager, not a Claude or ChatGPT transcript reader/writer. It includes one Claude plugin/skill surface but no cross-harness package/config import. Exact source review and local-test limitation: `docs/research/evidence/claudia-review-2026-11-20.txt`.


### skillpm (`sbroenne/skillpm`) — npm Skill assets only

| Source surface | Observed support | Nexus Memory disposition |
|---|---|---|
| npm Skill package | One `skills/<name>/SKILL.md` per package; npm dependency/lockfile; nested `node_modules` and workspace scans | Borrow package/lock mechanics for portable Skills, keep package provenance/hash separate from host projection |
| Host projection | Delegates to `npx skills@1.7.0 add ...`; no explicit `--all` or `--agent`; host discovery delegated | Report exact detected targets/version; probe each host, don't infer support from the universal format |
| Uninstall | Removes npm package, re-wires remaining Skills, but leaves stale copied Skill and `skills-lock.json` | Require preview, explicit stale-file cleanup, and rollback before using this pattern |
| Project/Session data | No conversation Project/Section/session/transcript model | No Session or hierarchy conversion |

Local Node 26 lint/build and 65 unit tests passed; synthetic isolated Codex install/list/uninstall exercised the projection, including stale-copy behavior. This evidence says nothing about ChatGPT Projects/Sections or Claude Desktop Chat/Cowork/Code session compatibility. See `docs/research/evidence/skillpm-review-2026-11-20.txt`.


### TiguClaw (`tigu77/tiguclaw`) — native multi-channel session graph, no import adapter

| Surface | Observed behavior | Nexus Memory disposition |
|---|---|---|
| Session identity | Channel/thread key plus provider session ID; transcript index maps one thread to provider sid/JSONL path | Use separate `LogicalSession` and `ProviderSessionRef`; never overload a universal ID |
| Transcript | Local SQLite text rows + FTS; turn tool items separately stored; raw Claude SDK JSONL indexed incrementally | Preserve raw payload/turn events and attachments separately; TiguClaw text projection is lossy for multimodal blocks |
| Branch/fork | Immutable parent lineage with transcript/chat/time cutoffs; Claude SDK session fork is boundary-verified | Strong branch-provenance/watermark pattern; not cross-Harness session portability |
| Projects | Absolute path + `PROJECT.md` registry; linked to conversations; project tools/skills/MCP are inherited | Candidate for Project/workspace link model; no Section/Section Group hierarchy |
| Migration | No external transcript/session import/export or ChatGPT/Claude Desktop converter found | No direct migration support; do not infer from shared Claude formats |

The release CI passed on Node 22 for v0.86.0; local Node 26 full regression had one fixture-specific failure (21 assertions in `plugin-fetch-redirect`) because the test patches Undici dispatcher `.1` while Node 26 uses `.2` as current. Detailed observed and inferred boundary: `docs/research/evidence/tiguclaw-review-2026-11-20.txt`.

### secretctl (`forest6511/secretctl`) — credential vault, not MCP/session migration

| Surface | Observed | Nexus Memory disposition |
|---|---|---|
| Secret storage | Local encrypted vault; metadata/masked reads; API values stay in vault | Store a secret reference/alias in migration metadata; never export the raw value |
| MCP `secret_run` | Default-deny policy; command allowlist; secrets enter launched process environment; output sanitization | Optional target-side credential integration after command-scope review |
| Projects / Sessions / Sections | No conversation or harness hierarchy/import model | No session/project/section conversion |
| MCP config | Provides its own secret MCP server; no host MCP config parser/translator | Do not count as MCP migration support |

Apache-2.0, latest release v0.8.8 (Jan 2026); local Go tests not run because Go is unavailable. This is an adjacent security primitive only. See `docs/research/evidence/secretctl-review-2026-11-20.txt`.


### Skillet (`Brattlof/skillet`) — Skills/MCP package manager, not session portability

| Surface | Observed source support | Compatibility conclusion |
|---|---|---|
| Skills | `~/.claude/skills` plus shared `~/.agents/skills` | File placement only; a portable `SKILL.md` does not guarantee identical host activation/frontmatter/permissions. |
| MCP | Explicit JSON writers for Claude Code project `.mcp.json`, Cursor, Windsurf, Gemini CLI, Cline | No Codex MCP adapter or Claude Desktop Chat/Cowork/Code session/config adapter in the `mcpClients` table; config write is not a runtime acceptance test. |
| Claude-specific assets | commands, hooks, subagents, output styles under Claude Code scopes | Host-specific items cannot be generalized to ChatGPT or Claude Desktop modes. |
| Project/Section/Session | No conversation Project/Section/session/transcript graph or importer/exporter | No session/hierarchy conversion or fidelity claim. |
| Provenance/security | commit/checksum lock, frozen verification, prune managed assets; HTTPS/ref validation and safe-path tests | Good reproducible asset-projection reference; executable Skills/MCP remain a trust boundary. |

Exact main commit CI passed, but local Go tests were not run because Go is absent. See `docs/research/evidence/skillet-review-2026-11-20.txt`.


### Toki (`harperreed/toki`) — todo Projects/MCP, not harness Sessions

| Surface | Observed | Compatibility conclusion |
|---|---|---|
| Project/task hierarchy | One Project (UUID, name, directory path) contains Todo records | Workspace/task grouping only; no Section Group, nested Section or conversation-session parent/fork graph. |
| Export/import | YAML/JSON/Markdown/SQLite export; YAML-only import; IDs used for duplicate skip | Preserves task attributes only. Project created time is lost; import can print per-item errors and still return success. |
| Storage | SQLite or Markdown; backend copy of Projects/Todos/tags | Not provider data; non-transactional writes and existing-target `--force` is not a clean replacement. |
| MCP | stdio task CRUD, resources and workflow prompts; README offers Claude Desktop setup | MCP API invocation is not session import and does not create/continue a Claude Desktop or hosted Cloud session. |
| License | README says MIT; no LICENSE file and API SPDX is null | Unverified; do not adopt as a dependency without license clarification. |

Local Go tests could not run because the Go binary is absent. Exact main commit CI #75 reports Success, with cache/action warnings. See `docs/research/evidence/toki-review-2026-11-21.txt`.


### Agent Farm (`greenfield-inc/agent-farm`) — high-value CLI telemetry reference, no importer

| Surface | Observed source support | Nexus Memory disposition |
|---|---|---|
| Harnesses | Claude Code CLI and Codex CLI profiles/variants; custom base URL/API key env reference for each | Useful CLI provider/gateway adapter pattern; not Claude Desktop Chat/Cowork/Code or hosted Cloud. |
| Workspace | Tracked `.agent-farm/workspace.yaml`, trust review, project path, instructions/MCP connections | Repo/workspace ≠ ChatGPT Project/Section Group; no ChatGPT project parser. |
| Session graph | Per-run local UUID, native-session mapping, launch record, parent session id, trace/span IDs, worktree, turn/token/cost projection | Strong local observational model; `--resume` reopens the same harness, not a converter. |
| Export | Explicit session/launch roots, descendants, optional content consent, filtered logs/metrics and session metadata | Not importable/replayable: traces are explicitly left out; no importer or session writer. |
| Security | Telemetry local by default, content opt-in; keys referenced by env-var name | All agents start with approvals bypassed (`--dangerously-skip-permissions` / `--yolo`); filesystem is not sandboxed. |

Local validation: typecheck passed, 361/370 tests passed with 9 platform/tool skips, and a provider smoke test passed against a synthetic localhost gateway. See `docs/research/evidence/agent-farm-review-2026-11-21.txt`. License is unverified (no LICENSE/package license field).


### Agent Farm (`greenfield-inc/agent-farm`) — high-value CLI telemetry reference, no importer

| Surface | Observed source support | Nexus Memory disposition |
|---|---|---|
| Harnesses | Claude Code CLI and Codex CLI profiles/variants; custom base URL/API key env reference for each | Useful CLI provider/gateway adapter pattern; not Claude Desktop Chat/Cowork/Code or hosted Cloud. |
| Workspace | Tracked `.agent-farm/workspace.yaml`, trust review, project path, instructions/MCP connections | Repo/workspace ≠ ChatGPT Project/Section Group; no ChatGPT project parser. |
| Session graph | Per-run local UUID, native-session mapping, launch record, parent session id, trace/span IDs, worktree, turn/token/cost projection | Strong local observational model; `--resume` reopens the same harness, not a converter. |
| Export | Explicit session/launch roots, descendants, optional content consent, filtered logs/metrics and session metadata | Not importable/replayable: traces are explicitly left out; no importer or session writer. |
| Security | Telemetry local by default, content opt-in; keys referenced by env-var name | All agents start with approvals bypassed (`--dangerously-skip-permissions` / `--yolo`); filesystem is not sandboxed. |

Local validation: typecheck passed, 361/370 tests passed with 9 platform/tool skips, and a provider smoke test passed against a synthetic localhost gateway. See `docs/research/evidence/agent-farm-review-2026-11-21.txt`. License is unverified (no LICENSE/package license field).


### LocalVault (`inventlist/localvault`) — encrypted secret vault/MCP reference, not a session migrator

| Surface | Observed source support | Nexus Memory disposition |
|---|---|---|
| “Projects” / groups | Dot-notation groups for secret names inside vaults | Not ChatGPT Projects, Sections, or session hierarchy. |
| Import / sync | `.env`, JSON, YAML credential import; optional encrypted vault sync through InventList API | Does not import transcripts; service bearer token is not a model-provider API key. Never migrate secret values. |
| MCP / harnesses | stdio secret-management tools; installer documents Claude Code CLI, Cursor, Windsurf; Claude Code-only guard hook | Useful security pattern, not an MCP/config/session portability tool. Claude Desktop modes not verified. |
| “Session” | Eight-hour decrypted-vault-key cache | Not an AI conversation session, turn, branch, or subtask. |

**Disposition:** retain only as an adjacent secret-handling reference. The guard fails open, so do not treat it as the migration tool’s isolation boundary. License is unresolved: source README/LICENSE say Apache-2.0 while gemspec/RubyGems metadata say MIT. [Evidence](research/evidence/localvault-review-2026-11-21.txt).


### CueCards (`opencue/cuecards`) — high-value project-profile / asset-adapter reference, not a session migrator

| Surface | Observed support | Nexus Memory disposition |
|---|---|---|
| Project profile | One `.cue.profile` selector per working directory; YAML profile inheritance/composition for Skills, MCPs, plugins, persona, playbooks, gates | Useful per-project asset grouping pattern; not ChatGPT Project/Section or a nested Session tree. |
| Native runtimes | Claude Code CLI and Codex receive full content-hashed profile runtimes | No Claude Desktop Chat/Cowork/Code or hosted Cloud session. |
| Other agents | Cursor, Cline, Windsurf, Gemini, Antigravity, Copilot, Roo, Amp, Aider receive partial one-way Skills/rules + MCP outputs; Aider has no MCP | Good explicit adapter/capability-matrix reference; not full profile or transcript parity. |
| Session/log data | Local analytics events and transcript-derived Skill use/miss signals; session IDs and duration, redacted prompt snippet | No conversation event graph, parent/fork relations, attachments, token usage or resume/import/export. |
| Repo-only importers | Claude Code history, Copilot events, Hermes JSON → text examples for Skill evaluation | Developer-side dataset generation, not shipped and not a native Session writer. |

**Disposition:** shortlist as a strong adjacent profile/schema/adapter reference only. Current visible upstream core CI repeats `Grader sandbox failed to start`; a local isolated profile test subset passed, while the same eval-test failure reproduced locally. See [full evidence](research/evidence/cuecards-review-2026-11-21.txt).


### Herdr Agent Config Manager (`Phoobobo/herdr-agent-config-manager`) — Skills inventory/central links, not config or session migration

| Surface | Observed behavior | Nexus Memory disposition |
|---|---|---|
| Skills | Scans 11 named agent config roots; moves/copies skill dirs to `~/.agents/skills` and symlinks selected harnesses | Useful narrow Skills centralization pattern; not a cross-harness semantic translator. |
| MCP/plugins/hooks | Read-only inventory; MCP output summarizes name/source/transport plus command/args or URL; plugin and hook names/commands | No configuration import/export or target adapter. Redact output before model context. |
| Project/session hierarchy | No project/section/session graph, transcript import, or native session write | Not supported. |
| Safety | CLI mutations need `--apply`; organizer detects divergent skill conflicts, archive is reversible; TUI selection probe deleted a divergent unselected real copy | Do not use TUI selection on real copies until conflict preflight/archive protection exists. |

**Security note:** a temp canary appeared in `detect --json` for MCP args, URL query and hook command; environment values were not emitted. The bundled agent Skill recommends JSON inventory, so redact before AI handoff. [Full review](research/evidence/herdr-agent-config-manager-review-2026-11-21.txt).


### Smartsheet CLI Agent Power Tools (`smartsheet/cli-agent-power-tools`) — prompt resources, not session migration

| Surface | Observed support | Nexus Memory disposition |
|---|---|---|
| Agent/Skill-like resources | Six Markdown agent definitions each for Claude Code and Gemini CLI; host-specific YAML tool allowlists target Smartsheet MCP. | Useful test fixture for format-aware resource renderers; preserve source bytes and separately report host-specific semantics. |
| Claude Desktop modes | Smartsheet’s launch article documents the **Code Tab** reusing Claude Code agents. | Does not establish Chat or Cowork session/config import; do not mark all Desktop modes supported from Code Tab evidence. |
| MCP | Separate shell setup for Claude/Gemini registers a PAT-authenticated Smartsheet server. | MCP endpoint registration is not MCP configuration portability, API-key gateway migration, or conversation migration. Never transfer PAT values. |
| Projects / Sections / Sessions | No ChatGPT export, project/section graph, conversation events, branch/child-session tree, media, token ledger, or session writer found. | Not a migration engine or session fidelity benchmark. |
| Scheduling / automation | `USAGE.md` provides cron and CI shell examples around CLI invocations. | A usage recipe is not a native scheduled-task object or cross-harness scheduler adapter. |
| Safety / quality | Gemini variant has automated-chain instructions that conflict with its own explicit-approval rule; setup scripts remove current server before validating new credentials and pass credentials in process args. No test suite/workflow exists in the pinned tree. | Do not reuse prompt policies or setup scripts without independent review and adapter tests. |

**Disposition:** retain only as an adjacent prompt/MCP adapter reference. It shows that a portable agent resource needs a canonical body, runtime-specific manifest/permissions, chain policy and behavioral tests—not just copying a Markdown file. [Full evidence](research/evidence/cli-agent-power-tools-review-2026-11-21.txt).


### Lokalite (`RubenGlez/lokalite`) — credential references, not portable Sessions

| Surface | Observed support | Nexus Memory disposition |
|---|---|---|
| “Projects” and environments | Credential vault scopes are project → environment → secret; optional filesystem path; one active environment per project. | Useful for secret-dependency grouping only. Not ChatGPT/Codex Project, Section Group, Session, nested workspace, or branch graph. |
| MCP client configuration | Local writer for Claude Code, Claude Desktop, Cursor, Windsurf; manual JSON for other MCP clients. | A Claude Desktop MCP entry is not a Chat/Cowork/Code conversation importer or Cloud Session writer. No ChatGPT/Code/Cowork-specific restore. |
| Secret transport | `lokalite://` refs, local process injection, handoff script; secret values absent from MCP response. | Preserve names/references and request destination re-binding; never move secret values into transcript bundles. Not provider API-base/gateway routing. |
| Security | AES-256-GCM values + Keychain key; per-secret allow/block/approve/strict; activity log. | Valuable reference. Process-name `block` is best effort; values enter the agent-controlled shell after handoff; metadata plaintext. |
| Config mutation | Valid JSON entries are preserved; synthetic malformed-config test showed invalid file replaced with minimal Lokalite config. Default tool set also exposes `use_environment`. | Require parse errors to abort with backup/rollback; treat environment switch as a state-changing operation. |
| Platform / quality | macOS 14+, local build exit 0 and 180 tests pass; latest release v2.9.0. | No Windows path or cross-harness session fidelity metric. |

**Disposition:** high-value adjacent credential/security reference; exclude from the core session engine and migration-accuracy claims. [Full source and tests](research/evidence/lokalite-review-2026-11-21.txt).

## Claude Desktop on third-party inference (3P): all modes are now in scope

User-confirmed target: Chat, Cowork, and Code in Claude Desktop configured for a third-party provider/gateway (typically API key). Keep this separate from Anthropic-hosted Claude.ai/Cowork/Claude Code Cloud and from local Claude Code CLI. First-party docs now describe the official 3P app session stores and a source-specific import wizard: the wizard can import Claude.ai chats/projects and local earlier-install Cowork/Code data, but it is not a generic ChatGPT archive writer. It is a one-time copy, has attachment/project-folder caveats, and some state needs re-binding. Chat/Cowork UI is also gradually being unified, so adapters must capture actual mode/surface and client version rather than assume distinct UI modes always map to distinct session stores. Details and primary-source links: [`claude-desktop-3p-chat-cowork-code-2026-11-21.txt`](research/evidence/claude-desktop-3p-chat-cowork-code-2026-11-21.txt).

The first-party gateway contract requires streaming `POST /v1/messages` and tool use; `GET /v1/models` is optional, and prompt-cache breakpoints/usage need preservation. The built-in 3P import path is Claude-source-specific and version-gated; copying data between devices requires matching OS/app version and does not bring API keys, connector sign-ins, permission grants, Code environment values, or all plugin/settings data. Treat Chat/Cowork `local-agent-mode-sessions/` state/audit and Claude Code's JSONL transcript as separate schemas. No public ChatGPT archive importer or generic target-store writer was found. [Gateway](https://claude.com/docs/third-party/claude-desktop/gateway) · [Import](https://claude.com/docs/third-party/claude-desktop/import) · [Local data](https://claude.com/docs/third-party/claude-desktop/data-storage).

## Adjacent package manager only — nathfavour/anyisland (2026-11-21)

AnyIsland's manifest and SQLite registry describe installed developer tools, not a Harness Project, Section, conversation or session. Its integration Skill is for AnyIsland package distribution, and its shell-history path is an insecure plaintext mock rather than a verifiable encrypted archive. Do not use it to justify MCP/Skill or history migration support. The release workflow is not a migration test suite. [Pinned review evidence](research/evidence/anyisland-review-2026-11-21.txt).

## Ocul-PM — local work journal and agent observer, not a conversation migrator

`bunhine0452/Ocul-PM` (MIT, v4.11.2 at pinned `9dd0f85`) is an adjacent project-context/journal reference. Its watcher `Session` aggregates work time and file events plus a list of native agent session IDs; it does not encode turn order, message/tool-result payloads, branch/fork edges or a generic project/session import. `SessionId::imported()` has no production caller found in the reviewed tree; manual backdating is not a transcript importer. It offers no ChatGPT source or Claude Desktop mode-specific destination writer. Local macOS frontend/Rust tests passed (1,975 / 1,234), but upstream Windows portability has two spawn-budget test failures. A synthetic hook probe also confirmed raw prompt/assistant fields can persist with mode 0644 under umask 022; do not copy this raw-inbox behavior. [Full evidence](research/evidence/ocul-pm-review-2026-11-21.txt).

## Norte (`compilando/norte`): adjacent governed-operation journal

`norte` is a local file manager and MCP-backed file-operation engine, not a coding-agent transcript importer. Its persistent `<state_dir>/session.json` stores UI layouts, paths, cursor/history, marks, search and open panels. Its built-in assistant's `Reader`/`Order`/`Answer`/`Failed` turns are in controller memory (200-turn display cap; request history further capped) and are not fields in `SessionBody`. The separate agent `--session` label is `Actor::Agent` for policy, approvals and undo; the hash-chained `journal.db` records reversible file mutations, not prompts or conversation events. There is no ChatGPT Project/Section or conversation export/import path in the reviewed code.

**Disposition:** borrow only the separation of permission, operation audit, undo, UI-state persistence and provider credentials. Do not claim its `Session` or journal as ChatGPT/Codex migration support. Local test caveats: selected tests pass broadly but 3 host-dependent tests fail on macOS; the workspace gate fails to compile on macOS. Core/AI/MCP use AGPL-3.0-only while protocol/frontend crates are MIT/Apache. [Pinned source and test ledger](research/evidence/compilando-norte-review-2026-11-21.txt).


## MTIX (hyper-swe/mtix): task/context plane, not transcript transport

MTIX provides hierarchical epics/stories/issues/micro-tasks, agent sessions, MCP tools, task annotations/history and checksummed JSON board import/export. Its project is a task scope; no SectionGroup model was found. Its Session table stores agent/project/start/end/status/summary and task counts, not messages; node session_id associates work items, and context assembly is a parent-task briefing. First-party setup covers Claude Desktop, Claude Code, Codex, Cursor, Windsurf and pi, but that is MCP/briefing portability—not session import. Cowork is not documented here. Keep as an adjacent task-memory integration/reference, exclude from conversation fidelity scores. [Source/test review](research/evidence/hyper-swe-mtix-review-2026-11-21.txt).


## todo-cli (JoeyWangTW/todo-cli): Gemini task/tmux wrapper, not cross-harness session transfer

The app persists a flat task array (title/details/done/yoloMode/createdAt plus a tmux sessionName) and starts Gemini CLI with an initial prompt inside a tmux process. That sessionName is not a Gemini native conversation ID; the UI's last-50-line pane preview is volatile and there is no transcript reader/exporter/importer, ChatGPT Project/Section model, or Claude/Codex adapter. Gemini CLI has its own project-scoped resumable conversations, but todo-cli neither records their IDs nor calls resume. README treats Codex/Claude Code support as future work. Exclude from the migration engine; retain only as a task-to-live-process comparison. YOLO auto-approves tools; connected MCP servers inherit user permissions. [Source and local checks](research/evidence/todo-cli-review-2026-11-21.txt).


## Candidate evidence — CocoaSkills (2026-11-21)

ivanopcode/cocoaskills supplies project-local skill package/lock delivery across six code environments, but does not model or transfer conversation sessions. Its project MCP adapters cover Claude Code, Codex CLI, and Cursor only; they do not authenticate or launch services and do not provide a Claude Desktop Chat/Cowork connector. Keep Skills, MCP declarations, authenticated connectors, and ConversationSession as separate compatibility capabilities. Review and test each Claude Desktop mode independently. Detailed evidence: docs/research/evidence/cocoaskills-review-2026-11-21.txt.


## Candidate evidence — Conus (2026-11-21)

Pandusss/conus captures Claude Code/Codex sessions as agent_session_id plus project, turns, activity facts, and short prompt/answer excerpts, and gives tasks parent/child structure. It does not import/export conversations or parent/child Session graphs; session activity expires after 30 days. Gemini CLI receives MCP board tools but not equivalent hook session capture. Generic MCP connection is not a native Desktop adapter. Keep task hierarchy, agent-session tracking, message transcript, media, token usage, scheduled task, skill, and MCP configuration as separate compatibility features. Candidate evidence: docs/research/evidence/pandusss-conus-review-2026-11-21.txt.


## Candidate evidence — CData Google Ad Manager MCP (2026-11-21)

CDataSoftware/google-ad-manager-mcp-server-by-cdata is archived/deprecated and targets one data source through a local stdio MCP server. Its README documents a Claude Desktop MCP config, but its only registered tools are GetTables, GetColumns and RunQuery; it contains no assistant session/project schema or import/export path. It is a connector example only, not Claude Desktop session migration or compatibility across Chat/Cowork/Code. The separately installed CData JDBC driver and provider OAuth are external dependencies. Evidence: docs/research/evidence/cdatasoftware-google-ad-manager-mcp-review-2026-11-21.txt.

### `evoerax/awesome-harness-engineering` — discovery list only; no compatibility evidence (2026-11-21)

This Markdown catalogue is not an adapter and its harness checkmarks cannot populate the Nexus compatibility matrix. Current first-party docs contradict its Codex “no hooks,” OpenClaw “no hooks/MCP,” and Gemini CLI “no hooks/MCP” rows; the file provides no version date, source citation per capability, or tested conversion. Do not use its stated support percentages/counts or benchmark claims as fidelity scores. It also omits the user's confirmed Claude Desktop Chat/Cowork/Code target-session coverage and ChatGPT Project/Section import. [Source audit](research/evidence/evoerax-awesome-harness-engineering-review-2026-11-21.txt).

### sboorlagadda/artmark — adjacent artifact-memory reference only (2026-11-21)

Artmark adds a local catalog of canonical artifact pointers and retrieval cards, then delegates live-source access to the host harness. Its shipped Skill describes Codex and Claude Code local use; it has no ChatGPT Projects/Sections import, conversation graph, Claude Code session restore, Claude Desktop Chat/Cowork/Code adapter, MCP server, or target-native session writer. Do not score its lexical artifact search as session transfer fidelity. [Evidence](research/evidence/artmark-review-2026-11-21.txt).

### t59688/skillpack-manager — Skill assets only; path traversal reproduced (2026-11-21)

The adapter list maps 13 global Skill directories (including Claude Code, Codex, Cursor, OpenCode and Gemini) and can package/install/update skills. It does not establish actual harness activation or provide chat/session, ChatGPT Project/Section, Claude Desktop Chat/Cowork/Code, MCP, plugin, memory or schedule adapters. Synthetic local probes showed untrusted manifest `name` and `path` values escape the chosen target/pack roots; `audit` did not detect them. Do not treat this tool as safe for user data or as a production resource migrator until path containment is fixed and tested. [Evidence](research/evidence/skillpack-manager-review-2026-11-21.txt).


## `travelhawk/agentpm` — Skills/resource plane only (reviewed 2026-11-21)

| Plane | Observed support | Migration interpretation |
|---|---|---|
| Skills / agent definitions | Git/local/registry sources; generic, Codex, Claude target adapters; install records and project/global/workspace scope | Adjacent resource installer. Verify semantic behavior and per-mode activation separately. |
| Plugin packages | Claude Code and Codex marketplace integrations | Not a general plugin/MCP/session dependency converter. |
| MCP | Current plan says MCP config installation is out of scope | No automatic MCP server declaration, credential, consent, or restore mapping. |
| Projects / Sections / Sessions | No ChatGPT or Claude conversational project/section/session/message/branch importer or writer found | **Unsupported**; `agentpm.yaml` “project” denotes a resource contract only. |
| Claude Desktop | No Chat, Cowork, or Code session adapter found | All three user-confirmed modes require separate capability evidence and tests; a gateway/API key is not a session-import API. |
| Test status | Exact-SHA upstream Node 24 CI passed; local Node 26 suite had 273 passing tests and two package-resolution suite failures | Record as an unresolved local toolchain/test-resolution discrepancy, not as proof of migration fidelity. See `research/evidence/travelhawk-agentpm-review-2026-11-21.txt`. |


## `walidboulanouar/ay-claude-templates` — Claude Code extension manager, not session migration (reviewed 2026-11-21)

Published npm 1.0.0 compiled files were read and matched the reviewed vulnerable source paths; findings apply to the shipped artifact, not only the repository checkout. 

| Plane | Observed support | Migration interpretation / disposition |
|---|---|---|
| Skills, agents, commands, hooks, plugins, MCP-labelled packages, settings | AY marketplace install into `~/.claude` or `cwd/.claude`; OAuth-backed AY API; package metadata and version | Claude Code resource plane only; no cross-Harness semantic adapter or conversation/session restore. Not API-key/session migration. |
| Claude Desktop Chat/Cowork/Code | No Desktop paths or mode-specific adapters in source | Unsupported; keep the three modes separately assessed. |
| Claude Code custom config | `getClaudePaths()` hardcodes `~/.claude`; no `CLAUDE_CONFIG_DIR` read | Fails to follow current official custom config/history/plugin location behavior. |
| Project/Section/Session/Message/Branch/Attachment/Token/Schedule | No importer/exporter or conversation schema found | Unsupported; team workspaces are members/packages/settings lists, not chat hierarchy. |
| Safety | API slug is joined to the resource root without containment; synthetic actual-source install escapes that root. JSZip backslash entry projects outside the root on Windows; built-in `hook.sh` is rejected. | **Do not adopt/use on user directories or untrusted marketplace data** without path validation, Windows containment tests, and a coherent hook policy. See the full evidence/Poc record. |
| Verification maturity | No tracked `tests/` or `.github/workflows/`; `npm test` exit 127 (`vitest: command not found`); no GitHub Actions runs observed | No automated CI/test evidence. |


## `zavora-ai/macos-zlaunch-manager` — local launchd MCP, no session portability (reviewed 2026-11-21)

| Plane | Observed support | Migration interpretation / disposition |
|---|---|---|
| MCP | Local stdio JSON-RPC server exposing 19 `launchd_*` tools for macOS service management | OS-control connector, not a provider/Harness session adapter. Mutating tools are high impact; no server-side confirmation. |
| Claude Desktop | README shows raw local `claude_desktop_config.json`; project has no `.mcpb`/`manifest.json` package | Does not establish current Desktop Extension distribution or support across Chat/Cowork/Code. Current first-party guidance describes `.mcpb` install flow. |
| ChatGPT/Codex/Claude Code projects and sessions | No Project/Section/Session/message/transcript/branch importer, writer, or model found | **Unsupported**; no cross-Harness migration value. |
| Safety / tests | Actual-source temp POC: `launchd_create` label `../../escaped.poc` writes outside LaunchAgents. Release builds pass; Swift test exits 1 (no Tests target). Latest upstream release CI predates current head and omits MCP. | Exclude from engine; never auto-approve mutating launchd tools; require path containment and tests before reuse. |


## `ai-agent-manager/agent-manager` — strong Skills resource plane, no conversation restore (reviewed 2026-11-21)

| Capability | Observed support | Nexus interpretation |
|---|---|---|
| Skills | Versioned discovery bundles, Git/HTTP/artefact sources, optional SHA pins, system/repo scopes, six provisioners (`agents`, Claude Code, Cursor, Copilot, Kiro, Devin Desktop) | High-value `ResourceBundle`/`SourcePin`/`SkillInstall` reference; installs shared skill assets, does not prove semantic behavior in a target harness. |
| Agents / Projects | Atlassian Rovo `StudioAgent` provisioning; API Project carries team/tool restriction data | Provider-specific control plane; not ChatGPT/Codex conversational Projects or subagent/session hierarchy. |
| Claude Code plugins / MCP | Git importer scans Claude Code plugin marketplace `skills/` only; no plugin installer or MCP server/config adapter found | Skill extraction only, not plugin/MCP/connector portability. |
| Sessions / messages / memory / schedules | Local Session is UI bundle/auth/membership snapshot; no transcript/session graph/import/export | **Unsupported**; no ChatGPT/Codex or Claude Desktop Chat/Cowork/Code session adapter. |
| Quality | Exact v1.24.0 SHA CI + integration pass; local 1,366/1,368 root tests after UI build (two keychain backend failures); npm full audit 0 vulnerabilities. | Shortlist as a resource-plane comparator, not a migration engine. npm `latest` tag still points to 1.23.1 while 1.24.0 exists. |


## `omarmfouad25/google-marketing-agent` — domain MCP with unpublished safety PR, no session portability (reviewed 2026-11-21)

| Plane | Main v0.3.0 observed support | Nexus interpretation |
|---|---|---|
| MCP / Google APIs | 63 Google Ads, GA4, Search Console and Tag Manager tools; local OAuth credentials | Domain-specific tools, not provider session export/import. |
| Skills / plugin | 14 Google-marketing workflows in Claude Code plugin; Skills directory can be loaded by compatible clients | A domain Skill package; not cross-Harness memory or conversation context. |
| Write safety | Profile writes default false; with writes enabled, `confirm: true` directly applies. Main GTM `workspaceId` is interpolated without validation; custom segment may be created before the rest of its batch. | **Do not use v0.3 for unattended writes**; host permission alone is not a bound preview. |
| Open PR #1 (0.4.0) | Unmerged preview-ID/hash gate, optional MCP elicitation, strict-profile setting, GTM validation, drift-aware rollback; 272 tests pass on branch | Useful safety design lead only. `requireHumanApproval` must be enabled where a host cannot elicit; still no session migration. |
| Dependency state | Official `npm audit`: 17 production advisories (2 high); 20 full (2 critical dev/test). PR changes no dependency versions. | Require dependency updates and re-audit before credentialed deployment. |
| Sessions / Projects / memory | No conversation/session/project-section/import/export schema found | **Unsupported**; exclude from migration engine. |


## `SoonIter/skills-package-manager` — Skill directory distribution only (reviewed 2026-11-21)

| Capability | Observed support | Nexus interpretation |
|---|---|---|
| Skill sources | Pinned Git/GitHub, npm, local/link, and tarball Skill folders via `skills.json` | Reuse only as a narrow `ResourcePlane` source/revision/linking pattern. |
| Harness destinations | 45 hard-coded names map to skill directories; `linkTargets` allows custom paths | Path placement is not semantic resource conversion or a runtime compatibility guarantee. |
| ChatGPT/Codex Projects, Sections, Sessions | No project/session/message tree, branch/subtask, transcript, or import/export model | **Unsupported**; cannot migrate the requested project/session hierarchy. |
| Other resources | No MCP/plugin, memory, attachment/media, token/cost, or scheduled-task importer | Model these resource types separately; do not infer support from Skills or a `claude-code` path. |
| Claude Desktop / Claude Code Cloud | No separate Chat, Cowork, Code mode, or Cloud session adapter | **Unsupported**; keep all three Desktop modes separate in the matrix. |
| Quality / current state | 134/134 local tests and direct core/plugin builds pass; pnpm install blocked by unapproved build scripts. Latest v0.11.0 release 2026-06-05; two related PRs remain open. | Tests establish package behavior, not cross-Harness session fidelity or accuracy. Exclude as a migration engine. |

Review evidence: `docs/research/evidence/skills-package-manager-review-2026-11-21.txt`. Inventory now 75/303 reviewed / 228 unreviewed; next `AI-Colleagues/skill-mgr`.


## `AI-Colleagues/skill-mgr` — Skill lifecycle only; unsafe to adopt unchanged (reviewed 2026-11-21)

| Capability | Observed support | Nexus interpretation |
|---|---|---|
| Skill sources | Local directory or GitHub shorthand root/subpath; validates AgentSkills `SKILL.md` | Reuse only as a narrow `SkillProvisioner` pattern; GitHub ref follows current default branch without commit pin/provenance. |
| Harness targets | Five fixed local roots: Claude, Codex, Gemini, OpenClaw, Orcheo | No ChatGPT target or Claude Desktop Chat/Cowork/Code-specific adapter; a `~/.claude/skills` directory is not session compatibility. |
| Projects / Sections / Sessions / memory | No conversation/project/message model or import/export | **Unsupported**; cannot satisfy project/section/session hierarchy migration. |
| MCP / plugins / attachments / schedules | No resource model or adapter found | **Unsupported**; preserve as distinct resources in Nexus. |
| Code/test quality | 135/135 tests, 100% local statement/branch coverage; ruff, mypy, format pass; exact-commit PyPI provenance | Strong quality for its narrow feature scope; does not validate semantic cross-Harness fidelity. |
| Local install safety | POC shows local source symlink content is copied outside source root; same-name install replaces unmanaged target directory and deletes unrelated sentinel | **Do not auto-run on user roots unchanged**; require source link containment, ownership markers/conflict preview, and backup/rollback. |
| Licensing/activity | No LICENSE file or project license field found; PyPI 0.4.0/CI last observed 2026-04-24 | Treat reuse license as unresolved; scope is too narrow and safety gaps block direct adoption. |

Review evidence: `docs/research/evidence/skill-mgr-review-2026-11-21.txt`. Inventory now 76/303 reviewed / 227 unreviewed; next `bl1nk-bot/skills-cli`.


## `bl1nk-bot/skills-cli` — advertised Skill overlay, currently non-buildable; not a session migrator (reviewed 2026-11-21)

| Capability | Observed support | Nexus interpretation |
|---|---|---|
| Project/global Skills | README describes `./skills` over `~/.agents/skills`, per-agent symlinks; CLI source exposes basic install/list/uninstall but not the full documented update/all/merged-list surface | At most a conceptual ResourcePlane split; do not infer complete implementation from README. |
| Provider conversion / registry | `c2g` and `g2c` prototypes are not wired into the executable; registry returns stub search data and MCP pings | Not usable converters or a functional MCP service. |
| Projects / Sections / Sessions | No ChatGPT Project/Section/group or conversational Session/message/branch/subtask graph; `.blink/sessions` is BL1NK task execution state | **Unsupported**; cannot transfer requested hierarchy or resume conversations. |
| Claude Desktop modes / gateway | No Chat, Cowork, Code, Desktop 3P gateway, or local/self-hosted Claude Code transcript writer | **Unsupported across all three confirmed Desktop modes.** Keep client/gateway/runtime adapters distinct. |
| Build / security | Root cargo test fails at dangling doc comment after `--locked` refuses lock update; registry fails compile. Traversal test is ineffective; static path validation issues found but not exploited. | Reject as executable dependency. No migration accuracy metric applies. |
| Release / CI | No GitHub Releases; zip dependency PR #6 is still open; Clippy workflow has `continue-on-error: true`. | No trustworthy shipped version/green compile gate demonstrated. |

Review evidence: `docs/research/evidence/skills-cli-review-2026-11-21.txt`. Inventory now 77/303 reviewed / 226 unreviewed; next `CassianFlorin/skill-hub`.


## `CassianFlorin/skill-hub` — strong Skill ResourcePlane; no session migration (reviewed 2026-11-21)

| Capability | Observed support | Nexus interpretation |
|---|---|---|
| Skill storage / provenance | Separate managed store, project-discovered roots, runtime copies; lock records source, ref, resolved commit, checksum, targets and deployed runtimes | Strong adjacent pattern for `ResourceBundle`, `ResourceInstall`, provenance and deployment state. |
| Lifecycle / UX | Preview, holds, history, rollback, JSONL audit; native SwiftUI macOS front end shells out to JSON CLI | Useful CLI-GUI boundary and rollback UX reference; audit errors are best-effort, not a durable migration ledger. |
| Runtime adapters | Codex, Claude, Gemini and Hermes Skill directories; copy-based deployment | A `.claude/skills` target means Skills only; do not infer Desktop Chat/Cowork/Code or 3P gateway support. |
| Projects / Sections / Sessions | Discovers Skill folders under known local roots; no provider Project/Section/session graph, transcript or branch model | **Unsupported** for the requested ChatGPT Project/Section/Session migration. |
| Other transfer data | No MCP/plugin conversion, attachments/media, token ledger, memory or scheduled-task import | Separate adapters and loss accounting remain necessary. |
| Quality / safety | Exact-head CI #77 passed three platform jobs; local Go unavailable, npm wrapper 3/3; static file-symlink copy concern | Keep as a high-quality adjacent reference, not the transfer engine; set a symlink policy before ingesting untrusted roots. |

Review evidence: `docs/research/evidence/skill-hub-review-2026-11-21.txt`. Inventory now 78/303 reviewed / 225 unreviewed; next `Heretyc/subagent-mcp`.


## `Heretyc/subagent-mcp` — orchestration/handoff reference; no history migration (reviewed 2026-11-21)

| Capability | Observed support | Nexus interpretation |
|---|---|---|
| Sub-agent tasks | Interactive local Claude/Codex child drivers; `launch_agent`, `send_message`, `poll_agent`, `wait`, `kill_agent`; depth/prompt markers | Useful lifecycle/control-plane model, but no durable `parent_id`/child-session graph or import/export of child conversations. |
| Durable cross-turn context | One compact handoff per project/cwd key with session authorship/lifecycle; overflow file supported | Reuse only as a bounded summary checkpoint; not a raw transcript, attachments, or branch restore. |
| Usage/context telemetry | Latest session sample stores model, harness, source path, input/output/cache counts and context window | Useful token/context signal adapter idea; overwritten latest sample, no per-message cost ledger. |
| Direct API providers | Configurable base URL, model and env-key names; one non-streaming `/v1/messages` or `/v1/chat/completions` task request | Separate from Claude Desktop's third-party-inference session store; not a session writer or universal gateway guarantee. |
| Claude Desktop | Documented MCP-only wiring; no per-turn injection hook | MCP server presence does not mean Chat, Cowork, or Code session migration support. |
| ChatGPT Projects / Sections / Sessions | No reader/writer or graph model found in inspected CLI/MCP API | **Unsupported**; no message/branch/attachment import or migration accuracy score. |
| Quality | Build passes locally; Node26/macOS arm64 test suite 147/150 with three failures, reproduced in targeted run; prior PR #425 Ubuntu Node20 gate passed on pre-merge head; current main push run was not a test gate | Keep for architecture concepts, not code adoption without resolving integration/test portability and verifying target compatibility. |

Review evidence: `docs/research/evidence/subagent-mcp-review-2026-11-21.txt`. Inventory now 79/303 reviewed / 224 unreviewed; next `hiadamhere/spm`.


## `hiadamhere/spm` — Skill ResourcePlane only; source gap and overwrite risk (reviewed 2026-11-21)

| Capability | Observed support | Nexus interpretation |
|---|---|---|
| Skill distribution | Git catalogs, shared `.agents/skills` copy, host-specific Skill folder links, project/global scope, source commit tracking | Useful only as a target-path inventory and conceptual split between canonical Skill asset and per-host deployment. Folder presence is not runtime activation/fidelity. |
| MCP / Plugin | MCP exposes spm's own search/list/info/install/catalog operations; no generic MCP config or plugin-manifest conversion found | Do not confuse an MCP server interface with transfer of MCP declarations or call history. |
| Project / Section / Session | Public docs and decompiled 0.4.0 package contain no ChatGPT/Codex Project/Section/session/message/event/fork serializer | **Unsupported** for the requested conversation migration. |
| Attachments, branches, usage, memory, schedules | No media/attachment import, branch/subtask graph, token ledger, memory or timer/schedule adapter | Separate serializers/adapters and loss reporting remain necessary. |
| Claude targets | Claude Code skill path only; no Claude Desktop Chat/Cowork/Code session adapter or third-party gateway history writer | A `.claude/skills` entry is not Claude Desktop compatibility. |
| Source and quality | Public repo is docs/catalog/skill only; published NuGet 0.4.0's PDB SourceLink points to private `skills-package-manager-private` at unavailable SHA `742a52d...`; decompiled code shows possible replacement of real target directories; no public core tests | Keep as a weak reference only; do not reuse the installer until upstream source is available and conflict/rollback behavior is tested. No migration-accuracy score applies. |

Evidence: `docs/research/evidence/hiadamhere-spm-review-2026-11-21.txt`. Inventory **80/303 reviewed / 223 pending**; next `keynv-labs/keynv`.

## Candidate compatibility review — keynv-labs/keynv (2026-11-21)

| Surface | Observed support | Nexus disposition |
|---|---|---|
| Claude Code / Cursor text redaction | Raw text scanning/redaction for Claude Code JSONL and Cursor logs; local watcher and manual scrub | Adjacent privacy-plane reference only; not a data importer or serializer |
| ChatGPT/Codex Projects, sections, sessions | No archive reader, graph model, native writer, or migration tests found | No support |
| Claude Desktop Chat / Cowork / Code | No mode-specific store adapter; no third-party-inference session import path found | All three remain user-confirmed scope; this candidate covers none of them |
| Skills/MCP/plugins/memory/schedules | Secrets MCP tools and vault setup, not portable definitions/state migration | Do not count as resource/session portability |
| Safety and quality | 824 tests passed, 1 skipped, 10 TODO; typecheck/build pass; Biome lint fails on two format findings; audit reports 88 findings including 4 critical | Do not adopt directly; source warns of active append loss in watcher rewrite path |

The keynv watcher reads a transcript/log, scrubs in memory, then renames a temp file over the original; its own source calls out loss of a concurrent append. A completed JSONL parse does not establish semantic session preservation. Dependency audit findings identify vulnerable locked versions, not verified reachable exploitation. Full source and command ledger: [keynv-labs-keynv-review-2026-11-21.txt](research/evidence/keynv-labs-keynv-review-2026-11-21.txt).

## Candidate compatibility review — KRISH-exe-29/ai-agent-skill-router (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| Skills | Agent Skills folders; install guides for Claude Code, Codex, Cursor, Gemini CLI, Copilot, Antigravity, OpenCode and Windsurf/Devin; tested install using skills@1.7.6 | Useful ResourcePlane copy/install example, not cross-format conversion |
| MCP/plugins | Inventory records MCP server names only; Claude plugin metadata can be disabled through Claude CLI with undo | No transport/config/env/credential converter; plugin management is not Desktop session migration |
| Usage history | Opt-in read of Claude Code JSONL to aggregate selected tool/skill/agent/MCP names and timestamps | Not a transcript importer; no ChatGPT/Codex conversation history mapping |
| Project/Section/Session hierarchy | No project groups, message/branch graph, attachments, token/event ledger, memory or schedules | No support |
| Claude Desktop modes | Claude Code plugin/skill only; no Chat, Cowork, Code mode-specific store adapter or 3P gateway writer | All three modes remain in user-confirmed scope and require separate destination adapters/tests |
| Quality/safety | 3 local selftests/schema checks pass; exact-main CI passes. Per-item scope/hash/undo checks are useful. A macOS symlink-path CLI invocation is a silent no-op although canonical path passes. | Adjacent design reference only; fix path guard and test symlink launch variants before reusing scripts |

Full source and install reproduction: [ai-agent-skill-router-review-2026-11-21.txt](research/evidence/ai-agent-skill-router-review-2026-11-21.txt).

## Candidate compatibility review — nemesiscodex/pulse-tm (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| Tasks/project context | CLI, TUI and MCP manage tag-grouped tasks and one-level subtasks in project-root .pulse YAML | Adjacent TaskGraph/TaskContext model; not a provider Project or SectionGroup |
| Claude/Codex/other sessions | No session ids, messages, branches, attachments, tool-call transcript, token ledger, or import/export | No session migration support |
| Claude Desktop Chat/Cowork/Code / API gateway | MCP server can be configured as a task tool, but no mode-specific client session adapter or 3P gateway writer | All Desktop modes remain separate target scope |
| Quality | 21 synthetic/local tests pass, build passes; CI-defined typecheck fails after current dependency resolution; GitHub Actions has 0 runs and Releases has none | Do not shortlist as migration engine |
| Data integrity | YAML is directly rewritten synchronously; malformed YAML is treated as empty, then a subsequent add overwrites it | Preserve raw files and add parser recovery/atomic transactions before reusing the storage pattern |

Evidence: [pulse-tm-review-2026-11-21.txt](research/evidence/pulse-tm-review-2026-11-21.txt).

## Candidate compatibility review — rtaparay/Open-Skills-Manager (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| Agent Skills | Install/manage SKILL.md repositories in seven VS Code-based roots; discover local skills in .agents/.claude/.codex directories | ResourcePlane only; local folder discovery is not transcript/session support |
| ChatGPT/Codex Projects, Sections, sessions | No conversation/session archive model or importer/exporter | No support |
| Claude Desktop Chat/Cowork/Code and third-party inference | No client session adapter; product is a VS Code extension | No support; all three remain separate target modes |
| MCP/plugins/memory/schedules | No cross-client MCP/plugin config converter, credential transfer, memory or schedule migration | No support |
| Safety/quality | Collision copy removes existing target; static path escape from dot-only catalog names; npm audit finds vulnerable adm-zip 0.5.16; typecheck/compile pass but no tests/CI | Do not reuse installer/storage path unmodified |

Full evidence: [open-skills-manager-review-2026-11-21.txt](research/evidence/open-skills-manager-review-2026-11-21.txt).


## Candidate compatibility review — Spaztazim/lucid-context-engine (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| Host | OpenClaw ContextEngine plugin; configured external QMD shim for workspace retrieval | Narrow retrieval/context-injection plane only |
| ChatGPT/Codex Projects, Section Groups, Sessions | No reader, archive format, hierarchy model, or writer | Unsupported; cannot move the requested Destruction Era graph |
| Claude Code / Claude Desktop Chat, Cowork, Code / 3P gateway | No source or destination adapter for any of the confirmed modes | Unsupported across all three Desktop modes and local/API-key routes |
| Ingest / memory | ingest() returns ingested=false; assemble() reads QMD snippets and leaves input messages unchanged | Not a durable transcript or memory store; never substitute for the canonical event archive |
| Attachments, tools, usage, branches, MCP/plugins, schedules | No transfer schemas or readers/writers | Unsupported; no accuracy metric applies |
| Quality / dependency boundary | No tests, test script, CI workflow, release, or lockfile; current build checks could not start because tsc is absent | Reject as migration dependency; only a small retrieval integration can inform the optional Memory/Retrieval plane |

Evidence: [lucid-context-engine-review-2026-11-21.txt](research/evidence/lucid-context-engine-review-2026-11-21.txt).


## Candidate compatibility review — stefafafan/skm (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| Agent Skills | GitHub SKILL.md sources, project/global manifests, resolved commit+content lock, cached store, copy/link/wrap materialization | Historical ResourcePlane reference only; README/npm package are deprecated and repo is archived |
| ChatGPT/Codex Projects, Sections, Sessions | No transcript, Project/Section, Session/event, branch, subtask or import/export model | Unsupported; cannot migrate Destruction Era |
| Claude Code / Desktop Chat, Cowork, Code / 3P gateway | Only user-configured output folders such as .claude/skills; no client or gateway session adapter | Skill folder placement is not Claude session compatibility |
| MCP/plugins/memory/schedules/assets/usage | No corresponding resource or conversation transfer schemas | Unsupported |
| Safety / quality | 131 tests + lint pass; five format issues; symlinked project output path POC deleted an unmanaged canary outside project; production audit flags ws 8.19.0 (1 high, 1 moderate) | Do not reuse installer unchanged; no migration fidelity metric applies |

Evidence: [stefafafan-skm-review-2026-11-21.txt](research/evidence/stefafafan-skm-review-2026-11-21.txt).


## Candidate compatibility review — asm-cli/asm-cli (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| Skills | Central file store; symlink projection to configured Claude/Codex/Cursor/Gemini Skill roots | ResourcePlane pattern only; no session state |
| MCP | Imports selected Claude/Codex settings and injects config into Claude settings.json / Codex config.toml | Config transfer is not transcript transfer; no credential encryption or Claude Desktop runtime path |
| Plugins | Scans selected Claude/Codex plugin locations and symlinks packages | Limited resource support; not all Harnesses or Desktop modes |
| ChatGPT/Codex Projects, Sections, Sessions | No transcript, Project/Section, Session/event, branch, subtask or import/export schema | Unsupported |
| Claude Code / Claude Desktop Chat, Cowork, Code / 3P gateway | No session reader/writer; Desktop config path helper is test-only | Unsupported across all three Desktop modes and local/API-key routes |
| Safety / quality | Go tests/vet/build pass; no license file; confirmed --id path traversal and MCP localBinary prefix deletion in isolated temp probes; MCP secrets stored plaintext | Do not reuse code or run migration on untrusted profiles; require license resolution and path/transaction fixes |

Evidence: [asm-cli-asm-cli-review-2026-11-21.txt](research/evidence/asm-cli-asm-cli-review-2026-11-21.txt).


## Candidate compatibility review — b2amedina/omaset (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| Host | Omarchy v4.5+ local Linux settings via Quickshell UI, CLI, and stdio MCP | Narrow desktop-settings control plane, not a generic Harness adapter |
| ChatGPT/Codex Projects, Section Groups, Sessions | No conversation archive, project/section hierarchy, message/event/branch/subtask schema or importer/exporter | Unsupported; cannot move Destruction Era |
| Claude Code local / Claude Desktop Chat, Cowork, Code / 3P gateway | No session reader/writer; Claude Desktop config-path helper is test-only | Unsupported in every confirmed Desktop mode and API-key/gateway session path |
| Skills, MCP/plugins, memory, attachments, token/usage, schedules | MCP server exposes Omarchy settings; no cross-Harness resource bundle or conversation-associated state migration | Unsupported; night-light scheduling is a display setting, not an agent task |
| Quality | MIT and root LICENSE; 23/29 tests reported passing on disposable macOS compatibility copy; six failures involve BSD `wc`, absent locale fixture, or `setsid` | Retain only shared settings/control, atomic-write and undo ideas; not migration fidelity evidence |

Evidence: [omaset-review-2026-11-21.txt](research/evidence/omaset-review-2026-11-21.txt).


## Candidate compatibility review — dougrn/MCP-MegaBrain (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| MCP memory records | Rules, mandatory-spec directives, failure/fix “experiences”, golden snippets; local SQLite/FTS5; working stdio MCP tools | Adjacent MemoryPlane; requires an agent to call tools and is not automatic history migration |
| ChatGPT/Codex Projects, Section Groups, Sessions | No transcript import/export, hierarchy, branch/subtask, attachment, tool-event or usage schema | Unsupported; cannot move Destruction Era |
| Claude Desktop Chat, Cowork, Code / gateway; Claude Code Cloud | README shows a generic Claude Desktop MCP config, not mode-specific session stores; no gateway/archive adapter | MCP availability is not session restore; all three modes remain unverified/unsupported as migration targets |
| Project scoping and privacy | Project strings collapse to the basename; same-basename projects expose one another’s records in a reproduced in-memory probe; DB 0644 and data dir 0755 under umask 022 | Do not treat project labels as tenant boundaries; do not use its DB unmodified for private multi-project memory |
| Quality | MIT; locked local pytest 17/17; disposable MCP stdio e2e passed; no tracked CI workflows; README test count/schema-migration claim is stale/unverified | Keep as an adjacent prompt-memory pattern, not a fidelity or production security certification |

Evidence: [dougrn-mcp-megabrain-review-2026-11-21.txt](research/evidence/dougrn-mcp-megabrain-review-2026-11-21.txt).

 
## Candidate compatibility review — eddieran/skillpm (2026-11-21)

| Surface | Observed support | Nexus interpretation |
|---|---|---|
| Agent Skills | Seven marked verified and three best-effort filesystem targets; global/project manifests, lockfiles, dependency resolution and sync | Strong adjacent ResourcePlane reference; the current adapter contract copies files rather than invoking a native session API |
| ChatGPT/Codex Projects, Section Groups, Sessions | No conversation archive, session/event/fork graph, attachments or Project/Section importer/exporter | Unsupported; cannot move Destruction Era |
| Claude Code local / Claude Desktop Chat, Cowork, Code / 3P gateway | Claude Code Skill path is supported; no Claude Desktop mode/session writer or API-key gateway adapter | Skill-folder compatibility does not prove session restore; all three Desktop modes remain unsupported/unverified |
| MCP, Plugins, memory, schedules | No runtime transfer implementations; memory/scheduler docs are historical and removed from v4.0.0 | Unsupported |
| Quality / safety | Exact-HEAD CI and six-lane nightly E2E passed; security scheduled workflow fails at govulncheck; local scan reports 2 module-only x/mod findings. Temp POCs reproduced symlink write/read, ancillary injection scan gap, destination collision, crafted ref path escape and incomplete rollback | Keep design patterns only; do not adopt filesystem/security implementation unchanged |

Evidence: [eddieran-skillpm-review-2026-11-21.txt](research/evidence/eddieran-skillpm-review-2026-11-21.txt).


### Elixion-ai/claudepass (reviewed 2026-11-21)

| Capability | Observed support | Nexus Memory classification |
|---|---|---|
| Local secrets | Encrypted local Vault, Handle manifests, child-process injection/redaction; Claude Code plugin, Codex AGENTS snippet, local MCP stdio | Adjacent SecretPlane only; never a session/project importer |
| Projects / Sections / sessions / attachments / schedules / memory | No import/export or session graph; cloud sessions and relay explicitly out of scope | Unsupported |
| Claude Desktop modes | Local CLI plugin writer only; no account-backed Chat/Cowork writer or gateway/session relay. Official current matrix: skills load all three; hooks are ignored in Chat but load in Cowork/Code; local MCP is ignored in Chat | Keep Chat, Cowork and Code as separate adapters; plugin-folder similarity is not transfer fidelity |
| Platforms/security | Windows Broker unsupported; no per-session ACL; documented redaction gaps; local govulncheck found zero reachable symbols and one unused OpenPGP module advisory | Do not assume portability, authorization, or redaction is a sandbox |

Detailed review: [claudepass-review-2026-11-21.txt](research/evidence/claudepass-review-2026-11-21.txt).


### higherorderfunctor/nix-agentic-tools (reviewed 2026-11-21)

| Capability | Observed support | Nexus Memory classification |
|---|---|---|
| Context/rules/Skills/MCP/agents/hooks/settings | Declarative Nix modules for selected Claude Code, Codex, Kiro, Kimchi and Copilot surfaces; Home Manager/devenv emit different user/project placements with runtime-specific omissions | Strong ResourcePlacement/capability-matrix reference; configuration generation, not archive migration |
| Gateway inference | CPA-style instance/client-key/upstream-route config reaches Claude Code and Codex CLI | Useful local CLI gateway reference; not Desktop Chat/Cowork/Code session config |
| Projects/Sections/session hierarchy/attachments | No importer/exporter. Contains Kiro-specific research docs and a Claude CLI handoff design, not a cross-harness product | Unsupported by this repo |
| Kiro session source | Current package pins CLI 3.5.0; raw schema/probes are KAS 2.15.1/2.15.2. Official current CLI supports local V3 ZIP save/load and JSON scripts; cloud sessions are separate and local save/load is unavailable for cloud | Strong adapter research lead; version revalidation required before code |
| Build/platform | Exact-head CI passes Darwin/Linux package shards and Nix checks; local Nix unavailable; Windows is not the supported CI/build target | Solid Nix-centric reference, not universal macOS/Windows app |

Detailed evidence: [higherorderfunctor-nix-agentic-tools-review-2026-11-21.txt](research/evidence/higherorderfunctor-nix-agentic-tools-review-2026-11-21.txt).


### interrupted-sh/murk (reviewed 2026-11-21)

| Capability | Observed support | Nexus Memory classification |
|---|---|---|
| Secrets/API keys | Age-encrypted `.murk` repo vault, recipient/group/private scopes, expiring agent grants, CLI environment injection, masked output, optional MCP and client config | Adjacent SecretPlane; requires explicit grant/isolation policy |
| Projects/sessions/history/attachments/usage | No conversation, Project/Section, transcript, attachment or usage import/export | Unsupported |
| Security boundary | Same-user agents can read operator key/unset env flags; `murk_get` exposes values to model context; output masking is not a sandbox; pre-1.0 and not audited | Do not treat as per-session authorization or sandbox |
| Quality | Local workspace all-features tests, fmt, clippy pass; exact-HEAD Linux/macOS/Windows CI, advisories, fuzz and invariant checks pass | Strong adjacent implementation reference, not a migrator |

Detailed review: [interrupted-sh-murk-review-2026-11-21.txt](research/evidence/interrupted-sh-murk-review-2026-11-21.txt).


### jnMetaCode/skillet (reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Skills | Git/registry/local install of `SKILL.md` folders; default `.claude/skills/`; commit-pinned lockfile | Adjacent Skills AssetPlane reference; host semantics still need per-client tests |
| MCP | Three stdio tools: search, install registry Skill, list installed Skills; manual MCP config example | Connector/asset tooling only; not migration of MCP server definitions or credentials |
| Projects / Sections / sessions / artifacts / schedules | No reader or writer found; no transcripts, branches, attachments, tokens, memory, or schedules | Unsupported; not a session migrator |
| Claude Desktop modes / Claude Code API-key route | No mode-specific Chat, Cowork, Code or local/self-hosted session adapter | All three Desktop modes remain separate targets requiring independent adapters/tests |

Evidence: [pinned source and test review](research/evidence/jnmetacode-skillet-review-2026-11-21.txt).


### Josepavese/nido (reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Skills | One optional Codex-compatible `nido-vm-testing` Skill, manually copied; teaches VM operations | Adjacent Skill sample; no resource migration or mode-specific Desktop installer |
| MCP | Local stdio MCP exposes VM/image/template/blueprint/system and event tools/resources; registration block is printed, not automatically installed | Local resource/runtime control only; no remote API-key session endpoint or MCP-config migrator |
| Projects / Sections / conversation Sessions | Local VM, image, blueprint, template and event-resource hierarchy; no chat archive/import/export contract | Unsupported as conversation migration; “durable MCP session” means VM lifecycle calls |
| Snapshots / schedules | Disk-only snapshots require stopped VM; daily GitHub workflow refreshes image catalog | Not model-context checkpoints or user task schedules |
| Claude Desktop Chat/Cowork/Code / Claude Code API-key | No session reader/writer or mode-specific desktop adapter | Unsupported for context/session transfer; local MCP compatibility must be tested per mode |

Evidence: [pinned code, test and CI review](research/evidence/josepavese-nido-review-2026-11-21.txt).


### LiorStrugach/task-manager-mcp (reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Task / plan export | Flat tasks list, ordered plan list and plain notes; local JSON round-trip tested | Adjacent Task/Plan data-plane sample; not a conversation archive |
| MCP | Local tools/resources/prompts; documented Claude Desktop install uses mcp_server_fixed.py | Generic local MCP only; no API-key session endpoint or cross-harness config migration |
| Package/runtime quality | Tests fail collection (missing mcp_server); current MCP 2.3.0 import fails; wheel misses console entrypoint module | Reject as dependency until tests, package contents and SDK pin are corrected |
| Projects / Sections / Sessions / artifacts | No chat/session objects, ancestry, images, attachments, token usage, memory or schedule transfer | Unsupported for Nexus conversation migration |

Evidence: [pinned source/package/runtime review](research/evidence/liorstrugach-task-manager-mcp-review-2026-11-21.txt).


## Current target-scope check — Claude Desktop third-party gateway (2026-11-21)

| Destination | First-party documented surface | Transfer implication / verification boundary |
|---|---|---|
| Claude Desktop Chat | Third-party gateway uses a configured gateway base URL and credential; Desktop docs describe Chat requests using the Anthropic Messages API | A provider route does not import ChatGPT projects/conversations; keep gateway credential in OS secure storage/secret reference, not in session archive |
| Claude Desktop Cowork | Desktop 3P mode plus Projects/tasks/context/memory/scheduled tasks; source documents local-vs-cloud behavior and local sessions | Treat task session, project, project memory, attachments, connected local folder, and scheduled task as distinct nodes; validate on exact Desktop version/profile |
| Claude Desktop Code | Desktop passes its configured third-party provider into Code sessions; local Claude Code transcripts/project state are distinct from hosted Cloud sessions | Exercise its own session import/resume/project path, skills/MCP/plugins/hooks, credentials and file outputs separately |
| Local/self-hosted Claude Code CLI | Gateway route is configured independently from Desktop (e.g. `ANTHROPIC_BASE_URL` plus gateway credential); local transcript/settings directories remain distinct | Do not conflate CLI env config with Desktop's per-app `inferenceGateway*` configuration, or with Anthropic-hosted Cloud Code |

Official Desktop 3P source docs explicitly distinguish Chat, Cowork, Code and describe gateway requirements; the native import wizard imports Claude.ai archives plus local earlier Desktop Cowork/Code history, not ChatGPT exports. This remains a source-specific file-copy mechanism, not an official ChatGPT-to-Claude importer. Exact version and OS are still required; import docs flag 5.11492.0 and 5.1231.0 as behaviorally material cutoffs. No real target profile or private user session was opened. [Details and official source URLs](research/evidence/skillspp-review-2026-11-21.txt).

### omer-ayhan/skillspp (#98)

| Plane | Observed support | Nexus Memory classification |
|---|---|---|
| Agent Skills | Installs Markdown Skills into per-agent global/project paths | Adjacent ResourcePlane, not cross-Harness hierarchy/session migration |
| MCP | One exported `skills.validate` tool | Validation only, not MCP registry/session/config import |
| Projects / Section Groups / sessions / attachments / schedules | No source or target schema/reader/writer for these objects | Unsupported for the requested migration |
| Installer safety | Default GitHub hook execution and a reproduced destination symlink escape in disposable probes | Reject unchanged install implementation |

Evidence: [pinned source, tests and synthetic probes](research/evidence/skillspp-review-2026-11-21.txt). Registry progress: 98/303 reviewed, 205 pending; next `patterson-agents/cli`.


### patterson-agents/cli (#99, reviewed 2026-11-21)

| Surface | Observed | Nexus Memory classification |
|---|---|---|
| Skills/MCP/instructions/config | Canonical config IR, target emitters, CLI + stdio MCP projection; local config adoption | Useful independent ResourcePlane and safe-write design reference |
| Projects / Section Groups / sessions | `PattersonProject` means agent configuration; no conversation/session/attachment graph | Not a migration adapter; no session fidelity support |
| Claude Desktop Chat/Cowork/Code / 3P inference | No adapter; target list covers Claude Code and developer config targets, not Desktop Chat/Cowork | Unsupported for the confirmed three-mode Desktop destination |
| License/test gate | Internal-use proprietary license; exact-HEAD upstream Gate passed, local test not run | Do not reuse source; local quality evidence is indirect, not a local pass |

`init --import` is a config-adoption path for `.mcp.json`, instruction markdown and Claude settings, not a conversation export parser. [Pinned repo](https://github.com/patterson-agents/cli/tree/fca318f1dc775c017129cbf1856b96b7d1cfbcf4); [test Gate](https://github.com/patterson-agents/cli/actions/runs/31654277707); [detailed review](research/evidence/patterson-agents-cli-review-2026-11-21.txt).

Registry: 99/303 reviewed, 204 pending; next `rcdelfin/agentkit`.


### rcdelfin/agentkit (#100, reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Instructions | Global SYSTEM/AGENTS links for Pi, Claude Code, Codex, Gemini; Codex gets generated combined AGENTS.md | Narrow global ResourcePlane; no project/user scope graph or versioned config importer |
| Skills | 15 allowlisted Markdown-only Skills linked to Pi/Claude/Codex in opt-in mode | Skills-only projection, not MCP/plugin/session transfer; each included Skill needs its own license review |
| Projects / Section Groups / Sessions / attachments | None; no conversation import/export model | Unsupported for migration fidelity |
| Claude Desktop Chat/Cowork/Code / gateway | No target-specific adapter | Unsupported; no inference gateway or Desktop session routing |
| Reversibility | Regular-file backups restore; foreign symlinks can be deleted and fresh Claude wrapper can remain after unlink | Avoid running live until symlink ownership and residue behavior are fixed or explicitly accepted |

Evidence: [pinned source](https://github.com/rcdelfin/agentkit/tree/f5bb34e7e09799ca3a5191970e66864a96517583), [installer](https://github.com/rcdelfin/agentkit/blob/f5bb34e7e09799ca3a5191970e66864a96517583/setup.sh), [isolated-HOME probe ledger](research/evidence/agentkit-review-2026-11-21.txt).

Registry: 100/303 reviewed, 203 pending; next `rolecraft-sh/.github`.


### rolecraft-sh/.github (#101, screened 2026-11-21)

Organization profile only (`profile/README.md`); no Harness reader/writer or Project/Section/Session data model. It advertises a separate RoleCraft CLI; that core repository is already reviewed separately, so this page is not additional compatibility evidence. [Pinned profile repository](https://github.com/rolecraft-sh/.github/tree/a36eb962fc27a35d9c79ce0e3e1e3a0cadfe94ae/profile).


### rolecraft-sh/skills (#102, reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Agent Skills | 52 curated Markdown Skills with `author`, `slug`, `license` frontmatter; install flow delegates to separate RoleCraft CLI; README links to missing `skills/core/skill-orchestration` path | Content/ResourcePlane only; metadata validator is not a loader-fidelity test |
| Project/session hierarchy | No Project/Section/Session objects or transcript importer | Unsupported for hierarchy/history migration |
| MCP/plugins/memory/schedules | No import/export adapter | Unsupported |
| Claude Desktop Chat/Cowork/Code via gateway | No adapter; archived repo's linked core is a separate reviewed project | Unsupported for confirmed target |

Evidence: [pinned repository](https://github.com/rolecraft-sh/skills/tree/12b10bccadd7348235ee49bf4b18bc6729616e01) and [review ledger](research/evidence/rolecraft-skills-review-2026-11-21.txt).


### sergionoodles/skillshard (#103, reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Agent Skills | Global/project filesystem inventory; delegates install/update/remove to `skills` CLI; per-agent links and enable/disable | Adjacent Skill ResourcePlane manager only |
| `Project(PathBuf)` | Root path used to locate `.agents/skills` and Skillshard state | Filesystem installation scope, **not** a conversational Project or Section Group |
| ChatGPT/Codex Projects, Sections, Sessions, branches, events, attachments | No model, importer, writer, or recovery path found | Unsupported |
| Claude Desktop Chat/Cowork/Code 3P gateway and local Claude Code | No adapter or app-state writer found | Unsupported for confirmed target |
| Security and reliability | Partner risk lookup is advisory/fail-open; multi-step directory moves/links/state writes have no transaction journal in inspected operations | Do not treat as a security gate or migration transaction engine |
| Legal/test evidence | GitHub license metadata null/no `LICENSE`; release workflow only; local offline tests blocked by uncached `gpui-kit` | No source reuse; no local test-pass claim |

Disposition: reject as a Session/Project migration dependency. Retain only the independent product idea of a dedicated Skills ResourcePlane UI. [Pinned source](https://github.com/sergionoodles/skillshard/tree/05345c60ba4506add81eda1e3d97f0091738121c), [source review](research/evidence/skillshard-review-2026-11-21.txt).

### stefanvo78/cross-agent-memory (#104, reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Copilot CLI / local Claude Code / Gemini CLI | Stop-hook ingestion into local SQLite; extracted summaries, selected files/tasks/decisions and optional text checkpoint | Adjacent derived-memory adapter; does not restore native sessions |
| ChatGPT/Codex | README says planned; no parser is wired in CLI | Unsupported |
| Claude Desktop Chat/Cowork/Code via third-party inference | No Desktop store reader, writer, or app adapter | Unsupported for confirmed target |
| Project / Section / Session hierarchy | Project is inferred from Git remote or local folder; session table has no event/parent/fork/subtask edges or sidebar membership | Cannot preserve source hierarchy |
| Attachments / media / token usage / skills / MCP plugins / schedules | No canonical fields or transfer path | Unsupported |
| Git handoff | Up to 20 reduced summaries + knowledge entries, no raw checkpoints/embeddings, re-imported into local project DB | Lossy derived context plane only |
| Reliability/security | Gemini project attribution can fall back across all project dirs; setup replaces hooks; possible stale vectors on replacement; unauthenticated dashboard with no explicit loopback bind | Do not treat as production-safe migration writer without fixes and isolated tests |
| Legal / CI | package.json claims MIT but no LICENSE/GitHub licenseInfo; exact-HEAD GitHub Actions CI success; local tests not run | No source reuse until license file clarified |

Disposition: reject as a Session/Project migration dependency. Retain its local hook + searchable Handoff concept only as an independently implemented derived-memory plane. Exact source and risk evidence: [pinned GitHub repository](https://github.com/stefanvo78/cross-agent-memory/tree/df69336b661b417752647120e5a7d6c4f6ccff80) and [review ledger](research/evidence/cross-agent-memory-review-2026-11-21.txt).

### thesmart/install (#105, reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Agent Skill | Detects local OS/package-manager availability and guides package install/update/remove/search/list | Generic package-operation Skill only |
| Harness projects/sessions/memory | No source adapter, graph, canonical model, exporter or importer | Unsupported |
| ChatGPT/Codex / Claude Desktop Chat/Cowork/Code | No harness parser or mode-specific adapter | Unsupported for confirmed target |
| Security / operations | Explicit consent and privilege guardrails are positive; documented eval of machine output has a reproduced SHELL-based command-injection path | Do not execute or reuse as-is |
| Accuracy / quality | Reference includes nonexistent Go search subcommand; no tests or CI found | Low confidence across package-manager references |
| License | PolyForm Internal Use 1.0.0; forbids distribution/sublicensing | Cannot bundle in Nexus Memory without separate permission |

Disposition: reject as a Nexus Memory migration dependency. Retain only the high-level pattern of explicit consent before package operations, independently implemented and tested. [Pinned repo](https://github.com/thesmart/install/tree/91f5092e6adec840361875a72b0022d3290f94e2) and [review evidence](research/evidence/thesmart-install-review-2026-11-21.txt).

### weiox/skm (#106, reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Skills for Codex / Claude Code | Source-of-truth tree with personal/vendor packs; symlinked shared export entrypoints | Skill ResourcePlane only |
| ChatGPT/Codex Projects, Sections, sessions, branches, attachments | Explicitly out of scope; no history model or adapter | Unsupported |
| Claude Desktop Chat/Cowork/Code third-party provider | No Desktop store or session adapter | Unsupported for confirmed target |
| Sync and migration safety | Fake-home suite passes, but force sync deletes all contents of existing real entrypoint directories; independently reproduced in an isolated fake HOME | High data-loss risk without inventory/approval/backup |
| CI and license | No CI runs; no root LICENSE/GitHub license metadata found | No implementation reuse until licensing clarified |

Disposition: reject as a session migrator. Consider only the independently reimplemented source-tree/export-view idea for Skills. Do not equate Codex and Claude Code skill symlinks with cross-Harness project/session transfer. [Pinned source](https://github.com/weiox/skm/tree/cb2ab2e7ebca2668777f1168084eaff3dd76a132), [review evidence](research/evidence/weiox-skm-review-2026-11-21.txt).

### wess/loom (#107, reviewed 2026-11-21)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Skill packages | YAML manifests fetch Git or SHA-256-checked archives and install a SKILL.md bundle into a configured skill directory; defaults cover Claude Code, Codex, Cursor | Adjacent Skills ResourcePlane only |
| Projects, Sections, sessions, events, attachments, token use, memory, schedules | No schema, parser, importer/exporter, or session writer | Unsupported |
| Claude Desktop Chat/Cowork/Code via third-party inference; Claude Code API-key sessions | No Desktop mode/session store integration; "agent" config is just a skills-directory target | Unsupported for confirmed target |
| Safety | Isolated install probe deleted a foreign target marker; `name: ../outside` passed validation and installed beyond skills root, deleting a marker there | Reject as-is; path traversal and destructive overwrite reproduced only in temporary fixtures |
| Tests / CI / license | 15 Rust unit tests pass locally; exact-HEAD CI and Pages succeed; no install-path tests found; MIT | Source is license-compatible, but no migration fidelity evidence |

Disposition: reject as a migration dependency. Retain only independently implemented manifest, checksum, and resource-projection concepts; require canonical immutable digests, safe path allowlists, managed-target ownership, dry-run/approval, staging, and rollback. [Pinned source](https://github.com/wess/loom/tree/8da92268c6562bf59180492ceb40b65f5325c752), [source/test evidence](research/evidence/wess-loom-review-2026-11-21.txt).

### yearzen1/LocalSkillManager (#108, reviewed 2026-11-22)

| Surface | Observed support | Nexus Memory classification |
|---|---|---|
| Skills | Local Markdown/directory add, global/project `.agents/skills` copies, list/search/remove, group pull/push; strict names and symlink rejection | Comparatively strong narrow Skills ResourcePlane reference |
| Groups | Global TOML lists of Skill names and nested `@group` references, cycle/missing-reference detection; project scope is current working directory | Not ChatGPT Projects or Section Groups |
| Sessions, messages, branch/subtask/event graph, attachments, token use, memory, schedules | No schema, source parser, importer/exporter or writer | Unsupported |
| Claude Desktop Chat/Cowork/Code and Claude Code session data | No harness-specific store reader/writer; README only manages `.agents/skills` | Unsupported for confirmed target |
| Safety / verification | Strict path-safe Skill IDs, no-overwrite unless `--force`, atomic staging/rollback; 243 unit tests and 178 nonfailing CLI tests passed, but one upgrade permission CLI test fails; strict Clippy fails dead-code warning | Useful patterns, confidence limited by red full suite and no CI |
| License / release maturity | MIT; HEAD package 0.11.0, latest observed tag v0.9.1; no GitHub Actions runs | License-compatible source, but no migration fidelity evidence |

Disposition: retain only as a Skills ResourcePlane reference; reject as a cross-Harness migration dependency. A skill group is only a list of local resource IDs, not a Session hierarchy or Project Section Group. [Pinned source](https://github.com/yearzen1/LocalSkillManager/tree/809eb98210038fcf02c6eb386f3436e9db10fbc8), [review ledger](research/evidence/yearzen-localskillmanager-review-2026-11-22.txt).

### Discovery-only Skills catalog reviewed 2026-11-22

zhuyansen/awesome-agent-skills-managers expands the Skills/resource discovery layer by 177 net-new names, but has no source-to-target Project/Section/Session adapter or native restore proof. The directory categories are not Harness schemas. Keep external_readme_security_grade distinct from code audit/security review, retain per-repository license provenance, and rerun compatibility checks per exact app/mode/version. See research/evidence/awesome-agent-skills-managers-review-2026-11-22.txt.

### zongwu233/skillctl (#110) — Skills resource-plane only

It inventories SKILL.md roots for selected local runtimes and writes Claude/Codex enable switches; it does not adapt transcript/session/project graphs or Claude Desktop Chat/Cowork/Code. Do not claim Cloud session compatibility from its third-party CLI support. Its project-only Codex profile path resolves to user-global config, so profile scope is not portable as-is. Review evidence: research/evidence/zongwu233-skillctl-review-2026-11-22.txt.

### zzj1965186613/agentforge (#111) — local Markdown Skills only

The available adapters target Claude Code commands, Cursor, Copilot, Aider, and Hermes; no Codex, Claude Desktop modes, session data, Project/Section graph, or API-key Cloud session path exists. The marketplace client is a stub, so search is only for bundled/installed local Markdown. Do not equate its generic AgentForge package or pip install agentforge with the MIT GitHub repository: the PyPI slug currently identifies an unrelated GPL project. See research/evidence/agentforge-review-2026-11-22.txt.

### AidarKhusainov/agent-skills-manager (#112) — Agent Skills only

One stateless Codex/ChatGPT plugin for selected GitHub `SKILL.md` resources; no runtime session store, Project/Section/Session schema, history importer/exporter, or Claude Desktop Chat/Cowork/Code / Claude Code adapter. The manual E2E matrix is not yet executed. Keep its approval/preservation/provenance patterns as a narrow ResourcePlane reference only. [Review evidence](research/evidence/agent-skills-manager-review-2026-11-22.txt).

### akhenda/inline-commenting-convention (#113) — portable prose, not data portability

The MIT repository provides one Codex-style code-comment/JSDoc Skill and manually copied AGENTS.md/CLAUDE.md snippets. It has no executable importer/exporter, state format, session graph, or Claude Desktop mode adapter. Use only as optional coding-instruction content; do not count it as cross-Harness Session support. [Review evidence](research/evidence/akhenda-inline-commenting-convention-review-2026-11-22.txt).

### All-The-Vibes/ATV-PaperBoard (#114) — report output only

Native wrappers exist for Claude Code CLI, Codex CLI, Copilot CLI, plus Copilot Coding Agent Actions. The core only converts JSON/Markdown inputs into HTML/design/meta artifacts in per-harness directories; “sections” are report-layout sections, not ChatGPT Section Groups. There is no conversation/session parser or target restore. Cross-harness artifact aggregation is a stated non-goal. Keep only optional report presentation and thin adapter patterns. [Review evidence](research/evidence/atv-paperboard-review-2026-11-22.txt).


### Skills package managers are not SessionGraph adapters — Reno (#115)

Reno manages Agent Skill files for a few local CLI harnesses. Its central inventory/store is an adjacent ResourcePlane pattern only; it has no ChatGPT Projects/Section Groups/session graph or Claude Desktop Chat/Cowork/Code importer. Do not infer plugin/MCP capability from README flags: the install path handles Skills only. Security probes found traversal, symlink scan/copy mismatch, fail-open file truncation and nested rollback loss. Keep external resource ingestion isolated and fail closed; see research/evidence/reno-review-2026-11-22.txt.

### Narrative handoff is not transcript portability — cross-harness-sync (#116)

This protocol can project an agent-authored project snapshot to any harness that can read files and run git, but provides no platform-specific ChatGPT or Claude Desktop session adapters. It preserves selected narrative state, not message IDs, branch/subtask graphs, attachments, token usage, memory stores or schedules. Treat Claude Code / Codex / Cursor examples as file+git interoperability, not fidelity-tested session compatibility. Current main also has OS and state-safety defects; PR #7 is draft only. Evidence: research/evidence/cross-harness-sync-review-2026-11-22.txt.

### Skill-resource management is not SessionGraph migration — cagedbird-org/skills (#117)

The pinned Go CLI models desired manifest, exact commit/content lock, installed Skill files and symlink mirrors. It has no ChatGPT Project/Section/Session import, message graph, attachments, usage, schedule or Desktop mode adapters. `go vet`/race tests/build passed, but a synthetic manifest entry named `..` escaped its target and removed a sibling sentinel in a temporary directory. The public owner repo is archived; keep only the resource pin/drift-report pattern after fixing traversal, not the implementation or overwrite policy. Evidence: `research/evidence/cagedbird-skills-review-2026-11-22.txt`.

Primary: 117/303 reviewed, 186 pending; 177 supplemental pending; 363 combined primary + supplemental pending excluding manual additions. Next: Dark-Ohm/pz-mod-manager. Research remains incomplete.

### PZ Mod Manager is an MCP product, not Harness migration — Dark-Ohm/pz-mod-manager (#118)

The working MCP server exposes a JSON-schema tool surface over the same CLI command table, but its 50 tools administer Project Zomboid servers/mods/profiles. `.pzpack` carries game mod order and server connection state, not AI conversations. No Project/Section Group/Session import or Claude adapter exists. Test suite: 62 pass/4 ignored; release build succeeds with 26 warnings. Exclude it from migration dependencies; retain only generic tool-registry/readOnly-hint patterns. Evidence: `research/evidence/dark-ohm-pz-mod-manager-review-2026-11-22.txt`.

Primary: 118/303 reviewed, 185 pending; 177 supplemental pending; 362 combined primary + supplemental pending excluding manual additions. Next: ebenhzr1/agent-smith. Research remains incomplete.

### Skill package metadata is not Harness integration — ebenhzr1/agent-smith (#119)

This MIT prototype advertises Claude/OpenAI/Gemini/Cursor, but the installed target is always its own `~/.agent-smith/skills` directory; it has no SessionGraph or native host adapters. Isolated tests found remote installs create a stub after fetching only the registry JSON, publish saves locally, and a destination symlink lets installation write outside the advertised sandbox. CI unit tests pass 28 but omit install/publish; lint/Prettier fail and are non-gating. The README’s npm package name is owned by an unrelated CLI. Exclude as a migration dependency; retain only generic semver metadata. Evidence: `research/evidence/ebenhzr1-agent-smith-review-2026-11-22.txt`.

Primary: 119/303 reviewed, 184 pending; 177 supplemental pending; 361 combined primary + supplemental pending excluding manual additions. Next: erdemtuna/craft. Research remains incomplete.

### A reproducible Skill dependency manager is not a Session migrator — erdemtuna/craft (#120)

Craft's MVS/subpath selection, signed versioned release, commit+integrity pinfile and project/global resource split are high-value ResourcePlane references. It only targets Claude Code and Copilot by detection (or a manually supplied path) and contains no Project/Section/Session, transcript, media, MCP/plugin or memory transfer. Pinned v0.5.0 tests/vet/build pass, but current go-git, go-billy and x/crypto dependencies have govulncheck-reachable advisories, including path traversal/symlink and credential handling; the open PR also documents an off-by-one total-dependency limit. Keep architecture ideas, not the current binary. Evidence: `research/evidence/erdemtuna-craft-review-2026-11-22.txt`.

Primary: 120/303 reviewed, 183 pending; 177 supplemental pending; 360 combined primary + supplemental pending excluding manual additions. Next: eugen1408/skill-sync. Research remains incomplete.

### Skill Sync is a Skill UX/adapter, not session portability — eugen1408/skill-sync (#121)

The Electron app centralizes official/Git/local Skills, a canonical `.agents/skills` store and links to a static 72-agent table. It can inspire a ResourcePlane UI, but its table lists only Claude Code (not the three Claude Desktop modes), and it has no Project/Section/Session, MCP, plugin or memory importer. The 274-test suite passes, yet npm audit reports two high production dependencies and an isolated failed-reinstall probe showed the existing canonical skill is deleted before a replacement copy succeeds. Evidence: `research/evidence/eugen1408-skill-sync-review-2026-11-22.txt`.

Primary: 121/303 reviewed, 182 pending; 177 supplemental pending; 359 combined primary + supplemental pending excluding manual additions. Next: Hardt-LLC/AgentPack. Research remains incomplete.

### AgentPack validates extension/config portability, not chat-session portability — Hardt-LLC/AgentPack (#122)

Its 18 targets, canonical Skills/MCP/instructions/hooks/plugin metadata, capability labels and reversible sync may serve as a ResourcePlane reference. The canonical pack/schema has no Project/Section/Session graph or transcript/event/media/token/schedule serializer; import and collection concern native config. The single `claude` target is Claude Code—none of Claude Desktop Chat, Cowork or Desktop Code has a separate adapter, so those three target projections remain uncovered. Despite green tests/typecheck/lint/build (487 tests), the target matrix is not evidence of session compatibility. `pnpm audit --prod` against npmjs reports two high and one moderate vulnerable production dependency advisories; do not reuse unpatched parsers for untrusted imports. Evidence: `research/evidence/hardt-llc-agentpack-review-2026-11-22.txt`.

Primary corpus: 122/303 reviewed, 181 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 358 excluding manual additions. Next primary candidate: harsha-pyla/skillhub. Research remains incomplete.

### SkillHub's Skills are not Projects or sessions; claimed paths need per-Harness proof — harsha-pyla/skillhub (#123)

This four-target CLI manages `SKILL.md` copies and a tiny lockfile only; it cannot move ChatGPT Project/Section/session hierarchies or transcripts, MCP, plugins, memory or schedules. Its static path table has no path tests; repository source uses `.github/copilot/skills` and `~/.gemini/config/skills`, while current GitHub/Gemini docs use `.github/skills`/`.agents/skills` and `~/.gemini/skills`/`~/.agents/skills`; its Codex `.codex/skills` path needs validation against the current `.agents/skills` CLI guidance. Claude Code `.claude/skills` is not automatically a Cowork/cloud-skill channel: vendor docs describe account-synced Skills for Cowork/cloud. Keep all three Claude Desktop modes separate and mark paths unsupported until tested on the user's third-party-provider Desktop version. Source-level install/remove path flaws also make this a no-reuse security case. Evidence: `research/evidence/harsha-pyla-skillhub-review-2026-11-22.txt`.

Primary corpus: 123/303 reviewed, 180 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 357 excluding manual additions. Next primary candidate: Hayatelin/skillhub. Research remains incomplete.

### Hayatelin SkillHub is a Skill tool, not session portability — unsafe archive install (#124)

The four target directories are conventions, not session adapters, and do not include the requested Claude Desktop modes. The `~/.skillhub/skills` “global” list is not a native location and there is no global install flag; Codex's current official install guidance uses `.agents/skills`, not the candidate's `.codex/skills`. More importantly, an offline proof with a symlink chain demonstrated `safe_extract_tar()` writing a tar member outside its temporary destination on CPython 3.12, while the repo claims Python 3.8+ and CI covers 3.8/3.11. Its only archive regression test checks a literal `../` filename. Keep lint/scaffold/catalog UX only; block use as a trusted cross-harness installer until tar symlink escape and overwrite rollback are fixed. Evidence: `research/evidence/hayatelin-skillhub-review-2026-11-22.txt`.

Primary corpus: 124/303 reviewed, 179 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 356 excluding manual additions. Next primary candidate: jniltinho/ad-manager. Research remains incomplete.

### “Session” and MCP name collisions are not session migration — jniltinho/ad-manager (#125)

This candidate's MCP tools and “sessions” operate Windows/Samba Active Directory, SMB client connections, user/group/OUs, shares, backups and directory migration. It exposes no LLM conversation, Project/Section tree or Claude destination writer. Treat as an unrelated MCP server, not a source/target Harness. Evidence: `research/evidence/jniltinho-ad-manager-review-2026-11-22.txt`.

Primary corpus: 125/303 reviewed, 178 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 355 excluding manual additions. Next primary candidate: Juliusolsson05/agent-manager. Research remains incomplete.

### Agent Manager's targets do not imply Projects/Skills/session compatibility — Juliusolsson05/agent-manager (#126)

Only Markdown commands/prompts and stdio MCP fields are represented; no Skills, plugin bundle, remote HTTP/OAuth MCP, Project/Section/Session graph or Claude Desktop Chat/Cowork/Code adapter exists. OpenCode current docs expect `opencode.json(c)` with `mcp.servers` and typed local/remote objects, but this adapter writes `.opencode.json` with `mcpServers`; Codex removal fails on `config.toml`. The test command prints TODO and exits 0, so no live adapter fidelity has been proven. Temp probes found command name path traversal and plaintext env storage. Evidence: `research/evidence/juliusolsson05-agent-manager-review-2026-11-22.txt`.

Primary corpus: 126/303 reviewed, 177 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 354 excluding manual additions. Next primary candidate: KAFKA2306/agent-resources. Research remains incomplete.


## 2026-11-22 — mode reconfirmation and Cowork locality split

The user confirmed Chat, Cowork, and Code are all target surfaces, but the adapter key must be logical rather than a hard-coded UI tab: Anthropic is rolling Chat and Cowork into one conversation experience, while Code remains separately surfaced. Cowork Projects group instructions, context, scheduled tasks and memory and can be used from Chat/Cowork; the current Projects help page says Projects are not yet available in Claude Code. In the account-based consumer deployment, Cowork tasks are cloud-executed by default for Pro/Max/Ultra since 2026-10-06, whereas earlier local tasks remain local and local files require the Desktop app to be open. These are not the same thing as the third-party-inference Desktop deployment, whose gateway key routes inference to an external `/v1/messages` provider and whose local data store separates Chat/Cowork session folders from Code transcripts.

Compatibility rows therefore need two independent axes: `(deployment: Claude Desktop 3P gateway | account-hosted Cowork | local/self-hosted Claude Code)` and `(logical surface: Chat | Cowork | Code)`, plus OS/version and task locality. The built-in 3P import documents copies from Claude.ai and earlier Claude Desktop sessions, not arbitrary ChatGPT exports. Do not infer that an API key can create or resume Anthropic-hosted Cowork sessions, or that a Claude Code transcript writer creates a native Chat/Cowork conversation. Sources checked 2026-11-22: [3P gateway](https://claude.com/docs/third-party/claude-desktop/gateway), [3P local data](https://claude.com/docs/third-party/claude-desktop/data-storage), [3P import](https://claude.com/docs/third-party/claude-desktop/import), [Cowork Projects](https://support.claude.com/en/articles/14116274-organize-your-tasks-with-projects-in-claude-cowork), [Cowork rollout/locality](https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile), [Chat/Cowork unification](https://support.claude.com/en/articles/16761823-claude-cowork-and-chat-are-one-claude).

## Candidate #127 — KAFKA2306/agent-resources: Skills-only compatibility

This repository's `agr` target named `claude` is Claude Code CLI's `.claude/skills` directory, not Claude Desktop. `agr` currently represents dependency type `skill` only; its one-off `agrx` runner starts a CLI and cleans up a temporary Skill. It does not create a ChatGPT-to-Claude conversation or project graph, nor write Claude Desktop 3P Chat/Cowork/Code state. The Codex path table still uses `.codex/skills` while current OpenAI developer docs show `.agents/skills/`; OpenCode V2 prefers `.opencode/skills/` while retaining old-path discovery. Even Skills-path presence is therefore a per-version fixture/runtime test, not “perfectly compatible.” Evidence: [candidate review](research/evidence/kafka2306-agent-resources-review-2026-11-22.txt); [Codex paths](https://developers.openai.com/api/reference/cli); [OpenCode Skills](https://opencode.ai/docs/skills/).

Primary corpus: 127/303 reviewed, 176 pending; 177 supplemental net-new pending; combined primary + supplemental pending: 353 excluding manual additions. Next: `kayaman/agentskills`. Research remains incomplete.


## Candidate #128 — `kayaman/agentskills`: path presence is surface-specific

The manager detects Cursor, Claude Code, Codex, GitHub Copilot, Amp, Cline, Continue and Kiro, but writes only `.agents/skills/` / `~/.agents/skills/`. Current official documentation verifies `.agents/skills` for Codex, Cursor and Copilot; OpenCode V2 also loads its `.agents/skills` compatibility path. Claude Code instead documents project/personal `.claude/skills`, and its docs say Cowork/cloud sessions load account-enabled Skills rather than local `~/.claude/skills`. Thus the manager's Claude Code/Claude Desktop compatibility is unverified and should not be counted from marker detection; no client-level test was run. [Codex](https://developers.openai.com/api/reference/cli) · [Claude Code](https://code.claude.com/docs/en/skills) · [Cursor](https://cursor.com/docs/skills) · [Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills) · [OpenCode](https://opencode.ai/docs/skills/).

Candidate does not model ChatGPT Projects, Section Groups, transcripts/session graphs, attachments/tokens, MCP, general plugins, memory or schedules. More importantly, the lock omits pinned refs and its update flow defaults back to `main`; a temp-only probe confirmed deletion outside `.agents/skills`, and a failed reinstall deletes the previous Skill while leaving the old lock; a forced update fetch failure also returns exit 0 with a misleading “up to date” message. Hash tests reproduced false equality for files differing only in dotfiles and for path/content framing collisions. Local Rust tests and release build pass, but rustfmt and strict Clippy do not. Keep only format/registry concepts. [Review](research/evidence/kayaman-agentskills-review-2026-11-22.txt).

Primary corpus: 128/303 reviewed, 175 pending; 177 supplemental net-new pending; combined pending: 352, excluding manual additions. Next candidate: `kayaman/skillz`.


### Current native Skills manager comparator (2026-11-22)

GitHub CLI `gh skill` is documented in public preview for CLI v2.90.0+, including target host and scope, `@TAG`/`@SHA`, `--pin`, source/ref/tree-SHA provenance, and a preview-before-install workflow. This is a useful native Skills-plane comparator and can reduce duplicate adapter logic after version testing; it provides no ChatGPT Project/Section or Session import. `kayaman/agentskills` PR #6 remains open/unmerged; latest visible PR CI passed, but Copilot review recommends changes because the default repo lacks the advertised bare-name Skill. [GitHub CLI Skills docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) · [PR #6](https://github.com/kayaman/agentskills/pull/6).


## Candidate #129 — `kayaman/skillz`: no native migration adapter

The Python sibling uses the same shared `.agents/skills` path as candidate #128 and does not serialize into each detected harness. Current Claude Code documents `.claude/skills`; neither candidate has a Claude Desktop Chat/Cowork/Code writer. It has no Project/Section/session/MCP/plugin/memory/schedule conversion. Local tests pass, but source-level probes show unvalidated remove paths, destructive non-transactional replacement, hashes that miss hidden files/collide, update failures that exit 0, stale lock metadata, and temp-dir leakage after update installation failure. Not a safe migration dependency. Evidence: `research/evidence/kayaman-skillz-review-2026-11-22.txt`.

Primary corpus: 129/303 reviewed; 174 pending; 177 supplemental net-new pending; combined pending 351 excluding manual additions. Next candidate: `MaNongJSZ/SkillHub`.


## Candidate #132 — `msking18/cognitive-personas`: no Claude Desktop session writer

The repository offers an Antigravity plugin and a Claude Code `.claude/` output-style bundle (plus Cursor/Roo/Copilot adapters). Its list of cross-harness instruction adapters does not establish native session import: it contains no ChatGPT Project/Section/Session model, no transcript graph or attachment/tool provenance serializer, and no Claude Desktop 3P Chat/Cowork/Code storage adapter. The `agent-memory-mcp` v3.2 additions are proposed only. A test-backed hook gate is not dependable approval state: it records the marker before asking, permits the second matching action, emits `ask` rather than `force_ask`, and fails open on malformed/error input. Do not count this as a SessionGraph or native Desktop compatibility result. Evidence: `research/evidence/msking18-cognitive-personas-review-2026-11-22.txt`.

Primary corpus after candidate #132: **132/303 reviewed, 171 pending**; 177 supplemental net-new pending; combined pending **348** excluding manual additions. Next primary candidate: `ngmkhoi/tavily-mcp-manager`.


## Candidate #133 — `ngmkhoi/tavily-mcp-manager`: Claude Code only, no Desktop gateway

This candidate generates/installs one Tavily MCP server for Codex, Claude Code CLI, Gemini CLI and OpenCode. The “claude” adapter uses the Claude Code CLI's user scope and `~/.claude.json`; it does not target Claude Desktop's third-party-inference config or its Chat, Cowork, or Code logical surfaces. It transfers neither general MCP/plugin settings nor ChatGPT Projects, Section Groups, Session graphs, transcripts, media, memory or schedules. Current Claude Code docs distinguish local/user `~/.claude.json` from project `.mcp.json` and their scope/approval semantics ([official MCP docs](https://code.claude.com/docs/en/mcp)). Keep only the narrow secret-store patterns; fallback config writer is unsafe for reuse because it overwrites an existing entry without force and resets config/backup file modes under a normal umask. Evidence: `research/evidence/ngmkhoi-tavily-mcp-manager-review-2026-11-22.txt`.

Primary corpus after candidate #133: **133/303 reviewed, 170 pending**; 177 supplemental net-new pending; combined pending **347** excluding manual additions. Next primary candidate: `nicolavalenti/mem`.


## Candidate #134 — `nicolavalenti/mem`: three transcript readers, no Desktop modes

The project ingests plain transcript text from Claude Code, Pi, and Codex session files into a local semantic store. Its `claude` path is the CLI's `~/.claude/projects` tree, not Claude Desktop third-party-inference Chat/Cowork/Code. It has no ChatGPT export reader, Project/Section membership, event/branch/parent-child graph, media/tool/token preservation, resource/plugin/schedule migration, or target-specific Desktop writer. `resume.py` prints stored Markdown handoffs; it does not restore a Pi/Codex native session. A synthetic Pi handoff emitted `claude --resume <Pi session id>`, showing the resume hint is not harness-aware. Also, the local embedding database is separate from idle summary calls to the configured Claude CLI model. Evidence: `research/evidence/nicolavalenti-mem-review-2026-11-22.txt`.

Primary corpus after candidate #134: **134/303 reviewed, 169 pending**; 177 supplemental net-new pending; combined pending **346** excluding manual additions. Next: `Primuez/skill-installer`.


## Candidate #135 — `Primuez/skill-installer`: Skill-only and license-blocked

The candidate writes a `SKILL.md` folder to one generic skills directory and may back it up to GitHub/GWS. It has no ChatGPT Project/Section/Session graph, conversation restore, MCP/plugin/credential, memory/schedule migration, or Claude Desktop 3P Chat/Cowork/Code writer. Runtime badges and the shipped meta-SKILL do not establish a tested adapter matrix. The only integration is an individual skill installer workflow. Security and license review also disqualify its writer: nonzero scanner failure can be reported SAFE, a `/tree/` URL becomes HTML content, `../` escapes the skills root, and the governing license is proprietary/non-commercial while the README claims MIT. Evidence: `research/evidence/primuez-skill-installer-review-2026-11-22.txt`.

Primary inventory after candidate #135: **135/303 reviewed, 168 pending**; 177 supplemental pending; combined pending **345** excluding manual additions. Next: `rbutera/harness-bridge`.


## Candidate #140 — `sirrobot01/mnemo`: local coding-session handoff, not archive migration

The pinned reader set ingests Claude Code, Codex CLI, Continue and other coding-agent local stores into Mnemo's own session/task catalog. It does not read ChatGPT exports or reconstruct ChatGPT Project/Section membership, and it has no Claude Desktop third-party-inference Chat, Cowork or Code writer. Its Task/session many-to-many association and compiled WorkingState are continuity/handoff primitives, not an explicit parent/fork/subtask conversation graph.

Compatibility warning from source: Claude nested tool-use blocks are projected away when only text blocks are extracted; Codex tool-call/result records have names but no argument/output fields in the parser struct; Continue stores text and ingestion-time timestamps. Do not claim full transcript fidelity. A PostgreSQL adapter that drops raw session content and reduces paths to basenames is a useful privacy boundary pattern, but must not be mistaken for export capability. Pinned source review and test limitation: `research/evidence/sirrobot01-mnemo-review-2026-11-22.txt`.


## Candidate #141 — timonwong/skimi: Skill ResourcePlane, no Desktop/session graph

Skimi installs Skills through five fixed home-level paths (Claude Code, .agents, Codex, OpenClaw, Pi). It does not support Claude Desktop third-party-inference Chat/Cowork/Code and cannot migrate ChatGPT Projects/Sections, sessions, attachments, MCP, plugins, memory, or schedules. Its strict configuration/lock, agent filters, conflict reports, and ownership-checked symlink transaction are useful ResourcePlane patterns, but not proof of cross-Harness session compatibility.

Pinned-source caveats: a remote repo subdirectory is joined without verifying it remains under the clone (source-level path-confinement risk, not dynamically tested); a live repo pull can mutate Skill content already exposed through symlinks before install planning/lock commit completes; default config install can remove managed skills not declared in the full desired state. Evidence: research/evidence/timonwong-skimi-review-2026-11-22.txt.


## Candidate #142 — xpera-ch/goodboy: local Skill registry, no SessionGraph

GoodBoy manages a local personal Skill registry, project .claude/skills copies, and global symlinks for Claude Code, Codex, Gemini and shared .agents directories. It does not migrate ChatGPT Projects/Sections/sessions or Claude Desktop third-party-inference Chat/Cowork/Code. Its registry-client package is still an unimplemented Phase 3 stub.

Its integrity hash and versioned local store are useful ResourcePlane patterns, but source-level and isolated tests found compatibility risks: manifest restore ignores the prior exact lock/range and installs latest (rewriting the range); global symlink operations can replace/remove an unrelated link; and a failure in one of several target directories can leave earlier links unrecorded. Declared permissions are advisory and upgrades do not re-prompt. Evidence: research/evidence/xpera-ch-goodboy-review-2026-11-22.txt.


## Claude Desktop 3P native import/export is source-specific, not a generic ChatGPT adapter

Current Anthropic documentation confirms the user-selected destination as three local/client-managed surfaces: Chat, Cowork, and Code. Chat/Cowork session state and Code session records/transcripts use separate stores; Unified Claude can change which mode a home-screen conversation becomes. Desktop's own cross-device ZIP can carry Claude sessions, Projects/files, memory, scheduled tasks, saved Skills, uploaded plugins, some preferences, and local MCP commands; the archive may contain passwords/API keys and is sensitive. The native importer handles Claude.ai history and supported earlier Claude Desktop/Cowork/Code sessions, not arbitrary ChatGPT/Codex archives. A supported source-specific copy is useful as a target serializer oracle, but no generic external import API is documented.

Automatic migration is versioned and lossy: recent releases preserve many Project/resource categories but still require review/relinking of some folders, approvals, model selection, connector sign-ins, Code attachments, and plugin marketplace identity. Chat, Cowork, and Code retention are configured separately. See [Desktop 3P data storage](https://claude.com/docs/third-party/claude-desktop/data-storage), [import history](https://claude.com/docs/third-party/claude-desktop/import), [configuration reference](https://claude.com/docs/third-party/claude-desktop/configuration), and the captured evidence in `docs/research/evidence/claude-desktop-3p-current-review-2026-11-22.txt`.


## Candidate #144 — agents-mcp/cli: MCP config projection only

At pinned HEAD `cbf03ff339f876dbb3d7792a806c1c30bf3d4c6e`, this MIT CLI compiles a proposed project/global `.agents/mcp.json` into seven listed runtime adapters (Claude Code CLI, Cursor, VS Code, OpenCode, Windsurf, Zed, Antigravity). It does not target Codex, Claude Desktop Chat/Cowork/Code, or the third-party inference gateway; it does not read or create session/project/Section hierarchies, Skills, memory, schedules, or chat history. Antigravity has per-plugin output but the `import` command skips it because there is no single native config path. Its translation matrix calls out missing `cwd`, placeholder fallback loss, and transport inference.

Treat `.agents/mcp.json` as an adjacent candidate format, not an established universal importer: its Agent Plugins MCP 1.0.0 basis is a plugin-root `mcp.json`; the upstream spec has no portable credential-reference fields and says remote headers are literal, while this CLI adds a workspace/global `.agents` store and placeholder semantics for headers/URLs. The tested implementation also had a plaintext-secret leak in default import, ignored `--no-sync`, silent same-name conflict resolution, and a server-name path traversal that wrote outside `.agents/plugins`. Full pinned source and synthetic evidence: `docs/research/evidence/agents-mcp-cli-review-2026-11-22.txt`.


## Candidate #144 — agents-mcp/cli: MCP config projection only

At pinned HEAD `cbf03ff339f876dbb3d7792a806c1c30bf3d4c6e`, this MIT CLI compiles a proposed project/global `.agents/mcp.json` into seven listed runtime adapters (Claude Code CLI, Cursor, VS Code, OpenCode, Windsurf, Zed, Antigravity). It does not target Codex, Claude Desktop Chat/Cowork/Code, or the third-party inference gateway; it does not read or create session/project/Section hierarchies, Skills, memory, schedules, or chat history. Antigravity has per-plugin output but the import command skips it because there is no single native config path. Its translation matrix calls out missing `cwd`, placeholder fallback loss, and transport inference.

Treat `.agents/mcp.json` as an adjacent candidate format, not an established universal importer: its Agent Plugins MCP 1.0.0 basis is a plugin-root `mcp.json`; the upstream spec has no portable credential-reference fields and says remote headers are literal, while this CLI adds a workspace/global `.agents` store and placeholder semantics for headers/URLs. The tested implementation also had a plaintext-secret leak in default import, ignored `--no-sync`, silent same-name conflict resolution, and a server-name path traversal that wrote outside `.agents/plugins`. Full pinned source and synthetic evidence: `docs/research/evidence/agents-mcp-cli-review-2026-11-22.txt`.


## SecretPlane boundary — Hitesh-Sisara/agentic-keyvault

Agentic KeyVault is a credential store with a credential-namespace “Project”, versioned secrets, a CLI, and MCP reads/writes; it is not a Harness Project/Section/Session or chat-archive format. Do not put plaintext keys in a cross-Harness bundle. Carry at most opaque credential references and explicit reauthorization requirements, then relink at the destination. A synthetic test also showed the worker accepts a project-scoped secret with a repo ID owned by a different project; this is a tested scope-consistency/integrity gap, not a demonstrated cross-project read. Evidence and limits: `research/evidence/hitesh-sisara-agentic-keyvault-review-2026-11-23.txt`.


## Candidate #178 — huqiwei123/agentkit is ResourcePlane-only

Supports only two adapter IDs, Codex and generic Claude, with file-copy installs and a Codex-specific MCP TOML template. It does not transform session/project/Section structures or configure Claude Desktop third-party-gateway Chat/Cowork/Code/local Claude Code sessions. Profiles are flat resource-ID lists. Do not reuse installer as-is: unvalidated resource IDs escaped the chosen target in a synthetic install; a partial failure left files behind; the shipped bootstrap profile refers to a nonexistent skill and is not validated. Full evidence: `research/evidence/huqiwei123-agentkit-review-2026-11-23.txt`.


## Candidate #179 — Jaxz714/skills-hub is Skills-folder-only

It maps GitHub repos to local Skills directories (Claude Code, Codex, Cursor, `.agents`, generic) but has no Project/Section/Session archive or Claude Desktop third-party-gateway adapter. Its single platform classifier and raw repository clone are not cross-Harness semantic conversion. A local update probe changed recorded `codex` to `unknown`; no tests exist. Full scope and evidence: `research/evidence/jaxz714-skills-hub-review-2026-11-23.txt`.


## Candidate #180 — privacy-rights-plugin: five asset layouts, no session adapter

The Jacq manifest describes Claude Code/OpenCode/Codex/Cursor/OpenClaw layouts and fallback behavior, which is a useful ResourcePlane packaging example. It carries no session/project hierarchy or transcript state. Current committed dist is incomplete relative to shared sources: Skills refer to shared/email-templates, but no target dist includes shared assets; Discover/Dashboard are advertised but absent. Jacq is external and unpinned, so exact rebuild behavior is unverified. Full evidence: `research/evidence/jondwillis-privacy-rights-plugin-review-2026-11-23.txt`.

## Candidate #181 — jp-999/dev-team is project-task coordination only

Its canonical role files feed Cursor, Claude Code and CrewAI outputs; sequential CrewAI tasks write `.devteam/` artifacts. The plan CLI enumerated 11 roles. This is not a native chat/session store or Project/Section model: no conversation history, parent/fork graph, media, token accounting, or Claude Desktop third-party-gateway mode support. Keep as a resource adapter and project blackboard reference, not a session migration adapter. Evidence: `research/evidence/jp-999-dev-team-review-2026-11-23.txt`.

## Candidate #182 — `kamalsrini17/mcp-client` is a generic REST sample

The name is not borne out by the implementation: Axios posts PM workflow documents to ordinary REST routes; no MCP JSON-RPC/SDK or Harness adapter exists. No Project/Section/session graph, history import, Skills, Plugins, memory, media, or scheduler. Typecheck and a loopback mock passed; live localhost writes were avoided. Reject as a migrator. Evidence: `research/evidence/kamalsrini17-mcp-client-review-2026-11-23.txt`.

## Candidate #183 — cli-butler: local Skill, not Harness migration

This MIT Skill demonstrates per-channel provenance, manual-install journal, read-only reference tracing and fixture-backed package adapters. It does not model projects/sections/sessions or move transcripts/resources across Harnesses. Despite 184/184 isolated tests, synthetic source-derived probes confirmed package-name shell injection via `bash -c` and a mismatch between the documented `.bak` app-symlink safeguard and actual unlink behavior. Treat it only as a Skill packaging/testing reference; do not reuse its writers as-is. Evidence: `research/evidence/kelegele-cli-butler-review-2026-11-23.txt`.

## Candidate #184 — ctx: resource registry, not SessionGraph migration

This dual CLI/MCP tool is a useful broad ResourcePlane candidate for Skills, MCP configs and CLIs, but its discovery is limited to specific Claude Code/OpenClaude/OpenCode/Hermes resource paths and contains no project/section/session/history importer. Temp tests reproduced Skill path traversal, partial auto-import on a missing registry directory, plaintext MCP env values, and a broken git sync initializer. No source tests/lockfile were found. Do not connect it to real user HOME or reuse its writers until redesigned. Evidence: `research/evidence/kingimperio-ctx-review-2026-11-23.txt`.

## Candidate #185 — dora-explores-binaries: manual Skill copy only

One canonical prompt is offered as a Claude Code plugin, Codex Skill, Cursor/Windsurf rule, or generic system-prompt addition; it can be pasted into ChatGPT Custom GPT or Claude Project instructions. This is human-managed resource/content portability only, not a Project/Section/Session or transcript importer. No Claude Desktop mode-specific adapter or target-runtime fidelity tests are present. Evidence: `research/evidence/kizuno18-dora-explores-binaries-review-2026-11-23.txt`.

## Candidate #186 — `Knaackee/linxmd` is resource packaging only

Pinned `d831a3ac078bfd6322e87ba10bd860a52be2001f`. Local/GitHub artifact package manager for agents, Skills, workflows and templates with Copilot/Claude Code/OpenCode agent renderers; no Projects, Sections, transcript/session hierarchy, attachments, usage or scheduled-task migration. Skills go only to Claude Code. .NET 8 compatibility copy: 152/152 tests; native .NET 10 run unavailable on installed SDK 8.0.129. Isolated probes reproduced stale wrappers after remove and a synthetic skill path escaping its project. Retain only as a ResourcePlane manifest/dependency reference, not a state migrator.

## Candidate #187 — korakotlee/koharness: ResourcePlane and wiki pointers, no SessionGraph

Pinned ada356b058f3b84b6abe54f0b17a1367031e038a. KoHarness tracks a shared dotfiles repository for Skills, MCP settings and some Antigravity workflows. Its raw/wiki/AGENTS.md structure is Markdown navigation, not native project/session history. Implemented hosts are Claude Code, Google Antigravity and Codex; README mention of Claude CoWork is not backed by a Desktop mode adapter. A synthetic CLI run showed Claude MCP link failure at .claude.json/mcp.json, and sync materialized an env placeholder into tracked mcp/mcp.json via a symlink. Empty-home sync created steering files for all 3 hosts. Go tests passed 15 packages using isolated Go 1.24.0, but CI workflow does not test and pins Go 1.23 despite go.mod 1.24.0. No LICENSE file/SPDX was present. Keep as adjacent architecture reference only.

## Candidate #188 — krishna-kudari/agent-skills-manager: Skills path installer only

Pinned 9b11ae223bad40510b1cb9a81bea39c95521cd66, MIT. Raycast extension discovers and installs Skills from skills.sh/GitHub into per-agent directories; lock metadata supports Git commit update checks. No Project/Section/SessionGraph, transcript, media, schedule, MCP, plugin or memory migration. Claude Code is only a skill directory adapter, not Claude Desktop mode coverage. Despite README language, current InstallFlow disables project scope and forces global. Type-check/lint/build passed; no test script/files. A synthetic source-module probe showed symlink dereference can import outside-skill content and install deletes an unmanaged target directory. Retain only as a Skills-plane path registry reference; harden containment and backups before reuse.

## Candidate #189 — lakshay2395/employee-management-mcp-server-client-demo: protocol example only

Pinned 7bc698c446d0167eb49f3144490b62fbe96a2ad7. Genuine FastMCP Resources/Tools/Prompts + SSE LangChain/Gemini client for a domain-specific HR/MySQL database. No session, project, transcript, hierarchy, memory or harness configuration migration. README Session is an MCP transport connection. Python syntax check passed; no tests/dependencies/CI/license found. Source hardcodes a MySQL root empty-password config and binds 0.0.0.0:8000; not run against a real DB or network. Retain as concept reference only.


## Candidate #190 — `Lartweib/dotai`: strong resource/config pack, no session migration

Pinned `36eabaec4d4a1d2e840d37c873f3054767be3860`, MIT. Go pack engine for Claude Code CLI, Antigravity CLI (`agy`) and OpenCode. Plans, dry-run, backups/journaling, isolated install, restore, Skills/MCP/hooks/permissions/settings and plugin mods make it a high-quality ResourcePlane reference. Tests: 15 packages pass `go test ./...` and `go test -race ./...`, `go vet`, module verify and six gated rulesync E2Es pass. Synthetic fake-HOME probe confirmed isolated API-key/base-URL passthrough to a fake Claude CLI without mutating user config or writing the key. No Project/Section/SessionGraph, transcript/media/attachment/token/schedule/memory migration, ChatGPT/Codex target or Claude Desktop modes. Evidence: `research/evidence/lartweib-dotai-review-2026-11-23.txt`.

## Claude Desktop on third-party inference: three capabilities, distinct local data plane

User-confirmed scope is Chat, Cowork and Code in Claude Desktop on 3P (the official provider/gateway configuration), plus local/self-hosted Claude Code. The official Anthropic importer only moves Claude's own account chats/projects and local Cowork/Code sessions; it does not establish a ChatGPT/Codex import path. It omits cloud sessions and member-export attachment contents, requires manual memory/connector/provider-key handling, and is a one-time copy. Unified Claude is now rolling Chat and Cowork into one experience, so source mode and capability need explicit fields rather than assuming independent roots; Code remains a distinct session plane. Desktop 3P Chat/Cowork session state/transcript/audit/uploads/outputs live under `Claude-3p/local-agent-mode-sessions`; Code session metadata is under `Claude-3p/claude-code-sessions`, with actual transcripts under `~/.claude/projects/`. Keep these target native paths separate from Anthropic-hosted Claude Code Cloud and the messages-level API. Official source matrix and security gaps: `research/evidence/lartweib-dotai-review-2026-11-23.txt`.


## Candidate #191 — `lazyworkshop-create/skills-manager`: Skills copy tool only; unsafe/outdated target assumptions

Pinned `9d794f6491444b9705e0d0914092dd8552a972a1`. Python CLI discovers/copies Skills from wshobson/agents for VS Code or generic paths; no Project/Section/SessionGraph, transcript, media, token, MCP/plugin, memory, scheduler or API-key migration. `--claude-install` writes a generic `Claude/skills` folder, not the official Desktop 3P user-extension model or the `.claude/skills` filesystem path for Claude Code. `py_compile` and `--help` passed; no tests, CI, dependency lock or license file. Isolated synthetic probe showed a configured name traverses outside target, deletes a preexisting unmanaged target and dereferences a Skill symlink to copy external synthetic content. Default update path also runs pip on Skill requirements via `shell=True`; not run. Weak Skills-plane reference only. Evidence: `research/evidence/lazyworkshop-create-skills-manager-review-2026-11-23.txt`.

## Claude Desktop 3P target — full mode scope confirmed

User-confirmed target: Chat + Cowork + Code under local Claude Desktop third-party inference/API-key gateway mode, separately from Anthropic-hosted Cloud. The official product exposes all three; Chat/Cowork may be unified and Code stays separate. Chat/Cowork session data and Code transcript/index are distinct local data planes. Claude’s native importer documents Claude.ai and local Claude Cowork/Code sources, not a ChatGPT/Codex import API; rate ChatGPT/Codex → 3P as Nexus-adapter-required and not yet target-native validated.

| Surface | Core records | Compatibility stance |
|---|---|---|
| Chat | local session state, transcript/audit, uploads/outputs, project context/memory | preserve as `mode=chat`; require project/group/message mapping and attachment checksums |
| Cowork | local task sessions/VM workspace, tools, folders, memory, scheduled-task runs | preserve task/run graph; local schedule needs awake device/app |
| Code | Desktop metadata/index plus `~/.claude/projects/` transcript and workspace/trust refs | distinct adapter; no synthetic resumability without explicit target-supported import/trust |
| Unified Chat/Cowork | UI combines two surfaces; effective toolset may resolve to Cowork or Chat | store source mode and realized target mode |

Do not conflate Projects with sidebar groups, or app-managed 3P Skills/MCP/plugins with Code CLI filesystem extensions. Keep unsupported topology and payloads in an encrypted archive with per-item loss/verification records. Full primary evidence: `research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`.

## Candidate #193 — `liangquanzhou/agentctl`

| Surface | What it covers | Migration verdict |
|---|---|---|
| Claude Code | Native config/Skills/MCP/rules/hooks/commands/static subagents | Resource config only; no session import, transcript tree, Project/Section or attachments. |
| Claude Desktop 3P | Declared `claude-3p` MCP config and Cowork Skills cache projection | Experimental: hard-coded macOS private cache; no target path on clean install; first sorted org/account chosen; not official API-validated. |
| ChatGPT/Codex | No source-specific conversation/project parser | No cross-Harness session migration. |

The Go test suite is substantial (553 individual tests; race/vet/build pass), but tests exercise agentctl's synthetic writer, not a real Claude Desktop app. The user-confirmed 3P target still needs separate Chat/Cowork/Code adapters and complete SessionGraph/attachment provenance. Source detail: `research/evidence/liangquanzhou-agentctl-review-2026-11-23.txt`.

## Candidate #194 — `lidorshimoni/agentic-coding-design-patterns`

| Surface | Claimed output | Evidence-based stance |
|---|---|---|
| Claude Code | `.claude/commands/*.md`, `CLAUDE.md` | Legacy slash-command projection, not current recommended `.claude/skills`; no session history. |
| Antigravity | `.agents/skills/*/SKILL.md`, `GEMINI.md` | Content projection only. |
| Cursor/Windsurf/Roo/Cline/Copilot | rules/instruction files | Text flattening with format-specific loss; no state/session support. |
| ChatGPT/Codex/Desktop 3P | none | Not supported by the compiler; no session/Project/Section graph. |

A fake target showed the Copilot export replaces existing unmanaged `AGENTS.md` and Copilot instructions without a rollback/diff. `py_compile`, `--list`, and `bash -n` pass; no test/CI suite or target-app fidelity test. Full result: `research/evidence/lidorshimoni-agentic-coding-design-patterns-review-2026-11-23.txt`.

## Candidate #195 — `LMPrado-DZ23/awesome-agent-plugins`

This is a curated installer/catalog for MCP, Skills, native plugins and tools across 13 clients; it is not a data-migration engine. Its “Sessions & Messages” category describes installable DSH session utilities (including already-reviewed `Nwflower/dsh-chat-import`) and a queued session-reader source; it has no ChatGPT/Codex-to-Claude Desktop 3P transcript/project importer. Its documented E2E covers only a few specific client install paths, not 13-way session parity. Useful for ResourcePlane discovery; all candidate installs still need code/security audit. See `research/evidence/LMPrado-DZ23-awesome-agent-plugins-review-2026-11-23.txt`.


## Candidate #196 — `mabyko/AgentHarnessManager`

| Surface | Observed implementation | Nexus disposition |
|---|---|---|
| Skill groups | `SkillGroup {id,name,symbol,skillIDs}` and active group IDs; activation controls installed Skill files. | Useful local ResourcePlane pattern; not a ChatGPT/Codex sidebar Section or Project membership. |
| Work profiles | Name/note and Skill member/path/agent snapshots. | Not a conversation Project, session, branch or subtask graph. |
| Conversation/session state | No chat transcript, Project/Section index, session parent/child schema, attachment bundle or import/export implementation found. | No SessionGraph adapter. |
| MCP/CLI | Local status/list/show/check/groups/plan/request/requests; mutation request queues a human-reviewed Skill change. | Safe local Skill-management reference; does not write/import Claude Desktop 3P Chat/Cowork/Code. |

The macOS app build and 93 Swift package tests passed; synthetic CLI/MCP and app-state checks passed. This is source and synthetic-fixture evidence only, not a target-app fidelity test. Full record: `research/evidence/mabyko-agentharnessmanager-review-2026-11-23.txt`.

## Claude Desktop 3P mode-specific evidence refresh (2026-11-23)

The user confirms Chat, Cowork, and Code on the locally managed third-party-inference Desktop client. Current official docs describe per-device app data and distinct store shapes: Chat/Cowork in `local-agent-mode-sessions/` (session state, workdirs, uploads/outputs, audits and scoped memory), Code metadata in `claude-code-sessions/`, and Code transcript JSONL in `~/.claude/projects/`; some user-level files such as `~/Claude/` are shared. Chat/Cowork audits contain prompts/tool events and usage but are unencrypted; Code does not write that audit log. Unified Claude can route the same home-screen entry to Cowork or Chat depending on device capability. The official importer is documented for Claude.ai exports and local prior Cowork/Code sessions, not as a general ChatGPT/Codex importer. Keep all three Desktop modes distinct from Anthropic-hosted Cloud and from standalone CLI; lock app version/OS and test discovery/resume separately. Evidence and direct official links: `research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`.


## Candidate #197 — madshn/ai-playbooks

| Surface | Observed coverage | Nexus disposition |
|---|---|---|
| Claude Code credentials | One prompt-based Skill uses 1Password Environments + local .env/direnv for environment variables and MCP environment-variable interpolation. | Narrow credential ResourcePlane; not a conversation/session migrator. |
| Codex / Gemini | README marks ports as not implemented / TBD. | No verified adapter; “cross-harness” is not history portability. |
| ChatGPT/Codex Projects, Section Groups, session branches and attachments | No parsers, schemas, imports or outputs present. | No SessionGraph coverage. |
| Claude Desktop 3P Chat/Cowork/Code | No target-mode adapter or session writer. | No Chat/Cowork/Code session coverage. |

The Skill is natural-language instructions, not tested code. It writes a temporary plaintext import file and its value-based scan prints the full matching lines; its optional vault cleanup blocks on length difference only. Source and official dependency/version notes: research/evidence/madshn-ai-playbooks-review-2026-11-23.txt.


## Candidate #198 — AntoSkills compatibility boundary

| Surface | Observed behavior | Nexus disposition |
|---|---|---|
| Claude Code Skill resources | Writes pinned Skill files into .claude/skills; lockfile and store preserve version/integrity. | Adjacent ResourcePlane reference only; no conversation/session import. |
| Codex Skill resources | Writes shared Agent Skills into .agents/skills. | ResourcePlane support only; no Codex Project, Section or session tree. |
| Claude Desktop 3P Chat | No Chat conversation store or writer. | Unsupported. |
| Claude Desktop 3P Cowork | No Cowork project/task/session, memory or scheduled-task adapter. | Unsupported. |
| Claude Desktop 3P Code | Embedded Code overlap with Claude Code paths is possible but not demonstrated or tested. | Unverified; do not claim compatibility. |
| ChatGPT/Codex Projects, Sections and sessions | No source parser, canonical session graph or destination writer. | Not a SessionGraph migration candidate. |

The package's 121 passing tests and synthetic end-to-end checks validate the package manager's own Skills lifecycle, not transcript/session fidelity. A possible first-install collision with an unmanaged same-name Skill directory should be resolved with ownership-aware preflight and preservation, because the current replacement path deletes a real directory. Full source, provenance and command outcomes: research/evidence/magnumquest39-cloud-antoskills-review-2026-11-23.txt.


## Candidate #199 — skill-forger compatibility boundary

| Surface | Observed coverage | Nexus disposition |
|---|---|---|
| Claude Code Skills | Default target; delegates to the Vercel Skills CLI and stores source/skill names. | ResourcePlane only; no session history or project migration. |
| Codex / Cursor / GitHub Copilot Skills | README documents agent flags for these targets; actual path behavior is delegated. | Skills content only; not Codex Project, Section or session hierarchy. |
| Claude Desktop 3P Chat | No Chat session, store or adapter. | Unsupported. |
| Claude Desktop 3P Cowork | No Cowork project, task, memory or schedule adapter. | Unsupported. |
| Claude Desktop 3P Code | Possible overlap through Claude Code target, but no 3P app-specific discovery or writer test. | Unverified; do not infer compatibility. |
| ChatGPT/Codex Projects, Sections, messages, branches and sessions | No parser, graph schema, importer or export. | Not a SessionGraph migrator. |

The CLI test suite covers source parsing, config updates, lock-entry removal, path discovery and gitignore helpers (36 tests), not installation fidelity. A synthetic all-skills uninstall showed that config/lock state can be removed while the disk Skill remains. Full source, exact outputs and limitations: research/evidence/marcm8793-skill-forger-review-2026-11-23.txt.


## Candidate #200 — Skills Manager compatibility boundary

| Surface | Observed coverage | Nexus disposition |
|---|---|---|
| Claude global Skills | Default ~/.claude/skills target; pre-install static scan and source metadata. | Strong ResourcePlane safety reference; not a Claude session or Project writer. |
| Codex / Cursor / OpenCode Skills | Global directories and CLI selection; no conversation-level group membership. | Resource files only, not Codex Projects/Sections or session tree. |
| Claude Desktop 3P Chat | No Chat history/session model. | Unsupported. |
| Claude Desktop 3P Cowork | No Cowork project, task, memory or schedule model. | Unsupported. |
| Claude Desktop 3P Code | Claude Code target path may overlap, but the app's 3P local session store is not read or written. | Unverified; do not infer compatibility. |
| ChatGPT/Codex session hierarchy | No SessionGraph, parent-child, branch, transcript, attachment, token-use or project/section transfer. | Not a migration adapter. |

Candidate #200 is a security scanner and Skill installer. Main has 155 passing unit tests; its unmerged scanner PR has 176 passing tests and richer ZIP/TAR analysis. Neither suite is a target-session fidelity test. See research/evidence/mazen160-skills-manager-review-2026-11-23.txt.

## Candidate #201 — mejbaurbahar/awesome-qa-agent-skills

| Source/target capability | Observed |
|---|---|
| Skill content | 194 QA/PM Skills in a source/license-tracked catalog; its installer writes Claude Code and Antigravity skill directories. Resource content only. |
| ChatGPT/Codex Project, Section Group, session nesting/branches/transcript | No reader, event model, or writer. |
| Attachments, links, token usage, memory, scheduled tasks | No migration model. |
| Claude Desktop third-party-gateway Chat / Cowork / Code | No session-store adapter or mode-specific writer. |
| Safe reversible install | Normal fake-home install/uninstall smoke passes, but synthetic replaced-path and modified-manifest probes delete user-owned temp data. Require strict managed-root/content identity and transactional recovery before borrowing installer patterns. |

Full pinned-source and execution evidence: docs/research/evidence/mejbaurbahar-awesome-qa-agent-skills-review-2026-11-23.txt.

## Candidate #202 — miles990/skillpkg

| Source/target capability | Observed |
|---|---|
| Skills/resource content | Project-local Skill package/dependency model; Syncer declares Claude Code (.claude/skills), Cursor (.cursor/skills), Codex (.codex/skills) and Copilot (.github/skills) targets. An official Codex skill guide still documents .codex/skills. |
| Resource import/export fidelity | Importer/exporter handle SKILL.md as one Skill object; reference/scripts/assets are not represented in the imported object or exported bundle. Same-count asset changes can be reported unchanged. |
| MCP | Core syncMcpConfig can serialize configured values to .mcp.json, but CodeGraph shows syncAll is called only by syncer.test; CLI auto-sync and MCP sync_skills call syncToTarget, so normal CLI/MCP install/sync does not reach this writer. If called directly, it overwrites unrelated existing server entries and stores env values literally. No generic per-Harness credential-reference or import format. |
| ChatGPT/Codex Projects, Sections, nested sessions, branches, transcripts, attachments, token usage, memory, scheduled tasks | No source model, importer or writer. |
| Claude Desktop 3P Chat / Cowork / Code | README shows a generic Desktop MCP client setup only. No mode-specific session-store or gateway adapter. |
| Safe, reproducible use | README marks package manager archived. Tests 259/261; lint 7 errors; build/typecheck pass. Synthetic probes found path escapes and destructive cleanup/config overwrite. Do not use as-is. |

Full evidence: docs/research/evidence/miles990-skillpkg-review-2026-11-23.txt.

## Candidate #203 — MlsMoon/moon-game-dev-tool-manager

| Source/target capability | Observed |
|---|---|
| Skills and resources | Git-managed Agent Skills install into `.agents`, `.claude`, `.grok`, legacy `.codex`; Unity Plugins and Packages use project paths. ResourcePlane only. |
| Project / Section Group / SessionGraph / turn, subtask, fork, transcript | No reader, schema or writer. |
| Attachments, token usage, persistent memory, scheduled tasks, MCP/plugin session dependencies | No portable session migration model. |
| Claude Desktop 3P Chat / Cowork / Code | No mode-specific session store or gateway adapter. |
| Safe Skill install | `SkillCopy.Replace` deletes an existing non-Git target without requiring a marker; a synthetic Core probe reproduced unowned file deletion and traversal via unvalidated `id` outside a disposable workspace. Plugin/Package containment check is separate. |
| Build/test evidence | Original local SDK 8.0.129 compile exited 1 at eight ambiguous `Split` calls; compatibility-copy tests had 21 pass / 3 macOS Windows-path assumptions fail. Official pinned Windows CI #18 is green. |

Full pinned-source and execution evidence: docs/research/evidence/mlsmoon-moon-game-dev-tool-manager-review-2026-11-23.txt.

## Candidate #204 — mocikadev/mocika-samsara

| Source/target capability | Observed |
|---|---|
| Portable memory | Markdown lessons with error/skill/pattern/insight types, occurrences, rules, index and log; Git-backed local store. Useful sidecar model, not a session event log. |
| MCP and Skills | Six stdio tools for lessons/search/status/promote/index/prime. Separate self-evolution Skill; MCP writes individual lesson records. |
| OpenCode | Plugin injects `prime` at system-transform/compaction and runs `reflect` at idle; it does not persist or import the OpenCode session. |
| Claude Desktop 3P Chat/Cowork/Code / local Claude Code | Init adds selected MCP/instruction config paths; no mode-specific session-store reader or writer, no API-key/gateway session setup; fake-home config smoke is not live client validation. |
| ChatGPT/Codex Projects, Section Groups, session/branch/transcript/attachments/usage/schedules | No importer, exporter, entity model or mapping. README conversion is AI/manual lesson entry. |
| Safe writes | Confirmed CLI writes outside the knowledge root for `domain=../../...` and `keyword=../../../...`; MCP forwards these strings. `init --dry-run` still creates directories. |
| Quality | 46 tests, fmt, clippy `-D warnings`, locked release build pass; official latest CI #20 at pinned commit is green. |

Full pinned-source and execution evidence: docs/research/evidence/mocikadev-mocika-samsara-review-2026-11-23.txt.

## Candidate #205 — pewpewgogo/agentcrew

| Source/target capability | Observed |
|---|---|
| Project structure | Project → Milestone → Task; tasks have one optional milestone, no parent-task/subtask relation. Per-project KB stores repos, URLs, tech stack and notes. |
| Context/memory | Append-only text entries target a project/milestone/task and record human/agent author, app user, timestamp. Useful handoff context, not conversation transcripts. |
| MCP | 15 tools for projects, KB, milestones, tasks and context. HTTP server auth uses AgentCrew API keys; not provider API keys or inference routing. |
| ChatGPT/Codex Projects/Sections, session/turn/branch/message/transcript, attachments/tokens/schedules | No source schema, import/export or adapter. |
| Claude Desktop 3P Chat/Cowork/Code / Claude Code | Bundled Skill/init targets Claude Code (`~/.claude/skills`, `~/.claude.json`); no Desktop mode/session-store adapter. |
| Security/testing | Server hashes keys, CLI config chmods `~/.agentcrew/config.json` to 0600; MCP init writer created a synthetic API bearer in `.claude.json` mode 0644. Build/lint pass; 16 non-DB tests pass; DB suites blocked by absent PostgreSQL. |

Full source and execution evidence: docs/research/evidence/pewpewgogo-agentcrew-review-2026-11-23.txt.

## Candidate #206 — Predator404/aiToolManager

| Source/target capability | Observed |
|---|---|
| Skills and Commands | Canonical `.agents` files with per-harness native symlink mirrors for OMP, Claude Code, Prime Agent; global vs filesystem project scope. |
| MCP / extensions / hooks | Per-harness native MCP files; OMP and Prime native enable fields, Claude Code shadow sidecar; extensions for OMP/Prime, Plugin toggle and Hooks for Claude Code. |
| ChatGPT/Codex Projects/Sections, conversation sessions/branches/messages/transcripts/attachments/tokens/schedules | No entity/import/export model; the “project” is a local directory scope. |
| Claude Desktop 3P Chat/Cowork/Code / local Claude Code sessions | No Desktop mode or session-store adapter; Claude Code support is resource config only. |
| Write safety | Confirmed temp probes: enable deletes unowned mirror dir; same-name import deletes existing canonical extras; promotion misses non-SKILL.md conflicts; MCP config rewrite relaxes file permissions to 0644. |
| Quality/license | 100 tests and typecheck pass; no CI/release; package private, no license file/declaration. |

Full pinned-source and execution evidence: docs/research/evidence/predator404-aitoolmanager-review-2026-11-23.txt.


## Candidate #207 — pyhu26-public/agent-moringgroove

| Capability | Observed |
|---|---|
| Local/self-hosted Claude Code | Folder-based web UI and herdr terminal resume the same native local `sessionId`; app metadata is JSON. |
| ChatGPT/Codex Projects, Section Groups, full session hierarchy | No importer/exporter or source IDs/parent-fork graph; “folder project” is just a disk directory. |
| Claude Desktop 3P Chat/Cowork/Code | No client store access or mode-specific adapter; do not infer Desktop support from `.claude` paths. |
| History fidelity | UI reads at most 200 native messages, omits images/nontext, tool results and history ancestry; Windows-native returns empty. |
| MCP/Skills | Per-folder `.mcp.json` and `.claude/skills`; not a cross-Harness plugin package. New synthetic MCP config with env secret was mode 0644. |
| Safety/provenance | Synthetic HTTP API followed a docs symlink outside the registered folder; Skill DELETE removed an unowned asset. No license, releases or CI workflow observed; lockfile install is inconsistent. |

Disposition: local Claude Code session-resume UX reference only; not a Nexus migrator. Full pinned evidence: `docs/research/evidence/pyhu26-public-agent-moringgroove-review-2026-11-23.txt`.


## Candidate #208 — Kimi Code / qingyunk/skill-manager

| Capability | Evidence and boundary |
|---|---|
| Kimi Skills | This repo scans Kimi user/project directories and generic `.agents/skills`, validates frontmatter, and writes Kimi user Skills. It does not manage MCP or general plugin bundles. |
| Kimi CLI/Desktop session format | First-party docs place sessions under `$KIMI_CODE_HOME/sessions/<workDirKey>/<sessionId>`, with `state.json`, main/subagent `wire.jsonl`, and fork behavior; Desktop shares the CLI session store. |
| Kimi native import/export | Official CLI docs: `kimi export` ZIP/Markdown; `kimi import-sessions` imports recent Claude Code/Codex sessions only (15/30 days, max 100/run). The visible imported context is one summary message; complete history and original files are preserved. `/import-from-cc-codex` imports selected instructions/Skills/MCP. None of these features are implemented by qingyunk/skill-manager. |
| ChatGPT Projects/Section Groups | No importer or documented ChatGPT source support. |
| Security | Synthetic `name: .. --force` deleted the fake Kimi home; plugin `skills` traversal read an outside temp Skill. Kimi's own plugin docs require path containment after symlink resolution. |

See `docs/research/evidence/qingyunk-skill-manager-review-2026-11-23.txt` and linked first-party Kimi docs within.


## Candidate #209 — `Rafa-Innerchispa/inneros-personal-brain`

| Capability | Observed |
|---|---|
| Shared long-term memory | Cognee graph-memory/retrieval sidecar, web retrieval, orchestration and optional bounded local artifact. Useful adjacent MemoryPlane concept, not a source transcript adapter. |
| ChatGPT/Codex Projects, Section Groups, session tree | No session/message IDs, branch graph, project/section relations, transcript import/export, or attachment/token accounting in the reviewed main-branch model. |
| Claude Desktop 3P Chat/Cowork/Code | No mode-specific local-store writer or native session resume path. Does not become one because the repo describes cross-agent memory. |
| Security | Direct `cognee_remember` and `CogneeMemoryStore.add` paths bypass the curator. Fake-client POC showed synthetic credential/path strings remained in the persisted request. |
| Quality | 23 isolated tests passed (two deprecation warnings); no live provider/Cognee test. Main has no detected license. PR #5 remains open and its code diff was not independently reviewed. |

Disposition: **shared-memory architecture reference only; no code reuse as the Nexus SessionGraph or migrator.** Full pinned source/test and synthetic-probe record: `docs/research/evidence/rafa-innerchispa-inneros-personal-brain-review-2026-11-23.txt`. Current Claude Desktop 3P import/storage boundary is summarized in the dated `claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt` addendum.


## Claude Desktop 3P current import boundary — official Help Center cross-check

The current third-party-provider move is an Anthropic-source workflow: per-user Claude chats/projects plus local Cowork/Code sessions can be copied into Claude Desktop on 3P; Cowork/Code cloud sessions, personal-export original file bytes, memory, instructions, Skills and connectors have separate omissions/steps. It is not a ChatGPT/Codex source importer. The Help Center says imported Cowork projects from Chat are one at a time, and current Cowork Projects are not Claude Code Projects. In 3P, history is local to the device; the official cloud `--teleport` session path is distinct and requires Claude account auth. Keep all three Claude Desktop surfaces in scope while retaining their mode-specific local target stores. Sources: [3P migration](https://support.claude.com/en/articles/18426225-move-from-claude-enterprise-to-claude-desktop-on-a-cloud-provider), [Cowork Projects](https://support.claude.com/en/articles/14116274-organize-your-tasks-with-projects-in-claude-cowork), [non-Anthropic history import FAQ](https://support.claude.com/en/articles/8114491-get-started-with-claude), [Claude Code Cloud](https://code.claude.com/docs/en/claude-code-on-the-web).


## Candidate #210 — `RafaelQSantos-RQS/MyAgentControl` (OpenCode resource manager)

| Capability | Observed |
|---|---|
| Harness scope | OpenCode-compatible `.opencode/` tree only; installs embedded Markdown/config resources. No model/runtime calls. |
| Resource organization | Five install profiles, 248 entries across agents/subagents/commands/tools/plugins/Skills/context/config, plus dependency expansion and SHA-256 manifest. Profiles are not Section Groups. |
| Session/project migration | No ChatGPT/Codex transcript importer/exporter, Project/Section model, event/branch/session IDs, attachments, tokens, or history resume. “Project” is a filesystem/context noun. |
| Quality | 120 tests pass; fmt, Clippy `-D warnings`, release build pass; pinned CI run green. Pre-v1, 0 stars/forks, no releases or PRs. |
| Safety | Synthetic symlink-parent tests created files outside `--dir`; collision still entered manifest, and `remove` deleted a foreign outside sentinel before exit 1. |

Disposition: registry/profile and hash-ledger reference only; reject writer/remover for Nexus until symlink-resolved path containment, collision ownership, and atomic rollback pass. Full evidence: `docs/research/evidence/rafaelqsantos-rqs-myagentcontrol-review-2026-11-23.txt`.


## Candidate #211 — `ramon-sg/agent-skills` and current Agent Skills interoperability

| Capability | Observed |
|---|---|
| Skill payload | Five Agent Skills folders (planning, narrative-summary, visual-preview, code-audit, test-audit), each with `SKILL.md`; optional scripts/references/templates; catalog dependency edges and editable `project.md` overlays. |
| Migration/session graph | No conversation/session import/export, ChatGPT Project/Section Group model, history IDs, attachments, token accounting, MCP server, or project/session restoration. |
| Target installation | Candidate README and E2E tests use `@ramon-sg/skills-manager` and default `.agents/skills/`. Its lock pins manager 1.1.0 for tests; convenient README install uses major `@1` unless the repository runner config pins it. |
| Claude compatibility | Anthropic docs specify `.claude/skills/` for project/local Code and account-enabled sync for Cowork/cloud; no `.agents/skills` path appears in current Claude Code docs. Candidate's cloud claim is not demonstrated by its tests and may not apply to Claude Desktop 3P. |
| Quality | 20/20 tests pass with `CODEX_CI` unset; GitHub current pinned CI passes; v0.5.0 release exists. Initial test runner hung under inherited `CODEX_CI=1` because its synchronous launcher waits for a foreground server. |

Disposition: high-quality Skill ResourcePlane reference; reject as a session/project migrator. Treat `.agents/skills/` as one target adapter, not a cross-Harness compatibility proof. Full evidence: `docs/research/evidence/ramon-sg-agent-skills-review-2026-11-23.txt`; normative path matrix: `docs/research/evidence/agent-skills-standard-runtime-paths-2026-11-23.txt`.


## Candidate #212 — `ricardosalcedo/agentpack` (MCP dependency / export plane)

| Capability | Observed |
|---|---|
| Resource/dependency model | `agentpack.json` and lock capture MCP/agent package versions, integrity, stdio/remote transport, dependency edges, profiles, capability requirements and tool names/descriptions. Useful concepts for Nexus Memory's ResourcePlane; not a source project/session hierarchy. |
| Claude Desktop output | `export --target claude-desktop` serializes locked MCP servers as `mcpServers`; implementation writes `claude_desktop_config.json` in the current working directory. It is a narrow config payload, not an installer for Claude Desktop 3P's managed settings, Marketplace/plugins, account connectors, per-mode storage, or API gateway credentials. |
| Chat/Cowork/Code session portability | No ChatGPT/Codex importer/exporter, Project/Section IDs, conversation events, branches, child tasks, files, attachments, session checkpoints, token accounting, or loss report. |
| Tests | `cargo test --locked` default parallel: exit 101, 19 passed / 4 failed due tests mutating global working directory; repository README prescribes serialized execution. `cargo test --locked -- --test-threads=1`: exit 0, 23 passed. The suite has no import/fetch/export command regression tests. |
| Security | Synthetic `import --command` probe executed injected JS; synthetic `fetch ..` probe overwrote the disposable project `agentpack.json`. Security blocker for those writers; no live MCP server, secret, or non-temporary path was used. |

Disposition: retain the declarative dependency/profile concepts as a reference only; do not reuse its importer/cache writer until both reproduced issues are fixed and regression-tested. Full pinned-source evidence: `docs/research/evidence/ricardosalcedo-agentpack-review-2026-11-23.txt`.


## Candidate #213 — `roedyrustam/ctxbridge` (cross-agent memory plane)

| Capability | Observed |
|---|---|
| Memory | Local project/global SQLite FTS5 stores; typed decision/rule/fact/lesson/todo, tags, source agent, priority, token estimate; MCP save/recall/forget/capsule/sync tools. Useful for cross-harness memory injection, not history transfer. |
| Project and session hierarchy | Project scope is a repo directory; no ChatGPT Project ID/Section Group or session/message/task/event graph. Capsules are generated summaries; no lossless transcript/attachment/session export. |
| Target adapters | Writes `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `CODEX.md`, `.gemini/GEMINI.md`; this covers coding-tool instruction files, not Claude Desktop 3P Chat, Cowork, or Code-local session stores. |
| JSONL migration fidelity | Synthetic import preserves scope/kind/title/content/source_agent/priority/tags, but overwrites ID/hash/created_at/updated_at/token_estimate; JSONL export omits capsule history. Not a provenance-preserving interchange format. |
| File safety | Disposable symlink probe: `AGENTS.md` linked outside the chosen project; `ctxbridge sync` exit 0 followed the link and appended the managed block to the outside sentinel. Require explicit symlink policy and realpath containment before reuse. |
| Dependencies | `cargo audit` finds `libsqlite3-sys 0.30.1` bundled SQLite CVE-2026-119375 (patched crate version >=0.39.0; exploit requires opening an attacker-crafted DB plus mismatched WAL); `chrono 0.4.45` reported unmaintained. |
| Quality | Local `cargo test --locked`: 19 passed across 7 suites; format, Clippy with warnings denied, and release build pass. GitHub CI#3 and release run pass; metadata sync run #2 failed. |

Disposition: retain architecture concepts for the ResourcePlane and compact handoff UX only. Do not describe it as Projects/Sections/Session migration or claim lossless memory import. Full source/test/POC/advisory evidence: `docs/research/evidence/roedyrustam-ctxbridge-review-2026-11-23.txt`.


## Candidate #214 — `Saber5656/skillet` (design only; Agent Skills plane)

| Capability | Observed |
|---|---|
| Package model | Proposed index, semver, pinned commits, integrity hash, lockfile, adapters, consent, receipt-tracked copy materialization. This is a strong Skill resource-plane design, not a runtime-tested feature. |
| Target harnesses | v1 design names local Claude Code and Codex only. Claude Desktop 3P Chat/Cowork/Code, ChatGPT Projects/Sections, Codex Projects/Session history, plugins, MCP and agent config are out of scope. |
| Skill formats/paths | Uses the Agent Skills `SKILL.md` payload. The design selects `.claude/skills` and `.codex/skills`; current official OpenAI sources also document `.agents/skills` and a package-root/plugin format. Require product/version-specific path tests; parsing or copying the common payload does not verify discovery or invocation. |
| Sessions and provenance | No transcript, SessionGraph, project/section identity, branching/child tasks, attachments, token counts, tool events, schedules, output artifacts, or source-to-target session IDs. |
| Implementation status | Main contains 55 tracked files, all README/docs; no `src/`, `tests/`, `package.json`, package lock, GitHub workflow, release, or `LICENSE`. 40 open GitHub issues mirror 40 implementation issue drafts; local review counted 0 checked and 209 unchecked acceptance boxes. |
| Licensing/quality | No license declaration was found; do not assume reuse rights. No code/tests/build/CI result can be claimed. GitHub shows 0 stars/forks, 1 closed PR, no release, and no workflow runs. |
| Security claims | Strong and specific design controls (no fetched-code execution, explicit consent, pinned commits/hash, enumerated Git extraction, path/symlink filters, receipt-only mutation, rollback). They remain unimplemented/unverified here; the design itself defers signing and prompt-injection scanning. |

Disposition: keep as a high-quality architecture/security checklist for a future ResourcePlane package manager, but not as a migration tool or source implementation. Full source-state and cross-check evidence: `docs/research/evidence/saber5656-skillet-review-2026-11-23.txt`.

## Candidate #215 — `saturnarians/ctx-manager` (context ledger, not migration)

| Capability | Observed |
|---|---|
| Context/resource plane | Deterministic Markdown heading slices and a short phase/category ledger; MCP tools wrap the same local functions. Useful only as an adjacent continuation convention. |
| Session/project/section plane | No ChatGPT/Codex Projects, sidebar Section membership, conversation ancestry, branch/task graph, raw messages, attachments/media, tool results, tokens, scheduling, MCP/plugin state migration or resume IDs. |
| Claude targets | README examples mention Claude Code hooks/MCP clients, but no local transcript import/export and no Claude Desktop 3P Chat/Cowork/Code session adapter. Anthropic-hosted Cloud remains separate. |
| Verification boundary | 21 unit tests pass on CPython 3.14/3.12; no MCP path-safety/concurrency tests. Synthetic probes show Docs read escape, config-ledger write escape, phase drift, overbroad “Verified” label, and forced lost updates. |
| Distribution | PyPI 0.2.0 is stale relative to the later same-version main fix; pin artifact hash and source commit separately. Dependency audit findings require transport reachability triage. |

Use its Markdown slicing idea only after redesign; do not treat its ledger as a lossless session store or deploy untrusted project configuration without path containment. Evidence: `docs/research/evidence/saturnarians-ctx-manager-review-2026-11-23.txt`.

## Candidate #216 — `sefas-labs/ai-skills-manager` (Skills ResourcePlane only)

| Capability | Observed |
|---|---|
| Provider adapters | Four declared local Skill readers: Claude Code, Cursor, Codex and GitHub Copilot. Claude Code path may scan read-only claude.ai-synced Skills; this is not Claude Desktop Chat/Cowork/Code session storage. |
| Resource operations | GitHub Skill inspection, exact-commit staging, visibility checks, validation/security heuristics, install, provenance, update diff, copy/move and recoverable uninstall. |
| History migration | No ChatGPT/Codex Project, sidebar Section Group, SessionGraph, branches/subtasks, user re-prompts, attachments/media, tools, tokens/cost, schedule, MCP/plugin or native resume state. |
| Validation | Local 57 tests + typecheck/build/smoke pass. Live editor E2E not run because it reads real home Skill paths and contacts GitHub; it is not necessary to establish the absence of any session model. |
| Security/dependencies | Good path validation and no-execute install model; heuristic review is explicitly not a guarantee. npm audit flags 7 dev/build package records, while production dependencies audit clean. |

Keep as a high-value ResourcePlane design reference; do not conflate Skill-file visibility with session/project portability. See `docs/research/evidence/sefas-labs-ai-skills-manager-review-2026-11-23.txt`.

## Candidate #217 — `shqear93/mcp-manager` (unsafe MCP configuration utility)

| Capability | Observed |
|---|---|
| MCP registry/config | Basic source registry + static writers; no server liveness, schema roundtrip, capability negotiation, session binding or conversation migration. |
| Project/global scope | Registry scope is configurable, but agent writers always resolve `os.homedir()` config paths; project mode also writes global config. |
| Client paths | Current official Claude Code MCP scopes: `~/.claude.json` and project `.mcp.json`, not `~/.claude/config.json`; Cursor uses `~/.cursor/mcp.json` / `.cursor/mcp.json`, not `settings.json`; Kimi CLI uses `~/.kimi/mcp.json`; Cline CLI uses `~/.cline/data/settings/cline_mcp_settings.json`; Aider does not have established native MCP config support. Codex path aligns at a basic level. |
| Safety | Untrusted MCP definition name can escape registry root; `remove` path can recursively delete outside. Registry collision overwrite deletes existing data without backup/consent. Synthetic secret persisted in a 0644 config; HTTP URL discarded. |
| Restore | `experimental_restore` reads lock and lists missing paths only; it does not recreate files/configs. |

Reject as a writer/adaptor until path containment, ownership checks, transactional backup/rollback, credential policy and exact per-host/version schemas are implemented. Evidence: `docs/research/evidence/shqear93-mcp-manager-review-2026-11-23.txt`.


## Candidate #218 — `simonwu53/agent-skills` (Skill library only)

| Capability | Observed |
|---|---|
| Resource model | Bash Skill manager: source Git repo/local folder/ZIP, register `SKILL.md` skills by category, pin, copy or symlink into selected tool paths, and sync repository submodules. |
| Claude target paths | One generic Claude mapping: `~/.claude/skills/` global and project `.claude/skills/`; no Chat/Cowork/Code mode split, 3P-vs-standard Desktop profile or app-managed Skills writer. |
| Projects/Sections/Sessions | None. No ChatGPT/Codex Project/Section Group identifiers, transcript/turn/event nodes, parent/child/branch relations, media, context token/cost, schedules, MCP invocation history, or native-resume data. |
| Safety / restore | Explicit `--skill` path traversal outside the cloned repo reproduced in temp; `--install` default clears a complete target Skills directory after confirmation, and `--update` removes named target before copying. No transaction receipt/backup restore. ZIP `../` member did not escape with the tested macOS `unzip`; no general ZIP member validation is implemented. |
| Tests / provenance | One offline smoke script: 47/47 pass. No CI workflow. Source Git submodule pointers retain commit IDs; installed copies do not carry a verified per-file digest/receipt. |

Disposition: low-priority ResourcePlane design reference only. Do not reuse its path selector or treat a generic Claude skill directory as validated Desktop 3P support. Review: `docs/research/evidence/simonwu53-agent-skills-review-2026-11-23.txt`; current target mode contract: `docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`.


## Candidate #219 — `sjmgarnier/skill-manager` (AI Skill workflow, no sessions)

| Capability | Observed |
|---|---|
| Product | `SKILL.md` prompt + registry/update/platform scripts around `gh skill` and `npx skills`; user-approved Skill source installation only. |
| Project/Section/Session | None: no Projects, Section Groups, conversation turns/events, branches, attachments, tokens, MCP/plugin auth, schedules or native resume IDs. |
| Host coverage | Generic resource install; not Desktop 3P mode-specific. The detector treats `~/.agents/skills` as Warp, while current OpenAI docs use that as Codex user Skill path; its Codex table instead says `~/.codex/skills`. |
| Validation | 23 Bats cases declared, not run because `bats` is absent. Shell `bash -n` passed; isolated registry/update manual checks passed. |
| State/safety | `.registry.yaml` (JSON subset) has one row per repo and omits target host/scope mapping. Direct non-atomic writes; one 32-process temp stress run retained all rows, so no loss was reproduced. Several install commands are applied sequentially, without a cross-install transaction/rollback record. |

Disposition: low-priority Skills ResourcePlane reference; reject as a Project/Section/session migrator and fix platform identity before unattended use. Current provider/account-backed Desktop Skill surfaces are conditional and distinct from local filesystem skills. Evidence: `docs/research/evidence/sjmgarnier-skill-manager-review-2026-11-23.txt` and `docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`.


## Candidate #220 — `stevengonsalvez/reflect-kb` (archived MemoryPlane documents only)

| Capability | Observed |
|---|---|
| Current artifact | Archived `main` commit `d3375adb9fb403c4f8c657ca5001322d13fd0826`; only README/docs/license/workflow remain. No source, package manifest, tests or runnable CLI in this checkout. |
| Knowledge model described | Markdown learnings, structured frontmatter, content-hash `doc_id`, entity sidecars, local GraphRAG/QMD index, Git-backed KB and search. Default path in usage guide is `~/.claude/global-learnings/`, with `GLOBAL_LEARNINGS_PATH` override. |
| Session migration | None documented. No ChatGPT/Codex Project/Section/session parser, turns/events, branch/child tree, attachments, token/cost data, memory-to-source links, MCP/plugins or target resume IDs. |
| Native Claude mapping | Not Claude Code Auto Memory (`~/.claude/projects/<project>/memory/`) or resumable session JSONL (`~/.claude/projects/<project>/<session-id>.jsonl`). Documentation also disagrees about the custom KB path (`~/.learnings/` vs `~/.claude/global-learnings/`). |
| Validation | No code or tests remain in the pinned repository; CI workflow references `pip install -e .[dev]` and `pytest`, but no project manifest/source exists. Latest archive CI run was cancelled; prior code runs shown failed. |

Disposition: retain only as a design reference for a derived Knowledge/Memory plane; keep immutable source SessionGraph as canonical and attach every derived note to source event IDs. Do not treat it as a working migrator. Evidence: `docs/research/evidence/stevengonsalvez-reflect-kb-review-2026-11-23.txt`.


## Candidate #221 — summer-via/skill-package-manager (Skills resource-only)

| Capability | Observed |
|---|---|
| Resource model | Git-native Skill installer with skill.json, refs/lock information, ~/.agents/skills, copy/symlink modes. |
| Project / Section / SessionGraph | None. No cross-harness project IDs, sections, session hierarchy, turn/event payloads, files/media, token/cost, schedules, plugins/MCP history or target resume IDs. |
| Claude Desktop 3P modes | No mode-specific support. User-confirmed compatibility scope remains Chat, Cowork, and Code as separate adapters; local/self-hosted Claude Code is another separate adapter. |
| Validation | TypeScript build passed. No test script/directory. Synthetic /tmp remove traversal deleted a sibling sentinel; install collision deleted an unmanaged target directory. |
| Safety / disposition | Delete-before-copy and uncontained delete paths have no ownership receipt or rollback. Reject writer; retain only as low-priority ResourcePlane terminology reference. |

Evidence: research/evidence/summer-via-skill-package-manager-review-2026-11-24.txt. Official 2026-11-24 vendor evidence for Desktop 3P and its Claude-origin-only importer is in research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt.


## Candidate #222 — sunven/skills-box

| Capability | Observed |
|---|---|
| Target product | macOS-first Tauri desktop manager for Agent Skills, local project scopes and native plugin operations. |
| Agent/resource coverage | Vendored skills@1.7.4 catalog with 79 agent definitions; inspected paths include Codex and Claude Code. Native plugin host enum is Codex and Claude CLI only. |
| Project/Section/session migration | None. Local registered directory scope is not a ChatGPT/Codex Project; no Section Groups, transcript/event graph, branches, media, token/cost, schedules or resume IDs. |
| Desktop 3P | No Claude Desktop 3P Chat/Cowork/Code data-store adapters or cross-harness history import/export. |
| Tests/build | pnpm 540/540; frontend build passed; Rust cargo test rerun 896 passed, 31 ignored after one earlier AppUpdateBusy failure. |
| Supply chain | Production pnpm audit clean through registry.npmjs.org; full dev tree has high ansi-regex 5.0.0. cargo audit reports cookie 0.18.2 + url 2.5.8 vulnerabilities and 8 warnings; reachability not assessed. |
| Safety/distribution | Strict Skill path validation, scoped previews/backups; snapshot restoration absent. Native-plugin removal has no rollback. No license; released binary is macOS Apple Silicon only. |

Disposition: strong adjacent ResourcePlane/UI reference only; not the requested project/session migrator. Do not reuse code without a license. Full source/build/test/audit review: research/evidence/sunven-skills-box-review-2026-11-24.txt.


## Candidate #223 — suqiangqiang2012-dot/agent-skill-manager

| Capability | Observed |
|---|---|
| Product | Agent Skill management workflow packaged as SKILL.md plus Python scripts; stable GitHub release check/install/rollback and gated release preparation/publication. |
| Declared targets | Codex Windows/macOS; WorkBuddy Windows 5.5.4+. Other adapters are fail-closed/planned. |
| Current Codex path | Candidate resolves CODEX_HOME/skills or ~/.codex/skills. Current official OpenAI CLI docs list project .agents/skills/ and user ~/.agents/skills/. Default-path mismatch reproduced under synthetic HOME; explicit install-root override exists. |
| Projects/Sections/Sessions | None. No chat project/section identifiers, transcripts, session graphs, parent/fork edges, media, token/cost, schedules or target resume IDs. |
| MCP/plugins | No MCP server or native plugin import/export; it manages Agent Skill packages only. |
| Tests/safety | 15 unit tests pass; release_tool validates 8 files. Stable-only GitHub source, SHA-256 checks, traversal/symlink rejection, explicit overwrite and rollback confirmation, staged install, backups. Live public install was not completed due no-auth API 403 after correcting the Python CA bundle. |
| License / decision | No declared license; do not copy code. Retain release/approval/rollback concepts only. |

Evidence: research/evidence/suqiangqiang2012-dot-agent-skill-manager-review-2026-11-24.txt and research/evidence/agent-skills-standard-runtime-paths-2026-11-23.txt.


## Candidate #224 — theonepichael/agent-toolkit

| Capability | Observed |
|---|---|
| Harnesses | Local analytics readers for Pi, Claude Code CLI, OpenCode, Copilot CLI, Antigravity, and Codex CLI; workflow tooling also targets six coding CLIs. |
| Data projection | Normalized text/token/cost `SessionRecord` with session ID/cwd/time and boolean subagent marker. No stable event IDs/order, parent/fork graph, tools/results/permissions, media bytes, Project/Section links, or resume handles. |
| Migration surface | No ChatGPT/Codex Project or Section Group importer, generic event export, cross-harness transform, or target native restore/resume writer found in reviewed paths. |
| Claude Desktop 3P | No app-specific Chat/Cowork/Code session reader. Claude Code CLI JSONL is a separate profile, not proof of Desktop mode coverage. |
| Validation | 135 analyzer + 45 worker-audit + 24 run-metric tests passed; 130 queue-runner tests had 2 failures/1 error on macOS `/tmp` canonicalization. README's full `uv run pytest` gate was unavailable here. Python CI jobs are Ubuntu-only. |
| Decision | High-value observability/parser prior art only. Do not call it a migrator or reuse the lossy record as canonical SessionGraph. |

Pinned `main` `5daf67975c8ffac3241b49341edbc76f3350820f`; MIT. Details: `research/evidence/theonepichael-agent-toolkit-review-2026-11-24.txt`.


## Candidate #225 — timianmalloo/x-harness-x-model-bench

| Capability | Observed |
|---|---|
| Product | Apache-2.0 cross-harness/model/pack benchmark; per-cell native harness process, workspace and harness home. |
| Session-related value | Native readers for Claude Code, Codex, Copilot, Antigravity and Grok-like stores; normalizes selected model/tool/error/usage/reasoning/prompt/harness facts. Benchmark archives copy cell files with hashes and credential-name exclusions. |
| Conversation fidelity | Selective `Extraction`/`ProcessTrace`, not full turn/event interchange; no full message stream, image/file bytes, Project/Section membership, parent/fork/subtask IDs or destination resume handle. |
| Migration surface | CLI exposes bench lifecycle/reporting and run resume only; no cross-harness import/export or target-native conversation restore. |
| Tests | Focused suites: 518 passed, 1 skipped, 1 failed. Failure: macOS path equivalence in `tools/grok_served_model.py` for Windows-style vs slash-style path strings. Full CI ring not run. |
| Decision | High-value SessionObservability + archive-integrity prior art; not a migrator or canonical SessionGraph format. |

Pinned `main` `560d2fae9eaebb6450ab33b752df6ca288b5de6e`. Full evidence: `research/evidence/timianmalloo-x-harness-x-model-bench-review-2026-11-24.txt`.

## Current Claude Desktop on 3P storage crosswalk — 2026-11-24

Treat “third-party provider/API gateway” as an inference setting, not an Anthropic Cloud conversation store. Official 3P docs enumerate Chat, Cowork and Code as local Desktop modes and document independent local data directories: macOS ~/Library/Application Support/Claude-3p/, Windows %LOCALAPPDATA%/Claude-3p/ (with legacy MSIX/version-specific locations), and Linux ~/.config/Claude-3p/. These are separate from standard Desktop data.

| Target adapter | Native local shape | Migration/fidelity hazards |
|---|---|---|
| claude-desktop-chat | local-agent-mode-sessions: per-session state JSON plus working directory, uploads, outputs, and audit.jsonl. Audit records prompts/responses/tool inputs/results, returned thinking, permission decisions, model and token usage. | Audit file unencrypted; partial HMAC chaining is not verified/completeness proof. Outside-project Chat has no project memory; inside-project Chat can read/update project memory. Keep the raw file/attachments and event provenance. |
| claude-desktop-cowork | Shares Chat/Cowork state family but adds Cowork VM/session home, project/global memory, local folders, scheduled tasks, and output/live artifact files (often under ~/Claude/). | Project/task folder links are path-bound; VM/state/output are separate resources. Schedules run as fresh sessions and normally require awake device/app. Do not flatten a schedule or workspace into a historic conversation. |
| claude-desktop-code | Desktop metadata in Claude-3p/claude-code-sessions; native transcript in ~/.claude/projects/. | Code does not use Chat/Cowork audit.jsonl. Claude Code setup in ~/.claude/ and ~/.claude.json (Skills/plugins/hooks/permissions/MCP/trusted folders) is shared with standalone CLI. SSH Code has remote transcripts, uploads and credential context. |
| claude-code-cli | Native Claude Code session/transcript, settings and shared ~/.claude/ resource tree. | Distinct launcher/provider/auth and native resume behavior from embedded Desktop Code. Desktop passes its own configured provider to embedded sessions; CLI separately reads environment/settings/managed policy. |

The [official storage reference](https://claude.com/docs/third-party/claude-desktop/data-storage) also says Cowork and Code schedules are separate, the Desktop app's Claude-origin import/export is not a cross-harness archive, and import omits or requires rebinding some file paths, trust and credentials. The [3P feature matrix](https://claude.com/docs/third-party/claude-desktop/feature-matrix) distinguishes local history from Anthropic cloud sessions. The [embedded Code reference](https://claude.com/docs/third-party/claude-desktop/code) and [CLI migration guide](https://support.claude.com/en/articles/18466061-move-claude-code-cli-users) confirm separate configuration surfaces. Validate each mode against its own on-device discovery/resume behavior; record provider/auth mode, version, OS, workspace and project relationships. Full source trace: research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt.

## Candidate #226 — toshon-jennings/agent-advisor

| Capability | Observed |
|---|---|
| Product | MIT selective-routing hub for Codex, Claude Code and Antigravity; canonical platform trees exported one-way to three spokes. |
| Session migration | None found: no ChatGPT/Codex Project/Section/session reader, attachment/event archive, import/export or target native-resume writer. |
| Safety prior art | Manifest-defined resource paths, expected remote/root identity, containment/symlink/type/dirty/ignored-file checks, all-spoke preflight/revalidation, native validators, checksummed copy, post-write equality and scoped rollback. |
| Limits | TOCTOU remains. Rollback is per-spoke after apply starts, so global atomicity is not guaranteed. No behavioral test suite in hub; local syntax/help only. |
| Decision | Keep safe ResourcePlane export design concepts; reject as session migrator. |

Pinned main 02d8c757f04e00a3d8f9da51507ba9a23b9b350f. Evidence: research/evidence/toshon-jennings-agent-advisor-review-2026-11-24.txt.

## Candidate #227 — weixuanteo/skills-manager

| Capability | Observed |
|---|---|
| Harness/resource scope | Skill directories for universal .agents, Claude Code, Codex, Cursor, Gemini CLI, Copilot, Windsurf, Kiro, OpenCode, Amp, Goose, Cline, Roo Code and GitHub Copilot. Also discovers Skill folders within Claude Code plugin installs. |
| Project support | Scans user-selected project filesystem roots and common agent-specific Skill directories. These are local folders, not a ChatGPT/Codex Project record, section group or session graph. |
| Import/export | Remote Skill browsing via skills.sh/GitHub, preview, per-agent install via the skills CLI and install/update/remove command generation. No generic Skill archive export, MCP writer, conversation import/export, ChatGPT Project/Section map, attachments or target resume. |
| Provenance | Tracks install method, source/install path, git/npm/skills-cli metadata, agent/scope locations, file tree, current commit/package status and command log. Useful adjacent ResourcePlane fields. |
| Security/quality | Local server defaults to loopback; exact command confirmation and generated-command allowlist; synthetic traversal/command/cross-origin smoke passed. Branch-ref check/fetch race remains. 35 tests and build pass. Current dependency audit has 9 advisories (8 moderate, 1 low) in Hono/node-server versions. |
| Decision | Adjacent Skill management UX only; no session migration fit. Code is unlicensed and not reused. |

Pinned main 3aa4419870ca2a73fc90aea919042d606736ea9c. Full evidence: research/evidence/weixuanteo-skills-manager-review-2026-11-24.txt.

## Candidate #228 — CyberGuild and DeepSeek Harness boundary profile

| Capability | Observed |
|---|---|
| CyberGuild | Manually maintained Markdown roster/QuestBoard distributed as a Skill; explicit appointment/on-demand loading only. Not an event graph, importer, hierarchy, or resume writer. |
| DSH Workspace | Optional host registry: canonical directory + stable ID/title + ordered Session membership, validated through SessionHeader.cwd. It is distinct from the event log and is not a nested Section tree. |
| DSH Session | Append-only typed log is source of truth; message history is derived. Header stores id/version/time/cwd and selected lineage metadata; fork cut is exact. Ordinary fork and direct subagent parent differ. Attempts, interruption, usage, tool records and plugin events exceed rendered transcript data. |
| DSH persistence | Per-Session JSONL log, Zstandard frames by default or raw lines; header separate; per-session handle/write ownership, explicit flush and version migration/crash-repair semantics. Workspace, Skills and schedules are separate state. |
| DSH Skills | Project `.dsh/skills` / `.agents/skills`, user `$DSH_HOME/skills` / `.agents/skills`, custom/bundled roots. CyberGuild adapter covers only user `.dsh/skills` on Windows. |
| DSH Schedule | Host-owned durable tasks with explicit timing/target; historical Session events or delivery receipts do not prove active scheduled execution or model completion. |
| Decision | Keep explicit appointment/minimal context only. Preserve nested Section Groups in Nexus metadata if target is flat; model Workspace, events/lineage, Skills, schedules, media, plugins/MCP, credentials separately. |

The user reconfirmed all Claude Desktop third-party-provider modes—Chat, Cowork, Code—plus local/self-hosted Claude Code; test distinct adapters for native discovery/import/attachments/resume. See `research/evidence/deepseek-harness-session-project-profile-2026-11-24.txt`.

## Candidate #229 — SkillHub boundary and operational quality

| Capability | Observed |
|---|---|
| Resource support | Local Skill repo metadata/catalog, shallow clone, SKILL.md scan, global copy-install/update/uninstall/diff to 73 static agent IDs. 73 IDs map to 66 directories; some aliases share one global folder. |
| Cross-machine sync | Git-tracked `data/skills.json` syncs metadata and a cloned flag, not immutable source hashes, installed file content, user-local paths or session state; other machine clones current remote branch. |
| Source coverage | No Project/Section Group or Session/event importer, parent/fork graph, edits/interrupts, attachments/media, token/cost, MCP/plugins, schedules, credential or native resume support. No ChatGPT/Codex conversation transport. |
| Security | Backend listens without explicit host (observed `*:18787`); wildcard CORS and no auth; synthetic cross-origin GET/POST succeeded. Symlink in cloned SKILL.md read a sentinel outside clone root despite direct `../` being rejected. |
| Data integrity | Distinct `owner-repo` clone path can collide (`a-b/c` vs `a/b-c`). Copy-update leaves source-deleted files in installed target and has no stage/rollback. |
| Quality | Node 26.7/npm 11.19: 70 unit/component/server tests pass; build passes. Tests omit install/update/uninstall/path/CORS behavior. Prod npm audit 0; full tree 6 dev advisories, 2 critical. 44 commits, 0 stars/forks, no release, license or workflow. |
| Decision | Reject for Nexus migration and for real-profile write use as reviewed. Retain only metadata-vs-machine-local separation as conceptual ResourcePlane reference; no code reuse. |

Full evidence and exact synthetic outputs: `research/evidence/xdlkc-skillhub-review-2026-11-24.txt`.

## Candidate #230 — skillpkg package-registry boundary

| Capability | Observed |
|---|---|
| Resource type | Versioned single Skill bundle; SKILL.md frontmatter + supporting files, JSON index, tar.gz, optional SHA256, S3-compatible private object storage. |
| Harness target | Generic `~/.skillpkg/skills` store only. No Claude Desktop 3P Chat/Cowork/Code, native Claude/Codex/DSH install routing, per-project roots, MCP or plugins. |
| Project/session state | None: no Project/Section, Session log, parent/fork/edit/interrupt relation, attachments, tokens/cost, schedule, memory or resume. |
| Version/dependency behavior | HTTP source can pin a version and verify its index SHA; no signature. `requires` is metadata only. Local filesystem source ignores version; semver comparison is string-based; update command is unimplemented. |
| Security / write safety | `remove` and `install` path escape skills root; untrusted index `file` escaped temp staging and wrote synthetic bytes; optional empty publish token accepted writes; plaintext token file 0644 under umask 022. |
| Availability | MIT; 8 commits, 0 stars/forks, no release/CI/tests. Built from source in isolated Python 3.12 venv; compileall/pip check/CLI smoke passed. PyPI name `skillpkg` belongs to a different maintainer; separate `skillpkg-cli` is a new manual review lead. |
| Decision | Reject as migrator and do not reuse current implementation. Keep only package/index/hash as conceptual ResourcePlane reference. |

Evidence: `research/evidence/xfan3696-collab-skillpkg-review-2026-11-24.txt`.


## Candidate #231 — Xichun123/dsh-skills-manager (2026-11-24)

| Capability | Observed |
|---|---|
| Harness / resource plane | DSH-only Skill provider and Settings/composer UI. Private Skill library under `$DSH_HOME/skill-manager/.agents/skills/`; `skills-lock.json` for source and `state.json` for global/workspace/manual-only state. |
| Project / Session coverage | “Project” scope means a registered DSH workspace path and descendants. No ChatGPT/Codex Project, Section Group, Session/event graph, parent/fork/subagent, transcript import or native resume. |
| Target profiles | No ChatGPT/Codex importer and no Claude Desktop third-party-provider Chat/Cowork/Code writer or local/self-hosted Claude Code adapter. |
| Runtime compatibility | Source uses `connection.rpc.handle('/skill-manager', ...)`; package peer ranges stop at DSH `0.1.5-alpha.1`. Open issue #1 reports activation injection failure and HTTP 405 on DSH `0.2.0-rc.2`, plus peer-range install rejection. Source corroborates route/range, but issue's runtime results were not independently reproduced here. |
| Quality / security | Node 26.7 / pnpm 11.25: build + 24 tests pass. README `pnpm validate` is not a defined package script. Production audit against official npm registry: 0; full dependency-tree audit: 1 high Zod and 1 low KaTeX. No live DSH session/import or Desktop transport test. |
| License / decision | Package says `UNLICENSED`; no source reuse. Adjacent Skill adapter design only; reject as Nexus Project/Session migrator pending license and current DSH fixes. |

Evidence and attribution limits: `research/evidence/xichun123-dsh-skills-manager-review-2026-11-24.txt`; [open issue #1](https://github.com/Xichun123/dsh-skills-manager/issues/1).


## Candidate #232 — yyeret/ai-threads-kanban (2026-11-24)

| Capability | Observed |
|---|---|
| Local readers | Claude Code project JSONL, Codex index + rollout JSONL (including unindexed rollouts), Gemini CLI chat JSONL and source-level Antigravity logs. README/install hook instructions primarily cover Claude/Codex/Gemini; Antigravity native refresh wiring is not shown. |
| Workflow identity | One durable work-thread row can contain sessions from multiple harnesses, but ID is inferred from repository basename + first-prompt hash and same-repo fuzzy Jaccard; not a native Session/fork/parent identity. |
| Project / Session fidelity | No ChatGPT Project/Section/Section Group or Claude Desktop 3P Chat/Cowork/Code profile. Registry stores summaries and transcript path references; no raw event archive, typed branch/parent/child/subagent edges, attachment payloads, tokens/cost, MCP/plugin/schedule transfer, portable bundle, or target import/resume. |
| Resume / archive | Native commands for Claude Code, Codex, Gemini; Antigravity direct CLI resume unavailable. Codex explicit-Done can rewrite `session_index.jsonl` and move rollout files; it is a destination-specific side effect, not migration. |
| Security / integrity | Local server binds 127.0.0.1 but has no auth/CSRF/origin check or HTTP-method restriction; disposable synthetic GET from `Origin: https://evil.invalid` changed state. Synthetic Codex ID produces unquoted shell resume string (not executed). Optional Drive/Dropbox state is eventually consistent/last-writer-wins; no transaction journal. |
| Quality / decision | MIT, pinned `9f948221f805f486205afc0763bcef164e5a4dfb`, 25 commits, 0 stars/forks, no CI/release. Node 26.7/npm 11.19: 20 tests pass using temp HOME; scanner/classifier has no coverage. Retain as adjacent SessionInventory/workflow prior art only; do not install or reuse as-is pending hardening. |

Detailed evidence and attribution: `research/evidence/yyeret-ai-threads-kanban-review-2026-11-24.txt`.


## Candidate #233 — zuhabul/yo-code (documentation/provenance screen only)

| Capability | Observed from public docs |
|---|---|
| Intended product | Recovered CLI rebrand with agents/Skills/hooks/rules/MCP/plugins and “cross-harness workflows”; README focuses on local development, not data migration. |
| API-key fit | README/AUTH docs describe local Anthropic-compatible account keys, optional API base URL and account rotation after 429. The same docs say the runtime remains Anthropic-protocol-specific. This has not been runtime-verified here. |
| Migration boundary | No ChatGPT/Codex import/export or Project/Section/session graph migration is documented. Because source inspection stopped at the license gate, this is not a claim that all internal code was inspected to prove absence. |
| Provenance / legality | `LICENSE` and `SOURCE_PROVENANCE.md` claim leaked proprietary Anthropic Claude Code origin and prohibit competing-product use/deployment. Exclude source/code-derived designs from Nexus; require clean-room provenance and legal review for any future reconsideration. |
| Maturity | `private:true`, Bun 1.3.9, no Releases; 4 open Dependabot PRs and several failed Actions runs. README states full CLI boot is blocked by missing recovered modules. Bun unavailable; no dependency installation/runtime check attempted. |
| Decision | Screened out as an implementation candidate; no source reuse and no claim of verified API compatibility or session migration. |

Evidence: `research/evidence/zuhabul-yo-code-review-2026-11-24.txt`.
## Candidate #235 — agent-history compatibility boundary (2026-11-24)

| Capability | Evidence / boundary |
|---|---|
| Local-source reads | Claude Code JSONL (fork/sidechain/bridge hints and project memory), Codex CLI JSONL, OpenCode/Hermes SQLite, OpenClaw, plus Grok/Gemini CLI/T3 Code adapters in the registry. Read-only history ingestion; not a general import/export API. |
| Claude.ai Chat | Explicit import from a user-downloaded export only. Projects/docs/instructions and account/project memory become separate searchable records; the importer says current chat exports do not link chats to Projects. Not a live API or a target writer. |
| Claude Desktop Chat/Cowork/Code | README coverage explicitly excludes live claude.ai Chat, claude.ai/code Cloud sessions and Claude Desktop Cowork. Local Claude Code transcript reading is not evidence of Desktop Code project/session re-homing or API-Key gateway compatibility. No native writer for any of the three Desktop modes. |
| Session/project fidelity | Text/chunk search and source IDs, cwd, timestamps, aliases, some fork/subagent metadata; not a lossless event stream or complete SessionGraph. Branch choice, typed attachments, tool payloads, usage/token counts, and ChatGPT Section/Project relationships are not recreated. Claude.ai attachments contribute only extracted text, capped at 100,000 characters. |
| Skills/MCP/plugins/memory/schedules | Local Claude Code memory Markdown and exported Claude project instructions/memory are indexable. Its plugin/MCP and cron/Task Scheduler entries update/search that index; they do not migrate source resource definitions or ChatGPT scheduled-task semantics. |
| Validation/security | MIT; scoped parser/identity suite 105 passed/56 skipped; full suite 434 passed/410 skipped. 409 skips are SQLite-extension-dependent on the review Python; 1 is Windows-only. Local redaction defaults off, and full indexed text can contain credentials. Not a production suitability or full-platform pass. |

Disposition: adjacent history-ingestion/retrieval prior art only. It cannot satisfy ChatGPT's **Destruction Era** Project/Section/Session migration into Claude Desktop third-party-gateway Chat, Cowork and Code or local/self-hosted Claude Code API-Key sessions. Keep the source/target profile matrix disaggregated; see `research/evidence/lvtd-dgtl-agent-history-review-2026-11-24.txt`.


## Candidate #236 — neosun100/aiw compatibility boundary (2026-11-24)

| Capability | Evidence / boundary |
|---|---|
| Product | MIT local tmux process/workspace manager, REST/WebSocket, CLI and stdio MCP. Creates or operates live CLI processes; not a transcript archive or migration tool. |
| Project/session model | Workspace metadata has name/tool/model/description/directory/created time. No ChatGPT Project or Section Group source, message/event records, Session parent/fork/subtask graph, active branch, attachments, tool history or token usage. |
| Target coverage | No ChatGPT importer or Claude Desktop Chat/Cowork/Code session writer. Launching `claude` via configurable CLI command is not a local/self-hosted API-Key provider adapter or target-native history restore. No skill/plugin/MCP definitions, memory or task schedule migration. |
| Security | Server default `0.0.0.0`; no built-in authentication/authorization; routes and terminal WebSocket can send commands/kill/attach; tmux calls use `shell=True` command strings. README requires reverse-proxy auth/HTTPS before exposure. Not suitable as a network-facing Nexus execution backend without reengineering. |
| Correctness / tests | Advertised rename references undefined `SESSION_PREFIX` (safe synthetic probe confirmed NameError). `mcp>=1.0.0` is unbounded: 14 tests fail against 2.3.0; pinning 1.0.0 yields 66/66 pass. Tests do not cover rename, auth, live tmux, or deployment security. |
| Maturity | Pinned main HEAD Jan 8, 2026, v0.2.0; GitHub Releases page had no releases and Issues showed 0 open at review. CodeGraph 13 Python files / 218 nodes / 434 edges. |

Disposition: low migration relevance; retain only as an adjacent live-workspace orchestration example. Do not equate a tmux process with a portable Harness Session. Full review: `research/evidence/neosun100-aiw-review-2026-11-24.txt`.


## Candidate #237 — i3T4AN/Archivist-MCP compatibility boundary (2026-11-24)

| Capability | Evidence / boundary |
|---|---|
| Memory model | Project-scoped typed knowledge graph: decisions, incidents, rules, entities, observations, generic Session/Artifact node types, typed edges, audit/conflict/version lifecycle. Useful as a separate derived memory plane. |
| Session representation | Relational sessions table has only ID/project/user/client/timestamps; observations can optionally reference it. No MCP session-create/import operation, transcript/message events, turn order, active branch, parent/subtask tree, usage or media. Generic `Session` nodes are not the relational table. |
| Portability | `export_audit_log` returns bounded/redacted audit events + digest, not graph contents. Snapshot/restore is an SQLite recovery operation, not a source→target transfer bundle. No ChatGPT export parser, Claude Desktop writer, Projects/Sections importer, skill/plugin/schedule conversion. |
| Retrieval and memory | MCP tools allow agents on compatible transports to share this server's curated memory; `core_memory.md/.json` is a budgeted projection and can truncate items. This does not recreate source history. Hash-local embeddings are implemented; other named embedding providers return no backend in the reviewed commit. |
| Security | SQLCipher is optional and encryption-required defaults false; fake test sentinel remained raw in node content. HTTP defaults loopback but permits unauthenticated tools when no token map is configured; Team SSE requires bearer tokens and scope. Retention purge applies only to observations, not nodes/artifacts/audit. |
| Maturity / tests | MIT, 3 commits, 4 stars, no release, 0 open issues at review. Full suite 79 passed/5.89s in isolated venv. Not production maturity certification. |

Disposition: high-value memory graph/retrieval prior art for a distinct target adapter, not a ChatGPT-to-Claude Session migration implementation. See `research/evidence/i3T4AN-archivist-mcp-review-2026-11-24.txt`.


## Candidate #238 — maideps/ai-harness-framework (2026-11-24)

| Capability | Evidence / boundary |
|---|---|
| Harnesses | Project-local coding workflow documented for Claude Code, Codex and Gemini CLI. Optional Context7 MCP wiring; not an all-Harness resource/config importer. |
| Session model | `.harness/traces/` stores start/end timestamps, git branch/commit, active feature, verification summary, changed-file paths and decision summaries. `progress/`, `PROGRESS.md`, `feature_list.json`, `.harness/state/` and `DECISIONS.md` model feature/workflow state, not provider turns or native transcript lineage. |
| Hierarchy/resources | No ChatGPT Project/Section Group or native Session/parent/fork/subtask graph, message/media/attachment/token schema, arbitrary Skills/MCP/plugins/scheduler migration, or Claude Desktop 3P/local Claude Code native session writer. |
| Safety/operations | `create-harness` preserves existing files; upgrade snapshots framework-owned files it replaces and preserves project/instance state. Useful for staged adoption/rollback patterns, not portable archive behavior. |
| Quality/maturity | MIT, pinned `e0de706a240892ea2d3a66e5d7a56ec59d75d48e`; full `npm run check` exit 0 (RTK-visible coverage 74.93 ≥65; no test count surfaced); no direct `sessionTrace` test found. GitHub at review: 2 stars, 0 forks, 6 open issues, latest v0.5.0. |
| Decision | Adjacent coding workflow/verification reference only; not a ChatGPT → Claude Desktop session migrator. |

Evidence: `research/evidence/maideps-ai-harness-framework-review-2026-11-24.txt`. Primary corpus 238/303 reviewed, 65 pending; supplemental 177 pending; manual additions 21/9 pending; combined pending 242 (manual-inclusive 251).

## Target clarification — Claude Desktop third-party inference includes three modes

First-party docs specify Chat, Cowork and Code route through an Anthropic Messages API-compatible gateway (`POST /v1/messages` streaming and tool use required; model discovery optional). Desktop gateway credentials/config are provider routing, not history import permission; configuration is separate from Claude Code CLI `ANTHROPIC_BASE_URL`/settings. A gateway-configured Desktop cannot use Anthropic-hosted cloud environments or Remote Control. This validates all three destination modes while preserving distinct session-store and local/cloud boundaries; each mode needs its own versioned round-trip/loss gate. Official refs: https://claude.com/docs/third-party/claude-desktop/gateway ; https://code.claude.com/docs/en/llm-gateway-connect ; https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile .


## Candidate #239 — 1naruto-1/agent-connect (2026-11-24)

| Capability | Evidence / boundary |
|---|---|
| Source/target coding CLIs | Cursor, Claude Code CLI, Codex CLI and Pi; documented 4 adapters × 3 other tools = 12 directions. MIT pinned `42287c14a8fd381bc7ef7a96076a5cba5b4d75f6`. Not ChatGPT web/app or ChatGPT Codex app. |
| Session identity/hierarchy | One selected session at a time, filtered by current project/CWD. Claude/Pi/Codex readers choose resume-effective histories and flatten to a linear stream; abandoned branches are skipped/counted, not recreated as a tree. No Project/Section Group or child-session graph. |
| Events/resources | Canonical five-kind stream covers text, thinking, tool call/result and markers. No typed media/attachment, usage/cost, model, policy, schedule, memory or installed Skills/MCP/plugin configuration. MCP calls in transcript can be copied, not MCP server/auth configuration. |
| Claude target fit | Writes `~/.claude/projects/<encoded-cwd>/<id>.jsonl` for Claude Code CLI, not `Claude-3p/local-agent-mode-sessions` Chat/Cowork or the `Claude-3p/claude-code-sessions` Desktop metadata/profile. Desktop 3P Code transcript store is shared with Claude Code CLI, but UI discovery from a CLI-only writer is unverified; exact client-version gate required. |
| Security/side effects | Local-only transcript read/write and no model API key needed. POSIX reports 0700/0600; Cursor write checks app shutdown and uses SQLite transaction. However, Codex writer copies config from the newest other local Codex session (synthetic base-instructions/turn-context canaries confirmed), creating cross-project context bleed. Target write and report are not a single atomic transaction; no batch/dedupe. |
| Validation | Bun 1.3.14 full check: 122 pass / 0 fail / 386 expect calls / 11 files; Darwin arm64 standalone build, `smoke:build`, and checksum verification passed. Synthetic fixtures only; no actual Codex/Claude/Cursor/Pi process or app-level resume test, no ChatGPT source, no 3P Chat/Cowork test. Repo had 2 stars, 0 forks, 0 open issues; latest release v0.2.5 (July 26), reviewed main commit Aug 9. |
| Decision | High-value *coding CLI continuity* reference, not the requested ChatGPT Project/Section/Session/resources to Claude Desktop 3P migration. Potential CLI-code writer prototype reference only; do not claim target UI integration or lossless media/branch fidelity. |

Evidence: `research/evidence/1naruto-1-agent-connect-review-2026-11-24.txt`. Primary 239/303 reviewed, 64 pending; supplemental 177 pending; manual additions 21/9 pending; combined pending 241, manual-inclusive 250.

## Claude Desktop 3P: current storage and native import contract (2026-11-24)

First-party docs specify: 3P Chat/Cowork history, session workdirs, uploads/outputs, memory and audit logs reside under the app's `local-agent-mode-sessions/`; Code metadata is under `claude-code-sessions/`, and transcripts reside in `~/.claude/projects/`. Claude Desktop 3P Code uses the Claude Code engine; terminal sessions may resume a Code transcript from either mode, but app-list visibility remains mode-specific. Unified Claude combines Chat and Cowork on the home surface; Code remains separate.

The official import wizard copies claude.ai exports and supported earlier local Claude Desktop Cowork/Code sessions. It is a one-time, source-specific operation, not a ChatGPT export importer. Some projects/custom groups, memory, schedules, plugins/skills and Chat/Cowork attachments may transfer, with limitations: no connector sign-ins, Code attachment files, permission decisions, project links, or project knowledge / personal-export attachment contents. Validate every retained/lost item per source and client version; never infer support from the native 3P importer. First-party refs: https://claude.com/docs/third-party/claude-desktop/data-storage ; https://claude.com/docs/third-party/claude-desktop/import ; https://claude.com/docs/third-party/claude-desktop/unified-claude .


### CLUE — memory/retrieval layer, not session migration (candidate #253)

`henryyu333/CLUE` is MIT local-first personal memory plus text-only local recall for seven coding Harnesses. Its approve/Git-receipt/undo workflow and rebuildable SQLite FTS cache are adjacent design references. The session row has no parent/child/project-section graph, files, tool/approval/token events or destination writer; transcript parsing truncates and redacts text. `clue export` is a secret-scrubbed context pack, not a chat/session export. The Claude adapter wires Claude Code CLI hooks only, not Claude Desktop 3P Chat/Cowork/Code. Tests/typecheck were not run because the required Bun executable is absent; do not assign fidelity/round-trip claims. See `docs/research/evidence/henryyu333-clue-review-2026-11-24.txt`.

Anthropic's provider guide now explicitly lists its Enterprise migration's supported scope: own Chats/Projects and on-device Cowork/Code sessions. Cloud Cowork sessions and uploaded/project-knowledge files do not move; memory, personal instructions, Skills and connectors require separate handling; a Desktop session ZIP excludes Claude Code CLI sessions. Personal exports cannot be imported into another personal Claude account. Keep these as distinct source/version-specific lanes; do not equate them with ChatGPT migration or generic API-key behavior.


### Smyrti — README claim only; provenance stop (candidate #254)

`Hrishikesh2512/Smyrti` advertises a ChatGPT/Claude/Gemini web-UI “working memory” continuation prompt, not raw transcript migration. GitHub returns `license: null`, and the tracked tree contains no grant. The source was not reviewed or run. Do not list it as a compatibility adapter or make any fidelity claim; it remains a discovery lead pending explicit licensing and a fresh source audit. See `docs/research/evidence/hrishikesh2512-smyrti-screen-2026-11-24.txt`.


### agent-session-grep — SessionGraph/search prior art, not a migrator (candidate #255)

`Lain-in-coding/agent-session-grep` has a useful message-level model (stable Session ID; text Messages; source-document fingerprints; occurrence placements; optional spans; parent/fork/sidechain edges). It supports 14 local coding Harnesses, all Experimental, but no ChatGPT source or Claude Desktop 3P target. `Session` is only an ID; no Project/Section or session-to-session graph exists. Attachment/content-block support is only a Draft RFC; shipped Messages are plain text. Its deterministic handoff pack does not inject, and native resume runs the source CLI rather than converting the Session. Full workspace tests/fmt/Clippy passed, but no real-app transfer was tested. See `docs/research/evidence/lain-in-coding-agent-session-grep-review-2026-11-24.txt`.


### AgentSessions — close sibling of agent-session-grep, not a migrator (candidate #256)

This snapshot adds a local-search usage Skill, but no Skill/MCP config importer. Its provider-session graph and provider adapters are materially the same family as #255; all 199 of its Rust crate files exist in that later repo, 160 byte-identical. It has no ChatGPT source, Project/Section graph, Claude Desktop 3P target writer or transcript conversion. The README's external-process adapter wording conflicts with the contributor guide, which says that protocol remains planned; no loader/schema exists in the current tree. Full code and test review: `docs/research/evidence/lain-in-coding-agent-sessions-review-2026-11-24.txt`.


## Candidate #257: landywei/my-ex capability result

| Capability | Observed result |
|---|---|
| Native source | Codex local JSONL only |
| Projects / Section Groups / cross-Session hierarchy | Not represented; CWD/thread name only |
| Session/turn content | First request/last reply summary; detailed user + combined assistant text + tool I/O, capped |
| Images/files, timestamps, token usage, forks/subtasks, exact event order | Not preserved by the projection |
| Skills / MCP / plugins / schedules / memory state transfer | None; MCP is a read/search endpoint only |
| Target write / import / rollback | None |
| Claude Desktop 3P Chat / Cowork / Code or Claude Code API gateway | No target adapter or compatibility test |

Disposition: adjacent local Codex-memory retrieval example; not a migrator. See research/evidence/landywei-my-ex-review-2026-11-24.txt.


## Candidate #258: agentlog capability result

| Capability | Observed result |
|---|---|
| Native source | Claude Code CLI, Codex rollout JSONL, DSH JSONL.zstd |
| ChatGPT / Projects / Section Groups | Not supported or represented |
| Transcript fields | One Session ID, CWD, title, timestamps, model, ordered Turns, text/thinking/tool blocks, aggregate usage |
| Parent/fork/subtask graph, assets/attachments, schedules, Skills/MCP/plugins | Not preserved or imported |
| Output | Read-only listing/search/show plus standalone JSON/Markdown export |
| Target import/write / Claude Desktop 3P or Claude Code gateway | None |
| Quality | Go test/vet/build + gofmt pass; source suite lacks DSH adapter test; synthetic DSH reader test passes |

Disposition: high-value adjacent ReaderAdapter/export prior art, not a migration engine. See research/evidence/liyixuan201211-agentlog-review-2026-11-24.txt.


## Candidate #259: AgentGit capability result

| Capability | Observed result |
|---|---|
| Native input | Manually started agent task + repository file snapshots |
| Task hierarchy | parentSessionId/flowId/branchName for AgentGit records only |
| Existing Harness Session import | None |
| ChatGPT Projects/Sections/attachments/token data | Not read or represented |
| Skills/MCP/plugins/schedules | MCP tools are for AgentGit task ledger; no resource migration |
| Target Chat/Cowork/Code/Claude Code gateway write | None |
| Safety | Preview token and conflict checks; synthetic ../outside ledger path bypassed project boundary and deleted sibling |
| Privacy | Ordinary .gitignore not honored; synthetic .env copied into snapshots; sensitive scan only reported changed files and did not redact |

Disposition: adjacent task-flow and file-provenance patterns only; security blocker for reuse. See research/evidence/nexivaservices-agentgit-review-2026-11-24.txt.


## Candidate #260: NomaDamas/wombat capability result

| Capability | Observed result |
|---|---|
| Native sources | 20 local coding-agent parsers, including Codex and Claude Code CLI; no ChatGPT export parser |
| Projects / Section Groups | No first-class Project or Section model; a cwd-derived slug is only a mirror path component |
| Session hierarchy | Optional provider-specific subagent parent ID/flag; no general root/session/branch/task graph |
| Turn fidelity | Role + plain text + timestamp + source offset; provider-dependent tools, reasoning, context, images/attachments and other blocks are dropped from mirror |
| Trace | Re-reads the original source file by path/offset; not self-contained after source removal |
| Output | Local prefix-stable Markdown mirror, SQLite catalog, optional MinSync search; not a target-native session export |
| Skills / MCP / plugins / memory / schedules | Not imported or modeled |
| Claude Desktop 3P Chat / Cowork / Code | No source or target adapter demonstrated |
| Local Claude Code API-key/gateway | Reads Claude Code CLI history only; no gateway session writer/restore |
| Verification | 74 repository tests pass; fmt passes; strict Clippy has one lint; no live cross-Harness transfer tested |

Disposition: broad multi-Harness **reader/search prior art only**, not a Destruction Era migrator. See `docs/research/evidence/nomadamas-wombat-review-2026-11-24.txt`.


## Candidate #261: Rylaispirit/grok-build-manager capability result

| Capability | Observed result |
|---|---|
| Harness | Grok Build CLI only; local manager UI |
| Project model | User-selected filesystem cwd; Git/worktree controls; no imported ChatGPT Project/Section Group |
| Session model | Native Grok session id/created/updated/status/summary; resume/fork delegated to Grok CLI; no cross-session graph |
| Session export/import | Markdown export via `grok export`; no ChatGPT source or target restore adapter |
| Claude Desktop 3P Chat/Cowork/Code | No source/target support demonstrated |
| Local Claude Code API-key/gateway | No adapter; app requires Grok CLI/account |
| Skills / MCP / plugins / hooks | Grok-local management only; no transfer/export model |
| Safety | Loopback + shell:false are positive; synthetic cross-origin text/plain POST reached a fake CLI with `bypassPermissions`; no auth/Origin/CSRF guard |
| Validation | 2 npm tests pass; no route security tests; official npm audit reports 0 advisories for locked dependency |

Disposition: adjacent single-Harness manager/UI prior art only; do not adopt backend without a CSRF/auth boundary and route tests. See `docs/research/evidence/rylaispirit-grok-build-manager-review-2026-11-24.txt`.


## Candidate #262: uniStark/pi-session-find capability result

| Capability | Observed result |
|---|---|
| Native source | Current Pi TUI session only (`getBranch`; `getEntries` with `--all`) |
| Session structure | Entry IDs and active/inactive boolean; no exported parent/branch graph or cross-session edges |
| Content | User text, assistant text, thinking, tool args/results, `!cmd`, custom/compaction/branch-summary meta; images become `[图片]`, unknown block types dropped |
| Projects / Section Groups | None |
| Export/import | None; searching is local/read-only except Enter navigates current Pi position |
| Skills/MCP/plugins/schedules | Not modeled or transferred |
| Claude Desktop Chat/Cowork/Code; Claude Code API-key gateway | No target adapter |
| Validation | npm latest 0.1.0; code matches npm tar; `npm test` fails because script absent; no Pi runtime test |
| Product defect | `meta` category is generated but no UI preset/control exposes it |

Disposition: useful Pi content-reader and active-branch UX reference only; not a Destruction Era migrator. Full review: `docs/research/evidence/unistark-pi-session-find-review-2026-11-25.txt`.


## Candidate #263: uwings/session-migration-prompt capability result

| Capability | Observed result |
|---|---|
| Source | Current AI conversation, summarized by model after manual prompt; no transcript/file parser |
| Projects / Section Groups / Session graph | No object representation; multi-task/file status is prose |
| Exact turns, branches, tool events, attachments, token/model/time data | Not preserved as structured records |
| Skills / MCP / plugins / memory / schedules | Can be mentioned in free text only; no automated transfer |
| Destination | User pastes summary into a new chat; no Claude Desktop Chat/Cowork/Code or Claude Code gateway writer |
| Tests / accuracy | No test suite or reproducible benchmark artifacts; README score claims unverified |
| License | README says Apache-2.0; LICENSE and GitHub detect MIT—conflict unresolved |

Disposition: prompt/Skill summary fallback only, explicitly lossy; not a native session migration adapter. See `docs/research/evidence/uwings-session-migration-prompt-review-2026-11-25.txt`.


## Candidate #264: windviki/sessiondex capability result

| Capability | Observed result |
|---|---|
| Native sources | Claude Code CLI, ZCode, Kimi Code, DSH, Qoder, OpenCode |
| Session model | Agent/session id/title/cwd/source paths/times/subagent boolean; no parent edge/project/section model |
| Message projection | Role/text/reasoning/tool summaries/timestamp/locator/subagent/cwd; no typed attachments, token/model metadata or target resource state |
| Storage | Contentless FTS postings; SQLite stores capped text/reasoning/tool excerpts plus session metadata and source paths/locators |
| Full message retrieval | Re-reads original source through locator; requires source file to remain |
| Import/export/target writer | None; CLI/REST/MCP are search/list/show/read/scan |
| Claude Desktop Chat/Cowork/Code, ChatGPT Projects/Sections | No source or target adapters |
| Security | Default host loopback and token unset; token is optional. Synthetic `/api/messages/read` with untrusted locator read a temp JSONL outside configured root; token-on blocks missing token |
| Validation | 61 synthetic tests pass; test suite lacks untrusted-locator boundary test |

Disposition: high-value read/search/MCP prior art, not Session migration. See `docs/research/evidence/windviki-sessiondex-review-2026-11-25.txt`.


## Candidate #265: yoyooyooo/pi-session-history capability result

| Capability | Observed result |
|---|---|
| Native source | Pi local `sessions/<project>/*.jsonl` only |
| Session model | ID/path/time/size/cwd/title/record/diagnostic counts; no Project/Section Groups or cross-session parent graph |
| Read fidelity | Trajectory-normalized, paginated text; bounded tool args/results; no demonstrated typed-attachment, usage, or complete event/branch portability |
| Interactions | `pi_history` list/search/read; `/history` preview, prompt handoff, or explicit native `ctx.switchSession` resume |
| Import/export / target writer | None; no ChatGPT/Codex source or Claude Desktop Chat/Cowork/Code / Claude Code writer |
| Skills/MCP/plugins/memory/schedules | Not transferred |
| Safety / privacy | Resolves real paths and rejects outside-root/symlink escape; response includes private local path/cwd; no live-user data tested |
| Validation | 10 npm tests pass; format/lint/typecheck and pack dry-run pass; 0 production audit findings, 9 total dev+transitive findings |

Disposition: useful narrow Pi local reader and path-boundary reference; not a session/project migrator. Full evidence: `docs/research/evidence/yoyooyooo-pi-session-history-review-2026-11-25.txt`.


## Candidate #266: Abhiram-Vengala/Continuum capability result

| Capability | Observed result |
|---|---|
| Source ingestion | Chrome DOM text scraping for ChatGPT, Claude.ai and Gemini web UI; no account export/archive parser |
| Stored object | Typed semantic `MemoryUnit` notes with scope/confidence/source_session; original turns are not retained |
| Project / section structure | `project_id` only appears in an unused schema field; no Project, Section Group, folder or membership graph |
| Session hierarchy / fidelity | One ID per visible conversation; no parent/fork/subtask/branch edges, turn IDs/order, attachments, tool events, token usage or schedules |
| Destinations | Rendered prompt for a provider and manual clipboard copy into a new chat; no native import, session create/resume, export archive or target writer |
| Claude Desktop 3P Chat/Cowork/Code / local Claude Code | No target reader/writer or gateway/session-state integration |
| Skills/MCP/plugins/memory | Memory extraction notes only; no reusable Skill/MCP/plugin/credential migration. Groq sees recent message text. |
| Safety / durability | No API auth; wildcard CORS; direct-script bind 0.0.0.0; global episodic/semantic reads can mix sessions; Qdrant `:memory:`; checked-in SQLite DB with one record (content not opened) |
| Validation / legal | No LICENSE file / SPDX and no automated tests; unittest discovery: 0 tests (exit 5). Python AST + five Node syntax checks pass. |

Disposition: adjacent memory-extraction prior art only; not a session/project migrator and not eligible for backend reuse without license, privacy, isolation, persistence and security remediation. Full review: `docs/research/evidence/abhiram-vengala-continuum-review-2026-11-25.txt`.

## Candidate #267: Aixand/manager-suite capability result

| Capability | Observed result |
|---|---|
| Scope / license | Five independent managers (Agent, Conversation, MCP, Prompt, Skill); Apache-2.0; pinned main `7be93efc46eb1068745904b0764ae77c54aaafe4`; beta candidate |
| ChatGPT intake / Projects / Section Groups | No ChatGPT archive parser or ChatGPT project/section entity model |
| Session continuity | Claude/Copilot same-provider continuation reuses original native history under a destination profile; cross-provider continuation unsupported. OpenCode can make same-provider native-export copies with Manager identity/revision ancestry/explicit branches |
| Session hierarchy / fidelity | OpenCode copy graph is useful adjacent lineage prior art, not a general parent/subtask/fork graph; child sessions, runtime state, external artifacts, and in-progress work are not fully copied |
| Conversation Manager | Creates/retains locally managed conversations, turns/events/queues/approvals; lists its recorded references rather than all provider history; documented transcript readback is provider-dependent (Codex path implemented) |
| Skills/MCP/prompts | Local/GitHub import into owned stores with explicit acceptance/reconciliation; application delivery is separate; no automatic existing-Harness adoption, plugin, credential, memory or schedule migration |
| Claude Desktop 3P Chat/Cowork/Code | No reader, mode-aware data model, native writer, or post-import reopen check for any of the three confirmed modes |
| Local Claude Code API-key/gateway | Constrained Linux+version same-provider CLI continuation; no ChatGPT source import or gateway-mode migration qualification. Credentials remain provider-owned |
| Validation | All five component checks pass locally; Conversation 278 pass/59 skipped after temp-path correction; Prompt 215 pass; Agent 1 failure/44 errors/80 skipped; MCP 1 failure/1 skipped; Skill 2 errors/1 skipped |

Disposition: keep stable logical references, copy ancestry/branch tracking, idempotent receipts, version-gated native continuation, and explicit resource provenance/delivery as design references. Do not count this as a migration success or reuse code wholesale. Full evidence: `docs/research/evidence/aixand-manager-suite-review-2026-11-25.txt`. Primary inventory **267/303 reviewed, 36 pending**; next `Alot1z/agents-handoff`; supplemental net-new 177 pending; manual additions 21/9 pending; unresolved 213 primary+supplemental / 222 including manual. Research remains active/incomplete.

## Candidate #268: Alot1z/agents-handoff capability result

| Capability | Observed result |
|---|---|
| Scope / license | `agents-handoff` 2.0.7, MIT; generic portable handoff Skill/package; no runtime dependencies |
| Input | JSONL lines or role-marked plain text; standard ChatGPT ZIP/`conversations.json` mapping export not parsed (synthetic `conversations.json` returned exit 4) |
| Project structure | One slugged project folder with a flat `PROJECT.md` session list; no Section Groups, source project memberships or section mapping |
| Session model | Single ordered timeline and watermark; no parent/fork/branch tree or native message IDs. Cross-project links are keyword/Jaccard notes, not structural relationships |
| Content fidelity | Text + flattened tool-call text; raw source file is not included. Synthetic image bytes, usage fields, `parentUuid` and message IDs are absent from output |
| Destination | Folder artifacts readable by a fresh agent, not a target-native session import. No Desktop 3P Chat/Cowork/Code writer or local Claude Code gateway resume |
| Resources | Skill package is installable to Claude Code/Codex/generic skill folders; no migration of the user's installed Skills/MCP/plugins/memory/schedules/credentials |
| Security / integrity | Synthetic `--project .. --session ..` wrote files outside `HANDOFFS_ROOT` and overwrote a sibling sentinel. Secrets are not scanned/redacted and are written in clear text. Same-line-count timeline edit still verifies; hashes are self-consistent, not signed. |
| Validation | Node 26.7/npm 11.19: 53 CLI tests, 6 demo tests, docs check, and 2-session index check pass; synthetic probes exposed missing boundaries. No live user data/apps were accessed. |

Disposition: useful portable **handoff-only** design reference; not a Destruction Era session migration or native import. Do not adopt the writer without root containment, atomic writes, sensitive-data controls and output-integrity verification. Full evidence: `docs/research/evidence/alotz-agents-handoff-review-2026-11-25.txt`. Primary inventory **268/303 reviewed, 35 pending**; next `Aryan-sourcee/context-capsule`; supplemental net-new 177 pending; manual additions 21/9 pending; unresolved 212 primary+supplemental / 221 including manual. Research remains active/incomplete.


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


### Claude Desktop third-party-mode control surface checked 2026-11-25

The live official Configuration Reference exposes a gateway provider selector (`inferenceProvider: gateway`), gateway base URL and gateway API-key fields, and independent Chat, Cowork, and Code capability settings. It also defines separate retention controls for Chat, Cowork, and Code. `scheduledTasksEnabled` is documented for Cowork and Code, not as a generic Chat transcript feature. This confirms the three Desktop modes have distinct settings/lifecycle surfaces and must be validated independently. **These are deployment/configuration controls, not a public cross-Harness history-import API.** The reference says `chatTabEnabled` and `coworkTabEnabled` are deprecated after 2026-12-17 in favor of `desktopHome`; exact setting names and version gates must be rechecked at implementation time. Source: [Claude Desktop Configuration Reference](https://claude.com/docs/third-party/claude-desktop/configuration) (gateway keys and surface toggles; session-retention and scheduled-task entries). Do not write gateway secrets into a portable archive or copy an API key as ordinary JSON.


## Candidate #278 — datawithdanny/cache-manager-mcp (2026-11-25)

Pinned default-branch HEAD `1609df1e075746e7c5556a2fdd46d38679302781` (2026-06-26, `Add value-explainer SVG to README`), package `@dannyma/cache-manager-mcp@0.1.4`, MIT. It is a local stdio MCP server with a small Zed extension wrapper. Its useful adjacent capability is an agent-authored Markdown checkpoint with an alias/session key and optional flat `project_group`, returned to an agent on a later `resume_or_start`; it also supplies heartbeat/TTL dashboards and Claude Code token/cache cost estimates. It is not a native transcript importer: README explicitly says most MCP clients do not expose stable native thread IDs, exact thread restore is not automatic, and the notifier cannot observe host-client messages, create a chat, prefill it, or know its native ID. Its restart path is “read summary, start a fresh client conversation,” not restoration of the old chat.

The stored “session” is timer metadata (ID, label, cwd, timestamps, a bounded heartbeat/action tail and optional Claude transcript IDs) in `sessions.json`; aliases, titles and one free-form project group are in `aliases.json`; checkpoint content is an agent-supplied Markdown summary. There is no source Project/Section/branch/subtask graph, message/event sequence, image/file bytes, tool trace, MCP/plugin/Skill inventory, schedule import, or target-native writer. The group is a sticky dashboard label, defaulting to the working-directory basename; README lists project-scoped memory stores as future work. Usage/cost collection is a separate Claude Code JSONL reader, not transcript transfer; hard-coded prices are documented as a June-2026 snapshot and may be stale. Its instruction protocol relies on the model calling `resume_or_start`, `heartbeat`, and `checkpoint`; the server itself cannot clear or prefill a client conversation. Generic MCP interoperability is not proof of support across Claude Desktop Chat/Cowork/Code or local Claude Code gateway configurations.

`npm test` passed all 10 chained smoke scripts (including 30 web-dashboard checks, 4 failover checks, MCP, notifier, timers, attribution and project-group behavior). The root Zed Rust shim compiles with `cargo test --manifest-path Cargo.toml`, but reports **0 tests**. No authenticated desktop, transcript, external gateway, or real user data was exercised. Two disposable `/tmp` probes exposed security/integrity caveats: `save_memory` wrote the synthetic summary as a plain Markdown file with mode `0644` and the store directory as `0755` under this review host's inherited umask; and after a deliberately malformed synthetic `sessions.json`, `start_session` returned `ok: true` and rewrote the index from an empty fallback, replacing the malformed bytes without a warning. Source also uses direct, non-atomic JSON writes and no locking while README describes multiple MCP clients sharing a store; concurrent-update loss is a source-level risk, not dynamically reproduced. Startup pruning defaults to 30 days while preserving only the newest checkpoint per session/alias, so it is unsuitable as an archive of all historical checkpoints.

Disposition: **not a Harness migration engine and not an AI-independent universal transfer tool**. Retain only the local, cross-chat checkpoint-memory pattern, alias naming, and project-label UX as optional adjacent MemoryPlane ideas; a Nexus implementation should add explicit graph IDs, backup/atomic writes, encryption/permissions, retention audit, and target-specific validation rather than adopting this persistence layer unchanged. It supplies no verified adapter for ChatGPT/Codex Projects/Section Groups/“Destruction Era” or the four user-confirmed Claude tracks. Detailed evidence: `docs/research/evidence/datawithdanny-cache-manager-mcp-review-2026-11-25.txt`.

Inventory: **278/303 primary repositories reviewed, 25 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 202; total pending including manual additions 211. Next primary candidate: `digiogithub/agentd`. Research remains active/incomplete.


## Candidate #279 — digiogithub/agentd (2026-11-25)

Pinned `main` HEAD `0ad5e5f64d5be56f97c82e7e7baf2d97505bd58a` (2026-11-24, `docs: backlog notes plan, mobile phase done in agentd-app`), MIT. This is an active terminal/runtime manager: it launches arbitrary CLI Harnesses (Claude Code, Codex, Pando and other binaries) in PTYs, supports detach/reattach, screen viewing, terminal input, queues/mailbox, per-session task/status views, and a Linux/macOS native desktop client. It can organize running processes with flat project-path aliases and default names such as `codex@webapp`; it does **not** read or restore native ChatGPT/Codex/Claude session archives. Claude CLI/Code inside a managed PTY is a process boundary, not an importer for the tool's native transcript/session format.

Persistence is nuanced: the daemon's live session registry, screen emulator, screen-history/chat view, task list and up-to-100 turn summaries live in memory; the README says daemon restart kills all agent processes and marks session persistence/replay as future work. However, each launched session is assigned a **local raw PTY-output log** at `<state>/logs/<session>.log` (session input may be echoed by the terminal, but this is not a structured conversation transcript, and there is no importer/replay contract). Default cap is 50 MB with one `.1` rollover. The semantic Chat tab reconstructs display items from the live session's bounded `proto.View.Lines`; it is available only for agentd sessions, while zellij/tmux/plain-shell sessions show terminal-only UI. Turn records retain only turn number/outcome/origin/status/timing, bounded to 100 and held in memory; they are not message histories. A per-host versioned `docs.json` document store and SQLite backlog/mailbox are persistent adjacent memory/work-queue features, not cross-Harness conversation archives. Project alias is one path label, not a parent/child Project/Section hierarchy.

The current GitHub Releases page shows **v0.9.0**, released 2026-11-24 from abbreviated commit `0ad5e5f`, matching this checkout. The current README still labels the software “prototype (v0.1, pre-release),” so release-status wording is stale. GitHub CI run #37 passed for this same latest commit on Linux; workflow tests/vets on Linux and only builds/vets on macOS. On this macOS arm64 review host, Go was absent from PATH, so the official Go 1.27.4 darwin-arm64 archive was downloaded to `/tmp`, checksum-verified against go.dev and used without installing globally. `go build ./...` and `go vet ./...` passed. `go test ./...` exited 1 with reproducible Mac test failures: `cmd/agentd/TestShimConflicts` (the own-symlink re-link is rejected; source compares `EvalSymlinks(link)` to a non-canonical executable string), `internal/daemon/TestReviewPromptBeforeSubmitRecheck` (expected a `conflict` guard when a menu appears after paste, got nil), `internal/desktopui/core/TestLaunchFirstPrompt` (first prompt was not executed; Bash displayed `00~echo first-$((2+3))01~` then `00~echo: command not found`), and provision tests that see Homebrew executables appended from `SystemBinDirs` despite their temporary PATH. Each was rerun individually and reproduced. The provision failures are host/test isolation sensitivity; the guard and prompt failures are potential macOS-specific behavior gaps. Do not infer the Linux CI run covers them: the macOS job does not run tests.

Security/portability positives from code and docs: the daemon uses a user-only Unix socket (0700 directory, 0600 socket), session log directory/files use 0700/0600, process identity and ACL checks, and optional SSH/Noise relay with view/operate/admin scopes. The README warns same-user hostile code can inspect process environments/ptrace; session tokens are passed to child environments. Default mode is local; only mailbox message bodies are sent to recipient agents/model providers. Windows is unsupported. The desktop/mobile clients are operational manager frontends (mobile is a separate repository), not history migrators.

Disposition: **strong adjacent multi-agent terminal orchestration prior art, but not a Nexus Memory migration engine**. Retain its alias/path naming, live-session UX, bounded turn/event stream, task/mailbox and permission/relay ideas for a separate OrchestrationPlane. Do not treat its PTY logs or chat-shaped live view as lossless source history, and do not claim Project/Section/branch hierarchy, attachments, token accounting, Skills/MCP/plugin transfer or native ChatGPT/Codex → Claude Desktop/local Claude Code restore. Candidate source: [pinned README](https://github.com/digiogithub/agentd/blob/0ad5e5f64d5be56f97c82e7e7baf2d97505bd58a/README.md); release and CI evidence is recorded in the review ledger.

Inventory: **279/303 primary repositories reviewed, 24 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 201; total pending including manual additions 210. Next primary candidate: `ekpootu/ai-agents-document-os`. Research remains active/incomplete.


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


## User reaffirmation — Claude Desktop modes (2026-11-25)

The user clarified that **all three Claude Desktop modes—Chat, Cowork, and Code—are included**. Keep them as three distinct acceptance lanes, independently checking gateway setup, local/cloud state boundary, transcript discovery, attachment/asset behavior, native resume, and supported import/write paths. Do not collapse them because they share a client, gateway, or some storage. Local/self-hosted Claude Code is a separate fourth lane; Anthropic-hosted Cloud remains explicitly out of the API-key/gateway target unless separately authorized. The source name remains **Destruction Era**.

## Candidate #296 — rucnyz/agents-sesame (2026-11-25)

`agents-sesame` is a MIT-declared Rust local session-history search/preview/resume TUI, not a portable migration tool. It indexes flat text/session metadata for ten coding agents and resumes in the original CLI; it has no ChatGPT Project/Section importer, no Claude Desktop 3P Chat/Cowork/Code adapter, no Claude Code writer, and no Skills/MCP/plugin/memory/schedule/attachment/API-key migration. Its Claude-only `ase relocate` moves storage between Claude Code project directories, not between harnesses.

Pinned checkout `3d3ab396a08a96c0a8a9f063eb2ba31c17069fcb`, v0.1.2; `Cargo.toml` declares MIT but checkout lacks LICENSE text. Source review found flat schema with no Section/Project or parent/branch/subagent graph, plus content projection omissions. Synthetic relocation-to-nonexistent-directory exited 0 and rewrote cwd to that path. Synthetic fake HOME 0755/umask 022 showed index 0755 and segment files 0644 with a fabricated marker. Keep as search UX reference only; gate reuse on license-text/provenance follow-up. `cargo test --locked` 75 passed; build/fmt passed; strict CI Clippy failed (12 style warnings promoted to errors, exit 101). No real user history was read. Evidence: `docs/research/evidence/rucnyz-agents-sesame-review-2026-11-25.txt`.

Inventory: **296/303 primary candidates reviewed, 7 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 184; total pending including manual additions 193. Next primary candidate: `sabaiway/agent-workflow-kit`. Research remains active/incomplete.


## Candidate #297 — sabaiway/agent-workflow-kit (2026-11-25)

`sabaiway/agent-workflow-kit` (MIT, v1.3.0, Node >=18) is useful adjacent prior art for **curated project memory and a portable Skill/workflow**, not a session or project-hierarchy migrator. It deploys an `AGENTS.md` entry point, a `CLAUDE.md` alias, `docs/ai/` handover/plan/state/decisions/issues/changelog/history files, and cap/index/archive checks. Its bootstrap/upgrade is an AI-agent procedure that asks the user decisions; the installer only copies the skill payload. There is no ChatGPT Project/Section import, session transcript/event/fork/subtask graph, attachment/usage preservation, Claude Desktop third-party-gateway Chat/Cowork/Code writer, or local Claude Code transcript importer. No MCP/plugin/API credential/scheduled-task migration. Codex and Devin Desktop receive thin launchers; other `AGENTS.md` consumers need manual integration. Windows skips POSIX launchers.

A synthetic fake-HOME reproduction found the Codex launcher silently replaces **any** existing `~/.codex/skills/agent-workflow-kit` symlink even without `--force` and creates no backup; a regular-file conflict is left alone. No user home was accessed. The code/test suite: 44/44 helper tests pass, installer and shell syntax checks pass; no installer/launcher/bootstrap integration tests. Retain as curated-memory architecture reference, not a full-history transfer dependency; fix the symlink ownership check before operational use. Full evidence: `docs/research/evidence/sabaiway-agent-workflow-kit-review-2026-11-25.txt`.

Scope remains Claude Desktop third-party-inference **Chat, Cowork and Code as three separate acceptance lanes**, plus local/self-hosted Claude Code as a fourth. They are not collapsed by shared Markdown, gateway, or client. Source target remains **Destruction Era**.

Inventory: **297/303 primary candidates reviewed, 6 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 183; total pending including manual additions 192. Next primary candidate: `SamiAhmadBeg/Continuity`. Research remains active/incomplete.


## Candidate #298 — SamiAhmadBeg/Continuity (2026-11-25)

`Continuity` is the most directly named web-context bridge reviewed in this slice, but it is a Chrome extension for scraping rendered pages and injecting a prompt—not a native session/project migrator. It stores flat last-query/last-response context records, not full conversation trees. No ChatGPT Projects/Sections, branches/subtasks, tool results, usage, attachments, stable session IDs, MCP/Skills/plugins, schedules, or target-native writers. `claude.ai` URL support does not mean Claude Desktop Chat/Cowork/Code or local Claude Code support. API keys are only for hardcoded OpenAI/Anthropic summarization endpoints; no gateway base URL exists.

Source snapshot is MIT, manifest v1.0.0, commit `9ffd4e3538ae569d5433ef3911ba069d259d12a1` (2025-07-30); official repository shows 0 stars/forks, 3 commits, no releases. There is no automated test suite; the HTML “test suite” simulates success rather than exercising the extension. Synthetic VM checks reproduced: popup init crashes due missing `status` element; API key input IDs mismatch; Clear All removes storage but leaves the live service-worker Map returning the supposedly deleted record; “Use LLM Summary” toggles a wrong key and the background ignores it; mocked background path attempts to send a synthetic marker to hardcoded OpenAI despite the false setting. No network or real user data was involved. The manifest omits the external API host permissions required by Chrome for service-worker cross-origin fetch, so the LLM path is also not operational as configured. Do not use as a migration engine; keep only as lossy handoff UX prior art, not production code. Full review: `docs/research/evidence/samiahmadbeg-continuity-review-2026-11-25.txt`.

Scope remains Claude Desktop third-party-inference **Chat, Cowork, Code as independent acceptance tracks**, plus local/self-hosted Claude Code; the browser extension's `claude.ai` page match is not acceptance for those clients. The source project remains **Destruction Era**.

Inventory: **298/303 primary candidates reviewed, 5 pending**; supplemental net-new catalog 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 182; total pending including manual additions 191. Next primary candidate: `Seroliya/session-history`. Research remains active/incomplete.


## Candidate #299 — Seroliya/session-history (2026-11-25)

`session-history` is a high-value **read-side** Skill/CLI for DSH, Codex and local Claude Code transcripts. It builds a typed turn/item model with references, views, token/character budgets, tool/action extraction, lineage, compaction and handoff. It is not a migration engine: no ChatGPT source/Projects/Sections, no Claude Desktop Chat/Cowork/Code reader or writer, no destination import/export adapter, no attachment bytes, skills/MCP/plugins, schedules, gateway credentials or loss report. It can inform Nexus source parsers and lineage model but cannot transfer **Destruction Era** into Claude.

The MIT v1.1.0 source snapshot has a major privacy gap: display output redacts synthetic API-key text, but default disk caches persisted the unredacted key in `index.json` and gzip digest files at 0644 under a 0755 fake HOME/cache. `--no-cache` avoids that cache. The installer/uninstaller also treats any symlink at the reserved skill slot as owned; a synthetic fake DSH_HOME showed install overwriting and uninstall deleting user-created symlinks without backup/`--force`.

`npm test` exits 1 on this macOS host: 21/21 Claude synthetic checks pass, but installer idempotence is 10/11 due `/var/folders` vs `/private/var/folders` path canonicalization. Separate synthetic DSH multi-frame and Codex parent/fork smoke probes passed; no real history or network call was used. Full evidence: `docs/research/evidence/seroliya-session-history-review-2026-11-25.txt`.

User-confirmed target scope remains Claude Desktop third-party-inference **Chat, Cowork, Code as separate acceptance lanes**, plus local/self-hosted Claude Code; this read-only skill supports only the last of those as a source, not a target.

Inventory: **299/303 primary candidates reviewed, 4 pending**; supplemental net-new 177 pending; manual additions 21 total / 9 pending; primary + supplemental pending 181; total pending including manual 190. Next primary candidate: `Shivala-08/contex-landing-page`. Research remains active/incomplete.


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
