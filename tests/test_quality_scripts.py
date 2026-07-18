from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = (
    "broad_exception.py",
    "filename_underscore_hygiene.py",
    "helper_duplicates.py",
    "max_file_loc.py",
    "method_loc.py",
    "path_structure_hygiene.py",
    "public_surface.py",
    "type_ignore_hygiene.py",
)


def test_quality_validators_pass_current_baselines() -> None:
    for validator in VALIDATORS:
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "validate" / validator)],
            check=True,
            capture_output=True,
            text=True,
        )
