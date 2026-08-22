from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

VALID_ACTIONS = {
    "chat",
    "comfort",
    "remind",
    "share",
    "play",
}


@dataclass(frozen=True)
class ProactiveSignal:
    """一次主动行为候选信号。

    由各驱动器（情绪 / 神经化学 / 时间 / 日记 / 记忆）产生，
    由 ProactiveGate 过滤、ProactiveEngine 决策。
    """

    signal_type: str
    reason: str
    score: float
    suggested_action: str
    payload: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                "score must be between 0.0 and 1.0"
            )

        if self.suggested_action not in VALID_ACTIONS:
            raise ValueError(
                f"unknown suggested_action: "
                f"{self.suggested_action}"
            )


@dataclass(frozen=True)
class ProactiveAction:
    """决策后要执行的主动行为。

    通过 content 属性与旧 ProactiveMessage 兼容。
    """

    signal: ProactiveSignal
    message: str

    @property
    def content(self) -> str:
        return self.message

    @property
    def source_interest_id(self) -> str:
        return f"proactive:{self.signal.signal_type}"


@dataclass(frozen=True)
class ProactiveMessage:
    """待发送的主动消息。"""

    content: str
    source_interest_id: str


@dataclass
class ProactiveContext:
    """主动决策所需的全部内部状态快照。"""

    now: datetime
    life_state: Any = None
    emotion_state: Any = None
    neuro_state: Any = None
    relationship_state: Any = None
    diary: Any = None
    interests: list = field(default_factory=list)
    last_user_interaction_at: datetime | None = None
    current_slot_id: str | None = None
