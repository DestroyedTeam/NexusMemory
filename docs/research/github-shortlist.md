# GitHub candidate screening — preliminary snapshot (2026-11-20)

## Discovery corpus

An anonymous GitHub repository-search API sweep used 12 broad queries across session migration/history, cross-harness portability, agent frameworks, skills managers, MCP managers, memory/handoff, and coding-agent history. It returned **309 result slots and 303 unique repository names** after deduplication. A separate manual review has now added **11 supplemental projects** that were not in that initial corpus; their review status is recorded separately in [`github-candidates.json`](github-candidates.json).

The deterministic keyword buckets are only triage aids: 89 session/conversation-portability candidates and 214 adjacent capability/harness candidates in the API corpus. This is not 303 approved projects. The next stage is to remove duplicates, abandoned shells, unrelated matches, missing/unacceptable licenses, and repos without verifiable code/tests, then deeply review a small evidence-backed shortlist. Stars are a discovery signal, not a quality score.

One candidate was immediately excluded after its license restricted OpenAI/Anthropic use; its clone and test artifacts were removed and it is not treated as a dependency or benchmark.

## Code/test reviews completed so far

| Candidate | Evidence collected | Preliminary value | Gaps / status |
|---|---|---|---|
| [`xhluca/session-migrate`](https://github.com/xhluca/session-migrate) — MIT | README/source inspect; `uv run pytest`: **1,757 passed, 63 skipped**. README claims 18 harness formats and 324 ordered routes; its route matrix is version-pinned and distinguishes native tests from skipped exact-client gates. | Strong adapter/test-pattern reference for native coding-session conversion. It explicitly reports omissions and provides target resume flows. | Not a full Project/Section or configuration migration system. Its own matrix excludes auth, hooks, policies, MCP and runtime config; branches/subagents are not generally reconstructed as target-native relationships. 63 native/client tests were skipped in this environment. |
| [`connectwithprakash/agent-session-bridge`](https://github.com/connectwithprakash/agent-session-bridge) — MIT, low-star | CodeGraph source inspection; `uv run pytest`: **312 passed, 1 skipped**. Its IR contains typed text/reasoning/tool-call/result/raw blocks, message IDs/parents, pending state, and a conversion report. The tests explicitly exercise branch-topology warnings. | Valuable low-star example of a small, auditable canonical IR and per-conversion asymmetry reporting. | Only Claude Code, Codex, and Hermes in the reviewed version; its docs say forks flatten when leaving the one harness with native branch IDs. No hosted ChatGPT Projects/Sections. |
| [`RealZST/HarnessKit`](https://github.com/RealZST/HarnessKit) — Apache-2.0 | Source inspected for adapter model; frontend `npm run build` passed (one bundle-size warning); frontend tests **374 passed / 45 files** with `NODE_OPTIONS=--no-experimental-webstorage`; Rust workspace tests **875 passed**. | Strong adjacent reference for enumerating skills/MCP/plugins/hooks/configs across many harnesses, with an adapter-based architecture and security/audit surface. | It manages extension/config inventories, not transcript/project-session migration. Source inspection shows the Hermes adapter does not yet model project-scope skills. Raw `npm test` on Node 26 initially failed because Node's experimental global `localStorage` shadowed jsdom; the test suite passed with the environment flag. |
| [`neiii/bridle`](https://github.com/neiii/bridle) — MIT | Source inspection of profile manager, harness paths, MCP parser and `EnvValue`; `cargo test --workspace`: **658 passed, 2 ignored**. | Useful configuration-profile and native-schema translation reference for Claude Code/OpenCode/Goose/Amp/Copilot CLI/Crush. | It switches profiles/configurations; it is not a session-history or Project hierarchy importer. Source inspection shows MCP env values may be represented as `Plain(String)` and emitted unchanged; Nexus Memory must not copy credentials into bundles or target configs by default. |
| [`vshulcz/deja-vu`](https://github.com/vshulcz/deja-vu) — MIT | README + code-level model/handoff/index review; repository claims 49 agent transcript sources, local indexing, search, MCP and compact cross-agent handoff. A local Go test could not run because `go` is absent from this environment; no test result is claimed. | Strong adjacent reference for local session catalog/search, provenance, memory recall and handoff across many agents. | Handoff/memory/search are not the same as native session import. The 49-source claim and accuracy still need tests/version evidence; not yet ranked as an implementation dependency. |
| [`jazzyalex/agent-sessions`](https://github.com/jazzyalex/agent-sessions) — MIT, v6.6 | Pinned `3dfa0405d204279b7581d85218ea04fa218af8a7`; source-reviewed session/event model, source registry, subagent hierarchy, archive manager, resume path and Markdown exporter. Full Xcode suite: 4,586 passed, 9 skipped, 1 locale-sensitive currency assertion failed; isolated failure passed under en-US. | Strong macOS UX/catalog reference: local search across 16+ sources, structured tool/error/meta events, limited native subagent/side-chat hierarchy, local file snapshot archive, and resume into supported original CLIs. | Not a source-to-target migrator. No ChatGPT source/Project/Section importer or Claude Cloud/API-key writer. Markdown export is presentation-oriented; app-local pinned archives are not cross-Harness bundles. No actual CLI/provider resume was run. Details: [RESEARCH.md](../RESEARCH.md#deep-review-jazzyalexagent-sessions-2026-11-20). |
| [`asheshgoplani/agent-deck`](https://github.com/asheshgoplani/agent-deck) — MIT | README screen; active cross-platform terminal/TUI for launching and attaching to several agents. | Useful for execution/session-process orchestration and resume UX. | A terminal-process manager is not a transcript converter or project hierarchy migrator. Code/tests not yet audited. |
| [`skillsynchq/txcript`](https://github.com/skillsynchq/txcript) — Apache-2.0, v0.14.4 | Pinned main commit `2bf712e` (2026-11-18); 225 stars/25 forks at review. Audited Rust store/codecs, ChatGPT and Cloud Cowork format docs, tests, and pinned CI (MSRV, stable lint/test, Windows, WASM, npm/crates dry runs all passed). Local tests were not run because this host has Rust 1.95 while the project declares 1.96. | Highest-value current session-adapter reference: native-preserving transcripts, shared Common projection, CLI/MCP/search, many harnesses, and an explicitly gated live ChatGPT reader. | ChatGPT uses Codex `auth.json` with `auth_mode=chatgpt` (not an API-key login or ChatGPT export ZIP), reads via private endpoints, and is pull-only. The common projection follows the active branch; side branches and attachments remain outside it. It writes local Claude Code sessions, not Anthropic-hosted Cloud sessions; Cloud Cowork is a read-only source. A related Skillsync CLI is a separate hosted product, not part of the open-source library. |
| [`wookat/agentmove`](https://github.com/wookat/agentmove) — Apache-2.0, v0.106.0 | Pinned main `17372b1`; model enumerates 47 clients. Local build passed; after building the CLI, 53 test files / 433 tests passed; package typecheck passed. The latest observed main workflow was green. | Broad local configuration/resource transfer for MCP, Skills, agents, commands, instructions, persona and selected memory/config layers; useful complement to a transcript adapter. | Its bundle has no conversation/session/branch/project-section/schedule graph and no ChatGPT adapter. Key-name redaction covers MCP env/headers and raw config, not arbitrary prose; `--include-secrets` bypasses it. Fixture/e2e tests are not live-client compatibility tests. |
| [`shenysun/skills-manager`](https://github.com/shenysun/skills-manager) — MIT, CLI `2026.11.4` | Pinned `948db52fa5dcfdae994073cf9d8c1fd05ab89205`; 243-star metadata snapshot. Full suite: 1,048/1,052 passed, 4 failed; triage shows two Git identity tests pass when `user.useConfigOnly=true`, one bootstrap test is contaminated by host `/Applications/ZCode.app`, and one “fresh” fixture is 92 days old. Bundled catalog source is 2026-08-18; disposable `catalog refresh` received HTTP 403. | Useful shared Skill hub, source provenance, per-scope distribution and rollback reference. | Skill-resource manager only; no Projects/Sections/session graphs, attachments, MCP/plugins, memory, or schedule migration. README’s 70+ agent count is not runtime certification. Catalog freshness/refresh reliability must be versioned and monitored. Details: [RESEARCH.md](../RESEARCH.md#deep-review-shenysunskills-manager-2026-11-20). |
| [`shuqinlee/ConvFlow`](https://github.com/shuqinlee/ConvFlow) — Apache-2.0 | Screened pinned clone `b78dfeb521dcdc2de3ca51a81b9b4f43056e2f70`; tree contains only LICENSE (CodeGraph: 0 files/nodes); GitHub shows one commit, 0 stars/forks, no releases. | No implementation evidence to reuse; description claims ChatGPT/Claude transfer but cannot be validated. | Exclude from technical shortlist unless source code/tests appear. No build, runtime, or compatibility test was possible. |
| [`Sai-Nitin123/ContextBridge`](https://github.com/Sai-Nitin123/ContextBridge) — license unresolved, package 0.2.0 | Pinned `2a4b9b460387679c9dcced9b7cad3b6afa0aa6d8`; clean isolated `npm ci --ignore-scripts`, 53 tests and build passed. Three synthetic probes reproduced secret leaks in derived summary/attachment metadata and a title-based historical-context fence breakout. | Useful local `.aicx` / composer-handoff UX reference; no external request API found in targeted source scan. | Not a native session restore or Claude API-Key/Cloud writer. Flat DOM transcript, no Projects/Sections/branches, metadata-only attachments, broad `<all_urls>` permissions, missing LICENSE; exclude as a dependency. Details: [RESEARCH.md](../RESEARCH.md#deep-review-sai-nitin123contextbridge-2026-11-20). |
| [`z2z23n0/agent-capsule`](https://github.com/z2z23n0/agent-capsule) — Apache-2.0 | Pinned `f506789` (2026-07-23); source-reviewed neutral/session/profile/schedule paths; pinned Go, Worker and deploy checks passed. Local Go tests were not run because Go is absent. | Useful implementation reference for Codex/Claude Code native session handoff, encrypted file/link capsules with source sidecars, and explicit Codex profile backups/verification. | Its profile migrator is Codex-to-Codex across Macs, not ChatGPT-hosted Project/Section to Claude Cloud. Cross-agent neutral transcripts have no branch graph or token/cost fields; schedule-import is a one-shot macOS LaunchAgent to pause/import/reopen Codex, not migration of a recurring task definition. |
| [`mindattic/Ciao-ChatGpt-Bonjour-Claude`](https://github.com/mindattic/Ciao-ChatGpt-Bonjour-Claude) — license unconfirmed | Pinned `7aa6bc8`; source-reviewed two browser-console scripts. GitHub shows 0 stars and archived by owner on 2026-10-08; no test suite was found. | Useful as an example of the simple “text export, then create chats in one selected Claude Project” route. | The exporter emits flat `.txt` transcripts; the importer sends each complete transcript as one prompt to Claude’s private API. This creates a new chat plus a model response, not the original message tree. It does not preserve ChatGPT Project/Section membership or target a Claude Code API-key session. Exclude as a dependency: archived, no license evidence, private endpoint coupling. |
| [`nrzz/claude-chat-ferry`](https://github.com/nrzz/claude-chat-ferry) — MIT, v1.1.0 | Pinned `1f637d7` (2026-10-29); 450/452 local tests passed with 2 skipped when the Claude binary was kept off `PATH`; all pinned upstream CI matrix checks passed. With local Claude Code 2.1.76 present, the optional fake-API resume test failed its “banner starts the first user message” assertion because a system reminder preceded it. In a disposable copy changing only that assertion to allow the preamble, the resume test passed and verified all imported turn markers plus the new prompt. | Strong small reference for ChatGPT export → local Claude Code session: zero runtime dependencies, read-only export parsing, native JSONL writer, explicit transcript/tool-size controls, secret-redacted Markdown export, and a real resume gate. | ChatGPT input is a static export, not live account/Project data. It follows only `current_node`; sections/project membership, images/attachments and token usage are not restored. Tools are summaries, and reasoning is optional. It writes to a local Claude Code project, not hosted Cloud. The upstream banner-at-byte-zero assertion is brittle across user/system context and Claude Code versions. |

## Native capability worth exploiting

OpenCode's CLI documents JSON import/export (with optional lossy `--sanitize`), while the HTTP transfer routes are marked experimental. Source review at `anomalyco/opencode` commit `011f9043e8a90dc9a1ac42fb1181486dd4d13b71` found a one-session `{info,messages}` transfer schema with structured messages, token/cost fields and inline-media handling. Parent IDs can be preserved only when imported topologically; source inspection suggests explicit fork boundaries are not replayed, and `time.updated` resets to import time. Open issue [#54336](https://github.com/anomalyco/opencode/issues/54336) reports message-ID collisions returning 500; the current pinned import code still inserts original message IDs without a visible preflight. This is a promising native adapter candidate with explicit loss/security gates, not a universal ChatGPT/Codex importer. No OpenCode CLI/API runtime or test suite was run in this review. [API](https://opencode.ai/docs/api) · [CLI commands](https://opencode.ai/docs/cli/commands) · [pinned transfer source](https://github.com/anomalyco/opencode/blob/011f9043e8a90dc9a1ac42fb1181486dd4d13b71/packages/core/src/session/transfer.ts)

## Preliminary conclusions

1. The market is not “only Skills/MCP” anymore: there are direct transcript converters, local catalogs, handoff/memory systems, terminal session managers, and extension/config managers. Their labels overlap, but their deliverables are materially different.
2. No candidate reviewed so far proves a single lossless path that recreates ChatGPT/Codex project sections, all conversation forks/subtasks, attachments, config/credentials, and native Claude Code API-key sessions together.
3. Architecture should combine a versioned source graph + provider readers/writers + explicit capability/loss reports. Native import is preferred where documented/verified; sidecar archive is mandatory for information the destination cannot represent.
4. The repository survey is not complete. Next deep-review passes must include the remaining high-signal direct converters and cross-agent memory/config projects, with source, tests, license, and update history—not README ranking alone.


## Pi coding agent — reviewed upstream (2026-11-20)

- Repository: earendil-works/pi, MIT, reviewed commit 1e34c3b4c7df78e716a8f53ad0bcf3a00feceedc; coding-agent package snapshot 1.5.2.
- Why it is valuable: compact JSONL session tree with explicit entry parent IDs, separate cross-file parentSession provenance, append-only event types, context compaction, user/project resource scopes, and extension-owned state.
- Important gaps: no stable cross-harness archive contract; no native Project/Section entity evidenced in reviewed core; exact cross-file fork boundary is not established by the header; no built-in scheduler evidenced by reviewed docs. Pi runtime tests were not executed here.
- Evidence: pinned upstream documentation, implementation and test-source links in docs/RESEARCH.md. Migration tests cover v1 ID/parent creation and idempotence but do not directly assert v2 hookMessage conversion; tree/file tests are substantial local persistence coverage, not cross-harness import tests. Test source was inspected, not executed. No rating based on README alone.

## Additional direct-converter screening (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [`MrMirhan/a2migrate`](https://github.com/MrMirhan/a2migrate) — Apache-2.0 | Pinned source review at `e785115`; source-domain/parser/writers/tests examined. GitHub API license field was `NOASSERTION`, but LICENSE/README explicitly say Apache-2.0. Pinned upstream CI passed Go 1.25 tests on Linux/macOS/Windows plus vet, format, lint and build. Local tests not run because Go is absent. | Low-star, useful reference for two-way Claude Code/OpenCode session and resource adapters, SQL transaction rollback, backup and subagent mapping. | Only Claude/OpenCode parsers are implemented; Codex/ChatGPT/Projects/Sections are not. Canonical message list has no event-tree/attachment representation. MCP writer writes raw env/header values into global config with mode 0644; do not reuse without credential redaction and restrictive permissions. Snapshot last pushed Aug 10. |
| [`azizmass/sessionport`](https://github.com/azizmass/sessionport) — MIT, v0.3.6 | Pinned commit `f5b0ffb`; local `npm test` **122/122 passed** and TypeScript build passed under Node 22.23.5. | Direct Claude Code/Codex/OpenCode readers and writers; tests exercise OpenCode v1/v2 database paths and tool/result normalization. | No ChatGPT source, Project/Section, memory, MCP, or schedule model. Claude reader retains `parentUuid` in IR, but the pinned Claude writer serializes a sequential `prevUuid` chain (branch flattening inferred from source). Codex writer emits `approval_policy: auto`; target permission defaults need explicit safety review. No live target CLI resume was tested. |
| [`mgreau/zen`](https://github.com/mgreau/zen) — MIT | Pinned source/docs at `45ce301`; GitHub CI/build/release checks succeeded. Docs pin Claude Code 2.1.200 + Codex CLI 0.142.0; local tests not run because Go is absent. | Strong example of direction-specific adapters: delegates Claude→Codex to Codex's own app-server importer and emits a local Claude session for Codex→Claude. Explicitly enumerates loss and size limits. | Not a ChatGPT/Project/Section or cloud migrator. Codex→Claude drops reasoning, sidechains, images/file-history; maps non-shell tools to text, truncates tool output at 32 KiB and session files at 4 MiB. No live client test in this review. Newer Codex main has suffix-append code, but issue #53403 remains open and its no-op failure path needs a release/client gate. |
| [`Kaseban/baton`](https://github.com/Kaseban/baton) — Apache-2.0 | Pinned commit `0543594`; local `cargo test --all-targets`: **35 passed**, 0 failed; pinned CI succeeded on Windows/Ubuntu/macOS. | Useful compact codec/MCP-server reference with typed parts, source provenance, selected image transfer and native writers for six harness formats. | Canonical Message/Session has no parent/fork/branch/Section graph or token/cost ledger. Codex/Gemini writers downgrade attachments to text placeholders; tests are codec-level, not live CLI resumes or a 9×9 route matrix. Not a Project/Section migrator. |

The original 303-record GitHub API corpus remains a metadata discovery set; the 11 manually surfaced candidates are separate supplements, not evidence of full-market coverage or compatibility.

## Deep-reviewed candidate from the original corpus

- **1naruto-1/agent-connect** — MIT, pinned `42287c14a8fd381bc7ef7a96076a5cba5b4d75f6`; keep as a useful local-session adapter, not a lossless universal migrator. Four adapters are implemented; canonical events omit hierarchy/media/usage/provider config. 122 local tests and typecheck passed. Detailed source-level limits: [`RESEARCH.md`](../RESEARCH.md#deep-review-1naruto-1agent-connect).

- **neosun100/aiw** — MIT, pinned `a9e4221aa39e20aa7c041528805f8a763c035158`; 5-star snapshot, 66 mocked tests passed. Low relevance to migration: manages live tmux workspaces and pane tails rather than transcript trees. Static review flags unauthenticated `0.0.0.0` API and shell interpolation; reject as a migration dependency. Details: [`RESEARCH.md`](../RESEARCH.md#deep-review-neosun100aiw).

- **Fabian-698/dsh-update-guide** — MIT, pinned `0fcb77d2a9abf8c28da32119a243a568bd9c3824` (2026-09-24), one-star snapshot. Useful DSH 0.1.x recovery patterns, but version-limited and not a cross-Harness importer. Bundled self-test passes synthetic gates (one owner-gate skip); targeted synthetic case reproduced that V4-only successor is not guarded by the repair script. Reject as a general Nexus dependency; see [`RESEARCH.md`](../RESEARCH.md#deep-review-fabian-698dsh-update-guide-2026-11-20).

### Chang-Tong/dsh-unified-context — DSH-bound context/session importer

MIT, 22-star snapshot (2026-11-20); package v0.5.0 at pinned commit `108a5f09a151754220f66e5e9a0214f98551d802` (former repository alias `Chang-Tong/dsh-import-agents`). Build and all 74 local tests passed. Its useful scope is five local session sources into DSH plus selected Skills/context/memory/automation migration; it is not a ChatGPT Project/Section or Claude Cloud/API-Key adapter. Our synthetic review reproduced unchecked `../` Skill target planning and an append-failure retry that skips a partially persisted session. Valuable format/architecture reference, unsafe to adopt without those fixes and version-pinned DSH resume gates; details in [`RESEARCH.md`](../RESEARCH.md#deep-review-chang-tongdsh-unified-context-former-dsh-import-agents-2026-11-20).

### License screen — Dicklesworthstone/coding_agent_session_search

High-signal original-corpus row (1,216-star snapshot; repository metadata advertises local indexing/search across 30+ sources), but excluded before dependency/benchmark evaluation: its MIT-titled LICENSE adds an OpenAI/Anthropic rider that denies rights to Restricted Parties and explicitly includes source analysis/indexing/testing in “use.” No implementation or test conclusions are recorded; no tests were run; the disposable clone/index were removed after discovering the rider. Keep it in the original 303 inventory as `license_restricted_excluded`, not among the 11 manual supplements.


### slash9494/ai-config-sync-manager — local config sync only

MIT, npm 0.1.13, pinned 3ac0566032807acabc79405245777edcc780d347 (47-star corpus snapshot). Its local Claude Code↔Codex sync covers instructions, Skills, Agents, MCP, hooks and permissions; plugins are status-only. After rtk npm run build:dist:no-sync, the local suite passed 443/445 with 2 skipped. Useful for config diff/backup/ledger patterns, but not a ChatGPT Project/Section/session migrator or Claude Cloud/API-Key writer. Reject as a core dependency: MCP secret-like environment values pass through by default, manual risk labels are not fully enforced approval gates, and partial apply is not atomic. Source/test details: RESEARCH.md.


### pgrigorr/memory-harness-kit — reviewed memory sidecar

Apache-2.0 in the repository LICENSE/pyproject (GitHub API snapshot says NOASSERTION); pinned commit 3374ead82060868b2398acffb40f945402bb4cac, 2-star snapshot. The 289-test canonical smoke and wheel/sdist proof passed. It provides a file-backed memory/retrieval pipeline and an optional Claude Code transcript hook, but not a ChatGPT/Codex/Cloud session migrator. Synthetic tests confirmed dialogue-only normalized projection, missing Project/Section/branch edges, raw+index secret-shaped marker retention, and a sanitized-ID overwrite collision. Keep as an adjacent architecture reference only; details in RESEARCH.md.


### yeelam-gordon/agent-cli-session-TUI — local catalog/resume, not migration

MIT, v0.3.3, pinned f81a993aa94071fd2150bd9cf4fd6710547b196e, 0-star snapshot. It searches six local CLI histories and resumes through the original CLI/session ID/cwd; there is no cross-provider writer or ChatGPT/Cloud import. Unit tests passed 220 with one ignored live remote test; six lifecycle tests compiled but were not run on real histories. Default grouping sends titles and cwd URIs to a hosted Microsoft endpoint; no transcript/summary/session ID is sent by default, and existing group names are opt-in. Set wordmatch before scanning to stay local. Useful discovery UX reference, not a migration dependency; see RESEARCH.md.

### MethodoxTech/coding-agent-sessions-history-vscode — partial reference
MIT; one-star snapshot; local Claude Code + Codex history viewer, search, date/project-path grouping, Markdown export, and original-CLI resume. README states no telemetry/account connection; source review found no remote history/grouping client. It does not import or restore Projects/sessions, preserve the full parent graph/media, or write to Cloud/API-Key sessions.

### RubenGlez/lokalite — Skill-adapter reference
MIT; 1,162-star inventory snapshot; package 4.3.2. A useful catalog/provenance/CLI path-mapping reference for Agent Skills across Claude, Cursor, Amp, Copilot/VS Code, Codex, Gemini CLI, Goose, OpenCode, Letta, Kilo Code, and project scope. It does not migrate sessions or MCP/plugin/memory/schedule state. Test suite: 225 passed, 3 drift assertions failed.

### erickochen/purple — adjacent MCP pattern
MIT; corpus snapshot 779 stars; purple-ssh 3.34.2. Security-pattern reference: stdio MCP server, 3 read-only allowlisted tools, 2 mutating tools, append-only JSONL audit. Claude Desktop bundle enables read-only; direct CLI does not by default. No harness session/project migration; documented cloud-provider tokens are plaintext. cargo test 7,344 passed / 5 ignored.

### tsonglew/dutis — governed MCP pattern
MIT declared in Cargo/README; no standalone LICENSE file; license metadata remains NOASSERTION. macOS app-handler manager with MCP stdio and one Dutis-only Skill. High-value transaction-security pattern (default-deny writes, approval token + plan digest, safety snapshot, audit, verification), but no Harness/session migration. 147 Rust tests passed; synthetic MCP E2E denied writes safely.

## Browser prompt-handoff candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [`MaazzAlii/context-saver-extension`](https://github.com/MaazzAlii/context-saver-extension) — license unresolved | Pinned commit `2e46bc79b266089a67ccc0c61d32f6cfce5a8f7e`; source-reviewed content capture, session storage, Mistral egress and manifest; 3 JS syntax checks and manifest JSON parse passed. No package/test/build setup. | Low-value example of a manual browser DOM capture + local saved-prompt UI; demonstrates explicit external summarization flow. | Not a native session/project/Section importer or API-Key Cloud writer. 150-step scroll cap can report success without a verified top; flat text loses hierarchy/assets/tool events; Mistral receives captured text; summary is not persisted with saved sessions. No standalone LICENSE; do not adopt as a dependency. Details: [RESEARCH.md](../RESEARCH.md#deep-review-maazzalii-context-saver-extension-2026-11-20). |

## Local provider/archive candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [laohu-aiskills/agent-session-vault](https://github.com/laohu-aiskills/agent-session-vault) — MIT | Pinned 8f46611; inspected 23-file source index, provider registry, backup/restore/migrate writers and the real-home integration script; 22 JS files passed syntax parsing. Synthetic CLI probe reproduced manifest path escape with --apply --yes --verify, including when --target was supplied. Full integration script not run because it indexes the caller's private local session sources. | Strong local adapter registry, raw-file/WAL/SHM backup, SHA-256 manifest, explicit dry-run/approval gates, and count-based loss-report reference. | No ChatGPT Project/Section source, no Cloud/API-Key target, flat normalized session/message model and default text-only migration. Restore lacks path containment: crafted ../ manifest entry wrote outside target in a temp-only test. SQLite db/WAL/SHM are copied separately (concurrent snapshot consistency unproven); --force tool_call/tool_result pair IDs are not preserved. Do not adopt as restore dependency before a fix and adversarial tests. Details: [RESEARCH.md](../RESEARCH.md#deep-review-laohu-aiskillsagent-session-vault-2026-11-20). |

## Direct local session-writer candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [llxgdtop/Agent-Session-Migration](https://github.com/llxgdtop/Agent-Session-Migration) — Apache-2.0 | Pinned 72263bfb; local source review and fixture-based cargo test --workspace: 95 passed / 6 suites. Standard clippy passed with two warnings; strict -D warnings failed on those lints. Two extra synthetic tests in a disposable copy reproduced ZCode multi-database partial commit and main-file-only backup missing a committed WAL row. | Strong deterministic Rust adapter/writer and golden-fixture reference for native Claude Code/Codex/ZCode file/database schemas; additive writes and schema checks. | No ChatGPT/Projects/Sections or cloud/API-Key writer; macOS-only; flat IR and no branch graph; tool/reasoning/assets/usage are dropped or textualized/truncated; model/provider metadata is synthesized. ZCode's two stores are not atomically coordinated, and WAL/SHM backups are absent. Use as a pattern reference only, not as a migration dependency. Details: [RESEARCH.md](../RESEARCH.md#deep-review-llxgdtopagent-session-migration-2026-11-20). |


## Cross-harness memory sidecar candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [YURIBEDRAN/rubi](https://github.com/YURIBEDRAN/rubi) — MIT, v0.6.0 | Pinned main `6780b453a1f8587b42bec318e55b912e13b4ca5e`; source reviewed across the MCP server, memory graph, connector installer, Claude transcript summarizer and tests. `npm test`: 17 passed. Two temporary synthetic runtime probes showed a fake token persisted without redaction and an in-root symlink read a file outside the memory root. | Strong pattern for local Markdown project/personal memory, code maps, hybrid recall and explicit per-harness MCP/hook/instruction tiers. | No ChatGPT Project/Section/session importer or Claude Cloud/API-Key writer; no session/branch/task graph, full transcript or arbitrary Skill/MCP/plugin/scheduler transfer. claude.ai/mobile is experimental/unvalidated. Treat as a memory-plane reference only; do not expose untrusted memory trees before deterministic redaction and realpath containment. Details: [RESEARCH.md](../RESEARCH.md#deep-review-yuribedranrubi-cross-harness-memory-sidecar-2026-11-20). |

## Local cross-agent history search candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [luckeyfaraday/athena-code](https://github.com/luckeyfaraday/athena-code) — MIT, OpenCode fork | Pinned current main 63e5143d; current GitHub page 27 stars / 3 forks, latest visible release v0.5.0 (2026-06-24). Source-reviewed local scanner/index/takeover/schema and tests. Isolated Bun test suite: 98 passed, 1 optional oracle skipped, 0 failed after setting TMPDIR to the physical /private/tmp path. Synthetic fake-token probe persisted the marker to SQLite. | Good reference for local cross-agent session search, FTS attribution, separate memory/recall stores, and resuming the original source through its native CLI. | No executable ChatGPT parser or Claude Cloud/API-Key writer, no Project/Section/branch/subagent structure or assets; only flat text search rows. No session-retention/delete path identified; no redactor; permissionless tool defaults. Treat as local search/resume UX reference, not a migration dependency or canonical archive. Details: [RESEARCH.md](../RESEARCH.md). |

## Cross-platform agent desktop/session manager screened (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [xtermium/xtermium](https://github.com/xtermium/xtermium) — Apache-2.0, Tauri/Rust | Current main pinned f7c55e0; live repository page 16 stars/2 forks, latest visible v0.10.0 release 2026-11-14. Source reviewed for Store/workspaces, AI-history UI/parsers, MCP tools and import/export boundaries. Targeted cargo test required generated RDP sidecar; after scripts/rdp.mjs built it, Claude/Codex history tests passed 2/2 (154 filtered). | Strong desktop UX reference: multi-protocol connections, workspace/folder organization, per-workspace agent prompt, local Claude/Codex/omp history listing and source-native resume. | Not AI transcript migration: no ChatGPT source or Cloud/API-Key writer, no Projects/Sections/branch graph/attachments; history listing is metadata-only and deletion removes source file. MobaXterm/OpenSSH imports cover connection profiles only; MCP is privileged terminal/remote-desktop control. Use only as desktop/session UX reference. Full review: RESEARCH.md. |


## Local cross-harness memory/index candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [leox255/termem](https://github.com/leox255/termem) — MIT declared; v0.6.3 | Pinned main a7901bc3a3fed1bcaac4860002e9b31531a5e594; live page 12 stars / 2 forks. CodeGraph: 554 nodes / 1,387 edges. Isolated cargo test --locked: 56 passed, 0 failed. Checkout has no root LICENSE despite Cargo/README MIT declarations. | Local Claude Code/Codex/Gemini/OpenCode/shell indexing, text search, paginated MCP reads, agent-authored summaries, source-native resume and generated harness wrappers. | No ChatGPT Projects/Sections or Cloud/API-Key writer; no session conversion or hierarchy graph. Text-only pages drop non-text assets, structured tools/results, usage and branch/subagent relationships. SQLite FTS stores sensitive transcript text; no deterministic redaction found. Use only as local memory/search reference; legal provenance needs verification. Details: RESEARCH.md. |


## Native local history import and desktop workspace candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [zavudev/leon](https://github.com/zavudev/leon) — Apache-2.0, v0.16.2 | Pinned main 1fe87724d62a5d29f40982daecd13392a977872b; live page 10 stars / 1 fork; latest release 2026-11-05. CodeGraph: 612 files, 25,143 nodes / 120,582 edges. Focused leon-history suite: 217 passed, 0 failed. | High-value source adapter architecture: machine/project/worktree/session tree, Claude/Codex/OpenCode local history importer, account roots, idempotent fingerprint/cursor import, read-only OpenCode DB, skip/loss diagnostics and token counts by model/day. | Not ChatGPT Projects/Sections or Cloud/API-Key migration; no cross-provider writer. Text-only message IR; images/results dropped, tool calls textified, subagent/fork edges incomplete, OpenCode child sessions omitted, no cost field. Desktop README says Linux/Windows builds not yet tried by a human. Use as importer/UX reference, not canonical archive or dependency. Full review: RESEARCH.md. |


## Cross-harness Skills portability candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [itaywol/adeptability](https://github.com/itaywol/adeptability) — MIT, v1.10.0 | Pinned main c5b1b81b2e0ae71bd8afeeade28eaea6f8fd1bf5; remote main matched. Live page 9 stars / 0 forks. CLI enumerated 56 harness entries (five specialized renderers plus generic per-skill adapters). Full isolated Go suite passed with Go 1.25.14. Synthetic temp-only symlink probe showed project .claude symlink can redirect sync writes outside project. | Strong Skills/subagent schema, renderer, sidecar, drift/hash, reverse-import and safety-scan reference. | Skills/agents only; no session/project/section graph, MCP/plugin migration or Cloud/API-Key transcript writer. Activation/sidecars/model/overrides/size budgets lose target-specific information; loop command only scaffolds cron. Root symlink write escape must be contained before use on untrusted projects. Details: RESEARCH.md. |


## Local session manager and native-history importer candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [AblazeGHR/pan](https://github.com/AblazeGHR/pan) — AGPL-3.0 | Pinned main 74f475250b54959aaab13ffa83be820cada68a32; live page 8 stars / 1 fork. Source-reviewed Session/Workspace model, DSH/Codex/OpenCode/Kimi/CBC readers, import/reimport pipeline, Jobs and MCP setup. 82 targeted import/reimport tests passed; separate native terminal-control tests return 501 on this Darwin host. | Rich local Session/Workspace/manager-child UI, DSH import, per-session MCP, Jobs, usage side data and careful native reimport conflict guards. | Not ChatGPT Projects/Sections or Cloud/API-Key migration; source hierarchy/attachments/auth/MCP/schedules not imported wholesale. Memory/Character paused; API lacks auth by default if PAN_HOST exposes it; AGPL legal gate. Use as architecture/reference only, not migration dependency. Details: RESEARCH.md. |

## Local event-log Harness / project-layout candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [termide/termide](https://github.com/termide/termide) — MIT, v0.50.0 | Pinned main `5c3eec4915380da479c2bb03f6843342e7a9e17d`, 189 stars / 10 forks. Focused tests: 41 session + 41 project + 4 export passed. | Strong local append-only typed session log, project/layout separation, ACP native resume, Skills roots and partial `.mcp.json` support. | Not a ChatGPT importer or Claude Cloud/API-Key writer; no Section Group; Markdown export drops reasoning/tools/results/notices; fork does not record source session ID; schedules are session-bound `/loop`/`/goal`. Use as adapter/reference, not canonical archive/dependency. Details: [RESEARCH.md](../RESEARCH.md). |

## Claude Code session tooling candidate reviewed (license-restricted; 2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [bobmatnyc/claude-mpm](https://github.com/bobmatnyc/claude-mpm) — root Elastic-2.0; npm package metadata conflicts (MIT); release v6.5.83 | Pinned main `25203d34f20982c5871574b5059949ab85ab5a6b`; 158 stars by `gh` / 159 in live page, 33 forks; 4 main commits after release. Isolated session/pause/transcript/export tests: 407 passed, 1 skipped. Synthetic probe: 50th active-session cap evicted oldest without persisting it. | Valuable Claude Code native-JSONL reader, subagent transcript analysis, checkpoint/resume-summary and MCP session-control examples. | Not a ChatGPT/Codex importer or Claude Cloud writer. Pause/metadata/aggregate exports are distinct and lossy relative to native JSONL; images and non-text are omitted, tool result excerpts capped at 500, subagent links heuristic. Optional HTTP MCP can be ngrok-exposed without auth. EL2/metadata conflict blocks source reuse. Details: [RESEARCH.md](../RESEARCH.md). |

## RoleCraft — Skills/MCP resource adapter, not session migration (reviewed 2026-11-20)

`rolecraft-sh/rolecraft` is MIT, v2.6.2, reviewed at `edfd87eed27288fa9e29521eb90e946130075842`. The manifest declares 90 agents (65 verified) and 9 MCP targets. Source review plus 195 focused tests confirms skill copy/symlink, agent-specific paths, lockfile content provenance, profile configuration snapshots, and MCP scanning/gating—but no ChatGPT/Codex session/project hierarchy. Keep as a resource-plane reference only. Important: unscannable MCP content is REVIEW/approval-required in source/tests, despite a stale README line saying SAFE; synthetic profile import/export retained a fake API-key sentinel and dropped project/local overrides. Full findings and caveats are in `docs/RESEARCH.md`.
## Kendex — high-value customization adapter, not cross-harness session migration (2026-11-20)

MIT Rust/Tauri desktop app and CLI; reviewed at main SHA 260b6492363b47d84ba1f893c5223120ad6a9f4a, current tag v1.22.2 (2026-11-18). It maps eight coding harnesses through one per-kind/per-scope capability table and manages agents, skills, hooks, commands, MCP, plugins and Pi extensions. Strong reference for Nexus's resource adapter and source/install provenance.

Pi-only extensions add a native session browser/tree, live/recent event bridge, branch-persisted scheduled prompts, and a Pi ↔ Claude Code session-resume marker. They do not constitute ChatGPT/Codex Project/Section/transcript migration. The Claude bridge requires a logged-in Claude Code account, not the requested API-Key-only Cloud path. Review status: source reviewed; tests not run (Bun unavailable; installed Rust 1.95 < declared 1.96 MSRV). Full evidence is in docs/research/evidence/kendex-review-2026-11-20.txt.
## AgentSkillsManager — skill-directory browser, not conversation or project migration (reviewed 2026-11-20)

lasoons/AgentSkillsManager is a MIT VS Code extension at main commit f603f685e46d53bbf538f0c3014545255ee50e4c (package 0.6.0; last source commit observed 2026-01-17; no GitHub release). It searches local skill repositories and a claude-plugins.dev catalog, then installs SKILL.md packages into the active IDE directory. It has no session/project graph. The cloud ZIP path uses vulnerable adm-zip 0.5.16, buffers without an app-level size cap and deletes the previous target before copying; de-prioritize for Nexus ingestion. See docs/RESEARCH.md and the evidence record.

## Skills compatibility preflight candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [hnaymyh123-henry/skills-compat-manager](https://github.com/hnaymyh123-henry/skills-compat-manager) — MIT, package metadata 0.1.0 Alpha | Pinned clean main/remote HEAD `8be1357e06a350cf13eb670b4d7ff24e4fc54bae`; GitHub page snapshot 84 stars / 0 forks. Isolated Python 3.12 resolution `fastmcp 4.2.3` + `mcp 2.3.0` fails MCP import; 39 non-MCP tests pass, full suite fails collection. Synthetic tests exposed basename collision and shell-chain allowlist bypass (no command executed). | Useful four-dimension `COMPAT.yaml` / MCP preflight concept for the Nexus resource plane. | No project/session/section/attachment/turn/schedule migration. Compatibility is advisory; no API key validity/quota/runtime capability test. SDK import mismatch and weak `shell=True` gate block direct reuse. Details: `docs/RESEARCH.md` and the evidence record. |

## Local knowledge and session-ingestion candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [itlackey/akm](https://github.com/itlackey/akm) — MPL-2.0; latest inspected branch `release/0.11.0` (`0.11.0-beta.0`) | Default `main` `ec8318e`; release branch `fce5837` (Nov 20) includes current 0.10.261130-beta.6 line. 81 focused session-reader/filter/summary/OpenCode-store tests pass. Three latest project extraction tests fail on macOS path aliasing; direct queue-owner probe reproduces. GitHub page snapshot 70 stars / 4 forks. | Strong local-first memory/resource manager and practical Claude Code/Codex/OpenCode reader, pre-filter, session-hash tracking, OS scheduler and app/CLI reference. | Not ChatGPT import or Claude Cloud writer. Session outputs are summary assets pointing at local logs; no parent/SectionGroup/event multimodal/token model. MCP is complementary, not migrated. macOS `/var/folders` → `/private/var/folders` ownership failure in latest branch. Review AKM plugins separately. Evidence: `docs/RESEARCH.md`. |

## Cross-agent skills desktop app reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [beautyfree/skiller](https://github.com/beautyfree/skiller) — SUL-1.0, v0.3.8 | Pinned `019d1ab`; latest release Oct 23; 49 native agent target files. Focused Project/sync/Skills CLI tests: 45 passed, 0 failed. | Polished Electron desktop UI, shared `.agents/skills`, project-scoped Skills, dotagents provenance/sync, Skills CLI lock integration. | SUL limits reuse/distribution; does not migrate session/project conversation hierarchy, MCP config, schedules or Cloud history. `Project.group` groups skill workspaces only. Keep as Skills/UI reference, not migration engine. Evidence: `docs/RESEARCH.md`. |

## Adjacent MCP-backed environment tool reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [jacopobonomi/venv_manager](https://github.com/jacopobonomi/venv_manager) — MIT | Pinned/remote HEAD `fd561c3`; Go 1.24.2; upstream CI #22 passed on Aug 24, 2026. No local tests (Go missing). Source review found MCP `safe` confirmations and an unimplemented MCP sandbox branch. | Useful optional Python environment subresource: registry, project path/tags, package snapshots/diffs/rollback, MCP tool interface. | No session/project/section hierarchy, transcript/attachments, MCP config importer, Cloud/API-Key conversation writer or schedules. `Project` is only a local filesystem path attached to a venv. Keep as a small dependency-resource reference; evidence: `docs/RESEARCH.md`. |

## Kiro-native configuration and chat metadata app reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [kirodotdev-labs/config-control-kiro](https://github.com/kirodotdev-labs/config-control-kiro) — Apache-2.0, v3.0.0 | Pinned/remote HEAD `580d2df`; upstream Build and Test #41 passed; local Go race-test packages passed; frontend 51/51 and build passed; official npm audit found 0 vulnerabilities. | Kiro Global/Workspace config and Memory adapter reference; reads Kiro V3 session metadata, usage/context, subagent parents and tangent/rewind branches. | No transcript/tool/image/attachment payload transfer or cross-harness Project/Section importer. Session reader is metadata-only; Kiro Cloud archive support is unavailable/unverified. Keep as Kiro-specific source-model reference, not migration engine. Evidence: `docs/RESEARCH.md`. |


## Adjacent secret/API-key infrastructure reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [danieljustus/symaira-vault](https://github.com/danieljustus/symaira-vault) — Apache-2.0, latest v0.25.0 (main is newer) | Pinned main HEAD `3ae3791`; 34 stars / 3 forks snapshot; pre-1.0. Full `cargo test --workspace --all-features --locked` passed; fmt + Clippy passed. Latest upstream CI on parent failed because a hosted macOS arm64 runner could not be acquired; HEAD itself is docs-only. | Strong optional credential-security reference: per-agent MCP tools/paths/tokens, encrypted vault, secure API-key resolution without exposing values to child processes, human approval and audited broker. | Password-manager/CXF imports only; not session/context migration. Secret folder paths are not projects. No transcript, Section/Session graph, attachments, or Cloud API-key migration. Windows unsupported. Keep as a separately scoped secret-reference provider, not the Nexus migration engine. Evidence: `docs/RESEARCH.md`. |


## Adjacent brand-asset MCP and reversible import reference reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [pwnera/artbucket](https://github.com/pwnera/artbucket) — AGPL-3.0, v2.8.0 | Pinned main `84e3412` (2026-10-23); 33 stars / 0 forks snapshot; 734 local unit tests pass; typecheck, lint, frozen MCP/API contract all pass. | Strong adjacent design reference: project-bound MCP grants, frozen tool interface, resource hierarchy, preview/review/apply/undo asset import. | DAM Projects/Collections/brand-page sections are not ChatGPT Project/Section/Session; app chat is backed by external `ASSISTANT_URL`, no portable transcript import/export or Cloud writer; own Cloud product has closed; AGPL obligations. Keep as API/migration-UX reference only, not migration engine. Evidence: `docs/research/evidence/artbucket-review-2026-11-20.txt`. |


## Cross-agent Skills package manager reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [yeasy/ask](https://github.com/yeasy/ask) — MIT, main `9878297`, release v1.11.0 | 27 stars / 4 forks; exact-head upstream Linux/macOS test workflow passed; standalone Lint/Format passed; local Go absent. Main CI lint job misconfigures golangci action v6 with v2.1; prior security scan on parent failed on Go stdlib/dependency advisories. | High Skills-plane reference: 19 target directories, project/global scopes, lockfile/source commit, offline/private sources, static scanner, web/desktop app packaging. | No MCP/plugin config, Projects/Sections/Sessions, transcript/attachment/memory/schedule import or Cloud API-key writer. Treat security scan as unresolved pending current-head rerun; not a session converter. Evidence: `docs/research/evidence/yeasy-ask-review-2026-11-20.txt`. |

## Cross-harness asset manager reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [seed-forge/harness-ai-kit](https://github.com/seed-forge/harness-ai-kit) — Apache-2.0, PyPI/GitHub v0.2.0 latest | Pinned main `43d6a65`; 26 stars / 2 forks snapshot; local public-release gate tests 30/30; exact-HEAD CI gate passed; public 0.18.18 upload failed PyPI OIDC validation. Downloaded PyPI wheel SHA verified against official PyPI JSON. | High-value asset-plane pattern: typed manifest/lock, source hashes, staging/sync, runtime materialization across multiple coding harnesses. | No Project/Section/Session/transcript/attachment/token/schedule importer or Cloud Session writer. Main `0.18.18` is ahead of actual published `0.2.0`; do not market unshipped runtime behavior. Generic `.agents` placement is not native host registration. Evidence: `docs/research/evidence/harness-ai-kit-review-2026-11-20.txt`. |

## Adjacent Skills discovery/export UI reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [24KaratAu/openhub](https://github.com/24KaratAu/openhub) — MIT, v0.2.0 | Pinned main `eb8a50b`; 21 stars / 4 forks; upstream CI/release succeeded Sep27. Exact local CI runner re-execution Nov20 fails 1 time-sensitive scorer test; remaining two subprocess test files pass. | Small adjacent Skills catalog/exporter: project/global SKILL.md destinations, installed-skill scanning and backup/rollback on update. | Not session migration: no Project/Section/thread graph, turn/attachment/memory/schedule transfer, MCP config or Cloud API-Key writer. Export is not host validation; same-slug export overwrites, installer shell-composes a catalog slug, test runner deletes HOME cache DB. Keep only as low-cost Skill UX/rollback reference; evidence: `docs/research/evidence/24karatau-openhub-review-2026-11-20.txt`. |

## Windows-local filesystem MCP/Skills candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [xiaode-ai/nanofile-connector](https://github.com/xiaode-ai/nanofile-connector) — MIT, v1.0.9 | Pinned main `26a75c6`; current GitHub API snapshot 22 stars / 1 fork; seven Skills, 27 unique MCP tool declarations; JSON parse and JS syntax checks passed. `npm test` has no script. | Small adjacent example of Skills/MCP/host-specific plugin manifest packaging for a Windows-local file manager. | Not session migration: no ChatGPT/Codex Project/Section/transcript or Claude Desktop/Cloud history writer. Claude plugin path and portable Agent Plugins format require per-host validation; synthetic MCP probe exposed lifecycle/framing concerns. Evidence: `docs/research/evidence/nanofile-connector-review-2026-11-20.txt`. |

## Obsidian Skills-library/export candidate reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [cbruyndoncx/obsidian-skills-manager](https://github.com/cbruyndoncx/obsidian-skills-manager) — license unverified, v0.2.0 | Pinned main `68f74ea`; 19 stars / 3 forks; no test script or CI; scratch production build passed after `npm ci --ignore-scripts`. | Obsidian vault Skill-library UX, per-skill version/provenance state, staged install and rollback. | No session/project/chat migration. Cross-tool export strips metadata and overwrites fixed consolidated Markdown files for Cursor/Copilot/Windsurf/Cline; no native target activation test. Plugin data stores GitHub PAT/registry API keys. No LICENSE; do not adopt as dependency. Evidence: `docs/research/evidence/obsidian-skills-manager-review-2026-11-20.txt`. |

## MCP host configuration/package manager reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [superradcompany/tool-cli](https://github.com/superradcompany/tool-cli) — Apache-2.0, v0.2.0 | Pinned main `bdae5ee`; 18 stars / 2 forks; local `cargo test` 148 passed; fmt check passed; exact-HEAD GitHub Rust Tests run #22245113653 succeeded. Temporary-home `host add claude-code ... --dry-run` preview succeeded without writing config. | High-value adjacent MCPB/tool registry + 11 host-specific MCP config adapters with confirmation, dry-run and backups; encrypted OAuth credential store. | No ChatGPT/Codex Project/Section/session archive, conversation history importer/exporter, Skills/plugin transfer, attachment graph, memory or schedule model. Host add/remove/preview lack direct coverage; MCP tool config is not session restore. Evidence: `docs/research/evidence/tool-cli-review-2026-11-20.txt`. |

## Cross-harness Skills library/synchronizer reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [andrader/jup](https://github.com/andrader/jup) — license unverified/no LICENSE, package/release v0.20.0 | Pinned main `2019ba873fb316d685d09c29bfe30b8c281af8bf`; GitHub snapshot 17 stars / 3 forks, `archived=false`; isolated full suite 95 passed; synthetic local skill add created a symlink and `skills.lock`. | Adjacent Skills resource-plane reference: local/GitHub source provenance, lockfile and link/copy sync into configured local/global harness paths. | No Project/Section/session/transcript/event, attachment, token, MCP/plugin, memory, schedule, ChatGPT reader or Claude Desktop/Code/hosted Cloud session writer. `skills_lock_session` is just a lockfile manager. No license file; sync can remove same-name destination; do not adopt as dependency. Evidence: `docs/research/evidence/jup-review-2026-11-20.txt`. |

## Task orchestration / local session-reference project reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [ktreharrison/tkmd](https://github.com/ktreharrison/tkmd) — MIT OR Apache-2.0, v0.4.0 | Pinned main `14db41f`; 16 stars / 3 forks; local full suite 126 passed, 0 failed, 2 ignored; `cargo check` and fmt passed; strict Clippy fails one current lint. Synthetic probe confirmed task `session_id`/`sessions[]` serialization and native CLI argv dispatch through a stub. | Strong adjacent task/session-reference model: task DAG, local/global scope, per-task agent session IDs, task event stream, local CLI resume mapping, human sign-off and verification receipts. | No Project/Section/Session-content graph, transcript import/export, branch/child conversation links, attachments/tokens, MCP host config importer or Claude Desktop/Code/Cloud session writer. Session IDs only resume via source local CLI; task eval/command fields are executable and must remain inert in migration. Evidence: `docs/research/evidence/tkmd-review-2026-11-20.txt`. |

## Cross-harness agent asset package manager reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [grimoire-rs/grimoire](https://github.com/grimoire-rs/grimoire) — Apache-2.0, latest v0.16.1 | Pinned main `5676c2c`; official v0.16.1 release Nov19; full isolated Rust workspace tests 7,563 passed; fmt/check passed; strict Clippy fails `run_unlinked_image` dead code. Local Skill install + Claude/Codex plugin export succeeded; local MCP source was refused. | High-value asset plane: digest-locked skills/rules/agents/MCP/bundles, host-native renderers, explicit support/degraded/refuse matrix, plugin marketplace export and drift checks. | Not session migration: no ChatGPT/Codex Project/Section/transcript, turns/branches/attachments/tokens, memory/schedules or Claude Desktop/Code API-key Session importer/writer. ChatGPT/Claude Desktop marketplace routes distribute plugins only; Claude Code plugin-account sync does not work with API-key/cloud-provider auth. MCP path import is unsupported; executable commands/hooks need inert preview and approval. Evidence: `docs/research/evidence/grimoire-review-2026-11-20.txt`. |


### Adjacent workflow tool: `yuvalsuede/claudia`

- GPL-3.0 Bun/SQLite task manager with project/sprint/task trees, task dependencies, task-scoped 64KB JSON context, MCP server and one Claude plugin/skill. Task hierarchy ≠ conversation-session hierarchy; generated MCP `session-*` is a per-process task-owner identifier, not provider session content. No session transcript import/export or cross-harness project/section transfer.
- **Verdict:** retain as a workflow-plane reference only; not a direct Nexus migration engine. Package/plugin version drift and no releases noted; local test suite could not run because Bun is absent (no result claimed). Source evidence: `docs/research/evidence/claudia-review-2026-11-20.txt`.


### Adjacent asset tool: `sbroenne/skillpm`

- MIT npm package manager for Agent Skills: lockable npm packages + recursive scanner + `skills@1.7.0` host projection. Useful for the Skill asset plane only; it has no MCP/project/session migration. Local synthetic Codex probe succeeded, but uninstall left a stale `.agents/skills` copy and lock file.
- Local lint/build/tests pass (65); the installed agent CLI is a separate versioned dependency and no session fidelity metric exists. Review full project-config lead APM separately. Evidence: `docs/research/evidence/skillpm-review-2026-11-20.txt`.


### High-value harness architecture reference: `tigu77/tiguclaw`

- Apache-2.0 self-hosted multi-LLM runtime with local thread/transcript store, explicit branch lineage, Claude Agent SDK forks, Projects linked to conversations, memory, schedules, MCP and subagents. The session graph is useful to model, but no external session import/export or ChatGPT Project/Section adapter was found.
- Same-commit official CI passed on Node 22. Local Node 26 regression run had one harness-fixture compatibility failure; details and security boundaries in `docs/research/evidence/tiguclaw-review-2026-11-20.txt`.


### Adjacent security tool: `forest6511/secretctl`

- Apache-2.0 local vault with MCP `secret_run` that injects selected secrets into allowed subprocesses; useful only as a credential-reference/security lead. It does not manage Projects/Sessions/Sections, transcripts, or MCP config migration.
- Screened out of the core migration-engine shortlist; Go was unavailable locally, so no tests claimed. Evidence: `docs/research/evidence/secretctl-review-2026-11-20.txt`.


## Cross-harness asset package manager reviewed (2026-11-20)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [Brattlof/skillet](https://github.com/Brattlof/skillet) — MIT, main `7f3b43c` | Exact-head CI #77 passed; 10 stars / 0 forks snapshot; local Go unavailable so local tests/build not claimed. | Strong narrow asset-plane pattern: explicit host renderers, checksum/commit lock, frozen verification, managed-file prune and config preservation. | No ChatGPT Project/Section/session or Claude Desktop Chat/Cowork/Code history writer, attachments/branches/memory/schedule or Cloud/API-Key Session writer. Claude MCP route writes Claude Code project `.mcp.json`. Keep as design reference, not migration engine. Evidence: `docs/research/evidence/skillet-review-2026-11-20.txt`. |


## Adjacent project/task workflow and MCP candidate reviewed (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [harperreed/toki](https://github.com/harperreed/toki) — README claims MIT; license unverified | Main `c79f094`; 10 stars / 2 forks snapshot; exact-main CI #75 reports Success; local Go unavailable, no local tests claimed. | Small task Project/Todo schema, path-aware work context, MCP task CRUD/resources/prompts, SQLite/Markdown storage. | Not a session migrator: YAML-only import, no Section/session/transcript/attachment/branch/token/memory/schedule graph. Partial import can return success after errors; migration non-transactional; SQLite backup/WAL fidelity unverified. No LICENSE file despite README claim. Exclude from core engine. Evidence: `docs/research/evidence/toki-review-2026-11-21.txt`. |


## High-value harness/session-telemetry reference reviewed (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [greenfield-inc/agent-farm](https://github.com/greenfield-inc/agent-farm) — license unverified, npm 0.2.38 | Main `77bc1fa`; 8 stars / 0 forks snapshot; exact CI #330 passed; local typecheck and 361 tests passed, 9 skipped; synthetic local gateway smoke passed on Claude Code + Codex CLIs. | High-value design: profiles/workspaces/skills/MCP projection, provider gateway with secret env references, per-run OTel session metadata, parent/child and launch IDs, conversation normalization. | No ChatGPT Project/Section or Desktop/Cloud session importer/writer. Export explicitly omits traces, so the evidence bundle is not replayable. Sessions are only native CLI runs; launches bypass approvals and are not filesystem-sandboxed. No LICENSE/package license field. Keep as reference, not core importer. Evidence: `docs/research/evidence/agent-farm-review-2026-11-21.txt`. |


## High-value harness/session-telemetry reference reviewed (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [greenfield-inc/agent-farm](https://github.com/greenfield-inc/agent-farm) — license unverified, npm 0.2.38 | Main `77bc1fa`; 8 stars / 0 forks snapshot; exact CI #330 passed; local typecheck and 361 tests passed, 9 skipped; synthetic local gateway smoke passed on Claude Code + Codex CLIs. | High-value design: profiles/workspaces/skills/MCP projection, provider gateway with secret env references, per-run OTel session metadata, parent/child and launch IDs, conversation normalization. | No ChatGPT Project/Section or Desktop/Cloud session importer/writer. Export explicitly omits traces, so the evidence bundle is not replayable. Sessions are only native CLI runs; launches bypass approvals and are not filesystem-sandboxed. No LICENSE/package license field. Keep as reference, not core importer. Evidence: `docs/research/evidence/agent-farm-review-2026-11-21.txt`. |


## Incremental review checkpoint (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / status |
|---|---|---|---|
| [`inventlist/localvault`](https://github.com/inventlist/localvault) — license conflict (Apache-2.0 source vs MIT gemspec/RubyGems) | Exact-main commit `9a9750b`; code review of vault crypto, sync payload, stdio MCP tools, key cache, Claude Code hook; upstream CI #72 passed; local suite not run (Ruby/Bundler too old). | Adjacent security reference: secret-plane separation, explicit reveal gate, process-scoped env injection. | Secret vault only; no Projects/Sections, conversation graph, desktop modes, transcript importer, skills/plugin/scheduled-task migration. Do not adopt as dependency until license is clarified. See [`RESEARCH.md`](../RESEARCH.md) and evidence report. |

Candidate progress is now **55/303 reviewed, 248 unreviewed**; next: `opencue/cuecards`. This is triage progress, not a completeness claim or compatibility guarantee.


## Incremental review checkpoint — Herdr Agent Config Manager (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / status |
|---|---|---|---|
| [`Phoobobo/herdr-agent-config-manager`](https://github.com/Phoobobo/herdr-agent-config-manager) — MIT, low adoption | Pinned master `bac8484`; 25 Python tests pass; synthetic inventory and dry-run/apply link test; synthetic secret-canary and divergent-copy probes. | Narrow canonical Skills store/symlink manager; inventory model for 11 known agent directories. | MCP/plugin/hook inventory only; no ChatGPT Projects/Sections or session migration. JSON inventory leaks MCP arg/URL/hook canaries to agent context; TUI can delete divergent real copy. No upstream test CI/release. Retain only as adjacent reference with safeguards. |

Candidate progress is **57/303 reviewed, 246 unreviewed**; next: `smartsheet/cli-agent-power-tools`.


## Adjacent agent-resource reference — Smartsheet CLI Agent Power Tools (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [`smartsheet/cli-agent-power-tools`](https://github.com/smartsheet/cli-agent-power-tools) — MIT; pinned main `7e41cca` | Six paired Claude Code/Gemini CLI Markdown agents; source/docs/scripts reviewed; isolated fake-CLI setup probes; no source tests/workflow or real API calls. | Narrow host-specific agent manifest/tool allowlists, structured handoffs and explicit write-preview patterns; useful adapter test fixture. | Not a Project/session migrator. No ChatGPT Project/Section/turn/attachment/session graph or Desktop Chat/Cowork/hosted Cloud writer. Gemini prompt variant conflicts on approval in automated chains; setup scripts remove prior MCP before validating PAT and place PAT in process argv. Retain only as a cautious resource-adapter reference. [Evidence](research/evidence/cli-agent-power-tools-review-2026-11-21.txt). |

Inventory progress: **58/303 reviewed, 245 unreviewed**; next: `RubenGlez/lokalite`. Progress is candidate triage, not completeness or compatibility proof.


## Adjacent credential plane — Lokalite (`RubenGlez/lokalite`), 2026-11-21

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [`RubenGlez/lokalite`](https://github.com/RubenGlez/lokalite) — MIT, macOS 14+; pinned main `1fa2543`, latest release v2.9.0 | CodeGraph: 103 files; local `swift build` exit 0; full `swift test` 180/180 pass; synthetic malformed-config writer probe. Upstream CI #340 passed on v2.9.0 app commit. | Strong credential plane: AES-GCM + Keychain, env/project secret refs, local MCP handoff, approval tiers and access logging. | Not a Session/Project/Section migrator or model-provider gateway; client writer supports Claude Code/Desktop, Cursor, Windsurf only; macOS-only. Config parse failure can overwrite malformed client config; default “read-only” MCP still changes active environment; `block` relies on best-effort process detection. Retain as credential-reference/security design reference only. [Evidence](research/evidence/lokalite-review-2026-11-21.txt). |

Inventory progress: **59/303 reviewed, 244 unreviewed**; next: `bunhine0452/Ocul-PM`. Candidate triage is not a completeness or compatibility claim.

### Adjacent local project journal — `bunhine0452/Ocul-PM` (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [`bunhine0452/Ocul-PM`](https://github.com/bunhine0452/Ocul-PM) — MIT, v4.11.2, pinned `9dd0f85ad64c3e5b9b75c29fbe5e8141aa66cc34` | CodeGraph + source review; local macOS suites: 1,975 frontend tests and 1,234 Rust tests passed; typecheck/build/lint/fmt/clippy passed. Synthetic hook-input canaries persisted as raw plaintext in `.oculpm/hooks/claude-events.jsonl` (0644 under umask 022). Upstream Portability #305 failed two Windows spawn-budget tests; CI/E2E/Release succeeded. | Useful project-journal/planner and agent file-activity observation reference; distinguishes task/work activity from per-agent session IDs. | Not ChatGPT Project/Section/session import or Claude Desktop Chat/Cowork/Code restore; no production caller for `SessionId::imported()`. Raw hook inbox retains full prompt/assistant fields until consumption/1MiB compaction and has no time TTL. Keep as adjacent memory/observer reference only; see [full source/test review](research/evidence/ocul-pm-review-2026-11-21.txt). |

Inventory progress: **60/303 reviewed, 243 unreviewed**; next: `compilando/norte`. Candidate triage is not a completeness or compatibility claim.

### Norte (`compilando/norte`) — governed file operations, not agent-session migration (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [`compilando/norte`](https://github.com/compilando/norte) — multi-license, v0.3.0-alpha.16, pinned `52256ccb816999705fb681a5336d39839497d099` | CodeGraph 957 files / 31,214 nodes / 154,718 edges; CodeGraph status current; focused local tests/doctests and portability failure ledger in full report. Latest scheduled remote integration #62 passed on this commit; CI/GUI/Release workflows are disabled. | Useful reference for default-deny policy, MCP scopes, human approval, LIFO undo, hash-chained file-operation audit, and distinct UI-state vs agent-actor IDs. | No ChatGPT export, Project/Section membership, transcript/turn importer, branch/subagent graph, attachment/token ledger or cross-Harness writer. Built-in AI chat is in-memory and capped; “MCP session” labels journal actor identity, not conversation history. macOS workspace build failed and 3 focused host-specific tests failed. Core/AI/MCP are AGPL-only. Adjacent safety/audit reference only. [Evidence](research/evidence/compilando-norte-review-2026-11-21.txt). |

Inventory progress: **61/303 reviewed, 242 unreviewed**; next: `hyper-swe/mtix`. Candidate triage is not a completeness or compatibility claim.


### hyper-swe/mtix — hierarchical task context and MCP, not provider transcript migration (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [hyper-swe/mtix](https://github.com/hyper-swe/mtix) — Apache-2.0, main pinned 12c6a41582f3639f0438f92bf74ba0749429dfeb, v0.5.4-beta latest release | CodeGraph 3,297 files / 51,586 nodes / 182,572 edges; local selected service/MCP/SQLite tests passed after release-tag setup; current CI #1356 success on pinned head. | Excellent adjacent reference for parent-derived task briefings, hierarchical work items, MCP task tools, board export/import, task history and explicit agent lifecycle metadata. | Session records are agent-run metadata and task counts, not chat turns; no SectionGroup or native provider transcript/media/fork/import/writer. Claude setup is integration/config, not Chat/Cowork/Code session transfer. Adjacent task-memory layer only. [Evidence](research/evidence/hyper-swe-mtix-review-2026-11-21.txt). |

Inventory progress: **62/303 reviewed, 241 unreviewed**; next: JoeyWangTW/todo-cli. Candidate triage is not a completeness or compatibility claim.


### JoeyWangTW/todo-cli — Gemini CLI tmux todo app, not a session migrator (2026-11-21)

| Candidate | Evidence collected | Preliminary value | Gaps / disposition |
|---|---|---|---|
| [JoeyWangTW/todo-cli](https://github.com/JoeyWangTW/todo-cli) — MIT, main pinned 22caf3182d01d321264f1ee189e8ce457b25c190, 9 commits | CodeGraph 7 files / 66 nodes / 149 edges; 7/7 JS syntax checks and synthetic task/storage round-trip passed. | Demonstrates a task-to-live-process relationship and highlights the distinction between a tmux handle and the Gemini CLI's own project-scoped resumable conversation. | Flat task array; task JSON has no native Gemini session ID or transcript; preview is ephemeral; no export/import or other harness backend. YOLO is high risk with user-privileged MCP; no test/build/release gate found. Pass as migration engine; adjacent comparison only. [Evidence](research/evidence/todo-cli-review-2026-11-21.txt). |

Inventory progress: **66/303 reviewed, 237 unreviewed; next: evoerax/awesome-harness-engineering**. Candidate triage is not a completeness or compatibility claim.


## ivanopcode/cocoaskills — adjacent skills/MCP installation reference (reviewed 2026-11-21)

Pinned main 4dc5b0864f806872ad4791a5de65bdb2b5613a81, Apache-2.0. Useful for reproducible Skillfile/lock dependency pins, adapters, managed-file ownership, MCP drift protection, consent, and transactional writes. Skills target Claude Code/Codex CLI/Cursor/Gemini/OpenCode/Windsurf; project MCP config targets only Claude Code/Codex CLI/Cursor. Not a ChatGPT Projects/Sections or Claude Desktop Chat/Cowork/Code session migrator. Same-commit upstream CI is red; 1,311 focused tests, 28 corrected conformance tests, and 73 CLI-golden tests passed locally, but the full suite was not completed. See docs/research/evidence/cocoaskills-review-2026-11-21.txt.


## Pandusss/conus — agent task/session activity ledger (reviewed 2026-11-21)

Pinned main 83ab2b7994818c06386549ee456809023265a583, MIT. Conus has real Session rows keyed by provider agent_session_id, task parent/child relations, task/session event history, commit links, and bounded prompt/answer excerpts. It is useful for the task/session attribution and audit-ledger layer, but not a cross-Harness conversation importer: no full transcript, media, token/cost data, fork/session tree, ChatGPT Projects/Sections, or Claude Desktop Chat/Cowork adapter. Hooks are stronger for Claude Code/Codex; Gemini is MCP-board-only. Upstream CI passed the exact source commit. Local typecheck/build/generated checks and 357 CLI/protocol + 150 UI tests passed; database-backed tests could not be reproduced locally because no Docker/Postgres daemon was reachable. See docs/research/evidence/pandusss-conus-review-2026-11-21.txt.


## CDataSoftware/google-ad-manager-mcp-server-by-cdata — deprecated connector example (reviewed 2026-11-21)

Pinned final source 31676a0aa80f4221656fe6ca445669cad1caf627, MIT; owner archived the repo on 2026-11-17. It is a provider-specific local stdio MCP server over a separately licensed CData JDBC driver. It registers metadata and SQL query tools, not CRUD or session migration. README documents a Claude Desktop MCP config only, and contradicts its own read-only notice later by claiming write/update/delete. Maven tests (11) and packaging passed locally, but they do not exercise the proprietary driver/provider connection. Exclude from the migration engine; retain only as a Claude Desktop MCP setup example. See docs/research/evidence/cdatasoftware-google-ad-manager-mcp-review-2026-11-21.txt.

Inventory progress: **67/303 reviewed, 236 unreviewed**; next: `sboorlagadda/artmark`. Candidate triage is not a completeness or compatibility claim.

## Screened and not shortlisted: evoerax/awesome-harness-engineering (2026-11-21)

Static Markdown “awesome” index only; no implementation, tests or CI. Several harness rows are already false against current vendor docs (Codex hooks; OpenClaw hooks/MCP; Gemini hooks/MCP), prompt/benchmark data are unpinned/unreproducible, and README's MIT claim lacks a tracked LICENSE. Do not adopt or use as compatibility evidence. It may be used only as a lead list after independent review. [Evidence](evidence/evoerax-awesome-harness-engineering-review-2026-11-21.txt).

Inventory progress: **67/303 reviewed, 236 unreviewed**; next: `sboorlagadda/artmark`. Candidate triage is not a completeness or compatibility claim.

## sboorlagadda/artmark — adjacent memory reference, not migration engine (2026-11-21)

Apache-2.0, v0.2.3, pinned `231313e914be18a17c3bb4a028fe6bd9698acf66`. Keep the canonical artifact pointer + source/catalog provenance + lexical retrieval pattern as an optional memory-plane reference. Exclude from the conversation importer shortlist: no Sessions, message/branch tree, ChatGPT Projects/Sections, external history writer, Claude Desktop mode adapters, attachments, token data, schedules, or shipped MCP. The Skill is a host instruction, not migrated memory. Tests/build pass locally; two recent scheduled upstream `cargo audit` runs failed but public logs did not reveal why. [Evidence](evidence/artmark-review-2026-11-21.txt).

Inventory progress: **68/303 reviewed, 235 unreviewed**; next: `t59688/skillpack-manager`. Candidate triage is not a completeness or compatibility claim.

## t59688/skillpack-manager — Skills asset manager, security blocker (2026-11-21)

MIT Skill-packaging and install/sync manager for 13 global skill folders; not a chat/session/project/memory/MCP/plugin migrator. Local 37 tests/build pass, but source inspection plus two isolated CLI probes confirm malicious `name`/`path` can write outside the target or copy files outside the pack. `audit` missed these probes. Do not adopt/use against user data until upstream or Nexus adds path containment, atomic replacement, and adversarial tests. Keep only as an adjacent resource-plane pattern. [Evidence](evidence/skillpack-manager-review-2026-11-21.txt).

Inventory progress: **69/303 reviewed, 234 unreviewed**; next: `travelhawk/agentpm`. Candidate triage is not a completeness or compatibility claim.


## Screened but not shortlisted — `walidboulanouar/ay-claude-templates` (2026-11-21)

Published npm 1.0.0 tarball inspection confirmed the same path-boundary and hook-validation findings; package lifecycle scripts were not run.

Claude Code-only package marketplace, no conversation/session importer or Claude Desktop modes; fixed config root; isolated source POCs demonstrate slug traversal, Windows backslash ZIP escape projection, and a blocked built-in hook template. No tests/CI evidence. Exclude from adoption/migration engine; see `evidence/ay-claude-templates-review-2026-11-21.txt`.

Inventory progress: **71/303 reviewed, 232 unreviewed**; next: `zavora-ai/macos-zlaunch-manager`. Candidate triage is not a completeness or compatibility claim.


## Screened false positive — `zavora-ai/macos-zlaunch-manager` (2026-11-21)

A macOS launchd GUI/CLI plus local MCP for 19 service-control tools, not a Harness/session migrator. No conversation/session import model; current Desktop Extension `.mcpb` package absent. Sandboxed source POC confirms MCP `launchd_create` label traversal writes outside its intended LaunchAgents root; mutating tools must not be auto-approved. Exclude from engine. [Evidence](evidence/macos-zlaunch-manager-review-2026-11-21.txt).

Inventory: **72/303 reviewed, 231 unreviewed**; next `ai-agent-manager/agent-manager`.


## High-value adjacent reference — `ai-agent-manager/agent-manager` (reviewed 2026-11-21)

Shortlist for Skills/resource distribution only: versioned discovery bundles, per-source provenance/cache, repo/system scopes, six provisioners and strong exact-SHA cross-platform CI. It is **not** a conversation/session migration engine: `Session` is local bundle/auth/membership UI state; `Project` is Atlassian API metadata; no ChatGPT/Codex project, Section, transcript, memory, schedule, MCP config, or Desktop-mode adapter. npm `latest` tag lags 1.24.0 at 1.23.1. [Evidence](evidence/agent-manager-review-2026-11-21.txt).

Inventory: **73/303 reviewed, 230 unreviewed**; next `omarmfouad25/google-marketing-agent`.


## Screened — MCP safety reference only, not a session migrator: `omarmfouad25/google-marketing-agent` (2026-11-21)

Google Ads/GA4/GSC/GTM local MCP + 14 domain Skills. Main v0.3 boolean `confirm: true` directly applies when writes are enabled; unmerged PR #1 improves this with preview-ID binding and rollback but remains unreleased. Official npm audit flags production and dev vulnerabilities. No conversation/session/project-section import/export. Keep only as a safety-pattern example; exclude from migration-engine shortlist. [Evidence](evidence/google-marketing-agent-review-2026-11-21.txt).

Inventory: **74/303 reviewed, 229 unreviewed**; next `SoonIter/skills-package-manager`.


## Screened, not shortlisted — `SoonIter/skills-package-manager` (2026-11-21)

Local pinned source review: useful only for pinned SKILL.md source records and 45 Harness-specific skill directory links. It does not migrate Projects/Sections/Sessions, transcripts/branches/attachments, MCP/plugin declarations, memory, schedules, or Claude Desktop's three modes. Main v0.11.0; 134/134 tests plus direct core/plugin builds pass; pnpm install is blocked by unapproved dependency build scripts. Two relevant PRs remain open. Exclude as a session-migration engine; retain only as an adjacent Skill resource-plane example. [Evidence](evidence/skills-package-manager-review-2026-11-21.txt).

Inventory: **75/303 reviewed, 228 unreviewed**; next `AI-Colleagues/skill-mgr`. Candidate triage is not a completeness or compatibility claim.


## Screened, not shortlisted — `AI-Colleagues/skill-mgr` (2026-11-21)

Well-structured five-target AgentSkills (`SKILL.md`) CLI/library with 135/135 tests, 100% measured local statement/branch coverage, clean lint/typecheck, successful exact-source PyPI provenance and a successful release CI run. It is **not** a session/project migrator: no ChatGPT/Codex hierarchy, conversation history, MCP/plugins, memory, attachments, schedules or Desktop mode adapters. Two disposable local-source POCs show symlink dereference into the installed Skill and destructive replacement of a same-name unmanaged destination. GitHub refs are moving default-branch downloads; license is unspecified in the inspected tree. Keep only as an architecture reference after fixing containment/ownership/revision issues. [Evidence](evidence/skill-mgr-review-2026-11-21.txt).

Inventory: **76/303 reviewed, 227 unreviewed**; next `bl1nk-bot/skills-cli`. Candidate triage is not a completeness or compatibility claim.


## Screened out — `bl1nk-bot/skills-cli` (2026-11-21)

README-level project/global Skill overlay only; no ChatGPT Project/Section/Session tree, transcript import/export, branches, attachments, MCP/plugins, memory, scheduling, or Claude Desktop Chat/Cowork/Code / local Claude Code adapter. Main fails the local Rust test build; its separate registry check also fails, and its open `zip` upgrade is not merged. Static path containment risks are recorded, not reproduced. Do not shortlist as a migration engine; retain only a weak ResourcePlane concept if useful after redesign. [Evidence](evidence/skills-cli-review-2026-11-21.txt).

Inventory: **77/303 reviewed, 226 unreviewed**; next `CassianFlorin/skill-hub`. Candidate screening is incremental, not a completeness or compatibility claim.


## Keep as adjacent architecture reference — `CassianFlorin/skill-hub` (2026-11-21)

High-quality, released Skills package manager with a native SwiftUI macOS GUI, JSON CLI boundary, source/commit/checksum lock, runtime deploy matrix, update preview, holds, rollback history and audit. The exact-head GitHub CI passed Ubuntu/macOS/Windows; local Go was unavailable and npm wrapper tests were 3/3. This is **not** a session migrator: no ChatGPT Project/Section/Session tree, transcript/branch/media/token, MCP/plugin, memory, schedules, or Claude Desktop three-mode/3P gateway adapter. Keep for ResourcePlane design only; adopt no installer code unchanged before explicit symlink and transaction-safety review. [Evidence](evidence/skill-hub-review-2026-11-21.txt).

Inventory: **78/303 reviewed, 225 unreviewed**; next `Heretyc/subagent-mcp`. Candidate triage is incremental, not a completeness claim.


## Keep as adjacent control-plane reference — `Heretyc/subagent-mcp` (2026-11-21)

Sub-agent MCP server with local Claude/Codex drivers, gated permissions, provider routing, bounded handoff notes and latest context/token samples. Its strong orchestration lifecycle is relevant to a future `OrchestrationPlane`, but the process-local `AgentState`, depth/prompt markers and short handoff records are not an importable session graph. It can register as MCP-only in Claude Desktop, and its optional direct API adapter calls gateway-compatible endpoints for its own tasks; neither restores Claude Desktop or ChatGPT sessions. Local build passes; local tests are 147/150 with three reproduced failures. Keep as architecture reference only; exclude as migration engine. [Evidence](evidence/subagent-mcp-review-2026-11-21.txt).

Inventory: **79/303 reviewed, 224 unreviewed**; next `hiadamhere/spm`. Candidate screening is incremental, not exhaustive.


## Screened out as migration engine — `hiadamhere/spm` (2026-11-21)

Skills catalog/deployer only. Public repo has docs/catalog/skill, not implementation/tests; NuGet 0.4.0 PDB links to unavailable private source. Decompilation shows Skill folder deployment, single record per Skill name, and a potential overwrite of existing real target directories (static finding, not reproduced). No ChatGPT Projects/Sections/Sessions, transcript/branch/media/token, MCP/plugin conversion, memory/schedules or Claude Desktop mode/gateway session import. Keep only as a weak ResourcePlane/path inventory lead; do not use the installer. [Evidence](evidence/hiadamhere-spm-review-2026-11-21.txt).

Inventory: **80/303 reviewed, 223 unreviewed**; next `keynv-labs/keynv`. Screening is incremental, not a completeness or compatibility claim.

## Screened out as migration engine — keynv-labs/keynv (2026-11-21)

Useful only as an adjacent secret-redaction/privacy-plane reference. It scans supported Claude Code JSONL and Cursor text surfaces; no ChatGPT/Codex Project, Section, conversation Session, branch, attachment, MCP/plugin, memory, schedule or Claude Desktop Chat/Cowork/Code importer/writer exists. The watcher can overwrite an active append-only file using read-redact-temp-rename; source warns appends between read and rename can be lost. Do not use on source transcripts pending a concurrency-safe design. Local tests/build and the audit/lint findings are recorded in [evidence](evidence/keynv-labs-keynv-review-2026-11-21.txt). Inventory: 81/303 reviewed, 222 pending; next KRISH-exe-29/ai-agent-skill-router.

## Retain only as adjacent ResourcePlane reference — KRISH-exe-29/ai-agent-skill-router (2026-11-21)

The Apache-2.0 project offers a model-driven Skill router, multi-harness SKILL.md paths, scoped MCP-name inventory, opt-in Claude Code tool-usage counts and a user-approved, revalidated trash/undo path. It does not migrate Projects, Section Groups, sessions, messages, attachments, memory, schedules, MCP definitions or Claude Desktop Chat/Cowork/Code. A disposable macOS install also found a silent exit-0 when the scanner is launched through the .claude skill symlink; canonical path passes. Retain only as a medium-value resource/approval UX reference, not a conversion engine. [Evidence](evidence/ai-agent-skill-router-review-2026-11-21.txt).

## Keep only as adjacent TaskGraph reference — nemesiscodex/pulse-tm (2026-11-21)

Useful for durable local task context across work sessions: tags-as-epics, task/subtask status, order, timestamps, YAML and a five-tool MCP wrapper. Not a conversation/session importer, not Project/Section hierarchy, and not Claude Desktop Chat/Cowork/Code compatibility. No releases or CI runs; local 21-test suite passes but the current OpenTUI dependency resolution fails TypeScript lint. Synthetic parse-error test demonstrates malformed YAML can be replaced on the next add. Keep only as a TaskGraph design lead; do not copy its storage as a migration archive. [Evidence](evidence/pulse-tm-review-2026-11-21.txt).

## Narrow ResourcePlane reference only — rtaparay/Open-Skills-Manager (2026-11-21)

A VS Code-fork extension for browsing Skill repos/local folders and installing SKILL.md into active IDE skill directories. No session/project/section import or Claude Desktop Chat/Cowork/Code support. Build/typecheck passed in a disposable copy, but no tests/CI are present; installation path can recursively remove an existing target and remote skill names are not path-contained. npm audit identifies a high adm-zip dependency finding on ZIP import. Do not use as a Nexus migration engine or installer without transaction/containment fixes. [Evidence](evidence/open-skills-manager-review-2026-11-21.txt).


## Screened, not shortlisted — Spaztazim/lucid-context-engine (2026-11-21)

A small OpenClaw-only QMD retrieval/context-injection plugin. Its ingest method stores nothing and it has no source/target migration adapters, canonical archive, project/session hierarchy, or Claude Desktop/API-key destination. A synthetic retrieval probe passed, but no tests, CI, releases, lockfile, or reproducible build were present. Keep only as an optional retrieval-plane example, not a Nexus Memory dependency. Full evidence: [lucid-context-engine-review-2026-11-21.txt](research/evidence/lucid-context-engine-review-2026-11-21.txt).


## Historical ResourcePlane reference only — stefafafan/skm (2026-11-21)

An MIT Skill manifest/lock/cache CLI with 131 passing tests and successful exact-head CI; valuable for requested source vs resolved commit/integrity separation. Not a session migrator; archived and explicitly deprecated. A temporary fixture reproduced an output-directory symlink escape that deletes unmanaged sibling content, and production audit finds vulnerable ws 8.19.0 through Ink. Do not adopt or install as the Nexus dependency. Full evidence: [stefafafan-skm-review-2026-11-21.txt](research/evidence/stefafafan-skm-review-2026-11-21.txt).


## Multi-resource plane reference only — asm-cli/asm-cli (2026-11-21)

The Go CLI centrally stores Skills, MCP configs/binaries and selected Plugins, then projects them into Claude/Codex/Cursor/Gemini environments. Exact release binary builds for Linux amd64, macOS arm64 and Windows amd64; local tests/vet/build pass. Not a transcript/session migrator. GitHub license metadata is null and no LICENSE exists; two exact-release temporary probes confirmed store-ID traversal and MCP binary deletion outside the configured agent root. Design inspiration only; no code reuse. Full evidence: [asm-cli-asm-cli-review-2026-11-21.txt](research/evidence/asm-cli-asm-cli-review-2026-11-21.txt).


## Screened — b2amedina/omaset (2026-11-21)

MIT Omarchy-only local settings UI/CLI/MCP, not conversation, Project/Section, Session or Cloud gateway migration. Shared typed control surfaces and atomic field writes/undo are adjacent patterns only. Temporary macOS test-copy result: 23/29 passed, six platform/fixture failures; no cross-Harness test. Claude Desktop Chat, Cowork and Code are all unsupported. [Detailed evidence](evidence/omaset-review-2026-11-21.txt).

Corpus status: **88/303 reviewed, 215 pending**; next: `dougrn/MCP-MegaBrain`. Research remains incomplete.


## Adjacent MemoryPlane only — dougrn/MCP-MegaBrain (2026-11-21)

MIT local SQLite/FTS5 memory MCP with rules/spec directives/experiences/patterns, a working stdio interface and 17 passing locked tests. It does not import sessions, Projects, Sections, transcripts, branches, attachments, schedules, or Claude Desktop modes. A synthetic in-memory POC reproduced all four record types crossing between unrelated projects sharing a basename; a temporary mode probe observed 0644 DB / 0755 directory. Keep only as a record/query design lead, not a Nexus session migrator; fix identity scoping and private storage first. [Detailed evidence](evidence/dougrn-mcp-megabrain-review-2026-11-21.txt).

Corpus status: **89/303 reviewed, 214 pending**; next `eddieran/skillpm`. Research remains incomplete.

 
## High-value Skills ResourcePlane reference only — eddieran/skillpm (2026-11-21)

Apache-2.0; exact HEAD 26fb1c6. Strong local CLI design for Agent Skills manifests/locks, dependency resolution, support-status labels, scanners, sync and file injection. It does not carry Projects, Sections, sessions, attachments, MCP/plugins, memory or schedules, and does not implement Claude Desktop modes or Cloud/API-key session writers. CI and nightly E2E pass, but security workflow fails at govulncheck; local probes reproduce a predictable-temp symlink file write, source symlink read outside the checkout, ancillary prompt-injection scan gap, basename overwrite, crafted adapter path escape and partial rollback corruption. Keep the design patterns, not implementation. [Detailed review](evidence/eddieran-skillpm-review-2026-11-21.txt).

Corpus status: **90/303 reviewed, 213 pending**; next Elixion-ai/claudepass. Research remains incomplete.


## Adjacent SecretPlane/security reference only — Elixion-ai/claudepass (2026-11-21)

MIT, exact HEAD a18b332. Small adoption snapshot (2 stars, 1 fork), but unusually explicit security/operational docs and local race/CI coverage. Useful for secret handles, encrypted local storage, project/global refs and redaction threat modelling. Not a Harness migrator: no Projects/Sections/session export, no Desktop account installer, no gateway relay, and no per-session secret ACL. Local Claude Code 2.1.76 validation exposed a version-specific manifest/`--strict` compatibility issue; current official docs now support those fields. [Evidence](evidence/claudepass-review-2026-11-21.txt).

Corpus status: **91/303 reviewed, 212 pending**; next `higherorderfunctor/nix-agentic-tools`. Research remains incomplete.


## High-value declarative config + Kiro session research reference — higherorderfunctor/nix-agentic-tools (2026-11-21)

Unlicense; exact HEAD b68c1e9; 2 stars/0 forks. Nix monorepo for Home Manager/devenv and selected Claude Code/Codex/Kiro/Copilot resources. Strong type-checked resource placements, gateway/inference config and broad exact-HEAD CI. Not a ChatGPT/Codex Project or session mover. Its Kiro v3 schema notes are unusually valuable, but explicitly pinned to an older KAS 2.15.1/2.15.2 build; the repo now packages Kiro CLI 3.5.0. Current official Kiro docs expose local ZIP/script session transfer but separate cloud sessions, so treat old filesystem schema as historical until re-probed. [Evidence](evidence/higherorderfunctor-nix-agentic-tools-review-2026-11-21.txt).

Corpus status: **92/303 reviewed, 211 pending**; next `interrupted-sh/murk`. Research remains incomplete.


## Adjacent SecretPlane reference only — interrupted-sh/murk (2026-11-21)

Dual MIT/Apache, v0.15.2, exact HEAD 8e88470. Strong encrypted Git vault, recipient/group/private scopes, temporary agent grants, tag policy and MCP/editor wiring; full workspace tests and multi-platform CI pass. It does not transfer ChatGPT/Codex Projects, Section Groups, sessions, attachments or schedules. Its agent controls are explicitly experimental guardrails, not isolation: same-user access can bypass them and `murk_get` places values in model context. Keep its secret-reference patterns, not its session story. [Evidence](evidence/interrupted-sh-murk-review-2026-11-21.txt).

Corpus status: **93/303 reviewed, 210 pending**; next `jnMetaCode/skillet`. Research remains incomplete.


## Skills AssetPlane reference only — jnMetaCode/skillet (2026-11-21)

MIT, v0.1.2, exact main HEAD `b972e3dc28da0a0c94b6c4ec56a07ac491f966e8`, 2 stars/3 forks. Compact Git-backed Skill registry and `.claude/skills/` installer with commit-pinned lockfile and three stdio MCP tools; exact-head CI succeeded, local tests 16/16 including live GitHub install. Good adjacent Skills distribution pattern, not a Project/Section/Session importer, not a mode-specific Claude Desktop writer, and not an API-key session adapter. [Evidence](evidence/jnmetacode-skillet-review-2026-11-21.txt).

Corpus status: **94/303 reviewed, 209 pending**; next `Josepavese/nido`. Research remains incomplete.


## Adjacent local execution ResourcePlane — Josepavese/nido (2026-11-21)

MIT, latest listed release v4.11.0, exact main HEAD `b0d419977bd095ddf643d8976eef721bd833567a`, 2 stars/1 fork. Strongly tested QEMU VM manager with CLI/TUI/local stdio MCP and a Codex-compatible VM-testing Skill. The “durable MCP session” is VM lifecycle persistence, not conversation history; subscriptions are ephemeral and snapshots disk-only. Retain as optional isolated execution reference, not session migration or API-key Cloud adapter. [Evidence](evidence/josepavese-nido-review-2026-11-21.txt).

Corpus status: **95/303 reviewed, 208 pending**; next `LiorStrugach/task-manager-mcp`. Research remains incomplete.


## Low-quality adjacent Task/Plan plane — LiorStrugach/task-manager-mcp (2026-11-21)

MIT is claimed in project metadata but GitHub does not identify a license and no LICENSE file exists; 2 stars/1 fork, no releases or CI, last push 2025-04-08. Task/Plan/Notes JSON import/export is not a chat/session archive. Isolated check found broken test collection, MCP SDK v2 import failure, and wheel entrypoint omission; do not depend on it. [Evidence](evidence/liorstrugach-task-manager-mcp-review-2026-11-21.txt).

Corpus status: **96/303 reviewed, 207 pending**; next `nathfavour/anyisland`. Research remains incomplete.


## Adjacent package manager only — nathfavour/anyisland (2026-11-21)

Pinned `71a4b571adb076a1285f89ad137948d3e01a90f0` (2 stars/0 forks, no GitHub license, one v0.0.0 release, no test CI). Go tests and vet pass under an official checksum-verified Go 1.27.4 toolchain, but the project is a tool/package manager with no Harness conversation schema or import/export path. Source review shows a plaintext `Encrypt` mock contradicting its E2EE docs, no production shell-hook wiring for the described history sync, and build-plan shell commands executed with `bash -c` without the documented explicit approval step. Reject as a migration dependency; retain only as an adjacent package ResourcePlane concept. [Evidence](evidence/anyisland-review-2026-11-21.txt).

Corpus status: **97/303 reviewed, 206 pending**; next `omer-ayhan/skillspp`. Research remains incomplete.


## Skills ResourcePlane only — omer-ayhan/skillspp (#98, 2026-11-21)

MIT, v1.3.0, pinned HEAD `2440a90013889d59e915f838dac8710088c42955`, 2 stars/0 forks. It manages Skill files and provides a validation-only MCP tool, not ChatGPT Projects/Section Groups/Session graphs or Claude Desktop Chat/Cowork/Code/API-gateway sessions. Exact-pnpm typecheck, lint, unit/integration/contract/e2e/build/test:ci checks pass, but isolated probes reproduced default execution of GitHub-sourced pre/post-install shell hooks and a destination symlink escape. Do not adopt its installer unchanged. [Pinned review](evidence/skillspp-review-2026-11-21.txt).

Corpus status: **98/303 reviewed, 205 pending**; next `patterson-agents/cli`. Research remains incomplete.


## Internal config manager, not a session migrator — patterson-agents/cli (#99, 2026-11-21)

Exact HEAD `fca318f1dc775c017129cbf1856b96b7d1cfbcf4`; 2 stars/0 forks, 5 open issues, no release. Exact-HEAD upstream Gate run 31654277707 passed typecheck/test/lint (Bun 1.3.14), but local tests were not run because Bun and Socket CLI are unavailable; the repo mandates Socket scoring before dependency installation. Its strict IR and drift-safe FileOp/coverage architecture are useful independent design references. `init --import` only lifts `.mcp.json`, Claude/AGENTS instruction files, and `.claude/settings.json`; it has no conversation/session graph or Claude Desktop Chat/Cowork/Code 3P gateway writer. LICENSE is `LicenseRef-Patterson-Internal` and bars third-party redistribution absent written authorization; do not reuse source. [Evidence](evidence/patterson-agents-cli-review-2026-11-21.txt).

Corpus status: **99/303 reviewed, 204 pending**; next `rcdelfin/agentkit`. Research remains incomplete.


## Instructions/Skills linker only — rcdelfin/agentkit (#100, 2026-11-21)

MIT, pinned HEAD `f5bb34e7e09799ca3a5191970e66864a96517583`, 2 stars/0 forks, 30 commits. It links shared instructions and 15 allowlisted Markdown-only Skills into user-level Pi/Claude Code/Codex roots (plus instruction files for Gemini); it has no Session/Project/Section importer, MCP/plugin migration, ChatGPT/Codex history, Claude Desktop Chat/Cowork/Code gateway adapter, CI, releases or tests. Isolated temporary-HOME probes reproduce `--unlink` deleting a foreign instruction symlink and leaving a generated Claude `@import` wrapper after fresh install/unlink; existing regular-file backups restore correctly. Keep as a narrow ResourcePlane example only; review per-Skill licenses. [Evidence](evidence/agentkit-review-2026-11-21.txt).

Corpus status: **100/303 reviewed, 203 pending**; next `rolecraft-sh/.github`. Research remains incomplete.


## Screened repository profile — rolecraft-sh/.github (#101, 2026-11-21)

This GitHub repository contains only `profile/README.md`, an organization landing page linking the separate RoleCraft CLI, GitHub Action, registry, Skills and VS Code extension. It has no implementation, migration schema, tests or release artifacts. Do not treat its claimed 86+ agent support or MIT badge as code evidence for this repository; the linked `rolecraft-sh/rolecraft` core has its own already-reviewed entry. [Profile evidence](evidence/rolecraft-github-profile-review-2026-11-21.txt).

Corpus status: **101/303 reviewed, 202 pending**; next `rolecraft-sh/skills`. Survey remains incomplete.


## Archived Skill corpus, not a state migrator — rolecraft-sh/skills (#102, 2026-11-21)

MIT, pinned HEAD `12b10bccadd7348235ee49bf4b18bc6729616e01`, archived 2026-09-11, 2 stars/0 forks; 52 Skills. `node scripts/validate-skill.js` validates frontmatter only (52/52 pass); no Actions runs or releases were observed. The README also links to a missing `skills/core/skill-orchestration` path. It has no Projects/Section/Session graph, attachment/memory/schedule transfer, MCP/plugin configuration importer, or Claude Desktop Chat/Cowork/Code gateway adapter. All 52 frontmatter records claim MIT, but each Skill's upstream license provenance has not been independently checked. The RoleCraft CLI is a separate already-reviewed repo. [Evidence](evidence/rolecraft-skills-review-2026-11-21.txt).

Corpus status: **102/303 reviewed, 201 pending**; next `sergionoodles/skillshard`. Research remains incomplete.


## Skills manager UI, not a session migrator — sergionoodles/skillshard (#103, 2026-11-21)

Pinned `05345c60ba4506add81eda1e3d97f0091738121c` (`v0.6.0`). Rust/GPUI app manages local Skills across agent directories and delegates to `skills` CLI; `Project(PathBuf)` means a filesystem install scope. No chat/session graph, Project/Section import, attachment history, or Claude Desktop gateway adapter. Partner audits are advisory/fail-open. No declared license; exact-HEAD release packaging passed but no test CI; our offline test run could not resolve `gpui-kit` (exit 101), so local tests remain unverified. Reject as migration dependency; keep only a low-weight Skills ResourcePlane UI comparison. [Evidence](evidence/skillshard-review-2026-11-21.txt).

Corpus status: **103/303 reviewed, 200 pending**; next `stefanvo78/cross-agent-memory`. Research remains incomplete.

## Cross-agent memory handoff, not a full session migrator — stefanvo78/cross-agent-memory (#104, 2026-11-21)

Pinned df69336b661b417752647120e5a7d6c4f6ccff80. Local SQLite/FTS/vector memory, MCP retrieval and stop hooks ingest Copilot CLI, Claude Code CLI and Gemini CLI; ChatGPT/Codex is planned only. Schema and Git sync retain summaries/knowledge, not native messages, branches, Sections, attachments, token data or session restore. Good adjacent derived-memory/Handoff comparison; reject as migration dependency. Exact-head CI passed, but local tests were not run; no LICENSE file despite MIT package metadata. Source review found memory persistence, project attribution, hook-overwrite and vector cleanup risks. [Evidence](evidence/cross-agent-memory-review-2026-11-21.txt).

Corpus status: **104/303 reviewed, 199 pending**; next thesmart/install. Research remains incomplete.

## Package-manager Agent Skill, not a Harness migration tool — thesmart/install (#105, 2026-11-21)

Pinned 91f5092e6adec840361875a72b0022d3290f94e2, v1.0.1. Covers package-manager selection across OSes, but has no Project/Section/Session or memory adapter. Good explicit-consent pattern; reject the actual Skill/code due a reproduced eval injection via unescaped SHELL, a nonexistent go search reference, no CI/tests, and PolyForm Internal Use terms prohibiting redistribution. [Review](evidence/thesmart-install-review-2026-11-21.txt).

Corpus status: **105/303 reviewed, 198 pending**; next weiox/skm. Research remains incomplete.

## Skill source-of-truth manager, not a session migrator — weiox/skm (#106, 2026-11-21)

Pinned cb2ab2e7ebca2668777f1168084eaff3dd76a132. Manages Codex/Claude Code Skills from ~/.skm, exporting symlinked entrypoints. It explicitly excludes chat history and tool-internal state, has no Project/Section/session graph, and no Claude Desktop mode adapter. Fake-home tests pass, yet force sync erased unmanaged skill directories in an isolated fake HOME; doctor also skips non-symlink entries. No CI or detected license. Retain only the source/export boundary concept; reject as a migration dependency. [Evidence](evidence/weiox-skm-review-2026-11-21.txt).

Corpus status: **106/303 reviewed, 197 pending**; next wess/loom. Research remains incomplete.

## Skill package manager, not a session migrator — wess/loom (#107, 2026-11-21)

Pinned `8da92268c6562bf59180492ceb40b65f5325c752`, MIT, v0.1.1. Manages Skill manifests and directory installs for Claude Code/Codex/Cursor; has no Project/Section/session graph, history import/export, attachment/token/memory plane, or Claude Desktop mode writer. Local Rust tests 15/15 pass and exact-HEAD CI/Pages are green, but tests do not cover installer path safety. A fake-only install probe confirmed unconditional replacement of an existing skill folder; a `../outside` manifest name also passed validation, wrote beyond the configured skills root, and deleted a foreign marker. Keep only the independently implemented manifest/checksum/projection ideas; reject source as migration dependency until path ownership and staging safeguards are built. [Evidence](evidence/wess-loom-review-2026-11-21.txt).

Corpus status: **107/303 reviewed, 196 pending**; next `yearzen1/LocalSkillManager`. Research remains incomplete.

## Local Skills transfer manager, not Session migration — yearzen1/LocalSkillManager (#108, 2026-11-22)

Pinned HEAD `809eb98210038fcf02c6eb386f3436e9db10fbc8`, package 0.11.0, MIT. Supports local Markdown/directory Skills, global/project `.agents/skills` copies, and global nested TOML groups; no Project/Section/session graph or Claude Desktop modes. Positive source patterns: validated path-safe names, no-overwrite default, symlink refusal, staged atomic replace/rollback. Local E2E group-pull fixture passed; `cargo fmt` and release build pass, but full suite has one failing upgrade-permissions integration test, strict Clippy fails a Windows-only dead-code warning on macOS, and GitHub Actions has no runs. Keep as adjacent Skills ResourcePlane reference only. [Review](evidence/yearzen-localskillmanager-review-2026-11-22.txt).

Corpus status: **108/303 reviewed, 195 pending**; next `zhuyansen/awesome-agent-skills-managers`. Research remains incomplete.

## Skills-manager discovery index only — zhuyansen/awesome-agent-skills-managers (#109, 2026-11-22)

Pinned 855e594724f937a642fc044d7b6432c6f7a69332. Static CC0-licensed directory text/selection with 192 repo rows; this does not grant rights over listed projects. Useful breadth expansion for Skills/resource-plane discovery only, not code quality or session migration evidence. JSON adds 177 net-new names after 15 overlaps; 185/192 safe entries are externally graded from README/install-step signals, not full source/security review. Benchmark is one synthetic install/risk/prune/sync task, not transcript fidelity. Full evidence: [review ledger](evidence/awesome-agent-skills-managers-review-2026-11-22.txt), [supplemental JSON](awesome-agent-skills-managers-supplemental-2026-11-22.json).

Primary API corpus: **109/303 reviewed, 194 pending**. With 177 net-new candidates, primary + supplemental queue has 371 pending (manual additions remain separate); total distinct names across primary, manual, and catalog sources: **491**. Next primary candidate: zongwu233/skillctl. Research remains incomplete.

## Local Skills inventory and installer gate — zongwu233/skillctl (#110, 2026-11-22)

MIT, pinned 2abe39b2e24b6a641be7bd324b10b38011d5ea5e; 2 stars, no CI/release runs observed. Local CLI manages SKILL.md directories and rough description budgets across Claude Code/Codex/OpenCode/Pi/OMP, but has no Project/Section/Session/transcript/attachment API or model-usage ledger. Local suite passed 57 tests; scanner wasn't installed. Source/probes found project-only Codex writes leak into HOME, Codex settings blocks are replaced wholesale, invalid Claude JSON is overwritten, scanner parse failure can become SAFE, copied symlinks are dereferenced, and --force deletion is non-transactional. Keep as a narrow ResourcePlane design reference only. [Evidence](evidence/zongwu233-skillctl-review-2026-11-22.txt).

Primary corpus: **110/303 reviewed, 193 pending**; plus 177 new supplemental pending candidates; next primary candidate zzj1965186613/agentforge. Research remains incomplete.

## Skills bundle and command installer — zzj1965186613/agentforge (#111, 2026-11-22)

MIT, 2 stars, pinned HEAD 164533ddaf2be7af0c091704392f3be04f79f290. Local suite 226/226 plus Ruff/format pass; latest visible upstream CI #6 is green on seven jobs. However, this is a local Markdown Skills CLI, not a Project/Session migrator. Its remote marketplace client is all NotImplementedError, only 15 bundled Markdown skills are present, and Claude Code output goes to .claude/commands. The README pip install agentforge resolves to a different, existing GPL DataBassGit PyPI package. Path escape, symlink overwrite, and stale-source update probes also reproduced. Do not adopt as-is; see [full evidence](evidence/agentforge-review-2026-11-22.txt).

Primary corpus: **111/303 reviewed, 192 pending**; 177 supplemental candidates remain pending; next primary candidate AidarKhusainov/agent-skills-manager. Research remains incomplete.

## Skills-only manager — AidarKhusainov/agent-skills-manager (#112, 2026-11-22)

MIT; pinned master `df260b1003cea5a30fdc7a78dacaf93efb9e8e69`, tag v0.2.4, 1 star. Ships one stateless `manage` Skill for GitHub `SKILL.md` discovery/status/approval-gated install/update/remove, not project/session transfer. No Projects, Section Groups, session hierarchy, transcript/media/token/schedule support, or Claude Desktop/Claude Code destination adapter. Local 26/26 unit tests and validator pass; upstream default and PR checks pass, but manual skill-routing and write E2E remain unrun. Open PR #8 v0.2.5 is metadata/prompt routing only and does not add backend support. Use only as a narrow Skill ResourcePlane UX/security reference; reject as migration dependency. [Evidence](evidence/agent-skills-manager-review-2026-11-22.txt).

Primary: **112/303 reviewed, 191 pending**; plus 177 net-new supplemental pending. Next primary candidate: akhenda/inline-commenting-convention. Research remains incomplete.

## Inline-commenting Skill — akhenda/inline-commenting-convention (#113, 2026-11-22)

MIT, pinned HEAD `f297c7d93a4b3d8d6f8c16997b9ed1c802d859b0`, 1 star. High quality as a small coding-convention Skill for intent-focused comments/JSDoc, but “cross-harness” means manually copy instruction snippets. No code, tests, CI, Session/Project model or migration adapter. Retain as an optional InstructionPlane resource only; not migration evidence. [Evidence](evidence/akhenda-inline-commenting-convention-review-2026-11-22.txt).

Primary corpus: **113/303 reviewed, 190 pending**; plus 177 net-new supplemental candidates. Next primary candidate: All-The-Vibes/ATV-PaperBoard. Research remains incomplete.

## Cross-harness HTML artifact renderer — All-The-Vibes/ATV-PaperBoard (#114, 2026-11-22)

Apache-2.0, pinned main `4b068bcab8e4dc105f0ef975ee224564f5d63383`, 1 star/1 fork. Implements HTML/design/meta report outputs for Claude Code, Codex CLI, Copilot CLI and Copilot Agent Actions, not agent session transfer. Per-harness stores; README says unified cross-harness artifact gallery is not implemented. Local 212/215 tests pass (3 skipped), Ruff, wheel, smoke render and two `_dist` parity checks pass. Raw HTML is unsanitized; source-input provenance claimed by README is absent from metadata; uninstall remains an unmerged PR. Keep as optional Resource/ReportPlane reference only. [Evidence](evidence/atv-paperboard-review-2026-11-22.txt).

Primary corpus: **114/303 reviewed, 189 pending**; plus 177 supplemental pending. Next primary candidate: BANCUNXUEBI/reno. Research remains incomplete.


## Skills manager vs SessionGraph — BANCUNXUEBI/reno (#115)

Reno’s local store/inventory is adjacent to reusable Skill resources, not a session portability layer. It has no Project/Section/Session serializer or Claude Desktop mode adapter; the README overstates MCP/Plugin readiness relative to the Skills-only installer. Four isolated synthetic checks found archive traversal, a symlink scanner/copy gap, silent acceptance after scanning only 500 of 651 files, and nested-file loss on rollback. Keep only the abstract inventory separation idea; do not adopt the implementation. Full evidence: docs/research/evidence/reno-review-2026-11-22.txt.

Primary corpus: 115/303 reviewed, 188 pending; 177 supplemental pending; 365 combined primary + supplemental pending excluding manual additions. Next primary candidate: Beicxxxx/cross-harness-sync. Research remains incomplete.

## Narrative handoff protocol — Beicxxxx/cross-harness-sync (#116)

High-value narrow reference for project-level continuity: plain Markdown state, git transport, layered retrieval and mechanical omission checks. It does not transfer ChatGPT Project/Section/Session history or media. Current main has reproduced state-overwrite and false secret-ignore PASS defects; the macOS verifier crashes. PR #7 proposes fixes but is draft/unreleased. Do not adopt main as-is; keep the architecture idea separate from lossless SessionGraph. Full evidence: docs/research/evidence/cross-harness-sync-review-2026-11-22.txt.

Primary: 116/303 reviewed, 187 pending; 177 supplemental pending; 364 combined primary + supplemental pending excluding manual additions. Next: cagedbird-org/skills. Research remains incomplete.

## 2026-11-22 candidate #117 — cagedbird-org/skills

Pinned `main` `7e39209b5eb705714d2988f92ac35ca0b7334ba3`; skill-only Go manifest/lock/disk/mirror manager, no Project/Section/Session graph or Claude Desktop mode adapter. `go vet` and `go test -race -count=1 ./...` passed; build/version passed. A synthetic manifest using skill name `..` reproducibly escaped its configured target and removed a sibling sentinel in a disposable temp directory. Public repo is archived; README module alias points to `cagedbird043/skills`, whose URL now redirects to the archived page. Keep only the pinned-resource/drift-report design idea; reject as migration dependency, and do not trust untrusted manifests. Evidence: `docs/research/evidence/cagedbird-skills-review-2026-11-22.txt`.

Primary corpus: 117/303 reviewed, 186 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 363 excluding manual additions. Next primary candidate: Dark-Ohm/pz-mod-manager. Research remains incomplete.

## 2026-11-22 candidate #118 — Dark-Ohm/pz-mod-manager

Pinned `master` `e04311449785d27b866c2993d27f6681302326b6`, MIT. This is a Project Zomboid server/client/mod manager with GUI, JSON CLI and a working MCP interface; `.pzpack` tracks game mods/server settings. The 50 MCP tools are game operations, not session/memory migration. Release workspace tests: 62 passed, 4 ignored; build succeeds with 26 warnings. Isolated MCP handshake confirmed the described surface. Pass as an off-topic search false positive; only generic command-table/schema/mutation-hint architecture is adjacent. Evidence: `docs/research/evidence/dark-ohm-pz-mod-manager-review-2026-11-22.txt`.

Primary corpus: 118/303 reviewed, 185 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 362 excluding manual additions. Next primary candidate: ebenhzr1/agent-smith. Research remains incomplete.

## 2026-11-22 candidate #119 — ebenhzr1/agent-smith

Pinned HEAD `821e9442266fa256df781626cebd45499236c8c7`, MIT, one-star early-stage Skill package-manager concept. It has no SessionGraph or per-Harness adapter and writes only to `~/.agent-smith/skills`; configured installDir/platform tags are ignored. A loopback registry probe proved remote install fetches JSON but creates a metadata-only stub, while publish only saves local metadata. A separate isolated test reproduced a symlink write outside the stated sandbox. 28 unit tests pass, but they omit the installer; ESLint (120 errors/22 warnings) and Prettier (14 files) fail, and CI masks both. README’s `npm install -g @agent-smith/cli` resolves to an unrelated LynxAI package; requested repo version 0.2.1 is absent from npm. Do not adopt; keep only versioned resource metadata as a weak design reference. Evidence: `docs/research/evidence/ebenhzr1-agent-smith-review-2026-11-22.txt`.

Primary corpus: 119/303 reviewed, 184 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 361 excluding manual additions. Next primary candidate: erdemtuna/craft. Research remains incomplete.

## 2026-11-22 candidate #120 — erdemtuna/craft

Pinned signed release v0.5.0 / main HEAD `38a686ac308616ab2b6e7647b6ce3d50881fa18a` (MIT). Of reviewed skill-resource tools, this is a stronger package/lock reference: MVS, subpath selection, commit+SHA-256 pins, project vendoring and global install. However it handles only Skill files; auto-detection covers Claude Code and GitHub Copilot, not Claude Desktop's three modes or Session/Project/MCP/plugin data. All 13 packages pass `go test -race`; vet/build/gofmt pass; total statement coverage 60.2%. govulncheck v1.10.0 reports 20 symbol-reachable vulnerabilities in go-git/go-billy/x-crypto, including ref/path traversal, symlink and credential-redirect issues; v0.5.0 pins versions below fixes. One open PR (#34) reports a resolver limit off-by-one (201 allowed vs 200). High-value architecture reference only; do not deploy the pinned version for untrusted Skills before dependency upgrades and security re-verification. Evidence: `docs/research/evidence/erdemtuna-craft-review-2026-11-22.txt`.

Primary corpus: 120/303 reviewed, 183 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 360 excluding manual additions. Next primary candidate: eugen1408/skill-sync. Research remains incomplete.

## 2026-11-22 candidate #121 — eugen1408/skill-sync

Pinned master `fc78bf37f5531daef373031c732fe57f6a2f5abb`, release v0.9.0, MIT. Strong desktop UX/Skill resource-plane reference: three source types, canonical `.agents/skills` library, selectable per-agent paths/symlinks, 72 declared target IDs and a skills.sh official CLI path. But the table has only `claude-code` (no Desktop Chat/Cowork/Code) and no Project/Section/Session, MCP/plugin or memory migration. 41 test files/274 pass, typecheck/lint/build pass; npm audit finds 2 high-severity prod packages. A temporary failed-reinstall test showed `copyInto` deletes the existing canonical skill before a missing-source copy fails. Keep UX/path-adapter ideas, not lossless migration or unsafe replacement policy. Evidence: `docs/research/evidence/eugen1408-skill-sync-review-2026-11-22.txt`.

Primary corpus: 121/303 reviewed, 182 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 359 excluding manual additions. Next primary candidate: Hardt-LLC/AgentPack. Research remains incomplete.

## 2026-11-22 candidate #122 — Hardt-LLC/AgentPack

Pinned v0.3.0 / `b76f0e4`, MIT; local suite **487 passed**, typecheck/lint/build pass. High-value ResourcePlane reference for Skills, MCP, instructions, hooks/plugin metadata, capability negotiation, reversible sync and collection inboxes. It has no Project/Section/Session transcript graph, and its `claude` target is Claude Code only—not Claude Desktop Chat/Cowork/Code. `pnpm audit --prod` reports 2 high + 1 moderate production advisories. Useful component manager, not a session migrator. Evidence: `docs/research/evidence/hardt-llc-agentpack-review-2026-11-22.txt`.

Primary corpus: 122/303 reviewed, 181 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 358 excluding manual additions. Next primary candidate: harsha-pyla/skillhub. Research remains incomplete.

## 2026-11-22 candidate #123 — harsha-pyla/skillhub

A small four-target Skills package manager, not a Projects/Sessions migrator. Local tests **15 passed**, build passed, npm audit found 0 dependency advisories; however a mocked probe confirmed URL text enters a shell-backed `execSync` command, a safe temp CLI probe showed `remove ../../victim` deletes outside the Skill directory, and a simulated copy failure deletes the prior Skill. Its scanner is heuristic, agent paths lack coverage and differ from current vendor references, and package/release metadata conflict. Exclude from installer reuse; retain only low-confidence catalog/lock UX reference. Evidence: `docs/research/evidence/harsha-pyla-skillhub-review-2026-11-22.txt`.

Primary corpus: 123/303 reviewed, 180 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 357 excluding manual additions. Next primary candidate: Hayatelin/skillhub. Research remains incomplete.

## 2026-11-22 candidate #124 — Hayatelin/skillhub

Useful zero-dependency Skill linter/scaffolder/offline-registry reference; not a Project/Session/MCP/plugin/memory migrator and no Claude Desktop modes. Local suite **40 passed**. However, a disposable CPython 3.12.10 probe proved the `safe_extract_tar` guard can write through an in-archive symlink outside its staging root. It supports Python 3.8+ but calls `tar.extractall()` with no safe filter; existing tests only reject literal `../`. Also unpinned main/master downloads and destructive `--force` replacement. Do not use as a remote installer until fixed; retain only lint/scaffold/search ideas. Evidence: `docs/research/evidence/hayatelin-skillhub-review-2026-11-22.txt`.

Primary corpus: 124/303 reviewed, 179 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 356 excluding manual additions. Next primary candidate: jniltinho/ad-manager. Research remains incomplete.

## 2026-11-22 candidate #125 — jniltinho/ad-manager

**Pass: unrelated.** Active Directory/Samba web/desktop/CLI/MCP administration; its “sessions” are AD operator cookies or SMB client connections and its migrations are directory migrations. It has no agent conversation, Project/Section or Harness adapter. No AD app/account/service was launched. Evidence: `docs/research/evidence/jniltinho-ad-manager-review-2026-11-22.txt`.

Primary corpus: 125/303 reviewed, 178 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 355 excluding manual additions. Next primary candidate: Juliusolsson05/agent-manager. Research remains incomplete.

## 2026-11-22 candidate #126 — Juliusolsson05/agent-manager

Partial command/prompt + stdio MCP ResourcePlane manager; not a Skills, Projects or Sessions migrator and no Claude Desktop modes. Typecheck/build pass and npm production audit is clean, but `npm test` only prints TODO and exits 0. Temp probes confirmed command-path traversal, Codex remove failing on TOML, OpenCode schema/path mismatch and plaintext MCP env writes. Keep adapter/profile concepts only; do not reuse its unsafe mutators or treat it as verified. Evidence: `docs/research/evidence/juliusolsson05-agent-manager-review-2026-11-22.txt`.

Primary corpus: 126/303 reviewed, 177 pending; 177 supplemental candidates remain pending; combined primary + supplemental pending is 354 excluding manual additions. Next primary candidate: KAFKA2306/agent-resources. Research remains incomplete.


## 2026-11-22 — KAFKA2306/agent-resources (#127, reviewed but not shortlisted as a migrator)

MIT, pinned `b461929bd7138afa8211f8492662e972ff0776e1`, `agr` 0.7.8. `agr`/`agrx` are a Skills directory package manager and temporary Skill CLI runner for several coding tools. Focused library tests 136 passed; CLI tests 188 passed / 5 skipped; `ty` check passes. The repo-wide offline suite had 19 unrelated failures and Ruff found 47 diagnostics. No Projects, Sections, transcripts, events, attachments, tokens, MCP/plugin/memory/schedule, or Claude Desktop mode migration; Claude target is Claude Code CLI. `agrx` interactive Claude execution adds `--dangerously-skip-permissions`. Keep only target path/lock/resource-plane ideas and require current-version validation; not a Nexus session adapter. [Evidence](evidence/kafka2306-agent-resources-review-2026-11-22.txt).

Primary corpus: 127/303 reviewed, 176 pending; 177 supplemental net-new pending; combined pending 353. Next: `kayaman/agentskills`.


## 2026-11-22 — kayaman/agentskills (#128, not a migrator)

Apache-2.0 Rust Skill installer; pinned `a5093afcb84a27dbbd7a816f8e92bd5058313cf2`. 58 Rust tests and release build pass, but format check and strict Clippy fail. It detects eight harness markers but writes only `.agents/skills`, so Claude Code/Desktop compatibility is not proven (Claude Code docs use `.claude/skills`; Chat/Cowork are separate). No Project/Section/session/MCP/plugin/memory/schedule migration. Temp-only probes found delete-path traversal, destructive failed reinstall with stale lock, omitted dotfiles and hash framing collision. Keep only the Skills package/lock concept; reject as an installer dependency. [Evidence](evidence/kayaman-agentskills-review-2026-11-22.txt).

Primary corpus: 128/303 reviewed, 175 pending; 177 supplemental net-new pending; combined pending 352. Next: `kayaman/skillz`.

Candidate #128 comparison note: the current GitHub CLI `gh skill` public preview documents host/scope selection, preview-before-install, tag/SHA pinning and provenance, so it is the stronger current baseline for deterministic Skills management; it still does not address Project/Session migration.

Candidate #128 follow-up: a forced update-fetch failure was logged, but the command exited 0 and printed `All skills are up to date.`; this is a false-success condition, not successful reconciliation. See full evidence.


## 2026-11-22 — kayaman/skillz (#129, duplicate Skills-only tool)

Apache-2.0 Python sibling of `kayaman/agentskills`, one commit, no release/CI workflow found. It writes only `.agents/skills`; no ChatGPT Project/Section/session or Claude Desktop modes. 32 tests, Ruff, formatting pass; mypy has one error. Temp-only probes reproduced `remove ../../../victim`, destructive reinstall/stale lock, hash collisions and dotfile omissions, update errors reported as exit 0, and temp-dir leakage after lock-write failure. Keep the Skills format idea only; reject its mutators. [Evidence](evidence/kayaman-skillz-review-2026-11-22.txt).

Primary corpus: 129/303 reviewed, 174 pending; 177 supplemental net-new pending; combined pending 351. Next: `MaNongJSZ/SkillHub`.


## 2026-11-22 — LKCY23/agent-session-migration (#145, orchestration Skill only)

Pinned HEAD `5d2c56b1662a4c5da1c95949ad17643a7d304b19`. This repository installs and routes among session-migrate, harnext, dsh-chat-import, and ccx; it does not implement ChatGPT Project/Section or Claude Desktop 3P Chat/Cowork/Code session conversion. No license file was found. Its DSH reference omits ChatGPT `conversations.json` and all-branch DAG import that upstream `dsh-chat-import v0.26.2` documents; review the DSH parser itself before considering it as an intermediate. Dry-run only; no installation or Antigravity writes. Full evidence: `evidence/LKCY23-agent-session-migration-review-2026-11-22.txt`.

Primary corpus: 145/303 reviewed, 158 pending; 177 supplemental net-new pending; combined pending 335. Next executable action: source-audit pinned `Nwflower/dsh-chat-import v0.26.2` for ChatGPT Project/Section, branch, attachment, tool-call, and Claude Code export fidelity. The existing deep-review record for `1naruto-1/agent-connect` will not be repeated.


## 2026-11-22 — Nwflower/dsh-chat-import (#146, supplemental importer review)

MIT, pinned tag `v0.26.2` / HEAD `1e3e63e533abd709e646f49eca08e8a5c6de9176`. The ChatGPT parser imports a `conversations.json` mapping and can emit each root→leaf branch as its own DSH session. It is a strong DSH intermediate, not the requested universal migrator: no Project/Section membership, project assets/instructions/memory, active-node linkage or native Claude Desktop 3P Chat/Cowork writer. Synthetic tests reproduced non-text image-only turn loss/misalignment, no project metadata, default-last-child selection rather than the fixture's `current_node`, and the docs-vs-tool-schema mismatch for `import_chat(target=...)`. Separate DSH→Claude Code JSONL export requires a cwd; ChatGPT has none and defaults to a dedicated DSH import workspace. [Full evidence](evidence/Nwflower-dsh-chat-import-review-2026-11-22.txt).

Primary corpus remains 145/303 reviewed, 158 pending; 177 supplemental net-new pending; manual additions 12. Next: source-compare upstream latest `v0.26.8` against this pinned tag.

## Nwflower/dsh-chat-import — keep as a high-quality adapter/IR reference, not the complete target backend (reviewed 2026-11-22)

Latest pinned release reviewed: v0.26.8 (`4b946717d67ee8f41919913f50f7571a4bd44945`), compared to v0.26.2. The ChatGPT converter is unchanged; current focused tests pass, and upstream latest release workflow is green. Worth borrowing: per-source parsers, branch-all graph traversal, canonical turn/step IR, explicit degradation counts, idempotent import and safe preview. Disqualifier for the requested product: ChatGPT Project/Section membership and non-text assets are not restored; current `import_chat` has no `target` parameter; its separate panel transfer writes only Claude Code JSONL, not native Claude Desktop 3P Chat/Cowork records or Code registration metadata. Full source/test/synthetic-probe record: `docs/research/evidence/Nwflower-dsh-chat-import-review-2026-11-22.txt`.

## ai-agent-manager/github-dispatcher-action — adjacent CI skill dispatcher only (reviewed dc81e8a)

Retain as a resource-plane / event-trigger architecture reference, not as a session migration engine. It installs remote skills and dispatches Claude Code CLI, Copilot CLI or pi against pull-request diffs; it has no ChatGPT/Codex session or project parser, no Claude Desktop Chat/Cowork/Code writer, and no transcript graph. Local typecheck, 90 tests, build and lint pass; exact main CI is green. Production safeguards remain essential: approval-bypass modes, broad `git add -A` in `act`, no built-in commenter-role gate, and the external skill installer defaults to `latest`. [Detailed source/test/security evidence](research/evidence/ai-agent-manager-github-dispatcher-action-review-2026-11-22.txt).

## AJV009/ddev-drupal-devkit — exclude as migration backend; keep upstream Drupal Devkit as separate resource-plane lead (reviewed c9c6ccd)

The DDEV wrapper installs Drupal Devkit and optionally Claude Code in a container; it does not transport Project/Section/session history. Static install-manifest audit found three absent `global_files` source paths, two absent script targets, no project-file entries, an API-key path that writes to `web_environment` rather than the documented gitignored secret file, no tests/readme/license/releases, and no DDEV integration run. Do not deploy this wrapper as-is. The separate Drupal Devkit is a cross-harness skill/plugin installer (8 CLI harnesses), not a session migration engine, and must be separately audited. [Evidence](evidence/AJV009-ddev-drupal-devkit-review-2026-11-22.txt).

## ansonTGN/skills-hub-rs — Skills-only library and sync tool, not a session migrator (reviewed 2026-11-22)

MIT Rust CLI/Tauri app at main HEAD `085e986288ae212f1845834c9ee06282ece2e157`; GitHub lists `v0.2.0-alpha.2` as a pre-release, and main CI #18 for this HEAD passes. The core stores Skills locally and syncs `SKILL.md` directories through 47 static harness paths. It has no ChatGPT/Codex Project/Section/session parser or Claude Desktop 3P Chat/Cowork/Code destination writer. The Claude Code adapter covers `.claude/skills`; MCPJam is only a Skills path. Local core checks passed (format, 6/6 tests, strict Clippy, release build) and an isolated temporary `claude_code` project target received a matching-hash Skill symlink. Keep it as a ResourcePlane reference only. Source-derived risks: shallow clone + caller ref without resolved commit lock; overwrite removes the existing target before a replacement is safely created. No Tauri build or real target write. [Evidence](evidence/ansonTGN-skills-hub-rs-review-2026-11-22.txt).

Primary corpus: **148/303 reviewed, 155 pending**; supplemental net-new catalog **177 pending**; primary+supplemental pending **332**, excluding 12 manual additions. Next: `anverse/agentskills-manager`. Claude target clarification: the user confirmed Desktop 3P **Chat, Cowork, Code** plus local/self-hosted Claude Code; see [scope confirmation](evidence/claude-desktop-3p-scope-confirmation-2026-11-22.txt).


## anverse/agentskills-manager — Skill package-manager design only; commands not implemented (reviewed 2026-11-22)

Apache-2.0 at main HEAD fbfa1dca5612dd4a348d85e05f6b02aff6065e64; latest release shown is v0.0.1, and README explicitly says concept/development phase. Despite the detailed agentskills.yml/lockfile/install docs, the built CLI exposes only help and version—no installer, config parser, lockfile, materializer, or filesystem mutation exists. go test ./..., coverage, vet, gofmt, build, and actual binary checks passed on temporary Go 1.26.11; the only E2E cases are help/version. Main CI #2 is green on this skeleton, not on a migration engine. Keep its content hash, immutable store, copy-vs-link, and ownership-safe deletion ADRs as design references only. It does not model ChatGPT/Codex session/project trees or any Claude Desktop 3P/local-session surface. Evidence: docs/research/evidence/anverse-agentskills-manager-review-2026-11-22.txt.

Primary corpus: 149/303 reviewed, 154 pending; supplemental net-new pending 177; combined pending 331, excluding 12 manual additions. Next primary candidate: arthamegayasa/nam-stack.


## arthamegayasa/nam-stack — five Skills, not a manager or session migrator (reviewed 2026-11-22)

MIT personal repository at `main` HEAD `d645ff1438f90f6d19e5ded3cecf3f51f35dfc49` (0 stars/0 forks snapshot; no releases). Contains five Skills for Claude Code, Codex, and Grok Build. It has no ChatGPT/Codex Projects, Sections, session hierarchy, MCP/plugin deployment, memory, or schedule migration. The structure validator/self-tests pass and 13 local fake-HTTP evals pass, but a temporary-only `--name ../escaped` probe showed `openai_image.py` writes outside `--out`; `openrouter_image.py` contains the same unchecked join. Keep only as a portability/security fixture. Its README's unpinned `xingkongliang/skills-manager` dependency is queued for a separate code audit. [Full evidence](evidence/arthamegayasa-nam-stack-review-2026-11-22.txt).

The user confirmed Claude Desktop 3P target scope is all three modes—Chat, Cowork, and Code—plus local/self-hosted Claude Code. Treat the modes as separate acceptance checks; see [official-doc-derived route and packaging constraints](evidence/claude-desktop-3p-skills-routing-2026-11-22.txt).

Primary corpus: **150/303 reviewed, 153 pending**; supplemental net-new pending **177**; combined **330** pending; 13 manual additions with 1 pending. Next primary: `arynull/skillden`.


## arynull/skillden — local Skills package manager only; data-loss risks reproduced (reviewed 2026-11-22)

MIT Python package at `main` HEAD `23104d439ccfc169ad310076f73c46443125e47c`; GitHub currently shows v0.5.1 and its latest CI run on this commit passes. Actual target adapters are only local Claude Code Skills, Cursor, and generic. It has a local SQLite Skill registry, content hashes, dependency resolution, project pinning/lockfile and scanner, but no Claude Desktop 3P Chat/Cowork/Code, Codex/ChatGPT Projects/Sections/session graph, MCP/plugins, memory or schedules.

Local Python 3.12.4 install, Ruff and 12 CI-style smoke commands passed. Temporary-only probes: owner/name basenames collide and a second install overwrites the first without `--force`; crafted `.skillden/pins.json` entry `author/..` made `unpin` remove project files before an exit-1 traceback. Additional observed defects: CLI `--version` says 0.4.0 while package is 0.5.1, and `info` prints blank description/author/license. Keep only as a ResourcePlane concept fixture; do not reuse its current mutation semantics. [Full source and runtime evidence](evidence/arynull-skillden-review-2026-11-22.txt).

Primary corpus: **151/303 reviewed, 152 pending**; supplemental net-new pending **177**; combined **329** pending; 13 manual additions with 1 pending. Next: `brainpower168/skill-manager`.


## brainpower168/skill-manager — Windows Skill junction manager only; destructive CLI paths reproduced (reviewed 2026-11-22)

MIT, 5-commit Python CLI at `main` HEAD `830ca5d91818969088bde3b38c21ba9f60c2eaad` (0 stars/0 forks; no releases or Actions runs). Centralizes a global Skill copy and links to configured per-agent global Skills folders. README verifies Windows 10/11 + ZCode; macOS/Linux remain roadmap. No ChatGPT/Codex Projects/Sections/sessions, MCP/plugins, memory, schedules, project-scope or Claude Desktop 3P Chat/Cowork/Code adapter.

Temporary-only POCs: `remove ../victim` deleted a sibling directory outside the library; `install --force` with a simulated junction-creation failure deleted an existing real Skill, reported replacement success and returned 0 without creating a link. Config is machine-specific and stored beside the script; symlinked parent paths can be misclassified; existing same-name library content prevents update. Keep only as a low-priority Windows ResourcePlane concept, not an installer/migrator. [Full source and runtime evidence](evidence/brainpower168-skill-manager-review-2026-11-22.txt).

Primary corpus: **152/303 reviewed, 151 pending**; supplemental net-new pending **177**; combined **328** pending; 13 manual additions with 1 pending. Next: `CDataSoftware/google-campaign-manager-360-mcp-server-by-cdata`.


## CDataSoftware/google-campaign-manager-360-mcp-server-by-cdata — archived single-source MCP adapter, not migration (reviewed 2026-11-22)

MIT local Java/stdio MCP server, exact main HEAD `1dc44b6c99367a5c503b73488ba561999aa4ea85`. GitHub archived it on 2026-11-17; README says deprecated/no updates. It wraps an external CData Campaign Manager 360 JDBC driver and has a Claude Desktop `mcpServers` sample, but only tools for table/column metadata and SQL query. There is no MCP config migration, Projects/Sections/Sessions/message-branch handling, or Desktop 3P API-key/Chat/Cowork/Code runtime test. Maven test/package passed (11 utility tests), but no integration test or JDBC driver is bundled. Source intent is read-only and uses `executeQuery`; no write tools exist, although a generic README paragraph contradicts this and the source does not explicitly set JDBC read-only or restrict query tables. Keep only as a local MCP command/transport/auth-reference design fixture. [Full evidence](evidence/cdatasoftware-google-campaign-manager-360-mcp-review-2026-11-22.txt).

Primary corpus: **153/303 reviewed, 150 pending**; supplemental net-new pending **177**; combined **327** pending; 13 manual additions with 1 pending. Next: `clictl/cli`.


## 2026-11-22 — clictl/cli (#154, ResourcePlane manager only)

Pinned `main` HEAD `80a83a81c8978b883adbf7b7b67af70e0b0e7a61` (Apache-2.0, 0-star snapshot, latest visible v0.1.2). Worth studying for typed API/CLI/MCP/Skill manifests, local MCP config writers, vault references, and sandbox metadata. Not a ChatGPT/Codex Project/Section/Session or transcript migrator; its Claude Desktop target is local MCP JSON only. Go tests and vet pass. Isolated temporary probes reproduced Skill file path traversal/sibling overwrite, a Codex Skill filename mapping defect, and `forget ../config --all` deleting a disposable sibling config. Sandbox defaults must be audited rather than copied. User scope remains Claude Desktop 3P **Chat, Cowork, Code (all three, tested separately)** plus local/self-hosted Claude Code. [Full evidence](evidence/clictl-cli-review-2026-11-22.txt).

Primary corpus: **154/303 reviewed, 149 pending**; supplemental net-new **177 pending**; manual additions **13** with **1 pending**; total unresolved including manual **327**. Next: `CTOUT/agentsmith`.


## 2026-11-22 — CTOUT/agentsmith (#155, asset sync only)

Pinned main HEAD `fded2989b580230e43467e36369964ef3cbc5e60`, MIT, 0-star snapshot, only visible release v0.1.0. It syncs `awesome-copilot` markdown assets to VS Code, Kiro, and Antigravity at repo/user scope; no Project/Section/Session graph, MCP transfer, attachments, schedules, or Claude Desktop 3P Chat/Cowork/Code/local Claude Code adapter. Local build/lint/format and 72 tests pass after build. Disposable POCs found exactly 25% removal is allowed despite ≥25% docs, and failed forced directory copy deletes old target before failure, leaving stale subscription hash. Keep adapter/loss reporting, hashes, subscriptions, and dry-run UX as ResourcePlane ideas only. [Evidence](evidence/ctout-agentsmith-review-2026-11-22.txt).

Primary corpus: **155/303 reviewed, 148 pending**; supplemental 177 pending; manual additions 13 with 1 pending; total unresolved including manual 326. Next: `DaveGerson/aiskills`.


## 2026-11-22 — DaveGerson/aiskills (#156, process/skill sidecars, not session transfer)

Pinned `master` HEAD `7e238306d47507bf6e63032d76b862a54d05a06d` (MIT; 0 stars/forks; 2 commits; no release/Actions). Two original skills provide a Markdown program-docs/decision-log workflow and a Claude ArtifactData-backed status page; setup templates cover Claude Code, Antigravity, Codex. Useful as authored continuity documentation, not a native transcript/Project/Section/Session exporter. Seed validation passed 59 docs. Synthetic probes confirmed both `make_batches.py` and `make_harness.py` accept a manifest file path escaping the seed directory; the first can direct later ArtifactData reads to an external file. Claude Code 2.1.76 rejects the marketplace manifest's root `description`; Codex local marketplace registration worked, but no install was attempted. [Full evidence](evidence/davegerson-aiskills-review-2026-11-22.txt).

Primary corpus: **156/303 reviewed, 147 pending**; supplemental 177 pending; manual additions 13 with 1 pending; total unresolved including manual 325. Next: `David-Sat/agpx`.


## 2026-11-22 — David-Sat/agpx (#157, Skills/MCP package manager, not session migration)

Pinned main HEAD `61b51e587422738c8735011eedb30308cd1c8890` (MIT; 0-star snapshot; package v0.3.1). It contains 19 resource adapters and installs Skills/MCP/env config. Claude Desktop only writes MCP configuration; Skills target is null, and implementation has no separate 3P Chat, Cowork, or Code session paths. No Codex ID or session/project/Section/branch/attachment/schedule schema. Its Claude Code MCP path `~/.claude/mcp.json` conflicts with current official `~/.claude.json` user/local and `.mcp.json` project scope docs. Local Node 26.7 build + test passed 27/27; CLI reports 0.1.0 despite package 0.3.1. Four disposable probes reproduced manifest path traversal, update/non-TTY trust bypasses, and removal of manually added files within a Skill directory. No real command, credentials, or user data were accessed. Keep only adapter/dry-run patterns as an adjacent ResourcePlane reference. [Detailed source/runtime evidence](evidence/david-sat-agpx-review-2026-11-22.txt).

Claude Desktop remains confirmed in scope for **all three** API-key/gateway surfaces (Chat, Cowork, Code), each separately tested, plus local/self-hosted Claude Code; do not conflate this with Anthropic-hosted Cloud sessions. Primary corpus: **157/303 reviewed, 146 pending**; supplemental 177 pending; manual 13 with 1 pending; total unresolved including manual **324**. Next: `davidjamesshelley-netizen/skillpack`.


## 2026-11-23 — davidjamesshelley-netizen/skillpack (#158, README-only proposal)

Pinned main HEAD `bfe9f5407a100f75e6c4dcb66b5fe9f8a8e4c151`. Checkout contains only README.md (one commit); no source, package manifest, tests, CI, or LICENSE. README sketches a versioned Skills registry/CLI and declares Apache-2.0, but that license is unverified. `npm view skillpack` returns v0.1.3 from a different repository, `joventuraz/skillpack`, so the README's install command is not attributable to this proposal. No session, Project, Section, MCP, API, or migration implementation. Screen as README-only; keep manifest fields only as unvalidated ideas. [Evidence](evidence/davidjamesshelley-netizen-skillpack-review-2026-11-23.txt).

User-confirmed target is still Claude Desktop 3P Chat, Cowork and Code (all three, separately), plus local/self-hosted Claude Code. Inventory: **158/303 reviewed, 145 pending**; 177 supplemental pending; manual 13 with 1 pending; total unresolved including manual **323**. Next: `devansh0703/skill-router`.


## 2026-11-23 — devansh0703/skill-router (#159, skill shelf helpers, no session transfer)

Pinned main HEAD `f545fe5aff9abb7a0362bf16403ac299ac3de14e` (MIT). Two Skills provide runtime shelf routing and local skill-manager helpers; no project/session/event/branch/attachment/MCP/schedule migration. On host GNU Bash 3.2.57, `catalog.sh` emits associative-array errors yet exits 0 without output; unmatched manager search exits 1 on `${desc,,}`. List, validate (2/2), and doctor pass. Synthetic-only POCs: `disable ../outside/victim` moves a file outside `SKILLS_HOME`; disable/enable collisions silently overwrite existing copies. Keep only live-shelf routing concept; do not use mutators as safe migration writes. [Evidence](evidence/devansh0703-skill-router-review-2026-11-23.txt).

Confirmed target remains Desktop 3P **Chat, Cowork, Code** as separate acceptance tracks plus local/self-hosted Claude Code. Inventory **159/303 reviewed, 144 pending**; supplemental 177; manual 13 with 1 pending; total unresolved including manual **322**. Next: `DoryZi/token-efficient-lifecycle`.


## 2026-11-23 — DoryZi/token-efficient-lifecycle (#160, subscription workflow, not migration)

Pinned main HEAD `e3ef5437767b1cec77e1c2969d86ed391dc7709c` (MIT, early 0.1.0). Cross-harness orchestration covers Claude Code and Codex **subscription** CLIs, plus a constrained Playwright worker; it does not migrate Projects, Sections, Sessions, branches, attachments, MCP/plugins, memory, or schedules. API-key billing is explicitly rejected and Claude Desktop 3P modes are not targets. The Claude orchestrator uses `auto` permission mode, suppresses prompts, and grants Bash/Read/Write/Edit without a filesystem sandbox. Browser worker has better command/model restrictions, but inherits the full parent environment into Playwright and accepts `../` attachments outside task directory in synthetic validation. Tests: orchestrator 13/14 (one macOS `/var` vs `/private/var` canonical-path assertion mismatch); browser 54 passed using locked deps, fake CLI/browser/model. No live account or browser used. [Evidence](evidence/doryzi-token-efficient-lifecycle-review-2026-11-23.txt).

Keep only bounded handoff/attempt/verification patterns. Target remains Desktop 3P Chat/Cowork/Code separately + local/self-hosted Claude Code; candidate satisfies none. Inventory **160/303 reviewed, 143 pending**; supplemental 177; manual additions 13 with 1 pending; total unresolved including manual **321**. Next: `Dual-Forge/skills-manager`.


## 2026-11-23 — Dual-Forge/skills-manager (#161, Skills only)

Pinned main `9bff2528ce7cdfe7e39bedbebf6b8e35029547b0` (MIT root license; third-party bundle notices remain). Valuable only as a local Skills catalog/bundle/provider-root reference; it has no ChatGPT/Codex Projects/Sections/Session graph, transcript/attachment/memory/schedule migration, or Claude Desktop 3P Chat/Cowork/Code/local Claude Code writer. 41/41 tests pass, but actual-function temp probes reproduced installer path escape from `.agents/skills`, destructive replacement of a user's sidecar file, and missed sidecar updates when `SKILL.md` matches. API-key code generates Skills, not sessions. Do not adopt its installer as a transactional writer; full details: [evidence](evidence/dual-forge-skills-manager-review-2026-11-23.txt).

Latest user clarification reconfirms separate acceptance tracks for Desktop 3P Chat, Cowork and Code, plus local/self-hosted Claude Code. Inventory **161/303 reviewed, 142 pending**; supplemental pending 177; combined pending 319; manual additions 13 with 1 pending; unresolved including manual 320. Next: `ducconit/gvm`.


## 2026-11-23 — ducconit/gvm (#162, toolchain manager, not session transfer)

Pinned `c6407df8614ce312cce0de455aa4e1533e17e82a` (MIT). It manages Go toolchains and includes a stdio MCP server plus one Skill installer for local provider paths; no Project/Section/Session graph, transcript, attachment, memory, schedule, or Claude Desktop Chat/Cowork/Code/session adapter. Useful adjacent patterns: Skill path mapping, MCP schema, SHA-verified official Go toolchain archives, Tar/Zip-Slip checks, staged installs. Risks: fake-server POC showed self-update replaces the executable when release SHA is absent; GitHub release asset uses a `digest` field in current REST docs while source reads only `sha256` (schema inference; direct API fetch blocked); installers omit checksum verification. Synthetic Skills install overwrote a temp SKILL.md; MCP uninstall tool directly removed a synthetic Go version without server-side confirmation (host may add approval). Race tests passed after canonical TMPDIR correction; `go vet` and six cross-build targets passed; GitHub main CI run #5 green. [Full evidence](evidence/ducconit-gvm-review-2026-11-23.txt).

Inventory **162/303 reviewed, 141 pending**; supplemental pending 177; combined pending 318; manual additions 13 with 1 pending; unresolved including manual 319. Next: `EfanWang/skills-manager`.


## 2026-11-23 — EfanWang/skills-manager (#163, Skills only)

Pinned main `1f0482bf822835d19552487a2a6345735cdffa0d` (MIT, May 19). A single-skills-root provenance/update tool with backup and atomic rename; no Project/Section/Session graph or Claude Desktop Chat/Cowork/Code transfer. Its SKILL.md delegates unresolved source tracing to agent WebSearch. All 80 tests pass. Temporary probes found inventory follows a sibling symlink and reads an external synthetic SKILL.md, and the `.git/config` gate auto-claims a fake GitHub origin without checking remote content. GitHub shows no Releases or Actions workflows. Keep only path-contained installs, backups, atomic swap, and rollback as adjacent Skill-resource patterns; full evidence [here](evidence/efanwang-skills-manager-review-2026-11-23.txt).

Target remains Desktop 3P Chat/Cowork/Code separately plus local/self-hosted Claude Code. Inventory **163/303 reviewed, 140 pending**; supplemental pending 177; combined pending 317; manual additions 13 with 1 pending; unresolved including manual 318. Next: `ekupekuAI/agenthub`.


## 2026-11-23 — ekupekuAI/agenthub (#164, Skills supply-chain reference)

Pinned `bc74259f22ab2c043aaed3f5abb3e1e29e72dbb4` (MIT). Useful transactional/integrity patterns for Skills, but no native Project/Section/Session or Claude Desktop Chat/Cowork/Code/local Claude Code transfer. Node 24 CI-equivalent checks pass; Node 26 source/test suite fails on removed TS transform flag, while Node 26 production web build and bundled worker test pass. Keep as resource-plane reference only. [Evidence](evidence/ekupekuai-agenthub-review-2026-11-23.txt).

Confirmed targets remain Desktop 3P Chat/Cowork/Code separately plus local/self-hosted Claude Code. Inventory **164/303 reviewed, 139 pending**; supplemental 177; combined pending 316; manual 13 with 1 pending; unresolved including manual 317. Next: `emanuelet/skill-manager`.


## 2026-11-23 — emanuelet/skill-manager (#165, Skills/MCP resource reference)

Pinned `5fbf417e9ae30cbcbcf20515f83239dde1c142d4` (MIT). Useful local Skill store, `.skills.json` manifests, profiles, MCP tool discovery and session-start Skill activation; no session/project/section migration. Local Node 26 suite 870/870 after canonical TMPDIR; upstream CI is unrun/broken (`npm ci` but only pnpm lock; Node20/22 vs engines >=24). Synthetic CLI POCs reproduced loss of distinct refs when duplicate Skill bodies are deduped and nested symlink import from outside the Skills root. Do not reuse auto-adopt as a writer until fixed. [Evidence](evidence/emanuelet-skill-manager-review-2026-11-23.txt).

Targets remain Desktop 3P Chat/Cowork/Code separately plus local/self-hosted Claude Code. Inventory **165/303 reviewed, 138 pending**; supplemental 177; combined pending 315; manual 13 with 1 pending; unresolved including manual 316. Next: `fabiomartino/shroud-layer`.


## 2026-11-23 — fabiomartino/shroud-layer (#166, empty repository)

Git clone exits 0 with empty-repository warning; official GitHub page confirms repository is empty. No HEAD, README, LICENSE, source, tests, CI or releases. Description/topics are not enough to infer an overlay or migration implementation. Exclude pending future source publication. [Evidence](evidence/fabiomartino-shroud-layer-review-2026-11-23.txt).

Targets remain Desktop 3P Chat/Cowork/Code separately + local/self-hosted Claude Code. Inventory **166/303 reviewed, 137 pending**; supplemental 177; combined pending 314; manual 13 with 1 pending; unresolved including manual 315. Next: `facundoPri/agent-config-manager`.


## 2026-11-23 — facundoPri/agent-config-manager (#167, session-observability reference)

Pinned `a6f6af755edfd0edb338e5032761822fabc9e566` (MIT). Resource inventory/archive across Skills/MCP/hooks and an opt-in local proxy that records live Claude Code/beta Codex calls. Useful to model captured context, but no historical Session/Project migration or Claude Desktop Chat/Cowork/Code target. Bun tests 10/10 pass. POCs: path traversal in Skill detail, prompt-body sentinel retained in logs, Codex missing IDs collapse by day, and prefix collision links two child threads to one spawn. [Evidence](evidence/facundopri-agent-config-manager-review-2026-11-23.txt).

Targets remain Desktop 3P Chat/Cowork/Code separately plus local/self-hosted Claude Code. Inventory **167/303 reviewed, 136 pending**; supplemental 177; combined 313; manual 13 with 1 pending; unresolved including manual 314. Next: `fei-bai-inc/sine-kits-skills`.


## 2026-11-23 — fei-bai-inc/sine-kits-skills (#168, universal Skill content reference)

Pinned `c450388630135adc5cfc2e48491df66c252fadbe`. Two generic Skills use schema-discovered Sine Kits operations with explicit grants/idempotency; no cross-Harness chat/session/project migration. No repository license or product code/test suite; npm CLI/contracts 0.3.0 referenced by Skills are not published (latest queried 0.2.0). Keep protocol ideas only; do not count as a migration tool. [Evidence](evidence/fei-bai-inc-sine-kits-skills-review-2026-11-23.txt).

Targets remain Desktop 3P Chat/Cowork/Code separately plus local/self-hosted Claude Code. Inventory **168/303 reviewed, 135 pending**; supplemental 177; combined 312; manual 13 with 1 pending; unresolved including manual 313. Next: `FutureHax/openclaw-skill-manager`.

## Candidate #169 — FutureHax/openclaw-skill-manager: OpenClaw Skill lifecycle only, not Harness migration

Pinned `main` HEAD `03f3542203522a3fcb0be9f030f768b2db90a0fa` (2026-02-12). It is a Shell/Markdown agent Skill that detects capability gaps, creates/pushes OpenClaw Skills, tracks them as pending, and asks for approval before installing. It provides no ChatGPT/Codex Project, Section Group, session/fork graph, transcript/attachment, MCP/plugin/memory/schedule or Claude Desktop 3P Chat/Cowork/Code/local Claude Code adapter. README says MIT but the checkout has no LICENSE; the GitHub Releases page has none. Keep only the approval/pending lifecycle idea.

Isolated temp-HOME tests with fake git/curl: benign pending CRUD and a mocked fresh install pass. However `install.sh` returns success while placing SKILL.md under an unexpected nested directory when the destination exists but is empty; `SKILL_NAME=../../../outside/skills/escaped` writes outside the configured Skills root. `pending.sh remove` executes a safe injected Python print expression from its name parameter. `create.sh` was not run with a token and no real GitHub write occurred. No upstream test suite. Reject its scripts as a migration writer. [Full pinned-source review and literal test results](research/evidence/futurehax-openclaw-skill-manager-review-2026-11-23.txt).

The user confirmed all three Claude Desktop third-party-gateway modes—Chat, Cowork, and Code—must be validated separately, plus local/self-hosted Claude Code. Primary inventory **169/303 reviewed, 134 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **311**; manual additions **13**, one pending; unresolved including manual **312**. Next primary candidate: `GastonGelhorn/worktree-mcp-manager`. Research remains active and incomplete.

## Candidate #170 — GastonGelhorn/worktree-mcp-manager: task/worktree coordination, not conversation migration

Pinned `main` HEAD `5ac16072b04a8687940fb82eada37afcfe3995ae` (2026-04-15). Rust worktree core + CLI, macOS Tauri/React app and stdio MCP support branch isolation, task claims/heartbeats, handoff and generated `CLAUDE.md`/`.cursorrules`. These are useful Taskplane/worktree patterns, but it does not read or restore ChatGPT/Codex Projects, Section Groups, conversational Session/event/fork graphs, messages, attachments, usage, Skills/MCP/plugin configs, memories or schedules. Its MCP `Session` is process identity, not a transcript. Registering an MCP server in Claude Desktop is not a third-party API-key session importer.

Checks: frontend **50/50**; MCP **33/33** and MCP TypeScript build pass. Rust core **130 passed / 3 failed** (date-brittle heartbeat freshness, `src/main.rs` misclassification, score-threshold mismatch); CLI package has 0 tests; whole Cargo workspace cannot build because expected Tauri CLI sidecar is absent. Root Vite build fails because `index.html` is missing. Three isolated temp-HOME probes reproduced a path-prefix allowlist bypass, unredacted context in the audit log, and `remove_worktree` bypassing session-guard path extraction. README says MIT, but no LICENSE exists and the MCP package declares ISC; releases page is empty. Keep shared-core/MCP/task-context patterns only; reject as migration engine. [Full pinned source, POC outputs and error ledger](research/evidence/gastongelhorn-worktree-mcp-manager-review-2026-11-23.txt).

Targets remain three separate Claude Desktop third-party-gateway tracks (Chat, Cowork, Code) plus local/self-hosted Claude Code. Primary inventory **170/303 reviewed, 133 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **310**; manual additions **13**, one pending; unresolved including manual **311**. Next primary candidate: `gitstq/SkillVault`. Research remains active and incomplete.

## Candidate #171 — gitstq/SkillVault: Skill catalog only; pip name collides with a separate memory library

Pinned `main` HEAD `11426134735995fca445f059c250eec1a6822021` (2026-05-17, one commit). The MIT Python CLI stores Skill Markdown and metadata in its own `~/.skillvault/registry`, supports a bundled six-Skill catalog, JSON import/export and tag/platform filtering. A temp-HOME CLI install wrote only to that registry; no Claude/Cursor/Copilot/Windsurf target Skill file was created. It is not a Project/Section/Session, transcript, attachment, MCP/plugin, memory/schedule or Claude Desktop 3P/local Code session migrator. Its platform values are metadata, not deploy adapters. Tests pass **39/39**; source-level regex validation is advisory: a `subprocess` high-risk finding is still `valid=true` by default. [Full pinned source and POCs](research/evidence/gitstq-skillvault-review-2026-11-23.txt).

Important package-name collision: README says `pip install skillvault`, but official PyPI `skillvault==0.1.3` belongs to a different maintainer/project; its package metadata points to the placeholder repository `yourusername/skillvault`, not this GitHub repo. Its SHA-256 verified sdist is a separate SQLite/vector memory library that can extract reusable knowledge from conversations to draft Skills, but flattens messages, retains only a short source excerpt, and has no Harness transcript adapter. Its docs promise humans control canonical Skills, but a synthetic temp-DB run showed agent-mode `extract()` can auto-promote a draft after the usage threshold without `approve()`; PyPI sdist tests **15/15** after adding test-only `respx` absent from dev extras. Do not confuse these packages or follow the GitHub README pip command as if it installed this repo.

The confirmed destination remains separate Claude Desktop third-party-gateway Chat/Cowork/Code tracks plus local/self-hosted Claude Code. Primary inventory **171/303 reviewed, 132 pending**; supplemental net-new pending **177**; combined primary and supplemental pending **309**; manual additions **13**, one pending; unresolved including manual **310**. Next primary candidate: `gluestick-sh/gluestick-integrated-with-mcp`. Research remains active and incomplete.


## Candidate #172 — gluestick-sh/gluestick-integrated-with-mcp: Windows MCP package manager, not session migration

Pinned `main` HEAD `9d02da15c26c6efd27023aacac0d4cb7acbad8f0`. Windows-only Scoop-compatible Go package manager; its stdio MCP setup documents Claude Desktop but only registers local package/bucket tools (14 `glue_*` tools), not a third-party API-key gateway or ChatGPT/Codex Project/Section/Session history importer. Default writes use a five-minute single-use confirmation token and re-check policy; auto-yes/policy-auto bypasses confirmation. Keep local MCP config, typed JSON, approval/audit patterns only. Windows Actions #11 passed; local Windows cross-build passed. Native macOS full tests failed as platform-specific, and the concurrent audit-chain test fails under the non-Windows no-op lock; do not treat that as Windows runtime evidence. [Pinned source, tests, warnings and exact results](evidence/gluestick-sh-gluestick-integrated-with-mcp-review-2026-11-23.txt).

All Claude Desktop third-party-gateway modes remain separately in scope (Chat, Cowork, Code), plus local/self-hosted Claude Code. Primary inventory **172/303 reviewed, 131 pending**; supplemental net-new pending **177**; combined pending **308**; manual additions **13**, one pending; unresolved including manual **309**. Next: `GoblinRules/ecpa-connections-manager`. Research active and incomplete.


## Candidate #173 — GoblinRules/ecpa-connections-manager: strong MCP/Skills config reference, not session migration

Audited release root HEAD 791a22a52f2cfabda279bfa893f3dc3f74d5af11 and exact v0.8.1 source GoblinRules/ecpa-plugins@5275342b6f8bfc2c3e5da6f453509292561df0ad (current relevant source paths unchanged). The Windows ECPA suite has separate MCP Manager and Agent Skills plugins: careful Claude Code↔Codex MCP subset translation with preview/version checks/backups/rollback, plus a reviewed SKILL.md editor. Valuable architecture for Nexus config/asset-plane safety; not a ChatGPT/Codex Project, Section/Session/transcript/attachment/token/schedule importer, not Claude Desktop third-party Chat/Cowork/Code, and not a Claude Code history migrator. Connection-manager project assignments are local folder→credential references, not Harness Projects.

Verification: Connections Manager 8 tests pass; full Rust workspace 32/32 passes with non-symlink TMPDIR (initial default macOS temp path failed because /var aliases /private/var and shared path guard rejects symlink ancestors); MCP/Skills plugin-suite 9/9; full Clippy and format pass; gateway Python suite 22 passed/5 Windows-only skips. No real credentials, upstream request, user config or session was used. Full findings and error/test ledger: evidence/goblinrules-ecpa-connections-manager-review-2026-11-23.txt.

Confirmed target remains Claude Desktop third-party-gateway Chat/Cowork/Code separately plus local/self-hosted Claude Code; label Destruction Era retained. Primary inventory 173/303 reviewed, 130 pending; supplemental net-new pending 177; combined primary+supplemental pending 307; manual additions 13, one pending; unresolved including manual 308. Next: GustavoGutierrez/skillweaver. Research active and incomplete.


## Candidate #174 — GustavoGutierrez/skillweaver: Skills/Rules manager only; installer has unverified/partial-write gaps

Pinned HEAD 630ca593dda8cf118f0d108b475c19bfcd97e926 (v0.0.4, latest release 2026-05-12). Actual Rust TUI/CLI stores profiles of Skill IDs and rules, scans local roots, downloads per-skill ZIPs into .agents/skills and may link/copy to .claude/skills. It has no ChatGPT/Codex Project/Section/Session graph, transcripts, media, schedules, MCP/plugin or memory migration, and no Claude Desktop Chat/Cowork/Code target. Do not count as a session migrator.

Quality notes: tests pass 20/20, check/fmt/clippy pass with a q-free TMPDIR, but cargo test --locked fails due manifest 0.0.4 vs Cargo.lock 0.0.3. POCs showed profile install_mode=copy still symlinks; lock hashes remain pending; malformed ZIP without SKILL.md installs as success; a later missing artifact leaves earlier files behind; archive containment checks can create an outside directory before rejecting. A q typed in an input modal exits the TUI and breaks a registered-source test when the path contains q. Keep profile schema/local skill-root discovery as comparative notes only, not an implementation base. Evidence: research/evidence/gustavogutierrez-skillweaver-review-2026-11-23.txt.

Claude Desktop third-party-gateway Chat/Cowork/Code remain separate tracks; local/self-hosted Claude Code remains distinct. Primary inventory 174/303 reviewed, 129 pending; supplemental net-new pending 177; combined pending 306; manual additions 13, one pending; unresolved including manual 307. Next candidate: harry-leon/ai-agent-skills-registry. Research active/incomplete.


## Candidate #175 — harry-leon/ai-agent-skills-registry (Skillary): adjacent Skills registry, not a session migrator

Pinned current `main` HEAD `11d3972c118b44c91e3ad37e15de45c77486014c`. Strong private-by-default SKILL.md registry and hardened GitHub/ZIP/path ingestion; source includes file/version/blob hashes and auth/visibility/fork policies. But Prisma `Session` is login/auth only; Projects/Sections/conversation graph/transcripts/media/tokens, MCP session config, plugins, memories, schedules, and Claude Desktop Chat/Cowork/Code/local Claude Code migration are absent. Unit suite 38/38, lint, format and corrected dummy-S3 production build pass; PostgreSQL integration tests could not run (no DB at 127.0.0.1:5432). README CLI claims `npx skillary add`, package is private/no-bin, UI copies `npx skillvault add`, and npm `skillary@0.0.3` resolves to a different yurtsever/skillary project; treat installation docs as unverified. Retain security/Skills design only; pass as direct solution. Evidence: `research/evidence/harry-leon-ai-agent-skills-registry-review-2026-11-23.txt`.

New manual lead (README-screened only, not source-reviewed): `nikships/skills-registry` — cross-agent skills gateway + Go CLI/npm launcher + native macOS app; queued for code/tests review, not counted as session-migration evidence.

Current counts: primary 175/303 reviewed, 128 pending; supplemental net-new pending 177; primary + supplemental pending 305; manual additions 14, 2 pending; unresolved including manual 307. Next primary candidate: Heverton-web/skill-manager. Claude Desktop third-party-gateway Chat/Cowork/Code remain separate tracks; local/self-hosted Claude Code remains distinct. “Destruction Era” spelling correction retained. Research remains active/incomplete.


## Candidate #176 — Heverton-web/skill-manager: Skills + OpenCode monitor, not a migrator; dashboard execution risk

Pinned current main `4c9acccad4644b62896dcb63e794f0d936b35d94` (commit 2026-08-05). The monorepo's Skills Manager claims 13 IDEs, but selected IDE IDs are stored rather than passed to generic `npx skills add`; Codex and Claude generate the same command, and fallback writes only `.claude/skills`. Its Skills package declares no test script. A temporary localhost POC confirmed unauthenticated wildcard-CORS `/api/toggle` can shell-inject through a request-controlled skill value; only a fake npx and temp marker were used. Do not run the dashboard unmodified. The separate OpenCode Monitor is a single-Harness live event/token-cost dashboard, not a session exporter. Its API exposes JSONL events with wildcard CORS; a synthetic-data POC confirmed read exposure. The monitor test suite passed 23/23 with its OpenCode URL pointed at refused localhost port 1. Full evidence: `research/evidence/heverton-web-skill-manager-review-2026-11-23.txt`.

OpenCode API update: official current docs describe experimental native session export/import; `parentID`/fork/project relations, cursor-paginated typed messages, file attachments with base64/MIME/source, agent/skill attachments, tool states, cost/token usage, permissions and revert metadata are represented. Parent must be imported before child; event streaming is volatile. This is a high-value OpenCode adapter opportunity, not cross-Harness compatibility. Evidence: `research/evidence/opencode-native-session-transfer-api-2026-11-23.txt`; compatibility matrix updated.

Counts: primary 176/303 reviewed, 127 pending; supplemental net-new pending 177; primary + supplemental pending 304; manual additions 14, 2 pending; unresolved including manual 306. Next primary candidate: Hitesh-Sisara/agentic-keyvault. Claude Desktop third-party-gateway Chat/Cowork/Code remain separate tracks; local/self-hosted Claude Code remains distinct; “Destruction Era” spelling retained. Research is active/incomplete; no completion email sent.


## Candidate #177 — `Hitesh-Sisara/agentic-keyvault`: useful SecretPlane boundary only

Pinned current main `f39c1cf859e79a30b684291f1a2a599cc8527a96`. Cloudflare Workers + D1 credential vault with a Go CLI and stdio MCP server; its Projects group API keys/env secrets, not Harness Projects. Reject as a Project/Section/session/transcript or Claude Desktop Chat/Cowork/Code/local Claude Code migrator. Preserve secret values outside portable bundles and require target-side relinking. Source review found envelope encryption with a Worker-held KEK (server decrypts by design), project-scoped tokens, version history, and plaintext-returning MCP reads. A disposable synthetic test confirmed project-A writer + project-B repoId is accepted (201); classify as association integrity gap, not proven cross-project read access. Worker 28/28 tests; synthetic extension 29/29; typecheck and Wrangler dry-run build pass. Go/Bun missing; MCP package has no tests. Evidence: `research/evidence/hitesh-sisara-agentic-keyvault-review-2026-11-23.txt`.

Primary 177/303 reviewed, 126 pending; supplemental net-new 177 pending; combined 303; manual additions 14, two pending; unresolved 305. Next primary: `huqiwei123/agentkit`. Research active/incomplete.


## Candidate #178 — `huqiwei123/agentkit`: fail as a migrator and unsafe installer

At pinned HEAD `4a963eaa8b4a880d5e9042920f0c2877b8d63056`, it is a small resource registry + Codex/Claude file copier, not an archive/session migrator. The README advertises reusable skills, agents, commands, hooks, roles and MCP; source adapters have only `codex` and `claude`, and Claude omits MCP templates. Synthetic testing reproduced path traversal outside the requested target and a failed second write that left the first file behind. The bundled bootstrap profile names missing sample-skill; `validate`/`doctor` miss the broken reference, so install crashes. Keep only the basic resource/profile model as inspiration; do not run against untrusted resource trees. Worker? Python unit suite: 16/16 pass but misses these cases. Evidence: `research/evidence/huqiwei123-agentkit-review-2026-11-23.txt`.

Primary 178/303 reviewed, 125 pending; supplemental pending 177; combined 302; manual 14, two pending; unresolved 304. Next `Jaxz714/skills-hub`. Research active/incomplete.


## Candidate #179 — `Jaxz714/skills-hub`: useful Skill discovery only; update label bug

At pinned HEAD `2670bbb911b0182ba42cd243eed113fda1c5210e`, this is an alpha GitHub Skill search/clone/update/scaffold CLI for Claude Code, Codex, Cursor, `.agents` and generic Skills directories. It does not migrate sessions, projects, Sections, media, schedules, memory, or Claude Desktop 3P gateway modes. No test suite. A disposable local remote POC confirmed a successful update flips platform metadata from `codex` to `unknown`. CLI startup also creates all platform folders (observed in temp HOME); publish always uses `--public` in source. Keep as a low-priority Skill-plane reference, not a Nexus migrator. Evidence: `research/evidence/jaxz714-skills-hub-review-2026-11-23.txt`.

Primary 179/303 reviewed, 124 pending; supplemental pending 177; combined 301; manual 14, two pending; unresolved 303. Next `jondwillis/privacy-rights-plugin`. Research active/incomplete.


## Candidate #180 — `jondwillis/privacy-rights-plugin`: cross-Harness ResourcePlane only

One-commit Apache-2.0 plugin; manifest targets Claude Code, OpenCode, Codex, Cursor and OpenClaw with fallback directories. Not a conversation/project/session migrator. Committed dist files for all targets contain references to shared/email-templates, but no target packages those shared templates; README's Discover/Dashboard claims are also absent from the only three skills. Jacq is external/unpinned and missing in review environment; no tests. Keep only as a packaging-matrix reference; do not endorse legal claims without current primary legal review. Evidence: `research/evidence/jondwillis-privacy-rights-plugin-review-2026-11-23.txt`.

Primary 180/303 reviewed, 123 pending; supplemental 177; combined 300; manual 14 (2 pending); unresolved 302. Next `jp-999/dev-team`.

## Candidate #181 — `jp-999/dev-team`: canonical role source, no session graph

Pinned `d4b132ea32ccdafec64c7bfa6aa0de8e4aa081e4`. Source roles synchronize to Cursor and Claude Code, with a sequential CrewAI engine writing per-role files to `.devteam/`. `--plan` enumerated 11 roles; there is no transcript, parent/fork, Projects/Sections, attachments/tokens, or Claude Desktop 3P Chat/Cowork/Code adapter. Sync smoke passed in a disposable copy; no test suite and no full provider run. Synthetic upskill findings did not affect the static cycle-selected improvement. Keep only as a resource-plane/task-blackboard reference. Evidence: `research/evidence/jp-999-dev-team-review-2026-11-23.txt`.

Primary 181/303 reviewed, 122 pending; supplemental pending 177; combined 299; manual 14, two pending; unresolved 301. Next `kamalsrini17/mcp-client`. Research active/incomplete.

## Candidate #182 — `kamalsrini17/mcp-client`: reject keyword false positive

Pinned `98c224e6bb3dadc307ee9368ef2733c42195c0ec`. Two TypeScript files implement a generic Axios REST product-management workflow, not MCP JSON-RPC and not harness/session migration. Typecheck passed; synthetic loopback test observed six REST calls. No tests, no target adapter, and no projects/sections/session model. `localhost:3000` write entrypoint not run. Evidence: `research/evidence/kamalsrini17-mcp-client-review-2026-11-23.txt`.

Primary 182/303 reviewed, 121 pending; supplemental pending 177; combined 298; manual 14, two pending; unresolved 300. Next `kelegele/cli-butler`. Research active/incomplete.

## Candidate #183 — `kelegele/cli-butler`: Skill pattern only; unsafe writers

Pinned `2a44cb76ec357ec9b9d99002045fd55052536c56`. A local CLI management Skill with channel provenance, journal, dry-run safety and 184/184 isolated tests. Not a session/project or cross-Harness importer. Temp probes confirmed shell injection from an unvalidated package name and `.app` symlink removal without `.bak`, contrary to its requirements. Keep only its adapter/provenance/test-fixture ideas; do not reuse writers directly. Evidence: `research/evidence/kelegele-cli-butler-review-2026-11-23.txt`.

Primary 183/303 reviewed, 120 pending; supplemental pending 177; combined 297; manual 14, two pending; unresolved 299. Next `KingImperio/ctx`. Research active/incomplete.

## Candidate #184 — `KingImperio/ctx`: adjacent ResourcePlane, no sessions

Pinned `16ad7a730d57bb3a78e5531d3a6bcc3aeece365e`. Broad Skills/MCP/CLI registry and dual MCP/CLI interface; no SessionGraph/Project/Section, transcript, attachment or schedule import. 13 JS files pass syntax checks; no tests/lockfile. Temp probes confirmed path traversal during skill auto-import, partial write on a missing MCP registry, plaintext MCP env persistence, and `sync init` argument-type failure. Do not reuse current auto-import/sync writers on real user state. Evidence: `research/evidence/kingimperio-ctx-review-2026-11-23.txt`.

Primary 184/303 reviewed, 119 pending; supplemental pending 177; combined 296; manual 14, two pending; unresolved 298. Next `Kizuno18/dora-explores-binaries`. Research active/incomplete.

## Candidate #185 — `Kizuno18/dora-explores-binaries`: content portability only

Pinned `9af34d9f8246613064e1bcf9b74289a2b101301d`. One canonical, prompt-only `SKILL.md` has manual install paths for Claude Code, Codex, Cursor/Windsurf, generic LLM/API, ChatGPT Custom GPTs and Claude Projects. No session, project/section, transcript or Claude Desktop 3P-mode adapter. Plugin JSON parses; no runtime tests, only Markdown lint/link CI. Keep as a minimal Skills-plane packaging example, not a migration tool. Evidence: `research/evidence/kizuno18-dora-explores-binaries-review-2026-11-23.txt`.

Primary 185/303 reviewed, 118 pending; supplemental pending 177; combined 295; manual 14, two pending; unresolved 297. Next `Knaackee/linxmd`. Research active/incomplete.

## Candidate #186 — `Knaackee/linxmd`: useful artifact package pattern, not a migrator

Pinned `d831a3ac078bfd6322e87ba10bd860a52be2001f`. Installs local/GitHub agents, Skills, workflows and templates; renders agents for Copilot, Claude Code and OpenCode (Skills only Claude Code). No Project/Section/SessionGraph or transcript/media/token/schedule/memory migration. Disposable .NET 8 target-framework override test: 152/152; native .NET 10 target blocked by local SDK 8.0.129. Dynamic probes showed generated wrappers persist after removal and a synthetic skill name can escape the project. ResourcePlane reference only.

Primary 186/303 reviewed, 117 pending; supplemental pending 177; combined 294; manual 14, two pending; unresolved 296. Next `korakotlee/koharness`. Research active/incomplete.


## Candidate #187 — korakotlee/koharness: useful memory docs and capability sync, not a chat migrator

Pinned ada356b058f3b84b6abe54f0b17a1367031e038a. Versioned dotfiles repo, Skills/MCP/Antigravity workflows, and raw/wiki/AGENTS.md documentation. No ChatGPT/Codex Projects/Sections/Sessions or transcripts/events migration; Claude Desktop three modes are not adapter targets. Fifteen Go test packages pass with verified Go 1.24.0. Disposable tests reproduced Claude MCP target-path failure, unconditional AGENTS.md creation, and a synthetic environment value written back into tracked shared mcp/mcp.json. No LICENSE file/SPDX. Retain only as architecture reference pending security and licensing fixes.

Primary 187/303 reviewed, 116 pending; supplemental pending 177; combined 293; manual 14, two pending; unresolved 295. Next krishna-kudari/agent-skills-manager. Research active/incomplete.


## Candidate #188 — krishna-kudari/agent-skills-manager: 40+ Skills paths, no conversation migration

Pinned 9b11ae223bad40510b1cb9a81bea39c95521cd66, MIT Raycast extension. Skills from skills.sh/GitHub; symlink/copy, global lock, commit-hash update detection. No Projects/Sections/Sessions, transcript/media/token/scheduler/MCP/plugin/memory transfer; Claude Desktop Chat/Cowork/Code are not targets. The current UI forces global scope although README claims project scope. Type-check/lint/build pass, but there are no tests; dynamic probe found symlink dereference of outside-skill content and deletion of unmanaged target content. Skills-plane reference only.

Primary 188/303 reviewed, 115 pending; supplemental pending 177; combined 292; manual 14, two pending; unresolved 294. Next lakshay2395/employee-management-mcp-server-client-demo. Research active/incomplete.


## Candidate #189 — lakshay2395/employee-management-mcp-server-client-demo: MCP protocol demo only

Pinned 7bc698c446d0167eb49f3144490b62fbe96a2ad7. FastMCP HR/MySQL CRUD server, resource/prompt primitives and LangChain/Gemini SSE client. ClientSession is protocol state, not conversation history. No Project/Section/Session migration or cross-Harness adapters. Python syntax check passed; no tests, dependency lock, CI, or license. Unsafe demo defaults include root/empty password and 0.0.0.0 binding; not executed.

Primary 189/303 reviewed, 114 pending; supplemental pending 177; combined 291; manual 14, two pending; unresolved 293. Next Lartweib/dotai. Research active/incomplete.


## Candidate #190 — `Lartweib/dotai`: strong resource/config pack, not session migration

Pinned `36eabaec4d4a1d2e840d37c873f3054767be3860`, MIT. Multi-harness config packs for Claude Code CLI, Antigravity CLI and OpenCode. 15 Go test packages pass normally and with race; vet, module verification, gofmt, six rulesync E2Es, isolated CLI API-key/base-url pass-through and restore all pass. No Projects/Sections/SessionGraph/history migration or Claude Desktop mode target. ResourcePlane reference only. Evidence: `research/evidence/lartweib-dotai-review-2026-11-23.txt`.

Primary 190/303 reviewed, 113 pending; supplemental pending 177; combined 290; manual 14, two pending; unresolved 292. Next `lazyworkshop-create/skills-manager. Scope confirmation: Claude Desktop 3P covers Chat, Cowork and Code; local/self-hosted Claude Code CLI and Anthropic-hosted Cloud remain separate. Research active/incomplete.


## Candidate #191 — `lazyworkshop-create/skills-manager`: narrow Skills UX, not migration

Pinned `9d794f6491444b9705e0d0914092dd8552a972a1`; no license/tests/CI/lockfile. Copies Skills from wshobson/agents to VS Code, generic project or custom folder. Advertised Claude path is not current Desktop 3P app-managed Skills nor the `~/.claude/skills`/`.claude/skills` Code layout. No Projects, Sections, SessionGraph, MCP/plugins, memory, schedules or API-key flow. Fake-only probe found path traversal outside target, destination overwrite, symlink dereference; default update can invoke pip via shell. Reject for implementation; preserve only as UI reference. Evidence: `research/evidence/lazyworkshop-create-skills-manager-review-2026-11-23.txt`.

Primary 191/303 reviewed, 112 pending; supplemental 177; combined 289; manual 14, two pending; unresolved 291. Next `learnrudi/cli. Research active/incomplete.

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


## 2026-11-23 continuation — candidate #196 `mabyko/AgentHarnessManager`

MIT, native SwiftUI macOS app; pinned `e64249777df41377e93d5ce12a259d6fd264e4c5`. It is a serious local Skills/instruction and agent-config manager with reviewed operations and journal/rollback, not a conversation migrator. Its `SkillGroup.skillIDs` group installed resources; work profiles are resource/path snapshots, not ChatGPT/Codex Projects or Sections. No transcript/session/project/branch/attachment importer or Claude Desktop 3P mode writer. `swift test` passed 93 tests, Xcode app build passed, and isolated CLI/MCP/app-state checks passed. Keep as ResourcePlane safety/UX reference only. Evidence: `docs/research/evidence/mabyko-agentharnessmanager-review-2026-11-23.txt`.

Counts: primary **196/303 reviewed, 107 pending**; supplemental net-new pending **177**; primary + supplemental pending **284**; manual additions **15, 3 pending**; unresolved including manual **287**. Next primary candidate: `madshn/ai-playbooks`. Research remains active/incomplete; no completion email sent.


## 2026-11-23 continuation — candidate #197 madshn/ai-playbooks

MIT; main pinned b8f5897764f7c7c82dad47303972aeaf84c503f2. The single published 1p-creds Skill is a prompt-oriented workflow for moving credential values into 1Password Environments, with a Claude Code implementation only; Codex/Gemini ports are TBD. The README's “cross-harness” refers to environment inheritance, not portable sessions. No Project/Section/session graph, message/branch/attachment import, or Claude Desktop 3P adapter is present. Static review noted sensitive output and weak delete verification; no real credential interaction or functional test was run. Keep as an adjacent credential-hygiene reference, not migration code. Evidence: docs/research/evidence/madshn-ai-playbooks-review-2026-11-23.txt.

Counts: primary 197/303 reviewed, 106 pending; supplemental net-new pending 177; primary + supplemental pending 283; manual additions 15, 3 pending; unresolved including manual 286. Next primary candidate: magnumquest39-cloud/AntoSkills. Research remains active/incomplete.


## 2026-11-23 continuation — candidate #198 magnumquest39-cloud/AntoSkills

Pinned main d87ad2628e0f2840e25895f2af11cf064b47a3a7 (MIT). AntoSkills is a useful Skills ResourcePlane package manager for Claude Code/Codex, with a tested MCP server, immutable content pins, lock/store integrity and profile groups. It has no ChatGPT/Codex Project/Section/session graph, transcript/attachment/token/memory/schedule importer, or validated Claude Desktop 3P Chat/Cowork/Code adapter. Static code review found possible first-install clobbering because directory-name checks consult the lockfile only while linkSkill removes any real existing directory. Keep as an adjacent implementation reference, not a migration engine. npm package verification and isolated tests are documented in docs/research/evidence/magnumquest39-cloud-antoskills-review-2026-11-23.txt.

Counts: primary 198/303 reviewed, 105 pending; supplemental net-new pending 177; primary + supplemental pending 282; manual additions 15, 3 pending; unresolved including manual 285. Next primary candidate: marcm8793/skill-forger. Research remains active/incomplete; no completion email sent.


## 2026-11-23 continuation — candidate #199 marcm8793/skill-forger

Pinned main / tag v0.1.10 at 0cd67497e3dc9b92729ae8dcbf26514d9560f96e (MIT). skill-forger is a declarative skills.json wrapper over the Vercel Skills CLI, useful only as adjacent Skill ResourcePlane tooling. It contains no Project/Section/session graph or ChatGPT/Codex import/export, and has no Claude Desktop 3P Chat/Cowork/Code adapter. 36 tests and build checks pass but do not validate target imports; synthetic all-skills uninstall leaves the Skill file after removing config/lock state. npm integrity verified; source bundle reproducibility remains inconclusive. Full evidence: docs/research/evidence/marcm8793-skill-forger-review-2026-11-23.txt.

Counts: primary 199/303 reviewed, 104 pending; supplemental net-new pending 177; primary + supplemental pending 281; manual additions 15, 3 pending; unresolved including manual 284. Next primary candidate: mazen160/skills-manager. Research remains active/incomplete; no completion email sent.


## 2026-11-23 continuation — candidate #200 mazen160/skills-manager

Pinned main 9bb8d40f77701ceb02dd15f49430c45dd04b8166 (MIT, package/PyPI 1.0.4). Strong adjacent security scanner/installer for global Skills across Claude, Cursor, Codex and OpenCode; not a ChatGPT/Codex Project/Section/session importer and not a Claude Desktop 3P Chat/Cowork/Code writer. Main's 155 tests passed; PyPI wheel module exactly matches Git main but PyPI has no provenance and GitHub release metadata lags the 1.0.4 package.

A draft, unmerged scanner PR adds richer static analysis and recursive archive scanning; its 176 tests and CI pass. A synthetic TAR with 1,001 entries showed the PR misses a malicious final member without reporting truncation; a synthetic failure in the shared atomic copy rollback path lost the old destination after both replacement and restore renames failed. Useful ResourcePlane safety concepts only, not migration code. Evidence: docs/research/evidence/mazen160-skills-manager-review-2026-11-23.txt.

Counts: primary 200/303 reviewed, 103 pending; supplemental net-new pending 177; combined pending 280; manual additions 15, 3 pending; unresolved including manual 283. Next primary candidate: mejbaurbahar/awesome-qa-agent-skills. Research remains active/incomplete.

## 2026-11-23 continuation — candidate #201 mejbaurbahar/awesome-qa-agent-skills

Pinned current main 1665963f605ceecb2ee14aea140a704c2046cae8 (MIT). The 194-Skill QA/PM collection has useful source/license/commit records and working catalog/install smoke for Claude Code and Antigravity, but it is not a chat/session/project migrator and has no Claude Desktop third-party-gateway Chat/Cowork/Code writer. Synthetic uninstall probes deleted a replaced installed path and a manifest-listed outside-root temp directory; source refresh also removes old files before validating replacements. Keep only as a low-priority ResourcePlane content reference. Full evidence: evidence/mejbaurbahar-awesome-qa-agent-skills-review-2026-11-23.txt.

Counts: primary 201/303 reviewed, 102 pending; supplemental net-new pending 177; combined pending 279; manual additions 15, 3 pending; unresolved including manual 282. Next primary candidate: miles990/skillpkg. Research remains active/incomplete.

## 2026-11-23 continuation — candidate #202 miles990/skillpkg

Pinned main 8ec9655e8267e1fe9b37a4edc488c16f591233e7; README marks it archived/superseded. It is a useful historical Skill/MCP resource manifest and serializer for Claude Code, Cursor, Codex and Copilot, not a Project/Section/session migrator. The CLI has no standalone sync or migrate command despite README/MIGRATION.md guidance. Local tests 259/261; build/typecheck pass, lint fails. POCs show cleanup deleting unowned skill dirs, MCP config overwrite, path traversal through unvalidated Skill names, same-count stale asset sync, and Codex Skill import misclassification/loss of references. Do not reuse its writer; retain only resource-model ideas. Full evidence: evidence/miles990-skillpkg-review-2026-11-23.txt.

Counts: primary 202/303 reviewed, 101 pending; supplemental net-new 177; combined pending 278; manual additions 15, 3 pending; unresolved including manual 281. Next primary candidate: MlsMoon/moon-game-dev-tool-manager. Research remains active/incomplete.

## 2026-11-23 continuation — candidate #203 MlsMoon/moon-game-dev-tool-manager

Pinned `develop` at `f204cb9271954895200a92c282f71ffdb963997b` (MIT; Windows WPF; latest Release v0.2.5). This is a catalog/installer for MlsMoon Agent Skills and Unity Plugins/Packages, not a Project/Section/session graph migrator. It has no conversation/session/task/fork hierarchy, transcript, attachment, token, memory, schedule or Claude Desktop 3P Chat/Cowork/Code adapter. Keep only as a low-priority ResourcePlane reference.

Source-path review found ordinary Skill install names are joined into `.agents/skills/<id>` without containment validation, and `SkillCopy.Replace` recursively deletes any existing non-Git destination without requiring an ownership marker. A synthetic Core probe confirmed both deletion of an unmarked colliding Skill folder and traversal with `id=../../../escaped-skill` to an unmarked directory outside the disposable workspace; only synthetic temp data was used. Plugin/Package install paths have a separate workspace-containment check. Original local tests could not compile on SDK 8.0.129 due eight ambiguous C# 12 `string.Split` overloads; an isolated compatibility copy reached 21 passed / 3 macOS path-assumption failures. The pinned commit's official Windows CI run #18 is green; this is not a claimed upstream CI failure. Detailed source, exact outputs and limits: `docs/research/evidence/mlsmoon-moon-game-dev-tool-manager-review-2026-11-23.txt`.

Disposition: reject as a core Nexus Memory migration engine; consider catalog UX only after implementing path containment, ownership-aware staged writes, and rollback. Primary **203/303 reviewed, 100 pending**; supplemental net-new pending **177**; combined pending **277**; manual additions **15, 3 pending**; unresolved including manual **280**. Next primary candidate: `mocikadev/mocika-samsara`. Claude Desktop targets remain separately tracked as 3P Chat, Cowork and Code, plus local/self-hosted Claude Code; Anthropic-hosted Cloud is outside that local target. Research remains active/incomplete; no completion email sent.

## 2026-11-23 continuation — candidate #204 mocikadev/mocika-samsara

Pinned `main` at `4de9564444e235164ea3e1b4443b4478866627a1` (2026-05-30; `samsara` v1.0.0; MIT OR Apache-2.0). Samsara is a local-first Markdown knowledge/experience manager with typed error/skill/pattern/insight lessons, promotion to rules, Git sync, a six-tool stdio MCP server, an OpenCode prompt-injection plugin, and selected instruction/config setup. Keep as a strong Memory/ResourcePlane reference, not a Projects/Sections/SessionGraph migration engine: no session/task/parent-child/fork/message/transcript/attachment/usage/schedule import/export was found, and its README migration is AI-batched or manual lesson writes. The MCP server's `write_lesson` is a content writer, not a session importer; no Claude Desktop 3P gateway/mode writer was found.

Local checks passed: 46 tests across 8 suites, `cargo fmt --check`, clippy `-D warnings`, and locked release build. Official CI #20 at the reviewed commit and release v1.0.0 are green/current. Isolated release-binary POCs reproduced path traversal through raw lesson `domain` and `keyword`, creating synthetic files outside a temp knowledge root; a fake-home `--dry-run init` also created directories. A fake-home normal init preserved unrelated MCP servers and was idempotent, but does not establish live Desktop compatibility. `push`/auto-commit use `git add -A` with no secret filtering visible; do not place API keys in the store. Full sources, outputs and caveats: `docs/research/evidence/mocikadev-mocika-samsara-review-2026-11-23.txt`.

Primary **204/303 reviewed, 99 pending**; supplemental net-new pending **177**; combined pending **276**; manual additions **15, 3 pending**; unresolved including manual **279**. Next primary candidate: `pewpewgogo/agentcrew`. Claude Desktop targets remain all three third-party-gateway modes (Chat, Cowork, Code), separate from local/self-hosted Claude Code and Anthropic-hosted Cloud. Research remains active/incomplete; no completion email sent.

## 2026-11-23 continuation — candidate #205 pewpewgogo/agentcrew

Pinned `main` at `5af3a362fc1c37834ad0c60c8d3d2d6bb84c65e5` (2026-06-01; MIT; v0.1.0). AgentCrew is a team Project → Milestone → Task manager with per-project repos/URLs/tech-stack/notes and an append-only human/agent context log exposed through REST, MCP and CLI. This is a useful shared-work-context reference, not a ChatGPT/Codex Project/Section or Claude Desktop Chat/Cowork/Code SessionGraph importer. Context records are only a target type/id, author kind, timestamp and plain note; there are no conversation/session/message IDs, parent/fork topology, attachments, token usage or schedule importers. The `cs_s_` session token is an app auth token, not a chat session; `cs_k_` is an AgentCrew API key, not a provider key.

Build and lint pass. Six explicit non-DB suites (16 tests) pass. Full 29-file Vitest run could not initialize 23 DB-backed suites because Docker/PostgreSQL were unavailable and `localhost:54329` refused connections; do not call it a passing full suite. A fake-only writer probe showed the Claude Code MCP API bearer key is written plaintext into a newly created `~/.claude.json` file with mode 0644 under this environment's default umask (while `~/.agentcrew/config.json` is chmod 0600). No real token, server, or user config was used. The repo has no CI workflow or GitHub release. Detailed schema/source/outputs and limitations: `docs/research/evidence/pewpewgogo-agentcrew-review-2026-11-23.txt`.

Disposition: keep only as a project/task context and append-only provenance design reference; reject as a session migration engine. Primary **205/303 reviewed, 98 pending**; supplemental net-new pending **177**; combined pending **275**; manual additions **15, 3 pending**; unresolved including manual **278**. Next primary candidate: `Predator404/aiToolManager`. Claude Desktop 3P Chat/Cowork/Code remain separately tracked from local/self-hosted Claude Code and Anthropic-hosted Cloud. Research remains active/incomplete; no completion email sent.

## 2026-11-23 continuation — candidate #206 Predator404/aiToolManager

Pinned `main` at `1d331d49ddc6e83b27fa521ace1a59ee4dd7ff2d` (2026-08-22; Node CLI/TUI v0.1.0). This is a strong **resource/config-plane** reference for OMP (oh-my-pi), Claude Code and Prime Agent: canonical `.agents` Skill/Command store, per-harness native symlink mirrors, scoped native MCP/extension/hook handling, and metadata. Its project scope is a filesystem project root, not a ChatGPT Project/Section; it has no conversation SessionGraph or session/message/transcript/attachment/token/schedule importer/exporter. It omits ChatGPT/Codex and Claude Desktop 3P Chat/Cowork/Code. Package is private and checkout has no license declaration/README/LICENSE, so code reuse is not cleared.

Quality: all 100 tests across 10 files pass; TypeScript typecheck passes; CLI help exposes only resource/config categories. Isolated POCs found: `skill enable` deletes an unowned real directory at a mirror path; same-name `skill import` silently replaces an existing canonical folder; promote compares only `SKILL.md` then deletes global-only assets if that file matches; atomic MCP JSON rewrite changed `.claude.json` from 0600 to 0644 while storing a synthetic bearer key. A simulated Windows path check also shows backslash `..` segments accepted by the current slash-only validator (no Windows runtime test). Full evidence and exact outputs: `docs/research/evidence/predator404-aitoolmanager-review-2026-11-23.txt`.

Disposition: retain the native per-harness config-adapter and sidecar concepts only; do not use as SessionGraph migration engine or copy its unsafe writer without ownership, whole-tree conflicts, Windows-safe paths, staging/rollback and permission preservation. Primary **206/303 reviewed, 97 pending**; supplemental net-new pending **177**; combined pending **274**; manual additions **15, 3 pending**; unresolved including manual **277**. Next candidate: `pyhu26-public/agent-moringgroove`. Research active/incomplete; no completion email sent.


## Candidate #207 — pyhu26-public/agent-moringgroove: local Code UI, not migrator

| Source/target capability | Observed |
|---|---|
| Session UI | One or more folder Agents, each with native Claude Code `sessionId`; web chat and herdr PTY share/resume that same local session. |
| Transcript/history | Native files live in `~/.claude/projects`; `/api/chat/history` is limited to 200 and is lossy, not import/export. |
| Project/Section/SessionGraph | No ChatGPT/Codex model or migration API; project means filesystem folder. No session tree/fork/attachment/usage/schedule archive. |
| Claude Desktop 3P modes | No adapter for Chat, Cowork, or Code. |
| Quality/security | `npm ci` fails on out-of-sync lockfile; unlocked install + 30 tests/build pass. POCs found docs symlink escape, mode-0644 plaintext MCP env and recursive Skill deletion. No license evidence. |

Disposition: keep as local Claude Code UX reference only. Full evidence: `research/evidence/pyhu26-public-agent-moringgroove-review-2026-11-23.txt`.


## Candidate #208 — qingyunk/skill-manager: Kimi Skill plane only

| Capability | Observed |
|---|---|
| Kimi resource plane | One Kimi plugin Skill plus local Node CLI for list/show/validate/new/install/disable/enable; scans Kimi user/project/extra/plugin and generic `.agents/skills`. |
| Session/Project/Section migration | None in this repo. Kimi's separate native CLI supports recent Claude Code/Codex session import and session ZIP/Markdown export, but not documented ChatGPT import. |
| Interoperability value | Kimi Plugin Builder officially converts Claude/Codex manifests, MCP registry JSON, marketplaces and Skill-only repositories. Keep this platform capability distinct from `skill-manager`. |
| Safety | `.. --force` erased fake KIMI_CODE_HOME; escaping plugin `skills` path displayed outside sentinel. Official Kimi plugin spec requires realpath containment. |

Disposition: low-priority Skill ResourcePlane reference only; never core migration implementation. Full evidence: `research/evidence/qingyunk-skill-manager-review-2026-11-23.txt`.


## Candidate #209 — `Rafa-Innerchispa/inneros-personal-brain`: memory plane, not session migration

Pinned `main` / `origin/main` at `c0f899bdde77eb25b555878a44f1764861199308`. The 12-route FastAPI personal-brain service stores curated evidence/outcomes into shared Cognee memory and uses Bright Data/Strands/local Qwen; no source conversation/session graph, ChatGPT/Codex Project or Section import, or Claude Desktop 3P mode writer was found. Twenty-three isolated tests pass, but fake-client probes reproduced direct uncurated memory writes of a synthetic key/private path; curation misses synthetic email, AWS-like key and macOS path examples. No detected license; no code reuse as migrator. GitHub PR #5 is still open; its author reports 48 curated seed facts and live recall, but that PR is not merged and its source diff was not independently audited here. Review: `research/evidence/rafa-innerchispa-inneros-personal-brain-review-2026-11-23.txt`.

Primary inventory **209/303 reviewed, 94 pending**. Next primary candidate: `RafaelQSantos-RQS/MyAgentControl`.


## Candidate #210 — `RafaelQSantos-RQS/MyAgentControl`: OpenCode resource installer only

Pinned `92b3fd6bffcf6b2d255cd26052d1b53e190d8889` (main, 2026-08-30). 248 static registry components and five installer profiles for an OpenCode-compatible `.opencode/` tree; no ChatGPT/Codex Projects, Section Groups, session/transcript graph or Claude Desktop 3P target. Local tests 120/120, fmt, Clippy and release build pass; pinned GitHub CI green. Synthetic symlink-parent POCs demonstrated write-outside-root, manifest appropriation of a colliding foreign file, and deletion of that file before a failing cleanup exit. Keep profile/manifest design as a ResourcePlane reference but reject this implementation's writer/remover. Full evidence: `research/evidence/rafaelqsantos-rqs-myagentcontrol-review-2026-11-23.txt`.

Primary inventory **210/303 reviewed, 93 pending**; next `ramon-sg/agent-skills`.


## Candidate #211 — `ramon-sg/agent-skills`: reusable Skill catalog, not a migrator

Pinned `f0d7da8867dc9939b647d5d9c428adff77b81a18`, 2026-11-21. Five polished Spanish Skills with `SKILL.md`, `skills-catalog.json` dependencies, editable per-repo `project.md` overlays, an integrity-locking external manager, and a local HTML preview server. `npm ci` succeeds; `npm test` is 20/20 when `CODEX_CI` is unset. The README's default `.agents/skills/` install and Claude-cloud claim are not validated against Anthropic's documented `.claude/skills/` project/local path or Claude-account-synced Cowork/cloud Skills. Keep as a strong ResourcePlane/cross-platform content example, not a Projects/Sections/session importer or verified Claude Desktop 3P adapter. Full evidence: `research/evidence/ramon-sg-agent-skills-review-2026-11-23.txt`; official path evidence: `research/evidence/agent-skills-standard-runtime-paths-2026-11-23.txt`.

Primary inventory **211/303 reviewed, 92 pending**.

Next primary candidate: `ricardosalcedo/agentpack` (#212).


## Candidate #212 — `ricardosalcedo/agentpack`: dependency manager, not history migrator

Pinned `07b11d6bd182c533ac5a9c7093fb594670c7759b`, MIT. AgentPack has a useful manifest/lock model for MCP/agent dependencies, versions, profiles, transports and capability contracts, plus a narrow Claude Desktop `mcpServers` JSON export to the current working directory. It does not represent Project/Section/session ancestry, messages, attachments, token usage, or Claude Desktop 3P per-mode local state. Rust gates: 23/23 tests pass only when serialized; the parallel run reproduced global-CWD race failures (19/23, exit 101). Disposable code probes confirmed JS injection via unescaped `--command` interpolation and project-manifest overwrite via `fetch ..`; reject those writers pending fixes. Evidence: `research/evidence/ricardosalcedo-agentpack-review-2026-11-23.txt`.

Primary inventory **212/303 reviewed, 91 pending**. Next primary candidate: `roedyrustam/ctxbridge` (#213), a cross-agent memory/context bridge queued for pinned source review.


## Candidate #213 — `roedyrustam/ctxbridge`: useful memory plane, not a session migrator

Pinned `9c03ce2da94ac38eaec2beef964d16e0c3cbf534`, MIT v0.2.0. Local project/global SQLite memory stores, MCP operations, instruction-file adapters, JSONL snapshots and compact handoff capsules make this a strong adjacent memory-plane reference for five coding harnesses. It does not import ChatGPT/Codex Project/Section/session hierarchies or Claude Desktop 3P Chat/Cowork/Code transcripts. A synthetic import regenerated record IDs/timestamps/hashes/token estimates, and a symlink probe made `sync` write outside the selected project. `cargo audit` flags bundled `libsqlite3-sys 0.30.1` CVE-2026-119375 (conditional on opening an untrusted crafted DB/WAL) and unmaintained `chrono`. Keep the memory/schema/capsule ideas; do not reuse its importer/writer without provenance and path-safety changes. Evidence: `research/evidence/roedyrustam-ctxbridge-review-2026-11-23.txt`.

Primary inventory **213/303 reviewed, 90 pending**. Next: `Saber5656/skillet` (#214).


## Candidate #214 — `Saber5656/skillet`: strong design, no software implementation

The pinned `4d42851c5281a5604e32befb16fa8dfadd584d94` snapshot is a detailed 54-file, 4,502-line documentation contribution planning a safe `@skillet/cli` Agent Skills package manager. It proposes versioned indexes/locks, integrity, consent, no code execution, filtered Git tree extraction, receipts, rollback and 40 issue gates. It does **not** contain the CLI, tests, package manifest, CI, releases, or a declared license. GitHub shows 40 open implementation issues and no workflow runs/releases. v1 handles local Skills for Claude Code/Codex only; Projects, Section Groups, sessions, transcripts, attachments, MCP/plugins and Claude Desktop 3P modes are outside scope. Codex path assumptions differ across current official sources (`.agents/skills` vs `.codex/skills`). Keep as a security/design checklist, not a runnable migrator. Full evidence: `research/evidence/saber5656-skillet-review-2026-11-23.txt`.

Primary inventory **214/303 reviewed, 89 pending**; next candidate: `saturnarians/ctx-manager` (#215).

## Candidate #215 — `saturnarians/ctx-manager`: context ledger only

| Capability | Observed |
|---|---|
| Product | Python CLI + MCP stdio server for Markdown header slicing, phase selection and `Memory_Ledger.md` summaries. |
| Project/Section/Session migration | None: no transcript/event graph, session ancestry, source IDs, attachments, tool results, token accounting, schedules or target-native resume IDs. |
| Tests/build | 21 tests pass on Python 3.14.3 and 3.12.4; source/wheel build succeeds. Tests omit MCP path containment and concurrency. |
| Synthetic safety findings | `query_slice` read outside `Docs/`; config-controlled ledger write escaped project root; CLI/MCP phase results diverge; dirty-file count can label an unrelated claim “Verified”; forced 12-writer race lost 11 entries. All probes used `/tmp` synthetic data only. |
| Release/dependency note | GitHub main `0112b8c...` phase fix is absent from same-version PyPI 0.2.0; audit reports 25 dependency advisories, not all shown reachable on stdio. |
| Claude destination | No Claude Desktop 3P Chat/Cowork/Code or local Claude Code session importer; no HTTP/API-key gateway. |

Disposition: keep only its Markdown slicer / compact handoff-ledger pattern as a low-priority context reference. Do not use its writers as-is; require path containment, robust concurrent append, and honest verification semantics. Full evidence: `research/evidence/saturnarians-ctx-manager-review-2026-11-23.txt`.

Primary inventory **215/303 reviewed, 88 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Next primary candidate: `sefas-labs/ai-skills-manager` (#216).

## Candidate #216 — `sefas-labs/ai-skills-manager`: Skills ResourcePlane, not history migration

| Capability | Observed |
|---|---|
| Skill inventory | Visibility matrix across Claude Code, Cursor, Codex and Copilot local/workspace paths; diagnostics for duplicates, invalid frontmatter, broken links; extra user-configured locations. |
| Install/update safety | Exact commit/tree provenance, bounded staging, symlink/submodule skip, path validation, heuristic review, explicit overwrite consent, recoverable backups and rollback. |
| Session/Project/Section plane | None: no ChatGPT/Codex Project or Section Group, conversation graph, branches/subtasks, tool results, media, token/cost, schedules, memory or resume/import API. Claude adapter is Claude Code Skills only; no Desktop 3P Chat/Cowork/Code session writer. |
| Local gates | `npm ci --ignore-scripts`, 57/57 tests, typecheck, build and 1/1 smoke pass. Live editor E2E not rerun because its script scans real home Skills and contacts GitHub; manual dialogs are listed as pending upstream. |
| Dependencies/status | `npm audit`: 7 dev/build package records (2 high, 5 moderate); production audit 0; no fixes applied. GitHub: MIT, 0 stars/forks, 1 open PR, 0 issues/releases, one PR CI failure attributed to runner capacity/internal service error. |

Disposition: strong ResourcePlane/reference UX; do not choose as a session migrator. Do not treat its author-dated market analysis as a comprehensive market survey. Full evidence: `research/evidence/sefas-labs-ai-skills-manager-review-2026-11-23.txt`.

Primary inventory **216/303 reviewed, 87 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Next primary candidate: `shqear93/mcp-manager` (#217).

## Candidate #217 — `shqear93/mcp-manager`: reject current writers; no session migration

| Capability | Observed |
|---|---|
| Product | Node CLI registry for MCP source directories; symlink/copy into six agent config formats; `experimental_lock/restore`. |
| Session/Project/Section transfer | None: no histories, message trees, Project/Section Groups, branches, attachments, tokens, schedules, MCP tool history or resume IDs. No Claude Desktop 3P Chat/Cowork/Code adapter. |
| Validation | `npm run check` is syntax-only; `npm run smoke` prints help. No test script/files or CI/release evidence. |
| Synthetic writer findings | Registry add/remove path escape; outside sentinel deletion; name collision recursively deletes registry data without consent/backup; project mode still writes global config; supplied secret is stored plaintext in mode-0644 config; remote URL omitted; “restore” only checks path presence. |
| Harness adapters | Codex base path plausible; Claude, Cursor, Kimi and Cline paths/schema mismatch current client docs; Aider native MCP support is not established. |

Disposition: reject source code for current writes. The registry concept is only a low-level idea; reimplement with validated names, containment, ownership manifests, staging/rollback, secure secret handling and versioned adapter tests. Full evidence: `research/evidence/shqear93-mcp-manager-review-2026-11-23.txt`.

Primary inventory **217/303 reviewed, 86 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Next primary candidate: `simonwu53/agent-skills` (#218).


Primary inventory **217/303 reviewed, 86 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Next primary candidate: `simonwu53/agent-skills` (#218).

## Candidate #218 — `simonwu53/agent-skills`: Skill library, not session migration

| Capability | Observed |
|---|---|
| Product | Bash manager for Git-submodule/local/ZIP Skill sources, config.yaml categories/pins, copy/symlink install and submodule sync. |
| Session/Project/Section transfer | None; no transcript, Project/Section identity, SessionGraph, turns/events, branches, attachments, tokens/cost, memory/schedules, MCP/plugins or resume IDs. |
| Claude 3P coverage | One generic `~/.claude/skills` / project `.claude/skills` map; no mode-specific Chat/Cowork/Code reader/writer. Current official docs keep Desktop app-managed Skills distinct from Code filesystem Skills. |
| Validation | Offline temporary `test/smoke_test.sh`: 47 passed, 0 failed. No Actions workflow or unit suite. |
| Safety | Synthetic explicit selector `../../../../../outside` escaped the registered repository and installed an outside temp SKILL.md. Default clear and `--update` are destructive target replacements without rollback receipts. ZIP traversal not reproduced on this platform. |

Disposition: low-priority ResourcePlane reference only; reject its selector and overwrite semantics for a trusted migration writer. Evidence: `research/evidence/simonwu53-agent-skills-review-2026-11-23.txt`.

Primary inventory **218/303 reviewed, 85 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 262, including manual pending 265. Next primary candidate: `sjmgarnier/skill-manager` (#219).


Primary inventory **218/303 reviewed, 85 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Next primary candidate: `sjmgarnier/skill-manager` (#219).

## Candidate #219 — `sjmgarnier/skill-manager`: Skills workflow, not SessionGraph

| Capability | Observed |
|---|---|
| Product | AI-invoked `SKILL.md` + Bash/Python helper scripts to install/update GitHub Skills via `gh skill` or `npx skills`, with a local repo registry. |
| Session/Project/Section transfer | None: no source Project IDs, Section Groups, session/message tree, branch/task links, attachments, token/cost ledger, MCP event history or target resume IDs. |
| Interop finding | `detect-platform.sh` maps `$HOME/.agents/` to Warp; current official Codex user Skills use `~/.agents/skills/`. A synthetic detector run at that path printed `warp`; user confirmation mitigates but does not correct the default identity. `SKILL.md` also states an older/different Codex path. |
| Validation | 23 Bats tests declared but not run (Bats absent); `bash -n` passes and synthetic registry/update probes pass. GitHub CLI 2.96 supports the described commands. No workflow/release/license found. |

Disposition: keep only as an adjacent ResourcePlane reference; no session migration value. Evidence: `research/evidence/sjmgarnier-skill-manager-review-2026-11-23.txt`.

Primary inventory **219/303 reviewed, 84 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 261, including manual pending 264. Next primary candidate: `stevengonsalvez/reflect-kb` (#220).


Primary inventory **219/303 reviewed, 84 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Next primary candidate: `stevengonsalvez/reflect-kb` (#220).

## Candidate #220 — `stevengonsalvez/reflect-kb`: archived derived-memory reference

| Capability | Observed |
|---|---|
| Repository state | Archived on 2026-05-18; pinned tree is docs-only after source removal. MIT, 22 commits, 0 stars/forks, 0 issues, one open Renovate PR, no release. |
| Described data | Local Markdown learnings, hash-based document ID, entity sidecars, GraphRAG/QMD search and optional Git-backed KB. This is a curated MemoryPlane, not conversation history. |
| Session/Project/Section | None in the archived documentation. No export reader, source IDs, session hierarchy, turns/branches, media, tokens, schedules or resume IDs. |
| Validation | No source, package manifest or tests remain. CI currently references `pip install -e .[dev]`/`pytest`; the archive run was cancelled and preceding CI runs failed. No implementation was tested. |
| Scope distinction | Custom `~/.claude/global-learnings/` (also docs mention `~/.learnings/`) is distinct from Claude Code Auto Memory and local session JSONL. |

Disposition: keep only for MemoryPlane retrieval/metadata ideas; never replace immutable source SessionGraph with summaries. Evidence: `research/evidence/stevengonsalvez-reflect-kb-review-2026-11-23.txt`.

Primary inventory **220/303 reviewed, 83 pending**; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 260, including manual pending 263. Next primary candidate: `summer-via/skill-package-manager` (#221).


## Candidate #221 — summer-via/skill-package-manager (2026-11-24)

| Capability | Review |
|---|---|
| Product | MIT TypeScript/Git Skill package manager; skill.json, dependency refs, install/update/remove, copies or symlinks into ~/.agents/skills. |
| Session/project transfer | None: no ChatGPT/Codex project/section/session reader, event graph, attachments/media, tokens/cost, scheduling, MCP/plugins or target resume IDs. |
| Test/build | npm run build passed. No test script and no tests/ directory. |
| Safety | Synthetic-only remove ../../sentinel deleted a sibling fixture; install target collision deleted an unmanaged sentinel before writing. |
| Decision | Reject as a writer; retain only lockfile/ref vocabulary as low-priority resource-plane prior art. |

Pinned master f303dfbcc7248a84d1ea88afc111d87d4951b23a; full note: research/evidence/summer-via-skill-package-manager-review-2026-11-24.txt.

Primary inventory 221/303 reviewed, 82 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 259, including manual pending 262. Next primary candidate: sunven/skills-box (#222).


## Candidate #222 — sunven/skills-box (2026-11-24)

| Capability | Review |
|---|---|
| Product | macOS-first Tauri desktop manager for Skills, local project scopes and Claude/Codex CLI plugin operations. |
| Coverage | Vendored agent catalog has 79 definitions; projects are local folders. No ChatGPT/Codex Project/Section/session transfer, transcript graph or Desktop 3P Chat/Cowork/Code adapters. |
| Tests/build | pnpm 540/540; frontend build passed; Rust suite full rerun 896 passed / 31 ignored after one earlier AppUpdateBusy failure. |
| Audit/distribution | Production pnpm audit clean via official registry; one high dev advisory; cargo audit 2 vulnerable versions + 8 warnings. GitHub v0.1.9 release is macOS Apple Silicon only. |
| Decision | Useful ResourcePlane/UI patterns only. No declared license means no source reuse; snapshots also have no restore workflow. |

Pinned main 9ab4b1e15ba99fb7297423266d4b409dc4f931ce; current GitHub v0.1.9 release is later/active. Full review: research/evidence/sunven-skills-box-review-2026-11-24.txt.

Primary inventory 222/303 reviewed, 81 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 258, including manual pending 261. Next primary candidate: suqiangqiang2012-dot/agent-skill-manager (#223).


## Candidate #223 — suqiangqiang2012-dot/agent-skill-manager (2026-11-24)

| Capability | Review |
|---|---|
| Product | Versioned Agent Skill catalog/release manager with check, install, backup, rollback, and separately approved publish. |
| Targets | Codex Windows/macOS and WorkBuddy Windows 5.5.4+. Claude Code, Cursor, OpenClaw, DeepSeek Harness and WorkBuddy macOS are planned/unsupported. |
| Session migration | None: no Projects, Section Groups, chat/session history, event graph, attachments, MCP/plugins, memory, schedules or native-resume state. |
| Compatibility risk | Default Codex directory .codex/skills differs from current official .agents/skills and ~/.agents/skills; synthetic path probe reproduced mismatch. |
| Quality | 15 tests pass; stable releases, hashes, safe ZIP extraction, staged install, backups, exact confirmation tokens. No declared license. Live public install was blocked by no-auth GitHub 403, not by a user-data error. |
| Decision | Keep lifecycle concepts only, not source code and not as a migrator. |

Pinned main e606f9604d675450a47c54ccad240a7902eaf298; v0.3.0 release is stable. Full note: research/evidence/suqiangqiang2012-dot-agent-skill-manager-review-2026-11-24.txt.

Primary inventory 223/303 reviewed, 80 pending; supplemental 177 pending; manual 15 total / 3 pending; primary+supplemental pending 257, including manual pending 260. Next primary candidate: theonepichael/agent-toolkit (#224).


## Candidate #224 — theonepichael/agent-toolkit (2026-11-24)

| Capability | Review |
|---|---|
| Product | MIT cross-harness workflow toolkit (Claude Code, Copilot CLI, OpenCode, Antigravity, Pi, Codex CLI) with local transcript/cost analytics. |
| Session representation | Lossy `SessionRecord`: text, token/cost metadata, timestamp/cwd/session ID, boolean subagent. It does not preserve raw event order, parent/fork links, tools/results/permissions, attachments or target resume identifiers. |
| Project/Section migration | No reviewed ChatGPT/Codex Project or Section Group importer/transformer, nor target native restore writer. |
| Claude Desktop 3P | No Chat/Cowork/Code mode store adapter. CLI session reader is separate from the three user-confirmed Desktop modes and the local/self-hosted CLI profile. |
| Test evidence | Three suites passed (204 tests total); a separate 130-test queue-runner suite had 2 failures and 1 error on macOS `/tmp` → `/private/tmp`; the CI matrix is Ubuntu-only; full `uv run pytest` unavailable. |
| Decision | Keep local parsers/usage/cost/diagnostic patterns as observability prior art only, not as a canonical archive or migrator. |

Pinned `main` `5daf67975c8ffac3241b49341edbc76f3350820f`; MIT. Full note: `research/evidence/theonepichael-agent-toolkit-review-2026-11-24.txt`.

Primary inventory 224/303 reviewed, 79 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 256, including manual pending 259. Next primary candidate: `timianmalloo/x-harness-x-model-bench` (#225).


## Candidate #225 — timianmalloo/x-harness-x-model-bench (2026-11-24)

| Capability | Review |
|---|---|
| Product | Apache-2.0 harness × model × pack coding-agent benchmark; each cell uses its own native harness process/home and working copy. |
| Related data | Cross-harness native readers, selected token/model/tool/error/reasoning/prompt facts, append-only ledger, verified cell archives. |
| Migration fit | No source Project/Section/session import/export or target conversation restore. Run-level resume is benchmark recovery only. `Extraction` is lossy versus full message/media/session graph. |
| Tests | 518 passed, 1 skipped, 1 failed in focused reader/archive/resume/view groups. Failure is Grok path separator normalization on macOS; full CI ring not run. |
| Decision | High-value observability/archive-integrity prior art, not a session migrator. |

Pinned `main` `560d2fae9eaebb6450ab33b752df6ca288b5de6e`; Apache-2.0. Full evidence: `research/evidence/timianmalloo-x-harness-x-model-bench-review-2026-11-24.txt`.

Primary inventory 225/303 reviewed, 78 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending; primary+supplemental pending 255, including manual pending 258. Next primary candidate: `toshon-jennings/agent-advisor` (#226).

## Candidate #226 — toshon-jennings/agent-advisor (2026-11-24)

| Capability | Review |
|---|---|
| Product | MIT hub for selective routing (solo/delegate/audit/full) across Codex, Claude Code and Antigravity, with one-way platform-plugin/config export to separate spokes. |
| Session/project migration | None found: no ChatGPT/Codex Projects, Section Groups, conversation/event import/export, attachments, cross-session links, or native-resume writer. Agent “projects/specs” are not transcript hierarchy. |
| Useful prior art | Manifest-driven spoke sync with destination identity/path/type/symlink/dirty/ignored-file guards, preflight and revalidation, native validators, post-write drift equality and scoped rollback. Strong ResourcePlane/export safety only. |
| Transaction limits | Explicitly leaves TOCTOU risk; rollback is per-spoke after mutation starts, so a multi-spoke operation can finish mixed/partial. Do not claim atomic commit. |
| Verification | No hub tests/ suite; CI workflow validates platform trees, generated outputs, shell syntax and managed paths. Latest visible Action #16 passed on pinned 02d8c757. Local bash -n and --help passed; no live --check/--push was run. |
| Decision | Reject as migrator; retain selected safe-export/routing patterns, not source code or its routing modes as session structure. |

Pinned main 02d8c757f04e00a3d8f9da51507ba9a23b9b350f, 2026-09-15; MIT with explicit Daniel McAteer/Sol Advisor origin attribution; 0 stars/forks, 20 commits. Full source review: research/evidence/toshon-jennings-agent-advisor-review-2026-11-24.txt.

Primary inventory 226/303 reviewed, 77 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Primary+supplemental pending 254; including manual pending 257. Next primary candidate: weixuanteo/skills-manager (#227).

## Candidate #227 — weixuanteo/skills-manager (2026-11-24)

| Capability | Review |
|---|---|
| Product | Local Skills inventory/preview/install/update/remove UI across Claude Code, Codex, Cursor and other skill folders; install methods include skills CLI, npm, git and Claude plugin Skills. |
| Resource model | Skill frontmatter, filesystem files, agent/scope locations, install method/provenance and update status. Project = a local directory root, not a conversation Project/Section. |
| Session/MCP/plugin migration | None: no ChatGPT/Codex Project or Section Group, session/event reader, attachment archive, MCP server transfer, schedule or target resume writer. Claude plugin scanning covers Skills only. |
| Quality | Isolated pnpm 12.3.4 install passed supply-chain policy gate (273 entries); tests 35/35; typecheck/build pass with bundle-size warning. No CI workflows, no release, no declared license, 0 stars/forks. |
| Security | Local 127.0.0.1 default, confirmation dialog and generated-command allowlist; temp smoke blocked path traversal, arbitrary command and cross-origin POST. Branch is checked at pinned preview SHA, but install command resolves ref after check (TOCTOU). Production audit: 9 advisories (8 moderate, 1 low) in Hono/node-server. |
| Decision | Useful adjacent Skill ResourcePlane UX/design patterns only. Not a session migrator; do not reuse unlicensed source. |

Pinned main 3aa4419870ca2a73fc90aea919042d606736ea9c. Full source/test/audit evidence: research/evidence/weixuanteo-skills-manager-review-2026-11-24.txt.

Primary inventory 227/303 reviewed, 76 pending; supplemental net-new 177 pending; manual additions 15 total / 3 pending. Primary+supplemental pending 253; including manual pending 256. Next primary candidate: WoodSettler/CyberGuild (#228).

## Candidate #228 — WoodSettler/CyberGuild (2026-11-24)

| Capability | Review |
|---|---|
| Product | Cross-harness appointment/QuestBoard Skill for Claude Code, Codex and DSH. |
| Migration | No Project/Section or Session/event import/export, typed lineage, attachments, MCP/plugins, schedules or target resume. QuestBoard is manual Markdown. |
| DSH adapter | Windows-only user-level junction to `~/.dsh/skills`; not project `.dsh/skills`/`.agents/skills` or Workspace/Session integration. Checker only checks package files/links. |
| Quality | Pinned `a199c207087e99217cae2d456fa4b915b10e8fba`; 0 stars/forks, no license/release/CI. Package checker passed; no live native-harness test. |
| Decision | Reject as migrator; retain explicit opt-in/minimal context only; no unlicensed source reuse. |

Primary 228/303 reviewed, 75 pending; supplemental net-new 177 pending; manual 15 total / 3 pending. Combined primary+supplemental pending 252, including manual pending 255. Next `xdlkc/SkillHub` (#229). Full evidence: `research/evidence/woodsettler-cyberguild-review-2026-11-24.txt`; DSH profile: `research/evidence/deepseek-harness-session-project-profile-2026-11-24.txt`.

## Candidate #229 — xdlkc/SkillHub (2026-11-24)

| Capability | Review |
|---|---|
| Product | Local Skill repo catalog and copier across 73 global agent IDs; metadata-only multi-machine Git sync. |
| Migration | No Project/Section/session/lineage/edit/attachment/MCP/plugin/schedule/resume transfer. |
| Findings | Wildcard-bound unauthenticated API; CORS `*`; synthetic symlink read outside clone root; clone path collision; update leaves stale deleted files. |
| Quality | 70 tests and build pass; tests miss install routes. Production audit 0; full tree 6 dev advisories, 2 critical. No license, release, or CI. |
| Decision | Reject as a migrator and avoid real profile writes until core safety/data-integrity fixes; no code reuse. |

Evidence: `research/evidence/xdlkc-skillhub-review-2026-11-24.txt`. Primary 229/303 reviewed, 74 pending; supplemental net-new 177; manual additions 15/3 pending. Combined pending 251; manual-inclusive 254. Next `xfan3696-collab/skillpkg` (#230).

## Candidate #230 — xfan3696-collab/skillpkg (2026-11-24)

| Capability | Review |
|---|---|
| Product | MIT S3/MinIO registry for versioned individual SKILL.md bundles with SHA and JSON index. |
| Migration | No native harness install paths, Project/Section/session, lineage, media, MCP/plugins, schedule, memory or resume. Generic `~/.skillpkg/skills` only. |
| Quality | 8 commits, 0 stars/forks, no release/CI/tests; Python 3.12 source install/compile/pip-check/CLI smoke pass. `update` unimplemented. |
| Security | CLI path traversal, remote index tarball filename escapes temporary staging, optional unauthenticated publish, plaintext 0644 publish token, lexical semver latest bug reproduced in synthetic fixtures. |
| Distribution | README `pip install skillpkg` conflicts with unrelated PyPI 0.0.6; separate Exaggarate `skillpkg-cli` queued for manual source review. |
| Decision | Reject as migration tool and do not reuse as-is. Retain only conceptual versioned ResourcePlane bundle/index/hash patterns. |

Evidence: `research/evidence/xfan3696-collab-skillpkg-review-2026-11-24.txt`.

Primary 230/303 reviewed, 73 pending; supplemental net-new 177; manual additions 16 total/4 pending; combined primary+supplemental pending 250, manual-inclusive 254. Next primary `Xichun123/dsh-skills-manager` (#231).


## Candidate #231 — Xichun123/dsh-skills-manager (2026-11-24)

| Capability | Review |
|---|---|
| Product | DSH-only private Skill provider/library with provenance lock and separate global/workspace/manual-only state. |
| Migration | No ChatGPT/Codex Project/Section or Session/event/lineage/media/MCP/plugin/schedule/memory import, export or resume; no Claude Desktop 3P mode or local Claude Code adapter. |
| Current DSH | Open issue #1 reports activation injection and custom RPC HTTP 405 blockers on DSH 0.2.0-rc.2; source confirms route and peer-range ceiling, but live runtime result not independently reproduced. |
| Quality | Pinned `13004c2e00c90e68d383ae63a31932dfb12a172a`; `UNLICENSED`, 30 commits, 0 stars/forks, no release. Build + 24 tests pass; `pnpm validate` absent. Production audit 0; full-tree audit 1 high + 1 low. |
| Decision | Keep only as a DSH ResourcePlane design reference. Reject as migrator and reuse no source. |

Evidence: `research/evidence/xichun123-dsh-skills-manager-review-2026-11-24.txt`. Primary 231/303 reviewed, 72 pending; supplemental net-new 177; manual additions 16/4 pending. Combined primary+supplemental pending 249; manual-inclusive 253. Next primary: `yyeret/ai-threads-kanban` (#232).


## Candidate #232 — yyeret/ai-threads-kanban (2026-11-24)

| Capability | Review |
|---|---|
| Product | Local cross-Harness work-thread board; scans Claude Code, Codex, Gemini CLI and Antigravity history; overlays stages/goals and native resume links. |
| Migration boundary | Summaries + transcript paths only; no ChatGPT Projects/Sections, Claude Desktop 3P modes, raw event bundle, typed branch/parent/subagent graph, attachments or target import. “Thread” identity is prompt/repo-basename heuristic clustering. |
| Side effects / security | Codex rename/archive mutates native index and moves rollout. Loopback-only server accepts unauthenticated GET mutations; synthetic Origin request changed temp state. A synthetic Codex ID reached an unquoted shell resume string; not executed. |
| Quality | MIT, pinned `9f948221f805f486205afc0763bcef164e5a4dfb`, 25 commits, 0 stars/forks, no CI/release. 20 tests pass with temp homes; scanner/classifier untested. |
| Decision | High-value SessionInventory/workflow prior art only. Do not install or reuse as-is; harden identity, server, resume, archive and sync before integration. |

Evidence: `research/evidence/yyeret-ai-threads-kanban-review-2026-11-24.txt`. Primary 232/303 reviewed, 71 pending; supplemental net-new 177; manual additions 16/4 pending. Combined primary+supplemental pending 248; manual-inclusive 252. Next primary `zuhabul/yo-code` (#233).


## Candidate #233 — zuhabul/yo-code (2026-11-24; screened, no deep source review)

| Capability | Review |
|---|---|
| Product | Recovered/rebranded CLI with public docs for local Anthropic-compatible API-key accounts; not described as a cross-Harness migration tool. |
| Migration evidence | No ChatGPT/Codex Project/Section/Session import/export described in public docs. Full source absence not asserted because provenance gate halted deeper inspection. |
| Provenance / license | Own LICENSE/SOURCE_PROVENANCE claim proprietary Anthropic Claude Code sourcemap-leak origin and prohibit competing-product use/deployment. Hard stop for Nexus implementation/reuse. |
| Maturity | README reports full CLI boot blocked by missing recovered modules. Bun unavailable here; no install/runtime check. 4 open Dependabot PRs, CI failures, no Releases. |
| Decision | Screen out; no code or code-derived design reuse. Require clean-room provenance and legal review to reconsider. |

Evidence: `research/evidence/zuhabul-yo-code-review-2026-11-24.txt`. Primary 233/303 reviewed or screened, 70 pending; supplemental net-new 177; manual 16/4 pending. Combined pending 247; manual-inclusive 251. Next primary: `zxu756/AgentVM` (#234).
## Candidate #235 — lvtd-dgtl/agent-history (2026-11-24)

| Capability | Review |
|---|---|
| Product | MIT, local-first transcript search/archive with Ollama embeddings/SQLite, retrieval/injection, MCP and optional hub. |
| Source adapters | Claude Code (local JSONL, forks/subagents/project memory), Codex CLI, OpenCode, Hermes, OpenClaw, Grok, Gemini CLI, T3 Code; Claude.ai export import is explicit and snapshot-only. |
| Import fidelity | Claude.ai exports produce records for chats, projects/docs/instructions, memories, design chats and extracted attachment text; the code says export chats are not linked to Projects. No full branch/event graph; tool/thinking content and media/usage are omitted; attachment text cap 100k. |
| Target coverage | No ChatGPT source or target writer; live Claude Chat, claude.ai/code Cloud sessions and Claude Desktop Cowork are explicitly listed as uncovered. Local Claude Code reading is not a Desktop API-Key/gateway resume test. |
| Privacy / quality | Local secret redaction off by default; full text retained; README says no at-rest encryption. Scoped parser/identity: 105 pass/56 skipped; full suite: 434 pass/410 skipped, including 409 SQLite-extension skips on review Python 3.12 and one Windows-only. |
| Decision | Keep as valuable local read-adapter, history coverage, alias and retrieval prior art; not a ChatGPT Project/Section/Session migration solution. Do not treat indexing/search as migration fidelity. |

Evidence: `research/evidence/lvtd-dgtl-agent-history-review-2026-11-24.txt`. Primary 235/303 reviewed, 68 pending; supplemental net-new 177 pending; manual additions 21/9 pending; combined pending 245, manual-inclusive 254. Next primary: `neosun100/aiw` (#236).
## Additional discovery leads captured during candidate #235 review (2026-11-24; not reviewed)

These official repository pages surfaced in the broader search and are queued only as leads; no license, provenance, source implementation, tests or migration fidelity has been audited yet:

| Repository | Why it was queued | Status |
|---|---|---|
| [XDUwt/claude-desktop-history](https://github.com/XDUwt/claude-desktop-history) | README describes local Claude Desktop Code/Cowork account re-homing and Chat export, directly relevant to mode-specific storage. | Pending code/license review; treat all claims as unverified. |
| [rpeck/claude-explorer](https://github.com/rpeck/claude-explorer) | Search result describes browsing/search/export across Claude Desktop Chat, Code and Cowork. | Pending code/license review; test whether any function writes/re-homes native sessions. |
| [contextberg/agent-history](https://github.com/contextberg/agent-history) | Search result describes cross-agent history and MCP handoff. | Pending code/license review; distinguish recall/handoff from full migration. |
| [LinnkLabs/AgentHistory](https://github.com/LinnkLabs/AgentHistory) | Search result describes Claude Code/Codex history and Cowork discovery. | Pending code/license review; read-only inventory may not migrate. |
| [ericblue/cowork-explorer](https://github.com/ericblue/cowork-explorer) | Search result describes a Claude Desktop Cowork history viewer/exporter. | Pending code/license review; Cowork-specific storage reference only so far. |


## Candidate #236 — neosun100/aiw (2026-11-24)

| Capability | Review |
|---|---|
| Product | MIT tmux workspace/process manager; CLI, REST/WebSocket and stdio MCP. Keeps local agent terminals alive; does not archive or import conversation history. |
| Hierarchy | Only per-workspace name/tool/model/dir/description/created metadata; no Project/Section/Session event graph, lineage, attachments or usage. |
| Security | HTTP defaults to `0.0.0.0`, has no built-in auth, and exposes send/kill/terminal attach; shell command construction uses `shell=True`. README requires auth proxy/HTTPS before exposure. |
| Correctness | Rename path has undefined `SESSION_PREFIX`; safe synthetic probe confirmed NameError. Open MCP range breaks against 2.3.0 (14 tests fail); 1.0.0 passes 66 tests. |
| Decision | Low migration relevance; adjacent orchestration only, not a Nexus importer/backend. |

Evidence: `research/evidence/neosun100-aiw-review-2026-11-24.txt`. Primary 236/303 reviewed, 67 pending; supplemental 177 pending; manual 21/9 pending; combined pending 244, manual-inclusive 253. Next primary: `i3T4AN/Archivist-MCP` (#237).

### Integrity note — candidate #234 AgentVM

The followup234 verification ledger recorded the AgentVM evidence file, but it was absent from the followup235 project ZIP and the inventory entry was still `unreviewed`. The file is restored from the observed followup234 run and the row now agrees with the cumulative reviewed count. See `research/evidence/zxu756-agentvm-review-2026-11-24.txt`.


## Candidate #237 — i3T4AN/Archivist-MCP (2026-11-24)

| Capability | Review |
|---|---|
| Product | MIT local-first project-memory MCP with typed knowledge graph, audit/version controls, hybrid retrieval, core-memory materializer and snapshots. |
| Session fidelity | A `sessions` metadata table exists, but no session creation/import tool or transcript/event hierarchy. Observations optionally FK to sessions; generic `Session` nodes are distinct. Safe synthetic unknown-session probe failed with FK error. |
| Export | `export_audit_log` is audit-only; snapshots restore the whole local DB. No graph content export/import or ChatGPT/Claude target adapter. |
| Security | Encryption optional/off by default; synthetic fake key persisted raw in node content. HTTP accepts unauthenticated tools if token map empty; team SSE uses bearer scope. Purge only covers observations. |
| Quality | 79 tests passed in 5.89s in disposable venv; 3 commits, 4 stars, no release, 0 open issues. Strong adjacent memory-model reference, not evidence of production support. |
| Decision | Keep as optional derived memory-plane prior art, not a source SessionGraph or migration implementation. |

Evidence: `research/evidence/i3T4AN-archivist-mcp-review-2026-11-24.txt`. Primary 237/303 reviewed, 66 pending; supplemental 177 pending; manual 21/9 pending; combined pending 243, manual-inclusive 252. Next primary: `maideps/ai-harness-framework` (#238).


## Candidate #238 — maideps/ai-harness-framework (2026-11-24)

MIT coding-workflow harness for Claude Code/Codex/Gemini CLI; progress and session-trace files store task/git/verification metadata, not transcript turns or Session lineage. No ChatGPT Projects/Section converter or Claude Desktop third-party-gateway Chat/Cowork/Code writer. Full check passed; relevance is adjacent workflow state only. [Review evidence](evidence/maideps-ai-harness-framework-review-2026-11-24.txt).


## Candidate #239 — 1naruto-1/agent-connect (2026-11-24)

MIT local coding-CLI session continuity for Cursor / Claude Code CLI / Codex CLI / Pi; 122 tests pass, but it has no ChatGPT/ChatGPT Codex Project/Section source and no Claude Desktop 3P Chat/Cowork writer. Linearizes selected active branches, drops/marks prior forks, lacks typed media/usage/project resource dependencies. Synthetic safe-home test exposed unrelated Codex session `base_instructions`/`turn_context` copied into new target session. Keep only as narrow adapter prior art; see [full review](evidence/1naruto-1-agent-connect-review-2026-11-24.txt).


## Candidate #240 — dawnnnnnnnnnnnnnnnn/agent-hoard (2026-11-24)

MIT local disk scanner/cleanup manager, not a ChatGPT Project/Section/Session migrator. Flat session inventory; DSH/Codex-only local archive actions; no Claude Desktop 3P Chat/Cowork/Code or local Claude Code API-key writer. Full suite passed under disposable HOME (5 pass / 0 fail / 1 skip), but MCP plan validation is incomplete; synthetic-only probes confirmed no-confirm/out-of-root HTTP move and no-confirm purge. Keep only as inventory prior art and do not deploy as-is. Review evidence: research/evidence/dawnnnnnnnnnnnnnnnn-agent-hoard-review-2026-11-24.txt.

Primary corpus **240/303 reviewed, 63 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **240**, manual-inclusive **249**. Nexus research/prototype remains active and incomplete; no Destruction Era migration or research-completion notice is claimed. Next primary: NeoHsu/mnemark (#241).


## Candidate #241 — NeoHsu/mnemark (2026-11-24)

MIT v0.10.1 local-first curated-memory store for Claude Code/Codex/Pi/Gemini CLI/OpenCode. Strong optional memory-plane prior art with scopes, trust/provenance, graph context and Mnemark-specific JSON/bundle transfer; not a ChatGPT Project/Section/session importer or Claude Desktop 3P Chat/Cowork/Code writer. Synthetic ChatGPT-shaped conversation JSON was rejected by the memory wire schema; same-store bundle roundtrip succeeded. Keep separate from the canonical SessionGraph; plaintext DB/bundles require private encrypted storage/transfer. Local Rust tests: 273 passed; format, Clippy, doc-drift passed; full mise/security gate not run. Full review: research/evidence/neohsu-mnemark-review-2026-11-24.txt.

Primary corpus **241/303 reviewed, 62 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **239**, manual-inclusive **248**. Nexus research and prototype remain active/incomplete; no Destruction Era migration or completion notice is claimed. Next primary: slonana-labs/agichan (#242).


## Candidate #242 — slonana-labs/agichan (2026-11-24; documentation/license screen only)

README describes a cross-machine live coding-agent task swarm (manager/worker tasks, per-worker branches, MCP/Skill/CLI/Claude Code hooks); no ChatGPT Project/Section/Session importer or Claude Desktop 3P Chat/Cowork/Code writer is specified. No LICENSE/COPYING/grant found; GitHub SPDX metadata is null. Source review, execution and reuse stopped at provenance gate. README claims remain unverified. Evidence: research/evidence/slonana-labs-agichan-review-2026-11-24.txt.

Primary corpus **242/303 reviewed or screened, 61 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **238**, manual-inclusive **247**. Nexus research remains active/incomplete; no migration or completion notice is claimed. Next primary: chrisreedbates/a2a-dms (#243).


## Candidate #243 — chrisreedbates/a2a-dms (2026-11-24)
MIT local tmux wake/coordination helper, not a history/session migration adapter. No ChatGPT Project/Section/Session graph, transcript import/export, or Claude Desktop 3P Chat/Cowork/Code/local Claude Code API-key writer. README calls its ring a wake cue and says durable work remains in external queues; liveness is machine-local. Syntax and isolated install checks passed; synthetic probes exposed `lease` path escape and a dual-cooldown gap that permits duplicate wake. Keep only as low-fit coordination prior art; no direct code reuse. Evidence: `research/evidence/chrisreedbates-a2a-dms-review-2026-11-24.txt`.


## Candidate #244 — benvenker/agent-session-search (2026-11-24)
Strong local lexical session-recall/search adapter for seven coding-agent roots plus custom text roots; bounded results preserve file paths, not full conversation/project/session graphs. No ChatGPT Project/Section source or Claude Desktop Chat/Cowork/Code target writer. Synthetic ChatGPT JSON search returned only a path/snippet; the optional cass shim rejected a ChatGPT `mapping` export. MIT v0.9.1. Full tests pass with FFF v0.9.6 (370/370); current FFF v0.11.0 causes fail-closed native schema drift (2 tests), while managed search uses sequential fallback. Keep as read/retrieval prior art, not migration. Evidence: `research/evidence/benvenker-agent-session-search-review-2026-11-24.txt`.

## Candidate #245 — rore/Pallium (2026-11-24)
MIT local searchable selected-turn history and plain-text Relay; 258 focused history/visibility/relay tests passed, one skipped after provisioning its optional vector extra. Strong retrieval/provenance/forgetting prior art, but not a ChatGPT Project/Section/session-graph migration adapter, attachment/event transfer system, or Claude Desktop 3P Chat/Cowork/Code/local Claude Code writer. Evidence: `research/evidence/rore-pallium-review-2026-11-24.txt`.

Primary corpus **245/303 reviewed, 58 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **235**, manual-inclusive **244**. Next: `zen-solutions-dev/zen-agent-skills` (#246). Research remains active/incomplete.

## Candidate #246: zen-solutions-dev/zen-agent-skills (2026-11-24)
Strong portable-Skills and generated-adapter prior art; not a session, Project/Section, or MCP migration tool. Includes a separate, maintainer-only Claude Code observatory draft, not shipped to adopters. MIT; 9 acceptance gates passed in one local OS/Python cell; no actual target client or user session tested. Evidence: `research/evidence/zen-agent-skills-review-2026-11-24.txt`.

Primary corpus **246/303 reviewed, 57 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **234**, manual-inclusive **243**. Next: `AndySze/session-seek` (#247). Research remains active/incomplete.


## Candidate #247 — AndySze/session-seek (2026-11-24)

Local Claude Code/Codex JSONL search via MCP (semantic + ripgrep), not a Project/Section/session-graph migration or Claude Desktop 3P Chat/Cowork/Code writer. MIT; one-star snapshot. Synthetic MCP smoke passed, but synthetic delete/reindex test left removed Codex text searchable in LanceDB (privacy/fidelity blocker); package `index` script references missing `test-index.ts`. Keep only as moderate read/retrieval prior art; no dependency recommendation. Evidence: `research/evidence/andy-session-seek-review-2026-11-24.txt`.

Primary corpus **247/303 reviewed, 56 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **233**, manual-inclusive **242**. Next: `Burney-Web-Services/Best-Foot-Forward` (#248). Research remains active/incomplete.


## Candidate #248 — Burney-Web-Services/Best-Foot-Forward (2026-11-24)

High-value local-first career-memory / cross-agent Skills / MCP prior art, not a Harness-session migrator. Its synthetic `get_profile_bundle` exposes selected JSON career caches plus one Claude Code `user_profile.md`, not transcripts, forks, application database, or attachments. Cleanup Skills have useful user-vs-agent provenance rules but are agent-mediated and lossy. MIT; full suite 519 passed/14 UAT skips on each CI Python version (3.11/3.12/3.13). Keep as narrow architecture reference; no direct dependency recommendation. Evidence: `research/evidence/burney-best-foot-forward-review-2026-11-24.txt`.

Primary corpus **248/303 reviewed, 55 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **232**, manual-inclusive **241**. Next: `chazhyseni/ai-skillweave` (#249). Research remains active/incomplete.


## Candidate #249 — chazhyseni/ai-skillweave (2026-11-24; screen only)

README claims local correction/history-to-Skills extraction and reversible Skills delivery across Harnesses; highly relevant to the Skills plane, but does not document ChatGPT Project/Section/full Session import or Claude Desktop Chat/Cowork/Code session creation. No LICENSE/grant found (GitHub license null; root LICENSE 404). Source/tests/installer were not inspected or run. No code/design reuse recommendation. Evidence: `research/evidence/chazhyseni-ai-skillweave-screen-2026-11-24.txt`.

Primary corpus **249/303 reviewed or screened, 54 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **231**, manual-inclusive **240**. Next: `DevExpGbb/swampup-skills` (#250). Research remains active/incomplete.


## Candidate #250 — DevExpGbb/swampup-skills (2026-11-24)

Tiny APM catalog of three static developer Skills; useful only as Skills-packaging prior art. No Session/Project/Section, memory, MCP server, attachment or gateway migration. MIT is declared in README/apm.yml but no LICENSE text is present; APM's docs call this an author assertion. README test command fails because `tests/` is absent; APM/native Harness installation was not run. No migration-engine recommendation. Evidence: `research/evidence/devexgbb-swampup-skills-review-2026-11-24.txt`.

Primary corpus **250/303 reviewed, 53 pending**; supplemental net-new **177 pending**; manual additions **21 total / 9 pending**; primary+supplemental pending **230**, manual-inclusive **239**. Next: `dexmaddy/ai-agent-harness` (#251). Research remains active/incomplete.


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

