#!/usr/bin/env python3
"""Build a native, self-contained macOS `Nexus Memory.app` bundle (Swift AppKit + WKWebView + custom .icns icon).

Bundles:
- `Contents/MacOS/nexus-memory-app`: Compiled native Swift/AppKit + WKWebView macOS binary
  (dark unified full-size titlebar, native `NSOpenPanel` file/folder picker bridge, native `⌘Q/⌘W/⌘R` menu,
  plus `--self-test` and `--cli ...` zero-GUI passthrough).
- `Contents/Resources/AppIcon.icns`: High-res futuristic Obsidian Neural macOS app icon (generated via `iconutil`).
- `Contents/Resources/app/nexus_memory/`: Self-contained pure-stdlib Python package.
- `Contents/Resources/backend_entry.py`: Local `127.0.0.1` desktop backend entrypoint.
- Ad-hoc `codesign --force --deep --sign -` for clean local macOS execution.
"""

from __future__ import annotations

import argparse
import math
import plistlib
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

SWIFT_HOST_SRC = r"""
import Cocoa
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, NSWindowDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var backendProcess: Process?
    var backendURL: URL?

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMenu()
        startBackendAndOpenWindow()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        if let proc = backendProcess, proc.isRunning {
            proc.terminate()
        }
    }

    private func setupMenu() {
        let mainMenu = NSMenu()
        let appItem = NSMenuItem()
        mainMenu.addItem(appItem)
        let appMenu = NSMenu()
        appMenu.addItem(NSMenuItem(title: "Quit Nexus Memory", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        appItem.submenu = appMenu

        let editItem = NSMenuItem()
        mainMenu.addItem(editItem)
        let editMenu = NSMenu(title: "Edit")
        editMenu.addItem(NSMenuItem(title: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x"))
        editMenu.addItem(NSMenuItem(title: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c"))
        editMenu.addItem(NSMenuItem(title: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v"))
        editMenu.addItem(NSMenuItem(title: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a"))
        editItem.submenu = editMenu

        let winItem = NSMenuItem()
        mainMenu.addItem(winItem)
        let winMenu = NSMenu(title: "Window")
        winMenu.addItem(NSMenuItem(title: "Close", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w"))
        winMenu.addItem(NSMenuItem(title: "Minimize", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m"))
        winItem.submenu = winMenu

        NSApp.mainMenu = mainMenu
    }

    private func resolvePythonAndBackend() -> (String, String) {
        let resPath = Bundle.main.resourcePath ?? (CommandLine.arguments[0] as NSString).deletingLastPathComponent + "/../Resources"
        let backendScript = (resPath as NSString).appendingPathComponent("backend_entry.py")
        let envPy = ProcessInfo.processInfo.environment["NEXUS_MEMORY_PYTHON"] ?? ""
        let candidates = [envPy, "__PYTHON_BIN__", "/opt/anaconda3/bin/python3", "/opt/homebrew/bin/python3", "/usr/bin/python3"]
        for c in candidates where !c.isEmpty {
            if FileManager.default.isExecutableFile(atPath: c) {
                return (c, backendScript)
            }
        }
        return ("/usr/bin/python3", backendScript)
    }

    private func startBackendAndOpenWindow() {
        let (pyBin, backendScript) = resolvePythonAndBackend()
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: pyBin)
        proc.arguments = [backendScript, "--server-only"]
        var env = ProcessInfo.processInfo.environment
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc.environment = env

        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = FileHandle.nullDevice

        do {
            try proc.run()
            self.backendProcess = proc
        } catch {
            showFatalAlert("无法启动 Nexus Memory 本地引擎: \(error.localizedDescription)")
            return
        }

        let handle = pipe.fileHandleForReading
        var buffer = Data()
        var foundURL: String? = nil
        let deadline = Date().addingTimeInterval(8.0)
        while Date() < deadline {
            let chunk = handle.availableData
            if chunk.isEmpty { break }
            buffer.append(chunk)
            if let str = String(data: buffer, encoding: .utf8), let nl = str.firstIndex(of: "\n") {
                let firstLine = String(str[..<nl])
                if let d = firstLine.data(using: .utf8),
                   let obj = try? JSONSerialization.jsonObject(with: d) as? [String: Any],
                   let u = obj["url"] as? String {
                    foundURL = u
                    break
                }
            }
        }

        guard let urlStr = foundURL, let url = URL(string: urlStr) else {
            showFatalAlert("本地后端启动超时，请确认本机 Python 3.11+ 可用。")
            return
        }
        self.backendURL = url
        createMainWindow(url: url)
    }

    private func createMainWindow(url: URL) {
        let rect = NSRect(x: 0, y: 0, width: 1260, height: 820)
        let style: NSWindow.StyleMask = [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView]
        window = NSWindow(contentRect: rect, styleMask: style, backing: .buffered, defer: false)
        window.title = "Nexus Memory"
        window.titleVisibility = .hidden
        window.titlebarAppearsTransparent = true
        window.isMovableByWindowBackground = true
        window.minSize = NSSize(width: 980, height: 640)
        window.backgroundColor = NSColor(calibratedRed: 0.031, green: 0.043, blue: 0.071, alpha: 1.0)
        window.appearance = NSAppearance(named: .darkAqua)
        window.delegate = self
        window.center()

        let cfg = WKWebViewConfiguration()
        cfg.userContentController.add(self, name: "nexusNative")
        webView = WKWebView(frame: window.contentView!.bounds, configuration: cfg)
        webView.autoresizingMask = [.width, .height]
        webView.setValue(false, forKey: "drawsBackground")
        webView.navigationDelegate = self
        window.contentView?.addSubview(webView)
        webView.load(URLRequest(url: url))

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "nexusNative",
              let body = message.body as? [String: Any],
              let action = body["action"] as? String, action == "pick" else { return }
        let mode = (body["mode"] as? String) ?? "file"
        let panel = NSOpenPanel()
        panel.canChooseFiles = (mode != "dir")
        panel.canChooseDirectories = (mode == "dir")
        panel.allowsMultipleSelection = false
        panel.beginSheetModal(for: window) { resp in
            let picked = (resp == .OK) ? (panel.url?.path ?? "") : ""
            if let encoded = try? JSONSerialization.data(withJSONObject: [picked]),
               let arrStr = String(data: encoded, encoding: .utf8) {
                self.webView.evaluateJavaScript("window.__nexusNativePicked((\(arrStr))[0])", completionHandler: nil)
            }
        }
    }

    private func showFatalAlert(_ msg: String) {
        let alert = NSAlert()
        alert.messageText = "Nexus Memory"
        alert.informativeText = msg
        alert.alertStyle = .critical
        alert.runModal()
        NSApp.terminate(nil)
    }
}

// Fast zero-GUI CLI / --self-test passthrough
let cliArgs = Array(CommandLine.arguments.dropFirst())
if let first = cliArgs.first, first == "--self-test" || first == "--cli" || first.hasPrefix("-") {
    let resPath = Bundle.main.resourcePath ?? ((CommandLine.arguments[0] as NSString).deletingLastPathComponent + "/../Resources")
    let backendScript = (resPath as NSString).appendingPathComponent("backend_entry.py")
    let envPy = ProcessInfo.processInfo.environment["NEXUS_MEMORY_PYTHON"] ?? ""
    let candidates = [envPy, "__PYTHON_BIN__", "/opt/anaconda3/bin/python3", "/opt/homebrew/bin/python3", "/usr/bin/python3"]
    let pyBin = candidates.first { !$0.isEmpty && FileManager.default.isExecutableFile(atPath: $0) } ?? "/usr/bin/python3"
    let p = Process()
    p.executableURL = URL(fileURLWithPath: pyBin)
    p.arguments = [backendScript] + cliArgs
    var cliEnv = ProcessInfo.processInfo.environment
    cliEnv["PYTHONDONTWRITEBYTECODE"] = "1"
    p.environment = cliEnv
    p.standardInput = FileHandle.standardInput
    p.standardOutput = FileHandle.standardOutput
    p.standardError = FileHandle.standardError
    try? p.run()
    p.waitUntilExit()
    exit(p.terminationStatus)
}

let app = NSApplication.shared
app.setActivationPolicy(.regular)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
"""

BACKEND_ENTRY_PY = """#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

sys.dont_write_bytecode = True
APP_DIR = Path(__file__).resolve().parent / "app"
if APP_DIR.is_dir() and str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from nexus_memory import __version__
from nexus_memory.cli import main as cli_main
from nexus_memory.desktop_ui import launch_desktop


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--self-test":
        print(json.dumps({
            "app": "Nexus Memory.app",
            "version": __version__,
            "ui_engine": "Native Swift AppKit + WKWebView (Obsidian Neural Console)",
            "bundled_package_dir": str(APP_DIR),
            "self_test": "ok",
        }, ensure_ascii=False))
        return 0
    if args and args[0] == "--cli":
        return cli_main(args[1:])
    if args and args[0] != "--server-only" and not args[0].startswith("--port"):
        return cli_main(args)
    return launch_desktop(args)


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _write_png_rgba(path: Path, size: int, pixels: bytearray) -> None:
    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw = bytearray()
    stride = size * 4
    for y in range(size):
        raw.append(0)
        raw.extend(pixels[y * stride : (y + 1) * stride])
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def _generate_icns(dst_icns: Path) -> bool:
    """Generate a crisp futuristic Obsidian Neural macOS .icns icon using pure Python + sips/iconutil."""
    if not shutil.which("sips") or not shutil.which("iconutil"):
        return False
    size = 512
    buf = bytearray(size * size * 4)
    cx = cy = size / 2.0
    # 3 neural node positions (triangle)
    nodes = [(size * 0.31, size * 0.35), (size * 0.69, size * 0.35), (size * 0.50, size * 0.69)]
    edges = [(nodes[0], nodes[1]), (nodes[0], nodes[2]), (nodes[1], nodes[2])]

    def dist_seg(px: float, py: float, a: tuple[float, float], b: tuple[float, float]) -> float:
        vx, vy = b[0] - a[0], b[1] - a[1]
        wx, wy = px - a[0], py - a[1]
        c1 = wx * vx + wy * vy
        if c1 <= 0:
            return math.hypot(px - a[0], py - a[1])
        c2 = vx * vx + vy * vy
        if c2 <= c1:
            return math.hypot(px - b[0], py - b[1])
        t = c1 / c2
        return math.hypot(px - (a[0] + t * vx), py - (a[1] + t * vy))

    pad = size * 0.08
    rad = size * 0.21
    for y in range(size):
        for x in range(size):
            # Rounded squircle mask
            dx = max(abs(x - cx) - (size / 2.0 - pad - rad), 0.0)
            dy = max(abs(y - cy) - (size / 2.0 - pad - rad), 0.0)
            sd = math.hypot(dx, dy) - rad
            if sd > 1.5:
                continue
            alpha = max(0.0, min(1.0, 1.0 - sd))
            u, v = x / size, y / size
            # Deep obsidian + subtle cyan/indigo aurora gradient
            r = 10 + 16 * u + 22 * (1.0 - v)
            g = 15 + 22 * (1.0 - v) + 12 * u
            b = 28 + 44 * u + 32 * (1.0 - v)

            # Luminous outer ring glow
            ring = abs(sd + 4.0)
            if ring < 5.0:
                gl = (1.0 - ring / 5.0) * 0.55
                r += 56 * gl
                g += 189 * gl
                b += 248 * gl

            # Neural edges glow
            for a, bpt in edges:
                d = dist_seg(x, y, a, bpt)
                if d < 18.0:
                    w = max(0.0, 1.0 - d / 18.0) ** 2
                    r += 75 * w
                    g += 175 * w
                    b += 255 * w
                if d < 7.5:
                    r, g, b = 220, 245, 255

            # Neural nodes
            for nx, ny in nodes:
                dn = math.hypot(x - nx, y - ny)
                if dn < 46.0:
                    w = max(0.0, 1.0 - dn / 46.0) ** 1.8
                    r += 56 * w
                    g += 189 * w
                    b += 248 * w
                if dn < 24.0:
                    r, g, b = 56, 189, 248
                if dn < 13.0:
                    r, g, b = 245, 250, 255

            off = (y * size + x) * 4
            buf[off] = min(255, int(r))
            buf[off + 1] = min(255, int(g))
            buf[off + 2] = min(255, int(b))
            buf[off + 3] = min(255, int(alpha * 255))

    with tempfile.TemporaryDirectory(prefix="nexus_icns_") as td:
        tdir = Path(td)
        base_png = tdir / "base_512.png"
        _write_png_rgba(base_png, size, buf)
        iconset = tdir / "AppIcon.iconset"
        iconset.mkdir()
        for px, name in [
            (16, "icon_16x16.png"),
            (32, "icon_16x16@2x.png"),
            (32, "icon_32x32.png"),
            (64, "icon_32x32@2x.png"),
            (128, "icon_128x128.png"),
            (256, "icon_128x128@2x.png"),
            (256, "icon_256x256.png"),
            (512, "icon_256x256@2x.png"),
            (512, "icon_512x512.png"),
        ]:
            subprocess.run(["sips", "-z", str(px), str(px), str(base_png), "--out", str(iconset / name)], check=True, capture_output=True)
        res = subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(dst_icns)], capture_output=True)
        return res.returncode == 0 and dst_icns.is_file()


def build_macos_app(repo_root: Path, out_dir: Path, *, adhoc_sign: bool = True) -> Path:
    app_path = out_dir / "Nexus Memory.app"
    if app_path.exists():
        shutil.rmtree(app_path)

    contents = app_path / "Contents"
    macos_dir = contents / "MacOS"
    res_dir = contents / "Resources"
    pkg_dst = res_dir / "app" / "nexus_memory"
    macos_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy pure-stdlib nexus_memory package cleanly
    shutil.copytree(
        repo_root / "src" / "nexus_memory",
        pkg_dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    # 2. Write backend_entry.py
    backend_py = res_dir / "backend_entry.py"
    backend_py.write_text(BACKEND_ENTRY_PY, encoding="utf-8")
    backend_py.chmod(0o755)

    # 3. Generate custom macOS AppIcon.icns
    has_icon = _generate_icns(res_dir / "AppIcon.icns")

    # 4. Compile native Swift AppKit + WKWebView binary (fallback to shell wrapper if swiftc absent)
    bin_path = macos_dir / "nexus-memory-app"
    swiftc = shutil.which("swiftc")
    if sys.platform == "darwin" and swiftc:
        with tempfile.TemporaryDirectory(prefix="nexus_swift_") as td:
            src_file = Path(td) / "main.swift"
            src_file.write_text(SWIFT_HOST_SRC.replace("__PYTHON_BIN__", sys.executable), encoding="utf-8")
            subprocess.run(
                [swiftc, "-O", str(src_file), "-o", str(bin_path), "-framework", "Cocoa", "-framework", "WebKit"],
                check=True,
            )
    else:
        bin_script = f'#!/usr/bin/env sh\nset -eu\nDIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec env PYTHONDONTWRITEBYTECODE=1 "{sys.executable}" "$DIR/../Resources/backend_entry.py" "$@"\n'
        bin_path.write_text(bin_script, encoding="utf-8")
    bin_path.chmod(bin_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Read canonical version from src/nexus_memory/__init__.py
    sys.path.insert(0, str(repo_root / "src"))
    from nexus_memory import __version__ as app_version

    # 5. Write Info.plist
    plist_data = {
        "CFBundleName": "Nexus Memory",
        "CFBundleDisplayName": "Nexus Memory",
        "CFBundleIdentifier": "io.nexusmemory.desktop",
        "CFBundleVersion": app_version,
        "CFBundleShortVersionString": app_version,
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "nexus-memory-app",
        "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.developer-tools",
        **({"CFBundleIconFile": "AppIcon"} if has_icon else {}),
    }
    with (contents / "Info.plist").open("wb") as pf:
        plistlib.dump(plist_data, pf)

    # 6. Ad-hoc codesign on macOS
    if adhoc_sign and sys.platform == "darwin" and shutil.which("codesign"):
        subprocess.run(
            ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
            check=True,
            capture_output=True,
        )

    return app_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build native macOS Nexus Memory.app bundle")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "dist")
    parser.add_argument("--no-sign", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    app = build_macos_app(repo_root, args.out_dir.expanduser().resolve(), adhoc_sign=not args.no_sign)
    print(f"Built native macOS app bundle: {app}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
