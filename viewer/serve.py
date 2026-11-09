"""Tiny local 3D model viewer server.

Serves the project folder plus /api/models, a JSON list of every .stl/.obj
under it with modification times, so the page can auto-reload changed models.

Usage: python3 viewer/serve.py [port]
"""
import json
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTS = {".stl", ".obj"}
SKIP_DIRS = {".venv", "node_modules", ".git", "viewer"}


def read_settings(model: Path):
    """Optional print settings sidecar: <model name>.settings.json (shared by .stl/.3mf)."""
    side = model.with_suffix(".settings.json")
    try:
        return json.loads(side.read_text())
    except (OSError, ValueError):
        return None


def list_models():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in EXTS:
                st = p.stat()
                out.append({
                    "path": p.relative_to(ROOT).as_posix(),
                    "mtime": st.st_mtime,
                    "size": st.st_size,
                    "settings": read_settings(p),
                })
    out.sort(key=lambda m: m["mtime"], reverse=True)
    return out


FOCUS = ROOT / "viewer" / "focus.json"


def read_focus():
    """Optional list of paths the page should show (written by whoever is editing)."""
    try:
        data = json.loads(FOCUS.read_text())
        return {"mtime": FOCUS.stat().st_mtime, "show": data.get("show", []),
                "arrange": data.get("arrange"), "explode": data.get("explode"),
                "offsets": data.get("offsets")}
    except (OSError, ValueError):
        return None


def read_trackers():
    """Every <project>/tracker.json: what the user has provided and what's still needed."""
    out = []
    for t in sorted(ROOT.glob("*/tracker.json")):
        if t.parent.name.startswith(".") or t.parent.name in SKIP_DIRS:
            continue
        try:
            data = json.loads(t.read_text())
        except (OSError, ValueError):
            continue
        data["dir"] = t.parent.name
        out.append(data)
    return out


class Handler(SimpleHTTPRequestHandler):
    def _allowed(self):
        """Read-only, local-only: refuse other hosts (DNS rebinding) and hidden paths."""
        host = self.headers.get("Host", "").rsplit(":", 1)[0].strip("[]")
        if host not in ("localhost", "127.0.0.1", "::1"):
            self.send_error(403)
            return False
        if any(part.startswith(".") for part in self.path.split("?")[0].split("/")):
            self.send_error(404)   # .git, .venv, pid/log files
            return False
        return True

    def do_HEAD(self):
        if self._allowed():
            super().do_HEAD()

    def do_GET(self):
        if not self._allowed():
            return
        if self.path.split("?")[0] == "/api/tracker":
            page = (ROOT / "viewer" / "tracker.html").stat().st_mtime
            body = json.dumps({"projects": read_trackers(), "page": page}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.split("?")[0] in ("/tracker", "/tracker/"):
            self.path = "/viewer/tracker.html"
        if self.path.split("?")[0] == "/api/models":
            page = (ROOT / "viewer" / "index.html").stat().st_mtime  # page reloads itself when this changes
            body = json.dumps({"models": list_models(), "focus": read_focus(), "page": page}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in ("/", "/index.html"):
            self.path = "/viewer/index.html"
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(ROOT)))
    print(f"Viewer running at http://localhost:{port}/", flush=True)
    server.serve_forever()
