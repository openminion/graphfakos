"""Provider protocol and validation helpers."""

from __future__ import annotations

from collections import deque
from typing import Protocol, runtime_checkable

from .models import (
    GraphFakosActionStatus,
    GraphFakosDiagnostics,
    GraphFakosGraph,
    GraphFakosGraphAction,
    GraphFakosGraphAnalytics,
    GraphFakosKnowledgeCapture,
    GraphFakosRequest,
)


@runtime_checkable
class GraphFakosProvider(Protocol):
    provider_id: str
    provider_label: str
    graph_role: str
    capabilities: tuple[str, ...]

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        """Return one provider-neutral graph for the viewer request."""


@runtime_checkable
class GraphFakosComparisonProvider(Protocol):
    def load_comparison_graph(
        self,
        request: GraphFakosRequest,
    ) -> GraphFakosGraph | None:
        """Return one comparison snapshot for diff-oriented screens."""


@runtime_checkable
class GraphFakosOverlayProvider(Protocol):
    def load_overlay_graphs(
        self,
        request: GraphFakosRequest,
    ) -> tuple[GraphFakosGraph, ...]:
        """Return provider graphs that should be compared or overlaid."""


@runtime_checkable
class GraphFakosKnowledgeCaptureProvider(Protocol):
    def capture_knowledge(
        self,
        capture: GraphFakosKnowledgeCapture,
    ) -> GraphFakosGraph | dict[str, object] | None:
        """Accept a workbench note or observation and refresh provider graph state."""


@runtime_checkable
class GraphFakosGraphActionProvider(Protocol):
    def submit_graph_action(
        self,
        action: GraphFakosGraphAction,
    ) -> GraphFakosActionStatus | dict[str, object] | None:
        """Accept a provider-neutral draft graph edit or merge request."""


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
    self_loop_edge_ids: list[str] = []
    for edge in graph.edges:
        if edge.id in seen_edge_ids:
            duplicate_edge_ids.append(edge.id)
        seen_edge_ids.add(edge.id)
        if edge.source_id == edge.target_id:
            self_loop_edge_ids.append(edge.id)
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
    disconnected_node_ids = _disconnected_node_ids(graph)
    return GraphFakosDiagnostics(
        node_count=len(graph.nodes),
        edge_count=len(graph.edges),
        provenance_count=len(graph.provenance),
        citation_count=len(graph.citations),
        orphan_node_ids=tuple(sorted(node_ids - connected_node_ids)),
        duplicate_edge_ids=tuple(sorted(set(duplicate_edge_ids))),
        unknown_provenance_ids=tuple(sorted(unknown_provenance_ids)),
        unknown_citation_ids=tuple(sorted(unknown_citation_ids)),
        self_loop_edge_ids=tuple(sorted(set(self_loop_edge_ids))),
        disconnected_node_ids=disconnected_node_ids,
        warnings=graph.warnings,
    )


def analyze_graph(graph: GraphFakosGraph) -> GraphFakosGraphAnalytics:
    degrees = _degree_map(graph)
    node_count = len(graph.nodes)
    edge_count = len(graph.edges)
    max_degree = max(degrees.values(), default=0)
    hub_floor = max(3, max_degree - 1)
    hub_node_ids = tuple(
        sorted(node_id for node_id, degree in degrees.items() if degree >= hub_floor)
    )
    possible_edges = node_count * max(node_count - 1, 0)
    density = edge_count / possible_edges if possible_edges else 0.0
    return GraphFakosGraphAnalytics(
        component_count=_component_count(graph),
        node_count=node_count,
        edge_count=edge_count,
        hub_node_ids=hub_node_ids,
        orphan_node_ids=diagnose_graph(graph).orphan_node_ids,
        max_degree=max_degree,
        average_degree=(sum(degrees.values()) / node_count if node_count else 0.0),
        density=density,
    )


def _degree_map(graph: GraphFakosGraph) -> dict[str, int]:
    degrees = {node.id: 0 for node in graph.nodes}
    for edge in graph.edges:
        if edge.source_id in degrees:
            degrees[edge.source_id] += 1
        if edge.target_id in degrees:
            degrees[edge.target_id] += 1
    return degrees


def _component_count(graph: GraphFakosGraph) -> int:
    if not graph.nodes:
        return 0
    adjacency: dict[str, set[str]] = {node.id: set() for node in graph.nodes}
    for edge in graph.edges:
        if edge.source_id in adjacency and edge.target_id in adjacency:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)
    remaining = set(adjacency)
    count = 0
    while remaining:
        count += 1
        start = next(iter(remaining))
        frontier: deque[str] = deque([start])
        remaining.remove(start)
        while frontier:
            node_id = frontier.popleft()
            for neighbor in adjacency.get(node_id, ()):
                if neighbor not in remaining:
                    continue
                remaining.remove(neighbor)
                frontier.append(neighbor)
    return count


def _disconnected_node_ids(graph: GraphFakosGraph) -> tuple[str, ...]:
    if not graph.nodes:
        return ()
    adjacency: dict[str, set[str]] = {node.id: set() for node in graph.nodes}
    for edge in graph.edges:
        if edge.source_id in adjacency and edge.target_id in adjacency:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)
    remaining = set(adjacency)
    components: list[set[str]] = []
    while remaining:
        start = next(iter(remaining))
        frontier: deque[str] = deque([start])
        seen = {start}
        remaining.remove(start)
        while frontier:
            node_id = frontier.popleft()
            for neighbor in adjacency.get(node_id, ()):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                remaining.discard(neighbor)
                frontier.append(neighbor)
        components.append(seen)
    if len(components) <= 1:
        return ()
    primary = max(components, key=len)
    disconnected = sorted(node_id for node_id in adjacency if node_id not in primary)
    return tuple(disconnected)


def load_provider_graph(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> GraphFakosGraph:
    graph = provider.load_graph(request)
    validate_graph(graph)
    return graph


def load_comparison_graph(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> GraphFakosGraph | None:
    if not isinstance(provider, GraphFakosComparisonProvider):
        return None
    graph = provider.load_comparison_graph(request)
    if graph is None:
        return None
    validate_graph(graph)
    return graph


def load_overlay_graphs(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> tuple[GraphFakosGraph, ...]:
    if not isinstance(provider, GraphFakosOverlayProvider):
        return ()
    graphs = provider.load_overlay_graphs(request)
    for graph in graphs:
        validate_graph(graph)
    return graphs


__all__ = [
    "analyze_graph",
    "diagnose_graph",
    "GraphFakosComparisonProvider",
    "GraphFakosGraphActionProvider",
    "GraphFakosKnowledgeCaptureProvider",
    "GraphFakosOverlayProvider",
    "GraphFakosProvider",
    "load_comparison_graph",
    "load_overlay_graphs",
    "load_provider_graph",
    "validate_graph",
]
