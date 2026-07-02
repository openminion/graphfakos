"""Static graph viewer rendering."""

from __future__ import annotations

from collections import defaultdict, deque
from html import escape
import json
from math import cos, pi, sin, sqrt
import shlex
from urllib.parse import urlencode

from graphfakos.browser import viewer_runtime_script
from graphfakos.models import (
    GraphFakosActionStatus,
    GraphFakosCitation,
    GraphFakosDiagnostics,
    GraphFakosEdge,
    GraphFakosGraphAction,
    GraphFakosSavedQuery,
    GraphFakosSavedView,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvenance,
    GraphFakosRequest,
    GraphFakosScreen,
    GraphFakosViewerState,
)
from graphfakos.provider import (
    GraphFakosProvider,
    analyze_graph,
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

_GRAPH_ACTION_TYPES: tuple[tuple[str, str], ...] = (
    ("draft_node", "Draft node"),
    ("draft_edge", "Draft edge"),
    ("merge_alias", "Merge alias"),
)
_MINIMAP_WIDTH = 180
_MINIMAP_HEIGHT = 90
_MINIMAP_NODE_RADIUS = 4


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
    graph, request, comparison_graph, overlay_graphs = _provider_view_context(
        provider,
        base_request,
        path,
        query,
    )
    return render_graph_viewer(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )


def render_provider_path_fragment(
    provider: GraphFakosProvider,
    base_request: GraphFakosRequest,
    path: str,
    query: dict[str, list[str]],
) -> str:
    graph, request, comparison_graph, overlay_graphs = _provider_view_context(
        provider,
        base_request,
        path,
        query,
    )
    return render_graph_fragment(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )


def _provider_view_context(
    provider: GraphFakosProvider,
    base_request: GraphFakosRequest,
    path: str,
    query: dict[str, list[str]],
) -> tuple[
    GraphFakosGraph,
    GraphFakosRequest,
    GraphFakosGraph | None,
    tuple[GraphFakosGraph, ...],
]:
    screen = _screen_from_path(path) or base_request.screen
    request = _request_from_query(base_request.with_screen(screen), query)
    graph = load_provider_graph(provider, request)
    comparison_graph = load_comparison_graph(provider, request)
    overlay_graphs = load_overlay_graphs(provider, request)
    return graph, request, comparison_graph, overlay_graphs


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
        f"{_STYLE}</head><body class='gf-page' data-theme='{escape(request.theme)}'>"
        "<div class='gf-shell'>"
        f"{_nav(request)}"
        f"{body}</div>{_viewer_script_tag()}</body></html>"
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
        preset_id=(
            _first_query_value(query, "preset")
            or _first_query_value(query, "preset_id")
            or request.preset_id
        ),
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
        render_limit=int(
            _first_query_value(query, "render_limit") or request.render_limit
        ),
        camera_x=_float_query_value(query, "camera_x", request.camera_x),
        camera_y=_float_query_value(query, "camera_y", request.camera_y),
        camera_zoom=_float_query_value(query, "camera_zoom", request.camera_zoom),
        render_engine=_first_query_value(query, "render_engine")
        or request.render_engine,
        theme=_first_query_value(query, "theme") or request.theme,
        saved_view_id=_first_query_value(query, "saved_view_id")
        or request.saved_view_id,
        show_orphans=_bool_query_value(query, "show_orphans", request.show_orphans),
        show_neighbor_links=_bool_query_value(
            query,
            "show_neighbor_links",
            request.show_neighbor_links,
        ),
        edge_clutter=_first_query_value(query, "edge_clutter") or request.edge_clutter,
        analytics_overlay=_first_query_value(query, "analytics_overlay")
        or request.analytics_overlay,
    )


def _first_query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key) or []
    return values[0] if values and values[0] else None


def _float_query_value(
    query: dict[str, list[str]],
    key: str,
    fallback: float | None,
) -> float | None:
    value = _first_query_value(query, key)
    if value is None:
        return fallback
    try:
        return float(value)
    except ValueError:
        return fallback


def _bool_query_value(
    query: dict[str, list[str]],
    key: str,
    fallback: bool,
) -> bool:
    value = _first_query_value(query, key)
    if value is None:
        return fallback
    return value.casefold() not in {"0", "false", "no", "off"}


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
        {
            "token": "kind:<value>",
            "meaning": "Filter nodes by provider-neutral node kind.",
        },
        {"token": "tag:<value>", "meaning": "Filter nodes that include one graph tag."},
        {
            "token": "source:<value>",
            "meaning": "Filter nodes by provider-declared source label.",
        },
        {"token": "id:<value>", "meaning": "Match node ids directly."},
        {"token": "label:<value>", "meaning": "Match node labels directly."},
        {"token": "summary:<value>", "meaning": "Match node summaries directly."},
        {"token": "edge:<value>", "meaning": "Filter visible edges by edge kind."},
        {
            "token": "has:provenance",
            "meaning": "Require provenance references on matched nodes.",
        },
        {
            "token": "has:citation",
            "meaning": "Require citation references on matched nodes.",
        },
        {"token": "has:score", "meaning": "Require scored nodes."},
        {
            "token": '"quoted phrase"',
            "meaning": "Keep whitespace together in one free-text match.",
        },
        {
            "token": "score>=0.8",
            "meaning": "Filter nodes by numeric score comparisons.",
        },
        {
            "token": "time>=2026-06-01",
            "meaning": "Filter nodes by ISO-like timestamp comparisons.",
        },
    )


def review_preset_manifest(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None = None,
) -> tuple[dict[str, str], ...]:
    focus = _preferred_focus_node(graph, request)
    focus_id = focus.id if focus is not None else None
    presets: list[dict[str, str]] = [
        _preset_entry(
            "overview",
            "Overview",
            "Explore the highest-signal graph nodes through the shared force layout.",
            _preset_request(
                request,
                preset_id="overview",
                screen="explore",
                layout="force",
                focus_node_id=focus_id,
            ),
        ),
        _preset_entry(
            "focus",
            "Focus Review",
            "Open a depth-two neighborhood around the current anchor node.",
            _preset_request(
                request,
                preset_id="focus",
                screen="neighborhood",
                layout="focus",
                focus_node_id=focus_id,
                max_depth=2,
            ),
        ),
        _preset_entry(
            "evidence",
            "Evidence",
            "Review provenance and citation coverage before trusting the graph.",
            _preset_request(
                request,
                preset_id="evidence",
                screen="provenance",
                layout="grouped",
            ),
        ),
        _preset_entry(
            "timeline",
            "Timeline",
            "Inspect freshness-oriented timestamps across the current graph snapshot.",
            _preset_request(
                request,
                preset_id="timeline",
                screen="timeline",
                layout="timeline",
            ),
        ),
        _preset_entry(
            "health",
            "Graph Health",
            "Check provider metadata, graph health, and overlay readiness together.",
            _preset_request(
                request,
                preset_id="health",
                screen="provider_status",
            ),
        ),
        _preset_entry(
            "context",
            "Context",
            "Preview the graph items most likely to surface in host context assembly.",
            _preset_request(
                request,
                preset_id="context",
                screen="context_preview",
            ),
        ),
    ]
    if comparison_graph is not None:
        presets.insert(
            4,
            _preset_entry(
                "diff",
                "Diff Review",
                "Compare the current graph against its baseline before export or replay.",
                _preset_request(
                    request,
                    preset_id="diff",
                    screen="diff",
                    comparison_graph_id=(
                        request.comparison_graph_id or comparison_graph.graph_id
                    ),
                ),
            ),
        )
    return tuple(presets)


def render_graph_fragment(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None = None,
    overlay_graphs: tuple[GraphFakosGraph, ...] = (),
) -> str:
    route = _route_href(request)
    body = _render_screen(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )
    state_json = _json_attribute(GraphFakosViewerState.from_request(request).to_dict())
    graph_json = _json_attribute(_filtered_graph(graph, request).to_dict())
    return (
        "<graphfakos-viewer data-graphfakos-component='viewer' "
        f"data-state-json='{state_json}' data-graph-json='{graph_json}' "
        f"render-engine='{escape(request.render_engine)}' theme='{escape(request.theme)}'>"
        "<main class='gf-content gf-embed-root' data-graphfakos-embed='true' "
        f"data-graphfakos-screen='{escape(request.screen)}' "
        f"data-graphfakos-route='{escape(route)}' "
        f"data-graphfakos-preset='{escape(request.preset_id)}'>"
        f"{_header(graph, request, comparison_graph, overlay_graphs)}"
        f"{_integration_panel(graph, request, comparison_graph, overlay_graphs)}"
        f"{_preset_rail(review_preset_manifest(graph, request, comparison_graph=comparison_graph), request.preset_id)}"
        f"{body}</main></graphfakos-viewer>"
    )


def _json_attribute(payload: object) -> str:
    return escape(
        json.dumps(payload, sort_keys=True, separators=(",", ":")), quote=True
    )


def _json_script(data_attribute: str, payload: object) -> str:
    content = (
        json.dumps(payload, sort_keys=True, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    return f"<script type='application/json' {data_attribute}='true'>{content}</script>"


def _viewer_script_tag() -> str:
    return f"<script>\n{viewer_runtime_script()}\n</script>"


def _route_href(
    request: GraphFakosRequest,
    *,
    screen: GraphFakosScreen | None = None,
    overrides: dict[str, object] | None = None,
) -> str:
    route = f"/{screen or request.screen}"
    payload: dict[str, object] = {}
    for key, value in request.to_dict().items():
        if key == "screen":
            continue
        route_key = "preset" if key == "preset_id" else key
        if isinstance(value, dict):
            for filter_key, filter_value in value.items():
                if filter_value not in ("", None):
                    payload[filter_key] = filter_value
            continue
        if isinstance(value, bool):
            payload[route_key] = "true" if value else "false"
            continue
        if value not in ("", None, False):
            payload[route_key] = value
    if overrides:
        for key, value in overrides.items():
            route_key = "preset" if key in {"preset", "preset_id"} else key
            if value in ("", None):
                payload.pop(route_key, None)
                continue
            payload[route_key] = value
    return route + (f"?{urlencode(payload)}" if payload else "")


def _nav(request: GraphFakosRequest) -> str:
    links = ""
    for screen, label in _SCREEN_NAV:
        current = 'aria-current="page"' if request.screen == screen else ""
        links += (
            f"<a href='{_route_href(request, screen=screen, overrides={'preset_id': None})}' "
            f"{current}>{escape(label)}</a>"
        )
    return f"<nav class='gf-nav' aria-label='GraphFakos screens'><h1>GraphFakos</h1>{links}</nav>"


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
        f"{_badge(f'render:{request.render_engine}', 'neutral')}"
        f"{_badge(f'theme:{request.theme}', 'blue')}"
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
        "radial": "Radial layout that rings nodes around the current focus.",
        "hierarchical": "Layered layout for source-to-artifact review paths.",
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
    embed_path = _route_href(
        request, overrides={"render_limit": min(request.render_limit, 60)}
    )
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
        f"{_workspace_controls(graph, request)}"
        f"{_local_graph_controls(graph, request, focus)}"
        f"{_graph_canvas(filtered_graph, request, focus.id if focus else None, selected_edge.id if selected_edge else None)}"
        f"{_selection_summary(filtered_graph, focus, selected_edge)}"
        f"{_query_summary(active_query)}"
        "<section class='gf-panel'><h3>Visible Nodes</h3>"
        f"{_node_cards(filtered_graph.nodes[: request.limit], request)}</section>"
    )
    secondary = (
        _graph_navigator(graph, filtered_graph, request, focus)
        + _command_palette(graph, request)
        + _analytics_panel(graph, request)
        + _export_replay_panel(graph, request)
        + _focus_workflow(graph, request, focus)
        + _knowledge_capture_panel(request, focus)
        + _graph_action_panel(focus)
        + _inspector(graph, focus, selected_edge)
    )
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
        f"{_local_graph_controls(graph, request, focus)}"
        f"{_graph_canvas(neighborhood_graph, request, focus.id, request.selected_edge_id)}"
    )
    primary += _panel(
        f"Around {focus.label}",
        f"<p class='gf-empty'>Depth {max(request.max_depth, 1)} neighborhood.</p>"
        f"{_node_cards(neighbors, request) if neighbors else _empty('No neighboring nodes match this view yet.')}",
    )
    secondary = (
        _graph_navigator(graph, neighborhood_graph, request, focus)
        + _analytics_panel(graph, request)
        + _focus_workflow(graph, request, focus)
        + _knowledge_capture_panel(request, focus)
        + _graph_action_panel(focus)
        + _inspector(graph, focus, _selected_edge(graph, request))
    )
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
            _empty(
                "At least two graph nodes are required before a path can be explored."
            ),
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
    secondary = (
        _graph_navigator(graph, path_graph, request, source)
        + _analytics_panel(graph, request)
        + _focus_workflow(graph, request, source)
        + _knowledge_capture_panel(request, source)
        + _graph_action_panel(source)
        + _inspector(graph, source, _selected_edge(graph, request))
    )
    return _split(primary, secondary)


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
        _panel("Evidence Coverage", _evidence_summary(graph))
        + _panel(
            "Citations",
            _summary_note(
                f"{len(graph.citations)} citation reference(s) are available."
            )
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
    diff = build_graph_diff(graph, comparison_graph)
    body = (
        _summary_note(
            f"Comparing {graph.provider_label} against {comparison_graph.provider_label}."
        )
        + _badges(
            (
                (f"{diff['summary']['added node count']} added nodes", "accent"),
                (f"{diff['summary']['removed node count']} removed nodes", "neutral"),
                (f"{diff['summary']['changed node count']} changed nodes", "blue"),
                (f"{diff['summary']['changed edge count']} changed edges", "blue"),
            )
        )
        + _key_values(diff["summary"])
        + _diff_section("Change Hotspots", diff["change_hotspots"])
        + _diff_section("Added nodes", diff["added_nodes"])
        + _diff_section("Removed nodes", diff["removed_nodes"])
        + _diff_section("Changed nodes", diff["changed_nodes"])
        + _diff_section("Added edges", diff["added_edges"])
        + _diff_section("Removed edges", diff["removed_edges"])
        + _diff_section("Changed edges", diff["changed_edges"])
        + _diff_section("Snapshot changes", diff["snapshot_changes"])
    )
    left = _panel(
        "Snapshot Diff",
        body,
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
        + _analytics_panel(graph, GraphFakosRequest(screen="provider_status"))
        + _panel(
            "Sample Nodes",
            _node_cards(graph.nodes[:5], GraphFakosRequest(screen="provider_status")),
        )
        + _panel("Overlay Providers", _overlay_summary(overlay_graphs))
        + _panel("Query Syntax", _query_syntax_panel())
        + _panel("Warnings", _list(graph.warnings)),
    )


def _graph_health(diagnostics: GraphFakosDiagnostics) -> str:
    tone = "accent" if diagnostics.healthy else "blue"
    summary = _badges(
        (
            ("healthy" if diagnostics.healthy else "needs review", tone),
            (f"{diagnostics.node_count} nodes", "neutral"),
            (f"{diagnostics.edge_count} edges", "neutral"),
        )
    ) + _key_values(
        {
            "provenance": diagnostics.provenance_count,
            "citations": diagnostics.citation_count,
            "orphan nodes": len(diagnostics.orphan_node_ids),
            "duplicate edges": len(diagnostics.duplicate_edge_ids),
            "unknown provenance refs": len(diagnostics.unknown_provenance_ids),
            "unknown citation refs": len(diagnostics.unknown_citation_ids),
            "self-loop edges": len(diagnostics.self_loop_edge_ids),
            "secondary-component nodes": len(diagnostics.disconnected_node_ids),
        }
    )
    details = (
        _diagnostic_list("Orphan nodes", diagnostics.orphan_node_ids)
        + _diagnostic_list("Duplicate edge ids", diagnostics.duplicate_edge_ids)
        + _diagnostic_list("Unknown provenance ids", diagnostics.unknown_provenance_ids)
        + _diagnostic_list("Unknown citation ids", diagnostics.unknown_citation_ids)
        + _diagnostic_list("Self-loop edge ids", diagnostics.self_loop_edge_ids)
        + _diagnostic_list(
            "Secondary-component nodes",
            diagnostics.disconnected_node_ids,
        )
    )
    return summary + (details or _empty("No graph diagnostics."))


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
        f"{name}: {', '.join(values[:5])}" for name, values in facets.items() if values
    ]
    return _panel_body("Available Facets", _list(items))


def _filter_toolbar(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    action: str,
) -> str:
    filters = request.filters
    layout_options = (
        "force",
        "circle",
        "grouped",
        "timeline",
        "focus",
        "radial",
        "hierarchical",
    )
    return (
        "<section class='gf-toolbar' aria-label='Graph filters'>"
        f"<form method='get' action='{escape(action)}'>"
        f"<input name='query' value='{escape(request.query)}' "
        "placeholder='Search or use kind:, tag:, has:, score>=, time>='>"
        f"{_select('node_kind', 'Node kind', _facet_values(graph, 'node_kind'), filters.get('node_kind', ''))}"
        f"{_select('edge_kind', 'Edge kind', _facet_values(graph, 'edge_kind'), filters.get('edge_kind', ''))}"
        f"{_select('tag', 'Tag', _facet_values(graph, 'tag'), filters.get('tag', ''))}"
        f"{_select('source', 'Source', _facet_values(graph, 'source'), filters.get('source', ''))}"
        f"<input name='min_score' value='{escape(filters.get('min_score', ''))}' "
        "placeholder='Min score'>"
        f"{_select('layout', 'Layout', layout_options, request.layout)}"
        f"{_select('render_engine', 'Renderer', ('svg', 'canvas', 'webgl'), request.render_engine)}"
        f"{_select('theme', 'Theme', ('default', 'ink', 'paper'), request.theme)}"
        f"<input name='limit' value='{request.limit}' placeholder='Cards'>"
        f"<input name='render_limit' value='{request.render_limit}' placeholder='Canvas'>"
        f"<input type='hidden' name='saved_view_id' value='{escape(request.saved_view_id)}'>"
        f"<input type='hidden' name='show_orphans' value='{str(request.show_orphans).lower()}'>"
        f"<input type='hidden' name='show_neighbor_links' value='{str(request.show_neighbor_links).lower()}'>"
        f"<input type='hidden' name='edge_clutter' value='{escape(request.edge_clutter)}'>"
        f"<input type='hidden' name='analytics_overlay' value='{escape(request.analytics_overlay)}'>"
        f"<input type='hidden' name='preset' value='{escape(request.preset_id)}'>"
        f"<input type='hidden' name='focus_node_id' value='{escape(request.focus_node_id or '')}'>"
        f"<input type='hidden' name='selected_edge_id' value='{escape(request.selected_edge_id or '')}'>"
        f"<input type='hidden' name='comparison_graph_id' value='{escape(request.comparison_graph_id or '')}'>"
        "<button type='submit'>Filter</button>"
        "</form></section>"
    )


def _workspace_controls(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    saved_view = GraphFakosSavedView.from_request(
        request,
        view_id=request.saved_view_id or "route",
        label="Current route view",
    )
    replay_route = _route_href(
        request,
        overrides={"saved_view_id": saved_view.view_id, "render_engine": "svg"},
    )
    return (
        "<section class='gf-toolbar gf-workspace-controls' aria-label='Saved workspace controls'>"
        "<form method='get' action='/explore'>"
        f"<input name='saved_view_id' value='{escape(saved_view.view_id)}' placeholder='Saved view id'>"
        f"{_select('theme', 'Theme', ('default', 'ink', 'paper'), request.theme)}"
        f"<input type='hidden' name='query' value='{escape(request.query)}'>"
        f"<input type='hidden' name='layout' value='{escape(request.layout)}'>"
        f"<input type='hidden' name='focus_node_id' value='{escape(request.focus_node_id or '')}'>"
        f"<input type='hidden' name='camera_x' value='{request.camera_x if request.camera_x is not None else 0}'>"
        f"<input type='hidden' name='camera_y' value='{request.camera_y if request.camera_y is not None else 0}'>"
        f"<input type='hidden' name='camera_zoom' value='{request.camera_zoom if request.camera_zoom is not None else 1}'>"
        "<button type='submit'>Replay View</button>"
        f"<a class='gf-inline-link' href='{escape(replay_route)}'>Share route</a>"
        "</form>"
        f"{_json_script('data-gf-saved-view', saved_view.to_dict())}"
        f"<p class='gf-note'>Saved view JSON captures camera, filters, selected lens, renderer, theme, and layout for {escape(graph.provider_label)}.</p>"
        "</section>"
    )


def _local_graph_controls(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    focus_id = focus.id if focus is not None else request.focus_node_id or ""
    analytics = analyze_graph(graph)
    return (
        "<section class='gf-toolbar gf-local-controls' aria-label='Local graph controls'>"
        "<form method='get' action='/neighborhood'>"
        f"<input type='hidden' name='focus_node_id' value='{escape(focus_id)}'>"
        f"<input type='hidden' name='layout' value='{escape(request.layout)}'>"
        f"<input type='hidden' name='query' value='{escape(request.query)}'>"
        f"{_select('max_depth', 'Depth', ('1', '2', '3'), str(max(request.max_depth, 1)))}"
        f"{_select('show_neighbor_links', 'Neighbor links', ('true', 'false'), str(request.show_neighbor_links).lower())}"
        f"{_select('show_orphans', 'Orphans', ('true', 'false'), str(request.show_orphans).lower())}"
        f"{_select('edge_clutter', 'Edge clutter', ('normal', 'reduced'), request.edge_clutter)}"
        f"{_select('analytics_overlay', 'Overlay', ('degree', 'components', 'provenance'), request.analytics_overlay)}"
        "<button type='submit'>Apply Local Lens</button>"
        "</form>"
        f"<p class='gf-note'>Local controls: {analytics.component_count} component(s), "
        f"{len(analytics.orphan_node_ids)} orphan node(s), max degree {analytics.max_degree}.</p>"
        "</section>"
    )


def _command_palette(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    saved_queries = (
        GraphFakosSavedQuery("hubs", "Hubs", "has:score", {"min_score": "0.8"}),
        GraphFakosSavedQuery("evidence", "Evidence", "has:provenance"),
        GraphFakosSavedQuery("warnings", "Warnings", "kind:warning"),
    )
    query_errors = _query_errors(request.query)
    rows = []
    for saved_query in saved_queries:
        route = _route_href(
            request.with_screen("explore"),
            overrides={"query": saved_query.query, **saved_query.filters},
        )
        rows.append(
            f"<div class='gf-route-row'><div>{escape(saved_query.label)}"
            f"<span class='gf-inline-note'>{escape(saved_query.query)}</span></div>"
            f"<a class='gf-inline-link' href='{escape(route)}'>Run</a></div>"
        )
    error_html = (
        _panel_body("Query Validation", _list(query_errors))
        if query_errors
        else _summary_note("Query validation passed; current graph state is preserved.")
    )
    return _panel(
        "Command Palette",
        _summary_note(
            "Run saved queries, jump by route, or use keyboard focus on the search field."
        )
        + _html_list(rows)
        + error_html
        + _json_script(
            "data-gf-saved-queries",
            [item.to_dict() for item in saved_queries],
        ),
    )


def _query_errors(query: str) -> tuple[str, ...]:
    try:
        shlex.split(query)
    except ValueError as exc:
        return (f"query parse warning: {exc}",)
    return ()


def _analytics_panel(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    analytics = analyze_graph(graph)
    body = _badges(
        (
            (f"overlay:{request.analytics_overlay}", "blue"),
            (f"{analytics.component_count} component(s)", "neutral"),
            (f"max degree {analytics.max_degree}", "accent"),
        )
    ) + _key_values(
        {
            "average degree": round(analytics.average_degree, 2),
            "density": round(analytics.density, 4),
            "hub nodes": len(analytics.hub_node_ids),
            "orphan nodes": len(analytics.orphan_node_ids),
        }
    )
    if analytics.hub_node_ids:
        body += _panel_body("Hub Nodes", _list(list(analytics.hub_node_ids[:8])))
    if analytics.orphan_node_ids:
        body += _panel_body("Orphans", _list(list(analytics.orphan_node_ids[:8])))
    return _panel("Analytics Overlay", body)


def _export_replay_panel(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    state = GraphFakosSavedView.from_request(
        request,
        view_id=request.saved_view_id or "route",
        label="Current route view",
    )
    bundle_preview = {
        "schema_version": "graphfakos.replay.v1",
        "bundle_id": f"{graph.graph_id}:{request.screen}",
        "viewer_state": state.state.to_dict(),
        "graph_id": graph.graph_id,
    }
    return _panel(
        "Export and Replay",
        _summary_note(
            "Static exports stay view-only; replay bundles carry exact graph state for review."
        )
        + _key_values(
            {
                "share route": _route_href(request),
                "bundle schema": bundle_preview["schema_version"],
                "saved view": state.view_id,
                "nodes": len(graph.nodes),
                "edges": len(graph.edges),
            }
        )
        + _json_script("data-gf-replay-bundle-preview", bundle_preview),
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
        f"<input type='hidden' name='preset' value='{escape(request.preset_id)}'>"
        f"{_select_pairs('focus_node_id', 'Focus node', node_options, focus_id)}"
        f"<input name='max_depth' value='{max(request.max_depth, 1)}' "
        "placeholder='Depth'>"
        f"{_select('edge_kind', 'Edge kind', _facet_values(graph, 'edge_kind'), request.filters.get('edge_kind', ''))}"
        f"{_select('layout', 'Layout', ('force', 'circle', 'grouped', 'focus', 'radial', 'hierarchical'), request.layout)}"
        f"{_select('show_neighbor_links', 'Neighbor links', ('true', 'false'), str(request.show_neighbor_links).lower())}"
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
        f"<input type='hidden' name='preset' value='{escape(request.preset_id)}'>"
        f"{_select_pairs('source_node_id', 'Source node', node_options, source_id)}"
        f"{_select_pairs('target_node_id', 'Target node', node_options, target_id)}"
        f"{_select('edge_kind', 'Edge kind', _facet_values(graph, 'edge_kind'), request.filters.get('edge_kind', ''))}"
        f"{_select('layout', 'Layout', ('force', 'circle', 'grouped', 'focus', 'radial', 'hierarchical'), request.layout)}"
        f"{_select('edge_clutter', 'Edge clutter', ('normal', 'reduced'), request.edge_clutter)}"
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
        html += f"<option value='{escape(value)}'{current}>{escape(text)}</option>"
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
    orphan_node_ids = set(diagnose_graph(graph).orphan_node_ids)
    return tuple(
        node
        for node in graph.nodes
        if _node_matches_query(node, parsed_query)
        and _node_matches_filters(node, filters, min_score)
        and (request.show_orphans or node.id not in orphan_node_ids)
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


def _query_summary(items: tuple[str, ...]) -> str:
    if not items:
        return _panel("Active Query", _empty("Using the default graph view."))
    return _panel("Active Query", _badges([(item, "neutral") for item in items]))


def _query_syntax_panel() -> str:
    return _list(
        [f"{item['token']} - {item['meaning']}" for item in query_syntax_reference()]
    )


def _preset_entry(
    preset_id: str,
    label: str,
    summary: str,
    request: GraphFakosRequest,
) -> dict[str, str]:
    return {
        "id": preset_id,
        "label": label,
        "summary": summary,
        "screen": request.screen,
        "route": _route_href(request),
    }


def _preset_request(
    request: GraphFakosRequest,
    *,
    preset_id: str,
    screen: GraphFakosScreen,
    layout: str | None = None,
    query: str = "",
    focus_node_id: str | None = None,
    source_node_id: str | None = None,
    target_node_id: str | None = None,
    comparison_graph_id: str | None = None,
    max_depth: int | None = None,
    filters: dict[str, str] | None = None,
) -> GraphFakosRequest:
    return GraphFakosRequest(
        screen=screen,
        preset_id=preset_id,
        query=query,
        focus_node_id=focus_node_id,
        selected_edge_id=None,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        comparison_graph_id=comparison_graph_id or request.comparison_graph_id,
        max_depth=max_depth if max_depth is not None else request.max_depth,
        filters=dict(filters or {}),
        layout=layout or request.layout,
        include_provenance=request.include_provenance,
        include_provider_payload=request.include_provider_payload,
        limit=request.limit,
        render_limit=request.render_limit,
        camera_x=request.camera_x,
        camera_y=request.camera_y,
        camera_zoom=request.camera_zoom,
    )


def _preset_rail(
    presets: tuple[dict[str, str], ...],
    active_preset_id: str,
) -> str:
    if not presets:
        return ""
    cards = ""
    for preset in presets:
        active = "true" if preset["id"] == active_preset_id else "false"
        cards += (
            f"<a class='gf-preset-card' data-active='{active}' "
            f"href='{escape(preset['route'])}' aria-label='{escape(preset['label'])} preset'>"
            f"<strong>{escape(preset['label'])}</strong>"
            f"<span>{escape(preset['summary'])}</span></a>"
        )
    return (
        "<section class='gf-panel gf-preset-panel' aria-label='Review presets'>"
        "<div class='gf-panel-heading'><h3>Review Presets</h3>"
        "<p class='gf-note'>Jump into repeatable graph review flows without rebuilding routes by hand.</p>"
        "</div>"
        f"<div class='gf-preset-grid'>{cards}</div></section>"
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


def _selected_node(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    candidates: tuple[GraphFakosNode, ...],
) -> GraphFakosNode | None:
    node_map = graph.node_map()
    if request.focus_node_id and request.focus_node_id in node_map:
        return node_map[request.focus_node_id]
    if candidates:
        ranked_candidate_ids = {node.id for node in candidates}
        ranked = _ranked_nodes(
            graph,
            ranked_candidate_ids,
        )
        for node in ranked:
            if node.id in ranked_candidate_ids:
                return node
    return _preferred_focus_node(graph, request)


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


def _graph_navigator(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    source_graph = visible_graph if visible_graph.nodes else graph
    diagnostics = diagnose_graph(graph)
    summary: dict[str, object] = {
        "total nodes": len(graph.nodes),
        "total edges": len(graph.edges),
        "visible nodes": len(visible_graph.nodes),
        "visible edges": len(visible_graph.edges),
        "components": 1 + len(diagnostics.disconnected_node_ids)
        if diagnostics.disconnected_node_ids
        else 1,
        "render limit": request.render_limit,
    }
    if focus is not None:
        summary["focus node"] = focus.label
    if visible_graph.stats.get("hidden_nodes") not in (None, 0):
        summary["hidden nodes"] = visible_graph.stats["hidden_nodes"]
    if visible_graph.stats.get("hidden_edges") not in (None, 0):
        summary["hidden edges"] = visible_graph.stats["hidden_edges"]
    recommended = _ranked_nodes(
        source_graph,
        {focus.id} if focus is not None else set(),
    )[:4]
    rows = [_navigator_row(node, request, source_graph) for node in recommended]
    body = _summary_note(
        "Switch between global graph, local depth, evidence, and path lenses without leaving the workbench."
    )
    body += _lens_routes(graph, request, focus)
    body += _key_values(summary)
    if rows:
        body += _panel_body("Recommended Focus", _html_list(rows))
    return _panel("Navigator", body)


def _lens_routes(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    anchor = _preferred_focus_node(graph, request)
    focus_id = (
        focus.id if focus is not None else (anchor.id if anchor is not None else "")
    )
    chips = [
        (
            "Global",
            _route_href(
                request.with_screen("explore"), overrides={"focus_node_id": None}
            ),
        ),
        (
            "Evidence",
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "query": "has:provenance",
                    "focus_node_id": focus_id or None,
                },
            ),
        ),
        ("Timeline", _route_href(request.with_screen("timeline"))),
        ("Status", _route_href(request.with_screen("provider_status"))),
        ("Context", _route_href(request.with_screen("context_preview"))),
    ]
    if focus_id:
        chips.insert(
            1,
            (
                "Local d1",
                _route_href(
                    request.with_screen("neighborhood"),
                    overrides={
                        "focus_node_id": focus_id,
                        "max_depth": 1,
                        "layout": "focus",
                    },
                ),
            ),
        )
        chips.insert(
            2,
            (
                "Local d2",
                _route_href(
                    request.with_screen("neighborhood"),
                    overrides={
                        "focus_node_id": focus_id,
                        "max_depth": 2,
                        "layout": "focus",
                    },
                ),
            ),
        )
    if focus_id and anchor is not None and anchor.id != focus_id:
        chips.append(
            (
                "Path",
                _route_href(
                    request.with_screen("path"),
                    overrides={
                        "source_node_id": focus_id,
                        "target_node_id": anchor.id,
                        "layout": "focus",
                    },
                ),
            )
        )
    rows = "".join(
        f"<a class='gf-route-chip' href='{escape(route)}'>{escape(label)}</a>"
        for label, route in chips
    )
    return f"<div class='gf-lens-grid' aria-label='Graph view lenses'>{rows}</div>"


def _navigator_row(
    node: GraphFakosNode,
    request: GraphFakosRequest,
    graph: GraphFakosGraph,
) -> str:
    degree = _node_degree_map(graph).get(node.id, 0)
    explore_route = _route_href(
        request.with_screen("explore"),
        overrides={"focus_node_id": node.id, "selected_edge_id": None},
    )
    neighborhood_route = _route_href(
        request.with_screen("neighborhood"),
        overrides={
            "focus_node_id": node.id,
            "selected_edge_id": None,
            "layout": "focus",
            "max_depth": 2,
        },
    )
    pinned = "Pinned" if node.visual.pinned else "Ranked"
    return (
        f"<div class='gf-route-row'><div><a href='{explore_route}'>{escape(node.label)}</a>"
        f"<span class='gf-inline-note'>{degree} connection(s) · {escape(pinned)}</span></div>"
        f"<a class='gf-inline-link' href='{neighborhood_route}'>Neighborhood</a></div>"
    )


def _knowledge_capture_panel(
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    focus_id = focus.id if focus is not None else ""
    focus_label = focus.label if focus is not None else "the graph"
    kinds = ("note", "memory", "document", "code", "task", "question", "warning")
    options = "".join(
        f"<option value='{escape(kind)}'>{escape(kind.title())}</option>"
        for kind in kinds
    )
    return (
        "<section class='gf-panel gf-capture-panel'>"
        "<div class='gf-panel-heading'><h3>Capture Knowledge</h3>"
        "<span class='gf-mini-label'>Preview server</span></div>"
        + _summary_note(
            "Add a note, code observation, or question for the host provider or worker to persist and rebuild into the graph."
        )
        + "<form class='gf-capture-form' method='post' action='/api/knowledge' "
        "data-gf-knowledge-form='true'>"
        f"<label>Text<textarea name='text' rows='5' required "
        f"placeholder='Write an observation about {escape(focus_label)}'></textarea></label>"
        f"<label>Kind<select name='kind'>{options}</select></label>"
        "<label>Tags<input name='tags' placeholder='ui, graph, code'></label>"
        "<label>Source<input name='source' value='workbench'></label>"
        f"<input type='hidden' name='link_node_id' value='{escape(focus_id)}'>"
        "<input type='hidden' name='link_edge_kind' value='mentions'>"
        f"<input type='hidden' name='screen' value='{escape(request.screen)}'>"
        "<button type='submit'>Add to graph</button>"
        "<p class='gf-capture-status' data-gf-knowledge-status='true'></p>"
        "</form></section>"
    )


def _graph_action_panel(focus: GraphFakosNode | None) -> str:
    target_id = focus.id if focus is not None else ""
    action = _draft_graph_action(target_id)
    status = _draft_action_status(action)
    return (
        "<section class='gf-panel gf-action-panel'>"
        "<div class='gf-panel-heading'><h3>Graph Authoring</h3>"
        "<span class='gf-mini-label'>Provider action</span></div>"
        + _summary_note(
            "Draft node, edge, merge, and alias requests are provider-neutral; the host owns persistence."
        )
        + "<form class='gf-capture-form' method='post' action='/api/action' data-gf-action-form='true'>"
        f"<label>Action<select name='action_type'>{_graph_action_options()}</select></label>"
        f"<label>Target<input name='target_id' value='{escape(target_id)}'></label>"
        "<label>Label<input name='label' placeholder='New node or edge label'></label>"
        "<label>Body<textarea name='body' rows='3' placeholder='Why should the provider apply this?'></textarea></label>"
        "<button type='submit'>Queue action</button>"
        "<p class='gf-capture-status' data-gf-action-status-text='true'></p>"
        "</form>"
        f"{_json_script('data-gf-action-template', action.to_dict())}"
        f"{_json_script('data-gf-action-status', status.to_dict())}"
        "</section>"
    )


def _draft_graph_action(target_id: str) -> GraphFakosGraphAction:
    return GraphFakosGraphAction(
        action_id="draft:route",
        action_type="draft_node",
        label="Draft graph note",
        target_id=target_id,
    )


def _draft_action_status(action: GraphFakosGraphAction) -> GraphFakosActionStatus:
    return GraphFakosActionStatus(
        action_id=action.action_id,
        status="draft",
        message="GraphFakos can submit this provider-neutral action to a host provider.",
    )


def _graph_action_options() -> str:
    return "".join(
        f"<option value='{escape(value)}'>{escape(label)}</option>"
        for value, label in _GRAPH_ACTION_TYPES
    )


def _focus_workflow(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    if focus is None:
        return ""
    anchor = _preferred_focus_node(graph, request)
    routes = [
        (
            "Evidence view",
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "query": "has:provenance",
                    "focus_node_id": focus.id,
                    "selected_edge_id": None,
                    "layout": "focus",
                },
            ),
        ),
        (
            "Neighborhood x2",
            _route_href(
                request.with_screen("neighborhood"),
                overrides={
                    "focus_node_id": focus.id,
                    "selected_edge_id": None,
                    "max_depth": 2,
                    "layout": "focus",
                },
            ),
        ),
    ]
    if anchor is not None and anchor.id != focus.id:
        routes.append(
            (
                "Path to anchor",
                _route_href(
                    request.with_screen("path"),
                    overrides={
                        "source_node_id": focus.id,
                        "target_node_id": anchor.id,
                        "selected_edge_id": None,
                        "layout": "focus",
                    },
                ),
            )
        )
    rows = [
        (
            f"<div class='gf-route-row'><div>{escape(label)}</div>"
            f"<a class='gf-inline-link' href='{route}'>Open</a></div>"
        )
        for label, route in routes
    ]
    return _panel(
        "Workflow",
        _summary_note(
            "Move from one selected node into evidence review, local neighborhood, or path tracing."
        )
        + _html_list(rows),
    )


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
    degree_map = _node_degree_map(graph)
    hidden_nodes = int(graph.stats.get("hidden_nodes", 0) or 0)
    hidden_edges = int(graph.stats.get("hidden_edges", 0) or 0)
    edge_lines = ""
    for edge in graph.edges:
        if edge.source_id not in positions or edge.target_id not in positions:
            continue
        x1, y1 = positions[edge.source_id]
        x2, y2 = positions[edge.target_id]
        selected = "true" if edge.id == selected_edge_id else "false"
        path_edge = "true" if request.screen == "path" else "false"
        edge_lines += (
            f"<a href='{_explore_href(request, selected_edge_id=edge.id, focus_node_id=selected_id)}'>"
            f"<line class='gf-edge' data-edge-id='{escape(edge.id)}' "
            f"data-source-id='{escape(edge.source_id)}' data-target-id='{escape(edge.target_id)}' "
            f"data-kind='{escape(edge.kind)}' data-selected='{selected}' "
            f"data-path='{path_edge}' data-clutter='{escape(request.edge_clutter)}' "
            f"x1='{x1:.1f}' y1='{y1:.1f}' "
            f"x2='{x2:.1f}' y2='{y2:.1f}' marker-end='url(#gf-arrow)'>"
            f"<title>{escape(edge.label or edge.kind)}</title></line>"
            "</a>"
        )
    node_marks = ""
    for index, node in enumerate(graph.nodes):
        x, y = positions[node.id]
        selected = "true" if node.id == selected_id else "false"
        pinned = "true" if node.visual.pinned else "false"
        degree = degree_map.get(node.id, 0)
        node_marks += (
            f"<a href='{_explore_href(request, focus_node_id=node.id)}'>"
            f"<g class='gf-node' data-kind='{escape(node.kind)}' data-selected='{selected}' "
            f"data-node-id='{escape(node.id)}' data-node-ref='{escape(node.id)}' "
            f"data-provenance-ids='{escape(' '.join(node.provenance_ids))}' "
            f"data-citation-ids='{escape(' '.join(node.citation_ids))}' "
            f"data-pinned='{pinned}' data-degree='{degree}' data-x='{x:.1f}' data-y='{y:.1f}' "
            f"transform='translate({x:.1f} {y:.1f})'>"
            f"{_node_shape(node)}"
            f"<text y='{_node_label_y(index):.1f}' text-anchor='middle'>{escape(_node_label(node))}</text>"
            f"<title>{escape(node.summary or node.label)}</title></g></a>"
        )
    camera_x = request.camera_x if request.camera_x is not None else 0
    camera_y = request.camera_y if request.camera_y is not None else 0
    camera_zoom = request.camera_zoom if request.camera_zoom is not None else 1
    return (
        "<section class='gf-panel gf-canvas-panel'><div class='gf-panel-heading'>"
        "<h3>Graph Canvas</h3>"
        f"{_canvas_toolbar(request)}</div>"
        f"{_graph_search_panel(graph, request)}"
        f"<p class='gf-note'>Layout {escape(request.layout)}. Rendering {len(graph.nodes)} node(s) "
        f"and {len(graph.edges)} edge(s).</p>"
        f"{_renderer_notice(request)}"
        f"{_render_budget_panel(request, hidden_nodes, hidden_edges)}"
        f"<div class='gf-canvas-grid'><div class='gf-canvas-shell' tabindex='0' "
        f"data-camera-x='{camera_x:.2f}' data-camera-y='{camera_y:.2f}' "
        f"data-camera-zoom='{camera_zoom:.2f}'>"
        f"<svg class='gf-canvas' viewBox='0 0 {width} {height}' "
        "role='img' aria-label='GraphFakos graph canvas'>"
        "<defs><marker id='gf-arrow' markerWidth='8' markerHeight='8' refX='7' "
        "refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z'></path></marker></defs>"
        f"<g class='gf-viewport' transform='translate({camera_x:.2f} {camera_y:.2f}) scale({camera_zoom:.2f})'>"
        f"{edge_lines}{node_marks}</g></svg></div>"
        f"{_graph_minimap(graph, positions, width, height, selected_id)}</div>"
        f"{_group_controls(graph, request)}"
        f"{_graph_canvas_legend(graph)}</section>"
    )


def _canvas_toolbar(request: GraphFakosRequest) -> str:
    saved_route = _route_href(
        request,
        overrides={
            "camera_x": request.camera_x,
            "camera_y": request.camera_y,
            "camera_zoom": request.camera_zoom,
        },
    )
    return (
        "<div class='gf-canvas-tools' aria-label='Graph camera controls'>"
        "<button type='button' data-gf-camera='zoom-in' title='Zoom in' aria-label='Zoom in'>+</button>"
        "<button type='button' data-gf-camera='zoom-out' title='Zoom out' aria-label='Zoom out'>-</button>"
        "<button type='button' data-gf-camera='fit' title='Fit graph' aria-label='Fit graph'>Fit</button>"
        "<button type='button' data-gf-camera='reset' title='Reset camera' aria-label='Reset camera'>Reset</button>"
        "<button type='button' data-gf-camera='fullscreen' title='Fullscreen' aria-label='Fullscreen'>Full</button>"
        f"<a class='gf-tool-link' data-gf-save-view='true' href='{escape(saved_route)}'>Saved view</a>"
        "</div>"
    )


def _graph_search_panel(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    options = "".join(
        f"<option value='{escape(node.id)}' label='{escape(node.label)}'></option>"
        for node in _ranked_nodes(graph, set())
    )
    return (
        "<form class='gf-command-bar' method='get' action='/explore' aria-label='Graph search palette'>"
        "<input list='gf-node-search-options' name='focus_node_id' class='gf-search-input' "
        "placeholder='Jump to node, edge, or path target'>"
        f"<datalist id='gf-node-search-options'>{options}</datalist>"
        f"<input type='hidden' name='query' value='{escape(request.query)}'>"
        f"<input type='hidden' name='layout' value='{escape(request.layout)}'>"
        f"<input type='hidden' name='render_limit' value='{request.render_limit}'>"
        "<button type='submit'>Jump</button>"
        "</form>"
    )


def _renderer_notice(request: GraphFakosRequest) -> str:
    if request.render_engine == "svg":
        return ""
    return (
        "<p class='gf-note gf-renderer-notice'>"
        f"Requested renderer {escape(request.render_engine)} is recorded for host workbenches; "
        "this portable export degrades to the static SVG renderer."
        "</p>"
    )


def _render_budget_panel(
    request: GraphFakosRequest,
    hidden_nodes: int,
    hidden_edges: int,
) -> str:
    if hidden_nodes <= 0 and hidden_edges <= 0:
        return ""
    larger_limit = request.render_limit + max(25, request.render_limit // 2)
    route = _route_href(request, overrides={"render_limit": larger_limit})
    return _panel_body(
        "Render Budget",
        _summary_note(
            f"{hidden_nodes} node(s) and {hidden_edges} edge(s) are summarized outside the current canvas budget."
        )
        + f"<a class='gf-inline-link' href='{escape(route)}'>Show more</a>",
    )


def _node_shape(node: GraphFakosNode) -> str:
    radius = _node_radius(node)
    shape = (node.visual.shape or "").casefold()
    if shape == "square" or node.kind == "provider":
        size = radius * 1.7
        offset = size / 2
        return (
            f"<rect x='-{offset:.1f}' y='-{offset:.1f}' width='{size:.1f}' "
            f"height='{size:.1f}' rx='7'></rect>"
        )
    if shape == "diamond" or node.kind == "document":
        return f"<polygon points='0,-{radius} {radius},{0} 0,{radius} -{radius},0'></polygon>"
    if shape == "pill" or node.kind == "artifact":
        width = radius * 2.5
        height = radius * 1.45
        return (
            f"<rect x='-{width / 2:.1f}' y='-{height / 2:.1f}' "
            f"width='{width:.1f}' height='{height:.1f}' rx='{height / 2:.1f}'></rect>"
        )
    return f"<circle r='{radius}'></circle>"


def _graph_minimap(
    graph: GraphFakosGraph,
    positions: dict[str, tuple[float, float]],
    width: int,
    height: int,
    selected_id: str | None,
) -> str:
    nodes = "".join(
        _minimap_node(node, positions[node.id], width, height, selected_id)
        for node in graph.nodes
        if node.id in positions
    )
    return (
        "<aside class='gf-minimap' aria-label='Graph minimap'>"
        "<div class='gf-minimap-heading'>Minimap</div>"
        f"<svg viewBox='0 0 {_MINIMAP_WIDTH} {_MINIMAP_HEIGHT}' role='img' "
        "aria-label='Visible graph minimap'>"
        f"{nodes}</svg></aside>"
    )


def _minimap_node(
    node: GraphFakosNode,
    position: tuple[float, float],
    width: int,
    height: int,
    selected_id: str | None,
) -> str:
    x, y = position
    selected = "true" if node.id == selected_id else "false"
    scaled_x = x / width * _MINIMAP_WIDTH
    scaled_y = y / height * _MINIMAP_HEIGHT
    return (
        f"<circle cx='{scaled_x:.1f}' cy='{scaled_y:.1f}' "
        f"r='{_MINIMAP_NODE_RADIUS}' data-selected='{selected}' "
        f"data-node-ref='{escape(node.id)}' data-minimap-node-id='{escape(node.id)}'>"
        f"<title>{escape(node.label)}</title></circle>"
    )


def _group_controls(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    kinds = _facet_values(graph, "node_kind")
    if not kinds:
        return ""
    buttons = "".join(
        f"<button type='button' data-gf-group='{escape(kind)}'>{escape(kind)}</button>"
        for kind in kinds
    )
    links = "".join(
        f"<a href='{_route_href(request, overrides={'node_kind': kind})}'>{escape(kind)}</a>"
        for kind in kinds
    )
    return (
        "<div class='gf-group-controls' aria-label='Node group controls'>"
        f"<div>{buttons}</div><div class='gf-group-fallback'>{links}</div></div>"
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


def _node_label_y(index: int) -> float:
    return -28 if index % 2 else 34


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
    if focus is not None and focus.visual.pinned:
        payload["pinned"] = "yes"
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
        f"{_badges(_node_badges(node, graph))}"
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
    if node.visual.pinned:
        metadata["pinned"] = "yes"
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
            f"<article class='gf-card' data-node-ref='{escape(node.id)}'>"
            f"<div>{_badges(_node_badges(node))}</div>"
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
            f"<article class='gf-card' data-node-ref='{escape(node.id)}'>"
            f"<div>{_badges(_node_badges(node) + [(f'score {score}', 'blue')])}</div>"
            f"<h4><a href='{_explore_href(link_request, focus_node_id=node.id)}'>{escape(node.label)}</a></h4>"
            f"<p>{escape(node.summary or node.id)}</p>"
            f"{_badges([(tag, 'blue') for tag in node.tags[:3]])}</article>"
        )
    return cards


def _node_badges(
    node: GraphFakosNode,
    graph: GraphFakosGraph | None = None,
) -> list[tuple[str, str]]:
    badges = [(node.kind, "accent")]
    if node.visual.pinned:
        badges.append(("pinned", "blue"))
    if graph is not None and _node_degree_map(graph).get(node.id, 0) >= 3:
        badges.append(("hub", "neutral"))
    return badges


def _graph_canvas_legend(graph: GraphFakosGraph) -> str:
    degree_map = _node_degree_map(graph)
    pinned_count = sum(1 for node in graph.nodes if node.visual.pinned)
    hub_count = sum(1 for node in graph.nodes if degree_map.get(node.id, 0) >= 3)
    kind_count = len(_graph_facets(graph).get("node_kind", ()))
    return (
        "<div class='gf-canvas-legend'>"
        f"{_badge(f'{pinned_count} pinned', 'blue')}"
        f"{_badge(f'{hub_count} hubs', 'neutral')}"
        f"{_badge(f'{kind_count} kinds', 'accent')}"
        "</div>"
    )


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


def _evidence_summary(graph: GraphFakosGraph) -> str:
    node_provenance = sum(1 for node in graph.nodes if node.provenance_ids)
    node_citations = sum(1 for node in graph.nodes if node.citation_ids)
    edge_provenance = sum(1 for edge in graph.edges if edge.provenance_ids)
    edge_citations = sum(1 for edge in graph.edges if edge.citation_ids)
    provider_counts = _count_rows(
        item.provider_id or "unknown" for item in graph.provenance
    )
    source_type_counts = _count_rows(
        item.source_type or "unknown" for item in graph.provenance
    )
    citation_counts = _count_rows(
        item.path or item.uri or "inline" for item in graph.citations
    )
    return (
        _key_values(
            {
                "node provenance": f"{node_provenance} / {len(graph.nodes)}",
                "node citations": f"{node_citations} / {len(graph.nodes)}",
                "edge provenance": f"{edge_provenance} / {len(graph.edges)}",
                "edge citations": f"{edge_citations} / {len(graph.edges)}",
                "provenance providers": len(
                    {item.provider_id for item in graph.provenance}
                ),
                "source types": len(
                    {item.source_type for item in graph.provenance if item.source_type}
                ),
            }
        )
        + _panel_body("Provider Coverage", _list(provider_counts))
        + _panel_body("Source Types", _list(source_type_counts))
        + _panel_body("Citation Locations", _list(citation_counts))
    )


def _count_rows(values: object) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        if isinstance(value, str) and value:
            counts[value] += 1
    return [
        f"{label}: {count}"
        for label, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0].casefold()),
        )[:6]
    ]


def _adjacency_map(
    graph: GraphFakosGraph,
) -> dict[str, tuple[tuple[GraphFakosEdge, str], ...]]:
    adjacency: dict[str, list[tuple[GraphFakosEdge, str]]] = defaultdict(list)
    for edge in graph.edges:
        adjacency[edge.source_id].append((edge, edge.target_id))
        adjacency[edge.target_id].append((edge, edge.source_id))
    return {key: tuple(value) for key, value in adjacency.items()}


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


def _layout_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if request.layout == "timeline":
        return _timeline_positions(graph, width, height)
    if request.layout == "circle":
        return _ring_positions(graph, width, height)
    if request.layout == "grouped":
        return _grouped_positions(graph, width, height)
    if request.layout == "focus":
        return _focus_positions(graph, width, height, focus_node_id)
    if request.layout == "radial":
        return _radial_positions(graph, width, height, focus_node_id)
    if request.layout == "hierarchical":
        return _hierarchical_positions(graph, width, height, focus_node_id)
    return _force_positions(graph, width, height, focus_node_id)


def _force_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if not graph.nodes:
        return {}
    anchor = _force_anchor_id(graph, focus_node_id)
    adjacency = _adjacency_map(graph)
    degree_map = _node_degree_map(graph)
    center = (width / 2, height / 2)
    positions = {anchor: center}
    inner_ring = sorted(
        {
            neighbor_id
            for _edge, neighbor_id in adjacency.get(anchor, ())
            if neighbor_id != anchor
        },
        key=lambda node_id: (
            -degree_map.get(node_id, 0),
            graph.node_map()
            .get(node_id, GraphFakosNode(id=node_id, label=node_id, kind="node"))
            .label.casefold(),
        ),
    )
    outer_nodes = [
        node
        for node in _ranked_nodes(graph, {anchor, *inner_ring})
        if node.id not in {anchor, *inner_ring}
    ]
    inner_radius = min(width, height) * 0.2
    outer_radius = min(width, height) * 0.36
    for index, node_id in enumerate(inner_ring):
        angle = (2 * pi * index / max(len(inner_ring), 1)) - (pi / 2)
        positions[node_id] = (
            center[0] + inner_radius * cos(angle),
            center[1] + inner_radius * sin(angle),
        )
    for index, node in enumerate(outer_nodes):
        angle = (2 * pi * index / max(len(outer_nodes), 1)) - (pi / 2)
        positions[node.id] = (
            center[0] + outer_radius * cos(angle),
            center[1] + outer_radius * sin(angle),
        )
    for node in graph.nodes:
        positions.setdefault(node.id, center)
    return _relax_force_positions(graph, positions, anchor, width, height)


def _force_anchor_id(graph: GraphFakosGraph, focus_node_id: str | None) -> str:
    node_ids = {node.id for node in graph.nodes}
    if focus_node_id and focus_node_id in node_ids:
        return focus_node_id
    focus = _preferred_focus_node(graph, GraphFakosRequest())
    return (focus or graph.nodes[0]).id


def _relax_force_positions(
    graph: GraphFakosGraph,
    positions: dict[str, tuple[float, float]],
    anchor: str,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    node_ids = [node.id for node in _ranked_nodes(graph, set())]
    if len(node_ids) <= 2:
        return _bounded_positions(graph, positions, anchor, width, height)
    margin = 46.0
    area = max((width - margin * 2) * (height - margin * 2), 1.0)
    ideal_distance = sqrt(area / len(node_ids)) * 0.82
    fixed_ids = {
        node.id
        for node in graph.nodes
        if node.id == anchor
        or (
            node.visual.pinned
            and node.visual.x is not None
            and node.visual.y is not None
        )
    }
    positions = _bounded_positions(graph, positions, anchor, width, height)
    for step in range(72):
        temperature = max(2.5, ideal_distance * (1 - step / 72) * 0.34)
        shifts = {node_id: [0.0, 0.0] for node_id in node_ids}
        for left_index, left_id in enumerate(node_ids):
            left_x, left_y = positions[left_id]
            for right_id in node_ids[left_index + 1 :]:
                right_x, right_y = positions[right_id]
                dx = left_x - right_x
                dy = left_y - right_y
                distance = sqrt(dx * dx + dy * dy) or 0.01
                force = (ideal_distance * ideal_distance) / distance
                offset_x = dx / distance * force
                offset_y = dy / distance * force
                shifts[left_id][0] += offset_x
                shifts[left_id][1] += offset_y
                shifts[right_id][0] -= offset_x
                shifts[right_id][1] -= offset_y
        for edge in graph.edges:
            if edge.source_id not in positions or edge.target_id not in positions:
                continue
            source_x, source_y = positions[edge.source_id]
            target_x, target_y = positions[edge.target_id]
            dx = source_x - target_x
            dy = source_y - target_y
            distance = sqrt(dx * dx + dy * dy) or 0.01
            force = (distance * distance) / max(ideal_distance, 1.0)
            offset_x = dx / distance * force * 0.62
            offset_y = dy / distance * force * 0.62
            shifts[edge.source_id][0] -= offset_x
            shifts[edge.source_id][1] -= offset_y
            shifts[edge.target_id][0] += offset_x
            shifts[edge.target_id][1] += offset_y
        for node_id in node_ids:
            if node_id in fixed_ids:
                continue
            x, y = positions[node_id]
            shift_x, shift_y = shifts[node_id]
            length = sqrt(shift_x * shift_x + shift_y * shift_y) or 1.0
            move = min(length, temperature)
            next_x = x + shift_x / length * move
            next_y = y + shift_y / length * move
            center_pull = 0.012 if step > 36 else 0.006
            next_x += (width / 2 - next_x) * center_pull
            next_y += (height / 2 - next_y) * center_pull
            positions[node_id] = _bounded_point(next_x, next_y, width, height, margin)
    return _bounded_positions(graph, positions, anchor, width, height)


def _bounded_positions(
    graph: GraphFakosGraph,
    positions: dict[str, tuple[float, float]],
    anchor: str,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    bounded: dict[str, tuple[float, float]] = {}
    margin = 46.0
    for node in graph.nodes:
        if node.id == anchor:
            bounded[node.id] = (width / 2, height / 2)
            continue
        if (
            node.visual.pinned
            and node.visual.x is not None
            and node.visual.y is not None
        ):
            bounded[node.id] = _bounded_point(
                node.visual.x,
                node.visual.y,
                width,
                height,
                margin,
            )
            continue
        x, y = positions.get(node.id, (width / 2, height / 2))
        bounded[node.id] = _bounded_point(x, y, width, height, margin)
    return bounded


def _bounded_point(
    x: float,
    y: float,
    width: int,
    height: int,
    margin: float,
) -> tuple[float, float]:
    return (
        min(max(x, margin), width - margin),
        min(max(y, margin), height - margin),
    )


def _ring_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    center_x = width / 2
    center_y = height / 2
    radius = min(width, height) * 0.34
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(_ranked_nodes(graph, set())):
        angle = (2 * pi * index / max(len(graph.nodes), 1)) - (pi / 2)
        x = (
            node.visual.x
            if node.visual.x is not None
            else center_x + radius * cos(angle)
        )
        y = (
            node.visual.y
            if node.visual.y is not None
            else center_y + radius * sin(angle)
        )
        positions[node.id] = (x, y)
    return positions


def _grouped_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    groups: dict[str, list[GraphFakosNode]] = defaultdict(list)
    for node in _ranked_nodes(graph, set()):
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
        key=lambda node: (
            min(node.timestamps.values()) if node.timestamps else node.label.casefold()
        ),
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
    anchor = focus_node_id
    if not anchor:
        focus = _preferred_focus_node(graph, GraphFakosRequest())
        anchor = focus.id if focus is not None else None
    positions = _ring_positions(graph, width, height)
    if not anchor or anchor not in positions:
        return positions
    positions[anchor] = (width / 2, height / 2)
    remaining = [node for node in _ranked_nodes(graph, {anchor}) if node.id != anchor]
    radius = min(width, height) * 0.24
    for index, node in enumerate(remaining):
        angle = 2 * pi * index / max(len(remaining), 1)
        positions[node.id] = (
            width / 2 + radius * cos(angle),
            height / 2 + radius * sin(angle),
        )
    return positions


def _radial_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if not graph.nodes:
        return {}
    anchor = focus_node_id or graph.nodes[0].id
    adjacency = _adjacency_map(graph)
    center = (width / 2, height / 2)
    positions = {anchor: center}
    rings: dict[int, list[str]] = defaultdict(list)
    frontier: deque[tuple[str, int]] = deque([(anchor, 0)])
    seen = {anchor}
    while frontier:
        node_id, depth = frontier.popleft()
        for _edge, next_id in adjacency.get(node_id, ()):
            if next_id in seen:
                continue
            seen.add(next_id)
            rings[depth + 1].append(next_id)
            frontier.append((next_id, depth + 1))
    unseen = [node.id for node in _ranked_nodes(graph, seen) if node.id not in seen]
    if unseen:
        rings[max(rings.keys(), default=0) + 1].extend(unseen)
    for depth, node_ids in sorted(rings.items()):
        radius = min(width, height) * min(0.16 + depth * 0.11, 0.42)
        for index, node_id in enumerate(node_ids):
            angle = (2 * pi * index / max(len(node_ids), 1)) - (pi / 2)
            positions[node_id] = (
                center[0] + radius * cos(angle),
                center[1] + radius * sin(angle),
            )
    for node in graph.nodes:
        positions.setdefault(node.id, center)
    return positions


def _hierarchical_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if not graph.nodes:
        return {}
    adjacency = _adjacency_map(graph)
    anchor = focus_node_id or _ranked_nodes(graph, set())[0].id
    levels: dict[int, list[str]] = defaultdict(list)
    frontier: deque[tuple[str, int]] = deque([(anchor, 0)])
    seen = {anchor}
    while frontier:
        node_id, depth = frontier.popleft()
        levels[depth].append(node_id)
        for _edge, next_id in adjacency.get(node_id, ()):
            if next_id in seen:
                continue
            seen.add(next_id)
            frontier.append((next_id, depth + 1))
    remaining = [node.id for node in _ranked_nodes(graph, seen) if node.id not in seen]
    if remaining:
        levels[max(levels.keys(), default=0) + 1].extend(remaining)
    positions: dict[str, tuple[float, float]] = {}
    level_count = max(len(levels), 1)
    for level_index, node_ids in sorted(levels.items()):
        y = 80 + level_index * max((height - 160) / max(level_count - 1, 1), 1)
        for index, node_id in enumerate(node_ids):
            x = 90 + index * max((width - 180) / max(len(node_ids) - 1, 1), 1)
            positions[node_id] = (x, y)
    return positions


def build_graph_diff(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
) -> dict[str, object]:
    current_node_map = graph.node_map()
    comparison_node_map = comparison_graph.node_map()
    current_edge_map = graph.edge_map()
    comparison_edge_map = comparison_graph.edge_map()
    current_node_payloads = {
        node_id: node.to_dict() for node_id, node in current_node_map.items()
    }
    comparison_node_payloads = {
        node_id: node.to_dict() for node_id, node in comparison_node_map.items()
    }
    current_edge_payloads = {
        edge_id: edge.to_dict() for edge_id, edge in current_edge_map.items()
    }
    comparison_edge_payloads = {
        edge_id: edge.to_dict() for edge_id, edge in comparison_edge_map.items()
    }
    current_node_ids = {node.id for node in graph.nodes}
    comparison_node_ids = {node.id for node in comparison_graph.nodes}
    current_edge_ids = {edge.id for edge in graph.edges}
    comparison_edge_ids = {edge.id for edge in comparison_graph.edges}
    changed_node_details = _changed_item_details(
        current_node_ids & comparison_node_ids,
        current_node_payloads,
        comparison_node_payloads,
    )
    changed_edge_details = _changed_item_details(
        current_edge_ids & comparison_edge_ids,
        current_edge_payloads,
        comparison_edge_payloads,
    )
    changed_nodes = _changed_item_summaries(changed_node_details)
    changed_edges = _changed_item_summaries(changed_edge_details)
    snapshot_changes, snapshot_fields = _snapshot_changes(graph, comparison_graph)
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
            "changed node count": len(changed_nodes),
            "changed edge count": len(changed_edges),
            "snapshot change count": len(snapshot_changes),
            "change hotspot count": len(
                _change_hotspots(
                    changed_node_details,
                    changed_edge_details,
                    snapshot_fields,
                )
            ),
        },
        "added_nodes": tuple(sorted(current_node_ids - comparison_node_ids)),
        "removed_nodes": tuple(sorted(comparison_node_ids - current_node_ids)),
        "changed_nodes": changed_nodes,
        "changed_node_details": tuple(
            {"id": item_id, "fields": list(fields)}
            for item_id, fields in changed_node_details
        ),
        "added_edges": tuple(sorted(current_edge_ids - comparison_edge_ids)),
        "removed_edges": tuple(sorted(comparison_edge_ids - current_edge_ids)),
        "changed_edges": changed_edges,
        "changed_edge_details": tuple(
            {"id": item_id, "fields": list(fields)}
            for item_id, fields in changed_edge_details
        ),
        "snapshot_changes": snapshot_changes,
        "change_hotspots": _change_hotspots(
            changed_node_details,
            changed_edge_details,
            snapshot_fields,
        ),
    }


def _snapshot_changes(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if graph.snapshot is None and comparison_graph.snapshot is None:
        return (), ()
    current = graph.snapshot.to_dict() if graph.snapshot is not None else {}
    comparison = (
        comparison_graph.snapshot.to_dict()
        if comparison_graph.snapshot is not None
        else {}
    )
    if current == comparison:
        return (), ()
    fields = _changed_fields(current, comparison)
    return (_changed_field_summary("snapshot", fields),), fields


def _changed_item_details(
    item_ids: set[str],
    current_payloads: dict[str, dict[str, object]],
    comparison_payloads: dict[str, dict[str, object]],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        sorted(
            (
                item_id,
                _changed_fields(
                    current_payloads[item_id],
                    comparison_payloads[item_id],
                ),
            )
            for item_id in item_ids
            if current_payloads[item_id] != comparison_payloads[item_id]
        )
    )


def _changed_field_summary(
    item_id: str,
    changed_fields: tuple[str, ...],
) -> str:
    return f"{item_id}: {', '.join(changed_fields)}"


def _changed_fields(
    current: dict[str, object],
    comparison: dict[str, object],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            key
            for key in set(current) | set(comparison)
            if current.get(key) != comparison.get(key)
        )
    )


def _changed_item_summaries(
    details: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[str, ...]:
    return tuple(_changed_field_summary(item_id, fields) for item_id, fields in details)


def _change_hotspots(
    changed_node_details: tuple[tuple[str, tuple[str, ...]], ...],
    changed_edge_details: tuple[tuple[str, tuple[str, ...]], ...],
    snapshot_fields: tuple[str, ...],
) -> tuple[str, ...]:
    counts: dict[str, int] = defaultdict(int)
    for _item_id, fields in (*changed_node_details, *changed_edge_details):
        for field in fields:
            counts[field] += 1
    for field in snapshot_fields:
        counts[f"snapshot.{field}"] += 1
    if not counts:
        return ()
    return tuple(
        f"{field}: {count}"
        for field, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0].casefold()),
        )
    )


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
    return (
        "<ul class='gf-list'>"
        + "".join(f"<li>{escape(item)}</li>" for item in items)
        + "</ul>"
    )


def _html_list(items: list[str] | tuple[str, ...]) -> str:
    if not items:
        return _empty("No items.")
    return (
        "<ul class='gf-list'>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
    )


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
    return (
        "<div class='gf-badges'>"
        + "".join(_badge(text, tone) for text, tone in items if text)
        + "</div>"
    )


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
body.gf-page[data-theme="ink"] {
  --gf-bg: #111612;
  --gf-ink: #eef4ec;
  --gf-muted: #b5c1b7;
  --gf-line: #334039;
  --gf-panel: #171f1a;
  --gf-soft: #202a24;
  --gf-accent: #7ad4ba;
  --gf-accent-soft: #17382f;
  --gf-blue: #9ec4ff;
  --gf-blue-soft: #172b46;
  color-scheme: dark;
}
body.gf-page[data-theme="paper"] {
  --gf-bg: #fbf3df;
  --gf-ink: #30251b;
  --gf-muted: #7d6d5e;
  --gf-line: #eadbc1;
  --gf-panel: #fffaf0;
  --gf-soft: #f5ead3;
  --gf-accent: #9a5f2c;
  --gf-accent-soft: #f1ddbf;
  --gf-blue: #596f95;
  --gf-blue-soft: #dee5f1;
}
.gf-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 224px minmax(0, 1fr);
}
.gf-nav {
  border-right: 1px solid var(--gf-line);
  background: var(--gf-panel);
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
.gf-preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
}
.gf-preset-card {
  display: grid;
  gap: 5px;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 10px;
  background: var(--gf-panel);
  color: var(--gf-ink);
}
.gf-preset-card span {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-preset-card[data-active="true"] {
  border-color: var(--gf-accent);
  background: var(--gf-accent-soft);
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
.gf-mini-label {
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
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
.gf-panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.gf-command-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto;
  gap: 8px;
  margin-bottom: 12px;
}
.gf-command-bar input {
  min-width: 0;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
}
.gf-command-bar button,
.gf-canvas-tools button {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  background: var(--gf-panel);
  color: var(--gf-ink);
  font: inherit;
  font-weight: 700;
  min-height: 34px;
  padding: 6px 10px;
}
.gf-command-bar button {
  border-color: var(--gf-accent);
  background: var(--gf-accent);
  color: #fff;
}
.gf-canvas-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.gf-tool-link,
.gf-inline-link,
.gf-route-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 5px 9px;
  background: var(--gf-panel);
  font-size: 13px;
  font-weight: 700;
}
.gf-lens-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0 0 12px;
}
.gf-route-chip {
  background: var(--gf-soft);
  color: var(--gf-ink);
}
.gf-route-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}
.gf-inline-note {
  color: var(--gf-muted);
  display: block;
  font-size: 12px;
  margin-top: 2px;
}
.gf-capture-panel {
  border-color: #c8d8d0;
}
.gf-action-panel,
.gf-workspace-controls,
.gf-local-controls {
  border-color: color-mix(in srgb, var(--gf-accent) 24%, var(--gf-line));
}
.gf-capture-form {
  display: grid;
  gap: 10px;
}
.gf-capture-form label {
  color: var(--gf-muted);
  display: grid;
  gap: 5px;
  font-size: 13px;
  font-weight: 700;
}
.gf-capture-form input,
.gf-capture-form select,
.gf-capture-form textarea {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  color: var(--gf-ink);
  font: inherit;
  min-width: 0;
  padding: 9px 10px;
}
.gf-capture-form textarea {
  resize: vertical;
}
.gf-capture-form button {
  border: 1px solid var(--gf-accent);
  border-radius: 8px;
  background: var(--gf-accent);
  color: white;
  font: inherit;
  font-weight: 700;
  min-height: 36px;
  padding: 8px 10px;
}
.gf-capture-status {
  color: var(--gf-muted);
  font-size: 13px;
  margin: 0;
  min-height: 18px;
}
.gf-capture-status[data-state="error"] {
  color: #b42318;
}
.gf-capture-status[data-state="saved"] {
  color: var(--gf-accent);
}
.gf-canvas-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 190px;
  gap: 12px;
  align-items: start;
}
.gf-canvas-shell {
  min-width: 0;
  outline: none;
}
.gf-canvas-shell:focus-visible {
  box-shadow: 0 0 0 3px var(--gf-accent-soft);
}
.gf-canvas {
  width: 100%;
  min-height: 360px;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  background:
    radial-gradient(circle at 20px 20px, color-mix(in srgb, var(--gf-line) 34%, transparent) 1px, transparent 1px),
    var(--gf-panel);
  background-size: 28px 28px;
  cursor: grab;
  touch-action: none;
}
.gf-canvas:active { cursor: grabbing; }
.gf-canvas defs path,
.gf-edge {
  fill: #768078;
}
.gf-edge {
  stroke: #9ea9a2;
  stroke-width: 1.5;
  transition: stroke .16s ease, stroke-width .16s ease, opacity .16s ease;
}
.gf-edge[data-selected="true"] {
  stroke: var(--gf-blue);
  stroke-width: 4;
}
.gf-edge[data-path="true"] {
  stroke: var(--gf-accent);
  stroke-width: 3;
}
.gf-edge[data-clutter="reduced"] {
  opacity: .42;
  stroke-width: 1;
}
.gf-edge[data-clutter="hidden"] {
  opacity: .08;
}
.gf-edge:hover {
  stroke: var(--gf-accent);
  stroke-width: 3;
}
.gf-node circle,
.gf-node rect,
.gf-node polygon {
  fill: var(--gf-accent-soft);
  stroke: var(--gf-accent);
  stroke-width: 2;
  transition: fill .16s ease, stroke .16s ease, stroke-width .16s ease, opacity .16s ease;
}
.gf-node[data-kind="artifact"] circle,
.gf-node[data-kind="artifact"] rect,
.gf-node[data-kind="artifact"] polygon {
  fill: #fff3d6;
  stroke: #9b6b17;
}
.gf-node[data-kind="document"] circle,
.gf-node[data-kind="document"] rect,
.gf-node[data-kind="document"] polygon {
  fill: #e8edf7;
  stroke: var(--gf-blue);
}
.gf-node[data-kind="memory"] circle,
.gf-node[data-kind="memory"] rect,
.gf-node[data-kind="memory"] polygon {
  fill: #e8f1dd;
  stroke: #587a2e;
}
.gf-node[data-selected="true"] circle,
.gf-node[data-selected="true"] rect,
.gf-node[data-selected="true"] polygon,
.gf-node:hover circle,
.gf-node:hover rect,
.gf-node:hover polygon,
.gf-node[data-highlight="true"] circle,
.gf-node[data-highlight="true"] rect,
.gf-node[data-highlight="true"] polygon {
  fill: var(--gf-blue-soft);
  stroke: var(--gf-blue);
  stroke-width: 3;
  filter: drop-shadow(0 4px 8px rgb(0 0 0 / 18%));
}
.gf-node[data-hidden="true"],
.gf-edge[data-hidden="true"] {
  opacity: .16;
}
.gf-node text {
  fill: var(--gf-ink);
  font-size: 12px;
  font-weight: 700;
  paint-order: stroke;
  stroke: #fbfcfa;
  stroke-width: 5px;
  stroke-linejoin: round;
  pointer-events: none;
}
.gf-minimap {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  background: var(--gf-panel);
  padding: 10px;
}
.gf-minimap-heading {
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
  text-transform: uppercase;
}
.gf-minimap svg {
  display: block;
  width: 100%;
  border: 1px solid var(--gf-line);
  border-radius: 6px;
  background: var(--gf-panel);
}
.gf-minimap circle {
  fill: var(--gf-accent-soft);
  stroke: var(--gf-accent);
}
.gf-minimap circle[data-selected="true"] {
  fill: var(--gf-blue-soft);
  stroke: var(--gf-blue);
  stroke-width: 2;
}
.gf-group-controls {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}
.gf-group-controls button,
.gf-group-fallback a {
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  background: var(--gf-panel);
  color: var(--gf-muted);
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  margin: 0 4px 4px 0;
  padding: 5px 9px;
}
.gf-group-controls button[data-active="false"] {
  background: var(--gf-soft);
  color: var(--gf-muted);
  text-decoration: line-through;
}
.gf-card[data-highlight="true"],
.gf-list li[data-highlight="true"] {
  border-color: var(--gf-blue);
  box-shadow: 0 0 0 2px var(--gf-blue-soft);
}
.gf-card {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 12px;
  background: var(--gf-panel);
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
  background: var(--gf-panel);
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
  background: var(--gf-soft);
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
  .gf-canvas-grid,
  .gf-integration,
  .gf-header,
  .gf-command-bar,
  .gf-toolbar form { grid-template-columns: 1fr; }
  .gf-summary { justify-content: flex-start; }
}
@media (prefers-reduced-motion: reduce) {
  .gf-edge,
  .gf-node circle,
  .gf-node rect,
  .gf-node polygon {
    transition: none;
  }
}
</style>
"""


_SCRIPT = """
<script>
(() => {
  const number = (value, fallback) => {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  };
  const updateSavedLink = (shell, state) => {
    const link = shell.closest(".gf-canvas-panel")?.querySelector("[data-gf-save-view]");
    if (!link) return;
    const url = new URL(link.getAttribute("href") || window.location.href, window.location.origin);
    url.searchParams.set("camera_x", state.x.toFixed(2));
    url.searchParams.set("camera_y", state.y.toFixed(2));
    url.searchParams.set("camera_zoom", state.zoom.toFixed(2));
    link.setAttribute("href", `${url.pathname}${url.search}`);
  };
  const applyCamera = (shell, viewport, state) => {
    viewport.setAttribute("transform", `translate(${state.x} ${state.y}) scale(${state.zoom})`);
    shell.dataset.cameraX = state.x.toFixed(2);
    shell.dataset.cameraY = state.y.toFixed(2);
    shell.dataset.cameraZoom = state.zoom.toFixed(2);
    updateSavedLink(shell, state);
  };
  const connectedEdges = (shell, nodeId) => [
    ...shell.querySelectorAll(`[data-source-id="${CSS.escape(nodeId)}"], [data-target-id="${CSS.escape(nodeId)}"]`),
  ];
  document.querySelectorAll(".gf-canvas-shell").forEach((shell) => {
    const svg = shell.querySelector(".gf-canvas");
    const viewport = shell.querySelector(".gf-viewport");
    if (!svg || !viewport) return;
    const state = {
      x: number(shell.dataset.cameraX, 0),
      y: number(shell.dataset.cameraY, 0),
      zoom: number(shell.dataset.cameraZoom, 1),
    };
    applyCamera(shell, viewport, state);
    const moveCamera = (next) => {
      state.x = next.x ?? state.x;
      state.y = next.y ?? state.y;
      state.zoom = Math.min(3, Math.max(0.35, next.zoom ?? state.zoom));
      applyCamera(shell, viewport, state);
    };
    shell.closest(".gf-canvas-panel")?.querySelectorAll("[data-gf-camera]").forEach((button) => {
      button.addEventListener("click", () => {
        const action = button.dataset.gfCamera;
        if (action === "zoom-in") moveCamera({ zoom: state.zoom * 1.18 });
        if (action === "zoom-out") moveCamera({ zoom: state.zoom / 1.18 });
        if (action === "fit" || action === "reset") moveCamera({ x: 0, y: 0, zoom: 1 });
        if (action === "fullscreen") shell.requestFullscreen?.();
      });
    });
    shell.addEventListener("keydown", (event) => {
      if (event.key === "+" || event.key === "=") moveCamera({ zoom: state.zoom * 1.18 });
      if (event.key === "-") moveCamera({ zoom: state.zoom / 1.18 });
      if (event.key === "0") moveCamera({ x: 0, y: 0, zoom: 1 });
      if (event.key.toLowerCase() === "f") shell.requestFullscreen?.();
    });
    let drag = null;
    svg.addEventListener("pointerdown", (event) => {
      const node = event.target.closest?.(".gf-node");
      event.preventDefault();
      svg.setPointerCapture(event.pointerId);
      if (node) {
        drag = {
          type: "node",
          node,
          nodeId: node.dataset.nodeId,
          startX: event.clientX,
          startY: event.clientY,
          x: number(node.dataset.x, 0),
          y: number(node.dataset.y, 0),
        };
        return;
      }
      drag = { type: "pan", startX: event.clientX, startY: event.clientY, x: state.x, y: state.y };
    });
    svg.addEventListener("pointermove", (event) => {
      if (!drag) return;
      const dx = event.clientX - drag.startX;
      const dy = event.clientY - drag.startY;
      if (drag.type === "pan") {
        moveCamera({ x: drag.x + dx, y: drag.y + dy });
        return;
      }
      const x = drag.x + dx / state.zoom;
      const y = drag.y + dy / state.zoom;
      drag.node.dataset.x = x.toFixed(1);
      drag.node.dataset.y = y.toFixed(1);
      drag.node.setAttribute("transform", `translate(${x} ${y})`);
      connectedEdges(shell, drag.nodeId).forEach((edge) => {
        if (edge.dataset.sourceId === drag.nodeId) {
          edge.setAttribute("x1", x.toFixed(1));
          edge.setAttribute("y1", y.toFixed(1));
        }
        if (edge.dataset.targetId === drag.nodeId) {
          edge.setAttribute("x2", x.toFixed(1));
          edge.setAttribute("y2", y.toFixed(1));
        }
      });
    });
    svg.addEventListener("pointerup", () => { drag = null; });
    svg.addEventListener("pointercancel", () => { drag = null; });
  });
  document.querySelectorAll("[data-gf-group]").forEach((button) => {
    button.dataset.active = "true";
    button.addEventListener("click", () => {
      const kind = button.dataset.gfGroup;
      const active = button.dataset.active !== "false";
      button.dataset.active = active ? "false" : "true";
      document.querySelectorAll(`.gf-node[data-kind="${CSS.escape(kind)}"]`).forEach((node) => {
        node.dataset.hidden = active ? "true" : "false";
      });
      document.querySelectorAll(".gf-edge").forEach((edge) => {
        const source = document.querySelector(`.gf-node[data-node-id="${CSS.escape(edge.dataset.sourceId)}"]`);
        const target = document.querySelector(`.gf-node[data-node-id="${CSS.escape(edge.dataset.targetId)}"]`);
        edge.dataset.hidden = source?.dataset.hidden === "true" || target?.dataset.hidden === "true" ? "true" : "false";
      });
    });
  });
  document.querySelectorAll("[data-node-ref]").forEach((item) => {
    item.addEventListener("mouseenter", () => {
      document.querySelectorAll(`[data-node-ref="${CSS.escape(item.dataset.nodeRef)}"]`).forEach((match) => {
        match.dataset.highlight = "true";
      });
    });
    item.addEventListener("mouseleave", () => {
      document.querySelectorAll("[data-highlight]").forEach((match) => {
        match.dataset.highlight = "false";
      });
    });
  });
})();
</script>
"""


__all__ = [
    "build_graph_diff",
    "build_viewer_route",
    "parse_viewer_request",
    "query_syntax_reference",
    "render_graph_fragment",
    "render_graph_viewer",
    "render_provider_path",
    "review_preset_manifest",
    "screen_manifest",
]
