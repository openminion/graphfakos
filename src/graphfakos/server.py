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
_VIEWER_CONTEXT_FIELD = "viewer_context"


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
                payload = self._parse_action_payload(raw_payload)
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
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
            if self._should_redirect_after_action(result):
                self.send_response(303)
                self.send_header("Location", self._safe_return_path())
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
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

        def _parse_action_payload(self, raw_payload: str) -> dict[str, object]:
            content_type = self.headers.get("Content-Type", "")
            media_type = content_type.split(";", 1)[0].strip().lower()
            if media_type in ("", "application/json"):
                payload = json.loads(raw_payload)
                if not isinstance(payload, dict):
                    raise TypeError("body must be an object")
                return payload
            if media_type == "application/x-www-form-urlencoded":
                fields = parse_qs(raw_payload, keep_blank_values=True)
                return _normalize_form_action_payload(
                    {
                        key: values[-1] if values else ""
                        for key, values in fields.items()
                    }
                )
            raise TypeError("body must be JSON or application/x-www-form-urlencoded")

        def _should_redirect_after_action(
            self,
            payload: dict[str, object],
        ) -> bool:
            if payload.get("ok") is not True:
                return False
            content_type = self.headers.get("Content-Type", "")
            media_type = content_type.split(";", 1)[0].strip().lower()
            if media_type != "application/x-www-form-urlencoded":
                return False
            accept = self.headers.get("Accept", "")
            return "application/json" not in accept.lower()

        def _safe_return_path(self) -> str:
            fallback = default_path if default_path.startswith("/") else "/explore"
            referer = self.headers.get("Referer", "")
            if not referer:
                return fallback
            parsed = urlparse(referer)
            if parsed.path.startswith("/api/") or not parsed.path.startswith("/"):
                return fallback
            if parsed.query:
                return f"{parsed.path}?{parsed.query}"
            return parsed.path or fallback

        def log_message(self, format: str, *args: object) -> None:
            return

    server = LocalViewerHttpServer((host, port), Handler)
    bound_host, bound_port = server.server_address
    server.preview_url = f"http://{bound_host}:{bound_port}{default_path}"
    return server


def _normalize_form_action_payload(payload: dict[str, object]) -> dict[str, object]:
    provider_payload = _form_provider_payload(payload)
    viewer_context = _json_mapping(payload.get(_VIEWER_CONTEXT_FIELD))
    if viewer_context:
        provider_payload = {**provider_payload, _VIEWER_CONTEXT_FIELD: viewer_context}
    if provider_payload:
        payload["provider_payload"] = provider_payload
    return payload


def _form_provider_payload(payload: dict[str, object]) -> dict[str, object]:
    provider_payload = payload.get("provider_payload")
    if isinstance(provider_payload, dict):
        return dict(provider_payload)
    parsed = _json_mapping(provider_payload)
    return parsed if parsed is not None else {}


def _json_mapping(value: object) -> dict[str, object] | None:
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise TypeError("JSON form payload fields must be objects")
    return parsed


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
