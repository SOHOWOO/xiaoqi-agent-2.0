from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EmotionType(str, Enum):
    """小七的基础情绪。"""

    HAPPY = "happy"
    LONELY = "lonely"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    CALM = "calm"


@dataclass(frozen=True)
class EmotionState:
    """某一时刻的多维情绪快照。

    每个维度 0.0 ~ 1.0，表示该情绪的强度。
    """

    happy: float
    lonely: float
    excited: float
    anxious: float
    angry: float
    calm: float

    _FIELDS = (
        "happy",
        "lonely",
        "excited",
        "anxious",
        "angry",
        "calm",
    )

    def __post_init__(self) -> None:
        for name in self._FIELDS:
            value = getattr(self, name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0.0 and 1.0"
                )

    def level(
        self,
        emotion: EmotionType,
    ) -> float:
        """按情绪枚举读取强度。"""

        return getattr(self, emotion.value)

    def dominant(self) -> EmotionType:
        """返回当前强度最高的情绪。"""

        return max(
            EmotionType,
            key=lambda e: self.level(e),
        )

    def as_dict(self) -> dict:
        """返回以 emotion value 为键的字典。"""

        return {
            e.value: self.level(e)
            for e in EmotionType
        }


@dataclass(frozen=True)
class EmotionEvent:
    """一次直接的情绪事件（如用户安慰 / 冲突）。"""

    emotion: EmotionType
    intensity: float = 0.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(
                "intensity must be between 0.0 and 1.0"
            )
