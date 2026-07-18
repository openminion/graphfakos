#!/usr/bin/env python3
"""Validate GraphFakos function and method LOC against a ratchet baseline."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "src" / "graphfakos"
DEFAULT_BASELINE = REPO_ROOT / "scripts" / "baselines" / "method_loc_baseline.tsv"
DEFAULT_CEILING = 100


@dataclass(frozen=True)
class MethodRow:
    path: str
    qualname: str
    loc: int


@dataclass(frozen=True)
class BaselineEntry:
    path: str
    qualname: str
    loc: int
    reason: str


def _node_loc(node: ast.AST) -> int:
    end_lineno = getattr(node, "end_lineno", None)
    lineno = getattr(node, "lineno", None)
    if not isinstance(end_lineno, int) or not isinstance(lineno, int):
        return 0
    return max(0, end_lineno - lineno + 1)


class FunctionCollector(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.stack: list[str] = []
        self.rows: list[MethodRow] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record(node)
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record(node)
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def _record(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualname = ".".join([*self.stack, node.name]) if self.stack else node.name
        self.rows.append(
            MethodRow(path=self.path, qualname=qualname, loc=_node_loc(node))
        )


def iter_methods(*, repo_root: Path, source_root: Path) -> list[MethodRow]:
    rows: list[MethodRow] = []
    for path in sorted(source_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        collector = FunctionCollector(path.relative_to(repo_root).as_posix())
        collector.visit(tree)
        rows.extend(collector.rows)
    return rows


def load_baseline(path: Path) -> dict[tuple[str, str], BaselineEntry]:
    if not path.exists():
        return {}
    entries: dict[tuple[str, str], BaselineEntry] = {}
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip() or raw.startswith("#"):
            continue
        parts = raw.split("\t", 3)
        if len(parts) != 4:
            raise SystemExit(
                f"method-loc baseline line {line_number}: "
                "expected path<TAB>qualname<TAB>loc<TAB>reason"
            )
        rel, qualname, raw_loc, reason = (part.strip() for part in parts)
        try:
            loc = int(raw_loc)
        except ValueError as exc:
            raise SystemExit(
                f"method-loc baseline line {line_number}: invalid loc {raw_loc!r}"
            ) from exc
        entries[(rel, qualname)] = BaselineEntry(rel, qualname, loc, reason)
    return entries


def validate(
    *,
    repo_root: Path,
    source_root: Path,
    baseline_path: Path,
    ceiling: int,
) -> tuple[list[str], dict[str, int]]:
    rows = iter_methods(repo_root=repo_root, source_root=source_root)
    baseline = load_baseline(baseline_path)
    seen: set[tuple[str, str]] = set()
    findings: list[str] = []
    over_ceiling = 0

    for row in rows:
        key = (row.path, row.qualname)
        entry = baseline.get(key)
        if row.loc > ceiling:
            over_ceiling += 1
            if entry is None:
                findings.append(
                    f"new_over_ceiling_method: {row.path}:{row.qualname} "
                    f"has {row.loc} LOC > {ceiling}"
                )
                continue
            seen.add(key)
            if row.loc > entry.loc:
                findings.append(
                    f"baselined_method_grew: {row.path}:{row.qualname} "
                    f"has {row.loc} LOC > baseline {entry.loc}"
                )
        elif entry is not None:
            seen.add(key)
            findings.append(
                f"stale_method_baseline: {row.path}:{row.qualname} "
                f"is {row.loc} LOC <= {ceiling}"
            )

    for key, entry in sorted(baseline.items()):
        if key not in seen:
            findings.append(f"missing_baselined_method: {entry.path}:{entry.qualname}")

    metrics = {
        "checked": len(rows),
        "ceiling": ceiling,
        "over_ceiling": over_ceiling,
        "baseline_entries": len(baseline),
    }
    return findings, metrics


def print_report(
    name: str, findings: list[str], metrics: dict[str, int], *, as_json: bool
) -> None:
    payload = {
        "validator": name,
        "ok": not findings,
        "metrics": metrics,
        "findings": findings,
    }
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(name, file=sys.stderr)
    for key, value in metrics.items():
        print(f"  {key.replace('_', ' ')}: {value}", file=sys.stderr)
    if not findings:
        print("  ok: method-LOC baseline is clean.", file=sys.stderr)
        return
    print("  findings:", file=sys.stderr)
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--ceiling", type=int, default=DEFAULT_CEILING)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    findings, metrics = validate(
        repo_root=args.repo_root.resolve(),
        source_root=args.source_root.resolve(),
        baseline_path=args.baseline.resolve(),
        ceiling=max(1, args.ceiling),
    )
    print_report("method_loc", findings, metrics, as_json=args.json)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
