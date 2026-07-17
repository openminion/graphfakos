"""Desktop bootstrap helpers for the packaged GraphFakos application."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import hmac
import json
import os
import secrets
from typing import Mapping

from .adapters import DEMO_SCENARIOS, DemoGraphProvider, FixtureGraphProvider
from .cli import handle_provider_action
from .models import GraphFakosRequest
from .server import RequestAuthorizer, make_local_viewer_server
from .ui import render_provider_path, render_provider_path_fragment

_DEFAULT_TOKEN_FD = 3
_DESKTOP_TOKEN_HEADER = "X-GraphFakos-Desktop-Token"
_MAX_TOKEN_BYTES = 4096


@dataclass(frozen=True, slots=True)
class DesktopBackendReady:
    schema_version: int
    event: str
    host: str
    port: int
    app_path: str
    backend_version: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "event": self.event,
            "host": self.host,
            "port": self.port,
            "app_path": self.app_path,
            "backend_version": self.backend_version,
        }


def read_desktop_token_from_fd(fd: int = _DEFAULT_TOKEN_FD) -> str:
    """Read the per-launch desktop token from an inherited private pipe."""
    try:
        raw = os.read(fd, _MAX_TOKEN_BYTES + 1)
    except OSError as exc:
        raise RuntimeError("desktop token pipe could not be read") from exc
    if not raw or len(raw) > _MAX_TOKEN_BYTES:
        raise RuntimeError("desktop token pipe was empty or too large")
    try:
        token = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise RuntimeError("desktop token pipe must contain UTF-8") from exc
    if len(token) < 32:
        raise RuntimeError("desktop token is too short")
    return token


def desktop_authorizer(token: str) -> RequestAuthorizer:
    def authorize_request(
        method: str,
        path: str,
        headers: Mapping[str, str],
    ) -> bool:
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        candidate = normalized_headers.get(_DESKTOP_TOKEN_HEADER.lower(), "")
        return method in {"GET", "POST"} and hmac.compare_digest(candidate, token)

    return authorize_request


def desktop_backend_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GraphFakos desktop backend")
    parser.add_argument("--token-fd", type=int, default=_DEFAULT_TOKEN_FD)
    parser.add_argument("--demo-scenario", choices=DEMO_SCENARIOS, default="")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args(argv)

    token = read_desktop_token_from_fd(args.token_fd)
    provider = (
        DemoGraphProvider(args.demo_scenario)
        if args.demo_scenario
        else FixtureGraphProvider()
    )
    request = GraphFakosRequest(screen="explore")
    server = make_local_viewer_server(
        render_path=lambda path, query: render_provider_path(
            provider, request, path, query
        ),
        render_fragment_path=lambda path, query: render_provider_path_fragment(
            provider,
            request,
            path,
            query,
        ),
        handle_action=lambda path, payload: handle_provider_action(
            provider, path, payload
        ),
        default_path="/explore",
        host=args.host,
        port=args.port,
        authorize_request=desktop_authorizer(token),
        allowed_origins=("openminion://app",),
    )
    host, port = server.server_address
    ready = DesktopBackendReady(
        schema_version=1,
        event="desktop.backend.ready",
        host=str(host),
        port=int(port),
        app_path="/explore",
        backend_version="0.0.1",
    )
    print(json.dumps(ready.to_dict(), sort_keys=True), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def generate_desktop_token() -> str:
    return secrets.token_urlsafe(48)


__all__ = [
    "DesktopBackendReady",
    "desktop_authorizer",
    "desktop_backend_main",
    "generate_desktop_token",
    "read_desktop_token_from_fd",
]
