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
    GraphFakosExpansionRequest,
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
_CAPTURE_TEMPLATES: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "note",
        "Note",
        "note",
        "ui, graph",
        "Capture a durable observation about the selected graph context.",
    ),
    (
        "question",
        "Question",
        "question",
        "question, follow-up",
        "Ask what should be checked next in this graph context.",
    ),
    (
        "code",
        "Code observation",
        "code",
        "code, graph",
        "Capture a source or code observation tied to this graph context.",
    ),
    (
        "warning",
        "Warning",
        "warning",
        "warning, review",
        "Flag a risk, stale edge, or unexpected graph relationship.",
    ),
)
_MINIMAP_WIDTH = 180
_MINIMAP_HEIGHT = 90
_MINIMAP_NODE_RADIUS = 4
_FILTER_TOOLBAR_STATE_EXCLUDES = (
    "query",
    "layout",
    "render_engine",
    "theme",
    "limit",
    "render_limit",
    "saved_view_id",
    "show_orphans",
    "show_neighbor_links",
    "edge_clutter",
    "analytics_overlay",
    "preset_id",
    "focus_node_id",
    "selected_edge_id",
    "comparison_graph_id",
)
_LOCAL_CONTROL_STATE_EXCLUDES = (
    "focus_node_id",
    "layout",
    "query",
    "max_depth",
    "show_neighbor_links",
    "show_orphans",
    "edge_clutter",
    "analytics_overlay",
)
_PHYSICS_STATE_EXCLUDES = (
    "center_force",
    "repel_force",
    "link_distance",
    "node_scale",
    "edge_scale",
    "edge_opacity",
    "label_density",
)
_STYLE_STATE_EXCLUDES = (
    "style_color_by",
    "style_size_by",
    "style_edge_width_by",
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
        selected_node_ids=_tuple_query_value(
            query, "selected_node_ids", request.selected_node_ids
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
        camera_yaw=_float_query_value(query, "camera_yaw", request.camera_yaw),
        camera_pitch=_float_query_value(query, "camera_pitch", request.camera_pitch),
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
        center_force=_float_query_value(query, "center_force", request.center_force),
        repel_force=_float_query_value(query, "repel_force", request.repel_force),
        link_distance=_float_query_value(query, "link_distance", request.link_distance),
        node_scale=_float_query_value(query, "node_scale", request.node_scale),
        edge_scale=_float_query_value(query, "edge_scale", request.edge_scale),
        edge_opacity=_float_query_value(query, "edge_opacity", request.edge_opacity),
        label_density=_float_query_value(query, "label_density", request.label_density),
        pinned_positions=_positions_query_value(
            query, "pinned_positions", request.pinned_positions
        ),
        style_color_by=_first_query_value(query, "style_color_by")
        or request.style_color_by,
        style_size_by=_first_query_value(query, "style_size_by")
        or request.style_size_by,
        style_edge_width_by=_first_query_value(query, "style_edge_width_by")
        or request.style_edge_width_by,
        min_degree=_int_query_value(query, "min_degree", request.min_degree),
        max_degree=_int_query_value(query, "max_degree", request.max_degree),
        component_id=_first_query_value(query, "component_id") or request.component_id,
        connected_to_node_id=_first_query_value(query, "connected_to_node_id")
        or request.connected_to_node_id,
        evidence_filter=_first_query_value(query, "evidence_filter")
        or request.evidence_filter,
        cluster_id=_first_query_value(query, "cluster_id") or request.cluster_id,
        timeline_frame=_first_query_value(query, "timeline_frame")
        or request.timeline_frame,
        timeline_playback=_first_query_value(query, "timeline_playback")
        or request.timeline_playback,
        pivot_node_id=_first_query_value(query, "pivot_node_id")
        or request.pivot_node_id,
        pivot_mode=_first_query_value(query, "pivot_mode") or request.pivot_mode,
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


def _int_query_value(
    query: dict[str, list[str]],
    key: str,
    fallback: int | None,
) -> int | None:
    value = _first_query_value(query, key)
    if value is None:
        return fallback
    try:
        return int(value)
    except ValueError:
        return fallback


def _tuple_query_value(
    query: dict[str, list[str]],
    key: str,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    value = _first_query_value(query, key)
    if value is None:
        return fallback
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _positions_query_value(
    query: dict[str, list[str]],
    key: str,
    fallback: dict[str, tuple[float, float]],
) -> dict[str, tuple[float, float]]:
    value = _first_query_value(query, key)
    if value is None:
        return dict(fallback)
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return dict(fallback)
    parsed: dict[str, tuple[float, float]] = {}
    if not isinstance(payload, dict):
        return dict(fallback)
    for node_id, position in payload.items():
        if not isinstance(node_id, str):
            continue
        if not isinstance(position, (list, tuple)) or len(position) != 2:
            continue
        try:
            parsed[node_id] = (float(position[0]), float(position[1]))
        except (TypeError, ValueError):
            continue
    return parsed


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
            if route_key == "pinned_positions":
                if value:
                    payload[route_key] = json.dumps(
                        value, sort_keys=True, separators=(",", ":")
                    )
                continue
            for filter_key, filter_value in value.items():
                if filter_value not in ("", None):
                    payload[filter_key] = filter_value
            continue
        if isinstance(value, list | tuple):
            if value:
                payload[route_key] = ",".join(str(item) for item in value)
            continue
        if isinstance(value, bool):
            payload[route_key] = "true" if value else "false"
            continue
        if not _route_value_is_empty(value):
            payload[route_key] = value
    if overrides:
        for key, value in overrides.items():
            route_key = "preset" if key in {"preset", "preset_id"} else key
            if value in ("", None):
                payload.pop(route_key, None)
                continue
            payload[route_key] = value
    return route + (f"?{urlencode(payload)}" if payload else "")


def _route_value_is_empty(value: object) -> bool:
    return value is None or value == "" or (isinstance(value, bool) and not value)


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
        return _render_timeline(graph, request)
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
        f"{_physics_display_controls(request)}"
        f"{_active_lens_bar(graph, filtered_graph, request, focus, selected_edge)}"
        f"{_interaction_guide_panel(graph, filtered_graph, request, focus, selected_edge)}"
        f"{_graph_canvas(filtered_graph, request, focus.id if focus else None, selected_edge.id if selected_edge else None)}"
        f"{_selection_summary(filtered_graph, focus, selected_edge)}"
        f"{_query_summary(active_query)}"
        "<section class='gf-panel'><h3>Visible Nodes</h3>"
        f"{_node_cards(filtered_graph.nodes[: request.limit], request)}</section>"
    )
    secondary = (
        _graph_navigator(graph, filtered_graph, request, focus)
        + _navigation_map_panel(graph, filtered_graph, request, focus, selected_edge)
        + _relationship_trail_panel(filtered_graph, request, focus)
        + _search_results_panel(filtered_graph, request, focus)
        + _graph_data_table_panel(filtered_graph, request)
        + _relationship_data_table_panel(filtered_graph, request)
        + _evidence_coverage_map_panel(filtered_graph, request)
        + _facet_explorer_panel(filtered_graph, request)
        + _expansion_planner_panel(filtered_graph, request, focus)
        + _command_palette(graph, filtered_graph, request, focus, selected_edge)
        + _readability_coach_panel(filtered_graph, request)
        + _display_recipes_panel(filtered_graph, request, focus)
        + _advanced_filter_panel(filtered_graph, request)
        + _component_explorer_panel(graph, request)
        + _selection_workbench_panel(filtered_graph, request)
        + _style_rules_panel(filtered_graph, request)
        + _timeline_animation_panel(graph, request)
        + _investigation_pivot_panel(filtered_graph, request, focus)
        + _context_menu_panel(request, focus, selected_edge)
        + _analytics_panel(graph, request)
        + _export_replay_panel(graph, request)
        + _focus_workflow(graph, request, focus)
        + _knowledge_capture_panel(filtered_graph, request, focus)
        + _graph_action_panel(filtered_graph, request, focus)
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
        + _relationship_trail_panel(neighborhood_graph, request, focus)
        + _analytics_panel(graph, request)
        + _focus_workflow(graph, request, focus)
        + _knowledge_capture_panel(neighborhood_graph, request, focus)
        + _graph_action_panel(neighborhood_graph, request, focus)
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
        + _relationship_trail_panel(path_graph, request, source)
        + _analytics_panel(graph, request)
        + _focus_workflow(graph, request, source)
        + _knowledge_capture_panel(path_graph, request, source)
        + _graph_action_panel(path_graph, request, source)
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


def _render_timeline(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    events = _timeline_event_payloads(graph, request)
    visible_events = [
        event
        for event in events
        if not request.timeline_frame or event["value"] == request.timeline_frame
    ]
    return _panel(
        "Timeline and Freshness",
        _summary_note(
            f"{len(visible_events)} of {len(events)} timestamp event(s) are visible across {len(graph.nodes)} node(s)."
        )
        + _timeline_frame_rail(graph, request)
        + _timeline_event_cards(visible_events)
        + _json_script(
            "data-gf-timeline-events",
            {
                "events": visible_events,
                "selected_frame": request.timeline_frame,
                "playback": request.timeline_playback,
            },
        ),
    )


def _timeline_event_payloads(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for node in graph.nodes:
        for field, value in sorted(node.timestamps.items()):
            events.append(
                {
                    "node_id": node.id,
                    "label": node.label,
                    "kind": node.kind,
                    "field": field,
                    "value": value,
                    "route": _route_href(
                        request.with_screen("timeline"),
                        overrides={
                            "timeline_frame": value,
                            "timeline_playback": "step",
                            "focus_node_id": node.id,
                        },
                    ),
                    "focus_route": _explore_href(request, focus_node_id=node.id),
                    "case_packet_route": _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "pivot_node_id": node.id,
                            "pivot_mode": "timeline",
                        },
                    ),
                }
            )
    return sorted(
        events,
        key=lambda event: (
            event["value"],
            event["label"].casefold(),
            event["field"],
        ),
    )


def _timeline_frame_rail(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    frames = _timeline_frames(graph)
    if not frames:
        return _empty("No timeline frames are available.")
    links = [
        (
            "<a class='gf-route-chip' "
            f"data-active='{str(frame == request.timeline_frame).lower()}' "
            f"href='{escape(_route_href(request.with_screen('timeline'), overrides={'timeline_frame': frame, 'timeline_playback': 'step'}))}'>"
            f"{escape(frame)}</a>"
        )
        for frame in frames
    ]
    return (
        "<div class='gf-timeline-rail' data-gf-timeline-rail='true'>"
        + "".join(links)
        + "</div>"
    )


def _timeline_event_cards(events: list[dict[str, str]]) -> str:
    if not events:
        return _empty("No events match the selected timeline frame.")
    html = "<div class='gf-timeline-grid' data-gf-timeline-cards='true'>"
    for event in events:
        html += (
            "<article class='gf-card gf-timeline-card'>"
            f"<h4>{escape(event['label'])}</h4>"
            + _badges(
                [
                    (event["kind"], "accent"),
                    (event["field"], "blue"),
                    (event["value"], "neutral"),
                ]
            )
            + "<div class='gf-route-row'>"
            + f"<div>Open frame</div><a class='gf-inline-link' href='{escape(event['route'])}'>Open</a></div>"
            + "<div class='gf-route-row'>"
            + f"<div>Focus node</div><a class='gf-inline-link' href='{escape(event['focus_route'])}'>Open</a></div>"
            + "<div class='gf-route-row'>"
            + f"<div>Timeline case packet</div><a class='gf-inline-link' href='{escape(event['case_packet_route'])}'>Open</a></div>"
            + "</article>"
        )
    return f"{html}</div>"


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
        + _diff_change_workbench(graph, comparison_graph, request, diff)
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


def _diff_change_workbench(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    diff: dict[str, object],
) -> str:
    changes = _diff_change_payloads(graph, comparison_graph, request, diff)
    if not changes:
        return _empty("No route-backed diff changes are available.")
    return (
        "<section class='gf-diff-workbench' data-gf-diff-workbench='true'>"
        "<h4>Diff Review Workbench</h4>"
        + _diff_change_cards(changes)
        + _json_script(
            "data-gf-diff-workbench",
            {
                "changes": changes,
                "current_graph_id": graph.graph_id,
                "comparison_graph_id": comparison_graph.graph_id,
            },
        )
        + "</section>"
    )


def _diff_change_payloads(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    diff: dict[str, object],
) -> list[dict[str, object]]:
    node_map = graph.node_map()
    comparison_node_map = comparison_graph.node_map()
    edge_map = graph.edge_map()
    comparison_edge_map = comparison_graph.edge_map()
    changes: list[dict[str, object]] = []

    for node_id in _string_items(diff.get("added_nodes")):
        node = node_map.get(node_id)
        if node is not None:
            changes.append(_diff_node_change("added_node", node, request))
    for node_id in _string_items(diff.get("removed_nodes")):
        node = comparison_node_map.get(node_id)
        if node is not None:
            changes.append(_diff_node_change("removed_node", node, request))
    for detail in _dict_items(diff.get("changed_node_details")):
        node_id = str(detail.get("id", ""))
        node = node_map.get(node_id) or comparison_node_map.get(node_id)
        if node is not None:
            changes.append(
                _diff_node_change(
                    "changed_node",
                    node,
                    request,
                    fields=_string_items(detail.get("fields")),
                )
            )

    for edge_id in _string_items(diff.get("added_edges")):
        edge = edge_map.get(edge_id)
        if edge is not None:
            changes.append(_diff_edge_change("added_edge", edge, graph, request))
    for edge_id in _string_items(diff.get("removed_edges")):
        edge = comparison_edge_map.get(edge_id)
        if edge is not None:
            changes.append(
                _diff_edge_change("removed_edge", edge, comparison_graph, request)
            )
    for detail in _dict_items(diff.get("changed_edge_details")):
        edge_id = str(detail.get("id", ""))
        edge = edge_map.get(edge_id) or comparison_edge_map.get(edge_id)
        owner_graph = graph if edge_id in edge_map else comparison_graph
        if edge is not None:
            changes.append(
                _diff_edge_change(
                    "changed_edge",
                    edge,
                    owner_graph,
                    request,
                    fields=_string_items(detail.get("fields")),
                )
            )

    for item in _string_items(diff.get("snapshot_changes")):
        changes.append(
            {
                "change_type": "snapshot",
                "item_type": "snapshot",
                "id": "snapshot",
                "label": item,
                "fields": [],
                "route": _route_href(request.with_screen("diff")),
            }
        )
    return changes[:12]


def _diff_node_change(
    change_type: str,
    node: GraphFakosNode,
    request: GraphFakosRequest,
    *,
    fields: list[str] | None = None,
) -> dict[str, object]:
    return {
        "change_type": change_type,
        "item_type": "node",
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "fields": fields or [],
        "route": _explore_href(request, focus_node_id=node.id),
        "case_packet_route": _route_href(
            request.with_screen("explore"),
            overrides={"pivot_node_id": node.id, "pivot_mode": "evidence_bundle"},
        ),
    }


def _diff_edge_change(
    change_type: str,
    edge: GraphFakosEdge,
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    fields: list[str] | None = None,
) -> dict[str, object]:
    node_map = graph.node_map()
    source = node_map.get(edge.source_id)
    target = node_map.get(edge.target_id)
    label = (
        f"{source.label if source else edge.source_id} -> "
        f"{target.label if target else edge.target_id}"
    )
    return {
        "change_type": change_type,
        "item_type": "edge",
        "id": edge.id,
        "label": label,
        "kind": edge.kind,
        "fields": fields or [],
        "route": _route_href(
            request.with_screen("path"),
            overrides={
                "source_node_id": edge.source_id,
                "target_node_id": edge.target_id,
                "selected_edge_id": edge.id,
                "layout": "focus",
            },
        ),
        "source_route": _explore_href(request, focus_node_id=edge.source_id),
        "target_route": _explore_href(request, focus_node_id=edge.target_id),
    }


def _diff_change_cards(changes: list[dict[str, object]]) -> str:
    html = "<div class='gf-diff-grid' data-gf-diff-cards='true'>"
    for change in changes:
        fields = change.get("fields")
        field_text = ", ".join(fields) if isinstance(fields, list) else ""
        case_packet_route = change.get("case_packet_route")
        source_route = change.get("source_route")
        target_route = change.get("target_route")
        extra_routes = ""
        if isinstance(case_packet_route, str):
            extra_routes += (
                "<div class='gf-route-row'>"
                f"<div>Case packet</div><a class='gf-inline-link' href='{escape(case_packet_route)}'>Open</a></div>"
            )
        if isinstance(source_route, str):
            extra_routes += (
                "<div class='gf-route-row'>"
                f"<div>Source node</div><a class='gf-inline-link' href='{escape(source_route)}'>Open</a></div>"
            )
        if isinstance(target_route, str):
            extra_routes += (
                "<div class='gf-route-row'>"
                f"<div>Target node</div><a class='gf-inline-link' href='{escape(target_route)}'>Open</a></div>"
            )
        html += (
            "<article class='gf-card gf-diff-card'>"
            f"<h4>{escape(str(change.get('label', change.get('id', 'change'))))}</h4>"
            + _badges(
                [
                    (str(change.get("change_type", "change")), "accent"),
                    (str(change.get("item_type", "item")), "blue"),
                    (str(change.get("kind", "")), "neutral"),
                ]
            )
            + (f"<p>Fields: {escape(field_text)}</p>" if field_text else "")
            + "<div class='gf-route-row'>"
            + f"<div>Review change</div><a class='gf-inline-link' href='{escape(str(change.get('route', '#')))}'>Open</a></div>"
            + extra_routes
            + "</article>"
        )
    return f"{html}</div>"


def _string_items(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, str)]


def _dict_items(value: object) -> list[dict[str, object]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, dict)]


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
        f"{_select('render_engine', 'Renderer', ('svg', 'canvas', '3d'), request.render_engine)}"
        f"{_select('theme', 'Theme', ('default', 'ink', 'paper', 'space'), request.theme)}"
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
        f"{_state_hidden_inputs(request, exclude=_FILTER_TOOLBAR_STATE_EXCLUDES)}"
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
        f"{_select('theme', 'Theme', ('default', 'ink', 'paper', 'space'), request.theme)}"
        f"<input type='hidden' name='query' value='{escape(request.query)}'>"
        f"<input type='hidden' name='layout' value='{escape(request.layout)}'>"
        f"<input type='hidden' name='focus_node_id' value='{escape(request.focus_node_id or '')}'>"
        f"<input type='hidden' name='camera_x' value='{request.camera_x if request.camera_x is not None else 0}'>"
        f"<input type='hidden' name='camera_y' value='{request.camera_y if request.camera_y is not None else 0}'>"
        f"<input type='hidden' name='camera_zoom' value='{request.camera_zoom if request.camera_zoom is not None else 1}'>"
        "<button type='submit'>Replay View</button>"
        f"<a class='gf-inline-link' href='{escape(replay_route)}'>Share route</a>"
        "</form>"
        "<div class='gf-workbook' data-gf-workbook='true' aria-label='Local saved view slots'>"
        "<div class='gf-workbook-row'>"
        "<input data-gf-workbook-name='true' value='' placeholder='Local slot label'>"
        "<button type='button' data-gf-workbook-action='save'>Save slot</button>"
        "<button type='button' data-gf-workbook-action='clear'>Clear slots</button>"
        "</div>"
        "<div class='gf-workbook-list' data-gf-workbook-list='true'>"
        "<p class='gf-note'>JavaScript can save local browser-only slots here; static export keeps the share route above.</p>"
        "</div>"
        "<p class='gf-capture-status' data-gf-workbook-status='true'></p>"
        "</div>"
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
        f"{_state_hidden_inputs(request, exclude=_LOCAL_CONTROL_STATE_EXCLUDES)}"
        "<button type='submit'>Apply Local Lens</button>"
        "</form>"
        f"<p class='gf-note'>Local controls: {analytics.component_count} component(s), "
        f"{len(analytics.orphan_node_ids)} orphan node(s), max degree {analytics.max_degree}.</p>"
        "</section>"
    )


def _physics_display_controls(request: GraphFakosRequest) -> str:
    return (
        "<section class='gf-toolbar gf-physics-controls' aria-label='Physics and display controls'>"
        "<form method='get' action='/explore'>"
        f"<input name='center_force' value='{request.center_force:g}' placeholder='Center force'>"
        f"<input name='repel_force' value='{request.repel_force:g}' placeholder='Repel force'>"
        f"<input name='link_distance' value='{request.link_distance:g}' placeholder='Link distance'>"
        f"<input name='node_scale' value='{request.node_scale:g}' placeholder='Node scale'>"
        f"<input name='edge_scale' value='{request.edge_scale:g}' placeholder='Edge scale'>"
        f"<input name='edge_opacity' value='{request.edge_opacity:g}' placeholder='Edge opacity'>"
        f"<input name='label_density' value='{request.label_density:g}' placeholder='Label density'>"
        f"{_state_hidden_inputs(request, exclude=_PHYSICS_STATE_EXCLUDES)}"
        "<button type='submit'>Tune View</button>"
        "</form>"
        "<p class='gf-note'>Physics and display controls are route-backed so SVG export, local server, and embeds share the same view model.</p>"
        "</section>"
    )


def _active_lens_bar(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    payload = _active_lens_payload(graph, visible_graph, request, focus, selected_edge)
    routes = payload["routes"]
    route_links = ""
    if isinstance(routes, dict):
        route_links = "".join(
            f"<a class='gf-route-chip' href='{escape(str(route))}'>{escape(label)}</a>"
            for label, route in routes.items()
        )
    return (
        "<section class='gf-active-lens' aria-label='Active graph lens' "
        "data-gf-active-lens-panel='true'>"
        "<div>"
        "<p class='gf-eyebrow'>Active lens</p>"
        f"{_badges(_active_lens_badges(payload))}"
        "</div>"
        f"<nav class='gf-active-lens-actions' aria-label='Active lens reset routes'>{route_links}</nav>"
        f"{_json_script('data-gf-active-lens', payload)}"
        "</section>"
    )


def _active_lens_payload(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> dict[str, object]:
    return {
        "screen": request.screen,
        "provider_id": graph.provider_id,
        "query": request.query,
        "filters": dict(request.filters),
        "focus_node_id": focus.id if focus is not None else request.focus_node_id,
        "focus_label": focus.label if focus is not None else "",
        "selected_node_ids": list(request.selected_node_ids),
        "selected_edge_id": selected_edge.id
        if selected_edge is not None
        else request.selected_edge_id,
        "layout": request.layout,
        "render_engine": request.render_engine,
        "theme": request.theme,
        "visible_node_count": len(visible_graph.nodes),
        "visible_edge_count": len(visible_graph.edges),
        "hidden_node_count": visible_graph.stats.get("hidden_nodes", 0),
        "hidden_edge_count": visible_graph.stats.get("hidden_edges", 0),
        "pinned_count": len(request.pinned_positions),
        "advanced_filters": _active_advanced_filter_payload(request),
        "routes": _active_lens_routes(request),
    }


def _active_lens_badges(payload: dict[str, object]) -> tuple[tuple[str, str], ...]:
    badges: list[tuple[str, str]] = [
        (f"screen:{payload['screen']}", "accent"),
        (f"layout:{payload['layout']}", "neutral"),
        (f"renderer:{payload['render_engine']}", "blue"),
        (f"theme:{payload['theme']}", "neutral"),
        (f"{payload['visible_node_count']} visible node(s)", "accent"),
    ]
    focus_label = str(payload.get("focus_label") or payload.get("focus_node_id") or "")
    if focus_label:
        badges.append((f"focus:{focus_label}", "blue"))
    query = str(payload.get("query") or "")
    if query:
        badges.append((f"query:{query}", "neutral"))
    filters = payload.get("filters")
    if isinstance(filters, dict) and filters:
        badges.append((f"{len(filters)} filter(s)", "neutral"))
    selected_node_ids = payload.get("selected_node_ids")
    if isinstance(selected_node_ids, list) and selected_node_ids:
        badges.append((f"{len(selected_node_ids)} selected", "blue"))
    selected_edge_id = str(payload.get("selected_edge_id") or "")
    if selected_edge_id:
        badges.append(("edge selected", "blue"))
    pinned_count = int(payload.get("pinned_count") or 0)
    if pinned_count:
        badges.append((f"{pinned_count} pinned", "neutral"))
    return tuple(badges)


def _active_advanced_filter_payload(request: GraphFakosRequest) -> dict[str, object]:
    return {
        key: value
        for key, value in {
            "min_degree": request.min_degree,
            "max_degree": request.max_degree,
            "component_id": request.component_id,
            "connected_to_node_id": request.connected_to_node_id,
            "evidence_filter": request.evidence_filter,
            "cluster_id": request.cluster_id,
        }.items()
        if value not in ("", None)
    }


def _active_lens_routes(request: GraphFakosRequest) -> dict[str, str]:
    return {
        "Overview": _route_href(
            request.with_screen("explore"),
            overrides={
                **_clear_filter_overrides(request),
                **_clear_advanced_filter_overrides(),
                "query": None,
                "focus_node_id": None,
                "selected_node_ids": None,
                "selected_edge_id": None,
                "source_node_id": None,
                "target_node_id": None,
                "pivot_node_id": None,
                "pivot_mode": None,
            },
        ),
        "Clear query": _route_href(request, overrides={"query": None}),
        "Clear filters": _route_href(
            request,
            overrides={
                **_clear_filter_overrides(request),
                **_clear_advanced_filter_overrides(),
            },
        ),
        "Clear focus": _route_href(
            request,
            overrides={"focus_node_id": None, "pivot_node_id": None},
        ),
        "Clear selection": _route_href(
            request,
            overrides={"selected_node_ids": None, "selected_edge_id": None},
        ),
        "Reset camera": _route_href(
            request,
            overrides={"camera_x": None, "camera_y": None, "camera_zoom": None},
        ),
        "SVG fallback": _route_href(request, overrides={"render_engine": "svg"}),
    }


def _interaction_guide_panel(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    payload = _interaction_guide_payload(
        graph,
        visible_graph,
        request,
        focus,
        selected_edge,
    )
    return (
        "<section class='gf-interaction-guide' "
        "aria-label='Graph interaction guide' data-gf-interaction-guide-panel='true'>"
        "<div class='gf-guide-copy'>"
        "<p class='gf-eyebrow'>Interaction guide</p>"
        "<h3>Explore, select, and edit without losing the static fallback.</h3>"
        "<p>Use these routes and shortcuts to move through the graph workbench. "
        "Pointer and keyboard enhancements improve local preview, while links and forms keep exports usable.</p>"
        "</div>"
        + _interaction_guide_cards(payload["steps"])
        + _json_script("data-gf-interaction-guide", payload)
        + "</section>"
    )


def _interaction_guide_payload(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> dict[str, object]:
    focus_id = focus.id if focus is not None else request.focus_node_id
    selected_edge_id = (
        selected_edge.id if selected_edge is not None else request.selected_edge_id
    )
    steps = [
        _interaction_step(
            "search",
            "Search or jump",
            "/ or Ctrl+K",
            "Focus the command search, then jump to a node or preserve the route as a shareable link.",
            _route_href(request.with_screen("explore"), overrides={"query": None}),
        ),
        _interaction_step(
            "camera",
            "Move the graph",
            "+ / - / fit",
            "Pan, zoom, fit selected items, reset the camera, or use the static SVG route when JavaScript is off.",
            _route_href(
                request.with_screen("explore"),
                overrides={"camera_x": None, "camera_y": None, "camera_zoom": None},
            ),
        ),
        _interaction_step(
            "select",
            "Select graph items",
            "Shift-click / box",
            "Select nodes or edges for side-panel inspection, bulk routes, and case-packet pivots.",
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "selected_node_ids": ",".join(request.selected_node_ids)
                    if request.selected_node_ids
                    else None,
                    "selected_edge_id": selected_edge_id or None,
                },
            ),
        ),
        _interaction_step(
            "local",
            "Open local context",
            "L",
            "Switch from global view into a focused neighborhood while preserving filters and display controls.",
            _route_href(
                request.with_screen("neighborhood"),
                overrides={
                    "focus_node_id": focus_id or None,
                    "max_depth": 1,
                    "layout": "focus",
                },
            ),
            disabled=not focus_id,
        ),
        _interaction_step(
            "evidence",
            "Review evidence",
            "E",
            "Filter to provenance-bearing graph items and inspect citations without changing provider data.",
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "query": "has:provenance",
                    "analytics_overlay": "provenance",
                    "focus_node_id": focus_id or None,
                },
            ),
        ),
        _interaction_step(
            "author",
            "Capture or author",
            "Forms",
            "Use local preview forms to submit provider-neutral notes or graph actions; providers decide persistence.",
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "focus_node_id": focus_id or None,
                    "selected_edge_id": selected_edge_id or None,
                },
            ),
        ),
    ]
    visible_steps = [step for step in steps if not step["disabled"]]
    return {
        "provider_id": graph.provider_id,
        "screen": request.screen,
        "focus_node_id": focus_id or "",
        "selected_edge_id": selected_edge_id or "",
        "visible_node_count": len(visible_graph.nodes),
        "visible_edge_count": len(visible_graph.edges),
        "step_count": len(visible_steps),
        "steps": visible_steps,
        "fallback": {
            "static_svg": "Route links and GET forms remain usable without JavaScript.",
            "local_preview": "JavaScript enhances pan, zoom, selection, pins, and in-place fragment refresh.",
        },
        "provider_boundary": (
            "GraphFakos teaches viewer interactions and shapes local action payloads; "
            "providers own persistence, graph rebuilds, and semantic truth."
        ),
    }


def _interaction_step(
    step_id: str,
    label: str,
    shortcut: str,
    summary: str,
    route: str,
    *,
    disabled: bool = False,
) -> dict[str, object]:
    return {
        "id": step_id,
        "label": label,
        "shortcut": shortcut,
        "summary": summary,
        "route": route,
        "disabled": disabled,
    }


def _interaction_guide_cards(steps: object) -> str:
    if not isinstance(steps, list) or not steps:
        return _empty("No interaction guide steps are available.")
    html = "<div class='gf-guide-grid'>"
    for step in steps:
        if not isinstance(step, dict):
            continue
        label = str(step.get("label") or step.get("id") or "Step")
        shortcut = str(step.get("shortcut") or "")
        summary = str(step.get("summary") or "")
        route = str(step.get("route") or "#")
        html += (
            "<a class='gf-guide-card' href='"
            f"{escape(route)}'>"
            f"<strong>{escape(label)}</strong>"
            f"<span>{escape(shortcut)}</span>"
            f"<p>{escape(summary)}</p>"
            "</a>"
        )
    return f"{html}</div>"


def _clear_filter_overrides(request: GraphFakosRequest) -> dict[str, object]:
    return {key: None for key in request.filters}


def _clear_advanced_filter_overrides() -> dict[str, object]:
    return {
        "min_degree": None,
        "max_degree": None,
        "component_id": None,
        "connected_to_node_id": None,
        "evidence_filter": None,
        "cluster_id": None,
    }


def _command_palette(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    payload = _command_palette_payload(
        graph,
        visible_graph,
        request,
        focus,
        selected_edge,
    )
    query_errors = _query_errors(request.query)
    error_html = (
        _panel_body("Query Validation", _list(query_errors))
        if query_errors
        else _summary_note("Query validation passed; current graph state is preserved.")
    )
    return _panel(
        "Command Palette",
        _summary_note(
            "Search, jump, review evidence, open local graph lenses, or start provider-neutral authoring from one static-friendly command surface."
        )
        + "<section class='gf-command-palette' data-gf-command-palette-panel='true'>"
        + "<label class='gf-command-search'>Quick action search"
        "<input data-gf-command-search='true' data-gf-command-palette-search='true' "
        "placeholder='Try evidence, local, author, export...'></label>"
        f"{_command_palette_groups(payload['groups'])}"
        "<p class='gf-command-status' data-gf-command-palette-status='true' aria-live='polite'></p>"
        "</section>"
        + error_html
        + _json_script("data-gf-saved-queries", payload["saved_queries"])
        + _json_script("data-gf-command-palette", payload),
    )


def _command_palette_payload(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> dict[str, object]:
    saved_queries = (
        GraphFakosSavedQuery("hubs", "Hubs", "has:score", {"min_score": "0.8"}),
        GraphFakosSavedQuery("evidence", "Evidence", "has:provenance"),
        GraphFakosSavedQuery("warnings", "Warnings", "kind:warning"),
    )
    anchor = focus or _preferred_focus_node(visible_graph, request)
    source_node, target_node = _navigation_path_pair(
        graph, visible_graph, selected_edge
    )
    source_id = source_node.id if source_node is not None else ""
    target_id = target_node.id if target_node is not None else ""
    focus_id = anchor.id if anchor is not None else request.focus_node_id or ""
    groups = [
        _command_group(
            "query",
            "Saved Queries",
            [
                _command_action(
                    saved_query.query_id,
                    saved_query.label,
                    f"Run {saved_query.query}",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={"query": saved_query.query, **saved_query.filters},
                    ),
                    "query",
                    "Run",
                )
                for saved_query in saved_queries
            ],
        ),
        _command_group(
            "navigate",
            "Navigate",
            (
                _command_action(
                    "global",
                    "Global graph",
                    "Return to the full graph with the current display controls.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={"focus_node_id": None, "selected_edge_id": None},
                    ),
                    "navigate",
                    "Open",
                ),
                _command_action(
                    "local",
                    "Local neighborhood",
                    "Inspect the best current focus node at depth 1.",
                    _route_href(
                        request.with_screen("neighborhood"),
                        overrides={
                            "focus_node_id": focus_id or None,
                            "max_depth": 1,
                            "layout": "focus",
                        },
                    ),
                    "navigate",
                    "Open",
                    disabled=not focus_id,
                ),
                _command_action(
                    "path",
                    "Trace path",
                    "Open the path lens for the selected edge or visible anchors.",
                    _route_href(
                        request.with_screen("path"),
                        overrides={
                            "source_node_id": source_id or None,
                            "target_node_id": target_id or None,
                            "layout": "focus",
                        },
                    ),
                    "navigate",
                    "Trace",
                    disabled=not (source_id and target_id),
                ),
                _command_action(
                    "timeline",
                    "Timeline",
                    "Review timestamped nodes with step-safe playback.",
                    _route_href(
                        request.with_screen("timeline"),
                        overrides={"timeline_playback": "step", "layout": "timeline"},
                    ),
                    "navigate",
                    "Open",
                ),
                _command_action(
                    "status",
                    "Provider status",
                    "Inspect graph diagnostics, warnings, and provider capability notes.",
                    _route_href(request.with_screen("provider_status")),
                    "navigate",
                    "Open",
                ),
            ),
        ),
        _command_group(
            "review",
            "Review",
            (
                _command_action(
                    "evidence",
                    "Evidence review",
                    "Filter to provenance-bearing items and switch to provenance overlay.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "query": "has:provenance",
                            "analytics_overlay": "provenance",
                            "evidence_filter": "with_provenance",
                        },
                    ),
                    "review",
                    "Review",
                ),
                _command_action(
                    "case-packet",
                    "Build case packet",
                    "Create a structural investigation packet for the current focus.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "pivot_node_id": focus_id or None,
                            "pivot_mode": "neighbors",
                        },
                    ),
                    "review",
                    "Build",
                    disabled=not focus_id,
                ),
                _command_action(
                    "diff",
                    "Diff review",
                    "Compare current graph state with a baseline or overlay graph.",
                    _route_href(request.with_screen("diff")),
                    "review",
                    "Open",
                ),
                _command_action(
                    "context",
                    "Context preview",
                    "Preview graph context cards that a host could feed to an agent.",
                    _route_href(request.with_screen("context_preview")),
                    "review",
                    "Open",
                ),
            ),
        ),
        _command_group(
            "author",
            "Author",
            (
                _command_action(
                    "capture",
                    "Capture knowledge",
                    "Jump to the capture form with the current graph context attached.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={"focus_node_id": focus_id or None},
                    )
                    + "#capture-knowledge",
                    "author",
                    "Capture",
                    disabled="knowledge_capture" not in graph.capabilities,
                ),
                _command_action(
                    "draft-action",
                    "Draft graph action",
                    "Jump to provider-neutral graph action controls.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "focus_node_id": focus_id or None,
                            "selected_edge_id": selected_edge.id
                            if selected_edge is not None
                            else None,
                        },
                    )
                    + "#graph-authoring",
                    "author",
                    "Draft",
                    disabled="graph_action" not in graph.capabilities,
                ),
            ),
        ),
        _command_group(
            "export",
            "Export",
            (
                _command_action(
                    "share-route",
                    "Share route",
                    "Copy or open the current exact route state.",
                    _route_href(request),
                    "export",
                    "Open",
                ),
                _command_action(
                    "presentation",
                    "Presentation export view",
                    "Switch to paper theme, SVG fallback, and lower visual clutter.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "theme": "paper",
                            "render_engine": "svg",
                            "edge_clutter": "reduced",
                            "label_density": 0.82,
                        },
                    ),
                    "export",
                    "Apply",
                ),
            ),
        ),
    ]
    action_count = sum(len(group["actions"]) for group in groups)
    return {
        "screen": request.screen,
        "focus_node_id": focus_id,
        "selected_edge_id": selected_edge.id if selected_edge is not None else "",
        "visible_node_count": len(visible_graph.nodes),
        "visible_edge_count": len(visible_graph.edges),
        "group_count": len(groups),
        "action_count": action_count,
        "saved_queries": [item.to_dict() for item in saved_queries],
        "groups": groups,
        "provider_boundary": (
            "Command palette entries change only GraphFakos route/view state or "
            "jump to provider-neutral authoring forms; providers own persistence."
        ),
    }


def _command_group(
    group_id: str,
    label: str,
    actions: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> dict[str, object]:
    return {
        "id": group_id,
        "label": label,
        "actions": list(actions),
    }


def _command_action(
    action_id: str,
    label: str,
    summary: str,
    route: str,
    group: str,
    verb: str,
    *,
    disabled: bool = False,
) -> dict[str, object]:
    return {
        "id": action_id,
        "label": label,
        "summary": summary,
        "route": route,
        "group": group,
        "verb": verb,
        "disabled": disabled,
    }


def _command_palette_groups(groups: object) -> str:
    if not isinstance(groups, list) or not groups:
        return _empty("No command palette actions are available.")
    html = ""
    for group in groups:
        if not isinstance(group, dict):
            continue
        actions = group.get("actions")
        if not isinstance(actions, list):
            continue
        html += (
            "<section class='gf-command-group'>"
            f"<h4>{escape(str(group.get('label') or group.get('id') or 'Commands'))}</h4>"
        )
        for action in actions:
            if not isinstance(action, dict):
                continue
            disabled = bool(action.get("disabled"))
            route = "#" if disabled else str(action.get("route") or "#")
            verb = "Unavailable" if disabled else str(action.get("verb") or "Open")
            html += (
                "<div class='gf-route-row gf-command-row' "
                f"data-command-group='{escape(str(action.get('group') or ''))}' "
                f"data-command-id='{escape(str(action.get('id') or ''))}' "
                f"data-disabled='{str(disabled).lower()}'>"
                f"<div><strong>{escape(str(action.get('label') or action.get('id') or 'Command'))}</strong>"
                f"<span class='gf-inline-note'>{escape(str(action.get('summary') or ''))}</span></div>"
                f"<a class='gf-inline-link' href='{escape(route)}'>{escape(verb)}</a></div>"
            )
        html += "</section>"
    return html


def _query_errors(query: str) -> tuple[str, ...]:
    try:
        shlex.split(query)
    except ValueError as exc:
        return (f"query parse warning: {exc}",)
    return ()


def _search_results_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    payload = _search_results_payload(graph, request, focus)
    mode = str(payload["mode"]).replace("_", " ")
    return _panel(
        "Search Results",
        _summary_note(
            f"Ranked {mode} from the current visible graph, with route-backed jumps."
        )
        + "<section class='gf-search-results' data-gf-search-results-panel='true'>"
        f"{_search_result_rows(payload['results'])}"
        "</section>" + _json_script("data-gf-search-results", payload),
    )


def _search_results_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> dict[str, object]:
    query_terms = tuple(_parse_query(request.query)["terms"])
    focused_ids = {focus.id} if focus is not None else set()
    degree_map = _node_degree_map(graph)
    results = [
        _search_result_payload(graph, request, node, focus, query_terms, degree_map)
        for node in _ranked_nodes(graph, focused_ids)
    ][:8]
    return {
        "query": request.query,
        "mode": _search_result_mode(request),
        "focus_id": focus.id if focus is not None else None,
        "visible_node_count": len(graph.nodes),
        "result_count": len(results),
        "results": results,
    }


def _search_result_mode(request: GraphFakosRequest) -> str:
    if request.query:
        return "query_matches"
    if request.filters or any(
        (
            request.min_degree is not None,
            request.max_degree is not None,
            request.connected_to_node_id,
            request.component_id,
            request.cluster_id,
            request.evidence_filter,
        )
    ):
        return "filtered_nodes"
    return "top_visible_nodes"


def _search_result_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    node: GraphFakosNode,
    focus: GraphFakosNode | None,
    query_terms: tuple[str, ...],
    degree_map: dict[str, int],
) -> dict[str, object]:
    degree = degree_map.get(node.id, 0)
    evidence_route = _route_href(
        request.with_screen("provenance"),
        overrides={"focus_node_id": node.id, "selected_edge_id": None},
    )
    path_route = None
    if focus is not None and focus.id != node.id:
        path_edges = _shortest_path_edges(graph, focus.id, node.id)
        if path_edges:
            path_route = _route_href(
                request.with_screen("path"),
                overrides={
                    "source_node_id": focus.id,
                    "target_node_id": node.id,
                    "layout": "focus",
                    "selected_edge_id": None,
                },
            )
    return {
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "source": node.source,
        "score": node.score,
        "degree": degree,
        "matched_terms": [
            term for term in query_terms if _node_contains_text(node, term)
        ],
        "focus_route": _explore_href(request, focus_node_id=node.id),
        "local_route": _route_href(
            request.with_screen("neighborhood"),
            overrides={
                "focus_node_id": node.id,
                "max_depth": 1,
                "layout": "focus",
                "selected_edge_id": None,
            },
        ),
        "evidence_route": evidence_route,
        "path_route": path_route,
    }


def _search_result_rows(items: object) -> str:
    if not isinstance(items, list) or not items:
        return _empty("No visible nodes match the current query or filters.")
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("id") or "node")
        kind = str(item.get("kind") or "node")
        degree = str(item.get("degree", 0))
        score = item.get("score")
        score_note = f" · score {score}" if score is not None else ""
        rows.append(
            "<div class='gf-route-row gf-search-result-row'>"
            f"<div>{escape(label)}"
            f"<span class='gf-inline-note'>{escape(kind)} · degree {escape(degree)}{escape(score_note)}</span></div>"
            "<span class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('focus_route') or '#'))}'>Focus</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('local_route') or '#'))}'>Local</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('evidence_route') or '#'))}'>Evidence</a>"
            f"{_search_result_path_link(item)}"
            "</span></div>"
        )
    return _html_list(rows)


def _search_result_path_link(item: dict[str, object]) -> str:
    route = item.get("path_route")
    if not route:
        return ""
    return f"<a class='gf-inline-link' href='{escape(str(route))}'>Path</a>"


def _expansion_planner_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    if not graph.nodes:
        return _panel(
            "Expansion Planner",
            _empty("No visible nodes are available for expansion planning."),
        )
    payload = _expansion_planner_payload(graph, request, focus)
    node_options = tuple((node.id, node.label) for node in _ranked_nodes(graph, set()))
    edge_kinds = tuple(sorted({edge.kind for edge in graph.edges if edge.kind}))
    node_kinds = tuple(sorted({node.kind for node in graph.nodes if node.kind}))
    return _panel(
        "Expansion Planner",
        _summary_note(
            "Plan provider-owned neighbor expansion without making GraphFakos fetch or persist graph data."
        )
        + "<form method='get' action='/neighborhood' class='gf-panel-form' aria-label='Expansion planner controls'>"
        f"{_select_pairs('focus_node_id', 'Expansion source', node_options, str(payload['source_id']))}"
        f"{_select('max_depth', 'Depth', ('1', '2', '3'), str(payload['depth']))}"
        f"{_select('edge_kind', 'Edge kind', edge_kinds, str(payload['edge_kind']))}"
        f"{_select('node_kind', 'Node kind', node_kinds, str(payload['node_kind']))}"
        f"{_state_hidden_inputs(request, exclude=('focus_node_id', 'max_depth', 'edge_kind', 'node_kind'))}"
        "<button type='submit'>Preview Local Expansion</button>"
        "</form>"
        "<section class='gf-expansion-planner' data-gf-expansion-planner-panel='true'>"
        f"{_expansion_suggestion_rows(payload['suggestions'])}"
        "</section>" + _json_script("data-gf-expansion-plan", payload),
    )


def _expansion_planner_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> dict[str, object]:
    source = _expansion_source_node(graph, focus)
    edge_kind = request.filters.get("edge_kind", "")
    node_kind = request.filters.get("node_kind", "")
    depth = max(request.max_depth, 1)
    expansion_request = GraphFakosExpansionRequest(
        source_id=source.id,
        depth=depth,
        edge_kind=edge_kind,
        node_kind=node_kind,
    )
    suggestions = [
        _expansion_suggestion_payload(graph, request, node, edge_kind, node_kind)
        for node in _ranked_nodes(graph, {source.id})
    ][:6]
    return {
        "status": "planned",
        "source_id": source.id,
        "source_label": source.label,
        "depth": depth,
        "edge_kind": edge_kind,
        "node_kind": node_kind,
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "request": expansion_request.to_dict(),
        "suggestions": suggestions,
        "provider_boundary": (
            "GraphFakos plans the expansion request; providers or hosts own fetching, "
            "persisting, and rebuilding graph data."
        ),
    }


def _expansion_source_node(
    graph: GraphFakosGraph,
    focus: GraphFakosNode | None,
) -> GraphFakosNode:
    node_ids = {node.id for node in graph.nodes}
    if focus is not None and focus.id in node_ids:
        return focus
    return _ranked_nodes(graph, set())[0]


def _expansion_suggestion_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    node: GraphFakosNode,
    edge_kind: str,
    node_kind: str,
) -> dict[str, object]:
    degree = _node_degree_map(graph).get(node.id, 0)
    incident_edge_kinds = sorted(
        {
            edge.kind
            for edge in graph.edges
            if edge.kind and (edge.source_id == node.id or edge.target_id == node.id)
        }
    )
    return {
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "degree": degree,
        "incident_edge_kinds": incident_edge_kinds,
        "request": GraphFakosExpansionRequest(
            source_id=node.id,
            depth=1,
            edge_kind=edge_kind,
            node_kind=node_kind,
        ).to_dict(),
        "local_route": _route_href(
            request.with_screen("neighborhood"),
            overrides={"focus_node_id": node.id, "max_depth": 1, "layout": "focus"},
        ),
        "deeper_route": _route_href(
            request.with_screen("neighborhood"),
            overrides={"focus_node_id": node.id, "max_depth": 2, "layout": "focus"},
        ),
        "case_route": _route_href(
            request.with_screen("explore"),
            overrides={"pivot_node_id": node.id, "pivot_mode": "neighbors"},
        ),
    }


def _expansion_suggestion_rows(items: object) -> str:
    if not isinstance(items, list) or not items:
        return _empty("No expansion candidates are visible.")
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("id") or "node")
        kind = str(item.get("kind") or "node")
        degree = str(item.get("degree", 0))
        rows.append(
            "<div class='gf-route-row gf-expansion-row'>"
            f"<div>{escape(label)}"
            f"<span class='gf-inline-note'>{escape(kind)} · degree {escape(degree)}</span></div>"
            "<span class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('local_route') or '#'))}'>Local d1</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('deeper_route') or '#'))}'>Local d2</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('case_route') or '#'))}'>Case</a>"
            "</span></div>"
        )
    return _html_list(rows)


def _graph_data_table_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    payload = _graph_data_table_payload(graph, request)
    return _panel(
        "Graph Data Table",
        _summary_note(
            "Visible graph rows keep navigation, selection, and structural metrics usable beside the canvas."
        )
        + _badges(
            (
                (f"{payload['visible_node_count']} visible node(s)", "accent"),
                (f"{payload['visible_edge_count']} visible edge(s)", "blue"),
                (f"{payload['row_count']} row(s)", "neutral"),
            )
        )
        + _graph_data_rows(payload["rows"])
        + _json_script("data-gf-graph-data-table", payload),
    )


def _graph_data_table_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    degree_map = _node_degree_map(graph)
    component_ids = _node_component_ids(graph)
    selected_ids = set(request.selected_node_ids)
    rows = [
        _graph_data_row_payload(node, request, degree_map, component_ids, selected_ids)
        for node in sorted(
            graph.nodes,
            key=lambda item: (
                item.id not in selected_ids,
                item.id != request.focus_node_id,
                -degree_map.get(item.id, 0),
                -(item.score if item.score is not None else 0),
                item.label.casefold(),
            ),
        )[:16]
    ]
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "row_count": len(rows),
        "selected_node_ids": list(request.selected_node_ids),
        "focus_node_id": request.focus_node_id,
        "rows": rows,
        "provider_boundary": (
            "GraphFakos lists visible graph structure and route actions; "
            "providers remain responsible for durable storage and semantic truth."
        ),
    }


def _graph_data_row_payload(
    node: GraphFakosNode,
    request: GraphFakosRequest,
    degree_map: dict[str, int],
    component_ids: dict[str, str],
    selected_ids: set[str],
) -> dict[str, object]:
    next_selected = tuple(dict.fromkeys((*request.selected_node_ids, node.id)))
    return {
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "source": node.source,
        "degree": degree_map.get(node.id, 0),
        "component_id": component_ids.get(node.id, ""),
        "score": node.score,
        "confidence": node.confidence,
        "tags": list(node.tags),
        "provenance_count": len(node.provenance_ids),
        "citation_count": len(node.citation_ids),
        "selected": node.id in selected_ids,
        "focused": node.id == request.focus_node_id,
        "routes": {
            "focus": _explore_href(request, focus_node_id=node.id),
            "local": _route_href(
                request.with_screen("neighborhood"),
                overrides={"focus_node_id": node.id, "max_depth": 1},
            ),
            "case": _route_href(
                request.with_screen("explore"),
                overrides={"pivot_node_id": node.id, "pivot_mode": "neighbors"},
            ),
            "select": _route_href(
                request.with_screen("explore"),
                overrides={"selected_node_ids": ",".join(next_selected)},
            ),
        },
    }


def _graph_data_rows(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return _empty("No visible graph rows.")
    html = "<div class='gf-data-table' data-gf-graph-data-table-panel='true'>"
    for row in rows:
        if not isinstance(row, dict):
            continue
        routes = row.get("routes")
        if not isinstance(routes, dict):
            routes = {}
        markers = []
        if row.get("focused"):
            markers.append(("focused", "accent"))
        if row.get("selected"):
            markers.append(("selected", "blue"))
        html += (
            "<article class='gf-card gf-data-row'>"
            f"<h4>{escape(str(row.get('label') or row.get('id') or 'node'))}</h4>"
            + _badges(
                (
                    (str(row.get("kind") or "node"), "neutral"),
                    (f"degree {row.get('degree', 0)}", "accent"),
                    (str(row.get("component_id") or "component"), "blue"),
                    *markers,
                )
            )
            + _key_values(
                {
                    "id": row.get("id"),
                    "source": row.get("source"),
                    "score": row.get("score"),
                    "confidence": row.get("confidence"),
                    "evidence": (
                        f"{row.get('provenance_count', 0)} provenance / "
                        f"{row.get('citation_count', 0)} citation"
                    ),
                    "tags": ", ".join(str(tag) for tag in row.get("tags", [])[:4])
                    if isinstance(row.get("tags"), list)
                    else "",
                }
            )
            + "<div class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('focus') or '#'))}'>Focus</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('local') or '#'))}'>Local</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('case') or '#'))}'>Case</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('select') or '#'))}'>Select</a>"
            "</div></article>"
        )
    return f"{html}</div>"


def _relationship_data_table_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    payload = _relationship_data_table_payload(graph, request)
    return _panel(
        "Relationship Data Table",
        _summary_note(
            "Visible edge rows make relationships inspectable, filterable, and traceable without JavaScript."
        )
        + _badges(
            (
                (f"{payload['visible_edge_count']} visible edge(s)", "accent"),
                (f"{payload['row_count']} row(s)", "neutral"),
            )
        )
        + _relationship_data_rows(payload["rows"])
        + _json_script("data-gf-relationship-data-table", payload),
    )


def _relationship_data_table_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    node_map = graph.node_map()
    rows = [
        _relationship_data_row_payload(edge, request, node_map)
        for edge in sorted(
            graph.edges,
            key=lambda item: (
                item.id != request.selected_edge_id,
                item.kind.casefold(),
                -(item.confidence if item.confidence is not None else 0),
                item.id.casefold(),
            ),
        )[:18]
    ]
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "row_count": len(rows),
        "selected_edge_id": request.selected_edge_id,
        "rows": rows,
        "provider_boundary": (
            "GraphFakos lists visible relationship structure and routes; "
            "providers own durable relationship truth and mutation."
        ),
    }


def _relationship_data_row_payload(
    edge: GraphFakosEdge,
    request: GraphFakosRequest,
    node_map: dict[str, GraphFakosNode],
) -> dict[str, object]:
    source = node_map.get(edge.source_id)
    target = node_map.get(edge.target_id)
    return {
        "id": edge.id,
        "label": edge.label or edge.kind,
        "kind": edge.kind,
        "source_id": edge.source_id,
        "source_label": source.label if source is not None else edge.source_id,
        "target_id": edge.target_id,
        "target_label": target.label if target is not None else edge.target_id,
        "weight": edge.weight,
        "confidence": edge.confidence,
        "direction": edge.direction,
        "provenance_count": len(edge.provenance_ids),
        "citation_count": len(edge.citation_ids),
        "selected": edge.id == request.selected_edge_id,
        "routes": {
            "inspect": _explore_href(
                request,
                selected_edge_id=edge.id,
                focus_node_id=request.focus_node_id,
            ),
            "source": _explore_href(request, focus_node_id=edge.source_id),
            "target": _explore_href(request, focus_node_id=edge.target_id),
            "path": _route_href(
                request.with_screen("path"),
                overrides={
                    "source_node_id": edge.source_id,
                    "target_node_id": edge.target_id,
                    "selected_edge_id": edge.id,
                    "layout": "focus",
                },
            ),
            "kind": _route_href(
                request.with_screen("explore"),
                overrides={"edge_kind": edge.kind, "selected_edge_id": edge.id},
            ),
        },
    }


def _relationship_data_rows(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return _empty("No visible relationship rows.")
    html = (
        "<div class='gf-relationship-table' "
        "data-gf-relationship-data-table-panel='true'>"
    )
    for row in rows:
        if not isinstance(row, dict):
            continue
        routes = row.get("routes")
        if not isinstance(routes, dict):
            routes = {}
        markers = (("selected", "blue"),) if row.get("selected") else ()
        html += (
            "<article class='gf-card gf-relationship-row'>"
            f"<h4>{escape(str(row.get('source_label') or row.get('source_id') or 'source'))}"
            " -> "
            f"{escape(str(row.get('target_label') or row.get('target_id') or 'target'))}</h4>"
            + _badges(
                (
                    (str(row.get("kind") or "edge"), "accent"),
                    (str(row.get("direction") or "directed"), "neutral"),
                    *markers,
                )
            )
            + _key_values(
                {
                    "id": row.get("id"),
                    "label": row.get("label"),
                    "confidence": row.get("confidence"),
                    "weight": row.get("weight"),
                    "evidence": (
                        f"{row.get('provenance_count', 0)} provenance / "
                        f"{row.get('citation_count', 0)} citation"
                    ),
                }
            )
            + "<div class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('inspect') or '#'))}'>Inspect</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('source') or '#'))}'>Source</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('target') or '#'))}'>Target</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('path') or '#'))}'>Path</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('kind') or '#'))}'>Kind</a>"
            "</div></article>"
        )
    return f"{html}</div>"


def _evidence_coverage_map_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    payload = _evidence_coverage_map_payload(graph, request)
    return _panel(
        "Evidence Coverage Map",
        _summary_note(
            "Visible provenance and citation coverage stays structural; GraphFakos does not decide truth."
        )
        + _badges(
            (
                (
                    f"{payload['node_coverage']['with_any']} node(s) with evidence",
                    "accent",
                ),
                (
                    f"{payload['edge_coverage']['with_any']} edge(s) with evidence",
                    "blue",
                ),
                (f"{payload['gap_count']} visible gap(s)", "neutral"),
            )
        )
        + _evidence_coverage_rows(payload["coverage_rows"])
        + _json_script("data-gf-evidence-coverage-map", payload),
    )


def _evidence_coverage_map_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    node_coverage = _evidence_coverage_counts(graph.nodes)
    edge_coverage = _evidence_coverage_counts(graph.edges)
    rows = [
        _evidence_coverage_row(
            "nodes-with-provenance",
            "Nodes with provenance",
            node_coverage["with_provenance"],
            len(graph.nodes),
            _route_href(
                request.with_screen("explore"),
                overrides={"evidence_filter": "with_provenance"},
            ),
            "Declared provenance references on visible nodes.",
        ),
        _evidence_coverage_row(
            "nodes-missing-provenance",
            "Nodes missing provenance",
            node_coverage["missing_provenance"],
            len(graph.nodes),
            _route_href(
                request.with_screen("explore"),
                overrides={"evidence_filter": "missing_provenance"},
            ),
            "Visible nodes without declared provenance references.",
        ),
        _evidence_coverage_row(
            "nodes-with-citation",
            "Nodes with citations",
            node_coverage["with_citation"],
            len(graph.nodes),
            _route_href(
                request.with_screen("explore"),
                overrides={"evidence_filter": "with_citation"},
            ),
            "Declared citation references on visible nodes.",
        ),
        _evidence_coverage_row(
            "nodes-missing-citation",
            "Nodes missing citations",
            node_coverage["missing_citation"],
            len(graph.nodes),
            _route_href(
                request.with_screen("explore"),
                overrides={"evidence_filter": "missing_citation"},
            ),
            "Visible nodes without declared citation references.",
        ),
        _evidence_coverage_row(
            "edges-with-evidence",
            "Edges with evidence",
            edge_coverage["with_any"],
            len(graph.edges),
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "query": "has:provenance",
                    "analytics_overlay": "provenance",
                },
            ),
            "Visible relationships with provenance or citation references.",
        ),
        _evidence_coverage_row(
            "edges-missing-evidence",
            "Edges missing evidence",
            edge_coverage["missing_any"],
            len(graph.edges),
            _route_href(request.with_screen("provenance")),
            "Visible relationships without provenance or citation references.",
        ),
    ]
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "node_coverage": node_coverage,
        "edge_coverage": edge_coverage,
        "gap_count": node_coverage["missing_any"] + edge_coverage["missing_any"],
        "coverage_rows": rows,
        "provider_boundary": (
            "GraphFakos reports declared evidence coverage only; providers own "
            "source quality, claim truth, and evidence policy."
        ),
    }


def _evidence_coverage_counts(items: object) -> dict[str, int]:
    rows = [item for item in items if hasattr(item, "provenance_ids")]
    with_provenance = sum(1 for item in rows if item.provenance_ids)
    with_citation = sum(1 for item in rows if item.citation_ids)
    with_any = sum(1 for item in rows if item.provenance_ids or item.citation_ids)
    total = len(rows)
    return {
        "total": total,
        "with_provenance": with_provenance,
        "with_citation": with_citation,
        "with_any": with_any,
        "missing_provenance": total - with_provenance,
        "missing_citation": total - with_citation,
        "missing_any": total - with_any,
    }


def _evidence_coverage_row(
    row_id: str,
    label: str,
    count: int,
    total: int,
    route: str,
    summary: str,
) -> dict[str, object]:
    ratio = count / total if total else 0
    return {
        "id": row_id,
        "label": label,
        "count": count,
        "total": total,
        "ratio": round(ratio, 3),
        "percent": round(ratio * 100),
        "route": route,
        "summary": summary,
    }


def _evidence_coverage_rows(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return _empty("No evidence coverage rows are visible.")
    html = "<div class='gf-evidence-coverage' data-gf-evidence-coverage-panel='true'>"
    for row in rows:
        if not isinstance(row, dict):
            continue
        percent = int(row.get("percent") or 0)
        html += (
            "<article class='gf-evidence-coverage-row'>"
            "<div>"
            f"<h4>{escape(str(row.get('label') or row.get('id') or 'Coverage'))}</h4>"
            f"<p>{escape(str(row.get('summary') or ''))}</p>"
            "</div>"
            "<div class='gf-evidence-meter' "
            f"aria-label='{escape(str(row.get('label') or 'Coverage'))}: {percent} percent'>"
            f"<span style='width: {percent}%'></span>"
            "</div>"
            "<div class='gf-trail-actions'>"
            f"<strong>{escape(str(row.get('count', 0)))} / {escape(str(row.get('total', 0)))}</strong>"
            f"<a class='gf-inline-link' href='{escape(str(row.get('route') or '#'))}'>Review</a>"
            "</div>"
            "</article>"
        )
    return f"{html}</div>"


def _facet_explorer_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    payload = _facet_explorer_payload(graph, request)
    return _panel(
        "Facet Explorer",
        _summary_note(
            "Route-backed facets expose structural and provider-declared fields without changing graph truth."
        )
        + _facet_explorer_sections(payload["facets"])
        + _json_script("data-gf-facet-explorer", payload),
    )


def _facet_explorer_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    facets = [
        _facet_section(
            "node_kind",
            "Node kinds",
            _node_value_counts((node.kind for node in graph.nodes if node.kind)),
            request,
            active_value=request.filters.get("node_kind", ""),
        ),
        _facet_section(
            "source",
            "Sources",
            _node_value_counts((node.source for node in graph.nodes if node.source)),
            request,
            active_value=request.filters.get("source", ""),
        ),
        _facet_section(
            "tag",
            "Tags",
            _node_value_counts(
                (tag for node in graph.nodes for tag in node.tags if tag)
            ),
            request,
            active_value=request.filters.get("tag", ""),
        ),
        _facet_section(
            "component_id",
            "Components",
            _node_value_counts(_node_component_ids(graph).values()),
            request,
            active_value=request.component_id,
        ),
        _evidence_facet_section(graph, request),
        _degree_facet_section(graph, request),
    ]
    visible_facets = [facet for facet in facets if facet["items"]]
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "facets": visible_facets,
        "provider_boundary": (
            "GraphFakos counts visible structural fields and declared metadata; "
            "providers own field meaning and persistence."
        ),
    }


def _facet_section(
    facet_id: str,
    label: str,
    counts: dict[str, int],
    request: GraphFakosRequest,
    *,
    active_value: str,
) -> dict[str, object]:
    return {
        "id": facet_id,
        "label": label,
        "items": [
            {
                "value": value,
                "label": value,
                "count": count,
                "active": value == active_value,
                "route": _route_href(
                    request.with_screen("explore"), overrides={facet_id: value}
                ),
            }
            for value, count in _sorted_counts(counts)[:8]
        ],
    }


def _evidence_facet_section(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    counts = {
        "with_provenance": sum(1 for node in graph.nodes if node.provenance_ids),
        "with_citation": sum(1 for node in graph.nodes if node.citation_ids),
        "missing_provenance": sum(1 for node in graph.nodes if not node.provenance_ids),
        "missing_citation": sum(1 for node in graph.nodes if not node.citation_ids),
    }
    return {
        "id": "evidence_filter",
        "label": "Evidence",
        "items": [
            {
                "value": value,
                "label": value.replace("_", " "),
                "count": count,
                "active": value == request.evidence_filter,
                "route": _route_href(
                    request.with_screen("explore"),
                    overrides={"evidence_filter": value},
                ),
            }
            for value, count in counts.items()
            if count
        ],
    }


def _degree_facet_section(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    degree_map = _node_degree_map(graph)
    buckets = {
        "isolated": sum(1 for degree in degree_map.values() if degree == 0),
        "degree 1-2": sum(1 for degree in degree_map.values() if 1 <= degree <= 2),
        "degree 3+": sum(1 for degree in degree_map.values() if degree >= 3),
    }
    routes = {
        "isolated": {"min_degree": 0, "max_degree": 0},
        "degree 1-2": {"min_degree": 1, "max_degree": 2},
        "degree 3+": {"min_degree": 3, "max_degree": None},
    }
    active = _active_degree_bucket(request)
    return {
        "id": "degree",
        "label": "Degree",
        "items": [
            {
                "value": value,
                "label": value,
                "count": count,
                "active": value == active,
                "route": _route_href(
                    request.with_screen("explore"), overrides=routes[value]
                ),
            }
            for value, count in buckets.items()
            if count
        ],
    }


def _active_degree_bucket(request: GraphFakosRequest) -> str:
    if request.min_degree == 0 and request.max_degree == 0:
        return "isolated"
    if request.min_degree == 1 and request.max_degree == 2:
        return "degree 1-2"
    if request.min_degree == 3 and request.max_degree is None:
        return "degree 3+"
    return ""


def _node_value_counts(values: object) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    if not isinstance(values, str):
        for value in values:
            text = str(value).strip()
            if text:
                counts[text] += 1
    return dict(counts)


def _sorted_counts(counts: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))


def _facet_explorer_sections(facets: object) -> str:
    if not isinstance(facets, list) or not facets:
        return _empty("No facet values are visible.")
    html = "<div class='gf-facet-explorer' data-gf-facet-explorer-panel='true'>"
    for facet in facets:
        if not isinstance(facet, dict):
            continue
        items = facet.get("items")
        if not isinstance(items, list) or not items:
            continue
        html += (
            "<section class='gf-facet-group'>"
            f"<h4>{escape(str(facet.get('label') or facet.get('id') or 'Facet'))}</h4>"
        )
        for item in items:
            if not isinstance(item, dict):
                continue
            active = " aria-current='true'" if item.get("active") else ""
            html += (
                f"<a class='gf-facet-pill' href='{escape(str(item.get('route') or '#'))}'{active}>"
                f"<span>{escape(str(item.get('label') or item.get('value') or 'value'))}</span>"
                f"<strong>{escape(str(item.get('count', 0)))}</strong></a>"
            )
        html += "</section>"
    return f"{html}</div>"


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


def _readability_coach_panel(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    payload = _readability_coach_payload(graph, request)
    suggestions = payload["suggestions"]
    return _panel(
        "Readability Coach",
        _summary_note(
            "Structural display checks suggest route-backed tuning without changing provider data."
        )
        + _badges(
            (
                (str(payload["status"]).replace("_", " "), "accent"),
                (f"{payload['visible_node_count']} node(s)", "neutral"),
                (f"{payload['visible_edge_count']} edge(s)", "neutral"),
            )
        )
        + _readability_suggestion_rows(suggestions)
        + _json_script("data-gf-readability-coach", payload),
    )


def _readability_coach_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    analytics = analyze_graph(graph)
    hidden_nodes = int(graph.stats.get("hidden_nodes") or 0)
    hidden_edges = int(graph.stats.get("hidden_edges") or 0)
    edge_pressure = len(graph.edges) / max(len(graph.nodes), 1)
    metrics = {
        "average_degree": round(analytics.average_degree, 2),
        "density": round(analytics.density, 4),
        "edge_pressure": round(edge_pressure, 2),
        "hidden_nodes": hidden_nodes,
        "hidden_edges": hidden_edges,
        "label_density": request.label_density,
        "edge_opacity": request.edge_opacity,
        "edge_clutter": request.edge_clutter,
        "render_engine": request.render_engine,
        "render_limit": request.render_limit,
    }
    suggestions = _readability_suggestions(
        request,
        visible_node_count=len(graph.nodes),
        visible_edge_count=len(graph.edges),
        edge_pressure=edge_pressure,
        average_degree=analytics.average_degree,
        hidden_nodes=hidden_nodes,
        hidden_edges=hidden_edges,
    )
    return {
        "status": "needs_tuning" if suggestions else "comfortable",
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "metrics": metrics,
        "suggestions": suggestions,
    }


def _readability_suggestions(
    request: GraphFakosRequest,
    *,
    visible_node_count: int,
    visible_edge_count: int,
    edge_pressure: float,
    average_degree: float,
    hidden_nodes: int,
    hidden_edges: int,
) -> list[dict[str, object]]:
    suggestions: list[dict[str, object]] = []
    if hidden_nodes or hidden_edges:
        larger_limit = request.render_limit + max(25, request.render_limit // 2)
        suggestions.append(
            _readability_suggestion(
                "increase-render-budget",
                "Show more graph",
                f"{hidden_nodes} node(s) and {hidden_edges} edge(s) are outside the current render budget.",
                _route_href(request, overrides={"render_limit": larger_limit}),
            )
        )
    if edge_pressure > 1.4 and request.edge_clutter != "reduced":
        suggestions.append(
            _readability_suggestion(
                "reduce-edge-clutter",
                "Reduce edge clutter",
                "The visible graph has more edges than nodes; soften the edge layer first.",
                _route_href(
                    request,
                    overrides={
                        "edge_clutter": "reduced",
                        "edge_opacity": min(request.edge_opacity, 0.55),
                    },
                ),
            )
        )
    if request.label_density > 0.65 and (visible_node_count > 12 or average_degree > 2):
        suggestions.append(
            _readability_suggestion(
                "lower-label-density",
                "Lower label density",
                "Dense views scan better when only the highest-signal labels stay visible.",
                _route_href(request, overrides={"label_density": 0.45}),
            )
        )
    if request.edge_opacity > 0.7 and visible_edge_count > visible_node_count:
        suggestions.append(
            _readability_suggestion(
                "soften-edges",
                "Soften edges",
                "High edge opacity can overpower node groups in connected views.",
                _route_href(request, overrides={"edge_opacity": 0.5}),
            )
        )
    if visible_node_count > 30 and request.render_engine != "canvas":
        suggestions.append(
            _readability_suggestion(
                "try-canvas",
                "Try canvas renderer",
                "Canvas can make denser local previews smoother while SVG remains the fallback.",
                _route_href(request, overrides={"render_engine": "canvas"}),
            )
        )
    return suggestions


def _readability_suggestion(
    suggestion_id: str,
    title: str,
    reason: str,
    route: str,
) -> dict[str, object]:
    return {
        "id": suggestion_id,
        "title": title,
        "reason": reason,
        "route": route,
    }


def _readability_suggestion_rows(items: object) -> str:
    if not isinstance(items, list) or not items:
        return _empty(
            "Current display settings are within comfortable structural limits."
        )
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("id") or "Suggestion")
        reason = str(item.get("reason") or "")
        route = str(item.get("route") or "#")
        rows.append(
            "<div class='gf-route-row gf-readability-row'>"
            f"<div>{escape(title)}<span class='gf-inline-note'>{escape(reason)}</span></div>"
            f"<a class='gf-inline-link' href='{escape(route)}'>Apply</a></div>"
        )
    return _html_list(rows)


def _display_recipes_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    payload = _display_recipes_payload(graph, request, focus)
    return _panel(
        "Display Recipes",
        _summary_note(
            "Quick view recipes tune layout, filters, and display controls without changing provider data."
        )
        + _display_recipe_cards(payload["recipes"])
        + _json_script("data-gf-display-recipes", payload),
    )


def _display_recipes_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> dict[str, object]:
    focus_id = focus.id if focus is not None else request.focus_node_id
    if not focus_id:
        preferred = _preferred_focus_node(graph, request)
        focus_id = preferred.id if preferred is not None else ""
    recipes = [
        _display_recipe(
            request,
            "display-readable",
            "Readable review",
            "Balanced labels and softened edges for small and medium graphs.",
            {
                "layout": "force",
                "edge_clutter": "reduced",
                "edge_opacity": 0.65,
                "label_density": 0.65,
                "node_scale": 1.08,
                "render_engine": "svg",
            },
        ),
        _display_recipe(
            request,
            "display-dense",
            "Dense scan",
            "Fewer labels, softer links, and a larger render budget for busy graphs.",
            {
                "layout": "grouped",
                "edge_clutter": "reduced",
                "edge_opacity": 0.42,
                "label_density": 0.35,
                "render_engine": "canvas",
                "render_limit": max(request.render_limit, 240),
            },
        ),
        _display_recipe(
            request.with_screen("neighborhood"),
            "display-local",
            "Local focus",
            "Open the selected node as a one-hop local graph.",
            {
                "focus_node_id": focus_id,
                "layout": "focus",
                "max_depth": 1,
                "show_neighbor_links": True,
                "edge_clutter": "normal",
            },
        ),
        _display_recipe(
            request,
            "display-evidence",
            "Evidence review",
            "Prioritize provenance-bearing nodes and evidence overlays.",
            {
                "query": "has:provenance",
                "analytics_overlay": "provenance",
                "evidence_filter": "with_provenance",
                "edge_opacity": 0.7,
                "label_density": 0.75,
            },
        ),
        _display_recipe(
            request.with_screen("timeline"),
            "display-timeline",
            "Timeline review",
            "Switch to timestamped review with reduced motion-safe stepping.",
            {
                "layout": "timeline",
                "timeline_playback": "step",
                "edge_clutter": "reduced",
                "label_density": 0.8,
            },
        ),
        _display_recipe(
            request,
            "display-export",
            "Presentation export",
            "Paper theme, SVG fallback, and readable labels for portable snapshots.",
            {
                "theme": "paper",
                "render_engine": "svg",
                "edge_clutter": "reduced",
                "edge_opacity": 0.72,
                "label_density": 0.82,
                "camera_x": 0,
                "camera_y": 0,
                "camera_zoom": 1,
            },
        ),
    ]
    return {
        "active_recipe_id": request.preset_id,
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "recipes": recipes,
        "provider_boundary": (
            "Display recipes only change GraphFakos viewer state; providers own "
            "durable storage, semantic truth, and graph updates."
        ),
    }


def _display_recipe(
    request: GraphFakosRequest,
    recipe_id: str,
    label: str,
    summary: str,
    overrides: dict[str, object],
) -> dict[str, object]:
    route_overrides = {"preset_id": recipe_id, **overrides}
    return {
        "id": recipe_id,
        "label": label,
        "summary": summary,
        "overrides": route_overrides,
        "route": _route_href(request, overrides=route_overrides),
        "active": request.preset_id == recipe_id,
    }


def _display_recipe_cards(recipes: object) -> str:
    if not isinstance(recipes, list) or not recipes:
        return _empty("No display recipes are available.")
    html = "<div class='gf-display-recipes' data-gf-display-recipes-panel='true'>"
    for recipe in recipes:
        if not isinstance(recipe, dict):
            continue
        active = "true" if recipe.get("active") else "false"
        html += (
            "<a class='gf-recipe-card' "
            f"data-active='{active}' href='{escape(str(recipe.get('route') or '#'))}'>"
            f"<strong>{escape(str(recipe.get('label') or recipe.get('id') or 'Recipe'))}</strong>"
            f"<span>{escape(str(recipe.get('summary') or ''))}</span>"
            "</a>"
        )
    return f"{html}</div>"


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


def _state_hidden_inputs(
    request: GraphFakosRequest,
    *,
    exclude: tuple[str, ...] = (),
) -> str:
    excluded = {
        "screen",
        "filters",
        "include_provenance",
        "include_provider_payload",
        *exclude,
    }
    fields = []
    for key, value in request.to_dict().items():
        if key in excluded:
            continue
        route_key = "preset" if key == "preset_id" else key
        if isinstance(value, bool):
            encoded = "true" if value else "false"
        elif _route_value_is_empty(value):
            continue
        elif isinstance(value, dict):
            if not value:
                continue
            encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
        elif isinstance(value, (list, tuple)):
            if not value:
                continue
            encoded = ",".join(str(item) for item in value)
        else:
            encoded = str(value)
        fields.append(
            f"<input type='hidden' name='{escape(route_key)}' value='{escape(encoded)}'>"
        )
    for filter_key, filter_value in sorted(request.filters.items()):
        if filter_key in excluded or not filter_value:
            continue
        fields.append(
            f"<input type='hidden' name='{escape(filter_key)}' value='{escape(filter_value)}'>"
        )
    return "".join(fields)


def _advanced_filter_panel(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    return _panel(
        "Advanced Filters",
        "<form method='get' action='/explore' class='gf-panel-form' aria-label='Advanced graph filters'>"
        f"<input name='min_degree' value='{'' if request.min_degree is None else request.min_degree}' placeholder='Min degree'>"
        f"<input name='max_degree' value='{'' if request.max_degree is None else request.max_degree}' placeholder='Max degree'>"
        f"{_select_pairs('connected_to_node_id', 'Connected to', node_options, request.connected_to_node_id)}"
        f"{_select('evidence_filter', 'Evidence', ('with_provenance', 'with_citation', 'missing_provenance', 'missing_citation', 'warnings'), request.evidence_filter)}"
        f"{_state_hidden_inputs(request, exclude=('min_degree', 'max_degree', 'connected_to_node_id', 'evidence_filter'))}"
        "<button type='submit'>Apply Advanced Filters</button>"
        "</form>"
        + _summary_note(
            "Degree, neighbor, and evidence filters stay structural and provider-neutral."
        ),
    )


def _component_explorer_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    components = _component_groups(graph)
    component_cards = _component_card_payloads(graph, request, components)
    rows = []
    for component_id, node_ids in components.items():
        selected = " selected" if request.component_id == component_id else ""
        rows.append(
            f"<option value='{escape(component_id)}'{selected}>"
            f"{escape(component_id)} ({len(node_ids)} nodes)</option>"
        )
    return _panel(
        "Component Explorer",
        "<form method='get' action='/explore' class='gf-panel-form' aria-label='Component explorer'>"
        "<select name='component_id' aria-label='Component'>"
        "<option value=''>All components</option>"
        f"{''.join(rows)}</select>"
        f"<input name='cluster_id' value='{escape(request.cluster_id)}' placeholder='Provider cluster id'>"
        f"{_state_hidden_inputs(request, exclude=('component_id', 'cluster_id'))}"
        "<button type='submit'>Open Component</button>"
        "</form>"
        + _panel_body(
            "Structural Components",
            _component_cards(component_cards),
        )
        + _json_script(
            "data-gf-component-map",
            {"components": component_cards, "selected": request.component_id},
        ),
    )


def _component_card_payloads(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    components: dict[str, tuple[str, ...]],
) -> list[dict[str, object]]:
    node_map = graph.node_map()
    degree_map = _node_degree_map(graph)
    cards: list[dict[str, object]] = []
    for component_id, node_ids in components.items():
        nodes = tuple(node_map[node_id] for node_id in node_ids if node_id in node_map)
        if not nodes:
            continue
        node_id_set = {node.id for node in nodes}
        edges = tuple(
            edge
            for edge in graph.edges
            if edge.source_id in node_id_set and edge.target_id in node_id_set
        )
        hub = sorted(
            nodes,
            key=lambda node: (
                -degree_map.get(node.id, 0),
                -(node.score if node.score is not None else 0),
                node.label.casefold(),
            ),
        )[0]
        kinds: dict[str, int] = defaultdict(int)
        for node in nodes:
            if node.kind:
                kinds[node.kind] += 1
        cards.append(
            {
                "component_id": component_id,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "hub_node_id": hub.id,
                "hub_label": hub.label,
                "hub_degree": degree_map.get(hub.id, 0),
                "kinds": dict(
                    sorted(
                        kinds.items(),
                        key=lambda item: (-item[1], item[0].casefold()),
                    )
                ),
                "route": _route_href(
                    request.with_screen("explore"),
                    overrides={"component_id": component_id, "focus_node_id": hub.id},
                ),
                "hub_route": _explore_href(request, focus_node_id=hub.id),
                "case_packet_route": _route_href(
                    request.with_screen("explore"),
                    overrides={"pivot_node_id": hub.id, "pivot_mode": "neighbors"},
                ),
            }
        )
    return sorted(
        cards,
        key=lambda item: (
            -int(item["node_count"]),
            str(item["component_id"]),
        ),
    )


def _component_cards(cards: list[dict[str, object]]) -> str:
    if not cards:
        return _empty("No structural components.")
    html = "<div class='gf-component-grid' data-gf-component-cards='true'>"
    for card in cards:
        kinds = card.get("kinds")
        kind_badges: list[tuple[str, str]] = []
        if isinstance(kinds, dict):
            kind_badges = [
                (f"{kind}:{count}", "neutral")
                for kind, count in sorted(kinds.items())[:4]
            ]
        html += (
            "<article class='gf-card gf-component-card'>"
            f"<h4>{escape(str(card['component_id']))}</h4>"
            + _badges(
                [
                    (f"{card['node_count']} nodes", "accent"),
                    (f"{card['edge_count']} edges", "blue"),
                    (f"hub degree {card['hub_degree']}", "neutral"),
                ]
            )
            + _badges(kind_badges)
            + f"<p>Hub: {escape(str(card['hub_label']))}</p>"
            + "<div class='gf-route-row'>"
            + f"<div>Open component</div><a class='gf-inline-link' href='{escape(str(card['route']))}'>Open</a></div>"
            + "<div class='gf-route-row'>"
            + f"<div>Focus hub</div><a class='gf-inline-link' href='{escape(str(card['hub_route']))}'>Open</a></div>"
            + "<div class='gf-route-row'>"
            + f"<div>Build case packet</div><a class='gf-inline-link' href='{escape(str(card['case_packet_route']))}'>Open</a></div>"
            + "</article>"
        )
    return f"{html}</div>"


def _selection_workbench_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    selected_ids = request.selected_node_ids or (
        (request.focus_node_id,) if request.focus_node_id else ()
    )
    node_map = graph.node_map()
    selected_labels = [
        node_map[node_id].label if node_id in node_map else node_id
        for node_id in selected_ids
    ]
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    selection_sets = _selection_set_payload(graph, request, selected_ids)
    return _panel(
        "Multi-Select Workbench",
        _summary_note(
            f"{len(selected_ids)} selected node(s). Shift-click in the enhanced viewer toggles multi-select."
        )
        + "<form method='get' action='/explore' class='gf-panel-form' aria-label='Multi-select controls'>"
        f"<input name='selected_node_ids' value='{escape(','.join(selected_ids))}' placeholder='node:a,node:b'>"
        f"{_select_pairs('focus_node_id', 'Focus node', node_options, request.focus_node_id or '')}"
        f"{_state_hidden_inputs(request, exclude=('selected_node_ids', 'focus_node_id'))}"
        "<button type='submit'>Review Selection</button>"
        "</form>"
        + _panel_body("Selected Subgraph", _list(selected_labels))
        + _selection_set_cards(selection_sets["sets"])
        + _json_script("data-gf-selection-sets", selection_sets),
    )


def _selection_set_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    selected_ids: tuple[str, ...],
) -> dict[str, object]:
    degree_map = _node_degree_map(graph)
    component_ids = _node_component_ids(graph)
    focus_component = component_ids.get(request.focus_node_id or "", "")
    focus_component_ids = tuple(
        node.id
        for node in graph.nodes
        if focus_component and component_ids.get(node.id) == focus_component
    )
    hubs = tuple(
        node.id
        for node in sorted(
            graph.nodes,
            key=lambda item: (-degree_map.get(item.id, 0), item.label.casefold()),
        )
        if degree_map.get(node.id, 0) >= 3
    )
    evidence_nodes = tuple(
        node.id for node in graph.nodes if node.provenance_ids or node.citation_ids
    )
    sets = [
        _selection_set(
            request,
            "visible",
            "Select visible",
            "Carry every currently visible node into graph actions or case review.",
            tuple(node.id for node in graph.nodes),
        ),
        _selection_set(
            request,
            "hubs",
            "Select hubs",
            "Select structurally central visible nodes.",
            hubs,
        ),
        _selection_set(
            request,
            "evidence",
            "Select evidence",
            "Select visible nodes with provenance or citation links.",
            evidence_nodes,
        ),
        _selection_set(
            request,
            "focus-component",
            "Select focus component",
            "Select all visible nodes in the focused structural component.",
            focus_component_ids,
        ),
        _selection_set(
            request,
            "clear",
            "Clear selection",
            "Reset node and edge selection while preserving the current lens.",
            (),
            clear=True,
        ),
    ]
    return {
        "selected_node_ids": list(selected_ids),
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "sets": sets,
        "provider_boundary": (
            "Selection sets are GraphFakos viewer state only; providers decide "
            "whether submitted actions persist or rebuild graph data."
        ),
    }


def _selection_set(
    request: GraphFakosRequest,
    set_id: str,
    label: str,
    summary: str,
    node_ids: tuple[str, ...],
    *,
    clear: bool = False,
) -> dict[str, object]:
    overrides: dict[str, object] = {
        "selected_node_ids": None if clear else ",".join(node_ids),
        "selected_edge_id": None if clear else request.selected_edge_id,
    }
    case_overrides: dict[str, object] = {
        "selected_node_ids": None if clear else ",".join(node_ids),
        "pivot_node_id": node_ids[0] if node_ids else None,
        "pivot_mode": "neighbors" if node_ids else None,
    }
    return {
        "id": set_id,
        "label": label,
        "summary": summary,
        "node_ids": list(node_ids),
        "count": len(node_ids),
        "route": _route_href(request.with_screen("explore"), overrides=overrides),
        "case_route": _route_href(
            request.with_screen("explore"), overrides=case_overrides
        ),
    }


def _selection_set_cards(sets: object) -> str:
    if not isinstance(sets, list) or not sets:
        return _empty("No selection sets are available.")
    html = "<div class='gf-selection-sets' data-gf-selection-sets-panel='true'>"
    for item in sets:
        if not isinstance(item, dict):
            continue
        html += (
            "<article class='gf-selection-set-card'>"
            f"<h4>{escape(str(item.get('label') or item.get('id') or 'Selection set'))}</h4>"
            + _badges(((f"{item.get('count', 0)} node(s)", "accent"),))
            + f"<p>{escape(str(item.get('summary') or ''))}</p>"
            + "<div class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('route') or '#'))}'>Apply</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('case_route') or '#'))}'>Case</a>"
            "</div></article>"
        )
    return f"{html}</div>"


def _style_rules_panel(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    style_payload = {
        "color_by": request.style_color_by,
        "size_by": request.style_size_by,
        "edge_width_by": request.style_edge_width_by,
        "kinds": list(_graph_facets(graph).get("node_kind", ())),
    }
    return _panel(
        "Attribute Styling",
        "<form method='get' action='/explore' class='gf-panel-form' aria-label='Attribute style controls'>"
        f"{_select('style_color_by', 'Color by', ('kind', 'source', 'score', 'component'), request.style_color_by)}"
        f"{_select('style_size_by', 'Size by', ('score', 'degree', 'confidence', 'kind'), request.style_size_by)}"
        f"{_select('style_edge_width_by', 'Edge width by', ('kind', 'weight', 'confidence'), request.style_edge_width_by)}"
        f"{_state_hidden_inputs(request, exclude=_STYLE_STATE_EXCLUDES)}"
        "<button type='submit'>Apply Styling</button>"
        "</form>"
        + _badges(
            (
                (f"color:{request.style_color_by}", "accent"),
                (f"size:{request.style_size_by}", "blue"),
                (f"edge:{request.style_edge_width_by}", "neutral"),
            )
        )
        + _json_script("data-gf-style-rules", style_payload),
    )


def _timeline_animation_panel(
    graph: GraphFakosGraph, request: GraphFakosRequest
) -> str:
    frames = _timeline_frames(graph)
    return _panel(
        "Timeline/Diff Animation",
        "<form method='get' action='/explore' class='gf-panel-form' aria-label='Timeline animation controls'>"
        f"{_select('timeline_frame', 'Timeline frame', frames, request.timeline_frame)}"
        f"{_select('timeline_playback', 'Playback', ('stopped', 'playing', 'step'), request.timeline_playback)}"
        f"{_state_hidden_inputs(request, exclude=('timeline_frame', 'timeline_playback'))}"
        "<button type='submit'>Scrub Timeline</button>"
        "</form>"
        + _summary_note(
            "Animation is optional; static export renders the selected frame and exposes replay metadata."
        )
        + _json_script("data-gf-diff-frames", {"frames": list(frames)}),
    )


def _investigation_pivot_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    pivot_id = request.pivot_node_id or (focus.id if focus is not None else "")
    pivot_mode = request.pivot_mode or "neighbors"
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    case_packet = _case_packet_payload(graph, request, pivot_id, pivot_mode)
    return _panel(
        "Investigation Pivot",
        "<form method='get' action='/explore' class='gf-panel-form' aria-label='Investigation pivot controls'>"
        f"{_select_pairs('pivot_node_id', 'Pivot node', node_options, pivot_id)}"
        f"{_select('pivot_mode', 'Pivot mode', ('neighbors', 'paths', 'timeline', 'evidence_bundle'), pivot_mode)}"
        f"{_state_hidden_inputs(request, exclude=('pivot_node_id', 'pivot_mode'))}"
        "<button type='submit'>Build Case Packet</button>"
        "</form>"
        + _case_packet_view(case_packet)
        + _summary_note(
            "GraphFakos packages structural pivots only; providers own semantic truth and enrichment."
        )
        + _json_script("data-gf-investigation-case", case_packet),
    )


def _case_packet_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    pivot_id: str,
    pivot_mode: str,
) -> dict[str, object]:
    route = _route_href(
        request,
        overrides={"pivot_node_id": pivot_id, "pivot_mode": pivot_mode},
    )
    pivot = graph.node_map().get(pivot_id)
    if pivot is None:
        return {
            "pivot_node_id": pivot_id,
            "pivot_mode": pivot_mode,
            "route": route,
            "status": "missing",
        }

    degree_map = _node_degree_map(graph)
    component_ids = _node_component_ids(graph)
    component_id = component_ids.get(pivot.id, "")
    incident_edges = tuple(
        edge
        for edge in graph.edges
        if edge.source_id == pivot.id or edge.target_id == pivot.id
    )
    neighbors = _case_packet_neighbors(graph, request, pivot.id, degree_map)
    path_targets = _case_packet_path_targets(graph, request, pivot.id)
    timeline_events = [
        {"field": field, "value": value}
        for field, value in sorted(pivot.timestamps.items())
    ]
    component_nodes = [
        {"id": node.id, "label": node.label, "kind": node.kind}
        for node in graph.nodes
        if component_ids.get(node.id, "") == component_id
    ][:6]
    evidence_ids = sorted(
        {
            *pivot.provenance_ids,
            *(item for edge in incident_edges for item in edge.provenance_ids),
        }
    )
    citation_ids = sorted(
        {
            *pivot.citation_ids,
            *(item for edge in incident_edges for item in edge.citation_ids),
        }
    )
    return {
        "pivot_node_id": pivot.id,
        "pivot_label": pivot.label,
        "pivot_kind": pivot.kind,
        "pivot_mode": pivot_mode,
        "route": route,
        "status": "ready",
        "metrics": {
            "degree": degree_map.get(pivot.id, 0),
            "component": component_id,
            "neighbors": len(neighbors),
            "incident_edges": len(incident_edges),
            "provenance_refs": len(evidence_ids),
            "citation_refs": len(citation_ids),
            "timeline_events": len(timeline_events),
        },
        "neighbors": neighbors,
        "path_targets": path_targets,
        "evidence_bundle": {
            "provenance_ids": evidence_ids,
            "citation_ids": citation_ids,
        },
        "timeline_events": timeline_events,
        "component_sample": component_nodes,
    }


def _case_packet_neighbors(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    pivot_id: str,
    degree_map: dict[str, int],
) -> list[dict[str, object]]:
    node_map = graph.node_map()
    rows: list[dict[str, object]] = []
    for edge, neighbor_id in _adjacency_map(graph).get(pivot_id, ()):
        neighbor = node_map.get(neighbor_id)
        if neighbor is None:
            continue
        rows.append(
            {
                "id": neighbor.id,
                "label": neighbor.label,
                "kind": neighbor.kind,
                "edge_kind": edge.kind,
                "degree": degree_map.get(neighbor.id, 0),
                "route": _explore_href(request, focus_node_id=neighbor.id),
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            -int(item["degree"]),
            str(item["label"]).casefold(),
            str(item["id"]),
        ),
    )[:6]


def _case_packet_path_targets(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    pivot_id: str,
) -> list[dict[str, object]]:
    targets: list[dict[str, object]] = []
    for node in _ranked_nodes(graph, {pivot_id}):
        if node.id == pivot_id:
            continue
        path_edges = _shortest_path_edges(graph, pivot_id, node.id)
        if not path_edges:
            continue
        targets.append(
            {
                "id": node.id,
                "label": node.label,
                "kind": node.kind,
                "hop_count": len(path_edges),
                "route": _route_href(
                    request.with_screen("path"),
                    overrides={
                        "source_node_id": pivot_id,
                        "target_node_id": node.id,
                        "layout": "focus",
                        "selected_edge_id": None,
                    },
                ),
            }
        )
        if len(targets) >= 3:
            break
    return targets


def _case_packet_view(case_packet: dict[str, object]) -> str:
    if case_packet.get("status") == "missing":
        return _empty("Select a pivot node to build a structural case packet.")
    metrics = case_packet.get("metrics")
    neighbors = case_packet.get("neighbors")
    path_targets = case_packet.get("path_targets")
    evidence = case_packet.get("evidence_bundle")
    timeline_events = case_packet.get("timeline_events")
    component_sample = case_packet.get("component_sample")
    return (
        "<section class='gf-case-packet' data-gf-case-packet='true'>"
        "<h4>Case Packet</h4>"
        f"{_badges([(str(case_packet.get('pivot_kind', 'node')), 'accent'), (str(case_packet.get('pivot_mode', 'neighbors')), 'blue')])}"
        f"{_key_values(metrics if isinstance(metrics, dict) else {})}"
        "<h5>Nearest Neighbors</h5>"
        f"{_case_packet_link_list(neighbors)}"
        "<h5>Shortest Path Pivots</h5>"
        f"{_case_packet_link_list(path_targets, metric_key='hop_count', metric_label='hop')}"
        "<h5>Evidence Bundle</h5>"
        f"{_case_packet_evidence(evidence)}"
        "<h5>Timeline Markers</h5>"
        f"{_case_packet_key_list(timeline_events, 'field', 'value')}"
        "<h5>Component Sample</h5>"
        f"{_case_packet_key_list(component_sample, 'kind', 'label')}"
        "</section>"
    )


def _case_packet_link_list(
    items: object,
    *,
    metric_key: str = "edge_kind",
    metric_label: str = "",
) -> str:
    if not isinstance(items, list) or not items:
        return _empty("No structural items are available.")
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("id") or "item")
        route = str(item.get("route") or "#")
        metric = item.get(metric_key)
        metric_text = f"{metric_label} {metric}" if metric_label else str(metric or "")
        rows.append(
            "<div class='gf-route-row'>"
            f"<div>{escape(label)}<span class='gf-inline-note'>{escape(metric_text)}</span></div>"
            f"<a class='gf-inline-link' href='{escape(route)}'>Open</a></div>"
        )
    return _html_list(rows)


def _case_packet_evidence(evidence: object) -> str:
    if not isinstance(evidence, dict):
        return _empty("No evidence bundle.")
    provenance = evidence.get("provenance_ids")
    citations = evidence.get("citation_ids")
    return _key_values(
        {
            "provenance": ", ".join(provenance) if isinstance(provenance, list) else "",
            "citations": ", ".join(citations) if isinstance(citations, list) else "",
        }
    )


def _case_packet_key_list(
    items: object,
    key_field: str,
    value_field: str,
) -> str:
    if not isinstance(items, list) or not items:
        return _empty("No structural items are available.")
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get(key_field) or "")
        value = str(item.get(value_field) or "")
        rows.append(f"{key}: {value}" if key else value)
    return _list(rows)


def _context_menu_panel(
    request: GraphFakosRequest,
    node: GraphFakosNode | None,
    edge: GraphFakosEdge | None,
) -> str:
    node_id = node.id if node is not None else ""
    edge_id = edge.id if edge is not None else ""
    node_target = node_id or "none"
    edge_target = edge_id or "none"
    node_actions = _static_node_action_rows(request, node)
    edge_actions = _static_edge_action_rows(request, edge)
    return _panel(
        "Context Menus",
        "<details class='gf-context-menu' open><summary>Node Actions</summary>"
        f"{_html_list(node_actions) if node_actions else _list([f'Target: {node_target}'])}"
        "</details>"
        "<details class='gf-context-menu'><summary>Edge Actions</summary>"
        f"{_html_list(edge_actions) if edge_actions else _list([f'Target: {edge_target}'])}"
        "</details>",
    )


def _static_node_action_rows(
    request: GraphFakosRequest,
    node: GraphFakosNode | None,
) -> list[str]:
    if node is None:
        return []
    return [
        _route_action_row("Focus node", _explore_href(request, focus_node_id=node.id)),
        _route_action_row(
            "Expand neighborhood",
            _route_href(
                request.with_screen("neighborhood"),
                overrides={"focus_node_id": node.id, "max_depth": 1, "layout": "focus"},
            ),
        ),
        _route_action_row(
            "Evidence",
            _route_href(
                request.with_screen("provenance"),
                overrides={"focus_node_id": node.id},
            ),
        ),
        _route_action_row(
            "Trace path",
            _route_href(
                request.with_screen("path"),
                overrides={
                    "source_node_id": node.id,
                    "target_node_id": request.target_node_id,
                    "layout": "focus",
                    "selected_edge_id": None,
                },
            ),
        ),
        _route_action_row(
            "Build case packet",
            _route_href(
                request.with_screen("explore"),
                overrides={"pivot_node_id": node.id, "pivot_mode": "neighbors"},
            ),
        ),
        f"<span class='gf-inline-note'>Target: {escape(node.id)}</span>",
    ]


def _static_edge_action_rows(
    request: GraphFakosRequest,
    edge: GraphFakosEdge | None,
) -> list[str]:
    if edge is None:
        return []
    return [
        _route_action_row(
            "Inspect edge",
            _explore_href(
                request,
                selected_edge_id=edge.id,
                focus_node_id=request.focus_node_id,
            ),
        ),
        _route_action_row(
            "Trace path",
            _route_href(
                request.with_screen("path"),
                overrides={
                    "source_node_id": edge.source_id,
                    "target_node_id": edge.target_id,
                    "selected_edge_id": edge.id,
                    "layout": "focus",
                },
            ),
        ),
        _route_action_row(
            "Filter edge kind",
            _route_href(
                request.with_screen("explore"),
                overrides={"edge_kind": edge.kind, "selected_edge_id": edge.id},
            ),
        ),
        f"<span class='gf-inline-note'>Target: {escape(edge.id)}</span>",
    ]


def _route_action_row(label: str, route: str) -> str:
    return (
        f"<div class='gf-route-row'><div>{escape(label)}</div>"
        f"<a class='gf-inline-link' href='{escape(route)}'>Open</a></div>"
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


def _navigation_map_panel(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    payload = _navigation_map_payload(
        graph,
        visible_graph,
        request,
        focus,
        selected_edge,
    )
    return _panel(
        "Navigation Map",
        _summary_note(
            "Route-backed workbench lanes make screen changes, pivots, and review flows discoverable without JavaScript."
        )
        + _badges(
            (
                (f"{payload['lane_count']} lane(s)", "accent"),
                (f"{payload['visible_node_count']} visible node(s)", "neutral"),
                (f"{payload['visible_edge_count']} visible edge(s)", "neutral"),
            )
        )
        + _navigation_map_rows(payload["lanes"])
        + _json_script("data-gf-navigation-map", payload),
    )


def _navigation_map_payload(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> dict[str, object]:
    preferred_focus = focus or _preferred_focus_node(visible_graph, request)
    if preferred_focus is None:
        preferred_focus = _preferred_focus_node(graph, request)
    source, target = _navigation_path_pair(graph, visible_graph, selected_edge)
    focus_id = preferred_focus.id if preferred_focus is not None else ""
    lanes = [
        _navigation_lane(
            "global",
            "Global map",
            "Reset to the full visible graph and clear focused-node pressure.",
            "Explore",
            _route_href(
                request.with_screen("explore"),
                overrides={"focus_node_id": None, "layout": "force"},
            ),
            "g",
        ),
        _navigation_lane(
            "local",
            "Local graph",
            "Inspect the immediate neighborhood around the best current focus node.",
            "Open local",
            _route_href(
                request.with_screen("neighborhood"),
                overrides={
                    "focus_node_id": focus_id or None,
                    "max_depth": 1,
                    "layout": "focus",
                },
            ),
            "l",
            disabled=not focus_id,
        ),
        _navigation_lane(
            "path",
            "Trace path",
            "Move from a relationship or ranked pair into the path-tracing screen.",
            "Trace",
            _route_href(
                request.with_screen("path"),
                overrides={
                    "source_node_id": source.id if source is not None else None,
                    "target_node_id": target.id if target is not None else None,
                    "selected_edge_id": selected_edge.id
                    if selected_edge is not None
                    else None,
                    "layout": "focus",
                },
            ),
            "p",
            disabled=source is None or target is None,
        ),
        _navigation_lane(
            "evidence",
            "Evidence review",
            "Filter to evidence-bearing graph items and switch the overlay to provenance.",
            "Review evidence",
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "query": "has:provenance",
                    "analytics_overlay": "provenance",
                    "focus_node_id": focus_id or None,
                },
            ),
            "e",
        ),
        _navigation_lane(
            "timeline",
            "Timeline",
            "Review timestamped graph context with route-backed frame controls.",
            "Open timeline",
            _route_href(
                request.with_screen("timeline"),
                overrides={"timeline_playback": "step"},
            ),
            "t",
        ),
        _navigation_lane(
            "diff",
            "Diff review",
            "Compare graph snapshots and open change-focused review cards.",
            "Open diff",
            _route_href(request.with_screen("diff")),
            "d",
        ),
        _navigation_lane(
            "status",
            "Provider status",
            "Check provider capabilities, graph health, and adapter diagnostics.",
            "Open status",
            _route_href(request.with_screen("provider_status")),
            "s",
        ),
        _navigation_lane(
            "case",
            "Case packet",
            "Assemble a structural investigation packet around the current focus.",
            "Build case",
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "pivot_node_id": focus_id or None,
                    "pivot_mode": "neighbors",
                },
            ),
            "c",
            disabled=not focus_id,
        ),
    ]
    visible_lanes = [lane for lane in lanes if not lane["disabled"]]
    return {
        "screen": request.screen,
        "focus_node_id": focus_id,
        "selected_edge_id": selected_edge.id if selected_edge is not None else "",
        "visible_node_count": len(visible_graph.nodes),
        "visible_edge_count": len(visible_graph.edges),
        "lane_count": len(visible_lanes),
        "lanes": visible_lanes,
        "provider_boundary": (
            "GraphFakos exposes route-backed navigation lanes; providers own "
            "data loading, durable workflow state, and semantic meaning."
        ),
    }


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


def _navigation_lane(
    lane_id: str,
    label: str,
    summary: str,
    action_label: str,
    route: str,
    shortcut: str,
    *,
    disabled: bool = False,
) -> dict[str, object]:
    return {
        "id": lane_id,
        "label": label,
        "summary": summary,
        "action_label": action_label,
        "route": route,
        "shortcut_hint": shortcut,
        "disabled": disabled,
    }


def _navigation_map_rows(lanes: object) -> str:
    if not isinstance(lanes, list) or not lanes:
        return _empty("No navigation lanes are available for this graph.")
    html = "<div class='gf-navigation-map' data-gf-navigation-map-panel='true'>"
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        label = str(lane.get("label") or lane.get("id") or "Lane")
        summary = str(lane.get("summary") or "")
        shortcut = str(lane.get("shortcut_hint") or "")
        route = str(lane.get("route") or "#")
        action = str(lane.get("action_label") or "Open")
        html += (
            "<article class='gf-card gf-navigation-lane'>"
            f"<h4>{escape(label)}</h4>"
            + _badges(((f"key {shortcut}", "blue"),))
            + f"<p>{escape(summary)}</p>"
            + f"<a class='gf-inline-link' href='{escape(route)}'>{escape(action)}</a>"
            "</article>"
        )
    return f"{html}</div>"


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


def _relationship_trail_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    if focus is None:
        return ""
    payload = _relationship_trail_payload(graph, request, focus)
    return _panel(
        "Relationship Trail",
        _summary_note(
            "Follow structural hops from the selected node into local views or shortest-path traces."
        )
        + "<section class='gf-relationship-trail' data-gf-relationship-trail='true'>"
        "<h4>Nearest Hops</h4>"
        f"{_relationship_trail_rows(payload['neighbors'])}"
        "<h4>Path Targets</h4>"
        f"{_relationship_trail_rows(payload['path_targets'], path_mode=True)}"
        "</section>" + _json_script("data-gf-relationship-trail", payload),
    )


def _relationship_trail_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode,
) -> dict[str, object]:
    degree_map = _node_degree_map(graph)
    node_map = graph.node_map()
    neighbors: list[dict[str, object]] = []
    for edge, neighbor_id in _adjacency_map(graph).get(focus.id, ()):
        neighbor = node_map.get(neighbor_id)
        if neighbor is None:
            continue
        neighbors.append(
            {
                "id": neighbor.id,
                "label": neighbor.label,
                "kind": neighbor.kind,
                "edge_id": edge.id,
                "edge_kind": edge.kind,
                "degree": degree_map.get(neighbor.id, 0),
                "focus_route": _explore_href(request, focus_node_id=neighbor.id),
                "local_route": _route_href(
                    request.with_screen("neighborhood"),
                    overrides={
                        "focus_node_id": neighbor.id,
                        "max_depth": 1,
                        "layout": "focus",
                        "selected_edge_id": None,
                    },
                ),
                "path_route": _route_href(
                    request.with_screen("path"),
                    overrides={
                        "source_node_id": focus.id,
                        "target_node_id": neighbor.id,
                        "layout": "focus",
                        "selected_edge_id": None,
                    },
                ),
            }
        )
    neighbors = sorted(
        neighbors,
        key=lambda item: (
            -int(item["degree"]),
            str(item["edge_kind"]).casefold(),
            str(item["label"]).casefold(),
        ),
    )[:5]
    path_targets: list[dict[str, object]] = []
    for node in _ranked_nodes(graph, {focus.id}):
        if node.id == focus.id:
            continue
        path_edges = _shortest_path_edges(graph, focus.id, node.id)
        if not path_edges:
            continue
        path_targets.append(
            {
                "id": node.id,
                "label": node.label,
                "kind": node.kind,
                "hop_count": len(path_edges),
                "path_route": _route_href(
                    request.with_screen("path"),
                    overrides={
                        "source_node_id": focus.id,
                        "target_node_id": node.id,
                        "layout": "focus",
                        "selected_edge_id": None,
                    },
                ),
            }
        )
        if len(path_targets) >= 4:
            break
    return {
        "focus_id": focus.id,
        "focus_label": focus.label,
        "neighbors": neighbors,
        "path_targets": path_targets,
    }


def _relationship_trail_rows(items: object, *, path_mode: bool = False) -> str:
    if not isinstance(items, list) or not items:
        return _empty("No structural trail items are available.")
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("id") or "item")
        kind = str(item.get("kind") or "node")
        if path_mode:
            metric = f"{item.get('hop_count', 0)} hop(s)"
            route = str(item.get("path_route") or "#")
            rows.append(
                "<div class='gf-route-row'>"
                f"<div>{escape(label)}<span class='gf-inline-note'>{escape(kind)} · {escape(metric)}</span></div>"
                f"<a class='gf-inline-link' href='{escape(route)}'>Trace</a></div>"
            )
            continue
        edge_kind = str(item.get("edge_kind") or "edge")
        rows.append(
            "<div class='gf-route-row gf-trail-row'>"
            f"<div>{escape(label)}<span class='gf-inline-note'>{escape(kind)} · {escape(edge_kind)} · degree {escape(str(item.get('degree', 0)))}</span></div>"
            "<span class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('focus_route') or '#'))}'>Focus</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('local_route') or '#'))}'>Local</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('path_route') or '#'))}'>Path</a>"
            "</span></div>"
        )
    return _html_list(rows)


def _knowledge_capture_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    focus_id = focus.id if focus is not None else ""
    focus_label = focus.label if focus is not None else "the graph"
    supported = _graph_supports(graph, "knowledge_capture")
    support_tone = "accent" if supported else "neutral"
    support_label = "Capture supported" if supported else "Capture unsupported"
    submit_attrs = "" if supported else " disabled aria-disabled='true'"
    status_text = (
        ""
        if supported
        else "Current provider does not advertise workbench knowledge capture."
    )
    status_state = "" if supported else "error"
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    link_kinds = tuple(
        dict.fromkeys(
            (
                "mentions",
                "relates",
                "supports",
                "questions",
                *tuple(edge.kind for edge in graph.edges if edge.kind),
            )
        )
    )
    kinds = ("note", "memory", "document", "code", "task", "question", "warning")
    options = "".join(
        f"<option value='{escape(kind)}'>{escape(kind.title())}</option>"
        for kind in kinds
    )
    return (
        "<section class='gf-panel gf-capture-panel' id='capture-knowledge'>"
        "<div class='gf-panel-heading'><h3>Capture Knowledge</h3>"
        f"{_badge(support_label, support_tone)}</div>"
        + _summary_note(
            "Add a note, code observation, or question for the host provider or worker to persist and rebuild into the graph."
        )
        + "<form class='gf-capture-form' method='post' action='/api/knowledge' "
        f"data-gf-knowledge-form='true' data-gf-capability-supported='{str(supported).lower()}'>"
        f"{_capture_template_bar()}"
        f"<label>Text<textarea name='text' rows='5' required "
        f"placeholder='Write an observation about {escape(focus_label)}'></textarea></label>"
        f"<label>Kind<select name='kind'>{options}</select></label>"
        "<label>Tags<input name='tags' placeholder='ui, graph, code'></label>"
        "<label>Source<input name='source' value='workbench'></label>"
        f"<label>Attach to{_select_pairs('link_node_id', 'Attach note to node', node_options, focus_id)}</label>"
        f"<label>Relationship{_select('link_edge_kind', 'Relationship kind', link_kinds, 'mentions')}</label>"
        f"<input type='hidden' name='screen' value='{escape(request.screen)}'>"
        f"{_viewer_context_hidden_input(request)}"
        f"{_viewer_context_preview(graph, request)}"
        f"<button type='submit'{submit_attrs}>Add to graph</button>"
        f"<p class='gf-capture-status' data-gf-knowledge-status='true' data-state='{status_state}'>{escape(status_text)}</p>"
        "</form></section>"
    )


def _capture_template_bar() -> str:
    buttons = "".join(
        "<button type='button' "
        f"data-gf-capture-template='{escape(template_id)}' "
        f"data-kind='{escape(kind)}' "
        f"data-tags='{escape(tags)}' "
        "data-source='workbench' "
        f"data-placeholder='{escape(placeholder, quote=True)}'>"
        f"{escape(label)}</button>"
        for template_id, label, kind, tags, placeholder in _CAPTURE_TEMPLATES
    )
    return (
        "<div class='gf-capture-templates' data-gf-capture-templates='true' "
        "aria-label='Knowledge capture templates'>"
        "<span>Quick presets</span>"
        f"{buttons}"
        "</div>"
    )


def _graph_action_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    action_type, target_id, source_id, target_node_id = _graph_action_defaults(
        graph,
        request,
        focus,
    )
    supported = _graph_supports(graph, "graph_action")
    support_tone = "accent" if supported else "neutral"
    support_label = "Actions supported" if supported else "Actions unsupported"
    submit_attrs = "" if supported else " disabled aria-disabled='true'"
    status_text = (
        ""
        if supported
        else "Current provider does not advertise graph authoring actions."
    )
    status_state = "" if supported else "error"
    action = _draft_graph_action(action_type, target_id, source_id, target_node_id)
    status = _draft_action_status(action)
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    return (
        "<section class='gf-panel gf-action-panel' id='graph-authoring'>"
        "<div class='gf-panel-heading'><h3>Graph Authoring</h3>"
        f"{_badge(support_label, support_tone)}</div>"
        + _summary_note(
            "Draft node, edge, merge, and alias requests are provider-neutral; the host owns persistence."
        )
        + "<form class='gf-capture-form' method='post' action='/api/action' "
        f"data-gf-action-form='true' data-gf-capability-supported='{str(supported).lower()}'>"
        f"<input type='hidden' name='action_id' value='{escape(action.action_id)}'>"
        f"<label>Action<select name='action_type'>{_graph_action_options(action_type)}</select></label>"
        f"<label>Target{_select_pairs('target_id', 'Action target node', node_options, target_id)}</label>"
        f"<label>Source node{_select_pairs('source_id', 'Draft edge source', node_options, source_id)}</label>"
        f"<label>Target node{_select_pairs('target_node_id', 'Draft edge target', node_options, target_node_id)}</label>"
        "<label>Label<input name='label' placeholder='New node or edge label'></label>"
        "<label>Tags<input name='tags' placeholder='editor, review'></label>"
        "<label>Body<textarea name='body' rows='3' placeholder='Why should the provider apply this?'></textarea></label>"
        f"{_viewer_context_hidden_input(request)}"
        f"{_viewer_context_preview(graph, request)}"
        f"<button type='submit'{submit_attrs}>Queue action</button>"
        f"<p class='gf-capture-status' data-gf-action-status-text='true' data-state='{status_state}'>{escape(status_text)}</p>"
        "</form>"
        f"{_json_script('data-gf-action-template', action.to_dict())}"
        f"{_json_script('data-gf-action-status', status.to_dict())}"
        "</section>"
    )


def _graph_supports(graph: GraphFakosGraph, capability: str) -> bool:
    return capability in set(graph.capabilities)


def _graph_action_defaults(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> tuple[str, str, str, str]:
    node_ids = {node.id for node in graph.nodes}
    selected = tuple(
        node_id for node_id in request.selected_node_ids if node_id in node_ids
    )
    selected_edge = next(
        (edge for edge in graph.edges if edge.id == request.selected_edge_id),
        None,
    )
    if selected_edge is not None:
        source_id = (
            selected_edge.source_id if selected_edge.source_id in node_ids else ""
        )
        target_node_id = (
            selected_edge.target_id if selected_edge.target_id in node_ids else ""
        )
        target_id = focus.id if focus is not None else source_id or target_node_id
        return "draft_edge", target_id, source_id, target_node_id
    target_id = focus.id if focus is not None else (selected[0] if selected else "")
    source_id = selected[0] if selected else target_id
    target_node_id = selected[1] if len(selected) > 1 else ""
    action_type = "draft_edge" if source_id and target_node_id else "draft_node"
    return action_type, target_id, source_id, target_node_id


def _viewer_context_payload(request: GraphFakosRequest) -> dict[str, object]:
    return {
        "screen": request.screen,
        "query": request.query,
        "focus_node_id": request.focus_node_id or "",
        "selected_node_ids": list(request.selected_node_ids),
        "selected_edge_id": request.selected_edge_id or "",
        "camera": {
            "x": request.camera_x if request.camera_x is not None else 0.0,
            "y": request.camera_y if request.camera_y is not None else 0.0,
            "zoom": request.camera_zoom if request.camera_zoom is not None else 1.0,
            "yaw": request.camera_yaw if request.camera_yaw is not None else 0.0,
            "pitch": (
                request.camera_pitch if request.camera_pitch is not None else 0.0
            ),
        },
        "layout": request.layout,
        "render_engine": request.render_engine,
        "theme": request.theme,
        "saved_view_id": request.saved_view_id,
        "filters": dict(request.filters),
    }


def _viewer_context_hidden_input(request: GraphFakosRequest) -> str:
    payload = _viewer_context_payload(request)
    value = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"<input type='hidden' name='viewer_context' value='{escape(value, quote=True)}'>"


def _viewer_context_preview(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    node_map = graph.node_map()
    edge_map = graph.edge_map()
    selected_labels = [
        node_map[node_id].label if node_id in node_map else node_id
        for node_id in request.selected_node_ids
    ]
    selected_edge = edge_map.get(request.selected_edge_id or "")
    selection = ", ".join(selected_labels)
    if selected_edge is not None:
        selection = selected_edge.label or selected_edge.kind
    if not selection:
        selection = request.focus_node_id or "visible graph"
    camera = (
        f"x={request.camera_x or 0:.1f}, "
        f"y={request.camera_y or 0:.1f}, "
        f"zoom={request.camera_zoom or 1:.2f}, "
        f"yaw={request.camera_yaw or 0:.1f}, "
        f"pitch={request.camera_pitch or 0:.1f}"
    )
    filters = ", ".join(
        f"{key}={value}" for key, value in sorted(request.filters.items()) if value
    )
    rows = (
        (
            "Screen",
            request.screen
            if not request.query
            else f"{request.screen}: {request.query}",
        ),
        ("Selection", selection),
        ("Camera", camera),
        ("View", f"{request.layout} / {request.render_engine} / {request.theme}"),
        ("Filters", filters or "none"),
    )
    items = "".join(
        "<li>"
        f"<span>{escape(label)}</span>"
        f"<strong data-gf-viewer-context-row='{escape(label.lower())}'>{escape(value)}</strong>"
        "</li>"
        for label, value in rows
    )
    return (
        "<aside class='gf-viewer-context-preview' "
        "data-gf-viewer-context-preview='true' aria-label='Submission context'>"
        "<b>Submission Context</b>"
        f"<ul>{items}</ul>"
        "</aside>"
    )


def _draft_graph_action(
    action_type: str,
    target_id: str,
    source_id: str,
    target_node_id: str,
) -> GraphFakosGraphAction:
    return GraphFakosGraphAction(
        action_id="draft:route",
        action_type=action_type,
        label="Draft graph edge" if action_type == "draft_edge" else "Draft graph note",
        target_id=target_id,
        source_id=source_id,
        target_node_id=target_node_id,
    )


def _draft_action_status(action: GraphFakosGraphAction) -> GraphFakosActionStatus:
    return GraphFakosActionStatus(
        action_id=action.action_id,
        status="draft",
        message="GraphFakos can submit this provider-neutral action to a host provider.",
    )


def _graph_action_options(selected: str) -> str:
    return "".join(
        f"<option value='{escape(value)}'{(' selected' if value == selected else '')}>{escape(label)}</option>"
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
    width = 1280
    height = 720
    positions = _layout_positions(graph, request, width, height, selected_id)
    degree_map = _node_degree_map(graph)
    component_ids = _node_component_ids(graph)
    selected_node_ids = set(request.selected_node_ids)
    if selected_id:
        selected_node_ids.add(selected_id)
    live_selection = _live_selection_status(graph, selected_node_ids, selected_edge_id)
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
        edge_width = _edge_width(edge, request)
        edge_opacity = _clamped(request.edge_opacity, 0.15, 1.0)
        edge_inspect_route = _explore_href(
            request,
            selected_edge_id=edge.id,
            focus_node_id=selected_id,
        )
        edge_path_route = _route_href(
            request.with_screen("path"),
            overrides={
                "source_node_id": edge.source_id,
                "target_node_id": edge.target_id,
                "selected_edge_id": edge.id,
                "layout": "focus",
            },
        )
        edge_kind_route = _route_href(
            request.with_screen("explore"),
            overrides={"edge_kind": edge.kind, "selected_edge_id": edge.id},
        )
        edge_label = edge.label or edge.kind
        edge_path = _curved_edge_path(x1, y1, x2, y2, edge.id)
        edge_lines += (
            f"<a href='{edge_inspect_route}' class='gf-graph-item-link' "
            f"aria-label='Inspect edge {escape(edge_label)}. Press Shift+F10 for actions.' "
            "data-gf-graph-item='edge'>"
            f"<path class='gf-edge' data-edge-id='{escape(edge.id)}' "
            f"data-source-id='{escape(edge.source_id)}' data-target-id='{escape(edge.target_id)}' "
            f"data-kind='{escape(edge.kind)}' data-selected='{selected}' "
            f"data-label='{escape(edge_label)}' "
            f"data-inspect-route='{escape(edge_inspect_route)}' "
            f"data-path-route='{escape(edge_path_route)}' "
            f"data-kind-route='{escape(edge_kind_route)}' "
            f"data-path='{path_edge}' data-clutter='{escape(request.edge_clutter)}' "
            f"data-edge-width='{edge_width:.2f}' data-edge-opacity='{edge_opacity:.2f}' "
            f"data-source-x='{x1:.1f}' data-source-y='{y1:.1f}' "
            f"data-target-x='{x2:.1f}' data-target-y='{y2:.1f}' "
            f"d='{edge_path}' stroke-width='{edge_width:.2f}' "
            f"opacity='{edge_opacity:.2f}' marker-end='url(#gf-arrow)'>"
            f"<title>{escape(edge_label)}</title></path>"
            "</a>"
        )
    node_marks = ""
    for index, node in enumerate(graph.nodes):
        x, y = positions[node.id]
        selected = "true" if node.id in selected_node_ids else "false"
        pinned = (
            "true"
            if node.visual.pinned or node.id in request.pinned_positions
            else "false"
        )
        degree = degree_map.get(node.id, 0)
        label = (
            f"<text class='gf-node-label' y='{_node_label_y(index):.1f}' "
            f"text-anchor='middle'>{escape(_node_label(node))}</text>"
            if _should_show_label(node, index, degree, request, len(graph.nodes))
            else ""
        )
        node_focus_route = _explore_href(request, focus_node_id=node.id)
        node_local_route = _route_href(
            request.with_screen("neighborhood"),
            overrides={"focus_node_id": node.id, "max_depth": 1, "layout": "focus"},
        )
        node_evidence_route = _route_href(
            request.with_screen("provenance"),
            overrides={"focus_node_id": node.id},
        )
        node_path_route = _route_href(
            request.with_screen("path"),
            overrides={
                "source_node_id": selected_id or node.id,
                "target_node_id": node.id if selected_id != node.id else None,
                "selected_edge_id": None,
                "layout": "focus",
            },
        )
        node_pivot_route = _route_href(
            request.with_screen("explore"),
            overrides={"pivot_node_id": node.id, "pivot_mode": "neighbors"},
        )
        content_preview = _node_content_preview(graph, node)
        content_title = _node_content_title(graph, node)
        z = _node_depth_z(node, index)
        node_marks += (
            f"<a href='{node_focus_route}' class='gf-graph-item-link' "
            f"aria-label='Focus node {escape(node.label)}. Press Shift+F10 for actions.' "
            "data-gf-graph-item='node'>"
            f"<g class='gf-node' data-kind='{escape(node.kind)}' data-selected='{selected}' "
            f"data-node-id='{escape(node.id)}' data-node-ref='{escape(node.id)}' "
            f"data-label='{escape(node.label)}' "
            f"data-summary='{escape(node.summary or node.source or node.id)}' "
            f"data-source='{escape(node.source)}' "
            f"data-content-title='{escape(content_title)}' "
            f"data-content-preview='{escape(content_preview)}' "
            f"data-focus-route='{escape(node_focus_route)}' "
            f"data-local-route='{escape(node_local_route)}' "
            f"data-evidence-route='{escape(node_evidence_route)}' "
            f"data-path-route='{escape(node_path_route)}' "
            f"data-pivot-route='{escape(node_pivot_route)}' "
            f"data-provenance-ids='{escape(' '.join(node.provenance_ids))}' "
            f"data-citation-ids='{escape(' '.join(node.citation_ids))}' "
            f"data-component-id='{escape(component_ids.get(node.id, ''))}' "
            f"data-cluster-id='{escape(_node_cluster_id(node))}' "
            f"data-style-color='{escape(_style_value(node, request.style_color_by, component_ids))}' "
            f"data-style-size='{escape(_style_value(node, request.style_size_by, component_ids, degree=degree))}' "
            f"data-pinned='{pinned}' data-provider-pinned='{str(node.visual.pinned).lower()}' "
            f"data-degree='{degree}' data-x='{x:.1f}' data-y='{y:.1f}' data-z='{z:.1f}' "
            f"data-layout-x='{x:.1f}' data-layout-y='{y:.1f}' data-layout-z='{z:.1f}' "
            f"transform='translate({x:.1f} {y:.1f})'>"
            f"{_node_shape(node, request, degree)}"
            f"{label}"
            f"<title>{escape(node.summary or node.label)}</title></g></a>"
        )
    camera_x = request.camera_x if request.camera_x is not None else 0
    camera_y = request.camera_y if request.camera_y is not None else 0
    camera_zoom = request.camera_zoom if request.camera_zoom is not None else 1
    camera_yaw = request.camera_yaw if request.camera_yaw is not None else 0
    camera_pitch = request.camera_pitch if request.camera_pitch is not None else 0
    return (
        "<section class='gf-panel gf-canvas-panel'><div class='gf-panel-heading'>"
        "<h3>Graph Canvas</h3>"
        f"{_canvas_toolbar(request)}</div>"
        f"{_graph_search_panel(graph, request)}"
        f"<p class='gf-note'>Layout {escape(request.layout)}. Rendering {len(graph.nodes)} node(s) "
        f"and {len(graph.edges)} edge(s). Fit zooms to the current selection or visible graph; "
        "drag empty canvas to pan; drag a node to pin it; "
        "Shift-drag empty canvas to box-select nodes; right-click or press Shift+F10 on "
        "nodes or edges for actions.</p>"
        "<p class='gf-shortcut-hint'>Navigation: drag empty space to pan, scroll to zoom toward the cursor, "
        "Alt/Option-drag a node to move its cluster, WASD or arrows move like a map, "
        "Q/E nudges depth in 3D mode, 0 resets camera, F fullscreen, Delete clears selection.</p>"
        f"<p class='gf-live-selection' data-gf-live-selection='true' aria-live='polite' "
        f"data-selected-count='{len(selected_node_ids)}' "
        f"data-edge-selected='{str(bool(selected_edge_id)).lower()}'>{escape(live_selection)}</p>"
        f"{_renderer_notice(request)}"
        f"{_render_budget_panel(request, hidden_nodes, hidden_edges)}"
        f"<div class='gf-canvas-grid'><div class='gf-canvas-shell' tabindex='0' "
        f"data-camera-x='{camera_x:.2f}' data-camera-y='{camera_y:.2f}' "
        f"data-camera-zoom='{camera_zoom:.2f}' data-camera-yaw='{camera_yaw:.2f}' "
        f"data-camera-pitch='{camera_pitch:.2f}' data-render-engine='{escape(request.render_engine)}'>"
        f"{_canvas_renderer(graph, request)}"
        f"<svg class='gf-canvas' viewBox='0 0 {width} {height}' "
        "role='img' aria-label='GraphFakos graph canvas'>"
        "<defs><marker id='gf-arrow' markerWidth='8' markerHeight='8' refX='7' "
        "refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z'></path></marker></defs>"
        f"<g class='gf-viewport' transform='translate({camera_x:.2f} {camera_y:.2f}) scale({camera_zoom:.2f})'>"
        f"{edge_lines}{node_marks}</g></svg></div>"
        f"{_node_inspect_overlay(graph, selected_id)}"
        f"{_graph_minimap(graph, request, positions, width, height, selected_id, (camera_x, camera_y, camera_zoom))}</div>"
        f"{_group_controls(graph, request)}"
        f"{_graph_canvas_legend(graph, request)}</section>"
    )


def _live_selection_status(
    graph: GraphFakosGraph,
    selected_node_ids: set[str],
    selected_edge_id: str | None,
) -> str:
    node_map = graph.node_map()
    edge_map = graph.edge_map()
    node_labels = [
        node_map[node_id].label if node_id in node_map else node_id
        for node_id in sorted(selected_node_ids)
        if node_id
    ]
    parts: list[str] = []
    if len(node_labels) == 1:
        parts.append(f"Selected 1 node: {node_labels[0]}.")
    elif len(node_labels) > 1:
        suffix = ", ..." if len(node_labels) > 3 else "."
        parts.append(
            f"Selected {len(node_labels)} nodes: {', '.join(node_labels[:3])}{suffix}"
        )
    if selected_edge_id:
        edge = edge_map.get(selected_edge_id)
        edge_label = edge.label or edge.kind if edge is not None else selected_edge_id
        parts.append(f"Selected edge: {edge_label}.")
    return (
        " ".join(parts)
        or "No selected graph items. Shift-click nodes or Shift-drag canvas to select several."
    )


def _canvas_toolbar(request: GraphFakosRequest) -> str:
    saved_route = _route_href(
        request,
        overrides={
            "camera_x": request.camera_x,
            "camera_y": request.camera_y,
            "camera_zoom": request.camera_zoom,
            "camera_yaw": request.camera_yaw,
            "camera_pitch": request.camera_pitch,
        },
    )
    clear_pins_route = _route_href(request, overrides={"pinned_positions": None})
    next_theme = "default" if request.theme == "space" else "space"
    theme_label = "Light" if request.theme == "space" else "Space"
    theme_route = _route_href(request, overrides={"theme": next_theme})
    return (
        "<div class='gf-canvas-tools' aria-label='Graph camera controls'>"
        "<button type='button' data-gf-camera='zoom-in' title='Zoom in' aria-label='Zoom in'>+</button>"
        "<button type='button' data-gf-camera='zoom-out' title='Zoom out' aria-label='Zoom out'>-</button>"
        "<button type='button' data-gf-camera='fit' title='Fit selected or visible graph' "
        "aria-label='Fit selected or visible graph'>Fit</button>"
        "<button type='button' data-gf-camera='reset' title='Reset camera' aria-label='Reset camera'>Reset</button>"
        "<button type='button' data-gf-camera='fullscreen' title='Fullscreen' aria-label='Fullscreen'>Full</button>"
        "<button type='button' data-gf-pin='reset' title='Reset pinned node positions' aria-label='Reset pinned node positions'>Reset Pins</button>"
        f"<a class='gf-tool-link gf-theme-toggle' data-gf-theme-toggle='true' href='{escape(theme_route)}'>{theme_label}</a>"
        f"<a class='gf-tool-link' href='{escape(clear_pins_route)}'>Clear pins</a>"
        f"<a class='gf-tool-link' data-gf-save-view='true' href='{escape(saved_route)}'>Saved view</a>"
        "</div>"
    )


def _graph_search_panel(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    options = "".join(
        f"<option value='{escape(node.id)}' label='{escape(node.label)}'></option>"
        for node in _ranked_nodes(graph, set())
    )
    return (
        "<form class='gf-command-bar' method='get' action='/explore' "
        "aria-label='Graph search palette' data-gf-search-form='true'>"
        "<input list='gf-node-search-options' name='focus_node_id' class='gf-search-input' "
        "data-gf-command-search='true' aria-keyshortcuts='/ Control+K Meta+K' "
        "placeholder='Jump to node, edge, or path target'>"
        f"<datalist id='gf-node-search-options'>{options}</datalist>"
        f"{_state_hidden_inputs(request, exclude=('focus_node_id',))}"
        "<button type='submit'>Jump</button>"
        "<span class='gf-command-shortcut'>/ or Ctrl+K</span>"
        "</form>"
    )


def _renderer_notice(request: GraphFakosRequest) -> str:
    if request.render_engine == "svg":
        return ""
    if request.render_engine == "canvas":
        return (
            "<p class='gf-note gf-renderer-notice'>"
            "Canvas renderer is enabled for progressive drawing; the SVG graph remains "
            "available as the static fallback and accessibility surface."
            "</p>"
        )
    if request.render_engine == "3d":
        return (
            "<p class='gf-note gf-renderer-notice'>"
            "3D navigation mode is selected. This portable export keeps the SVG graph "
            "as the accessibility fallback while browser hosts can enhance orbit, "
            "cluster drag, and space-style navigation from the same state."
            "</p>"
        )
    return (
        "<p class='gf-note gf-renderer-notice'>"
        f"Requested renderer {escape(request.render_engine)} is recorded for host workbenches; "
        "this portable export degrades to the static SVG renderer."
        "</p>"
    )


def _canvas_renderer(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    if request.render_engine != "canvas":
        return ""
    payload = {
        "graph_id": graph.graph_id,
        "nodes": [
            {
                "id": node.id,
                "label": node.label,
                "kind": node.kind,
                "score": node.score,
            }
            for node in graph.nodes
        ],
        "edges": [
            {
                "id": edge.id,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "kind": edge.kind,
                "weight": edge.weight,
            }
            for edge in graph.edges
        ],
    }
    return (
        "<canvas class='gf-canvas-renderer' data-gf-canvas='true' "
        "width='1280' height='720' aria-label='Canvas graph renderer'></canvas>"
        f"{_json_script('data-gf-canvas-payload', payload)}"
    )


def _curved_edge_path(x1: float, y1: float, x2: float, y2: float, edge_id: str) -> str:
    dx = x2 - x1
    dy = y2 - y1
    distance = sqrt(dx * dx + dy * dy) or 1.0
    bend_sign = -1 if sum(ord(char) for char in edge_id) % 2 else 1
    bend = min(46.0, max(10.0, distance * 0.12)) * bend_sign
    control_x = (x1 + x2) / 2 - dy / distance * bend
    control_y = (y1 + y2) / 2 + dx / distance * bend
    return f"M{x1:.1f},{y1:.1f} Q{control_x:.1f},{control_y:.1f} {x2:.1f},{y2:.1f}"


def _node_depth_z(node: GraphFakosNode, index: int) -> float:
    seed = sum(ord(char) for char in f"{node.kind}:{node.id}") + index * 37
    return float(seed % 360 - 180)


def _edge_width(edge: GraphFakosEdge, request: GraphFakosRequest) -> float:
    base = 1.4
    if request.style_edge_width_by == "weight" and edge.weight is not None:
        base = 1.0 + edge.weight * 2.0
    elif request.style_edge_width_by == "confidence" and edge.confidence is not None:
        base = 1.0 + edge.confidence * 2.0
    elif request.style_edge_width_by == "kind":
        base = 1.2 + (abs(hash(edge.kind)) % 4) * 0.35
    return _clamped(base * request.edge_scale, 0.5, 7.0)


def _should_show_label(
    node: GraphFakosNode,
    index: int,
    degree: int,
    request: GraphFakosRequest,
    visible_count: int,
) -> bool:
    density = _clamped(request.label_density, 0.0, 1.0)
    if node.id == request.focus_node_id or node.id in request.selected_node_ids:
        return True
    if visible_count <= 12:
        return density >= 0.2
    if visible_count >= 160:
        cadence = max(12, int(round(42 / max(density, 0.18))))
        return degree >= 5 or index % cadence == 0
    if visible_count >= 60:
        cadence = max(6, int(round(18 / max(density, 0.18))))
        return degree >= 4 or index % cadence == 0
    if density >= 0.95:
        return degree >= 2 or index % 4 == 0
    if degree >= 3:
        return density >= 0.35
    cadence = max(1, int(round(1 / max(density, 0.12))))
    return index % cadence == 0


def _style_value(
    node: GraphFakosNode,
    style_field: str,
    component_ids: dict[str, str],
    *,
    degree: int = 0,
) -> str:
    if style_field == "source":
        return node.source
    if style_field == "score":
        return "scored" if node.score is not None else "unscored"
    if style_field == "confidence":
        return "confident" if node.confidence is not None else "unknown"
    if style_field == "component":
        return component_ids.get(node.id, "")
    if style_field == "degree":
        return str(degree)
    return node.kind


def _clamped(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


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


def _node_shape(
    node: GraphFakosNode,
    request: GraphFakosRequest,
    degree: int,
) -> str:
    radius = _node_radius(node, request, degree)
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
    request: GraphFakosRequest,
    positions: dict[str, tuple[float, float]],
    width: int,
    height: int,
    selected_id: str | None,
    camera: tuple[float, float, float],
) -> str:
    nodes = "".join(
        _minimap_node(node, request, positions[node.id], width, height, selected_id)
        for node in graph.nodes
        if node.id in positions
    )
    return (
        "<aside class='gf-minimap' aria-label='Graph minimap'>"
        "<div class='gf-minimap-heading'>Minimap</div>"
        f"<svg viewBox='0 0 {_MINIMAP_WIDTH} {_MINIMAP_HEIGHT}' role='img' "
        "aria-label='Visible graph minimap'>"
        f"{_minimap_viewport(width, height, camera)}{nodes}</svg></aside>"
    )


def _minimap_viewport(
    width: int,
    height: int,
    camera: tuple[float, float, float],
) -> str:
    camera_x, camera_y, camera_zoom = camera
    zoom = max(camera_zoom, 0.01)
    min_x = _clamped(-camera_x / zoom, 0, width)
    min_y = _clamped(-camera_y / zoom, 0, height)
    max_x = _clamped((width - camera_x) / zoom, 0, width)
    max_y = _clamped((height - camera_y) / zoom, 0, height)
    rect_x = min(min_x, max_x) / width * _MINIMAP_WIDTH
    rect_y = min(min_y, max_y) / height * _MINIMAP_HEIGHT
    rect_width = abs(max_x - min_x) / width * _MINIMAP_WIDTH
    rect_height = abs(max_y - min_y) / height * _MINIMAP_HEIGHT
    return (
        "<rect class='gf-minimap-viewport' data-gf-minimap-viewport='true' "
        f"data-camera-x='{camera_x:.2f}' data-camera-y='{camera_y:.2f}' "
        f"data-camera-zoom='{camera_zoom:.2f}' "
        f"x='{rect_x:.1f}' y='{rect_y:.1f}' "
        f"width='{rect_width:.1f}' height='{rect_height:.1f}'></rect>"
    )


def _minimap_node(
    node: GraphFakosNode,
    request: GraphFakosRequest,
    position: tuple[float, float],
    width: int,
    height: int,
    selected_id: str | None,
) -> str:
    x, y = position
    selected = "true" if node.id == selected_id else "false"
    scaled_x = x / width * _MINIMAP_WIDTH
    scaled_y = y / height * _MINIMAP_HEIGHT
    focus_route = _explore_href(request, focus_node_id=node.id)
    return (
        f"<a href='{escape(focus_route)}' class='gf-minimap-node-link' "
        f"aria-label='Focus minimap node {escape(node.label)}' "
        f"data-gf-minimap-node='true' data-minimap-node-id='{escape(node.id)}' "
        f"data-node-ref='{escape(node.id)}' data-focus-route='{escape(focus_route)}'>"
        f"<circle cx='{scaled_x:.1f}' cy='{scaled_y:.1f}' "
        f"r='{_MINIMAP_NODE_RADIUS}' data-selected='{selected}' "
        f"data-node-ref='{escape(node.id)}' data-minimap-node-id='{escape(node.id)}'>"
        f"<title>{escape(node.label)}</title></circle></a>"
    )


def _group_controls(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    kinds = _facet_values(graph, "node_kind")
    if not kinds:
        return ""
    buttons = "".join(
        f"<button type='button' data-gf-group='{escape(kind)}' "
        f"data-active='true' title='Toggle {escape(kind)} nodes'>{escape(kind)}</button>"
        for kind in kinds
    )
    links = "".join(
        f"<a href='{_route_href(request, overrides={'node_kind': kind})}'>{escape(kind)}</a>"
        for kind in kinds
    )
    return (
        "<div class='gf-group-controls' aria-label='Node group controls'>"
        f"<div>{buttons}<button type='button' data-gf-group-show-all='true'>Show all</button></div>"
        f"<div class='gf-group-fallback'>{links}</div></div>"
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


def _node_radius(
    node: GraphFakosNode,
    request: GraphFakosRequest | None = None,
    degree: int = 0,
) -> int:
    scale = request.node_scale if request is not None else 1.0
    base = 10 if node.score is None else max(8, min(18, int(8 + node.score * 10)))
    if request is not None and request.style_size_by == "degree":
        base = max(base, 8 + min(degree, 8))
    if (
        request is not None
        and request.style_size_by == "confidence"
        and node.confidence
    ):
        base = max(base, int(8 + node.confidence * 10))
    return max(4, min(30, int(base * _clamped(scale, 0.35, 2.2))))


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


def _node_provider_content(
    graph: GraphFakosGraph, node: GraphFakosNode
) -> dict[str, object]:
    envelope = graph.provider_payload.get("viewer_envelope")
    if not isinstance(envelope, dict):
        return {}
    content_index = envelope.get("content_index")
    if not isinstance(content_index, dict):
        return {}
    content = content_index.get(node.id)
    return dict(content) if isinstance(content, dict) else {}


def _node_content_title(graph: GraphFakosGraph, node: GraphFakosNode) -> str:
    content = _node_provider_content(graph, node)
    return str(content.get("title") or node.label or node.id)


def _node_content_preview(graph: GraphFakosGraph, node: GraphFakosNode) -> str:
    content = _node_provider_content(graph, node)
    text = str(content.get("text") or content.get("preview") or "")
    if text.strip():
        return text.strip()
    return node.summary or node.source or node.id


def _node_inspect_overlay(
    graph: GraphFakosGraph,
    selected_id: str | None,
) -> str:
    node = graph.node_map().get(selected_id or "") if selected_id else None
    title = _node_content_title(graph, node) if node is not None else "Select a node"
    summary = (
        _node_content_preview(graph, node)
        if node is not None
        else "Click any graph node to inspect its content, evidence, and actions."
    )
    node_id = node.id if node is not None else ""
    source = node.source if node is not None else ""
    kind = node.kind if node is not None else "node"
    metadata = _node_metadata(node) if node is not None else {}
    metadata_json = _json_attribute(metadata)
    properties = _key_values(metadata) if metadata else _empty("No properties yet.")
    open_state = "false"
    return (
        "<aside class='gf-inspect-overlay' data-gf-inspect-overlay='true' "
        f"data-open='{open_state}' aria-live='polite' aria-label='Selected node inspector'>"
        "<div class='gf-inspect-overlay-bar'>"
        "<span data-gf-inspect-kind='true'>"
        f"{escape(kind)}</span>"
        "<button type='button' data-gf-inspect-close='true' aria-label='Close inspector'>Close</button>"
        "</div>"
        f"<h3 data-gf-inspect-title='true'>{escape(title)}</h3>"
        f"<p data-gf-inspect-summary='true'>{escape(summary)}</p>"
        "<details class='gf-inspect-section' open>"
        "<summary>Content</summary>"
        f"<p data-gf-inspect-content='true'>{escape(summary)}</p>"
        "</details>"
        "<details class='gf-inspect-section'>"
        "<summary>Properties</summary>"
        f"<div data-gf-inspect-properties='true' data-properties-json='{metadata_json}'>"
        f"{properties}</div>"
        "</details>"
        "<details class='gf-inspect-section'>"
        "<summary>Evidence</summary>"
        "<p data-gf-inspect-evidence='true'>"
        "Use Evidence for provenance and citations without mutating provider truth.</p>"
        "</details>"
        "<form class='gf-inspect-command' data-gf-inspect-command='true'>"
        "<label>Note<textarea name='note' rows='3' "
        "placeholder='Draft a provider-neutral note or follow-up action'></textarea></label>"
        f"<input type='hidden' name='target_id' data-gf-inspect-target-id='true' value='{escape(node_id)}'>"
        f"<input type='hidden' name='source' data-gf-inspect-source='true' value='{escape(source)}'>"
        "<div class='gf-inspect-actions'>"
        "<button type='button' data-gf-overlay-action='center'>Center</button>"
        "<button type='button' data-gf-overlay-action='local'>Local</button>"
        "<button type='button' data-gf-overlay-action='evidence'>Evidence</button>"
        "<button type='button' data-gf-overlay-action='draft_note'>Draft note</button>"
        "</div></form></aside>"
    )


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


def _graph_canvas_legend(
    graph: GraphFakosGraph,
    request: GraphFakosRequest | None = None,
) -> str:
    payload = _graph_canvas_legend_payload(graph, request)
    return (
        "<aside class='gf-canvas-legend' data-gf-canvas-legend-panel='true' "
        "aria-label='Canvas visual legend'>"
        "<div class='gf-canvas-legend-heading'>"
        "<strong>Visual Legend</strong>"
        "<span>Shapes, styles, and evidence markers</span>"
        "</div>"
        + _graph_canvas_legend_section(
            "Node kinds",
            payload["node_kinds"],
            "kind",
        )
        + _graph_canvas_legend_section(
            "Edge kinds",
            payload["edge_kinds"],
            "edge",
        )
        + _graph_canvas_marker_rows(payload["markers"])
        + _badges(
            (
                (f"color:{payload['style_rules']['color_by']}", "accent"),
                (f"size:{payload['style_rules']['size_by']}", "blue"),
                (f"edge:{payload['style_rules']['edge_width_by']}", "neutral"),
            )
        )
        + _json_script("data-gf-canvas-legend", payload)
        + "</aside>"
    )


def _graph_canvas_legend_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest | None,
) -> dict[str, object]:
    degree_map = _node_degree_map(graph)
    pinned_count = sum(1 for node in graph.nodes if node.visual.pinned)
    hub_count = sum(1 for node in graph.nodes if degree_map.get(node.id, 0) >= 3)
    selected_count = len(request.selected_node_ids) if request is not None else 0
    selected_edge_id = request.selected_edge_id if request is not None else ""
    node_kind_counts = _node_value_counts(node.kind for node in graph.nodes)
    edge_kind_counts = _node_value_counts(edge.kind for edge in graph.edges)
    evidence_node_count = sum(
        1 for node in graph.nodes if node.provenance_ids or node.citation_ids
    )
    evidence_edge_count = sum(
        1 for edge in graph.edges if edge.provenance_ids or edge.citation_ids
    )
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "node_kinds": [
            _legend_item(kind, count, _legend_route(request, "node_kind", kind))
            for kind, count in _sorted_counts(node_kind_counts)
        ],
        "edge_kinds": [
            _legend_item(kind, count, _legend_route(request, "edge_kind", kind))
            for kind, count in _sorted_counts(edge_kind_counts)
        ],
        "markers": [
            {
                "id": "selected",
                "label": "Selected",
                "count": selected_count + (1 if selected_edge_id else 0),
                "meaning": "Blue stroke and glow identify selected nodes or edges.",
            },
            {
                "id": "pinned",
                "label": "Pinned",
                "count": pinned_count,
                "meaning": "Dashed node outlines indicate pinned or saved positions.",
            },
            {
                "id": "hub",
                "label": "Hub",
                "count": hub_count,
                "meaning": "High-degree graph items are useful navigation anchors.",
            },
            {
                "id": "evidence",
                "label": "Evidence",
                "count": evidence_node_count + evidence_edge_count,
                "meaning": "Evidence counts reflect provenance or citation links only.",
            },
        ],
        "style_rules": {
            "color_by": request.style_color_by if request is not None else "kind",
            "size_by": request.style_size_by if request is not None else "score",
            "edge_width_by": request.style_edge_width_by
            if request is not None
            else "kind",
        },
        "provider_boundary": (
            "GraphFakos explains visible structural styling; providers own "
            "semantic meaning and any provider-specific style metadata."
        ),
    }


def _legend_item(value: str, count: int, route: str) -> dict[str, object]:
    return {
        "value": value,
        "count": count,
        "route": route,
    }


def _legend_route(
    request: GraphFakosRequest | None,
    field: str,
    value: str,
) -> str:
    if request is None:
        return "#"
    return _route_href(request.with_screen("explore"), overrides={field: value})


def _graph_canvas_legend_section(
    label: str,
    items: object,
    prefix: str,
) -> str:
    if not isinstance(items, list) or not items:
        return ""
    rows = ""
    for item in items[:6]:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value") or "")
        count = str(item.get("count") or 0)
        route = str(item.get("route") or "#")
        rows += (
            f"<a class='gf-legend-pill' data-legend-{escape(prefix)}='{escape(value)}' "
            f"href='{escape(route)}'>"
            f"<span>{escape(value)}</span><strong>{escape(count)}</strong></a>"
        )
    return (
        "<section class='gf-canvas-legend-group'>"
        f"<h4>{escape(label)}</h4>"
        f"<div>{rows}</div>"
        "</section>"
    )


def _graph_canvas_marker_rows(markers: object) -> str:
    if not isinstance(markers, list) or not markers:
        return ""
    rows = ""
    for marker in markers:
        if not isinstance(marker, dict):
            continue
        rows += (
            "<div class='gf-legend-marker'>"
            f"<span data-marker='{escape(str(marker.get('id') or 'marker'))}'></span>"
            "<div>"
            f"<strong>{escape(str(marker.get('label') or 'Marker'))} "
            f"({escape(str(marker.get('count', 0)))})</strong>"
            f"<p>{escape(str(marker.get('meaning') or ''))}</p>"
            "</div></div>"
        )
    return f"<section class='gf-canvas-legend-markers'>{rows}</section>"


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


def _layout_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if request.layout == "timeline":
        positions = _timeline_positions(graph, width, height)
    elif request.layout == "circle":
        positions = _ring_positions(graph, width, height)
    elif request.layout == "grouped":
        positions = _grouped_positions(graph, width, height)
    elif request.layout == "focus":
        positions = _focus_positions(graph, width, height, focus_node_id)
    elif request.layout == "radial":
        positions = _radial_positions(graph, width, height, focus_node_id)
    elif request.layout == "hierarchical":
        positions = _hierarchical_positions(graph, width, height, focus_node_id)
    else:
        positions = _force_positions(graph, request, width, height, focus_node_id)
    return _apply_pinned_positions(graph, request, positions, width, height)


def _force_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
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
    distance_scale = _clamped(request.link_distance, 0.45, 2.2)
    inner_radius = min(width, height) * 0.2 * distance_scale
    outer_radius = min(width, height) * 0.36 * distance_scale
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
    return _relax_force_positions(graph, request, positions, anchor, width, height)


def _force_anchor_id(graph: GraphFakosGraph, focus_node_id: str | None) -> str:
    node_ids = {node.id for node in graph.nodes}
    if focus_node_id and focus_node_id in node_ids:
        return focus_node_id
    focus = _preferred_focus_node(graph, GraphFakosRequest())
    return (focus or graph.nodes[0]).id


def _relax_force_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
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
    ideal_distance = (
        sqrt(area / len(node_ids)) * 0.82 * _clamped(request.link_distance, 0.45, 2.2)
    )
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
                force = (
                    (ideal_distance * ideal_distance)
                    / distance
                    * _clamped(request.repel_force, 0.1, 4.0)
                )
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
            center_pull = (
                request.center_force if step > 36 else request.center_force / 2
            )
            next_x += (width / 2 - next_x) * center_pull
            next_y += (height / 2 - next_y) * center_pull
            positions[node_id] = _bounded_point(next_x, next_y, width, height, margin)
    return _bounded_positions(graph, positions, anchor, width, height)


def _apply_pinned_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    positions: dict[str, tuple[float, float]],
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    if not request.pinned_positions:
        return positions
    pinned = dict(positions)
    for node in graph.nodes:
        if node.id not in request.pinned_positions:
            continue
        x, y = request.pinned_positions[node.id]
        pinned[node.id] = _bounded_point(x, y, width, height, 46.0)
    return pinned


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
        groups[_node_cluster_id(node) or node.kind or "node"].append(node)
    positions: dict[str, tuple[float, float]] = {}
    group_names = sorted(groups)
    if not group_names:
        return positions
    center_x = width / 2
    center_y = height / 2
    orbit_x = width * 0.36
    orbit_y = height * 0.32
    for group_index, group_name in enumerate(group_names):
        angle = (2 * pi * group_index / max(len(group_names), 1)) - (pi / 2)
        cluster_nodes = groups[group_name]
        cluster_center_x = center_x + orbit_x * cos(angle)
        cluster_center_y = center_y + orbit_y * sin(angle)
        local_radius = max(22.0, min(120.0, 18.0 + len(cluster_nodes) * 1.8))
        for node_index, node in enumerate(cluster_nodes):
            if node_index == 0:
                positions[node.id] = _bounded_point(
                    cluster_center_x,
                    cluster_center_y,
                    width,
                    height,
                    34.0,
                )
                continue
            local_angle = node_index * 2.399963229728653
            local_distance = min(local_radius, 14 + sqrt(node_index) * 12)
            positions[node.id] = _bounded_point(
                cluster_center_x + local_distance * cos(local_angle),
                cluster_center_y + local_distance * sin(local_angle),
                width,
                height,
                34.0,
            )
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
body.gf-page[data-theme="space"] {
  --gf-bg: #060b1c;
  --gf-ink: #eef5ff;
  --gf-muted: #aebbe0;
  --gf-line: #263458;
  --gf-panel: #0b1229;
  --gf-soft: #101a36;
  --gf-accent: #64d9f3;
  --gf-accent-soft: #0b3444;
  --gf-blue: #a998ff;
  --gf-blue-soft: #201a50;
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
  padding: 16px 18px 22px;
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
  border-radius: 14px;
  padding: 12px;
  margin-bottom: 12px;
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
.gf-panel-form {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}
.gf-panel-form input,
.gf-panel-form select {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  color: var(--gf-ink);
  font: inherit;
  min-width: 0;
  padding: 9px 10px;
}
.gf-panel-form button {
  border: 1px solid var(--gf-accent);
  border-radius: 8px;
  background: var(--gf-accent);
  color: white;
  font: inherit;
  font-weight: 700;
  padding: 9px 10px;
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
  grid-template-columns: minmax(220px, 1fr) auto auto;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.gf-command-bar input {
  min-width: 0;
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  padding: 8px 10px;
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
.gf-command-shortcut {
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 800;
  padding: 6px 9px;
  white-space: nowrap;
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
.gf-theme-toggle {
  border-color: color-mix(in srgb, var(--gf-blue) 45%, var(--gf-line));
  background: color-mix(in srgb, var(--gf-blue-soft) 76%, transparent);
}
.gf-lens-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0 0 12px;
}
.gf-active-lens {
  align-items: flex-start;
  background: linear-gradient(135deg, rgba(36, 108, 92, 0.09), rgba(52, 92, 140, 0.08));
  border: 1px solid var(--gf-line);
  border-radius: 18px;
  box-shadow: 0 12px 28px rgba(20, 35, 30, 0.08);
  display: flex;
  gap: 14px;
  justify-content: space-between;
  margin: 12px 0;
  padding: 14px;
}
.gf-active-lens-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}
.gf-route-chip {
  background: var(--gf-soft);
  color: var(--gf-ink);
}
.gf-interaction-guide {
  background:
    radial-gradient(circle at 12% 18%, color-mix(in srgb, var(--gf-blue-soft) 74%, transparent), transparent 34%),
    linear-gradient(135deg, white, color-mix(in srgb, var(--gf-soft) 82%, white));
  border: 1px solid color-mix(in srgb, var(--gf-blue) 22%, var(--gf-line));
  border-radius: 22px;
  box-shadow: var(--gf-shadow);
  display: grid;
  gap: 14px;
  margin: 12px 0 16px;
  padding: 18px;
}
.gf-guide-copy h3,
.gf-guide-copy p {
  margin: 0;
}
.gf-guide-copy h3 {
  font-size: 20px;
  letter-spacing: -.02em;
}
.gf-guide-copy p {
  color: var(--gf-muted);
  line-height: 1.55;
  margin-top: 6px;
}
.gf-guide-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}
.gf-guide-card {
  background: rgba(255, 255, 255, .78);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  color: var(--gf-ink);
  display: grid;
  gap: 5px;
  padding: 10px;
  text-decoration: none;
}
.gf-guide-card span {
  color: var(--gf-blue);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.gf-guide-card p {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.45;
  margin: 0;
}
.gf-route-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}
.gf-command-palette {
  display: grid;
  gap: 12px;
}
.gf-command-search {
  color: var(--gf-muted);
  display: grid;
  gap: 6px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.gf-command-search input {
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  color: var(--gf-ink);
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0;
  padding: 10px 11px;
  text-transform: none;
}
.gf-command-group {
  display: grid;
  gap: 8px;
}
.gf-command-group h4 {
  font-size: 13px;
  letter-spacing: .04em;
  margin: 0;
  text-transform: uppercase;
}
.gf-command-row {
  align-items: center;
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  padding: 9px 10px;
}
.gf-command-row[data-disabled="true"] {
  opacity: .56;
}
.gf-trail-row {
  align-items: center;
}
.gf-trail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}
.gf-inline-note {
  color: var(--gf-muted);
  display: block;
  font-size: 12px;
  margin-top: 2px;
}
.gf-facet-explorer {
  display: grid;
  gap: 10px;
}
.gf-facet-group {
  background: color-mix(in srgb, var(--gf-soft) 70%, white);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px;
}
.gf-facet-group h4 {
  flex: 1 0 100%;
  margin: 0 0 2px;
}
.gf-facet-pill {
  align-items: center;
  background: white;
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  color: var(--gf-ink);
  display: inline-flex;
  gap: 7px;
  padding: 5px 8px;
  text-decoration: none;
}
.gf-facet-pill[aria-current="true"] {
  background: var(--gf-accent-soft);
  border-color: color-mix(in srgb, var(--gf-accent) 35%, var(--gf-line));
}
.gf-facet-pill strong {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-navigation-map {
  display: grid;
  gap: 8px;
}
.gf-navigation-lane {
  background: color-mix(in srgb, var(--gf-blue-soft) 46%, white);
  border-left: 4px solid color-mix(in srgb, var(--gf-blue) 45%, var(--gf-line));
  display: grid;
  gap: 7px;
}
.gf-navigation-lane h4,
.gf-navigation-lane p {
  margin: 0;
}
.gf-navigation-lane p {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.45;
}
.gf-display-recipes {
  display: grid;
  gap: 8px;
}
.gf-recipe-card {
  background: color-mix(in srgb, var(--gf-soft) 76%, white);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  color: var(--gf-ink);
  display: grid;
  gap: 4px;
  padding: 10px;
  text-decoration: none;
}
.gf-recipe-card[data-active="true"] {
  background: var(--gf-accent-soft);
  border-color: color-mix(in srgb, var(--gf-accent) 35%, var(--gf-line));
}
.gf-recipe-card span {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.4;
}
.gf-selection-sets {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}
.gf-selection-set-card {
  background: color-mix(in srgb, var(--gf-blue-soft) 54%, white);
  border: 1px solid color-mix(in srgb, var(--gf-blue) 18%, var(--gf-line));
  border-radius: 14px;
  display: grid;
  gap: 7px;
  padding: 10px;
}
.gf-selection-set-card h4,
.gf-selection-set-card p {
  margin: 0;
}
.gf-relationship-table {
  display: grid;
  gap: 8px;
}
.gf-relationship-row {
  border-left: 4px solid color-mix(in srgb, var(--gf-blue) 42%, var(--gf-line));
}
.gf-relationship-row h4 {
  font-size: 14px;
  line-height: 1.35;
}
.gf-evidence-coverage {
  display: grid;
  gap: 8px;
}
.gf-evidence-coverage-row {
  background: color-mix(in srgb, var(--gf-soft) 76%, white);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  display: grid;
  gap: 8px;
  padding: 10px;
}
.gf-evidence-coverage-row h4,
.gf-evidence-coverage-row p {
  margin: 0;
}
.gf-evidence-coverage-row p {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.4;
}
.gf-evidence-meter {
  background: white;
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  height: 9px;
  overflow: hidden;
}
.gf-evidence-meter span {
  background: linear-gradient(90deg, var(--gf-accent), var(--gf-blue));
  display: block;
  height: 100%;
}
.gf-capture-panel {
  border-color: #c8d8d0;
}
.gf-action-panel,
.gf-workspace-controls,
.gf-local-controls,
.gf-physics-controls {
  border-color: color-mix(in srgb, var(--gf-accent) 24%, var(--gf-line));
}
.gf-workbook {
  background: color-mix(in srgb, var(--gf-soft) 76%, white);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  display: grid;
  gap: 8px;
  padding: 10px;
}
.gf-workbook-row,
.gf-workbook-slot {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.gf-workbook input {
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  color: var(--gf-ink);
  flex: 1 1 160px;
  font: inherit;
  min-height: 34px;
  padding: 7px 9px;
}
.gf-workbook button,
.gf-workbook a {
  border: 1px solid color-mix(in srgb, var(--gf-accent) 30%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-ink);
  font-size: 12px;
  font-weight: 800;
  padding: 6px 10px;
  text-decoration: none;
}
.gf-workbook button {
  background: white;
  cursor: pointer;
  font-family: inherit;
}
.gf-workbook-list {
  display: grid;
  gap: 6px;
}
.gf-workbook-slot {
  justify-content: space-between;
}
.gf-workbook-slot span {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-capture-form {
  display: grid;
  gap: 10px;
}
.gf-capture-templates {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}
.gf-capture-templates span {
  color: var(--gf-muted);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
  margin-right: 2px;
  text-transform: uppercase;
}
.gf-capture-form .gf-capture-templates button {
  background: color-mix(in srgb, var(--gf-accent) 9%, white);
  border: 1px solid color-mix(in srgb, var(--gf-accent) 28%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-ink);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  min-height: 30px;
  padding: 6px 10px;
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
.gf-viewer-context-preview {
  background: color-mix(in srgb, var(--gf-soft) 72%, white);
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  display: grid;
  gap: 8px;
  padding: 10px 12px;
}
.gf-viewer-context-preview b {
  color: var(--gf-ink);
  font-size: 13px;
}
.gf-viewer-context-preview ul {
  display: grid;
  gap: 6px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.gf-viewer-context-preview li {
  align-items: baseline;
  display: flex;
  gap: 10px;
  justify-content: space-between;
}
.gf-viewer-context-preview span {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-viewer-context-preview strong {
  color: var(--gf-ink);
  font-size: 12px;
  font-weight: 700;
  text-align: right;
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
.gf-context-menu {
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  margin-bottom: 10px;
  padding: 8px 10px;
}
.gf-context-menu summary {
  cursor: pointer;
  font-weight: 800;
}
.gf-case-packet {
  background: color-mix(in srgb, var(--gf-soft) 72%, white);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  display: grid;
  gap: 8px;
  margin: 12px 0;
  padding: 10px;
}
.gf-case-packet h4,
.gf-case-packet h5 {
  margin: 0;
}
.gf-surface-menu {
  background: color-mix(in srgb, var(--gf-panel) 94%, white);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  box-shadow: 0 18px 42px rgb(20 29 44 / 20%);
  display: grid;
  gap: 6px;
  min-width: 170px;
  padding: 10px;
  position: fixed;
  z-index: 20;
}
.gf-surface-menu strong {
  color: var(--gf-ink);
  font-size: 12px;
  overflow: hidden;
  padding: 2px 4px 5px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gf-surface-menu a,
.gf-surface-menu button {
  background: transparent;
  border: 0;
  border-radius: 8px;
  color: var(--gf-ink);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 7px 8px;
  text-align: left;
  text-decoration: none;
}
.gf-surface-menu a:hover,
.gf-surface-menu button:hover,
.gf-surface-menu a:focus-visible,
.gf-surface-menu button:focus-visible {
  background: var(--gf-accent-soft);
  outline: none;
}
.gf-canvas-grid {
  display: block;
  position: relative;
}
.gf-canvas-shell {
  min-width: 0;
  outline: none;
  position: relative;
}
.gf-canvas-shell:focus-visible {
  box-shadow: 0 0 0 3px var(--gf-accent-soft);
}
.gf-shortcut-hint {
  color: var(--gf-muted);
  font-size: 12px;
  margin: -4px 0 10px;
}
.gf-live-selection {
  align-items: center;
  background: color-mix(in srgb, var(--gf-blue-soft) 58%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-blue) 24%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-ink);
  display: inline-flex;
  font-size: 12px;
  font-weight: 800;
  margin: 0 0 10px;
  max-width: 100%;
  padding: 6px 10px;
}
.gf-live-selection[data-selected-count="0"][data-edge-selected="false"] {
  background: var(--gf-soft);
  color: var(--gf-muted);
  font-weight: 700;
}
.gf-canvas {
  width: 100%;
  height: min(74vh, 820px);
  min-height: 560px;
  border: 1px solid var(--gf-line);
  border-radius: 18px;
  background:
    radial-gradient(circle at 20px 20px, color-mix(in srgb, var(--gf-line) 34%, transparent) 1px, transparent 1px),
    var(--gf-panel);
  background-size: 28px 28px;
  cursor: grab;
  touch-action: none;
}
body.gf-page[data-theme="space"] .gf-canvas {
  background:
    radial-gradient(circle at 16% 24%, rgba(100, 217, 243, .12), transparent 25%),
    radial-gradient(circle at 78% 18%, rgba(169, 152, 255, .12), transparent 24%),
    radial-gradient(circle at 50% 80%, rgba(72, 255, 190, .08), transparent 24%),
    radial-gradient(circle at 18px 18px, rgba(238, 245, 255, .16) 1px, transparent 1px),
    linear-gradient(135deg, #030816, #070a1c 48%, #0e1234);
  background-size: auto, auto, auto, 64px 64px, auto;
  box-shadow: inset 0 0 130px rgba(100, 217, 243, .08), 0 20px 80px rgba(0, 0, 0, .22);
}
body.gf-page[data-theme="space"] .gf-edge {
  stroke: rgba(198, 224, 255, .44);
}
body.gf-page[data-theme="space"] .gf-node circle,
body.gf-page[data-theme="space"] .gf-node rect,
body.gf-page[data-theme="space"] .gf-node polygon {
  filter: drop-shadow(0 0 8px rgba(100, 217, 243, .24));
}
body.gf-page[data-theme="space"] .gf-node[data-kind="provider"] circle,
body.gf-page[data-theme="space"] .gf-node[data-kind="provider"] rect,
body.gf-page[data-theme="space"] .gf-node[data-kind="provider"] polygon {
  fill: #7dd3fc;
  stroke: #d8f4ff;
}
body.gf-page[data-theme="space"] .gf-node[data-kind="memory"] circle,
body.gf-page[data-theme="space"] .gf-node[data-kind="memory"] rect,
body.gf-page[data-theme="space"] .gf-node[data-kind="memory"] polygon {
  fill: #9ee66f;
  stroke: #e5ffd1;
}
body.gf-page[data-theme="space"] .gf-node[data-kind="artifact"] circle,
body.gf-page[data-theme="space"] .gf-node[data-kind="artifact"] rect,
body.gf-page[data-theme="space"] .gf-node[data-kind="artifact"] polygon {
  fill: #ffb86b;
  stroke: #ffe2b8;
}
body.gf-page[data-theme="space"] .gf-node[data-kind="document"] circle,
body.gf-page[data-theme="space"] .gf-node[data-kind="document"] rect,
body.gf-page[data-theme="space"] .gf-node[data-kind="document"] polygon {
  fill: #d9e7ff;
  stroke: #ffffff;
}
.gf-canvas-renderer {
  background: color-mix(in srgb, var(--gf-panel) 92%, var(--gf-blue));
  border: 1px solid var(--gf-line);
  border-radius: 8px;
  display: block;
  height: auto;
  margin-bottom: 10px;
  width: 100%;
}
.gf-canvas:active { cursor: grabbing; }
.gf-inspect-overlay {
  backdrop-filter: blur(14px);
  background: color-mix(in srgb, var(--gf-panel) 94%, transparent);
  border: 1px solid color-mix(in srgb, var(--gf-blue) 24%, var(--gf-line));
  border-radius: 18px;
  box-shadow: 0 18px 46px rgb(20 29 44 / 18%);
  display: none;
  gap: 10px;
  max-width: min(380px, calc(100% - 32px));
  padding: 14px;
  position: absolute;
  right: 18px;
  bottom: 110px;
  z-index: 8;
}
.gf-inspect-overlay[data-open="true"] {
  display: grid;
}
.gf-inspect-overlay-bar,
.gf-inspect-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: space-between;
}
.gf-inspect-overlay-bar span {
  color: var(--gf-blue);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .1em;
  text-transform: uppercase;
}
.gf-inspect-overlay h3 {
  margin: 0;
}
.gf-inspect-overlay p {
  color: var(--gf-muted);
  margin: 0;
}
.gf-inspect-section {
  background: color-mix(in srgb, var(--gf-soft) 62%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 12px;
  padding: 8px 10px;
}
.gf-inspect-section summary {
  cursor: pointer;
  font-weight: 900;
}
.gf-inspect-command {
  display: grid;
  gap: 8px;
}
.gf-inspect-command label {
  color: var(--gf-muted);
  display: grid;
  font-size: 12px;
  gap: 5px;
}
.gf-inspect-command textarea {
  background: color-mix(in srgb, var(--gf-panel) 86%, transparent);
  border: 1px solid var(--gf-line);
  border-radius: 10px;
  color: var(--gf-ink);
  font: inherit;
  min-height: 76px;
  padding: 8px;
  resize: vertical;
}
.gf-inspect-overlay button {
  background: var(--gf-blue-soft);
  border: 1px solid color-mix(in srgb, var(--gf-blue) 28%, var(--gf-line));
  border-radius: 999px;
  color: var(--gf-blue);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  padding: 6px 10px;
}
body.gf-page[data-theme="space"] .gf-inspect-overlay {
  background: rgba(8, 13, 35, .88);
  border-color: rgba(125, 211, 252, .32);
  box-shadow: 0 24px 70px rgba(0, 0, 0, .38), inset 0 0 0 1px rgba(255, 255, 255, .04);
}
body.gf-page[data-theme="space"] .gf-inspect-section,
body.gf-page[data-theme="space"] .gf-inspect-command textarea {
  background: rgba(17, 24, 48, .68);
  border-color: rgba(161, 182, 255, .22);
}
.gf-canvas defs path {
  fill: #768078;
}
.gf-edge {
  fill: none;
  stroke: #9ea9a2;
  stroke-width: 1.5;
  transition: stroke .16s ease, stroke-width .16s ease, opacity .16s ease;
}
.gf-edge[data-selected="true"] {
  stroke: var(--gf-blue);
  stroke-width: 4;
}
.gf-edge[data-stretched="true"] {
  opacity: .9;
  stroke: var(--gf-blue);
  stroke-width: 3;
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
.gf-graph-item-link:focus-visible {
  outline: none;
}
.gf-graph-item-link:focus-visible .gf-edge {
  stroke: var(--gf-blue);
  stroke-width: 4;
}
.gf-graph-item-link:focus-visible .gf-node circle,
.gf-graph-item-link:focus-visible .gf-node rect,
.gf-graph-item-link:focus-visible .gf-node polygon {
  filter: drop-shadow(0 0 0.45rem var(--gf-blue-soft));
  stroke: var(--gf-blue);
  stroke-width: 4;
}
.gf-selection-box {
  fill: color-mix(in srgb, var(--gf-blue-soft) 62%, transparent);
  pointer-events: none;
  stroke: var(--gf-blue);
  stroke-dasharray: 6 4;
  stroke-width: 2;
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
.gf-node[data-neighbor="true"] circle,
.gf-node[data-neighbor="true"] rect,
.gf-node[data-neighbor="true"] polygon,
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
.gf-node[data-pinned="true"] circle,
.gf-node[data-pinned="true"] rect,
.gf-node[data-pinned="true"] polygon {
  stroke-dasharray: 5 3;
}
.gf-node[data-hidden="true"],
.gf-edge[data-hidden="true"] {
  opacity: .16;
}
.gf-node text {
  fill: var(--gf-ink);
  font-size: 10px;
  font-weight: 700;
  paint-order: stroke;
  stroke: #fbfcfa;
  stroke-width: 5px;
  stroke-linejoin: round;
  pointer-events: none;
}
body.gf-page[data-theme="space"] .gf-node text {
  fill: #f4f8ff;
  stroke: #050817;
  stroke-width: 4px;
}
.gf-canvas-legend {
  background: color-mix(in srgb, var(--gf-soft) 74%, white);
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  display: grid;
  gap: 10px;
  margin-top: 10px;
  padding: 12px;
}
.gf-canvas-legend-heading {
  display: grid;
  gap: 2px;
}
.gf-canvas-legend-heading span {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-canvas-legend-group {
  display: grid;
  gap: 6px;
}
.gf-canvas-legend-group h4 {
  font-size: 12px;
  letter-spacing: .04em;
  margin: 0;
  text-transform: uppercase;
}
.gf-canvas-legend-group div {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.gf-legend-pill {
  align-items: center;
  background: white;
  border: 1px solid var(--gf-line);
  border-radius: 999px;
  color: var(--gf-ink);
  display: inline-flex;
  gap: 6px;
  padding: 4px 7px;
  text-decoration: none;
}
.gf-legend-pill strong {
  color: var(--gf-muted);
  font-size: 12px;
}
.gf-canvas-legend-markers {
  display: grid;
  gap: 7px;
}
.gf-legend-marker {
  display: grid;
  gap: 8px;
  grid-template-columns: 18px minmax(0, 1fr);
}
.gf-legend-marker > span {
  align-self: start;
  border: 2px solid var(--gf-accent);
  border-radius: 999px;
  height: 14px;
  margin-top: 2px;
  width: 14px;
}
.gf-legend-marker > span[data-marker="selected"] {
  background: var(--gf-blue-soft);
  border-color: var(--gf-blue);
}
.gf-legend-marker > span[data-marker="pinned"] {
  border-style: dashed;
}
.gf-legend-marker > span[data-marker="hub"] {
  background: var(--gf-accent-soft);
}
.gf-legend-marker > span[data-marker="evidence"] {
  background: #fff3d6;
  border-color: #9b6b17;
}
.gf-legend-marker strong {
  font-size: 12px;
}
.gf-legend-marker p {
  color: var(--gf-muted);
  font-size: 12px;
  line-height: 1.35;
  margin: 0;
}
.gf-minimap {
  border: 1px solid var(--gf-line);
  border-radius: 14px;
  background: color-mix(in srgb, var(--gf-panel) 80%, transparent);
  box-shadow: 0 16px 42px rgba(0, 0, 0, .18);
  padding: 8px;
  position: absolute;
  right: 14px;
  top: 14px;
  width: 148px;
  z-index: 3;
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
.gf-minimap-viewport {
  fill: color-mix(in srgb, var(--gf-blue-soft) 28%, transparent);
  pointer-events: none;
  stroke: var(--gf-blue);
  stroke-dasharray: 5 3;
  stroke-width: 1.5;
}
.gf-minimap-node-link {
  cursor: pointer;
}
.gf-minimap-node-link:focus-visible {
  outline: none;
}
.gf-minimap-node-link:focus-visible circle,
.gf-minimap-node-link:hover circle {
  fill: var(--gf-blue-soft);
  stroke: var(--gf-blue);
  stroke-width: 2;
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
.gf-group-controls [data-gf-group-show-all] {
  border-color: color-mix(in srgb, var(--gf-accent) 38%, var(--gf-line));
  color: var(--gf-accent);
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
.gf-component-grid {
  display: grid;
  gap: 10px;
}
.gf-component-card {
  border-color: color-mix(in srgb, var(--gf-blue) 24%, var(--gf-line));
}
.gf-timeline-rail {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 10px 0;
}
.gf-timeline-grid {
  display: grid;
  gap: 10px;
}
.gf-timeline-card {
  border-color: color-mix(in srgb, var(--gf-accent) 24%, var(--gf-line));
}
.gf-diff-workbench {
  border-top: 1px solid var(--gf-line);
  margin-top: 12px;
  padding-top: 12px;
}
.gf-diff-grid {
  display: grid;
  gap: 10px;
}
.gf-diff-card {
  border-color: color-mix(in srgb, var(--gf-accent) 30%, var(--gf-line));
}
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
