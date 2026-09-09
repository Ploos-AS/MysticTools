from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .metrics import metrics_snapshot, render_prometheus

DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 9108


class ExporterServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, *, root: Path):
        super().__init__(server_address, handler_class)
        self.root = root.resolve()


class ExporterHandler(BaseHTTPRequestHandler):
    server_version = "MysticToolsExporter/0"

    def log_message(self, format: str, *args) -> None:
        # Keep the exporter quiet by default; service managers can monitor
        # process state without per-scrape access-log noise.
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _snapshot(self) -> dict:
        return metrics_snapshot(self.server.root)  # type: ignore[attr-defined]

    def _handle_metrics(self) -> None:
        try:
            body = render_prometheus(self._snapshot()).encode("utf-8")
        except Exception as exc:
            payload = {"ok": False, "error": type(exc).__name__}
            self._send(503, (json.dumps(payload) + "\n").encode("utf-8"), "application/json; charset=utf-8")
            return
        self._send(200, body, "text/plain; version=0.0.4; charset=utf-8")

    def _handle_health(self) -> None:
        try:
            snapshot = self._snapshot()
            payload = {
                "ok": True,
                "root": str(self.server.root),  # type: ignore[attr-defined]
                "health": snapshot.get("health"),
                "metrics_schema_version": snapshot.get("schema_version"),
            }
            status = 200
        except Exception as exc:
            payload = {"ok": False, "error": type(exc).__name__}
            status = 503
        self._send(status, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"), "application/json; charset=utf-8")

    def _dispatch(self) -> None:
        path = urlsplit(self.path).path
        if path == "/metrics":
            self._handle_metrics()
        elif path == "/healthz":
            self._handle_health()
        else:
            self._send(404, b"not found\n", "text/plain; charset=utf-8")

    def do_GET(self) -> None:
        self._dispatch()

    def do_HEAD(self) -> None:
        self._dispatch()

    def do_POST(self) -> None:
        self._send(405, b"method not allowed\n", "text/plain; charset=utf-8")

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST


def create_server(root: Path, bind: str = DEFAULT_BIND, port: int = DEFAULT_PORT) -> ExporterServer:
    if not 0 <= int(port) <= 65535:
        raise ValueError("port must be between 0 and 65535")
    return ExporterServer((bind, int(port)), ExporterHandler, root=root)


def serve(root: Path, bind: str = DEFAULT_BIND, port: int = DEFAULT_PORT) -> None:
    with create_server(root, bind, port) as server:
        server.serve_forever(poll_interval=0.5)
