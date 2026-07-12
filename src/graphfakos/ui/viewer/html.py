"""Small HTML composition primitives shared by viewer modules."""

from __future__ import annotations

from html import escape
import json
from typing import Any


def split(primary: str, secondary: str) -> str:
    return f"<section class='gf-layout'><div>{primary}</div><aside>{secondary}</aside></section>"


def panel(title: str, body: str) -> str:
    return f"<section class='gf-panel'><h3>{escape(title)}</h3>{body}</section>"


def panel_body(title: str, body: str) -> str:
    return f"<section class='gf-subpanel'><h4>{escape(title)}</h4>{body}</section>"


def text_list(items: list[str] | tuple[str, ...]) -> str:
    if not items:
        return empty("No items.")
    return (
        "<ul class='gf-list'>"
        + "".join(f"<li>{escape(item)}</li>" for item in items)
        + "</ul>"
    )


def html_list(items: list[str] | tuple[str, ...]) -> str:
    if not items:
        return empty("No items.")
    return (
        "<ul class='gf-list'>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
    )


def key_values(payload: dict[str, Any]) -> str:
    rows = ""
    for key, value in payload.items():
        if value in (None, ""):
            continue
        rows += f"<dt>{escape(str(key))}</dt><dd>{escape(str(value))}</dd>"
    return f"<dl class='gf-kv'>{rows}</dl>" if rows else empty("No metadata.")


def empty(text: str) -> str:
    return f"<p class='gf-empty'>{escape(text)}</p>"


def summary_note(text: str) -> str:
    return f"<p class='gf-note'>{escape(text)}</p>"


def badges(items: list[tuple[str, str]] | tuple[tuple[str, str], ...]) -> str:
    return (
        "<div class='gf-badges'>"
        + "".join(badge(text, tone) for text, tone in items if text)
        + "</div>"
    )


def badge(text: str, tone: str) -> str:
    tone = tone or "neutral"
    return f"<span class='gf-badge' data-tone='{escape(tone)}'>{escape(text)}</span>"


def select(
    name: str,
    label: str,
    options: tuple[str, ...],
    selected: str,
) -> str:
    return select_pairs(
        name,
        label,
        tuple((option, option) for option in options),
        selected,
    )


def select_pairs(
    name: str,
    label: str,
    options: tuple[tuple[str, str], ...],
    selected: str,
) -> str:
    html = f"<select name='{escape(name)}' aria-label='{escape(label)}'>"
    html += f"<option value=''>{escape(label)}</option>"
    for value, text in options:
        current = " selected" if value == selected else ""
        html += f"<option value='{escape(value)}'{current}>{escape(text)}</option>"
    return f"{html}</select>"


def json_attribute(payload: object) -> str:
    return escape(
        json.dumps(payload, sort_keys=True, separators=(",", ":")), quote=True
    )


def json_script(data_attribute: str, payload: object) -> str:
    content = (
        json.dumps(payload, sort_keys=True, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    return f"<script type='application/json' {data_attribute}='true'>{content}</script>"


__all__ = [
    "badge",
    "badges",
    "empty",
    "html_list",
    "json_attribute",
    "json_script",
    "key_values",
    "panel",
    "panel_body",
    "select",
    "select_pairs",
    "split",
    "summary_note",
    "text_list",
]
