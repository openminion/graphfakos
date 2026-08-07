"""Explore-screen tool composition."""

from __future__ import annotations

from html import escape

from graphfakos.models import (
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
)
from graphfakos.ui.viewer import panel_stack
from graphfakos.ui.viewer.analysis import (
    _advanced_filter_panel,
    _analytics_panel,
    _component_explorer_panel,
    _context_menu_panel,
    _display_recipes_panel,
    _export_replay_panel,
    _investigation_pivot_panel,
    _readability_coach_panel,
    _selection_workbench_panel,
    _style_rules_panel,
    _timeline_animation_panel,
)
from graphfakos.ui.viewer.authoring import (
    _graph_action_panel,
    _knowledge_capture_panel,
)
from graphfakos.ui.viewer.canvas import _inspector, _node_cards
from graphfakos.ui.viewer.controls import (
    _active_lens_bar,
    _filter_toolbar,
    _interaction_guide_panel,
    _local_graph_controls,
    _physics_display_controls,
    _workspace_controls,
)
from graphfakos.ui.viewer.discovery import (
    _command_palette,
    _evidence_coverage_map_panel,
    _expansion_planner_panel,
    _facet_explorer_panel,
    _graph_data_table_panel,
    _relationship_data_table_panel,
    _search_results_panel,
)
from graphfakos.ui.viewer.html import (
    badges as _badges,
    empty as _empty,
    key_values as _key_values,
    panel as _panel,
    panel_body as _panel_body,
    summary_note as _summary_note,
)
from graphfakos.ui.viewer.navigation import (
    _graph_navigator,
    _navigation_map_panel,
    _relationship_trail_panel,
)
from graphfakos.viewer_contracts import workspace_manifest_for_graph


def explore_context(
    graph: GraphFakosGraph,
    filtered_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    """Render Explore tools in product-first groups instead of one long drawer."""
    return panel_stack(
        (
            _filter_toolbar(graph, request, "/explore"),
            _local_graph_controls(graph, request, focus),
            _active_lens_bar(graph, filtered_graph, request, focus, selected_edge),
            _provider_readiness_panel(graph, request),
            _graph_navigator(graph, filtered_graph, request, focus),
            _inspector(graph, focus, selected_edge),
            _knowledge_capture_panel(filtered_graph, request, focus),
            _graph_action_panel(filtered_graph, request, focus),
            _review_group(graph, filtered_graph, request, focus, selected_edge),
            _display_group(graph, filtered_graph, request, focus),
            _data_group(graph, filtered_graph, request, focus, selected_edge),
        )
    )


def _provider_readiness_panel(
    graph: GraphFakosGraph, request: GraphFakosRequest
) -> str:
    manifest = workspace_manifest_for_graph(graph, request)
    status = manifest.provider_status
    budget = manifest.performance_budget
    details = {
        "Provider": str(status.get("provider_label") or graph.provider_label),
        "Role": str(status.get("graph_role") or graph.graph_role),
        "Graph": graph.label,
        "Route": manifest.desktop_backend_path,
        "Manifest": manifest.schema_version,
    }
    if budget is not None:
        details["Visible"] = (
            f"{budget.rendered_node_count} nodes / {budget.rendered_edge_count} edges"
        )
        details["Source"] = (
            f"{budget.raw_node_count} nodes / {budget.raw_edge_count} edges"
        )
        details["Detail"] = budget.level_of_detail

    body = _key_values(details)
    body += _badge_panel(
        "Capabilities",
        _string_items(status.get("capabilities")),
        "neutral",
        "No provider capabilities declared.",
    )
    body += _badge_panel(
        "Viewer Actions",
        manifest.viewer_actions,
        "accent",
        "No viewer actions declared.",
    )
    body += _badge_panel(
        "Provider Actions",
        manifest.supported_actions + manifest.supported_captures,
        "success",
        "No provider-backed actions declared.",
    )
    facet_summaries = _facet_summaries(status.get("available_facets"))
    if facet_summaries:
        body += _panel_body(
            "Facets", _badges(tuple((item, "neutral") for item in facet_summaries))
        )
    warning_items = _string_items(status.get("warnings"))
    if warning_items:
        body += _panel_body(
            "Warnings", _badges(tuple((item, "warning") for item in warning_items[:3]))
        )
    if manifest.empty_state:
        message = str(manifest.empty_state.get("message") or "No visible graph data.")
        body += _panel_body("Empty State", _summary_note(message))
    return _panel("Provider Readiness", body)


def _badge_panel(
    title: str,
    items: tuple[str, ...],
    tone: str,
    empty_text: str,
) -> str:
    if not items:
        return _panel_body(title, _empty(empty_text))
    return _panel_body(title, _badges(tuple((item, tone) for item in items)))


def _string_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if item not in (None, ""))


def _facet_summaries(value: object) -> tuple[str, ...]:
    if not isinstance(value, dict):
        return ()
    summaries: list[str] = []
    for key, values in sorted(value.items()):
        count = len(values) if isinstance(values, (list, tuple)) else 0
        summaries.append(f"{key} ({count})")
    return tuple(summaries[:6])


def _review_group(
    graph: GraphFakosGraph,
    filtered_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    return _tool_group(
        "Review",
        "Evidence, relationships, analytics, and case-building helpers.",
        panel_stack(
            (
                _interaction_guide_panel(
                    graph, filtered_graph, request, focus, selected_edge
                ),
                _navigation_map_panel(
                    graph, filtered_graph, request, focus, selected_edge
                ),
                _relationship_trail_panel(filtered_graph, request, focus),
                _evidence_coverage_map_panel(filtered_graph, request),
                _component_explorer_panel(graph, request),
                _analytics_panel(graph, request),
                _readability_coach_panel(filtered_graph, request),
                _investigation_pivot_panel(filtered_graph, request, focus),
                _export_replay_panel(graph, request),
            )
        ),
        open_by_default=bool(focus or selected_edge),
    )


def _display_group(
    graph: GraphFakosGraph,
    filtered_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    return _tool_group(
        "Display",
        "Saved views, physics, filters, styling, and timeline controls.",
        panel_stack(
            (
                _workspace_controls(graph, request),
                _physics_display_controls(request),
                _advanced_filter_panel(filtered_graph, request),
                _facet_explorer_panel(filtered_graph, request),
                _style_rules_panel(filtered_graph, request),
                _timeline_animation_panel(graph, request),
                _display_recipes_panel(filtered_graph, request, focus),
            )
        ),
    )


def _data_group(
    graph: GraphFakosGraph,
    filtered_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    return _tool_group(
        "Data",
        "Tables, expansion planning, command palette, and visible nodes.",
        panel_stack(
            (
                _search_results_panel(filtered_graph, request, focus),
                _expansion_planner_panel(filtered_graph, request, focus),
                _command_palette(graph, filtered_graph, request, focus, selected_edge),
                _selection_workbench_panel(filtered_graph, request),
                _context_menu_panel(request, focus, selected_edge),
                _graph_data_table_panel(filtered_graph, request),
                _relationship_data_table_panel(filtered_graph, request),
                _panel(
                    "Visible Nodes",
                    _node_cards(filtered_graph.nodes[: request.limit], request),
                ),
            )
        ),
    )


def _tool_group(
    title: str,
    summary: str,
    body: str,
    *,
    open_by_default: bool = False,
) -> str:
    if not body:
        return ""
    open_attr = " open" if open_by_default else ""
    return (
        f"<details class='gf-tool-group'{open_attr}>"
        f"<summary><strong>{escape(title)}</strong><span>{escape(summary)}</span></summary>"
        f"<div>{body}</div></details>"
    )


__all__ = ["explore_context"]
