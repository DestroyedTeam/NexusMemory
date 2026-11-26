"""Cross-Harness Resource Plane Scanner & Projector.

Deterministically scans & transfers (with mandatory secret stripping and path containment):
- Skills (`SKILL.md` + assets, per-tool copy-vs-symlink deployment e.g. Antigravity copy mode)
- MCP Servers (`stdio`/`http`/`sse` configs — ALL secret env vars/headers stripped to `${VAR}`)
- Plugins (inventory + disabled-by-default target handoff)
- Instructions (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `.kiro/steering`)
- Memory (`MEMORY.md`, Claude project memory files)
- Permission Hints (advisory-only — NEVER auto-granted on target)
- Schedules / Automations (migrated `enabled: false` by default until user confirms)
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

from .claude_desktop_3p import default_claude_desktop_root
from .model import (
    InstructionRecord,
    McpServerRecord,
    MemoryRecord,
    PermissionHint,
    PluginRecord,
    ResourceBundle,
    ScheduleRecord,
    SkillRecord,
)
from .security import (
    atomic_write_bytes,
    atomic_write_json,
    ensure_private_dir,
    ensure_within_root,
    redact_text,
    sanitize_mcp_mapping,
    sanitize_single_segment,
)

# Per-Harness Skills root conventions (distilled from #301 vercel-labs/skills, #310 xingkongliang/skills-manager, #311 nikships/skills-registry)
HARNESS_SKILL_ROOTS: dict[str, dict[str, Any]] = {
    "claude-code": {"user_rel": ".claude/skills", "project_rel": ".claude/skills", "deploy_mode": "copy"},
    "claude-desktop-3p": {"user_rel": ".claude/skills", "project_rel": ".claude/skills", "deploy_mode": "copy"},
    "codex": {"user_rel": ".codex/skills", "project_rel": ".codex/skills", "deploy_mode": "copy"},
    "cursor": {"user_rel": ".cursor/skills", "project_rel": ".cursor/skills", "deploy_mode": "copy"},
    "windsurf": {"user_rel": ".windsurf/skills", "project_rel": ".windsurf/skills", "deploy_mode": "copy"},
    "opencode": {"user_rel": ".config/opencode/skills", "project_rel": ".opencode/skills", "deploy_mode": "copy"},
    "cline": {"user_rel": ".cline/skills", "project_rel": ".cline/skills", "deploy_mode": "copy"},
    "roo": {"user_rel": ".roo/skills", "project_rel": ".roo/skills", "deploy_mode": "copy"},
    "dsh": {"user_rel": ".dsh/skills", "project_rel": ".dsh/skills", "deploy_mode": "copy"},
    "gemini-cli": {"user_rel": ".gemini/skills", "project_rel": ".gemini/skills", "deploy_mode": "copy"},
    # Explicit copy mode for Antigravity (lesson from xingkongliang/skills-manager#691: Antigravity ignores symlinks in some paths)
    "antigravity": {"user_rel": ".agents/skills", "project_rel": ".agents/skills", "deploy_mode": "copy"},
    "pi": {"user_rel": ".pi/agent/skills", "project_rel": ".pi/skills", "deploy_mode": "copy"},
    "goose": {"user_rel": ".config/goose/skills", "project_rel": ".goose/skills", "deploy_mode": "copy"},
    "kiro": {"user_rel": ".kiro/skills", "project_rel": ".kiro/skills", "deploy_mode": "copy"},
    "zed": {"user_rel": ".config/zed/skills", "project_rel": ".zed/skills", "deploy_mode": "copy"},
    "universal": {"user_rel": ".agents/skills", "project_rel": ".agents/skills", "deploy_mode": "copy"},
}


def _parse_frontmatter(md_text: str) -> dict[str, Any]:
    """Parse minimal YAML frontmatter from `SKILL.md` without external PyYAML dependency."""
    if not md_text.startswith("---"):
        return {}
    parts = md_text.split("---", 2)
    if len(parts) < 3:
        return {}
    out: dict[str, Any] = {}
    for line in parts[1].splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                out[k] = v
    return out


def _scan_skills_dir(base_dir: Path, *, harness: str, scope: str) -> list[SkillRecord]:
    out: list[SkillRecord] = []
    if not base_dir.is_dir():
        return out
    for child in sorted(base_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            ensure_within_root(child, base_dir)
            fm = _parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        files_meta: list[dict[str, Any]] = []
        for f in sorted(child.rglob("*")):
            if not f.is_file() or f.is_symlink():
                continue
            try:
                ensure_within_root(f, child)
                data = f.read_bytes()
                files_meta.append(
                    {
                        "rel_path": f.relative_to(child).as_posix(),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "size_bytes": len(data),
                    }
                )
            except (OSError, ValueError):
                continue
        out.append(
            SkillRecord(
                name=sanitize_single_segment(str(fm.get("name") or child.name), fallback=child.name),
                source_harness=harness,
                scope=scope,
                source_path=str(child),
                description=str(fm.get("description") or ""),
                files=tuple(files_meta),
                frontmatter=fm,
            )
        )
    return out


def _extract_mcp_from_json(
    cfg_path: Path,
    *,
    harness: str,
    scope: str,
    secret_counter: Counter[str],
) -> tuple[list[McpServerRecord], list[PermissionHint], list[PluginRecord]]:
    servers: list[McpServerRecord] = []
    perms: list[PermissionHint] = []
    plugins: list[PluginRecord] = []
    if not cfg_path.is_file():
        return servers, perms, plugins
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            return servers, perms, plugins
    except (json.JSONDecodeError, OSError):
        return servers, perms, plugins

    raw_mcp = data.get("mcpServers") or data.get("mcp") or data.get("context_servers") or {}
    if isinstance(raw_mcp, dict):
        for name, spec in sorted(raw_mcp.items()):
            if not isinstance(spec, dict):
                continue
            cmd = spec.get("command")
            args = tuple(str(a) for a in spec.get("args", [])) if isinstance(spec.get("args"), list) else ()
            url = spec.get("url") or spec.get("serverUrl")
            transport = str(spec.get("type") or spec.get("transport") or ("stdio" if cmd else ("http" if url else "unknown")))
            env_tpl, stripped_env, env_counts = sanitize_mcp_mapping(spec.get("env"))
            hdr_tpl, stripped_hdr, hdr_counts = sanitize_mcp_mapping(spec.get("headers"))
            secret_counter.update(env_counts)
            secret_counter.update(hdr_counts)
            servers.append(
                McpServerRecord(
                    name=str(name),
                    source_harness=harness,
                    scope=scope,
                    transport=transport,
                    command=str(cmd) if cmd else None,
                    args=args,
                    url=str(url) if url else None,
                    env_keys=tuple(sorted(env_tpl.keys())),
                    env_template=env_tpl,
                    headers_template=hdr_tpl,
                    stripped_secret_keys=tuple(sorted(set(stripped_env) | set(stripped_hdr))),
                    source_path=str(cfg_path),
                )
            )

    # Advisory permission hints (never auto-granted)
    raw_perms = data.get("permissions")
    if isinstance(raw_perms, dict):
        for mode_key in ("allow", "deny", "ask"):
            rules = raw_perms.get(mode_key)
            if isinstance(rules, list):
                for rule in rules:
                    perms.append(
                        PermissionHint(
                            source_harness=harness,
                            scope=scope,
                            rule=f"{mode_key}:{rule}",
                            mode="advisory_only_never_auto_granted",
                            source_path=str(cfg_path),
                        )
                    )

    # Enabled plugins inventory (migrated disabled by default)
    raw_plugins = data.get("enabledPlugins") or data.get("plugins")
    if isinstance(raw_plugins, dict):
        for pname, pval in sorted(raw_plugins.items()):
            plugins.append(
                PluginRecord(
                    name=str(pname),
                    source_harness=harness,
                    scope=scope,
                    enabled=bool(pval) if isinstance(pval, bool) else None,
                    source_path=str(cfg_path),
                )
            )
    elif isinstance(raw_plugins, list):
        for pitem in raw_plugins:
            pname = pitem.get("name") if isinstance(pitem, dict) else str(pitem)
            plugins.append(
                PluginRecord(name=str(pname), source_harness=harness, scope=scope, source_path=str(cfg_path))
            )

    return servers, perms, plugins


def _extract_mcp_from_codex_toml(
    toml_path: Path,
    *,
    scope: str,
    secret_counter: Counter[str],
) -> list[McpServerRecord]:
    servers: list[McpServerRecord] = []
    if not toml_path.is_file():
        return servers
    try:
        data = tomllib.loads(toml_path.read_text(encoding="utf-8-sig"))
    except (tomllib.TOMLDecodeError, OSError):
        return servers
    raw_mcp = data.get("mcp_servers") or {}
    if isinstance(raw_mcp, dict):
        for name, spec in sorted(raw_mcp.items()):
            if not isinstance(spec, dict):
                continue
            cmd = spec.get("command")
            args = tuple(str(a) for a in spec.get("args", [])) if isinstance(spec.get("args"), list) else ()
            url = spec.get("url")
            transport = "stdio" if cmd else ("http" if url else "unknown")
            env_tpl, stripped_env, env_counts = sanitize_mcp_mapping(spec.get("env"))
            hdr_tpl, stripped_hdr, hdr_counts = sanitize_mcp_mapping(spec.get("http_headers"))
            secret_counter.update(env_counts)
            secret_counter.update(hdr_counts)
            servers.append(
                McpServerRecord(
                    name=str(name),
                    source_harness="codex",
                    scope=scope,
                    transport=transport,
                    command=str(cmd) if cmd else None,
                    args=args,
                    url=str(url) if url else None,
                    env_keys=tuple(sorted(env_tpl.keys())),
                    env_template=env_tpl,
                    headers_template=hdr_tpl,
                    stripped_secret_keys=tuple(sorted(set(stripped_env) | set(stripped_hdr))),
                    source_path=str(toml_path),
                )
            )
    return servers


def scan_resources(
    *,
    home: str | Path | None = None,
    project_dir: str | Path | None = None,
    platform: str | None = None,
    include_harnesses: tuple[str, ...] | None = None,
) -> ResourceBundle:
    """Strictly read-only scan of Skills, MCP servers (secret-stripped), Plugins, Instructions, Memory, Permissions, Schedules."""
    hroot = Path(home).expanduser() if home is not None else Path.home()
    proot = Path(project_dir).expanduser() if project_dir is not None else None
    wanted = set(include_harnesses) if include_harnesses else None

    skills: list[SkillRecord] = []
    mcps: list[McpServerRecord] = []
    plugins: list[PluginRecord] = []
    instructions: list[InstructionRecord] = []
    memories: list[MemoryRecord] = []
    perms: list[PermissionHint] = []
    schedules: list[ScheduleRecord] = []
    secret_counter: Counter[str] = Counter()

    def want(h: str) -> bool:
        return wanted is None or h in wanted

    # 1. Skills across all known Harness user/project roots
    seen_skill_paths: set[str] = set()
    for harness, spec in HARNESS_SKILL_ROOTS.items():
        if not want(harness):
            continue
        user_dir = hroot / spec["user_rel"]
        for sk in _scan_skills_dir(user_dir, harness=harness, scope="user"):
            if sk.source_path not in seen_skill_paths:
                seen_skill_paths.add(sk.source_path)
                skills.append(sk)
        if proot:
            proj_dir = proot / spec["project_rel"]
            for sk in _scan_skills_dir(proj_dir, harness=harness, scope="project"):
                if sk.source_path not in seen_skill_paths:
                    seen_skill_paths.add(sk.source_path)
                    skills.append(sk)

    # 2. MCP configs, permissions, plugins across Harnesses
    c3p_root = default_claude_desktop_root(home=hroot, platform=platform, third_party=True)
    cstd_root = default_claude_desktop_root(home=hroot, platform=platform, third_party=False)
    json_cfg_targets: list[tuple[str, str, Path]] = [
        ("claude-code", "user", hroot / ".claude.json"),
        ("claude-code", "user", hroot / ".claude" / "settings.json"),
        ("claude-desktop-3p", "user", c3p_root / "claude_desktop_config.json"),
        ("claude-desktop-standard", "user", cstd_root / "claude_desktop_config.json"),
        ("cursor", "user", hroot / ".cursor" / "mcp.json"),
        ("windsurf", "user", hroot / ".codeium" / "windsurf" / "mcp_config.json"),
        ("opencode", "user", hroot / ".config" / "opencode" / "opencode.json"),
        ("cline", "user", hroot / ".cline" / "cline_mcp_settings.json"),
        ("gemini-cli", "user", hroot / ".gemini" / "settings.json"),
        ("kiro", "user", hroot / ".kiro" / "settings" / "mcp.json"),
        ("zed", "user", hroot / ".config" / "zed" / "settings.json"),
    ]
    if proot:
        json_cfg_targets.extend(
            [
                ("claude-code", "project", proot / ".mcp.json"),
                ("claude-code", "project", proot / ".claude" / "settings.json"),
                ("cursor", "project", proot / ".cursor" / "mcp.json"),
                ("opencode", "project", proot / "opencode.json"),
                ("kiro", "project", proot / ".kiro" / "settings" / "mcp.json"),
            ]
        )
    for harness, scope, cfg_path in json_cfg_targets:
        if not want(harness):
            continue
        m_list, p_list, pl_list = _extract_mcp_from_json(cfg_path, harness=harness, scope=scope, secret_counter=secret_counter)
        mcps.extend(m_list)
        perms.extend(p_list)
        plugins.extend(pl_list)

    if want("codex"):
        mcps.extend(_extract_mcp_from_codex_toml(hroot / ".codex" / "config.toml", scope="user", secret_counter=secret_counter))
        if proot:
            mcps.extend(_extract_mcp_from_codex_toml(proot / ".codex" / "config.toml", scope="project", secret_counter=secret_counter))

    # 3. Instructions & Memory files (redacted!)
    instr_targets: list[tuple[str, str, Path]] = [
        ("claude-code", "user", hroot / ".claude" / "CLAUDE.md"),
        ("codex", "user", hroot / ".codex" / "AGENTS.md"),
        ("gemini-cli", "user", hroot / ".gemini" / "GEMINI.md"),
    ]
    if proot:
        instr_targets.extend(
            [
                ("claude-code", "project", proot / "CLAUDE.md"),
                ("codex", "project", proot / "AGENTS.md"),
                ("cursor", "project", proot / ".cursorrules"),
                ("windsurf", "project", proot / ".windsurfrules"),
                ("cline", "project", proot / ".clinerules"),
            ]
        )
    for harness, scope, ipath in instr_targets:
        if not want(harness) or not ipath.is_file():
            continue
        raw_bytes = ipath.read_bytes()
        redacted, rcounts = redact_text(raw_bytes.decode("utf-8", errors="replace"))
        secret_counter.update(rcounts)
        instructions.append(
            InstructionRecord(
                name=ipath.name,
                source_harness=harness,
                scope=scope,
                source_path=str(ipath),
                sha256=hashlib.sha256(raw_bytes).hexdigest(),
                size_bytes=len(raw_bytes),
                content_redacted=redacted,
            )
        )

    # Memory files (e.g., ~/.claude/projects/*/memory/*.md, ~/.codex/memory/*.md, project MEMORY.md)
    mem_roots = [
        ("claude-code", "user", hroot / ".claude" / "memory"),
        ("codex", "user", hroot / ".codex" / "memory"),
        ("dsh", "user", hroot / ".dsh" / "memory"),
    ]
    if proot and (proot / "MEMORY.md").is_file():
        raw_b = (proot / "MEMORY.md").read_bytes()
        red, rc = redact_text(raw_b.decode("utf-8", errors="replace"))
        secret_counter.update(rc)
        memories.append(
            MemoryRecord("MEMORY.md", "universal", "project", str(proot / "MEMORY.md"), hashlib.sha256(raw_b).hexdigest(), len(raw_b), red[:500])
        )
    for harness, scope, mdir in mem_roots:
        if not want(harness) or not mdir.is_dir():
            continue
        for mf in sorted(mdir.glob("*.md")):
            raw_b = mf.read_bytes()
            red, rc = redact_text(raw_b.decode("utf-8", errors="replace"))
            secret_counter.update(rc)
            memories.append(
                MemoryRecord(mf.name, harness, scope, str(mf), hashlib.sha256(raw_b).hexdigest(), len(raw_b), red[:500])
            )

    # 4. Schedules (optional JSON files under ~/.codex/schedules.json, ~/.claude/schedules.json, ~/.dsh/automations.json)
    for harness, spath in (
        ("codex", hroot / ".codex" / "schedules.json"),
        ("claude-code", hroot / ".claude" / "schedules.json"),
        ("claude-desktop-3p", c3p_root / "schedules.json"),
        ("dsh", hroot / ".dsh" / "automations.json"),
    ):
        if not want(harness) or not spath.is_file():
            continue
        try:
            sdata = json.loads(spath.read_text(encoding="utf-8-sig"))
            items = sdata if isinstance(sdata, list) else sdata.get("schedules", sdata.get("tasks", []))
            for item in items:
                if not isinstance(item, dict):
                    continue
                red_p, rc = redact_text(str(item.get("prompt") or item.get("instruction") or ""))
                secret_counter.update(rc)
                schedules.append(
                    ScheduleRecord(
                        name=str(item.get("name") or item.get("id") or "schedule"),
                        source_harness=harness,
                        schedule_expr=str(item.get("cron") or item.get("schedule") or ""),
                        prompt_redacted=red_p,
                        enabled=False,  # Always staged disabled until user explicitly enables
                        source_path=str(spath),
                    )
                )
        except (json.JSONDecodeError, OSError):
            continue

    return ResourceBundle(
        skills=tuple(skills),
        mcp_servers=tuple(mcps),
        plugins=tuple(plugins),
        instructions=tuple(instructions),
        memories=tuple(memories),
        permission_hints=tuple(perms),
        schedules=tuple(schedules),
        redacted_secret_counts=dict(secret_counter),
    )


def stage_resources_to_bundle(
    resources: ResourceBundle,
    *,
    bundle_resources_dir: Path,
    target_harness: str,
) -> dict[str, Any]:
    """Write sanitized Skills, MCP templates, instructions, memories, permissions, schedules into bundle."""
    ensure_private_dir(bundle_resources_dir)
    staged_skills: list[dict[str, Any]] = []
    skipped_skills: list[dict[str, Any]] = []

    # 1. Stage Skills by safe copy (never symlink escapes; Antigravity-safe!)
    skills_out = ensure_private_dir(bundle_resources_dir / "skills")
    for sk in resources.skills:
        safe_name = sanitize_single_segment(sk.name, fallback="skill")
        src_dir = Path(sk.source_path)
        dst_dir = ensure_within_root(skills_out / safe_name, skills_out)
        if not src_dir.is_dir():
            skipped_skills.append({"name": sk.name, "reason": "source_dir_missing"})
            continue
        if dst_dir.exists():
            skipped_skills.append({"name": sk.name, "reason": "duplicate_skill_name_kept_first"})
            continue
        ensure_private_dir(dst_dir)
        copied_files = 0
        for fmeta in sk.files:
            rel = fmeta["rel_path"]
            src_file = ensure_within_root(src_dir / rel, src_dir)
            dst_file = ensure_within_root(dst_dir / rel, dst_dir)
            if src_file.is_symlink():
                continue
            raw = src_file.read_bytes()
            atomic_write_bytes(dst_file, raw, mode=0o600)
            copied_files += 1
        staged_skills.append(
            {
                "name": safe_name,
                "source_harness": sk.source_harness,
                "copied_files": copied_files,
                "deploy_mode": HARNESS_SKILL_ROOTS.get(target_harness, {}).get("deploy_mode", "copy"),
                "bundle_path": f"resources/skills/{safe_name}",
            }
        )

    # 2. Stage secret-stripped MCP server config (JSON for Claude/Cursor/OpenCode, plus Codex TOML snippet!)
    mcp_json: dict[str, Any] = {"mcpServers": {}}
    codex_toml_lines: list[str] = ["# Nexus Memory sanitized Codex MCP snippet (fill credentials via env vars)"]
    for srv in resources.mcp_servers:
        entry: dict[str, Any] = {}
        if srv.command:
            entry["command"] = srv.command
            entry["args"] = list(srv.args)
        if srv.url:
            entry["url"] = srv.url
        if srv.env_template:
            entry["env"] = dict(srv.env_template)
        if srv.headers_template:
            entry["headers"] = dict(srv.headers_template)
        mcp_json["mcpServers"][srv.name] = entry

        safe_key = re.sub(r"[^A-Za-z0-9_-]", "_", srv.name)
        codex_toml_lines.append(f"\n[mcp_servers.{safe_key}]")
        if srv.command:
            codex_toml_lines.append(f"command = {json.dumps(srv.command)}")
            codex_toml_lines.append(f"args = {json.dumps(list(srv.args))}")
        if srv.url:
            codex_toml_lines.append(f"url = {json.dumps(srv.url)}")
        if srv.env_template:
            codex_toml_lines.append(f"[mcp_servers.{safe_key}.env]")
            for ek, ev in sorted(srv.env_template.items()):
                codex_toml_lines.append(f"{ek} = {json.dumps(ev)}")

    atomic_write_json(bundle_resources_dir / "mcp.sanitized.json", mcp_json)
    atomic_write_bytes(
        bundle_resources_dir / "codex-mcp.sanitized.toml",
        ("\n".join(codex_toml_lines) + "\n").encode("utf-8"),
        mode=0o600,
    )

    # 3. Stage Instructions, Memories, Advisory Permissions, Disabled Schedules
    if resources.instructions:
        inst_dir = ensure_private_dir(bundle_resources_dir / "instructions")
        for idx, ins in enumerate(resources.instructions, 1):
            fname = sanitize_single_segment(f"{idx:02d}-{ins.source_harness}-{ins.name}")
            atomic_write_bytes(ensure_within_root(inst_dir / fname, inst_dir), ins.content_redacted.encode("utf-8"))

    atomic_write_json(
        bundle_resources_dir / "resource_manifest.json",
        {
            "schema": "nexus-memory.resources.v1",
            "target_harness": target_harness,
            "summary": resources.summary_counts(),
            "staged_skills": staged_skills,
            "skipped_skills": skipped_skills,
            "mcp_servers": [m.to_dict() for m in resources.mcp_servers],
            "plugins_disabled_until_confirmed": [p.to_dict() for p in resources.plugins],
            "memories": [m.to_dict() for m in resources.memories],
            "permission_hints_advisory_only": [p.to_dict() for p in resources.permission_hints],
            "schedules_disabled_until_confirmed": [s.to_dict() for s in resources.schedules],
            "redacted_secret_counts": resources.redacted_secret_counts,
        },
    )
    return {
        "staged_skill_count": len(staged_skills),
        "skipped_skill_count": len(skipped_skills),
        "mcp_server_count": len(resources.mcp_servers),
        "stripped_secret_key_count": sum(len(m.stripped_secret_keys) for m in resources.mcp_servers),
        "instruction_count": len(resources.instructions),
        "memory_count": len(resources.memories),
        "permission_hint_count": len(resources.permission_hints),
        "schedule_count": len(resources.schedules),
        "redacted_secret_counts": resources.redacted_secret_counts,
    }
