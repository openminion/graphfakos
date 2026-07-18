#!/usr/bin/env python3
"""Guard against new heavily chained Python filenames."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = tuple(
    root
    for root in (
        REPO_ROOT / "src",
        REPO_ROOT / "scripts",
        REPO_ROOT / "tests",
        REPO_ROOT / "examples",
    )
    if root.exists()
)
BASELINE = REPO_ROOT / "scripts" / "baselines" / "filename_underscore_hygiene.tsv"
EXEMPT_FILENAMES = {"__init__.py", "__main__.py"}
INFO_ONLY_ROOTS = {"tests"}
UNDERSCORE_THRESHOLD = 1


def _display_relpath(path: Path, scan_root: Path) -> str:
    for base in (REPO_ROOT, scan_root.parent, scan_root):
        try:
            return path.relative_to(base).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def _scan_python_files() -> tuple[list[tuple[str, int]], int]:
    detected: list[tuple[str, int]] = []
    scanned = 0
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            scanned += 1
            if path.name in EXEMPT_FILENAMES:
                continue
            count = path.stem.count("_")
            if count <= UNDERSCORE_THRESHOLD:
                continue
            detected.append((_display_relpath(path, root), count))
    return sorted(set(detected)), scanned


def _load_baseline(path: Path = BASELINE) -> list[tuple[str, int]]:
    if not path.exists():
        return []
    rows: list[tuple[str, int]] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        relpath, sep, raw_count = line.partition("\t")
        if not sep or not relpath or not raw_count:
            raise SystemExit(
                f"{path} line {line_number} must be '<relpath>\\t<underscore_count>'"
            )
        try:
            count = int(raw_count)
        except ValueError as exc:
            raise SystemExit(
                f"{path} line {line_number} underscore count must be an integer"
            ) from exc
        rows.append((relpath, count))
    return sorted(rows)


def _entry_kind(entry: tuple[str, int]) -> str:
    relpath, _count = entry
    top_level = Path(relpath).parts[0] if relpath else ""
    return "info" if top_level in INFO_ONLY_ROOTS else "enforced"


def _enforced(entries: list[tuple[str, int]]) -> list[tuple[str, int]]:
    return sorted(entry for entry in entries if _entry_kind(entry) == "enforced")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args(argv)

    detected, scanned = _scan_python_files()
    if args.write_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Format: path<TAB>underscore_count"]
        lines.extend(f"{rel}\t{count}" for rel, count in _enforced(detected))
        BASELINE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"filename_underscore_hygiene: wrote {BASELINE.relative_to(REPO_ROOT)}")
        return 0

    baseline = _load_baseline()
    current_set = set(_enforced(detected))
    baseline_set = set(_enforced(baseline))
    new_entries = sorted(current_set - baseline_set)
    removed_entries = sorted(baseline_set - current_set)
    print(
        "filename_underscore_hygiene: "
        f"scanned={scanned} detected={len(detected)} baseline={len(baseline)}"
    )
    if not new_entries and not removed_entries:
        print("filename_underscore_hygiene: clean")
        return 0
    if new_entries:
        print("New enforced filename underscore drift:", file=sys.stderr)
        for rel, count in new_entries:
            print(f"  + {rel} ({count} underscores)", file=sys.stderr)
    if removed_entries:
        print("Baseline entries no longer detected:", file=sys.stderr)
        for rel, count in removed_entries:
            print(f"  - {rel} ({count} underscores)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
