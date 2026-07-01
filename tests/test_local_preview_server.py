from __future__ import annotations

import json
from threading import Thread
from urllib.request import Request
from urllib.request import urlopen

import pytest

from graphfakos import (
    DemoGraphProvider,
    FixtureGraphProvider,
    GraphFakosKnowledgeCapture,
    GraphFakosRequest,
    make_local_viewer_server,
)
from graphfakos.ui import render_provider_path, render_provider_path_fragment


def test_local_preview_server_serves_viewer_routes() -> None:
    provider = FixtureGraphProvider()
    request = GraphFakosRequest(screen="explore")
    try:
        server = make_local_viewer_server(
            render_path=lambda path, query: render_provider_path(
                provider,
                request,
                path,
                query,
            ),
            render_fragment_path=lambda path, query: render_provider_path_fragment(
                provider,
                request,
                path,
                query,
            ),
            port=0,
        )
    except PermissionError:
        pytest.skip("local socket binding is unavailable in this sandbox")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(server.preview_url, timeout=5) as response:
            explore_html = response.read().decode("utf-8")
        status_url = server.preview_url.rsplit("/", 1)[0] + "/provider_status"
        with urlopen(status_url, timeout=5) as response:
            status_html = response.read().decode("utf-8")
        fragment_request = Request(
            status_url,
            headers={
                "Accept": "application/json",
                "X-GraphFakos-Fragment": "1",
            },
        )
        with urlopen(fragment_request, timeout=5) as response:
            fragment_payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert "Graph Canvas" in explore_html
    assert "Provider Status" in status_html
    assert fragment_payload["kind"] == "graphfakos.fragment"
    assert fragment_payload["route"] == "/provider_status"
    assert "<graphfakos-viewer" in fragment_payload["fragment"]
    assert "<!doctype html>" not in fragment_payload["fragment"].casefold()


def test_local_preview_server_accepts_knowledge_capture_actions() -> None:
    provider = DemoGraphProvider()
    request = GraphFakosRequest(screen="explore", focus_node_id="agent:codex")
    try:
        server = make_local_viewer_server(
            render_path=lambda path, query: render_provider_path(
                provider,
                request,
                path,
                query,
            ),
            render_fragment_path=lambda path, query: render_provider_path_fragment(
                provider,
                request,
                path,
                query,
            ),
            handle_action=lambda path, payload: {
                "ok": True,
                "graph": provider.capture_knowledge(
                    GraphFakosKnowledgeCapture.from_dict(payload)
                ).to_dict(),
            },
            port=0,
        )
    except PermissionError:
        pytest.skip("local socket binding is unavailable in this sandbox")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        action_url = server.preview_url.rsplit("/", 1)[0] + "/api/knowledge"
        action_request = Request(
            action_url,
            data=json.dumps(
                {
                    "text": "Capture this as navigable graph knowledge.",
                    "tags": ["ui", "note"],
                    "link_node_id": "agent:codex",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(action_request, timeout=5) as response:
            action_payload = json.loads(response.read().decode("utf-8"))
        with urlopen(server.preview_url, timeout=5) as response:
            explore_html = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert action_payload["ok"] is True
    assert action_payload["graph"]["stats"]["capture_count"] == 1
    assert "Capture this as navigable graph knowledge." in explore_html
    assert "capture:001" in explore_html
