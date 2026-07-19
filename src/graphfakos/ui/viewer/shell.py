"""Graph-first document and workspace composition."""

from __future__ import annotations

from collections.abc import Iterable
from html import escape

from graphfakos.models import GraphFakosRequest
from graphfakos.ui.viewer.routing import _SCREEN_NAV, _route_href


def panel_stack(panels: Iterable[str]) -> str:
    """Render non-empty panels in their declared review order."""
    return "".join(panel for panel in panels if panel)


def render_navigation(request: GraphFakosRequest) -> str:
    primary_screens = {"explore", "neighborhood", "path"}
    primary_links = ""
    analysis_links = ""
    for screen, label in _SCREEN_NAV:
        current = 'aria-current="page"' if request.screen == screen else ""
        display_label = "Local" if screen == "neighborhood" else label
        link = (
            f"<a href='{_route_href(request, screen=screen, overrides={'preset_id': None})}' "
            f"{current}>{escape(display_label)}</a>"
        )
        if screen in primary_screens:
            primary_links += link
        else:
            analysis_links += link
    analysis_open = " open" if request.screen not in primary_screens else ""
    return (
        "<nav class='gf-nav' aria-label='GraphFakos screens'>"
        "<div class='gf-nav-heading'><h1>GraphFakos</h1>"
        "<button type='button' data-gf-nav-toggle='true' aria-label='Toggle navigation' "
        "aria-controls='gf-nav-menu' aria-expanded='true'>☰</button></div>"
        "<div id='gf-nav-menu' data-gf-nav-menu='true'>"
        f"<div class='gf-nav-primary'>{primary_links}</div>"
        f"<details class='gf-nav-analysis'{analysis_open}><summary>Analyze</summary>"
        f"{analysis_links}</details></div></nav>"
    )


def render_document(
    *,
    title: str,
    theme: str,
    navigation: str,
    content: str,
    styles: str,
    script: str,
) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)} - GraphFakos</title>{styles}</head>"
        f"<body class='gf-page' data-theme='{escape(theme)}'>"
        f"<div class='gf-shell'>{navigation}{content}</div>{script}</body></html>"
    )


def render_graph_workspace(primary: str, context: str) -> str:
    return (
        "<section class='gf-layout gf-layout-graph-first'>"
        f"<div class='gf-graph-primary'>{primary}</div>"
        "<details class='gf-context-drawer' data-gf-context-drawer='true'>"
        "<summary><span>Tools</span>"
        "<small>Filters, evidence, actions, and advanced tools</small></summary>"
        f"<div class='gf-context-scroll'>{context}</div></details></section>"
    )


__all__ = [
    "panel_stack",
    "render_document",
    "render_graph_workspace",
    "render_navigation",
]
