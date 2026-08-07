#!/usr/bin/env python3
"""Run GraphFakos integration checks across local sibling packages."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
PACKAGE_NAMES = ("graphfakos", "sophiagraph", "pragmagraph", "openminion")


@dataclass(frozen=True)
class PackageRoot:
    name: str
    root: Path

    @property
    def src(self) -> Path:
        return self.root / "src"

    @property
    def python(self) -> Path:
        for candidate in (
            self.root / ".venv" / "bin" / "python3.11",
            self.root / ".venv" / "bin" / "python",
        ):
            if candidate.exists():
                return candidate
        return Path(sys.executable)


@dataclass(frozen=True)
class Check:
    label: str
    package: str
    args: tuple[str, ...]
    pythonpath: tuple[str, ...]


def _package_roots() -> dict[str, PackageRoot]:
    return {
        name: PackageRoot(name=name, root=WORKSPACE_ROOT / name)
        for name in PACKAGE_NAMES
    }


def _missing_packages(packages: dict[str, PackageRoot]) -> list[str]:
    return [
        name
        for name, package in packages.items()
        if not package.root.exists() or not package.src.exists()
    ]


def _pythonpath(*packages: PackageRoot) -> tuple[str, ...]:
    return tuple(str(package.src) for package in packages)


def _run(check: Check, packages: dict[str, PackageRoot]) -> None:
    package = packages[check.package]
    cmd = [str(package.python), "-m", "pytest", "-q", *check.args]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(check.pythonpath)
    print(f"\n==> {check.label}", flush=True)
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=package.root, env=env, check=True)


def _source_checks(packages: dict[str, PackageRoot]) -> tuple[Check, ...]:
    graphfakos = packages["graphfakos"]
    sophiagraph = packages["sophiagraph"]
    pragmagraph = packages["pragmagraph"]
    openminion = packages["openminion"]
    all_sources = _pythonpath(graphfakos, pragmagraph, sophiagraph, openminion)
    return (
        Check(
            label="GraphFakos sibling provider smoke",
            package="graphfakos",
            args=("tests/test_sibling_provider_smoke.py",),
            pythonpath=_pythonpath(graphfakos, sophiagraph, pragmagraph),
        ),
        Check(
            label="Sophiagraph GraphFakos adapter and compatibility",
            package="sophiagraph",
            args=(
                "tests/test_graphfakos_adapter.py",
                "tests/test_collaborative_workbench.py",
                "tests/test_compatibility_contracts.py",
                "tests/test_embedding_hooks.py",
            ),
            pythonpath=_pythonpath(sophiagraph, graphfakos),
        ),
        Check(
            label="PragmaGraph GraphFakos adapter and viewer envelope",
            package="pragmagraph",
            args=(
                "tests/test_graphfakos_adapter.py",
                "tests/test_viewer_contract.py",
                "tests/test_ui_contracts.py",
                "tests/test_imports.py",
            ),
            pythonpath=_pythonpath(pragmagraph, graphfakos),
        ),
        Check(
            label="OpenMinion GraphFakos viewer integration",
            package="openminion",
            args=("-rs", "tests/context/knowledge/test_viewer.py"),
            pythonpath=all_sources,
        ),
        Check(
            label="OpenMinion PragmaGraph provider coenablement",
            package="openminion",
            args=(
                "tests/context/knowledge/test_pragmagraph_adapter.py",
                "tests/context/knowledge/test_pragmagraph_provider_swap.py",
                "tests/context/knowledge/test_config.py",
                "tests/context/knowledge/test_registry.py",
            ),
            pythonpath=all_sources,
        ),
    )


def _run_browser_e2e(packages: dict[str, PackageRoot]) -> None:
    graphfakos = packages["graphfakos"]
    print("\n==> GraphFakos browser viewer integration", flush=True)
    subprocess.run(["make", "browser-e2e"], cwd=graphfakos.root, check=True)


def _build_wheel(package: PackageRoot, wheelhouse: Path) -> Path:
    print(f"\n==> Build local wheel for {package.name}", flush=True)
    subprocess.run(
        [
            str(package.python),
            "-m",
            "build",
            "--wheel",
            "--outdir",
            str(wheelhouse),
        ],
        cwd=package.root,
        check=True,
    )
    wheels = sorted(wheelhouse.glob(f"{package.name.replace('-', '_')}-*.whl"))
    if not wheels:
        raise RuntimeError(f"no wheel produced for {package.name}")
    return wheels[-1]


def _run_wheel_smoke(packages: dict[str, PackageRoot]) -> None:
    with tempfile.TemporaryDirectory(prefix="graphfakos-integration-") as tmpdir:
        tmp = Path(tmpdir)
        wheelhouse = tmp / "wheelhouse"
        wheelhouse.mkdir()
        wheels = {
            name: _build_wheel(packages[name], wheelhouse) for name in PACKAGE_NAMES
        }
        venv = tmp / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        python = venv / "bin" / "python"
        pip = venv / "bin" / "pip"
        install_cmd = [
            str(pip),
            "install",
            "--find-links",
            str(wheelhouse),
            str(wheels["graphfakos"]),
            str(wheels["sophiagraph"]),
            str(wheels["pragmagraph"]),
            f"{wheels['openminion']}[viewer]",
        ]
        print("\n==> Install local wheels together", flush=True)
        print("+", " ".join(install_cmd), flush=True)
        subprocess.run(install_cmd, check=True)
        smoke = (
            "import graphfakos, sophiagraph, pragmagraph, openminion; "
            "from pragmagraph.viewer import build_viewer_fixture_envelope; "
            "from graphfakos.adapters.provider_envelope import graph_from_provider_envelope; "
            "envelope = build_viewer_fixture_envelope('viewer-scale-1k').to_dict(); "
            "graph = graph_from_provider_envelope(envelope, source_path='wheel-smoke'); "
            "assert graph.provider_id == 'pragmagraph'; "
            "assert graph.stats['hidden_nodes'] > 0; "
            "print('wheel_combo_smoke: ok')"
        )
        subprocess.run([str(python), "-c", smoke], check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run local GraphFakos sibling-package integration checks."
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="skip with status 0 when sibling package checkouts are unavailable",
    )
    parser.add_argument(
        "--include-browser-e2e",
        action="store_true",
        help="also run GraphFakos real-browser viewer E2E",
    )
    parser.add_argument(
        "--wheel-smoke",
        action="store_true",
        help="build local wheels and install the package combo in a fresh venv",
    )
    args = parser.parse_args(argv)

    packages = _package_roots()
    missing = _missing_packages(packages)
    if missing:
        message = f"missing sibling package checkout(s): {', '.join(missing)}"
        if args.allow_missing:
            print(f"integration-check: skipped - {message}")
            return 0
        print(f"integration-check: failed - {message}", file=sys.stderr)
        return 1

    try:
        for check in _source_checks(packages):
            _run(check, packages)
        if args.include_browser_e2e:
            _run_browser_e2e(packages)
        if args.wheel_smoke:
            if (
                not shutil.which("python3.11")
                and Path(sys.executable).name != "python3.11"
            ):
                print(
                    "integration-check: wheel smoke uses current Python",
                    file=sys.stderr,
                )
            _run_wheel_smoke(packages)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    print("\nintegration-check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
