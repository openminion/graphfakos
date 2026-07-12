from __future__ import annotations

from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from graphfakos import (
    GraphFakosGraphPatch,
    GraphFakosGraphRevision,
    GraphFakosLiveSessionCursor,
    GraphFakosPatchOperation,
    InMemoryGraphFakosLiveProvider,
    make_local_viewer_server,
)


def _provider() -> InMemoryGraphFakosLiveProvider:
    provider = InMemoryGraphFakosLiveProvider(revision=GraphFakosGraphRevision("0"))
    provider.publish_patch(
        GraphFakosGraphPatch(
            patch_id="patch-1",
            base_revision=GraphFakosGraphRevision("0"),
            result_revision=GraphFakosGraphRevision("1"),
            cursor=GraphFakosLiveSessionCursor("cursor-1"),
            operations=(GraphFakosPatchOperation(kind="edge_delete", target_id="old"),),
        )
    )
    return provider


def _server(**kwargs: object):
    try:
        return make_local_viewer_server(
            render_path=lambda path, query: "<html>viewer</html>",
            port=0,
            **kwargs,
        )
    except PermissionError:
        pytest.skip("local socket binding is unavailable in this sandbox")


def test_live_sse_emits_patch_and_resumes_with_heartbeat() -> None:
    server = _server(live_provider=_provider())
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = server.preview_url.rsplit("/", 1)[0]
    try:
        with urlopen(f"{base_url}/api/live", timeout=5) as response:
            first = response.read().decode("utf-8")
        resumed = Request(
            f"{base_url}/api/live",
            headers={"Last-Event-ID": "cursor-1"},
        )
        with urlopen(resumed, timeout=5) as response:
            second = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert "event: graphfakos.patch" in first
    assert "id: cursor-1" in first
    assert '"patch_id": "patch-1"' in first
    assert "event: graphfakos.heartbeat" in second


def test_live_server_rejects_unexpected_origin_and_records_diagnostic() -> None:
    server = _server(live_provider=_provider())
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = server.preview_url.rsplit("/", 1)[0]
    request = Request(
        f"{base_url}/api/live", headers={"Origin": "https://example.invalid"}
    )
    try:
        with pytest.raises(HTTPError) as raised:
            urlopen(request, timeout=5)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert raised.value.code == 403
    assert server.live_diagnostics().origin_rejection_count == 1


def test_live_server_uses_host_authorization_hook() -> None:
    server = _server(
        live_provider=_provider(),
        authorize_request=lambda method, path, headers: (
            headers.get("X-Test-Key") == "allowed"
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = server.preview_url.rsplit("/", 1)[0]
    try:
        with pytest.raises(HTTPError) as raised:
            urlopen(f"{base_url}/api/live", timeout=5)
        request = Request(f"{base_url}/api/live", headers={"X-Test-Key": "allowed"})
        with urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert raised.value.code == 403
    assert "graphfakos.patch" in body
    assert server.live_diagnostics().authorization_rejection_count == 1


def test_remote_bind_requires_explicit_authorization_hook() -> None:
    with pytest.raises(ValueError, match="allow_remote"):
        make_local_viewer_server(
            render_path=lambda path, query: "viewer", host="0.0.0.0", port=0
        )
    with pytest.raises(ValueError, match="authorization hook"):
        make_local_viewer_server(
            render_path=lambda path, query: "viewer",
            host="0.0.0.0",
            port=0,
            allow_remote=True,
        )
    with pytest.raises(ValueError, match="wildcard"):
        make_local_viewer_server(
            render_path=lambda path, query: "viewer",
            port=0,
            allowed_origins=("*",),
        )


def test_live_client_limit_is_bounded() -> None:
    server = _server(live_provider=_provider(), max_live_clients=1)
    try:
        assert server.acquire_live_client() is True
        assert server.acquire_live_client() is False
    finally:
        server.release_live_client()
        server.server_close()
