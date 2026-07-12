"""Search, expansion, graph tables, evidence coverage, and facet discovery panels."""

from __future__ import annotations

from html import escape
import shlex

from graphfakos.models import (
    GraphFakosEdge,
    GraphFakosExpansionRequest,
    GraphFakosGraph,
    GraphFakosNode,
    GraphFakosRequest,
    GraphFakosSavedQuery,
)
from graphfakos.ui.viewer.canvas import (
    _explore_href,
    _node_value_counts,
    _sorted_counts,
)
from graphfakos.ui.viewer.filtering import _node_contains_text, _parse_query
from graphfakos.ui.viewer.graph_ops import (
    _node_component_ids,
    _node_degree_map,
    _navigation_path_pair,
    _preferred_focus_node,
    _ranked_nodes,
    _shortest_path_edges,
)
from graphfakos.ui.viewer.html import (
    badges as _badges,
    empty as _empty,
    html_list as _html_list,
    json_script as _json_script,
    key_values as _key_values,
    panel as _panel,
    panel_body as _panel_body,
    select as _select,
    select_pairs as _select_pairs,
    summary_note as _summary_note,
    text_list as _list,
)
from graphfakos.ui.viewer.routing import (
    _route_href,
    state_hidden_inputs as _state_hidden_inputs,
)


def _command_palette(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> str:
    payload = _command_palette_payload(
        graph,
        visible_graph,
        request,
        focus,
        selected_edge,
    )
    query_errors = _query_errors(request.query)
    error_html = (
        _panel_body("Query Validation", _list(query_errors))
        if query_errors
        else _summary_note("Query validation passed; current graph state is preserved.")
    )
    return _panel(
        "Command Palette",
        _summary_note(
            "Search, jump, review evidence, open local graph lenses, or start provider-neutral authoring from one static-friendly command surface."
        )
        + "<section class='gf-command-palette' data-gf-command-palette-panel='true'>"
        + "<label class='gf-command-search'>Quick action search"
        "<input data-gf-command-search='true' data-gf-command-palette-search='true' "
        "placeholder='Try evidence, local, author, export...'></label>"
        f"{_command_palette_groups(payload['groups'])}"
        "<p class='gf-command-status' data-gf-command-palette-status='true' aria-live='polite'></p>"
        "</section>"
        + error_html
        + _json_script("data-gf-saved-queries", payload["saved_queries"])
        + _json_script("data-gf-command-palette", payload),
    )


def _command_palette_payload(
    graph: GraphFakosGraph,
    visible_graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
    selected_edge: GraphFakosEdge | None,
) -> dict[str, object]:
    saved_queries = (
        GraphFakosSavedQuery("hubs", "Hubs", "has:score", {"min_score": "0.8"}),
        GraphFakosSavedQuery("evidence", "Evidence", "has:provenance"),
        GraphFakosSavedQuery("warnings", "Warnings", "kind:warning"),
    )
    anchor = focus or _preferred_focus_node(visible_graph, request)
    source_node, target_node = _navigation_path_pair(
        graph, visible_graph, selected_edge
    )
    source_id = source_node.id if source_node is not None else ""
    target_id = target_node.id if target_node is not None else ""
    focus_id = anchor.id if anchor is not None else request.focus_node_id or ""
    groups = [
        _command_group(
            "query",
            "Saved Queries",
            [
                _command_action(
                    saved_query.query_id,
                    saved_query.label,
                    f"Run {saved_query.query}",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={"query": saved_query.query, **saved_query.filters},
                    ),
                    "query",
                    "Run",
                )
                for saved_query in saved_queries
            ],
        ),
        _command_group(
            "navigate",
            "Navigate",
            (
                _command_action(
                    "global",
                    "Global graph",
                    "Return to the full graph with the current display controls.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={"focus_node_id": None, "selected_edge_id": None},
                    ),
                    "navigate",
                    "Open",
                ),
                _command_action(
                    "local",
                    "Local neighborhood",
                    "Inspect the best current focus node at depth 1.",
                    _route_href(
                        request.with_screen("neighborhood"),
                        overrides={
                            "focus_node_id": focus_id or None,
                            "max_depth": 1,
                            "layout": "focus",
                        },
                    ),
                    "navigate",
                    "Open",
                    disabled=not focus_id,
                ),
                _command_action(
                    "path",
                    "Trace path",
                    "Open the path lens for the selected edge or visible anchors.",
                    _route_href(
                        request.with_screen("path"),
                        overrides={
                            "source_node_id": source_id or None,
                            "target_node_id": target_id or None,
                            "layout": "focus",
                        },
                    ),
                    "navigate",
                    "Trace",
                    disabled=not (source_id and target_id),
                ),
                _command_action(
                    "timeline",
                    "Timeline",
                    "Review timestamped nodes with step-safe playback.",
                    _route_href(
                        request.with_screen("timeline"),
                        overrides={"timeline_playback": "step", "layout": "timeline"},
                    ),
                    "navigate",
                    "Open",
                ),
                _command_action(
                    "status",
                    "Provider status",
                    "Inspect graph diagnostics, warnings, and provider capability notes.",
                    _route_href(request.with_screen("provider_status")),
                    "navigate",
                    "Open",
                ),
            ),
        ),
        _command_group(
            "review",
            "Review",
            (
                _command_action(
                    "evidence",
                    "Evidence review",
                    "Filter to provenance-bearing items and switch to provenance overlay.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "query": "has:provenance",
                            "analytics_overlay": "provenance",
                            "evidence_filter": "with_provenance",
                        },
                    ),
                    "review",
                    "Review",
                ),
                _command_action(
                    "case-packet",
                    "Build case packet",
                    "Create a structural investigation packet for the current focus.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "pivot_node_id": focus_id or None,
                            "pivot_mode": "neighbors",
                        },
                    ),
                    "review",
                    "Build",
                    disabled=not focus_id,
                ),
                _command_action(
                    "diff",
                    "Diff review",
                    "Compare current graph state with a baseline or overlay graph.",
                    _route_href(request.with_screen("diff")),
                    "review",
                    "Open",
                ),
                _command_action(
                    "context",
                    "Context preview",
                    "Preview graph context cards that a host could feed to an agent.",
                    _route_href(request.with_screen("context_preview")),
                    "review",
                    "Open",
                ),
            ),
        ),
        _command_group(
            "author",
            "Author",
            (
                _command_action(
                    "capture",
                    "Capture knowledge",
                    "Jump to the capture form with the current graph context attached.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={"focus_node_id": focus_id or None},
                    )
                    + "#capture-knowledge",
                    "author",
                    "Capture",
                    disabled="knowledge_capture" not in graph.capabilities,
                ),
                _command_action(
                    "draft-action",
                    "Draft graph action",
                    "Jump to provider-neutral graph action controls.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "focus_node_id": focus_id or None,
                            "selected_edge_id": selected_edge.id
                            if selected_edge is not None
                            else None,
                        },
                    )
                    + "#graph-authoring",
                    "author",
                    "Draft",
                    disabled="graph_action" not in graph.capabilities,
                ),
            ),
        ),
        _command_group(
            "export",
            "Export",
            (
                _command_action(
                    "share-route",
                    "Share route",
                    "Copy or open the current exact route state.",
                    _route_href(request),
                    "export",
                    "Open",
                ),
                _command_action(
                    "presentation",
                    "Presentation export view",
                    "Switch to paper theme, SVG fallback, and lower visual clutter.",
                    _route_href(
                        request.with_screen("explore"),
                        overrides={
                            "theme": "paper",
                            "render_engine": "svg",
                            "edge_clutter": "reduced",
                            "label_density": 0.82,
                        },
                    ),
                    "export",
                    "Apply",
                ),
            ),
        ),
    ]
    action_count = sum(len(group["actions"]) for group in groups)
    return {
        "screen": request.screen,
        "focus_node_id": focus_id,
        "selected_edge_id": selected_edge.id if selected_edge is not None else "",
        "visible_node_count": len(visible_graph.nodes),
        "visible_edge_count": len(visible_graph.edges),
        "group_count": len(groups),
        "action_count": action_count,
        "saved_queries": [item.to_dict() for item in saved_queries],
        "groups": groups,
        "provider_boundary": (
            "Command palette entries change only GraphFakos route/view state or "
            "jump to provider-neutral authoring forms; providers own persistence."
        ),
    }


def _command_group(
    group_id: str,
    label: str,
    actions: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> dict[str, object]:
    return {
        "id": group_id,
        "label": label,
        "actions": list(actions),
    }


def _command_action(
    action_id: str,
    label: str,
    summary: str,
    route: str,
    group: str,
    verb: str,
    *,
    disabled: bool = False,
) -> dict[str, object]:
    return {
        "id": action_id,
        "label": label,
        "summary": summary,
        "route": route,
        "group": group,
        "verb": verb,
        "disabled": disabled,
    }


def _command_palette_groups(groups: object) -> str:
    if not isinstance(groups, list) or not groups:
        return _empty("No command palette actions are available.")
    html = ""
    for group in groups:
        if not isinstance(group, dict):
            continue
        actions = group.get("actions")
        if not isinstance(actions, list):
            continue
        html += (
            "<section class='gf-command-group'>"
            f"<h4>{escape(str(group.get('label') or group.get('id') or 'Commands'))}</h4>"
        )
        for action in actions:
            if not isinstance(action, dict):
                continue
            disabled = bool(action.get("disabled"))
            route = "#" if disabled else str(action.get("route") or "#")
            verb = "Unavailable" if disabled else str(action.get("verb") or "Open")
            html += (
                "<div class='gf-route-row gf-command-row' "
                f"data-command-group='{escape(str(action.get('group') or ''))}' "
                f"data-command-id='{escape(str(action.get('id') or ''))}' "
                f"data-disabled='{str(disabled).lower()}'>"
                f"<div><strong>{escape(str(action.get('label') or action.get('id') or 'Command'))}</strong>"
                f"<span class='gf-inline-note'>{escape(str(action.get('summary') or ''))}</span></div>"
                f"<a class='gf-inline-link' href='{escape(route)}'>{escape(verb)}</a></div>"
            )
        html += "</section>"
    return html


def _query_errors(query: str) -> tuple[str, ...]:
    try:
        shlex.split(query)
    except ValueError as exc:
        return (f"query parse warning: {exc}",)
    return ()


def _search_results_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    payload = _search_results_payload(graph, request, focus)
    mode = str(payload["mode"]).replace("_", " ")
    return _panel(
        "Search Results",
        _summary_note(
            f"Ranked {mode} from the current visible graph, with route-backed jumps."
        )
        + "<section class='gf-search-results' data-gf-search-results-panel='true'>"
        f"{_search_result_rows(payload['results'])}"
        "</section>" + _json_script("data-gf-search-results", payload),
    )


def _search_results_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> dict[str, object]:
    query_terms = tuple(_parse_query(request.query)["terms"])
    focused_ids = {focus.id} if focus is not None else set()
    degree_map = _node_degree_map(graph)
    results = [
        _search_result_payload(graph, request, node, focus, query_terms, degree_map)
        for node in _ranked_nodes(graph, focused_ids)
    ][:8]
    return {
        "query": request.query,
        "mode": _search_result_mode(request),
        "focus_id": focus.id if focus is not None else None,
        "visible_node_count": len(graph.nodes),
        "result_count": len(results),
        "results": results,
    }


def _search_result_mode(request: GraphFakosRequest) -> str:
    if request.query:
        return "query_matches"
    if request.filters or any(
        (
            request.min_degree is not None,
            request.max_degree is not None,
            request.connected_to_node_id,
            request.component_id,
            request.cluster_id,
            request.evidence_filter,
        )
    ):
        return "filtered_nodes"
    return "top_visible_nodes"


def _search_result_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    node: GraphFakosNode,
    focus: GraphFakosNode | None,
    query_terms: tuple[str, ...],
    degree_map: dict[str, int],
) -> dict[str, object]:
    degree = degree_map.get(node.id, 0)
    evidence_route = _route_href(
        request.with_screen("provenance"),
        overrides={"focus_node_id": node.id, "selected_edge_id": None},
    )
    path_route = None
    if focus is not None and focus.id != node.id:
        path_edges = _shortest_path_edges(graph, focus.id, node.id)
        if path_edges:
            path_route = _route_href(
                request.with_screen("path"),
                overrides={
                    "source_node_id": focus.id,
                    "target_node_id": node.id,
                    "layout": "focus",
                    "selected_edge_id": None,
                },
            )
    return {
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "source": node.source,
        "score": node.score,
        "degree": degree,
        "matched_terms": [
            term for term in query_terms if _node_contains_text(node, term)
        ],
        "focus_route": _explore_href(request, focus_node_id=node.id),
        "local_route": _route_href(
            request.with_screen("neighborhood"),
            overrides={
                "focus_node_id": node.id,
                "max_depth": 1,
                "layout": "focus",
                "selected_edge_id": None,
            },
        ),
        "evidence_route": evidence_route,
        "path_route": path_route,
    }


def _search_result_rows(items: object) -> str:
    if not isinstance(items, list) or not items:
        return _empty("No visible nodes match the current query or filters.")
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("id") or "node")
        kind = str(item.get("kind") or "node")
        degree = str(item.get("degree", 0))
        score = item.get("score")
        score_note = f" · score {score}" if score is not None else ""
        rows.append(
            "<div class='gf-route-row gf-search-result-row'>"
            f"<div>{escape(label)}"
            f"<span class='gf-inline-note'>{escape(kind)} · degree {escape(degree)}{escape(score_note)}</span></div>"
            "<span class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('focus_route') or '#'))}'>Focus</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('local_route') or '#'))}'>Local</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('evidence_route') or '#'))}'>Evidence</a>"
            f"{_search_result_path_link(item)}"
            "</span></div>"
        )
    return _html_list(rows)


def _search_result_path_link(item: dict[str, object]) -> str:
    route = item.get("path_route")
    if not route:
        return ""
    return f"<a class='gf-inline-link' href='{escape(str(route))}'>Path</a>"


def _expansion_planner_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    if not graph.nodes:
        return _panel(
            "Expansion Planner",
            _empty("No visible nodes are available for expansion planning."),
        )
    payload = _expansion_planner_payload(graph, request, focus)
    node_options = tuple((node.id, node.label) for node in _ranked_nodes(graph, set()))
    edge_kinds = tuple(sorted({edge.kind for edge in graph.edges if edge.kind}))
    node_kinds = tuple(sorted({node.kind for node in graph.nodes if node.kind}))
    return _panel(
        "Expansion Planner",
        _summary_note(
            "Plan provider-owned neighbor expansion without making GraphFakos fetch or persist graph data."
        )
        + "<form method='get' action='/neighborhood' class='gf-panel-form' aria-label='Expansion planner controls'>"
        f"{_select_pairs('focus_node_id', 'Expansion source', node_options, str(payload['source_id']))}"
        f"{_select('max_depth', 'Depth', ('1', '2', '3'), str(payload['depth']))}"
        f"{_select('edge_kind', 'Edge kind', edge_kinds, str(payload['edge_kind']))}"
        f"{_select('node_kind', 'Node kind', node_kinds, str(payload['node_kind']))}"
        f"{_state_hidden_inputs(request, exclude=('focus_node_id', 'max_depth', 'edge_kind', 'node_kind'))}"
        "<button type='submit'>Preview Local Expansion</button>"
        "</form>"
        "<section class='gf-expansion-planner' data-gf-expansion-planner-panel='true'>"
        f"{_expansion_suggestion_rows(payload['suggestions'])}"
        "</section>" + _json_script("data-gf-expansion-plan", payload),
    )


def _expansion_planner_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> dict[str, object]:
    source = _expansion_source_node(graph, focus)
    edge_kind = request.filters.get("edge_kind", "")
    node_kind = request.filters.get("node_kind", "")
    depth = max(request.max_depth, 1)
    expansion_request = GraphFakosExpansionRequest(
        source_id=source.id,
        depth=depth,
        edge_kind=edge_kind,
        node_kind=node_kind,
    )
    suggestions = [
        _expansion_suggestion_payload(graph, request, node, edge_kind, node_kind)
        for node in _ranked_nodes(graph, {source.id})
    ][:6]
    return {
        "status": "planned",
        "source_id": source.id,
        "source_label": source.label,
        "depth": depth,
        "edge_kind": edge_kind,
        "node_kind": node_kind,
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "request": expansion_request.to_dict(),
        "suggestions": suggestions,
        "provider_boundary": (
            "GraphFakos plans the expansion request; providers or hosts own fetching, "
            "persisting, and rebuilding graph data."
        ),
    }


def _expansion_source_node(
    graph: GraphFakosGraph,
    focus: GraphFakosNode | None,
) -> GraphFakosNode:
    node_ids = {node.id for node in graph.nodes}
    if focus is not None and focus.id in node_ids:
        return focus
    return _ranked_nodes(graph, set())[0]


def _expansion_suggestion_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    node: GraphFakosNode,
    edge_kind: str,
    node_kind: str,
) -> dict[str, object]:
    degree = _node_degree_map(graph).get(node.id, 0)
    incident_edge_kinds = sorted(
        {
            edge.kind
            for edge in graph.edges
            if edge.kind and (edge.source_id == node.id or edge.target_id == node.id)
        }
    )
    return {
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "degree": degree,
        "incident_edge_kinds": incident_edge_kinds,
        "request": GraphFakosExpansionRequest(
            source_id=node.id,
            depth=1,
            edge_kind=edge_kind,
            node_kind=node_kind,
        ).to_dict(),
        "local_route": _route_href(
            request.with_screen("neighborhood"),
            overrides={"focus_node_id": node.id, "max_depth": 1, "layout": "focus"},
        ),
        "deeper_route": _route_href(
            request.with_screen("neighborhood"),
            overrides={"focus_node_id": node.id, "max_depth": 2, "layout": "focus"},
        ),
        "case_route": _route_href(
            request.with_screen("explore"),
            overrides={"pivot_node_id": node.id, "pivot_mode": "neighbors"},
        ),
    }


def _expansion_suggestion_rows(items: object) -> str:
    if not isinstance(items, list) or not items:
        return _empty("No expansion candidates are visible.")
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("id") or "node")
        kind = str(item.get("kind") or "node")
        degree = str(item.get("degree", 0))
        rows.append(
            "<div class='gf-route-row gf-expansion-row'>"
            f"<div>{escape(label)}"
            f"<span class='gf-inline-note'>{escape(kind)} · degree {escape(degree)}</span></div>"
            "<span class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('local_route') or '#'))}'>Local d1</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('deeper_route') or '#'))}'>Local d2</a>"
            f"<a class='gf-inline-link' href='{escape(str(item.get('case_route') or '#'))}'>Case</a>"
            "</span></div>"
        )
    return _html_list(rows)


def _graph_data_table_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    payload = _graph_data_table_payload(graph, request)
    return _panel(
        "Graph Data Table",
        _summary_note(
            "Visible graph rows keep navigation, selection, and structural metrics usable beside the canvas."
        )
        + _badges(
            (
                (f"{payload['visible_node_count']} visible node(s)", "accent"),
                (f"{payload['visible_edge_count']} visible edge(s)", "blue"),
                (f"{payload['row_count']} row(s)", "neutral"),
            )
        )
        + _graph_data_rows(payload["rows"])
        + _json_script("data-gf-graph-data-table", payload),
    )


def _graph_data_table_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    degree_map = _node_degree_map(graph)
    component_ids = _node_component_ids(graph)
    selected_ids = set(request.selected_node_ids)
    rows = [
        _graph_data_row_payload(node, request, degree_map, component_ids, selected_ids)
        for node in sorted(
            graph.nodes,
            key=lambda item: (
                item.id not in selected_ids,
                item.id != request.focus_node_id,
                -degree_map.get(item.id, 0),
                -(item.score if item.score is not None else 0),
                item.label.casefold(),
            ),
        )[:16]
    ]
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "row_count": len(rows),
        "selected_node_ids": list(request.selected_node_ids),
        "focus_node_id": request.focus_node_id,
        "rows": rows,
        "provider_boundary": (
            "GraphFakos lists visible graph structure and route actions; "
            "providers remain responsible for durable storage and semantic truth."
        ),
    }


def _graph_data_row_payload(
    node: GraphFakosNode,
    request: GraphFakosRequest,
    degree_map: dict[str, int],
    component_ids: dict[str, str],
    selected_ids: set[str],
) -> dict[str, object]:
    next_selected = tuple(dict.fromkeys((*request.selected_node_ids, node.id)))
    return {
        "id": node.id,
        "label": node.label,
        "kind": node.kind,
        "source": node.source,
        "degree": degree_map.get(node.id, 0),
        "component_id": component_ids.get(node.id, ""),
        "score": node.score,
        "confidence": node.confidence,
        "tags": list(node.tags),
        "provenance_count": len(node.provenance_ids),
        "citation_count": len(node.citation_ids),
        "selected": node.id in selected_ids,
        "focused": node.id == request.focus_node_id,
        "routes": {
            "focus": _explore_href(request, focus_node_id=node.id),
            "local": _route_href(
                request.with_screen("neighborhood"),
                overrides={"focus_node_id": node.id, "max_depth": 1},
            ),
            "case": _route_href(
                request.with_screen("explore"),
                overrides={"pivot_node_id": node.id, "pivot_mode": "neighbors"},
            ),
            "select": _route_href(
                request.with_screen("explore"),
                overrides={"selected_node_ids": ",".join(next_selected)},
            ),
        },
    }


def _graph_data_rows(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return _empty("No visible graph rows.")
    html = "<div class='gf-data-table' data-gf-graph-data-table-panel='true'>"
    for row in rows:
        if not isinstance(row, dict):
            continue
        routes = row.get("routes")
        if not isinstance(routes, dict):
            routes = {}
        markers = []
        if row.get("focused"):
            markers.append(("focused", "accent"))
        if row.get("selected"):
            markers.append(("selected", "blue"))
        html += (
            "<article class='gf-card gf-data-row'>"
            f"<h4>{escape(str(row.get('label') or row.get('id') or 'node'))}</h4>"
            + _badges(
                (
                    (str(row.get("kind") or "node"), "neutral"),
                    (f"degree {row.get('degree', 0)}", "accent"),
                    (str(row.get("component_id") or "component"), "blue"),
                    *markers,
                )
            )
            + _key_values(
                {
                    "id": row.get("id"),
                    "source": row.get("source"),
                    "score": row.get("score"),
                    "confidence": row.get("confidence"),
                    "evidence": (
                        f"{row.get('provenance_count', 0)} provenance / "
                        f"{row.get('citation_count', 0)} citation"
                    ),
                    "tags": ", ".join(str(tag) for tag in row.get("tags", [])[:4])
                    if isinstance(row.get("tags"), list)
                    else "",
                }
            )
            + "<div class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('focus') or '#'))}'>Focus</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('local') or '#'))}'>Local</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('case') or '#'))}'>Case</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('select') or '#'))}'>Select</a>"
            "</div></article>"
        )
    return f"{html}</div>"


def _relationship_data_table_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    payload = _relationship_data_table_payload(graph, request)
    return _panel(
        "Relationship Data Table",
        _summary_note(
            "Visible edge rows make relationships inspectable, filterable, and traceable without JavaScript."
        )
        + _badges(
            (
                (f"{payload['visible_edge_count']} visible edge(s)", "accent"),
                (f"{payload['row_count']} row(s)", "neutral"),
            )
        )
        + _relationship_data_rows(payload["rows"])
        + _json_script("data-gf-relationship-data-table", payload),
    )


def _relationship_data_table_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    node_map = graph.node_map()
    rows = [
        _relationship_data_row_payload(edge, request, node_map)
        for edge in sorted(
            graph.edges,
            key=lambda item: (
                item.id != request.selected_edge_id,
                item.kind.casefold(),
                -(item.confidence if item.confidence is not None else 0),
                item.id.casefold(),
            ),
        )[:18]
    ]
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "row_count": len(rows),
        "selected_edge_id": request.selected_edge_id,
        "rows": rows,
        "provider_boundary": (
            "GraphFakos lists visible relationship structure and routes; "
            "providers own durable relationship truth and mutation."
        ),
    }


def _relationship_data_row_payload(
    edge: GraphFakosEdge,
    request: GraphFakosRequest,
    node_map: dict[str, GraphFakosNode],
) -> dict[str, object]:
    source = node_map.get(edge.source_id)
    target = node_map.get(edge.target_id)
    return {
        "id": edge.id,
        "label": edge.label or edge.kind,
        "kind": edge.kind,
        "source_id": edge.source_id,
        "source_label": source.label if source is not None else edge.source_id,
        "target_id": edge.target_id,
        "target_label": target.label if target is not None else edge.target_id,
        "weight": edge.weight,
        "confidence": edge.confidence,
        "direction": edge.direction,
        "provenance_count": len(edge.provenance_ids),
        "citation_count": len(edge.citation_ids),
        "selected": edge.id == request.selected_edge_id,
        "routes": {
            "inspect": _explore_href(
                request,
                selected_edge_id=edge.id,
                focus_node_id=request.focus_node_id,
            ),
            "source": _explore_href(request, focus_node_id=edge.source_id),
            "target": _explore_href(request, focus_node_id=edge.target_id),
            "path": _route_href(
                request.with_screen("path"),
                overrides={
                    "source_node_id": edge.source_id,
                    "target_node_id": edge.target_id,
                    "selected_edge_id": edge.id,
                    "layout": "focus",
                },
            ),
            "kind": _route_href(
                request.with_screen("explore"),
                overrides={"edge_kind": edge.kind, "selected_edge_id": edge.id},
            ),
        },
    }


def _relationship_data_rows(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return _empty("No visible relationship rows.")
    html = (
        "<div class='gf-relationship-table' "
        "data-gf-relationship-data-table-panel='true'>"
    )
    for row in rows:
        if not isinstance(row, dict):
            continue
        routes = row.get("routes")
        if not isinstance(routes, dict):
            routes = {}
        markers = (("selected", "blue"),) if row.get("selected") else ()
        html += (
            "<article class='gf-card gf-relationship-row'>"
            f"<h4>{escape(str(row.get('source_label') or row.get('source_id') or 'source'))}"
            " -> "
            f"{escape(str(row.get('target_label') or row.get('target_id') or 'target'))}</h4>"
            + _badges(
                (
                    (str(row.get("kind") or "edge"), "accent"),
                    (str(row.get("direction") or "directed"), "neutral"),
                    *markers,
                )
            )
            + _key_values(
                {
                    "id": row.get("id"),
                    "label": row.get("label"),
                    "confidence": row.get("confidence"),
                    "weight": row.get("weight"),
                    "evidence": (
                        f"{row.get('provenance_count', 0)} provenance / "
                        f"{row.get('citation_count', 0)} citation"
                    ),
                }
            )
            + "<div class='gf-trail-actions'>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('inspect') or '#'))}'>Inspect</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('source') or '#'))}'>Source</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('target') or '#'))}'>Target</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('path') or '#'))}'>Path</a>"
            f"<a class='gf-inline-link' href='{escape(str(routes.get('kind') or '#'))}'>Kind</a>"
            "</div></article>"
        )
    return f"{html}</div>"


def _evidence_coverage_map_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    payload = _evidence_coverage_map_payload(graph, request)
    return _panel(
        "Evidence Coverage Map",
        _summary_note(
            "Visible provenance and citation coverage stays structural; GraphFakos does not decide truth."
        )
        + _badges(
            (
                (
                    f"{payload['node_coverage']['with_any']} node(s) with evidence",
                    "accent",
                ),
                (
                    f"{payload['edge_coverage']['with_any']} edge(s) with evidence",
                    "blue",
                ),
                (f"{payload['gap_count']} visible gap(s)", "neutral"),
            )
        )
        + _evidence_coverage_rows(payload["coverage_rows"])
        + _json_script("data-gf-evidence-coverage-map", payload),
    )


def _evidence_coverage_map_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    node_coverage = _evidence_coverage_counts(graph.nodes)
    edge_coverage = _evidence_coverage_counts(graph.edges)
    rows = [
        _evidence_coverage_row(
            "nodes-with-provenance",
            "Nodes with provenance",
            node_coverage["with_provenance"],
            len(graph.nodes),
            _route_href(
                request.with_screen("explore"),
                overrides={"evidence_filter": "with_provenance"},
            ),
            "Declared provenance references on visible nodes.",
        ),
        _evidence_coverage_row(
            "nodes-missing-provenance",
            "Nodes missing provenance",
            node_coverage["missing_provenance"],
            len(graph.nodes),
            _route_href(
                request.with_screen("explore"),
                overrides={"evidence_filter": "missing_provenance"},
            ),
            "Visible nodes without declared provenance references.",
        ),
        _evidence_coverage_row(
            "nodes-with-citation",
            "Nodes with citations",
            node_coverage["with_citation"],
            len(graph.nodes),
            _route_href(
                request.with_screen("explore"),
                overrides={"evidence_filter": "with_citation"},
            ),
            "Declared citation references on visible nodes.",
        ),
        _evidence_coverage_row(
            "nodes-missing-citation",
            "Nodes missing citations",
            node_coverage["missing_citation"],
            len(graph.nodes),
            _route_href(
                request.with_screen("explore"),
                overrides={"evidence_filter": "missing_citation"},
            ),
            "Visible nodes without declared citation references.",
        ),
        _evidence_coverage_row(
            "edges-with-evidence",
            "Edges with evidence",
            edge_coverage["with_any"],
            len(graph.edges),
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "query": "has:provenance",
                    "analytics_overlay": "provenance",
                },
            ),
            "Visible relationships with provenance or citation references.",
        ),
        _evidence_coverage_row(
            "edges-missing-evidence",
            "Edges missing evidence",
            edge_coverage["missing_any"],
            len(graph.edges),
            _route_href(request.with_screen("provenance")),
            "Visible relationships without provenance or citation references.",
        ),
    ]
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "node_coverage": node_coverage,
        "edge_coverage": edge_coverage,
        "gap_count": node_coverage["missing_any"] + edge_coverage["missing_any"],
        "coverage_rows": rows,
        "provider_boundary": (
            "GraphFakos reports declared evidence coverage only; providers own "
            "source quality, claim truth, and evidence policy."
        ),
    }


def _evidence_coverage_counts(items: object) -> dict[str, int]:
    rows = [item for item in items if hasattr(item, "provenance_ids")]
    with_provenance = sum(1 for item in rows if item.provenance_ids)
    with_citation = sum(1 for item in rows if item.citation_ids)
    with_any = sum(1 for item in rows if item.provenance_ids or item.citation_ids)
    total = len(rows)
    return {
        "total": total,
        "with_provenance": with_provenance,
        "with_citation": with_citation,
        "with_any": with_any,
        "missing_provenance": total - with_provenance,
        "missing_citation": total - with_citation,
        "missing_any": total - with_any,
    }


def _evidence_coverage_row(
    row_id: str,
    label: str,
    count: int,
    total: int,
    route: str,
    summary: str,
) -> dict[str, object]:
    ratio = count / total if total else 0
    return {
        "id": row_id,
        "label": label,
        "count": count,
        "total": total,
        "ratio": round(ratio, 3),
        "percent": round(ratio * 100),
        "route": route,
        "summary": summary,
    }


def _evidence_coverage_rows(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return _empty("No evidence coverage rows are visible.")
    html = "<div class='gf-evidence-coverage' data-gf-evidence-coverage-panel='true'>"
    for row in rows:
        if not isinstance(row, dict):
            continue
        percent = int(row.get("percent") or 0)
        html += (
            "<article class='gf-evidence-coverage-row'>"
            "<div>"
            f"<h4>{escape(str(row.get('label') or row.get('id') or 'Coverage'))}</h4>"
            f"<p>{escape(str(row.get('summary') or ''))}</p>"
            "</div>"
            "<div class='gf-evidence-meter' "
            f"aria-label='{escape(str(row.get('label') or 'Coverage'))}: {percent} percent'>"
            f"<span style='width: {percent}%'></span>"
            "</div>"
            "<div class='gf-trail-actions'>"
            f"<strong>{escape(str(row.get('count', 0)))} / {escape(str(row.get('total', 0)))}</strong>"
            f"<a class='gf-inline-link' href='{escape(str(row.get('route') or '#'))}'>Review</a>"
            "</div>"
            "</article>"
        )
    return f"{html}</div>"


def _facet_explorer_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> str:
    payload = _facet_explorer_payload(graph, request)
    return _panel(
        "Facet Explorer",
        _summary_note(
            "Route-backed facets expose structural and provider-declared fields without changing graph truth."
        )
        + _facet_explorer_sections(payload["facets"])
        + _json_script("data-gf-facet-explorer", payload),
    )


def _facet_explorer_payload(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    facets = [
        _facet_section(
            "node_kind",
            "Node kinds",
            _node_value_counts((node.kind for node in graph.nodes if node.kind)),
            request,
            active_value=request.filters.get("node_kind", ""),
        ),
        _facet_section(
            "source",
            "Sources",
            _node_value_counts((node.source for node in graph.nodes if node.source)),
            request,
            active_value=request.filters.get("source", ""),
        ),
        _facet_section(
            "tag",
            "Tags",
            _node_value_counts(
                (tag for node in graph.nodes for tag in node.tags if tag)
            ),
            request,
            active_value=request.filters.get("tag", ""),
        ),
        _facet_section(
            "component_id",
            "Components",
            _node_value_counts(_node_component_ids(graph).values()),
            request,
            active_value=request.component_id,
        ),
        _evidence_facet_section(graph, request),
        _degree_facet_section(graph, request),
    ]
    visible_facets = [facet for facet in facets if facet["items"]]
    return {
        "visible_node_count": len(graph.nodes),
        "visible_edge_count": len(graph.edges),
        "facets": visible_facets,
        "provider_boundary": (
            "GraphFakos counts visible structural fields and declared metadata; "
            "providers own field meaning and persistence."
        ),
    }


def _facet_section(
    facet_id: str,
    label: str,
    counts: dict[str, int],
    request: GraphFakosRequest,
    *,
    active_value: str,
) -> dict[str, object]:
    return {
        "id": facet_id,
        "label": label,
        "items": [
            {
                "value": value,
                "label": value,
                "count": count,
                "active": value == active_value,
                "route": _route_href(
                    request.with_screen("explore"), overrides={facet_id: value}
                ),
            }
            for value, count in _sorted_counts(counts)[:8]
        ],
    }


def _evidence_facet_section(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    counts = {
        "with_provenance": sum(1 for node in graph.nodes if node.provenance_ids),
        "with_citation": sum(1 for node in graph.nodes if node.citation_ids),
        "missing_provenance": sum(1 for node in graph.nodes if not node.provenance_ids),
        "missing_citation": sum(1 for node in graph.nodes if not node.citation_ids),
    }
    return {
        "id": "evidence_filter",
        "label": "Evidence",
        "items": [
            {
                "value": value,
                "label": value.replace("_", " "),
                "count": count,
                "active": value == request.evidence_filter,
                "route": _route_href(
                    request.with_screen("explore"),
                    overrides={"evidence_filter": value},
                ),
            }
            for value, count in counts.items()
            if count
        ],
    }


def _degree_facet_section(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
) -> dict[str, object]:
    degree_map = _node_degree_map(graph)
    buckets = {
        "isolated": sum(1 for degree in degree_map.values() if degree == 0),
        "degree 1-2": sum(1 for degree in degree_map.values() if 1 <= degree <= 2),
        "degree 3+": sum(1 for degree in degree_map.values() if degree >= 3),
    }
    routes = {
        "isolated": {"min_degree": 0, "max_degree": 0},
        "degree 1-2": {"min_degree": 1, "max_degree": 2},
        "degree 3+": {"min_degree": 3, "max_degree": None},
    }
    active = _active_degree_bucket(request)
    return {
        "id": "degree",
        "label": "Degree",
        "items": [
            {
                "value": value,
                "label": value,
                "count": count,
                "active": value == active,
                "route": _route_href(
                    request.with_screen("explore"), overrides=routes[value]
                ),
            }
            for value, count in buckets.items()
            if count
        ],
    }


def _active_degree_bucket(request: GraphFakosRequest) -> str:
    if request.min_degree == 0 and request.max_degree == 0:
        return "isolated"
    if request.min_degree == 1 and request.max_degree == 2:
        return "degree 1-2"
    if request.min_degree == 3 and request.max_degree is None:
        return "degree 3+"
    return ""


def _facet_explorer_sections(facets: object) -> str:
    if not isinstance(facets, list) or not facets:
        return _empty("No facet values are visible.")
    html = "<div class='gf-facet-explorer' data-gf-facet-explorer-panel='true'>"
    for facet in facets:
        if not isinstance(facet, dict):
            continue
        items = facet.get("items")
        if not isinstance(items, list) or not items:
            continue
        html += (
            "<section class='gf-facet-group'>"
            f"<h4>{escape(str(facet.get('label') or facet.get('id') or 'Facet'))}</h4>"
        )
        for item in items:
            if not isinstance(item, dict):
                continue
            active = " aria-current='true'" if item.get("active") else ""
            html += (
                f"<a class='gf-facet-pill' href='{escape(str(item.get('route') or '#'))}'{active}>"
                f"<span>{escape(str(item.get('label') or item.get('value') or 'value'))}</span>"
                f"<strong>{escape(str(item.get('count', 0)))}</strong></a>"
            )
        html += "</section>"
    return f"{html}</div>"
