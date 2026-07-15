"""Compact controls that sit directly on the graph surface."""

from __future__ import annotations

from html import escape

from graphfakos.models import GraphFakosRequest
from graphfakos.ui.viewer.routing import _route_href


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
    theme_label = "Light" if request.theme == "space" else "Space"
    theme_route = _route_href(request, overrides={"theme": next_theme})
    return (
        "<div class='gf-canvas-tools' aria-label='Graph camera controls'>"
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
        f"href='{escape(theme_route)}'>{theme_label}</a>"
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
    active_level = "local" if request.focus_node_id else "overview"
    levels = "".join(
        f"<button type='button' data-gf-scene-level='{level}' "
        f"data-active='{str(active_level == level).lower()}'>{label}</button>"
        for level, label in (
            ("overview", "Overview"),
            ("cluster", "Clusters"),
            ("local", "Local"),
        )
    )
    return (
        "<details class='gf-display-dock' data-gf-display-dock='true'>"
        "<summary><span>Display</span><small>scene</small></summary>"
        "<div class='gf-display-dock-body'>"
        f"<div class='gf-scene-levels' aria-label='Graph detail level'>{levels}</div>"
        "<label><span>Nodes</span>"
        f"<input type='range' min='0.35' max='1.6' step='0.05' "
        f"value='{request.node_scale:.2f}' data-gf-scene-control='node_scale'></label>"
        "<label><span>Labels</span>"
        f"<input type='range' min='0' max='1' step='0.05' "
        f"value='{request.label_density:.2f}' "
        "data-gf-scene-control='label_density'></label>"
        "<label><span>Links</span>"
        f"<input type='range' min='0.15' max='1' step='0.05' "
        f"value='{request.edge_opacity:.2f}' "
        "data-gf-scene-control='edge_opacity'></label>"
        "<p>Double-click a node to fly to it. Hover or select to reveal its "
        "neighborhood.</p></div></details>"
    )
