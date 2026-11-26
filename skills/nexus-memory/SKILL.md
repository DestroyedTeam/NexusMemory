---
name: nexus-memory
description: Deterministic, zero-AI-guesswork migration of AI agent Projects, Section Groups, Session DAGs, attachments, Skills, and secret-stripped MCP configs across Harnesses (ChatGPT, Codex, Claude Code CLI, Claude Desktop 3P Chat/Cowork/Code, OpenCode, Cursor, Windsurf, DSH, Cline/Roo, Gemini CLI, Antigravity, Pi, Goose, Aider, Continue, Zed, WorkBuddy, T3 Code, Kiro, Amp, Trae, Warp/Oz).
---

# Nexus Memory Agent Skill

Use this skill whenever the user wants to **discover, inspect, preview, migrate, verify, or roll back** AI agent Projects, Section Groups, conversation histories, attachments, Skills, or MCP configurations across Harnesses without ad-hoc manual guesswork.

## Mandatory Safety Rules

1. **Dry-run first, always.** Never pass `--write` or `--apply` until you have run `inspect` or dry-run `convert`/`apply` and confirmed the target lane and scope with the user.
2. **Never copy or transmit credentials.** Nexus Memory strips API keys, OAuth tokens, cookies, and secret MCP env values into `${ENV_VAR}` placeholders. Never bypass redaction or copy raw credential files.
3. **Preserve Claude Desktop 3P lane separation.** Never conflate or symlink:
   - `claude-desktop-3p-chat` (`Claude-3p/local-agent-mode-sessions`, mode `chat`)
   - `claude-desktop-3p-cowork` (`Claude-3p/local-agent-mode-sessions`, mode `cowork`)
   - `claude-desktop-3p-code` (`Claude-3p/claude-code-sessions` + `~/.claude/projects/<encoded-cwd>`)
   - `claude-code` (local / self-hosted Claude Code CLI, `~/.claude/projects/<encoded-cwd>`)
   - Anthropic-hosted Claude Code Cloud / `claude.ai` Projects are **not** an API-key gateway target.
4. **Never guess missing memberships.** If a source export lacks Project or Section Group metadata, keep it in the explicit `unknown` bucket rather than inventing names.
5. **Always verify and keep rollback handles.** After `--apply`, immediately check the `post_write_verification` status and retain the transaction journal directory for exact pristine-hash `rollback`.

## Standard Deterministic Workflow

```bash
# 1. Read-only Harness discovery (macOS / Windows / Linux)
scripts/run_nexus.sh discover --project /path/to/workspace

# 2. Check deterministic capability & fidelity matrix for a route
scripts/run_nexus.sh matrix --from chatgpt-export --to claude-code

# 3. Inspect source export (filter by project e.g. "Destruction Era")
scripts/run_nexus.sh inspect /path/to/chatgpt-export.zip --project "Destruction Era"

# 4. Preview conversion (no files written)
scripts/run_nexus.sh convert /path/to/chatgpt-export.zip \
  --project "Destruction Era" \
  --to claude-code \
  --cwd /path/to/workspace \
  --out /tmp/destruction-era-bundle \
  --include-resources

# 5. Stage verified local bundle (private 0700/0600 permissions, zero network calls)
scripts/run_nexus.sh convert /path/to/chatgpt-export.zip \
  --project "Destruction Era" \
  --to claude-desktop-3p-all \
  --cwd /path/to/workspace \
  --out /tmp/destruction-era-3p-bundle \
  --include-resources --write

# 6. Verify bundle integrity, SHA-256 assets, and secret-redaction audit
scripts/run_nexus.sh verify /tmp/destruction-era-3p-bundle

# 7. Dry-run transactional apply -> explicit --apply -> rollback if needed
scripts/run_nexus.sh apply /tmp/destruction-era-3p-bundle --target-root /path/to/Claude-3p --claude-dir /path/to/.claude
scripts/run_nexus.sh apply /tmp/destruction-era-3p-bundle --target-root /path/to/Claude-3p --claude-dir /path/to/.claude --apply
scripts/run_nexus.sh rollback /tmp/destruction-era-3p-bundle/.transactions/<tx-id>

# 8. Inspect bundle safely in hardened 127.0.0.1 offline viewer
scripts/run_nexus.sh viewer /tmp/destruction-era-3p-bundle --port 8765
```

## Supported Targets (`--to`)

- `claude-code`: Local / self-hosted Claude Code CLI (`~/.claude/projects/<encoded-cwd>`)
- `claude-desktop-3p-chat`: Claude Desktop 3P Chat lane
- `claude-desktop-3p-cowork`: Claude Desktop 3P Cowork lane
- `claude-desktop-3p-code`: Claude Desktop 3P Code lane (dual-key staged index + transcript)
- `claude-desktop-3p-all`: Stage all three Claude Desktop 3P lanes separately in one bundle
- `codex`, `antigravity`, `cursor`, `windsurf`, `opencode`, `pi` (native multi-branch DAG), `dsh` (V4), `gemini-cli`, `cline-roo`, `goose`, `continue`, `zed`, `aider`, `workbuddy`, `t3code`, `kiro`, `amp`, `trae`, `warp-oz`, `portable` (lossless canonical v2 archive)
