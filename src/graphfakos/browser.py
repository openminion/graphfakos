"""Browser runtime asset helpers."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def viewer_runtime_script() -> str:
    assets = files("graphfakos").joinpath("assets")
    return "\n".join(
        assets.joinpath(name).read_text(encoding="utf-8")
        for name in (
            "focus-trail.js",
            "spatial-map.js",
            "overview-control.js",
            "viewer.js",
        )
    )


@lru_cache(maxsize=1)
def viewer_renderer_script() -> str:
    return (
        files("graphfakos")
        .joinpath("assets", "renderer-3d.js")
        .read_text(encoding="utf-8")
    )


__all__ = ["viewer_renderer_script", "viewer_runtime_script"]
