from __future__ import annotations

from datetime import datetime

from .models import (
    ProactiveEvent,
    ProactiveTrigger,
)


class ProactiveEngine:
    """根据记忆生成主动行为。"""

    DEFAULT_TRIGGERS = [
        ProactiveTrigger(
            trigger_id="exam",
            keyword="考试",
            action="询问考试准备情况",
            importance=0.9,
        ),
        ProactiveTrigger(
            trigger_id="work",
            keyword="工作",
            action="关心工作状态",
            importance=0.7,
        ),
        ProactiveTrigger(
            trigger_id="travel",
            keyword="旅行",
            action="询问旅行计划",
            importance=0.7,
        ),
    ]

    def __init__(
        self,
        triggers=None,
    ):
        self.triggers = (
            triggers
            if triggers is not None
            else self.DEFAULT_TRIGGERS
        )

    def evaluate(
        self,
        text: str,
    ) -> list[ProactiveEvent]:

        events = []

        for trigger in self.triggers:
            if trigger.keyword in text:
                events.append(
                    ProactiveEvent(
                        trigger_id=trigger.trigger_id,
                        message=trigger.action,
                        created_at=datetime.now(),
                    )
                )

        return events
