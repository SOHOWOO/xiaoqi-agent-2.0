from __future__ import annotations

from dataclasses import dataclass

from ..life.proactive_engine import ProactiveEvent
from ..events import SimulationEvent
from ..relationship import RelationshipEngine


@dataclass(frozen=True)
class ProactiveMessage:
    """主动消息。"""

    content: str
    source_interest_id: str


class ProactiveTrigger:
    """把主动事件转换成带关系感的主动消息。"""

    def __init__(
        self,
        relationship_engine: RelationshipEngine | None = None,
    ):
        self.relationship_engine = (
            relationship_engine
            if relationship_engine is not None
            else RelationshipEngine()
        )


    def handle(
        self,
        event: ProactiveEvent,
    ) -> ProactiveMessage:

        message = self._build_message(
            event
        )

        return ProactiveMessage(
            content=message,
            source_interest_id=getattr(
                getattr(event, "interest", None),
                "interest_id",
                getattr(event, "slot_id", "unknown"),
            ),
        )


    def _build_message(
        self,
        event,
    ) -> str:

        state = self.relationship_engine.state

        interest = getattr(event, "interest", None)

        if interest is not None:
            topic = interest.content
        else:
            topic = getattr(
                event,
                "slot_id",
                "最近的事情",
            )


        if state.intimacy >= 0.7:
            return (
                f"欸，我突然想到你之前跟我说的「{topic}」，"
                "不知道最近有没有好一点呀？"
            )


        if state.familiarity >= 0.3:
            return (
                f"我刚刚想到你之前提到的「{topic}」，"
                "最近进展怎么样啦？"
            )


        return (
            f"我记得你之前提到过「{topic}」，"
            "最近怎么样了？"
        )
