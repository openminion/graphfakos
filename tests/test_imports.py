from __future__ import annotations

from pathlib import Path
from importlib.resources import files
import tomllib


def test_graphfakos_package_imports() -> None:
    import graphfakos
    import graphfakos.adapters
    import graphfakos.contracts
    import graphfakos.models
    import graphfakos.provider
    import graphfakos.render
    import graphfakos.server
    import graphfakos.static
    import graphfakos.testing
    import graphfakos.ui

    assert graphfakos.__version__ == "0.0.1"
    assert graphfakos.PACKAGE_STATUS == "semantic-alpha"
    assert "graphfakos.models" in graphfakos.STABLE_IMPORT_ROOTS
    assert "graphfakos.contracts" in graphfakos.STABLE_IMPORT_ROOTS
    assert "graphfakos.render" in graphfakos.STABLE_IMPORT_ROOTS
    assert "GraphFakosDiagnostics" in graphfakos.__all__
    assert "GraphFakosGraph" in graphfakos.__all__
    assert "diagnose_graph" in graphfakos.__all__
    assert "FixtureGraphProvider" in graphfakos.adapters.__all__
    assert "render_graph_viewer" in graphfakos.ui.__all__
    assert "GraphFakosProvider" in graphfakos.contracts.__all__
    assert "screen_manifest" in graphfakos.render.__all__


def test_graphfakos_screen_manifest_is_public() -> None:
    import graphfakos

    manifest = graphfakos.screen_manifest()
    explore = next(item for item in manifest if item["screen"] == "explore")
    context = next(item for item in manifest if item["screen"] == "context_preview")

    assert explore["label"] == "Explore"
    assert explore["route"] == "/explore"
    assert "Filter the graph" in explore["summary"]
    assert context["label"] == "Context"
    assert context["route"] == "/context_preview"
    assert "graph context" in context["summary"]


def test_version_metadata_matches_pyproject() -> None:
    import graphfakos

    root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text())

    assert graphfakos.__version__ == pyproject["project"]["version"]


def test_pyproject_public_release_metadata() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text())
    project = pyproject["project"]

    assert project["description"].startswith("Reusable graph viewer")
    assert "Typing :: Typed" in project["classifiers"]
    assert project["urls"]["Homepage"].endswith("/graphfakos")
    assert project["urls"]["Issues"].endswith("/graphfakos/issues")
    assert project["urls"]["Documentation"].endswith("/graphfakos/tree/main/docs")


def test_graphfakos_is_marked_typed() -> None:
    assert files("graphfakos").joinpath("py.typed").is_file()


def test_graphfakos_does_not_import_host_packages_from_source() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "graphfakos"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text()
        if (
            "import openminion" in text
            or "from openminion" in text
            or "import sophiagraph" in text
            or "from sophiagraph" in text
            or "import pragmagraph" in text
            or "from pragmagraph" in text
        ):
            offenders.append(str(path))
    assert offenders == []
