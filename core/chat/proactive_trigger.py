from __future__ import annotations

from dataclasses import dataclass

from ..life.proactive_engine import ProactiveEvent


@dataclass(frozen=True)
class ProactiveMessage:
    """主动消息。"""

    content: str
    source_interest_id: str


class ProactiveTrigger:
    """把主动事件转换成主动消息。"""

    def handle(
        self,
        event: ProactiveEvent,
    ) -> ProactiveMessage:

        return ProactiveMessage(
            content=event.message,
            source_interest_id=(
                event.interest.interest_id
            ),
        )
