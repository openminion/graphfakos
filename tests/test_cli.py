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
    assert "graphfakos.live" in payload["stable_import_roots"]


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


def test_python_m_graphfakos_ui_alias_writes_html(tmp_path) -> None:
    output_path = tmp_path / "graphfakos-ui-alias.html"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui",
            "--screen",
            "explore",
            "--html-out",
            str(output_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["screen"] == "explore"
    assert output_path.exists()


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
            "--camera-x",
            "8",
            "--camera-y",
            "-2",
            "--camera-zoom",
            "1.25",
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
    assert "data-camera-x='8.00'" in html
    assert "data-camera-y='-2.00'" in html
    assert "data-camera-zoom='1.25'" in html


def test_graphfakos_ui_preview_accepts_demo_scenario(tmp_path) -> None:
    output_path = tmp_path / "graphfakos-demo-dense.html"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui",
            "--demo-scenario",
            "dense",
            "--screen",
            "explore",
            "--layout",
            "grouped",
            "--render-limit",
            "240",
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

    assert payload["provider_id"] == "demo"
    assert payload["node_count"] == 36
    assert payload["edge_count"] == 60
    assert "Provider Cluster 1" in html
    assert "data-graph-json" in html


def test_graphfakos_ui_preview_writes_embed_and_report_outputs(tmp_path) -> None:
    output_path = tmp_path / "graphfakos-diff.html"
    artifact_path = tmp_path / "graphfakos-artifact.json"
    embed_path = tmp_path / "graphfakos-embed.html"
    report_path = tmp_path / "graphfakos-report.json"
    markdown_path = tmp_path / "graphfakos-report.md"
    dot_path = tmp_path / "graphfakos-report.dot"
    bundle_path = tmp_path / "graphfakos-replay.json"
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
            "--dot-out",
            str(dot_path),
            "--bundle-out",
            str(bundle_path),
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
    assert payload["dot"]["dot"] is True
    assert payload["replay_bundle"]["replay_bundle"] is True
    assert "Snapshot Diff" in output_path.read_text(encoding="utf-8")
    assert "data-graphfakos-embed='true'" in embed_path.read_text(encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["comparison_graph"]["provider_label"] == "Fixture Baseline"
    assert report["review_presets"]
    assert "# GraphFakos Report" in markdown_path.read_text(encoding="utf-8")
    assert 'digraph "fixture"' in dot_path.read_text(encoding="utf-8")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["provider_id"] == "fixture"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["graph"]["provider_id"] == "fixture"
    assert bundle["saved_views"][0]["view_id"] == "route"


def test_graphfakos_ui_preview_loads_provider_module_and_graph_artifact(
    tmp_path,
) -> None:
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


def test_graphfakos_ui_preview_rejects_provider_config_without_module() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui-preview",
            "--provider-config-json",
            '{"workspace": ".graph-workspace"}',
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--provider-config-json requires --provider-module" in result.stderr


def test_graphfakos_ui_preview_rejects_comparison_artifact_without_graph_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui-preview",
            "--comparison-graph-json",
            "comparison.json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--comparison-graph-json requires --graph-json" in result.stderr


def test_graphfakos_ui_preview_reports_provider_import_errors() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "ui-preview",
            "--provider-module",
            "graphfakos.adapters.missing_provider",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Unable to import provider module" in result.stderr
