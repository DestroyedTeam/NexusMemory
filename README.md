# Nexus Memory

**Local-first, zero-AI, deterministic, loss-aware migration across AI agent Harnesses.**

Nexus Memory migrates AI agent **Projects**, **Section Groups** (e.g. Codex `Destruction Era`), **Session DAGs** (branches, forks, subtasks, tool calls/results, interruptions), **binary attachments (SHA-256)**, **links**, **token/cost usage**, and **Resource Planes** (**Skills**, **secret-stripped MCP servers**, **Instructions**, **Memory**, **advisory Permission hints**, and **disabled-by-default Schedules**) across Harnesses — **pure Python 3.11+ stdlib, zero LLM calls at runtime, dry-run by default, with pristine-hash rollback**.

---

## 1. Supported Harnesses & Bidirectional Matrix (25 Harnesses / Lanes · 23 Full Bidirectional)

Run `nexus-memory matrix` for the machine-readable matrix (`E1` Docs → `E2` Schema Audit → `E3` Unit Fixtures → `E4` Real CLI / Isolated Runtime → `E5` Real User-Session Live Continuation):

| Harness / Lane | Surface | Evidence | Read | Write | Bidirectional? | Key Notes |
|---|---|---:|:---:|:---:|:---:|---|
| **OpenAI Codex CLI / App** (`codex-cli`) | `cli` / `desktop` | **E5** | Yes | Yes | **Yes** | Streams `.jsonl`/`.jsonl.zst`, joins `state_5.sqlite` (`projects`, `project_roots`, `thread_sections`, `thread_spawn_edges`) + `thread_history_1.sqlite`; live `codex 0.154.0 exec resume` verified |
| **Claude Code CLI** (`claude-code`) | `cli` | **E5** | Yes | Yes | **Yes** | Local / self-hosted API key or 3P gateway (`~/.claude/projects/<encoded-cwd>`); strict alternating-turn coalescing; live `claude 2.1.172 --resume` verified |
| **Google Antigravity** (`antigravity`) | `ide-ext` | **E5** | Yes | Yes | **Yes** | Full bidirectional `brain/<conv-id>/.system_generated/logs/transcript.jsonl` + `transcript_full.jsonl` + `metadata.json` (protected by `0600` backup & pristine rollback); live continuation into Claude & Codex verified; copy-mode skills |
| **Claude Desktop 3P — Chat / Cowork / Code** (`claude-desktop-3p-*`) | `desktop-3p` | **E4** | Yes | Yes | **Yes** | Strictly separated 3 lanes aligned to `Claude.app 7.37095.0`; Code lane dual-key verified (`cliSessionId` + `encodedProjectDir`) |
| **Cursor** (`cursor`) | `ide-ext` | **E4** | Yes | Yes | **Yes** | Bidirectional SQLite `state.vscdb` (`cursorDiskKV`: `composerData:*` + `bubbleId:*`) with collision protection & pristine rollback |
| **Tencent WorkBuddy** (`workbuddy`) | `desktop-app` | **E5** | Yes | Yes | **Yes** | Real `~/.workbuddy/workbuddy.db` + `projects/<encoded-cwd>/<id>.jsonl` (`<user_query>` unwrapping) + skills/MCP |
| **T3 Code** (`t3code`) | `desktop-app` | **E5** | Yes | Yes | **Yes** | Real `t3 doctor` + `t3 serve` verified: `statev2.sqlite` projections, `orchestration_events`, tags & `lineage` |
| **OpenCode** (`opencode`) | `cli` | **E5** | Yes | Yes | **Yes** | Real `opencode 2.4.1` (`session list` + `export`) verified: `opencode.db` v1/v2 (`session_v2`) + split `storage/` + MCP/skills |
| **Pi Coding Agent** (`pi`) | `cli` | **E5** | Yes | Yes | **Yes** | Real `pi 0.73.0 --export` verified: native tree-DAG JSONL (`id`/`parentId`) preserving multi-branch topology |
| **Gemini CLI** (`gemini-cli`) | `cli` | **E5** | Yes | Yes | **Yes** | Real `gemini 0.33.1 --list-sessions` verified: `tmp/<slug>/chats/session-*.json` + `.project_root` + lossless `projects.json` merge |
| **AWS Kiro** (`kiro`) | `cli` / `ide` | **E5** | Yes | Yes | **Yes** | Real `kiro-cli 3.6.2` & `Kiro.app 1.5.49` verified: full 8-table + `migrations` (v0..10) `data.sqlite3` (`conversations_v2`) + `sessions/cli/<id>.jsonl` + steering/MCP |
| **Sourcegraph Amp** (`amp`) | `cli` | **E3** | Yes | Yes | **Yes** | `~/.local/share/amp/threads/<id>.json` thread JSON |
| **ByteDance Trae / Trae Agent** (`trae`) | `ide-ext` | **E3** | Yes | Yes | **Yes** | Trae trajectory JSON preserving workspace & alternating turns |
| **Warp / Oz Agent** (`warp-oz`) | `terminal` | **E4** | Yes | Yes | **Yes** | Real `warp.sqlite` (`agent_conversations` + `ai_queries`, token-redacted) + `~/.warp/sessions/*.json` |
| **DeepSeek Harness (DSH)** (`dsh`) | `cli` | **E5** | Yes | Yes | **Yes** | Official `@deepseek-ai/dsh@0.2.2` verified (`Session.fromRestore`): V4 `sessions/<projectKey>/<id>/session.v4.jsonl[.zstd]` (2-frame checksummed Zstd) + legacy V4>V2 JSONL |
| **Cline / Roo Code** (`cline-roo`) | `ide-ext` | **E4** | Yes | Yes | **Yes** | Real `cline 3.0.75 history --json` & Open VSX `rooveterinaryinc.roo-cline@3.54.0` verified: `data/db/sessions.db` + `data/tasks/<id>/{api_conversation_history,ui_messages}.json` + Cursor `globalStorage` |
| **Goose** (`goose`) | `cli` | **E4** | Yes | Yes | **Yes** | Real `goose 1.61.1 session list & export` verified: `sessions/sessions.db` (schema v18) + legacy `.jsonl` |
| **Continue / Zed (Z Code / ACP)** (`continue`, `zed`) | `ide-ext` | **E4** | Yes | Yes | **Yes** | Real `cn 1.5.47 ls --json` & `Zed 1.30.2`: Continue `sessions.json` + `<id>.json` and Zed `threads/threads.db` (`json`/`zstd`) + JSON |
| **Aider** (`aider`) | `cli` | **E4** | Yes | Yes | **Yes** | Verified alongside `aider 0.86.2`: `.aider.chat.history.md` markdown turns read + write |
| **ChatGPT Export (ZIP / JSON)** (`chatgpt-export`) | `web-export` | **E3** | Yes | No | Export archive | Offline web export (no local writable store); full mapping DAG, fork points, interruptions, ZIP binary assets (SHA-256) |
| **Codex App** (`codex-app`) | `desktop` | **E5** | Yes | Yes | **Yes** | Full bidirectional read+write via shared `~/.codex` store & snapshot JSON preserving sidebar Sections separately from Projects |
| **Windsurf** (`windsurf`) | `ide-ext` | **E3** | Yes | Yes | **Yes** | Bidirectional `~/.codeium/windsurf/cascade/<id>.json` (`windsurf.cascade.v1`) + Skills, `mcp_config.json`, `.windsurfrules` |
| **Anthropic Hosted Cloud** (`claude-cloud-hosted`) | `hosted` | **E1** | No | No | Cloud-hosted | Requires `claude.ai` account auth; explicitly excluded from local API-key/3P gateway targets |

> **Lossless Portable Archive (`--to portable`):** Every migration bundle also writes `portable.json` (v2 canonical DAG + hierarchy + SHA-256 `assets/` + sanitized `resources/`) and `HANDOFF_REPORT.md`, so nothing native-unsupported (sidebar sections, multi-branch forks, tool metadata, images) is ever silently dropped.

---

## 2. Real-World Migration Scenarios

1. **Codex / ChatGPT `Destruction Era` → Claude Code CLI or Claude Desktop 3P (Chat / Cowork / Code):**
   - Filter a specific Codex sidebar section (`--section "Destruction Era"`) or project (`--project "..."`) directly from `~/.codex` (`state_5.sqlite` + `.jsonl.zst`) or a ChatGPT export ZIP, and project into `claude-code` or `claude-desktop-3p-all` (all 3 Claude Desktop 3P lanes staged cleanly without conflation).
2. **Claude Code ↔ Codex Bidirectional Handoff:**
   - Move active coding sessions between Claude Code (`~/.claude/projects`) and Codex (`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` + merged `session_index.jsonl`) without triggering API `400 Invalid Params`.
3. **Antigravity ↔ Claude Code / Codex / Gemini CLI Bidirectional Handoff:**
   - Extract or write Antigravity `brain/<conv-id>/.system_generated/logs/transcript.jsonl` + `metadata.json` (with `0600` pre-apply backup & exact SHA-256 rollback) and resume the exact context across Harnesses.
4. **Cross-CLI / IDE Portability (`OpenCode` / `Pi` / `Cursor` / `Cline` / `Goose` / `Continue` / `Zed` / `Aider` / `DSH`):**
   - Migrate sessions, Skills (copy-mode safe across macOS/Windows/Antigravity), and secret-stripped MCP server templates (`${ENV_VAR}`) across all supported tools.

---

## 3. Real-CLI & Live Continuation Verification (Zero Writes to Real Homes)

All probes below were executed against **real installed binaries** on macOS using 1–2 small read-only samples inside disposable sandboxes (zero mutations to `~/.codex`, `~/.gemini/antigravity`, `~/.claude/projects`, or `Claude-3p`):

| Verification Route | Target Binary | Protocol / Live Result | Bugs Caught & Fixed During Verification |
|---|---|---|---|
| **Codex (`Destruction Era`, `.jsonl.zst` + `state_5.sqlite`) → `claude-code`** | `claude 2.1.172 --resume` | **PASS (Live + Validator)** — `rc=0`, `consec_same=[]`, zero `Invalid Params`, real gateway continuation reply | Fixed consecutive same-role turns (`_coalesce_alternating_turns`), streaming >256 MiB rollouts, `project_roots` + `thread_sections` joins, and `.jsonl`→`.jsonl.zst` auto-resolution |
| **Antigravity (`transcript.jsonl`) → `claude-code`** | `claude 2.1.172 --resume` | **PASS (Live + Validator)** — `rc=0`, zero `Invalid Params`, real gateway continuation reply | Added strictly read-only Antigravity `transcript.jsonl` parser (`<USER_REQUEST>` extraction + tool event handling) |
| **OpenCode (split storage) → `claude-code`** | `claude 2.1.172 --resume` | **PASS (Validator)** — `rc=0`, `consec_same=[]`, zero `Invalid Params` | Added real split `storage/{session,message,part}` reader & writer |
| **Pi (`.jsonl`) → `claude-code`** | `claude 2.1.172 --resume` | **PASS (Validator)** — `rc=0`, `consec_same=[]`, zero `Invalid Params` | Verified tree-DAG branch flattening + lossless sidecar |
| **Claude Code → `codex`** | `codex 0.154.0 exec resume` | **PASS (Live + Validator)** — `rc=0`, zero `Invalid Params`, real live continuation reply | Fixed `session_meta.source` Rust enum (`"cli"`), `originator`/`cli_version`/`timestamp`, JSON-stringified `function_call.arguments`, strict `call_id` pairing, and `session_index.jsonl` lossless merge |
| **Antigravity → `codex`** | `codex 0.154.0 exec resume` | **PASS (Live + Validator)** — `rc=0`, zero `Invalid Params`, real live continuation reply | Verified paired tool filtering prevents Responses API `Invalid Params` |
| **Codex (`Destruction Era`) → `gemini-cli`** | `gemini 0.33.1 --list-sessions` | **PASS (Real CLI)** — `rc=0`, migrated session discovered & listed cleanly | Added `.project_root`, SHA-256 `projectHash`, and lossless `projects.json` merge |
| **Codex (`Destruction Era`) → `claude-desktop-3p-all`** | Isolated `Claude-3p` (`7.37095.0` schema) | **PASS** — Chat + Cowork + Code readback OK, `transcript_project_verified=True`, rollback exact SHA-256 match | Aligned sidecar fields (`cliSessionId`, `originCwd`, `titleSource`, `permissionMode`, `completedTurns`, `indexedAt`) |

---

## 4. Security & Transaction Guarantees

- **Dry-run by default:** `discover`, `inspect`, `matrix`, `resources`, `convert` (without `--write`), and `apply` (without `--apply`) never modify disk.
- **Zero credential leakage:** Strips API keys, OAuth tokens, cookies, and secret MCP env values into `${ENV_VAR}` placeholders; escapes prompt-injection closing tags in `HANDOFF_REPORT.md`.
- **Two-stage write gate + path containment:** Malformed config blocks writes safely; cloud-synced roots (iCloud/Dropbox/OneDrive/Google Drive/Box) require explicit `--allow-cloud-sync-path`; all paths verified via `is_relative_to` with symlink rejection.
- **Atomic writes + exact rollback:** `0o700`/`0o600` permissions, `os.replace` writes, `--on-collision refuse` default (with lossless merges for `session_index.jsonl` and `projects.json`), `0o600` pre-apply pristine tar backup, immediate post-write readback verification, and exact pristine-SHA-256 `rollback`.
- **Hardened offline viewer (`127.0.0.1`):** Strict CSP, `nosniff`, `assets/` containment, forced `attachment` download for HTML/SVG/JS.

---

## 5. Usage (CLI, Agent Skill, macOS `.app`, Windows `.exe`)

### A. CLI (Python 3.11+, zero runtime dependencies)

```bash
# 1. Read-only Harness discovery
PYTHONPATH=src python3 -m nexus_memory discover --project /path/to/workspace

# 2. Compatibility matrix (full or pairwise)
PYTHONPATH=src python3 -m nexus_memory matrix --format markdown
PYTHONPATH=src python3 -m nexus_memory matrix --from codex-cli --to claude-code

# 3. Inspect a Codex section (e.g. "Destruction Era") or ChatGPT export ZIP (read-only)
PYTHONPATH=src python3 -m nexus_memory inspect ~/.codex --from codex --section "Destruction Era" --limit 5

# 4. Preview -> Stage local bundle (--write) -> Verify
PYTHONPATH=src python3 -m nexus_memory convert ~/.codex --from codex \
  --section "Destruction Era" --limit 1 \
  --to claude-code --cwd /path/to/workspace --out /tmp/de-bundle --include-resources --write
PYTHONPATH=src python3 -m nexus_memory verify /tmp/de-bundle

# 5. Dry-run apply -> Transactional --apply -> Exact rollback or post-verify backup cleanup
PYTHONPATH=src python3 -m nexus_memory apply /tmp/de-bundle --target-root /tmp/isolated-claude
PYTHONPATH=src python3 -m nexus_memory apply /tmp/de-bundle --target-root /tmp/isolated-claude --apply
PYTHONPATH=src python3 -m nexus_memory rollback /tmp/de-bundle/.transactions/<tx-id> --cleanup-backup
PYTHONPATH=src python3 -m nexus_memory cleanup --prune --keep 3 --max-age-days 7 --max-mb 512 --apply

# 6. Hardened 127.0.0.1 offline bundle viewer
PYTHONPATH=src python3 -m nexus_memory viewer /tmp/de-bundle --port 8765
```

### B. Agent Skill (`skills/nexus-memory/`)

Copy [skills/nexus-memory/](skills/nexus-memory/) (`SKILL.md` + `scripts/run_nexus.sh`) into `~/.claude/skills/nexus-memory`, `~/.codex/skills/nexus-memory`, or `~/.agents/skills/nexus-memory` (copy mode).

### C. macOS `.app`, Windows `.exe`, & Debian/Ubuntu `.deb`

```bash
# macOS: Rebuild & verify native app bundle (ad-hoc signed, bundles src/nexus_memory)
python3 packaging/macos/build_macos_app.py
codesign --verify --deep --strict "dist/Nexus Memory.app"
"dist/Nexus Memory.app/Contents/MacOS/nexus-memory-app" --self-test
open "dist/Nexus Memory.app"

# Linux (Debian 12/13, Ubuntu, etc. — universal amd64/arm64 .deb)
python3 packaging/linux/build_deb.py
sudo apt install ./dist/nexus-memory_0.2.1_all.deb
nexus-memory --version
nexus-memory-desktop
```

Windows standalone `.exe` packaging specs live in [packaging/windows/nexus_memory.spec](packaging/windows/nexus_memory.spec) and [packaging/windows/build_windows.ps1](packaging/windows/build_windows.ps1), with prebuilt binaries published on GitHub Releases.

---

## 6. Research Corpus & Tests

- [docs/RESEARCH.md](docs/RESEARCH.md) — 326 source-audited GitHub repositories (303 primary + 23 manual, 0 pending)
- [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) & [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/research/supplemental-skills-managers-triage-2026-11-25.md](docs/research/supplemental-skills-managers-triage-2026-11-25.md) — 192 catalog rows triaged (177 net-new Skills managers)

```bash
# Full automated suite: unit + 625 (25x25) individual pairwise links + 576 batch N×N + Playwright Chromium GUI E2E + real-binary CLI acceptance
python3 -m pytest -q tests
```

---

## 7. License

Released under the [MIT License](LICENSE).
