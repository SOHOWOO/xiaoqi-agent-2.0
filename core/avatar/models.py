from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AvatarExpression:
    """
    角色表情状态。
    """

    emotion: str

    intensity: float = 1.0


@dataclass(frozen=True)
class AvatarMotion:
    """
    角色动作。
    """

    action: str


@dataclass(frozen=True)
class LipSyncData:
    """
    嘴型同步数据。
    """

    audio_path: str

    duration: float = 0.0
