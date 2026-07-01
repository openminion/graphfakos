from __future__ import annotations

import json
import shutil
import subprocess

from graphfakos.browser import viewer_runtime_script


def test_packaged_viewer_runtime_reducer_runs_in_node() -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required for the browser runtime harness"
    assert "submitKnowledge" in viewer_runtime_script()
    assert "knowledge-saved" in viewer_runtime_script()
    script = (
        viewer_runtime_script()
        + """
const runtime = globalThis.GraphFakosViewerRuntime;
let state = runtime.normalizeState({ camera_zoom: 9, filters: { node_kind: "provider" } });
state = runtime.reduce(state, { name: "select-node", target_id: "provider:third-party" });
state = runtime.reduce(state, { name: "camera", payload: { x: 8, y: -2, zoom: 1.25 } });
state = runtime.reduce(state, { name: "group-toggle", target_id: "provider" });
state = runtime.reduce(state, { name: "filter", target_id: "node_kind", payload: { value: "memory" } });
process.stdout.write(JSON.stringify({ state, eventName: runtime.eventName("select-node") }));
"""
    )

    result = subprocess.run(
        [node, "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["eventName"] == "graphfakos:select-node"
    assert payload["state"]["selected_node_id"] == "provider:third-party"
    assert payload["state"]["camera_x"] == 8
    assert payload["state"]["camera_y"] == -2
    assert payload["state"]["camera_zoom"] == 1.25
    assert payload["state"]["filters"]["node_kind"] == "memory"
    assert payload["state"]["hidden_groups"] == ["provider"]
