"""Graph lens, workspace, physics, and interaction controls."""

from __future__ import annotations

from html import escape

from graphfakos.models import (
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    GraphFakosSavedView,
)
from graphfakos.provider import analyze_graph
from graphfakos.ui.viewer.filtering import _facet_values
from graphfakos.ui.viewer.html import (
    badges as _badges,
    empty as _empty,
    json_script as _json_script,
    select as _select,
)
from graphfakos.ui.viewer.routing import (
    _route_href,
    state_hidden_inputs as _state_hidden_inputs,
)

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
