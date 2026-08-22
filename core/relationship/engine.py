from __future__ import annotations

import math
from datetime import datetime

from .models import RelationshipState

_EVENT_EFFECTS = {
    "user_interaction": {
        "familiarity": 0.020,
        "attachment": 0.015,
        "trust": 0.005,
        "shared_experience": 0.000,
    },
    "mutual_help": {
        "familiarity": 0.020,
        "attachment": 0.020,
        "trust": 0.050,
        "shared_experience": 0.010,
    },
    "shared_experience": {
        "familiarity": 0.020,
        "attachment": 0.015,
        "trust": 0.010,
        "shared_experience": 0.050,
    },
    "comfort": {
        "familiarity": 0.015,
        "attachment": 0.025,
        "trust": 0.030,
        "shared_experience": 0.005,
    },
    "conflict": {
        "familiarity": -0.010,
        "attachment": -0.030,
        "trust": -0.060,
        "shared_experience": -0.005,
    },
}

# 时间衰减速率（每天，指数形式 exp(-rate*days)）
_DECAY_RATES = {
    "familiarity": 0.020,
    "attachment": 0.008,
    "trust": 0.003,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class RelationshipEngine:
    """多维关系引擎。

    关系由两类力驱动：
    - 事件力（update）：互动 / 互助 / 共同经历 / 冲突
    - 时间力（tick）：长时间不互动，熟悉度与依恋缓慢衰减

    接入 LifeLoop 主循环后，时间衰减在每次 tick 自动发生，
    用户交互由 ChatService 触发 update。
    """

    def __init__(
        self,
        state: RelationshipState | None = None,
    ) -> None:
        self.state = (
            state
            if state is not None
            else RelationshipState()
        )

        # 引擎上次 tick 时刻，用于增量时间衰减。
        # 修复：此前用 (now - last_interaction) 累计时长做指数衰减，
        # 会被每次 tick 复合放大（7 天 672 tick 后关系几乎归零）。
        self._last_tick_at: datetime | None = None

    # ---------------------------------------------------------
    # 事件驱动
    # ---------------------------------------------------------

    def interact(
        self,
        now: datetime | None = None,
    ) -> RelationshipState:
        """用户互动（向后兼容接口）。"""

        return self.update(
            "user_interaction",
            intensity=1.0,
            now=now,
        )

    def update(
        self,
        event_type: str,
        intensity: float = 1.0,
        now: datetime | None = None,
    ) -> RelationshipState:
        """按事件类型更新关系维度。"""

        if not 0.0 <= intensity <= 1.0:
            raise ValueError(
                "intensity must be between 0.0 and 1.0"
            )

        effects = _EVENT_EFFECTS.get(
            event_type,
            {},
        )

        for name, delta in effects.items():
            current = getattr(self.state, name)
            setattr(
                self.state,
                name,
                _clamp(current + delta * intensity),
            )

        self.state.interaction_count += 1

        if now is not None:
            self.state.last_interaction_at = now

        return self.state

    # ---------------------------------------------------------
    # 时间驱动（时间衰减）
    # ---------------------------------------------------------

    def tick(
        self,
        now: datetime,
    ) -> RelationshipState:
        """按本次 tick 的时间增量衰减关系强度。

        首次调用仅记录基线时刻；之后每次只衰减
        自上次 tick 以来的时间差（delta_days），
        确保连续 N 次小步长 == 一次大步长。
        """

        if self._last_tick_at is None:
            self._last_tick_at = now
            return self.state

        delta_days = max(
            0.0,
            (now - self._last_tick_at).total_seconds()
            / 86400.0,
        )

        self._last_tick_at = now

        if delta_days <= 0:
            return self.state

        for name, rate in _DECAY_RATES.items():
            current = getattr(self.state, name)

            decayed = current * math.exp(-rate * delta_days)

            setattr(
                self.state,
                name,
                _clamp(decayed),
            )

        return self.state

    # ---------------------------------------------------------
    # 输出
    # ---------------------------------------------------------

    def build_context(self) -> str:
        s = self.state

        return "\n".join(
            [
                "【关系状态】",
                f"互动次数：{s.interaction_count}",
                f"信任度：{s.trust:.2f}",
                f"依恋度：{s.attachment:.2f}",
                f"熟悉度：{s.familiarity:.2f}",
                f"共同经历：{s.shared_experience:.2f}",
                f"关系阶段：{s.stage}",
            ]
        )

    def to_dict(self) -> dict:
        return self.state.as_dict()

    def restore(
        self,
        data: dict,
    ) -> None:
        """从持久化数据恢复。"""

        self.state = RelationshipState.from_dict(data)
