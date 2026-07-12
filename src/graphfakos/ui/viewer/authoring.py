"""Provider-neutral knowledge capture and graph action workflows."""

from __future__ import annotations

from html import escape
import json

from graphfakos.models import (
    GraphFakosActionStatus,
    GraphFakosGraph,
    GraphFakosGraphAction,
    GraphFakosNode,
    GraphFakosRequest,
)
from graphfakos.ui.viewer.graph_ops import _preferred_focus_node
from graphfakos.ui.viewer.html import (
    badge as _badge,
    html_list as _html_list,
    json_script as _json_script,
    panel as _panel,
    select as _select,
    select_pairs as _select_pairs,
    summary_note as _summary_note,
)
from graphfakos.ui.viewer.routing import _route_href

_GRAPH_ACTION_TYPES = (
    ("draft_node", "Draft node"),
    ("draft_edge", "Draft edge"),
    ("merge_alias", "Merge alias"),
)
_CAPTURE_TEMPLATES = (
    (
        "note",
        "Note",
        "note",
        "ui, graph",
        "Capture a durable observation about the selected graph context.",
    ),
    (
        "question",
        "Question",
        "question",
        "question, follow-up",
        "Ask what should be checked next in this graph context.",
    ),
    (
        "code",
        "Code observation",
        "code",
        "code, graph",
        "Capture a source or code observation tied to this graph context.",
    ),
    (
        "warning",
        "Warning",
        "warning",
        "warning, review",
        "Flag a risk, stale edge, or unexpected graph relationship.",
    ),
)


def _knowledge_capture_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    focus_id = focus.id if focus is not None else ""
    focus_label = focus.label if focus is not None else "the graph"
    supported = _graph_supports(graph, "knowledge_capture")
    support_tone = "accent" if supported else "neutral"
    support_label = "Capture supported" if supported else "Capture unsupported"
    submit_attrs = "" if supported else " disabled aria-disabled='true'"
    status_text = (
        ""
        if supported
        else "Current provider does not advertise workbench knowledge capture."
    )
    status_state = "" if supported else "error"
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    link_kinds = tuple(
        dict.fromkeys(
            (
                "mentions",
                "relates",
                "supports",
                "questions",
                *tuple(edge.kind for edge in graph.edges if edge.kind),
            )
        )
    )
    kinds = ("note", "memory", "document", "code", "task", "question", "warning")
    options = "".join(
        f"<option value='{escape(kind)}'>{escape(kind.title())}</option>"
        for kind in kinds
    )
    return (
        "<section class='gf-panel gf-capture-panel' id='capture-knowledge'>"
        "<div class='gf-panel-heading'><h3>Capture Knowledge</h3>"
        f"{_badge(support_label, support_tone)}</div>"
        + _summary_note(
            "Add a note, code observation, or question for the host provider or worker to persist and rebuild into the graph."
        )
        + "<form class='gf-capture-form' method='post' action='/api/knowledge' "
        f"data-gf-knowledge-form='true' data-gf-capability-supported='{str(supported).lower()}'>"
        f"{_capture_template_bar()}"
        f"<label>Text<textarea name='text' rows='5' required "
        f"placeholder='Write an observation about {escape(focus_label)}'></textarea></label>"
        f"<label>Kind<select name='kind'>{options}</select></label>"
        "<label>Tags<input name='tags' placeholder='ui, graph, code'></label>"
        "<label>Source<input name='source' value='workbench'></label>"
        f"<label>Attach to{_select_pairs('link_node_id', 'Attach note to node', node_options, focus_id)}</label>"
        f"<label>Relationship{_select('link_edge_kind', 'Relationship kind', link_kinds, 'mentions')}</label>"
        f"<input type='hidden' name='screen' value='{escape(request.screen)}'>"
        f"{_viewer_context_hidden_input(request)}"
        f"{_viewer_context_preview(graph, request)}"
        f"<button type='submit'{submit_attrs}>Add to graph</button>"
        f"<p class='gf-capture-status' data-gf-knowledge-status='true' data-state='{status_state}'>{escape(status_text)}</p>"
        "</form></section>"
    )


def _capture_template_bar() -> str:
    buttons = "".join(
        "<button type='button' "
        f"data-gf-capture-template='{escape(template_id)}' "
        f"data-kind='{escape(kind)}' "
        f"data-tags='{escape(tags)}' "
        "data-source='workbench' "
        f"data-placeholder='{escape(placeholder, quote=True)}'>"
        f"{escape(label)}</button>"
        for template_id, label, kind, tags, placeholder in _CAPTURE_TEMPLATES
    )
    return (
        "<div class='gf-capture-templates' data-gf-capture-templates='true' "
        "aria-label='Knowledge capture templates'>"
        "<span>Quick presets</span>"
        f"{buttons}"
        "</div>"
    )


def _graph_action_panel(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    action_type, target_id, source_id, target_node_id = _graph_action_defaults(
        graph,
        request,
        focus,
    )
    supported = _graph_supports(graph, "graph_action")
    support_tone = "accent" if supported else "neutral"
    support_label = "Actions supported" if supported else "Actions unsupported"
    submit_attrs = "" if supported else " disabled aria-disabled='true'"
    status_text = (
        ""
        if supported
        else "Current provider does not advertise graph authoring actions."
    )
    status_state = "" if supported else "error"
    action = _draft_graph_action(action_type, target_id, source_id, target_node_id)
    status = _draft_action_status(action)
    node_options = tuple((node.id, node.label) for node in graph.nodes)
    return (
        "<section class='gf-panel gf-action-panel' id='graph-authoring'>"
        "<div class='gf-panel-heading'><h3>Graph Authoring</h3>"
        f"{_badge(support_label, support_tone)}</div>"
        + _summary_note(
            "Draft node, edge, merge, and alias requests are provider-neutral; the host owns persistence."
        )
        + "<form class='gf-capture-form' method='post' action='/api/action' "
        f"data-gf-action-form='true' data-gf-capability-supported='{str(supported).lower()}'>"
        f"<input type='hidden' name='action_id' value='{escape(action.action_id)}'>"
        f"<label>Action<select name='action_type'>{_graph_action_options(action_type)}</select></label>"
        f"<label>Target{_select_pairs('target_id', 'Action target node', node_options, target_id)}</label>"
        f"<label>Source node{_select_pairs('source_id', 'Draft edge source', node_options, source_id)}</label>"
        f"<label>Target node{_select_pairs('target_node_id', 'Draft edge target', node_options, target_node_id)}</label>"
        "<label>Label<input name='label' placeholder='New node or edge label'></label>"
        "<label>Tags<input name='tags' placeholder='editor, review'></label>"
        "<label>Body<textarea name='body' rows='3' placeholder='Why should the provider apply this?'></textarea></label>"
        f"{_viewer_context_hidden_input(request)}"
        f"{_viewer_context_preview(graph, request)}"
        f"<button type='submit'{submit_attrs}>Queue action</button>"
        f"<p class='gf-capture-status' data-gf-action-status-text='true' data-state='{status_state}'>{escape(status_text)}</p>"
        "</form>"
        f"{_json_script('data-gf-action-template', action.to_dict())}"
        f"{_json_script('data-gf-action-status', status.to_dict())}"
        "</section>"
    )


def _graph_supports(graph: GraphFakosGraph, capability: str) -> bool:
    return capability in set(graph.capabilities)


def _graph_action_defaults(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> tuple[str, str, str, str]:
    node_ids = {node.id for node in graph.nodes}
    selected = tuple(
        node_id for node_id in request.selected_node_ids if node_id in node_ids
    )
    selected_edge = next(
        (edge for edge in graph.edges if edge.id == request.selected_edge_id),
        None,
    )
    if selected_edge is not None:
        source_id = (
            selected_edge.source_id if selected_edge.source_id in node_ids else ""
        )
        target_node_id = (
            selected_edge.target_id if selected_edge.target_id in node_ids else ""
        )
        target_id = focus.id if focus is not None else source_id or target_node_id
        return "draft_edge", target_id, source_id, target_node_id
    target_id = focus.id if focus is not None else (selected[0] if selected else "")
    source_id = selected[0] if selected else target_id
    target_node_id = selected[1] if len(selected) > 1 else ""
    action_type = "draft_edge" if source_id and target_node_id else "draft_node"
    return action_type, target_id, source_id, target_node_id


def _viewer_context_payload(request: GraphFakosRequest) -> dict[str, object]:
    return {
        "screen": request.screen,
        "query": request.query,
        "focus_node_id": request.focus_node_id or "",
        "selected_node_ids": list(request.selected_node_ids),
        "selected_edge_id": request.selected_edge_id or "",
        "camera": {
            "x": request.camera_x if request.camera_x is not None else 0.0,
            "y": request.camera_y if request.camera_y is not None else 0.0,
            "zoom": request.camera_zoom if request.camera_zoom is not None else 1.0,
            "yaw": request.camera_yaw if request.camera_yaw is not None else 0.0,
            "pitch": (
                request.camera_pitch if request.camera_pitch is not None else 0.0
            ),
        },
        "layout": request.layout,
        "render_engine": request.render_engine,
        "theme": request.theme,
        "saved_view_id": request.saved_view_id,
        "filters": dict(request.filters),
    }


def _viewer_context_hidden_input(request: GraphFakosRequest) -> str:
    payload = _viewer_context_payload(request)
    value = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"<input type='hidden' name='viewer_context' value='{escape(value, quote=True)}'>"


def _viewer_context_preview(graph: GraphFakosGraph, request: GraphFakosRequest) -> str:
    node_map = graph.node_map()
    edge_map = graph.edge_map()
    selected_labels = [
        node_map[node_id].label if node_id in node_map else node_id
        for node_id in request.selected_node_ids
    ]
    selected_edge = edge_map.get(request.selected_edge_id or "")
    selection = ", ".join(selected_labels)
    if selected_edge is not None:
        selection = selected_edge.label or selected_edge.kind
    if not selection:
        selection = request.focus_node_id or "visible graph"
    camera = (
        f"x={request.camera_x or 0:.1f}, "
        f"y={request.camera_y or 0:.1f}, "
        f"zoom={request.camera_zoom or 1:.2f}, "
        f"yaw={request.camera_yaw or 0:.1f}, "
        f"pitch={request.camera_pitch or 0:.1f}"
    )
    filters = ", ".join(
        f"{key}={value}" for key, value in sorted(request.filters.items()) if value
    )
    rows = (
        (
            "Screen",
            request.screen
            if not request.query
            else f"{request.screen}: {request.query}",
        ),
        ("Selection", selection),
        ("Camera", camera),
        ("View", f"{request.layout} / {request.render_engine} / {request.theme}"),
        ("Filters", filters or "none"),
    )
    items = "".join(
        "<li>"
        f"<span>{escape(label)}</span>"
        f"<strong data-gf-viewer-context-row='{escape(label.lower())}'>{escape(value)}</strong>"
        "</li>"
        for label, value in rows
    )
    return (
        "<aside class='gf-viewer-context-preview' "
        "data-gf-viewer-context-preview='true' aria-label='Submission context'>"
        "<b>Submission Context</b>"
        f"<ul>{items}</ul>"
        "</aside>"
    )


def _draft_graph_action(
    action_type: str,
    target_id: str,
    source_id: str,
    target_node_id: str,
) -> GraphFakosGraphAction:
    return GraphFakosGraphAction(
        action_id="draft:route",
        action_type=action_type,
        label="Draft graph edge" if action_type == "draft_edge" else "Draft graph note",
        target_id=target_id,
        source_id=source_id,
        target_node_id=target_node_id,
    )


def _draft_action_status(action: GraphFakosGraphAction) -> GraphFakosActionStatus:
    return GraphFakosActionStatus(
        action_id=action.action_id,
        status="draft",
        message="GraphFakos can submit this provider-neutral action to a host provider.",
    )


def _graph_action_options(selected: str) -> str:
    return "".join(
        f"<option value='{escape(value)}'{(' selected' if value == selected else '')}>{escape(label)}</option>"
        for value, label in _GRAPH_ACTION_TYPES
    )


def _focus_workflow(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    focus: GraphFakosNode | None,
) -> str:
    if focus is None:
        return ""
    anchor = _preferred_focus_node(graph, request)
    routes = [
        (
            "Evidence view",
            _route_href(
                request.with_screen("explore"),
                overrides={
                    "query": "has:provenance",
                    "focus_node_id": focus.id,
                    "selected_edge_id": None,
                    "layout": "focus",
                },
            ),
        ),
        (
            "Neighborhood x2",
            _route_href(
                request.with_screen("neighborhood"),
                overrides={
                    "focus_node_id": focus.id,
                    "selected_edge_id": None,
                    "max_depth": 2,
                    "layout": "focus",
                },
            ),
        ),
    ]
    if anchor is not None and anchor.id != focus.id:
        routes.append(
            (
                "Path to anchor",
                _route_href(
                    request.with_screen("path"),
                    overrides={
                        "source_node_id": focus.id,
                        "target_node_id": anchor.id,
                        "selected_edge_id": None,
                        "layout": "focus",
                    },
                ),
            )
        )
    rows = [
        (
            f"<div class='gf-route-row'><div>{escape(label)}</div>"
            f"<a class='gf-inline-link' href='{route}'>Open</a></div>"
        )
        for label, route in routes
    ]
    return _panel(
        "Workflow",
        _summary_note(
            "Move from one selected node into evidence review, local neighborhood, or path tracing."
        )
        + _html_list(rows),
    )
