from __future__ import annotations

from dataclasses import dataclass

from ..events import SimulationEvent


@dataclass(frozen=True)
class ProactiveMessage:
    """主动消息。"""

    content: str
    source_event_id: str


class ProactiveTrigger:
    """把主动事件转换成主动消息。"""

    def handle(
        self,
        event: SimulationEvent,
    ) -> ProactiveMessage | None:
        if event.event_type != "proactive_interest":
            return None

        return ProactiveMessage(
            content=(
                "我记得你之前提到过这件事，"
                "最近进展怎么样了？"
            ),
            source_event_id=event.event_id,
        )
