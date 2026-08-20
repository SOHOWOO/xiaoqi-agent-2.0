from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """小七的三类记忆。"""

    CANONICAL = "canonical"
    INTERACTION = "interaction"
    VIRTUAL_LIFE = "virtual_life"


class MemorySource(str, Enum):
    """记忆的具体来源。"""

    USER_PROVIDED = "user_provided"
    CONVERSATION = "conversation"
    LIFE_SIMULATION = "life_simulation"


@dataclass(frozen=True)
class MemoryRecord:
    """Memory Core 中的一条记忆。"""

    memory_id: str
    memory_type: MemoryType
    content: str
    created_at: datetime
    source: MemorySource

    # 重要程度：0.0 ~ 1.0
    importance: float = 0.5

    # 真实性/可靠性的信心：0.0 ~ 1.0
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.memory_id.strip():
            raise ValueError("memory_id cannot be empty")

        if not self.content.strip():
            raise ValueError("memory content cannot be empty")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0.0 and 1.0")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
