#!/usr/bin/env python3
"""Detect repeated private helper names across sibling GraphFakos files."""

from __future__ import annotations

import ast
import collections
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOT = REPO_ROOT / "src" / "graphfakos"
BASELINE = REPO_ROOT / "scripts" / "baselines" / "helper_duplicates_baseline.tsv"

EXCLUDED_NAMES = {
    "_as_bool",
    "_as_float",
    "_as_int",
    "_as_str",
    "_as_str_list",
    "_build",
    "_coerce_bool",
    "_coerce_float",
    "_coerce_int",
    "_coerce_str",
    "_count",
    "_debug",
    "_dedupe",
    "_format",
    "_from_dict",
    "_get",
    "_html_escape",
    "_json",
    "_normalize",
    "_parse",
    "_render",
    "_resolve",
    "_safe_json",
    "_to_dict",
    "_validate",
}


def _is_excluded_file(path: Path) -> bool:
    return path.name in {"__init__.py", "__main__.py"} or path.name.startswith("test_")


def _collect_private_functions(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return []
    names: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if name.startswith("_") and name not in EXCLUDED_NAMES:
                names.append(name)
    return names


def _load_baseline(path: Path = BASELINE) -> set[tuple[str, str, tuple[str, ...]]]:
    if not path.exists():
        return set()
    entries: set[tuple[str, str, tuple[str, ...]]] = set()
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", 3)
        if len(parts) != 4:
            raise SystemExit(
                f"helper-duplicates baseline line {line_number}: "
                "expected directory<TAB>function<TAB>files<TAB>reason"
            )
        directory, function_name, raw_files, _reason = (part.strip() for part in parts)
        files = tuple(item.strip() for item in raw_files.split(",") if item.strip())
        if not directory or not function_name or not files:
            raise SystemExit(
                f"helper-duplicates baseline line {line_number}: "
                "directory, function, and files are required"
            )
        entries.add((directory, function_name, files))
    return entries


def scan(scan_root: Path = SCAN_ROOT) -> list[tuple[str, str, tuple[str, ...]]]:
    by_directory: dict[Path, dict[str, list[Path]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    for path in sorted(scan_root.rglob("*.py")) if scan_root.exists() else ():
        if _is_excluded_file(path):
            continue
        for function_name in _collect_private_functions(path):
            by_directory[path.parent][function_name].append(path)

    findings: list[tuple[str, str, tuple[str, ...]]] = []
    for directory, function_map in sorted(by_directory.items()):
        rel_dir = directory.relative_to(REPO_ROOT).as_posix()
        for function_name, files in sorted(function_map.items()):
            if len(files) < 2:
                continue
            rendered = tuple(
                path.relative_to(REPO_ROOT).as_posix() for path in sorted(files)
            )
            findings.append((rel_dir, function_name, rendered))
    return findings


def main() -> int:
    current = set(scan())
    baseline = _load_baseline()
    new_findings = sorted(current - baseline)
    stale_baseline = sorted(baseline - current)
    if not new_findings and not stale_baseline:
        print(f"helper_duplicates: clean - {len(current)} baseline duplicate set(s)")
        return 0
    if new_findings:
        print("New duplicated private helper functions detected:", file=sys.stderr)
        for rel_dir, function_name, files in new_findings:
            print(
                f"  + {rel_dir}: duplicate helper {function_name!r} in {list(files)}",
                file=sys.stderr,
            )
    if stale_baseline:
        print("Helper duplicate baseline entries no longer detected:", file=sys.stderr)
        for rel_dir, function_name, files in stale_baseline:
            print(
                f"  - {rel_dir}: duplicate helper {function_name!r} in {list(files)}",
                file=sys.stderr,
            )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
