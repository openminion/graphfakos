"""Command-line entrypoints for GraphFakos."""

from __future__ import annotations

import argparse
import json

from .adapters import FixtureGraphProvider
from .models import GraphFakosRequest, GraphFakosScreen
from .server import serve_local_viewer
from .static import (
    write_embeddable_html,
    write_graph_markdown_report,
    write_graph_report,
    write_static_html,
)
from .ui import render_provider_path

_SCREENS: tuple[GraphFakosScreen, ...] = (
    "explore",
    "neighborhood",
    "path",
    "provenance",
    "timeline",
    "diff",
    "provider_status",
    "context_preview",
)


def smoke_payload() -> dict[str, object]:
    return {
        "package": "graphfakos",
        "version": "0.0.1",
        "status": "semantic-alpha",
        "semantic_contract": True,
        "openminion_imports": False,
        "stable_import_roots": [
            "graphfakos",
            "graphfakos.adapters",
            "graphfakos.contracts",
            "graphfakos.models",
            "graphfakos.provider",
            "graphfakos.render",
            "graphfakos.server",
            "graphfakos.static",
            "graphfakos.testing",
            "graphfakos.ui",
        ],
    }


def _request_from_args(args: argparse.Namespace) -> GraphFakosRequest:
    filters = {
        key: value
        for key, value in {
            "node_kind": args.node_kind,
            "edge_kind": args.edge_kind,
            "tag": args.tag,
            "source": args.source,
            "min_score": args.min_score,
        }.items()
        if value not in (None, "")
    }
    return GraphFakosRequest(
        screen=args.screen,
        query=args.query,
        focus_node_id=args.focus_node_id,
        selected_edge_id=args.selected_edge_id,
        source_node_id=args.source_node_id,
        target_node_id=args.target_node_id,
        comparison_graph_id=args.comparison_graph_id,
        max_depth=args.max_depth,
        filters=filters,
        layout=args.layout,
        limit=args.limit,
        render_limit=args.render_limit,
    )


def _print_payload(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return
    print(payload)


def ui_preview_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GraphFakos local graph viewer")
    parser.add_argument("--screen", choices=_SCREENS, default="explore")
    parser.add_argument("--query", default="")
    parser.add_argument("--focus-node-id")
    parser.add_argument("--selected-edge-id")
    parser.add_argument("--source-node-id")
    parser.add_argument("--target-node-id")
    parser.add_argument("--comparison-graph-id")
    parser.add_argument("--max-depth", type=int, default=1)
    parser.add_argument("--node-kind", default="")
    parser.add_argument("--edge-kind", default="")
    parser.add_argument("--tag", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--min-score", default="")
    parser.add_argument("--layout", default="force")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--render-limit", type=int, default=120)
    parser.add_argument("--html-out", default="graphfakos-ui-preview.html")
    parser.add_argument("--embed-out", default="")
    parser.add_argument("--report-out", default="")
    parser.add_argument("--markdown-report-out", default="")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    provider = FixtureGraphProvider()
    request = _request_from_args(args)
    if args.serve:
        result = serve_local_viewer(
            render_path=lambda path, query: render_provider_path(
                provider,
                request,
                path,
                query,
            ),
            default_path=f"/{request.screen}",
            host=args.host,
            port=args.port,
            open_browser=args.open,
        )
        _print_payload(result.to_dict(), as_json=args.json)
        return 0

    payload = write_static_html(
        provider,
        request,
        args.html_out,
        open_browser=args.open,
    )
    if args.embed_out:
        payload["embed"] = write_embeddable_html(provider, request, args.embed_out)
    if args.report_out:
        payload["report"] = write_graph_report(provider, request, args.report_out)
    if args.markdown_report_out:
        payload["markdown_report"] = write_graph_markdown_report(
            provider,
            request,
            args.markdown_report_out,
        )
    graph = provider.load_graph(request)
    payload.update(
        {
            "provider_id": graph.provider_id,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "route": f"/{request.screen}",
        }
    )
    _print_payload(payload, as_json=args.json)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="graphfakos package smoke")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    _print_payload(smoke_payload(), as_json=args.json)
    return 0


__all__ = [
    "main",
    "smoke_payload",
    "ui_preview_main",
]
