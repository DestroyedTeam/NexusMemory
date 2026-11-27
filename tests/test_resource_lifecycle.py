"""Regression tests for backup auto-pruning, post-verify cleanup, streaming I/O, and memory reclamation."""

from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from nexus_memory.bundle import write_bundle
from nexus_memory.cli import main as cli_main
from nexus_memory.desktop_ui import start_desktop_server
from nexus_memory.lifecycle import (
    cleanup_transaction_backup,
    delete_bundle_dir,
    get_process_memory_mb,
    prune_reclaimable_storage,
    reclaim_memory,
    scan_reclaimable_storage,
)
from nexus_memory.model import ConversationGraph, MessageNode
from nexus_memory.security import atomic_copy_file, atomic_write_json, atomic_write_stream, sha256_file
from nexus_memory.transaction import apply_bundle, rollback_transaction


def _sample_graph(idx: int = 1) -> ConversationGraph:
    u_id = f"u-{idx}"
    a_id = f"a-{idx}"
    return ConversationGraph(
        source_format="portable",
        source_id=f"lifecycle-conv-{idx}",
        title=f"Lifecycle Test Conversation {idx}",
        workspace="/tmp/lifecycle-ws",
        nodes=(
            MessageNode(
                node_id=u_id,
                parent_id=None,
                child_ids=(a_id,),
                role="user",
                text=f"Please migrate lifecycle test #{idx}.",
                timestamp="2026-11-28T00:00:00Z",
                content=f"Please migrate lifecycle test #{idx}.",
                raw_record={},
            ),
            MessageNode(
                node_id=a_id,
                parent_id=u_id,
                child_ids=(),
                role="assistant",
                text=f"Completed lifecycle migration #{idx} cleanly.",
                timestamp="2026-11-28T00:00:01Z",
                content=f"Completed lifecycle migration #{idx} cleanly.",
                raw_record={},
            ),
        ),
        root_ids=(u_id,),
        active_node_id=a_id,
        metadata={},
        raw_source={},
    )


def test_streaming_io_and_compact_json_primitives(tmp_path: Path) -> None:
    src = tmp_path / "big.bin"
    payload = os.urandom(3 * 1024 * 1024 + 77)  # > 3 MiB
    src.write_bytes(payload)
    expected_sha = hashlib.sha256(payload).hexdigest()
    assert sha256_file(src) == expected_sha

    dst = tmp_path / "copied.bin"
    written = atomic_copy_file(src, dst, mode=0o600)
    assert written == len(payload)
    assert sha256_file(dst) == expected_sha

    stream_dst = tmp_path / "streamed.bin"
    written_s = atomic_write_stream(stream_dst, io.BytesIO(payload), mode=0o600)
    assert written_s == len(payload)
    assert sha256_file(stream_dst) == expected_sha

    # Streaming JSON writer (pretty and compact)
    obj = {"items": [{"k": i, "text": "中文-测试-" + str(i)} for i in range(400)]}
    pretty_p = tmp_path / "pretty.json"
    compact_p = tmp_path / "compact.json"
    atomic_write_json(pretty_p, obj, compact=False)
    atomic_write_json(compact_p, obj, compact=True)
    assert json.loads(pretty_p.read_text(encoding="utf-8")) == obj
    assert json.loads(compact_p.read_text(encoding="utf-8")) == obj
    assert compact_p.stat().st_size < pretty_p.stat().st_size


def test_auto_prune_and_post_verify_backup_cleanup(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle-1"
    target_dir = tmp_path / "target-claude"
    write_bundle([_sample_graph(1)], out=bundle_dir, cwd="/tmp/lifecycle-ws", target="claude-code")

    # 1. Frequent applies (5x with rename + auto_prune_keep=2) must keep at most 2 active .tar.gz backups!
    tx_dirs: list[Path] = []
    for i in range(5):
        res = apply_bundle(
            bundle_dir,
            target_root=target_dir,
            apply=True,
            on_collision="rename",
            auto_prune_keep=2,
        )
        assert res["post_write_verification"]["ok"] is True
        tx_dirs.append(Path(res["journal_dir"]))
        time.sleep(0.02)

    inv = scan_reclaimable_storage(extra_roots=[bundle_dir], include_temp=False, include_desktop=False)
    assert inv["summary"]["total_transaction_count"] == 5
    assert inv["summary"]["active_backup_count"] == 2
    # Target files must still be completely intact
    assert len(list((target_dir / "projects").rglob("*.jsonl"))) == 5

    # 2. cleanup_backup_after_verify=True cleans backup archive immediately after readback verify passes
    bundle_2 = tmp_path / "bundle-2"
    target_2 = tmp_path / "target-claude-2"
    write_bundle([_sample_graph(2)], out=bundle_2, cwd="/tmp/lifecycle-ws", target="claude-code")
    res2 = apply_bundle(
        bundle_2,
        target_root=target_2,
        apply=True,
        cleanup_backup_after_verify=True,
    )
    assert res2["post_write_verification"]["ok"] is True
    assert res2["backup_cleaned"] is True
    assert not Path(res2["backup_archive"]).exists()
    assert (Path(res2["journal_dir"]) / "transaction.json").is_file()
    assert len(list((target_2 / "projects").rglob("*.jsonl"))) == 1

    # 3. Manual confirm & remove entire verified bundle (and safety refusal on arbitrary directory)
    cln = cleanup_transaction_backup(res2["journal_dir"], remove_bundle=True)
    assert cln["ok"] is True
    assert cln["removed_bundle"] is True
    assert not bundle_2.exists()
    assert len(list((target_2 / "projects").rglob("*.jsonl"))) == 1

    unsafe_dir = tmp_path / "not-a-nexus-bundle"
    unsafe_dir.mkdir()
    (unsafe_dir / "important.txt").write_text("do not delete", encoding="utf-8")
    with pytest.raises(ValueError):
        delete_bundle_dir(unsafe_dir)
    assert (unsafe_dir / "important.txt").is_file()


def test_rollback_with_cleanup_backup_and_cli_cleanup(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bundle_dir = tmp_path / "bundle-rb"
    target_dir = tmp_path / "target-rb"
    write_bundle([_sample_graph(3)], out=bundle_dir, cwd="/tmp/lifecycle-ws", target="claude-code")

    res = apply_bundle(bundle_dir, target_root=target_dir, apply=True)
    tx_dir = Path(res["journal_dir"])
    assert Path(res["backup_archive"]).is_file()

    # Rollback with cleanup_backup=True restores exact pre-apply state AND deletes spent backup tar.gz
    rb = rollback_transaction(tx_dir, cleanup_backup=True)
    assert rb["ok"] is True
    assert rb["backup_cleanup"]["ok"] is True
    assert not Path(res["backup_archive"]).exists()
    assert not list(target_dir.rglob("*.jsonl"))

    # CLI `cleanup` dry-run & apply on another bundle
    bundle_cli = tmp_path / "bundle-cli"
    target_cli = tmp_path / "target-cli"
    write_bundle([_sample_graph(4)], out=bundle_cli, cwd="/tmp/lifecycle-ws", target="claude-code")
    res_cli = apply_bundle(bundle_cli, target_root=target_cli, apply=True)
    tx_cli = Path(res_cli["journal_dir"])

    rc_dry = cli_main(["cleanup", "--tx-dir", str(tx_cli)])
    assert rc_dry == 0
    dry_out = json.loads(capsys.readouterr().out)
    assert dry_out["dry_run"] is True
    assert Path(res_cli["backup_archive"]).is_file()

    rc_real = cli_main(["cleanup", "--tx-dir", str(tx_cli), "--apply"])
    assert rc_real == 0
    real_out = json.loads(capsys.readouterr().out)
    assert real_out["dry_run"] is False
    assert not Path(res_cli["backup_archive"]).exists()


def test_repeated_migrations_bounded_memory_and_desktop_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_NO_BROWSER", "1")
    monkeypatch.setenv("NEXUS_SKIP_STARTUP_PRUNE", "1")

    # 1. Verify memory reclamation & bounded RSS across 12 repeated migrations
    reclaim_memory()
    rss_start = get_process_memory_mb()
    assert rss_start > 0
    for i in range(12):
        b = tmp_path / f"mem-bundle-{i}"
        t = tmp_path / f"mem-target-{i}"
        write_bundle([_sample_graph(100 + i)], out=b, cwd="/tmp/lifecycle-ws", target="claude-code")
        res = apply_bundle(b, target_root=t, apply=True, cleanup_backup_after_verify=True)
        assert res["post_write_verification"]["ok"] is True
        delete_bundle_dir(b)
    mem_info = reclaim_memory()
    assert mem_info["after_rss_mb"] > 0
    # Repeated small migrations must not leak more than 80 MB
    assert (mem_info["after_rss_mb"] - rss_start) < 80.0

    # 2. Verify Desktop API `/api/storage`, `/api/cleanup`, single-instance viewer, and job result eviction
    srv, base_url, token = start_desktop_server(port=0)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        def _req(path: str, body: dict | None = None) -> dict:
            data = json.dumps(body).encode("utf-8") if body is not None else None
            req = urllib.request.Request(
                base_url.rstrip("/") + path,
                data=data,
                headers={"X-Nexus-Token": token, "Content-Type": "application/json"},
                method="POST" if body is not None else "GET",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))

        st_inv = _req("/api/storage")
        assert st_inv["schema"] == "nexus-memory.storage-inventory.v1"
        assert st_inv["summary"]["process_rss_mb"] > 0

        mem_res = _req("/api/cleanup", {"mode": "reclaim_memory"})
        assert "after_rss_mb" in mem_res

        # Open viewer twice: first viewer server must be shut down cleanly (zero leaked viewer servers!)
        vb1 = tmp_path / "viewer-b1"
        vb2 = tmp_path / "viewer-b2"
        write_bundle([_sample_graph(201)], out=vb1, cwd="/tmp/lifecycle-ws", target="claude-code")
        write_bundle([_sample_graph(202)], out=vb2, cwd="/tmp/lifecycle-ws", target="claude-code")

        v1 = _req("/api/open-viewer", {"bundle": str(vb1)})
        with urllib.request.urlopen(v1["url"], timeout=5) as r1:
            assert r1.status == 200

        v2 = _req("/api/open-viewer", {"bundle": str(vb2)})
        with urllib.request.urlopen(v2["url"], timeout=5) as r2:
            assert r2.status == 200

        # First viewer server should now be closed (connection refused)
        with pytest.raises((urllib.error.URLError, OSError)):
            urllib.request.urlopen(v1["url"], timeout=2)

        # Async job result eviction after delivery
        started = _req("/api/jobs/preview", {"source": str(vb1), "source_format": "portable", "target": "codex"})
        jid = started["job_id"]
        first_done = None
        for _ in range(100):
            snap = _req(f"/api/jobs/{jid}")
            if snap["status"] == "done":
                first_done = snap
                break
            time.sleep(0.05)
        assert first_done is not None
        assert first_done["result"] is not None
        second_poll = _req(f"/api/jobs/{jid}")
        assert second_poll["result"] is None
        assert second_poll.get("result_delivered") is True
    finally:
        close_fn = getattr(srv.RequestHandlerClass, "_close_active_viewer", None)
        if callable(close_fn):
            close_fn()
        srv.shutdown()
        srv.server_close()


def test_prune_temp_sandbox_dir(tmp_path: Path) -> None:
    # Create a real Nexus-prefixed sandbox dir in OS temp dir and ensure prune removes it safely
    sb = Path(tempfile.gettempdir()) / f"nexus-memory-sandbox-test-{os.getpid()}"
    sb.mkdir(parents=True, exist_ok=True)
    (sb / "dummy.txt").write_text("sandbox test data", encoding="utf-8")
    try:
        res = prune_reclaimable_storage(
            clean_sandboxes=True,
            sandbox_max_age_hours=0,
            clean_bundles=False,
            include_desktop=False,
            include_temp=True,
            dry_run=False,
        )
        assert res["ok"] is True
        assert not sb.exists()
    finally:
        if sb.exists():
            import shutil

            shutil.rmtree(sb, ignore_errors=True)
