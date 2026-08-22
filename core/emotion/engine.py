from __future__ import annotations

import math
from typing import Mapping

from ..neurochemical.models import NeurochemicalState
from .coupling import map_neurochemical_to_emotions
from .models import (
    EmotionEvent,
    EmotionState,
    EmotionType,
)


EMOTION_BASELINE: dict[EmotionType, float] = {
    EmotionType.CALM: 0.50,
    EmotionType.HAPPY: 0.15,
    EmotionType.LONELY: 0.10,
    EmotionType.EXCITED: 0.10,
    EmotionType.ANXIOUS: 0.10,
    EmotionType.ANGRY: 0.05,
}

DEFAULT_DECAY_PER_HOUR = 0.15

NEUROCHEMICAL_BLEND_RATE = 0.5

# 神经化学→情绪 平滑的时间常数（小时）：
# 约 4 小时后情绪向神经化学目标趋近 ~63%。
NEUROCHEMICAL_BLEND_TAU_HOURS = 4.0

INVERSE_EMOTION: dict[EmotionType, EmotionType | None] = {
    EmotionType.HAPPY: EmotionType.LONELY,
    EmotionType.LONELY: EmotionType.HAPPY,
    EmotionType.EXCITED: EmotionType.CALM,
    EmotionType.ANXIOUS: EmotionType.CALM,
    EmotionType.ANGRY: EmotionType.CALM,
    EmotionType.CALM: None,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _baseline_state(
    baseline: Mapping[EmotionType, float],
) -> EmotionState:
    return EmotionState(
        **{
            e.value: baseline[e]
            for e in EmotionType
        }
    )


class EmotionEngine:
    """情绪引擎。

    情绪由三层共同塑造：
    1. 神经化学（update_from_neurochemical，底层驱动）
    2. 情绪事件（apply_event，瞬时冲击）
    3. 时间衰减（tick，向平静基线回归）

    事件效果会随神经化学更新逐渐被"拉回"到神经化学目标，
    体现"神经化学是情绪底层驱动力"的设定。
    """

    def __init__(
        self,
        baseline: Mapping[
            EmotionType, float
        ] | None = None,
        decay_per_hour: float = DEFAULT_DECAY_PER_HOUR,
        initial_state: EmotionState | None = None,
    ) -> None:
        self._baseline = (
            dict(baseline)
            if baseline is not None
            else dict(EMOTION_BASELINE)
        )

        if not 0.0 < decay_per_hour <= 1.0:
            raise ValueError(
                "decay_per_hour must be in (0.0, 1.0]"
            )

        self._decay_per_hour = decay_per_hour

        self._state = (
            initial_state
            if initial_state is not None
            else _baseline_state(self._baseline)
        )

    def tick(
        self,
        hours: float,
    ) -> EmotionState:
        """所有情绪向平静基线回归。

        采用与时间步长绑定的指数衰减（EMA），保证大步长
        与小步长复合的演化结果一致。
        """

        if hours < 0:
            raise ValueError(
                "hours must be non-negative"
            )

        if hours == 0:
            return self._state

        new_values: dict[str, float] = {}

        for e in EmotionType:
            old = self._state.level(e)
            baseline = self._baseline[e]

            decay = math.exp(
                -self._decay_per_hour * hours
            )

            new = baseline + (
                old - baseline
            ) * decay

            new_values[e.value] = _clamp(new)

        self._state = EmotionState(**new_values)

        return self._state

    def update_from_neurochemical(
        self,
        neuro_state: NeurochemicalState,
        attachment_drive: float | None = None,
        novelty: float = 0.0,
        elapsed_hours: float | None = None,
    ) -> EmotionState:
        """按神经化学映射情绪，并以平滑率过渡。

        传入 elapsed_hours 时使用时间绑定 EMA（α = 1-e^(-Δt/τ)），
        保证不同推进步长下演化一致；未传入时退回固定混合率。
        """

        target = map_neurochemical_to_emotions(
            neuro_state,
            attachment_drive=attachment_drive,
            novelty=novelty,
        )

        if elapsed_hours is not None:
            if elapsed_hours < 0:
                raise ValueError(
                    "elapsed_hours must be non-negative"
                )

            alpha = 1.0 - math.exp(
                -elapsed_hours
                / NEUROCHEMICAL_BLEND_TAU_HOURS
            )
        else:
            alpha = NEUROCHEMICAL_BLEND_RATE

        new_values: dict[str, float] = {}

        for e in EmotionType:
            old = self._state.level(e)
            goal = target.level(e)

            new = old + (
                goal - old
            ) * alpha

            new_values[e.value] = _clamp(new)

        self._state = EmotionState(**new_values)

        return self._state

    def apply_event(
        self,
        event: EmotionEvent,
    ) -> EmotionState:
        """应用一次情绪事件。

        目标情绪增强，相反情绪减弱，其余不变。
        """

        new_values: dict[str, float] = {}

        inverse = INVERSE_EMOTION[event.emotion]

        for e in EmotionType:
            value = self._state.level(e)

            if e == event.emotion:
                value += event.intensity
            elif e == inverse:
                value -= event.intensity * 0.5

            new_values[e.value] = _clamp(value)

        self._state = EmotionState(**new_values)

        return self._state

    def state(self) -> EmotionState:
        """返回当前快照（不可变）。"""

        return self._state

    def restore(
        self,
        state: EmotionState,
    ) -> None:
        """从持久化恢复状态。"""

        self._state = state

    def reset(self) -> None:
        """重置为平静基线。"""

        self._state = _baseline_state(self._baseline)

    # ---------------------------------------------------------
    # 派生指标
    # ---------------------------------------------------------

    def dominant_emotion(self) -> EmotionType:
        """当前主导情绪。"""

        return self._state.dominant()

    def valence(self) -> float:
        """情绪效价（正向程度），0.0 ~ 1.0。"""

        s = self._state

        return _clamp(
            0.5
            + 0.25 * (s.happy + s.excited)
            - 0.25 * (s.anxious + s.angry + s.lonely)
        )

    def arousal(self) -> float:
        """情绪唤醒度，0.0 ~ 1.0。"""

        s = self._state

        return _clamp(
            0.6 * s.excited
            + 0.3 * s.anxious
            + 0.2 * s.angry
        )

    def positive_tone(self) -> float:
        """对话表达时带出的积极语气权重。"""

        s = self._state

        return _clamp(
            s.happy + s.calm + 0.5 * s.excited
            - 0.5 * s.anxious
            - s.angry
            - 0.5 * s.lonely
        )
