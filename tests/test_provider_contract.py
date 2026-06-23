from __future__ import annotations

import pytest

from graphfakos import (
    FixtureGraphProvider,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    diagnose_graph,
    load_provider_graph,
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
    assert diagnostics.to_dict()["warnings"] == ["provider warning"]


def test_graph_to_dict_is_provider_neutral() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    payload = graph.to_dict()

    assert payload["provider_id"] == "fixture"
    assert payload["graph_role"] == "third_party"
    assert len(payload["nodes"]) == 4
    assert len(payload["edges"]) == 4


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
        "provider_status",
        "context_preview",
    ):
        html = render_static_html(CustomProvider(), GraphFakosRequest(screen=screen))
        assert "Custom Provider" in html
        assert "Integration Commands" in html
