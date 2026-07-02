"""GraphFakos module entrypoint."""

from __future__ import annotations

import sys

from .cli import main, ui_preview_main


def _dispatch(argv: list[str]) -> int:
    if argv and argv[0] in {"ui", "ui-preview"}:
        return ui_preview_main(argv[1:])
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(_dispatch(sys.argv[1:]))
