"""Provider protocol and validation helpers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import GraphFakosGraph, GraphFakosRequest


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
    for edge in graph.edges:
        if edge.source_id not in node_ids:
            raise ValueError(f"edge {edge.id!r} has unknown source {edge.source_id!r}")
        if edge.target_id not in node_ids:
            raise ValueError(f"edge {edge.id!r} has unknown target {edge.target_id!r}")


def load_provider_graph(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> GraphFakosGraph:
    graph = provider.load_graph(request)
    validate_graph(graph)
    return graph


__all__ = [
    "GraphFakosProvider",
    "load_provider_graph",
    "validate_graph",
]
