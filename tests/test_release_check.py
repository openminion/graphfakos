from __future__ import annotations

from pathlib import Path


def test_release_check_script_covers_viewer_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    release_check = (root / "scripts" / "release_check.py").read_text()

    assert "graphfakos-smoke" in release_check
    assert "graphfakos-ui" in release_check
    assert "GraphFakosDiagnostics" in release_check
    assert "GraphFakosGraph" in release_check
    assert "custom-provider-example.md" in release_check
    assert "diagnose_graph" in release_check
    assert "py.typed" in release_check
    assert "_assert_project_metadata" in release_check
    assert "twine" in release_check
