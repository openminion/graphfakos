"""Graph presets, navigation maps, lenses, and relationship trails."""

from __future__ import annotations

from html import escape

from graphfakos.models import (
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    GraphFakosScreen,
)
from graphfakos.provider import diagnose_graph
from graphfakos.ui.viewer.canvas import _explore_href
from graphfakos.ui.viewer.graph_ops import (
    _adjacency_map,
    _navigation_path_pair,
    _node_degree_map,
    _preferred_focus_node,
    _ranked_nodes,
    _shortest_path_edges,
)
from graphfakos.ui.viewer.html import (
    badges as _badges,
    empty as _empty,
    html_list as _html_list,
    json_script as _json_script,
    key_values as _key_values,
    panel as _panel,
    panel_body as _panel_body,
    summary_note as _summary_note,
    text_list as _list,
)
from graphfakos.ui.viewer.routing import _route_href, query_syntax_reference


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
