"""Command-line entrypoints for GraphFakos."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

from .adapters import FileGraphProvider, FixtureGraphProvider
from .models import GraphFakosRequest, GraphFakosScreen
from .provider import GraphFakosProvider
from .server import serve_local_viewer
from .static import (
    GraphPreviewOutputPaths,
    write_provider_preview_outputs,
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
            "graphfakos.artifacts",
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
        preset_id=args.preset,
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


def _provider_from_args(args: argparse.Namespace) -> GraphFakosProvider:
    _validate_provider_args(args)
    if args.graph_json:
        try:
            provider = FileGraphProvider(
                args.graph_json,
                comparison_graph_path=args.comparison_graph_json,
                overlay_graph_paths=tuple(args.overlay_graph_json),
            )
        except (OSError, TypeError, ValueError) as exc:
            raise SystemExit(f"Unable to load graph artifact provider: {exc}") from exc
        return provider
    if args.provider_module:
        try:
            module = importlib.import_module(args.provider_module)
        except ModuleNotFoundError as exc:
            raise SystemExit(
                f"Unable to import provider module {args.provider_module!r}: {exc}"
            ) from exc
        except Exception as exc:
            raise SystemExit(
                f"Provider module {args.provider_module!r} failed to import: {exc}"
            ) from exc
        if not hasattr(module, args.provider_class):
            raise SystemExit(
                f"Provider class {args.provider_class!r} was not found in "
                f"{args.provider_module!r}"
            )
        provider_type = getattr(module, args.provider_class)
        if not callable(provider_type):
            raise SystemExit(
                f"Provider class {args.provider_class!r} in "
                f"{args.provider_module!r} is not callable"
            )
        kwargs = _provider_config(args.provider_config_json)
        try:
            provider = provider_type(**kwargs)
        except TypeError as exc:
            raise SystemExit(
                f"Unable to construct provider {args.provider_class!r}: {exc}"
            ) from exc
        except Exception as exc:
            raise SystemExit(
                f"Provider {args.provider_class!r} raised during construction: {exc}"
            ) from exc
        if not isinstance(provider, GraphFakosProvider):
            raise SystemExit(
                f"Provider {args.provider_class!r} does not satisfy the "
                "GraphFakosProvider contract"
            )
        return provider
    return FixtureGraphProvider()


def _provider_config(raw_payload: str) -> dict[str, Any]:
    if not raw_payload:
        return {}
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--provider-config-json must be valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("--provider-config-json must decode to an object")
    return payload


def _validate_provider_args(args: argparse.Namespace) -> None:
    if args.graph_json and args.provider_module:
        raise SystemExit("--graph-json cannot be combined with --provider-module")
    if args.comparison_graph_json and not args.graph_json:
        raise SystemExit("--comparison-graph-json requires --graph-json")
    if args.overlay_graph_json and not args.graph_json:
        raise SystemExit("--overlay-graph-json requires --graph-json")
    if args.provider_config_json and not args.provider_module:
        raise SystemExit("--provider-config-json requires --provider-module")
    if (
        args.provider_class != "FixtureGraphProvider"
        and not args.provider_module
        and not args.graph_json
    ):
        raise SystemExit("--provider-class requires --provider-module")


def ui_preview_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GraphFakos local graph viewer")
    parser.add_argument("--screen", choices=_SCREENS, default="explore")
    parser.add_argument("--preset", default="")
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
    parser.add_argument("--artifact-out", default="")
    parser.add_argument("--embed-out", default="")
    parser.add_argument("--report-out", default="")
    parser.add_argument("--markdown-report-out", default="")
    parser.add_argument("--dot-out", default="")
    parser.add_argument("--graph-json", default="")
    parser.add_argument("--comparison-graph-json", default="")
    parser.add_argument("--overlay-graph-json", action="append", default=[])
    parser.add_argument("--provider-module", default="")
    parser.add_argument("--provider-class", default="FixtureGraphProvider")
    parser.add_argument("--provider-config-json", default="")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    provider = _provider_from_args(args)
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

    payload = write_provider_preview_outputs(
        provider,
        request,
        GraphPreviewOutputPaths(
            html_path=args.html_out,
            artifact_path=args.artifact_out,
            embed_path=args.embed_out,
            report_path=args.report_out,
            markdown_report_path=args.markdown_report_out,
            dot_path=args.dot_out,
        ),
        open_browser=args.open,
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
