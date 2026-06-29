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
    assert "graphfakos.artifacts" in payload["stable_import_roots"]


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
    assert "Integration Commands" in html


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


def test_graphfakos_ui_preview_writes_embed_and_report_outputs(tmp_path) -> None:
    output_path = tmp_path / "graphfakos-diff.html"
    artifact_path = tmp_path / "graphfakos-artifact.json"
    embed_path = tmp_path / "graphfakos-embed.html"
    report_path = tmp_path / "graphfakos-report.json"
    markdown_path = tmp_path / "graphfakos-report.md"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui-preview",
            "--screen",
            "diff",
            "--html-out",
            str(output_path),
            "--artifact-out",
            str(artifact_path),
            "--embed-out",
            str(embed_path),
            "--report-out",
            str(report_path),
            "--markdown-report-out",
            str(markdown_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["screen"] == "diff"
    assert payload["artifact"]["artifact"] is True
    assert payload["embed"]["embedded"] is True
    assert payload["report"]["report"] is True
    assert payload["markdown_report"]["markdown_report"] is True
    assert "Snapshot Diff" in output_path.read_text(encoding="utf-8")
    assert "data-graphfakos-embed='true'" in embed_path.read_text(encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["comparison_graph"]["provider_label"] == "Fixture Baseline"
    assert "# GraphFakos Report" in markdown_path.read_text(encoding="utf-8")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["provider_id"] == "fixture"


def test_graphfakos_ui_preview_loads_provider_module_and_graph_artifact(tmp_path) -> None:
    artifact_path = tmp_path / "graphfakos-artifact.json"
    html_path = tmp_path / "graphfakos-artifact.html"
    module_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui-preview",
            "--provider-module",
            "graphfakos.adapters.fixture",
            "--provider-class",
            "FixtureGraphProvider",
            "--artifact-out",
            str(artifact_path),
            "--html-out",
            str(tmp_path / "graphfakos-provider.html"),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    module_payload = json.loads(module_result.stdout)
    artifact_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui-preview",
            "--graph-json",
            str(artifact_path),
            "--comparison-graph-json",
            str(artifact_path),
            "--screen",
            "diff",
            "--html-out",
            str(html_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    artifact_payload = json.loads(artifact_result.stdout)
    html = html_path.read_text(encoding="utf-8")

    assert module_payload["artifact"]["artifact"] is True
    assert artifact_payload["provider_id"] == "fixture"
    assert artifact_payload["route"].startswith("/diff?")
    assert "Fixture Provider" in html
