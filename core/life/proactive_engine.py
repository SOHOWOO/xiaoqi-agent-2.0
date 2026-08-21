from __future__ import annotations

from datetime import datetime, timedelta

from ..memory.proactive import ProactiveInterest


class ProactiveEvent:
    """主动关心事件。"""

    def __init__(
        self,
        interest: ProactiveInterest,
        message: str,
        created_at: datetime,
        priority: float = 0.0,
    ):
        self.interest = interest
        self.message = message
        self.created_at = created_at
        self.priority = priority


class ProactiveEngine:
    """主动行为决策引擎。"""

    def __init__(self):
        self._triggered: dict[str, datetime] = {}

    def evaluate(
        self,
        interests: list[ProactiveInterest],
        now: datetime,
        relationship=None,
        life_state=None,
    ) -> list[ProactiveEvent]:

        events = []

        for interest in interests:

            last = self._triggered.get(
                interest.interest_id
            )

            if last:
                if now - last < timedelta(days=3):
                    continue

            score = self._score(
                interest,
                relationship,
                life_state,
            )

            if score < 0.6:
                continue

            events.append(
                ProactiveEvent(
                    interest=interest,
                    message=self._build_message(
                        interest,
                        relationship,
                    ),
                    created_at=now,
                    priority=score,
                )
            )

            self._triggered[
                interest.interest_id
            ] = now

        return sorted(
            events,
            key=lambda x: x.priority,
            reverse=True,
        )


    def _score(
        self,
        interest,
        relationship,
        life_state,
    ):

        score = interest.importance

        if relationship:
            score += (
                relationship.state.intimacy
                * 0.2
            )

        if life_state:
            energy = getattr(
                life_state,
                "energy",
                100,
            )

            if energy < 20:
                score -= 0.3

        return min(
            1.0,
            score,
        )


    def _build_message(
        self,
        interest,
        relationship=None,
    ):

        if relationship:
            stage = (
                relationship.state.stage
            )

            if stage in (
                "熟悉",
                "亲密",
            ):
                return (
                    f"我突然想到你之前说的："
                    f"{interest.content}，"
                    "后来怎么样啦？"
                )

        return (
            f"之前你提到："
            f"{interest.content}，"
            "最近怎么样了？"
        )
