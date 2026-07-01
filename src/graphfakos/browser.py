"""Browser runtime asset helpers."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def viewer_runtime_script() -> str:
    return (
        files("graphfakos").joinpath("assets", "viewer.js").read_text(encoding="utf-8")
    )


__all__ = ["viewer_runtime_script"]
