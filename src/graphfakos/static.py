"""Static HTML export helpers."""

from __future__ import annotations

import json
from pathlib import Path
import webbrowser

from .artifacts import write_graph_artifact
from .models import GraphFakosRequest
from .provider import (
    GraphFakosProvider,
    diagnose_graph,
    load_comparison_graph,
    load_overlay_graphs,
    load_provider_graph,
)
from .ui import (
    build_graph_diff,
    render_graph_fragment,
    render_graph_viewer,
    screen_manifest,
)


def render_static_html(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> str:
    graph = load_provider_graph(provider, request)
    return render_graph_viewer(
        graph,
        request,
        comparison_graph=load_comparison_graph(provider, request),
        overlay_graphs=load_overlay_graphs(provider, request),
    )


def render_embeddable_html(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> str:
    graph = load_provider_graph(provider, request)
    return render_graph_fragment(
        graph,
        request,
        comparison_graph=load_comparison_graph(provider, request),
        overlay_graphs=load_overlay_graphs(provider, request),
    )


def build_graph_report(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
) -> dict[str, object]:
    graph = load_provider_graph(provider, request)
    comparison_graph = load_comparison_graph(provider, request)
    overlay_graphs = load_overlay_graphs(provider, request)
    report: dict[str, object] = {
        "request": request.to_dict(),
        "graph": graph.to_dict(),
        "diagnostics": diagnose_graph(graph).to_dict(),
        "screen_manifest": list(screen_manifest()),
        "overlay_graphs": [item.to_dict() for item in overlay_graphs],
    }
    if comparison_graph is not None:
        report["comparison_graph"] = comparison_graph.to_dict()
        report["comparison_diff"] = build_graph_diff(graph, comparison_graph)
    return report


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


def write_provider_graph_artifact(
    provider: GraphFakosProvider,
    request: GraphFakosRequest,
    output_path: str,
) -> dict[str, object]:
    graph = load_provider_graph(provider, request)
    return write_graph_artifact(graph, output_path)


__all__ = [
    "build_graph_report",
    "render_embeddable_html",
    "render_graph_markdown_report",
    "render_static_html",
    "write_embeddable_html",
    "write_graph_markdown_report",
    "write_provider_graph_artifact",
    "write_graph_report",
    "write_static_html",
]
