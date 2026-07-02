"""Reusable local graph viewer server primitives."""

from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Callable
from urllib.parse import parse_qs, urlparse
import webbrowser

RenderPath = Callable[[str, dict[str, list[str]]], str]
ActionHandler = Callable[[str, dict[str, object]], dict[str, object]]
_MAX_ACTION_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class LocalViewerServerResult:
    url: str
    host: str
    port: int
    opened: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "url": self.url,
            "host": self.host,
            "port": self.port,
            "opened": self.opened,
        }


class LocalViewerHttpServer(ThreadingHTTPServer):
    preview_url: str


def make_local_viewer_server(
    *,
    render_path: RenderPath,
    render_fragment_path: RenderPath | None = None,
    handle_action: ActionHandler | None = None,
    default_path: str = "/explore",
    host: str = "127.0.0.1",
    port: int = 8767,
) -> LocalViewerHttpServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            route = parsed.path
            if parsed.query:
                route = f"{route}?{parsed.query}"
            if (
                render_fragment_path is not None
                and self.headers.get("X-GraphFakos-Fragment") == "1"
            ):
                fragment = render_fragment_path(parsed.path, query)
                body = json.dumps(
                    {
                        "kind": "graphfakos.fragment",
                        "route": route,
                        "fragment": fragment,
                    },
                    sort_keys=True,
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            html = render_path(parsed.path, query)
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if handle_action is None:
                self._send_json(
                    501,
                    {
                        "ok": False,
                        "error": "this GraphFakos preview does not support actions",
                    },
                )
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(
                    400,
                    {"ok": False, "error": "Content-Length must be numeric"},
                )
                return
            if content_length <= 0 or content_length > _MAX_ACTION_BYTES:
                self._send_json(
                    413,
                    {"ok": False, "error": "request body is empty or too large"},
                )
                return
            try:
                raw_payload = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(raw_payload)
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(400, {"ok": False, "error": "body must be JSON"})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"ok": False, "error": "body must be an object"})
                return
            try:
                result = handle_action(parsed.path, payload)
            except (TypeError, ValueError) as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
                return
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})
                return
            self._send_json(200, result)

        def _send_json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = LocalViewerHttpServer((host, port), Handler)
    bound_host, bound_port = server.server_address
    server.preview_url = f"http://{bound_host}:{bound_port}{default_path}"
    return server


def serve_local_viewer(
    *,
    render_path: RenderPath,
    render_fragment_path: RenderPath | None = None,
    handle_action: ActionHandler | None = None,
    default_path: str = "/explore",
    host: str = "127.0.0.1",
    port: int = 8767,
    open_browser: bool = False,
) -> LocalViewerServerResult:
    server = make_local_viewer_server(
        render_path=render_path,
        render_fragment_path=render_fragment_path,
        handle_action=handle_action,
        default_path=default_path,
        host=host,
        port=port,
    )
    opened = webbrowser.open(server.preview_url) if open_browser else False
    print(f"Serving GraphFakos viewer at {server.preview_url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    bound_host, bound_port = server.server_address
    return LocalViewerServerResult(
        url=server.preview_url,
        host=str(bound_host),
        port=int(bound_port),
        opened=opened,
    )


__all__ = [
    "LocalViewerHttpServer",
    "LocalViewerServerResult",
    "ActionHandler",
    "RenderPath",
    "make_local_viewer_server",
    "serve_local_viewer",
]
