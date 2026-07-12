"""Provider-neutral graph snapshot diff calculation and presentation."""

from __future__ import annotations

from collections import defaultdict
from html import escape

from graphfakos.models import GraphFakosGraph
from graphfakos.ui.viewer.html import empty as _empty, text_list as _list


def build_graph_diff(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
) -> dict[str, object]:
    current_node_map = graph.node_map()
    comparison_node_map = comparison_graph.node_map()
    current_edge_map = graph.edge_map()
    comparison_edge_map = comparison_graph.edge_map()
    current_node_payloads = {
        node_id: node.to_dict() for node_id, node in current_node_map.items()
    }
    comparison_node_payloads = {
        node_id: node.to_dict() for node_id, node in comparison_node_map.items()
    }
    current_edge_payloads = {
        edge_id: edge.to_dict() for edge_id, edge in current_edge_map.items()
    }
    comparison_edge_payloads = {
        edge_id: edge.to_dict() for edge_id, edge in comparison_edge_map.items()
    }
    current_node_ids = {node.id for node in graph.nodes}
    comparison_node_ids = {node.id for node in comparison_graph.nodes}
    current_edge_ids = {edge.id for edge in graph.edges}
    comparison_edge_ids = {edge.id for edge in comparison_graph.edges}
    changed_node_details = _changed_item_details(
        current_node_ids & comparison_node_ids,
        current_node_payloads,
        comparison_node_payloads,
    )
    changed_edge_details = _changed_item_details(
        current_edge_ids & comparison_edge_ids,
        current_edge_payloads,
        comparison_edge_payloads,
    )
    changed_nodes = _changed_item_summaries(changed_node_details)
    changed_edges = _changed_item_summaries(changed_edge_details)
    snapshot_changes, snapshot_fields = _snapshot_changes(graph, comparison_graph)
    return {
        "summary": {
            "current nodes": len(graph.nodes),
            "comparison nodes": len(comparison_graph.nodes),
            "current edges": len(graph.edges),
            "comparison edges": len(comparison_graph.edges),
            "added node count": len(current_node_ids - comparison_node_ids),
            "removed node count": len(comparison_node_ids - current_node_ids),
            "added edge count": len(current_edge_ids - comparison_edge_ids),
            "removed edge count": len(comparison_edge_ids - current_edge_ids),
            "changed node count": len(changed_nodes),
            "changed edge count": len(changed_edges),
            "snapshot change count": len(snapshot_changes),
            "change hotspot count": len(
                _change_hotspots(
                    changed_node_details,
                    changed_edge_details,
                    snapshot_fields,
                )
            ),
        },
        "added_nodes": tuple(sorted(current_node_ids - comparison_node_ids)),
        "removed_nodes": tuple(sorted(comparison_node_ids - current_node_ids)),
        "changed_nodes": changed_nodes,
        "changed_node_details": tuple(
            {"id": item_id, "fields": list(fields)}
            for item_id, fields in changed_node_details
        ),
        "added_edges": tuple(sorted(current_edge_ids - comparison_edge_ids)),
        "removed_edges": tuple(sorted(comparison_edge_ids - current_edge_ids)),
        "changed_edges": changed_edges,
        "changed_edge_details": tuple(
            {"id": item_id, "fields": list(fields)}
            for item_id, fields in changed_edge_details
        ),
        "snapshot_changes": snapshot_changes,
        "change_hotspots": _change_hotspots(
            changed_node_details,
            changed_edge_details,
            snapshot_fields,
        ),
    }


def _snapshot_changes(
    graph: GraphFakosGraph,
    comparison_graph: GraphFakosGraph,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if graph.snapshot is None and comparison_graph.snapshot is None:
        return (), ()
    current = graph.snapshot.to_dict() if graph.snapshot is not None else {}
    comparison = (
        comparison_graph.snapshot.to_dict()
        if comparison_graph.snapshot is not None
        else {}
    )
    if current == comparison:
        return (), ()
    fields = _changed_fields(current, comparison)
    return (_changed_field_summary("snapshot", fields),), fields


def _changed_item_details(
    item_ids: set[str],
    current_payloads: dict[str, dict[str, object]],
    comparison_payloads: dict[str, dict[str, object]],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        sorted(
            (
                item_id,
                _changed_fields(
                    current_payloads[item_id],
                    comparison_payloads[item_id],
                ),
            )
            for item_id in item_ids
            if current_payloads[item_id] != comparison_payloads[item_id]
        )
    )


def _changed_field_summary(
    item_id: str,
    changed_fields: tuple[str, ...],
) -> str:
    return f"{item_id}: {', '.join(changed_fields)}"


def _changed_fields(
    current: dict[str, object],
    comparison: dict[str, object],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            key
            for key in set(current) | set(comparison)
            if current.get(key) != comparison.get(key)
        )
    )


def _changed_item_summaries(
    details: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[str, ...]:
    return tuple(_changed_field_summary(item_id, fields) for item_id, fields in details)


def _change_hotspots(
    changed_node_details: tuple[tuple[str, tuple[str, ...]], ...],
    changed_edge_details: tuple[tuple[str, tuple[str, ...]], ...],
    snapshot_fields: tuple[str, ...],
) -> tuple[str, ...]:
    counts: dict[str, int] = defaultdict(int)
    for _item_id, fields in (*changed_node_details, *changed_edge_details):
        for field in fields:
            counts[field] += 1
    for field in snapshot_fields:
        counts[f"snapshot.{field}"] += 1
    if not counts:
        return ()
    return tuple(
        f"{field}: {count}"
        for field, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0].casefold()),
        )
    )


def _diff_section(title: str, items: tuple[str, ...]) -> str:
    return f"<h4>{escape(title)}</h4>{_list(items)}"


def _overlay_summary(overlay_graphs: tuple[GraphFakosGraph, ...]) -> str:
    if not overlay_graphs:
        return _empty("No overlay provider graphs are available.")
    rows = [
        f"{graph.provider_label}: {len(graph.nodes)} nodes, {len(graph.edges)} edges"
        for graph in overlay_graphs
    ]
    return _list(rows)
