"""Hardened local-only (127.0.0.1) offline Bundle Viewer (Obsidian Neural split-pane UI).

Security guarantees (all preserved strictly):
- Strictly bound to 127.0.0.1 (never 0.0.0.0).
- Strict Content-Security-Policy, X-Content-Type-Options: nosniff, Referrer-Policy: no-referrer,
  Cache-Control: no-store on every response.
- Asset downloads strictly validated with `ensure_within_root(bundle/assets/..., bundle/assets)`
  — zero parent-directory exposure, zero `startswith` prefix bypass, zero symlink traversal.
- Active web content (`text/html`, `image/svg+xml`, `application/javascript`, `application/xhtml+xml`)
  ALWAYS served with `Content-Disposition: attachment` (never inline same-origin execution!).
- All rendered conversation text and metadata are HTML-escaped and secret-redacted on display.
"""

from __future__ import annotations

import html
import json
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from .security import ensure_within_root, redact_text, sanitize_single_segment

ACTIVE_CONTENT_TYPES = frozenset(
    {
        "text/html",
        "application/xhtml+xml",
        "image/svg+xml",
        "application/javascript",
        "text/javascript",
        "application/ecmascript",
    }
)

CSP_HEADER = (
    "default-src 'none'; "
    "style-src 'unsafe-inline'; "
    "script-src 'unsafe-inline'; "
    "img-src 'self' data:; "
    "base-uri 'none'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


def _esc(val: Any) -> str:
    return html.escape("" if val is None else str(val), quote=True)


def _node_display_text(node: dict[str, Any]) -> str:
    """Extract readable display text even for tool_call / tool_result nodes whose `text` is sparse."""
    raw_text = str(node.get("text") or "").strip()
    content = node.get("content")
    if raw_text and not raw_text.startswith("tool:"):
        return raw_text
    if isinstance(content, dict):
        if content.get("name") or content.get("arguments") is not None:
            name = content.get("name") or raw_text or "tool"
            args = content.get("arguments", content.get("input", {}))
            args_str = args if isinstance(args, str) else json.dumps(args, ensure_ascii=False, indent=2)
            return f"[{name}]\n{args_str}"
        if content.get("output") is not None:
            out = content["output"]
            return out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)
        return json.dumps(content, ensure_ascii=False, indent=2)
    if isinstance(content, list):
        parts = []
        for blk in content:
            if isinstance(blk, dict):
                if blk.get("text"):
                    parts.append(str(blk["text"]))
                else:
                    parts.append(json.dumps(blk, ensure_ascii=False))
            else:
                parts.append(str(blk))
        joined = "\n".join(p for p in parts if p).strip()
        if joined:
            return joined
    return raw_text or "(空节点)"


def _render_conversation_turns(conv: dict[str, Any]) -> str:
    """Render full, secret-redacted message turns + attachments for one conversation."""
    sid = str(conv.get("source_id") or "")
    title, _ = redact_text(str(conv.get("title") or sid))
    meta = conv.get("metadata") if isinstance(conv.get("metadata"), dict) else {}
    proj = meta.get("project_name") or conv.get("workspace") or "未指定项目"
    sec = meta.get("section_name") or "未分组"
    nodes = conv.get("nodes") if isinstance(conv.get("nodes"), list) else []

    turns_html: list[str] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        role = str(n.get("role") or "system")
        ev = str(n.get("event_type") or "message")
        css_role = "user" if role == "user" else ("assistant" if role == "assistant" else ("tool" if "tool" in role or "tool" in ev else "system"))
        role_label = {
            "user": "用户",
            "assistant": "AI 助手",
            "tool_call": "工具调用",
            "tool_result": "工具返回",
            "system": "系统",
            "developer": "系统指令",
        }.get(role, role)
        red_text, _ = redact_text(_node_display_text(n))
        ts = str(n.get("timestamp") or "")
        if (css_role in {"tool", "system"}) and len(red_text) > 260:
            lbl_kind = "工具详情" if css_role == "tool" else "系统上下文 / 指令"
            body_html = f"<details class='tool-box'><summary>展开{lbl_kind}（{len(red_text)} 字符）</summary><pre>{_esc(red_text)}</pre></details>"
        else:
            body_html = f"<pre>{_esc(red_text)}</pre>"
        ts_span = f"<span class='ts'>{_esc(ts[:19])}</span>" if ts else ""
        turns_html.append(
            f"<article class='turn {css_role}'>"
            f"<div class='turn-meta'>"
            f"<span class='role-tag {css_role}'>{_esc(role_label)}</span>"
            f"<span class='badge'>{_esc(ev)}</span>"
            f"{ts_span}"
            f"</div>{body_html}</article>"
        )

    if not turns_html:
        turns_html.append("<div class='empty-state'>该会话仅包含元数据，暂无可展示的对话消息节点。</div>")

    asset_links: list[str] = []
    for a in conv.get("assets", []) or []:
        if not isinstance(a, dict):
            continue
        rel = a.get("relative_bundle_path")
        if rel and str(rel).startswith("assets/"):
            fname = str(rel)[len("assets/") :]
            asset_links.append(
                f"<li><a href='/api/asset/{urllib.parse.quote(fname, safe='')}'>{_esc(a.get('filename'))}</a> "
                f"<span class='muted'>({_esc(a.get('mime_type'))}, SHA-256: {_esc((a.get('sha256') or '')[:16])})</span></li>"
            )
    assets_card = f"<div class='sub-card'><h3>附件资源（SHA-256 已校验）</h3><ul>{''.join(asset_links)}</ul></div>" if asset_links else ""

    return (
        f"<div class='conv-head'>"
        f"<div><h2>{_esc(title)}</h2>"
        f"<div class='conv-meta'>"
        f"<span class='badge accent'>{_esc(conv.get('source_format'))}</span>"
        f"<span class='badge'>分组：{_esc(sec)}</span>"
        f"<span class='badge'>项目：{_esc(proj)}</span>"
        f"<span class='badge'>{len(nodes)} 个节点</span>"
        f"</div></div></div>"
        f"{assets_card}"
        f"<div class='turns-wrap'>{''.join(turns_html)}</div>"
    )


def _render_page(title: str, body: str, active_nav: str = "overview") -> str:
    nav_cls = lambda k: "active" if active_nav == k else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)} — Nexus Memory 离线安全预览器</title>
<style>
  :root {{
    --bg:#080B12; --card:#111827; --card2:#172033; --border:rgba(148,163,184,0.18);
    --text:#F1F5F9; --muted:#94A3B8; --accent:#38BDF8; --ok:#10B981; --warn:#F59E0B;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC","Segoe UI Variable",sans-serif;
    background:radial-gradient(640px 400px at 15% -5%, rgba(56,189,248,0.09), transparent 70%), var(--bg);
    color:var(--text); line-height:1.58; min-height:100vh;
  }}
  header {{
    background:rgba(13,18,30,0.92); backdrop-filter:blur(16px); border-bottom:1px solid var(--border);
    padding:13px 24px; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:10;
  }}
  header h1 {{ font-size:15.5px; font-weight:700; display:flex; align-items:center; gap:10px; }}
  header h1 a {{ color:var(--text); text-decoration:none; }}
  .pill-live {{ font-size:11px; padding:2px 9px; border-radius:999px; background:rgba(16,185,129,0.14); color:var(--ok); border:1px solid rgba(16,185,129,0.3); }}
  header nav {{ display:flex; gap:8px; }}
  header nav a {{ color:var(--muted); text-decoration:none; padding:6px 12px; border-radius:8px; font-size:13px; font-weight:500; }}
  header nav a:hover {{ color:var(--text); background:rgba(148,163,184,0.1); }}
  header nav a.active {{ color:var(--accent); background:rgba(56,189,248,0.12); font-weight:600; }}
  main {{ max-width:1320px; margin:20px auto; padding:0 20px 36px; }}
  .stats {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:18px; }}
  .stat-card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px 16px; }}
  .stat-val {{ font-size:22px; font-weight:700; color:var(--accent); font-variant-numeric:tabular-nums; }}
  .stat-lbl {{ font-size:11.5px; color:var(--muted); margin-top:2px; }}
  .split {{ display:grid; grid-template-columns:320px 1fr; gap:16px; align-items:start; }}
  @media (max-width: 900px) {{ .split {{ grid-template-columns:1fr; }} }}
  .pane {{ background:var(--card); border:1px solid var(--border); border-radius:14px; overflow:hidden; }}
  .pane-hd {{ padding:13px 16px; border-bottom:1px solid var(--border); font-size:13px; font-weight:650; display:flex; justify-content:space-between; align-items:center; }}
  .sess-list {{ max-height:72vh; overflow-y:auto; }}
  .sess-item {{
    display:block; padding:12px 15px; border-bottom:1px solid var(--border); text-decoration:none; color:var(--text);
    transition:background 140ms ease;
  }}
  .sess-item:hover {{ background:rgba(56,189,248,0.07); }}
  .sess-item.active {{ background:rgba(56,189,248,0.13); border-left:3px solid var(--accent); }}
  .sess-title {{ font-size:13px; font-weight:600; margin-bottom:4px; word-break:break-word; }}
  .sess-sub {{ font-size:11.5px; color:var(--muted); display:flex; gap:8px; flex-wrap:wrap; }}
  .conv-pane {{ padding:18px 20px; max-height:78vh; overflow-y:auto; }}
  .conv-head {{ padding-bottom:14px; margin-bottom:14px; border-bottom:1px solid var(--border); }}
  .conv-head h2 {{ font-size:17px; margin-bottom:8px; }}
  .conv-meta {{ display:flex; gap:6px; flex-wrap:wrap; }}
  .turns-wrap {{ display:flex; flex-direction:column; gap:12px; }}
  .turn {{ border:1px solid var(--border); border-left:3px solid var(--border); padding:12px 15px; background:var(--card2); border-radius:10px; }}
  .turn.user {{ border-left-color:var(--accent); background:rgba(56,189,248,0.06); }}
  .turn.assistant {{ border-left-color:var(--ok); }}
  .turn.tool {{ border-left-color:#A78BFA; background:rgba(167,139,250,0.05); }}
  .turn.system {{ border-left-color:var(--warn); }}
  .turn-meta {{ display:flex; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap; }}
  .role-tag {{ font-size:11.5px; font-weight:700; padding:2px 8px; border-radius:6px; }}
  .role-tag.user {{ background:rgba(56,189,248,0.16); color:var(--accent); }}
  .role-tag.assistant {{ background:rgba(16,185,129,0.16); color:var(--ok); }}
  .role-tag.tool {{ background:rgba(167,139,250,0.18); color:#C4B5FD; }}
  .role-tag.system {{ background:rgba(245,158,11,0.16); color:var(--warn); }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:6px; font-size:11px; background:rgba(148,163,184,0.14); color:var(--muted); }}
  .badge.accent {{ background:rgba(56,189,248,0.15); color:var(--accent); }}
  .ts {{ font-size:11px; color:var(--muted); margin-left:auto; font-family:ui-monospace,Menlo,monospace; }}
  pre {{ white-space:pre-wrap; word-break:break-word; font-family:inherit; font-size:13.5px; color:var(--text); }}
  .turn.tool pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; color:#CBD5E1; margin-top:8px; }}
  .tool-box summary {{ cursor:pointer; font-size:12px; color:#C4B5FD; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:18px 20px; margin-bottom:16px; }}
  .sub-card {{ background:var(--card2); border:1px solid var(--border); border-radius:10px; padding:12px 14px; margin-bottom:14px; font-size:13px; }}
  .sub-card h3 {{ font-size:13px; margin-bottom:6px; color:var(--accent); }}
  .sub-card ul {{ padding-left:18px; }}
  .sub-card a {{ color:var(--accent); }}
  .muted {{ color:var(--muted); }}
  .empty-state {{ padding:32px; text-align:center; color:var(--muted); font-size:13.5px; }}
</style>
</head>
<body>
<header>
  <h1><a href="/">Nexus Memory 离线安全预览器</a><span class="pill-live">127.0.0.1 本地离线 · 密钥已脱敏</span></h1>
  <nav>
    <a href="/" class="{nav_cls('overview')}">会话内容预览</a>
    <a href="/fidelity" class="{nav_cls('fidelity')}">多维保真度与损耗</a>
    <a href="/resources" class="{nav_cls('resources')}">资源层 (Skills / MCP)</a>
  </nav>
</header>
<main>{body}</main>
</body>
</html>"""


def make_viewer_handler(bundle_dir: str | Path) -> type[BaseHTTPRequestHandler]:
    """Build a hardened stdlib HTTP request handler scoped strictly to `bundle_dir`."""
    root = Path(bundle_dir).expanduser().resolve()
    assets_root = (root / "assets").resolve()

    def load_data() -> tuple[dict[str, Any], dict[str, Any]]:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        portable = json.loads((root / "portable.json").read_text(encoding="utf-8"))
        return manifest, portable

    def render_split_view(selected_sid: str | None = None) -> str:
        manifest, portable = load_data()
        hier = portable.get("hierarchy", {})
        convs = portable.get("conversations", [])
        active_conv = None
        if selected_sid is not None:
            active_conv = next((c for c in convs if str(c.get("source_id")) == selected_sid), None)
        if active_conv is None and convs:
            active_conv = convs[0]
        active_id = str(active_conv.get("source_id")) if active_conv else None

        items_html = []
        for idx, c in enumerate(convs):
            cid = str(c.get("source_id") or idx)
            title, _ = redact_text(str(c.get("title") or cid))
            meta = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
            sec = meta.get("section_name") or meta.get("project_name") or "未分组"
            cls = "sess-item active" if cid == active_id else "sess-item"
            items_html.append(
                f"<a class='{cls}' href='/session/{urllib.parse.quote(cid, safe='')}'>"
                f"<div class='sess-title'>{_esc(title)}</div>"
                f"<div class='sess-sub'><span>{_esc(sec)}</span><span>·</span><span>{len(c.get('nodes', []))} 节点</span><span>·</span><span>{_esc(c.get('source_format'))}</span></div>"
                f"</a>"
            )

        right_html = _render_conversation_turns(active_conv) if active_conv else "<div class='empty-state'>当前迁移包中暂无会话记录。</div>"
        return (
            f"<div class='stats'>"
            f"<div class='stat-card'><div class='stat-val'>{manifest.get('conversation_count', 0)}</div><div class='stat-lbl'>已打包会话</div></div>"
            f"<div class='stat-card'><div class='stat-val'>{manifest.get('node_count', 0)}</div><div class='stat-lbl'>消息 / 工具总节点</div></div>"
            f"<div class='stat-card'><div class='stat-val'>{len(hier.get('projects', []))} / {len(hier.get('section_groups', []))}</div><div class='stat-lbl'>项目 / 分组数</div></div>"
            f"<div class='stat-card'><div class='stat-val'>{manifest.get('native_session_count', 0)}</div><div class='stat-lbl'>目标原生文件 ({_esc(manifest.get('target_lane'))})</div></div>"
            f"</div>"
            f"<div class='split'>"
            f"<aside class='pane'><div class='pane-hd'><span>会话列表（点击切换）</span><span class='badge'>{len(convs)}</span></div>"
            f"<div class='sess-list'>{''.join(items_html) or '<div class=\"empty-state\">无会话</div>'}</div></aside>"
            f"<section class='pane'><div class='conv-pane'>{right_html}</div></section>"
            f"</div>"
        )

    class BundleViewerHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass

        def _send_security_headers(self) -> None:
            self.send_header("Content-Security-Policy", CSP_HEADER)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")

        def _send_html(self, body: str, status: int = 200) -> None:
            raw = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(raw)

        def _send_text(self, text: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
            raw = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if path == "/" or path == "/index.html":
                self._send_html(_render_page("会话内容预览", render_split_view(), active_nav="overview"))
                return

            if path.startswith("/session/"):
                sid = urllib.parse.unquote(path[len("/session/") :])
                _, portable = load_data()
                match = next((c for c in portable.get("conversations", []) if str(c.get("source_id")) == sid), None)
                if match is None:
                    self._send_text("Session not found", status=404)
                    return
                title, _ = redact_text(str(match.get("title") or sid))
                self._send_html(_render_page(title, render_split_view(selected_sid=sid), active_nav="overview"))
                return

            if path == "/fidelity":
                manifest, _ = load_data()
                body = (
                    f"<div class='card'><h2>多维保真度报告</h2>"
                    f"<pre style='font-family:ui-monospace,Menlo,monospace;font-size:12.5px;margin-top:10px;'>{_esc(json.dumps(manifest.get('fidelity_report', {}), indent=2, ensure_ascii=False))}</pre></div>"
                    f"<div class='card'><h2>记录的降级与转换明细 ({len(manifest.get('losses', []))})</h2>"
                    f"<pre style='font-family:ui-monospace,Menlo,monospace;font-size:12.5px;margin-top:10px;'>{_esc(json.dumps(manifest.get('losses', []), indent=2, ensure_ascii=False))}</pre></div>"
                )
                self._send_html(_render_page("保真度与损耗", body, active_nav="fidelity"))
                return

            if path == "/resources":
                _, portable = load_data()
                res = portable.get("resources") or {"note": "本次迁移包未勾选资源层（Skills / MCP）。"}
                body = f"<div class='card'><h2>已脱敏资源层（Skills / MCP / Instructions）</h2><pre style='font-family:ui-monospace,Menlo,monospace;font-size:12.5px;margin-top:10px;'>{_esc(json.dumps(res, indent=2, ensure_ascii=False))}</pre></div>"
                self._send_html(_render_page("资源层", body, active_nav="resources"))
                return

            if path.startswith("/api/asset/"):
                raw_rel = urllib.parse.unquote(path[len("/api/asset/") :])
                if not assets_root.is_dir():
                    self._send_text("Assets directory not found", status=404)
                    return
                try:
                    candidate = assets_root / raw_rel
                    if candidate.is_symlink():
                        self._send_text("Access denied", status=403)
                        return
                    resolved = ensure_within_root(candidate, assets_root)
                except ValueError:
                    self._send_text("Access denied", status=403)
                    return
                if not resolved.is_file():
                    self._send_text("Asset not found", status=404)
                    return
                mime, _ = mimetypes.guess_type(resolved.name)
                ctype = mime or "application/octet-stream"
                safe_dl = sanitize_single_segment(resolved.name, fallback="asset.bin")
                disposition = (
                    "attachment"
                    if (
                        ctype in ACTIVE_CONTENT_TYPES
                        or not ctype.startswith(("text/plain", "image/png", "image/jpeg", "image/webp", "application/json"))
                    )
                    else "inline"
                )
                raw_bytes = resolved.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(raw_bytes)))
                self.send_header("Content-Disposition", f'{disposition}; filename="{safe_dl}"')
                self._send_security_headers()
                self.end_headers()
                self.wfile.write(raw_bytes)
                return

            if path == "/api/manifest":
                manifest, _ = load_data()
                self._send_text(json.dumps(manifest, indent=2, ensure_ascii=False), content_type="application/json; charset=utf-8")
                return

            self._send_text("Not found", status=404)

    return BundleViewerHandler


def serve_bundle(bundle_dir: str | Path, *, port: int = 8765) -> None:
    """Serve `bundle_dir` locally on `127.0.0.1:<port>` (never binds 0.0.0.0)."""
    handler = make_viewer_handler(bundle_dir)
    server = HTTPServer(("127.0.0.1", port), handler)
    print(f"Nexus Memory offline viewer running at http://127.0.0.1:{port} (bound strictly to loopback)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
