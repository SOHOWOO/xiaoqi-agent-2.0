from __future__ import annotations

from datetime import timedelta
from typing import List

from .models import ProactiveContext, ProactiveSignal


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _hours_since_interaction(
    ctx: ProactiveContext,
) -> float | None:
    if ctx.last_user_interaction_at is None:
        return None

    delta = ctx.now - ctx.last_user_interaction_at

    if delta < timedelta(0):
        return 0.0

    return delta.total_seconds() / 3600.0


def _attachment_drive(
    ctx: ProactiveContext,
) -> float:
    """与 NeurochemicalEngine.attachment_drive 保持一致的默认公式。"""

    neuro = ctx.neuro_state

    if neuro is None:
        return 0.3

    return _clamp(
        0.5 * (1.0 - neuro.oxytocin)
        + 0.3 * neuro.cortisol
        + 0.2 * (1.0 - neuro.serotonin)
    )


class EmotionSignalGenerator:
    """情绪驱动的主动信号。

    孤独 → 主动聊天；焦虑 → 主动安慰。
    """

    def generate(
        self,
        ctx: ProactiveContext,
    ) -> List[ProactiveSignal]:
        emotion = ctx.emotion_state

        if emotion is None:
            return []

        signals: List[ProactiveSignal] = []

        if emotion.lonely >= 0.6:
            signals.append(
                ProactiveSignal(
                    signal_type="emotion:lonely",
                    reason="小七感到有点孤独，想找主人聊聊天",
                    score=emotion.lonely,
                    suggested_action="chat",
                )
            )

        if emotion.anxious >= 0.6:
            signals.append(
                ProactiveSignal(
                    signal_type="emotion:anxious",
                    reason="小七感到有些焦虑，想获得主人安慰",
                    score=emotion.anxious,
                    suggested_action="comfort",
                )
            )

        if emotion.excited >= 0.7:
            signals.append(
                ProactiveSignal(
                    signal_type="emotion:excited",
                    reason="小七很兴奋，想和主人分享",
                    score=emotion.excited,
                    suggested_action="share",
                )
            )

        return signals


class NeurochemicalSignalGenerator:
    """神经化学驱动的主动信号。

    依恋需求高 + 长时间没互动 → 主动聊天。
    """

    LONELY_HOURS = 4.0
    MIN_SCORE = 0.35

    def generate(
        self,
        ctx: ProactiveContext,
    ) -> List[ProactiveSignal]:
        attachment = _attachment_drive(ctx)

        if attachment < self.MIN_SCORE:
            return []

        hours = _hours_since_interaction(ctx)

        if hours is None:
            return []

        if hours < self.LONELY_HOURS:
            return []

        score = _clamp(
            attachment * 0.7
            + min(1.0, hours / 24.0) * 0.3
        )

        return [
            ProactiveSignal(
                signal_type="neurochemical:attachment",
                reason="小七好久没见到主人了，有些想他",
                score=score,
                suggested_action="chat",
            )
        ]


class TimeSignalGenerator:
    """时间 / 作息驱动的主动信号。

    晚间休息时段如果一整天都没互动 → 主动关心。
    """

    QUIET_HOURS = range(21, 24)
    MORNING_HOURS = range(7, 9)

    def generate(
        self,
        ctx: ProactiveContext,
    ) -> List[ProactiveSignal]:
        hour = ctx.now.hour

        hours = _hours_since_interaction(ctx)

        if hours is None or hours < 8:
            return []

        in_quiet = (
            hour in self.QUIET_HOURS
            or hour in self.MORNING_HOURS
        )

        if not in_quiet:
            return []

        slot = ctx.current_slot_id or ""

        if "sleep" in slot or "pre_sleep" in slot:
            return []

        return [
            ProactiveSignal(
                signal_type="time:long_absence",
                reason="今天和主人几乎没有互动，晚间想关心一下",
                score=0.7,
                suggested_action="chat",
                payload=f"已过去约 {int(hours)} 小时",
            )
        ]


class DiarySignalGenerator:
    """日记驱动的主动信号。

    今天还没聊过，且昨天有值得回味的日记 → 主动分享。
    """

    def generate(
        self,
        ctx: ProactiveContext,
    ) -> List[ProactiveSignal]:
        diary = ctx.diary

        if diary is None:
            return []

        hours = _hours_since_interaction(ctx)

        if hours is None or hours < 6:
            return []

        recent = diary.recent(limit=3)

        if not recent:
            return []

        latest = recent[-1]

        if latest.mood_tags and any(
            tag in ("happy", "excited")
            for tag in latest.mood_tags
        ):
            return [
                ProactiveSignal(
                    signal_type="diary:reminisce",
                    reason="小七翻看昨天的日记，想和主人分享开心的回忆",
                    score=0.6,
                    suggested_action="share",
                    payload=latest.content[:60],
                )
            ]

        return []


class MemorySignalGenerator:
    """记忆驱动的主动信号。

    高重要性的关注事项，超过冷却期 → 主动关心进展。
    """

    def __init__(
        self,
        cooldown_days: float = 3.0,
    ) -> None:
        self.cooldown = timedelta(
            days=cooldown_days
        )
        self._triggered: dict[str, object] = {}

    def generate(
        self,
        ctx: ProactiveContext,
    ) -> List[ProactiveSignal]:
        signals: List[ProactiveSignal] = []

        for interest in ctx.interests:
            interest_id = getattr(
                interest,
                "interest_id",
                str(id(interest)),
            )

            last = self._triggered.get(interest_id)

            if last is not None:
                if (
                    ctx.now
                    - last
                    < self.cooldown
                ):
                    continue

            importance = getattr(
                interest,
                "importance",
                0.8,
            )

            content = getattr(
                interest,
                "content",
                "",
            )

            self._triggered[interest_id] = ctx.now

            signals.append(
                ProactiveSignal(
                    signal_type="memory:interest",
                    reason="小七想起主人之前提到的重要事情",
                    score=_clamp(importance),
                    suggested_action="remind",
                    payload=content,
                )
            )

        return signals
