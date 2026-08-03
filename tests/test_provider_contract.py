from __future__ import annotations

import pytest

from graphfakos import (
    SUPPORTED_RENDER_ENGINES,
    DemoGraphProvider,
    FixtureGraphProvider,
    GraphFakosActionStatus,
    GraphFakosCameraPose,
    GraphFakosConnectionExplanation,
    GraphFakosEdge,
    GraphFakosExpansionRequest,
    GraphFakosGraph,
    GraphFakosGraphAction,
    GraphFakosGraphAnalytics,
    GraphFakosInspectorField,
    GraphFakosInspectorSchema,
    GraphFakosInvestigationSession,
    GraphFakosKnowledgeCapture,
    GraphFakosNode,
    GraphFakosPerformanceBudget,
    GraphFakosPerspective,
    GraphFakosProgressiveCluster,
    GraphFakosReplayBundle,
    GraphFakosRequest,
    GraphFakosSavedQuery,
    GraphFakosSavedView,
    GraphFakosTheme,
    GraphFakosViewerCommand,
    GraphFakosViewerEvent,
    GraphFakosViewerState,
    GraphFakosWorkspaceManifest,
    analyze_graph,
    build_fixture_graph,
    build_graph_replay_bundle,
    build_graph_report,
    build_viewer_route,
    diagnose_graph,
    explain_connection,
    load_comparison_graph,
    load_expanded_graph,
    load_overlay_graphs,
    load_provider_graph,
    parse_viewer_request,
    query_syntax_reference,
    render_graph_dot,
    render_static_html,
    review_preset_manifest,
    validate_graph,
    validate_render_engine,
    workspace_manifest_for_graph,
)
from graphfakos.testing import (
    GraphFakosProviderConformanceCase,
    assert_graph_dot_contract,
    assert_provider_conformance,
    assert_review_preset_contract,
)


def test_fixture_provider_satisfies_provider_contract() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())

    assert graph.provider_id == "fixture"
    assert graph.graph_role == "third_party"
    assert len(graph.nodes) == 4
    assert len(graph.edges) == 4
    assert graph.provenance
    assert graph.citations
    assert graph.provider_details["owner"] == "OpenMinion fixture"
    assert "diff" in graph.capability_details
    assert graph.snapshot is not None
    assert graph.snapshot.snapshot_id == "fixture-current"


def test_fixture_provider_satisfies_reusable_conformance_case(tmp_path) -> None:
    result = assert_provider_conformance(
        GraphFakosProviderConformanceCase(
            provider=FixtureGraphProvider(),
            request=GraphFakosRequest(screen="explore"),
            expected_role="third_party",
            expected_provider="Fixture Provider",
            expected_node="Operator Preference",
            expected_edge="supports",
            required_capabilities=(
                "search",
                "neighborhood",
                "path",
                "provider_status",
                "static_export",
            ),
            artifact_path=tmp_path / "fixture-graph.json",
        )
    )

    assert result.graph.provider_id == "fixture"
    assert result.replay_graph is not None
    assert result.report["saved_view"]


def test_validate_graph_rejects_unknown_edge_references() -> None:
    graph = GraphFakosGraph(
        graph_id="bad",
        label="Bad Graph",
        provider_id="bad",
        provider_label="Bad Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(GraphFakosNode(id="known", label="Known", kind="node"),),
        edges=(
            GraphFakosEdge(
                id="bad-edge",
                source_id="known",
                target_id="missing",
                kind="bad",
            ),
        ),
    )

    with pytest.raises(ValueError, match="unknown target"):
        validate_graph(graph)


def test_validate_graph_rejects_duplicate_edge_ids() -> None:
    graph = GraphFakosGraph(
        graph_id="bad",
        label="Bad Graph",
        provider_id="bad",
        provider_label="Bad Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(
            GraphFakosNode(id="one", label="One", kind="node"),
            GraphFakosNode(id="two", label="Two", kind="node"),
        ),
        edges=(
            GraphFakosEdge(
                id="duplicate",
                source_id="one",
                target_id="two",
                kind="relates",
            ),
            GraphFakosEdge(
                id="duplicate",
                source_id="two",
                target_id="one",
                kind="relates",
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate edge ids"):
        validate_graph(graph)


def test_diagnose_graph_reports_provider_neutral_health() -> None:
    graph = GraphFakosGraph(
        graph_id="diagnostic",
        label="Diagnostic Graph",
        provider_id="diagnostic",
        provider_label="Diagnostic Provider",
        graph_role="third_party",
        capabilities=(),
        nodes=(
            GraphFakosNode(
                id="one",
                label="One",
                kind="node",
                provenance_ids=("missing-provenance",),
            ),
            GraphFakosNode(id="two", label="Two", kind="node"),
            GraphFakosNode(
                id="orphan",
                label="Orphan",
                kind="node",
                citation_ids=("missing-citation",),
            ),
        ),
        edges=(
            GraphFakosEdge(
                id="edge",
                source_id="one",
                target_id="two",
                kind="relates",
            ),
        ),
        warnings=("provider warning",),
    )

    diagnostics = diagnose_graph(graph)

    assert diagnostics.healthy is False
    assert diagnostics.orphan_node_ids == ("orphan",)
    assert diagnostics.unknown_provenance_ids == ("missing-provenance",)
    assert diagnostics.unknown_citation_ids == ("missing-citation",)
    assert diagnostics.disconnected_node_ids == ("orphan",)
    assert diagnostics.to_dict()["warnings"] == ["provider warning"]


def test_graph_to_dict_is_provider_neutral() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    payload = graph.to_dict()

    assert payload["provider_id"] == "fixture"
    assert payload["graph_role"] == "third_party"
    assert len(payload["nodes"]) == 4
    assert len(payload["edges"]) == 4
    assert payload["available_facets"]["node_kind"] == [
        "artifact",
        "document",
        "memory",
        "provider",
    ]


def test_workspace_manifest_captures_progressive_viewer_contract() -> None:
    request = GraphFakosRequest(
        screen="explore",
        focus_node_id="provider:cluster-1",
        render_engine="3d",
        theme="space",
        layout="islands",
        render_limit=40,
        saved_view_id="ops-review",
    )
    graph = load_provider_graph(DemoGraphProvider(), request)
    manifest = workspace_manifest_for_graph(graph, request)
    payload = manifest.to_dict()
    restored = GraphFakosWorkspaceManifest.from_dict(payload)

    assert restored.schema_version == "graphfakos.workspace.v1"
    assert restored.graph_id == graph.graph_id
    assert restored.provider_id == "demo"
    assert restored.viewer_state.theme == "space"
    assert restored.saved_view is not None
    assert restored.saved_view.state.render_engine == "3d"
    assert restored.desktop_backend_path == "/explore"
    assert restored.supported_actions == (
        "draft_node",
        "draft_edge",
        "retag_group",
        "merge_alias",
    )
    assert restored.supported_captures == (
        "note",
        "question",
        "observation",
        "task",
    )
    assert "inspect_node" in restored.viewer_actions
    assert "show_provenance" in restored.viewer_actions
    assert restored.provider_status["provider_id"] == "demo"
    assert restored.provider_status["provider_label"] == "Demo Data Provider"
    assert restored.provider_status["available_facets"]
    assert restored.default_expansion_requests[0].source_id == "provider:cluster-1"
    assert restored.performance_budget is not None
    assert restored.performance_budget.rendered_node_count == len(graph.nodes)
    assert restored.clusters
    assert restored.clusters[0].visible_node_ids


def test_progressive_cluster_and_budget_contracts_round_trip() -> None:
    request = GraphFakosRequest(render_limit=12)
    graph = load_provider_graph(DemoGraphProvider(), request)
    manifest = workspace_manifest_for_graph(graph, request)
    assert manifest.clusters
    assert manifest.performance_budget is not None

    cluster = manifest.clusters[0]
    budget = manifest.performance_budget

    restored_cluster = GraphFakosProgressiveCluster.from_dict(cluster.to_dict())
    restored_budget = GraphFakosPerformanceBudget.from_dict(budget.to_dict())

    assert restored_cluster.cluster_id == cluster.cluster_id
    assert restored_cluster.node_count >= len(restored_cluster.visible_node_ids)
    assert restored_cluster.omitted_node_count >= 0
    assert restored_budget.raw_node_count >= restored_budget.rendered_node_count
    assert restored_budget.raw_edge_count >= restored_budget.rendered_edge_count


def test_workspace_manifest_respects_provider_declared_affordances() -> None:
    graph = GraphFakosGraph(
        graph_id="narrow-provider",
        label="Narrow Provider",
        provider_id="narrow",
        provider_label="Narrow Provider",
        graph_role="third_party",
        capabilities=("graph_action", "knowledge_capture"),
        nodes=(GraphFakosNode(id="node:one", label="One", kind="note"),),
        edges=(),
        provider_payload={
            "supported_actions": ("draft_node",),
            "supported_captures": ("note",),
        },
    )
    manifest = workspace_manifest_for_graph(graph, GraphFakosRequest())

    assert manifest.supported_actions == ("draft_node",)
    assert manifest.supported_captures == ("note",)


def test_workspace_manifest_reads_affordances_from_viewer_envelope() -> None:
    graph = GraphFakosGraph(
        graph_id="envelope-backed",
        label="Envelope Backed",
        provider_id="envelope",
        provider_label="Envelope Provider",
        graph_role="third_party",
        capabilities=("graph_action", "knowledge_capture"),
        nodes=(
            GraphFakosNode(
                id="node:one",
                label="One",
                kind="note",
                provider_payload={"cluster_id": "note-cluster"},
            ),
        ),
        edges=(),
        provider_payload={
            "viewer_envelope": {
                "supported_actions": ("draft_node",),
                "supported_captures": ("question",),
                "viewer_actions": ("search", "inspect_node"),
                "clusters": (
                    {
                        "id": "note-cluster",
                        "node_count": 3,
                        "edge_count": 2,
                        "cursor": "next-page",
                    },
                ),
            },
        },
    )

    manifest = workspace_manifest_for_graph(graph, GraphFakosRequest())

    assert manifest.supported_actions == ("draft_node",)
    assert manifest.supported_captures == ("question",)
    assert manifest.viewer_actions == ("search", "inspect_node")
    assert manifest.clusters[0].cluster_id == "note-cluster"
    assert manifest.clusters[0].node_count == 3
    assert manifest.clusters[0].expansion_cursor == "next-page"


def test_workspace_manifest_respects_provider_declared_viewer_actions() -> None:
    graph = GraphFakosGraph(
        graph_id="viewer-actions",
        label="Viewer Actions",
        provider_id="actions",
        provider_label="Actions Provider",
        graph_role="third_party",
        capabilities=("provider_status",),
        nodes=(GraphFakosNode(id="node:one", label="One", kind="note"),),
        edges=(),
        provider_payload={"viewer_actions": ("search", "inspect_node")},
    )
    manifest = workspace_manifest_for_graph(graph, GraphFakosRequest())

    assert manifest.viewer_actions == ("search", "inspect_node")
    assert manifest.provider_status["capabilities"] == ["provider_status"]


def test_workspace_manifest_carries_empty_state_hint() -> None:
    graph = GraphFakosGraph(
        graph_id="empty",
        label="Empty Graph",
        provider_id="empty-provider",
        provider_label="Empty Provider",
        graph_role="third_party",
        capabilities=("provider_status",),
        nodes=(),
        edges=(),
        warnings=("Nothing matched the current filters.",),
        stats={"empty_code": "filtered_empty"},
    )
    manifest = workspace_manifest_for_graph(graph, GraphFakosRequest())
    restored = GraphFakosWorkspaceManifest.from_dict(manifest.to_dict())

    assert restored.empty_state == {
        "code": "filtered_empty",
        "message": "Nothing matched the current filters.",
    }


def test_fixture_provider_exposes_comparison_and_overlay_graphs() -> None:
    provider = FixtureGraphProvider()
    request = GraphFakosRequest(screen="diff")

    comparison = load_comparison_graph(provider, request)
    overlays = load_overlay_graphs(provider, request)

    assert comparison is not None
    assert comparison.provider_label == "Fixture Baseline"
    assert len(comparison.nodes) == 3
    assert overlays
    assert overlays[0].provider_label == "Overlay Provider"


def test_build_graph_report_includes_overlay_and_comparison() -> None:
    report = build_graph_report(
        FixtureGraphProvider(), GraphFakosRequest(screen="diff")
    )

    assert report["diagnostics"]["healthy"] is True
    assert report["comparison_graph"]["provider_label"] == "Fixture Baseline"
    assert report["comparison_diff"]["summary"]["changed node count"] == 0
    assert report["overlay_graphs"][0]["provider_label"] == "Overlay Provider"
    assert report["request"]["screen"] == "diff"
    assert report["viewer_state"]["screen"] == "diff"
    assert report["graph"]["snapshot"]["snapshot_id"] == "fixture-current"


def test_viewer_route_helpers_are_public_and_stable() -> None:
    request = GraphFakosRequest(
        screen="diff",
        preset_id="diff",
        query="kind:file has:provenance",
        focus_node_id="node:one",
        comparison_graph_id="baseline",
        render_limit=80,
        camera_x=11.25,
        camera_y=-3.5,
        camera_zoom=1.3,
        camera_yaw=18.0,
        camera_pitch=-9.0,
        camera_pose=GraphFakosCameraPose(
            position=(120.0, -42.5, 780.25),
            target=(18.0, 4.5, -9.0),
        ),
        center_force=0.0,
        label_density=0.0,
    )

    route = build_viewer_route(request)
    parsed = parse_viewer_request(
        "/diff",
        {
            "preset": ["diff"],
            "query": ["kind:file has:provenance"],
            "focus_node_id": ["node:one"],
            "comparison_graph_id": ["baseline"],
            "render_limit": ["80"],
            "camera_x": ["11.25"],
            "camera_y": ["-3.5"],
            "camera_zoom": ["1.3"],
            "camera_yaw": ["18"],
            "camera_pitch": ["-9"],
            "camera_pose": ["120,-42.5,780.25,18,4.5,-9"],
            "center_force": ["0"],
            "label_density": ["0"],
        },
    )

    assert route.startswith("/diff?")
    assert parsed.screen == "diff"
    assert parsed.preset_id == "diff"
    assert parsed.comparison_graph_id == "baseline"
    assert parsed.render_limit == 80
    assert parsed.camera_x == 11.25
    assert parsed.camera_y == -3.5
    assert parsed.camera_zoom == 1.3
    assert parsed.camera_yaw == 18.0
    assert parsed.camera_pitch == -9.0
    assert parsed.camera_pose == request.camera_pose
    assert parsed.center_force == 0.0
    assert parsed.label_density == 0.0
    assert "center_force=0.0" in route
    assert "label_density=0.0" in route
    assert "camera_pose=120.000000%2C-42.500000%2C780.250000" in route


@pytest.mark.parametrize(
    "value",
    (
        "nan,0,1,2,3,4",
        "0,inf,1,2,3,4",
        "0,1,2,3,4",
    ),
)
def test_camera_pose_rejects_invalid_route_values(value: str) -> None:
    with pytest.raises(ValueError):
        GraphFakosCameraPose.from_query_value(value)

    fallback = GraphFakosCameraPose(
        position=(0.0, 0.0, 720.0),
        target=(0.0, 0.0, 0.0),
    )
    parsed = parse_viewer_request(
        "/explore",
        {"camera_pose": [value]},
        base_request=GraphFakosRequest(camera_pose=fallback),
    )
    assert parsed.camera_pose == fallback


def test_camera_pose_rejects_non_finite_direct_values() -> None:
    with pytest.raises(ValueError, match="must be finite"):
        GraphFakosCameraPose(
            position=(0.0, float("nan"), 720.0),
            target=(0.0, 0.0, 0.0),
        )


def test_focused_request_normalizes_focus_as_primary_selection() -> None:
    state = GraphFakosViewerState.from_request(
        GraphFakosRequest(
            focus_node_id="provider:third-party",
            selected_node_ids=("memory:operator-preference",),
        )
    )

    assert state.selected_node_id == "provider:third-party"
    assert state.selected_node_ids == (
        "provider:third-party",
        "memory:operator-preference",
    )


def test_dynamic_viewer_contracts_round_trip() -> None:
    request = GraphFakosRequest(
        screen="explore",
        focus_node_id="provider:third-party",
        selected_edge_id="edge:provider-serves-spec",
        layout="radial",
        filters={"node_kind": "provider"},
        camera_x=4.5,
        camera_y=-2.0,
        camera_zoom=1.4,
        camera_yaw=24.0,
        camera_pitch=-16.0,
        camera_pose=GraphFakosCameraPose(
            position=(64.0, -18.0, 640.0),
            target=(12.0, 8.0, -4.0),
        ),
        selected_node_ids=("provider:third-party", "memory:operator-preference"),
        center_force=0.02,
        repel_force=1.4,
        link_distance=1.2,
        node_scale=1.15,
        edge_scale=1.25,
        edge_opacity=0.75,
        label_density=0.6,
        pinned_positions={"provider:third-party": (320.0, 180.0)},
        style_color_by="component",
        style_size_by="degree",
        style_edge_width_by="weight",
        min_degree=1,
        component_id="component:1",
        connected_to_node_id="provider:third-party",
        evidence_filter="with_provenance",
        timeline_frame="2026-06-25",
        timeline_playback="step",
        pivot_node_id="provider:third-party",
        pivot_mode="evidence_bundle",
    )

    state = GraphFakosViewerState.from_request(request)
    rebuilt_state = GraphFakosViewerState.from_dict(state.to_dict())
    command = GraphFakosViewerCommand(
        name="filter",
        target_id="node_kind",
        payload={"value": "provider"},
    )
    event = GraphFakosViewerEvent(
        name="graphfakos:filter",
        state=rebuilt_state,
        target_id="node_kind",
        payload={"value": "provider"},
    )
    expansion = GraphFakosExpansionRequest(
        source_id="provider:third-party", depth=2, cursor="expand:provider:2"
    )
    theme = GraphFakosTheme(
        id="review",
        label="Review",
        node_colors={"provider": "#0f766e"},
        edge_colors={"serves": "#64748b"},
        node_shapes={"provider": "square"},
    )

    assert rebuilt_state.selected_node_id == "provider:third-party"
    assert rebuilt_state.selected_node_ids == (
        "provider:third-party",
        "memory:operator-preference",
    )
    assert rebuilt_state.pinned_positions["provider:third-party"] == (320.0, 180.0)
    assert rebuilt_state.style_color_by == "component"
    assert rebuilt_state.camera_yaw == 24.0
    assert rebuilt_state.camera_pitch == -16.0
    assert rebuilt_state.camera_pose == request.camera_pose
    assert rebuilt_state.timeline_playback == "step"
    assert rebuilt_state.pivot_mode == "evidence_bundle"
    assert rebuilt_state.to_route_query()["node_kind"] == "provider"
    assert GraphFakosViewerCommand.from_dict(command.to_dict()).payload == {
        "value": "provider"
    }
    assert GraphFakosViewerEvent.from_dict(event.to_dict()).state.camera_zoom == 1.4
    assert GraphFakosViewerEvent.from_dict(event.to_dict()).state.camera_yaw == 24.0
    assert (
        GraphFakosViewerEvent.from_dict(event.to_dict()).state.camera_pose
        == request.camera_pose
    )
    assert GraphFakosExpansionRequest.from_dict(expansion.to_dict()).depth == 2
    assert (
        GraphFakosExpansionRequest.from_dict(expansion.to_dict()).cursor
        == "expand:provider:2"
    )
    assert "node color provider: #0f766e" in theme.caption()


def test_knowledge_capture_contract_round_trips_provider_payload() -> None:
    capture = GraphFakosKnowledgeCapture(
        text="Remember that graph navigation needs local depth controls.",
        kind="note",
        tags=("ui", "graph"),
        source="workbench",
        link_node_id="provider:third-party",
        link_edge_kind="mentions",
        provider_payload={"screen": "explore"},
    )

    rebuilt = GraphFakosKnowledgeCapture.from_dict(capture.to_dict())
    parsed_tags = GraphFakosKnowledgeCapture.from_dict(
        {
            "text": "Comma tags are accepted from lightweight clients.",
            "tags": "one, two",
        }
    )

    assert rebuilt.text.startswith("Remember")
    assert rebuilt.tags == ("ui", "graph")
    assert rebuilt.provider_payload["screen"] == "explore"
    assert parsed_tags.tags == ("one", "two")


def test_saved_view_action_analytics_and_replay_contracts_round_trip() -> None:
    graph = load_provider_graph(FixtureGraphProvider(), GraphFakosRequest())
    request = GraphFakosRequest(
        screen="neighborhood",
        focus_node_id="provider:third-party",
        saved_view_id="ops-review",
        render_engine="canvas",
        theme="ink",
        show_orphans=False,
        show_neighbor_links=False,
        edge_clutter="reduced",
        analytics_overlay="degree",
        pinned_positions={"provider:third-party": (310.0, 220.0)},
        selected_node_ids=("provider:third-party",),
        style_color_by="source",
        style_size_by="degree",
        style_edge_width_by="weight",
    )
    saved_query = GraphFakosSavedQuery(
        query_id="hubs",
        label="Find hubs",
        query="degree>=3",
    )
    saved_view = GraphFakosSavedView.from_request(
        request,
        view_id="ops-review",
        label="Operator review",
        saved_queries=(saved_query,),
    )
    action = GraphFakosGraphAction(
        action_id="draft:one",
        action_type="merge_alias",
        target_id="provider:third-party",
        label="Merge provider aliases",
    )
    status = GraphFakosActionStatus(
        action_id=action.action_id,
        status="queued",
        message="Queued for provider review.",
    )
    analytics = analyze_graph(graph)
    bundle = GraphFakosReplayBundle(
        bundle_id="fixture:ops-review",
        graph=graph,
        viewer_state=GraphFakosViewerState.from_request(request),
        saved_views=(saved_view,),
        analytics=analytics,
    )

    rebuilt_view = GraphFakosSavedView.from_dict(saved_view.to_dict())
    assert rebuilt_view.state.theme == "ink"
    assert rebuilt_view.state.show_orphans is False
    assert rebuilt_view.pinned_positions["provider:third-party"] == (310.0, 220.0)
    assert rebuilt_view.state.selected_node_ids == ("provider:third-party",)
    assert rebuilt_view.state.style_edge_width_by == "weight"
    assert (
        GraphFakosGraphAction.from_dict(action.to_dict()).action_type == "merge_alias"
    )
    assert GraphFakosActionStatus.from_dict(status.to_dict()).status == "queued"
    assert GraphFakosGraphAnalytics.from_dict(analytics.to_dict()).node_count == 4
    rebuilt_bundle = GraphFakosReplayBundle.from_dict(bundle.to_dict())
    assert rebuilt_bundle.viewer_state.render_engine == "canvas"
    assert rebuilt_bundle.saved_views[0].saved_queries[0].query == "degree>=3"


def test_investigation_session_and_connection_explanation_round_trip() -> None:
    request = GraphFakosRequest(
        screen="explore",
        focus_node_id="provider:third-party",
        selected_edge_id="edge:provider-serves-spec",
        selected_node_ids=("document:viewer-spec",),
        pinned_positions={"provider:third-party": (120.0, 80.0)},
    )
    graph = load_provider_graph(FixtureGraphProvider(), request)
    explanation = explain_connection(graph, "edge:provider-serves-spec")

    assert explanation is not None
    assert explanation.source_label == "Third-party Provider"
    assert explanation.target_label == "Viewer Spec"
    assert "serves" in explanation.summary

    session = GraphFakosInvestigationSession.from_request(
        request,
        session_id="fixture-session",
        label="Fixture Session",
        expansion_requests=(
            GraphFakosExpansionRequest(source_id="provider:third-party", depth=2),
        ),
        connection_explanations=(explanation,),
    )
    rebuilt = GraphFakosInvestigationSession.from_dict(session.to_dict())
    rebuilt_connection = GraphFakosConnectionExplanation.from_dict(
        explanation.to_dict()
    )

    assert rebuilt.session_id == "fixture-session"
    assert rebuilt.selected_edge_id == "edge:provider-serves-spec"
    assert rebuilt.expansion_requests[0].depth == 2
    assert rebuilt.connection_explanations[0].relationship == "serves"
    assert rebuilt_connection.citation_ids == ("cite:provider-doc",)


def test_viewer_declaration_contracts_round_trip() -> None:
    perspective = GraphFakosPerspective.from_dict(
        {
            "perspective_id": "evidence",
            "label": "Evidence",
            "filters": {"evidence_filter": "with_evidence"},
            "node_kinds": ["document"],
        }
    )
    schema = GraphFakosInspectorSchema.from_dict(
        {
            "schema_id": "document-inspector",
            "node_kind": "document",
            "fields": [{"key": "path", "label": "Path", "source": "provider_payload"}],
        }
    )

    assert GraphFakosPerspective.from_dict(perspective.to_dict()) == perspective
    assert GraphFakosInspectorSchema.from_dict(schema.to_dict()) == schema
    assert schema.fields == (
        GraphFakosInspectorField(
            key="path",
            label="Path",
            source="provider_payload",
        ),
    )


def test_graph_report_includes_investigation_session_and_connection_explanation() -> (
    None
):
    report = build_graph_report(
        FixtureGraphProvider(),
        GraphFakosRequest(
            screen="explore",
            focus_node_id="provider:third-party",
            selected_edge_id="edge:provider-serves-spec",
        ),
    )

    session = report["investigation_session"]
    explanations = report["connection_explanations"]

    assert isinstance(session, dict)
    assert session["selected_edge_id"] == "edge:provider-serves-spec"
    assert session["expansion_requests"][0]["source_id"] == "provider:third-party"
    assert isinstance(explanations, list)
    assert explanations[0]["relationship"] == "serves"


def test_demo_provider_expands_bounded_neighborhood() -> None:
    provider = DemoGraphProvider("workbench-mixed")
    request = GraphFakosRequest(screen="neighborhood", focus_node_id="agent:reviewer")
    expanded = load_expanded_graph(
        provider,
        request,
        GraphFakosExpansionRequest(source_id="agent:reviewer", depth=1),
    )

    assert expanded is not None
    assert expanded.graph_id.endswith(":expanded:agent:reviewer")
    assert expanded.stats["expanded_source_id"] == "agent:reviewer"
    assert 1 <= len(expanded.nodes) < len(provider.load_graph(request).nodes)


def test_demo_provider_satisfies_workflow_conformance(tmp_path) -> None:
    result = assert_provider_conformance(
        GraphFakosProviderConformanceCase(
            provider=DemoGraphProvider("workbench-mixed"),
            request=GraphFakosRequest(
                screen="explore",
                focus_node_id="agent:reviewer",
            ),
            required_capabilities=(
                "knowledge_capture",
                "graph_action",
                "lazy_expansion",
            ),
            artifact_path=tmp_path / "demo-workflow.json",
            expansion_request=GraphFakosExpansionRequest(
                source_id="agent:reviewer",
                depth=1,
            ),
            capture=GraphFakosKnowledgeCapture(
                text="Capture a provider-neutral workflow note.",
                kind="note",
                tags=("workflow", "provider"),
                source="test",
                link_node_id="agent:reviewer",
            ),
            action=GraphFakosGraphAction(
                action_id="draft:workflow",
                action_type="draft_edge",
                source_id="agent:reviewer",
                target_node_id="doc:architecture",
                label="Workflow proof",
            ),
            expected_action_status="previewed",
        )
    )

    assert result.replay_graph is not None


def test_build_graph_replay_bundle_uses_provider_neutral_state() -> None:
    bundle = build_graph_replay_bundle(
        FixtureGraphProvider(),
        GraphFakosRequest(
            screen="explore",
            focus_node_id="provider:third-party",
            saved_view_id="route-share",
            theme="paper",
            analytics_overlay="warnings",
        ),
    )

    assert bundle.bundle_id == "fixture:explore"
    assert bundle.viewer_state.theme == "paper"
    assert bundle.saved_views[0].view_id == "route-share"
    assert bundle.analytics.hub_node_ids


def test_renderer_selection_contract_rejects_unsupported_engines() -> None:
    assert SUPPORTED_RENDER_ENGINES == ("svg", "canvas", "3d")
    assert validate_render_engine("svg") == "svg"
    assert validate_render_engine("canvas") == "canvas"
    assert validate_render_engine("3d") == "3d"

    with pytest.raises(ValueError, match="unsupported GraphFakos render engine"):
        validate_render_engine("webgl")


def test_review_preset_manifest_exposes_shared_review_flows() -> None:
    provider = FixtureGraphProvider()
    request = GraphFakosRequest(screen="explore", focus_node_id="provider:third-party")
    graph = load_provider_graph(provider, request)
    comparison = load_comparison_graph(provider, GraphFakosRequest(screen="diff"))

    presets = review_preset_manifest(
        graph,
        request,
        comparison_graph=comparison,
    )

    assert_review_preset_contract(
        presets,
        required_ids=("overview", "focus", "evidence", "diff", "health", "context"),
    )


def test_render_graph_dot_exports_provider_neutral_edges() -> None:
    graph = build_fixture_graph()

    dot = render_graph_dot(graph)

    assert_graph_dot_contract(
        dot,
        expected_node_ids=("provider:third-party", "artifact:static-export"),
        expected_edge_ids=("serves", "supports"),
    )


def test_query_syntax_reference_documents_tokens() -> None:
    syntax = query_syntax_reference()

    assert any(item["token"] == "kind:<value>" for item in syntax)
    assert any(item["token"] == "has:provenance" for item in syntax)
    assert any(item["token"] == "score>=0.8" for item in syntax)
    assert any(item["token"] == '"quoted phrase"' for item in syntax)


def test_custom_provider_can_render_all_shared_screens() -> None:
    class CustomProvider:
        provider_id = "custom"
        provider_label = "Custom Provider"
        graph_role = "third_party"
        capabilities = (
            "search",
            "neighborhood",
            "path",
            "provenance",
            "timeline",
            "provider_status",
            "context_preview",
            "static_export",
        )

        def load_graph(self, request: GraphFakosRequest) -> GraphFakosGraph:
            return GraphFakosGraph(
                graph_id="custom",
                label="Custom Graph",
                provider_id=self.provider_id,
                provider_label=self.provider_label,
                graph_role=self.graph_role,
                capabilities=self.capabilities,
                nodes=(
                    GraphFakosNode(
                        id="one",
                        label="One",
                        kind="record",
                        summary="First custom node.",
                        score=0.9,
                        source="custom",
                    ),
                    GraphFakosNode(
                        id="two",
                        label="Two",
                        kind="record",
                        summary="Second custom node.",
                        score=0.8,
                        source="custom",
                    ),
                ),
                edges=(
                    GraphFakosEdge(
                        id="one-two",
                        source_id="one",
                        target_id="two",
                        kind="connects",
                        label="connects",
                    ),
                ),
                provider_payload={
                    "integration_summary": "Custom provider preview.",
                    "integration_commands": ("python -m custom_graph preview --serve",),
                },
            )

    for screen in (
        "explore",
        "neighborhood",
        "path",
        "provenance",
        "timeline",
        "diff",
        "provider_status",
        "context_preview",
    ):
        html = render_static_html(CustomProvider(), GraphFakosRequest(screen=screen))
        assert "Custom Provider" in html
        assert "Integration Commands" in html
