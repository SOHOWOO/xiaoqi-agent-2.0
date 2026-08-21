from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ConversationState:
    """当前对话状态。"""

    topic: str | None = None

    mood: str = "neutral"

    user_emotion: str = "unknown"

    recent_messages: List[str] = field(
        default_factory=list
    )

    turn_count: int = 0

    def add_message(
        self,
        message: str,
    ) -> None:
        self.recent_messages.append(
            message
        )

        if len(self.recent_messages) > 10:
            self.recent_messages.pop(0)

        self.turn_count += 1
