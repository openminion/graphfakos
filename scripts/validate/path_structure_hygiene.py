#!/usr/bin/env python3
"""Guard GraphFakos source paths against hard-to-scan tree shapes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "graphfakos"
EXEMPT_FILENAMES = {"__init__.py", "__main__.py"}
DEPRECATED_DIR_NAMES = {
    "helpers": "use a concrete owner folder",
    "utils": "use a concrete owner folder",
    "processors": "use a domain owner folder",
    "handlers": "use a domain owner folder",
}
REDUNDANT_SUFFIX_RULES = {
    "_helpers": "prefer an explicit owner name over *_helpers.py",
    "_manager": "prefer the managed domain name over *_manager.py",
    "_processor": "prefer the processed domain name over *_processor.py",
    "_support": "prefer an explicit owner name over *_support.py",
    "_utils": "prefer a concrete owner name over *_utils.py",
    "_wrapper": "prefer the boundary name over *_wrapper.py",
}
REDUNDANT_REPO_PREFIXES = ("graphfakos_", "graph_fakos_")


def _relative(path: Path, root: Path = SOURCE_ROOT) -> str:
    return path.relative_to(root).as_posix()


def _parent_prefix_matches(path: Path) -> bool:
    parent = path.parent.name
    if not parent:
        return False
    stem_tokens = path.stem.split("_")
    if len(stem_tokens) <= 1:
        return False
    parent_tokens = {parent}
    if parent.endswith("s") and len(parent) > 1:
        parent_tokens.add(parent[:-1])
    return stem_tokens[0] in parent_tokens


def validate_source_tree(root: Path = SOURCE_ROOT) -> list[str]:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if path.is_dir():
            guidance = DEPRECATED_DIR_NAMES.get(path.name)
            if guidance is not None:
                findings.append(
                    f"{_relative(path, root)}/: vague folder name {path.name!r}; {guidance}"
                )
            continue
        if path.suffix != ".py" or path.name in EXEMPT_FILENAMES:
            continue
        rel = _relative(path, root)
        stem = path.stem
        for prefix in REDUNDANT_REPO_PREFIXES:
            if stem.startswith(prefix):
                findings.append(
                    f"{rel}: redundant repo prefix {prefix!r} in source filename"
                )
        for suffix, guidance in REDUNDANT_SUFFIX_RULES.items():
            if stem.endswith(suffix):
                findings.append(f"{rel}: redundant suffix {suffix!r}; {guidance}")
        if _parent_prefix_matches(path):
            findings.append(
                f"{rel}: filename repeats the parent owner; let the folder carry subsystem context"
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    findings = validate_source_tree()
    payload = {
        "validator": "path_structure_hygiene",
        "ok": not findings,
        "scan_root": str(SOURCE_ROOT),
        "deprecated_dir_names": dict(sorted(DEPRECATED_DIR_NAMES.items())),
        "redundant_suffixes": sorted(REDUNDANT_SUFFIX_RULES),
        "findings": findings,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    if not findings:
        print("path_structure_hygiene: clean", file=sys.stderr)
        return 0
    print("Path structure hygiene findings:", file=sys.stderr)
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
