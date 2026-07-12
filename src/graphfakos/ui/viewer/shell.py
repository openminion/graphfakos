"""Graph-first document and workspace composition."""

from __future__ import annotations

from collections.abc import Iterable
from html import escape


def panel_stack(panels: Iterable[str]) -> str:
    """Render non-empty panels in their declared review order."""
    return "".join(panel for panel in panels if panel)


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


__all__ = ["panel_stack", "render_document", "render_graph_workspace"]
