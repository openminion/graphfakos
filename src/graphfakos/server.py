"""Reusable local graph viewer server primitives."""

from __future__ import annotations

from dataclasses import dataclass, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from threading import Lock
from typing import Callable, Mapping
from urllib.parse import parse_qs, urlparse
import webbrowser

from .live import (
    GraphFakosGraphPatch,
    GraphFakosLiveProvider,
    GraphFakosLiveSessionCursor,
    GraphFakosLiveSessionDiagnostics,
    GraphFakosLiveSessionRequest,
)

RenderPath = Callable[[str, dict[str, list[str]]], str]
ActionHandler = Callable[[str, dict[str, object]], dict[str, object]]
RequestAuthorizer = Callable[[str, str, Mapping[str, str]], bool]
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
    live_provider: GraphFakosLiveProvider | None
    max_live_clients: int
    _live_clients: int
    _live_lock: Lock
    authorization_rejections: int
    origin_rejections: int

    def acquire_live_client(self) -> bool:
        with self._live_lock:
            if self._live_clients >= self.max_live_clients:
                return False
            self._live_clients += 1
            return True

    def release_live_client(self) -> None:
        with self._live_lock:
            self._live_clients = max(0, self._live_clients - 1)

    def live_diagnostics(self) -> GraphFakosLiveSessionDiagnostics:
        provider_diagnostics = getattr(self.live_provider, "diagnostics", None)
        if callable(provider_diagnostics):
            diagnostics = provider_diagnostics()
        else:
            diagnostics = GraphFakosLiveSessionDiagnostics()
        return replace(
            diagnostics,
            connection_count=self._live_clients,
            authorization_rejection_count=self.authorization_rejections,
            origin_rejection_count=self.origin_rejections,
        )


def make_local_viewer_server(
    *,
    render_path: RenderPath,
    render_fragment_path: RenderPath | None = None,
    handle_action: ActionHandler | None = None,
    default_path: str = "/explore",
    host: str = "127.0.0.1",
    port: int = 8767,
    live_provider: GraphFakosLiveProvider | None = None,
    allow_remote: bool = False,
    authorize_request: RequestAuthorizer | None = None,
    allowed_origins: tuple[str, ...] = (),
    max_live_clients: int = 16,
) -> LocalViewerHttpServer:
    _validate_server_exposure(
        host=host,
        allow_remote=allow_remote,
        authorize_request=authorize_request,
        allowed_origins=allowed_origins,
        max_live_clients=max_live_clients,
    )

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path == "/api/live":
                self._send_live_event(query)
                return
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
            if not self._request_allowed(parsed.path):
                return
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

        def _send_live_event(self, query: dict[str, list[str]]) -> None:
            if live_provider is None:
                self._send_json(501, {"ok": False, "error": "live mode is unavailable"})
                return
            if not self._request_allowed("/api/live"):
                return
            if not self.server.acquire_live_client():
                self._send_json(
                    429, {"ok": False, "error": "live client limit reached"}
                )
                return
            try:
                cursor_value = self.headers.get("Last-Event-ID", "")
                if not cursor_value:
                    cursor_value = (query.get("cursor") or [""])[-1]
                request = GraphFakosLiveSessionRequest(
                    session_id=(query.get("session_id") or ["local"])[-1],
                    cursor=(
                        GraphFakosLiveSessionCursor(cursor_value)
                        if cursor_value
                        else None
                    ),
                )
                live_provider.open_live_session(request)
                event = live_provider.load_patch(request)
                event_name = (
                    "graphfakos.patch"
                    if isinstance(event, GraphFakosGraphPatch)
                    else f"graphfakos.{event.status}"
                )
                lines = [f"event: {event_name}"]
                if isinstance(event, GraphFakosGraphPatch):
                    lines.append(f"id: {event.cursor.value}")
                lines.append(f"data: {json.dumps(event.to_dict(), sort_keys=True)}")
                body = ("\n".join(lines) + "\n\n").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "close")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            finally:
                self.server.release_live_client()

        def _request_allowed(self, path: str) -> bool:
            origin = self.headers.get("Origin", "")
            if not _origin_allowed(
                origin, self.headers.get("Host", ""), allowed_origins
            ):
                self.server.origin_rejections += 1
                self._send_json(403, {"ok": False, "error": "origin is not allowed"})
                return False
            if authorize_request is not None and not authorize_request(
                self.command,
                path,
                {key: value for key, value in self.headers.items()},
            ):
                self.server.authorization_rejections += 1
                self._send_json(
                    403, {"ok": False, "error": "request is not authorized"}
                )
                return False
            return True

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
    server.live_provider = live_provider
    server.max_live_clients = max_live_clients
    server._live_clients = 0
    server._live_lock = Lock()
    server.authorization_rejections = 0
    server.origin_rejections = 0
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
    live_provider: GraphFakosLiveProvider | None = None,
    allow_remote: bool = False,
    authorize_request: RequestAuthorizer | None = None,
    allowed_origins: tuple[str, ...] = (),
    max_live_clients: int = 16,
) -> LocalViewerServerResult:
    server = make_local_viewer_server(
        render_path=render_path,
        render_fragment_path=render_fragment_path,
        handle_action=handle_action,
        default_path=default_path,
        host=host,
        port=port,
        live_provider=live_provider,
        allow_remote=allow_remote,
        authorize_request=authorize_request,
        allowed_origins=allowed_origins,
        max_live_clients=max_live_clients,
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


def _validate_server_exposure(
    *,
    host: str,
    allow_remote: bool,
    authorize_request: RequestAuthorizer | None,
    allowed_origins: tuple[str, ...],
    max_live_clients: int,
) -> None:
    if max_live_clients <= 0:
        raise ValueError("max_live_clients must be positive")
    if "*" in allowed_origins:
        raise ValueError("wildcard origins are not allowed")
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if loopback:
        return
    if not allow_remote:
        raise ValueError("non-loopback bind requires explicit allow_remote=True")
    if authorize_request is None:
        raise ValueError("non-loopback bind requires a request authorization hook")


def _origin_allowed(origin: str, host: str, allowed_origins: tuple[str, ...]) -> bool:
    if not origin:
        return True
    same_origin = {f"http://{host}", f"https://{host}"}
    return origin in same_origin or origin in allowed_origins


__all__ = [
    "LocalViewerHttpServer",
    "LocalViewerServerResult",
    "ActionHandler",
    "RequestAuthorizer",
    "RenderPath",
    "make_local_viewer_server",
    "serve_local_viewer",
]
