from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationState:
    """当前对话状态。"""

    turn_count: int = 0

    last_user_message: str | None = None

    last_assistant_message: str | None = None

    conversation_started_at: datetime | None = None

    emotional_context: str = "平静"

    topics: list[str] = field(default_factory=list)


    def update_user_message(
        self,
        text: str,
        now: datetime | None = None,
    ) -> None:
        self.turn_count += 1
        self.last_user_message = text

        if self.conversation_started_at is None:
            self.conversation_started_at = now


    def update_assistant_message(
        self,
        text: str,
    ) -> None:
        self.last_assistant_message = text


    def add_topic(
        self,
        topic: str,
    ) -> None:
        if topic and topic not in self.topics:
            self.topics.append(topic)

        if len(self.topics) > 10:
            self.topics = self.topics[-10:]
