"""Repeatable headless Chromium GUI End-to-End suite for Nexus Memory (`desktop_ui`).

Launches `python -m nexus_memory.desktop_ui --server-only` in an isolated `HOME` subprocess
and drives the real Web UI through Playwright Chromium (strictly respecting `default-src 'none'; script-src 'unsafe-inline'` CSP without `unsafe-eval`):
- Discovery & 25-Harness Capability Matrix tabs + search filtering
- Info popovers (`ⓘ`) & Dark/Light theme switching
- Multi-hop real GUI migration chain:
  1. ChatGPT Destruction Era ZIP (with synthetic secret + 2 branches) -> OpenCode (`opencode.db`)
  2. OpenCode (`opencode.db`) -> T3 Code (`userdata/statev2.sqlite`)
  3. Direction Swap (`⇄ 互换`) + T3 Code -> DeepSeek DSH (`session.v4.jsonl[.zstd]`)
- Offline Bundle Viewer (`openViewer()`) CSP & content inspection
- One-click GUI Rollback (`#btn-rail-rollback`) + History Rollback tab (`#tab-rollback`) restoring empty SHA-256
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

try:
    from playwright.sync_api import expect, sync_playwright

    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_gui_chatgpt_fixture(zip_path: Path) -> None:
    png_bytes = b"\x89PNG\r\n\x1a\ngui-e2e-synthetic-diagram"
    convs = [
        {
            "id": "gui-conv-001",
            "title": "GUI E2E Architecture sk-ant-SECRETKEY12345678901234567890",
            "project_id": "proj-gui",
            "create_time": 1764100000,
            "update_time": 1764100500,
            "current_node": "n-a1",
            "mapping": {
                "root": {"id": "root", "parent": None, "children": ["n-u1"], "message": None},
                "n-u1": {
                    "id": "n-u1",
                    "parent": "root",
                    "children": ["n-a1", "n-a2"],
                    "message": {
                        "author": {"role": "user"},
                        "create_time": 1764100010,
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Verify automated Playwright GUI multi-hop migration.",
                                {"type": "image", "asset_pointer": "file-service://file-gui01", "name": "arch.png"},
                            ],
                        },
                    },
                },
                "n-a1": {
                    "id": "n-a1",
                    "parent": "n-u1",
                    "children": [],
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1764100020,
                        "content": {"content_type": "text", "parts": ["Branch Alpha verified in GUI E2E."]},
                    },
                },
                "n-a2": {
                    "id": "n-a2",
                    "parent": "n-u1",
                    "children": [],
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1764100030,
                        "content": {"content_type": "text", "parts": ["Branch Beta verified in GUI E2E."]},
                    },
                },
            },
        }
    ]
    projects = [{"id": "proj-gui", "name": "Destruction Era"}]
    sections = [{"id": "sec-gui", "name": "GUI Automation", "conversation_ids": ["gui-conv-001"]}]
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("conversations.json", json.dumps(convs))
        zf.writestr("projects.json", json.dumps(projects))
        zf.writestr("sections.json", json.dumps(sections))
        zf.writestr("file-gui01-arch.png", png_bytes)


def _chromium_launchable() -> bool:
    if not _HAS_PLAYWRIGHT:
        return False
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False


@unittest.skipUnless(_chromium_launchable(), "Playwright Chromium browser is not installed")
class DesktopGuiPlaywrightE2ETests(unittest.TestCase):
    def test_isolated_gui_multihop_migration_viewer_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nexus_gui_pw_") as td:
            root = Path(td)
            fake_home = root / "home"
            fake_home.mkdir()
            ws = root / "GuiWorkspace"
            ws.mkdir()
            subprocess.run(["git", "-C", str(ws), "init", "-q"], check=True)
            subprocess.run(
                ["git", "-C", str(ws), "-c", "user.name=Nexus", "-c", "user.email=n@example.com", "commit", "--allow-empty", "-qm", "init"],
                check=True,
            )

            zpath = root / "chatgpt-gui.zip"
            _make_gui_chatgpt_fixture(zpath)

            ready_file = root / "ready.json"
            env = dict(os.environ)
            env.update(
                {
                    "HOME": str(fake_home),
                    "XDG_DATA_HOME": str(fake_home / ".local/share"),
                    "XDG_CONFIG_HOME": str(fake_home / ".config"),
                    "PYTHONPATH": str(REPO_ROOT / "src"),
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "NEXUS_NO_BROWSER": "1",
                }
            )
            proc = subprocess.Popen(
                [sys.executable, "-m", "nexus_memory.desktop_ui", "--server-only", "--ready-file", str(ready_file)],
                cwd=str(ws),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.time() + 25.0
                while time.time() < deadline and not ready_file.is_file():
                    if proc.poll() is not None:
                        break
                    time.sleep(0.1)
                if not ready_file.is_file():
                    proc.terminate()
                    out_s, err_s = proc.communicate(timeout=5)
                    self.fail(f"desktop_ui failed to write ready.json (rc={proc.returncode}): stdout={out_s!r} stderr={err_s!r}")
                ready_info = json.loads(ready_file.read_text(encoding="utf-8"))
                app_url = ready_info["url"]

                with sync_playwright() as pw:
                    browser = pw.chromium.launch(headless=True)
                    context = browser.new_context(viewport={"width": 1440, "height": 920})
                    page = context.new_page()
                    page.goto(app_url, wait_until="networkidle")

                    # 1. Verify isolated HOME shows 0 pre-existing harnesses and 25 matrix entries
                    expect(page.locator("#cnt-detected")).to_have_text("0", timeout=10000)
                    expect(page.locator("#cnt-matrix")).to_have_text("25", timeout=10000)

                    # 2. Verify Theme Toggle & Info Popover (using DOM attribute checks — zero unsafe-eval)
                    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
                    page.locator(".theme-btn").click()
                    expect(page.locator("html")).to_have_attribute("data-theme", "light")
                    page.locator(".theme-btn").click()
                    page.locator("aside.sidebar .info-btn").click()
                    expect(page.locator("#info-popover")).to_be_visible()
                    expect(page.locator("#info-pop-title")).to_contain_text("零 AI")
                    page.locator(".info-pop-close").click()

                    # 3. Verify Matrix Tab search & Discover Tab
                    page.locator("#nav-matrix").click()
                    expect(page.locator("#tab-matrix")).to_be_visible()
                    expect(page.locator("#matrix-tbody tr")).to_have_count(25)
                    page.locator("#matrix-search").fill("dsh")
                    expect(page.locator("#matrix-tbody tr")).to_have_count(1)
                    expect(page.locator("#matrix-tbody tr").first).to_contain_text("E5")
                    page.locator("#matrix-search").fill("")
                    page.locator("#nav-migrate").click()

                    # 4. Expand ALL 24 sources & ALL 25 targets in Step 1
                    page.locator("#src-filter-all").click()
                    page.locator("#dst-filter-all").click()
                    self.assertGreaterEqual(page.locator("#source-grid .h-card").count(), 24)
                    self.assertGreaterEqual(page.locator("#target-grid .h-card").count(), 24)

                    # ── HOP 1: ChatGPT Export ZIP -> OpenCode SQLite (`opencode.db`) ──
                    page.locator('#source-grid .h-card[data-id="chatgpt-export"]').click()
                    page.locator('#target-grid .h-card[data-id="opencode"]').click()
                    page.locator("#limit-presets button[data-val='0']").click()
                    page.locator("#filter-section").fill("")
                    page.locator("#src-path").fill(str(zpath))
                    page.locator("#cwd-path").fill(str(ws))
                    b1_dir = root / "bundle-hop1-opencode"
                    t1_oc = root / "target-hop1-opencode"
                    page.locator("#out-path").fill(str(b1_dir))

                    # Step 1 -> Step 2 Preview
                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#preview-badge")).to_contain_text("✓ 1 条会话", timeout=15000)
                    expect(page.locator("#k-convs")).to_have_text("1")
                    expect(page.locator("#k-sess")).to_have_text("2")
                    reader_txt = page.locator("#preview-reader").inner_text()
                    self.assertIn("Verify automated Playwright GUI", reader_txt)
                    self.assertNotIn("SECRETKEY12345678901234567890", reader_txt)

                    # Step 2 -> Step 3 Generate & Verify Bundle
                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#bundle-badge")).to_contain_text("✓ SHA-256 校验通过", timeout=15000)

                    # Open Offline Bundle Viewer & verify rendered HTML in a second tab
                    page.locator("#btn-inline-viewer").click()
                    expect(page.locator("#guide-text")).to_contain_text("http://127.0.0.1:", timeout=10000)
                    guide_html = page.locator("#guide-text").inner_html()
                    m_url = re.search(r"http://127\.0\.0\.1:\d+/?", guide_html)
                    self.assertIsNotNone(m_url)
                    viewer_page = context.new_page()
                    viewer_resp = viewer_page.goto(m_url.group(0), wait_until="domcontentloaded")
                    self.assertIsNotNone(viewer_resp)
                    self.assertEqual(viewer_resp.status, 200)
                    self.assertIn("Branch Alpha verified in GUI E2E.", viewer_page.content())
                    self.assertNotIn("SECRETKEY12345678901234567890", viewer_page.content())
                    viewer_page.close()

                    # Step 3 -> Step 4 Apply to isolated OpenCode root
                    page.locator("#apply-target-root").fill(str(t1_oc))
                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#apply-badge")).to_contain_text("✓ 已迁入并读回校验通过", timeout=15000)
                    self.assertTrue((t1_oc / "opencode.db").is_file())
                    tx1_dir = page.locator("#rb-bundle").input_value()

                    # ── HOP 2: OpenCode (`opencode.db`) -> T3 Code (`statev2.sqlite`) ──
                    page.locator("#btn-main-cta").click()  # "↻ 新一次迁移"
                    page.locator('#source-grid .h-card[data-id="opencode"]').click()
                    page.locator('#target-grid .h-card[data-id="t3code"]').click()
                    page.locator("#src-path").fill(str(t1_oc))
                    b2_dir = root / "bundle-hop2-t3code"
                    t2_t3 = root / "target-hop2-t3code"
                    page.locator("#out-path").fill(str(b2_dir))

                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#preview-badge")).to_contain_text("✓ 2 条会话", timeout=15000)
                    expect(page.locator("#k-convs")).to_have_text("2")
                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#bundle-receipt")).to_contain_text("bundle-hop2-t3code", timeout=15000)
                    expect(page.locator("#bundle-badge")).to_contain_text("✓ SHA-256 校验通过")
                    page.locator("#apply-target-root").fill(str(t2_t3))
                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#apply-success-box")).to_contain_text("bundle-hop2-t3code", timeout=15000)
                    expect(page.locator("#apply-badge")).to_contain_text("✓ 已迁入并读回校验通过")
                    self.assertTrue((t2_t3 / "userdata" / "statev2.sqlite").is_file())
                    tx2_dir = page.locator("#rb-bundle").input_value()

                    # ── HOP 3: Swap Direction (`⇄ 互换`) + T3 Code -> DeepSeek DSH (`session.v4.jsonl.zstd`) + GUI Rollback ──
                    page.locator("#btn-swap").click()
                    expect(page.locator("#bridge-src-name")).to_have_text("T3 Code")
                    expect(page.locator("#bridge-dst-name")).to_have_text("OpenCode")
                    page.locator('#target-grid .h-card[data-id="dsh"]').click()
                    page.locator("#src-path").fill(str(t2_t3))
                    b3_dir = root / "bundle-hop3-dsh"
                    t3_dsh = root / "target-hop3-dsh"
                    page.locator("#out-path").fill(str(b3_dir))

                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#preview-badge")).to_contain_text("✓ 2 条会话", timeout=15000)
                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#bundle-receipt")).to_contain_text("bundle-hop3-dsh", timeout=15000)
                    page.locator("#apply-target-root").fill(str(t3_dsh))
                    page.locator("#btn-main-cta").click()
                    expect(page.locator("#apply-success-box")).to_contain_text("bundle-hop3-dsh", timeout=15000)
                    self.assertTrue(any((t3_dsh / "sessions").rglob("session.v4.jsonl")))

                    # One-click GUI Rollback on Hop 3 (`#btn-rail-rollback`)
                    page.locator("#btn-rail-rollback").click()
                    expect(page.locator("#apply-badge")).to_contain_text("↺ 已精确回滚至迁移前原状", timeout=15000)
                    self.assertEqual(sum(1 for p in t3_dsh.rglob("*") if p.is_file()), 0)

                    # Manual Rollback & Cleanup Tab (`#nav-rollback`) for Hop 2 & Hop 1
                    page.locator("#nav-rollback").click()
                    expect(page.locator("#tab-rollback")).to_be_visible()
                    expect(page.locator("#st-rss-mb")).to_contain_text("MB", timeout=10000)
                    page.locator("#btn-reclaim-memory").click()
                    expect(page.locator("#cleanup-status-msg")).to_contain_text("GC 内存回收", timeout=10000)
                    for tx_path, target_dir in ((tx2_dir, t2_t3), (tx1_dir, t1_oc)):
                        page.locator("#rb-bundle").fill(tx_path)
                        page.locator("#btn-manual-rollback").click()
                        expect(page.locator("#rb-json")).to_contain_text(Path(tx_path).name, timeout=15000)
                        expect(page.locator("#rb-json")).to_contain_text('"ok": true')
                        self.assertEqual(sum(1 for p in target_dir.rglob("*") if p.is_file()), 0)
                        page.locator("#btn-manual-cleanup-tx").click()
                        expect(page.locator("#rb-json")).to_contain_text('"reclaimed_bytes"', timeout=10000)

                    context.close()
                    browser.close()
            finally:
                proc.terminate()
                proc.wait(timeout=5)
