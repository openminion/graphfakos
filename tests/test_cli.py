from __future__ import annotations

import json
import subprocess
import sys


def test_python_m_graphfakos_smoke_json() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "graphfakos", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["package"] == "graphfakos"
    assert payload["semantic_contract"] is True
    assert payload["openminion_imports"] is False


def test_python_m_graphfakos_ui_preview_writes_html(tmp_path) -> None:
    output_path = tmp_path / "graphfakos-ui.html"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui-preview",
            "--screen",
            "provider_status",
            "--html-out",
            str(output_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    html = output_path.read_text(encoding="utf-8")

    assert payload["screen"] == "provider_status"
    assert payload["node_count"] == 4
    assert "GraphFakos" in html
    assert "Fixture Provider" in html
    assert "OpenMinion Integration" in html


def test_graphfakos_ui_preview_accepts_graph_filters(tmp_path) -> None:
    output_path = tmp_path / "graphfakos-filtered.html"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui-preview",
            "--screen",
            "explore",
            "--node-kind",
            "provider",
            "--edge-kind",
            "serves",
            "--selected-edge-id",
            "edge:provider-serves-spec",
            "--html-out",
            str(output_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    html = output_path.read_text(encoding="utf-8")

    assert payload["screen"] == "explore"
    assert "Third-party Provider" in html
    assert "edge:provider-serves-spec" in html
