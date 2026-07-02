"""Renderer selection contract for GraphFakos."""

from __future__ import annotations

SUPPORTED_RENDER_ENGINES = ("svg", "canvas")


def validate_render_engine(render_engine: str) -> str:
    if render_engine not in SUPPORTED_RENDER_ENGINES:
        supported = ", ".join(SUPPORTED_RENDER_ENGINES)
        raise ValueError(
            f"unsupported GraphFakos render engine {render_engine!r}; supported: {supported}"
        )
    return render_engine


__all__ = ["SUPPORTED_RENDER_ENGINES", "validate_render_engine"]
