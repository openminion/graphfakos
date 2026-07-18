from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

from graphfakos import GraphFakosGraphAction, GraphFakosKnowledgeCapture


def _example_module() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "examples" / "provider_host.py"
    spec = importlib.util.spec_from_file_location("provider_host_example", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_third_party_host_example_renders_and_accepts_actions() -> None:
    module = _example_module()
    provider = module.ThirdPartyHostProvider()

    capture_payload = provider.capture_knowledge(
        GraphFakosKnowledgeCapture(
            text="Remember that the host owns persistence.",
            kind="note",
            tags=("host", "boundary"),
            source="test",
            link_node_id="host:package",
        )
    )
    action_status = provider.submit_graph_action(
        GraphFakosGraphAction(
            action_id="draft:host-example",
            action_type="draft_edge",
            target_id="host:package",
            source_id="host:package",
            target_node_id="doc:integration",
            label="Host preview action",
        )
    )
    graph = provider.load_graph(module.GraphFakosRequest())
    html = module.render_preview_html(provider)

    assert capture_payload["ok"] is True
    assert action_status.status == "previewed"
    assert graph.stats["captures"] == 1
    assert graph.stats["actions"] == 1
    assert any(node.id == "note:1" for node in graph.nodes)
    assert any(node.id == "action:1" for node in graph.nodes)
    assert "Action readiness" in html
    assert (
        "Host accepted the provider-neutral capture payload."
        in capture_payload["status"]["message"]
    )


def test_third_party_host_example_uses_graphfakos_public_imports_only() -> None:
    path = Path(__file__).resolve().parents[1] / "examples" / "provider_host.py"
    tree = ast.parse(path.read_text())
    imports = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }

    assert "sophiagraph" not in imports
    assert "pragmagraph" not in imports
    assert "openminion" not in imports
    assert "graphfakos" in imports
