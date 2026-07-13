#!/usr/bin/env python3
"""Validate broad exception handler counts against a ratchet baseline."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "src" / "graphfakos"
DEFAULT_BASELINE = REPO_ROOT / "scripts" / "baselines" / "broad_exception_baseline.tsv"


@dataclass(frozen=True)
class BroadExceptionRow:
    path: str
    total: int
    silent_pass: int


@dataclass(frozen=True)
class BaselineEntry:
    path: str
    total: int
    silent_pass: int
    reason: str


def _matches_exception(node: ast.ExceptHandler) -> bool:
    if isinstance(node.type, ast.Name):
        return node.type.id == "Exception"
    if isinstance(node.type, ast.Tuple):
        return any(
            isinstance(elt, ast.Name) and elt.id == "Exception"
            for elt in node.type.elts
        )
    return False


def _silent_pass(node: ast.ExceptHandler) -> bool:
    return len(node.body) == 1 and isinstance(node.body[0], ast.Pass)


def scan(root: Path, repo_root: Path = REPO_ROOT) -> list[BroadExceptionRow]:
    rows: list[BroadExceptionRow] = []
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        counts = Counter()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler) or not _matches_exception(node):
                continue
            counts["total"] += 1
            if _silent_pass(node):
                counts["silent_pass"] += 1
        if counts["total"]:
            rows.append(
                BroadExceptionRow(
                    path=path.relative_to(repo_root).as_posix(),
                    total=counts["total"],
                    silent_pass=counts["silent_pass"],
                )
            )
    return rows


def load_baseline(path: Path) -> dict[str, BaselineEntry]:
    if not path.exists():
        return {}
    entries: dict[str, BaselineEntry] = {}
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip() or raw.startswith("#"):
            continue
        parts = raw.split("\t", 3)
        if len(parts) != 4:
            raise SystemExit(
                f"broad-exception baseline line {line_number}: "
                "expected path<TAB>total<TAB>silent_pass<TAB>reason"
            )
        rel, raw_total, raw_silent, reason = (part.strip() for part in parts)
        try:
            total = int(raw_total)
            silent = int(raw_silent)
        except ValueError as exc:
            raise SystemExit(
                f"broad-exception baseline line {line_number}: invalid count"
            ) from exc
        entries[rel] = BaselineEntry(rel, total, silent, reason)
    return entries


def validate(*, root: Path, baseline_path: Path) -> tuple[list[str], dict[str, int]]:
    rows = scan(root)
    baseline = load_baseline(baseline_path)
    seen: set[str] = set()
    findings: list[str] = []
    for row in rows:
        entry = baseline.get(row.path)
        if entry is None:
            findings.append(
                f"new_broad_exception_file: {row.path} has {row.total} broad handlers"
            )
            continue
        seen.add(row.path)
        if row.total > entry.total:
            findings.append(
                f"broad_exception_count_grew: {row.path} has {row.total} > baseline {entry.total}"
            )
        if row.silent_pass > entry.silent_pass:
            findings.append(
                f"silent_pass_count_grew: {row.path} has {row.silent_pass} > baseline {entry.silent_pass}"
            )

    for rel in sorted(set(baseline) - seen):
        findings.append(f"missing_broad_exception_baseline_file: {rel}")

    metrics = {
        "files_with_handlers": len(rows),
        "handler_count": sum(row.total for row in rows),
        "silent_pass_count": sum(row.silent_pass for row in rows),
        "baseline_entries": len(baseline),
    }
    return findings, metrics


def print_report(
    findings: list[str], metrics: dict[str, int], *, as_json: bool
) -> None:
    payload = {
        "validator": "broad_exception",
        "ok": not findings,
        "metrics": metrics,
        "findings": findings,
    }
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print("broad_exception", file=sys.stderr)
    for key, value in metrics.items():
        print(f"  {key.replace('_', ' ')}: {value}", file=sys.stderr)
    if not findings:
        print("  ok: broad-exception baseline is clean.", file=sys.stderr)
        return
    print("  findings:", file=sys.stderr)
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    findings, metrics = validate(
        root=args.root.resolve(), baseline_path=args.baseline.resolve()
    )
    print_report(findings, metrics, as_json=args.json)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
