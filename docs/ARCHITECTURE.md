# Architecture: first prototype

## Design contract

1. The imported source graph is authoritative; native target sessions are projections.
2. Unknown source fields stay in `portable.json`; unknown is not the same as “discarded.”
3. Parent/child edges and active-node selection remain explicit in the canonical format.
4. Conversion is read-only by default. `--write` creates a new, permission-restricted bundle and refuses to overwrite an existing path.
5. No API key is loaded, copied, or serialized. This prototype makes no model request.
6. The report distinguishes preserved sidecar data from native target data; it does not call semantic flattening “lossless.”

## Current data model

`ConversationGraph` contains stable source IDs, a node table, explicit parent/child edges, root IDs, active node ID, source metadata, and the full raw source object. ChatGPT `mapping` trees are represented as graphs. Codex JSONL is retained as an ordered raw record stream, with conversational records projected into a linear message chain; session metadata (including parent-session hints) stays in the sidecar.

The bundle builds a separate hierarchy index for section groups, projects, sessions, and parent-session/fork relations. Explicit source fields remain distinguishable from workspace-path inference and unknown/unassigned buckets. The prototype does not infer ChatGPT section membership from a title or sidebar order. A future source index will model account/workspace → section group → project → session relationships separately from the message graph.

## Cross-harness session log versus transcript

The compatibility research now includes event-sourced harnesses (notably DeepSeek Harness) where the durable append-only event log is the source of truth and model-visible messages are only one projection. Nexus Memory should therefore evolve beyond `ConversationGraph` alone: retain the raw source event stream and provenance, define a typed canonical event layer for messages/tool attempts/results/compaction/attachments/lifecycle records, and derive a message graph or target transcript from it. Projection loss must be explicit; a plain transcript cannot reconstruct failed attempts, exact tool results, event order, parent/fork sequence boundaries, or checkpoint history.

Hierarchy should be an independent, source-qualified graph: identity and containment edges for account/workspace/project/section/session, plus fork/subtask/subagent/workflow/automation relations. Do not assume every harness has a Section Group; DSH documents Workspace and Session, Antigravity uses Projects and session-attached task/artifact relations, and scheduled runs may create fresh conversations instead of resuming a session. Preserve attachments in a content-addressed store with source references and integrity hashes, while keeping target permission/auth scopes outside imported data.

The first-party Codex app snapshot exposes sidebar Section membership separately from Project records: Section `itemKeys` are source-qualified (`codex`/`chatgpt`), while threads carry `projectId` and Projects carry host/path metadata. Represent this as an organization/membership edge independent of project containment, and preserve original item keys as provenance; do not promote a custom sidebar Section into a Project or assume it owns the conversation.

Anthropic's 2026 Claude Code Projects beta adds a target-specific coordinator-conversation → worker-thread/session hierarchy, project Library, project memory/instructions, cloud environments, account connectors, and scheduled tasks. Its cloud threads deliberately exclude much of a local `.claude` setup (including repo Skills, `.mcp.json`, hooks and permissions), so each component needs an explicit target mapping and an activation check. Anthropic-hosted Cloud sessions require claude.ai authentication and the CLI cannot push an existing local transcript into Cloud; API-key-only users target the local CLI or a separately identified third-party cloud harness. Represent auth compatibility as a capability gate on the target adapter rather than treating an API key as a transferable project property. See [Claude Code Projects](https://code.claude.com/docs/en/claude-projects), [Sessions](https://code.claude.com/docs/en/sessions), and [Cloud sessions](https://code.claude.com/docs/en/claude-code-on-the-web).

OpenCode is a useful native-interchange reference, but its `{Session.Info, settled messages}` JSON is target-specific. Adapter tests must separately measure parent containment versus fork-boundary preservation, token/cost/timestamp mapping, inline-media handling, and privacy redaction; importing a parent tree in topological order is not the same as restoring the entire project, workspace snapshot, or configuration. Keep target-native export/import formats at adapter edges and retain the versioned Nexus event/graph archive as the cross-harness source of truth. See the [pinned OpenCode transfer implementation](https://github.com/anomalyco/opencode/blob/011f9043e8a90dc9a1ac42fb1181486dd4d13b71/packages/core/src/session/transfer.ts).

## Claude Code output

The writer creates one native JSONL session per source leaf path, which avoids silently flattening branches. Native transcripts currently contain only user/assistant text. Tool events, non-text typed blocks, timestamps that cannot be interpreted, attachments and unknown records remain in the portable sidecar and are disclosed in `manifest.json`.

The Claude Code session-file format is an observed implementation detail, not a supported import API. The writer tags a tested CLI version. A synthetic session was resumed with Claude Code 2.1.172 and continued through a localhost mock Messages API using a dummy key; no provider API was called. The prototype writes a local bundle, not to the user's `~/.claude`.

## Next architecture layers

- Source adapters: official account export, Codex local rollouts, project/section indexes, later harness-specific stores.
- Stable package: versioned JSON graph + content-addressed attachment blobs + original raw records + provenance.
- Target adapters: native import where documented/verified; otherwise explicit handoff package with branch-specific transcripts.
- Capability registry: per source/target pair, per feature, evidence date, tested version, confidence, loss reason.
- Security layer: secret markers and permission review, no credentials in bundles, hashes for every attachment, atomic write/rollback.
- Extensions: Agent Skills/MCP/plugins/permissions/memory/schedules are separate resource types with provider-specific auth and activation rules.


## Pi event-tree adapter implications

Pi provides a useful local-harness reference for separating the append-only session log, selected branch, and reconstructed model context. Nexus should preserve the full source entry graph and selected leaf, but separately record compaction/context-edit projections, images, tool results, usage, and extension-owned entries. The session header’s parentSession file path is provenance, not a guaranteed fork-boundary pointer. Keep cwd/project resources and MCP/Skills/extensions outside the message graph; the reviewed core docs do not establish a universal Project/Section or built-in schedule object. The Pi JSONL remains a versioned native format, not Nexus’s canonical interchange schema.

## Migration-tool review implications (2026-11-20)

The audited a2migrate and sessionport implementations confirm that native writers can make sessions discoverable in target stores, but a message array/parent chain is not a branch graph. Preserve source ancestry independently and only claim target branch fidelity when the writer consumes explicit parent edges and a target resume test proves them. Treat target settings emitted by converters—including Codex turn policy or MCP env/header values—as untrusted inputs: do not import grants or secret values; require redaction and an explicit permission review. Local unit tests and CI can validate serialization invariants, but cannot substitute for version-pinned native CLI resume checks.

Codex's first-party app-server exposes `externalAgentConfig/detect` and `externalAgentConfig/import` for selected Claude Code/Cursor resources and session files. The protocol includes Skills, MCP config, Memory, Plugins, Hooks, Subagents, Commands, instructions, and Sessions (`path`, `cwd`, `title`), but no ChatGPT Project or Section object. At OpenAI Codex commit `8653ca9e99b2c805107bde7b7d6f57a634c643d0`, the session exporter projects parsed sessions into ordered user/assistant text `ResponseItem`s, emits an import sentinel and estimated token count, and does not represent source tool calls as native calls or reproduce a Project/Section/fork graph. Session discovery remains bounded by source-specific limits and an existing cwd; changed-file import behavior must be version-pinned and verified rather than assumed. OpenAI's `codex-plugin-cc` also invokes that API for Claude Code → Codex session transfer, not the reverse ChatGPT → Claude route. This is a useful Codex target adapter and a concrete fidelity comparator, not a universal interchange contract. See [pinned exporter](https://github.com/openai/codex/blob/8653ca9e99b2c805107bde7b7d6f57a634c643d0/codex-rs/external-agent-migration/src/sessions/export.rs), [protocol types](https://github.com/openai/codex/blob/8653ca9e99b2c805107bde7b7d6f57a634c643d0/codex-rs/app-server-protocol/src/protocol/v2/config.rs), and [transfer caller](https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/scripts/lib/codex.mjs).

## Supplemental adapter research (2026-11-20)

`skillsynchq/txcript` is the strongest reviewed session-library candidate so far: its pinned transcript model keeps a native body beside a common projection, while its CLI separates read-only account sources from writable local harness stores. Its ChatGPT reader is a private, Codex-OAuth-backed, pull-only edge; the ChatGPT format docs explicitly reject account-export ZIPs and API-key auth. It converts the active branch, not ChatGPT Projects/Sections or all branch history, into the writable projection. The library's Cloud Cowork adapter is also read-only. Treat its store/codec seams and explicit capability gates as architecture input, not as a solution for hosted Cloud import.

`agentmove` suggests a complementary configuration plane, not a transcript engine: model its 47 client adapters as independent file/resource capabilities, keep MCP credentials redacted and require explicit re-authentication. `agent-capsule` shows a third distinct plane—Codex-local profile migration and Codex/Claude Code session capsules—but its scheduled import is an OS one-shot migration runner, not a recurring task converter. The Ciao browser scripts demonstrate why “chat imported” must be scored semantically: the destination gets one model-generated response to a transcript prompt, not the source chat's exact message/branch graph. None of these findings proves Project/Section or Claude Cloud/API-key equivalence.

`nrzz/claude-chat-ferry` adds a direct static-export adapter pattern: parse ChatGPT's `conversations.json`, select the current branch, normalize to turns, then write a native local Claude Code JSONL session. Its fixture coverage is broad, but the optional resume gate failed one assertion against our installed Claude Code 2.1.76 because the CLI prepended a system reminder before the imported banner. A disposable diagnostic copy changed only that starts-with assertion to a containment check; the E2E then passed and verified every imported marker and the new prompt against the fake API. Keep current branch, project/section membership, attachments, tool evidence, token usage and native session envelope as separate feature gates, and record target version/system context for every resume test.

## Adapter comparison: Agent Connect

Keep the normalized event model and hierarchy graph independent. Agent Connect demonstrates useful active-branch readers and safe append/import patterns, but its five-event canonical union cannot preserve forks, Project/Section membership, binary attachments, token/cost/permission metadata, or schedule definitions. Nexus should retain raw source events and sidecars, model lifecycle and parent relations separately, and validate each target by native resume rather than interpreting an advertised route count as fidelity.

## Distinguish live process workspaces from conversation archives

AIW demonstrates that “persistent session” may mean a live tmux process plus a small workspace metadata record, not a serialized model conversation. Nexus must classify process/workspace lifecycle separately from transcript events and durable parent/fork history. A terminal pane tail is a lossy observation, not a canonical session archive. Reuse the conceptual separation only; do not copy AIW's shell-interpolated control plane or unauthenticated network defaults.

## Version generations are authority edges, not just file variants

The DSH review demonstrates that migration/recovery tools must resolve the current authoritative session generation before proposing edits to retained legacy artifacts. In a V4→V2 coexistence directory, a V2 file may be a retained predecessor rather than the live session; a recovery tool must detect every later generation, bind by session identity/provenance, and refuse writes unless ownership and rollback are proven. Nexus should encode generation/supersession edges explicitly instead of inferring currentness from one successor filename.

## DSH import review: completion state and untrusted resource names

The reviewed `Chang-Tong/dsh-unified-context` DSH connector demonstrates two invariants Nexus must enforce even when a destination offers an idempotent native persistence API:

1. **A stable session ID is not a commit receipt.** A create→append→flush transaction can fail after some events have persisted. If retry interprets ID existence as success, the partial event stream becomes a permanent skipped record. Canonical migration state must distinguish `planned / created / streaming / verified / failed-partial / rolled-back`, preserve the event count/hash and last accepted sequence, and make restart behavior explicit. Prefer staging/atomic finalize where the target permits it; otherwise require a target-specific recovery path (resume append with sequence/hash validation, or remove the partial artifact only when ownership is proven) before reporting success.
2. **Portable metadata is untrusted input.** Skill/frontmatter names and path-derived IDs must be normalized to one safe component before joining an output root; resolve the destination and assert it remains inside the authorized root before any write. A dry-run should expose an invalid-path rejection—not merely show an escaping destination. Add traversal fixtures (`../`, absolute paths, separators, Unicode confusables) and prove no outside-root mutation.

The DSH plugin’s `create → append → flush → close` flow and `name → join(skillsRoot, name)` planner illustrate these failure classes. Our temporary fake-persistence test retained two events then threw; its second invocation skipped the already-created ID. Our traversal diagnostic planned `../escaped/SKILL.md` outside the temp root without applying the write. These are candidate-specific findings, not claims about DSH’s backend in production; they strengthen Nexus’s own transaction/containment requirements. The connector also reinforces that project/workspace placement, transcript events, shared memory/context, Skills, MCP configuration, permissions and scheduled tasks must be separate typed edges/resources—not one “session” blob. See [`RESEARCH.md`](RESEARCH.md#deep-review-chang-tongdsh-unified-context-former-dsh-import-agents-2026-11-20).

## Catalog/resume products are a separate adapter plane

The reviewed `jazzyalex/agent-sessions` app demonstrates that a multi-agent history browser can normalize events, infer limited subagent/side-chat parentage, keep local source-file archives and issue source-native resume commands without being a migration system. Nexus should model these as distinct capabilities: `discover/search`, `preserve-source-bytes`, `render/export`, and `create-target-session/resume` must have separate evidence gates. A Markdown export or local backup can support human handoff, but neither reconstructs ChatGPT Project/Section membership or proves a target-native session writer. See [`RESEARCH.md`](RESEARCH.md#deep-review-jazzyalexagent-sessions-2026-11-20).


## Config-sync plane versus migration graph

The reviewed slash9494/ai-config-sync-manager is a useful adjacent example, not a session-import engine. It synchronizes local Claude Code/Codex configuration files and exposes instructions, Skills, Agents, MCP, hooks, permissions and status-only plugin inventory. Keep this resource/config plane separate from Nexus Memory's canonical conversation graph (source object IDs, Project and Section membership, session/branch/subtask edges, ordered message/tool events, attachments/artifacts, memory state, and scheduled-task definitions). A host config diff cannot establish that a conversation or cloud project was recreated.

Patterns worth borrowing after independent design review: explicit source/target selection, selectors, dry-run previews, backups and per-item before/after hashes. Patterns to reject or strengthen: secrets copied by default; risk labels that do not correspond to enforced acknowledgement gates; target deletions applied from absence in the source; and non-atomic multi-item apply that continues after one operation fails. Nexus must default to no credential transfer, require explicit field-level approval for destructive or permission/hook changes, stage/validate the whole bundle before writes, and produce an exact loss/recovery report. This candidate provides no evidence for a Cloud API-Key session writer, ChatGPT Project/Section model, session branch graph, attachments, token accounting or schedule migration.


## Cross-harness memory-kit comparison: pgrigorr/memory-harness-kit

This project is a useful adjacent memory sidecar, not the canonical migration archive. It separates raw source files, normalized records/atomics, retrieval indexes, summaries and review queues; its Claude Code Stop hook can optionally persist a local transcript and defer indexing to SessionStart. That is a reference for separating evidence from generated recall.

Its session model is not sufficient for Nexus fidelity: the raw log is stored as a blob, while the normalized record has one session ID and dialogue text, no typed message/branch/parent-child/tool relation or Project/Section membership. Our synthetic event-chain check retained a complete raw sidecar but projected one dialogue-only record with project_slug=null. Secret-shaped test data survived both raw storage and normalized retrieval; an ID sanitization collision also overwrote an earlier transcript. Adapter acceptance therefore requires raw-secret exclusion and stable collision-resistant identity before persistent writes.

Keep memory retrieval and lossless conversation archival as separate layers. Nexus still needs a versioned canonical event graph, explicit source project/section/session relations, attachment and schedule objects, provenance and hashes, plus per-target native restore tests. Do not infer ChatGPT/Codex portability from the kit's generic/OpenClaw config contract or from green local tests.


## Local history catalog versus migration adapter

The reviewed agent-cli-session-TUI is a source-side discovery/resume tool. Its six providers parse metadata and bounded tails from native CLI folders; its resume action relaunches that same CLI with the original ID and cwd. It has a TUI session summary model and local flat thematic group assignment, but no versioned conversation export, target writer, message-event interchange graph, cross-provider branch mapping, Project/Section edges, attachment bundle, or schedule transfer. Treat it as a discovery connector only; do not mistake provider count or search coverage for migration coverage.

There is also a default egress decision: the remote grouping engine sends session titles and cwd URIs to an undocumented hosted endpoint. Its privacy-oriented local alternative is wordmatch, not a local model. Nexus adapters must make egress explicit before discovery and never send directory paths or summaries implicitly. Local archive/group metadata and native resume are useful source inventory UX patterns, not substitutes for a lossless canonical archive.

### MethodoxTech session-history UI reference
Treat this as local discovery/view/export/resume UX, not a migration engine: one-level date/project-path browsing groups, Markdown export, no target import writer, no raw parentUuid branch graph, and incomplete image/token payload preservation. README describes a local-only, no-telemetry/no-account-connection design.

### ai-agent-skills Skill adapter reference
Use only as a reference for a Skill library/catalog and explicit installation-path layer. Separate Agent Skills packages from session/project migration. Preserve per-target roots and scope semantics; the --all flag is not equivalent to all legacy agent paths. It provides no session, MCP, plugin, memory, or scheduler migration.

### skills-manager shared Skill hub reference (2026-11-20)
`shenysun/skills-manager` adds a shared hub/source registry and explicit user-scope symlink versus project-scope copy distribution, with collision checks, restore points and rollback affordances. Reuse this as a possible Skills adapter/catalog plane only. Keep a versioned catalog freshness date and test every path mapping on the target runtime; an advertised agent count or install-path mapping is not evidence that project scope, trust, session state or target activation is compatible. The review found no conversation graph or Project/Section importer, nor MCP/plugin/memory/attachment/schedule transfer. Its bundled agent catalog was already older than its 90-day doctor warning threshold at review time; `catalog refresh` was attempted only in a disposable home and received HTTP 403 from GitHub's commit endpoint.

### purple MCP security-pattern reference
Reference only the MCP adapter policy pattern: stdio transport, explicit read-only tool allowlist, redact command bodies in audit records, owner-only audit-file permissions. Do not adopt it as a migration source: its domain is SSH infrastructure, not AI sessions/projects/memory. Require an explicit read-only default; purple direct CLI mode is writable unless flagged.

### Dutis governed-MCP transaction reference
Reference the workflow boundary only: build a deterministic plan, evaluate local policy, require explicit approval for a fresh digest, snapshot before mutation, audit, then verify. Keep mutation tools absent by default. Dutis itself is a macOS app-handler manager, not a session/project migration source.


### Prompt handoff is not native session restoration

The reviewed `Sai-Nitin123/ContextBridge` is a useful counterexample: its `.aicx` stores a conversation projection, but its destination action inserts one continuation prompt into an interactive page composer. Keep this as an optional fallback projection only. Nexus's primary bundle must preserve typed events, source identities, hierarchy, attachments and integrity independently of generated summary text. Redaction must run over every derived field and opaque metadata, not only message text, and prompt-fence encoding must cover titles/summaries as well as message bodies before any write or clipboard action. See the synthetic leakage/fence probes in `docs/RESEARCH.md`.


### Prompt handoff is not native session restoration

The reviewed `Sai-Nitin123/ContextBridge` is a useful counterexample: its `.aicx` stores a conversation projection, but its destination action inserts one continuation prompt into an interactive page composer. Keep this as an optional fallback projection only. Nexus's primary bundle must preserve typed events, source identities, hierarchy, attachments and integrity independently of generated summary text. Redaction must run over every derived field and opaque metadata, not only message text, and prompt-fence encoding must cover titles/summaries as well as message bodies before any write or clipboard action. See the synthetic leakage/fence probes in `docs/RESEARCH.md`.

### DOM scraping and copy/paste are a lossy fallback, not an adapter

The MaazzAlii/context-saver-extension review confirms a useful classification boundary: a browser extension that reads currently rendered DOM and injects/copies one prompt has not imported a session. Such a path cannot promise hidden or unloaded history, stable message identity, branch/fork/subtask edges, binary assets, tool events, workspace/project membership, or target resume semantics. Nexus may offer this only as an explicitly lossy manual handoff, behind a visible egress choice and with capture-completeness warnings; it must not count toward native migration coverage. See the pinned source review in `docs/RESEARCH.md`.

### Restore archives are untrusted path inputs

The Agent Session Vault review reproduced a path escape from a crafted backup manifest: a rel path containing ../ was converted and written relative to the caller's working directory even with --target specified. Nexus must never treat dry-run, confirmation, overwrite gates, or a SHA-256 content check as path authorization. A restore planner must reject absolute/drive/UNC paths and dot-dot segments, normalize separators, canonicalize the destination (including symlinks), prove it is beneath an explicitly authorized provider root, detect alias/collision cases, and refuse the entire plan before any write if containment fails. Add adversarial manifest and symlink/path-normalization tests before implementing a restore/apply path. See the synthetic-only probe in docs/RESEARCH.md.



### SQLite sidecars must form a consistent snapshot

Agent Session Vault includes db, WAL and SHM paths in its backup inventory, but copies each file independently. Nexus must not treat “database + WAL + SHM present” as proof of a consistent live SQLite snapshot. Use a supported online-backup/snapshot mechanism or quiesce the source; bind the manifest hashes to that immutable snapshot and test restoration while the source is actively mutating.

### Native-format writers need provenance, not fabricated metadata

The Agent Session Migration review demonstrates a key Nexus contract: a target writer must not silently substitute a fixed model/provider/version/permission for unknown source metadata. Its Codex and ZCode writers currently synthesize model/provider values, while its common mapper converts tool/reasoning blocks into capped prose. Nexus should preserve typed events and provenance alongside any target rendering, attach a field-by-field loss report, and label non-native continuation bundles honestly. A target can parse the file yet still lose branch ancestry, tool invocation semantics, usage/cost, attachments and project/task links.

### Cross-database apply is a distributed transaction

Two individually atomic SQLite transactions are not one atomic migration. The synthetic Agent Session Migration probe reproduced a CLI-session commit followed by task-index failure, leaving an orphan session. Nexus must stage/backup/verify every target store, use an explicit journal/compensation strategy across stores, and test failures after each store commit; rollback must restore both stores to the original hashes.


### Shared memory is a separate plane from session migration

The reviewed `YURIBEDRAN/rubi` demonstrates a valuable cross-harness memory sidecar: project-local Markdown, a small always-read map, on-demand module pages, graph facts, and handoffs, served through MCP and enhanced by harness hooks. Reuse that separation, not the claim that a selected summary is a session. Nexus should keep (1) immutable source exports/raw evidence, (2) canonical typed event/session graphs with parent/fork/subtask edges, and (3) derived portable memory summaries as separately hashed objects. A handoff can supplement a session bundle but cannot replace message ordering, hidden/deleted events, attachment payloads, tool results, or token/cost metadata.

The Rubi source review also adds two concrete security gates for any memory service: (a) redact credentials deterministically before graph indexing, summaries, logs, backups or MCP results, rather than trusting “never store secrets” instructions; (b) enforce read/write containment after `realpath` resolution, including symlink tests. Synthetic probes showed a fake credential marker was persisted and an in-memory symlink could read a file outside the memory root. Nexus must reject untrusted/symlink escapes and fail closed before exposing or importing a memory tree.

Finally, classify per-harness integration as **native hook**, **MCP + instruction**, **manual config snippet**, or **unsupported/experimental**. A successful MCP handshake or config installer proves tool reachability, not that an agent will call the tool, that it can access a hosted API, or that its session/project hierarchy was transferred. Track these as separate adapter capabilities and acceptance events. See the [pinned Rubi review](RESEARCH.md#deep-review-yuribedranrubi-cross-harness-memory-sidecar-2026-11-20).

### Searchable history and native resume are not migration

The reviewed luckeyfaraday/athena-code project separates durable memory from a local SQLite FTS index and can resume a previously indexed source session by invoking that provider's CLI. Reuse the separation: curated memory, recall/search projection, immutable source archive, and target-native session writers must be different layers. A successful search or native source resume is not evidence that a conversation was migrated into a destination harness.

Nexus's canonical archive must retain parent/fork/subtask edges, typed tool events, attachments, source message IDs, timing, model/provider, token/cost, project/Section membership, and provenance even if its recall index intentionally stores only bounded text. The reviewed scanner's rows store agent/session/workspace/role/time/text and cannot represent those requirements.

The session index also motivates explicit privacy controls: user-selected roots and preview before scan, deterministic secret filtering before any derived store, retention/deletion semantics for sessions removed at source, and a clear one-click index purge. Its README warning not to store secrets is not an enforcement mechanism; a temp synthetic probe persisted a fake token. For takeover/resume, validate the workspace and ask before falling back to a different current directory. Finally, keep shell permission defaults opt-in and fail closed; the candidate's permissionless defaults are not appropriate for a migration tool processing private archives.

### Desktop connection hierarchies are not agent-session hierarchies

The reviewed xtermium app has a genuinely useful workspace/folder tree for its own saved connections and an independent local AI-history list that resumes Claude Code, Codex or omp through native CLI flags. This is adjacent desktop UX, not a session migration pipeline. Keep any Nexus desktop shell's connection profiles, API credentials, agent instructions/Skills/MCP, transcript archives and resume operations as separate typed domains; a generic “Session” noun is not enough to safely merge them.

xtermium's AI history row is metadata (source id/title/time/bytes/path), while its network connection session is a saved endpoint/profile. The former's transcript remains in the source tool file and delete removes that file; the latter participates in xtermium workspaces, folders, layouts, backups and sync. Nexus should make that distinction visible in its data model and UI, preserve originals during migration, and require an explicit export/restore transaction rather than using a browser-history-like list as the destination archive.

Its MCP can operate authenticated terminal/desktop sessions without revealing stored passwords; this shows why a migration assistant must receive least-privilege filesystem/API scopes and never inherit broad remote-control authority by default. See the pinned review in RESEARCH.md.


### termem review: keep local memory separate from migration archives

termem is a useful pattern for a local cross-agent search/recall sidecar, paginated MCP reads, and generated per-harness wrappers. It stores searchable transcript text in SQLite and resumes sessions through the original CLI, but has no destination writer. Nexus must not collapse this working-memory index into its canonical archive: preserve immutable source evidence and a lossless normalized event graph separately from derived summaries, retrieval indexes, and target-native session creation. A cwd tree, local CLI resume command, or MCP wrapper is not equivalent to Projects/Sections, cross-session hierarchy, or a Cloud/API-Key conversation.


### Leon review: reuse its source adapter seam, not its lossy history row

Leon provides a valuable local-history pattern: a HistorySource interface enumerates stable, fingerprinted items; provider parsers map them into a local session/message store; import cursors make repeated scans idempotent; survey/diagnostics explain skipped inputs. The shape is too lossy to be Nexus's canonical archive: tool invocations are textified, results and images are dropped, subagent/fork relationships are incomplete, and raw source fidelity is not represented. Nexus may borrow the adapter/report pattern, but must preserve original records, typed event and hierarchy graphs, attachment bytes/references, token/cost provenance, and explicit projection loss before generating a provider-native destination session.


### Adeptability review: a strong Skills adapter library, not the canonical migration graph

Adeptability is a good reference for a canonical Skill and agent schema, native renderers, sidecar assets, content-hash drift state and reverse import for selected harnesses. Its own code demonstrates why “Skill-compatible” is not lossless: each target has different activation, aggregation, sidecar and size-budget semantics; overrides are not reconstructed on import; Copilot and Codex can drop content. Nexus should borrow the adapter/registry approach only as one resource plane. Session events, Project/Section hierarchy, MCP/plugin configs, auth/permissions and schedules require distinct typed schemas and capability/loss matrices. Before invoking a renderer, resolve and validate the real destination path: a synthetic test showed that a repository .claude directory symlink can redirect sync writes outside the selected project root.


### Pan review: useful session-manager patterns, but not a canonical cross-harness archive

Pan demonstrates a local Session manager with Workspace membership, explicit manager/worker relationships, background Jobs, per-session MCP configuration and provider-specific import/reimport guards. Its native importer preserves practical role/content and some usage, but projects that into Pan's own history and does not carry the source hierarchy/configuration graph wholesale. Nexus should borrow source-native parsing, stable identities, usage side tables and conflict-confirmed reimport—not Pan's role/content projection as the canonical format. Keep raw event evidence, source-qualified Project/Section/Workspace membership, message/branch/task edges, binary attachments, credentials and schedules distinct; emit an explicit loss report at each target edge.

## Termide review implications: local event logs, project layout and ACP continuation

Termide's data model reinforces three distinctions for Nexus Memory:

1. **Project root/layout is not transcript ownership.** A path-hash project store holds a root, panel layout and trust/buffer metadata; session files live in a separate config-rooted hierarchy indexed by the panel directory. Preserve explicit references and provenance rather than moving a whole Termide data directory as one “project.” A UI `panel_groups` column is not a sidebar Section or project-parent relation.
2. **Keep different edges typed.** A message/event `parent_id` chain, a forked log's copied prefix count, a delegated task's `SessionParent` (source session/agent/call), and an ACP-native external session ID each represent different things. Nexus should keep source-session origin IDs and fork-point IDs even when a target copies the prefix, because Termide's fork header records only the copied count.
3. **Distinguish a native runtime resume from an import.** ACP `session/resume`/`session/load` may preserve an external CLI's native live state. Termide fallback replay is a new external conversation built from selected context, not recovery of the provider's complete event log. Nexus adapters must label “resume native session,” “replay messages,” and “create target-native session” separately and expose the associated fidelity/loss report.

Termide is a useful source for typed JSONL event modeling, compaction/replay, local Skill roots, and bounded MCP config adaptation. Its Markdown export is deliberately lossy; neither that file nor its private on-disk JSONL should become Nexus's universal archive. Keep API keys, OAuth tokens, grants, and user-approved permissions outside all bundles. [https://github.com/termide/termide](https://github.com/termide/termide); [release 0.50.0](https://github.com/termide/termide/releases/tag/0.50.0); [session schema](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/agent-core/src/session.rs); [message schema](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/agent-core/src/message.rs); [project layout](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/project/src/lib.rs); [project store](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/project/src/store.rs); [Agent docs](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/doc/en/agent.md); [architecture docs](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/doc/en/architecture.md); [Markdown exporter](https://github.com/termide/termide/blob/5c3eec4915380da479c2bb03f6843342e7a9e17d/crates/panel-agent/src/export.rs).

## Claude MPM review implications: separate capture, checkpoint, summary and native transcript

The review found four data planes that must not be collapsed into one “session export”: (1) session-ID/usage metadata JSON, (2) project-local pause JSON/Markdown checkpoints, (3) generated resume summaries, and (4) optional Socket.IO-captured `AgentSession` records. The Claude Code native JSONL is a fifth, source-owned store that the analyzer reads into a report. Each requires a different `source_format`, provenance, completeness statement and deletion policy.

For Nexus, treat MPM's transcript parser as a sample for a **read-only Claude source adapter**: load the main JSONL and subagent JSONLs; correlate Agent calls only with evidence and mark ambiguous timestamp matches; redact secrets for user-facing projections while retaining source evidence under explicit encryption/consent; preserve image/file blocks, complete tool results, sidechain/control events, native fork/parent IDs and provenance outside the MPM-style timeline report. Never convert a summary checkpoint or aggregate JSON to the canonical event archive without raw source linkage.

Do not confuse `claude-mpm run --resume`/`--fork-session` with importing into another Harness; both delegate to Claude's own native session identity. The MCP Session Server exposes orchestration, not a durable transcript store. Reuse no source code until the repository's conflicting MIT/Elastic-2.0 declarations and hosted-service restriction have been legally resolved. Its optional HTTP MCP control plane binds loopback by default but can be tunneled; it requires an authenticated boundary before remote exposure. [https://github.com/bobmatnyc/claude-mpm](https://github.com/bobmatnyc/claude-mpm); [release v6.5.83](https://github.com/bobmatnyc/claude-mpm/releases/tag/v6.5.83); [license](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/LICENSE); [README](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/README.md); [core session metadata](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/core/session_manager.py); [project-local pause export](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/cli/session_pause_manager.py); [resume-log generator](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/infrastructure/resume_log_generator.py); [MCP session server](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/mcp/session_manager.py); [HTTP MCP transport](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/mcp/session_server_http.py); [event capture/export](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/event_aggregator.py); [captured-session model](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/models/agent_session.py); [aggregate export CLI](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/cli/commands/aggregate.py); [Claude transcript reader](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/session_analysis/transcript_parser.py); [session-analysis report writer](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/session_analysis/markdown_writer.py); [channel-session registry](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/channels/session_registry.py); [internal periodic jobs](https://github.com/bobmatnyc/claude-mpm/blob/25203d34f20982c5871574b5059949ab85ab5a6b/src/claude_mpm/services/communication/message_bus.py).

### RoleCraft review: implement its resource plane, not its storage model

RoleCraft's manifest is valuable adapter input: it separates agent support tiers, install scopes, instruction formats, and MCP config shapes; its lock also demonstrates useful source/content hash/target provenance. Nexus should normalize those into versioned adapter capabilities while keeping `Project`, `Section`, `Session`, `Turn/Event`, `Artifact`, `Skill`, `MCPServer`, `Plugin`, `Schedule`, and their containment/reference edges as independent canonical entities. A RoleCraft profile is only a static agent configuration snapshot and must not be promoted to a session archive.

Before applying a RoleCraft-style profile, the Nexus adapter must report unsupported fields, redact env/token values, and round-trip-test every preserved field. This is required because the reviewed profile serializer accepts but drops `projectOverrides`/`localOverrides`, while export preserves nested env secrets. Unscannable MCP source must be represented as “content not inspected” and gated explicitly; never coerce that state to SAFE. Keep source URL/ref/digest, scanner version and findings, target format, and user approval as separate provenance fields.
### Kendex review: reuse the capability adapter plane, not its session boundary

Kendex demonstrates a useful architecture for the customization layer: one capability table maps harness × resource kind × scope × operations, and project/global scopes write harness-native files with explicit provenance. Nexus can reuse that pattern for Skills/MCP/plugins/hooks/commands, including managed/read-only/unsupported and target-specific render shapes.

Do not equate a local kendex.toml project root with a hosted Project/Section Group. Kendex's session-facing features live in separate Pi extensions: native Pi session files/tree, a bounded live event bridge, session-branch scheduled prompts, and a Pi-to-Claude Code resumption marker. The marker restores only when Pi-session identity/cwd/message fingerprint and the existing Claude session validate. None is a portable canonical record for ChatGPT/Codex message trees or attachments. Model source event history and its transcript projection separately in Nexus; keep export loss explicit.
### AgentSkillsManager review: quarantine cloud skills before any target write

This extension is a narrow VS Code skills browser. Its remote catalog returns SKILL.md sources, not a canonical harness/project/session model. It buffers a remote ZIP, extracts with the pinned adm-zip 0.5.16, deletes an existing destination before copying, and has no app-level integrity/digest or response/extraction budget in the inspected path. Nexus's import pipeline must instead stage content in quarantine, enforce byte/file limits, verify source and digest, scan before apply, use atomic replace/backup, and preserve installed provenance. Do not treat a directory layout as proof of a portable session or project hierarchy.

### Candidate pattern: skills-compat-manager (resource-plane only)

The reviewed tool models compatibility as four declared dimensions and returns an agent-readable preflight Delta through MCP. Nexus can map this concept into an adapter capability/evidence report, but must not confuse that report with durable memory. Keep canonical `Project`, `SectionGroup`, `Session`, `Turn/Event`, `Artifact`, and resource identity/relationship edges independent from harness-specific `COMPAT.yaml`. Use source-qualified identities (the candidate silently collapses equal skill basenames) and represent unsupported/unknown/runtime-unverified features explicitly.

The current candidate is not a migration adapter: its inspected tools handle skill listing, lookup, search, compatibility scans, runtime refresh, fix suggestions and repairs; no session/project hierarchy import/export exists. Its current MCP module also fails under the recorded SDK resolution, and its `shell=True` repair path is not protected by a complete shell grammar. Reuse no code until those are addressed.

### AKM review: reuse reader patterns, not its session projection

AKM shows a useful three-provider local reader pattern (Claude Code, Codex, OpenCode), read-only handling for OpenCode SQLite, content-hash idempotence, temp/dry-run planning, and auditable proposal staging. But its “session” is a source log plus a text-event projection that feeds an LLM summary; `sessions/**` assets store summary/topics and a local `log_path`, not the message stream. It has no canonical parent/fork/subtask edges or multimodal artifacts. Claude child traces are folded into the parent, Codex internal children are omitted, and OpenCode v2 child sessions are omitted.

Nexus should preserve raw event provenance and relations as its own durable graph, then offer summary/memory extraction as a distinct projection. The AKM `Project` is a path-selected configuration scope and should not be equated with ChatGPT Projects or Section Groups. Its task scheduler is a local execution backend, not source schedule import. The current macOS queue-owner realpath mismatch is a concrete warning: adapter identity comparisons must canonicalize both source and target paths consistently.

### Skiller review: separate the resource plane from the conversation graph

Skiller's strongest pattern is a source-aware Skills plane: canonical library identity, bundled/reference/marketplace sources, explicit agent installations, hash-based sync and conflict/secret findings. Its `Project` is a local path with a UI group and project Skills; the sync manifest carries Skills only. This is not a Session container, Section Group, or transcript format.

Nexus should keep project/session/turn/subtask/attachment/event relationships independent from this kind of installation matrix. A Skiller-like adapter may be appropriate only for the Skills subresource once the destination supports native Skills paths. Its SUL license is a reuse restriction, and source behavior should be reimplemented from public semantics if commercial distribution is planned.

### venv-manager review: environment identity is not conversation identity

venv-manager models `environment → optional project filesystem path + tags`, package snapshots, and recovery. This is a separate dependency-state subresource that may be referenced by a Nexus Project, but must never be substituted for a chat Project/Section/Session edge. Its MCP server's safe mode is an agent-facing mutation policy, not migration authorization; the `confirm` argument is not proof of human approval. Keep a future resource adapter read-only/allowlisted and explicitly report that the reviewed MCP ephemeral sandbox path is unimplemented. It provides no evidence for moving Destruction Era history or hosted Cloud sessions.

### Kiro source adapter: preserve the session graph separately from its dashboard

Config Control for Kiro demonstrates a useful Kiro local-source inventory: workspace path, local session ID, engine, agent/model, user-message count, usage/context counters, parent-session ID and `createdReason`. Map subagent containment (`parentSessionId`) separately from tangent/rewind branching (`createdReason` plus `parentSessionId`); don't collapse both into one generic parent. Preserve Kiro dashboard metadata (local title/bookmark/tags), Kiro-native tags, and the app's independent local labels as distinct source-qualified fields.

The reader is deliberately metadata-only and does not expose transcript events or attachments. For a real Kiro source, use the documented local V3 `/chat save` archive or another explicit export contract, not this UI's dashboard endpoint. Kiro Cloud history lives in a distinct remote store and its save/load archive commands are unavailable there; leave this edge unsupported rather than treating a visible listing/resume command as a transcript transfer. Kiro Memory uses its own preference/semantic types and Global/repository scopes; model it as a separate resource, not messages or instructions.


### Secret references must stay outside the portable conversation archive

Symaira Vault is a useful adjacent architecture for encrypted credentials, per-agent MCP scope, human approval and server-side API-key resolution. Nexus should keep `SecretReference` (provider, opaque entry/field handle, scope, provenance and last validation status) separate from `SessionEvent`, Skills/MCP config and message attachments. Migration bundles may carry a user-approved *reference* only when the destination can resolve it; they must never embed the vault's decrypted value, a bearer token, or source authentication material by default. Vault entry paths and password-manager collection nesting are not Project/Section/Session edges.


## Adjacent candidate boundary: Artbucket is not Nexus Memory's canonical graph

Artbucket is useful evidence that a resource-plane API can make Projects explicit, bind keys/scopes to project access, expose a stable MCP/tool contract, and model domain-owned Collections, brands and nested content sections. Its documented ZIP/PDF importer adds a strong safe-migration pattern: produce a plan, ask a person to review, apply, support undo, and enumerate metadata that did not travel.

Do not import its nouns as universal equivalents. Artbucket Projects are DAM libraries; Collections are asset sets; brand-page sections are page content. Its assistant chat UI's `chat` ID and turns belong to a separately configured `ASSISTANT_URL`; this codebase stores only the active ID in browser sessionStorage, and no server-side transcript importer/exporter or Cloud writer was found. Nexus's canonical portable graph still needs explicit source-specific entities/edges for session/project/section, parent/child/branch, records/turns, attachments, tool calls/results, timestamps, and source-native metadata; a target adapter must record each unsupported projection as a named loss rather than pretending Artbucket's catalog is isomorphic.

Treat Artbucket as an API governance and reversible domain-import design reference only, subject to its AGPL-3.0 license and the fact its own hosted Cloud product is closed. Evidence: `docs/research/evidence/artbucket-review-2026-11-20.txt`.


## Adjacent Skills-plane design: yeasy/ask

ASK's 19 explicit agent destination directories, local/global scopes, stable `ask.yaml`/`ask.lock`, source commit pinning, and safe path-copy/install flow provide a concrete reference for Nexus's Skills adapter layer. A portable bundle should record the original repository URL/ref and exact commit, validate SKILL.md, calculate source hash, scan for suspicious content, and project only to supported target directories. Keep the neutral Skill payload separate from harness-specific MCP/plugin/hook/resource configuration, and render a target capability/loss report; file presence is not session fidelity.

ASK itself does not cover chat history, Projects/Section Groups, conversation branches, attachments, tool execution, token accounting, memory, schedules or Cloud API-key session writes. Its local UI is intentionally loopback-only and unauthenticated; reuse the packaging/user experience patterns, not its server as a remote SaaS control plane. Evidence: `docs/research/evidence/yeasy-ask-review-2026-11-20.txt`.


## Adjacent asset plane: seed-forge/harness-ai-kit

`harness-ai-kit` reinforces the case for separating a **PortableAssetManifest** from the canonical conversation graph. Its typed manifest/lock stores reusable Skills, CLIs, plugins, hooks, subagents, MCPs and loops and resolves versions/checksums before staged runtime materialization. Nexus can borrow the declared-source + lock + validation + dry-run/stage/commit pattern. Preserve each asset's source/ref/hash and each destination's native install mode; after staging, separately validate that the target actually registers or can invoke the asset.

Keep the boundary explicit: this asset manifest does not model imported ChatGPT Projects, Section Groups, sessions, parent-child or branch edges, message/turn order, images/files/link references, tool calls/results, usage/token counts, or scheduled chat tasks. `LoopState` is orchestration progress (iterations, status, convergence metrics/errors), not a chat `SessionEvent` stream. A target that lacks native semantics must receive a loss report or a linked archival bundle rather than a falsely “equivalent” native project.

Also pin adapter contracts to published artifacts: current source advertises version 0.18.18 but PyPI still serves 0.2.0; the 0.18.18 PyPI upload workflow failed with an OIDC project-token error. Do not claim unsupported runtime profiles or managed-asset registration merely because main-branch code declares paths. Evidence: `docs/research/evidence/harness-ai-kit-review-2026-11-20.txt`.


## Skills-plane reference: 24KaratAu/openhub

OpenHub is a local repository catalog and SKILL.md exporter, with a useful installed-skill scanner and update flow that backs up old skill directories before replacement and restores them after a failed update. Nexus may borrow source/version display, target path preview, and tested reversible updates. Its “operation history” is repository/action audit (installed/exported/failed/updated), not an AI conversation event log. It does not supply the canonical Project/Section/session graph or a provider-side Cloud conversation writer.

Keep asset installation independent from session migration: a `SKILL.md` content digest/version is one portable asset object. A successful write into `.claude/skills` or `.agents/skills` is only a filesystem projection; target readiness still requires native discovery/activation and dependency validation. Do not infer Windsurf/Roo/Cline/AutoGen/CrewAI parity solely from a README matrix. Resolve duplicate slug destinations, ask before overwriting, and preserve unsupported fields in a loss report.

Security and testing boundaries: its updater validates tar paths, but plain export overwrites same-slug files; the installer uses a shell command composed from a repository slug; and `run_all_tests.py` deletes a default HOME cache DB. For Nexus, use argv-based process invocation, private temporary HOME/workdirs, explicit user-controlled write boundaries, and never let a vendor's test runner touch a user's catalog DB. Evidence: `docs/research/evidence/24karatau-openhub-review-2026-11-20.txt`.

## NanoFile connector: host manifests and conversation graph are separate planes

`xiaode-ai/nanofile-connector` is a bounded example of colocating a Windows-local MCP tool catalog, `SKILL.md` directories, and host-specific manifests. It does not model chat history or Projects/Sections. Nexus should keep a `PortableAssetManifest` and host-specific activation/configuration adapters separate from its canonical `Project/Section/Session/SessionEvent` graph; a declared MCP server or copied Skill is not evidence of session restoration.

The adapter must pin and report each manifest dialect rather than ship one file and claim universal compatibility. The reviewed root manifest follows Antigravity's schema, while current OpenAI portable Agent Plugins expects a root portable `plugin.json` and a typed/schema-declared `mcp.json`; Claude Code has its own `.claude-plugin` validation rules. Native discovery and activation must be verified per host/version before marking any asset as migrated.

For stdio MCP adapters, buffer UTF-8 newline-delimited messages independently of OS chunk boundaries, negotiate the supported protocol lifecycle rather than hardcode an old revision, send required lifecycle messages, surface stderr/process-exit errors, and test fragmented/combined output with a synthetic server. Store installer artifact hashes/signatures and pin versions before replacing binaries; never run a release script that stages/commits/pushes as part of ordinary import. See `docs/research/evidence/nanofile-connector-review-2026-11-20.txt`.

## Obsidian Skills Manager: preserve asset identity; never flatten into instruction files

The Obsidian Skills Manager demonstrates a library UI, provenance/version fields, and staged install/rollback, but its cross-tool exporter strips frontmatter and merges all Skills into one fixed Markdown file per host. Nexus should retain each `Skill` as its own source-qualified, content-hashed object with license/dependency/provenance and target-specific activation result; a merged rules/instructions file should be a separate lossy projection with an explicit diff, backup, and overwrite approval.

Do not migrate Obsidian plugin `loadData` wholesale into a portable bundle: it can contain GitHub PATs and registry API keys. Model these as secret references and re-authenticate at the destination. Treat finite content scanners as advisory findings, not proof of safety; verify scripts and referenced assets separately. The candidate has no declared license, so it is not a dependency source. Evidence: `docs/research/evidence/obsidian-skills-manager-review-2026-11-20.txt`.

## tool-cli: MCP server configuration is its own adapter plane

`superradcompany/tool-cli` is the clearest reviewed sample so far of managing installed MCP tools and writing host-specific registrations across multiple CLI/desktop clients. Borrow the explicit host registry, format-specific serialization, dry-run preview, overwrite policy, managed-entry metadata, confirmation, and config backup. Preserve these as `HostMcpConfig` operations—not as `Session`, `Project`, or `Section` data.

The distinction must survive in the canonical graph: MCP tool/package identity, launch transport, environment/args, OAuth state, installed version and host registration are independent resources. `tool-cli` encrypts credentials separately with a local key file; Nexus should export only secret references and require destination re-authentication. Its cookbook LangChain sample's in-memory message list/token tracker is not a durable session format and has no bearing on tool-cli's MCP host manager. Evidence: `docs/research/evidence/tool-cli-review-2026-11-20.txt`.

## JUP: Skills synchronization is a resource plane, not a session graph

`andrader/jup` provides a practical reference for source-qualified Skill installation, lock metadata, configurable local/global harness skill directories, and link/copy synchronization. Keep this behind `PortableSkill` / per-host activation adapters. A `skills.lock` entry describes the Skill source and installation locations; the function named `skills_lock_session` only serializes read/update/save of that lock file and is not an assistant conversation session.

Do not infer Project/Section, transcript/event, fork/child-task, attachment, token, MCP/plugin, memory, schedule or Cloud-session portability from multi-harness Skill sync. JUP has no such data plane. Its sync code can remove an existing same-slug destination before creating a link/copy, so Nexus should preflight collisions, preview, back up and require an explicit overwrite decision. The reviewed checkout had no license file; retain it as a behavioral reference, not a dependency. Evidence: `docs/research/evidence/jup-review-2026-11-20.txt`.

## TKMD: Task-to-session references are not portable Session records

`ktreharrison/tkmd` is a useful task-orchestration reference: Markdown task cards have status, owner, project label, `blocked_by`/`blocks` edges, eval receipts and one latest `session_id` plus a `sessions[]` list of agent-to-ID references. Its `.events.jsonl` audit records task transitions and session-ID metadata. Preserve this as a distinct `Task` / `TaskSessionReference` adapter; a task DAG does not represent primary/controlled conversation hierarchy, and a project string does not create a Project/Section container.

`tk u` delegates continuation to the source harness CLI (`claude -r`, `codex resume`, etc.). It does not read or migrate the referenced transcript; on a different host/account the ID may not resolve. Do not equate a successful `tk u` launch with migrated history, and do not auto-run imported full command strings or task `eval`/`on_done` actions. The MCP server is a task API, not an MCP configuration importer or conversation archive. Evidence: `docs/research/evidence/tkmd-review-2026-11-20.txt`.

## Grimoire: a strong asset plane, separate from the session graph

`grimoire-rs/grimoire` is the strongest reviewed implementation so far for **versioned agent assets**: a typed `Artifact` declaration, digest-pinned `grimoire.lock`, per-client capability decision, staged host-native projection, and output drift/install state. It covers Skills, Rules, Agents, MCP descriptors, bundles and optional hooks/settings; plugin export creates separate Claude and Agent Plugins (Codex) layouts. Borrow this as a resource plane behind Nexus's client adapters, not as the canonical `Project/Section/Session/SessionEvent` schema.

The official matrix targets Claude Code and many coding clients, while a distinct marketplace guide describes distributing plugin packages into ChatGPT/Codex and Claude Desktop Chat/Cowork. None of these package/marketplace surfaces moves Project membership or conversation history. Anthropic documents that Claude Code plugin sync requires Claude-account sign-in and does not run with API-key/cloud-provider auth; the Desktop marketplace guide covers Chat/Cowork, not session import. A local MCP descriptor path was explicitly refused by the CLI (exit 64); the tool's MCP support consumes pinned registry artifacts and projects them into client config. Keep imported MCP commands, hooks and credentials as inert, separately reviewed resources. Evidence: `docs/research/evidence/grimoire-review-2026-11-20.txt`.


## Claudia: task hierarchy is a separate workflow plane, not a session graph

`yuvalsuede/claudia` is useful as an adjacent design reference for task/project/sprint management and task-scoped structured context. Its SQLite schema has Projects, Sprints and Tasks; task `parent_id` yields a task tree, while dependency edges are modeled separately. It has no Section or conversation-session entity. The README's “remember context between sessions” means bounded JSON stored on a task (65,536 serialized characters in the implementation), not persisted turns or a portable session lineage.

Its generated `session-<8 hex>` MCP identity labels the current server-side agent for task ownership; it is not a Claude session identifier and is not durably linked to transcript content. Current project selection is process-local. A task can carry image URL/path/base64 metadata, but there is no ordered multimodal message/event stream. The bundled Claude plugin/skill and `.mcp.json` example should be treated as one host integration only. Do not map Claudia task parents to ChatGPT/Claude session parents, or its Projects/Sprints to ChatGPT Projects/Sections without an explicit, loss-reported conversion. Source evidence: `docs/research/evidence/claudia-review-2026-11-20.txt`.

## skillpm: npm-packaged Skills are an asset plane, not a Session migration

`sbroenne/skillpm` is a useful, narrow reference for distributing portable `SKILL.md` assets through npm: dependency semver/lockfiles, recursive `node_modules` scanning, npm workspace symlinks, duplicate frontmatter-name rejection, and project-scoped delegation to a client installer. It pins `skills@1.7.0`; current upstream `skills` is separately versioned, and current agent targets must not be assumed for the pinned version without testing. A synthetic Codex-context probe copied the skill byte-for-byte into `.agents/skills/demo-skill`.

Do not treat this as project/session migration. It has no Projects/Sections, session/transcript graph, message turns, attachment events, token accounting, memory lineage or scheduling. `uninstall` also left the copied skill and `skills-lock.json` after removing the npm package; cleanup needs an explicit preview/remove transaction. Skill host frontmatter and tool permissions are not universally portable. Full project configuration is explicitly out of scope in the repo and points to APM. Evidence: `docs/research/evidence/skillpm-review-2026-11-20.txt`.

## TiguClaw: strong session-graph reference, not a cross-harness migrator

`tigu77/tiguclaw` is one of the closest reviewed **self-hosted runtime/session-model references**: local threads across channels, provider session aliases, JSONL transcripts, ordered tool items, project links, and explicit branch lineage with transcript/chat/time cutoffs. Its Claude branch path calls the Agent SDK's `forkSession` and checks the resulting copy's final-message boundary before committing lineage. Borrow the distinction between logical thread, provider-native session, transcript timeline, and child branch checkpoint.

Do not treat TiguClaw's schema as an import/export tool. Projects are folder/`PROJECT.md` entries linked to conversations; no nested Sections/Section Groups or ChatGPT Project parser is present. Claude SDK JSONL is indexed for sessions TiguClaw already owns; no external harness transcript importer/exporter was found. Codex/OpenAI turns are stored as local transcript rows/tool items, not native provider forks. Project config formats for Skills/MCP are runtime extension surfaces, not session migration. It is a valuable design reference for Nexus's canonical Session/Thread graph, but every provider checkpoint and content-loss boundary must remain explicit. Evidence: `docs/research/evidence/tiguclaw-review-2026-11-20.txt`.

## Secrets are references, not session payloads

`forest6511/secretctl` is an adjacent local credential vault, not a migration tool. Its MCP exposes masked secret metadata and policy-gated command execution with secret values injected into a child process environment; it has no conversation/session/project/section model. For Nexus Memory, preserve only a named target-side credential reference in an import manifest and let the target resolve it from a vault—never copy raw API keys into transcript, Project or Skill data. A secure secret MCP server is not the same as migrating MCP configuration. Evidence: `docs/research/evidence/secretctl-review-2026-11-20.txt`.

## Skillet: host-specific asset materializer, not a session adapter

`Brattlof/skillet` is a MIT Go package manager for Skills, MCP, and Claude Code-specific commands/hooks/subagents/output styles. The code’s client table writes MCP to Claude Code project `.mcp.json`, Cursor, Windsurf, Gemini CLI and Cline; its shared `~/.agents/skills` path is the Skill interoperability surface. It records origin/commit/checksum in manifests and lockfiles, supports frozen verification, and merges JSON configs while retaining unrelated keys. This is a useful asset-plane pattern, not evidence that a target host has activated the result. No ChatGPT Project/Section/Session, Claude Desktop Chat/Cowork/Code session, transcript/attachment/branch, memory, schedule or Claude Cloud/API-Key session writer is present. Treat each asset conversion separately from Session graph fidelity. Source/evidence: `docs/research/evidence/skillet-review-2026-11-20.txt`.


## Toki: workflow Project is not a conversation Project

`harperreed/toki` models a path/UUID Project that contains Todo records and exposes task CRUD via a stdio MCP server. It can export a task catalog, but it has no Session, Section, transcript, event, branch, attachment, memory or schedule graph. Keep such a task store separate from Nexus's source-qualified Session/Project/Section graph. Its YAML importer can silently finish after per-item errors, backend migration is not transactional, and the SQLite backup copies only the main DB file; these behaviors are not a fidelity or rollback model. Evidence: `docs/research/evidence/toki-review-2026-11-21.txt`.


## Agent Farm: local harness-session observation, not cross-harness migration

`greenfield-inc/agent-farm` is one of the strongest reviewed references for a separate local session-observation plane. It launches Claude Code CLI and Codex CLI profiles, assigns Agent Farm launch/session IDs, records OTLP spans/logs/metrics and explicit parent-session links, and can normalize those streams into user/assistant/tool turns with token and cost fields. Keep `AgentFarmSessionId`, native provider session ID, `LaunchId`, trace/span IDs, and logical parent edges distinct. Its provider config also demonstrates a useful env-name-only secret reference for local CLI gateways.

Do not treat it as a session importer. The `telemetry export` bundle is filtered event evidence: it contains metadata/logs/metrics but deliberately omits `traces.jsonl`, so the source needed for its normalized turn graph is lost. No external ChatGPT/Claude transcript import, target Cloud writer, or replayable canonical archive was found. It supports Claude Code/Codex CLI, not Claude Desktop Chat/Cowork/Code. Content capture is opt-in, telemetry is local, and the default launch disables both harness approval prompts without filesystem isolation; use separate worktrees before testing. Evidence: `docs/research/evidence/agent-farm-review-2026-11-21.txt`.


## Agent Farm: local harness-session observation, not cross-harness migration

`greenfield-inc/agent-farm` is one of the strongest reviewed references for a separate local session-observation plane. It launches Claude Code CLI and Codex CLI profiles, assigns Agent Farm launch/session IDs, records OTLP spans/logs/metrics and explicit parent-session links, and can normalize those streams into user/assistant/tool turns with token and cost fields. Keep `AgentFarmSessionId`, native provider session ID, `LaunchId`, trace/span IDs, and logical parent edges distinct. Its provider config also demonstrates a useful env-name-only secret reference for local CLI gateways.

Do not treat it as a session importer. The `telemetry export` bundle is filtered event evidence: it contains metadata/logs/metrics but deliberately omits `traces.jsonl`, so the source needed for its normalized turn graph is lost. No external ChatGPT/Claude transcript import, target Cloud writer, or replayable canonical archive was found. It supports Claude Code/Codex CLI, not Claude Desktop Chat/Cowork/Code. Content capture is opt-in, telemetry is local, and the default launch disables both harness approval prompts without filesystem isolation; use separate worktrees before testing. Evidence: `docs/research/evidence/agent-farm-review-2026-11-21.txt`.


## Credential plane is separate from portable context

The LocalVault review reinforces a hard Nexus Memory invariant: provider/API credentials, OAuth tokens, MCP secrets, and decrypted unlock/session-cache keys are never transcript artifacts and never enter portable bundles. Store secret references (vault/key/environment variable), provenance and required destination scopes separately; require explicit user re-binding or just-in-time process injection on the target. Do not export plaintext to model context merely to make a migration “complete.” LocalVault’s MCP and process-injection design is an adjacent reference, not a dependency; its Claude Code guard is fail-open and cannot replace OS/process isolation. See [review evidence](research/evidence/localvault-review-2026-11-21.txt).


## Profile adapters are not session adapters

CueCards provides a useful data-plane pattern for Nexus Memory: distinguish full native runtime adapters from partial external writers, and state per-adapter capability/loss explicitly. Its project pin selects a composable asset profile (Skills/MCPs/plugins/persona/gates), but its nine non-native agent adapters materialize Skills/rules and MCP files rather than the whole profile; the two full runtime targets are Claude Code CLI and Codex. This does not transport conversation events, Project/Section membership, forks, attachments, token usage, or native resumes. Treat Skills/MCP transport as one asset plane; keep Session/Message/Tool/Event graphs and provider-auth (which must be re-bound, not copied) as separate planes. Cue's local usage event model and repo-only importers are not shipped session archives. [Evidence](research/evidence/cuecards-review-2026-11-21.txt).


## Cross-Harness inventory is sensitive; skill linking needs conflict checks

The Herdr Agent Config Manager review suggests a useful narrow primitive: canonical Skill content plus per-Harness links, with read-only inventories and explicit dry-run/apply mutations. However, an inventory is not safe for automatic model context as-is: its synthetic probe showed MCP command arguments, URL query parameters and hook commands flow into JSON output without redaction. Nexus Memory's inventory/report plane must redact credential-like command/URL fields before model exposure. Also preserve a content hash per source copy; a synthetic TUI selection probe removed a divergent real `.codex` Skill copy when collapsing to the Claude version. Use conflict reports or reversible archives before canonicalization; never let a convenience link-manager silently decide which copy wins. See [evidence](research/evidence/herdr-agent-config-manager-review-2026-11-21.txt).


## Smartsheet CLI Power Tools: test prompt semantics per host

`smartsheet/cli-agent-power-tools` contains paired Claude Code and Gemini CLI Markdown agent definitions backed by one product-specific MCP tool family. This is a useful *resource-adapter fixture*, not a source Session archive. Keep agent Markdown/frontmatter, MCP tool bindings, approval/chain policy, and external credentials as separate typed assets. The Gemini bodies differ materially from the Claude copies: automated-chain language and `invoke_agent` calls appear in Gemini, including a write-approval contradiction. Therefore semantic portability must be measured per host: preserve the original file, parse metadata without executing it, render only supported tool names, then test permission and confirmation invariants. Never infer Session, Project/Section, attachment, memory, or scheduler migration from prompt packaging. Detailed evidence: `docs/research/evidence/cli-agent-power-tools-review-2026-11-21.txt`.


## Lokalite: keep credentials outside portable context

`RubenGlez/lokalite` illustrates a credential plane distinct from Nexus Memory’s Project/Section/Session graph. Its local project/environment scopes and `lokalite://` references are useful shapes for carrying a *dependency handle* without its value. Nexus should serialize a secret dependency as `{source vault, secret-name, environment, required scope, access policy, provenance}` with value omitted, then ask the user to rebind it for the target Harness/provider. Do not migrate API tokens into transcript JSONL, MCP config, model context or migration logs. A secret vault does not configure a provider’s base URL, gateway protocol, model selection, Desktop mode, or Cloud session.

The candidate’s default MCP profile includes an environment-switch command despite being described as read-only, and its `block` tier is process-detection best effort; model these as capability and assurance details rather than a single `read_only` boolean. The client-config writer also falls back to an empty config when JSON parsing fails; add a fail-closed parse/backup/rollback adapter invariant. Evidence: `docs/research/evidence/lokalite-review-2026-11-21.txt`.

## Claude Desktop 3P is a distinct local destination and session schema (2026-11-21)

The confirmed destination is the third-party-inference Claude Desktop client for **Chat, Cowork, and Code**, not Anthropic-hosted Cloud. Model-provider authentication (`inferenceGatewayApiKey` or SSO/OIDC) is not session import authorization. For the 3P app, current official docs place Chat/Cowork state and workspaces under `local-agent-mode-sessions/`, Code session metadata under `claude-code-sessions/`, and Code transcripts in Claude Code's `~/.claude/projects/`. Preserve those as typed, linked surfaces instead of flattening into one generic `Session`; project memory, global memory/instructions, uploads, outputs, audit records, Code working folders/trust, and schedules are separately scoped. A rollout may unify Chat and Cowork into one continuous conversation, so mode is a versioned capability/state, not a fixed parent/child assumption.

The official 3P import wizard handles a limited Claude-origin set, not arbitrary ChatGPT JSON. A future writer must fail closed unless an official writer/import path is demonstrated on a disposable client version; undocumented local-state injection remains manual/unsupported. The app's 3P audit transcript is sensitive plaintext (including prompts, tool inputs/results, returned thinking, permissions and usage); backups must be protected, retention honored, and raw event logs excluded by default. Use a required coverage/loss matrix for projects/section-like grouping, attachments, files, memory, plugins/skills/MCP, permissions/credentials, scheduled tasks, Code worktrees and session ancestry. See [`claude-desktop-3p-chat-cowork-code-2026-11-21.txt`](research/evidence/claude-desktop-3p-chat-cowork-code-2026-11-21.txt).

Versioned target gate: the first-party Claude Desktop 3P wizard copies Claude.ai exports and local Cowork/Code sessions, but does not accept a generic ChatGPT history archive. It is a one-time source-specific import, and a Desktop-to-Desktop ZIP is explicitly unencrypted and omits auth credentials/connector sign-ins/permissions. A gateway API key selects inference; it is not a history authorization. Treat import version thresholds, app version, OS and per-mode native resume as adapter inputs, and do not write local application stores until a supported import route or disposable per-version test proves discoverability and resume.

## Claude Desktop 3P documentation refresh (2026-11-22)

The current official 3P docs now make the user-selected destination more concrete: Claude Desktop on third-party inference includes Chat, Cowork, and Code, routes inference to a configured provider, and persists conversations locally. The supported developer-mode gateway path reads Desktop's own third-party-inference configuration; it is not equivalent to setting a CLI `ANTHROPIC_BASE_URL`. An active gateway does not offer Anthropic-hosted cloud environments or Remote Control. Keep that target distinct from Anthropic-hosted Code/Cowork cloud sessions and from a standalone local Claude Code CLI.

The published store shape is explicitly mode-specific: Chat/Cowork state, workdirs, uploads, outputs, project memory, and audit records under `local-agent-mode-sessions/`; Code session records under `claude-code-sessions/` and transcript JSONL under the shared `~/.claude/projects/`. The native 3P wizard copies Claude-origin history and local prior Cowork/Code sessions; it does not establish a ChatGPT-origin writer. This updates our knowledge of the target data layout, not the portability contract: target version/OS tests, import recognition, native resume, and integrity checks remain required before enabling a writer. Evidence: [`claude-desktop-3p-current-review-2026-11-22.txt`](research/evidence/claude-desktop-3p-current-review-2026-11-22.txt).

## Session identity versus activity aggregates (Ocul-PM review, 2026-11-21)

Keep four concepts distinct: product Project/space, native conversation ID, observed work-activity session, and application window state. Ocul-PM demonstrates that one watcher work session can include multiple native conversation IDs plus file events without providing message ancestry. Nexus must never infer parent/child/fork relationships from a list of session IDs or shared workday. Also avoid copying raw hook-inbox implementations that append full prompt-bearing JSON with ambient umask and no TTL; consent, secret filtering, restrictive modes, retention and evidence minimization are explicit requirements. [Evidence](research/evidence/ocul-pm-review-2026-11-21.txt).

## Distinguish application UI state, conversation history, and operation audit (Norte review, 2026-11-21)

Norte demonstrates three independent records that use similar “session” language: its versioned `session.json` is a cross-frontend screen-state document; the assistant's `Turn` vector is an in-memory conversational context; the MCP agent's session label scopes permissions and file-operation audit/undo. Only the UI state is persisted by `SessionBody`; the assistant conversation is not in that body, and the journal contains actor/time/op/path/reversal data rather than messages. Nexus must represent `UiResumeState`, `AgentConversationId`, `OperationAuditEntry`, and `ConversationThread` as distinct types and never infer a parent/child conversation graph from an operation actor ID or a shared filesystem scope.

The hash-chained operation journal is a useful *audit-plane* model (tamper-evident provenance plus reversals), not a transcript store. The repository's broad agent support through MCP and provider adapters should be tracked independently from portable Skills/MCP configuration and from Projects/Sections/session migration. Component licenses also vary: core/AI/MCP are AGPL-3.0-only, while protocol/frontend libraries are MIT OR Apache-2.0. Full evidence: [`compilando-norte-review-2026-11-21.txt`](research/evidence/compilando-norte-review-2026-11-21.txt).


## Keep task/work-session graphs distinct from conversation graphs (MTIX review, 2026-11-21)

MTIX shows that a useful cross-harness work plane can store project-scoped task hierarchies, prompts, acceptance criteria, agent assignments, annotations, task history, and agent-run Sessions while still having no provider transcript. Its Session is a lifecycle record that summarizes tasks; its context chain is a work briefing. Nexus must use distinct Project/Section, TaskGraph, AgentRun, and ConversationThread models, and may import MTIX metadata only through an explicitly lossy/task-specific adapter—not treat task session_id as a provider conversation handle. [Evidence](research/evidence/hyper-swe-mtix-review-2026-11-21.txt).


## A tmux handle is not a native conversation identifier (todo-cli review, 2026-11-21)

JoeyWangTW/todo-cli persists task fields and a gemini-task-nanoid tmux session name, then captures pane output for display. It does not persist Gemini CLI's native session ID or transcript. Gemini CLI separately stores project-hash-scoped conversations and supports resuming by session ID. Nexus should model Task, HarnessProcess, NativeConversationSession, and ConversationThread as separate linked records, and require an explicit native session binding before claiming resumability. [Evidence](research/evidence/todo-cli-review-2026-11-21.txt).


## External design reference: CocoaSkills (reviewed 2026-11-21)

CocoaSkills informs the resource-install boundary, not the conversation model. Borrow canonical skill bundles + dependency locks + content hashes + explicit target adapters. Its MCP integration demonstrates managed native-config ownership, drift-aware reconciliation, explicit consent, staged output, and transactional recovery. Nexus should express these as independent SkillBundle, ResourceInstall, McpServerDeclaration, ConnectorAuthReference, and ConversationSession entities; a session may depend on a skill/MCP config but must never be collapsed into that dependency. CocoaSkills omits Claude Desktop Chat/Cowork and models Claude Code only; do not infer the desktop matrix from its CLI adapter. Evidence: docs/research/evidence/cocoaskills-review-2026-11-21.txt.


## External design reference: Conus (reviewed 2026-11-21)

Conus is a useful example of binding an AgentSession identifier to a Project and task claims, then recording typed SessionActivity and TaskEvents. It also distinguishes Conus's own primary key/ref from the harness's agent_session_id. Nexus can borrow this mapping and audit/event-ledger pattern, but should represent Task.parent separately from Session.parent/fork/continuation, and retain source transcript/message/media/token metadata outside a volatile 30-day activity table. Conus's Session source (startup/resume/clear/compact) is accepted but not persisted as a Session field at the reviewed commit. The implementation is not a session migrator. See docs/research/evidence/pandusss-conus-review-2026-11-21.txt.


## External connector boundary: CData Google Ad Manager MCP (reviewed 2026-11-21)

This archived sample illustrates a provider data-source adapter: a local stdio MCP process wraps an external JDBC driver and exposes metadata/query tools. It is not a HarnessAdapter, SessionSerializer, Skill/MCP package manager, or conversation migration path. Nexus should keep external resource connectors and conversation/session adapters separate. The source README's CRUD claim conflicts with its read-only banner and the registered metadata/query-only tools, so this repository should be treated as a dated setup example, not a quality template. Evidence: docs/research/evidence/cdatasoftware-google-ad-manager-mcp-review-2026-11-21.txt.

### Harness capability facts need provenance and surface/version dimensions (candidate review, 2026-11-21)

`evoerax/awesome-harness-engineering` is a useful negative design test: a static cross-harness checkmark matrix can look comprehensive while stale. Nexus's capability inventory should require `{harness, exact surface/mode, version/as-of date, scope, behavior, source URL or local probe, evidence class, confidence, unsupported/loss boundary}` per claim; hooks, MCP clients/servers, Skills, plugins and session stores are distinct capabilities. For example, Codex hooks and OpenClaw hooks/MCP now exist despite the candidate's “not supported” cells. Never turn a third-party list or skills-format match into proof of native Project/Section/Session restore. Keep Claude Desktop Chat, Cowork, and Code as separately assessed session surfaces and credential routing separate from persistence/import semantics. Evidence: `docs/research/evidence/evoerax-awesome-harness-engineering-review-2026-11-21.txt`.

### Artifact catalog is a separate memory plane (Artmark review, 2026-11-21)

Artmark is a strong narrow example of **artifact rediscovery**: canonical source identity + aliases, source-owned facts, agent-generated retrieval card, local lexical index, and an explicit return to the authoritative provider for current contents. Nexus may model this as `ArtifactPointer` + `CatalogCard` + `ResolverReference`, with provenance and consent, and link it from a `Message`/`Thread`; do not use the catalog as a substitute for transcript replay or a Session's parent/branch graph. Keep memory cards distinct from raw messages, attachments, token usage and schedule runs. The artmark Skill and its `context init` are instruction-plane injection, not ChatGPT or Claude Desktop session restoration. Its credential scanner is a design lead, not a blanket guarantee; URL credentials are filtered, arbitrary secret text and sensitive summaries still require separate controls. Evidence: `docs/research/evidence/artmark-review-2026-11-21.txt`.

### SkillPack informs ResourceInstaller shape, but not portability proof (2026-11-21)

`skillpack-manager` is an adjacent Skills-plane reference for a versioned `SkillBundle`, target-directory adapter registry, install record/checksum, diff/sync and source workspace. Nexus may borrow those separate resource entities; it must not equate byte-copying a Skill into `~/.claude/skills` with semantic compatibility, a Claude Desktop mode integration, or Session restore. More importantly, the reviewed implementation has no safe path boundary: manifest `skill.path` escapes are used by `path.resolve`, `skill.name` is joined into the target path, and the copy helper never verifies containment. Our temporary CLI probes demonstrated an outside-target write and copying a sibling source directory; the static audit called the latter clean/Low risk. Nexus's importer must reject traversal and symlink escapes for both source and destination, use a staged atomic transaction with rollback, and test malicious archives/manifest values before copying. Evidence: `docs/research/evidence/skillpack-manager-review-2026-11-21.txt`.


### AgentPM reinforces the separate resource plane (reviewed 2026-11-21)

`agentpm.yaml` plus `InstallRecord`/`RuntimeContextGraph` is a useful model for resource provenance and layered availability: global, project and temporary Skill installs can identify source, adapter, scope, target path and revision. Nexus can borrow a versioned `ResourceBundle`/`ResourceInstall` ledger and idempotent reconciliation pattern, but must not collapse these into `ConversationProject` or `Session`. AgentPM's project manifest does not model ChatGPT Project containment, source-qualified Section membership, session parent/fork/subtask edges, messages, attachments, token usage or scheduled runs. Plugin marketplaces and MCP declarations are also distinct resource classes. Claude Desktop Chat, Cowork and Code need independent adapters even when the same third-party gateway is configured. Evidence: `docs/research/evidence/travelhawk-agentpm-review-2026-11-21.txt`.


### AY Claude CLI is a narrow ResourceInstaller example — rejected for adoption (reviewed 2026-11-21)

The npm 1.0.0 tarball matches these source boundaries, so do not treat package publication as a safety fix. 

The package marketplace groups Skills, agents, commands, hooks, plugins, MCP-labelled packages, and settings under a Claude Code-only resource installer. This may help enumerate a `ResourceBundle` inventory, but its local “TeamWorkspace” is a membership/package/settings collection, not `ConversationProject` or `Session`. Do not derive a chat hierarchy from its workspace names or infer Claude Desktop support from Claude Code paths. Its source writes only to `~/.claude`/`cwd/.claude` and omits `CLAUDE_CONFIG_DIR`, despite Claude Code's current documented support for relocating settings/history/plugins.

It is also a negative security reference: package slugs are joined into destination paths without containment; a synthetic call to the actual source escaped `.claude/skills` in a disposable HOME. JSZip sanitizes forward-slash `..` entries, but preserves a Windows backslash path that `path.win32.join` resolves to `.claude/settings.json`; add canonical containment checks after normalization and test both archive encodings/platforms. The built-in `hook.sh` template is blocked by the `.sh` suspicious-file rule. Do not use this implementation on user data or import its security claims. Full evidence: `docs/research/evidence/ay-claude-templates-review-2026-11-21.txt`.


### A local MCP process is not a conversation adapter — ZLaunch Manager review (2026-11-21)

`zavora-ai/macos-zlaunch-manager` demonstrates a stdio MCP tool bridge around a macOS OS service manager. Its 19 `launchd_*` operations have an external-resource side-effect plane, not a `SessionSerializer`, `ConversationProject`, or `Section` model. Model the connector and its tool approval/risk metadata separately from conversation content, and never infer transcript movement from MCP availability. The MCP server directly exposes service creation/deletion and plist writes; an isolated source POC confirms label path escape outside the intended LaunchAgents root. Require server-side authorization/confirmation and canonical path containment. For Claude Desktop, distinguish raw local config from current `.mcpb` Desktop Extension packaging; this project lacks that manifest/package. [Full evidence](docs/research/evidence/macos-zlaunch-manager-review-2026-11-21.txt).


### Agent Manager informs `DiscoveryCatalogue` and `ResourceBundle`, not Session serialization (reviewed 2026-11-21)

`ai-agent-manager/agent-manager` is a positive reference for versioned discovery catalogues, source-specific bundle caches/provenance, safe namespaced Skill installs, repo vs system scope, per-harness `SkillProvisioner` classes, and a separate provider-specific Rovo provisioning flow. Nexus can borrow those resource-plane boundaries, collision rules and source pins. Do not reuse its `Session` or `Project` names as provider conversation entities: local Session means loaded catalogue/auth/membership state, while API Project is Atlassian team/project access metadata. Its Git-plugin importer only extracts Skills; MCP/plugin config, transcript/history, attachments, token ledgers, memory and schedules are outside the observed model. Keep `ConversationSession`, `ConversationProject`, `SectionMembership`, `ResourceBundle`, `McpServerDeclaration`, and `ProviderProject` distinct. Full evidence: `docs/research/evidence/agent-manager-review-2026-11-21.txt`.


### Google Marketing Agent is an MCP approval pattern, not a Session adapter (reviewed 2026-11-21)

This domain server demonstrates an important safety boundary: MCP write tools should be profile-scoped, preview a concrete Change, bind Confirmation to exact preview content/state, optionally elicit the human, snapshot prior state, and refuse rollback on drift. The released v0.3.0 only has read-only-by-default plus a boolean `confirm`; the stronger preview-ID/elicitation/rollback model exists in an open unmerged PR and must not be assumed in production. Its MCP Google account context, local OAuth credentials, Skills and `Project`/profile records are not conversation history. Model `McpServerDeclaration`/`ToolApprovalPolicy` separately from `ConversationSession`, and never substitute Google service change logs for user message transcripts. Full evidence: `docs/research/evidence/google-marketing-agent-review-2026-11-21.txt`.


### Skill package managers are a ResourcePlane, not a SessionSerializer

`SoonIter/skills-package-manager` demonstrates a pinned source manifest and broad skill-directory linker: source resolution and file placement are shared, while destination paths are host-specific. Nexus should model a Skill asset's source/revision, integrity, and per-Harness placement independently from `ConversationProject`, `SectionGroup`, `ConversationSession`, and `MessageNode`. Do not present SKILL.md portability as session fidelity: this candidate has no transcript graph, multimodal attachment preservation, MCP/plugin, memory, schedule, or Claude Desktop Chat/Cowork/Code session adapter. Its 45-name path table is useful only as a candidate compatibility inventory, not a verified guarantee of runtime activation. Keep its unmerged dependency/bootstrap PRs out of current capability claims. Evidence: `docs/research/evidence/skills-package-manager-review-2026-11-21.txt`.


### `skill-mgr` confirms the Skill plane is narrow — do not infer Session import (reviewed 2026-11-21)

`AI-Colleagues/skill-mgr` is a compact `SKILL.md` validator and five-root copy installer, with clean service/adapter/source boundaries and unusually high local test coverage. It has no conversation/session serializer and no mode-aware Claude Desktop or Cloud adapter. Its GitHub source records only the shorthand and reads the moving default branch, so Nexus's `ResourceInstall` should record immutable resolved revision + digest instead. The local-source symlink POC and same-name unmanaged-directory replacement show why a reusable provisioner needs canonical source containment, ownership/provenance markers, a conflict preview, and a preserved backup/rollback path before writing user targets. Evidence: `docs/research/evidence/skill-mgr-review-2026-11-21.txt`.


### `skills-cli` is not a Session serializer

`bl1nk-bot/skills-cli` is relevant only to a possible split between shared Skill assets and host-specific install locations. Its advertised project/global Skills merge does not supply conversation semantics. Its `.blink/sessions` metadata and ACP process buffer are execution state, while its README's future session concepts are not provider transcripts; the Claude↔Gemini converter files are unwired. Do not map these to `ConversationProject`, `SectionGroup`, `ConversationSession`, or `MessageNode`. The main crate currently fails to compile, and the registry crate also fails a check. Keep this below usable architecture references; no direct adoption or data-plane credit. [Evidence](research/evidence/skills-cli-review-2026-11-21.txt).


### `skill-hub` is a high-quality ResourcePlane reference, not conversation state

`CassianFlorin/skill-hub` models a managed Skill bundle, discovered project assets, deployed runtime copies, immutable source provenance and a rollback history. Nexus should preserve those as ResourcePlane records and keep them separate from `ConversationProject`, `SectionGroup`, `ConversationSession`, `MessageNode` and provider-native state. Its SwiftUI-on-JSON-CLI boundary is a useful macOS client pattern. The runtime named `claude` only receives Skill directory copies; do not map it to Claude Desktop Chat/Cowork/Code session support. Exact-head CI passed, but source-level symlink-copy and best-effort audit limitations matter before any direct adoption. [Evidence](research/evidence/skill-hub-review-2026-11-21.txt).


### `subagent-mcp` is an OrchestrationPlane, not a SessionSerializer

`Heretyc/subagent-mcp` is a useful reference for permission-gated interactive workers, process liveness, context-window sampling, and concise cross-turn handoffs. Keep those concepts separate from provider-native `ConversationSession` and a source conversation's message/branch graph: its `AgentState` map is process-local, the spawn-depth marker is not a durable parent edge, and handoffs are bounded summaries rather than transcripts. Its direct API-provider requests are task dispatch, not a Claude Desktop third-party-session writer. No ChatGPT Project/Section importer or Claude Desktop Chat/Cowork/Code history adapter was found. [Evidence](research/evidence/subagent-mcp-review-2026-11-21.txt).


### `hiadamhere/spm`: treat Skill distribution as ResourcePlane, not conversation transfer

The package models Skill catalogs, source revisions and per-harness folder placement; Nexus may borrow the *separation* between an immutable asset bundle and target-specific placement, but must maintain its own per-asset/per-project records and content hashes. `spm` itself stores a single install record per Skill name, not a per-project installation graph. Its public repo omits implementation/tests, while the published .NET binary's SourceLink points to an unavailable private repo; decompilation also found an unverified real-directory replacement path. Do not adopt this code or map its MCP management tools to session history. Evidence: `docs/research/evidence/hiadamhere-spm-review-2026-11-21.txt`.

### keynv: text redaction is not a SessionSerializer

keynv is an adjacent secrets/privacy plane: its Claude Code JSONL and Cursor log redactor sees raw text, while Nexus needs typed source records and target-native serializers for Project/Section/Session graphs, messages, branch edges, attachments, tools, memory and schedules. Do not conflate a secret alias vault's Project/Session labels with user conversation structures. The watcher’s active append-log read/rename race is a data-integrity warning; any Nexus redaction stage should operate on immutable staged copies, preserve original bytes, and be explicit/opt-in. It does not cover Claude Desktop Chat, Cowork, or Code. [Evidence](research/evidence/keynv-labs-keynv-review-2026-11-21.txt).

### ai-agent-skill-router: ResourcePlane routing, not SessionGraph conversion

This repository is a model-driven router plus inventory/approval/undo tool. Its Skill folders show the portability boundary of Agent Skills; MCP data is reduced to names, and Claude Code JSONL is read only for opt-in usage counts. Keep ResourceArtifact / ResourcePlacement / ResourceUsage / ApplyProposal separate from ConversationProject, SectionGroup, ConversationSession and MessageNode. Reuse none of its native session logic because none exists. Its revalidation/undo workflow is a useful inspiration, but a macOS launch through the generated Claude skill symlink can silently skip CLI main because the entrypoint guard compares noncanonical paths. [Evidence](research/evidence/ai-agent-skill-router-review-2026-11-21.txt).

### Pulse task persistence is TaskGraph, not ConversationGraph

Pulse is useful as a narrow TaskGraph reference: tag/epic → task → one-level subtask, status/order/timestamps, and local YAML per working tree, callable through a small MCP tool surface. Preserve Task / TaskGroup / TaskEvent as a distinct plane; never map a tag into ConversationProject/SectionGroup or a subtask into conversation branch/session lineage. The tool has no transcript importer, and malformed YAML can be overwritten after an empty-state fallback. [Evidence](research/evidence/pulse-tm-review-2026-11-21.txt).

### Open Skills Manager: skill deployment, not session portability

This VS Code extension is a Skill ResourcePlane discovery/deployment UI: repository → SKILL.md → IDE-specific directory. It has no conversation/session graph or target-native archive adapter. Keep SkillArtifact/SkillPlacement records separate from MCP configs, Plugins, ConversationProject, SectionGroup and SessionGraph. Its installer overwrites an existing destination tree, and cloud item names are used in the target path after only character replacement; do not reuse it as a migration transaction. [Evidence](research/evidence/open-skills-manager-review-2026-11-21.txt).


### LUCID Context Engine: retrieval is not archival memory (reviewed 2026-11-21)

Spaztazim/lucid-context-engine is an OpenClaw-specific read/retrieve/inject plugin, not a cross-Harness conversation archive: ingest() returns false, while assemble() searches QMD and adds snippets to a prompt. Keep any Nexus RetrievalPlane as an optional derived index with explicit provenance, trust labels, rebuildability, and opt-out. Never treat retrieved snippets, token estimates, or system-prompt injection as the source transcript, original memory state, or evidence that Project/Section/Session hierarchy was transferred. It has no Claude Code or Claude Desktop Chat/Cowork/Code/3P adapter.


### skm: useful Skill lockfile plane, unsafe as a migration engine (reviewed 2026-11-21)

The archived skm CLI cleanly separates requested Skill sources (skills.json), resolved commit and integrity state (skills.lock.json), cache storage (.skm), and generated target paths. This supports Nexus ResourceArtifact/ResourcePlacement provenance, but it does not represent transcript state. Keep resource installs as their own plane. Do not copy its materializer unchanged: a project output directory can pass lexical containment but resolve through a symlink to an external directory; a disposable install removed an unmanaged same-name canary outside the project. Require realpath/parent-symlink checks, managed ownership markers, non-destructive preview, and rollback before any analogous Nexus writes.


### ASM: a multi-resource projection plane, not a conversation archive (reviewed 2026-11-21)

ASM centralizes Skills, MCP definitions/binaries, and selected Plugins, then projects them back into agent homes. This reinforces separate ResourceArtifact, CredentialRef, ResourcePlacement, and AdapterCapability models; it does not provide ConversationGraph serialization. Do not reuse the implementation unchanged: no license is present, package IDs are joined to store paths without validation, MCP local-binary containment uses a string prefix, and native migration deletes the original binary before config injection completes. Store MCP env values as secret references with restrictive permissions, not plaintext resource copies.


### Omaset: shared local settings control plane, not conversation/session persistence (reviewed 2026-11-21)

Omaset’s UI, CLI and MCP surfaces share typed setting definitions and operations; its per-field atomic write, mode preservation, backup/undo and bounded subprocess ideas may inform a future Nexus Resource/Settings plane. Keep that separate from `ConversationProject`, `SectionGroup`, `ConversationSession`, and event/branch graphs. An MCP server for an application is not itself an MCP configuration migrator or transcript adapter. The repository targets Omarchy local system settings and contains no ChatGPT/Codex archive or Claude Desktop Chat/Cowork/Code gateway-session support. Test run was 23/29 on a temporary macOS-compatible fixture; do not use it as cross-platform certification. [Evidence](research/evidence/omaset-review-2026-11-21.txt).


### MCP-MegaBrain: record-based MemoryPlane, not ConversationGraph (reviewed 2026-11-21)

The local SQLite/FTS5 server shows how rules, specs, reusable patterns, and failure/fix notes can be queried by several local MCP-capable agents. Model these as a derived `MemoryArtifact` / `MemoryPlacement` plane with provenance, scope, trust and rebuild rules; do not map them to `ConversationSession`, `SectionGroup`, or source messages. It has no ChatGPT/Codex archive reader, session graph, API-key gateway writer, or verified Claude Desktop Chat/Cowork/Code session import. Its `normalize_project` collapses identities to the basename, causing common cross-project collisions; a disposable POC retrieved all four record categories across colliding project names. Its DB defaults to 0644 under umask 022 without explicit privacy controls. Keep only the MCP record/query pattern, not its project isolation or storage defaults. [Evidence](research/evidence/dougrn-mcp-megabrain-review-2026-11-21.txt).

 
### skillpm: valuable deterministic Skill ResourcePlane, not SessionGraph (reviewed 2026-11-21)

Its project/global manifest, source pins, checksums, dependency DAG, explicit supported-agent matrix, file adapters and dry-run/rollback UX are useful references for a Nexus ResourceArtifact/ResourcePlacement plane. Keep them separate from ConversationProject, SectionGroup, ConversationSession and event graphs: the adapter contract injects SKILL.md plus files and stores a ref list, not a conversation/session. The repository contains no MCP/plugin/session/memory/schedule mover; historical memory/scheduler subsystems are removed. Do not copy its filesystem transaction unmodified: temporary POCs reproduced a manifest symlink overwrite, out-of-root symlink read, skill-name collisions, crafted .. adapter path, and partial rollback leaving state inconsistent. [Evidence](research/evidence/eddieran-skillpm-review-2026-11-21.txt).


### ClaudePass: SecretPlane boundary, not ConversationGraph (reviewed 2026-11-21)

Opaque Handles, encrypted local Vault, project/global manifests, and process-bound injection are useful SecretPlane ideas; keep raw values out of exported session archives by default. Do not confuse its `.claudepass.toml` with a chat Project or its same-user Vault with per-session authorization: any process under the owner’s account can reach all handles. It has no conversation/session graph import/export, cloud relay, or attachment/history transfer. Claude Desktop Chat/Cowork/Code expose different plugin component/install surfaces; represent each as a separate capability, not one `Claude` target. Detailed scope, local-client compatibility, security findings and CI evidence: [review](research/evidence/claudepass-review-2026-11-21.txt).


### nix-agentic-tools: strong declarative ResourcePlacement pattern, not SessionGraph (reviewed 2026-11-21)

A typed shared `ai.*` source plus capability-gated runtime emitters is a strong architecture reference for Skills, MCP, agents, hooks, instructions, inference routes and global/project scope. It makes per-runtime exclusions explicit and surfaces warnings; retain that approach, but do not mistake generated config files for imported projects or conversations. Nix Home Manager/devenv are environment managers, not end-user universal migration surfaces.

Its Kiro archive/probe docs provide rich historic event-schema evidence (message union, flat sub-executions, snapshots, tool outputs and usage joins), but are pinned to KAS 2.15.1 while its package has moved to Kiro CLI 3.5.0. Current first-party Kiro docs support a versioned adapter boundary: local CLI V3 ZIP save/load or JSON scripts; cloud session state is separate; ACP V3 storage is server-owned. Revalidate every old field against current exports. [Evidence](research/evidence/higherorderfunctor-nix-agentic-tools-review-2026-11-21.txt).


### murk: scoped SecretPlane, not ConversationGraph (reviewed 2026-11-21)

Age-encrypted repo vaults, per-recipient/private/group values, time-bounded per-agent grants, tag policy and MCP/CLI access are good reference patterns for a separate `SecretReference` resource plane. Never conflate a grant with session history or a sandbox: the agent’s command runs as the user, can reach filesystem/network, and can bypass environment-only strictness unless OS isolation limits it. `murk_get` returns raw values into model context; `murk_exec` masks only exact stdout/stderr values. murk does not import/export Sessions, Projects, Sections or artifacts. [Evidence](research/evidence/interrupted-sh-murk-review-2026-11-21.txt).


### jnMetaCode/skillet — AssetPlane-only reference (reviewed 2026-11-21)

Borrow the small Git registry + resolved-commit lockfile + safe native Skill-directory installation pattern as an optional Skills adapter reference. Its stdio MCP server installs only registry Skills; it does not carry session state or configure arbitrary MCP servers. Treat installed `SKILL.md` and accompanying files as untrusted payloads until separately reviewed; installer path checks do not provide sandboxing, atomic rollback, or cross-host compatibility guarantees. No ConversationGraph, Project/Section hierarchy, attachments, usage, memory, schedules, or Claude Desktop mode session writer. [Evidence](research/evidence/jnmetacode-skillet-review-2026-11-21.txt).


### Josepavese/nido — adjacent execution ResourcePlane, not ConversationGraph (reviewed 2026-11-21)

Nido's strongest fit is a task-owned local VM execution plane with native CLI/TUI/MCP control and separate disk snapshots; it may inform a future optional isolated-run backend. Keep that model separate from Projects, Section membership, conversation branches, context and attachments. Its `MCPDurableSessions` scenario persists VM operations across tool calls, not assistant dialogue; event subscriptions are ephemeral and disk snapshots do not capture guest RAM. MCP grants local destructive host operations, and host mounts/forwarded ports/PCI cross the guest boundary, so it is not automatically a safe sandbox for arbitrary agent payloads. [Review evidence](research/evidence/josepavese-nido-review-2026-11-21.txt).


### LiorStrugach/task-manager-mcp — adjacent Task/Plan plane only (reviewed 2026-11-21)

Its flat task records, ordered plan steps and notes can inform a lightweight Task / PlanStep domain module, but should not be mapped onto conversation ancestry or Section membership. The app's JSON import/export covers only its own task/plan/notes data; it cannot resume model context. Do not depend on this repo: the tested package omits its console entrypoint module, its tests import a missing file, and its unbounded MCP SDK requirement is incompatible with current SDK v2. [Evidence](research/evidence/liorstrugach-task-manager-mcp-review-2026-11-21.txt).


### AnyIsland: adjacent package registry, not Harness session interchange (reviewed 2026-11-21)

The `anyisland.json` manifest/SQLite registry can inform a future typed package/resource inventory only. It carries no source session event stream, Project/Section membership, branch/fork/task relation, attachment payload, memory, or automation definition. Do not treat its shell-history text as transferable memory: the current `Encrypt` implementation reveals plaintext and a key prefix. A new Nexus `PackageArtifact` or `ShellCommandEvent` would be independent of `ConversationSession`; any future shell-history module must use real cryptography, bounded/verified redaction, explicit opt-in, and a tested restore path. Do not reuse AnyIsland's build execution path without sandboxing and transaction safeguards. [Source/test ledger](research/evidence/anyisland-review-2026-11-21.txt).


## Claude Desktop third-party inference is an endpoint plane, not a session plane (2026-11-21)

Model Claude Desktop Chat, Cowork, and Code as three separately verified workflow adapters sharing one configured provider plane; do not collapse them into an assumption that a gateway holds or imports all client state. The current first-party Desktop docs expose Gateway base URL + credential, require an Anthropic Messages API endpoint (`POST /v1/messages` streaming/tool use), and note cache-control use across Chat/Cowork/Code. The local app configuration is not equivalent to Claude Code CLI `ANTHROPIC_BASE_URL`/settings or account-backed Claude Code Cloud. Store credential handles under a `SecretReference`/secret-manager binding; exports must not serialize raw gateway keys.

Keep an explicit `ConversationGraph` with independent source-qualified identity, containment, sidebar grouping, branch/fork/subtask/subagent/workflow relations, ordered event/message lineage, and separate artifact/attachment/media/token/memory/schedule links. The user-confirmed Section Group label should be represented without assuming a destination-native identical object. For Claude Desktop 3P, current docs describe a local session store; its native import is one-time and source-specific to Claude.ai archives and local earlier Cowork/Code sessions, not a general target API. Hence first-phase output should be a loss-aware portability bundle plus target-specific, version-gated importer, with per-field fidelity labels and a reversible run manifest. Desktop Chat, Cowork, Code, and local/self-hosted Code each need their own golden fixtures and resume verification.

### skillspp #98 — adjacent Skills ResourcePlane; reject unsafe installer reuse

`omer-ayhan/skillspp` confirms a per-agent Skill package plane and exposes only a validation MCP tool. It has no Project/Section/Session or attachment graph. Its installer executes pre/post hooks through `sh -c` and its destination containment is lexical; isolated probes confirmed default execution of GitHub-origin hooks and a symlink destination write escape. Treat resource installs as high-risk writes behind explicit preview/approval, realpath containment, staging and rollback. [Review evidence](research/evidence/skillspp-review-2026-11-21.txt).


## patterson-agents/cli — strong independent config-plane patterns, legally unavailable source (#99)

Its canonical IR and emitter contract separate source intent from target writes: emitters output deterministic `FileOp[]`, explicit `CoverageGap`s account for unreachable concepts, and a single engine owns provenance/drift protection/never-write enforcement. `init --import` lifts local config files only. The root `PattersonProject` is agent configuration, not a conversational Project; no Session/event/attachment/memory graph was found in first-party TS/JS. The target set has no ChatGPT/Codex history importer and no Claude Desktop Chat/Cowork/Code gateway session adapter.

The repo's internal-use-only LICENSE precludes copying its source or bundled content into Nexus Memory without prior written authorization. Treat its architecture as an idea to independently reimplement and validate, not a dependency. Upstream exact-HEAD Gate run passed; local test/install was not attempted because Bun and Socket CLI are absent and its own policy requires dependency scoring first. [Review evidence](research/evidence/patterson-agents-cli-review-2026-11-21.txt).


## rcdelfin/agentkit — user-level Instructions/Skills ResourcePlane, not SessionGraph (#100)

Its strongest portable pattern is a small explicit allowlist of markdown Skills plus canonical instruction files linked into a few harnesses. It does not model Projects or sessions, and the linker is user-global rather than a source-qualified project/session hierarchy. `--unlink` lacks ownership proof for symlinks: a temp-HOME probe removed a foreign `.claude/CLAUDE.md` symlink, while a fresh setup/unlink left the generated regular wrapper. A clean implementation should record ownership/provenance for every link/generated file and only remove exact owned targets. Keep only that independent design lesson; a source-level MIT license does not blanket-license each embedded Skill. [Evidence](research/evidence/agentkit-review-2026-11-21.txt).


## rolecraft-sh/.github — organization profile, not architecture or implementation evidence (#101)

Its single tracked `profile/README.md` links separate RoleCraft products. Do not infer core CLI capabilities, session hierarchy, licensing or test quality from the profile page; use the separately pinned core repository review instead. [Screen evidence](research/evidence/rolecraft-github-profile-review-2026-11-21.txt).


## rolecraft-sh/skills — curated content ResourcePlane only (#102)

The archived repository supplies 52 Markdown Skills with author/slug/license metadata and a small syntax-presence validator. It can inform how a content bundle carries provenance, but its README also links to a missing `skills/core/skill-orchestration` path. It provides no source Harness parser, session graph, project/section hierarchy, attachment archive, or target writer. Its `deprecation-and-migration` Skill is software/API lifecycle guidance, not Harness-state migration. Do not treat “supports 86+ agents” in the adjacent RoleCraft CLI profile as a data-import fidelity guarantee. Independently validate any Skill's origin/license before reusing it. [Evidence](research/evidence/rolecraft-skills-review-2026-11-21.txt).


## sergionoodles/skillshard — separate Skills ResourcePlane from SessionGraph (#103)

Skillshard's narrow two-value `Scope` model (`Global` / `Project(PathBuf)`) demonstrates why Harness product nouns require typed namespaces: its project is a filesystem install root, not an imported Project object. A Nexus bundle must separately model `SkillAsset`, per-Harness install/link state, canonical copy, version/source/lock provenance, and secrets references, without conflating any of those with `Project`, `Section`, or `Session`. Its partner audit is explicitly advisory and fails open, so Nexus risk metadata should never be interpreted as sandboxing or proof that imported content is safe. Its multi-step filesystem operations also reinforce the independent `WritePlan` + staging + hash + rollback-journal requirement for all destructive resource writes. Candidate disposition and test limits: [review evidence](research/evidence/skillshard-review-2026-11-21.txt).

## stefanvo78/cross-agent-memory — derived Handoff plane, not canonical archive (#104)

Cross-Agent Memory is a useful comparison for a separate derived-memory service: local hooks -> source parser -> heuristic extraction -> searchable SQLite/FTS/vector store -> MCP handoff, optionally shared as a small human-readable Git artifact. Its session object is only a summary, task/file/decision fields and optional text checkpoint. It has no Project/Section/branch/event/attachment graph, and its Git sync intentionally omits raw checkpoint text and embeddings. Nexus should preserve source events and relation edges first; any such summary must be a regenerable projection with explicit field provenance, model/parser version and loss/confidence manifest.

The reviewed implementation also shows risks our write/read boundaries must avoid: replacing a session can leave vector rows without corresponding metadata; project inference can collapse worktrees or misattribute a Gemini session; installing hooks can overwrite pre-existing hook settings; dashboard reads lack auth and are not explicitly loopback-bound. The project-data and SecretReference planes must remain separate from shared Git summaries. Full disposition: [candidate review](research/evidence/cross-agent-memory-review-2026-11-21.txt).

## thesmart/install — consent pattern only; do not reuse the Skill (#105)

This package-manager Skill is not part of Nexus's Harness/session architecture. Its explicit-consent gate is a useful design requirement for future package/adapter installation features: name the package/action, verify intent is current, check existing state, and ask when multiple managers apply. Reimplement this independently. The current helper demonstrates why machine-readable shell output should be parsed as data, not eval'd: an isolated probe reproduced command execution through an unescaped SHELL value. Its PolyForm Internal Use license bars redistribution, so do not include the Skill or code in the product. [Evidence](research/evidence/thesmart-install-review-2026-11-21.txt).

## weiox/skm — Skills ResourcePlane and destructive sync boundary (#106)

SKM is a relevant adjacent example of source/personal/vendor/exported-view separation: skills are stored under one source tree and agent entrypoints are generated links. Nexus can adopt that distinction as a separate ResourcePlane, with each asset's source, license, version, and target capabilities tracked independently from conversations.

Do not reuse its force-sync behavior. Its bootstrap and dependent sync/install/update/organize flows can replace entire ~/.agents/skills and ~/.claude/skills directories. A fake-home probe confirmed existing foreign skill directories were deleted before the roots were replaced by links. Nexus should instead compute a realpath-aware ownership manifest, preview each operation, require explicit approval for each destructive replacement, stage writes, preserve unmanaged content, and journal rollback. Full evidence: [SKM review](research/evidence/weiox-skm-review-2026-11-21.txt).

## wess/loom — Skill manifest/projector only (#107)

Loom's YAML recipe, source refs/checksums, and explicit agent-directory projection are narrow ResourcePlane ideas. They do not imply a cross-Harness session model: its installed registry is only name/version/agent/path/source URL and has no Project/Section/session/event/attachment graph. Its generic configured agent is a folder destination, not a Claude Desktop Chat/Cowork/Code or API-key Claude Code session adapter. More importantly, the install path joins an insufficiently validated manifest name to the skills root, then recursively deletes an existing target; a `../outside` name passed validation and a fake-target test confirmed it can replace a directory beyond that root. Nexus must canonicalize and constrain path names, track ownership, plan/approve, stage atomically, preserve unmanaged content, and retain rollback receipts. Retain only the independent recipe/checksum concepts; reject the package manager as a migration dependency. [Candidate review](research/evidence/wess-loom-review-2026-11-21.txt).

## yearzen1/LocalSkillManager — atomic Skills transfer, not SessionGraph (#108)

This is the strongest local-resource transfer example in the currently reviewed skill-manager candidates: a strict `SkillName`, global/project `.agents/skills` roots, explicit copy-based pull/push, nested reusable group references, symlink refusal, and staged same-volume replacement with rollback. Reimplement those patterns only in a separate Skill ResourcePlane with provenance and target capability checks. Its `project` scope is simply the current working directory, and its groups are a global list of Skill IDs, not imported Projects or Section Groups. No message/session/branch/subtask/attachment/token/MCP/plugin/schedule model exists.

Before any source reuse, resolve the quality gates: exact HEAD has no CI runs, the full suite has one macOS read-only-directory upgrade test failure because it expects a later replacement error while the downloader fails earlier, and strict Clippy fails on an un-gated Windows-only helper. The local end-to-end Skills test passed but is not cross-Harness evidence. [Candidate review](research/evidence/yearzen-localskillmanager-review-2026-11-22.txt).

### Catalog ingestion is discovery, not migration or trust

Ingest curated lists such as awesome-agent-skills-managers through a provenance-preserving supplemental discovery source. Do not merge an external README/install-step grade into Nexus review_status, security verdict, or adapter capability. Each repo remains a distinct candidate requiring pinned source, license, code/test and target-behavior review. A Skills registry row proves nothing about Project/Section/session graphs, attachments, child tasks, schedules, memory or native restore. The external benchmark's single claude -p context probe is not a general session-token cost measurement. Evidence: research/evidence/awesome-agent-skills-managers-review-2026-11-22.txt.

### Skill inventory is not Session or Project migration — skillctl review (#110)

Skillctl is a useful local ResourcePlane comparator: frontmatter parsing, explicit runtime/scope inventory, conflict reporting, and a budget CLI. Its meter is chars/4 on descriptions and cannot estimate per-session token use. Keep resource inventory, context measurement, and SessionGraph separate. Independently implement fail-closed scanner validation, source/digest provenance, symlink containment, staged/rollback-capable Skill writes, atomic config updates, managed-block preservation, and true project-scoped writers; #110 probes showed where the candidate's current version fails these boundaries. Evidence: research/evidence/zongwu233-skillctl-review-2026-11-22.txt.

### Resource importer security gates — AgentForge candidate #111

A separate Skill adapter may convert frontmatter/content to a native command/rule file, but this loses folder assets and is not Session migration. Preserve a folder-level asset manifest, exact source digest/license, native target path semantics, and explicit scope. Candidate #111's validate() method exists but is not called during file/registry loading; path names then feed directly into write/unlink paths. Reject invalid names, resolve-and-contain destinations, reject symlink targets, stage writes and roll back on failure, and confirm destructive operations. Also treat registry and marketplace readiness separately: its marketplace client methods are stubs, and the PyPI distribution name is occupied by an unrelated project. Evidence: research/evidence/agentforge-review-2026-11-22.txt.

### Skill manager vs. SessionGraph — Agent Skills Manager (#112)

A well-scoped skill for GitHub `SKILL.md` discovery and approval-gated resource changes does not imply a portable Project, Section Group, or conversation graph. This candidate keeps source pins and local-edit preservation for optional private skill collections; reuse those concepts in a separate ResourcePlane with per-Harness capability reports. Do not reuse the manager as a session adapter: no ChatGPT export parser, Claude Desktop mode destinations, branch/subtask relationships, media, usage records, memory, or schedules. Its runtime selection E2Es remain unexecuted. Evidence: `research/evidence/agent-skills-manager-review-2026-11-22.txt`.

### Cross-Harness instructions are not cross-Harness adapters — candidate #113

A portable SKILL.md plus manually copied AGENTS.md/CLAUDE.md snippets can spread coding conventions, but it does not produce automatic compatibility or move durable state. Keep instruction artifacts in a separate InstructionPlane from Skill resource bytes and SessionGraph. Candidate `akhenda/inline-commenting-convention` is useful only for intent-focused comments/JSDoc; no API, mapping, serializer, graph, or destination restore path exists. Evidence: `research/evidence/akhenda-inline-commenting-convention-review-2026-11-22.txt`.

### Visual artifact persistence is not SessionGraph persistence — candidate #114

PaperBoard’s four pillars (render, validate, per-harness persist, gallery) operate on presentation artifacts. Its `{slug}.html`/`.DESIGN.md`/`.meta.yaml` triple discards the source input and contains no stable session/message identifiers or hierarchy. Its shared Python core/thin runtime wrappers may inform a separate HarnessAdapter/ReportPlane, but must not be mistaken for ChatGPT Project/Section/Session migration. It explicitly keeps harness galleries separate; raw HTML is not sanitized. Evidence: `research/evidence/atv-paperboard-review-2026-11-22.txt`.


### Resource inventories do not replace SessionGraph — Reno (#115)

A local store + inventory can organize reusable Skill assets, but Reno provides no conversation/session IDs, Section Groups, parent/subtask edges, attachments, usage, memory or schedule serialization. Keep a bounded ResourcePlane separate from the lossless SessionGraph and per-mode HarnessAdapters. Do not copy its archive or rollback implementation: local POCs reproduced extraction traversal, unscanned symlink content, truncated scanning accepted as low-risk, and nested data loss during rollback. Full evidence: research/evidence/reno-review-2026-11-22.txt.

### Separate narrative checkpoint from lossless SessionGraph — cross-harness-sync (#116)

The L0/L1/L2 model, decision index, handoff template and git-diffable project state are useful as a derived NarrativeStatePlane for resumability. They must not collapse the source EventGraph: this protocol stores summaries and authorization records, cannot prove they are truthful, and omits message/attachment/token/schedule payloads. Its project-scope and concurrency boundaries are explicit; current main also has reproduced overwrite, false-pass and POSIX crash issues. Evidence: research/evidence/cross-harness-sync-review-2026-11-22.txt.

### Candidate #117 — cagedbird-org/skills is a ResourcePlane, not SessionGraph

Its manifest → commit/content lock → installed files → mirrors state model is a useful inventory pattern for reusable Skills. It is not a transcript graph or migration adapter: no Project/Section/Session hierarchy, message edges, media, token usage, memory/schedules or Claude Desktop Chat/Cowork/Code imports exist. Its sync restores changed locked content and can overwrite user edits. A disposable probe also demonstrated `..` manifest-name traversal outside the configured target. Any Nexus Memory ResourcePlane should be non-destructive and validate canonicalized paths before effects; do not port its overwrite or current path-handling behavior. Evidence: `research/evidence/cagedbird-skills-review-2026-11-22.txt`.

### Candidate #118 — generic MCP transport does not imply portable agent state

Dark-Ohm/pz-mod-manager has a clean shared CLI/MCP command registry with JSON schemas and mutation hints, but the operations and `.pzpack` model are specific to Project Zomboid. Keep only the generic adapter pattern; do not map game environments, mod profiles, pack revisions or MCP tool execution to Nexus Memory Projects, Section Groups, Sessions, memories or schedules. Evidence: `research/evidence/dark-ohm-pz-mod-manager-review-2026-11-22.txt`.

### Candidate #119 — package registry without Harness adapters

A semver Skill catalog can inform a separate ResourcePlane, but Agent Smith’s implementation neither fetches remote skill payloads nor maps them to destination-native roots; it writes an app-private directory. Do not conflate platform tags with tested support. Its lexical sandbox follows destination symlinks; any Nexus importer must reject/resolve symlink components before writes. Its README npm install name currently belongs to another package. Evidence: `research/evidence/ebenhzr1-agent-smith-review-2026-11-22.txt`.

### Candidate #120 — a ResourcePlane reference with a vulnerable fetch stack

The `craft.yaml`/pinfile model, MVS resolver, explicit subpath select, git commit + content-integrity lock, global-versus-project install split and recoverable write-ahead note are useful for a dedicated Skill ResourcePlane. They are not SessionGraph state. Any future reuse must replace/upgrade the current go-git/go-billy/x-crypto chain, validate all remote refs/tree data, cover custom destination semantics, and fix the >200 dependency boundary before fetching untrusted packages. No Session/Project/Section graph, media, token, schedule, MCP, plugin or memory adapters exist. Evidence: `research/evidence/erdemtuna-craft-review-2026-11-22.txt`.

### Candidate #121 — canonical Skill library with static Harness link adapters

Skill Sync’s `.agents/skills` canonical directory plus explicit per-agent symlinks, global/project scopes, per-agent install outcomes and preview-before-replacing a real agent folder are useful ResourcePlane design references. Its 72-path table does not prove 72 live Harness integrations; current mapping has Claude Code only and no Claude Desktop mode-specific roots. Do not map its Skill catalog to SessionGraph. Its current file installation deletes the old canonical folder before copying the new source; a failed replacement can lose the prior Skill. Build transactional old/new promotion with rollback before applying a comparable pattern to user memory. Evidence: `research/evidence/eugen1408-skill-sync-review-2026-11-22.txt`.

### Candidate #122 — extension package manager, not a SessionGraph adapter

AgentPack is a strong pattern reference for the Nexus Memory ResourcePlane: a canonical component pack, per-Harness capability outcomes, a plan-before-write sync engine with checksums/backups/conflict gates, reversible adoption, a shared MCP gateway, and inward collection into a reviewable inbox. Keep those as design inputs. Its actual intermediate representation and workspace manifest are limited to Skills, MCP, instructions, hooks, plugin metadata, targets, profiles and gateway config. They do not represent chat messages, Project/Section hierarchy, branches/subtasks, session artifacts/media/token counts, schedules, or Claude Desktop modes. The `claude` adapter is Claude Code, not Desktop Chat/Cowork/Code. Its passing test suite therefore provides no session-fidelity or live Desktop restore evidence. Current production audit reports two high and one moderate parser/schema dependency advisories; reuse requires updating/mitigating those dependencies first. Evidence: `research/evidence/hardt-llc-agentpack-review-2026-11-22.txt`.

### Candidate #123 — SkillHub: not a session graph; unsafe install/remove primitives

SkillHub centralizes a public Skill catalog and a four-target local/global path table, with a per-Skill source URL/commit hash lockfile. It does not model Projects, Sections, sessions, transcripts, tasks, MCP/plugins, memory or schedules. More importantly, source review and safe disposable probes found shell command construction through `execSync` with URL-controlled owner/repo data, path traversal in `remove`, and non-transactional replacement that deletes the old Skill before copying the new one. Its scanner is a warning-only heuristic, not a trust boundary. Tests pass but do not cover those paths; npm audit is clean yet irrelevant to these source-level flaws. Keep only the registry/lockfile UX concept; do not reuse its installer or path manager. Evidence: `research/evidence/harsha-pyla-skillhub-review-2026-11-22.txt`.

### Candidate #124 — useful Skill ResourcePlane UX, vulnerable tar extraction

The offline skill registry, frontmatter linter and scaffold are simple low-dependency ResourcePlane ideas. This does not import Projects/Sections/Sessions or MCP/plugins/memory/schedules, only routes four skill directories, and lacks Claude Desktop Chat/Cowork/Code adapters. Its `safe_extract_tar` lexically checks member paths but then calls `tar.extractall` without validating symlink/hardlink targets; a disposable archive with an in-root symlink followed by an in-root-looking file wrote outside the staging directory on CPython 3.12.10. The project claims Python 3.8+ (CI 3.8/3.11), below the newer `tarfile` data-filter default. Never use this installer on untrusted GitHub repos until explicit link filtering / staging containment and an exploit regression test exist. `--force` also removes old Skills before copy and lacks rollback. Evidence: `research/evidence/hayatelin-skillhub-review-2026-11-22.txt`.

### Candidate #125 — MCP/“sessions” are Active Directory and SMB, not LLM Harness state

The repo exposes an audited MCP interface to Active Directory/Samba management and a desktop/web control panel. Its admin cookie sessions and SMB client “sessions” are unrelated to ChatGPT/Codex conversations; its data migrations are directory migrations. The presence of `.agents`/`.claude` developer files is repo-local authoring context, not a cross-agent sync capability. This is an auto-triage false positive; no migration adapter or canonical session graph was found. Pass. Evidence: `research/evidence/jniltinho-ad-manager-review-2026-11-22.txt`.

### Candidate #126 — command/MCP ResourcePlane only; not Skills or SessionGraph

Agent Manager stores Markdown slash-command prompts, profiles and a narrow four-target MCP schema. These are useful cues for target adapters and precedence, but the project cannot transfer a ChatGPT/Codex Session, Section tree, media, tool events, memory or schedules. Its MCP model drops remote URLs/OAuth/headers, the OpenCode projection does not match current OpenCode's `opencode.json` / `mcp.servers` schema, and Codex removal attempts JSON parsing of TOML. A temp CLI probe also confirmed `add ../../outside`/`remove ../../outside` writes/deletes outside its configured command directory. The test script is a TODO that exits 0, not a quality gate. Do not reuse its mutating commands or count four advertised adapters as verified. Evidence: `research/evidence/juliusolsson05-agent-manager-review-2026-11-22.txt`.


## SessionGraph boundary update — Claude Desktop Chat/Cowork/Code (2026-11-22)

Keep user-selected **logical surfaces** distinct from current UI labels. Anthropic is rolling Chat and Cowork into a single conversation experience; in the local third-party-inference store, their conversation sessions share `local-agent-mode-sessions/`, while Code records live separately under `claude-code-sessions/` and transcript JSONL is in Claude Code's `~/.claude/projects/`. Project memory under `spaces/<projectId>/memory/` is neither global instructions nor a session transcript. The account-hosted Cowork cloud session is a separate deployment/runtime from local 3P gateway inference. The canonical graph should represent `Deployment`, `Surface`, `SessionStore`, `ProjectMembership`, `TaskLocality`, `TranscriptRef`, and `GatewayCredentialRef` separately; the credential itself must never be copied. See `research/evidence/claude-desktop-3p-chat-cowork-code-2026-11-21.txt` and the current primary links recorded there.

## Candidate #127 — `agr` is a Skills ResourcePlane, not a session codec

`KAFKA2306/agent-resources` provides a Python Skill installer/synchronizer (`agr`) plus a one-off CLI Skill runner (`agrx`). Its `ToolConfig` path table and source/commit metadata can inform a target-specific ResourcePlane, but it models only `SKILL.md` entries, has no conversation event/provenance/Project/Section or attachment graph, no MCP/plugin/memory/schedule adapter, and no Claude Desktop mode target. Its `claude` path means local Claude Code CLI. The `agrx` interactive Claude path appends `--dangerously-skip-permissions`; avoid making that implicit in a Nexus operation. Treat its directory mappings as hints requiring version-pinned validation, particularly its Codex `.codex/skills` path compared with current `.agents/skills` guidance. Full evidence: `research/evidence/kafka2306-agent-resources-review-2026-11-22.txt`.


## Candidate #128 — `kayaman/agentskills`: shared Skills location is not an adapter matrix

This Rust installer recognizes eight harness markers but always materializes Skills in `.agents/skills` (or `~/.agents/skills`). Current vendor docs confirm that shared path for Codex, Cursor, GitHub Copilot and OpenCode V2 compatibility; Claude Code documents `.claude/skills`, while Cowork/Claude Desktop account skill behavior is separate. Treat `detect_primary_agent` as display/heuristic only, not proof that it serializes into the detected host's native store. The v3 lock omits the `git_ref` and commit; its content hash excludes dotfiles and lacks a path/content boundary. A failed copy after deleting an installed destination leaves the old Skill gone and its lock entry stale; a failed upstream fetch is warned but still exits 0 with “All skills are up to date.” A temp-only traversal removed a sibling directory through `remove ../../../victim`. Keep the SKILL.md ResourcePlane concept, not its installer/lock/update/rollback implementation. Evidence: `research/evidence/kayaman-agentskills-review-2026-11-22.txt`.


### ResourcePlane comparison — prefer native, versioned install contracts

As of 2026-11-22, GitHub CLI `gh skill` is public preview and documents preview-before-install, host/scope selection, `@TAG`/`@SHA` and `--pin`, plus provenance (source, ref, tree SHA). Evaluate it as a Skills-plane component instead of re-implementing these primitives, but do not treat Skills transfer as Project/Session migration. Candidate #128's open PR #6 is unmerged and its proposed bare-name source was flagged because the default repo lacked the advertised skill.


Candidate #128 also masks an upstream update failure: its per-Skill loop logs a warning and continues, then reports `All skills are up to date.` and exits 0. A fake-Git temp probe reproduced this with a still-installed Skill. The ResourcePlane must return machine-readable per-item success/failure and nonzero/partial status rather than equating an unchanged update count with success.


## Candidate #129 — `kayaman/skillz`: Python sibling, same ResourcePlane boundary

`skillz` is a Python near-parallel to candidate #128's Rust `agentskills`: same author's command set, `.agents/skills` path, eight-marker detection and v3 lock. It still lacks any SessionGraph/Project/Section or Claude Desktop mode writer. Its `remove` joins the unchecked name to the skills root, and temp-only probes showed `../../../victim` deletes outside the root. Reinstall deletes the old Skill before `copytree`; failure leaves new partial content and stale lock. `update` reports failed fetch/install then returns success and prints `All skills are up to date`; a lock-write failure also leaked fetched temp state. Hash excludes dotfiles and lacks path/content framing. Reject mutation/update code; keep only standard Skill format ideas. Evidence: `research/evidence/kayaman-skillz-review-2026-11-22.txt`.


### Candidate #130: SkillHub is an AssetPlane only (2026-11-22)

The pinned `MaNongJSZ/SkillHub` desktop app centralizes Skills and creates per-agent symlink/junction projections; its nested folder grouping is within the Skill catalog, not a Session/Project/Section graph. Its optional Claude Desktop writer detects only Windows `%LOCALAPPDATA%` and writes a `manifest.json` under an undocumented `local-agent-mode-sessions/skills-plugin/{uuid}/{uuid}` location. Current public Claude Desktop 3P docs do not establish that private path as a stable API; treat it as version-specific until tested against an authorized disposable client. The exact Rust library reproduced (1) `SKILL.md` frontmatter `name: ../outside` writing outside its configured registry, (2) overwrite deleting the old Skill before a failed Git clone, and (3) invalid manifest JSON being replaced with a new one-skill manifest. Local backend tests also cannot compile due an outdated AppConfig test fixture. Borrow only the high-level separate ResourcePlane and target-specific serializer concept; reject its path/manifest writers as a session-transfer foundation. Full evidence: `docs/research/evidence/manongjsz-skillhub-review-2026-11-22.txt`.


### Candidate #131: Agent Skill Manager is a local catalog, not a session graph (2026-11-22)

This macOS app reads installed Skill folders and separately stores a JSON list of links, commands, summaries, categories, favorites and UUIDs. It does not migrate Skill content or chat history. Its collection merge and safe Trash operations are useful UX/safety patterns; its installer only offers a user-confirmed terminal command and does not verify the result. It has no Claude Desktop 3P store adapter, no Project/Section/Session graph, and no license file/metadata. Treat import command strings as untrusted and keep the code out of Nexus until license status is resolved. Full evidence: `docs/research/evidence/michaelmjhhhh-agent-skill-manager-review-2026-11-22.txt`.


### Candidate #131: Agent Skill Manager is a local catalog, not a session graph (2026-11-22)

This native macOS utility scans installed Skill folders and stores bookmarks/commands in a separate local JSON collection. Its imported Skill records are not Session transcripts or Project/Section memberships; it has no Claude Desktop 3P store adapter. Useful adjacent patterns include lazy bounded file browsing, atomic collection JSON, explicit review before executing a terminal command, and path/inode-pinned Trash deletion. The command still runs with user permissions and installation success isn't checked. License is unresolved (no LICENSE/SPDX); do not reuse code until clarified. Full evidence: `docs/research/evidence/michaelmjhhhh-agent-skill-manager-review-2026-11-22.txt`.


### Candidate #132 — `msking18/cognitive-personas`: behavior adapter, not SessionGraph

This MIT, zero-dependency Node persona framework provides Antigravity hook scripts and file-based personas for Claude Code, Cursor, Roo Code, and GitHub Copilot. Its Claude Code adapter is `.claude/` output styles; there is no Claude Desktop 3P Chat/Cowork/Code data adapter, ChatGPT Project/Section/Session/transcript graph, attachment/resource transfer, or schedule/MCP/plugin/memory migration. The proposed `agent-memory-mcp` v3.2 schema is an RFC; current code only reads a few legacy pedagogy rows at SessionStart. A disposable call-pair reproduced `ask` then `allow` for two same-category operations in one conversation because the dedupe marker is saved before `ask` and the hook has no approval/denial feedback. Official Antigravity docs say `ask` can honor Always Allow; the plugin does not emit `force_ask`. Keep persona text/hydration as optional behavior-plane references, not a migration dependency; reject this guard and force-copy installer as a safe transaction pattern. Evidence: `research/evidence/msking18-cognitive-personas-review-2026-11-22.txt`.


### Candidate #133 — `ngmkhoi/tavily-mcp-manager`: one service, not MCP/resource migration

This MIT utility is a Tavily API-key vault/rotation CLI and launcher for one Tavily stdio MCP process. Its four host entries are Codex, Claude Code CLI, Gemini CLI and OpenCode; the Claude path uses `claude mcp add ... -s user` or a `~/.claude.json` fallback. It is not Claude Desktop 3P Chat/Cowork/Code, and does not model generic MCP transports/auth/resources, plugins, ChatGPT Project/Section/Session history, attachments, memory or schedules. Good adjacent patterns: separate 0600 key file and metadata, safe single-quote serialization, atomic locked key-store writes, masking, and dry-run/config preview. Reject the general fallback writer: isolated reproduction overwrote an existing Tavily entry without `--force`, reset a 0600 Claude config to 0644, and created a 0644 backup with a synthetic secret; `mcp install all` still exited 0 with one target in attention state. CI/local tests are green but do not cover those contracts. Evidence: `research/evidence/ngmkhoi-tavily-mcp-manager-review-2026-11-22.txt`.


### Candidate #134 — `nicolavalenti/mem`: Context/Handoff plane, not SessionGraph

This MIT repository provides a shared local vector-memory store for Claude Code, Codex and Pi, plus checkpoint handoffs; it extracts from those three local transcript roots only. Good design references are typed source/kind metadata, incremental changed-file ingest, one shared embedding space, mtime-bound checkpoint state and explicit decisions/open-items handoffs. It does not preserve a full conversation event graph, Project/Section memberships, parent/child task links, tools, attachments, branches, token/model data or restore state; Desktop Chat/Cowork/Code and ChatGPT exports are absent. Handoffs are lossy summaries (head/tail excerpt plus Claude CLI summary), and the transcript excerpt is passed to the configured Claude CLI provider, so “local store” is not a privacy guarantee for summarization. Synthetic Pi handoff proof reproduced a `claude --resume` command for a non-Claude session. Keep only the memory/context and handoff design, not the candidate as a migration engine. Evidence: `research/evidence/nicolavalenti-mem-review-2026-11-22.txt`.


### Candidate #135 — `Primuez/skill-installer`: unsafe Skill writer and non-commercial license

This is a skill-only installer to a generic directory, with GitHub/GWS backup—not a session, Project/Section, memory, MCP or plugin migrator. Its latest LICENSE is non-commercial/proprietary despite README text claiming MIT/commercial rights; no code reuse for Nexus without written authorization. There is no test or CI coverage. Isolated source probes showed a nonzero/empty SkillSpector result treated as safe, a GitHub tree URL stored as HTML, and `name: ../escaped` escaping the requested skills root. Unvalidated names also flow into shell-interpolated Git/GWS commands and the pipeline can push to remote backups without a separate confirmation step. Reject its implementation; at most retain a high-level “inspect before install and preserve source provenance” requirement for Nexus. Evidence: `research/evidence/primuez-skill-installer-review-2026-11-22.txt`.


## Candidate #140 — Mnemo task continuity is not the canonical conversation graph

`sirrobot01/mnemo` provides a useful local-first reader/task-handoff pattern: deterministic ingestion IDs, content fingerprinting, same-branch/idle-window grouping, explicit derived WorkingState, and a PostgreSQL boundary that strips absolute paths and raw event content. Its `Task ↔ Session` relation is many-to-many; a pinned Task can override branch separation, so it cannot be treated as a faithful source parent/child or fork relation. The domain schema lacks Project/Section, attachments, schedules and parent/fork edges. More importantly, the current readers flatten or omit parser payloads: nested Claude tool-use blocks, Codex tool arguments/results, and Continue source timestamps are not preserved. Nexus should keep source graph identity and runtime event payload separate from its optional derived handoff summary, and require target-native restoration plus loss accounting rather than treating a searchable/handoff index as session migration. Evidence: `research/evidence/sirrobot01-mnemo-review-2026-11-22.txt`.


## Candidate #141 — Skimi informs ResourcePlane transactions, not SessionGraph

Skimi's lock-file provenance, explicit per-agent targets, deterministic collision report, managed-link identity check, backup/rollback around link and lock changes, and read-only-fetch dry-run are useful Skill ResourcePlane patterns. Preserve them as requirements, not as a portable conversation model. The target directories are global home paths; there are no Project/Section/session/fork edges or Desktop 3P mode adapters.

Do not adopt the live-worktree symlink update behavior unchanged: source code pulls repositories before package discovery/apply while already-installed links resolve into those working trees, so a failed later plan does not roll back newly visible Skill bytes. Also add a path-containment check: remote repo subdirectory segments are joined to the clone without rejecting parent traversal. The latter is a source-level risk inference, not an executed exploit. Evidence: research/evidence/timonwong-skimi-review-2026-11-22.txt.


## Candidate #142 — GoodBoy's Skill lock is not portable state restoration

GoodBoy's separation of a local versioned content store, project manifest, exact lock, and integrity hash is a strong ResourcePlane pattern. However, install-from-manifest selects the registry's latest version without consulting the recorded lock version or semver range; an isolated integration run changed a project from range ^1.0.0 / lock 1.0.0 to installed 2.0.0 / range ^2.0.0. A project declaration therefore does not reproduce its locked resource contents. The local registry itself is outside the project manifest and is not remotely synced in Phase 1.

Global target writes also lack ownership-safe all-or-nothing semantics: an unowned symlink at the same name is replaced or removed, and a conflict in a later target can leave an earlier symlink without a lock record. Nexus should preserve exact version/content and all target mutations transactionally, with per-path ownership and recovery; Skills remain separate from Project/Section/Session graphs. Evidence: research/evidence/xpera-ch-goodboy-review-2026-11-22.txt.


## SecretPlane boundary — KeyVault is not a session/gateway migrator

Candidate #143 `ylz201/keyvault` reinforces that credentials are a separate plane from Skills/MCP definitions and conversation events. Current main is a local encrypted secret vault with opt-in MCP CRUD; its MCP `secrets_get` returns plaintext when enabled. Keep only its restrictive-by-default policy and local encrypted-store boundary as design references. Do not package credentials inside the Canonical Bundle: record an opaque locator and require explicit target-side reauthorization/relinking.

The repository's authenticated fixed-GET credential gateway exists only on an open, unmerged 0.2-alpha PR. It provides useful architectural ideas (OS-isolated admin/client identities, scoped expiring grants, credential-revision binding, durable no-retry request reservations, allowlisted output projection and secret-free audit codes) but is POSIX-only and is neither an inference proxy nor a Claude Desktop third-party-inference configuration writer. It has no transcript/project/session parser or importer. Do not describe it as current main or a released capability. Full source and local test caveats: `docs/research/evidence/ylz201-keyvault-review-2026-11-22.txt`.

## Claude Desktop 3P data-plane split

Model `surface`, `deployment`, `session-store`, `project`, `attachment/artifact`, `memory`, `schedule`, and `credential reference` as distinct objects. Current official docs locate Chat/Cowork under `local-agent-mode-sessions/`, Code metadata under `claude-code-sessions/`, and Code transcripts in Claude Code's `~/.claude/projects/` store. Native cross-device export/import covers Claude-owned state and can include secret-bearing configuration; it is not a generic archive format. The gateway endpoint/key is managed outside portable history. See `docs/research/evidence/claude-desktop-3p-current-review-2026-11-22.txt`.


## Candidate #144 — MCP ResourcePlane pattern, unsafe as-is

`agents-mcp/cli` provides useful reference ideas—pure per-target adapters, canonical MCP transport records, field-level loss warnings, deterministic ownership state, JSONC AST edits, and per-file atomic writes. Keep this plane separate from SessionGraph and source project membership. It has no conversation/session importer and does not cover Codex or Claude Desktop 3P.

Do not reuse the implementation as-is: a valid canonical config key `../../../escape` escaped the managed plugin subtree during `sync`; default import left detected secret values in versioned canonical/plugin files; `--no-sync` still synchronized; duplicate native server names silently selected the first adapter; and the clean `verify` workflow/CI is red. Make server-name path containment a validation invariant, never persist literal credentials, warn on conflicting source identities, and stage a full multi-file transaction with rollback before adopting any comparable ResourcePlane.


## Candidate #144 — MCP ResourcePlane pattern, unsafe as-is

`agents-mcp/cli` provides useful reference ideas—pure per-target adapters, canonical MCP transport records, field-level loss warnings, deterministic ownership state, JSONC AST edits, and per-file atomic writes. Keep this plane separate from SessionGraph and source project membership. It has no conversation/session importer and does not cover Codex or Claude Desktop 3P.

Do not reuse the implementation as-is: a valid canonical config key `../../../escape` escaped the managed plugin subtree during `sync`; default import left detected and undetected literal secret values in versioned canonical/plugin files; `--no-sync` still synchronized; duplicate native server names silently selected the first adapter; and the clean `verify` workflow/CI is red. Make server-name path containment a validation invariant, never persist literal credentials, warn on conflicting source identities, and stage a full multi-file transaction with rollback before adopting any comparable ResourcePlane.


## SecretPlane boundary — agentic-keyvault

Treat Hitesh-Sisara/agentic-keyvault as an adjacent external secret store, not a source/target session adapter. Nexus canonical records should store only credential locators, provider/scope metadata and a relink-needed status; secret material stays in an external vault and is never copied into exports, logs, or session bundles. Keep agent grants least-privilege. Candidate review and synthetic scope-integrity probe: `docs/research/evidence/hitesh-sisara-agentic-keyvault-review-2026-11-23.txt`.


## Candidate #178 — agentkit resource registry, reject writer as-is

Possible data-model inspiration: a small manifest per reusable resource, profile composition, and per-harness target adapters. Do not reuse its writer. Resource IDs become filesystem path components without target-root containment; an untrusted `../../outside` ID wrote outside the requested target in a disposable probe. `BaseAdapter.apply` writes sequentially without stage/backup/rollback; a conflict on the second item left the first write. Validate profile references against the actual resource set and stage all output behind a preview/atomic commit with path-safe destination mapping and ownership-aware rollback. This is not SessionGraph. See `docs/research/evidence/huqiwei123-agentkit-review-2026-11-23.txt`.


## Candidate #179 — GitHub Skills Hub as a narrow ResourcePlane reference

A basic Skill discovery/catalog/clone/update workflow can be a separate ResourcePlane feature, but it must not be represented as SessionGraph or Project/Section migration. Require pinned source revisions, content verification, explicit target adapters and non-mutating previews. Preserve target-platform metadata across updates; do not publish user resources publicly by default; constrain uninstall to app-owned roots. This repository has no session export/import and no test suite. Evidence: `docs/research/evidence/jaxz714-skills-hub-review-2026-11-23.txt`.


## Candidate #180 — multi-Harness content bundles need dependency closure

The plugin.yaml target/fallback map is a useful example of distinct ResourcePlane serializations (plugin manifest, AGENTS.md fallback, instructions, Skills). However, generated outputs must be dependency-closed: the committed target directories retain references to shared/email-templates while omitting those files. Nexus build artifacts should include/resolve every referenced dependency, validate output per adapter, and compare generated bundles against the canonical manifest. This project contains no SessionGraph or project/Section migration. See `docs/research/evidence/jondwillis-privacy-rights-plugin-review-2026-11-23.txt`.

## Candidate #181 — canonical role source is not canonical session state

This repository demonstrates an adapter pattern worth retaining: one role-definition tree can generate distinct Claude Code and Cursor artifacts while a CrewAI runtime reads the canonical definitions. Its `.devteam/` blackboard is project task-output state; the runtime creates sequential task files and a final phase marker, not a resumable SessionGraph. Nexus should reuse the source-to-adapter principle only for Skills/agents/config resources. Session state requires independent serializers for message events, forks/subtasks, files/media, project/section membership, costs/tokens and target resume; never infer it from a task log or `state.json`. Evidence: `docs/research/evidence/jp-999-dev-team-review-2026-11-23.txt`.

## Candidate #182 — reject keyword-only MCP references

A repository called `mcp-client` can still be an ordinary REST workflow. This sample uses Axios HTTP routes, not MCP JSON-RPC or protocol SDK; a local mock confirmed its six REST requests. Nexus candidate triage must validate transport, protocol, data model, and import/export behavior from source—not infer MCP or session capability from a repository name, topic, or README. Evidence: `docs/research/evidence/kamalsrini17-mcp-client-review-2026-11-23.txt`.

## Candidate #183 — resource-plane patterns, with unsafe writer boundaries

The standalone Skill's useful concepts are a canonical ownership/provenance model, explicit package-manager adapters, a local journal for unmanaged resources, bounded probes, dry-run plans and fixture-driven testing. These can inform Nexus's resource/config plane; they do not represent a session schema. Do not copy the CLI Butler write path: an untrusted package name reached `bash -c` in a synthetic probe, and its app-bundled symlink uninstall removed the link without `.bak` despite documented policy. Nexus adapters should pass argv arrays, stage/preview destructive changes, enforce ownership/root boundaries, and test hostile names/symlinks before commit. Evidence: `docs/research/evidence/kelegele-cli-butler-review-2026-11-23.txt`.

## Candidate #184 — shared ResourcePlane is useful, but isolate it from SessionGraph

A dedicated shared Skills/MCP/CLI registry with CLI and MCP façades is a useful product boundary; on-demand skill lookup can reduce prompt preloading. This project does not model native Projects/Sections/SessionGraph or transfer transcripts/attachments. Its current importer trusts Skill frontmatter as a destination path, can partially write before failing, stores MCP environment secrets as plaintext, and has a broken sync initializer. Nexus should treat third-party configs as untrusted; canonicalize and contain every path, redact/never sync credentials, stage all imports with transaction rollback, and separately version each Harness serializer. Evidence: `docs/research/evidence/kingimperio-ctx-review-2026-11-23.txt`.

## Candidate #185 — canonical Skill text is not canonical session state

A single source `SKILL.md` can be packaged as a Claude Code plugin, copied into Codex's Skill directory, transformed into editor rules, or prepended to an API system prompt. This is useful for a narrow ResourcePlane serializer and versioned content hash; it says nothing about Projects, Sections, SessionGraph, files, branches, tool results, memory or schedules. Keep content portability and session-state migration as separate planes, and test whether each host merely loads instructions or actually restores native state. Evidence: `docs/research/evidence/kizuno18-dora-explores-binaries-review-2026-11-23.txt`.


## Claude Desktop on third-party inference: target adapter boundaries (2026-11-23)

Treat Claude Desktop on 3P as a dedicated target profile with three capability labels (`chat`, `cowork`/unified task, and `code`) and a distinct local data root, not as generic Claude API state. Chat/Cowork records pair a session-state file with a local working directory holding transcript, uploads, outputs, and audit data. Project memory is scoped by a target project ID. Code has a Desktop session-index record (folder/settings/title/summary) but its transcript lives in Claude Code's own `~/.claude/projects/` store. Do not synthesize a transcript and pretend this index record makes it resumable: require a pinned/versioned importer contract and explicit trust approval.

Current Unified Claude combines Chat and Cowork for eligible accounts; retain both source mode and target realized mode as provenance, and model project/session links explicitly. Keep three destination profiles separate: Claude Desktop on 3P with gateway inference (all inference routes to the provider), local/self-hosted Claude Code CLI/API-key, and Anthropic-hosted cloud sessions. API keys and connector/MCP credentials are not portable session data; reauthorize them separately. Encrypt transfer archives and include a per-object loss ledger.

Vendor import documentation establishes a one-time Claude-to-Claude move path, not ChatGPT/Codex interoperability: target-side import can bring Claude chat/project records and local Cowork/Code sessions, but not the source harness's arbitrary data model. The adapter must preserve unsupported source topology and attachments in an archival package and report what is not resumed. Detailed official sources: `research/evidence/lartweib-dotai-review-2026-11-23.txt`.


## Skills target adapters for Claude Desktop 3P and Code (2026-11-23)

The local Skills plane is not one path shared across Claude surfaces. Desktop 3P user-created/user-uploaded Skills are app-managed user extensions stored with Desktop 3P local data; organizations provision reusable plugins/Skills through a marketplace or system-wide plugin directory. Claude Code filesystem Skills are personal `~/.claude/skills/` or project `.claude/skills/`. Claude account Skills sync to Code only for Claude-account authentication, not API-key/third-party-provider use. The schema should distinguish `desktop_3p_user_extension`, `desktop_3p_org_plugin`, and `claude_code_filesystem_skill`, preserve activation/provenance, and require source checksums and version pins. A generic directory copy to `~/Library/Application Support/Claude/skills` must not be marked as support for all modes. Candidate #191 confirms why: it advertises that generic path but does not map native 3P extension or Code scope. Evidence: `research/evidence/lazyworkshop-create-skills-manager-review-2026-11-23.txt`.

## 2026-11-23 continuation — candidate #192 + confirmed Claude Desktop 3P scope

User confirmed that the target covers **Chat, Cowork and Code**, all in Claude Desktop on third-party inference/API-key gateway mode. This means the local 3P Desktop application, not merely standalone Claude Code CLI; Anthropic-hosted Claude Code Cloud remains separate. Official 3P docs confirm provider-routed inference, local conversation storage, Chat/Cowork/Code, and a Claude-native importer for Claude.ai/local Claude sessions, not a documented ChatGPT/Codex source adapter. Chat and Cowork may be Unified Claude in the UI; Code remains separate. Model source surface and effective target mode explicitly.

Target storage differs by mode: Chat/Cowork use local-agent-mode session state, transcript/audit, uploads/outputs and memory; Code has a Desktop session index plus its transcript in `~/.claude/projects/`. App-managed Skills/plugins/MCP, Code filesystem configuration, local/project memory, scheduled tasks and project/group structures need distinct adapters. The official import wizard is one-time and has its own omissions; 3P scheduled tasks run locally and require an awake app/device. Do not directly mutate private target stores or call them officially supported. Current primary-source details: `docs/research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt`.

### Candidate #192 — `learnrudi/cli`, pinned `797980b5a906e258c54d54c49ad3cfbb367e5279` (MIT)

Detailed review: `docs/research/evidence/learnrudi-cli-review-2026-11-23.txt`. High-value ResourcePlane/host-control architecture: multi-harness Skills projection with digest/ownership/drift/rollback; MCP secrets and native CLI runtime management; isolated provider launch and native resume pointers. It is not a cross-Harness session importer. Current CLI retires `sessions`/`projects`/`import`; historical DB conversion is internal RUDI data and lossy; resume only works from a stored launch record with a native provider session ID; groups are parallel launches, not conversation branches. Isolated frozen install, documented unit tests (953 pass, 0 fail, 10 skipped), build and package dry-run pass; no live provider E2E.

Counts: primary **192/303 reviewed, 111 pending**; supplemental net-new pending **177**; primary + supplemental pending **288**; manual additions **14, 2 pending**; unresolved including manual **290**. Next primary candidate: `liangquanzhou/agentctl`. Research remains active/incomplete; no completion email sent.

## ResourcePlane candidate #193: agentctl (not SessionGraph)

`liangquanzhou/agentctl` is a useful reference for registry/capability-driven MCP/Skills/rules/hooks/commands/file projections, static subagent conversion, drift and rollback. Its `SubagentsSync` maps static role files, not runtime task children. It has no message/session/event import plane. Its Claude 3P Skills writer discovers a macOS private cache and is not sufficient for a production, cross-platform, profile-safe target adapter. Keep `ResourcePlane`/`HarnessAdapter` separate from canonical SessionGraph and the import/export evidence ledger. Review: `research/evidence/liangquanzhou-agentctl-review-2026-11-23.txt`.

## Candidate #194: pattern compiler is content transport, not session persistence

`lidorshimoni/agentic-coding-design-patterns` can project selected prompt/Skill text into several harness-specific instruction files, but its only “stateful” teaching example stores learning records in user-chosen files. It has no runtime session/message graph or import surface. Its Claude Code output is legacy commands; its broad untracked writes lack rollback/ownership and can replace existing rules. Use only as content metadata/reference; keep this separate from ResourcePlane, SessionGraph and native target adapters. See `research/evidence/lidorshimoni-agentic-coding-design-patterns-review-2026-11-23.txt`.

## Catalog/discovery source #195 — awesome-agent-plugins

Use this repo as a *secondary ResourcePlane discovery corpus*: its canonical YAML records distinguish MCP servers, portable Skills, native plugins/marketplaces, standards and tools; render per-client installers; keep alternatives/provenance; and validate catalog integrity. The README claims 589 entries/945 projects across 13 client IDs. Its Sessions & Messages page is a list of third-party utilities, not a session schema. Cross-reference and URL-deduplicate before importing leads; do not give catalog-listed code a security or migration-fidelity verdict from inclusion alone. Candidate #195 evidence: `research/evidence/LMPrado-DZ23-awesome-agent-plugins-review-2026-11-23.txt`.


## Candidate #196 — AgentHarnessManager groups Skills, not chat Sections

`mabyko/AgentHarnessManager` is a native macOS **ResourcePlane** manager with well-developed local review, approval, journaling and recovery patterns. Its `SkillGroup` contains only `skillIDs`, with activation changing Skill-file state; `WorkProfile` stores Skill member/path snapshots. Neither is a ChatGPT Project, Codex sidebar Section, or conversation-session hierarchy. The app has no transcript/project/session import/export model. Its stdio MCP exposes read/list/check/group/plan/request operations for the Skill library; writes are queued for human app review, and no apply tool is exposed. Keep it as a safety/UX reference, not a migration adapter. Exact pin/tests: `research/evidence/mabyko-agentharnessmanager-review-2026-11-23.txt`.



## Candidate #197 — credential workflow is not SessionGraph transport

madshn/ai-playbooks currently contains one Claude Code 1Password credential-management Skill. It moves environment variables and credentials between files/1Password, not Harness Projects, Sections, sessions, messages, branches, attachments, MCP declarations, memory, or schedules. Its “cross-harness” claim is about shell environment inheritance; Codex/Gemini are listed as not ported. The prompt workflow includes helpful manifest scoping and file-level cleanup concepts, but also writes plaintext temporarily, prints full rg hit lines, accepts equal-length-only vault checks, and can auto-stage/commit. Keep only the metadata-separation idea after a security review; do not model it as a migration adapter or rely on it without AI. Review: research/evidence/madshn-ai-playbooks-review-2026-11-23.txt.


## Candidate #198 — AntoSkills is a Skill ResourcePlane, not SessionGraph

magnumquest39-cloud/AntoSkills is a tested TypeScript MCP package manager for Claude Code and Codex Skills. Its immutable SHA/content lockfile, store, path checks and profile-as-Skill-ID set are useful ResourcePlane references. It has no chat Project/Section model, session/event/message/branch graph, attachment/usage mapper, memory/schedule importer or 3P Chat/Cowork writer. Claude Desktop Code overlap is unverified, so do not infer compatibility from its .claude/skills target. The installer checks name collisions against skills.lock but not pre-existing unmanaged directories, while linkSkill recursively clears a genuine directory at the destination. Reuse neither its data model nor destructive path behavior without a separate ownership/approval transaction. Review and test evidence: research/evidence/magnumquest39-cloud-antoskills-review-2026-11-23.txt.


## Candidate #199 — skill-forger manages Skill declarations, not session graphs

marcm8793/skill-forger wraps the Vercel Skills CLI around a repo-local skills.json and skills-lock.json. Its source list and optional Skill names are a lightweight ResourcePlane manifest; agent targets are delegated to the dependency rather than implemented as project/session adapters. There is no ChatGPT/Codex Project or Section model, transcript/session/branch graph, attachment/usage/memory/schedule transfer, or Claude Desktop 3P Chat/Cowork writer. In a synthetic all-skills uninstall, it removed manifest and lock entries while the previously materialized Skill file remained; the CLI emitted a warning. Keep only as an adjacent declaration/CLI reference. Full review: research/evidence/marcm8793-skill-forger-review-2026-11-23.txt.


## Candidate #200 — Skills Manager is a security-gated ResourcePlane, not SessionGraph

mazen160/skills-manager statically scans and installs Skills across four user-global agent directories. Its scanner architecture, deterministic policy gate, source inventory, stable findings, optional AI review boundary and update provenance are strong adjacent ResourcePlane references. It has no ChatGPT/Codex Project, Section, session/task tree, transcript, branch, attachment, usage, memory or schedule model. The published main target is global Skill storage, not conversation/session storage. Review the unmerged scanner PR separately; its TAR member-cap path misses a truncation finding, and copy_skill_tree deletes a backup even after restoration fails. Full evidence: research/evidence/mazen160-skills-manager-review-2026-11-23.txt.

## Candidate #201 — QA Skill library is ResourcePlane content, not a migration adapter

mejbaurbahar/awesome-qa-agent-skills catalogs Skills and projects them into Claude Code and Antigravity directories. Its commit/license ledger is useful for provenance metadata, but the implementation has no portable Project/Section/session graph or ChatGPT import/export. Keep imported Skill text as an independent ResourcePlane asset and never infer transcript/session fidelity from its shared Skill format. Its installer trusts manifest destination strings as ownership and recursively deletes them; its vendor refresh removes old directories before validating/copying replacements. Do not reuse that destructive implementation; require ownership-token checks, root containment, staging and rollback. Full evidence: research/evidence/mejbaurbahar-awesome-qa-agent-skills-review-2026-11-23.txt.

## Candidate #202 — skillpkg: useful package ResourcePlane, unsafe and archived

miles990/skillpkg models a Skill manifest/dependency graph, project-local package config, MCP definitions and target serializers; that is adjacent to Nexus Memory's ResourcePlane, not SessionGraph. Its README marks the project archived and points to Claude Code plugins. It has no Project/Section Group or conversation/session/branch/message/attachment/usage/memory/schedule model. Keep only the declarative resource ideas, not the implementation: cleanup deletes unowned output folders, MCP sync replaces the entire config, names can escape store/export roots, and incremental sync misses same-count asset content changes. Its core syncMcpConfig writer is only reached by syncAll, which CodeGraph finds called only by tests; CLI auto-sync and MCP sync_skills use syncToTarget. Full pinned source/runtime evidence: research/evidence/miles990-skillpkg-review-2026-11-23.txt.

## Candidate #203 — MlsMoon is a Skill/Unity resource catalog, not SessionGraph

MlsMoon/moon-game-dev-tool-manager separates ordinary Skills from Unity Plugin/Package paths but has no portable Project/Section or conversation/session graph. Its ordinary Skill installer takes catalog IDs into a path without root containment and replaces an existing non-Git destination without an ownership marker; a synthetic Core probe confirmed traversal outside a disposable workspace and deletion of an unmarked sentinel. The distinct Plugin/Package guard is not proof that all target paths are safe. Keep only catalog UX as an adjacent reference; Nexus writers must validate every path, verify ownership before replacement, stage writes and support rollback. Evidence: research/evidence/mlsmoon-moon-game-dev-tool-manager-review-2026-11-23.txt.

## Candidate #204 — Samsara is a useful memory plane, not SessionGraph

mocikadev/mocika-samsara models local Markdown experiences and promotes repeated lessons into rules; its MCP tools and OpenCode plugin demonstrate machine-triggered read injection. It does not model Projects/Sections, message trees, sessions, attachments, token usage, schedules, or native target restoration. Borrow the typed memory sidecar concept only after root containment, path-safe identifiers, zero-side-effect dry-run, provenance and secret-aware Git sync. Do not infer that auto-injection recreates a past session. Full evidence: research/evidence/mocikadev-mocika-samsara-review-2026-11-23.txt.

## Candidate #205 — AgentCrew is a team context log, not conversation history

AgentCrew's Project → Milestone → Task tree and append-only context notes can inspire a shared collaboration plane, but the context model stores only a target entity, author kind, timestamp and text note. Its `cs_s_` auth token and `cs_k_` MCP key are service credentials, not vendor conversation/session identities. There is no source-harness/message ancestry or attachment provenance and no session importer. Keep only the project/task provenance concept; do not flatten Nexus SessionGraph nodes into notes. The init writer's raw bearer token in `~/.claude.json` also needs restrictive permissions. Full evidence: research/evidence/pewpewgogo-agentcrew-review-2026-11-23.txt.

## Candidate #206 — aiToolManager's adapters are ResourcePlane only

Predator404/aiToolManager offers a useful pattern for explicit harness+scope adapters, canonical Skill/Command content, native MCP toggles and shadow sidecars. It models filesystem global/project configuration, not ChatGPT Projects/Sections or conversation/session trees. Its own tests passed, but temporary probes show writers can delete an unowned mirror directory, overwrite canonical imports, erase assets during promote when only SKILL.md matches, and relax an MCP config file to mode 0644. Borrow the adapter boundaries, not the destructive write paths; require content ownership, complete tree diff, staging, rollback and permission preservation. No license evidence to reuse source. Full evidence: research/evidence/predator404-aitoolmanager-review-2026-11-23.txt.


## Candidate #207 — Moringgroove is a local Code UI, not an interchange layer

Its tree is filesystem folder → app Agent records → local Claude Code `sessionId`; `.claude/projects` owns the native JSONL transcript. Web chat/PTY share one Claude session, while app history is a capped UI projection, not an event export. `docs/**/*.md` and `.claude/skills` are local context/resources, not ChatGPT Projects/Sections or a portable session graph. No parent/child/fork/session import/export or Desktop mode adapters. Keep only the same-session local UI concept; see `docs/research/evidence/pyhu26-public-agent-moringgroove-review-2026-11-23.txt`.


## Candidate #208 — Kimi Skill manager vs Kimi's native session exchange

This repository is one Kimi plugin Skill plus a local Node CLI for managing Agent Skills; it does not own session state. Kimi Code's separate native session model is `$KIMI_CODE_HOME/sessions/<workDirKey>/<sessionId>/{state.json,agents/*/wire.jsonl}` with fork/subagent streams and documented export/import. Keep the resource plane and SessionGraph distinct. Kimi's native import currently documents Claude Code/Codex only, bounded by date/count and using a summary wrapper plus preserved originals; it is not ChatGPT Project/Section migration. Full candidate and official-platform evidence: `docs/research/evidence/qingyunk-skill-manager-review-2026-11-23.txt`.


## Candidate #209 — durable memory is a projection, not the SessionGraph

The `inneros-personal-brain` review reinforces a hard schema boundary: durable curated facts/outcomes in Cognee are a useful shared MemoryPlane, but they do not preserve the source conversation event stream, parent/fork/branch topology, turn order, tool-result state, attachments or token accounting. Nexus must keep an immutable source SessionGraph and derive an explicitly consented/redacted memory projection from it; memory write APIs cannot be the archive or the restore target. Every shared-memory writer needs deterministic curation immediately before the write, including agent-callable tools and lower-level store adapters. See the pinned source and synthetic fake-client probes in `docs/research/evidence/rafa-innerchispa-inneros-personal-brain-review-2026-11-23.txt`.


## Candidate #210 — resource profiles are not Project Sections

MyAgentControl's five profiles and 248 registry entries describe preset OpenCode-compatible resources and their file dependencies. The `.mac/manifest.json` SHA-256 map is useful as a narrow installed-resource ownership ledger, but it does not represent source Project containment, Section Group membership, conversation ancestry, child tasks or message events. Keep a distinct ResourcePlane with per-harness native writers; never project these static `context/` files as a recovered SessionGraph. Its current writer/remover also lacks realpath/symlink containment: synthetic temp probes wrote outside `--dir`, adopted an unowned collided file into its manifest, then deleted that external sentinel. Record candidate #210 as a rejected writer until path ownership, staged transactions, and failure rollback are implemented. Evidence: `docs/research/evidence/rafaelqsantos-rqs-myagentcontrol-review-2026-11-23.txt`.


## Candidate #211 — portable Skill payload vs target runtime adapter

`ramon-sg/agent-skills` is a high-quality example of the ResourcePlane: a manifest-backed catalog of `SKILL.md` folders, dependency edges, per-repo overlays, scripts/references and deterministic tests. It contains no conversation/session data or Project/Section graph. The standard folder format does not standardize loader paths or runtime behavior: Codex uses `.agents/skills`; Claude Code documents `.claude/skills`; Cowork/cloud skills can be account-synced; OpenAI API skills can instead be remotely versioned bundle IDs. Keep a raw, provenance-preserving Skill bundle separate from target install/activation/permission semantics. `context: fork`, `argument-hint`, `project.md`, scripts, executable dependencies and account/plugin binding need explicit capability flags and a per-mode translation/loss report. See `docs/research/evidence/agent-skills-standard-runtime-paths-2026-11-23.txt`.


## Candidate #212 — MCP dependency manifests are not a SessionGraph

At pinned `ricardosalcedo/agentpack` commit `07b11d6bd182c533ac5a9c7093fb594670c7759b`, the manifest/lock model represents package names, versions, source/integrity, MCP transport, dependency edges, agent dependencies, capability contracts, profiles and tool metadata. This is a valuable ResourcePlane and dependency-DAG reference, with a narrow local JSON exporter for MCP server configuration. It has no ChatGPT Project or Section Group identity, session/event/branch/child-task graph, conversation messages, files/attachment payloads, token accounting, plugin/Skill payload inventory, scheduled tasks, or source-to-target ID lineage. Do not map package dependencies to conversation parent-child relations.

Security gate: `src/commands/import.rs` inserts `--command` verbatim into a generated JavaScript string before spawning Node; a disposable synthetic-SDK probe executed injected JavaScript and wrote a sentinel. `src/registry.rs::fetch_and_cache` uses `name.replace('/', "__")` without canonical path containment; the disposable `agentpack fetch .. --source file://...` probe wrote to `packages/../agentpack.json` and replaced the temporary project manifest. These probes stayed inside disposable temporary directories and used no real credentials/server. Exclude both import/fetch writer paths as reusable code until parameter serialization and path containment are repaired. Full reproduction and scope: `docs/research/evidence/ricardosalcedo-agentpack-review-2026-11-23.txt`.


## Candidate #213 — memory capsules are not a SessionGraph

`ctxbridge` gives Nexus Memory useful ResourcePlane ideas: per-project and global local memory stores; typed/tagged/pinned notes; MCP save/recall/sync tools; target instruction-file adapters; Git-friendly JSONL snapshots; and token-budgeted handoff capsules. Its tables model `memories`, tags, capsules, capsule items, and adapter sync state. They do not model ChatGPT/Codex Projects, Section Groups, session identity, message/tool events, parent/child task lineage, branch/checkpoint relationships, uploaded file bytes, or Claude Desktop 3P's per-mode stores. The JSONL exporter exports only project `memories`; importer recreates records rather than retaining source IDs or chronology. A capsule is a derived handoff payload, not the transcript/event stream.

Treat the project as a memory-plane/reference candidate, not a session importer. Reuse its file-sync patterns only after guarding symlink destinations and its dependency graph is remediated: the pinned bundled SQLite library is flagged by RustSec CVE-2026-119375 when opening a crafted DB/WAL pair; `chrono` is also listed as unmaintained. Full details and synthetic probes: `docs/research/evidence/roedyrustam-ctxbridge-review-2026-11-23.txt`.


## Candidate #214 — package-managing Skill content is not transferring sessions

`Saber5656/skillet` contributes a strong proposed ResourcePlane: immutable index entries; semver ranges; pinned Git commits and tree hashes; install consent; no execution of fetched SKILL payloads; enumerated extraction; bounded copy materialization; receipt-based drift and deletion; and an explicit adversarial test/release plan. But its v1 design only installs Agent Skills directories into Claude Code/Codex. It does not represent source Projects, Section Groups, sessions, parent/child tasks, messages/tool events, branches, attachment bytes, schedules, or destination resume IDs. MCP, Claude plugins, `.claude/commands`, and broader agent configuration are expressly out of scope.

Most importantly, this repository currently contains **the proposal, not the package manager**: no `src/`, `tests/`, `package.json`, lockfile, workflows, or license file. Its threats and rollback properties are intended controls, not verified behavior. Preserve it as design material only. The proposed Codex adapter path must be resolved against versioned official documentation and a live disposable profile before copying its adapter design. Evidence: `docs/research/evidence/saber5656-skillet-review-2026-11-23.txt`.

## Candidate #215 — context ledger is not SessionGraph

`ctx-manager` is a potentially useful ResourcePlane-side context-window convention: deterministic document slicing plus an append-only-looking compact phase ledger. It does not satisfy the canonical SessionGraph: no raw source events, stable source-message identity, branches, parent/child sessions, tools, media, attachments, token usage, Project/Section relations, schedules or target resume references. It must not replace provenance-preserving source records or the migration loss ledger.

Its current MCP calls accept a Docs-relative filename and project-configured ledger path without realpath containment. Synthetic tests confirmed reading outside the configured Docs root and writing outside the selected project. The fixed temporary ledger filename races under simultaneous writers; a forced 12-writer test lost 11 entries. MCP and CLI phase logic also disagree. If borrowing the concept, Nexus should use descriptor-safe relative paths, per-target locking/transaction journals, a claim-to-diff verification model, and shared schema/functions across CLI and MCP. Keep candidate #215 as a low-priority design reference only; evidence: `research/evidence/saturnarians-ctx-manager-review-2026-11-23.txt`.

## Candidate #216 — keep Skill ResourcePlane separate from SessionGraph

`sefas-labs/ai-skills-manager` contributes a useful adapter-driven resource inventory: provider path mappings, global/workspace/admin scopes, conflict visibility, Git commit/tree provenance, staged previews, exact diffs, consent, recoverable backup and rollback. Its four adapters are Claude Code, Cursor, Codex and Copilot. This is a resource plane over `SKILL.md` directories, not a session plane. It has no source Project/Section graph, Session IDs, messages, event ancestry, branches, interrupted continuations, attachments, tool call/result state, token usage, scheduled tasks, or target-native resume IDs; it does not write the three Claude Desktop 3P mode stores. Nexus should model Skills as a separately versioned/dependency-linked object, then attach its dependency edge to a SessionGraph node without flattening either representation. Full review: `research/evidence/sefas-labs-ai-skills-manager-review-2026-11-23.txt`.

## Candidate #217 — MCP inventory is not migration and its writer violates containment

`shqear93/mcp-manager` focuses on a registry of MCP server definitions and static projections into agent config files. MCP resource configuration is a ResourcePlane object; it is not the canonical SessionGraph or Project/Section/Conversation history. The implementation has no history/session data, no OAuth/session state export, and no ability to restore chat continuation. Source review found unsafe path use from unvalidated `definition.name`/CLI `name` to registry paths, recursive deletion before copy/symlink, config scope leakage and plaintext secret writes with default file permissions. No transactional source of truth or versioned adapter contract exists. Keep only the abstract registry idea; do not reuse the code. Evidence: `research/evidence/shqear93-mcp-manager-review-2026-11-23.txt`.


## Candidate #218 — Skill resource store is not SessionGraph

`simonwu53/agent-skills` keeps a local library of `SKILL.md` payloads, categories, source subpaths, pin state and installed target folders. That is an adjacent ResourcePlane and does not serialize any source session/event identity, parent/branch graph, Project/Section relation or target resume state. Keep `SkillBundle`/dependency provenance and a target-specific discovery/permission profile separate from `SessionGraph` edges; attaching a Skill to one session must not flatten or rewrite its own history. Its single `claude` path also cannot stand for three Claude Desktop 3P data planes: Chat/Cowork session-state and Code metadata/transcripts are stored separately, and app-managed Desktop Skills differ from Code filesystem Skills. Candidate evidence: `research/evidence/simonwu53-agent-skills-review-2026-11-23.txt`.


## Candidate #219 — host/scope-aware Skills remain a ResourcePlane

`sjmgarnier/skill-manager` is an AI-invoked installer/update workflow with repo-level Skill metadata; it does not archive a SessionGraph. Its `detect-platform.sh` infers identity from a path that is not unique: current Codex user Skills may live in `~/.agents/skills`, which the candidate classifies as Warp. This reinforces that each `SkillInstallation` needs explicit `host_id`, `scope`, resolved directory, actual installed ref/tree hash, and identity source—not inference from a shared directory name. Claude Desktop also has conditional account-shared Skills/Plugins plus device-local and org-managed delivery; these should be separate resource provenance edges attached to, but never substituted for, the SessionGraph. See `research/evidence/sjmgarnier-skill-manager-review-2026-11-23.txt`.


## Candidate #220 — derived learning KB is not the source SessionGraph

The archived `reflect-kb` v0.1.1 documentation describes a Git-backed Markdown KB with hashed note IDs, entity sidecars, GraphRAG/QMD retrieval and a Claude Code plugin. That is a useful **derived MemoryPlane**, not a faithful event archive: it has no source conversation/message IDs, Project/Section membership, session parent/fork edges, turn/tool payloads, attachments or resume references. Current Claude Code documents separately define Auto Memory (`~/.claude/projects/<project>/memory/`) and resumable transcript JSONL (`~/.claude/projects/<project>/<session-id>.jsonl`); reflect-kb's `~/.claude/global-learnings/` is a third store. Preserve this separation in Nexus: immutable SessionGraph → consented/traceable memory projections → target-specific recall adapters. The archived standalone repo has no code to reuse; evidence: `research/evidence/stevengonsalvez-reflect-kb-review-2026-11-23.txt`.


## Candidate #221 — Git-native Skill packages are not SessionGraph migration

summer-via/skill-package-manager is useful only as an adjacent ResourcePlane reference (skill.json, Git refs, lock/pin semantics). It has no conversation archive, Project/Section membership, session/event ancestry, user corrections/interruptions, media, token/cost, schedule, MCP/plugin state, or target resume model. Its install/remove functions unconditionally delete target directories and its manual remove path allows ../ escape in a synthetic fixture. Nexus must instead use typed ResourceInstallation records (source path/hash, host/version, user consent, ownership receipt, destination mode) and an atomic stage/verify/commit/rollback protocol. Review: research/evidence/summer-via-skill-package-manager-review-2026-11-24.txt.

Latest user confirmation keeps Desktop 3P Chat, Cowork, and Code all in scope. Anthropic’s current Enterprise-to-Desktop-on-3P guide explicitly names a customer LLM gateway, but its own migration wizard transfers Claude-origin data, not ChatGPT/Codex histories; local Cowork/Code sessions and cloud sessions have different eligibility. Maintain distinct readers/writers for desktop-chat, desktop-cowork, desktop-code, and local claude-code-cli; session-store identity is not inferred from the shared inference provider. Evidence: research/evidence/claude-desktop-3p-chat-cowork-code-scope-2026-11-23.txt.


## Candidate #222 — Skills Box is ResourcePlane prior art, not SessionGraph migration

sunven/skills-box demonstrates an adjacent ResourcePlane shape: a multi-agent catalog, global and local project Skill scopes, a native CLI-based plugin interface, update/discovery records, previewed operations and filesystem backups. Its Project is a registered local folder, and its persisted native-plugin operation record is the most recent management action per Claude/Codex CLI host—not an AI conversation or resumable session. It has no source Project/Section/session identifiers, turn/event graph, attachments, token ledger, memory/schedule transfer, Desktop 3P Chat/Cowork/Code adapters or target resume mapping. Scope all three Desktop 3P modes separately and do not infer session coverage from generic Claude/Codex plugin management. Evidence: research/evidence/sunven-skills-box-review-2026-11-24.txt.

Use only its validation/preview/verify and local scope concepts as prior art. Do not copy source code because GitHub declares no license. Also note that its current release is Apple Silicon macOS-only, operation snapshots have no restore workflow, and the latest pinned Rust lockfile audit has two vulnerability advisories. The app itself is not a migration prototype for ChatGPT/Codex Projects, Section Groups or Destruction Era sessions.


## Candidate #223 — stable Skill releases are ResourcePlane, not SessionGraph

suqiangqiang2012-dot/agent-skill-manager has useful release-lifecycle controls: stable-only source, typed Agent/OS/architecture targets, integrity hashes, staged package installs, per-agent state/backups, local-change overwrite confirmations, rollback confirmations, and separately gated Draft/publication/catalog actions. This is useful for packaging Nexus adapter/Skill payloads and provenance, but it does not archive or translate Projects, Section Groups, conversations, child/fork links, interruption lineage, attachments, tools, tokens, MCP/plugin state, schedules or native resume IDs.

Its current default Codex install path is CODEX_HOME/skills or ~/.codex/skills while the current official OpenAI reference lists .agents/skills and ~/.agents/skills. It needs an explicit compatible path profile plus host discovery validation before the ResourcePlane adapter is trusted. Only Codex Windows/macOS and WorkBuddy Windows are declared; Claude Code, Cursor, OpenClaw, DeepSeek Harness and WorkBuddy macOS remain planned. No license is declared, so do not copy source code. Full review: research/evidence/suqiangqiang2012-dot-agent-skill-manager-review-2026-11-24.txt.


## Candidate #224 — cross-harness session analytics are not SessionGraph migration

theonepichael/agent-toolkit's six local readers (Pi, Claude Code CLI, OpenCode, Copilot CLI, Antigravity and Codex CLI) are useful SessionObservability prior art: IDs, cwd/time, text, models, usage/cost, filters and malformed-record diagnostics. Its `SessionRecord` drops event identity/order, actual parent and fork edges, tools/results/permission events, attachments, project/section identity and resume handles; some adapters reduce lineage to a boolean subagent flag. Treat its rows as derived analytics, never the canonical archive. Nexus should preserve source events/relationships immutably first and compute these views second. The Claude Code JSONL reader does not implement Claude Desktop-on-3P Chat/Cowork/Code stores. The three target Desktop modes and local/self-hosted CLI remain separate profiles. Candidate evidence: `research/evidence/theonepichael-agent-toolkit-review-2026-11-24.txt`.


## Candidate #225 — telemetry projections and verified archives, not SessionGraph conversion

timianmalloo/x-harness-x-model-bench is useful prior art for Nexus's **SessionObservability** layer: native readers project Claude Code/Codex/Copilot/Antigravity/Grok records into measured model calls, tool calls, provider errors, missing-field diagnostics, served settings, reasoning items, prompt parts and harness events with native ordinals. Its run ledger and SHA-256-verified cell archives also demonstrate integrity-first benchmark snapshots. However, `Extraction` is intentionally a selective projection, not a raw message archive or cross-harness portable schema; it omits full user/assistant sequences, attachment payloads and project/Section/session parent/fork edges. `resume.py` resumes the benchmark run ledger and cells, not the harness conversation. Keep native bytes/events plus source relation IDs canonical; build these metrics rows as derived views. Full review: `research/evidence/timianmalloo-x-harness-x-model-bench-review-2026-11-24.txt`.

## Candidate #226 — routing/config hub and safe export, not SessionGraph

toshon-jennings/agent-advisor is a selectively routed workflow hub for Codex, Claude Code and Antigravity, exporting canonical platform plugin/config trees one-way to their separate repositories. It does not import/export conversation events, Projects/Sections, attachments or session lineage. Its spoke synchronizer is valuable adjacent ResourcePlane prior art: explicit origin/root identity; safe relative path and symlink containment; dirty/ignored-file refusals; validators; multi-target preflight/revalidation; checksum copy; post-write native validation and exact drift comparison; scoped compensation. Nexus can reuse these principles for resource/profile deployment and explain partial outcomes with evidence, not claim its workflow is a portable session format. Importantly, TOCTOU is narrowed rather than eliminated, and rollback after writes begin is per spoke, not a globally atomic commit; mixed results remain possible. Review: research/evidence/toshon-jennings-agent-advisor-review-2026-11-24.txt.

## Candidate #227 — a Skill resource manager, not SessionGraph transport

weixuanteo/skills-manager is a local cross-agent Skill directory inventory and install/update/remove UI. Its explicit Skill/provenance/location model, symlink deduplication, source preview, confirmation prompts and command log can inform the ResourcePlane UI and audit display. Its “project” denotes a local path; it has no Projects/SectionGroups, conversation events, branches, media, MCP history, schedules, memory or native resume. Keep package/catalog lifecycle and conversation graph migration separate. Do not reuse source code (no declared license), and consider the pinned Hono dependency audit findings before using it as a security reference. Full review: research/evidence/weixuanteo-skills-manager-review-2026-11-24.txt.

## Candidate #228 — QuestBoard convention, not SessionGraph transport

CyberGuild supplies explicit appointment and a manual project Markdown QuestBoard, not native session ancestry, durable message delivery, or Project/Section migration. Current official DSH docs expose separate planes: flat path-bound Workspace membership; per-Session append-only typed event logs with derived message history; provider-discovered Skills; host-owned schedules; and separate non-session Storage. Session header cwd and lineage metadata do not encode arbitrary nested Section Groups. Exact seed-prefix forks, subagent parenthood, Workspace membership and chronological follow-up are distinct typed edges. Preserve source Section nesting in Nexus metadata where DSH has no native field; never silently flatten it into a Skill or transcript label. The user's latest answer reconfirms Claude Desktop 3P Chat + Cowork + Code, plus local/self-hosted Claude Code; keep four independently versioned profiles. Evidence: `research/evidence/woodsettler-cyberguild-review-2026-11-24.txt`; `research/evidence/deepseek-harness-session-project-profile-2026-11-24.txt`.

## Candidate #229 — Skill catalog, not continuity plane

SkillHub implements only a local ResourcePlane catalog: repository metadata, shallow clones, `SKILL.md` discovery, and copy install/update/diff across static global agent paths. Its Git sync is limited to a public catalog JSON—not pinned Skill bodies, Project/Section structure, Session logs, or runnable continuation. It has no SessionGraph, event/branch/child lineage, attachment, MCP/plugin, schedule or memory import/export. Security/consistency review reproduced wildcard unauthenticated network API access, symlink escape when reading a cloned Skill, two valid owner/repo strings colliding to one clone directory, and stale destination files after update. Keep only the separation of shared catalog metadata from machine-local clones as an adjacent idea; do not copy code or expose it to real user state. Evidence: `research/evidence/xdlkc-skillhub-review-2026-11-24.txt`.

## Candidate #230 — versioned Skill registry, not SessionGraph

`xfan3696-collab/skillpkg` models one resource type: versioned SKILL.md tarballs in S3 with a JSON index and SHA. It can inspire a generic ResourcePlane blob/index format and separation of client from object-store credentials, but it does not map resources into each Harness's native global/project path, nor does it model Project/Section, Session events/branches, media, MCP/plugins, schedules, memory, lineage or resume. A mutable index and shared hash are not publisher signatures. The source itself is not safe to reuse: CLI path traversal, untrusted index path escaping temp download staging, default-open publish API, plaintext local publish tokens and lexical version ordering were reproduced in isolated fixtures. Evidence: `research/evidence/xfan3696-collab-skillpkg-review-2026-11-24.txt`.


## Candidate #231 — DSH Skill adapter, not SessionGraph

`Xichun123/dsh-skills-manager` demonstrates a narrow DSH ResourcePlane: private Skill storage, source lock/provenance, distinct global/workspace enablement and a manual-only policy kept outside source files. Its “Project” is a workspace path scope, not Projects/Sections or a conversation graph. It has no Session/event/lineage/media/MCP/plugin/schedule/memory import or resume and is not a reader/writer for the three Claude Desktop 3P modes or local Claude Code. The source is `UNLICENSED`. More importantly, open issue #1 reports the published plugin failing to activate and the custom RPC receiving HTTP 405 on DSH 0.2.0-rc.2; source registration and peer bounds are consistent with the report, but runtime findings remain reporter-attributed pending native reproduction. Keep only the design pattern; require a licensed, fixed, version-compatible adapter and native round-trip test before inclusion. Evidence: `research/evidence/xichun123-dsh-skills-manager-review-2026-11-24.txt`.


## Candidate #232 — cross-Harness workflow board, not SessionGraph

`yyeret/ai-threads-kanban` offers valuable adjacent SessionInventory UX: local readers, multiple native sessions per intent-level work thread, a persistent manual workflow overlay, and per-harness resume/archive actions. Its “thread” is not source lineage: IDs depend on repository basename and normalized first prompt, with same-repo fuzzy Jaccard clustering, so path collisions/false merges and missed continuations remain possible. The durable registry stores summary pointers, not raw events or a portable SessionGraph; it has no Project/Section/branch/parent/attachment/context import. Codex archive is a native state mutation; Claude/Gemini titles cannot be written. Keep as prior art for the UI/workflow layer only. Do not deploy as-is: the local unauthenticated server accepts state-changing GETs (synthetic Origin request reproduced in temp), and a crafted synthetic Codex session ID becomes an unquoted shell resume command (not executed). MIT license exists, but security and fidelity hardening are prerequisites for code reuse. Full review: `research/evidence/yyeret-ai-threads-kanban-review-2026-11-24.txt`.


## Candidate #233 — API-key CLI reference excluded by source provenance

`zuhabul/yo-code` documents local Anthropic-compatible API-key accounts for a single CLI, but does not present a portable Project/Session migration path in its public docs. Its own LICENSE/SOURCE_PROVENANCE state that the recovered code is proprietary Anthropic Claude Code material from a sourcemap leak and prohibit competing-product use/deployment. This is a legal stop gate: no implementation code or code-derived architecture may be used for Nexus; deeper source audit was deliberately stopped. README also reports the recovered full CLI cannot boot due to missing modules. Retain only as a screened lead, not as a Nexus design reference. Evidence: `research/evidence/zuhabul-yo-code-review-2026-11-24.txt`.
## Candidate #235 — local archive/search is a separate plane (2026-11-24)

`lvtd-dgtl/agent-history` is a strong reference for versioned read adapters, incremental/torn-JSONL reads, session aliases/fork hints, local memory-file indexing, read-only named-column SQLite access, coverage/retention checks, and retrieval integrations. Its canonical index is a chunk/provenance archive—not Nexus's event/SessionGraph. Session identity aliasing and `fork_of` hints do not encode a general graph of message parents, active branches, Project/Section membership, task/control edges, generated artifacts, typed media, or usage. The downloaded Claude.ai importer has no source project-to-conversation relationship in its current export adapter; it imports project docs/instructions and conversations as separate records.

Architectural implication: keep (1) immutable source event/archive, (2) normalized SessionGraph with native IDs and hierarchy edges, (3) target-native session writer, and (4) optional derived search/chunk index as separate artifacts and acceptance gates. Index/retrieval success is not proof of migration or resume. A target adapter must expose per-field loss/round-trip status and not turn unlinked records into inferred hierarchy.

Security implication: `agent-history` itself calls its local index a credential store; secret redaction defaults off locally and there is no at-rest encryption. Nexus should not inherit that default. Ingestion should default to a preview, preserve source bytes separately, redact secrets before any embedding/API egress, keep API keys in OS keychain/environment references rather than archives, and make retention/deletion/index destruction auditable. See `research/evidence/lvtd-dgtl-agent-history-review-2026-11-24.txt`.


## Candidate #236 — tmux workspace/process control is not session migration (2026-11-24)

`neosun100/aiw` models a live tmux process workspace plus a small metadata record (`tool`, `model`, `desc`, `dir`, `created`). This is useful adjacent orchestration, but it has no transcript reader/writer, event graph, source Project/Section relationship, Session parent/fork/task/artifact edges, attachment/usage model, or portable restore bundle. A project directory is a cwd binding, not a general project/group hierarchy. Keep this plane separate from immutable transcript archive, canonical SessionGraph and target-native importer.

Security boundary: AIW's management API can create workspaces, send commands, kill sessions and attach a browser terminal. Its default bind is `0.0.0.0`; no authentication middleware exists, and tmux subprocess calls use shell strings. AIW's own README advises adding reverse-proxy auth/HTTPS. Do not infer that a CLI/MCP wrapper makes command execution safe. Treat the tool as privileged local orchestration only, and do not import its default server posture into Nexus.

Dependency/API stability also matters: this pinned source uses the MCP Server decorator API available with mcp 1.0.0, but `pyproject.toml` leaves `mcp>=1.0.0` unbounded. On the current compatible mcp 2.3.0, all 14 MCP tests fail at import (`Server` has no `list_tools`); with 1.0.0, all 66 tests pass. Lock tested dependency ranges and smoke-test provider/MCP integrations independently.

## Corpus audit correction — candidate #234 evidence restoration (2026-11-24)

While reviewing #236, the actual #235 ZIP was reopened and found not to contain the #234 AgentVM evidence path named in the previous transaction ledger. Its primary inventory row also remained `unreviewed` although the ledger recorded the full review and tests. The current snapshot restores that evidence and reconciles the row; the count is computed against actual status flags. This is an artifact-integrity correction, not a new claim that the AgentVM tests were rerun today.


## Candidate #237 — derived knowledge graph vs source SessionGraph (2026-11-24)

`i3T4AN/Archivist-MCP` models project knowledge (Decision, Entity, Incident, Rule, Observation, Session and Artifact nodes) plus typed edges, version/lifecycle state and audit events. It is useful as a possible **post-import derived memory plane**: curated decisions/rules/incidents can persist across any MCP-connected clients, and core-memory Markdown/JSON can be generated under a token budget. Keep the untouched source archive and canonical Session/EventGraph separate: the materialized core memory is selective/truncated, and its `scope=branch` is a memory promotion state, not a conversation fork.

Do not mistake the SQL `sessions` table for a conversation log. It stores identity/project/user/client type and start/end timestamps; observations may reference one row. No MCP method creates or imports that relational session, no message/event ordering or parent/child hierarchy exists, and a generic graph node of type `Session` is not equivalent to a populated row. The safe probe confirmed a missing session FK fails as `INTERNAL_STORAGE_ERROR`.

Portability/security constraints: the only explicit `export_audit_log` surface returns limited audit metadata, not graph content; snapshot/restore is local SQLite recovery, not a portable cross-Harness bundle. Content is stored in SQLite without encryption by default, and the synthetic fake-key probe showed node content is not secret-redacted at ingest. Optional team transport has roles/project scope, but HTTP MCP permits unauthenticated requests if its token map is empty. A future Nexus-to-Archivist adapter must require a versioned memory export/import contract, encryption/redaction/retention controls and an explicit field-loss report; do not treat MCP connectivity as migration fidelity.


## Candidate #238 — work-session state is not conversation state (2026-11-24)

`maideps/ai-harness-framework` persists workflow Sessions as feature state, progress notes and git/verification trace records. Model these as `WorkSession`/`TaskProgress` and `VerificationEvidence`, not as a provider `ConversationSession`/`MessageEvent` graph. Its WIP=1 lanes, sharded feature files, user-owned surfaces, adoption backup and generated summary are useful project-workflow patterns only. Candidate tests do not establish transcript fidelity or desktop session resumption. See `research/evidence/maideps-ai-harness-framework-review-2026-11-24.txt`.

Official Claude Desktop 3P docs now expressly confirm Chat, Cowork and Code requests route through a gateway, with required streaming/tool-use support on Messages API. Gateway routing does not reconstitute native history; the Desktop gateway config is separate from local Claude Code CLI gateway env/settings. A configured third-party-inference target excludes Anthropic-hosted cloud environments and Remote Control. Keep `{surface, mode, execution locality, provider route, session store, import/resume capability}` as independent adapter/profile fields; test each mode separately.


## Candidate #239 — CLI session adapter is not a Project/session graph migrator (2026-11-24)

`1naruto-1/agent-connect` is valuable prior art for native coding CLI readers/writers and resume-effective transcript parsing, but its common model is a linear stream of `user`, `assistant-text`, `thinking`, `tool`, and `marker`. It intentionally projects active branches and counts skipped history; media, message IDs/parent edges, token usage, project/Section membership and resource configuration are outside the schema. Preserve full source event archives and explicit loss reports rather than treating a round-trip through this event union as lossless history.

Its Codex target writer imports the newest local target-Codex session's `base_instructions` and `turn_context` without requiring it to match the destination project; an isolated fake-marker probe reproduced unrelated context carryover. A Nexus target adapter should use explicit scope/config references or safe defaults and never inspect a user's unrelated project/session to create a new one.

Claude Desktop 3P requires mode/storage-aware writers: Chat/Cowork records live in `local-agent-mode-sessions/`; Code has app metadata in `claude-code-sessions/`, with transcript JSONL under shared `~/.claude/projects/`. Writing a CLI transcript alone may permit CLI resume but does not prove Desktop Code UI discoverability. Chat/Cowork and Code need distinct staged writers and native app-level verification. The vendor importer is source-specific (Claude export/earlier Desktop sessions) and one-time; it is not a ChatGPT archive adapter. Full evidence and first-party references: `research/evidence/1naruto-1-agent-connect-review-2026-11-24.txt`.


## Candidate #240 — local inventory is not migration; mutation plane is separate (2026-11-24)

AgentHoard distinguishes disk inventory, source-local archive flags and worktree cleanup; none of those is a portable SessionGraph or target-native import. Its session listing is flat metadata and its archive writer only handles DSH/Codex. The synthetic route probes also show why source discovery should be read-only by default: a loopback HTTP cleanup route accepted an Origin-tagged text/plain request to move an arbitrary path outside configured roots and a separate purge without confirm. In Nexus, enforce allowed-root containment plus origin/CSRF and authorization even on local services; require explicit confirmation for delete/move/restore and keep these operations outside the migration transaction. MCP confirmation on some tools does not substitute for server-wide mutation policy. See docs/research/evidence/dawnnnnnnnnnnnnnnnn-agent-hoard-review-2026-11-24.txt.


## Candidate #241 — curated memory projection is not a session archive (2026-11-24)

Mnemark's MIT store is useful as an optional destination for explicitly curated memory after user approval, but its project scopes, graph edges, workflow memories and Mnemark bundle do not encode ChatGPT Project/Section/Session hierarchy, message events, forks, subagents, attachments or target-native resumes. Its SessionStart hook is an injection point, not an ingestion adapter. Preserve immutable source events and the canonical SessionGraph independently; derive and loss-report any memory projection rather than treating memory import as transcript migration. Mnemark stores/bundles are plaintext; protect any optional adapter with trust downgrade, secret checks, encrypted storage/transfer and per-record scope mapping. See docs/research/evidence/neohsu-mnemark-review-2026-11-24.txt.


## Candidate #242 — live orchestration is not archival migration (2026-11-24)

README-only screen of slonana-labs/agichan describes manager/worker tasks, branches, encrypted live channel, MCP/Skill/CLI and Claude Code hooks. These do not encode a portable source ConversationSession/MessageEvent graph or target-native importer. No license grant was found, so source review and reuse stopped. Preserve the boundary between live task orchestration, memory projection and immutable conversation archive; do not infer session migration from a session-aware swarm. Evidence: docs/research/evidence/slonana-labs-agichan-review-2026-11-24.txt.


## Candidate #243 — local wake coordination is not session transport
A2A DMs is a side-plane pattern for waking an idle local terminal, not a canonical data adapter: a duty roster and ring file signal that an agent should inspect an external durable queue. Preserve this distinction in Nexus: control-plane wake notifications must not masquerade as message delivery, transcript migration, or SessionGraph preservation. The prototype has no source/target importer or record model. Its prompt-only zero-authority policy is not an enforceable trust boundary; the synthetic lease path escape and unsynchronized cooldown stores argue against direct code reuse. Evidence: `research/evidence/chrisreedbates-a2a-dms-review-2026-11-24.txt`.


## Candidate #244 — local retrieval plane, not canonical session transport
Agent Session Search is a useful read plane: source-root discovery, lexical probes, path canonicalization, bounded evidence, and search-result ranking can help locate sessions for an explicitly authorized export workflow. Keep it distinct from the canonical archive/importer. Its match-file candidates do not prove preserved Project/Section/Session edges, and a text snippet does not prove attachment or event fidelity. Its optional cass renderer is a narrow stdout projection, not a portable bundle. See `research/evidence/benvenker-agent-session-search-review-2026-11-24.txt`.


## Candidate #296 — local search indexes are not canonical archives (2026-11-25)

The `agents-sesame` review reinforces the boundary between a local retrieval/index plane and the canonical migration archive: its flat searchable session projection is useful for finding source material, but it does not encode Projects/Sections, event lineage, branch/subagent edges, attachments, or destination-native continuation. Search indexes may contain sensitive raw prompt/tool content; enforce private storage independently of the archive's permission policy. A search result or `--resume` in the original CLI is not proof of cross-Harness import or native target resume. Evidence: `docs/research/evidence/rucnyz-agents-sesame-review-2026-11-25.txt`.


## Candidate #297 — curated project memory is a distinct data plane (2026-11-25)

`agent-workflow-kit`'s `AGENTS.md` + `docs/ai/` handover/plan/decision/archive files are a useful cross-agent **curated context projection**, but they are not the canonical session/event archive. Keep user-authored summaries, source messages/tool payloads, project/sidebar membership, assets and target-native resume state separately typed, with provenance and explicit loss reports. A prompt-driven bootstrap is not a deterministic adapter; Skills/launcher distribution does not imply MCP/plugin/schedule migration. Review evidence: `docs/research/evidence/sabaiway-agent-workflow-kit-review-2026-11-25.txt`.


## Candidate #298 — browser prompt handoff is not session migration (2026-11-25)

Continuity's browser extension illustrates a narrow, explicitly lossy **capture → summarize/handoff → inject into text field** lane. Treat this as a projection from DOM text, not a canonical archive: stable conversation IDs, message lineage, branches, Projects/Sections, tools, attachments and native resume are absent. Preserve local transcript hierarchy and assets independently; keep API summarization opt-in and permission-checked; verify that deletion clears both persistence and live caches. Evidence: `docs/research/evidence/samiahmadbeg-continuity-review-2026-11-25.txt`.


## Candidate #299 — read-side session model and local-cache boundary (2026-11-25)

`session-history` contributes useful source-side concepts—typed turn/items, stable references, tool/result joins, compaction boundaries, fork lineage, subagents, and bounded views. Keep these in an immutable source-history plane; this candidate has no target writer. Its display redaction is not at-rest redaction: `buildDigest()` persists raw transcript items, so cache privacy must be enforced separately. Handoff summaries and lineage suggestions are projections, not a canonical project/session graph. Evidence: `docs/research/evidence/seroliya-session-history-review-2026-11-25.txt`.


## Candidate #300 — context cards are projections, not archives (2026-11-25)

The linked Context Transfer product confirms an important Nexus boundary: provider-neutral prose cards can be useful portable handoff artifacts, but they are model-generated, lossy projections. Keep them downstream of the canonical immutable source graph. ChatGPT's selected current-node path and Claude's chronological text are not the complete source tree or message envelope; IDs, timestamps, multimodal payloads and event edges must remain in the loss-aware archive. Native destination writers and import/resume checks are independent from successful card generation. Context cards should carry explicit provenance, omissions and review status, never be treated as proof that a native session migrated. Evidence: `docs/research/evidence/shivala-08-contex-landing-page-review-2026-11-25.txt`.


## Candidate #301 — Skills distribution is a separate plane (2026-11-25)

The prompt-only `steam-soda/skill-manager` and the mature `vercel-labs/skills` CLI reinforce that portable Skill files need their own adapter/lock plane, separate from canonical session/event migration. The CLI's source/ref/commit/content-hash lock and per-Harness path fan-out are useful prior art; they do not preserve a conversation graph, a Project/Section hierarchy, MCP configuration, or plugin runtime state. A Skill can trigger optional, reviewable, consent-gated actions but cannot guarantee session-start automation across hosts. Updates must be transactional: inventory local edits, produce a diff/backup, and only then replace; do not let `-y` or a check label imply safe/no-op. Treat `.claude-plugin` manifests as Skill-discovery inputs, not proof of plugin portability. Evidence: `docs/research/evidence/steam-soda-skill-manager-and-vercel-skills-review-2026-11-25.txt`.


## Candidate #302 — explicit transaction adapters remain separate from migration (2026-11-25)

The Fantasy Basketball Manager demonstrates a small, auditable MCP write pattern: expose mutation tools only behind a startup flag, require a fresh source snapshot, dry-preview and validate the exact target request, journal intent before one send, then verify by readback and do not auto-retry ambiguity. Nexus may adapt this boundary for target-side import/export: keep import permission separate from read-only discovery, bind previewed source/target identities and payload hashes, journal before writes, read back the resulting native hierarchy, and require human review when the destination cannot prove atomicity. This remains separate from its source of truth/archive. Do not copy the implementation: no license grant, app-specific ESPN schema, and its journal permission probe showed 0644 under a permissive fake HOME. Evidence: `docs/research/evidence/thespaceblade-fantasy-basketball-manager-review-2026-11-25.txt`.


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
