from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProactiveTrigger:
    """主动行为触发条件。"""

    trigger_id: str
    keyword: str
    action: str
    importance: float = 0.5


@dataclass(frozen=True)
class ProactiveEvent:
    """一次主动行为事件。"""

    trigger_id: str
    message: str
    created_at: datetime
