from __future__ import annotations

from dataclasses import replace

import pytest

from graphfakos import GraphFakosEdge, GraphFakosGraph, GraphFakosNode
from graphfakos.live import (
    GraphFakosGraphPatch,
    GraphFakosGraphRevision,
    GraphFakosLiveGraphState,
    GraphFakosLiveReplayBundle,
    GraphFakosLiveSessionCursor,
    GraphFakosLiveSessionRequest,
    GraphFakosPatchOperation,
    InMemoryGraphFakosLiveProvider,
    apply_graph_patch,
)


def _graph() -> GraphFakosGraph:
    return GraphFakosGraph(
        graph_id="live",
        label="Live graph",
        provider_id="fixture",
        provider_label="Fixture",
        graph_role="knowledge",
        capabilities=("live",),
        nodes=(GraphFakosNode(id="a", label="A", kind="item"),),
        edges=(),
    )


def _patch(
    *operations: GraphFakosPatchOperation, index: int = 1
) -> GraphFakosGraphPatch:
    return GraphFakosGraphPatch(
        patch_id=f"patch-{index}",
        base_revision=GraphFakosGraphRevision(str(index - 1)),
        result_revision=GraphFakosGraphRevision(str(index)),
        cursor=GraphFakosLiveSessionCursor(f"cursor-{index}"),
        operations=operations,
        occurred_at="2026-07-12T00:00:00Z",
    )


def test_live_patch_dtos_round_trip_all_operation_kinds() -> None:
    graph = _graph()
    patch = _patch(
        GraphFakosPatchOperation(
            kind="node_upsert", node=GraphFakosNode(id="b", label="B", kind="item")
        ),
        GraphFakosPatchOperation(
            kind="edge_upsert",
            edge=GraphFakosEdge(id="ab", source_id="a", target_id="b", kind="related"),
        ),
        GraphFakosPatchOperation(kind="edge_delete", target_id="old-edge"),
        GraphFakosPatchOperation(kind="node_delete", target_id="old-node"),
        GraphFakosPatchOperation(kind="graph_metadata_merge", metadata={"x": 1}),
        GraphFakosPatchOperation(kind="graph_metadata_replace", metadata={}),
        GraphFakosPatchOperation(kind="snapshot_reset", graph=graph),
    )

    assert GraphFakosGraphPatch.from_dict(patch.to_dict()) == patch


def test_patch_application_is_atomic_ordered_and_idempotent() -> None:
    state = GraphFakosLiveGraphState(
        graph=_graph(), revision=GraphFakosGraphRevision("0")
    )
    patch = _patch(
        GraphFakosPatchOperation(
            kind="node_upsert", node=GraphFakosNode(id="b", label="B", kind="item")
        ),
        GraphFakosPatchOperation(
            kind="edge_upsert",
            edge=GraphFakosEdge(id="ab", source_id="a", target_id="b", kind="related"),
        ),
        GraphFakosPatchOperation(kind="graph_metadata_merge", metadata={"live": True}),
    )

    updated = apply_graph_patch(state, patch)

    assert set(updated.graph.node_map()) == {"a", "b"}
    assert set(updated.graph.edge_map()) == {"ab"}
    assert updated.graph.provider_payload == {"live": True}
    assert updated.revision.value == "1"
    assert apply_graph_patch(updated, patch) is updated


def test_patch_failure_does_not_mutate_original_state() -> None:
    state = GraphFakosLiveGraphState(
        graph=_graph(), revision=GraphFakosGraphRevision("0")
    )
    patch = _patch(
        GraphFakosPatchOperation(
            kind="edge_upsert",
            edge=GraphFakosEdge(
                id="missing", source_id="a", target_id="missing", kind="related"
            ),
        )
    )

    with pytest.raises(ValueError, match="missing endpoint"):
        apply_graph_patch(state, patch)

    assert state.graph == _graph()


def test_patch_rejects_wrong_revision_and_requires_explicit_cascade() -> None:
    graph = replace(
        _graph(),
        nodes=(
            GraphFakosNode(id="a", label="A", kind="item"),
            GraphFakosNode(id="b", label="B", kind="item"),
        ),
        edges=(GraphFakosEdge(id="ab", source_id="a", target_id="b", kind="related"),),
    )
    state = GraphFakosLiveGraphState(graph=graph, revision=GraphFakosGraphRevision("0"))
    wrong_revision = replace(
        _patch(GraphFakosPatchOperation(kind="edge_delete", target_id="ab")),
        base_revision=GraphFakosGraphRevision("other"),
    )
    with pytest.raises(ValueError, match="does not match"):
        apply_graph_patch(state, wrong_revision)
    with pytest.raises(ValueError, match="explicit incident"):
        apply_graph_patch(
            state,
            _patch(GraphFakosPatchOperation(kind="node_delete", target_id="a")),
        )


def test_bounded_reference_provider_reports_overflow_reconnect_and_resync() -> None:
    provider = InMemoryGraphFakosLiveProvider(
        revision=GraphFakosGraphRevision("0"), max_queue=1
    )
    provider.publish_patch(
        _patch(GraphFakosPatchOperation(kind="edge_delete", target_id="x"))
    )
    provider.publish_patch(
        _patch(GraphFakosPatchOperation(kind="edge_delete", target_id="y"), index=2)
    )
    request = GraphFakosLiveSessionRequest(
        session_id="session", cursor=GraphFakosLiveSessionCursor("expired")
    )

    provider.open_live_session(request)
    status = provider.load_patch(request)
    diagnostics = provider.diagnostics()

    assert status.status == "resync_required"
    assert diagnostics.queue_depth == 1
    assert diagnostics.overflow_count == 1
    assert diagnostics.reconnect_count == 1
    assert diagnostics.resync_count == 1


def test_live_replay_bundle_round_trips_and_reaches_declared_revision() -> None:
    patch = _patch(
        GraphFakosPatchOperation(
            kind="node_upsert", node=GraphFakosNode(id="b", label="B", kind="item")
        )
    )
    bundle = GraphFakosLiveReplayBundle(
        initial_graph=_graph(),
        initial_revision=GraphFakosGraphRevision("0"),
        patches=(patch,),
        final_revision=GraphFakosGraphRevision("1"),
    )

    rebuilt = GraphFakosLiveReplayBundle.from_dict(bundle.to_dict())

    assert rebuilt == bundle
    assert set(rebuilt.replay().graph.node_map()) == {"a", "b"}
    with pytest.raises(ValueError, match="final revision"):
        replace(rebuilt, final_revision=GraphFakosGraphRevision("wrong")).replay()


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ({"kind": "unknown"}, "unsupported"),
        ({"kind": "node_upsert"}, "missing its payload"),
        ({"kind": "node_delete", "target_id": 3}, "must be a string"),
        (
            {"kind": "graph_metadata_merge", "metadata": {"bad": object()}},
            "JSON-compatible",
        ),
    ],
)
def test_malformed_operations_fail_clearly(
    operation: dict[str, object], message: str
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        GraphFakosPatchOperation.from_dict(operation)
