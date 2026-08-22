from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """xiaoqi-bus 规范化核心事件。"""

    USER_INTERACTION = "user_interaction"
    EMOTION_CHANGE = "emotion_change"
    NEUROCHEMICAL_CHANGE = "neurochemical_change"
    MEMORY_CONSOLIDATED = "memory_consolidated"
    PROACTIVE_TRIGGERED = "proactive_triggered"
    DIARY_WRITTEN = "diary_written"
    STATE_UPDATE = "state_update"


@dataclass(frozen=True)
class BusEvent:
    """一条总线事件。"""

    type: EventType
    data: dict
    timestamp: datetime
    payload: Any = None

    def to_dict(self) -> dict:
        """序列化，供外部系统（WebSocket / VRM / 前端）消费。"""

        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }
