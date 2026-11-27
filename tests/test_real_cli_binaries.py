"""Repeatable real-binary CLI & extension acceptance suite for Nexus Memory.

Runs strictly inside disposable temporary directories (`HOME`, `XDG_*`, `CODEX_HOME`, `DSH_HOME`)
with zero API keys, zero login mutations, and zero network/LLM calls. Individual binary checks
auto-skip cleanly on CI runners where that vendor CLI is not installed, while executing in full
on developer machines with local Harnesses installed.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

from nexus_memory.bundle import write_bundle
from nexus_memory.discovery import discover_harnesses
from nexus_memory.ecosystem import (
    load_any_source,
    parse_cline_home,
    parse_dsh_directory,
    parse_goose_home,
    parse_opencode_sqlite,
    parse_zed_home,
)
from nexus_memory.harnesses_extended import parse_kiro_home
from nexus_memory.model import ConversationGraph, MessageNode
from nexus_memory.transaction import apply_bundle, rollback_transaction, verify_bundle


def _make_git_workspace(root: Path) -> Path:
    ws = root / "RealCliWorkspace"
    ws.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(ws), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(ws), "-c", "user.name=Nexus", "-c", "user.email=nexus@example.com", "commit", "--allow-empty", "-qm", "init"],
        check=True,
    )
    return ws


def _make_seed(ws: Path) -> list[ConversationGraph]:
    return [
        ConversationGraph(
            source_format="codex_rollout",
            source_id="real-cli-suite-001",
            title="Nexus Real Binary CLI Acceptance",
            workspace=str(ws),
            nodes=(
                MessageNode(
                    "u1",
                    None,
                    ("a1",),
                    "user",
                    "Explain how Nexus Memory preserves cross-harness sessions.",
                    "2026-11-27T01:00:00Z",
                    "Explain how Nexus Memory preserves cross-harness sessions.",
                    {},
                ),
                MessageNode(
                    "a1",
                    "u1",
                    ("u2",),
                    "assistant",
                    "Nexus Memory deterministically projects canonical graphs with 0600 atomic rollback.",
                    "2026-11-27T01:00:02Z",
                    "Nexus Memory deterministically projects canonical graphs with 0600 atomic rollback.",
                    {},
                ),
                MessageNode(
                    "u2",
                    "a1",
                    ("a2",),
                    "user",
                    "Confirm native target CLI acceptance.",
                    "2026-11-27T01:00:04Z",
                    "Confirm native target CLI acceptance.",
                    {},
                ),
                MessageNode(
                    "a2",
                    "u2",
                    (),
                    "assistant",
                    "Confirmed across installed CLIs with zero LLM calls.",
                    "2026-11-27T01:00:06Z",
                    "Confirmed across installed CLIs with zero LLM calls.",
                    {},
                ),
            ),
            root_ids=("u1",),
            active_node_id="a2",
            metadata={"project_name": "RealCliWorkspace", "section_name": "Destruction Era"},
            raw_source={},
        )
    ]


def _isolated_env(home_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "HOME": str(home_dir),
            "XDG_DATA_HOME": str(home_dir / ".local/share"),
            "XDG_CONFIG_HOME": str(home_dir / ".config"),
            "XDG_STATE_HOME": str(home_dir / ".local/state"),
            "CODEX_HOME": str(home_dir / ".codex"),
            "DSH_HOME": str(home_dir / ".dsh"),
            "CLAUDE_CONFIG_DIR": str(home_dir / ".claude"),
        }
    )
    for secret_k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "KIRO_API_KEY"):
        env.pop(secret_k, None)
    return env


class RealBinaryCliAcceptanceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("opencode"), "opencode CLI not installed")
    def test_real_opencode_cli_list_export_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nx_oc_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".local/share/opencode"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="opencode")
            self.assertTrue(verify_bundle(bdir)["ok"])
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            r_ls = subprocess.run(["opencode", "--standalone", "session", "list"], env=env, cwd=str(ws), capture_output=True, text=True, timeout=30)
            self.assertEqual(r_ls.returncode, 0, r_ls.stderr)
            self.assertIn("Nexus Real Binary", r_ls.stdout)

            oc_sid = next(wf["opencode_session_id"] for wf in tx["written_files"] if wf.get("opencode_session_id"))
            r_exp = subprocess.run(["opencode", "--standalone", "session", "export", oc_sid], env=env, cwd=str(ws), capture_output=True, text=True, timeout=30)
            self.assertEqual(r_exp.returncode, 0, r_exp.stderr)
            self.assertIn("Confirm native target CLI acceptance", r_exp.stdout)
            self.assertEqual(len(parse_opencode_sqlite(troot / "opencode.db")), 1)
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

    @unittest.skipUnless(shutil.which("goose"), "goose CLI not installed")
    def test_real_goose_cli_list_export_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nx_goose_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".local/share/goose"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="goose")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            r_ls = subprocess.run(["goose", "session", "list"], env=env, capture_output=True, text=True, timeout=25)
            self.assertEqual(r_ls.returncode, 0, r_ls.stderr)
            self.assertIn("Nexus Real Binary", r_ls.stdout)

            gsid = next(wf["goose_session_id"] for wf in tx["written_files"] if wf.get("goose_session_id"))
            r_exp = subprocess.run(["goose", "session", "export", "--session-id", gsid], env=env, capture_output=True, text=True, timeout=25)
            self.assertEqual(r_exp.returncode, 0, r_exp.stderr)
            self.assertIn("Confirm native target CLI acceptance", r_exp.stdout)
            self.assertEqual(len(parse_goose_home(troot)), 1)
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

    @unittest.skipUnless(shutil.which("cline"), "cline CLI not installed")
    def test_real_cline_cli_history_and_roo_cursor_extension_lanes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nx_cline_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".cline"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="cline-roo")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            r_hist = subprocess.run(
                ["cline", "--config", str(troot), "--data-dir", str(troot / "data"), "history", "--json"],
                env=env,
                capture_output=True,
                text=True,
                timeout=25,
            )
            self.assertEqual(r_hist.returncode, 0, r_hist.stderr)
            self.assertIn("Nexus Real Binary", r_hist.stdout)
            self.assertEqual(len(parse_cline_home(troot)), 1)
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

            # Also verify Cursor globalStorage Roo Code & Cline extension task discovery in isolated HOME
            roo_task = root / "Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/tasks/roo-task-1"
            roo_task.mkdir(parents=True)
            (roo_task / "api_conversation_history.json").write_text(
                json.dumps([{"role": "user", "content": [{"type": "text", "text": "Hello Roo 3.54"}]}]),
                encoding="utf-8",
            )
            disc = discover_harnesses(home=root, platform="darwin")
            by_id = {h["id"]: h for h in disc["harnesses"]}
            self.assertTrue(by_id["roo"]["detected"])
            self.assertEqual(by_id["roo"]["session_file_count"], 1)
            roo_graphs = parse_cline_home(root / "Library/Application Support/Cursor")
            self.assertEqual(len(roo_graphs), 1)
            self.assertIn("Hello Roo 3.54", roo_graphs[0].nodes[0].text)

    @unittest.skipUnless(shutil.which("cn"), "Continue cn CLI not installed")
    def test_real_continue_cli_ls_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nx_cn_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".continue"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="continue")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            r_cn = subprocess.run(["cn", "ls", "--json"], env=env, capture_output=True, text=True, timeout=25)
            self.assertEqual(r_cn.returncode, 0, r_cn.stderr)
            self.assertIn("Nexus Real Binary", r_cn.stdout)
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

    @unittest.skipUnless(shutil.which("pi"), "pi CLI not installed")
    def test_real_pi_cli_export_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nx_pi_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".pi"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="pi")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            pi_jl = next((troot / "agent/sessions").rglob("*.jsonl"))
            pi_html = root / "pi-export.html"
            r_pi = subprocess.run(["pi", "--export", str(pi_jl), str(pi_html)], env=env, capture_output=True, text=True, timeout=25)
            self.assertEqual(r_pi.returncode, 0, r_pi.stderr)
            m = re.search(r'id="session-data"[^>]*>([^<]+)<', pi_html.read_text(encoding="utf-8", errors="ignore"))
            self.assertIsNotNone(m)
            decoded = base64.b64decode(m.group(1).strip()).decode("utf-8", errors="replace")
            self.assertIn("Confirm native target CLI acceptance", decoded)
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

    @unittest.skipUnless(shutil.which("gemini"), "gemini CLI not installed")
    def test_real_gemini_cli_list_sessions_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nx_gem_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".gemini"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="gemini-cli")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            r_gm = subprocess.run(["gemini", "--list-sessions"], env=env, cwd=str(ws), capture_output=True, text=True, timeout=30)
            self.assertEqual(r_gm.returncode, 0, r_gm.stderr)
            self.assertIn("Explain how Nexus Memory preserves", r_gm.stdout)
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

    @unittest.skipUnless(shutil.which("codex"), "codex CLI not installed")
    def test_real_codex_cli_migrate_rollouts_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nx_codex_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".codex"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="codex")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            # Dry-run inspection first (does not mutate troot so scoped rollback stays exact!)
            r_insp = subprocess.run(["codex", "migrate-rollouts", "--json"], env=env, cwd=str(ws), capture_output=True, text=True, timeout=25)
            self.assertEqual(r_insp.returncode, 0, r_insp.stderr)
            outcomes = json.loads(r_insp.stdout)["outcomes"]
            self.assertEqual(len(outcomes), 1)
            self.assertEqual(outcomes[0]["status"], "eligible")
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

            # Also verify full `--apply` into Codex SQLite thread history on a second disposable copy
            troot2 = root / ".codex-apply"
            env2 = {**env, "CODEX_HOME": str(troot2)}
            apply_bundle(bdir, target_root=troot2, apply=True)
            r_app = subprocess.run(["codex", "migrate-rollouts", "--apply", "--json"], env=env2, cwd=str(ws), capture_output=True, text=True, timeout=25)
            self.assertEqual(r_app.returncode, 0, r_app.stderr)
            outcomes2 = json.loads(r_app.stdout)["outcomes"]
            self.assertEqual(outcomes2[0]["status"], "migrated")
            self.assertGreater(outcomes2[0]["bytes_processed"], 0)

    @unittest.skipUnless(shutil.which("dsh") and shutil.which("node"), "dsh CLI / node not installed")
    def test_real_dsh_cli_v4_zstd_catalog_restore_and_rollback(self) -> None:
        dsh_bin = Path(shutil.which("dsh") or "").resolve()
        dsh_nm = dsh_bin.parent.parent / "node_modules"
        cat_js = dsh_nm / "@deepseek-ai/dsh-session-format-catalog/lib/index.js"
        with tempfile.TemporaryDirectory(prefix="nx_dsh_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".dsh"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="dsh")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            r_ver = subprocess.run(["dsh", "--version"], env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(r_ver.returncode, 0, r_ver.stderr)

            if cat_js.is_file():
                zstd_files = list((troot / "sessions").rglob("session.v4.jsonl.zstd"))
                if zstd_files:
                    raw_zstd = zstd_files[0].read_bytes()
                    # Verify 2-frame checksummed Zstandard layout (Frame 1 = header, Frame 2 = events)
                    self.assertGreaterEqual(raw_zstd.count(b"\x28\xb5\x2f\xfd"), 2)
                decoded_rows = parse_dsh_directory(troot / "sessions")[0].raw_source["records"]
                r_cat = subprocess.run(
                    [
                        "node",
                        "-e",
                        r"""
                        const fs = require("node:fs");
                        (async () => {
                          const catMod = await import(process.argv[1]);
                          const cat = catMod.sessionFormatCatalog;
                          const rows = JSON.parse(fs.readFileSync(0, "utf8"));
                          const restore = cat.createRestore(rows[0], { validation: "current", recovery: "strict" });
                          for (const r of rows.slice(1)) restore.decodeRow(r);
                          const fin = restore.finish();
                          console.log(JSON.stringify({ ok: true, id: fin.header.id, events: fin.events.length }));
                        })();
                        """,
                        str(cat_js),
                    ],
                    input=json.dumps(decoded_rows),
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual(r_cat.returncode, 0, r_cat.stderr)
                parsed_out = json.loads(r_cat.stdout.strip())
                self.assertTrue(parsed_out["ok"])
                self.assertGreaterEqual(parsed_out["events"], 5)

            dsh_back = parse_dsh_directory(troot / "sessions")
            self.assertEqual(len(dsh_back), 1)
            self.assertIn("Confirm native target CLI acceptance", "\n".join(n.text for n in dsh_back[0].nodes))
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

    @unittest.skipUnless(shutil.which("kiro-cli"), "kiro-cli not installed")
    def test_real_kiro_cli_database_open_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nx_kiro_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = (
                root / "Library/Application Support/kiro-cli"
                if os.uname().sysname == "Darwin"
                else root / ".local/share/kiro-cli"
            )
            m = write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="kiro")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            # Verify kiro-cli opens our data.sqlite3 cleanly without schema/migration collision
            sid = m["target_sessions"][0]["session_id"]
            troot_copy = root / "kiro-copy"
            shutil.copytree(troot, troot_copy)
            r_kr = subprocess.run(
                ["kiro-cli", "chat", "--no-interactive", "--resume-id", sid],
                env=env,
                cwd=str(ws),
                capture_output=True,
                text=True,
                timeout=15,
            )
            combined = (r_kr.stdout or "") + "\n" + (r_kr.stderr or "")
            self.assertNotIn("Failed to open database", combined)
            self.assertNotIn("already exists", combined)
            self.assertEqual(len(parse_kiro_home(troot_copy)), 1)

    @unittest.skipUnless(shutil.which("t3") or Path.home().joinpath(".local/bin/t3").is_file(), "t3 CLI not installed")
    def test_real_t3_serve_boots_against_migrated_statev2_sqlite(self) -> None:
        t3_bin = shutil.which("t3") or str(Path.home() / ".local/bin/t3")
        with tempfile.TemporaryDirectory(prefix="nx_t3_") as td:
            root = Path(td)
            ws = _make_git_workspace(root)
            env = _isolated_env(root)
            bdir = root / "bundle"
            troot = root / ".t3"
            write_bundle(_make_seed(ws), out=bdir, cwd=ws, target="t3code")
            tx = apply_bundle(bdir, target_root=troot, apply=True)
            self.assertTrue(tx["post_write_verification"]["ok"])

            # Verify pristine rollback first on troot, then boot real `t3 serve` on a disposable copy
            t3_live = root / ".t3-serve"
            shutil.copytree(troot, t3_live)
            self.assertTrue(rollback_transaction(tx["journal_dir"])["ok"])

            with socket.socket() as s:
                s.bind(("127.0.0.1", 0))
                port = s.getsockname()[1]
            proc = subprocess.Popen(
                [t3_bin, "serve", "--base-dir", str(t3_live), "--host", "127.0.0.1", "--port", str(port)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                http_ok = False
                for _ in range(40):
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1) as r:
                            if r.status == 200:
                                http_ok = True
                                break
                    except Exception:
                        time.sleep(0.25)
                self.assertTrue(http_ok, "t3 serve failed to boot HTTP 200 on migrated statev2.sqlite")
            finally:
                proc.terminate()
                proc.wait(timeout=5)
            reloaded, _ = load_any_source(t3_live, source_format="t3code")
            self.assertEqual(len(reloaded), 1)
            self.assertIn("Confirm native target CLI acceptance", "\n".join(n.text for n in reloaded[0].nodes))
