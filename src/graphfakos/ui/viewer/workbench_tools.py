"""Compact graph-surface tools for provider input, selection, and analysis."""

from __future__ import annotations

from html import escape
from math import ceil
from dataclasses import replace

from graphfakos.models import GraphFakosGraph, GraphFakosNode, GraphFakosRequest
from graphfakos.ui.viewer.graph_ops import _node_degree_map
from graphfakos.ui.viewer.routing import _route_href
from graphfakos.viewer_contracts import (
    GraphFakosPerspective,
    graph_perspectives,
    inspector_schema_for,
    inspector_values,
)


def canvas_workbench(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    return (
        "<section class='gf-canvas-workbench' aria-label='Graph workbench'>"
        f"{_selection_tools(request)}"
        f"{_distribution_tools(graph)}"
        f"{_perspective_tools(graph, request)}"
        f"{_import_tools()}"
        "</section>"
    )


def density_tuned_request(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> GraphFakosRequest:
    total_nodes = int(
        graph.stats.get("raw_node_count", len(graph.nodes)) or len(graph.nodes)
    )
    visible_nodes = len(graph.nodes)
    node_scale = request.node_scale
    label_density = request.label_density
    edge_opacity = request.edge_opacity
    if request.node_scale == 1.0 and total_nodes >= 100_000:
        node_scale = 0.42
    elif request.node_scale == 1.0 and visible_nodes >= 160:
        node_scale = 0.58
    if request.label_density == 1.0 and total_nodes >= 100_000:
        label_density = 0.3
    elif request.label_density == 1.0 and visible_nodes >= 160:
        label_density = 0.48
    if request.edge_opacity == 1.0 and (total_nodes >= 100_000 or visible_nodes >= 160):
        edge_opacity = 0.62
    if (node_scale, label_density, edge_opacity) == (
        request.node_scale,
        request.label_density,
        request.edge_opacity,
    ):
        return request
    return replace(
        request,
        node_scale=node_scale,
        label_density=label_density,
        edge_opacity=edge_opacity,
    )


def focus_locator() -> str:
    return (
        "<button type='button' class='gf-focus-locator' data-gf-focus-locator='true' "
        "hidden aria-label='Selected node is outside the current view'>"
        "<span aria-hidden='true'>&rarr;</span><strong data-gf-focus-locator-label>Focus</strong>"
        "</button>"
    )


def performance_hud() -> str:
    return (
        "<details class='gf-performance-hud' data-gf-performance-hud='true'>"
        "<summary>Performance</summary><dl>"
        "<div><dt>FPS</dt><dd data-gf-perf-fps>--</dd></div>"
        "<div><dt>Frame</dt><dd><span data-gf-perf-frame>--</span> ms</dd></div>"
        "<div><dt>Visible</dt><dd data-gf-perf-visible>--</dd></div>"
        "<div><dt>Links</dt><dd data-gf-perf-links>--</dd></div>"
        "<div><dt>Detail</dt><dd data-gf-perf-detail>--</dd></div>"
        "</dl></details>"
    )


def provider_inspector_fields(graph: GraphFakosGraph, node: GraphFakosNode) -> str:
    schema = inspector_schema_for(graph, node)
    if schema is None:
        return ""
    rows = "".join(
        "<div class='gf-provider-field'>"
        f"<dt>{escape(label)}</dt><dd>{escape(_display_value(value))}</dd>"
        "</div>"
        for label, value in inspector_values(node, schema).items()
    )
    return (
        "<section class='gf-provider-inspector' "
        f"data-schema-id='{escape(schema.schema_id)}'>"
        f"<h3>{escape(schema.schema_id)}</h3><dl>{rows}</dl></section>"
    )


def _selection_tools(_request: GraphFakosRequest) -> str:
    actions = (
        ("incoming", "Incoming", "Select incoming neighbors"),
        ("outgoing", "Outgoing", "Select outgoing neighbors"),
        ("expand", "Load details", "Ask the provider for a bounded drill-down"),
        ("only", "Only", "Show only this selection"),
        ("exclude", "Exclude", "Hide this selection"),
        ("dismiss", "Dismiss others", "Keep the selection and its connections"),
        ("invert", "Invert", "Select every other visible node"),
        ("restore", "Restore", "Restore the current provider graph"),
    )
    buttons = "".join(
        f"<button type='button' data-gf-selection-action='{action}' title='{title}'"
        f">{label}</button>"
        for action, label, title in actions
    )
    return (
        "<details class='gf-workbench-tool' open><summary>Selection</summary>"
        f"<div class='gf-tool-row'>{buttons}</div>"
        "<p data-gf-selection-workflow-status aria-live='polite'>Select a node to reveal connected workflows.</p>"
        "</details>"
    )


def _distribution_tools(graph: GraphFakosGraph) -> str:
    degrees = _node_degree_map(graph)
    degree_values = {node.id: float(degrees.get(node.id, 0)) for node in graph.nodes}
    score_values = {
        node.id: float(node.score) for node in graph.nodes if node.score is not None
    }
    return (
        "<details class='gf-workbench-tool'><summary>Distributions</summary>"
        "<p>Drag or click bins to select linked nodes.</p>"
        f"{_histogram('degree', degree_values)}"
        f"{_histogram('score', score_values)}"
        "</details>"
    )


def _histogram(key: str, values: dict[str, float]) -> str:
    if not values:
        return f"<div class='gf-histogram'><strong>{escape(key.title())}</strong><span>No values</span></div>"
    minimum = min(values.values())
    maximum = max(values.values())
    width = max((maximum - minimum) / 8, 1 if key == "degree" else 0.01)
    bins: list[tuple[float, float, int]] = []
    for index in range(8):
        lower = minimum + width * index
        upper = maximum + width if index == 7 else minimum + width * (index + 1)
        count = sum(lower <= value < upper for value in values.values())
        bins.append((lower, upper, count))
    tallest = max(count for _, _, count in bins) or 1
    bars = "".join(
        "<button type='button' class='gf-histogram-bin' "
        f"data-gf-distribution='{escape(key)}' data-min='{lower:.4f}' data-max='{upper:.4f}' "
        f"style='--bar:{ceil(count / tallest * 100)}%' "
        f"title='{count} nodes from {lower:.2f} to {upper:.2f}' "
        f"aria-label='{count} {escape(key)} values from {lower:.2f} to {upper:.2f}'><span>{count}</span></button>"
        for lower, upper, count in bins
    )
    return (
        f"<div class='gf-histogram' data-gf-histogram='{escape(key)}'>"
        f"<strong>{escape(key.title())}</strong><div>{bars}</div></div>"
    )


def _perspective_tools(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    perspectives = (*_default_perspectives(), *graph_perspectives(graph))
    links = "".join(_perspective_link(item, request) for item in perspectives)
    return (
        "<details class='gf-workbench-tool'><summary>Perspectives</summary>"
        f"<div class='gf-perspective-list'>{links}</div>"
        "<div class='gf-tool-row'><button type='button' data-gf-perspective-save>Save current</button>"
        "<button type='button' data-gf-perspective-manage>Saved views</button></div>"
        "<div data-gf-local-perspectives></div></details>"
    )


def _default_perspectives() -> tuple[GraphFakosPerspective, ...]:
    return (
        GraphFakosPerspective("structure", "Structure", "Cluster and degree view"),
        GraphFakosPerspective(
            "evidence",
            "Evidence",
            "Provenance-first review",
            filters={"evidence_filter": "with_evidence"},
            style_color_by="source",
            style_size_by="confidence",
        ),
        GraphFakosPerspective(
            "precision",
            "Precision",
            "High-detail local investigation",
            layout="focus",
            style_size_by="confidence",
        ),
    )


def _perspective_link(
    perspective: GraphFakosPerspective,
    request: GraphFakosRequest,
) -> str:
    overrides: dict[str, object] = {
        "layout": perspective.layout,
        "render_engine": perspective.render_engine,
        "style_color_by": perspective.style_color_by,
        "style_size_by": perspective.style_size_by,
        "style_edge_width_by": perspective.style_edge_width_by,
        **perspective.filters,
    }
    if perspective.node_kinds:
        overrides["node_kind"] = perspective.node_kinds[0]
    if perspective.edge_kinds:
        overrides["edge_kind"] = perspective.edge_kinds[0]
    route = _route_href(request.with_screen("explore"), overrides=overrides)
    return (
        f"<a href='{escape(route)}' data-perspective-id='{escape(perspective.perspective_id)}'>"
        f"<strong>{escape(perspective.label)}</strong><span>{escape(perspective.summary)}</span></a>"
    )


def _import_tools() -> str:
    return (
        "<details class='gf-workbench-tool'><summary>Open data</summary>"
        "<form data-gf-import-form><label>JSON format<select name='format'>"
        "<option value='provider_envelope'>Provider envelope</option>"
        "<option value='graph_artifact'>Graph artifact</option></select></label>"
        "<label>File<input type='file' name='file' accept='application/json,.json' required></label>"
        "<button type='submit'>Open graph</button></form>"
        "<p data-gf-import-status aria-live='polite'>Files stay in this local preview process.</p>"
        "</details>"
    )


def _display_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{key}: {item}" for key, item in value.items())
    return str(value)


__all__ = [
    "canvas_workbench",
    "density_tuned_request",
    "focus_locator",
    "performance_hud",
    "provider_inspector_fields",
]
