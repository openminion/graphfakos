from __future__ import annotations

import json
from threading import Thread
from urllib.request import Request
from urllib.request import urlopen
from urllib.parse import urlencode

import pytest

from graphfakos import (
    DemoGraphProvider,
    FixtureGraphProvider,
    GraphFakosKnowledgeCapture,
    GraphFakosRequest,
    make_local_viewer_server,
)
from graphfakos.cli import handle_provider_action
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


def test_local_preview_server_accepts_graph_authoring_actions() -> None:
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
            handle_action=lambda path, payload: handle_provider_action(
                provider,
                path,
                payload,
            ),
            port=0,
        )
    except PermissionError:
        pytest.skip("local socket binding is unavailable in this sandbox")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        action_url = server.preview_url.rsplit("/", 1)[0] + "/api/action"
        action_request = Request(
            action_url,
            data=json.dumps(
                {
                    "action_id": "draft:server",
                    "action_type": "draft_node",
                    "target_id": "agent:codex",
                    "label": "Server action preview",
                    "body": "Exercise the reusable graph editor endpoint.",
                    "tags": ["editor", "server"],
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
    assert action_payload["status"]["status"] == "previewed"
    assert action_payload["status"]["provider_payload"]["preview_only"] is True
    assert "Server action preview" in explore_html
    assert "action:001" in explore_html


def test_local_preview_server_accepts_form_encoded_workbench_actions() -> None:
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
            handle_action=lambda path, payload: handle_provider_action(
                provider,
                path,
                payload,
            ),
            port=0,
        )
    except PermissionError:
        pytest.skip("local socket binding is unavailable in this sandbox")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = server.preview_url.rsplit("/", 1)[0]
        capture_request = Request(
            f"{base_url}/api/knowledge",
            data=urlencode(
                {
                    "text": "No JavaScript capture still reaches the provider.",
                    "kind": "question",
                    "tags": "fallback, forms",
                    "source": "workbench",
                    "link_node_id": "agent:codex",
                    "link_edge_kind": "questions",
                    "viewer_context": json.dumps(
                        {
                            "screen": "explore",
                            "selected_node_ids": ["agent:codex"],
                            "selected_edge_id": "",
                            "camera": {"x": 4, "y": -2, "zoom": 1.2},
                        }
                    ),
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urlopen(capture_request, timeout=5) as response:
            capture_payload = json.loads(response.read().decode("utf-8"))
        action_request = Request(
            f"{base_url}/api/action",
            data=urlencode(
                {
                    "action_id": "draft:form",
                    "action_type": "draft_edge",
                    "target_id": "agent:codex",
                    "source_id": "agent:codex",
                    "target_node_id": "document:dynamic-viewer-spec",
                    "label": "Form action preview",
                    "body": "Exercise the ordinary browser form fallback.",
                    "tags": "editor, fallback",
                    "viewer_context": json.dumps(
                        {
                            "screen": "explore",
                            "selected_node_ids": [
                                "agent:codex",
                                "document:dynamic-viewer-spec",
                            ],
                            "selected_edge_id": "edge:agent-spec",
                            "camera": {"x": 4, "y": -2, "zoom": 1.2},
                        }
                    ),
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
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

    assert capture_payload["ok"] is True
    assert capture_payload["capture"]["tags"] == ["fallback", "forms"]
    assert capture_payload["capture"]["provider_payload"]["viewer_context"][
        "selected_node_ids"
    ] == ["agent:codex"]
    assert action_payload["ok"] is True
    assert action_payload["action"]["tags"] == ["editor", "fallback"]
    assert action_payload["action"]["provider_payload"]["viewer_context"][
        "selected_node_ids"
    ] == ["agent:codex", "document:dynamic-viewer-spec"]
    assert (
        action_payload["action"]["provider_payload"]["viewer_context"][
            "selected_edge_id"
        ]
        == "edge:agent-spec"
    )
    assert "No JavaScript capture still reaches the provider." in explore_html
    assert "Form action preview" in explore_html


def test_local_preview_server_redirects_browser_form_actions_to_viewer() -> None:
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
            handle_action=lambda path, payload: handle_provider_action(
                provider,
                path,
                payload,
            ),
            port=0,
        )
    except PermissionError:
        pytest.skip("local socket binding is unavailable in this sandbox")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = server.preview_url.rsplit("/", 1)[0]
        capture_request = Request(
            f"{base_url}/api/knowledge",
            data=urlencode(
                {
                    "text": "Browser form capture returns to the graph.",
                    "kind": "note",
                    "tags": "browser, fallback",
                    "source": "workbench",
                    "link_node_id": "agent:codex",
                    "link_edge_kind": "mentions",
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html",
                "Referer": server.preview_url,
            },
            method="POST",
        )
        with urlopen(capture_request, timeout=5) as response:
            capture_html = response.read().decode("utf-8")
            capture_url = response.geturl()
        action_request = Request(
            f"{base_url}/api/action",
            data=urlencode(
                {
                    "action_id": "draft:browser",
                    "action_type": "draft_node",
                    "target_id": "agent:codex",
                    "label": "Browser form action",
                    "body": "No-JavaScript action returns to the workbench.",
                    "tags": "browser, action",
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html",
                "Referer": server.preview_url,
            },
            method="POST",
        )
        with urlopen(action_request, timeout=5) as response:
            action_html = response.read().decode("utf-8")
            action_url = response.geturl()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert capture_url.endswith("/explore")
    assert action_url.endswith("/explore")
    assert "<graphfakos-viewer" in capture_html
    assert "<graphfakos-viewer" in action_html
    assert "Browser form capture returns to the graph." in capture_html
    assert "Browser form action" in action_html
