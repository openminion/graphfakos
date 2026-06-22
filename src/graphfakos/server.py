"""Reusable local graph viewer server primitives."""

from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlparse
import webbrowser

RenderPath = Callable[[str, dict[str, list[str]]], str]


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
            html = render_path(parsed.path, parse_qs(parsed.query))
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
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
    default_path: str = "/explore",
    host: str = "127.0.0.1",
    port: int = 8767,
    open_browser: bool = False,
) -> LocalViewerServerResult:
    server = make_local_viewer_server(
        render_path=render_path,
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
    "RenderPath",
    "make_local_viewer_server",
    "serve_local_viewer",
]
