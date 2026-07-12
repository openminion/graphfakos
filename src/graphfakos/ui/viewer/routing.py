"""Viewer route construction and request query parsing."""

from __future__ import annotations

from html import escape
import json
from typing import cast
from urllib.parse import urlencode

from graphfakos.models import GraphFakosRequest, GraphFakosScreen

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
        return cast(GraphFakosScreen, value)
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


def state_hidden_inputs(
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
