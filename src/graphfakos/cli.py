"""Command-line entrypoints for GraphFakos."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

from .adapters import (
    DEMO_SCENARIOS,
    DemoGraphProvider,
    FileGraphProvider,
    FixtureGraphProvider,
)
from .models import (
    GraphFakosActionStatus,
    GraphFakosGraphAction,
    GraphFakosGraph,
    GraphFakosKnowledgeCapture,
    GraphFakosRequest,
    GraphFakosScreen,
)
from .provider import (
    GraphFakosGraphActionProvider,
    GraphFakosKnowledgeCaptureProvider,
    GraphFakosProvider,
)
from .server import serve_local_viewer
from .static import (
    GraphPreviewOutputPaths,
    write_provider_preview_outputs,
)
from .ui import render_provider_path, render_provider_path_fragment

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
        "version": "0.0.4rc1",
        "status": "semantic-alpha",
        "semantic_contract": True,
        "openminion_imports": False,
        "stable_import_roots": [
            "graphfakos",
            "graphfakos.artifacts",
            "graphfakos.adapters",
            "graphfakos.browser",
            "graphfakos.contracts",
            "graphfakos.models",
            "graphfakos.provider",
            "graphfakos.render",
            "graphfakos.renderers",
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
        selected_node_ids=_tuple_from_csv(args.selected_node_ids),
        selected_edge_id=args.selected_edge_id,
        source_node_id=args.source_node_id,
        target_node_id=args.target_node_id,
        comparison_graph_id=args.comparison_graph_id,
        max_depth=args.max_depth,
        filters=filters,
        layout=args.layout,
        limit=args.limit,
        render_limit=args.render_limit,
        camera_x=args.camera_x,
        camera_y=args.camera_y,
        camera_zoom=args.camera_zoom,
        render_engine=args.render_engine,
        theme=args.theme,
        saved_view_id=args.saved_view_id,
        show_orphans=not args.hide_orphans,
        show_neighbor_links=not args.hide_neighbor_links,
        edge_clutter=args.edge_clutter,
        analytics_overlay=args.analytics_overlay,
        center_force=args.center_force,
        repel_force=args.repel_force,
        link_distance=args.link_distance,
        node_scale=args.node_scale,
        edge_scale=args.edge_scale,
        edge_opacity=args.edge_opacity,
        label_density=args.label_density,
        pinned_positions=_pinned_positions_from_json(args.pinned_positions_json),
        style_color_by=args.style_color_by,
        style_size_by=args.style_size_by,
        style_edge_width_by=args.style_edge_width_by,
        min_degree=args.min_degree,
        max_degree=args.max_degree,
        component_id=args.component_id,
        connected_to_node_id=args.connected_to_node_id,
        evidence_filter=args.evidence_filter,
        cluster_id=args.cluster_id,
        timeline_frame=args.timeline_frame,
        timeline_playback=args.timeline_playback,
        pivot_node_id=args.pivot_node_id,
        pivot_mode=args.pivot_mode,
    )


def _print_payload(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return
    print(payload)


def _provider_from_args(args: argparse.Namespace) -> GraphFakosProvider:
    _validate_provider_args(args)
    if args.demo_scenario:
        try:
            return DemoGraphProvider(args.demo_scenario)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
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


def _tuple_from_csv(raw_value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def _pinned_positions_from_json(raw_payload: str) -> dict[str, tuple[float, float]]:
    if not raw_payload:
        return {}
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--pinned-positions-json must be valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("--pinned-positions-json must decode to an object")
    positions: dict[str, tuple[float, float]] = {}
    for node_id, coordinate in payload.items():
        if not isinstance(node_id, str):
            raise SystemExit("--pinned-positions-json keys must be node id strings")
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
            raise SystemExit(
                "--pinned-positions-json values must be two-item coordinate arrays"
            )
        try:
            positions[node_id] = (float(coordinate[0]), float(coordinate[1]))
        except (TypeError, ValueError) as exc:
            raise SystemExit(
                "--pinned-positions-json coordinates must be numeric"
            ) from exc
    return positions


def _validate_provider_args(args: argparse.Namespace) -> None:
    if args.demo_scenario and (args.graph_json or args.provider_module):
        raise SystemExit(
            "--demo-scenario cannot be combined with --graph-json or --provider-module"
        )
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


def handle_provider_action(
    provider: GraphFakosProvider,
    path: str,
    payload: dict[str, object],
) -> dict[str, object]:
    if path == "/api/action":
        action = GraphFakosGraphAction.from_dict(payload)
        if not isinstance(provider, GraphFakosGraphActionProvider):
            status = GraphFakosActionStatus(
                action_id=action.action_id,
                status="unsupported",
                message="provider does not support graph edit actions",
            )
            return {"ok": False, "status": status.to_dict(), "action": action.to_dict()}
        result = provider.submit_graph_action(action)
        if isinstance(result, GraphFakosActionStatus):
            return {"ok": True, "status": result.to_dict(), "action": action.to_dict()}
        if isinstance(result, dict):
            return {"ok": True, "result": result, "action": action.to_dict()}
        status = GraphFakosActionStatus(
            action_id=action.action_id,
            status="queued",
            message="provider accepted the graph action",
        )
        return {"ok": True, "status": status.to_dict(), "action": action.to_dict()}
    if path != "/api/knowledge":
        return {"ok": False, "error": f"unsupported GraphFakos action path: {path}"}
    capture = GraphFakosKnowledgeCapture.from_dict(payload)
    if not isinstance(provider, GraphFakosKnowledgeCaptureProvider):
        return {
            "ok": False,
            "error": "provider does not support workbench knowledge capture",
            "capture": capture.to_dict(),
        }
    result = provider.capture_knowledge(capture)
    response: dict[str, object] = {"ok": True, "capture": capture.to_dict()}
    if isinstance(result, GraphFakosGraph):
        response["graph"] = result.to_dict()
        response["status"] = GraphFakosActionStatus(
            action_id=f"capture:{capture.link_node_id or 'graph'}",
            status="done",
            message="knowledge capture was applied by the provider",
            graph_id=result.graph_id,
        ).to_dict()
    elif isinstance(result, dict):
        response["result"] = result
    elif result is not None:
        response["result"] = {"value": str(result)}
    return response


def ui_preview_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GraphFakos local graph viewer")
    parser.add_argument("--screen", choices=_SCREENS, default="explore")
    parser.add_argument("--preset", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--focus-node-id")
    parser.add_argument("--selected-node-ids", default="")
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
    parser.add_argument("--camera-x", type=float)
    parser.add_argument("--camera-y", type=float)
    parser.add_argument("--camera-zoom", type=float)
    parser.add_argument("--render-engine", default="svg")
    parser.add_argument("--theme", default="default")
    parser.add_argument("--saved-view-id", default="")
    parser.add_argument("--hide-orphans", action="store_true")
    parser.add_argument("--hide-neighbor-links", action="store_true")
    parser.add_argument("--edge-clutter", default="normal")
    parser.add_argument("--analytics-overlay", default="degree")
    parser.add_argument("--center-force", type=float, default=0.012)
    parser.add_argument("--repel-force", type=float, default=1.0)
    parser.add_argument("--link-distance", type=float, default=1.0)
    parser.add_argument("--node-scale", type=float, default=1.0)
    parser.add_argument("--edge-scale", type=float, default=1.0)
    parser.add_argument("--edge-opacity", type=float, default=1.0)
    parser.add_argument("--label-density", type=float, default=1.0)
    parser.add_argument("--pinned-positions-json", default="")
    parser.add_argument("--style-color-by", default="kind")
    parser.add_argument("--style-size-by", default="score")
    parser.add_argument("--style-edge-width-by", default="kind")
    parser.add_argument("--min-degree", type=int)
    parser.add_argument("--max-degree", type=int)
    parser.add_argument("--component-id", default="")
    parser.add_argument("--connected-to-node-id", default="")
    parser.add_argument("--evidence-filter", default="")
    parser.add_argument("--cluster-id", default="")
    parser.add_argument("--timeline-frame", default="")
    parser.add_argument("--timeline-playback", default="stopped")
    parser.add_argument("--pivot-node-id", default="")
    parser.add_argument("--pivot-mode", default="")
    parser.add_argument("--html-out", default="graphfakos-ui-preview.html")
    parser.add_argument("--artifact-out", default="")
    parser.add_argument("--embed-out", default="")
    parser.add_argument("--report-out", default="")
    parser.add_argument("--markdown-report-out", default="")
    parser.add_argument("--dot-out", default="")
    parser.add_argument("--bundle-out", default="")
    parser.add_argument("--demo-scenario", choices=DEMO_SCENARIOS, default="")
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
            render_fragment_path=lambda path, query: render_provider_path_fragment(
                provider,
                request,
                path,
                query,
            ),
            handle_action=lambda path, payload: handle_provider_action(
                provider,
                path,
                payload,
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
            bundle_path=args.bundle_out,
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
