from __future__ import annotations

import pytest

from graphfakos import (
    FixtureGraphProvider,
    build_graph_report,
    build_viewer_route,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    diagnose_graph,
    load_comparison_graph,
    load_overlay_graphs,
    load_provider_graph,
    parse_viewer_request,
    query_syntax_reference,
    render_static_html,
    validate_graph,
)


def test_fixture_provider_satisfies_provider_contract() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())

    assert graph.provider_id == "fixture"
    assert graph.graph_role == "third_party"
    assert len(graph.nodes) == 4
    assert len(graph.edges) == 4
    assert graph.provenance
    assert graph.citations
    assert graph.provider_details["owner"] == "OpenMinion fixture"
    assert "diff" in graph.capability_details
    assert graph.snapshot is not None
    assert graph.snapshot.snapshot_id == "fixture-current"


def test_validate_graph_rejects_unknown_edge_references() -> None:
    graph = GraphFakosGraph(
        graph_id="bad",
        label="Bad Graph",
        provider_id="bad",
        provider_label="Bad Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(GraphFakosNode(id="known", label="Known", kind="node"),),
        edges=(
            GraphFakosEdge(
                id="bad-edge",
                source_id="known",
                target_id="missing",
                kind="bad",
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown target"):
        validate_graph(graph)


def test_validate_graph_rejects_duplicate_edge_ids() -> None:
    graph = GraphFakosGraph(
        graph_id="bad",
        label="Bad Graph",
        provider_id="bad",
        provider_label="Bad Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(
            GraphFakosNode(id="one", label="One", kind="node"),
            GraphFakosNode(id="two", label="Two", kind="node"),
        ),
        edges=(
            GraphFakosEdge(
                id="duplicate",
                source_id="one",
                target_id="two",
                kind="relates",
            ),
            GraphFakosEdge(
                id="duplicate",
                source_id="two",
                target_id="one",
                kind="relates",
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate edge ids"):
        validate_graph(graph)


def test_diagnose_graph_reports_provider_neutral_health() -> None:
    graph = GraphFakosGraph(
        graph_id="diagnostic",
        label="Diagnostic Graph",
        provider_id="diagnostic",
        provider_label="Diagnostic Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(
            GraphFakosNode(
                id="one",
                label="One",
                kind="node",
                provenance_ids=("missing-provenance",),
            ),
            GraphFakosNode(id="two", label="Two", kind="node"),
            GraphFakosNode(
                id="orphan",
                label="Orphan",
                kind="node",
                citation_ids=("missing-citation",),
            ),
        ),
        edges=(
            GraphFakosEdge(
                id="edge",
                source_id="one",
                target_id="two",
                kind="relates",
            ),
        ),
        warnings=("provider warning",),
    )

    diagnostics = diagnose_graph(graph)

    assert diagnostics.healthy is False
    assert diagnostics.orphan_node_ids == ("orphan",)
    assert diagnostics.unknown_provenance_ids == ("missing-provenance",)
    assert diagnostics.unknown_citation_ids == ("missing-citation",)
    assert diagnostics.disconnected_node_ids == ("orphan",)
    assert diagnostics.to_dict()["warnings"] == ["provider warning"]


def test_graph_to_dict_is_provider_neutral() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    payload = graph.to_dict()

    assert payload["provider_id"] == "fixture"
    assert payload["graph_role"] == "third_party"
    assert len(payload["nodes"]) == 4
    assert len(payload["edges"]) == 4
    assert payload["available_facets"]["node_kind"] == [
        "artifact",
        "document",
        "memory",
        "provider",
    ]


def test_fixture_provider_exposes_comparison_and_overlay_graphs() -> None:
    provider = FixtureGraphProvider()
    request = GraphFakosRequest(screen="diff")

    comparison = load_comparison_graph(provider, request)
    overlays = load_overlay_graphs(provider, request)

    assert comparison is not None
    assert comparison.provider_label == "Fixture Baseline"
    assert len(comparison.nodes) == 3
    assert overlays
    assert overlays[0].provider_label == "Overlay Provider"


def test_build_graph_report_includes_overlay_and_comparison() -> None:
    report = build_graph_report(FixtureGraphProvider(), GraphFakosRequest(screen="diff"))

    assert report["diagnostics"]["healthy"] is True
    assert report["comparison_graph"]["provider_label"] == "Fixture Baseline"
    assert report["comparison_diff"]["summary"]["changed node count"] == 0
    assert report["overlay_graphs"][0]["provider_label"] == "Overlay Provider"
    assert report["request"]["screen"] == "diff"
    assert report["graph"]["snapshot"]["snapshot_id"] == "fixture-current"


def test_viewer_route_helpers_are_public_and_stable() -> None:
    request = GraphFakosRequest(
        screen="diff",
        query="kind:file has:provenance",
        focus_node_id="node:one",
        comparison_graph_id="baseline",
        render_limit=80,
    )

    route = build_viewer_route(request)
    parsed = parse_viewer_request(
        "/diff",
        {
            "query": ["kind:file has:provenance"],
            "focus_node_id": ["node:one"],
            "comparison_graph_id": ["baseline"],
            "render_limit": ["80"],
        },
    )

    assert route.startswith("/diff?")
    assert parsed.screen == "diff"
    assert parsed.comparison_graph_id == "baseline"
    assert parsed.render_limit == 80


def test_query_syntax_reference_documents_tokens() -> None:
    syntax = query_syntax_reference()

    assert any(item["token"] == "kind:<value>" for item in syntax)
    assert any(item["token"] == "has:provenance" for item in syntax)
    assert any(item["token"] == "score>=0.8" for item in syntax)
    assert any(item["token"] == '"quoted phrase"' for item in syntax)


def test_custom_provider_can_render_all_shared_screens() -> None:
    class CustomProvider:
        provider_id = "custom"
        provider_label = "Custom Provider"
        graph_role = "third_party"
        capabilities = (
            "search",
            "neighborhood",
            "path",
            "provenance",
            "timeline",
            "provider_status",
            "context_preview",
            "static_export",
        )

        def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
            return GraphFakosGraph(
                graph_id="custom",
                label="Custom Graph",
                provider_id=self.provider_id,
                provider_label=self.provider_label,
                graph_role=self.graph_role,
                capabilities=self.capabilities,
                nodes=(
                    GraphFakosNode(
                        id="one",
                        label="One",
                        kind="record",
                        summary="First custom node.",
                        score=0.9,
                        source="custom",
                    ),
                    GraphFakosNode(
                        id="two",
                        label="Two",
                        kind="record",
                        summary="Second custom node.",
                        score=0.8,
                        source="custom",
                    ),
                ),
                edges=(
                    GraphFakosEdge(
                        id="one-two",
                        source_id="one",
                        target_id="two",
                        kind="connects",
                        label="connects",
                    ),
                ),
                provider_payload={
                    "integration_summary": "Custom provider preview.",
                    "integration_commands": ("python -m custom_graph preview --serve",),
                },
            )

    for screen in (
        "explore",
        "neighborhood",
        "path",
        "provenance",
        "timeline",
        "diff",
        "provider_status",
        "context_preview",
    ):
        html = render_static_html(CustomProvider(), GraphFakosRequest(screen=screen))
        assert "Custom Provider" in html
        assert "Integration Commands" in html
