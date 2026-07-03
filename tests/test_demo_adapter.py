from __future__ import annotations

from math import hypot
import re

import pytest

from graphfakos.adapters import DEMO_SCENARIOS, DemoGraphProvider, build_demo_graph
from graphfakos.models import (
    GraphFakosGraphAction,
    GraphFakosKnowledgeCapture,
    GraphFakosRequest,
)
from graphfakos.provider import diagnose_graph
from graphfakos.ui import render_graph_viewer


_NODE_POSITION_PATTERN = re.compile(
    r"data-node-id='([^']+)'.*?data-x='([-0-9.]+)' data-y='([-0-9.]+)'"
)


def test_demo_provider_exposes_visual_iteration_scenarios() -> None:
    assert DEMO_SCENARIOS == (
        "agent-memory",
        "source-code",
        "dense",
        "timeline",
        "warnings",
        "pathfinding",
        "provenance",
        "facets",
        "workbench-mixed",
        "budget",
        "islands",
    )

    graphs = [build_demo_graph(scenario) for scenario in DEMO_SCENARIOS]

    assert {graph.provider_id for graph in graphs} == {"demo"}
    assert min(len(graph.nodes) for graph in graphs) >= 8
    assert max(len(graph.nodes) for graph in graphs) >= 30
    assert any(graph.warnings for graph in graphs)
    assert all(graph.available_facets["node_kind"] for graph in graphs)


def test_workbench_mixed_demo_exercises_code_and_knowledge_workflows() -> None:
    graph = build_demo_graph("workbench-mixed")
    html = render_graph_viewer(
        graph,
        GraphFakosRequest(
            screen="explore",
            focus_node_id="agent:reviewer",
            selected_node_ids=("file:ui-app", "memory:layout-preference"),
            selected_edge_id="edge:agent-links-code",
            style_color_by="source",
            style_size_by="degree",
            style_edge_width_by="confidence",
        ),
    )

    node_ids = {node.id for node in graph.nodes}
    edge_kinds = {edge.kind for edge in graph.edges}

    assert graph.graph_id == "demo-workbench-mixed"
    assert len(graph.nodes) == 18
    assert len(graph.edges) == 19
    assert {
        "agent:reviewer",
        "file:ui-app",
        "memory:layout-preference",
        "document:ui-contracts",
        "test:browser-runtime",
    } <= node_ids
    assert {"observes", "owns", "covered_by", "flags", "queues"} <= edge_kinds
    assert any(node.kind == "warning" for node in graph.nodes)
    assert any(node.provenance_ids for node in graph.nodes)
    assert any(not node.provenance_ids for node in graph.nodes)
    assert any(edge.provenance_ids for edge in graph.edges)
    assert any(not edge.provenance_ids for edge in graph.edges)
    assert diagnose_graph(graph).node_count == 18
    assert "Interaction guide" in html
    assert "Evidence Coverage Map" in html
    assert "Visual Legend" in html
    assert "Capture Knowledge" in html
    assert "Graph Authoring" in html
    assert "data-gf-canvas-legend='true'" in html
    assert "data-gf-evidence-coverage-map='true'" in html


def test_demo_provider_supports_comparison_and_overlay_graphs() -> None:
    provider = DemoGraphProvider("dense")
    request = GraphFakosRequest(screen="diff", layout="grouped")

    graph = provider.load_graph(request)
    baseline = provider.load_comparison_graph(request)
    overlays = provider.load_overlay_graphs(request)

    assert graph.graph_id == "demo-dense"
    assert baseline.graph_id == "demo-dense-baseline"
    assert len(baseline.nodes) < len(graph.nodes)
    assert overlays[0].graph_id == "demo-dense-overlay"
    assert diagnose_graph(graph).node_count == 36
    assert diagnose_graph(graph).edge_count == 60


def test_demo_provider_turns_workbench_captures_into_graph_nodes() -> None:
    provider = DemoGraphProvider("agent-memory")
    before = provider.load_graph(GraphFakosRequest())

    after = provider.capture_knowledge(
        GraphFakosKnowledgeCapture(
            text="GraphFakos should let operators add knowledge beside the graph.",
            tags=("ui", "capture"),
            link_node_id="agent:codex",
        )
    )

    assert len(after.nodes) == len(before.nodes) + 1
    assert len(after.edges) == len(before.edges) + 1
    assert after.stats["capture_count"] == 1
    assert any(node.id == "capture:001" for node in after.nodes)
    assert any(edge.source_id == "agent:codex" for edge in after.edges)


def test_demo_provider_previews_graph_actions_as_graph_items() -> None:
    provider = DemoGraphProvider("agent-memory")
    before = provider.load_graph(GraphFakosRequest())

    status = provider.submit_graph_action(
        GraphFakosGraphAction(
            action_id="draft:demo",
            action_type="draft_edge",
            target_id="agent:codex",
            source_id="agent:codex",
            target_node_id="document:dynamic-viewer-spec",
            label="Review graph editor workflow",
            body="Preview this provider-neutral edit beside the graph.",
            tags=("editor", "preview"),
        )
    )
    after = provider.load_graph(GraphFakosRequest())

    assert status.status == "previewed"
    assert status.provider_payload["preview_only"] is True
    assert len(after.nodes) == len(before.nodes) + 1
    assert len(after.edges) == len(before.edges) + 2
    assert after.stats["action_count"] == 1
    assert after.provider_payload["workbench_actions_preview_only"] is True
    assert any(
        node.id == "action:001" and node.kind == "action" for node in after.nodes
    )
    assert any(edge.id == "edge:action:001:target" for edge in after.edges)
    assert any(edge.id == "edge:action:001:proposed" for edge in after.edges)


def test_demo_core_feature_scenarios_render_matching_ui_screens() -> None:
    path_graph = build_demo_graph("pathfinding")
    path_html = render_graph_viewer(
        path_graph,
        GraphFakosRequest(
            screen="path",
            source_node_id="provider:entry",
            target_node_id="artifact:result",
        ),
    )
    provenance_graph = build_demo_graph("provenance")
    provenance_html = render_graph_viewer(
        provenance_graph,
        GraphFakosRequest(screen="provenance"),
    )
    budget_graph = build_demo_graph("budget")
    budget_html = render_graph_viewer(
        budget_graph,
        GraphFakosRequest(screen="explore", render_limit=24),
    )

    assert "provider:entry" in path_html
    assert "artifact:result" in path_html
    assert "data-path='true'" in path_html
    assert "4 provenance record(s)" in provenance_html
    assert "Dynamic Viewer Spec" in provenance_html
    assert "Render Budget" in budget_html
    assert "Show more" in budget_html


def test_dense_demo_force_layout_is_deterministic_bounded_and_spread() -> None:
    graph = build_demo_graph("dense")
    request = GraphFakosRequest(screen="explore", layout="force")

    first_positions = _node_positions(render_graph_viewer(graph, request))
    second_positions = _node_positions(render_graph_viewer(graph, request))

    assert first_positions == second_positions
    assert set(first_positions) == {node.id for node in graph.nodes}
    _assert_positions_in_canvas(first_positions)
    assert _position_spread(first_positions) >= (700.0, 340.0)
    assert _closest_node_distance(first_positions) >= 18.0


def test_core_demo_force_layouts_keep_path_and_islands_readable() -> None:
    path_positions = _node_positions(
        render_graph_viewer(
            build_demo_graph("pathfinding"),
            GraphFakosRequest(
                screen="path",
                layout="force",
                source_node_id="provider:entry",
                target_node_id="artifact:result",
            ),
        )
    )
    islands_positions = _node_positions(
        render_graph_viewer(
            build_demo_graph("islands"),
            GraphFakosRequest(screen="explore", layout="force"),
        )
    )
    memory_positions = _node_positions(
        render_graph_viewer(
            build_demo_graph("agent-memory"),
            GraphFakosRequest(
                screen="explore",
                layout="force",
                focus_node_id="agent:codex",
            ),
        )
    )

    _assert_positions_in_canvas(path_positions)
    _assert_positions_in_canvas(islands_positions)
    _assert_positions_in_canvas(memory_positions)
    assert _distance(path_positions["provider:entry"], (460.0, 230.0)) <= 0.1
    assert _closest_node_distance(path_positions) >= 100.0
    assert _closest_node_distance(islands_positions) >= 90.0
    assert _distance(memory_positions["agent:codex"], (460.0, 230.0)) <= 0.1


def test_demo_facets_and_islands_exercise_provider_status() -> None:
    facets = build_demo_graph("facets")
    islands = build_demo_graph("islands")
    islands_diagnostics = diagnose_graph(islands)

    assert facets.available_facets["source"] == (
        "eval-demo",
        "memory-demo",
        "source-demo",
    )
    assert "policy" in facets.available_facets["tag"]
    assert islands_diagnostics.disconnected_node_ids
    assert "provider:secondary" in islands_diagnostics.disconnected_node_ids


def test_demo_provider_rejects_unknown_scenarios() -> None:
    with pytest.raises(ValueError, match="Unknown demo scenario"):
        DemoGraphProvider("real-production-data")


def _node_positions(html: str) -> dict[str, tuple[float, float]]:
    return {
        match.group(1): (float(match.group(2)), float(match.group(3)))
        for match in _NODE_POSITION_PATTERN.finditer(html)
    }


def _assert_positions_in_canvas(positions: dict[str, tuple[float, float]]) -> None:
    assert positions
    assert all(46.0 <= x <= 874.0 for x, _y in positions.values())
    assert all(46.0 <= y <= 414.0 for _x, y in positions.values())


def _position_spread(
    positions: dict[str, tuple[float, float]],
) -> tuple[float, float]:
    xs = [x for x, _y in positions.values()]
    ys = [y for _x, y in positions.values()]
    return max(xs) - min(xs), max(ys) - min(ys)


def _closest_node_distance(positions: dict[str, tuple[float, float]]) -> float:
    node_ids = list(positions)
    return min(
        _distance(positions[left_id], positions[right_id])
        for index, left_id in enumerate(node_ids)
        for right_id in node_ids[index + 1 :]
    )


def _distance(
    left: tuple[float, float],
    right: tuple[float, float],
) -> float:
    return hypot(left[0] - right[0], left[1] - right[1])
