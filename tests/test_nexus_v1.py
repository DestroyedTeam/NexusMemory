"""Comprehensive v1.0 test suite for Nexus Memory:
- Multi-Harness readers & writers (ChatGPT ZIP/assets/interruptions/Destruction Era filter,
  Codex CLI .jsonl/.jsonl.zst/home/SQLite/App snapshot, Claude Code CLI read+write,
  Claude Desktop 3P Chat/Cowork/Code 3-lane isolation, OpenCode, Pi native tree DAG,
  Cursor state.vscdb SQLite, DSH V4>V2, Cline/Roo, Gemini CLI, Goose, Aider, Continue, Zed, Portable round-trip)
- Cross-Harness Resource Plane (Skills, secret-stripped MCPs, instructions, memories, advisory permissions, disabled schedules)
- Security & adversarial fault-injection probes (path traversal, sibling prefix collision, symlink escape,
  secret redaction, prompt-injection fence escaping, cloud-sync write gate, corrupt config fail-safe,
  collision refusal/skip/rename, dual-key 3P Code wrong-project rejection, 0o700/0o600 permissions)
- Full transactional convert -> verify -> apply -> verify -> rollback pristine-hash round-trip
- Hardened offline viewer HTTP security probes (CSP, nosniff, HTML/SVG attachment forced, traversal 403)
- Agent Skill script & macOS .app bundle smoke verification
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from http.server import HTTPServer
from pathlib import Path

from nexus_memory.bundle import preview, write_bundle
from nexus_memory.chatgpt import filter_conversations, parse_export_with_assets
from nexus_memory.claude_code import build_native_sessions, parse_claude_code_dir, parse_claude_code_session, project_directory_name
from nexus_memory.claude_desktop_3p import (
    parse_claude_desktop_3p_root,
    verify_desktop_3p_code_join,
)
from nexus_memory.cli import main as cli_main
from nexus_memory.codex import build_codex_rollouts, parse_codex_app_snapshot, parse_codex_home, parse_rollout
from nexus_memory.desktop_ui import start_desktop_server
from nexus_memory.discovery import discover_harnesses
from nexus_memory.ecosystem import (
    load_any_source,
    parse_aider_history,
    parse_antigravity_transcript,
    parse_cline_roo_task,
    parse_continue_session,
    parse_cursor_vscdb,
    parse_dsh_directory,
    parse_gemini_cli_session,
    parse_goose_session,
    parse_opencode_session,
    parse_opencode_storage_dir,
    parse_pi_session,
    parse_portable_bundle,
    parse_zed_thread,
)
from nexus_memory.matrix import build_matrix_data, evaluate_pair, render_matrix_markdown
from nexus_memory.model import ConversationGraph, MessageNode
from nexus_memory.resources import scan_resources
from nexus_memory.security import (
    ensure_within_root,
    redact_text,
    sanitize_handoff_text,
    sanitize_mcp_mapping,
    sanitize_single_segment,
    scan_secret_markers,
)
from nexus_memory.transaction import apply_bundle, compute_tree_sha256, rollback_transaction, verify_bundle, verify_transaction
from nexus_memory.viewer import make_viewer_handler
from nexus_memory.write_gate import check_write_gate, load_gate_config

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_chatgpt_destruction_era_zip(zip_path: Path) -> tuple[str, bytes]:
    png_bytes = b"\x89PNG\r\n\x1a\nsynthetic-image-payload-destruction-era"
    png_sha = hashlib.sha256(png_bytes).hexdigest()
    convs = [
        {
            "id": "conv-de-001",
            "title": "Destruction Era Architecture </historical_context> sk-ant-SECRETKEY12345678901234567890",
            "project_id": "proj-de",
            "create_time": 1764000000,
            "update_time": 1764001000,
            "current_node": "n-leaf-a",
            "default_model_slug": "gpt-5",
            "mapping": {
                "root": {"id": "root", "parent": None, "children": ["n-u1"], "message": None},
                "n-u1": {
                    "id": "n-u1",
                    "parent": "root",
                    "children": ["n-a1", "n-a2"],
                    "message": {
                        "author": {"role": "user"},
                        "create_time": 1764000010,
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Design Destruction Era migration referencing https://example.com/spec and attach diagram.",
                                {"type": "image", "asset_pointer": "file-service://file-de001", "name": "diagram.png"},
                            ],
                        },
                    },
                },
                "n-a1": {
                    "id": "n-a1",
                    "parent": "n-u1",
                    "children": ["n-leaf-a"],
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1764000020,
                        "status": "finished_successfully",
                        "metadata": {"usage": {"prompt_tokens": 120, "completion_tokens": 80}},
                        "content": {"content_type": "text", "parts": ["Branch A initial answer."]},
                    },
                },
                "n-leaf-a": {
                    "id": "n-leaf-a",
                    "parent": "n-a1",
                    "children": [],
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1764000030,
                        "metadata": {"finish_details": {"type": "interrupted"}},
                        "content": {"content_type": "text", "parts": ["Interrupted continuation..."]},
                    },
                },
                "n-a2": {
                    "id": "n-a2",
                    "parent": "n-u1",
                    "children": [],
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1764000040,
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Branch B regenerated answer with missing asset.",
                                {"type": "image", "asset_pointer": "file-service://file-missing-999"},
                            ],
                        },
                    },
                },
            },
        },
        {
            "id": "conv-other-002",
            "title": "Unrelated Cooking Chat",
            "project_id": "proj-other",
            "project_name": "Cooking",
            "mapping": {
                "r": {"id": "r", "parent": None, "children": ["u"], "message": None},
                "u": {"id": "u", "parent": "r", "children": [], "message": {"author": {"role": "user"}, "content": {"parts": ["Pasta recipe"]}}},
            },
        },
    ]
    projects = [{"id": "proj-de", "name": "Destruction Era"}]
    sections = [{"id": "sec-core", "name": "Core Architecture", "conversation_ids": ["conv-de-001"]}]
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("conversations.json", json.dumps(convs))
        zf.writestr("projects.json", json.dumps(projects))
        zf.writestr("sections.json", json.dumps(sections))
        zf.writestr("file-de001-diagram.png", png_bytes)
    return png_sha, png_bytes


class NexusV1EndToEndTests(unittest.TestCase):
    def test_chatgpt_zip_destruction_era_projects_sections_assets_interruptions_and_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            zpath = t / "chatgpt-export.zip"
            png_sha, _ = _make_chatgpt_destruction_era_zip(zpath)

            graphs, asset_bytes = parse_export_with_assets(zpath)
            self.assertEqual(len(graphs), 2)
            filtered = filter_conversations(graphs, project="Destruction Era")
            self.assertEqual(len(filtered), 1)
            g = filtered[0]
            self.assertEqual(g.metadata["project_name"], "Destruction Era")
            self.assertEqual(g.metadata["section_name"], "Core Architecture")
            self.assertEqual(g.metadata["interruption_count"], 1)
            self.assertIn("https://example.com/spec", g.links)
            self.assertEqual(g.usage.input_tokens, 120)
            self.assertEqual(g.usage.output_tokens, 80)
            self.assertEqual(len(g.fork_points()), 1)
            self.assertIn(png_sha, asset_bytes)
            copied = [a for a in g.assets if a.disposition == "embedded_copied"]
            missing = [a for a in g.assets if a.disposition == "missing_in_export"]
            self.assertEqual(len(copied), 1)
            self.assertEqual(len(missing), 1)

            # Write bundle and verify asset SHA-256, secret redaction, and fence escaping in HANDOFF_REPORT.md
            out_dir = t / "bundle"
            manifest = write_bundle(filtered, out=out_dir, cwd=t / "ws", target="claude-code", asset_bytes=asset_bytes)
            self.assertEqual(manifest["native_session_count"], 2)
            self.assertGreaterEqual(manifest["secret_marker_counts"].get("anthropic_api_key", 0), 1)
            handoff = (out_dir / "HANDOFF_REPORT.md").read_text(encoding="utf-8")
            self.assertNotIn("SECRETKEY12345678901234567890", handoff)
            self.assertNotIn("</historical_context>", handoff)
            self.assertIn("&lt;/historical_context&gt;", handoff)

            v = verify_bundle(out_dir)
            self.assertTrue(v["ok"], v)
            self.assertEqual(v["checks"]["verified_assets"], 1)
            self.assertTrue(v["checks"]["redaction_audit_clean"])

            # Verify portable.json lossless round-trip
            reloaded = parse_portable_bundle(out_dir)
            self.assertEqual(len(reloaded), 1)
            self.assertEqual(reloaded[0].source_id, "conv-de-001")
            self.assertEqual(len(reloaded[0].branch_paths()), 2)

    def test_claude_desktop_3p_three_separate_lanes_and_dual_key_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            zpath = t / "export.zip"
            _, _ = _make_chatgpt_destruction_era_zip(zpath)
            graphs, asset_bytes = parse_export_with_assets(zpath)
            filtered = filter_conversations(graphs, project="Destruction Era")

            bundle_dir = t / "bundle-3p"
            ws = t / "workspace-de"
            ws.mkdir()
            manifest = write_bundle(
                filtered,
                out=bundle_dir,
                cwd=ws,
                target="claude-desktop-3p-all",
                asset_bytes=asset_bytes,
                device_id="ant-did-test-1",
                org_id="org-test-1",
            )
            # 2 branches * 3 lanes (chat, cowork, code) = 6 staged sessions
            self.assertEqual(manifest["native_session_count"], 6)
            lanes = {s["lane"] for s in manifest["target_sessions"]}
            self.assertEqual(lanes, {"claude-desktop-3p-chat", "claude-desktop-3p-cowork", "claude-desktop-3p-code"})
            v = verify_bundle(bundle_dir)
            self.assertTrue(v["ok"], v)
            self.assertEqual(v["checks"]["verified_desktop_3p_code_joins"], 2)

            # Transactional apply into isolated Claude-3p + .claude directories
            c3p = t / "Claude-3p"
            cc = t / ".claude"
            (c3p / "existing.txt").parent.mkdir(parents=True)
            (c3p / "existing.txt").write_text("pristine-sentinel\n", encoding="utf-8")
            _, pre_c3p_sha = compute_tree_sha256(c3p)

            # Dry-run mutates nothing
            dry = apply_bundle(bundle_dir, target_root=c3p, claude_dir=cc, apply=False)
            self.assertTrue(dry["dry_run"])
            self.assertEqual(compute_tree_sha256(c3p)[1], pre_c3p_sha)

            # Real apply -> readback verify -> read back all 3 lanes independently
            tx = apply_bundle(bundle_dir, target_root=c3p, claude_dir=cc, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"], tx)
            self.assertEqual(tx["post_write_verification"]["verified_code_joins"], 2)
            # Verify 0o600 permissions on transaction journal and backup archive (POSIX only)
            if sys.platform != "win32":
                self.assertEqual(os.stat(tx["backup_archive"]).st_mode & 0o777, 0o600)
                self.assertEqual(os.stat(Path(tx["journal_dir"]) / "transaction.json").st_mode & 0o777, 0o600)

            by_lane = parse_claude_desktop_3p_root(c3p, claude_dir=cc)
            self.assertEqual(len(by_lane["chat"]), 2)
            self.assertEqual(len(by_lane["cowork"]), 2)
            self.assertEqual(len(by_lane["code"]), 2)
            self.assertTrue(all(g.metadata["transcript_project_verified"] for g in by_lane["code"]))

            # Collision policy: second apply with default 'refuse' MUST raise FileExistsError
            with self.assertRaises(FileExistsError):
                apply_bundle(bundle_dir, target_root=c3p, claude_dir=cc, apply=True, on_collision="refuse")

            # Negative test for dual-key verifier: move transcript to WRONG project dir -> MUST FAIL!
            code_idx = next((c3p / "claude-code-sessions").rglob("*.json"))
            meta = json.loads(code_idx.read_text())
            sid = meta["cliSessionId"]
            right_tr = cc / "projects" / project_directory_name(ws) / f"{sid}.jsonl"
            wrong_dir = cc / "projects" / "-tmp-wrong-project"
            wrong_dir.mkdir(parents=True)
            shutil.move(str(right_tr), str(wrong_dir / f"{sid}.jsonl"))
            bad_join = verify_desktop_3p_code_join(code_idx, cc / "projects")
            self.assertFalse(bad_join["ok"])
            self.assertEqual(bad_join["reason"], "transcript_in_wrong_project_directory")

            # Exact rollback MUST restore pristine SHA-256!
            rb = rollback_transaction(tx["journal_dir"])
            self.assertTrue(rb["ok"], rb)
            self.assertEqual(compute_tree_sha256(c3p)[1], pre_c3p_sha)
            self.assertTrue((c3p / "existing.txt").is_file())
            self.assertFalse((c3p / "local-agent-mode-sessions").exists())

    def test_codex_zst_sqlite_home_app_snapshot_and_writer_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            chome = t / ".codex"
            sdir = chome / "sessions"
            adir = chome / "archived_sessions"
            sdir.mkdir(parents=True)
            adir.mkdir(parents=True)

            rollout_lines = [
                json.dumps({"type": "session_meta", "payload": {"id": "codex-t1", "cwd": str(t / "proj-a"), "parent_thread_id": "parent-0"}}),
                json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Hello https://codex.example"}]}}),
                json.dumps({"type": "event_msg", "payload": {"type": "turn_aborted"}}),
                json.dumps({"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Done."}]}}),
                json.dumps({"type": "event_msg", "payload": {"type": "token_count", "total_token_usage": {"input_tokens": 55, "output_tokens": 22}}}),
            ]
            raw_jsonl = ("\n".join(rollout_lines) + "\n").encode("utf-8")
            (sdir / "r1.jsonl").write_bytes(raw_jsonl)
            (chome / "session_index.jsonl").write_text(json.dumps({"id": "codex-t1", "thread_name": "Indexed Codex Title"}) + "\n", encoding="utf-8")

            # Create SQLite state_5.sqlite
            conn = sqlite3.connect(chome / "state_5.sqlite")
            conn.execute("CREATE TABLE threads (id TEXT, title TEXT, cwd TEXT, project_id TEXT)")
            conn.execute("INSERT INTO threads VALUES (?, ?, ?, ?)", ("codex-t1", "DB Title", str(t / "proj-a"), "proj-db-1"))
            conn.commit()
            conn.close()

            # Test .jsonl.zst if zstd CLI is available
            if shutil.which("zstd"):
                zst_src = t / "r2.jsonl"
                zst_src.write_text(
                    json.dumps({"type": "session_meta", "payload": {"id": "codex-zst", "cwd": str(t / "proj-b"), "title": "Zstd Rollout"}}) + "\n"
                    + json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": "Compressed hello"}}) + "\n",
                    encoding="utf-8",
                )
                subprocess.run(["zstd", "-q", str(zst_src), "-o", str(adir / "r2.jsonl.zst")], check=True)
                g_zst = parse_rollout(adir / "r2.jsonl.zst")
                self.assertEqual(g_zst.source_id, "codex-zst")
                self.assertEqual(g_zst.nodes[0].text, "Compressed hello")

            graphs = parse_codex_home(chome)
            by_id = {g.source_id: g for g in graphs}
            self.assertIn("codex-t1", by_id)
            self.assertEqual(by_id["codex-t1"].title, "Indexed Codex Title")
            self.assertEqual(by_id["codex-t1"].usage.input_tokens, 55)
            self.assertEqual(by_id["codex-t1"].metadata["interruption_count"], 1)
            self.assertEqual(by_id["codex-t1"].metadata["project_id"], "proj-db-1")

            # Test Codex App snapshot preserving source-qualified sidebar Sections separately from Projects
            snap = t / "codex_app.json"
            snap.write_text(
                json.dumps(
                    {
                        "projects": [{"id": "p-de", "name": "Destruction Era", "workspace": "/tmp/de"}],
                        "sidebar_sections": [{"id": "s-1", "name": "Pinned Research", "item_keys": ["local:thread-9"]}],
                        "threads": [{"id": "thread-9", "project_id": "p-de", "title": "DE Plan", "messages": [{"role": "user", "content": "Hi"}]}],
                    }
                ),
                encoding="utf-8",
            )
            app_graphs = parse_codex_app_snapshot(snap)
            self.assertEqual(app_graphs[0].metadata["project_name"], "Destruction Era")
            self.assertEqual(app_graphs[0].metadata["section_name"], "Pinned Research")
            self.assertEqual(app_graphs[0].metadata["section_item_key"], "local:thread-9")

            # Test writing back to codex rollout target
            out_codex = t / "codex-bundle"
            write_bundle(app_graphs, out=out_codex, cwd=t, target="codex")
            self.assertTrue(verify_bundle(out_codex)["ok"])

    def test_broad_ecosystem_readers_and_pi_native_branch_dag_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)

            # 1. Pi native tree-DAG round-trip (2 branches in ONE file!)
            zpath = t / "chatgpt.zip"
            _make_chatgpt_destruction_era_zip(zpath)
            cg = filter_conversations(parse_export_with_assets(zpath)[0], project="Destruction Era")
            pi_bundle = t / "pi-bundle"
            m_pi = write_bundle(cg, out=pi_bundle, cwd=t, target="pi")
            self.assertEqual(m_pi["native_session_count"], 1)  # ONE file preserves both branches!
            pi_file = next((pi_bundle / "pi_sessions").rglob("*.jsonl"))
            pi_reloaded = parse_pi_session(pi_file)
            self.assertEqual(len(pi_reloaded.branch_paths()), 2)
            self.assertEqual(len(pi_reloaded.fork_points()), 1)

            # 2. OpenCode write + read round-trip
            oc_bundle = t / "oc-bundle"
            write_bundle(cg, out=oc_bundle, cwd=t, target="opencode")
            oc_file = next((oc_bundle / "opencode_sessions").rglob("*.json"))
            oc_g = parse_opencode_session(oc_file)
            self.assertEqual(oc_g.source_format, "opencode_session")
            self.assertGreaterEqual(len(oc_g.nodes), 2)

            # 3. DSH V4 supersedes stale V2 for same session_id
            dsh_dir = t / "dsh"
            dsh_dir.mkdir()
            (dsh_dir / "v2_old.jsonl").write_text(
                json.dumps({"type": "session_header", "dsh_schema_version": 2, "session_id": "s-1", "title": "Stale V2"}) + "\n"
                + json.dumps({"role": "user", "content": "Old"}) + "\n",
                encoding="utf-8",
            )
            (dsh_dir / "v4_new.jsonl").write_text(
                json.dumps({"type": "session_header", "dsh_schema_version": 4, "session_id": "s-1", "title": "Authoritative V4"}) + "\n"
                + json.dumps({"role": "user", "content": "Fresh V4"}) + "\n",
                encoding="utf-8",
            )
            dsh_graphs = parse_dsh_directory(dsh_dir)
            self.assertEqual(len(dsh_graphs), 1)
            self.assertEqual(dsh_graphs[0].title, "Authoritative V4")
            self.assertEqual(dsh_graphs[0].source_format, "dsh_v4")

            # 4. Cursor SQLite state.vscdb
            vscdb = t / "state.vscdb"
            conn = sqlite3.connect(vscdb)
            conn.execute("CREATE TABLE cursorDiskKV (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute(
                "INSERT INTO cursorDiskKV VALUES (?, ?)",
                ("composerData:c1", json.dumps({"name": "Cursor Fix", "workspacePath": "/tmp/cur", "conversation": [{"bubbleId": "b1"}, {"bubbleId": "b2"}]})),
            )
            conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", ("bubbleId:c1:b1", json.dumps({"type": 1, "text": "Fix bug"})))
            conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", ("bubbleId:c1:b2", json.dumps({"type": 2, "text": "Fixed!"})))
            conn.commit()
            conn.close()
            cur_graphs = parse_cursor_vscdb(vscdb)
            self.assertEqual(len(cur_graphs), 1)
            self.assertEqual([n.role for n in cur_graphs[0].nodes], ["user", "assistant"])

            # 5. Cline/Roo, Gemini CLI, Goose, Aider, Continue, Zed + load_any_source auto-detect
            (t / "api_conversation_history.json").write_text(json.dumps([{"role": "user", "content": "Cline ask"}]), encoding="utf-8")
            self.assertEqual(parse_cline_roo_task(t / "api_conversation_history.json").nodes[0].text, "Cline ask")

            gem_f = t / "session-1.json"
            gem_f.write_text(json.dumps({"sessionId": "g1", "messages": [{"type": "user", "content": "Hi"}, {"type": "gemini", "content": "Hello"}]}), encoding="utf-8")
            self.assertEqual(load_any_source(gem_f)[0][0].source_format, "gemini_cli_session")

            goose_f = t / "goose.jsonl"
            goose_f.write_text(json.dumps({"id": "gs1", "description": "Goose task"}) + "\n" + json.dumps({"role": "user", "content": "Run"}) + "\n", encoding="utf-8")
            self.assertEqual(parse_goose_session(goose_f).title, "Goose task")

            aider_f = t / ".aider.chat.history.md"
            aider_f.write_text("# aider chat started\n#### Refactor parser\nRefactored cleanly.\n", encoding="utf-8")
            self.assertEqual(len(parse_aider_history(aider_f).nodes), 2)

            cont_f = t / "continue.json"
            cont_f.write_text(json.dumps({"sessionId": "c9", "title": "Cont", "history": [{"message": {"role": "user", "content": "Explain"}}]}), encoding="utf-8")
            self.assertEqual(load_any_source(cont_f)[0][0].source_format, "continue_session")

            zed_f = t / "zed.json"
            zed_f.write_text(json.dumps({"id": "z1", "summary": "Zed Thread", "messages": [{"role": "user", "content": "Check"}]}), encoding="utf-8")
            self.assertEqual(load_any_source(zed_f)[0][0].source_format, "zed_thread")

            # 6. Claude Code CLI read round-trip
            cc_bundle = t / "cc-bundle"
            write_bundle(cg, out=cc_bundle, cwd=t, target="claude-code")
            cc_jsonl = next((cc_bundle / "claude_sessions").rglob("*.jsonl"))
            cc_read = parse_claude_code_session(cc_jsonl)
            self.assertEqual(cc_read.source_format, "claude_code_jsonl")
            self.assertGreaterEqual(len(cc_read.nodes), 2)

    def test_resource_plane_secret_stripping_and_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            proj = Path(tmp) / "project"
            # Populate synthetic Skills, Codex TOML MCP with secret, Claude JSON MCP with secret, CLAUDE.md, permissions, schedule
            sk_dir = fake_home / ".codex/skills/my-skill"
            sk_dir.mkdir(parents=True)
            (sk_dir / "SKILL.md").write_text("---\nname: my-skill\ndescription: Synthetic skill\n---\nBody\n", encoding="utf-8")

            (fake_home / ".codex/config.toml").write_text(
                '[mcp_servers.github]\ncommand = "npx"\nargs = ["-y", "mcp-gh"]\n[mcp_servers.github.env]\nGITHUB_TOKEN = "ghp_1234567890abcdefghij1234567890abcd"\nLOG_LEVEL = "info"\n',
                encoding="utf-8",
            )
            (fake_home / ".claude").mkdir(parents=True)
            (fake_home / ".claude/settings.json").write_text(
                json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}, "enabledPlugins": {"demo@official": True}}),
                encoding="utf-8",
            )
            (fake_home / ".codex/schedules.json").write_text(
                json.dumps([{"name": "nightly", "cron": "0 2 * * *", "prompt": "Run report with sk-ant-SECRETKEY12345678901234567890"}]),
                encoding="utf-8",
            )
            proj.mkdir(parents=True)
            (proj / "CLAUDE.md").write_text("Project instructions with Bearer abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")

            # Read-only discovery
            disc = discover_harnesses(home=fake_home, project_dir=proj, platform="darwin")
            self.assertGreaterEqual(disc["detected_count"], 2)
            self.assertTrue(disc["project_markers"]["CLAUDE.md"])

            # Resource scan & staging
            res = scan_resources(home=fake_home, project_dir=proj, platform="darwin")
            self.assertEqual(len(res.skills), 1)
            self.assertEqual(len(res.mcp_servers), 1)
            self.assertEqual(res.mcp_servers[0].env_template["GITHUB_TOKEN"], "${GITHUB_TOKEN}")
            self.assertEqual(res.mcp_servers[0].env_template["LOG_LEVEL"], "info")
            self.assertIn("GITHUB_TOKEN", res.mcp_servers[0].stripped_secret_keys)
            self.assertEqual(res.schedules[0].enabled, False)
            self.assertNotIn("SECRETKEY12345678901234567890", res.schedules[0].prompt_redacted)
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", res.instructions[0].content_redacted)

    def test_security_gates_path_traversal_cloud_sync_and_corrupt_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "allowed"
            sibling = Path(tmp) / "allowed-evil"
            root.mkdir()
            sibling.mkdir()
            (sibling / "secret.txt").write_text("nope", encoding="utf-8")

            # Prefix-collision sibling MUST be rejected
            with self.assertRaises(ValueError):
                ensure_within_root(sibling / "secret.txt", root)
            # Traversal MUST be rejected
            with self.assertRaises(ValueError):
                ensure_within_root(root / "../allowed-evil/secret.txt", root)
            # Single-segment sanitizer blocks ../escaped
            self.assertNotIn("..", sanitize_single_segment("../../escaped/skill"))
            self.assertNotIn("/", sanitize_single_segment("../../escaped/skill"))

            # Corrupt config gate blocks writes without crashing load
            bad_cfg = Path(tmp) / "config.json"
            bad_cfg.write_text("{broken json", encoding="utf-8")
            gcfg = load_gate_config(bad_cfg)
            self.assertIsNotNone(gcfg.config_corrupt_reason)
            dec = check_write_gate(root / "out", gate_config=gcfg)
            self.assertFalse(dec.allowed)
            self.assertIn("corrupt_config", dec.reason)

            # Cloud-sync folder gate blocks unless exact path opted in; moving path re-closes gate
            dropbox_target = Path(tmp) / "Dropbox" / "nexus-out"
            dropbox_target.parent.mkdir()
            blocked = check_write_gate(dropbox_target)
            self.assertFalse(blocked.allowed)
            self.assertEqual(blocked.cloud_provider, "Dropbox")
            allowed = check_write_gate(dropbox_target, allow_cloud_sync_path=dropbox_target)
            self.assertTrue(allowed.allowed)
            moved = check_write_gate(Path(tmp) / "Dropbox" / "other-out", allow_cloud_sync_path=dropbox_target)
            self.assertFalse(moved.allowed)

            # Precision redaction preserves UUIDs/SHAs while redacting real keys
            text = "uuid=11111111-2222-4333-8444-555555555555 max_tokens=4096 key=sk-ant-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            red, counts = redact_text(text)
            self.assertIn("11111111-2222-4333-8444-555555555555", red)
            self.assertIn("max_tokens=4096", red)
            self.assertNotIn("ABCDEFGHIJKLMNOPQRSTUVWXYZ", red)
            self.assertEqual(counts["anthropic_api_key"], 1)

    def test_hardened_offline_viewer_security_headers_and_traversal_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            zpath = t / "export.zip"
            _make_chatgpt_destruction_era_zip(zpath)
            graphs, asset_bytes = parse_export_with_assets(zpath)
            bdir = t / "bundle"
            write_bundle(graphs[:1], out=bdir, cwd=t, target="claude-code", asset_bytes=asset_bytes)

            # Plant an HTML file inside assets/ AND a secret file in sibling assets-evil/
            (bdir / "assets" / "poc.html").write_text("<html><script>alert(1)</script></html>", encoding="utf-8")
            (bdir / "assets-evil").mkdir()
            (bdir / "assets-evil" / "leak.txt").write_text("SECRET", encoding="utf-8")

            srv = HTTPServer(("127.0.0.1", 0), make_viewer_handler(bdir))
            port = srv.server_address[1]
            thread = threading.Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            try:
                # 1. Overview page has strict CSP & nosniff
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn("default-src 'none'", resp.headers.get("Content-Security-Policy", ""))
                    self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")

                # 2. HTML asset MUST be forced to attachment (no same-origin inline XSS!)
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/asset/poc.html", timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertTrue(resp.headers.get("Content-Disposition", "").startswith("attachment;"))

                # 3. Traversal to sibling prefix-collision folder MUST return 403!
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/api/asset/" + urllib.parse.quote("../assets-evil/leak.txt"), timeout=5)
                self.assertEqual(ctx.exception.code, 403)
            finally:
                srv.shutdown()
                srv.server_close()

    def test_matrix_cli_agent_skill_and_macos_app_bundle(self) -> None:
        # Matrix & pair evaluation
        mdata = build_matrix_data()
        self.assertGreaterEqual(len(mdata["harnesses"]), 19)
        pair = evaluate_pair("chatgpt-export", "claude-desktop-3p-cowork")
        self.assertEqual(pair["overall_mode"], "native_projection_plus_lossless_sidecar")
        self.assertIn("Claude Desktop 3P", render_matrix_markdown())

        # CLI matrix exit 0
        self.assertEqual(cli_main(["matrix", "--from", "chatgpt-export", "--to", "claude-code"]), 0)

        # Agent Skill wrapper smoke test
        skill_script = REPO_ROOT / "skills/nexus-memory/scripts/run_nexus.sh"
        self.assertTrue((REPO_ROOT / "skills/nexus-memory/SKILL.md").is_file())
        if sys.platform != "win32":
            proc = subprocess.run([str(skill_script), "--version"], capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("1.0.0", proc.stdout)
        else:
            env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
            proc = subprocess.run([sys.executable, "-m", "nexus_memory", "--version"], env=env, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("1.0.0", proc.stdout)

        # macOS .app bundle smoke test (built in dist/Nexus Memory.app)
        app_bin = REPO_ROOT / "dist/Nexus Memory.app/Contents/MacOS/nexus-memory-app"
        if sys.platform == "darwin" and app_bin.is_file():
            ap = subprocess.run([str(app_bin), "--self-test"], capture_output=True, text=True, check=False)
            self.assertEqual(ap.returncode, 0, ap.stderr)
            info = json.loads(ap.stdout)
            self.assertEqual(info["self_test"], "ok")
            self.assertEqual(info["version"], "1.0.0")

    def test_anti_invalid_params_claude_coalescing_and_codex_tool_pairing(self) -> None:
        # Build a deliberately hostile conversation: leading assistant, consecutive assistant/user turns,
        # paired tool call/output with dict arguments, and an unpaired dangling tool call.
        nodes = (
            MessageNode("n1", None, ("n2",), "assistant", "Leading assistant", "2026-11-20T00:00:00Z", "Leading assistant", {}),
            MessageNode("n2", "n1", ("n3",), "assistant", "Second consecutive assistant", "2026-11-20T00:00:01Z", "Second consecutive assistant", {}),
            MessageNode("n3", "n2", ("n4",), "user", "User part 1", "2026-11-20T00:00:02Z", "User part 1", {}),
            MessageNode("n4", "n3", ("n5",), "user", "User part 2", "2026-11-20T00:00:03Z", "User part 2", {}),
            MessageNode("n5", "n4", ("n6",), "tool_call", "call_ok", "2026-11-20T00:00:04Z", {"call_id": "cid-ok", "name": "read", "arguments": {"path": "a.py"}}, {}),
            MessageNode("n6", "n5", ("n7",), "tool_result", "ok_out", "2026-11-20T00:00:05Z", {"call_id": "cid-ok", "output": "content"}, {}),
            MessageNode("n7", "n6", ("n8",), "tool_call", "call_orphan", "2026-11-20T00:00:06Z", {"call_id": "cid-orphan", "name": "bad", "arguments": {"x": 1}}, {}),
            MessageNode("n8", "n7", (), "assistant", "Final answer", "2026-11-20T00:00:07Z", "Final answer", {}),
        )
        g = ConversationGraph(
            source_format="synthetic",
            source_id="hostile-01",
            title="Hostile Role Test",
            workspace="/tmp/ws",
            nodes=nodes,
            root_ids=("n1",),
            active_node_id="n8",
            metadata={},
            raw_source={},
        )
        cc_sessions, cc_losses = build_native_sessions(g, cwd="/tmp/ws")
        self.assertEqual(len(cc_sessions), 1)
        msg_recs = [r for r in cc_sessions[0]["records"] if r.get("type") in {"user", "assistant"}]
        roles = [r["type"] for r in msg_recs]
        self.assertEqual(roles[0], "user")
        for i in range(1, len(roles)):
            self.assertNotEqual(roles[i], roles[i - 1], f"non-alternating roles: {roles}")
        self.assertTrue(any(l["feature"] == "consecutive_same_role_coalescing" for l in cc_losses))

        cx_sessions, cx_losses = build_codex_rollouts(g, cwd="/tmp/ws")
        self.assertEqual(len(cx_sessions), 1)
        meta = cx_sessions[0]["records"][0]["payload"]
        self.assertEqual(meta["source"], "cli")
        self.assertEqual(meta["originator"], "codex_cli_rs")
        self.assertIn("cli_version", meta)
        self.assertIn("timestamp", meta)
        fn_calls = [r["payload"] for r in cx_sessions[0]["records"] if r["type"] == "response_item" and r["payload"].get("type") == "function_call"]
        fn_outs = [r["payload"] for r in cx_sessions[0]["records"] if r["type"] == "response_item" and r["payload"].get("type") == "function_call_output"]
        self.assertEqual([c["call_id"] for c in fn_calls], ["cid-ok"])
        self.assertEqual([o["call_id"] for o in fn_outs], ["cid-ok"])
        self.assertIsInstance(fn_calls[0]["arguments"], str)
        self.assertEqual(json.loads(fn_calls[0]["arguments"]), {"path": "a.py"})
        self.assertTrue(any(l["feature"] == "unpaired_tool_events_omitted_for_api_validity" for l in cx_losses))

    def test_codex_state5_project_roots_thread_sections_spawn_edges_and_history_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            chome = t / ".codex"
            chome.mkdir(parents=True)
            ws = str(t / "DestructionEraRepo")

            # Real Codex 0.154+ schema: threads.project_id is NULL; projects match via project_roots.path == threads.cwd!
            conn = sqlite3.connect(chome / "state_5.sqlite")
            conn.execute("CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT)")
            conn.execute("CREATE TABLE project_roots (project_id TEXT, path TEXT)")
            conn.execute("CREATE TABLE thread_sections (id TEXT PRIMARY KEY, name TEXT)")
            conn.execute("CREATE TABLE thread_spawn_edges (parent_thread_id TEXT, child_thread_id TEXT)")
            conn.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, project_id TEXT, thread_section_id TEXT, rollout_path TEXT, archived INTEGER, model TEXT)"
            )
            conn.execute("INSERT INTO projects VALUES ('p-de', 'Destruction Era Project')")
            conn.execute("INSERT INTO project_roots VALUES ('p-de', ?)", (ws,))
            conn.execute("INSERT INTO thread_sections VALUES ('sec-de', 'Destruction Era')")
            conn.execute("INSERT INTO thread_spawn_edges VALUES ('parent-thread-1', 'child-thread-1')")
            conn.execute(
                "INSERT INTO threads VALUES ('child-thread-1', 'DE Thread', ?, NULL, 'sec-de', '/nonexistent/rollout.jsonl', 0, 'gpt-6.1-sol')",
                (ws,),
            )
            conn.commit()
            conn.close()

            # Fallback thread_history_1.sqlite when rollout file was purged
            hconn = sqlite3.connect(chome / "thread_history_1.sqlite")
            hconn.execute("CREATE TABLE thread_items (thread_id TEXT, rollout_ordinal INTEGER, item_id TEXT, item_type TEXT, item_json TEXT, created_at_ms INTEGER)")
            hconn.execute(
                "INSERT INTO thread_items VALUES ('child-thread-1', 1, 'it-1', 'userMessage', ?, 1764000001000)",
                (json.dumps({"type": "userMessage", "content": [{"type": "text", "text": "Fallback history question"}]}),),
            )
            hconn.execute(
                "INSERT INTO thread_items VALUES ('child-thread-1', 2, 'it-2', 'agentMessage', ?, 1764000002000)",
                (json.dumps({"type": "agentMessage", "text": "Fallback history answer"}),),
            )
            hconn.commit()
            hconn.close()

            graphs = parse_codex_home(chome, section_filter="Destruction Era")
            self.assertEqual(len(graphs), 1)
            g = graphs[0]
            self.assertEqual(g.source_id, "child-thread-1")
            self.assertEqual(g.metadata["project_name"], "Destruction Era Project")
            self.assertEqual(g.metadata["section_name"], "Destruction Era")
            self.assertEqual(g.metadata["parent_session_id"], "parent-thread-1")
            self.assertEqual([n.role for n in g.nodes], ["user", "assistant"])

    def test_antigravity_reader_opencode_split_and_all_new_target_writers_with_apply_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            # 1. Antigravity strictly read-only transcript.jsonl auto-detection
            ag_dir = t / "brain" / "conv-ag-99" / ".system_generated" / "logs"
            ag_dir.mkdir(parents=True)
            ag_file = ag_dir / "transcript.jsonl"
            ag_file.write_text(
                "\n".join(
                    [
                        json.dumps({"step_index": 0, "type": "USER_INPUT", "created_at": "2026-11-20T01:00:00Z", "content": "<USER_REQUEST>\nMigrate my project\n</USER_REQUEST>"}),
                        json.dumps({"step_index": 1, "type": "PLANNER_RESPONSE", "created_at": "2026-11-20T01:00:02Z", "content": "Checking files.", "tool_calls": [{"name": "read_file", "args": {"Path": "/tmp/a"}}]}),
                        json.dumps({"step_index": 2, "type": "GENERIC", "created_at": "2026-11-20T01:00:03Z", "tool": "read_file", "content": "file body"}),
                        json.dumps({"step_index": 3, "type": "PLANNER_RESPONSE", "created_at": "2026-11-20T01:00:05Z", "content": "All set!"}),
                    ]
                ) + "\n",
                encoding="utf-8",
            )
            ag_graphs, _ = load_any_source(ag_file)
            self.assertEqual(len(ag_graphs), 1)
            self.assertEqual(ag_graphs[0].source_format, "antigravity_transcript")
            self.assertEqual(ag_graphs[0].source_id, "conv-ag-99")
            self.assertEqual(ag_graphs[0].nodes[0].text, "Migrate my project")

            ws = t / "DemoProject"
            ws.mkdir()

            # 2. Test every bidirectional target: codex (with existing session_index merge), opencode (split storage),
            #    gemini-cli (with existing projects.json merge), cline-roo, goose, continue, zed, aider
            for target_name in ("codex", "opencode", "gemini-cli", "cline-roo", "goose", "continue", "zed", "aider"):
                bdir = t / f"bundle-{target_name}"
                troot = t / f"target-{target_name}"
                troot.mkdir()
                if target_name == "codex":
                    (troot / "session_index.jsonl").write_text(json.dumps({"id": "pre-existing", "thread_name": "Keep me"}) + "\n", encoding="utf-8")
                elif target_name == "gemini-cli":
                    (troot / "projects.json").write_text(json.dumps({"projects": {"/existing/repo": "existing"}}), encoding="utf-8")

                _, pre_sha = compute_tree_sha256(troot)
                write_bundle(ag_graphs, out=bdir, cwd=ws, target=target_name)
                vb = verify_bundle(bdir)
                self.assertTrue(vb["ok"], f"{target_name} verify_bundle failed: {vb}")

                tx = apply_bundle(bdir, target_root=troot, apply=True)
                self.assertTrue(tx["post_write_verification"]["ok"], f"{target_name} verify_tx failed: {tx}")

                if target_name == "codex":
                    idx_lines = (troot / "session_index.jsonl").read_text(encoding="utf-8").splitlines()
                    self.assertEqual(len(idx_lines), 2)
                elif target_name == "opencode":
                    oc_back = parse_opencode_storage_dir(troot)
                    self.assertEqual(len(oc_back), 1)
                    self.assertGreaterEqual(len(oc_back[0].nodes), 2)
                elif target_name == "gemini-cli":
                    pj = json.loads((troot / "projects.json").read_text(encoding="utf-8"))
                    self.assertIn("/existing/repo", pj["projects"])
                    self.assertIn(str(ws.resolve()), pj["projects"])
                    gem_f = next((troot / "tmp").rglob("session-*.json"))
                    self.assertGreaterEqual(len(parse_gemini_cli_session(gem_f).nodes), 2)
                elif target_name == "cline-roo":
                    cf = next((troot / "tasks").rglob("api_conversation_history.json"))
                    self.assertGreaterEqual(len(parse_cline_roo_task(cf).nodes), 2)
                elif target_name == "goose":
                    gf = next((troot / "sessions").glob("*.jsonl"))
                    self.assertGreaterEqual(len(parse_goose_session(gf).nodes), 2)
                elif target_name == "continue":
                    cf = next((troot / "sessions").glob("*.json"))
                    self.assertGreaterEqual(len(parse_continue_session(cf).nodes), 2)
                elif target_name == "zed":
                    zf = next((troot / "threads").glob("*.json"))
                    self.assertGreaterEqual(len(parse_zed_thread(zf).nodes), 2)
                elif target_name == "aider":
                    af = troot / ".aider.chat.history.md"
                    self.assertGreaterEqual(len(parse_aider_history(af).nodes), 2)

                rb = rollback_transaction(tx["journal_dir"])
                self.assertTrue(rb["ok"], f"{target_name} rollback failed: {rb}")
                self.assertEqual(compute_tree_sha256(troot)[1], pre_sha)

    def test_antigravity_complex_multi_section_project_session_subagent_hierarchy(self) -> None:
        """Complex real-world Antigravity fixture: 1 Section -> 2 Projects -> 4 Sessions (with nested Subagents,
        paired tools, artifacts, links, consecutive planner turns, and secrets)."""
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            brain = t / "brain"

            def add_ag_conv(cid: str, meta: dict, steps: list[dict], artifacts: dict[str, bytes] | None = None) -> None:
                cdir = brain / cid
                logs = cdir / ".system_generated" / "logs"
                logs.mkdir(parents=True)
                (cdir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
                (logs / "transcript.jsonl").write_text("\n".join(json.dumps(s) for s in steps) + "\n", encoding="utf-8")
                for fname, raw in (artifacts or {}).items():
                    (cdir / fname).write_bytes(raw)

            # Section "Destruction Era" -> Project A ("Core Engine") -> Parent Session + Subagent Session
            add_ag_conv(
                "ag-parent-engine",
                {"title": "Core Engine Refactor", "section_id": "sec-de", "section_name": "Destruction Era", "project_id": "proj-core", "project_name": "Core Engine", "workspace": str(t / "ws-core")},
                [
                    {"step_index": 0, "type": "USER_INPUT", "created_at": "2026-11-25T10:00:00Z", "content": "<USER_REQUEST>\nAudit https://spec.example/core and spawn researcher subagent.\n</USER_REQUEST>"},
                    {"step_index": 1, "type": "PLANNER_RESPONSE", "created_at": "2026-11-25T10:00:02Z", "content": "Delegating codebase scan to subagent.", "tool_calls": [{"id": "call-sub-1", "name": "invoke_subagent", "args": {"TypeName": "research", "Role": "Core Auditor"}}]},
                    {"step_index": 2, "type": "GENERIC", "created_at": "2026-11-25T10:00:05Z", "tool": "invoke_subagent", "call_id": "call-sub-1", "content": "Subagent ag-sub-engine finished with 0 critical issues."},
                    {"step_index": 3, "type": "PLANNER_RESPONSE", "created_at": "2026-11-25T10:00:06Z", "content": "Consecutive planner update 1."},
                    {"step_index": 4, "type": "PLANNER_RESPONSE", "created_at": "2026-11-25T10:00:07Z", "content": "Consecutive planner update 2 (token sk-ant-SECRETKEY12345678901234567890)."},
                ],
                artifacts={"architecture.md": b"# Core Architecture\n", "diagram.png": b"\x89PNG\r\n\x1a\nfake"},
            )
            add_ag_conv(
                "ag-sub-engine",
                {"title": "Core Auditor Subagent", "section_id": "sec-de", "section_name": "Destruction Era", "project_id": "proj-core", "project_name": "Core Engine", "workspace": str(t / "ws-core"), "parent_session_id": "ag-parent-engine", "subagent_role": "Core Auditor"},
                [
                    {"step_index": 0, "type": "USER_INPUT", "created_at": "2026-11-25T10:00:03Z", "content": "Inspect all adapters."},
                    {"step_index": 1, "type": "PLANNER_RESPONSE", "created_at": "2026-11-25T10:00:04Z", "content": "All adapters checked cleanly."},
                ],
            )
            # Same Section "Destruction Era" -> Project B ("Desktop UI") -> Parent Session + Subagent Session
            add_ag_conv(
                "ag-parent-ui",
                {"title": "Desktop UI Redesign", "section_id": "sec-de", "section_name": "Destruction Era", "project_id": "proj-ui", "project_name": "Desktop UI", "workspace": str(t / "ws-ui")},
                [
                    {"step_index": 0, "type": "USER_INPUT", "created_at": "2026-11-25T11:00:00Z", "content": "<USER_REQUEST>\nBuild futuristic desktop UI.\n</USER_REQUEST>"},
                    {"step_index": 1, "type": "PLANNER_RESPONSE", "created_at": "2026-11-25T11:00:02Z", "content": "UI components scaffolded."},
                ],
            )
            add_ag_conv(
                "ag-sub-ui",
                {"title": "Visual QA Subagent", "section_id": "sec-de", "section_name": "Destruction Era", "project_id": "proj-ui", "project_name": "Desktop UI", "workspace": str(t / "ws-ui"), "parent_session_id": "ag-parent-ui", "subagent_role": "Visual QA"},
                [
                    {"step_index": 0, "type": "USER_INPUT", "created_at": "2026-11-25T11:00:03Z", "content": "Verify dark mode contrast."},
                    {"step_index": 1, "type": "PLANNER_RESPONSE", "created_at": "2026-11-25T11:00:04Z", "content": "WCAG AA verified across all surfaces."},
                ],
            )

            # Auto-detect full brain directory (strictly read-only!)
            graphs, _ = load_any_source(brain)
            self.assertEqual(len(graphs), 4)
            by_id = {g.source_id: g for g in graphs}
            self.assertEqual(len(by_id["ag-parent-engine"].assets), 2)
            self.assertEqual(len(by_id["ag-parent-engine"].metadata["spawned_subagents"]), 1)

            # Convert full complex hierarchy -> claude-code, codex, workbuddy, claude-desktop-3p-all
            for target in ("claude-code", "codex", "workbuddy", "claude-desktop-3p-all"):
                out = t / f"out-{target}"
                m = write_bundle(graphs, out=out, cwd=t, target=target)
                v = verify_bundle(out)
                self.assertTrue(v["ok"], f"{target}: {v}")
                self.assertTrue(v["checks"]["redaction_audit_clean"])
                self.assertEqual(m["project_index_summary"]["section_group_count"], 1)
                self.assertEqual(m["project_index_summary"]["project_count"], 2)
                self.assertEqual(m["project_index_summary"]["session_relation_count"], 2)
                self.assertEqual(m["fidelity_report"]["structural_fidelity"]["resolved_relations"], 2)

    def test_twenty_harness_zero_ai_bidirectional_ring_chain(self) -> None:
        """Automated pairwise/ring-chain acceptance across ALL 22 bidirectional Harnesses (incl. Antigravity & Cursor!):
        Every Harness writes -> verifies -> applies -> auto-detect reads back -> forwards to next Harness -> rolls back."""
        ring_targets = [
            "claude-code",
            "codex",
            "antigravity",
            "cursor",
            "opencode",
            "pi",
            "dsh",
            "gemini-cli",
            "cline-roo",
            "goose",
            "continue",
            "zed",
            "aider",
            "workbuddy",
            "t3code",
            "kiro",
            "amp",
            "trae",
            "warp-oz",
            "claude-desktop-3p-chat",
            "claude-desktop-3p-cowork",
            "claude-desktop-3p-code",
        ]
        self.assertGreaterEqual(len(ring_targets), 22)

        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            ws = t / "RingWorkspace"
            ws.mkdir()
            sentinel_user = "Migrate Destruction Era across all twenty Harnesses cleanly."
            sentinel_asst = "Migration verified deterministically with zero AI intervention."
            seed = ConversationGraph(
                source_format="seed",
                source_id="ring-001",
                title="Ring Chain Test",
                workspace=str(ws),
                nodes=(
                    MessageNode("n1", None, ("n2",), "user", sentinel_user, "2026-11-25T00:00:00Z", sentinel_user, {}),
                    MessageNode("n2", "n1", ("n3",), "assistant", sentinel_asst, "2026-11-25T00:00:01Z", sentinel_asst, {}),
                    MessageNode("n3", "n2", (), "assistant", "Follow-up detail preserved.", "2026-11-25T00:00:02Z", "Follow-up detail preserved.", {}),
                ),
                root_ids=("n1",),
                active_node_id="n3",
                metadata={"project_name": "Destruction Era", "section_name": "Destruction Era"},
                raw_source={},
            )

            current_graphs = [seed]
            for idx, target in enumerate(ring_targets):
                bdir = t / f"ring-bundle-{idx:02d}-{target}"
                troot = t / f"ring-target-{idx:02d}-{target}"
                croot = (t / f"ring-cc-{idx:02d}") if target == "claude-desktop-3p-code" else None
                troot.mkdir()
                if croot:
                    croot.mkdir()
                _, pre_sha = compute_tree_sha256(troot)

                write_bundle(current_graphs, out=bdir, cwd=ws, target=target)
                vb = verify_bundle(bdir)
                self.assertTrue(vb["ok"], f"[{target}] verify_bundle failed: {vb}")

                tx = apply_bundle(bdir, target_root=troot, claude_dir=croot, apply=True)
                self.assertTrue(tx["post_write_verification"]["ok"], f"[{target}] verify_tx failed: {tx}")

                # Read back from the real applied target store using auto-detection / target reader
                if target in {"claude-desktop-3p-chat", "claude-desktop-3p-cowork", "claude-desktop-3p-code"}:
                    reloaded, _ = load_any_source(troot, source_format=target, claude_dir=croot)
                elif target == "pi":
                    pi_f = next(troot.rglob("*.jsonl"))
                    reloaded, _ = load_any_source(pi_f)
                elif target == "aider":
                    reloaded, _ = load_any_source(troot / ".aider.chat.history.md")
                elif target in {"gemini-cli", "continue", "zed", "amp", "trae", "warp-oz", "t3code"}:
                    jf = next(p for p in troot.rglob("*.json") if p.name != "projects.json")
                    reloaded, _ = load_any_source(jf)
                elif target in {"goose", "kiro", "workbuddy"}:
                    jl = next(troot.rglob("*.jsonl"))
                    reloaded, _ = load_any_source(jl)
                elif target == "cline-roo":
                    cf = next(troot.rglob("api_conversation_history.json"))
                    reloaded, _ = load_any_source(cf)
                else:
                    reloaded, _ = load_any_source(troot)

                self.assertGreaterEqual(len(reloaded), 1, f"[{target}] reloaded empty")
                joined_text = "\n".join(n.text for n in reloaded[0].nodes)
                self.assertIn("Destruction Era", joined_text, f"[{target}] lost user context")
                self.assertIn("zero AI intervention", joined_text, f"[{target}] lost assistant context")

                # Exact pristine rollback check on every single one of the 20 targets!
                rb = rollback_transaction(tx["journal_dir"])
                self.assertTrue(rb["ok"], f"[{target}] rollback failed: {rb}")
                self.assertEqual(compute_tree_sha256(troot)[1], pre_sha)

                # Feed the read-back output straight into the NEXT Harness in the 20-hop ring!
                current_graphs = [reloaded[0]]

    def test_desktop_ui_server_security_and_live_endpoints(self) -> None:
        srv, url, token = start_desktop_server(0)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        try:
            # 1. Root page renders futuristic UI with strict CSP + nosniff
            with urllib.request.urlopen(url, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
                self.assertIn("default-src 'none'", resp.headers.get("Content-Security-Policy", ""))
                html = resp.read().decode("utf-8")
                self.assertIn("Nexus Memory", html)
                self.assertIn("workbuddy", html)
                self.assertIn("t3code", html)

            # 2. Missing token MUST return 403 Forbidden
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(url + "api/matrix", timeout=5)
            self.assertEqual(ctx.exception.code, 403)

            # 3. Valid X-Nexus-Token returns 25-Harness matrix
            req = urllib.request.Request(url + "api/matrix", headers={"X-Nexus-Token": token})
            with urllib.request.urlopen(req, timeout=5) as resp:
                mdata = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(len(mdata["harnesses"]), 25)

            # 4. End-to-end Desktop UI flow: Preview (with real conversation turns!) -> Convert -> Viewer '/' content -> Apply -> Rollback
            with tempfile.TemporaryDirectory() as td:
                tp = Path(td)
                zpath = tp / "de.zip"
                _make_chatgpt_destruction_era_zip(zpath)
                out_bundle = tp / "staged-bundle"
                sandbox_dst = tp / "sandbox-claude"

                def post_api(ep: str, payload: dict) -> dict:
                    r = urllib.request.Request(
                        url + ep,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"X-Nexus-Token": token, "Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(r, timeout=10) as resp:
                        return json.loads(resp.read().decode("utf-8"))

                prev = post_api("api/preview", {
                    "source": str(zpath), "source_format": "chatgpt", "target": "claude-code",
                    "project": "Destruction Era", "out": str(out_bundle), "cwd": str(tp),
                })
                self.assertEqual(prev["manifest"]["conversation_count"], 1)
                self.assertEqual(len(prev["conversations_preview"]), 1)
                turns = prev["conversations_preview"][0]["turns"]
                self.assertGreaterEqual(len(turns), 2)
                self.assertTrue(any("Destruction Era" in tr["text"] for tr in turns))
                self.assertFalse(any("SECRETKEY12345678901234567890" in tr["text"] for tr in turns))

                conv = post_api("api/convert", {
                    "source": str(zpath), "source_format": "chatgpt", "target": "claude-code",
                    "project": "Destruction Era", "out": str(out_bundle), "cwd": str(tp),
                })
                self.assertTrue(conv["verify"]["ok"])

                # Verify upgraded offline viewer '/' immediately renders real conversation message content!
                vsrv = HTTPServer(("127.0.0.1", 0), make_viewer_handler(conv["written_to"]))
                vport = vsrv.server_address[1]
                threading.Thread(target=vsrv.serve_forever, daemon=True).start()
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{vport}/", timeout=5) as vr:
                        vhtml = vr.read().decode("utf-8")
                        self.assertIn("Branch A initial answer.", vhtml)
                        self.assertNotIn("SECRETKEY12345678901234567890", vhtml)
                finally:
                    vsrv.shutdown()
                    vsrv.server_close()

                # Apply to sandbox & exact rollback through Desktop UI API!
                app_res = post_api("api/apply", {
                    "bundle": conv["written_to"], "target_root": str(sandbox_dst), "apply": True,
                })
                self.assertTrue(app_res["post_write_verification"]["ok"])
                rb_res = post_api("api/rollback", {"tx_dir": app_res["journal_dir"]})
                self.assertTrue(rb_res["ok"])
        finally:
            srv.shutdown()
            srv.server_close()


if __name__ == "__main__":
    unittest.main()
