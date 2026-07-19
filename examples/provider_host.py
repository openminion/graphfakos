"""Minimal third-party host integration for GraphFakos.

Run with:

    python examples/provider_host.py

The example keeps provider truth and persistence in the host class while
GraphFakos owns DTOs, route state, static rendering, and local action payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from graphfakos import (
    GraphFakosActionStatus,
    GraphFakosCitation,
    GraphFakosEdge,
    GraphFakosGraph,
    GraphFakosGraphAction,
    GraphFakosKnowledgeCapture,
    GraphFakosNode,
    GraphFakosProvider,
    GraphFakosRequest,
    render_static_html,
)


@dataclass
class ThirdPartyHostProvider(GraphFakosProvider):
    provider_id = "third_party_host"
    provider_label = "Third-party Host"
    graph_role = "third_party"
    capabilities = (
        "search",
        "neighborhood",
        "path",
        "provider_status",
        "static_export",
        "knowledge_capture",
        "graph_action",
    )

    captured_notes: list[GraphFakosKnowledgeCapture] = field(default_factory=list)
    action_statuses: list[GraphFakosActionStatus] = field(default_factory=list)

    def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
        note_nodes = tuple(
            GraphFakosNode(
                id=f"note:{index}",
                label=f"Captured note {index}",
                kind=capture.kind,
                summary=capture.text,
                tags=capture.tags,
                source=capture.source,
                citation_ids=("cite:host-doc",),
            )
            for index, capture in enumerate(self.captured_notes, start=1)
        )
        action_nodes = tuple(
            GraphFakosNode(
                id=f"action:{index}",
                label=status.status.title(),
                kind="action",
                summary=status.message,
                tags=("action", status.status),
                source="host_action_log",
            )
            for index, status in enumerate(self.action_statuses, start=1)
        )
        nodes = (
            GraphFakosNode(
                id="host:package",
                label="Package Host",
                kind="provider",
                summary="The package owns graph truth and action persistence.",
                tags=("host", "provider"),
                source="third_party_host",
                citation_ids=("cite:host-doc",),
            ),
            GraphFakosNode(
                id="doc:integration",
                label="Integration Surface",
                kind="document",
                summary="GraphFakos renders the provider-neutral graph and forms.",
                tags=("docs", "integration"),
                source="third_party_host",
                citation_ids=("cite:host-doc",),
            ),
            *note_nodes,
            *action_nodes,
        )
        edges = (
            GraphFakosEdge(
                id="edge:host-doc",
                source_id="host:package",
                target_id="doc:integration",
                kind="documents",
                label="documents",
            ),
            *tuple(
                GraphFakosEdge(
                    id=f"edge:note:{index}",
                    source_id="host:package",
                    target_id=f"note:{index}",
                    kind="captured",
                    label="captured",
                )
                for index, _capture in enumerate(self.captured_notes, start=1)
            ),
            *tuple(
                GraphFakosEdge(
                    id=f"edge:action:{index}",
                    source_id=f"action:{index}",
                    target_id="host:package",
                    kind="targets",
                    label="targets",
                )
                for index, _status in enumerate(self.action_statuses, start=1)
            ),
        )
        return GraphFakosGraph(
            graph_id="third_party_host",
            label="Third-party Host Graph",
            provider_id=self.provider_id,
            provider_label=self.provider_label,
            graph_role=self.graph_role,
            capabilities=self.capabilities,
            nodes=nodes,
            edges=edges,
            citations=(
                GraphFakosCitation(
                    id="cite:host-doc",
                    label="Host integration example",
                    path="examples/provider_host.py",
                    line=1,
                ),
            ),
            stats={
                "captures": len(self.captured_notes),
                "actions": len(self.action_statuses),
                "request_screen": request.screen,
            },
            provider_payload={
                "host_boundary": (
                    "GraphFakos renders and submits provider-neutral payloads; "
                    "this host owns persistence decisions."
                )
            },
        )

    def capture_knowledge(
        self,
        capture: GraphFakosKnowledgeCapture,
    ) -> dict[str, object]:
        self.captured_notes.append(capture)
        status = GraphFakosActionStatus(
            action_id=f"capture:{len(self.captured_notes)}",
            status="applied",
            message="Host accepted the provider-neutral capture payload.",
            graph_id="third_party_host",
        )
        return {"ok": True, "status": status.to_dict(), "capture": capture.to_dict()}

    def submit_graph_action(
        self,
        action: GraphFakosGraphAction,
    ) -> GraphFakosActionStatus:
        status = GraphFakosActionStatus(
            action_id=action.action_id,
            status="previewed",
            message="Host previewed the graph action; persistence stays host-owned.",
            graph_id="third_party_host",
            provider_payload={"preview_only": True, "action_type": action.action_type},
        )
        self.action_statuses.append(status)
        return status


def render_preview_html(provider: ThirdPartyHostProvider | None = None) -> str:
    return render_static_html(provider or ThirdPartyHostProvider(), GraphFakosRequest())


def main() -> None:
    output = Path("third-party-host-graph.html")
    output.write_text(render_preview_html(), encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
