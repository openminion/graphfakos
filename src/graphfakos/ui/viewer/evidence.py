"""Path and evidence summary presentation."""

from __future__ import annotations

from collections import defaultdict
from html import escape

from graphfakos.models import GraphFakosEdge, GraphFakosGraph, GraphFakosNode
from graphfakos.ui.viewer.html import (
    empty as _empty,
    key_values as _key_values,
    panel_body as _panel_body,
    summary_note as _summary_note,
    text_list as _list,
)


def _path_summary(
    source: GraphFakosNode,
    target: GraphFakosNode,
    path_edges: list[GraphFakosEdge],
) -> str:
    if not path_edges:
        return _empty(
            f"No bounded path connects {source.label} to {target.label} in the current graph view."
        )
    hop_count = len(path_edges)
    return (
        _summary_note(
            f"{hop_count} edge hop(s) connect {source.label} to {target.label}."
        )
        + _list(
            [
                f"{edge.source_id} -> {edge.target_id} ({edge.label or edge.kind})"
                for edge in path_edges
            ]
        )
        + f"<p class='gf-empty'>Route starts at {escape(source.id)} and ends at {escape(target.id)}.</p>"
    )


def _evidence_summary(graph: GraphFakosGraph) -> str:
    node_provenance = sum(1 for node in graph.nodes if node.provenance_ids)
    node_citations = sum(1 for node in graph.nodes if node.citation_ids)
    edge_provenance = sum(1 for edge in graph.edges if edge.provenance_ids)
    edge_citations = sum(1 for edge in graph.edges if edge.citation_ids)
    provider_counts = _count_rows(
        item.provider_id or "unknown" for item in graph.provenance
    )
    source_type_counts = _count_rows(
        item.source_type or "unknown" for item in graph.provenance
    )
    citation_counts = _count_rows(
        item.path or item.uri or "inline" for item in graph.citations
    )
    return (
        _key_values(
            {
                "node provenance": f"{node_provenance} / {len(graph.nodes)}",
                "node citations": f"{node_citations} / {len(graph.nodes)}",
                "edge provenance": f"{edge_provenance} / {len(graph.edges)}",
                "edge citations": f"{edge_citations} / {len(graph.edges)}",
                "provenance providers": len(
                    {item.provider_id for item in graph.provenance}
                ),
                "source types": len(
                    {item.source_type for item in graph.provenance if item.source_type}
                ),
            }
        )
        + _panel_body("Provider Coverage", _list(provider_counts))
        + _panel_body("Source Types", _list(source_type_counts))
        + _panel_body("Citation Locations", _list(citation_counts))
    )


def _count_rows(values: object) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        if isinstance(value, str) and value:
            counts[value] += 1
    return [
        f"{label}: {count}"
        for label, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0].casefold()),
        )[:6]
    ]
