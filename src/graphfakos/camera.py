"""Provider-neutral camera pose values for durable 3D viewer navigation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import cast

from ._model_values import _float

Vector3 = tuple[float, float, float]


def float_value(
    payload: Mapping[str, object], key: str, default: float, owner: str
) -> float:
    return _float(payload.get(key, default), f"{owner}.{key}")


def optional_float(payload: Mapping[str, object], key: str, owner: str) -> float | None:
    value = payload.get(key)
    return None if value is None else _float(value, f"{owner}.{key}")


def add_pose_query(
    payload: dict[str, object], pose: GraphFakosCameraPose | None
) -> None:
    if pose:
        payload["camera_pose"] = pose.to_query_value()


def _vector3(value: object, field_name: str) -> Vector3:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be a three-number sequence")
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly three numbers")
    vector = cast(Vector3, tuple(_float(item, field_name) for item in value))
    if not all(isfinite(item) for item in vector):
        raise ValueError(f"{field_name} values must be finite")
    return vector


@dataclass(frozen=True, slots=True)
class GraphFakosCameraPose:
    """Exact 3D camera position and look-at target."""

    position: Vector3
    target: Vector3

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "position", _vector3(self.position, "camera_pose.position")
        )
        object.__setattr__(self, "target", _vector3(self.target, "camera_pose.target"))

    def to_dict(self) -> dict[str, object]:
        return {"position": list(self.position), "target": list(self.target)}

    def to_query_value(self) -> str:
        return ",".join(f"{value:.6f}" for value in (*self.position, *self.target))

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> GraphFakosCameraPose:
        return cls(
            position=_vector3(payload.get("position"), "camera_pose.position"),
            target=_vector3(payload.get("target"), "camera_pose.target"),
        )

    @classmethod
    def from_query_value(cls, value: str) -> GraphFakosCameraPose:
        values = tuple(float(item) for item in value.split(","))
        if len(values) != 6:
            raise ValueError("camera_pose must contain six comma-separated numbers")
        return cls(
            position=_vector3(values[:3], "camera_pose.position"),
            target=_vector3(values[3:], "camera_pose.target"),
        )


def camera_pose_or_none(value: object) -> GraphFakosCameraPose | None:
    if value is None:
        return None
    if isinstance(value, GraphFakosCameraPose):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("camera_pose must be an object")
    return GraphFakosCameraPose.from_dict(value)


__all__ = ["GraphFakosCameraPose"]
