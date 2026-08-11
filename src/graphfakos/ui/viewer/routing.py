"""Viewer route construction and request query parsing."""

from __future__ import annotations

from dataclasses import replace
from html import escape
import json
from typing import cast
from urllib.parse import urlencode

from graphfakos.camera import GraphFakosCameraPose
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

_TEXT_QUERY_KEYS = tuple(
    "query selected_edge_id source_node_id target_node_id comparison_graph_id "
    "layout render_engine theme saved_view_id scene_level edge_clutter "
    "analytics_overlay style_color_by style_size_by style_edge_width_by "
    "component_id connected_to_node_id evidence_filter cluster_id timeline_frame "
    "timeline_playback pivot_node_id pivot_mode".split()
)
_FLOAT_QUERY_KEYS = tuple(
    "camera_x camera_y camera_zoom camera_yaw camera_pitch center_force repel_force "
    "link_distance node_scale edge_scale edge_opacity label_density".split()
)
_INT_QUERY_KEYS = ("min_degree", "max_degree")
_TUPLE_QUERY_KEYS = ("selected_node_ids", "expanded_groups", "hidden_groups")


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
    values: dict[str, object] = {
        "preset_id": _first_query_match(
            query, ("preset", "preset_id"), request.preset_id
        ),
        "focus_node_id": _first_query_match(
            query, ("focus_node_id", "node_id"), request.focus_node_id
        ),
        "filters": filters,
        "max_depth": _required_int_query_value(query, "max_depth", request.max_depth),
        "limit": _required_int_query_value(query, "limit", request.limit),
        "render_limit": _required_int_query_value(
            query, "render_limit", request.render_limit
        ),
        "camera_pose": _camera_pose_query_value(query, request.camera_pose),
        "show_orphans": _bool_query_value(query, "show_orphans", request.show_orphans),
        "show_neighbor_links": _bool_query_value(
            query, "show_neighbor_links", request.show_neighbor_links
        ),
        "pinned_positions": _positions_query_value(
            query, "pinned_positions", request.pinned_positions
        ),
    }
    values.update(
        {
            key: _first_query_value(query, key) or getattr(request, key)
            for key in _TEXT_QUERY_KEYS
        }
    )
    values.update(
        {
            key: _tuple_query_value(query, key, getattr(request, key))
            for key in _TUPLE_QUERY_KEYS
        }
    )
    values.update(
        {
            key: _float_query_value(query, key, getattr(request, key))
            for key in _FLOAT_QUERY_KEYS
        }
    )
    values.update(
        {
            key: _int_query_value(query, key, getattr(request, key))
            for key in _INT_QUERY_KEYS
        }
    )
    return replace(request, **values)


def _first_query_match(
    query: dict[str, list[str]],
    keys: tuple[str, ...],
    fallback: str | None,
) -> str | None:
    for key in keys:
        value = _first_query_value(query, key)
        if value is not None:
            return value
    return fallback


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


def _camera_pose_query_value(
    query: dict[str, list[str]],
    fallback: GraphFakosCameraPose | None,
) -> GraphFakosCameraPose | None:
    value = _first_query_value(query, "camera_pose")
    if value is None:
        return fallback
    try:
        return GraphFakosCameraPose.from_query_value(value)
    except (TypeError, ValueError):
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


def _required_int_query_value(
    query: dict[str, list[str]],
    key: str,
    fallback: int,
) -> int:
    value = _int_query_value(query, key, fallback)
    return fallback if value is None else value


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


def _local_node_route(request: GraphFakosRequest, node_id: str) -> str:
    """Open one node's neighborhood with a camera fitted to the new scope."""
    return _route_href(
        request.with_screen("neighborhood"),
        overrides={
            "camera_scope": "fresh",
            "camera_x": None,
            "camera_y": None,
            "camera_zoom": None,
            "camera_yaw": None,
            "camera_pitch": None,
            "camera_pose": None,
            "focus_node_id": node_id,
            "max_depth": 1,
            "layout": "focus",
        },
    )


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
            if route_key == "camera_pose":
                payload[route_key] = GraphFakosCameraPose.from_dict(
                    value
                ).to_query_value()
                continue
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
