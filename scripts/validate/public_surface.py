#!/usr/bin/env python3
"""Guard GraphFakos source from hidden sibling/runtime package imports."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "graphfakos"
FORBIDDEN_IMPORT_ROOTS = {"openminion", "sophiagraph", "pragmagraph"}


def _import_root(name: str) -> str:
    return name.split(".", 1)[0]


def scan(source_root: Path = SOURCE_ROOT) -> list[str]:
    findings: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = _import_root(alias.name)
                    if root in FORBIDDEN_IMPORT_ROOTS:
                        findings.append(f"{rel}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = _import_root(node.module)
                if root in FORBIDDEN_IMPORT_ROOTS:
                    findings.append(
                        f"{rel}:{node.lineno}: from {node.module} import ..."
                    )
    return findings


def main() -> int:
    findings = scan()
    if not findings:
        print("public_surface: clean - no hidden sibling/runtime imports")
        return 0
    print("Forbidden source imports detected:", file=sys.stderr)
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
