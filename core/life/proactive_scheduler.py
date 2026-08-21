from __future__ import annotations

from datetime import datetime, timedelta


class ProactiveDecision:
    def __init__(
        self,
        allowed: bool,
        score: float,
        reason: str,
    ):
        self.allowed = allowed
        self.score = score
        self.reason = reason


class ProactiveScheduler:
    """
    主动行为决策系统。

    决定：
    - 是否应该主动
    - 主动优先级
    - 是否避免打扰
    """

    def __init__(
        self,
        cooldown_minutes: int = 30,
    ):
        self.cooldown = timedelta(
            minutes=cooldown_minutes
        )

        self.last_trigger_time = None


    def evaluate(
        self,
        now: datetime,
        relationship,
        importance: float = 0.5,
        emotional_state: str = "normal",
    ) -> ProactiveDecision:

        score = 0.0


        # 关系权重
        score += (
            relationship.intimacy
            * 0.4
        )


        # 事件重要性
        score += (
            importance
            * 0.4
        )


        # 情绪权重
        if emotional_state in (
            "sad",
            "lonely",
            "stress",
        ):
            score += 0.2


        # 冷却保护
        if self.last_trigger_time:

            if (
                now - self.last_trigger_time
                < self.cooldown
            ):
                return ProactiveDecision(
                    False,
                    score,
                    "cooldown",
                )


        # 夜间减少打扰
        if now.hour >= 23 or now.hour <= 7:

            score -= 0.3


        allowed = score >= 0.35


        if allowed:
            self.last_trigger_time = now


        return ProactiveDecision(
            allowed,
            score,
            "approved"
            if allowed
            else "low_score",
        )

    def tick(
        self,
        interests,
        now: datetime,
    ):
        """
        批量处理主动兴趣事件。
        兼容 LifeLoop 调用接口。
        """

        events = []

        for interest in interests:

            relationship = getattr(
                interest,
                "relationship",
                type(
                    "Relationship",
                    (),
                    {"intimacy": 0.5}
                )()
            )

            decision = self.evaluate(
                now=now,
                relationship=relationship,
                importance=getattr(
                    interest,
                    "importance",
                    0.5,
                ),
                emotional_state=getattr(
                    interest,
                    "emotion",
                    "normal",
                ),
            )

            if not decision.allowed:
                continue

            if hasattr(interest, "to_event"):
                events.append(
                    interest.to_event()
                )
            else:
                events.append(
                    interest
                )

        return events

