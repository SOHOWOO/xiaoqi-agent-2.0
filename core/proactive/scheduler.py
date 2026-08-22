from __future__ import annotations

from datetime import timedelta

from .models import ProactiveContext, ProactiveSignal


class ProactiveGate:
    """主动行为的门控层。

    负责：
    - 冷却保护（指数退避：连续主动后冷却逐渐拉长，
      避免失联时像"提醒器"一样频繁打扰）
    - 打扰避免（睡眠 / 深夜不主动打扰）
    - 精力保护（太累时不主动）

    用户回应后应调用 reset_backoff() 重置退避。
    """

    SLEEP_SLOT_KEYWORDS = ("sleep", "pre_sleep")

    def __init__(
        self,
        cooldown_minutes: int = 6 * 60,
        backoff_factor: float = 2.0,
        max_cooldown_minutes: int = 48 * 60,
    ) -> None:
        self._base_cooldown = timedelta(
            minutes=cooldown_minutes
        )

        if backoff_factor < 1.0:
            raise ValueError(
                "backoff_factor must be >= 1.0"
            )

        if max_cooldown_minutes < cooldown_minutes:
            raise ValueError(
                "max_cooldown_minutes must be >= "
                "cooldown_minutes"
            )

        self.backoff_factor = backoff_factor
        self.max_cooldown = timedelta(
            minutes=max_cooldown_minutes
        )

        self._consecutive = 0
        self._last_trigger: object | None = None

    def _current_cooldown(self) -> timedelta:
        exponent = max(0, self._consecutive - 1)
        raw = self._base_cooldown * (
            self.backoff_factor ** exponent
        )

        return min(self.max_cooldown, raw)

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
                < self._current_cooldown()
            ):
                return False

        return True

    def record_trigger(
        self,
        now,
    ) -> None:
        self._consecutive += 1
        self._last_trigger = now

    def reset_backoff(
        self,
    ) -> None:
        """用户回应后重置退避冷却。"""

        self._consecutive = 0
        self._last_trigger = None
