"""Static graph viewer rendering."""

from __future__ import annotations

from html import escape
from math import cos, pi, sin
from urllib.parse import urlencode

from graphfakos.models import (
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvenance,
    GraphFakosRequest,
    GraphFakosScreen,
)
from graphfakos.provider import GraphFakosProvider, load_provider_graph

_SCREEN_NAV: tuple[tuple[GraphFakosScreen, str], ...] = (
    ("explore", "Explore"),
    ("neighborhood", "Neighborhood"),
    ("path", "Path"),
    ("provenance", "Provenance"),
    ("timeline", "Timeline"),
    ("provider_status", "Provider Status"),
    ("context_preview", "Context"),
)


def screen_manifest() -> tuple[dict[str, str], ...]:
    return tuple({"screen": screen, "label": label} for screen, label in _SCREEN_NAV)


def render_provider_path(
    provider: GraphFakosProvider,
    base_request: GraphFakosRequest,
    path: str,
    query: dict[str, list[str]],
) -> str:
    screen = _screen_from_path(path) or base_request.screen
    request = _request_from_query(base_request.with_screen(screen), query)
    graph = load_provider_graph(provider, request)
    return render_graph_viewer(graph, request)


def render_graph_viewer(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    body = _render_screen(graph, request)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(graph.label)} - GraphFakos</title>"
        f"{_STYLE}</head><body class='gf-page'><div class='gf-shell'>"
        f"{_nav(request.screen)}"
        "<main class='gf-content'>"
        f"{_header(graph, request)}"
        f"{_integration_panel(graph)}"
        f"{body}</main></div></body></html>"
    )


def _screen_from_path(path: str) -> GraphFakosScreen | None:
    value = path.strip("/") or "explore"
    aliases = {
        "": "explore",
        "providers": "provider_status",
        "provider-status": "provider_status",
        "context": "context_preview",
    }
    value = aliases.get(value, value)
    valid = {screen for screen, _label in _SCREEN_NAV}
    if value in valid:
        return value  # type: ignore[return-value]
    return None


def _request_from_query(
    request: GraphFakosRequest,
    query: dict[str, list[str]],
) -> GraphFakosRequest:
    filters = dict(request.filters)
    for key in ("node_kind", "edge_kind", "tag", "source", "min_score"):
        value = _first_query_value(query, key)
        if value:
            filters[key] = value
        elif key in query:
            filters.pop(key, None)
    return GraphFakosRequest(
        screen=request.screen,
        query=_first_query_value(query, "query") or request.query,
        focus_node_id=(
            _first_query_value(query, "focus_node_id")
            or _first_query_value(query, "node_id")
            or request.focus_node_id
        ),
        selected_edge_id=_first_query_value(query, "selected_edge_id")
        or request.selected_edge_id,
        source_node_id=_first_query_value(query, "source_node_id")
        or request.source_node_id,
        target_node_id=_first_query_value(query, "target_node_id")
        or request.target_node_id,
        max_depth=int(_first_query_value(query, "max_depth") or request.max_depth),
        filters=filters,
        layout=_first_query_value(query, "layout") or request.layout,
        include_provenance=request.include_provenance,
        include_provider_payload=request.include_provider_payload,
        limit=int(_first_query_value(query, "limit") or request.limit),
    )


def _first_query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key) or []
    return values[0] if values and values[0] else None


def _nav(active_screen: str) -> str:
    links = ""
    for screen, label in _SCREEN_NAV:
        current = 'aria-current="page"' if active_screen == screen else ""
        links += f"<a href='/{screen}' {current}>{escape(label)}</a>"
    return f"<nav class='gf-nav'><h1>GraphFakos</h1>{links}</nav>"


def _header(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    return (
        "<header class='gf-header'>"
        "<div><p class='gf-eyebrow'>Graph lens</p>"
        f"<h2>{escape(_screen_title(request.screen))}</h2>"
        f"<p>{escape(graph.label)}</p></div>"
        "<div class='gf-summary'>"
        f"{_badge(graph.graph_role, 'accent')}"
        f"{_badge(f'{len(graph.nodes)} nodes', 'blue')}"
        f"{_badge(f'{len(graph.edges)} edges', 'neutral')}"
        f"{_badge(graph.provider_label, 'neutral')}"
        "</div></header>"
    )


def _screen_title(screen: str) -> str:
    return dict(_SCREEN_NAV).get(screen, "Explore")


def _integration_panel(graph: GraphFakosGraph) -> str:
    role = _role_description(graph.graph_role)
    capabilities = tuple(graph.capabilities[:4])
    commands = _integration_commands(graph)
    command_list = "".join(f"<code>{escape(command)}</code>" for command in commands)
    return (
        "<section class='gf-panel gf-integration' "
        "aria-label='OpenMinion integration'>"
        "<div><h3>OpenMinion Integration</h3>"
        f"<p class='gf-empty'>{escape(role)}</p>"
        f"{_badges([(capability, 'blue') for capability in capabilities])}"
        "</div><div class='gf-code-list'>"
        f"{command_list}</div></section>"
    )


def _role_description(role: str) -> str:
    descriptions = {
        "memory": "Second-brain durable memory graph.",
        "source": "Third-brain observed source graph.",
        "document": "Document knowledge graph.",
        "code": "Code knowledge graph.",
        "artifact": "Artifact knowledge graph.",
        "hybrid": "Hybrid graph lens.",
        "third_party": "Third-party graph provider.",
    }
    return descriptions.get(role, f"{role.replace('_', ' ').title()} graph.")


def _integration_commands(graph: GraphFakosGraph) -> tuple[str, ...]:
    commands = graph.provider_payload.get("integration_commands")
    if isinstance(commands, (list, tuple)) and all(
        isinstance(command, str) for command in commands
    ):
        return tuple(commands)
    return (
        "graphfakos-ui --screen explore --serve --open",
        "graphfakos-ui --screen provider_status --html-out graphfakos-ui-preview.html --json",
    )


def _render_screen(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    if request.screen == "neighborhood":
        return _render_neighborhood(graph, request)
    if request.screen == "path":
        return _render_path(graph, request)
    if request.screen == "provenance":
        return _render_provenance(graph)
    if request.screen == "timeline":
        return _render_timeline(graph)
    if request.screen == "provider_status":
        return _render_provider_status(graph)
    if request.screen == "context_preview":
        return _render_context_preview(graph)
    return _render_explore(graph, request)


def _render_explore(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    filtered_graph = _filtered_graph(graph, request)
    focus = _selected_node(graph, request, filtered_graph.nodes)
    selected_edge = _selected_edge(graph, request)
    primary = (
        f"{_filter_toolbar(graph, request, '/explore')}"
        f"{_graph_canvas(filtered_graph, focus.id if focus else None, selected_edge.id if selected_edge else None)}"
        "<section class='gf-panel'><h3>Visible Nodes</h3>"
        f"{_node_cards(filtered_graph.nodes[: request.limit])}</section>"
    )
    secondary = _inspector(graph, focus, selected_edge)
    return _split(primary, secondary)


def _render_neighborhood(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    focus = _selected_node(graph, request, tuple(graph.nodes))
    if focus is None:
        return _panel("Neighborhood", _empty("No nodes are available."))
    visible_ids = _neighborhood_node_ids(graph, focus.id, max(request.max_depth, 1))
    neighbor_ids = visible_ids - {focus.id}
    neighbors = tuple(node for node in graph.nodes if node.id in neighbor_ids)
    edges = _filter_edges_by_request(
        tuple(
            edge
            for edge in graph.edges
            if edge.source_id in visible_ids and edge.target_id in visible_ids
        ),
        request,
    )
    neighborhood_graph = _graph_with_items(graph, (focus, *neighbors), edges)
    primary = (
        f"{_neighborhood_toolbar(graph, request, focus.id)}"
        f"{_graph_canvas(neighborhood_graph, focus.id, request.selected_edge_id)}"
    )
    primary += _panel(
        f"Around {focus.label}",
        f"<p class='gf-empty'>Depth {max(request.max_depth, 1)} neighborhood.</p>"
        f"{_node_cards(neighbors)}",
    )
    secondary = _inspector(graph, focus, _selected_edge(graph, request))
    return _split(primary, secondary)


def _neighborhood_node_ids(
    graph: GraphFakosGraph,
    node_id: str,
    max_depth: int,
) -> set[str]:
    visible = {node_id}
    frontier = {node_id}
    for _depth in range(max_depth):
        next_frontier: set[str] = set()
        for edge in graph.edges:
            if edge.source_id in frontier and edge.target_id not in visible:
                next_frontier.add(edge.target_id)
            if edge.target_id in frontier and edge.source_id not in visible:
                next_frontier.add(edge.source_id)
        visible.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break
    return visible


def _render_path(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    source, target = _path_nodes(graph, request)
    if source is None or target is None:
        return _panel("Path", _empty("At least two nodes are required."))
    path_edges = _shortest_path_edges(graph, source.id, target.id)
    path_node_ids = {source.id, target.id}
    for edge in path_edges:
        path_node_ids.add(edge.source_id)
        path_node_ids.add(edge.target_id)
    path_nodes = tuple(node for node in graph.nodes if node.id in path_node_ids)
    path_graph = _graph_with_items(graph, path_nodes, tuple(path_edges))
    primary = (
        f"{_path_toolbar(graph, request, source.id, target.id)}"
        f"{_graph_canvas(path_graph, source.id, request.selected_edge_id)}"
    )
    primary += _panel(
        f"{source.label} to {target.label}",
        _edge_list(tuple(path_edges)) if path_edges else _empty("No bounded path found."),
    )
    return _split(primary, _inspector(graph, source, _selected_edge(graph, request)))


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
        provider_payload=graph.provider_payload,
    )


def _render_provenance(graph: GraphFakosGraph) -> str:
    items = "".join(_provenance_card(item) for item in graph.provenance)
    citations = "".join(
        "<article class='gf-card'>"
        f"<h4>{escape(citation.label or citation.id)}</h4>"
        f"<p>{escape(citation.excerpt or citation.path or citation.uri)}</p>"
        f"{_badges([(citation.path, 'blue')] if citation.path else [])}"
        "</article>"
        for citation in graph.citations
    )
    return _split(
        _panel("Provenance", items or _empty("No provenance provided.")),
        _panel("Citations", citations or _empty("No citations provided.")),
    )


def _render_timeline(graph: GraphFakosGraph) -> str:
    rows = []
    for node in graph.nodes:
        for key, value in sorted(node.timestamps.items()):
            rows.append(f"{value} - {node.label} ({key})")
    return _panel("Timeline and Freshness", _list(rows))


def _render_provider_status(graph: GraphFakosGraph) -> str:
    status = {
        "provider_id": graph.provider_id,
        "provider_label": graph.provider_label,
        "graph_role": graph.graph_role,
        "capabilities": ", ".join(graph.capabilities),
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "provenance": len(graph.provenance),
        "citations": len(graph.citations),
        "generated_at": graph.generated_at,
    }
    return _split(
        _panel("Provider Status", _key_values(status)),
        _panel("Sample Nodes", _node_cards(graph.nodes[:5]))
        + _panel("Warnings", _list(graph.warnings)),
    )


def _render_context_preview(graph: GraphFakosGraph) -> str:
    items = [
        f"{node.label} - {node.kind} - score={node.score if node.score is not None else 'n/a'}"
        for node in sorted(
            graph.nodes,
            key=lambda item: item.score if item.score is not None else 0,
            reverse=True,
        )[:8]
    ]
    return _split(
        _panel("Context Assembly Preview", _list(items)),
        _panel(
            "Provider Contribution",
            _key_values(
                {
                    "provider": graph.provider_label,
                    "role": graph.graph_role,
                    "capabilities": ", ".join(graph.capabilities),
                }
            ),
        ),
    )


def _filter_toolbar(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    action: str,
) -> str:
    filters = request.filters
    return (
        "<section class='gf-toolbar' aria-label='Graph filters'>"
        f"<form method='get' action='{escape(action)}'>"
        f"<input name='query' value='{escape(request.query)}' "
        "placeholder='Search nodes, edges, provenance'>"
        f"{_select('node_kind', 'Node kind', _node_kinds(graph), filters.get('node_kind', ''))}"
        f"{_select('edge_kind', 'Edge kind', _edge_kinds(graph), filters.get('edge_kind', ''))}"
        f"{_select('tag', 'Tag', _node_tags(graph), filters.get('tag', ''))}"
        f"{_select('source', 'Source', _node_sources(graph), filters.get('source', ''))}"
        f"<input name='min_score' value='{escape(filters.get('min_score', ''))}' "
        "placeholder='Min score'>"
        f"<input type='hidden' name='layout' value='{escape(request.layout)}'>"
        f"<input type='hidden' name='limit' value='{request.limit}'>"
        "<button type='submit'>Filter</button>"
        "</form></section>"
    )


def _neighborhood_toolbar(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus_id: str,
) -> str:
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    return (
        "<section class='gf-toolbar' aria-label='Neighborhood controls'>"
        "<form method='get' action='/neighborhood'>"
        f"{_select_pairs('focus_node_id', 'Focus node', node_options, focus_id)}"
        f"<input name='max_depth' value='{max(request.max_depth, 1)}' "
        "placeholder='Depth'>"
        f"{_select('edge_kind', 'Edge kind', _edge_kinds(graph), request.filters.get('edge_kind', ''))}"
        "<button type='submit'>Expand</button>"
        "</form></section>"
    )


def _path_toolbar(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    source_id: str,
    target_id: str,
) -> str:
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    return (
        "<section class='gf-toolbar' aria-label='Path controls'>"
        "<form method='get' action='/path'>"
        f"{_select_pairs('source_node_id', 'Source node', node_options, source_id)}"
        f"{_select_pairs('target_node_id', 'Target node', node_options, target_id)}"
        f"{_select('edge_kind', 'Edge kind', _edge_kinds(graph), request.filters.get('edge_kind', ''))}"
        "<button type='submit'>Find Path</button>"
        "</form></section>"
    )


def _select(
    name: str,
    label: str,
    options: tuple[str, ...],
    selected: str,
) -> str:
    pairs = tuple((option, option) for option in options)
    return _select_pairs(name, label, pairs, selected)


def _select_pairs(
    name: str,
    label: str,
    options: tuple[tuple[str, str], ...],
    selected: str,
) -> str:
    html = f"<select name='{escape(name)}' aria-label='{escape(label)}'>"
    html += f"<option value=''>{escape(label)}</option>"
    for value, text in options:
        current = " selected" if value == selected else ""
        html += (
            f"<option value='{escape(value)}'{current}>"
            f"{escape(text)}</option>"
        )
    return f"{html}</select>"


def _node_kinds(graph: GraphFakosGraph) -> tuple[str, ...]:
    return tuple(sorted({node.kind for node in graph.nodes if node.kind}))


def _edge_kinds(graph: GraphFakosGraph) -> tuple[str, ...]:
    return tuple(sorted({edge.kind for edge in graph.edges if edge.kind}))


def _node_tags(graph: GraphFakosGraph) -> tuple[str, ...]:
    return tuple(sorted({tag for node in graph.nodes for tag in node.tags if tag}))


def _node_sources(graph: GraphFakosGraph) -> tuple[str, ...]:
    return tuple(sorted({node.source for node in graph.nodes if node.source}))


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
    return _graph_with_items(graph, nodes, edges)


def _filtered_nodes(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> tuple[GraphFakosNode, ...]:
    query = request.query.casefold().strip()
    filters = request.filters
    min_score = _min_score(filters.get("min_score", ""))
    return tuple(
        node
        for node in graph.nodes
        if _node_matches_query(node, query)
        and _node_matches_filters(node, filters, min_score)
    )


def _node_matches_query(node: GraphFakosNode, query: str) -> bool:
    if not query:
        return True
    return (
        query in node.label.casefold()
        or query in node.kind.casefold()
        or query in node.summary.casefold()
        or query in node.source.casefold()
        or any(query in tag.casefold() for tag in node.tags)
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
    if min_score is not None and (node.score is None or node.score < min_score):
        return False
    return True


def _filter_edges_by_request(
    edges: tuple[GraphFakosEdge, ...],
    request: GraphFakosRequest,
) -> tuple[GraphFakosEdge, ...]:
    edge_kind = request.filters.get("edge_kind", "")
    if not edge_kind:
        return edges
    return tuple(edge for edge in edges if edge.kind == edge_kind)


def _min_score(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _selected_node(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    candidates: tuple[GraphFakosNode, ...],
) -> GraphFakosNode | None:
    node_map = graph.node_map()
    if request.focus_node_id and request.focus_node_id in node_map:
        return node_map[request.focus_node_id]
    return candidates[0] if candidates else (graph.nodes[0] if graph.nodes else None)


def _selected_edge(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> GraphFakosEdge | None:
    if not request.selected_edge_id:
        return None
    return graph.edge_map().get(request.selected_edge_id)


def _path_nodes(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> tuple[GraphFakosNode | None, GraphFakosNode | None]:
    node_map = graph.node_map()
    source = node_map.get(request.source_node_id or "") if request.source_node_id else None
    target = node_map.get(request.target_node_id or "") if request.target_node_id else None
    if source is not None and target is not None:
        return source, target
    if len(graph.nodes) < 2:
        return None, None
    return graph.nodes[0], graph.nodes[-1]


def _shortest_path_edges(
    graph: GraphFakosGraph,
    source_id: str,
    target_id: str,
) -> list[GraphFakosEdge]:
    frontier: list[tuple[str, list[GraphFakosEdge]]] = [(source_id, [])]
    seen = {source_id}
    while frontier:
        node_id, path = frontier.pop(0)
        if node_id == target_id:
            return path
        for edge in graph.edges:
            if edge.source_id == node_id:
                next_id = edge.target_id
            elif edge.target_id == node_id:
                next_id = edge.source_id
            else:
                continue
            if next_id in seen:
                continue
            seen.add(next_id)
            frontier.append((next_id, [*path, edge]))
    return []


def _graph_canvas(
    graph: GraphFakosGraph,
    selected_id: str | None,
    selected_edge_id: str | None,
) -> str:
    if not graph.nodes:
        return _panel("Graph Canvas", _empty("No graph nodes."))
    width = 920
    height = 460
    center_x = width / 2
    center_y = height / 2
    radius = min(width, height) * 0.34
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(graph.nodes):
        angle = (2 * pi * index / max(len(graph.nodes), 1)) - (pi / 2)
        x = node.visual.x if node.visual.x is not None else center_x + radius * cos(angle)
        y = node.visual.y if node.visual.y is not None else center_y + radius * sin(angle)
        positions[node.id] = (x, y)
    edge_lines = ""
    for edge in graph.edges:
        if edge.source_id not in positions or edge.target_id not in positions:
            continue
        x1, y1 = positions[edge.source_id]
        x2, y2 = positions[edge.target_id]
        selected = "true" if edge.id == selected_edge_id else "false"
        edge_lines += (
            f"<a href='{_explore_href(selected_edge_id=edge.id, focus_node_id=selected_id)}'>"
            f"<line class='gf-edge' data-selected='{selected}' x1='{x1:.1f}' y1='{y1:.1f}' "
            f"x2='{x2:.1f}' y2='{y2:.1f}'><title>{escape(edge.label or edge.kind)}</title></line>"
            "</a>"
        )
    node_marks = ""
    for node in graph.nodes:
        x, y = positions[node.id]
        selected = "true" if node.id == selected_id else "false"
        node_marks += (
            f"<a href='{_explore_href(focus_node_id=node.id)}'>"
            f"<g class='gf-node' data-kind='{escape(node.kind)}' data-selected='{selected}'>"
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{_node_radius(node)}'></circle>"
            f"<text x='{x:.1f}' y='{y + 28:.1f}' text-anchor='middle'>{escape(node.label[:24])}</text>"
            f"<title>{escape(node.summary or node.label)}</title></g></a>"
        )
    return (
        "<section class='gf-panel'><h3>Graph Canvas</h3>"
        f"<svg class='gf-canvas' viewBox='0 0 {width} {height}' "
        "role='img' aria-label='GraphFakos graph canvas'>"
        f"{edge_lines}{node_marks}</svg></section>"
    )


def _explore_href(
    *,
    focus_node_id: str | None = None,
    selected_edge_id: str | None = None,
) -> str:
    query = {
        key: value
        for key, value in {
            "focus_node_id": focus_node_id,
            "selected_edge_id": selected_edge_id,
        }.items()
        if value
    }
    return "/explore" + (f"?{urlencode(query)}" if query else "")


def _node_radius(node: GraphFakosNode) -> int:
    if node.score is None:
        return 18
    return max(16, min(28, int(16 + node.score * 10)))


def _inspector(
    graph: GraphFakosGraph,
    node: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    if node is None:
        return _panel("Inspector", _empty("Select a node."))
    incident = tuple(
        edge
        for edge in graph.edges
        if edge.source_id == node.id or edge.target_id == node.id
    )
    provenance = tuple(
        item for item in graph.provenance if item.id in set(node.provenance_ids)
    )
    body = (
        f"{_badges([(node.kind, 'accent'), *[(tag, 'blue') for tag in node.tags[:4]]])}"
        f"<p>{escape(node.summary or node.source or node.id)}</p>"
        f"{_key_values(_node_metadata(node))}"
        "<h3>Connections</h3>"
        f"{_edge_list(incident)}"
        "<h3>Selected Edge</h3>"
        f"{_edge_detail(graph, selected_edge)}"
        "<h3>Provenance</h3>"
        f"{''.join(_provenance_card(item) for item in provenance) or _empty('No node provenance.')}"
    )
    return _panel("Inspector", body)


def _edge_detail(
    graph: GraphFakosGraph,
    edge: GraphFakosEdge | None,
) -> str:
    if edge is None:
        return _empty("Click an edge to inspect its relationship metadata.")
    node_map = graph.node_map()
    source = node_map.get(edge.source_id)
    target = node_map.get(edge.target_id)
    provenance = tuple(
        item for item in graph.provenance if item.id in set(edge.provenance_ids)
    )
    metadata = {
        "id": edge.id,
        "label": edge.label,
        "source": source.label if source else edge.source_id,
        "target": target.label if target else edge.target_id,
        "weight": edge.weight,
        "confidence": edge.confidence,
    }
    return (
        f"{_badges([(edge.kind, 'accent'), (edge.direction, 'blue')])}"
        f"{_key_values(metadata)}"
        f"{''.join(_provenance_card(item) for item in provenance)}"
    )


def _node_metadata(node: GraphFakosNode) -> dict[str, object]:
    metadata: dict[str, object] = {
        "id": node.id,
        "source": node.source,
    }
    if node.score is not None:
        metadata["score"] = node.score
    if node.confidence is not None:
        metadata["confidence"] = node.confidence
    metadata.update(node.timestamps)
    return metadata


def _node_cards(nodes: tuple[GraphFakosNode, ...]) -> str:
    if not nodes:
        return _empty("No nodes match.")
    cards = ""
    for node in nodes:
        cards += (
            "<article class='gf-card'>"
            f"<div>{_badge(node.kind, 'accent')}</div>"
            f"<h4><a href='{_explore_href(focus_node_id=node.id)}'>{escape(node.label)}</a></h4>"
            f"<p>{escape(node.summary or node.id)}</p>"
            f"{_badges([(tag, 'blue') for tag in node.tags[:3]])}</article>"
        )
    return cards


def _edge_list(edges: tuple[GraphFakosEdge, ...]) -> str:
    if not edges:
        return _empty("No edges.")
    return _list(
        [
            f"{edge.source_id} -> {edge.target_id} ({edge.label or edge.kind})"
            for edge in edges
        ]
    )


def _provenance_card(item: GraphFakosProvenance) -> str:
    return (
        "<article class='gf-card'>"
        f"<h4>{escape(item.source_label or item.id)}</h4>"
        f"{_badges([(item.source_type, 'accent')] if item.source_type else [])}"
        f"<p>{escape(item.excerpt or item.source_uri or item.id)}</p>"
        f"{_key_values({'observed_at': item.observed_at, 'confidence': item.confidence})}"
        "</article>"
    )


def _split(primary: str, secondary: str) -> str:
    return f"<section class='gf-layout'><div>{primary}</div><aside>{secondary}</aside></section>"


def _panel(title: str, body: str) -> str:
    return f"<section class='gf-panel'><h3>{escape(title)}</h3>{body}</section>"


def _list(items: list[str] | tuple[str, ...]) -> str:
    if not items:
        return _empty("No items.")
    return "<ul class='gf-list'>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _key_values(payload: dict[str, object]) -> str:
    rows = ""
    for key, value in payload.items():
        if value in (None, ""):
            continue
        rows += f"<dt>{escape(str(key))}</dt><dd>{escape(str(value))}</dd>"
    return f"<dl class='gf-kv'>{rows}</dl>" if rows else _empty("No metadata.")


def _empty(text: str) -> str:
    return f"<p class='gf-empty'>{escape(text)}</p>"


def _badges(items: list[tuple[str, str]] | tuple[tuple[str, str], ...]) -> str:
    return "<div class='gf-badges'>" + "".join(_badge(text, tone) for text, tone in items if text) + "</div>"


def _badge(text: str, tone: str) -> str:
    tone = tone or "neutral"
    return f"<span class='gf-badge' data-tone='{escape(tone)}'>{escape(text)}</span>"


_STYLE = """
<style>
:root {
  color-scheme: light;
  --gf-bg: #f6f7f3;
  --gf-ink: #17211d;
  --gf-muted: #66716c;
  --gf-line: #d8ded7;
  --gf-panel: #ffffff;
  --gf-soft: #eef2ee;
  --gf-accent: #246c5c;
  --gf-accent-soft: #ddf0eb;
  --gf-blue: #345c8c;
  --gf-blue-soft: #e2eaf6;
}
* { box-sizing: border-box; }
body.gf-page {
  margin: 0;
  background: var(--gf-bg);
  color: var(--gf-ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  line-height: 1.45;
}
.gf-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 224px minmax(0, 1fr);
}
.gf-nav {
  border-right: 1px solid var(--gf-line);
  background: #fbfcfa;
  padding: 20px 14px;
}
.gf-nav h1 {
  margin: 0 0 18px;
  font-size: 18px;
}
.gf-nav a {
  display: flex;
  align-items: center;
  min-height: 36px;
  margin: 4px 0;
  padding: 8px 10px;
  border-radius: 8px;
  color: var(--gf-muted);
  text-decoration: none;
  font-size: 14px;
}
.gf-nav a[aria-current="page"] {
  background: var(--gf-accent-soft);
  color: var(--gf-accent);
  font-weight: 700;
}
.gf-content {
  min-width: 0;
  padding: 24px;
}
.gf-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: start;
  margin-bottom: 18px;
}
.gf-eyebrow {
  margin: 0 0 4px;
  color: var(--gf-muted);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
}
.gf-header h2 {
  margin: 0;
  font-size: 30px;
  line-height: 1.1;
}
.gf-header p {
  margin: 8px 0 0;
  color: var(--gf-muted);
}
.gf-summary,
.gf-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.gf-summary { justify-content: flex-end; }
.gf-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, .8fr);
  gap: 16px;
  align-items: start;
}
.gf-integration {
  display: grid;
  grid-template-columns: minmax(220px, .7fr) minmax(0, 1.3fr);
  gap: 12px;
  align-items: start;
}
.gf-panel {
  background: var(--gf-panel);
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.gf-panel h3 {
  margin: 0 0 12px;
  font-size: 16px;
}
.gf-toolbar { margin-bottom: 16px; }
.gf-toolbar form {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) repeat(4, minmax(120px, .45fr)) auto auto;
  gap: 8px;
}
.gf-toolbar input,
.gf-toolbar select {
  min-width: 0;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
}
.gf-toolbar button {
  border: 1px solid var(--gf-accent);
  border-radius: 8px;
  background: var(--gf-accent);
  color: white;
  padding: 10px 14px;
  font: inherit;
  font-weight: 700;
}
.gf-canvas {
  width: 100%;
  min-height: 360px;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  background: #fbfcfa;
}
.gf-edge {
  stroke: #9ea9a2;
  stroke-width: 1.5;
}
.gf-edge[data-selected="true"] {
  stroke: var(--gf-blue);
  stroke-width: 4;
}
.gf-edge:hover {
  stroke: var(--gf-accent);
  stroke-width: 3;
}
.gf-node circle {
  fill: var(--gf-accent-soft);
  stroke: var(--gf-accent);
  stroke-width: 2;
}
.gf-node[data-selected="true"] circle {
  fill: var(--gf-blue-soft);
  stroke: var(--gf-blue);
  stroke-width: 3;
}
.gf-node text {
  fill: var(--gf-ink);
  font-size: 12px;
  font-weight: 700;
}
.gf-card {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 12px;
  background: #fff;
  margin-bottom: 10px;
  overflow-wrap: anywhere;
}
.gf-card h4 {
  margin: 8px 0;
  font-size: 15px;
}
.gf-card p { margin: 8px 0; }
.gf-badge {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--gf-soft);
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 700;
}
.gf-badge[data-tone="accent"] {
  background: var(--gf-accent-soft);
  color: var(--gf-accent);
}
.gf-badge[data-tone="blue"] {
  background: var(--gf-blue-soft);
  color: var(--gf-blue);
}
.gf-list {
  display: grid;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.gf-list li {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 9px 10px;
  background: #fff;
  overflow-wrap: anywhere;
}
.gf-kv {
  display: grid;
  grid-template-columns: minmax(100px, .45fr) minmax(0, 1fr);
  gap: 8px 12px;
  margin: 0;
}
.gf-kv dt {
  color: var(--gf-muted);
  font-size: 13px;
}
.gf-kv dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.gf-empty {
  margin: 0;
  color: var(--gf-muted);
}
.gf-code-list {
  display: grid;
  gap: 8px;
  margin: 0;
}
.gf-code-list code {
  display: block;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  background: #fbfcfa;
  padding: 9px 10px;
  color: var(--gf-ink);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  overflow-wrap: anywhere;
}
a {
  color: var(--gf-accent);
  text-decoration: none;
}
@media (max-width: 840px) {
  .gf-shell { grid-template-columns: 1fr; }
  .gf-nav { border-right: 0; border-bottom: 1px solid var(--gf-line); }
  .gf-layout,
  .gf-integration,
  .gf-header,
  .gf-toolbar form { grid-template-columns: 1fr; }
  .gf-summary { justify-content: flex-start; }
}
</style>
"""


__all__ = [
    "render_graph_viewer",
    "render_provider_path",
    "screen_manifest",
]
