#!/usr/bin/env python3
"""Deterministic release checks for the standalone graphfakos package."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    subprocess.run(cmd, cwd=cwd, check=True, env=env)


def _run_capture(
    cmd: list[str],
    *,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
) -> str:
    print("+", " ".join(cmd))
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    print(result.stdout, end="")
    return result.stdout


def _assert_package_docs_shape(root: Path) -> None:
    required_paths = [
        root / "README.md",
        root / "API_COMPATIBILITY.md",
        root / "RELEASING.md",
        root / "docs" / "README.md",
        root / "docs" / "custom-provider-example.md",
        root / "docs" / "source-tree-owner-map.md",
        root / "docs" / "ui-contracts.md",
        root / "src" / "graphfakos" / "__init__.py",
        root / "src" / "graphfakos" / "contracts.py",
        root / "src" / "graphfakos" / "models.py",
        root / "src" / "graphfakos" / "provider.py",
        root / "src" / "graphfakos" / "render.py",
        root / "src" / "graphfakos" / "py.typed",
    ]
    missing = [
        str(path.relative_to(root)) for path in required_paths if not path.exists()
    ]
    if missing:
        raise RuntimeError(f"package docs/layout drifted: missing {missing!r}")


def _assert_project_metadata(root: Path) -> None:
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    project = metadata["project"]
    urls = project.get("urls", {})
    classifiers = set(project.get("classifiers", []))
    if project.get("name") != "graphfakos":
        raise RuntimeError(f"unexpected project name: {project.get('name')!r}")
    if project.get("version") != "0.0.1":
        raise RuntimeError(f"unexpected initial version: {project.get('version')!r}")
    if "Typing :: Typed" not in classifiers:
        raise RuntimeError("pyproject must advertise typed package support")
    for key in ("Homepage", "Repository", "Issues", "Documentation"):
        if key not in urls:
            raise RuntimeError(f"missing project URL: {key}")


def _assert_smoke_payload(stdout: str) -> None:
    payload = json.loads(stdout)
    if payload.get("package") != "graphfakos":
        raise RuntimeError(f"unexpected smoke package: {payload!r}")
    if payload.get("semantic_contract") is not True:
        raise RuntimeError(f"semantic alpha smoke expected: {payload!r}")
    if "graphfakos.models" not in payload.get("stable_import_roots", []):
        raise RuntimeError(f"models import root missing from smoke: {payload!r}")
    if "graphfakos.render" not in payload.get("stable_import_roots", []):
        raise RuntimeError(f"render import root missing from smoke: {payload!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run graphfakos release checks")
    parser.add_argument(
        "--skip-twine",
        action="store_true",
        help="skip `twine check dist/*`",
    )
    parser.add_argument(
        "--skip-wheel-smoke",
        action="store_true",
        help="skip fresh-wheel install smoke",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    _assert_package_docs_shape(root)
    _assert_project_metadata(root)
    shutil.rmtree(root / "build", ignore_errors=True)
    shutil.rmtree(root / "dist", ignore_errors=True)
    for egg_info in root.glob("src/*.egg-info"):
        shutil.rmtree(egg_info, ignore_errors=True)

    python = sys.executable
    _run(
        [python, "-m", "pytest", "-q"],
        cwd=root,
        extra_env={"PYTHONPATH": str(root / "src")},
    )
    _run([python, "-m", "build"], cwd=root)
    if not args.skip_twine:
        dist_files = sorted((root / "dist").glob("*"))
        with tempfile.TemporaryDirectory(prefix="graphfakos-twine-") as twine_tmp:
            venv_dir = Path(twine_tmp) / "venv"
            _run([python, "-m", "venv", str(venv_dir)], cwd=root)
            twine_python = venv_dir / "bin" / "python"
            twine_pip = venv_dir / "bin" / "pip"
            _run([str(twine_pip), "install", "twine>=5,<7"], cwd=root)
            _run(
                [
                    str(twine_python),
                    "-m",
                    "twine",
                    "check",
                    *[str(path) for path in dist_files],
                ],
                cwd=root,
            )
    if not args.skip_wheel_smoke:
        with tempfile.TemporaryDirectory(prefix="graphfakos-release-") as tmpdir:
            tmp = Path(tmpdir)
            venv_dir = tmp / "venv"
            _run([python, "-m", "venv", str(venv_dir)], cwd=root)
            pip = venv_dir / "bin" / "pip"
            wheel_python = venv_dir / "bin" / "python"
            smoke = venv_dir / "bin" / "graphfakos-smoke"
            ui_preview = venv_dir / "bin" / "graphfakos-ui"
            wheel = sorted((root / "dist").glob("graphfakos-*.whl"))[-1]
            _run([str(pip), "install", str(wheel)], cwd=root)
            _run(
                [
                    str(wheel_python),
                    "-c",
                    (
                        "from importlib.resources import files; "
                        "from graphfakos import GraphFakosGraph, "
                        "GraphFakosDiagnostics, GraphFakosProvider, "
                        "FixtureGraphProvider, build_graph_report, "
                        "diagnose_graph, render_embeddable_html, "
                        "render_static_html, screen_manifest; "
                        "from graphfakos.contracts import GraphFakosRequest; "
                        "from graphfakos.render import render_graph_fragment, "
                        "render_graph_viewer; "
                        "assert files('graphfakos').joinpath('py.typed').is_file()"
                    ),
                ],
                cwd=root,
            )
            _assert_smoke_payload(_run_capture([str(smoke), "--json"], cwd=root))
            _run_capture(
                [
                    str(ui_preview),
                    "--screen",
                    "diff",
                    "--html-out",
                    str(tmp / "graphfakos-ui.html"),
                    "--embed-out",
                    str(tmp / "graphfakos-ui-embed.html"),
                    "--report-out",
                    str(tmp / "graphfakos-report.json"),
                    "--json",
                ],
                cwd=root,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
