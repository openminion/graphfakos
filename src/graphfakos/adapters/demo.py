"""Deterministic demo graphs for viewer iteration."""

from __future__ import annotations

from dataclasses import replace

from graphfakos.models import (
    GraphFakosCitation,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosKnowledgeCapture,
    GraphFakosNode,
    GraphFakosProvenance,
    GraphFakosRequest,
    GraphFakosSnapshot,
    GraphFakosVisual,
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
    "budget",
    "islands",
)

_KIND_STYLES = {
    "agent": ("#2563eb", "circle"),
    "artifact": ("#d97706", "pill"),
    "chunk": ("#0891b2", "circle"),
    "decision": ("#7c3aed", "diamond"),
    "document": ("#16a34a", "diamond"),
    "event": ("#db2777", "circle"),
    "file": ("#0f766e", "square"),
    "memory": ("#dc2626", "circle"),
    "module": ("#475569", "square"),
    "note": ("#246c5c", "circle"),
    "provider": ("#111827", "square"),
    "question": ("#ca8a04", "diamond"),
    "session": ("#4f46e5", "pill"),
    "symbol": ("#9333ea", "circle"),
    "task": ("#0f766e", "pill"),
    "test": ("#65a30d", "pill"),
    "tool": ("#0284c7", "circle"),
    "warning": ("#ea580c", "diamond"),
}


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
    )

    def __init__(self, scenario: str = "agent-memory") -> None:
        self.scenario = _normalize_scenario(scenario)
        self._captures: list[GraphFakosKnowledgeCapture] = []

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        graph = build_demo_graph(self.scenario, request)
        return _graph_with_captures(graph, tuple(self._captures))

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


def _agent_memory_graph() -> tuple[
    tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]
]:
    rows = (
        ("provider:openminion", "OpenMinion Runtime", "provider", "provider runtime"),
        ("agent:codex", "Codex Agent", "agent", "agent runtime"),
        ("session:design-review", "Design Review Session", "session", "session review"),
        (
            "memory:operator-prefers-commands",
            "Prefers Copyable Commands",
            "memory",
            "memory preference",
        ),
        ("memory:ui-polish", "Viewer Polish Preference", "memory", "memory ui"),
        (
            "decision:server-workbench",
            "Server Workbench Direction",
            "decision",
            "decision viewer",
        ),
        (
            "document:dynamic-viewer-spec",
            "Dynamic Viewer Spec",
            "document",
            "document spec",
        ),
        ("artifact:preview-html", "Preview HTML Export", "artifact", "artifact export"),
        ("tool:browser-preview", "Browser Preview Tool", "tool", "tool browser"),
        ("event:fragment-loaded", "Fragment Loaded Event", "event", "event browser"),
        ("chunk:provider-contract", "Provider Contract Chunk", "chunk", "chunk docs"),
        (
            "warning:stale-preview",
            "Stale Static Preview Warning",
            "warning",
            "warning static",
        ),
    )
    edges = (
        ("edge:runtime-hosts-agent", "provider:openminion", "agent:codex", "hosts"),
        (
            "edge:agent-observes-session",
            "agent:codex",
            "session:design-review",
            "observes",
        ),
        (
            "edge:session-records-pref",
            "session:design-review",
            "memory:operator-prefers-commands",
            "records",
        ),
        (
            "edge:session-records-ui",
            "session:design-review",
            "memory:ui-polish",
            "records",
        ),
        (
            "edge:ui-supports-decision",
            "memory:ui-polish",
            "decision:server-workbench",
            "supports",
        ),
        (
            "edge:commands-support-decision",
            "memory:operator-prefers-commands",
            "decision:server-workbench",
            "supports",
        ),
        (
            "edge:decision-updates-spec",
            "decision:server-workbench",
            "document:dynamic-viewer-spec",
            "updates",
        ),
        (
            "edge:spec-produces-artifact",
            "document:dynamic-viewer-spec",
            "artifact:preview-html",
            "produces",
        ),
        (
            "edge:tool-loads-artifact",
            "tool:browser-preview",
            "artifact:preview-html",
            "loads",
        ),
        (
            "edge:event-confirms-tool",
            "event:fragment-loaded",
            "tool:browser-preview",
            "confirms",
        ),
        (
            "edge:chunk-documents-spec",
            "chunk:provider-contract",
            "document:dynamic-viewer-spec",
            "documents",
        ),
        (
            "edge:warning-flags-artifact",
            "warning:stale-preview",
            "artifact:preview-html",
            "flags",
        ),
    )
    return _nodes(rows), _edges(edges)


def _source_code_graph() -> tuple[
    tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]
]:
    rows = (
        ("module:graphfakos", "graphfakos package", "module", "module package"),
        ("file:server", "server.py", "file", "file server"),
        ("file:viewer-js", "assets/viewer.js", "file", "file browser"),
        ("file:ui-app", "ui/app.py", "file", "file renderer"),
        ("file:models", "models.py", "file", "file dto"),
        ("symbol:serve-local", "serve_local_viewer", "symbol", "symbol server"),
        ("symbol:viewer-element", "<graphfakos-viewer>", "symbol", "symbol browser"),
        ("symbol:request", "GraphFakosRequest", "symbol", "symbol dto"),
        ("symbol:provider", "GraphFakosProvider", "symbol", "symbol protocol"),
        ("test:server", "test_local_preview_server", "test", "test server"),
        ("test:browser", "test_browser_runtime", "test", "test browser"),
        ("document:ui-contracts", "UI Contracts Doc", "document", "document contract"),
        ("artifact:wheel", "Built Wheel", "artifact", "artifact package"),
    )
    edges = (
        ("edge:module-owns-server", "module:graphfakos", "file:server", "owns"),
        ("edge:module-owns-viewer", "module:graphfakos", "file:viewer-js", "owns"),
        ("edge:module-owns-ui", "module:graphfakos", "file:ui-app", "owns"),
        ("edge:module-owns-models", "module:graphfakos", "file:models", "owns"),
        ("edge:server-defines-serve", "file:server", "symbol:serve-local", "defines"),
        (
            "edge:viewer-defines-element",
            "file:viewer-js",
            "symbol:viewer-element",
            "defines",
        ),
        ("edge:models-define-request", "file:models", "symbol:request", "defines"),
        ("edge:models-define-provider", "file:models", "symbol:provider", "defines"),
        ("edge:test-covers-server", "test:server", "symbol:serve-local", "covers"),
        ("edge:test-covers-viewer", "test:browser", "symbol:viewer-element", "covers"),
        (
            "edge:docs-describe-element",
            "document:ui-contracts",
            "symbol:viewer-element",
            "describes",
        ),
        ("edge:wheel-packages-viewer", "artifact:wheel", "file:viewer-js", "packages"),
        ("edge:ui-uses-request", "file:ui-app", "symbol:request", "uses"),
        ("edge:server-renders-ui", "file:server", "file:ui-app", "renders"),
    )
    return _nodes(rows), _edges(edges)


def _dense_graph() -> tuple[tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]]:
    rows: list[tuple[str, str, str, str]] = []
    for cluster in range(1, 7):
        rows.append(
            (
                f"provider:cluster-{cluster}",
                f"Provider Cluster {cluster}",
                "provider",
                "provider cluster",
            )
        )
        for item in range(1, 6):
            kind = ("memory", "document", "artifact", "tool", "session")[item - 1]
            rows.append(
                (
                    f"{kind}:c{cluster}-{item}",
                    f"{kind.title()} C{cluster}.{item}",
                    kind,
                    f"{kind} cluster-{cluster} dense",
                )
            )
    edges: list[tuple[str, str, str, str]] = []
    for cluster in range(1, 7):
        hub = f"provider:cluster-{cluster}"
        member_ids = [
            f"{kind}:c{cluster}-{index}"
            for index, kind in enumerate(
                ("memory", "document", "artifact", "tool", "session"), start=1
            )
        ]
        for member in member_ids:
            edges.append((f"edge:{hub}:{member}", hub, member, "serves"))
        for left, right in zip(member_ids, member_ids[1:]):
            edges.append((f"edge:{left}:{right}", left, right, "relates"))
        next_hub = f"provider:cluster-{(cluster % 6) + 1}"
        edges.append((f"edge:{hub}:{next_hub}", hub, next_hub, "cross-links"))
    return _nodes(tuple(rows)), _edges(tuple(edges))


def _timeline_graph() -> tuple[tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]]:
    rows: list[tuple[str, str, str, str]] = []
    for day in range(1, 19):
        kind = ("event", "memory", "document", "artifact", "decision", "test")[day % 6]
        rows.append(
            (
                f"{kind}:timeline-{day:02d}",
                f"{kind.title()} Timeline {day:02d}",
                kind,
                f"{kind} timeline day-{day:02d}",
            )
        )
    edges = [
        (
            f"edge:timeline-{day:02d}-{day + 1:02d}",
            rows[day - 1][0],
            rows[day][0],
            "precedes",
        )
        for day in range(1, len(rows))
    ]
    edges.extend(
        (
            ("edge:timeline-01-09", rows[0][0], rows[8][0], "revisits"),
            ("edge:timeline-03-15", rows[2][0], rows[14][0], "revisits"),
            ("edge:timeline-06-18", rows[5][0], rows[17][0], "produces"),
        )
    )
    return _nodes(tuple(rows)), _edges(tuple(edges))


def _warnings_graph() -> tuple[tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]]:
    rows = (
        ("provider:healthy", "Healthy Provider", "provider", "provider healthy"),
        ("provider:stale", "Stale Provider", "warning", "provider warning stale"),
        ("memory:isolated", "Isolated Memory", "memory", "memory isolated"),
        (
            "document:missing-citation",
            "Missing Citation Doc",
            "document",
            "document warning",
        ),
        ("artifact:partial-export", "Partial Export", "artifact", "artifact partial"),
        ("tool:retry", "Retry Tool", "tool", "tool recovery"),
        ("event:timeout", "Timeout Event", "event", "event warning"),
        (
            "decision:manual-review",
            "Manual Review Required",
            "decision",
            "decision warning",
        ),
    )
    edges = (
        (
            "edge:healthy-serves-doc",
            "provider:healthy",
            "document:missing-citation",
            "serves",
        ),
        (
            "edge:stale-flags-doc",
            "provider:stale",
            "document:missing-citation",
            "flags",
        ),
        (
            "edge:doc-produces-partial",
            "document:missing-citation",
            "artifact:partial-export",
            "produces",
        ),
        ("edge:timeout-triggers-retry", "event:timeout", "tool:retry", "triggers"),
        (
            "edge:retry-escalates-review",
            "tool:retry",
            "decision:manual-review",
            "escalates",
        ),
    )
    return _nodes(rows), _edges(edges)


def _pathfinding_graph() -> tuple[
    tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]
]:
    rows = (
        ("provider:entry", "Entry Provider", "provider", "provider path source"),
        ("session:request", "Request Session", "session", "session path"),
        ("memory:constraint", "User Constraint", "memory", "memory path"),
        ("decision:route", "Route Decision", "decision", "decision path"),
        ("document:plan", "Execution Plan", "document", "document path"),
        ("tool:validator", "Validator Tool", "tool", "tool path"),
        ("artifact:result", "Result Artifact", "artifact", "artifact path target"),
        ("warning:dead-end", "Dead-end Candidate", "warning", "warning path"),
        ("document:alternate", "Alternate Plan", "document", "document branch"),
        ("test:path-proof", "Path Proof Test", "test", "test path"),
    )
    edges = (
        ("edge:path-01", "provider:entry", "session:request", "receives"),
        ("edge:path-02", "session:request", "memory:constraint", "uses"),
        ("edge:path-03", "memory:constraint", "decision:route", "shapes"),
        ("edge:path-04", "decision:route", "document:plan", "produces"),
        ("edge:path-05", "document:plan", "tool:validator", "validates"),
        ("edge:path-06", "tool:validator", "artifact:result", "emits"),
        ("edge:path-branch-01", "session:request", "document:alternate", "branches"),
        ("edge:path-branch-02", "document:alternate", "warning:dead-end", "dead-ends"),
        ("edge:path-proof", "test:path-proof", "artifact:result", "covers"),
    )
    return _nodes(rows), _edges(edges)


def _evidence_graph() -> tuple[tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]]:
    rows = (
        ("provider:evidence", "Evidence Provider", "provider", "provider evidence"),
        ("document:spec", "Spec Section", "document", "document evidence citation"),
        ("chunk:markdown", "Markdown Chunk", "chunk", "chunk evidence citation"),
        ("memory:decision", "Remembered Decision", "memory", "memory evidence"),
        ("event:review", "Review Event", "event", "event evidence"),
        ("artifact:report", "Evidence Report", "artifact", "artifact evidence"),
        ("test:coverage", "Coverage Test", "test", "test evidence"),
        ("warning:weak-claim", "Weak Claim", "warning", "warning evidence"),
    )
    edges = (
        ("edge:evidence-serves-spec", "provider:evidence", "document:spec", "serves"),
        ("edge:evidence-spec-chunk", "document:spec", "chunk:markdown", "contains"),
        ("edge:evidence-chunk-memory", "chunk:markdown", "memory:decision", "supports"),
        ("edge:evidence-review-memory", "event:review", "memory:decision", "confirms"),
        (
            "edge:evidence-memory-report",
            "memory:decision",
            "artifact:report",
            "exports",
        ),
        ("edge:evidence-test-report", "test:coverage", "artifact:report", "covers"),
        (
            "edge:evidence-warning-memory",
            "warning:weak-claim",
            "memory:decision",
            "flags",
        ),
    )
    nodes = list(_nodes(rows))
    edges_out = list(_edges(edges))
    nodes[1] = replace(
        nodes[1],
        provenance_ids=("prov:demo-spec",),
        citation_ids=("cite:demo-spec",),
    )
    nodes[2] = replace(
        nodes[2],
        provenance_ids=("prov:demo-markdown",),
        citation_ids=("cite:demo-markdown",),
    )
    nodes[3] = replace(
        nodes[3],
        provenance_ids=("prov:demo-session", "prov:demo-markdown"),
        citation_ids=("cite:demo-spec", "cite:demo-markdown"),
    )
    edges_out[2] = replace(
        edges_out[2],
        provenance_ids=("prov:demo-markdown",),
        citation_ids=("cite:demo-markdown",),
    )
    edges_out[3] = replace(
        edges_out[3],
        provenance_ids=("prov:demo-session",),
        citation_ids=("cite:demo-session",),
    )
    return tuple(nodes), tuple(edges_out)


def _facets_graph() -> tuple[tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]]:
    rows = (
        ("provider:memory", "Memory Provider", "provider", "provider memory trust"),
        ("provider:source", "Source Provider", "provider", "provider source freshness"),
        ("provider:eval", "Eval Provider", "provider", "provider eval scoring"),
        ("memory:preference", "Preference Memory", "memory", "memory preference trust"),
        ("memory:policy", "Policy Memory", "memory", "memory policy trust"),
        ("file:runtime", "runtime.py", "file", "source runtime freshness"),
        ("file:test", "test_runtime.py", "file", "source test coverage"),
        ("symbol:runner", "Runner Symbol", "symbol", "source runtime symbol"),
        ("document:readme", "README Section", "document", "docs onboarding source"),
        ("artifact:eval-report", "Eval Report", "artifact", "eval scoring artifact"),
        ("test:smoke", "Smoke Test", "test", "eval smoke coverage"),
        ("warning:low-score", "Low Score Warning", "warning", "eval warning scoring"),
    )
    nodes = list(_nodes(rows))
    for index, node in enumerate(nodes):
        source = ("memory-demo", "source-demo", "eval-demo")[index % 3]
        nodes[index] = replace(node, source=source)
    edges = (
        ("edge:facet-01", "provider:memory", "memory:preference", "serves"),
        ("edge:facet-02", "provider:memory", "memory:policy", "serves"),
        ("edge:facet-03", "provider:source", "file:runtime", "indexes"),
        ("edge:facet-04", "provider:source", "file:test", "indexes"),
        ("edge:facet-05", "file:runtime", "symbol:runner", "defines"),
        ("edge:facet-06", "document:readme", "file:runtime", "documents"),
        ("edge:facet-07", "provider:eval", "artifact:eval-report", "emits"),
        ("edge:facet-08", "test:smoke", "artifact:eval-report", "covers"),
        ("edge:facet-09", "warning:low-score", "artifact:eval-report", "flags"),
        ("edge:facet-10", "memory:policy", "symbol:runner", "constrains"),
    )
    return tuple(nodes), _edges(edges)


def _budget_graph() -> tuple[tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]]:
    rows: list[tuple[str, str, str, str]] = []
    kinds = ("memory", "document", "artifact", "tool", "session", "event", "test")
    for index in range(1, 86):
        kind = kinds[index % len(kinds)]
        rows.append(
            (
                f"{kind}:budget-{index:03d}",
                f"{kind.title()} Budget {index:03d}",
                kind,
                f"{kind} budget page-{(index - 1) // 10 + 1}",
            )
        )
    edges = [
        (
            f"edge:budget-chain-{index:03d}",
            rows[index - 1][0],
            rows[index][0],
            "streams-to",
        )
        for index in range(1, len(rows))
    ]
    edges.extend(
        (
            (
                f"edge:budget-cross-{index:03d}",
                rows[index][0],
                rows[index + 10][0],
                "cross-links",
            )
            for index in range(0, len(rows) - 10, 10)
        )
    )
    return _nodes(tuple(rows)), _edges(tuple(edges))


def _islands_graph() -> tuple[tuple[GraphFakosNode, ...], tuple[GraphFakosEdge, ...]]:
    rows = (
        ("provider:primary", "Primary Provider", "provider", "provider primary"),
        ("memory:primary-a", "Primary Memory A", "memory", "memory primary"),
        ("document:primary-b", "Primary Document B", "document", "document primary"),
        ("artifact:primary-c", "Primary Artifact C", "artifact", "artifact primary"),
        ("provider:secondary", "Secondary Provider", "provider", "provider secondary"),
        ("memory:secondary-a", "Secondary Memory A", "memory", "memory secondary"),
        (
            "document:secondary-b",
            "Secondary Document B",
            "document",
            "document secondary",
        ),
        ("event:orphan-a", "Orphan Event A", "event", "event orphan"),
        ("warning:orphan-b", "Orphan Warning B", "warning", "warning orphan"),
        ("test:orphan-c", "Orphan Test C", "test", "test orphan"),
    )
    edges = (
        ("edge:island-main-01", "provider:primary", "memory:primary-a", "serves"),
        ("edge:island-main-02", "memory:primary-a", "document:primary-b", "supports"),
        ("edge:island-main-03", "document:primary-b", "artifact:primary-c", "produces"),
        (
            "edge:island-secondary-01",
            "provider:secondary",
            "memory:secondary-a",
            "serves",
        ),
        (
            "edge:island-secondary-02",
            "memory:secondary-a",
            "document:secondary-b",
            "supports",
        ),
    )
    return _nodes(rows), _edges(edges)


def _nodes(rows: tuple[tuple[str, str, str, str], ...]) -> tuple[GraphFakosNode, ...]:
    nodes: list[GraphFakosNode] = []
    for index, (node_id, label, kind, tag_text) in enumerate(rows, start=1):
        color, shape = _KIND_STYLES.get(kind, ("#64748b", "circle"))
        nodes.append(
            GraphFakosNode(
                id=node_id,
                label=label,
                kind=kind,
                summary=f"Synthetic {kind} node for GraphFakos viewer iteration.",
                tags=tuple(sorted(set(tag_text.split()))),
                score=round(1.0 - (index % 9) * 0.06, 2),
                confidence=round(0.72 + (index % 5) * 0.05, 2),
                source="demo",
                timestamps={
                    "observed_at": f"2026-06-{((index - 1) % 28) + 1:02d}T09:00:00+00:00"
                },
                provenance_ids=("prov:demo-generator",),
                citation_ids=("cite:demo-contract",),
                visual=GraphFakosVisual(
                    color=color,
                    shape=shape,
                    size=2 if index <= 3 else 1,
                    group=kind,
                    pinned=index <= 2,
                ),
                provider_payload={
                    "demo_index": index,
                    "iteration_note": "safe synthetic data",
                },
            )
        )
    return tuple(nodes)


def _visual_for(kind: str) -> GraphFakosVisual:
    color, shape = _KIND_STYLES.get(kind, ("#64748b", "circle"))
    return GraphFakosVisual(color=color, shape=shape, size=2, group=kind, pinned=True)


def _edges(rows: tuple[tuple[str, str, str, str], ...]) -> tuple[GraphFakosEdge, ...]:
    return tuple(
        GraphFakosEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            kind=kind,
            label=kind,
            weight=round(0.8 + (index % 4) * 0.2, 2),
            confidence=round(0.74 + (index % 5) * 0.04, 2),
            provenance_ids=("prov:demo-generator",),
            citation_ids=("cite:demo-contract",),
            visual=GraphFakosVisual(
                color="#64748b",
                shape="line",
                size=1 + (index % 3),
            ),
        )
        for index, (edge_id, source_id, target_id, kind) in enumerate(rows, start=1)
    )


def _provenance(scenario: str) -> tuple[GraphFakosProvenance, ...]:
    items = [
        GraphFakosProvenance(
            id="prov:demo-generator",
            provider_id="demo",
            source_type="synthetic",
            source_label="GraphFakos demo generator",
            excerpt="Deterministic mock data for viewer iteration.",
            observed_at="2026-07-01T00:00:00+00:00",
            confidence=1.0,
        )
    ]
    if scenario == "provenance":
        items.extend(
            (
                GraphFakosProvenance(
                    id="prov:demo-spec",
                    provider_id="demo",
                    source_type="document",
                    source_label="Dynamic viewer spec",
                    source_uri="https://github.com/openminion/graphfakos",
                    excerpt="Spec evidence attached to document nodes.",
                    observed_at="2026-06-29T12:00:00+00:00",
                    confidence=0.93,
                ),
                GraphFakosProvenance(
                    id="prov:demo-markdown",
                    provider_id="demo",
                    source_type="markdown",
                    source_label="README chunk",
                    excerpt="Markdown evidence attached to chunk and memory nodes.",
                    observed_at="2026-06-30T15:00:00+00:00",
                    confidence=0.88,
                ),
                GraphFakosProvenance(
                    id="prov:demo-session",
                    provider_id="demo",
                    source_type="session",
                    source_label="Review session",
                    excerpt="Session evidence attached to review-confirmed edges.",
                    observed_at="2026-07-01T09:00:00+00:00",
                    confidence=0.8,
                ),
            )
        )
    return tuple(items)


def _citations(scenario: str) -> tuple[GraphFakosCitation, ...]:
    items = [
        GraphFakosCitation(
            id="cite:demo-contract",
            label="GraphFakos UI Contracts",
            path="docs/ui-contracts.md",
            line=1,
            excerpt="Provider-neutral viewer contract for demo iteration.",
        )
    ]
    if scenario == "provenance":
        items.extend(
            (
                GraphFakosCitation(
                    id="cite:demo-spec",
                    label="Dynamic Viewer Spec",
                    path="docs/specs/graphfakos-dynamic-viewer-workbench-2026-07-01-spec.md",
                    line=1,
                    excerpt="Dynamic viewer workbench requirements.",
                ),
                GraphFakosCitation(
                    id="cite:demo-markdown",
                    label="README Demo Section",
                    path="README.md",
                    line=1,
                    excerpt="Generated demo scenario commands.",
                ),
                GraphFakosCitation(
                    id="cite:demo-session",
                    label="Review Session Note",
                    path="docs/README.md",
                    line=1,
                    excerpt="Evidence surfaced during synthetic review.",
                ),
            )
        )
    return tuple(items)


def _facets(
    nodes: tuple[GraphFakosNode, ...],
    edges: tuple[GraphFakosEdge, ...],
) -> dict[str, tuple[str, ...]]:
    tags = sorted({tag for node in nodes for tag in node.tags})
    return {
        "node_kind": tuple(sorted({node.kind for node in nodes})),
        "edge_kind": tuple(sorted({edge.kind for edge in edges})),
        "tag": tuple(tags),
        "source": tuple(sorted({node.source for node in nodes if node.source})),
    }


def _scenario_warnings(scenario: str) -> tuple[str, ...]:
    if scenario == "warnings":
        return (
            "synthetic stale provider warning",
            "synthetic isolated node for disconnected-state review",
        )
    if scenario == "dense":
        return ("dense graph intentionally stresses edge clutter and group controls",)
    if scenario == "islands":
        return ("synthetic disconnected islands for provider-status diagnostics",)
    if scenario == "budget":
        return ("synthetic large graph for render-budget and show-more review",)
    return ()


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
