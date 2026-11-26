# Supplemental Catalog Triage: `awesome-agent-skills-managers` (2026-11-25)

- **Source:** `zhuyansen/awesome-agent-skills-managers` @ `855e594724f937a642fc044d7b6432c6f7a69332` (`data/skills.json`, generated `2026-11-21`)
- **Total rows:** 192 (15 overlapping with already source-audited primary/manual inventory; **177 net-new**).
- **Key finding:** 100% of the 177 net-new entries belong to the **Skills / Plugin / Registry resource plane** (`cli`, `app`, `registry`, `general`, `sync`, `team`). **None** of the 177 net-new entries is a cross-Harness session-graph, ChatGPT Projects/Sections, or Claude Desktop 3P (`Chat`/`Cowork`/`Code`) migration tool.
- **Triage disposition:** Classified as Skills-plane ecosystem inventory. High-signal Skills-plane engineering patterns (path containment, per-tool copy-vs-symlink fallback for Antigravity, central repo + multi-target fan-out, lockfile hashing, gateway `SKILL.md` on-demand loading) were extracted via source audits of top representatives (`vercel-labs/skills`, `xingkongliang/skills-manager`, `nikships/skills-registry`, `shenysun/skills-manager`, `slash9494/ai-config-sync-manager`) and built directly into Nexus Memory v1.0's resource plane.

## Breakdown of 177 Net-New Entries
- **Categories:** `cli`: 54, `app`: 46, `registry`: 36, `general`: 25, `sync`: 11, `team`: 5
- **Top Languages:** `TypeScript`: 64, `Python`: 38, `Go`: 21, `JavaScript`: 14, `Rust`: 13, `HTML`: 7, `Unspecified`: 6, `Shell`: 4, `Swift`: 4, `Vue`: 3
- **Reported Licenses:** `MIT`: 109, `None`: 32, `Apache-2.0`: 28, `NOASSERTION`: 6, `AGPL-3.0`: 1, `GPL-3.0`: 1
- **Missing License Metadata:** 32 entries (reuse license-gated).

## Top 20 Starred Net-New Skills-Plane Entries (Snapshot Metadata)
| Stars | Repository | License | Language | Category | Description |
|---:|---|---|---|---|---|
| 28,201 | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) | MIT | - | registry | PM Skills Marketplace: 100+ agentic skills, commands, and plugins — from discovery to strategy, execution, lau |
| 8,126 | [HKUDS/AgentPilot](https://github.com/HKUDS/AgentPilot) | MIT | Python | app | AgentPilot: Make Your Agents Move Better and Faster |
| 7,674 | [xingkongliang/skills-manager](https://github.com/xingkongliang/skills-manager) | MIT | Rust | app | A lightweight desktop app to manage, sync, and organize AI agent skills across 50+ coding tools — Claude Code, |
| 7,190 | [tech-leads-club/agent-skills](https://github.com/tech-leads-club/agent-skills) | NOASSERTION | TypeScript | registry | The secure, validated skill registry for professional AI coding agents. Extend Antigravity, Claude Code, Curso |
| 5,437 | [iflytek/skillhub](https://github.com/iflytek/skillhub) | Apache-2.0 | Java | team | Self-hosted, open-source agent skill registry for enterprises. Publish & version skill packages, govern with R |
| 4,427 | [microsoft/apm](https://github.com/microsoft/apm) | Apache-2.0 | Python | general | Agent Package Manager |
| 3,782 | [davepoon/buildwithclaude](https://github.com/davepoon/buildwithclaude) | MIT | Python | registry | A single hub to find Claude Skills, Agents, Commands, Hooks, Plugins, and Marketplace collections to extend Cl |
| 3,264 | [runkids/skillshare](https://github.com/runkids/skillshare) | MIT | Go | general | 📚 Sync skills, agents, MCP, plugins to all AI CLI tools with one command and simplify team sharing. |
| 2,935 | [jeremylongshore/tons-of-skills-marketplace](https://github.com/jeremylongshore/tons-of-skills-marketplace) | MIT | Python | registry | Model-agnostic agent-skills platform with a harness-free canonical layer, verified adapters, and the ccpi pack |
| 2,417 | [FrancyJGLisboa/agent-skills-platform](https://github.com/FrancyJGLisboa/agent-skills-platform) | MIT | Python | team | Build tested agent skills and govern their lifecycle through a user-defined marketplace: evidence, discovery,  |
| 2,118 | [Shpigford/chops](https://github.com/Shpigford/chops) | NOASSERTION | Swift | app | Your AI agent skills, finally organized. A macOS app to browse, edit, and manage skills across Claude Code, Cu |
| 1,882 | [qufei1993/skills-hub](https://github.com/qufei1993/skills-hub) | MIT | Rust | app | A cross-platform desktop app to manage Agent Skills in one place and sync them to multiple AI coding tools’ gl |
| 1,657 | [activeloopai/hivemind](https://github.com/activeloopai/hivemind) | Apache-2.0 | TypeScript | sync | Hivemind turns your traces into reusable skills across agents |
| 1,585 | [rohitg00/skillkit](https://github.com/rohitg00/skillkit) | Apache-2.0 | TypeScript | cli | Supercharge AI coding agents with portable skills. Install, translate & share skills across Claude Code, Curso |
| 1,540 | [daymade/claude-code-skills](https://github.com/daymade/claude-code-skills) | MIT | Python | registry | Professional Claude Code skills marketplace featuring production-ready skills for enhanced development workflo |
| 1,447 | [skillsgate/skillsgate](https://github.com/skillsgate/skillsgate) | MIT | TypeScript | app |  |
| 1,378 | [Dimillian/CodexSkillManager](https://github.com/Dimillian/CodexSkillManager) | MIT | Swift | app | macOS app to manage your Codex skills |
| 1,208 | [binance/binance-skills-hub](https://github.com/binance/binance-skills-hub) | None | Python | registry | Binance Skills Hub is an open skills marketplace that gives AI agents native access to crypto |
| 1,027 | [pathintegral-institute/mcpm.sh](https://github.com/pathintegral-institute/mcpm.sh) | MIT | Python | cli | CLI MCP package manager & registry for all platforms and all clients. Search & configure MCP servers. Advanced |
| 976 | [luongnv89/asm](https://github.com/luongnv89/asm) | MIT | TypeScript | cli | The universal skill manager for AI coding agents. |
