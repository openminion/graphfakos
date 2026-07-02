from __future__ import annotations

import pytest

from graphfakos.adapters import DEMO_SCENARIOS, DemoGraphProvider, build_demo_graph
from graphfakos.models import GraphFakosKnowledgeCapture, GraphFakosRequest
from graphfakos.provider import diagnose_graph
from graphfakos.ui import render_graph_viewer


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
        "budget",
        "islands",
    )

    graphs = [build_demo_graph(scenario) for scenario in DEMO_SCENARIOS]

    assert {graph.provider_id for graph in graphs} == {"demo"}
    assert min(len(graph.nodes) for graph in graphs) >= 8
    assert max(len(graph.nodes) for graph in graphs) >= 30
    assert any(graph.warnings for graph in graphs)
    assert all(graph.available_facets["node_kind"] for graph in graphs)


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
