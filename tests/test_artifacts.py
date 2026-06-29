from __future__ import annotations

import json

from graphfakos import (
    diagnose_graph,
    FileGraphProvider,
    FixtureGraphProvider,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    graph_artifact_schema,
    graph_from_dict,
    load_comparison_graph,
    load_graph_artifact,
    load_overlay_graphs,
    load_provider_graph,
    write_graph_artifact,
)


def test_graph_artifact_round_trip_and_file_provider(tmp_path) -> None:
    provider = FixtureGraphProvider()
    request = GraphFakosRequest(screen="diff")
    graph = load_provider_graph(provider, request)
    comparison = load_comparison_graph(provider, request)
    overlay = load_overlay_graphs(provider, request)[0]
    graph_path = tmp_path / "graph.json"
    comparison_path = tmp_path / "comparison.json"
    overlay_path = tmp_path / "overlay.json"

    write_graph_artifact(graph, str(graph_path))
    write_graph_artifact(comparison, str(comparison_path))
    write_graph_artifact(overlay, str(overlay_path))
    file_provider = FileGraphProvider(
        str(graph_path),
        comparison_graph_path=str(comparison_path),
        overlay_graph_paths=(str(overlay_path),),
    )

    loaded = load_provider_graph(file_provider, request)
    loaded_comparison = load_comparison_graph(file_provider, request)
    loaded_overlays = load_overlay_graphs(file_provider, request)

    assert loaded.to_dict() == graph.to_dict()
    assert loaded_comparison is not None
    assert loaded_comparison.to_dict() == comparison.to_dict()
    assert loaded_overlays[0].to_dict() == overlay.to_dict()


def test_graph_from_dict_and_schema_are_public() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    payload = graph.to_dict()
    rebuilt = graph_from_dict(payload)
    schema = graph_artifact_schema()

    assert rebuilt.to_dict() == payload
    assert schema["title"] == "GraphFakos Graph Artifact"
    assert "graph_id" in schema["required"]


def test_load_graph_artifact_reads_written_file(tmp_path) -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    path = tmp_path / "artifact.json"

    write_graph_artifact(graph, str(path))
    loaded = load_graph_artifact(str(path))

    assert loaded.graph_id == graph.graph_id
    assert json.loads(path.read_text(encoding="utf-8"))["provider_id"] == "fixture"


def test_graph_from_dict_preserves_snapshot_metadata() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    rebuilt = GraphFakosGraph.from_dict(graph.to_dict())

    assert rebuilt.snapshot is not None
    assert rebuilt.snapshot.snapshot_id == "fixture-current"


def test_diagnostics_include_self_loops_and_secondary_components() -> None:
    graph = GraphFakosGraph(
        graph_id="diagnostic",
        label="Diagnostic Graph",
        provider_id="diag",
        provider_label="Diagnostic Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(
            GraphFakosNode(id="a", label="A", kind="node"),
            GraphFakosNode(id="b", label="B", kind="node"),
            GraphFakosNode(id="c", label="C", kind="node"),
            GraphFakosNode(id="d", label="D", kind="node"),
        ),
        edges=(
            GraphFakosEdge(id="a-b", source_id="a", target_id="b", kind="relates"),
            GraphFakosEdge(id="c-c", source_id="c", target_id="c", kind="loops"),
        ),
    )
    diagnostics = diagnose_graph(graph)

    assert diagnostics.self_loop_edge_ids == ("c-c",)
    assert diagnostics.disconnected_node_ids == ("c", "d")
