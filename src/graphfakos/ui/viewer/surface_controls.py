"""Compact controls that sit directly on the graph surface."""

from __future__ import annotations

from collections import defaultdict
from html import escape

from graphfakos.models import GraphFakosGraph, GraphFakosNode, GraphFakosRequest
from graphfakos.ui.viewer.filtering import _facet_values
from graphfakos.ui.viewer.graph_ops import _node_cluster_id
from graphfakos.ui.viewer.html import panel_body as _panel_body
from graphfakos.ui.viewer.html import summary_note as _summary_note
from graphfakos.ui.viewer.routing import _route_href


def navigation_help(
    request: GraphFakosRequest,
    node_count: int,
    edge_count: int,
    renderer_notice: str,
) -> str:
    pointer_help = (
        "drag empty canvas to orbit; right-drag to pan; scroll to zoom; "
        "tap or click a node to inspect it"
        if request.render_engine == "3d"
        else "drag empty canvas to pan; scroll to zoom; click a node to inspect it"
    )
    return (
        "<details class='gf-canvas-help'><summary aria-label='Navigation help'>?</summary><div>"
        f"<p class='gf-note'>Layout {escape(request.layout)}. Rendering {node_count} node(s) "
        f"and {edge_count} edge(s). Fit zooms to the current selection or visible graph; "
        f"{pointer_help}; drag a node to pin it; Shift-drag empty canvas to box-select "
        "nodes; right-click or press Shift+F10 on nodes or edges for actions.</p>"
        "<p class='gf-shortcut-hint'>Navigation: mouse drag orbits in 3D, right-drag pans, "
        "and scroll zooms toward the cursor; touch drag orbits, pinch zooms, and two-finger "
        "drag pans; Alt/Option-drag a node to move its cluster, WASD or arrows move like a "
        "map, use Focus on a group card to fly to it, [ and ] retrace graph focus, J/K steps "
        "through connected items, Enter or . focuses the current selection, Home fits the "
        "visible graph, Q/E orbits in 3D mode, 0 resets camera, F fullscreen, Delete clears "
        f"selection.</p>{renderer_notice}</div></details>"
    )


def touch_guide(request: GraphFakosRequest) -> str:
    if request.render_engine != "3d":
        return ""
    return (
        "<div class='gf-touch-guide' data-gf-touch-guide='true' aria-hidden='true'>"
        "<span>Tap inspect</span><span>Drag orbit</span>"
        "<span>Pinch zoom</span><span>Two fingers move</span></div>"
    )


def canvas_toolbar(request: GraphFakosRequest) -> str:
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
    theme_label = "Light" if request.theme == "space" else "Dark"
    theme_route = _route_href(request, overrides={"theme": next_theme})
    return (
        "<div class='gf-canvas-tools' aria-label='Graph camera controls'>"
        "<div class='gf-focus-history' aria-label='Graph navigation history'>"
        "<button type='button' data-gf-focus-history='back' title='Previous graph focus' "
        "aria-label='Previous graph focus' disabled>&larr;</button>"
        "<button type='button' data-gf-focus-history='forward' title='Next graph focus' "
        "aria-label='Next graph focus' disabled>&rarr;</button></div>"
        "<button type='button' data-gf-camera='zoom-in' title='Zoom in' "
        "aria-label='Zoom in'>+</button>"
        "<button type='button' data-gf-camera='zoom-out' title='Zoom out' "
        "aria-label='Zoom out'>-</button>"
        "<button type='button' data-gf-camera='fit' "
        "title='Fit selected or visible graph' "
        "aria-label='Fit selected or visible graph'>Fit</button>"
        "<button type='button' data-gf-layout-reset='true' "
        "title='Reset graph formation' aria-label='Reset graph formation'>"
        "Reflow</button>"
        f"<a class='gf-tool-link gf-theme-toggle' data-gf-theme-toggle='true' "
        f"href='{escape(theme_route)}' title='Switch graph theme' "
        f"aria-label='{theme_label}'>{theme_label}</a>"
        "<button type='button' data-gf-camera='fullscreen' title='Fullscreen graph' "
        "aria-label='Fullscreen graph'>Full</button>"
        "<details class='gf-tool-menu'><summary aria-label='More graph controls'>"
        "•••</summary><div>"
        "<button type='button' data-gf-camera='reset'>Reset camera</button>"
        "<button type='button' data-gf-history='undo' disabled>Undo</button>"
        "<button type='button' data-gf-history='redo' disabled>Redo</button>"
        "<button type='button' data-gf-pin='reset'>Clear pins</button>"
        f"<a class='gf-tool-link' href='{escape(clear_pins_route)}'>"
        "Reset saved pins</a>"
        f"<a class='gf-tool-link' data-gf-save-view='true' "
        f"href='{escape(saved_route)}'>Saved view</a></div></details></div>"
    )


def display_controls(request: GraphFakosRequest) -> str:
    active_level = request.scene_level or (
        "local" if request.focus_node_id else "overview"
    )
    levels = "".join(
        f"<button type='button' data-gf-scene-level='{level}' "
        f"data-active='{str(active_level == level).lower()}'>{label}</button>"
        for level, label in (
            ("overview", "Overview"),
            ("islands", "Islands"),
            ("cluster", "Clusters"),
            ("local", "Local"),
            ("precision", "Precision"),
        )
    )
    return (
        "<details class='gf-display-dock' data-gf-display-dock='true'>"
        "<summary><span>Density</span><small>dots / labels / links</small></summary>"
        "<div class='gf-display-dock-body'>"
        f"<div class='gf-scene-levels' aria-label='Graph detail level'>{levels}</div>"
        "<label><span>Dots</span>"
        f"<input type='range' min='0.2' max='1.6' step='0.05' "
        f"value='{request.node_scale:.2f}' data-gf-scene-control='node_scale'></label>"
        "<label><span>Labels</span>"
        f"<input type='range' min='0' max='1' step='0.05' "
        f"value='{request.label_density:.2f}' "
        "data-gf-scene-control='label_density'></label>"
        "<label><span>Links</span>"
        f"<input type='range' min='0.15' max='1' step='0.05' "
        f"value='{request.edge_opacity:.2f}' "
        "data-gf-scene-control='edge_opacity'></label>"
        "<p>Keep overview sparse; use Local or Precision only after focusing "
        "an island or node.</p></div></details>"
    )


def render_budget_panel(
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


def group_controls(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    kinds = _facet_values(graph, "node_kind")
    clusters = _cluster_control_rows(graph)
    if not kinds and not clusters:
        return ""
    hidden = set(request.hidden_groups)
    kind_buttons = "".join(
        f"<button type='button' data-gf-group='{escape(kind)}' "
        f"data-active='{str(kind not in hidden).lower()}' "
        f"title='Toggle {escape(kind)} nodes. Alt-click to focus.'>{escape(kind)}</button>"
        for kind in kinds
    )
    kind_links = "".join(
        f"<a href='{_route_href(request, overrides={'node_kind': kind})}'>{escape(kind)}</a>"
        for kind in kinds
    )
    cluster_buttons = "".join(
        f"<article class='gf-cluster-card' data-gf-group-card='{escape(cluster_id)}' data-active='{str(cluster_id not in hidden).lower()}'>"
        f"<button type='button' class='gf-cluster-focus' data-gf-group-focus='{escape(cluster_id)}' aria-label='Focus cluster {escape(label)}'><span>cluster</span><strong>{escape(label)}</strong><small>{count} nodes · {hub}</small>"
        f"</button><button type='button' class='gf-cluster-toggle' data-gf-group='{escape(cluster_id)}' "
        f"data-active='{str(cluster_id not in hidden).lower()}' aria-pressed='{str(cluster_id not in hidden).lower()}' aria-label='Show or hide cluster {escape(label)}'>Visible</button></article>"
        for cluster_id, label, count, hub in clusters
    )
    return (
        "<div class='gf-group-controls' aria-label='Node group controls'>"
        "<div class='gf-group-controls-head'>"
        "<span>Dense navigation</span>"
        f"<button type='button' data-gf-group-show-all='true'>Show all</button></div>"
        f"<div class='gf-group-kind-row'>{kind_buttons}</div>"
        f"<div class='gf-group-cluster-row'>{cluster_buttons}</div>"
        f"<div class='gf-group-fallback'>{kind_links}</div></div>"
    )


def _cluster_control_rows(
    graph: GraphFakosGraph,
) -> list[tuple[str, str, int, str]]:
    buckets: dict[str, list[GraphFakosNode]] = defaultdict(list)
    for node in graph.nodes:
        buckets[_node_cluster_id(node)].append(node)
    rows = []
    for cluster_id, nodes in sorted(
        buckets.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )[:12]:
        if not cluster_id:
            continue
        hub = max(nodes, key=lambda node: node.score or 0.0)
        rows.append(
            (cluster_id, _cluster_label(cluster_id, hub), len(nodes), hub.label)
        )
    return rows


def _cluster_label(cluster_id: str, hub: GraphFakosNode) -> str:
    if cluster_id.startswith("scale-"):
        return "Scale " + cluster_id.removeprefix("scale-").upper()
    if cluster_id.startswith("cluster-"):
        return "Cluster " + cluster_id.removeprefix("cluster-").upper()
    return hub.visual.group or hub.kind.title()


def compass_hud() -> str:
    """Render the compact live 3D orientation control."""
    return (
        "<button type='button' class='gf-orientation-hud' "
        "data-gf-orientation-reset='true' aria-label='Reset 3D orientation' "
        "title='Reset 3D orientation'>"
        "<span data-gf-orientation-compass='true' aria-hidden='true'>N</span>"
        "<span><strong data-gf-orientation-yaw='true'>0°</strong>"
        "<small data-gf-orientation-pitch='true'>level</small></span></button>"
    )


def spatial_trail(request: GraphFakosRequest) -> str:
    """Render a route-backed semantic location trail for the graph surface."""
    root_route = _route_href(
        request,
        overrides={
            "focus_node_id": None,
            "selected_node_ids": None,
            "selected_edge_id": None,
            "camera_x": 0,
            "camera_y": 0,
            "camera_zoom": 1,
            "camera_yaw": 0,
            "camera_pitch": 0,
            "camera_pose": None,
        },
    )
    hidden = "" if request.focus_node_id else " hidden"
    current = (
        "<span class='gf-spatial-current' aria-current='location'>"
        f"{escape(request.focus_node_id or '')}</span>"
        if request.focus_node_id
        else ""
    )
    return (
        f"<nav class='gf-spatial-trail' data-gf-spatial-trail='true' "
        f"aria-label='Current graph location'{hidden}>"
        f"<a href='{escape(root_route)}' data-gf-spatial-root='true'>All graph</a>"
        f"<span class='gf-spatial-items' data-gf-spatial-items='true'>{current}</span>"
        "</nav>"
    )
