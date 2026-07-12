"""Provider-neutral graph query and filter evaluation."""

from __future__ import annotations

from collections import defaultdict
import shlex

from graphfakos.models import (
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
)
from graphfakos.provider import diagnose_graph
from graphfakos.ui.viewer.graph_ops import (
    _connected_node_ids,
    _graph_with_items,
    _node_cluster_id,
    _node_component_ids,
    _node_degree_map,
    _render_limited_graph,
)


def _graph_facets(graph: GraphFakosGraph) -> dict[str, tuple[str, ...]]:
    return {
        "node_kind": tuple(sorted({node.kind for node in graph.nodes if node.kind})),
        "edge_kind": tuple(sorted({edge.kind for edge in graph.edges if edge.kind})),
        "tag": tuple(sorted({tag for node in graph.nodes for tag in node.tags if tag})),
        "source": tuple(sorted({node.source for node in graph.nodes if node.source})),
    }


def _facet_values(graph: GraphFakosGraph, name: str) -> tuple[str, ...]:
    if graph.available_facets.get(name):
        return graph.available_facets[name]
    return _graph_facets(graph).get(name, ())


def _filtered_graph(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> GraphFakosGraph:
    nodes = _filtered_nodes(graph, request)
    node_ids = {node.id for node in nodes}
    edges = _filter_edges_by_request(
        tuple(
            edge
            for edge in graph.edges
            if edge.source_id in node_ids and edge.target_id in node_ids
        ),
        request,
    )
    return _render_limited_graph(
        _graph_with_items(graph, nodes, edges),
        request,
        preferred_node_ids={
            item_id
            for item_id in (
                request.focus_node_id,
                request.source_node_id,
                request.target_node_id,
                request.connected_to_node_id,
                request.pivot_node_id,
                *request.selected_node_ids,
            )
            if item_id
        },
        preferred_edge_id=request.selected_edge_id,
    )


def _filtered_nodes(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> tuple[GraphFakosNode, ...]:
    parsed_query = _parse_query(request.query)
    filters = request.filters
    min_score = _min_score(filters.get("min_score", ""))
    orphan_node_ids = set(diagnose_graph(graph).orphan_node_ids)
    degree_map = _node_degree_map(graph)
    connected_ids = _connected_node_ids(graph, request.connected_to_node_id)
    component_ids = _node_component_ids(graph)
    return tuple(
        node
        for node in graph.nodes
        if _node_matches_query(node, parsed_query)
        and _node_matches_filters(node, filters, min_score)
        and (request.show_orphans or node.id not in orphan_node_ids)
        and _node_matches_advanced_filters(
            node,
            graph,
            request,
            degree_map,
            connected_ids,
            component_ids,
        )
    )


def _node_matches_query(
    node: GraphFakosNode, parsed_query: dict[str, tuple[str, ...]]
) -> bool:
    free_text = parsed_query["terms"]
    if free_text and not all(_node_contains_text(node, term) for term in free_text):
        return False
    for value in parsed_query["id"]:
        if value.casefold() not in node.id.casefold():
            return False
    for value in parsed_query["label"]:
        if value.casefold() not in node.label.casefold():
            return False
    for value in parsed_query["summary"]:
        if value.casefold() not in node.summary.casefold():
            return False
    for value in parsed_query["kind"]:
        if value != node.kind:
            return False
    for value in parsed_query["tag"]:
        if value not in node.tags:
            return False
    for value in parsed_query["source"]:
        if value != node.source:
            return False
    for value in parsed_query["has"]:
        if value == "provenance" and not node.provenance_ids:
            return False
        if value == "citation" and not node.citation_ids:
            return False
        if value == "score" and node.score is None:
            return False
    if not _node_matches_score_filters(node, parsed_query["score"]):
        return False
    if not _node_matches_time_filters(node, parsed_query["time"]):
        return False
    if parsed_query["terms"] or any(
        parsed_query[key] for key in parsed_query if key != "terms"
    ):
        return True
    return True


def _node_contains_text(node: GraphFakosNode, term: str) -> bool:
    if not term:
        return True
    return (
        term in node.id.casefold()
        or term in node.label.casefold()
        or term in node.kind.casefold()
        or term in node.summary.casefold()
        or term in node.source.casefold()
        or any(term in tag.casefold() for tag in node.tags)
    )


def _node_matches_filters(
    node: GraphFakosNode,
    filters: dict[str, str],
    min_score: float | None,
) -> bool:
    if filters.get("node_kind") and node.kind != filters["node_kind"]:
        return False
    if filters.get("tag") and filters["tag"] not in node.tags:
        return False
    if filters.get("source") and node.source != filters["source"]:
        return False
    return min_score is None or (node.score is not None and node.score >= min_score)


def _node_matches_advanced_filters(
    node: GraphFakosNode,
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    degree_map: dict[str, int],
    connected_ids: set[str],
    component_ids: dict[str, str],
) -> bool:
    degree = degree_map.get(node.id, 0)
    if request.min_degree is not None and degree < request.min_degree:
        return False
    if request.max_degree is not None and degree > request.max_degree:
        return False
    if connected_ids and node.id not in connected_ids:
        return False
    if request.component_id and component_ids.get(node.id) != request.component_id:
        return False
    if request.evidence_filter and not _node_matches_evidence_filter(
        node, graph, request.evidence_filter
    ):
        return False
    return not request.cluster_id or _node_cluster_id(node) == request.cluster_id


def _node_matches_evidence_filter(
    node: GraphFakosNode,
    graph: GraphFakosGraph,
    evidence_filter: str,
) -> bool:
    provenance_ids = {item.id for item in graph.provenance}
    citation_ids = {item.id for item in graph.citations}
    if evidence_filter == "with_provenance":
        return bool(node.provenance_ids)
    if evidence_filter == "with_citation":
        return bool(node.citation_ids)
    if evidence_filter == "missing_provenance":
        return not node.provenance_ids or any(
            item_id not in provenance_ids for item_id in node.provenance_ids
        )
    if evidence_filter == "missing_citation":
        return not node.citation_ids or any(
            item_id not in citation_ids for item_id in node.citation_ids
        )
    if evidence_filter == "warnings":
        text = " ".join(graph.warnings).casefold()
        return node.id.casefold() in text or node.label.casefold() in text
    return True


def _filter_edges_by_request(
    edges: tuple[GraphFakosEdge, ...],
    request: GraphFakosRequest,
) -> tuple[GraphFakosEdge, ...]:
    edge_kind = request.filters.get("edge_kind", "")
    parsed_query = _parse_query(request.query)
    filtered = edges
    if edge_kind:
        filtered = tuple(edge for edge in filtered if edge.kind == edge_kind)
    query_edge_kinds = parsed_query["edge"]
    if query_edge_kinds:
        filtered = tuple(edge for edge in filtered if edge.kind in query_edge_kinds)
    if not request.show_neighbor_links and request.focus_node_id:
        filtered = tuple(
            edge
            for edge in filtered
            if request.focus_node_id in {edge.source_id, edge.target_id}
        )
    return filtered


def _min_score(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_query(query: str) -> dict[str, tuple[str, ...]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    try:
        tokens = shlex.split(query)
    except ValueError:
        tokens = query.split()
    for raw_token in tokens:
        comparison = _comparison_token(raw_token)
        if comparison is not None:
            name, normalized = comparison
            buckets[name].append(normalized)
            continue
        if ":" not in raw_token:
            buckets["terms"].append(raw_token.casefold())
            continue
        key, value = raw_token.split(":", 1)
        normalized_key = key.strip().casefold()
        normalized_value = value.strip()
        if not normalized_value:
            continue
        if normalized_key in {
            "kind",
            "tag",
            "source",
            "id",
            "label",
            "summary",
            "has",
            "edge",
        }:
            buckets[normalized_key].append(normalized_value.casefold())
            continue
        buckets["terms"].append(raw_token.casefold())
    return {
        key: tuple(values)
        for key, values in {
            "terms": buckets.get("terms", []),
            "kind": buckets.get("kind", []),
            "tag": buckets.get("tag", []),
            "source": buckets.get("source", []),
            "id": buckets.get("id", []),
            "label": buckets.get("label", []),
            "summary": buckets.get("summary", []),
            "has": buckets.get("has", []),
            "edge": buckets.get("edge", []),
            "score": buckets.get("score", []),
            "time": buckets.get("time", []),
        }.items()
    }


def _comparison_token(raw_token: str) -> tuple[str, str] | None:
    for prefix, name in (
        ("score>=", "score"),
        ("score<=", "score"),
        ("score>", "score"),
        ("score<", "score"),
        ("time>=", "time"),
        ("time<=", "time"),
        ("time>", "time"),
        ("time<", "time"),
    ):
        if raw_token.startswith(prefix) and raw_token[len(prefix) :]:
            return name, raw_token.casefold()
    return None


def _node_matches_score_filters(
    node: GraphFakosNode,
    tokens: tuple[str, ...],
) -> bool:
    if not tokens:
        return True
    if node.score is None:
        return False
    return all(_match_numeric_token(node.score, token, "score") for token in tokens)


def _node_matches_time_filters(
    node: GraphFakosNode,
    tokens: tuple[str, ...],
) -> bool:
    if not tokens:
        return True
    values = tuple(
        value for value in node.timestamps.values() if isinstance(value, str) and value
    )
    if not values:
        return False
    return all(
        any(_match_string_token(value, token, "time") for value in values)
        for token in tokens
    )


def _match_numeric_token(value: float, token: str, prefix: str) -> bool:
    operator, expected = _split_comparison_token(token, prefix)
    try:
        numeric = float(expected)
    except ValueError:
        return False
    if operator == ">=":
        return value >= numeric
    if operator == "<=":
        return value <= numeric
    if operator == ">":
        return value > numeric
    return value < numeric


def _match_string_token(value: str, token: str, prefix: str) -> bool:
    operator, expected = _split_comparison_token(token, prefix)
    current = value.casefold()
    if operator == ">=":
        return current >= expected
    if operator == "<=":
        return current <= expected
    if operator == ">":
        return current > expected
    return current < expected


def _split_comparison_token(token: str, prefix: str) -> tuple[str, str]:
    for operator in (">=", "<=", ">", "<"):
        marker = f"{prefix}{operator}"
        if token.startswith(marker):
            return operator, token[len(marker) :]
    raise ValueError(f"Unsupported comparison token: {token}")


def _active_query_terms(request: GraphFakosRequest) -> tuple[str, ...]:
    parsed = _parse_query(request.query)
    chips = [f"layout:{request.layout}"]
    if request.preset_id:
        chips.append(f"preset:{request.preset_id}")
    for key, values in parsed.items():
        for value in values:
            chips.append(value if key == "terms" else f"{key}:{value}")
    for key, value in request.filters.items():
        if value:
            chips.append(f"{key}:{value}")
    if request.render_limit:
        chips.append(f"render_limit:{request.render_limit}")
    return tuple(chips)
