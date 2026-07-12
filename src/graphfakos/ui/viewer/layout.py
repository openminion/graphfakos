"""Deterministic graph coordinate and force-layout calculations."""

from __future__ import annotations

from collections import defaultdict, deque
from math import cos, pi, sin, sqrt

from graphfakos.models import GraphFakosGraph, GraphFakosNode, GraphFakosRequest
from graphfakos.ui.viewer.graph_ops import (
    _adjacency_map,
    _node_cluster_id,
    _node_degree_map,
    _preferred_focus_node,
    _ranked_nodes,
)


def _layout_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if request.layout == "timeline":
        positions = _timeline_positions(graph, width, height)
    elif request.layout == "circle":
        positions = _ring_positions(graph, width, height)
    elif request.layout == "grouped":
        positions = _grouped_positions(graph, width, height)
    elif request.layout == "focus":
        positions = _focus_positions(graph, width, height, focus_node_id)
    elif request.layout == "radial":
        positions = _radial_positions(graph, width, height, focus_node_id)
    elif request.layout == "hierarchical":
        positions = _hierarchical_positions(graph, width, height, focus_node_id)
    else:
        positions = _force_positions(graph, request, width, height, focus_node_id)
    return _apply_pinned_positions(graph, request, positions, width, height)


def _force_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if not graph.nodes:
        return {}
    anchor = _force_anchor_id(graph, focus_node_id)
    adjacency = _adjacency_map(graph)
    degree_map = _node_degree_map(graph)
    center = (width / 2, height / 2)
    positions = {anchor: center}
    inner_ring = sorted(
        {
            neighbor_id
            for _edge, neighbor_id in adjacency.get(anchor, ())
            if neighbor_id != anchor
        },
        key=lambda node_id: (
            -degree_map.get(node_id, 0),
            graph.node_map()
            .get(node_id, GraphFakosNode(id=node_id, label=node_id, kind="node"))
            .label.casefold(),
        ),
    )
    outer_nodes = [
        node
        for node in _ranked_nodes(graph, {anchor, *inner_ring})
        if node.id not in {anchor, *inner_ring}
    ]
    distance_scale = _clamped(request.link_distance, 0.45, 2.2)
    inner_radius = min(width, height) * 0.2 * distance_scale
    outer_radius = min(width, height) * 0.36 * distance_scale
    for index, node_id in enumerate(inner_ring):
        angle = (2 * pi * index / max(len(inner_ring), 1)) - (pi / 2)
        positions[node_id] = (
            center[0] + inner_radius * cos(angle),
            center[1] + inner_radius * sin(angle),
        )
    for index, node in enumerate(outer_nodes):
        angle = (2 * pi * index / max(len(outer_nodes), 1)) - (pi / 2)
        positions[node.id] = (
            center[0] + outer_radius * cos(angle),
            center[1] + outer_radius * sin(angle),
        )
    for node in graph.nodes:
        positions.setdefault(node.id, center)
    return _relax_force_positions(graph, request, positions, anchor, width, height)


def _force_anchor_id(graph: GraphFakosGraph, focus_node_id: str | None) -> str:
    node_ids = {node.id for node in graph.nodes}
    if focus_node_id and focus_node_id in node_ids:
        return focus_node_id
    focus = _preferred_focus_node(graph, GraphFakosRequest())
    return (focus or graph.nodes[0]).id


def _relax_force_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    positions: dict[str, tuple[float, float]],
    anchor: str,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    node_ids = [node.id for node in _ranked_nodes(graph, set())]
    if len(node_ids) <= 2:
        return _bounded_positions(graph, positions, anchor, width, height)
    margin = 46.0
    area = max((width - margin * 2) * (height - margin * 2), 1.0)
    ideal_distance = (
        sqrt(area / len(node_ids)) * 0.82 * _clamped(request.link_distance, 0.45, 2.2)
    )
    fixed_ids = {
        node.id
        for node in graph.nodes
        if node.id == anchor
        or (
            node.visual.pinned
            and node.visual.x is not None
            and node.visual.y is not None
        )
    }
    positions = _bounded_positions(graph, positions, anchor, width, height)
    for step in range(72):
        temperature = max(2.5, ideal_distance * (1 - step / 72) * 0.34)
        shifts = {node_id: [0.0, 0.0] for node_id in node_ids}
        for left_index, left_id in enumerate(node_ids):
            left_x, left_y = positions[left_id]
            for right_id in node_ids[left_index + 1 :]:
                right_x, right_y = positions[right_id]
                dx = left_x - right_x
                dy = left_y - right_y
                distance = sqrt(dx * dx + dy * dy) or 0.01
                force = (
                    (ideal_distance * ideal_distance)
                    / distance
                    * _clamped(request.repel_force, 0.1, 4.0)
                )
                offset_x = dx / distance * force
                offset_y = dy / distance * force
                shifts[left_id][0] += offset_x
                shifts[left_id][1] += offset_y
                shifts[right_id][0] -= offset_x
                shifts[right_id][1] -= offset_y
        for edge in graph.edges:
            if edge.source_id not in positions or edge.target_id not in positions:
                continue
            source_x, source_y = positions[edge.source_id]
            target_x, target_y = positions[edge.target_id]
            dx = source_x - target_x
            dy = source_y - target_y
            distance = sqrt(dx * dx + dy * dy) or 0.01
            force = (distance * distance) / max(ideal_distance, 1.0)
            offset_x = dx / distance * force * 0.62
            offset_y = dy / distance * force * 0.62
            shifts[edge.source_id][0] -= offset_x
            shifts[edge.source_id][1] -= offset_y
            shifts[edge.target_id][0] += offset_x
            shifts[edge.target_id][1] += offset_y
        for node_id in node_ids:
            if node_id in fixed_ids:
                continue
            x, y = positions[node_id]
            shift_x, shift_y = shifts[node_id]
            length = sqrt(shift_x * shift_x + shift_y * shift_y) or 1.0
            move = min(length, temperature)
            next_x = x + shift_x / length * move
            next_y = y + shift_y / length * move
            center_pull = (
                request.center_force if step > 36 else request.center_force / 2
            )
            next_x += (width / 2 - next_x) * center_pull
            next_y += (height / 2 - next_y) * center_pull
            positions[node_id] = _bounded_point(next_x, next_y, width, height, margin)
    return _bounded_positions(graph, positions, anchor, width, height)


def _apply_pinned_positions(
    graph: GraphFakosGraph,
    request: GraphFakosRequest,
    positions: dict[str, tuple[float, float]],
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    if not request.pinned_positions:
        return positions
    pinned = dict(positions)
    for node in graph.nodes:
        if node.id not in request.pinned_positions:
            continue
        x, y = request.pinned_positions[node.id]
        pinned[node.id] = _bounded_point(x, y, width, height, 46.0)
    return pinned


def _bounded_positions(
    graph: GraphFakosGraph,
    positions: dict[str, tuple[float, float]],
    anchor: str,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    bounded: dict[str, tuple[float, float]] = {}
    margin = 46.0
    for node in graph.nodes:
        if node.id == anchor:
            bounded[node.id] = (width / 2, height / 2)
            continue
        if (
            node.visual.pinned
            and node.visual.x is not None
            and node.visual.y is not None
        ):
            bounded[node.id] = _bounded_point(
                node.visual.x,
                node.visual.y,
                width,
                height,
                margin,
            )
            continue
        x, y = positions.get(node.id, (width / 2, height / 2))
        bounded[node.id] = _bounded_point(x, y, width, height, margin)
    return bounded


def _bounded_point(
    x: float,
    y: float,
    width: int,
    height: int,
    margin: float,
) -> tuple[float, float]:
    return (
        min(max(x, margin), width - margin),
        min(max(y, margin), height - margin),
    )


def _ring_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    center_x = width / 2
    center_y = height / 2
    radius = min(width, height) * 0.34
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(_ranked_nodes(graph, set())):
        angle = (2 * pi * index / max(len(graph.nodes), 1)) - (pi / 2)
        x = (
            node.visual.x
            if node.visual.x is not None
            else center_x + radius * cos(angle)
        )
        y = (
            node.visual.y
            if node.visual.y is not None
            else center_y + radius * sin(angle)
        )
        positions[node.id] = (x, y)
    return positions


def _grouped_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    groups: dict[str, list[GraphFakosNode]] = defaultdict(list)
    for node in _ranked_nodes(graph, set()):
        groups[_node_cluster_id(node) or node.kind or "node"].append(node)
    positions: dict[str, tuple[float, float]] = {}
    group_names = sorted(groups)
    if not group_names:
        return positions
    center_x = width / 2
    center_y = height / 2
    orbit_x = width * 0.36
    orbit_y = height * 0.32
    for group_index, group_name in enumerate(group_names):
        angle = (2 * pi * group_index / max(len(group_names), 1)) - (pi / 2)
        cluster_nodes = groups[group_name]
        cluster_center_x = center_x + orbit_x * cos(angle)
        cluster_center_y = center_y + orbit_y * sin(angle)
        local_radius = max(22.0, min(120.0, 18.0 + len(cluster_nodes) * 1.8))
        for node_index, node in enumerate(cluster_nodes):
            if node_index == 0:
                positions[node.id] = _bounded_point(
                    cluster_center_x,
                    cluster_center_y,
                    width,
                    height,
                    34.0,
                )
                continue
            local_angle = node_index * 2.399963229728653
            local_distance = min(local_radius, 14 + sqrt(node_index) * 12)
            positions[node.id] = _bounded_point(
                cluster_center_x + local_distance * cos(local_angle),
                cluster_center_y + local_distance * sin(local_angle),
                width,
                height,
                34.0,
            )
    return positions


def _timeline_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
) -> dict[str, tuple[float, float]]:
    ordered = sorted(
        graph.nodes,
        key=lambda node: (
            min(node.timestamps.values()) if node.timestamps else node.label.casefold()
        ),
    )
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(ordered):
        x = 100 + index * max((width - 180) / max(len(ordered) - 1, 1), 1)
        y = 150 if index % 2 else height - 140
        positions[node.id] = (x, y)
    return positions


def _focus_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    anchor = focus_node_id
    if not anchor:
        focus = _preferred_focus_node(graph, GraphFakosRequest())
        anchor = focus.id if focus is not None else None
    positions = _ring_positions(graph, width, height)
    if not anchor or anchor not in positions:
        return positions
    positions[anchor] = (width / 2, height / 2)
    remaining = [node for node in _ranked_nodes(graph, {anchor}) if node.id != anchor]
    radius = min(width, height) * 0.24
    for index, node in enumerate(remaining):
        angle = 2 * pi * index / max(len(remaining), 1)
        positions[node.id] = (
            width / 2 + radius * cos(angle),
            height / 2 + radius * sin(angle),
        )
    return positions


def _radial_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if not graph.nodes:
        return {}
    anchor = focus_node_id or graph.nodes[0].id
    adjacency = _adjacency_map(graph)
    center = (width / 2, height / 2)
    positions = {anchor: center}
    rings: dict[int, list[str]] = defaultdict(list)
    frontier: deque[tuple[str, int]] = deque([(anchor, 0)])
    seen = {anchor}
    while frontier:
        node_id, depth = frontier.popleft()
        for _edge, next_id in adjacency.get(node_id, ()):
            if next_id in seen:
                continue
            seen.add(next_id)
            rings[depth + 1].append(next_id)
            frontier.append((next_id, depth + 1))
    unseen = [node.id for node in _ranked_nodes(graph, seen) if node.id not in seen]
    if unseen:
        rings[max(rings.keys(), default=0) + 1].extend(unseen)
    for depth, node_ids in sorted(rings.items()):
        radius = min(width, height) * min(0.16 + depth * 0.11, 0.42)
        for index, node_id in enumerate(node_ids):
            angle = (2 * pi * index / max(len(node_ids), 1)) - (pi / 2)
            positions[node_id] = (
                center[0] + radius * cos(angle),
                center[1] + radius * sin(angle),
            )
    for node in graph.nodes:
        positions.setdefault(node.id, center)
    return positions


def _hierarchical_positions(
    graph: GraphFakosGraph,
    width: int,
    height: int,
    focus_node_id: str | None,
) -> dict[str, tuple[float, float]]:
    if not graph.nodes:
        return {}
    adjacency = _adjacency_map(graph)
    anchor = focus_node_id or _ranked_nodes(graph, set())[0].id
    levels: dict[int, list[str]] = defaultdict(list)
    frontier: deque[tuple[str, int]] = deque([(anchor, 0)])
    seen = {anchor}
    while frontier:
        node_id, depth = frontier.popleft()
        levels[depth].append(node_id)
        for _edge, next_id in adjacency.get(node_id, ()):
            if next_id in seen:
                continue
            seen.add(next_id)
            frontier.append((next_id, depth + 1))
    remaining = [node.id for node in _ranked_nodes(graph, seen) if node.id not in seen]
    if remaining:
        levels[max(levels.keys(), default=0) + 1].extend(remaining)
    positions: dict[str, tuple[float, float]] = {}
    level_count = max(len(levels), 1)
    for level_index, node_ids in sorted(levels.items()):
        y = 80 + level_index * max((height - 160) / max(level_count - 1, 1), 1)
        for index, node_id in enumerate(node_ids):
            x = 90 + index * max((width - 180) / max(len(node_ids) - 1, 1), 1)
            positions[node_id] = (x, y)
    return positions


def _clamped(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
