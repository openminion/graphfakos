"""Provider protocol and validation helpers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import GraphFakosDiagnostics, GraphFakosGraph, GraphFakosRequest


@runtime_checkable
class GraphFakosProvider(Protocol):
    provider_id: str
    provider_label: str
    graph_role: str
    capabilities: tuple[str, ...]

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        """Return one provider-neutral graph for the viewer request."""


def validate_graph(graph: GraphFakosGraph) -> None:
    """Validate graph references that the viewer relies on."""
    node_ids = {node.id for node in graph.nodes}
    duplicate_node_count = len(graph.nodes) - len(node_ids)
    if duplicate_node_count:
        raise ValueError("GraphFakosGraph contains duplicate node ids")
    edge_ids = {edge.id for edge in graph.edges}
    duplicate_edge_count = len(graph.edges) - len(edge_ids)
    if duplicate_edge_count:
        raise ValueError("GraphFakosGraph contains duplicate edge ids")
    for edge in graph.edges:
        if edge.source_id not in node_ids:
            raise ValueError(f"edge {edge.id!r} has unknown source {edge.source_id!r}")
        if edge.target_id not in node_ids:
            raise ValueError(f"edge {edge.id!r} has unknown target {edge.target_id!r}")


def diagnose_graph(graph: GraphFakosGraph) -> GraphFakosDiagnostics:
    node_ids = {node.id for node in graph.nodes}
    connected_node_ids = {
        node_id
        for edge in graph.edges
        for node_id in (edge.source_id, edge.target_id)
        if node_id in node_ids
    }
    provenance_ids = {item.id for item in graph.provenance}
    citation_ids = {item.id for item in graph.citations}
    seen_edge_ids: set[str] = set()
    duplicate_edge_ids: list[str] = []
    unknown_provenance_ids: set[str] = set()
    unknown_citation_ids: set[str] = set()
    for edge in graph.edges:
        if edge.id in seen_edge_ids:
            duplicate_edge_ids.append(edge.id)
        seen_edge_ids.add(edge.id)
        unknown_provenance_ids.update(
            item_id for item_id in edge.provenance_ids if item_id not in provenance_ids
        )
        unknown_citation_ids.update(
            item_id for item_id in edge.citation_ids if item_id not in citation_ids
        )
    for node in graph.nodes:
        unknown_provenance_ids.update(
            item_id for item_id in node.provenance_ids if item_id not in provenance_ids
        )
        unknown_citation_ids.update(
            item_id for item_id in node.citation_ids if item_id not in citation_ids
        )
    return GraphFakosDiagnostics(
        node_count=len(graph.nodes),
        edge_count=len(graph.edges),
        provenance_count=len(graph.provenance),
        citation_count=len(graph.citations),
        orphan_node_ids=tuple(sorted(node_ids - connected_node_ids)),
        duplicate_edge_ids=tuple(sorted(set(duplicate_edge_ids))),
        unknown_provenance_ids=tuple(sorted(unknown_provenance_ids)),
        unknown_citation_ids=tuple(sorted(unknown_citation_ids)),
        warnings=graph.warnings,
    )


def load_provider_graph(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> GraphFakosGraph:
    graph = provider.load_graph(request)
    validate_graph(graph)
    return graph


__all__ = [
    "diagnose_graph",
    "GraphFakosProvider",
    "load_provider_graph",
    "validate_graph",
]
