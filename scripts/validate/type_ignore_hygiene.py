#!/usr/bin/env python3
"""Require coded `# type: ignore[...]` pragmas in GraphFakos Python files."""

from __future__ import annotations

import re
import sys
import tokenize
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = tuple(
    root
    for root in (REPO_ROOT / "src", REPO_ROOT / "tests", REPO_ROOT / "scripts")
    if root.exists()
)
TYPE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore(?:\[([^\]]+)\])?", re.IGNORECASE)


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        files.extend(
            path for path in root.rglob("*.py") if "__pycache__" not in path.parts
        )
    return sorted(files)


def scan() -> tuple[list[tuple[str, int]], dict[str, int]]:
    bare: list[tuple[str, int]] = []
    code_counts: dict[str, int] = {}
    for path in _iter_python_files():
        try:
            tokens = tokenize.generate_tokens(path.open(encoding="utf-8").readline)
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        try:
            comments = (token for token in tokens if token.type == tokenize.COMMENT)
            for token in comments:
                for match in TYPE_IGNORE_RE.finditer(token.string):
                    qualifier = match.group(1)
                    if qualifier is None:
                        bare.append((rel, token.start[0]))
                        continue
                    for code in (item.strip() for item in qualifier.split(",")):
                        if code:
                            code_counts[code] = code_counts.get(code, 0) + 1
        except tokenize.TokenError:
            continue
    return bare, code_counts


def main() -> int:
    bare, code_counts = scan()
    if not bare:
        print(
            "type_ignore_hygiene: clean - "
            f"0 bare ignores; {sum(code_counts.values())} qualified ignores"
        )
        return 0
    print(
        f"type-ignore hygiene: {len(bare)} bare `# type: ignore` without `[code]` qualifier:",
        file=sys.stderr,
    )
    for rel, lineno in bare[:20]:
        print(f"  {rel}:{lineno}", file=sys.stderr)
    if len(bare) > 20:
        print(f"  ... and {len(bare) - 20} more", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
