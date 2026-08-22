from __future__ import annotations

from datetime import timedelta

from .models import ProactiveContext, ProactiveSignal


class ProactiveGate:
    """主动行为的门控层。

    负责：
    - 冷却保护（两次主动之间至少间隔一段时间）
    - 打扰避免（睡眠 / 深夜不主动打扰）
    - 精力保护（太累时不主动）
    """

    SLEEP_SLOT_KEYWORDS = ("sleep", "pre_sleep")

    def __init__(
        self,
        cooldown_minutes: int = 60,
    ) -> None:
        self.cooldown = timedelta(
            minutes=cooldown_minutes
        )
        self._last_trigger: object | None = None

    def _is_sleeping(
        self,
        ctx: ProactiveContext,
    ) -> bool:
        slot = ctx.current_slot_id or ""

        if any(
            keyword in slot
            for keyword in self.SLEEP_SLOT_KEYWORDS
        ):
            return True

        if ctx.life_state is not None:
            energy = getattr(
                ctx.life_state,
                "energy",
                None,
            )

            if energy is not None and energy < 0.2:
                return True

        return False

    def decide(
        self,
        ctx: ProactiveContext,
        signal: ProactiveSignal,
    ) -> bool:
        if self._is_sleeping(ctx):
            return False

        if ctx.now.hour >= 23 or ctx.now.hour <= 6:
            return False

        if ctx.life_state is not None:
            energy = getattr(
                ctx.life_state,
                "energy",
                None,
            )

            if energy is not None and energy < 0.25:
                return False

        if self._last_trigger is not None:
            if (
                ctx.now - self._last_trigger
                < self.cooldown
            ):
                return False

        return True

    def record_trigger(
        self,
        now,
    ) -> None:
        self._last_trigger = now
