"""Static HTML export helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import webbrowser

from .artifacts import write_graph_artifact
from .models import (
    GraphFakosGraph,
    GraphFakosReplayBundle,
    GraphFakosRequest,
    GraphFakosSavedView,
    GraphFakosViewerState,
)
from .provider import (
    GraphFakosProvider,
    analyze_graph,
    diagnose_graph,
    load_comparison_graph,
    load_overlay_graphs,
    load_provider_graph,
)
from .ui import (
    build_viewer_route,
    build_graph_diff,
    render_graph_fragment,
    render_graph_viewer,
    review_preset_manifest,
    screen_manifest,
)


def render_static_html(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> str:
    graph, comparison_graph, overlay_graphs = _loaded_graphs(provider, request)
    return render_graph_viewer(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )


def render_embeddable_html(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> str:
    graph, comparison_graph, overlay_graphs = _loaded_graphs(provider, request)
    return render_graph_fragment(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )


def build_graph_report(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> dict[str, object]:
    graph, comparison_graph, overlay_graphs = _loaded_graphs(provider, request)
    return _graph_report_payload(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )


def _graph_report_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> dict[str, object]:
    report: dict[str, object] = {
        "request": request.to_dict(),
        "viewer_state": GraphFakosViewerState.from_request(request).to_dict(),
        "saved_view": GraphFakosSavedView.from_request(
            request,
            view_id=request.saved_view_id or "route",
            label="Current route view",
        ).to_dict(),
        "analytics": analyze_graph(graph).to_dict(),
        "graph": graph.to_dict(),
        "diagnostics": diagnose_graph(graph).to_dict(),
        "screen_manifest": list(screen_manifest()),
        "overlay_graphs": [item.to_dict() for item in overlay_graphs],
        "review_presets": list(
            review_preset_manifest(
                graph,
                request,
                comparison_graph=comparison_graph,
            )
        ),
    }
    if comparison_graph is not None:
        report["comparison_graph"] = comparison_graph.to_dict()
        report["comparison_diff"] = build_graph_diff(graph, comparison_graph)
    return report


def _loaded_graphs(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> tuple[
    GraphFakosGraph,
    GraphFakosGraph | None,
    tuple[GraphFakosGraph, ...],
]:
    return (
        load_provider_graph(provider, request),
        load_comparison_graph(provider, request),
        load_overlay_graphs(provider, request),
    )


@dataclass(frozen=True, slots=True)
class GraphPreviewOutputPaths:
    html_path: str
    artifact_path: str = ""
    embed_path: str = ""
    report_path: str = ""
    markdown_report_path: str = ""
    dot_path: str = ""
    bundle_path: str = ""


def build_graph_replay_bundle(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> GraphFakosReplayBundle:
    graph = load_provider_graph(provider, request)
    saved_view = GraphFakosSavedView.from_request(
        request,
        view_id=request.saved_view_id or "route",
        label="Current route view",
    )
    return GraphFakosReplayBundle(
        bundle_id=f"{graph.graph_id}:{request.screen}",
        graph=graph,
        viewer_state=GraphFakosViewerState.from_request(request),
        created_at=graph.generated_at,
        saved_views=(saved_view,),
        analytics=analyze_graph(graph),
    )


def render_graph_markdown_report(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> str:
    report = build_graph_report(provider, request)
    graph = report["graph"]
    diagnostics = report["diagnostics"]
    snapshot = graph.get("snapshot") if isinstance(graph, dict) else None
    lines = [
        "# GraphFakos Report",
        "",
        f"- Screen: `{request.screen}`",
        f"- Provider: `{graph.get('provider_label', '')}`",
        f"- Role: `{graph.get('graph_role', '')}`",
        f"- Nodes: `{len(graph.get('nodes', []))}`",
        f"- Edges: `{len(graph.get('edges', []))}`",
        f"- Healthy: `{diagnostics.get('healthy')}`",
    ]
    if isinstance(snapshot, dict) and snapshot.get("snapshot_id"):
        lines.append(f"- Snapshot: `{snapshot['snapshot_id']}`")
    if "comparison_graph" in report:
        comparison = report["comparison_graph"]
        if isinstance(comparison, dict):
            lines.append(f"- Comparison: `{comparison.get('provider_label', '')}`")
    comparison_diff = report.get("comparison_diff")
    lines.extend(
        [
            "",
            "## Diagnostics",
            "",
            f"- Orphan nodes: `{len(diagnostics.get('orphan_node_ids', []))}`",
            f"- Duplicate edges: `{len(diagnostics.get('duplicate_edge_ids', []))}`",
            f"- Unknown provenance refs: `{len(diagnostics.get('unknown_provenance_ids', []))}`",
            f"- Unknown citation refs: `{len(diagnostics.get('unknown_citation_ids', []))}`",
            f"- Self-loop edges: `{len(diagnostics.get('self_loop_edge_ids', []))}`",
            f"- Secondary-component nodes: `{len(diagnostics.get('disconnected_node_ids', []))}`",
        ]
    )
    if isinstance(comparison_diff, dict):
        summary = comparison_diff.get("summary", {})
        lines.extend(
            [
                "",
                "## Diff Summary",
                "",
                f"- Changed nodes: `{summary.get('changed node count', 0)}`",
                f"- Changed edges: `{summary.get('changed edge count', 0)}`",
                f"- Snapshot changes: `{summary.get('snapshot change count', 0)}`",
            ]
        )
        hotspots = comparison_diff.get("change_hotspots", [])
        if hotspots:
            lines.extend(["", "### Change Hotspots", ""])
            lines.extend(f"- {item}" for item in hotspots)
        for title, key in (
            ("Changed nodes", "changed_nodes"),
            ("Changed edges", "changed_edges"),
            ("Snapshot changes", "snapshot_changes"),
        ):
            items = comparison_diff.get(key, [])
            if not items:
                continue
            lines.extend(["", f"### {title}", ""])
            lines.extend(f"- {item}" for item in items)
    return "\n".join(lines) + "\n"


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


def write_embeddable_html(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_path: str,
) -> dict[str, object]:
    html = render_embeddable_html(provider, request)
    path = Path(output_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return {
        "output_path": str(path),
        "screen": request.screen,
        "embedded": True,
    }


def write_graph_report(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_path: str,
) -> dict[str, object]:
    payload = build_graph_report(provider, request)
    path = Path(output_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "output_path": str(path),
        "screen": request.screen,
        "report": True,
    }


def write_graph_replay_bundle(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_path: str,
) -> dict[str, object]:
    bundle = build_graph_replay_bundle(provider, request)
    return _write_json_output(
        bundle.to_dict(),
        output_path,
        screen=request.screen,
        key="replay_bundle",
    )


def write_graph_markdown_report(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_path: str,
) -> dict[str, object]:
    markdown = render_graph_markdown_report(provider, request)
    path = Path(output_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return {
        "output_path": str(path),
        "screen": request.screen,
        "markdown_report": True,
    }


def render_graph_dot(graph: GraphFakosGraph) -> str:
    lines = [f'digraph "{graph.graph_id}" {{']
    lines.append('  graph [label="GraphFakos export", labelloc=t];')
    for node in graph.nodes:
        label = _dot_escape(node.label or node.id)
        kind = _dot_escape(node.kind)
        lines.append(f'  "{_dot_escape(node.id)}" [label="{label}\\n({kind})"];')
    for edge in graph.edges:
        label = _dot_escape(edge.label or edge.kind)
        lines.append(
            f'  "{_dot_escape(edge.source_id)}" -> "{_dot_escape(edge.target_id)}" '
            f'[label="{label}"];'
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_graph_dot(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_path: str,
) -> dict[str, object]:
    graph = load_provider_graph(provider, request)
    dot = render_graph_dot(graph)
    path = _resolved_output_path(output_path)
    path.write_text(dot, encoding="utf-8")
    return {
        "output_path": str(path),
        "screen": request.screen,
        "dot": True,
    }


def write_provider_graph_artifact(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_path: str,
) -> dict[str, object]:
    graph = load_provider_graph(provider, request)
    return write_graph_artifact(graph, output_path)


def write_provider_preview_outputs(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_paths: GraphPreviewOutputPaths,
    *,
    open_browser: bool = False,
) -> dict[str, object]:
    graph, comparison_graph, overlay_graphs = _loaded_graphs(provider, request)
    html = render_graph_viewer(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )
    payload = _write_html_output(
        html,
        output_paths.html_path,
        screen=request.screen,
        open_browser=open_browser,
    )
    if output_paths.artifact_path:
        payload["artifact"] = write_graph_artifact(graph, output_paths.artifact_path)
    if output_paths.embed_path:
        embed_html = render_graph_fragment(
            graph,
            request,
            comparison_graph=comparison_graph,
            overlay_graphs=overlay_graphs,
        )
        payload["embed"] = _write_embed_output(
            embed_html,
            output_paths.embed_path,
            screen=request.screen,
        )
    report = _graph_report_payload(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )
    if output_paths.report_path:
        payload["report"] = _write_json_output(
            report,
            output_paths.report_path,
            screen=request.screen,
            key="report",
        )
    if output_paths.markdown_report_path:
        markdown = render_graph_markdown_report(provider, request)
        payload["markdown_report"] = _write_markdown_output(
            markdown,
            output_paths.markdown_report_path,
            screen=request.screen,
        )
    if output_paths.dot_path:
        payload["dot"] = _write_dot_output(
            render_graph_dot(graph),
            output_paths.dot_path,
            screen=request.screen,
        )
    if output_paths.bundle_path:
        bundle = GraphFakosReplayBundle(
            bundle_id=f"{graph.graph_id}:{request.screen}",
            graph=graph,
            viewer_state=GraphFakosViewerState.from_request(request),
            created_at=graph.generated_at,
            saved_views=(
                GraphFakosSavedView.from_request(
                    request,
                    view_id=request.saved_view_id or "route",
                    label="Current route view",
                ),
            ),
            analytics=analyze_graph(graph),
        )
        payload["replay_bundle"] = _write_json_output(
            bundle.to_dict(),
            output_paths.bundle_path,
            screen=request.screen,
            key="replay_bundle",
        )
    payload.update(
        {
            "provider_id": graph.provider_id,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "route": build_viewer_route(request),
        }
    )
    return payload


def _write_html_output(
    html: str,
    output_path: str,
    *,
    screen: str,
    open_browser: bool,
) -> dict[str, object]:
    path = _resolved_output_path(output_path)
    path.write_text(html, encoding="utf-8")
    opened = webbrowser.open(path.as_uri()) if open_browser else False
    return {
        "output_path": str(path),
        "screen": screen,
        "opened": opened,
    }


def _write_embed_output(
    html: str,
    output_path: str,
    *,
    screen: str,
) -> dict[str, object]:
    path = _resolved_output_path(output_path)
    path.write_text(html, encoding="utf-8")
    return {
        "output_path": str(path),
        "screen": screen,
        "embedded": True,
    }


def _write_json_output(
    payload: dict[str, object],
    output_path: str,
    *,
    screen: str,
    key: str,
) -> dict[str, object]:
    path = _resolved_output_path(output_path)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "output_path": str(path),
        "screen": screen,
        key: True,
    }


def _write_markdown_output(
    markdown: str,
    output_path: str,
    *,
    screen: str,
) -> dict[str, object]:
    path = _resolved_output_path(output_path)
    path.write_text(markdown, encoding="utf-8")
    return {
        "output_path": str(path),
        "screen": screen,
        "markdown_report": True,
    }


def _write_dot_output(
    dot: str,
    output_path: str,
    *,
    screen: str,
) -> dict[str, object]:
    path = _resolved_output_path(output_path)
    path.write_text(dot, encoding="utf-8")
    return {
        "output_path": str(path),
        "screen": screen,
        "dot": True,
    }


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _resolved_output_path(output_path: str) -> Path:
    path = Path(output_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


__all__ = [
    "GraphPreviewOutputPaths",
    "build_graph_replay_bundle",
    "build_graph_report",
    "render_graph_dot",
    "render_embeddable_html",
    "render_graph_markdown_report",
    "render_static_html",
    "write_graph_dot",
    "write_graph_replay_bundle",
    "write_embeddable_html",
    "write_graph_markdown_report",
    "write_provider_preview_outputs",
    "write_provider_graph_artifact",
    "write_graph_report",
    "write_static_html",
]
