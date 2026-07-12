"""Deterministic demo graphs for viewer iteration."""

from __future__ import annotations

from dataclasses import replace

from graphfakos.models import (
    GraphFakosActionStatus,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosGraphAction,
    GraphFakosKnowledgeCapture,
    GraphFakosNode,
    GraphFakosRequest,
    GraphFakosSnapshot,
)
from graphfakos.adapters.demo_scenarios import (
    _agent_memory_graph,
    _budget_graph,
    _citations,
    _dense_graph,
    _evidence_graph,
    _facets,
    _facets_graph,
    _islands_graph,
    _pathfinding_graph,
    _provenance,
    _scenario_warnings,
    _source_code_graph,
    _timeline_graph,
    _visual_for,
    _warnings_graph,
    _workbench_mixed_graph,
)

DEMO_SCENARIOS = (
    "agent-memory",
    "source-code",
    "dense",
    "timeline",
    "warnings",
    "pathfinding",
    "provenance",
    "facets",
    "workbench-mixed",
    "budget",
    "islands",
)


def build_demo_graph(
    scenario: str = "agent-memory",
    request: GraphFakosRequest | None = None,
) -> GraphFakosGraph:
    request = request or GraphFakosRequest()
    scenario = _normalize_scenario(scenario)
    if scenario == "source-code":
        nodes, edges = _source_code_graph()
    elif scenario == "dense":
        nodes, edges = _dense_graph()
    elif scenario == "timeline":
        nodes, edges = _timeline_graph()
    elif scenario == "warnings":
        nodes, edges = _warnings_graph()
    elif scenario == "pathfinding":
        nodes, edges = _pathfinding_graph()
    elif scenario == "provenance":
        nodes, edges = _evidence_graph()
    elif scenario == "facets":
        nodes, edges = _facets_graph()
    elif scenario == "workbench-mixed":
        nodes, edges = _workbench_mixed_graph()
    elif scenario == "budget":
        nodes, edges = _budget_graph()
    elif scenario == "islands":
        nodes, edges = _islands_graph()
    else:
        nodes, edges = _agent_memory_graph()
    warnings = _scenario_warnings(scenario)
    provenance = _provenance(scenario)
    citations = _citations(scenario)
    return GraphFakosGraph(
        graph_id=f"demo-{scenario}",
        label=f"Demo Graph: {scenario.replace('-', ' ').title()}",
        provider_id="demo",
        provider_label="Demo Data Provider",
        graph_role="demo",
        capabilities=(
            "search",
            "neighborhood",
            "path",
            "provenance",
            "timeline",
            "diff",
            "overlay",
            "provider_status",
            "static_export",
            "local_preview",
            "knowledge_capture",
            "graph_action",
        ),
        nodes=nodes,
        edges=edges,
        provenance=provenance,
        citations=citations,
        warnings=warnings,
        stats={
            "scenario": scenario,
            "request_screen": request.screen,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        generated_at="2026-07-01T00:00:00+00:00",
        snapshot=GraphFakosSnapshot(
            snapshot_id=f"demo-{scenario}-current",
            label=f"{scenario.replace('-', ' ').title()} Current",
            created_at="2026-07-01T00:00:00+00:00",
            source_label="GraphFakos deterministic demo generator",
            comparison_ids=(f"demo-{scenario}-baseline",),
        ),
        provider_details={
            "owner": "GraphFakos demo generator",
            "scenario": scenario,
            "purpose": "Viewer-side iteration without real provider data.",
        },
        capability_details={
            "local_preview": "Serve deterministic demo graphs for UI iteration.",
            "diff": "Compare the current demo graph against a trimmed baseline.",
            "overlay": "Show a companion provider view for layout stress testing.",
            "timeline": "Exercise timestamp-aware layouts and freshness panels.",
            "path": "Exercise shortest-path source and target controls.",
            "provenance": "Exercise evidence coverage and citation panels.",
            "provider_status": "Exercise diagnostics, facets, and warning states.",
            "knowledge_capture": (
                "Accept temporary workbench captures during local preview sessions."
            ),
            "graph_action": (
                "Render provider-neutral graph edit requests as preview-only action nodes."
            ),
        },
        available_facets=_facets(nodes, edges),
        provider_payload={
            "integration_summary": (
                "Synthetic graph data for testing GraphFakos viewer controls, "
                "layouts, filters, provenance, and provider-status panels."
            ),
            "integration_commands": tuple(
                f"graphfakos-ui --demo-scenario {item} --serve --open"
                for item in DEMO_SCENARIOS
            ),
        },
    )


def build_demo_baseline_graph(
    scenario: str = "agent-memory",
    request: GraphFakosRequest | None = None,
) -> GraphFakosGraph:
    graph = build_demo_graph(scenario, request)
    keep_count = max(4, int(len(graph.nodes) * 0.72))
    kept_ids = {node.id for node in graph.nodes[:keep_count]}
    nodes = tuple(node for node in graph.nodes if node.id in kept_ids)
    edges = tuple(
        edge
        for edge in graph.edges
        if edge.source_id in kept_ids and edge.target_id in kept_ids
    )
    scenario = _normalize_scenario(scenario)
    return GraphFakosGraph(
        graph_id=f"demo-{scenario}-baseline",
        label=f"Demo Baseline: {scenario.replace('-', ' ').title()}",
        provider_id="demo-baseline",
        provider_label="Demo Baseline",
        graph_role=graph.graph_role,
        capabilities=graph.capabilities,
        nodes=nodes,
        edges=edges,
        provenance=graph.provenance,
        citations=graph.citations,
        warnings=("baseline trims recently generated demo items",),
        stats={
            "scenario": scenario,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        generated_at="2026-06-28T00:00:00+00:00",
        snapshot=GraphFakosSnapshot(
            snapshot_id=f"demo-{scenario}-baseline",
            label=f"{scenario.replace('-', ' ').title()} Baseline",
            created_at="2026-06-28T00:00:00+00:00",
            source_label="GraphFakos deterministic demo generator",
        ),
        provider_details=graph.provider_details,
        capability_details=graph.capability_details,
        available_facets=_facets(nodes, edges),
        provider_payload=graph.provider_payload,
    )


def build_demo_overlay_graphs(
    scenario: str = "agent-memory",
    request: GraphFakosRequest | None = None,
) -> tuple[GraphFakosGraph, ...]:
    graph = build_demo_graph(scenario, request)
    nodes = tuple(node for index, node in enumerate(graph.nodes) if index % 3 != 1)
    kept_ids = {node.id for node in nodes}
    edges = tuple(
        edge
        for edge in graph.edges
        if edge.source_id in kept_ids and edge.target_id in kept_ids
    )
    scenario = _normalize_scenario(scenario)
    overlay = GraphFakosGraph(
        graph_id=f"demo-{scenario}-overlay",
        label=f"Demo Overlay: {scenario.replace('-', ' ').title()}",
        provider_id="demo-overlay",
        provider_label="Demo Overlay Provider",
        graph_role="demo",
        capabilities=("overlay", "provider_status", "report"),
        nodes=nodes,
        edges=edges,
        provenance=graph.provenance,
        citations=graph.citations,
        warnings=("overlay intentionally omits every third demo cluster item",),
        stats={
            "scenario": scenario,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        generated_at="2026-06-30T00:00:00+00:00",
        snapshot=GraphFakosSnapshot(
            snapshot_id=f"demo-{scenario}-overlay",
            label=f"{scenario.replace('-', ' ').title()} Overlay",
            created_at="2026-06-30T00:00:00+00:00",
            source_label="GraphFakos deterministic demo generator",
        ),
        provider_details={"owner": "GraphFakos demo overlay"},
        capability_details={"overlay": "Companion graph for visual comparison."},
        available_facets=_facets(nodes, edges),
        provider_payload=graph.provider_payload,
    )
    return (overlay,)


class DemoGraphProvider:
    provider_id = "demo"
    provider_label = "Demo Data Provider"
    graph_role = "demo"
    capabilities = (
        "search",
        "neighborhood",
        "path",
        "provenance",
        "timeline",
        "diff",
        "overlay",
        "provider_status",
        "static_export",
        "local_preview",
        "knowledge_capture",
        "graph_action",
    )

    def __init__(self, scenario: str = "agent-memory") -> None:
        self.scenario = _normalize_scenario(scenario)
        self._captures: list[GraphFakosKnowledgeCapture] = []
        self._actions: list[GraphFakosGraphAction] = []

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        graph = build_demo_graph(self.scenario, request)
        return _graph_with_workbench_items(
            graph,
            tuple(self._captures),
            tuple(self._actions),
        )

    def load_comparison_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        return build_demo_baseline_graph(self.scenario, request)

    def load_overlay_graphs(
        self,
        request: GraphFakosRequest,
    ) -> tuple[GraphFakosGraph, ...]:
        return build_demo_overlay_graphs(self.scenario, request)

    def capture_knowledge(
        self,
        capture: GraphFakosKnowledgeCapture,
    ) -> GraphFakosGraph:
        self._captures.append(capture)
        return self.load_graph(GraphFakosRequest())

    def submit_graph_action(
        self,
        action: GraphFakosGraphAction,
    ) -> GraphFakosActionStatus:
        self._actions.append(action)
        return GraphFakosActionStatus(
            action_id=action.action_id,
            status="previewed",
            message="demo provider rendered this provider-neutral graph action as preview-only graph content",
            graph_id=f"demo-{self.scenario}",
            provider_payload={
                "preview_node_id": f"action:{len(self._actions):03d}",
                "preview_only": True,
            },
        )


def _graph_with_workbench_items(
    graph: GraphFakosGraph,
    captures: tuple[GraphFakosKnowledgeCapture, ...],
    actions: tuple[GraphFakosGraphAction, ...],
) -> GraphFakosGraph:
    graph = _graph_with_captures(graph, captures)
    return _graph_with_actions(graph, actions)


def _graph_with_actions(
    graph: GraphFakosGraph,
    actions: tuple[GraphFakosGraphAction, ...],
) -> GraphFakosGraph:
    if not actions:
        return graph
    node_ids = {node.id for node in graph.nodes}
    nodes = list(graph.nodes)
    edges = list(graph.edges)
    for index, action in enumerate(actions, start=1):
        node_id = f"action:{index:03d}"
        label = action.label or action.action_type.replace("_", " ").title()
        nodes.append(
            GraphFakosNode(
                id=node_id,
                label=_capture_label(label),
                kind="action",
                summary=action.body or "Preview-only provider-neutral graph action.",
                tags=action.tags,
                source="workbench-action",
                provenance_ids=("prov:demo-generator",),
                citation_ids=("cite:demo-contract",),
                visual=_visual_for("action"),
                provider_payload={"action": action.to_dict(), "preview_only": True},
            )
        )
        if action.target_id and action.target_id in node_ids:
            edges.append(
                GraphFakosEdge(
                    id=f"edge:action:{index:03d}:target",
                    source_id=action.target_id,
                    target_id=node_id,
                    kind=action.action_type,
                    label=action.action_type.replace("_", " "),
                    confidence=1.0,
                    provenance_ids=("prov:demo-generator",),
                    citation_ids=("cite:demo-contract",),
                )
            )
        if action.source_id in node_ids and action.target_node_id in node_ids:
            edges.append(
                GraphFakosEdge(
                    id=f"edge:action:{index:03d}:proposed",
                    source_id=action.source_id,
                    target_id=action.target_node_id,
                    kind=action.action_type,
                    label=f"proposed {action.action_type.replace('_', ' ')}",
                    confidence=0.5,
                    provenance_ids=("prov:demo-generator",),
                    citation_ids=("cite:demo-contract",),
                    provider_payload={
                        "action_id": action.action_id,
                        "preview_only": True,
                    },
                )
            )
        node_ids.add(node_id)
    return replace(
        graph,
        nodes=tuple(nodes),
        edges=tuple(edges),
        stats={
            **graph.stats,
            "action_count": len(actions),
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        available_facets=_facets(tuple(nodes), tuple(edges)),
        provider_payload={
            **graph.provider_payload,
            "workbench_action_count": len(actions),
            "workbench_actions_preview_only": True,
        },
    )


def _graph_with_captures(
    graph: GraphFakosGraph,
    captures: tuple[GraphFakosKnowledgeCapture, ...],
) -> GraphFakosGraph:
    if not captures:
        return graph
    node_ids = {node.id for node in graph.nodes}
    nodes = list(graph.nodes)
    edges = list(graph.edges)
    for index, capture in enumerate(captures, start=1):
        node_id = f"capture:{index:03d}"
        label = _capture_label(capture.text)
        kind = capture.kind or "note"
        nodes.append(
            GraphFakosNode(
                id=node_id,
                label=label,
                kind=kind,
                summary=capture.text,
                tags=capture.tags,
                source=capture.source or "workbench",
                timestamps={"created_at": capture.created_at}
                if capture.created_at
                else {},
                provenance_ids=("prov:demo-generator",),
                citation_ids=("cite:demo-contract",),
                visual=_visual_for(kind),
                provider_payload={"capture": capture.to_dict()},
            )
        )
        if capture.link_node_id and capture.link_node_id in node_ids:
            edges.append(
                GraphFakosEdge(
                    id=f"edge:capture:{index:03d}",
                    source_id=capture.link_node_id,
                    target_id=node_id,
                    kind=capture.link_edge_kind or "mentions",
                    label=capture.link_edge_kind or "mentions",
                    confidence=1.0,
                    provenance_ids=("prov:demo-generator",),
                    citation_ids=("cite:demo-contract",),
                )
            )
        node_ids.add(node_id)
    return replace(
        graph,
        nodes=tuple(nodes),
        edges=tuple(edges),
        stats={
            **graph.stats,
            "capture_count": len(captures),
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        available_facets=_facets(tuple(nodes), tuple(edges)),
        provider_payload={
            **graph.provider_payload,
            "workbench_capture_count": len(captures),
        },
    )


def _capture_label(text: str) -> str:
    line = next((item.strip() for item in text.splitlines() if item.strip()), "Note")
    return line if len(line) <= 48 else f"{line[:45]}..."


def _normalize_scenario(scenario: str) -> str:
    value = (scenario or "agent-memory").strip().lower().replace("_", "-")
    if value not in DEMO_SCENARIOS:
        allowed = ", ".join(DEMO_SCENARIOS)
        raise ValueError(
            f"Unknown demo scenario {scenario!r}; expected one of: {allowed}"
        )
    return value


__all__ = [
    "DEMO_SCENARIOS",
    "DemoGraphProvider",
    "build_demo_baseline_graph",
    "build_demo_graph",
    "build_demo_overlay_graphs",
]
