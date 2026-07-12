"""Provider-neutral graph traversal, ranking, and render selection."""

from __future__ import annotations

from collections import defaultdict, deque

from graphfakos.models import (
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
)


def _neighborhood_node_ids(
    graph: GraphFakosGraph,
    node_id: str,
    max_depth: int,
) -> set[str]:
    visible = {node_id}
    frontier = {node_id}
    adjacency = _adjacency_map(graph)
    for _depth in range(max_depth):
        next_frontier: set[str] = set()
        for frontier_id in frontier:
            for _edge, neighbor_id in adjacency.get(frontier_id, ()):
                if neighbor_id not in visible:
                    next_frontier.add(neighbor_id)
        visible.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break
    return visible


def _graph_with_items(
    graph: GraphFakosGraph,
    nodes: tuple[GraphFakosNode, ...],
    edges: tuple[GraphFakosEdge, ...],
) -> GraphFakosGraph:
    return GraphFakosGraph(
        graph_id=graph.graph_id,
        label=graph.label,
        provider_id=graph.provider_id,
        provider_label=graph.provider_label,
        graph_role=graph.graph_role,
        capabilities=graph.capabilities,
        nodes=nodes,
        edges=edges,
        provenance=graph.provenance,
        citations=graph.citations,
        warnings=graph.warnings,
        stats=graph.stats,
        generated_at=graph.generated_at,
        snapshot=graph.snapshot,
        provider_details=graph.provider_details,
        capability_details=graph.capability_details,
        available_facets=graph.available_facets,
        provider_payload=graph.provider_payload,
    )


def _preferred_focus_node(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> GraphFakosNode | None:
    node_map = graph.node_map()
    for node_id in (
        request.focus_node_id,
        request.source_node_id,
        request.target_node_id,
    ):
        if node_id and node_id in node_map:
            return node_map[node_id]
    ranked = _ranked_nodes(graph, set())
    return ranked[0] if ranked else None


def _path_nodes(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> tuple[GraphFakosNode | None, GraphFakosNode | None]:
    node_map = graph.node_map()
    source = (
        node_map.get(request.source_node_id or "") if request.source_node_id else None
    )
    target = (
        node_map.get(request.target_node_id or "") if request.target_node_id else None
    )
    if source is not None and target is not None:
        return source, target
    if len(graph.nodes) < 2:
        return None, None
    ranked = _ranked_nodes(graph, set())
    if len(ranked) < 2:
        return graph.nodes[0], graph.nodes[-1]
    return ranked[0], ranked[1]


def _navigation_path_pair(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    selected_edge: GraphFakosEdge | None,
) -> tuple[GraphFakosNode | None, GraphFakosNode | None]:
    node_map = graph.node_map()
    if selected_edge is not None:
        source = node_map.get(selected_edge.source_id)
        target = node_map.get(selected_edge.target_id)
        if source is not None and target is not None:
            return source, target
    source_graph = visible_graph if visible_graph.nodes else graph
    if len(source_graph.nodes) < 2:
        return None, None
    ranked = _ranked_nodes(source_graph, set())
    if len(ranked) < 2:
        return source_graph.nodes[0], source_graph.nodes[-1]
    return ranked[0], ranked[1]


def _shortest_path_edges(
    graph: GraphFakosGraph,
    source_id: str,
    target_id: str,
) -> list[GraphFakosEdge]:
    frontier: deque[tuple[str, list[GraphFakosEdge]]] = deque([(source_id, [])])
    seen = {source_id}
    adjacency = _adjacency_map(graph)
    while frontier:
        node_id, path = frontier.popleft()
        if node_id == target_id:
            return path
        for edge, next_id in adjacency.get(node_id, ()):
            if next_id in seen:
                continue
            seen.add(next_id)
            frontier.append((next_id, [*path, edge]))
    return []


def _adjacency_map(
    graph: GraphFakosGraph,
) -> dict[str, tuple[tuple[GraphFakosEdge, str], ...]]:
    adjacency: dict[str, list[tuple[GraphFakosEdge, str]]] = defaultdict(list)
    for edge in graph.edges:
        adjacency[edge.source_id].append((edge, edge.target_id))
        adjacency[edge.target_id].append((edge, edge.source_id))
    return {key: tuple(value) for key, value in adjacency.items()}


def _connected_node_ids(graph: GraphFakosGraph, node_id: str) -> set[str]:
    if not node_id:
        return set()
    connected = {node_id}
    for edge, neighbor_id in _adjacency_map(graph).get(node_id, ()):
        connected.add(edge.source_id)
        connected.add(edge.target_id)
        connected.add(neighbor_id)
    return connected


def _component_groups(graph: GraphFakosGraph) -> dict[str, tuple[str, ...]]:
    adjacency = _adjacency_map(graph)
    remaining = {node.id for node in graph.nodes}
    components: dict[str, tuple[str, ...]] = {}
    index = 1
    while remaining:
        start = sorted(remaining)[0]
        queue = deque([start])
        seen = {start}
        while queue:
            current = queue.popleft()
            for _edge, neighbor_id in adjacency.get(current, ()):
                if neighbor_id not in seen:
                    seen.add(neighbor_id)
                    queue.append(neighbor_id)
        remaining -= seen
        components[f"component:{index}"] = tuple(sorted(seen))
        index += 1
    return components


def _node_component_ids(graph: GraphFakosGraph) -> dict[str, str]:
    return {
        node_id: component_id
        for component_id, node_ids in _component_groups(graph).items()
        for node_id in node_ids
    }


def _node_cluster_id(node: GraphFakosNode) -> str:
    value = node.provider_payload.get("cluster_id") or node.visual.group
    return value if isinstance(value, str) else ""


def _timeline_frames(graph: GraphFakosGraph) -> tuple[str, ...]:
    frames = sorted(
        {
            timestamp
            for node in graph.nodes
            for timestamp in node.timestamps.values()
            if timestamp
        }
    )
    return tuple(frames[:12])


def _node_degree_map(graph: GraphFakosGraph) -> dict[str, int]:
    degrees = {node.id: 0 for node in graph.nodes}
    for edge in graph.edges:
        if edge.source_id in degrees:
            degrees[edge.source_id] += 1
        if edge.target_id in degrees:
            degrees[edge.target_id] += 1
    return degrees


def _ranked_nodes(
    graph: GraphFakosGraph,
    preferred_node_ids: set[str],
) -> list[GraphFakosNode]:
    degree_map = _node_degree_map(graph)
    return sorted(
        graph.nodes,
        key=lambda node: (
            node.id not in preferred_node_ids,
            not node.visual.pinned,
            -degree_map.get(node.id, 0),
            -(node.score if node.score is not None else 0),
            node.label.casefold(),
        ),
    )


def _render_limited_graph(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    preferred_node_ids: set[str],
    preferred_edge_id: str | None,
) -> GraphFakosGraph:
    if len(graph.nodes) <= request.render_limit:
        return graph
    ranked_nodes = _ranked_nodes(graph, preferred_node_ids)
    visible_nodes = tuple(ranked_nodes[: request.render_limit])
    visible_ids = {node.id for node in visible_nodes}
    visible_edges = tuple(
        edge
        for edge in graph.edges
        if edge.source_id in visible_ids and edge.target_id in visible_ids
    )
    if preferred_edge_id and preferred_edge_id not in {
        edge.id for edge in visible_edges
    }:
        extra_edge = graph.edge_map().get(preferred_edge_id)
        if (
            extra_edge is not None
            and extra_edge.source_id in visible_ids
            and extra_edge.target_id in visible_ids
        ):
            visible_edges = (*visible_edges, extra_edge)
    stats = dict(graph.stats)
    stats["hidden_nodes"] = max(len(graph.nodes) - len(visible_nodes), 0)
    stats["hidden_edges"] = max(len(graph.edges) - len(visible_edges), 0)
    return _graph_with_items(
        GraphFakosGraph(
            graph_id=graph.graph_id,
            label=graph.label,
            provider_id=graph.provider_id,
            provider_label=graph.provider_label,
            graph_role=graph.graph_role,
            capabilities=graph.capabilities,
            nodes=graph.nodes,
            edges=graph.edges,
            provenance=graph.provenance,
            citations=graph.citations,
            warnings=graph.warnings,
            stats=stats,
            generated_at=graph.generated_at,
            provider_details=graph.provider_details,
            capability_details=graph.capability_details,
            available_facets=graph.available_facets,
            provider_payload=graph.provider_payload,
        ),
        visible_nodes,
        tuple(visible_edges),
    )
