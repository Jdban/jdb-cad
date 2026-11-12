"""Tiny local 3D model viewer server.

Serves the project folder plus /api/models, a JSON list of every .stl/.obj/.3mf
under it with modification times, so the page can auto-reload changed models.
Read-only except one thing: POST /api/inbox saves uploaded files into inbox/ (same-origin only).

Usage: python3 viewer/serve.py [port]
"""
import json
import os
import re
import secrets
import sys
from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTS = {".stl", ".obj", ".3mf"}
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
                # kit writes every _print.3mf next to a same-named .stl: list the .stl only.
                # A .3mf on its own (a download, a Bambu project) is listed.
                if p.suffix.lower() == ".3mf" and p.with_suffix(".stl").exists():
                    continue
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
        for key, name in (("parts_md", "PARTS.md"), ("notes_md", "NOTES.md")):   # shown expandable on the page
            try:
                data[key] = (t.parent / name).read_text()
            except OSError:
                data[key] = ""
        out.append(data)
    return out


# Host names the browser may use. Extra names (e.g. a home server's name, behind an auth proxy)
# come from VIEWER_ALLOWED_HOSTS, comma-separated.
ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"} | {
    h.strip() for h in os.environ.get("VIEWER_ALLOWED_HOSTS", "").split(",") if h.strip()}
# Address to listen on. 127.0.0.1 (default) = this machine only. In Docker it must be 0.0.0.0,
# and compose.yaml publishes the port on the host's 127.0.0.1 only.
BIND = os.environ.get("VIEWER_BIND", "127.0.0.1")


# ---- inbox: the ONLY place the server writes -------------------------------------------
# The tracker page posts files (and a note) here; the agent turns them into a project later.
# Every upload is one file: POST /api/inbox?batch=<id>&name=<file name>, raw body.
INBOX = ROOT / "inbox"
INBOX_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".stl", ".3mf", ".obj",
              ".step", ".stp", ".f3d", ".pdf", ".txt", ".md", ".zip", ".mp4", ".mov"}
INBOX_MAX = 200 * 1024 * 1024        # per file
BATCH_RE = re.compile(r"^\d{4}-\d\d-\d\d_\d{6}_[a-z0-9]{4}$")


def safe_name(name: str):
    """A plain file name (no folders, no leading dot), or None."""
    name = name.replace("\\", "/").split("/")[-1].strip()
    name = re.sub(r"[^A-Za-z0-9._ ()+-]", "_", name)[:120]
    if not name or name.startswith(".") or Path(name).suffix.lower() not in INBOX_EXTS:
        return None
    return name


def read_inbox():
    """Batches in the inbox, newest first: [{batch, files: [{name, size}], note}]."""
    out = []
    if INBOX.is_dir():
        for d in sorted(INBOX.iterdir(), reverse=True):
            if not d.is_dir() or not BATCH_RE.match(d.name):
                continue
            files = [{"name": f.name, "size": f.stat().st_size} for f in sorted(d.iterdir())
                     if f.is_file() and f.name != "note.txt" and not f.name.startswith(".")]
            note = (d / "note.txt").read_text() if (d / "note.txt").exists() else ""
            out.append({"batch": d.name, "files": files, "note": note})
    return out


class Handler(SimpleHTTPRequestHandler):
    def _allowed(self):
        """Read-only, local-only: refuse other hosts (DNS rebinding) and hidden paths."""
        host = self.headers.get("Host", "").rsplit(":", 1)[0].strip("[]")
        if host not in ALLOWED_HOSTS:
            self.send_error(403)
            return False
        # decode first: "/%2egit/HEAD" must be treated as "/.git/HEAD"
        path = unquote(self.path.split("?")[0].split("#")[0]).replace("\\", "/")
        if any(part.startswith(".") for part in path.split("/")):
            self.send_error(404)   # .git, .venv, pid/log files
            return False
        return True

    def _same_origin(self):
        """Writes only from our own pages. Other websites can make your browser POST to
        localhost; they can't send a matching Origin, or the X-Inbox header without a CORS
        preflight (which this server never approves)."""
        origin = urlparse(self.headers.get("Origin", ""))
        host = self.headers.get("Host", "")
        return (self.headers.get("X-Inbox") == "1" and origin.scheme in ("http", "https")
                and origin.netloc == host and origin.hostname in ALLOWED_HOSTS)

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not self._allowed():
            return
        route, _, query = self.path.partition("?")
        if route != "/api/inbox":
            self.send_error(404)
            return
        if not self._same_origin():
            self.send_error(403)
            return
        q = parse_qs(query)
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.send_error(411)
            return
        if length > INBOX_MAX:
            self.send_error(413)
            return
        batch = q.get("batch", [""])[0]
        if not batch:   # first file of a send: start a new batch folder
            batch = datetime.now().strftime("%Y-%m-%d_%H%M%S_") + secrets.token_hex(2)
        if not BATCH_RE.match(batch):
            self.send_error(400, "bad batch")
            return
        raw = q.get("name", [""])[0]
        name = "note.txt" if raw == "note.txt" else safe_name(raw)
        if not name:
            self.send_error(415, "file type not accepted")
            return
        folder = INBOX / batch
        folder.mkdir(parents=True, exist_ok=True)
        target, n = folder / name, 1
        while target.exists():   # never overwrite
            target = folder / f"{Path(name).stem} ({n}){Path(name).suffix}"
            n += 1
        tmp = folder / f".part-{secrets.token_hex(4)}"
        try:
            with open(tmp, "wb") as f:
                left = length
                while left > 0:
                    chunk = self.rfile.read(min(left, 1 << 20))
                    if not chunk:
                        raise OSError("upload cut short")
                    f.write(chunk)
                    left -= len(chunk)
            tmp.rename(target)
        except OSError:
            tmp.unlink(missing_ok=True)
            self.send_error(500, "could not save")
            return
        self._json(200, {"batch": batch, "saved": target.name})

    def do_HEAD(self):
        if self._allowed():
            super().do_HEAD()

    def do_GET(self):
        if not self._allowed():
            return
        if self.path.split("?")[0] == "/api/tracker":
            page = (ROOT / "viewer" / "tracker.html").stat().st_mtime
            body = json.dumps({"projects": read_trackers(), "inbox": read_inbox(), "page": page}).encode()
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
        route, _, query = self.path.partition("?")
        if route in ("/", "/index.html"):   # keep ?show=... (tracker "view" links) working
            self.path = "/viewer/index.html" + ("?" + query if query else "")
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = ThreadingHTTPServer((BIND, port), partial(Handler, directory=str(ROOT)))
    print(f"Viewer running at http://localhost:{port}/", flush=True)
    server.serve_forever()
