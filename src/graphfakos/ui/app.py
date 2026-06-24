"""Static graph viewer rendering."""

from __future__ import annotations

from collections import defaultdict, deque
from html import escape
from math import cos, pi, sin
from urllib.parse import urlencode

from graphfakos.models import (
    GraphFakosCitation,
    GraphFakosDiagnostics,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvenance,
    GraphFakosRequest,
    GraphFakosScreen,
)
from graphfakos.provider import (
    GraphFakosProvider,
    diagnose_graph,
    load_comparison_graph,
    load_overlay_graphs,
    load_provider_graph,
)

_SCREEN_NAV: tuple[tuple[GraphFakosScreen, str], ...] = (
    ("explore", "Explore"),
    ("neighborhood", "Neighborhood"),
    ("path", "Path"),
    ("provenance", "Provenance"),
    ("timeline", "Timeline"),
    ("diff", "Diff"),
    ("provider_status", "Provider Status"),
    ("context_preview", "Context"),
)


def screen_manifest() -> tuple[dict[str, str], ...]:
    summaries = {
        "explore": "Filter the graph, select nodes, and inspect relationships.",
        "neighborhood": "Expand one focus node to inspect nearby graph structure.",
        "path": "Trace the shortest visible path between two graph nodes.",
        "provenance": "Review provenance records and graph citations together.",
        "timeline": "Scan graph timestamps and freshness-oriented metadata.",
        "diff": "Compare one graph snapshot with a baseline or overlay provider view.",
        "provider_status": "Inspect provider metadata, capabilities, and graph health.",
        "context_preview": "Preview the graph context most likely to be surfaced.",
    }
    return tuple(
        {
            "screen": screen,
            "label": label,
            "route": f"/{screen}",
            "summary": summaries[screen],
        }
        for screen, label in _SCREEN_NAV
    )


def render_provider_path(
    provider: GraphFakosProvider,
    base_request: GraphFakosRequest,
    path: str,
    query: dict[str, list[str]],
) -> str:
    screen = _screen_from_path(path) or base_request.screen
    request = _request_from_query(base_request.with_screen(screen), query)
    graph = load_provider_graph(provider, request)
    comparison_graph = load_comparison_graph(provider, request)
    overlay_graphs = load_overlay_graphs(provider, request)
    return render_graph_viewer(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )


def render_graph_viewer(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None = None,
    overlay_graphs: tuple[GraphFakosGraph, ...] = (),
) -> str:
    body = render_graph_fragment(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(graph.label)} - GraphFakos</title>"
        f"{_STYLE}</head><body class='gf-page'><div class='gf-shell'>"
        f"{_nav(request)}"
        f"{body}</div></body></html>"
    )


def _screen_from_path(path: str) -> GraphFakosScreen | None:
    value = path.strip("/") or "explore"
    aliases = {
        "": "explore",
        "providers": "provider_status",
        "provider-status": "provider_status",
        "context": "context_preview",
        "compare": "diff",
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
        comparison_graph_id=_first_query_value(query, "comparison_graph_id")
        or request.comparison_graph_id,
        max_depth=int(_first_query_value(query, "max_depth") or request.max_depth),
        filters=filters,
        layout=_first_query_value(query, "layout") or request.layout,
        include_provenance=request.include_provenance,
        include_provider_payload=request.include_provider_payload,
        limit=int(_first_query_value(query, "limit") or request.limit),
        render_limit=int(_first_query_value(query, "render_limit") or request.render_limit),
    )


def _first_query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key) or []
    return values[0] if values and values[0] else None


def build_viewer_route(
    request: GraphFakosRequest,
    *,
    screen: GraphFakosScreen | None = None,
    overrides: dict[str, str | int | None] | None = None,
) -> str:
    return _route_href(request, screen=screen, overrides=overrides)


def parse_viewer_request(
    path: str,
    query: dict[str, list[str]],
    *,
    base_request: GraphFakosRequest | None = None,
) -> GraphFakosRequest:
    request = base_request or GraphFakosRequest()
    screen = _screen_from_path(path) or request.screen
    return _request_from_query(request.with_screen(screen), query)


def query_syntax_reference() -> tuple[dict[str, str], ...]:
    return (
        {"token": "kind:<value>", "meaning": "Filter nodes by provider-neutral node kind."},
        {"token": "tag:<value>", "meaning": "Filter nodes that include one graph tag."},
        {"token": "source:<value>", "meaning": "Filter nodes by provider-declared source label."},
        {"token": "id:<value>", "meaning": "Match node ids directly."},
        {"token": "label:<value>", "meaning": "Match node labels directly."},
        {"token": "summary:<value>", "meaning": "Match node summaries directly."},
        {"token": "edge:<value>", "meaning": "Filter visible edges by edge kind."},
        {"token": "has:provenance", "meaning": "Require provenance references on matched nodes."},
        {"token": "has:citation", "meaning": "Require citation references on matched nodes."},
        {"token": "has:score", "meaning": "Require scored nodes."},
    )


def render_graph_fragment(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None = None,
    overlay_graphs: tuple[GraphFakosGraph, ...] = (),
) -> str:
    body = _render_screen(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )
    return (
        "<main class='gf-content gf-embed-root' data-graphfakos-embed='true'>"
        f"{_header(graph, request, comparison_graph, overlay_graphs)}"
        f"{_integration_panel(graph, request, comparison_graph, overlay_graphs)}"
        f"{body}</main>"
    )


def _route_href(
    request: GraphFakosRequest,
    *,
    screen: GraphFakosScreen | None = None,
    overrides: dict[str, str | int | None] | None = None,
) -> str:
    route = f"/{screen or request.screen}"
    payload: dict[str, str | int] = {}
    for key, value in request.to_dict().items():
        if key == "screen":
            continue
        if isinstance(value, dict):
            for filter_key, filter_value in value.items():
                if filter_value not in ("", None):
                    payload[filter_key] = filter_value
            continue
        if value not in ("", None, False):
            payload[key] = value
    if overrides:
        for key, value in overrides.items():
            if value in ("", None):
                payload.pop(key, None)
                continue
            payload[key] = value
    return route + (f"?{urlencode(payload)}" if payload else "")


def _nav(request: GraphFakosRequest) -> str:
    links = ""
    for screen, label in _SCREEN_NAV:
        current = 'aria-current="page"' if request.screen == screen else ""
        links += f"<a href='{_route_href(request, screen=screen)}' {current}>{escape(label)}</a>"
    return f"<nav class='gf-nav'><h1>GraphFakos</h1>{links}</nav>"


def _header(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    overlay_summary = ""
    if overlay_graphs:
        overlay_summary = _badge(f"{len(overlay_graphs)} overlay graph(s)", "blue")
    diff_summary = ""
    if comparison_graph is not None:
        diff_summary = _badge(f"compare {comparison_graph.provider_label}", "neutral")
    snapshot_note = ""
    if graph.snapshot is not None:
        snapshot_note = (
            f"<p class='gf-note'>Snapshot {escape(graph.snapshot.label or graph.snapshot.snapshot_id)}"
            f"{' generated ' + escape(graph.snapshot.created_at) if graph.snapshot.created_at else ''}.</p>"
        )
    return (
        "<header class='gf-header'>"
        "<div><p class='gf-eyebrow'>Graph lens</p>"
        f"<h2>{escape(_screen_title(request.screen))}</h2>"
        f"<p>{escape(graph.label)}</p>"
        f"<p class='gf-note'>{escape(_layout_description(request.layout))}</p>"
        f"{snapshot_note}</div>"
        "<div class='gf-summary'>"
        f"{_badge(graph.graph_role, 'accent')}"
        f"{_badge(f'{len(graph.nodes)} nodes', 'blue')}"
        f"{_badge(f'{len(graph.edges)} edges', 'neutral')}"
        f"{_badge(graph.provider_label, 'neutral')}"
        f"{diff_summary}{overlay_summary}"
        "</div></header>"
    )


def _screen_title(screen: str) -> str:
    return dict(_SCREEN_NAV).get(screen, "Explore")


def _layout_description(layout: str) -> str:
    labels = {
        "force": "Balanced graph layout for general exploration.",
        "circle": "Circular layout that keeps every node visible.",
        "grouped": "Grouped layout that clusters nodes by kind.",
        "timeline": "Timeline-aware layout for timestamped graph items.",
        "focus": "Focus layout that centers the selected or active node.",
    }
    return labels.get(layout, f"{layout.title()} layout.")


def _integration_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    role = _role_description(graph.graph_role)
    capabilities = tuple(graph.capabilities[:4])
    commands = _integration_commands(graph)
    summary = _integration_summary(graph)
    command_list = "".join(f"<code>{escape(command)}</code>" for command in commands)
    deep_link = _route_href(request)
    embed_path = _route_href(request, overrides={"render_limit": min(request.render_limit, 60)})
    comparison_note = ""
    if comparison_graph is not None:
        comparison_note = (
            "<p class='gf-note'>"
            f"Diff is available against {escape(comparison_graph.provider_label)}."
            "</p>"
        )
    overlay_note = ""
    if overlay_graphs:
        overlay_note = (
            "<p class='gf-note'>"
            f"{len(overlay_graphs)} overlay provider graph(s) are available for side-by-side review."
            "</p>"
        )
    return (
        "<section class='gf-panel gf-integration' "
        "aria-label='Package integration'>"
        "<div><h3>Integration Commands</h3>"
        f"<p class='gf-empty'>{escape(role)}</p>"
        f"<p>{escape(summary)}</p>"
        "<p class='gf-note'>OpenMinion Integration and other host previews can "
        "reuse the same provider-neutral routes.</p>"
        f"{comparison_note}{overlay_note}"
        f"{_badges([(capability, 'blue') for capability in capabilities])}"
        "</div><div class='gf-code-list'>"
        f"{command_list}"
        f"<code>Deep link: {escape(deep_link)}</code>"
        f"<code>Embed route: {escape(embed_path)}</code>"
        f"<code>Query syntax: {escape(', '.join(item['token'] for item in query_syntax_reference()[:4]))}</code>"
        "</div></section>"
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


def _integration_summary(graph: GraphFakosGraph) -> str:
    summary = graph.provider_payload.get("integration_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    return (
        f"Use these commands to preview the {graph.provider_label} graph through "
        "the shared GraphFakos workbench."
    )


def _render_screen(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    if request.screen == "neighborhood":
        return _render_neighborhood(graph, request)
    if request.screen == "path":
        return _render_path(graph, request)
    if request.screen == "provenance":
        return _render_provenance(graph)
    if request.screen == "timeline":
        return _render_timeline(graph)
    if request.screen == "diff":
        return _render_diff(graph, request, comparison_graph, overlay_graphs)
    if request.screen == "provider_status":
        return _render_provider_status(graph, overlay_graphs)
    if request.screen == "context_preview":
        return _render_context_preview(graph)
    return _render_explore(graph, request)


def _render_explore(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    filtered_graph = _filtered_graph(graph, request)
    focus = _selected_node(graph, request, filtered_graph.nodes)
    selected_edge = _selected_edge(graph, request)
    active_query = _active_query_terms(request)
    primary = (
        f"{_filter_toolbar(graph, request, '/explore')}"
        f"{_graph_canvas(filtered_graph, request, focus.id if focus else None, selected_edge.id if selected_edge else None)}"
        f"{_selection_summary(filtered_graph, focus, selected_edge)}"
        f"{_query_summary(active_query)}"
        "<section class='gf-panel'><h3>Visible Nodes</h3>"
        f"{_node_cards(filtered_graph.nodes[: request.limit], request)}</section>"
    )
    secondary = _inspector(graph, focus, selected_edge)
    return _split(primary, secondary)


def _render_neighborhood(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    focus = _selected_node(graph, request, tuple(graph.nodes))
    if focus is None:
        return _panel(
            "Neighborhood",
            _empty("No nodes are available for neighborhood expansion."),
        )
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
        f"{_graph_canvas(neighborhood_graph, request, focus.id, request.selected_edge_id)}"
    )
    primary += _panel(
        f"Around {focus.label}",
        f"<p class='gf-empty'>Depth {max(request.max_depth, 1)} neighborhood.</p>"
        f"{_node_cards(neighbors, request) if neighbors else _empty('No neighboring nodes match this view yet.')}",
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


def _render_path(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    source, target = _path_nodes(graph, request)
    if source is None or target is None:
        return _panel(
            "Path",
            _empty("At least two graph nodes are required before a path can be explored."),
        )
    path_edges = _shortest_path_edges(graph, source.id, target.id)
    path_node_ids = {source.id, target.id}
    for edge in path_edges:
        path_node_ids.add(edge.source_id)
        path_node_ids.add(edge.target_id)
    path_nodes = tuple(node for node in graph.nodes if node.id in path_node_ids)
    path_graph = _graph_with_items(graph, path_nodes, tuple(path_edges))
    primary = (
        f"{_path_toolbar(graph, request, source.id, target.id)}"
        f"{_graph_canvas(path_graph, request, source.id, request.selected_edge_id)}"
    )
    primary += _panel(
        f"{source.label} to {target.label}",
        _path_summary(source, target, path_edges),
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
        snapshot=graph.snapshot,
        provider_details=graph.provider_details,
        capability_details=graph.capability_details,
        available_facets=graph.available_facets,
        provider_payload=graph.provider_payload,
    )


def _render_provenance(graph: GraphFakosGraph) -> str:
    items = "".join(_provenance_card(item) for item in graph.provenance)
    citations = "".join(_citation_card(citation) for citation in graph.citations)
    return _split(
        _panel(
            "Provenance",
            _summary_note(
                f"{len(graph.provenance)} provenance record(s) support this graph view."
            )
            + (items or _empty("No provenance provided.")),
        ),
        _panel(
            "Citations",
            _summary_note(f"{len(graph.citations)} citation reference(s) are available.")
            + (citations or _empty("No citations provided.")),
        ),
    )


def _render_timeline(graph: GraphFakosGraph) -> str:
    rows = []
    for node in graph.nodes:
        for key, value in sorted(node.timestamps.items()):
            rows.append(f"{value} - {node.label} ({key})")
    return _panel(
        "Timeline and Freshness",
        _summary_note(
            f"{len(rows)} timestamp event(s) are visible across {len(graph.nodes)} node(s)."
        )
        + _list(rows),
    )


def _render_diff(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    if comparison_graph is None:
        return _split(
            _panel(
                "Snapshot Diff",
                _empty("This provider does not expose a comparison snapshot yet."),
            ),
            _panel("Overlay Providers", _overlay_summary(overlay_graphs)),
        )
    diff = _graph_diff(graph, comparison_graph)
    left = _panel(
        "Snapshot Diff",
        _summary_note(
            f"Comparing {graph.provider_label} against {comparison_graph.provider_label}."
        )
        + _key_values(diff["summary"])
        + _diff_section("Added nodes", diff["added_nodes"])
        + _diff_section("Removed nodes", diff["removed_nodes"])
        + _diff_section("Added edges", diff["added_edges"])
        + _diff_section("Removed edges", diff["removed_edges"]),
    )
    right = _panel("Overlay Providers", _overlay_summary(overlay_graphs))
    return _split(left, right)


def _render_provider_status(
    graph: GraphFakosGraph,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    diagnostics = diagnose_graph(graph)
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
    if graph.snapshot is not None:
        status["snapshot"] = graph.snapshot.label or graph.snapshot.snapshot_id
        status["snapshot_created_at"] = graph.snapshot.created_at
    return _split(
        _panel(
            "Provider Status",
            _key_values(status)
            + _provider_details(graph)
            + _capability_details(graph)
            + _facet_details(graph),
        ),
        _panel("Graph Health", _graph_health(diagnostics))
        + _panel("Sample Nodes", _node_cards(graph.nodes[:5], GraphFakosRequest(screen="provider_status")))
        + _panel("Overlay Providers", _overlay_summary(overlay_graphs))
        + _panel("Query Syntax", _query_syntax_panel())
        + _panel("Warnings", _list(graph.warnings)),
    )


def _graph_health(diagnostics: GraphFakosDiagnostics) -> str:
    tone = "accent" if diagnostics.healthy else "blue"
    summary = (
        _badges(
            (
                ("healthy" if diagnostics.healthy else "needs review", tone),
                (f"{diagnostics.node_count} nodes", "neutral"),
                (f"{diagnostics.edge_count} edges", "neutral"),
            )
        )
        + _key_values(
            {
                "provenance": diagnostics.provenance_count,
                "citations": diagnostics.citation_count,
                "orphan nodes": len(diagnostics.orphan_node_ids),
                "duplicate edges": len(diagnostics.duplicate_edge_ids),
                "unknown provenance refs": len(diagnostics.unknown_provenance_ids),
                "unknown citation refs": len(diagnostics.unknown_citation_ids),
            }
        )
    )
    details = (
        _diagnostic_list("Orphan nodes", diagnostics.orphan_node_ids)
        + _diagnostic_list("Duplicate edge ids", diagnostics.duplicate_edge_ids)
        + _diagnostic_list("Unknown provenance ids", diagnostics.unknown_provenance_ids)
        + _diagnostic_list("Unknown citation ids", diagnostics.unknown_citation_ids)
    )
    return summary + (details if details else _empty("No graph diagnostics."))


def _diagnostic_list(title: str, items: tuple[str, ...]) -> str:
    if not items:
        return ""
    return f"<h4>{escape(title)}</h4>{_list(items)}"


def _render_context_preview(graph: GraphFakosGraph) -> str:
    ranked_nodes = tuple(
        sorted(
            graph.nodes,
            key=lambda item: item.score if item.score is not None else 0,
            reverse=True,
        )[:8]
    )
    return _split(
        _panel(
            "Context Assembly Preview",
            _summary_note(
                f"Top {len(ranked_nodes)} node(s) are ranked for reusable viewer context."
            )
            + _context_cards(ranked_nodes, GraphFakosRequest(screen="context_preview")),
        ),
        _panel(
            "Provider Contribution",
            _key_values(
                {
                    "provider": graph.provider_label,
                    "role": graph.graph_role,
                    "capabilities": ", ".join(graph.capabilities),
                    "warnings": len(graph.warnings),
                }
            ),
        ),
    )


def _provider_details(graph: GraphFakosGraph) -> str:
    if not graph.provider_details:
        return ""
    return _panel_body("Provider Details", _key_values(graph.provider_details))


def _capability_details(graph: GraphFakosGraph) -> str:
    if not graph.capability_details:
        return ""
    items = [
        f"{capability}: {description}"
        for capability, description in graph.capability_details.items()
    ]
    return _panel_body("Capability Notes", _list(items))


def _facet_details(graph: GraphFakosGraph) -> str:
    facets = graph.available_facets or _graph_facets(graph)
    if not facets:
        return ""
    items = [
        f"{name}: {', '.join(values[:5])}"
        for name, values in facets.items()
        if values
    ]
    return _panel_body("Available Facets", _list(items))


def _filter_toolbar(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    action: str,
) -> str:
    filters = request.filters
    layout_options = ("force", "circle", "grouped", "timeline", "focus")
    return (
        "<section class='gf-toolbar' aria-label='Graph filters'>"
        f"<form method='get' action='{escape(action)}'>"
        f"<input name='query' value='{escape(request.query)}' "
        "placeholder='Search or use kind:, tag:, source:, id:, has:'>"
        f"{_select('node_kind', 'Node kind', _facet_values(graph, 'node_kind'), filters.get('node_kind', ''))}"
        f"{_select('edge_kind', 'Edge kind', _facet_values(graph, 'edge_kind'), filters.get('edge_kind', ''))}"
        f"{_select('tag', 'Tag', _facet_values(graph, 'tag'), filters.get('tag', ''))}"
        f"{_select('source', 'Source', _facet_values(graph, 'source'), filters.get('source', ''))}"
        f"<input name='min_score' value='{escape(filters.get('min_score', ''))}' "
        "placeholder='Min score'>"
        f"{_select('layout', 'Layout', layout_options, request.layout)}"
        f"<input name='limit' value='{request.limit}' placeholder='Cards'>"
        f"<input name='render_limit' value='{request.render_limit}' placeholder='Canvas'>"
        f"<input type='hidden' name='focus_node_id' value='{escape(request.focus_node_id or '')}'>"
        f"<input type='hidden' name='selected_edge_id' value='{escape(request.selected_edge_id or '')}'>"
        f"<input type='hidden' name='comparison_graph_id' value='{escape(request.comparison_graph_id or '')}'>"
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
        f"{_select('edge_kind', 'Edge kind', _facet_values(graph, 'edge_kind'), request.filters.get('edge_kind', ''))}"
        f"{_select('layout', 'Layout', ('force', 'circle', 'grouped', 'focus'), request.layout)}"
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
        f"{_select('edge_kind', 'Edge kind', _facet_values(graph, 'edge_kind'), request.filters.get('edge_kind', ''))}"
        f"{_select('layout', 'Layout', ('force', 'circle', 'grouped', 'focus'), request.layout)}"
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
    return tuple(
        node
        for node in graph.nodes
        if _node_matches_query(node, parsed_query)
        and _node_matches_filters(node, filters, min_score)
    )


def _node_matches_query(node: GraphFakosNode, parsed_query: dict[str, tuple[str, ...]]) -> bool:
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
    if parsed_query["terms"] or any(parsed_query[key] for key in parsed_query if key != "terms"):
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
    if min_score is not None and (node.score is None or node.score < min_score):
        return False
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
    for raw_token in query.split():
        if ":" not in raw_token:
            buckets["terms"].append(raw_token.casefold())
            continue
        key, value = raw_token.split(":", 1)
        normalized_key = key.strip().casefold()
        normalized_value = value.strip()
        if not normalized_value:
            continue
        if normalized_key in {"kind", "tag", "source", "id", "label", "summary", "has", "edge"}:
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
        }.items()
    }


def _active_query_terms(request: GraphFakosRequest) -> tuple[str, ...]:
    parsed = _parse_query(request.query)
    chips = [f"layout:{request.layout}"]
    for key, values in parsed.items():
        for value in values:
            chips.append(value if key == "terms" else f"{key}:{value}")
    for key, value in request.filters.items():
        if value:
            chips.append(f"{key}:{value}")
    if request.render_limit:
        chips.append(f"render_limit:{request.render_limit}")
    return tuple(chips)


def _query_summary(items: tuple[str, ...]) -> str:
    if not items:
        return _panel("Active Query", _empty("Using the default graph view."))
    return _panel("Active Query", _badges([(item, "neutral") for item in items]))


def _query_syntax_panel() -> str:
    return _list(
        [f"{item['token']} - {item['meaning']}" for item in query_syntax_reference()]
    )


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


def _graph_canvas(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    selected_id: str | None,
    selected_edge_id: str | None,
) -> str:
    if not graph.nodes:
        return _panel("Graph Canvas", _empty("No graph nodes."))
    width = 920
    height = 460
    positions = _layout_positions(graph, request, width, height, selected_id)
    edge_lines = ""
    for edge in graph.edges:
        if edge.source_id not in positions or edge.target_id not in positions:
            continue
        x1, y1 = positions[edge.source_id]
        x2, y2 = positions[edge.target_id]
        selected = "true" if edge.id == selected_edge_id else "false"
        edge_lines += (
            f"<a href='{_explore_href(request, selected_edge_id=edge.id, focus_node_id=selected_id)}'>"
            f"<line class='gf-edge' data-selected='{selected}' x1='{x1:.1f}' y1='{y1:.1f}' "
            f"x2='{x2:.1f}' y2='{y2:.1f}'><title>{escape(edge.label or edge.kind)}</title></line>"
            "</a>"
        )
    node_marks = ""
    for index, node in enumerate(graph.nodes):
        x, y = positions[node.id]
        selected = "true" if node.id == selected_id else "false"
        node_marks += (
            f"<a href='{_explore_href(request, focus_node_id=node.id)}'>"
            f"<g class='gf-node' data-kind='{escape(node.kind)}' data-selected='{selected}'>"
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{_node_radius(node)}'></circle>"
            f"<text x='{x:.1f}' y='{_node_label_y(index, y):.1f}' text-anchor='middle'>{escape(_node_label(node))}</text>"
            f"<title>{escape(node.summary or node.label)}</title></g></a>"
        )
    return (
        "<section class='gf-panel'><h3>Graph Canvas</h3>"
        f"<p class='gf-note'>Layout {escape(request.layout)}. Rendering {len(graph.nodes)} node(s) and {len(graph.edges)} edge(s).</p>"
        f"<svg class='gf-canvas' viewBox='0 0 {width} {height}' "
        "role='img' aria-label='GraphFakos graph canvas'>"
        f"{edge_lines}{node_marks}</svg></section>"
    )


def _explore_href(
    request: GraphFakosRequest,
    *,
    focus_node_id: str | None = None,
    selected_edge_id: str | None = None,
) -> str:
    return _route_href(
        request.with_screen("explore"),
        overrides={
            "focus_node_id": focus_node_id,
            "selected_edge_id": selected_edge_id,
        },
    )


def _node_radius(node: GraphFakosNode) -> int:
    if node.score is None:
        return 18
    return max(16, min(28, int(16 + node.score * 10)))


def _node_label(node: GraphFakosNode) -> str:
    return node.label[:22] + ("..." if len(node.label) > 22 else "")


def _node_label_y(index: int, y: float) -> float:
    return y - 24 if index % 2 else y + 28


def _selection_summary(
    graph: GraphFakosGraph,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    payload: dict[str, object] = {
        "visible nodes": len(graph.nodes),
        "visible edges": len(graph.edges),
    }
    if focus is not None:
        payload["focus node"] = focus.label
    if selected_edge is not None:
        payload["selected edge"] = selected_edge.label or selected_edge.kind
    if graph.stats.get("hidden_nodes") not in (None, 0):
        payload["hidden nodes"] = graph.stats["hidden_nodes"]
    if graph.stats.get("hidden_edges") not in (None, 0):
        payload["hidden edges"] = graph.stats["hidden_edges"]
    return _panel(
        "Visible Graph",
        _summary_note(
            "Selections made here carry into the shared inspector and graph routes."
        )
        + _key_values(payload),
    )


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
    citations = tuple(
        item for item in graph.citations if item.id in set(node.citation_ids)
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
        "<h3>Citations</h3>"
        f"{''.join(_citation_card(item) for item in citations) or _empty('No node citations.')}"
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
    citations = tuple(
        item for item in graph.citations if item.id in set(edge.citation_ids)
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
        f"{''.join(_citation_card(item) for item in citations)}"
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


def _node_cards(
    nodes: tuple[GraphFakosNode, ...],
    request: GraphFakosRequest | None = None,
) -> str:
    if not nodes:
        return _empty("No nodes match.")
    cards = ""
    link_request = request or GraphFakosRequest()
    for node in nodes:
        cards += (
            "<article class='gf-card'>"
            f"<div>{_badge(node.kind, 'accent')}</div>"
            f"<h4><a href='{_explore_href(link_request, focus_node_id=node.id)}'>{escape(node.label)}</a></h4>"
            f"<p>{escape(node.summary or node.id)}</p>"
            f"{_badges([(tag, 'blue') for tag in node.tags[:3]])}</article>"
        )
    return cards


def _context_cards(
    nodes: tuple[GraphFakosNode, ...],
    request: GraphFakosRequest | None = None,
) -> str:
    if not nodes:
        return _empty("No ranked context nodes are available.")
    cards = ""
    link_request = request or GraphFakosRequest()
    for node in nodes:
        score = node.score if node.score is not None else "n/a"
        cards += (
            "<article class='gf-card'>"
            f"<div>{_badge(node.kind, 'accent')}{_badge(f'score {score}', 'blue')}</div>"
            f"<h4><a href='{_explore_href(link_request, focus_node_id=node.id)}'>{escape(node.label)}</a></h4>"
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


def _path_summary(
    source: GraphFakosNode,
    target: GraphFakosNode,
    path_edges: list[GraphFakosEdge],
) -> str:
    if not path_edges:
        return _empty(
            f"No bounded path connects {source.label} to {target.label} in the current graph view."
        )
    hop_count = len(path_edges)
    return (
        _summary_note(
            f"{hop_count} edge hop(s) connect {source.label} to {target.label}."
        )
        + _list(
            [
                f"{edge.source_id} -> {edge.target_id} ({edge.label or edge.kind})"
                for edge in path_edges
            ]
        )
        + f"<p class='gf-empty'>Route starts at {escape(source.id)} and ends at {escape(target.id)}.</p>"
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


def _citation_card(item: GraphFakosCitation) -> str:
    label = item.label or item.id
    location = ""
    if item.path and item.line is not None:
        location = f"{item.path}:{item.line}"
    elif item.path:
        location = item.path
    elif item.uri:
        location = item.uri
    return (
        "<article class='gf-card'>"
        f"<h4>{escape(label)}</h4>"
        f"<p>{escape(item.excerpt or location or item.id)}</p>"
        f"{_key_values({'path': item.path, 'line': item.line, 'uri': item.uri})}"
        "</article>"
    )


def _adjacency_map(
    graph: GraphFakosGraph,
) -> dict[str, tuple[tuple[GraphFakosEdge, str], ...]]:
    adjacency: dict[str, list[tuple[GraphFakosEdge, str]]] = defaultdict(list)
    for edge in graph.edges:
        adjacency[edge.source_id].append((edge, edge.target_id))
        adjacency[edge.target_id].append((edge, edge.source_id))
    return {key: tuple(value) for key, value in adjacency.items()}


def _render_limited_graph(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    preferred_node_ids: set[str],
    preferred_edge_id: str | None,
) -> GraphFakosGraph:
    if len(graph.nodes) <= request.render_limit:
        return graph
    ranked_nodes = sorted(
        graph.nodes,
        key=lambda node: (
            node.id not in preferred_node_ids,
            -(node.score if node.score is not None else 0),
            node.label.casefold(),
        ),
    )
    visible_nodes = tuple(ranked_nodes[: request.render_limit])
    visible_ids = {node.id for node in visible_nodes}
    visible_edges = tuple(
        edge
        for edge in graph.edges
        if edge.source_id in visible_ids and edge.target_id in visible_ids
    )
    if preferred_edge_id and preferred_edge_id not in {edge.id for edge in visible_edges}:
        extra_edge = graph.edge_map().get(preferred_edge_id)
        if extra_edge is not None and extra_edge.source_id in visible_ids and extra_edge.target_id in visible_ids:
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


def _layout_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if request.layout == "timeline":
        return _timeline_positions(graph, width, height)
    if request.layout == "grouped":
        return _grouped_positions(graph, width, height)
    if request.layout == "focus":
        return _focus_positions(graph, width, height, focus_node_id)
    return _ring_positions(graph, width, height)


def _ring_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    center_x = width / 2
    center_y = height / 2
    radius = min(width, height) * 0.34
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(graph.nodes):
        angle = (2 * pi * index / max(len(graph.nodes), 1)) - (pi / 2)
        x = node.visual.x if node.visual.x is not None else center_x + radius * cos(angle)
        y = node.visual.y if node.visual.y is not None else center_y + radius * sin(angle)
        positions[node.id] = (x, y)
    return positions


def _grouped_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    groups: dict[str, list[GraphFakosNode]] = defaultdict(list)
    for node in graph.nodes:
        groups[node.kind or "node"].append(node)
    positions: dict[str, tuple[float, float]] = {}
    group_names = sorted(groups)
    for group_index, group_name in enumerate(group_names):
        column_x = 120 + group_index * max((width - 220) / max(len(group_names), 1), 1)
        for row_index, node in enumerate(groups[group_name]):
            positions[node.id] = (column_x, 90 + row_index * 70)
    return positions


def _timeline_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    ordered = sorted(
        graph.nodes,
        key=lambda node: min(node.timestamps.values()) if node.timestamps else node.label.casefold(),
    )
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(ordered):
        x = 100 + index * max((width - 180) / max(len(ordered) - 1, 1), 1)
        y = 150 if index % 2 else height - 140
        positions[node.id] = (x, y)
    return positions


def _focus_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    positions = _ring_positions(graph, width, height)
    if not focus_node_id or focus_node_id not in positions:
        return positions
    positions[focus_node_id] = (width / 2, height / 2)
    remaining = [node for node in graph.nodes if node.id != focus_node_id]
    radius = min(width, height) * 0.24
    for index, node in enumerate(remaining):
        angle = 2 * pi * index / max(len(remaining), 1)
        positions[node.id] = (
            width / 2 + radius * cos(angle),
            height / 2 + radius * sin(angle),
        )
    return positions


def _graph_diff(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
) -> dict[str, object]:
    current_node_ids = {node.id for node in graph.nodes}
    comparison_node_ids = {node.id for node in comparison_graph.nodes}
    current_edge_ids = {edge.id for edge in graph.edges}
    comparison_edge_ids = {edge.id for edge in comparison_graph.edges}
    return {
        "summary": {
            "current nodes": len(graph.nodes),
            "comparison nodes": len(comparison_graph.nodes),
            "current edges": len(graph.edges),
            "comparison edges": len(comparison_graph.edges),
            "added node count": len(current_node_ids - comparison_node_ids),
            "removed node count": len(comparison_node_ids - current_node_ids),
            "added edge count": len(current_edge_ids - comparison_edge_ids),
            "removed edge count": len(comparison_edge_ids - current_edge_ids),
        },
        "added_nodes": tuple(sorted(current_node_ids - comparison_node_ids)),
        "removed_nodes": tuple(sorted(comparison_node_ids - current_node_ids)),
        "added_edges": tuple(sorted(current_edge_ids - comparison_edge_ids)),
        "removed_edges": tuple(sorted(comparison_edge_ids - current_edge_ids)),
    }


def _diff_section(title: str, items: tuple[str, ...]) -> str:
    return f"<h4>{escape(title)}</h4>{_list(items)}"


def _overlay_summary(overlay_graphs: tuple[GraphFakosGraph, ...]) -> str:
    if not overlay_graphs:
        return _empty("No overlay provider graphs are available.")
    rows = [
        f"{graph.provider_label}: {len(graph.nodes)} nodes, {len(graph.edges)} edges"
        for graph in overlay_graphs
    ]
    return _list(rows)


def _split(primary: str, secondary: str) -> str:
    return f"<section class='gf-layout'><div>{primary}</div><aside>{secondary}</aside></section>"


def _panel(title: str, body: str) -> str:
    return f"<section class='gf-panel'><h3>{escape(title)}</h3>{body}</section>"


def _panel_body(title: str, body: str) -> str:
    return f"<section class='gf-subpanel'><h4>{escape(title)}</h4>{body}</section>"


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


def _summary_note(text: str) -> str:
    return f"<p class='gf-note'>{escape(text)}</p>"


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
.gf-subpanel {
  border-top: 1px solid var(--gf-line);
  margin-top: 12px;
  padding-top: 12px;
}
.gf-subpanel h4 {
  margin: 0 0 10px;
  font-size: 14px;
}
.gf-note {
  margin: 0 0 12px;
  color: var(--gf-muted);
}
.gf-toolbar { margin-bottom: 16px; }
.gf-toolbar form {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) repeat(6, minmax(110px, .45fr)) auto auto;
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
  paint-order: stroke;
  stroke: #fbfcfa;
  stroke-width: 5px;
  stroke-linejoin: round;
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
    "build_viewer_route",
    "parse_viewer_request",
    "query_syntax_reference",
    "render_graph_fragment",
    "render_graph_viewer",
    "render_provider_path",
    "screen_manifest",
]
