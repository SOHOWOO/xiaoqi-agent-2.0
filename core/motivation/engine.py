from __future__ import annotations

from datetime import timedelta
from typing import Any, List

from .models import Motivation, MotivationType


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _hours_since_interaction(
    ctx: Any,
) -> float | None:
    if ctx.last_user_interaction_at is None:
        return None

    delta = ctx.now - ctx.last_user_interaction_at

    if delta < timedelta(0):
        return 0.0

    return delta.total_seconds() / 3600.0


def _attachment_drive(
    ctx: Any,
) -> float:
    """依恋需求（与 NeurochemicalEngine 默认公式一致）。"""

    neuro = ctx.neuro_state

    if neuro is None:
        return 0.3

    return _clamp(
        0.5 * (1.0 - neuro.oxytocin)
        + 0.3 * neuro.cortisol
        + 0.2 * (1.0 - neuro.serotonin)
    )


class MotivationEngine:
    """动机引擎（Desire Layer）。

    从底层状态提炼高阶语义动机，形成
        State -> Motivation -> Action Planner -> Proactive
    的决策链路。未来可扩展学习 / 探索等更多动机类型。
    """

    LONELY_HOURS = 4.0
    ABSENCE_HOURS = 4.0
    ATTACHMENT_THRESHOLD = 0.55
    REMIND_COOLDOWN_DAYS = 3.0

    def __init__(
        self,
        remind_cooldown_days: float = REMIND_COOLDOWN_DAYS,
    ) -> None:
        self.remind_cooldown = timedelta(
            days=remind_cooldown_days
        )
        self._reminded: dict[str, object] = {}

    def evaluate(
        self,
        ctx: Any,
    ) -> List[Motivation]:
        motivations: List[Motivation] = []

        craving = self._craving_contact(ctx)
        if craving is not None:
            motivations.append(craving)

        comfort = self._comfort(ctx)
        if comfort is not None:
            motivations.append(comfort)

        share = self._share(ctx)
        if share is not None:
            motivations.append(share)

        remind = self._remind(ctx)
        if remind is not None:
            motivations.append(remind)

        play = self._play(ctx)
        if play is not None:
            motivations.append(play)

        motivations.sort(
            key=lambda m: m.intensity,
            reverse=True,
        )

        return motivations

    # ---------------------------------------------------------
    # 各动机的提炼规则
    # ---------------------------------------------------------

    def _craving_contact(
        self,
        ctx: ProactiveContext,
    ) -> Motivation | None:
        """孤独感高，或依恋需求高且久未互动 → 渴望联系。"""

        lonely = (
            ctx.emotion_state.lonely
            if ctx.emotion_state is not None
            else 0.0
        )

        attachment = _attachment_drive(ctx)
        hours = _hours_since_interaction(ctx)

        if lonely >= 0.6:
            return Motivation(
                type=MotivationType.CRAVING_CONTACT,
                intensity=lonely,
                reasons=("小七感到有些孤独，想找主人聊聊天",),
            )

        if (
            attachment >= self.ATTACHMENT_THRESHOLD
            and hours is not None
            and hours >= self.ABSENCE_HOURS
        ):
            score = _clamp(
                attachment * 0.7
                + min(1.0, hours / 24.0) * 0.3
            )

            return Motivation(
                type=MotivationType.CRAVING_CONTACT,
                intensity=score,
                reasons=(
                    "小七好久没见到主人了，有些想他",
                ),
            )

        return None

    def _comfort(
        self,
        ctx: ProactiveContext,
    ) -> Motivation | None:
        """焦虑感高 → 渴望被安慰。"""

        anxious = (
            ctx.emotion_state.anxious
            if ctx.emotion_state is not None
            else 0.0
        )

        if anxious < 0.6:
            return None

        return Motivation(
            type=MotivationType.COMFORT,
            intensity=anxious,
            reasons=("小七感到有些焦虑，想获得主人安慰",),
        )

    def _share(
        self,
        ctx: ProactiveContext,
    ) -> Motivation | None:
        """兴奋度高，或日记有开心回忆 → 想分享。"""

        excited = (
            ctx.emotion_state.excited
            if ctx.emotion_state is not None
            else 0.0
        )

        if excited >= 0.7:
            return Motivation(
                type=MotivationType.SHARE,
                intensity=excited,
                reasons=("小七很兴奋，想和主人分享",),
            )

        diary = ctx.diary
        hours = _hours_since_interaction(ctx)

        if (
            diary is not None
            and (hours is None or hours >= 6)
        ):
            recent = diary.recent(limit=3)

            if recent and any(
                tag in ("happy", "excited")
                for tag in recent[-1].mood_tags
            ):
                return Motivation(
                    type=MotivationType.SHARE,
                    intensity=0.6,
                    reasons=(
                        "小七翻看昨天的日记，想分享开心的回忆",
                    ),
                    payload=recent[-1].content[:60],
                )

        return None

    def _remind(
        self,
        ctx: ProactiveContext,
    ) -> Motivation | None:
        """高重要性关注事项，超过冷却期 → 想提醒进展。"""

        for interest in ctx.interests:
            interest_id = getattr(
                interest,
                "interest_id",
                str(id(interest)),
            )

            last = self._reminded.get(interest_id)

            if last is not None:
                if (
                    ctx.now - last
                    < self.remind_cooldown
                ):
                    continue

            importance = getattr(
                interest,
                "importance",
                0.8,
            )

            if importance < 0.7:
                continue

            self._reminded[interest_id] = ctx.now

            return Motivation(
                type=MotivationType.REMIND,
                intensity=_clamp(importance),
                reasons=(
                    "小七想起主人之前提到的重要事情",
                ),
                payload=getattr(
                    interest,
                    "content",
                    "",
                ),
            )

        return None

    def _play(
        self,
        ctx: ProactiveContext,
    ) -> Motivation | None:
        """精力充沛 + 情绪低迷（无聊）→ 想玩耍解闷。"""

        if ctx.life_state is None:
            return None

        energy = getattr(
            ctx.life_state,
            "energy",
            None,
        )

        if energy is None or energy < 0.6:
            return None

        neuro = ctx.neuro_state

        if neuro is None:
            return None

        if neuro.dopamine >= 0.3:
            return None

        return Motivation(
            type=MotivationType.PLAY,
            intensity=0.55,
            reasons=("小七有点无聊，想和主人玩点什么",),
        )
