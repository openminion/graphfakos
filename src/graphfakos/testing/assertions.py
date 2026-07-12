"""Reusable assertions for GraphFakos-backed viewer output."""

from __future__ import annotations

from ..live import (
    GraphFakosGraphPatch,
    GraphFakosGraphRevision,
    GraphFakosLiveGraphState,
    GraphFakosLiveProvider,
    GraphFakosLiveSessionRequest,
    apply_graph_patch,
)
from ..models import GraphFakosGraph


def assert_graph_viewer_contract(
    html: str,
    *,
    expected_role: str,
    expected_provider: str,
    expected_node: str,
    expected_edge: str,
) -> None:
    assert "GraphFakos" in html
    assert "Graph Canvas" in html
    assert "Integration Commands" in html
    assert expected_role in html
    assert expected_provider in html
    assert expected_node in html
    assert expected_edge in html
    assert "Review Presets" in html
    assert "Navigator" in html


def assert_review_preset_contract(
    presets: tuple[dict[str, str], ...],
    *,
    required_ids: tuple[str, ...],
) -> None:
    preset_ids = {item["id"] for item in presets}
    for required_id in required_ids:
        assert required_id in preset_ids
    for preset in presets:
        assert preset["route"].startswith("/")
        assert preset["label"]
        assert preset["summary"]


def assert_graph_dot_contract(
    dot: str,
    *,
    expected_node_ids: tuple[str, ...],
    expected_edge_ids: tuple[str, ...] = (),
) -> None:
    assert dot.startswith('digraph "')
    for node_id in expected_node_ids:
        assert f'"{node_id}"' in dot
    for edge_id in expected_edge_ids:
        assert edge_id in dot


def assert_live_provider_contract(
    provider: GraphFakosLiveProvider,
    *,
    initial_graph: GraphFakosGraph,
    initial_revision: str,
    request: GraphFakosLiveSessionRequest,
) -> GraphFakosLiveGraphState:
    status = provider.open_live_session(request)
    assert status.status == "live"
    event = provider.load_patch(request)
    assert isinstance(event, GraphFakosGraphPatch)
    state = apply_graph_patch(
        GraphFakosLiveGraphState(
            graph=initial_graph,
            revision=GraphFakosGraphRevision(initial_revision),
        ),
        event,
    )
    assert state.cursor == event.cursor
    assert state.revision == event.result_revision
    return state


__all__ = [
    "assert_graph_dot_contract",
    "assert_review_preset_contract",
    "assert_graph_viewer_contract",
    "assert_live_provider_contract",
]
