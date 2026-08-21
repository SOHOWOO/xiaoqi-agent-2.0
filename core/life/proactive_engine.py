from __future__ import annotations

from datetime import datetime

from ..memory.proactive import (
    ProactiveInterest,
)


class ProactiveEvent:
    """主动关心事件。"""

    def __init__(
        self,
        interest: ProactiveInterest,
        message: str,
        created_at: datetime,
    ):
        self.interest = interest
        self.message = message
        self.created_at = created_at


class ProactiveEngine:
    """把未来关注转换成主动事件。"""

    def __init__(self):
        self._triggered: set[str] = set()

    def evaluate(
        self,
        interests: list[ProactiveInterest],
        now: datetime,
    ) -> list[ProactiveEvent]:

        events = []

        for interest in interests:

            if interest.interest_id in self._triggered:
                continue

            if self._should_trigger(
                interest,
                now,
            ):
                events.append(
                    ProactiveEvent(
                        interest=interest,
                        message=self._build_message(
                            interest
                        ),
                        created_at=now,
                    )
                )

                self._triggered.add(
                    interest.interest_id
                )

        return events


    def _should_trigger(
        self,
        interest: ProactiveInterest,
        now: datetime,
    ) -> bool:
        """
        第一版：
        高重要关注经过一天后允许触发。
        """

        delta = (
            now - interest.created_at
        )

        return (
            interest.importance >= 0.8
            and delta.days >= 1
        )


    def _build_message(
        self,
        interest: ProactiveInterest,
    ) -> str:

        return (
            f"之前你提到："
            f"{interest.content}，"
            "最近怎么样了？"
        )
