"""Interactive graph canvas, minimap, inspector, and legend rendering."""

from __future__ import annotations

from collections import defaultdict
from html import escape
from math import sqrt

from graphfakos.models import (
    GraphFakosCitation,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosProvenance,
    GraphFakosRequest,
)
from graphfakos.ui.viewer.filtering import _facet_values
from graphfakos.ui.viewer.graph_ops import (
    _node_cluster_id,
    _node_component_ids,
    _node_degree_map,
    _ranked_nodes,
)
from graphfakos.ui.viewer.html import (
    badges as _badges,
    empty as _empty,
    json_attribute as _json_attribute,
    json_script as _json_script,
    key_values as _key_values,
    panel as _panel,
    panel_body as _panel_body,
    summary_note as _summary_note,
    text_list as _list,
)
from graphfakos.ui.viewer.layout import _clamped, _layout_positions
from graphfakos.ui.viewer.routing import (
    _route_href,
    state_hidden_inputs as _state_hidden_inputs,
)

_MINIMAP_WIDTH = 180
_MINIMAP_HEIGHT = 90
_MINIMAP_NODE_RADIUS = 4


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
    detail_mode = _initial_detail_mode(request, len(graph.nodes))
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
        label_priority = _node_label_priority(
            node,
            index,
            degree,
            request,
            len(graph.nodes),
        )
        label = (
            f"<text class='gf-node-label' data-label-priority='{escape(label_priority)}' "
            f"y='{_node_label_y(index):.1f}' "
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
            f"data-label-priority='{escape(label_priority)}' "
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
    total_nodes = int(
        graph.stats.get("raw_node_count", len(graph.nodes)) or len(graph.nodes)
    )
    total_edges = int(
        graph.stats.get("raw_edge_count", len(graph.edges)) or len(graph.edges)
    )
    available_nodes = len(graph.nodes) + hidden_nodes
    available_edges = len(graph.edges) + hidden_edges
    return (
        "<section class='gf-panel gf-canvas-panel'><div class='gf-panel-heading'>"
        "<h3>Graph Canvas</h3>"
        f"{_canvas_toolbar(request)}</div>"
        f"{_graph_search_panel(graph, request)}"
        "<div class='gf-scene-status'>"
        f"<span data-gf-scene-counts='true'>Total {total_nodes:,}/{total_edges:,} · "
        f"available {available_nodes:,}/{available_edges:,} · drawn {len(graph.nodes):,}/{len(graph.edges):,}</span>"
        f"<span class='gf-detail-status'><strong data-gf-detail-mode='true'>{escape(detail_mode.title())} view</strong>"
        " Labels and edges become denser as you zoom in.</span></div>"
        "<details class='gf-canvas-help'><summary>Navigation help</summary>"
        f"<p class='gf-note'>Layout {escape(request.layout)}. Rendering {len(graph.nodes)} node(s) "
        f"and {len(graph.edges)} edge(s). Fit zooms to the current selection or visible graph; "
        "drag empty canvas to pan; drag a node to pin it; Shift-drag empty canvas to box-select "
        "nodes; right-click or press Shift+F10 on nodes or edges for actions.</p>"
        "<p class='gf-shortcut-hint'>Navigation: drag empty space to pan, scroll to zoom toward the cursor, "
        "Alt/Option-drag a node to move its cluster, WASD or arrows move like a map, "
        "Q/E nudges depth in 3D mode, 0 resets camera, F fullscreen, Delete clears selection.</p>"
        f"{_renderer_notice(request)}</details>"
        f"<div class='gf-canvas-grid'><div class='gf-canvas-shell' tabindex='0' "
        f"data-camera-x='{camera_x:.2f}' data-camera-y='{camera_y:.2f}' "
        f"data-camera-zoom='{camera_zoom:.2f}' data-camera-yaw='{camera_yaw:.2f}' "
        f"data-camera-pitch='{camera_pitch:.2f}' data-render-engine='{escape(request.render_engine)}' "
        f"data-detail-mode='{escape(detail_mode)}' data-total-nodes='{total_nodes}' "
        f"data-available-nodes='{available_nodes}' data-visible-nodes='{len(graph.nodes)}' "
        f"data-label-density='{request.label_density:.2f}'>"
        f"{_canvas_renderer(graph, request)}"
        + (
            "<div class='gf-webgl-surface' data-gf-webgl-surface='true' "
            "role='application' aria-label='Interactive 3D graph scene'></div>"
            if request.render_engine == "3d"
            else ""
        )
        + f"<svg class='gf-canvas' viewBox='0 0 {width} {height}' "
        "role='img' aria-label='GraphFakos graph canvas'>"
        "<defs><marker id='gf-arrow' markerWidth='8' markerHeight='8' refX='7' "
        "refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z'></path></marker></defs>"
        f"<g class='gf-viewport' transform='translate({camera_x:.2f} {camera_y:.2f}) scale({camera_zoom:.2f})'>"
        f"{edge_lines}{node_marks}</g></svg></div>"
        "<noscript><p class='gf-note'>JavaScript is off. Use the linked SVG nodes, graph data tables, and route-backed controls to inspect this graph.</p></noscript>"
        f"{_node_inspect_overlay(graph, selected_id)}"
        f"{_graph_minimap(graph, request, positions, width, height, selected_id, (camera_x, camera_y, camera_zoom))}</div>"
        f"<p class='gf-live-selection' data-gf-live-selection='true' aria-live='polite' "
        f"data-selected-count='{len(selected_node_ids)}' "
        f"data-edge-selected='{str(bool(selected_edge_id)).lower()}'>{escape(live_selection)}</p>"
        "<p class='gf-live-selection' data-gf-live-status='true' data-state='idle' "
        "aria-live='polite'>Live updates: idle.</p>"
        "<button type='button' class='gf-compact-button' data-gf-live-resync='true' "
        "hidden>Resync live graph</button>"
        f"{_group_controls(graph, request)}"
        f"{_render_budget_panel(request, hidden_nodes, hidden_edges)}"
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
        "<button type='button' data-gf-layout-reset='true' title='Reset graph formation' aria-label='Reset graph formation'>Layout</button>"
        "<button type='button' data-gf-history='undo' title='Undo scene change' aria-label='Undo scene change' disabled>Undo</button>"
        "<button type='button' data-gf-history='redo' title='Redo scene change' aria-label='Redo scene change' disabled>Redo</button>"
        "<button type='button' data-gf-camera='fullscreen' title='Fullscreen' aria-label='Fullscreen'>Full</button>"
        "<button type='button' data-gf-pin='reset' title='Clear pinned node positions' aria-label='Clear pinned node positions'>Clear Pins</button>"
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


def _node_label_priority(
    node: GraphFakosNode,
    index: int,
    degree: int,
    request: GraphFakosRequest,
    visible_count: int,
) -> str:
    if node.id == request.focus_node_id or node.id in request.selected_node_ids:
        return "focus"
    if node.visual.pinned or node.id in request.pinned_positions:
        return "focus"
    if degree >= 6:
        return "hub"
    if visible_count <= 36:
        return "local"
    if degree >= 4:
        return "bridge"
    if index % 16 == 0:
        return "landmark"
    return "ambient"


def _initial_detail_mode(request: GraphFakosRequest, visible_count: int) -> str:
    zoom = request.camera_zoom if request.camera_zoom is not None else 1.0
    density = _clamped(request.label_density, 0.0, 1.0)
    if zoom >= 2.1:
        return "precision"
    if zoom >= 1.35 or visible_count <= 48:
        return "detail"
    if zoom >= 0.85 or density >= 0.62 or visible_count <= 110:
        return "balanced"
    return "overview"


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
    base = 8 if node.score is None else max(5, min(14, int(5 + node.score * 8)))
    if request is not None and request.style_size_by == "degree":
        base = max(base, 6 + min(degree, 6))
    if (
        request is not None
        and request.style_size_by == "confidence"
        and node.confidence
    ):
        base = max(base, int(6 + node.confidence * 8))
    return max(3, min(24, int(base * _clamped(scale, 0.35, 2.2))))


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
