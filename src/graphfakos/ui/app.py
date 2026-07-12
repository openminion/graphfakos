"""Static graph viewer rendering."""

from __future__ import annotations

from html import escape

from graphfakos.browser import viewer_renderer_script, viewer_runtime_script
from graphfakos.models import (
    GraphFakosDiagnostics,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    GraphFakosViewerState,
)
from graphfakos.provider import (
    GraphFakosProvider,
    diagnose_graph,
    load_comparison_graph,
    load_overlay_graphs,
    load_provider_graph,
)
from graphfakos.ui.viewer import panel_stack, render_document, render_graph_workspace
from graphfakos.ui.viewer.controls import (
    _filter_toolbar,
    _workspace_controls,
    _local_graph_controls,
    _physics_display_controls,
    _active_lens_bar,
    _interaction_guide_panel,
)
from graphfakos.ui.viewer.discovery import (
    _command_palette,
    _search_results_panel,
    _expansion_planner_panel,
    _graph_data_table_panel,
    _relationship_data_table_panel,
    _evidence_coverage_map_panel,
    _facet_explorer_panel,
)
from graphfakos.ui.viewer.analysis import (
    _analytics_panel,
    _readability_coach_panel,
    _display_recipes_panel,
    _export_replay_panel,
    _neighborhood_toolbar,
    _path_toolbar,
    _advanced_filter_panel,
    _component_explorer_panel,
    _selection_workbench_panel,
    _style_rules_panel,
    _timeline_animation_panel,
    _investigation_pivot_panel,
    _context_menu_panel,
)
from graphfakos.ui.viewer.navigation import (
    _query_summary,
    _query_syntax_panel,
    _preset_entry,
    _preset_request,
    _preset_rail,
    _selected_node,
    _selected_edge,
    _graph_navigator,
    _navigation_map_panel,
    _relationship_trail_panel,
)
from graphfakos.ui.viewer.authoring import (
    _knowledge_capture_panel,
    _graph_action_panel,
    _focus_workflow,
)
from graphfakos.ui.viewer.evidence import (
    _path_summary,
    _evidence_summary,
)
from graphfakos.ui.viewer.diffing import (
    build_graph_diff,
    _diff_section,
    _overlay_summary,
)
from graphfakos.ui.viewer.canvas import (
    _graph_canvas,
    _explore_href,
    _selection_summary,
    _inspector,
    _node_cards,
    _context_cards,
    _provenance_card,
    _citation_card,
)
from graphfakos.ui.viewer.filtering import (
    _graph_facets,
    _filtered_graph,
    _filter_edges_by_request,
    _active_query_terms,
)
from graphfakos.ui.viewer.graph_ops import (
    _graph_with_items,
    _neighborhood_node_ids,
    _path_nodes,
    _preferred_focus_node,
    _shortest_path_edges,
    _timeline_frames,
)
from graphfakos.ui.viewer.html import (
    badge as _badge,
    badges as _badges,
    empty as _empty,
    json_attribute as _json_attribute,
    json_script as _json_script,
    key_values as _key_values,
    panel as _panel,
    panel_body as _panel_body,
    split as _split,
    summary_note as _summary_note,
    text_list as _list,
)
from graphfakos.ui.viewer.routing import (
    _SCREEN_NAV,
    _request_from_query,
    _route_href,
    _screen_from_path,
    build_viewer_route,
    parse_viewer_request,
    query_syntax_reference,
)
from graphfakos.ui.viewer.styles import viewer_styles


def screen_manifest() -> tuple[dict[str, str], ...]:
    summaries = {
        "explore": "Filter the graph, select nodes, and inspect relationships.",
        "neighborhood": "Expand one focus node to inspect nearby graph structure.",
        "path": "Trace the shortest visible path between two graph nodes.",
        "provenance": "Review provenance records and graph citations together.",
        "timeline": "Scan graph timestamps and freshness-oriented metadata.",
        "diff": "Compare one graph snapshot with a baseline or overlay provider view.",
        "provider_status": "Inspect provider metadata, capabilities, and graph health.",
        "context_preview": "Preview the graph context most likely to be surfaced.",
    }
    return tuple(
        {
            "screen": screen,
            "label": label,
            "route": f"/{screen}",
            "summary": summaries[screen],
        }
        for screen, label in _SCREEN_NAV
    )


def render_provider_path(
    provider: GraphFakosProvider,
    base_request: GraphFakosRequest,
    path: str,
    query: dict[str, list[str]],
) -> str:
    graph, request, comparison_graph, overlay_graphs = _provider_view_context(
        provider,
        base_request,
        path,
        query,
    )
    return render_graph_viewer(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )


def render_provider_path_fragment(
    provider: GraphFakosProvider,
    base_request: GraphFakosRequest,
    path: str,
    query: dict[str, list[str]],
) -> str:
    graph, request, comparison_graph, overlay_graphs = _provider_view_context(
        provider,
        base_request,
        path,
        query,
    )
    return render_graph_fragment(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )


def _provider_view_context(
    provider: GraphFakosProvider,
    base_request: GraphFakosRequest,
    path: str,
    query: dict[str, list[str]],
) -> tuple[
    GraphFakosGraph,
    GraphFakosRequest,
    GraphFakosGraph | None,
    tuple[GraphFakosGraph, ...],
]:
    screen = _screen_from_path(path) or base_request.screen
    request = _request_from_query(base_request.with_screen(screen), query)
    graph = load_provider_graph(provider, request)
    comparison_graph = load_comparison_graph(provider, request)
    overlay_graphs = load_overlay_graphs(provider, request)
    return graph, request, comparison_graph, overlay_graphs


def render_graph_viewer(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None = None,
    overlay_graphs: tuple[GraphFakosGraph, ...] = (),
) -> str:
    body = render_graph_fragment(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )
    return render_document(
        title=graph.label,
        theme=request.theme,
        navigation=_nav(request),
        content=body,
        styles=viewer_styles(),
        script=_viewer_script_tag(),
    )


def review_preset_manifest(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None = None,
) -> tuple[dict[str, str], ...]:
    focus = _preferred_focus_node(graph, request)
    focus_id = focus.id if focus is not None else None
    presets: list[dict[str, str]] = [
        _preset_entry(
            "overview",
            "Overview",
            "Explore the highest-signal graph nodes through the shared force layout.",
            _preset_request(
                request,
                preset_id="overview",
                screen="explore",
                layout="force",
                focus_node_id=focus_id,
            ),
        ),
        _preset_entry(
            "focus",
            "Focus Review",
            "Open a depth-two neighborhood around the current anchor node.",
            _preset_request(
                request,
                preset_id="focus",
                screen="neighborhood",
                layout="focus",
                focus_node_id=focus_id,
                max_depth=2,
            ),
        ),
        _preset_entry(
            "evidence",
            "Evidence",
            "Review provenance and citation coverage before trusting the graph.",
            _preset_request(
                request,
                preset_id="evidence",
                screen="provenance",
                layout="grouped",
            ),
        ),
        _preset_entry(
            "timeline",
            "Timeline",
            "Inspect freshness-oriented timestamps across the current graph snapshot.",
            _preset_request(
                request,
                preset_id="timeline",
                screen="timeline",
                layout="timeline",
            ),
        ),
        _preset_entry(
            "health",
            "Graph Health",
            "Check provider metadata, graph health, and overlay readiness together.",
            _preset_request(
                request,
                preset_id="health",
                screen="provider_status",
            ),
        ),
        _preset_entry(
            "context",
            "Context",
            "Preview the graph items most likely to surface in host context assembly.",
            _preset_request(
                request,
                preset_id="context",
                screen="context_preview",
            ),
        ),
    ]
    if comparison_graph is not None:
        presets.insert(
            4,
            _preset_entry(
                "diff",
                "Diff Review",
                "Compare the current graph against its baseline before export or replay.",
                _preset_request(
                    request,
                    preset_id="diff",
                    screen="diff",
                    comparison_graph_id=(
                        request.comparison_graph_id or comparison_graph.graph_id
                    ),
                ),
            ),
        )
    return tuple(presets)


def render_graph_fragment(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None = None,
    overlay_graphs: tuple[GraphFakosGraph, ...] = (),
) -> str:
    route = _route_href(request)
    body = _render_screen(
        graph,
        request,
        comparison_graph=comparison_graph,
        overlay_graphs=overlay_graphs,
    )
    state_json = _json_attribute(GraphFakosViewerState.from_request(request).to_dict())
    graph_json = _json_attribute(_filtered_graph(graph, request).to_dict())
    developer_panels = (
        f"{_integration_panel(graph, request, comparison_graph, overlay_graphs)}"
        f"{_preset_rail(review_preset_manifest(graph, request, comparison_graph=comparison_graph), request.preset_id)}"
    )
    if request.screen == "explore":
        supplemental = (
            "<details class='gf-developer-tools'><summary>Integration &amp; review presets</summary>"
            f"{developer_panels}</details>"
        )
    else:
        supplemental = developer_panels
    return (
        "<graphfakos-viewer data-graphfakos-component='viewer' "
        f"data-state-json='{state_json}' data-graph-json='{graph_json}' "
        f"render-engine='{escape(request.render_engine)}' theme='{escape(request.theme)}'>"
        "<main class='gf-content gf-embed-root' data-graphfakos-embed='true' "
        f"data-graphfakos-screen='{escape(request.screen)}' "
        f"data-graphfakos-route='{escape(route)}' "
        f"data-graphfakos-preset='{escape(request.preset_id)}'>"
        f"{_header(graph, request, comparison_graph, overlay_graphs)}"
        f"{body}{supplemental}</main></graphfakos-viewer>"
    )


def _viewer_script_tag() -> str:
    return (
        f"<script>\n{viewer_renderer_script()}\n</script>"
        f"<script>\n{viewer_runtime_script()}\n</script>"
    )


def _nav(request: GraphFakosRequest) -> str:
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
        "aria-expanded='true'>☰</button></div>"
        f"<div class='gf-nav-primary'>{primary_links}</div>"
        f"<details class='gf-nav-analysis'{analysis_open}><summary>Analyze</summary>{analysis_links}</details>"
        "</nav>"
    )


def _header(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    overlay_summary = ""
    if overlay_graphs:
        overlay_summary = _badge(f"{len(overlay_graphs)} overlay graph(s)", "blue")
    diff_summary = ""
    if comparison_graph is not None:
        diff_summary = _badge(f"compare {comparison_graph.provider_label}", "neutral")
    snapshot_note = ""
    if graph.snapshot is not None:
        snapshot_note = (
            f"<p class='gf-note'>Snapshot {escape(graph.snapshot.label or graph.snapshot.snapshot_id)}"
            f"{' generated ' + escape(graph.snapshot.created_at) if graph.snapshot.created_at else ''}.</p>"
        )
    return (
        "<header class='gf-header'>"
        "<div><p class='gf-eyebrow'>Graph lens</p>"
        f"<h2>{escape(_screen_title(request.screen))}</h2>"
        f"<p>{escape(graph.label)}</p>"
        f"<p class='gf-note'>{escape(_layout_description(request.layout))}</p>"
        f"{snapshot_note}</div>"
        "<div class='gf-summary'>"
        f"{_badge(graph.graph_role, 'accent')}"
        f"{_badge(f'{len(graph.nodes)} nodes', 'blue')}"
        f"{_badge(f'{len(graph.edges)} edges', 'neutral')}"
        f"{_badge(graph.provider_label, 'neutral')}"
        f"{_badge(f'render:{request.render_engine}', 'neutral')}"
        f"{_badge(f'theme:{request.theme}', 'blue')}"
        f"{diff_summary}{overlay_summary}"
        "</div></header>"
    )


def _screen_title(screen: str) -> str:
    return dict(_SCREEN_NAV).get(screen, "Explore")


def _layout_description(layout: str) -> str:
    labels = {
        "force": "Balanced graph layout for general exploration.",
        "circle": "Circular layout that keeps every node visible.",
        "grouped": "Grouped layout that clusters nodes by kind.",
        "timeline": "Timeline-aware layout for timestamped graph items.",
        "focus": "Focus layout that centers the selected or active node.",
        "radial": "Radial layout that rings nodes around the current focus.",
        "hierarchical": "Layered layout for source-to-artifact review paths.",
    }
    return labels.get(layout, f"{layout.title()} layout.")


def _integration_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    role = _role_description(graph.graph_role)
    capabilities = tuple(graph.capabilities[:4])
    commands = _integration_commands(graph)
    summary = _integration_summary(graph)
    command_list = "".join(f"<code>{escape(command)}</code>" for command in commands)
    deep_link = _route_href(request)
    embed_path = _route_href(
        request, overrides={"render_limit": min(request.render_limit, 60)}
    )
    comparison_note = ""
    if comparison_graph is not None:
        comparison_note = (
            "<p class='gf-note'>"
            f"Diff is available against {escape(comparison_graph.provider_label)}."
            "</p>"
        )
    overlay_note = ""
    if overlay_graphs:
        overlay_note = (
            "<p class='gf-note'>"
            f"{len(overlay_graphs)} overlay provider graph(s) are available for side-by-side review."
            "</p>"
        )
    return (
        "<section class='gf-panel gf-integration' "
        "aria-label='Package integration'>"
        "<div><h3>Integration Commands</h3>"
        f"<p class='gf-empty'>{escape(role)}</p>"
        f"<p>{escape(summary)}</p>"
        "<p class='gf-note'>OpenMinion Integration and other host previews can "
        "reuse the same provider-neutral routes.</p>"
        f"{comparison_note}{overlay_note}"
        f"{_badges([(capability, 'blue') for capability in capabilities])}"
        "</div><div class='gf-code-list'>"
        f"{command_list}"
        f"<code>Deep link: {escape(deep_link)}</code>"
        f"<code>Embed route: {escape(embed_path)}</code>"
        f"<code>Query syntax: {escape(', '.join(item['token'] for item in query_syntax_reference()[:4]))}</code>"
        "</div></section>"
    )


def _role_description(role: str) -> str:
    descriptions = {
        "memory": "Second-brain durable memory graph.",
        "source": "Third-brain observed source graph.",
        "document": "Document knowledge graph.",
        "code": "Code knowledge graph.",
        "artifact": "Artifact knowledge graph.",
        "hybrid": "Hybrid graph lens.",
        "third_party": "Third-party graph provider.",
    }
    return descriptions.get(role, f"{role.replace('_', ' ').title()} graph.")


def _integration_commands(graph: GraphFakosGraph) -> tuple[str, ...]:
    commands = graph.provider_payload.get("integration_commands")
    if isinstance(commands, (list, tuple)) and all(
        isinstance(command, str) for command in commands
    ):
        return tuple(commands)
    return (
        "graphfakos-ui --screen explore --serve --open",
        "graphfakos-ui --screen provider_status --html-out graphfakos-ui-preview.html --json",
    )


def _integration_summary(graph: GraphFakosGraph) -> str:
    summary = graph.provider_payload.get("integration_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    return (
        f"Use these commands to preview the {graph.provider_label} graph through "
        "the shared GraphFakos workbench."
    )


def _render_screen(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    if request.screen == "neighborhood":
        return _render_neighborhood(graph, request)
    if request.screen == "path":
        return _render_path(graph, request)
    if request.screen == "provenance":
        return _render_provenance(graph)
    if request.screen == "timeline":
        return _render_timeline(graph, request)
    if request.screen == "diff":
        return _render_diff(graph, request, comparison_graph, overlay_graphs)
    if request.screen == "provider_status":
        return _render_provider_status(graph, overlay_graphs)
    if request.screen == "context_preview":
        return _render_context_preview(graph)
    return _render_explore(graph, request)


def _render_explore(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    filtered_graph = _filtered_graph(graph, request)
    focus = _selected_node(graph, request, filtered_graph.nodes)
    selected_edge = _selected_edge(graph, request)
    active_query = _active_query_terms(request)
    primary = (
        f"{_graph_canvas(filtered_graph, request, focus.id if focus else None, selected_edge.id if selected_edge else None)}"
        f"{_selection_summary(filtered_graph, focus, selected_edge)}"
        f"{_query_summary(active_query)}"
    )
    secondary = panel_stack(
        (
            _filter_toolbar(graph, request, "/explore"),
            _workspace_controls(graph, request),
            _local_graph_controls(graph, request, focus),
            _physics_display_controls(request),
            _active_lens_bar(graph, filtered_graph, request, focus, selected_edge),
            _interaction_guide_panel(
                graph, filtered_graph, request, focus, selected_edge
            ),
            _graph_navigator(graph, filtered_graph, request, focus),
            _navigation_map_panel(graph, filtered_graph, request, focus, selected_edge),
            _relationship_trail_panel(filtered_graph, request, focus),
            _search_results_panel(filtered_graph, request, focus),
            _graph_data_table_panel(filtered_graph, request),
            _relationship_data_table_panel(filtered_graph, request),
            _evidence_coverage_map_panel(filtered_graph, request),
            _facet_explorer_panel(filtered_graph, request),
            _expansion_planner_panel(filtered_graph, request, focus),
            _command_palette(graph, filtered_graph, request, focus, selected_edge),
            _readability_coach_panel(filtered_graph, request),
            _display_recipes_panel(filtered_graph, request, focus),
            _advanced_filter_panel(filtered_graph, request),
            _component_explorer_panel(graph, request),
            _selection_workbench_panel(filtered_graph, request),
            _style_rules_panel(filtered_graph, request),
            _timeline_animation_panel(graph, request),
            _investigation_pivot_panel(filtered_graph, request, focus),
            _context_menu_panel(request, focus, selected_edge),
            _analytics_panel(graph, request),
            _export_replay_panel(graph, request),
            _focus_workflow(graph, request, focus),
            _knowledge_capture_panel(filtered_graph, request, focus),
            _graph_action_panel(filtered_graph, request, focus),
            _inspector(graph, focus, selected_edge),
            _panel(
                "Visible Nodes",
                _node_cards(filtered_graph.nodes[: request.limit], request),
            ),
        )
    )
    return render_graph_workspace(primary, secondary)


def _render_neighborhood(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    focus = _selected_node(graph, request, tuple(graph.nodes))
    if focus is None:
        return _panel(
            "Neighborhood",
            _empty("No nodes are available for neighborhood expansion."),
        )
    visible_ids = _neighborhood_node_ids(graph, focus.id, max(request.max_depth, 1))
    neighbor_ids = visible_ids - {focus.id}
    neighbors = tuple(node for node in graph.nodes if node.id in neighbor_ids)
    edges = _filter_edges_by_request(
        tuple(
            edge
            for edge in graph.edges
            if edge.source_id in visible_ids and edge.target_id in visible_ids
        ),
        request,
    )
    neighborhood_graph = _graph_with_items(graph, (focus, *neighbors), edges)
    primary = (
        f"{_neighborhood_toolbar(graph, request, focus.id)}"
        f"{_local_graph_controls(graph, request, focus)}"
        f"{_graph_canvas(neighborhood_graph, request, focus.id, request.selected_edge_id)}"
    )
    primary += _panel(
        f"Around {focus.label}",
        f"<p class='gf-empty'>Depth {max(request.max_depth, 1)} neighborhood.</p>"
        f"{_node_cards(neighbors, request) if neighbors else _empty('No neighboring nodes match this view yet.')}",
    )
    secondary = (
        _graph_navigator(graph, neighborhood_graph, request, focus)
        + _relationship_trail_panel(neighborhood_graph, request, focus)
        + _analytics_panel(graph, request)
        + _focus_workflow(graph, request, focus)
        + _knowledge_capture_panel(neighborhood_graph, request, focus)
        + _graph_action_panel(neighborhood_graph, request, focus)
        + _inspector(graph, focus, _selected_edge(graph, request))
    )
    return _split(primary, secondary)


def _render_path(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    source, target = _path_nodes(graph, request)
    if source is None or target is None:
        return _panel(
            "Path",
            _empty(
                "At least two graph nodes are required before a path can be explored."
            ),
        )
    path_edges = _shortest_path_edges(graph, source.id, target.id)
    path_node_ids = {source.id, target.id}
    for edge in path_edges:
        path_node_ids.add(edge.source_id)
        path_node_ids.add(edge.target_id)
    path_nodes = tuple(node for node in graph.nodes if node.id in path_node_ids)
    path_graph = _graph_with_items(graph, path_nodes, tuple(path_edges))
    primary = (
        f"{_path_toolbar(graph, request, source.id, target.id)}"
        f"{_graph_canvas(path_graph, request, source.id, request.selected_edge_id)}"
    )
    primary += _panel(
        f"{source.label} to {target.label}",
        _path_summary(source, target, path_edges),
    )
    secondary = (
        _graph_navigator(graph, path_graph, request, source)
        + _relationship_trail_panel(path_graph, request, source)
        + _analytics_panel(graph, request)
        + _focus_workflow(graph, request, source)
        + _knowledge_capture_panel(path_graph, request, source)
        + _graph_action_panel(path_graph, request, source)
        + _inspector(graph, source, _selected_edge(graph, request))
    )
    return _split(primary, secondary)


def _render_provenance(graph: GraphFakosGraph) -> str:
    items = "".join(_provenance_card(item) for item in graph.provenance)
    citations = "".join(_citation_card(citation) for citation in graph.citations)
    return _split(
        _panel(
            "Provenance",
            _summary_note(
                f"{len(graph.provenance)} provenance record(s) support this graph view."
            )
            + (items or _empty("No provenance provided.")),
        ),
        _panel("Evidence Coverage", _evidence_summary(graph))
        + _panel(
            "Citations",
            _summary_note(
                f"{len(graph.citations)} citation reference(s) are available."
            )
            + (citations or _empty("No citations provided.")),
        ),
    )


def _render_timeline(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    events = _timeline_event_payloads(graph, request)
    visible_events = [
        event
        for event in events
        if not request.timeline_frame or event["value"] == request.timeline_frame
    ]
    return _panel(
        "Timeline and Freshness",
        _summary_note(
            f"{len(visible_events)} of {len(events)} timestamp event(s) are visible across {len(graph.nodes)} node(s)."
        )
        + _timeline_frame_rail(graph, request)
        + _timeline_event_cards(visible_events)
        + _json_script(
            "data-gf-timeline-events",
            {
                "events": visible_events,
                "selected_frame": request.timeline_frame,
                "playback": request.timeline_playback,
            },
        ),
    )


def _timeline_event_payloads(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for node in graph.nodes:
        for field, value in sorted(node.timestamps.items()):
            events.append(
                {
                    "node_id": node.id,
                    "label": node.label,
                    "kind": node.kind,
                    "field": field,
                    "value": value,
                    "route": _route_href(
                        request.with_screen("timeline"),
                        overrides={
                            "timeline_frame": value,
                            "timeline_playback": "step",
                            "focus_node_id": node.id,
                        },
                    ),
                    "focus_route": _explore_href(request, focus_node_id=node.id),
                    "case_packet_route": _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "pivot_node_id": node.id,
                            "pivot_mode": "timeline",
                        },
                    ),
                }
            )
    return sorted(
        events,
        key=lambda event: (
            event["value"],
            event["label"].casefold(),
            event["field"],
        ),
    )


def _timeline_frame_rail(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    frames = _timeline_frames(graph)
    if not frames:
        return _empty("No timeline frames are available.")
    links = [
        (
            "<a class='gf-route-chip' "
            f"data-active='{str(frame == request.timeline_frame).lower()}' "
            f"href='{escape(_route_href(request.with_screen('timeline'), overrides={'timeline_frame': frame, 'timeline_playback': 'step'}))}'>"
            f"{escape(frame)}</a>"
        )
        for frame in frames
    ]
    return (
        "<div class='gf-timeline-rail' data-gf-timeline-rail='true'>"
        + "".join(links)
        + "</div>"
    )


def _timeline_event_cards(events: list[dict[str, str]]) -> str:
    if not events:
        return _empty("No events match the selected timeline frame.")
    html = "<div class='gf-timeline-grid' data-gf-timeline-cards='true'>"
    for event in events:
        html += (
            "<article class='gf-card gf-timeline-card'>"
            f"<h4>{escape(event['label'])}</h4>"
            + _badges(
                [
                    (event["kind"], "accent"),
                    (event["field"], "blue"),
                    (event["value"], "neutral"),
                ]
            )
            + "<div class='gf-route-row'>"
            + f"<div>Open frame</div><a class='gf-inline-link' href='{escape(event['route'])}'>Open</a></div>"
            + "<div class='gf-route-row'>"
            + f"<div>Focus node</div><a class='gf-inline-link' href='{escape(event['focus_route'])}'>Open</a></div>"
            + "<div class='gf-route-row'>"
            + f"<div>Timeline case packet</div><a class='gf-inline-link' href='{escape(event['case_packet_route'])}'>Open</a></div>"
            + "</article>"
        )
    return f"{html}</div>"


def _render_diff(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    comparison_graph: GraphFakosGraph | None,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    if comparison_graph is None:
        return _split(
            _panel(
                "Snapshot Diff",
                _empty("This provider does not expose a comparison snapshot yet."),
            ),
            _panel("Overlay Providers", _overlay_summary(overlay_graphs)),
        )
    diff = build_graph_diff(graph, comparison_graph)
    body = (
        _summary_note(
            f"Comparing {graph.provider_label} against {comparison_graph.provider_label}."
        )
        + _badges(
            (
                (f"{diff['summary']['added node count']} added nodes", "accent"),
                (f"{diff['summary']['removed node count']} removed nodes", "neutral"),
                (f"{diff['summary']['changed node count']} changed nodes", "blue"),
                (f"{diff['summary']['changed edge count']} changed edges", "blue"),
            )
        )
        + _key_values(diff["summary"])
        + _diff_change_workbench(graph, comparison_graph, request, diff)
        + _diff_section("Change Hotspots", diff["change_hotspots"])
        + _diff_section("Added nodes", diff["added_nodes"])
        + _diff_section("Removed nodes", diff["removed_nodes"])
        + _diff_section("Changed nodes", diff["changed_nodes"])
        + _diff_section("Added edges", diff["added_edges"])
        + _diff_section("Removed edges", diff["removed_edges"])
        + _diff_section("Changed edges", diff["changed_edges"])
        + _diff_section("Snapshot changes", diff["snapshot_changes"])
    )
    left = _panel(
        "Snapshot Diff",
        body,
    )
    right = _panel("Overlay Providers", _overlay_summary(overlay_graphs))
    return _split(left, right)


def _diff_change_workbench(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    diff: dict[str, object],
) -> str:
    changes = _diff_change_payloads(graph, comparison_graph, request, diff)
    if not changes:
        return _empty("No route-backed diff changes are available.")
    return (
        "<section class='gf-diff-workbench' data-gf-diff-workbench='true'>"
        "<h4>Diff Review Workbench</h4>"
        + _diff_change_cards(changes)
        + _json_script(
            "data-gf-diff-workbench",
            {
                "changes": changes,
                "current_graph_id": graph.graph_id,
                "comparison_graph_id": comparison_graph.graph_id,
            },
        )
        + "</section>"
    )


def _diff_change_payloads(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    diff: dict[str, object],
) -> list[dict[str, object]]:
    node_map = graph.node_map()
    comparison_node_map = comparison_graph.node_map()
    edge_map = graph.edge_map()
    comparison_edge_map = comparison_graph.edge_map()
    changes: list[dict[str, object]] = []

    for node_id in _string_items(diff.get("added_nodes")):
        node = node_map.get(node_id)
        if node is not None:
            changes.append(_diff_node_change("added_node", node, request))
    for node_id in _string_items(diff.get("removed_nodes")):
        node = comparison_node_map.get(node_id)
        if node is not None:
            changes.append(_diff_node_change("removed_node", node, request))
    for detail in _dict_items(diff.get("changed_node_details")):
        node_id = str(detail.get("id", ""))
        node = node_map.get(node_id) or comparison_node_map.get(node_id)
        if node is not None:
            changes.append(
                _diff_node_change(
                    "changed_node",
                    node,
                    request,
                    fields=_string_items(detail.get("fields")),
                )
            )

    for edge_id in _string_items(diff.get("added_edges")):
        edge = edge_map.get(edge_id)
        if edge is not None:
            changes.append(_diff_edge_change("added_edge", edge, graph, request))
    for edge_id in _string_items(diff.get("removed_edges")):
        edge = comparison_edge_map.get(edge_id)
        if edge is not None:
            changes.append(
                _diff_edge_change("removed_edge", edge, comparison_graph, request)
            )
    for detail in _dict_items(diff.get("changed_edge_details")):
        edge_id = str(detail.get("id", ""))
        edge = edge_map.get(edge_id) or comparison_edge_map.get(edge_id)
        owner_graph = graph if edge_id in edge_map else comparison_graph
        if edge is not None:
            changes.append(
                _diff_edge_change(
                    "changed_edge",
                    edge,
                    owner_graph,
                    request,
                    fields=_string_items(detail.get("fields")),
                )
            )

    for item in _string_items(diff.get("snapshot_changes")):
        changes.append(
            {
                "change_type": "snapshot",
                "item_type": "snapshot",
                "id": "snapshot",
                "label": item,
                "fields": [],
                "route": _route_href(request.with_screen("diff")),
            }
        )
    return changes[:12]


def _diff_node_change(
    change_type: str,
    node: GraphFakosNode,
    request: GraphFakosRequest,
    *,
    fields: list[str] | None = None,
) -> dict[str, object]:
    return {
        "change_type": change_type,
        "item_type": "node",
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "fields": fields or [],
        "route": _explore_href(request, focus_node_id=node.id),
        "case_packet_route": _route_href(
            request.with_screen("explore"),
            overrides={"pivot_node_id": node.id, "pivot_mode": "evidence_bundle"},
        ),
    }


def _diff_edge_change(
    change_type: str,
    edge: GraphFakosEdge,
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    *,
    fields: list[str] | None = None,
) -> dict[str, object]:
    node_map = graph.node_map()
    source = node_map.get(edge.source_id)
    target = node_map.get(edge.target_id)
    label = (
        f"{source.label if source else edge.source_id} -> "
        f"{target.label if target else edge.target_id}"
    )
    return {
        "change_type": change_type,
        "item_type": "edge",
        "id": edge.id,
        "label": label,
        "kind": edge.kind,
        "fields": fields or [],
        "route": _route_href(
            request.with_screen("path"),
            overrides={
                "source_node_id": edge.source_id,
                "target_node_id": edge.target_id,
                "selected_edge_id": edge.id,
                "layout": "focus",
            },
        ),
        "source_route": _explore_href(request, focus_node_id=edge.source_id),
        "target_route": _explore_href(request, focus_node_id=edge.target_id),
    }


def _diff_change_cards(changes: list[dict[str, object]]) -> str:
    html = "<div class='gf-diff-grid' data-gf-diff-cards='true'>"
    for change in changes:
        fields = change.get("fields")
        field_text = ", ".join(fields) if isinstance(fields, list) else ""
        case_packet_route = change.get("case_packet_route")
        source_route = change.get("source_route")
        target_route = change.get("target_route")
        extra_routes = ""
        if isinstance(case_packet_route, str):
            extra_routes += (
                "<div class='gf-route-row'>"
                f"<div>Case packet</div><a class='gf-inline-link' href='{escape(case_packet_route)}'>Open</a></div>"
            )
        if isinstance(source_route, str):
            extra_routes += (
                "<div class='gf-route-row'>"
                f"<div>Source node</div><a class='gf-inline-link' href='{escape(source_route)}'>Open</a></div>"
            )
        if isinstance(target_route, str):
            extra_routes += (
                "<div class='gf-route-row'>"
                f"<div>Target node</div><a class='gf-inline-link' href='{escape(target_route)}'>Open</a></div>"
            )
        html += (
            "<article class='gf-card gf-diff-card'>"
            f"<h4>{escape(str(change.get('label', change.get('id', 'change'))))}</h4>"
            + _badges(
                [
                    (str(change.get("change_type", "change")), "accent"),
                    (str(change.get("item_type", "item")), "blue"),
                    (str(change.get("kind", "")), "neutral"),
                ]
            )
            + (f"<p>Fields: {escape(field_text)}</p>" if field_text else "")
            + "<div class='gf-route-row'>"
            + f"<div>Review change</div><a class='gf-inline-link' href='{escape(str(change.get('route', '#')))}'>Open</a></div>"
            + extra_routes
            + "</article>"
        )
    return f"{html}</div>"


def _string_items(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, str)]


def _dict_items(value: object) -> list[dict[str, object]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, dict)]


def _render_provider_status(
    graph: GraphFakosGraph,
    overlay_graphs: tuple[GraphFakosGraph, ...],
) -> str:
    diagnostics = diagnose_graph(graph)
    status = {
        "provider_id": graph.provider_id,
        "provider_label": graph.provider_label,
        "graph_role": graph.graph_role,
        "capabilities": ", ".join(graph.capabilities),
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "provenance": len(graph.provenance),
        "citations": len(graph.citations),
        "generated_at": graph.generated_at,
    }
    if graph.snapshot is not None:
        status["snapshot"] = graph.snapshot.label or graph.snapshot.snapshot_id
        status["snapshot_created_at"] = graph.snapshot.created_at
    return _split(
        _panel(
            "Provider Status",
            _key_values(status)
            + _provider_details(graph)
            + _capability_details(graph)
            + _facet_details(graph),
        ),
        _panel("Graph Health", _graph_health(diagnostics))
        + _analytics_panel(graph, GraphFakosRequest(screen="provider_status"))
        + _panel(
            "Sample Nodes",
            _node_cards(graph.nodes[:5], GraphFakosRequest(screen="provider_status")),
        )
        + _panel("Overlay Providers", _overlay_summary(overlay_graphs))
        + _panel("Query Syntax", _query_syntax_panel())
        + _panel("Warnings", _list(graph.warnings)),
    )


def _graph_health(diagnostics: GraphFakosDiagnostics) -> str:
    tone = "accent" if diagnostics.healthy else "blue"
    summary = _badges(
        (
            ("healthy" if diagnostics.healthy else "needs review", tone),
            (f"{diagnostics.node_count} nodes", "neutral"),
            (f"{diagnostics.edge_count} edges", "neutral"),
        )
    ) + _key_values(
        {
            "provenance": diagnostics.provenance_count,
            "citations": diagnostics.citation_count,
            "orphan nodes": len(diagnostics.orphan_node_ids),
            "duplicate edges": len(diagnostics.duplicate_edge_ids),
            "unknown provenance refs": len(diagnostics.unknown_provenance_ids),
            "unknown citation refs": len(diagnostics.unknown_citation_ids),
            "self-loop edges": len(diagnostics.self_loop_edge_ids),
            "secondary-component nodes": len(diagnostics.disconnected_node_ids),
        }
    )
    details = (
        _diagnostic_list("Orphan nodes", diagnostics.orphan_node_ids)
        + _diagnostic_list("Duplicate edge ids", diagnostics.duplicate_edge_ids)
        + _diagnostic_list("Unknown provenance ids", diagnostics.unknown_provenance_ids)
        + _diagnostic_list("Unknown citation ids", diagnostics.unknown_citation_ids)
        + _diagnostic_list("Self-loop edge ids", diagnostics.self_loop_edge_ids)
        + _diagnostic_list(
            "Secondary-component nodes",
            diagnostics.disconnected_node_ids,
        )
    )
    return summary + (details or _empty("No graph diagnostics."))


def _diagnostic_list(title: str, items: tuple[str, ...]) -> str:
    if not items:
        return ""
    return f"<h4>{escape(title)}</h4>{_list(items)}"


def _render_context_preview(graph: GraphFakosGraph) -> str:
    ranked_nodes = tuple(
        sorted(
            graph.nodes,
            key=lambda item: item.score if item.score is not None else 0,
            reverse=True,
        )[:8]
    )
    return _split(
        _panel(
            "Context Assembly Preview",
            _summary_note(
                f"Top {len(ranked_nodes)} node(s) are ranked for reusable viewer context."
            )
            + _context_cards(ranked_nodes, GraphFakosRequest(screen="context_preview")),
        ),
        _panel(
            "Provider Contribution",
            _key_values(
                {
                    "provider": graph.provider_label,
                    "role": graph.graph_role,
                    "capabilities": ", ".join(graph.capabilities),
                    "warnings": len(graph.warnings),
                }
            ),
        ),
    )


def _provider_details(graph: GraphFakosGraph) -> str:
    if not graph.provider_details:
        return ""
    return _panel_body("Provider Details", _key_values(graph.provider_details))


def _capability_details(graph: GraphFakosGraph) -> str:
    if not graph.capability_details:
        return ""
    items = [
        f"{capability}: {description}"
        for capability, description in graph.capability_details.items()
    ]
    return _panel_body("Capability Notes", _list(items))


def _facet_details(graph: GraphFakosGraph) -> str:
    facets = graph.available_facets or _graph_facets(graph)
    if not facets:
        return ""
    items = [
        f"{name}: {', '.join(values[:5])}" for name, values in facets.items() if values
    ]
    return _panel_body("Available Facets", _list(items))


__all__ = [
    "build_graph_diff",
    "build_viewer_route",
    "parse_viewer_request",
    "query_syntax_reference",
    "render_graph_fragment",
    "render_graph_viewer",
    "render_provider_path",
    "review_preset_manifest",
    "screen_manifest",
]
