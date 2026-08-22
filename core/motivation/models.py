from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MotivationType(str, Enum):
    """小七的高阶行为动机（Desire Layer）。

    由底层状态（神经化学 / 情绪 / 关系 / 记忆 / 作息）提炼而来，
    再交给 Action Planner 决定具体执行策略。
    """

    CRAVING_CONTACT = "craving_contact"
    COMFORT = "comfort"
    SHARE = "share"
    REMIND = "remind"
    PLAY = "play"


@dataclass(frozen=True)
class Motivation:
    """一条高阶行为动机。"""

    type: MotivationType
    intensity: float
    reasons: tuple[str, ...] = ()
    payload: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(
                "intensity must be between 0.0 and 1.0"
            )
