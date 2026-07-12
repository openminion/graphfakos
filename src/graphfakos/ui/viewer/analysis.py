"""Graph readability, analytics, selection, styling, and investigation panels."""

from __future__ import annotations

from collections import defaultdict
from html import escape

from graphfakos.models import (
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    GraphFakosSavedView,
)
from graphfakos.provider import analyze_graph
from graphfakos.ui.viewer.canvas import _explore_href
from graphfakos.ui.viewer.filtering import _facet_values, _graph_facets
from graphfakos.ui.viewer.graph_ops import (
    _adjacency_map,
    _component_groups,
    _node_component_ids,
    _node_degree_map,
    _preferred_focus_node,
    _ranked_nodes,
    _shortest_path_edges,
    _timeline_frames,
)
from graphfakos.ui.viewer.html import (
    badges as _badges,
    empty as _empty,
    html_list as _html_list,
    json_script as _json_script,
    key_values as _key_values,
    panel as _panel,
    panel_body as _panel_body,
    select as _select,
    select_pairs as _select_pairs,
    summary_note as _summary_note,
    text_list as _list,
)
from graphfakos.ui.viewer.routing import (
    _route_href,
    state_hidden_inputs as _state_hidden_inputs,
)

_STYLE_STATE_EXCLUDES = ("style_color_by", "style_size_by", "style_edge_width_by")


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
