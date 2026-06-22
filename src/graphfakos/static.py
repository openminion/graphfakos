"""Static HTML export helpers."""

from __future__ import annotations

from pathlib import Path
import webbrowser

from .models import GraphFakosRequest
from .provider import GraphFakosProvider, load_provider_graph
from .ui import render_graph_viewer


def render_static_html(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> str:
    graph = load_provider_graph(provider, request)
    return render_graph_viewer(graph, request)


def write_static_html(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_path: str,
    *,
    open_browser: bool = False,
) -> dict[str, object]:
    html = render_static_html(provider, request)
    path = Path(output_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    opened = webbrowser.open(path.as_uri()) if open_browser else False
    return {
        "output_path": str(path),
        "screen": request.screen,
        "opened": opened,
    }


__all__ = [
    "render_static_html",
    "write_static_html",
]
