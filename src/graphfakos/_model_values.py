"""Strict value parsing shared by provider-neutral graph DTOs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise TypeError(f"{field_name} must be a mapping")


def _mapping_list(value: object, field_name: str) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, list):
        return tuple(_mapping(item, field_name) for item in value)
    if isinstance(value, tuple):
        return tuple(_mapping(item, field_name) for item in value)
    raise TypeError(f"{field_name} must be a list of mappings")


def _required_string(
    payload: Mapping[str, object],
    key: str,
    field_name: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _string(value: object, field_name: str) -> str:
    if isinstance(value, str):
        return value
    raise TypeError(f"{field_name} must be a string")


def _string_or_none(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _string(value, field_name)


def _bool(value: object, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise TypeError(f"{field_name} must be a bool")


def _int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an int")
    return value


def _int_or_none(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _int(value, field_name)


def _float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")
    return float(value)


def _float_or_none(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    return _float(value, field_name)


def _string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        items: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise TypeError(f"{field_name} must contain only strings")
            items.append(item)
        return tuple(items)
    raise TypeError(f"{field_name} must be a list of strings")


def _tag_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    return _string_tuple(value, field_name)


def _string_dict(value: object, field_name: str) -> dict[str, str]:
    mapping = _mapping(value, field_name)
    parsed: dict[str, str] = {}
    for key, item in mapping.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise TypeError(f"{field_name} must map strings to strings")
        parsed[key] = item
    return parsed


def _string_tuple_dict(value: object, field_name: str) -> dict[str, tuple[str, ...]]:
    mapping = _mapping(value, field_name)
    parsed: dict[str, tuple[str, ...]] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            raise TypeError(f"{field_name} must use string keys")
        parsed[key] = _string_tuple(item, f"{field_name}.{key}")
    return parsed


def _position_dict(value: object, field_name: str) -> dict[str, tuple[float, float]]:
    mapping = _mapping(value, field_name)
    parsed: dict[str, tuple[float, float]] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            raise TypeError(f"{field_name} must use string keys")
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise TypeError(f"{field_name}.{key} must be a two-item coordinate")
        parsed[key] = (
            _float(item[0], f"{field_name}.{key}.x"),
            _float(item[1], f"{field_name}.{key}.y"),
        )
    return parsed


def _object_dict(value: object, field_name: str) -> dict[str, object]:
    mapping = _mapping(value, field_name)
    parsed: dict[str, object] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            raise TypeError(f"{field_name} must use string keys")
        parsed[key] = item
    return parsed


def _json_compatible_dict(value: Mapping[str, object]) -> dict[str, object]:
    return {key: _json_compatible(item) for key, item in value.items()}


def _json_compatible(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _json_compatible(item)
            for key, item in cast(Mapping[object, object], value).items()
        }
    if isinstance(value, tuple):
        return [_json_compatible(item) for item in value]
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    return value
