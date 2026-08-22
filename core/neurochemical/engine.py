from __future__ import annotations

import math
from typing import Mapping

from .models import (
    DEFAULT_PROFILES,
    NeurochemicalProfile,
    NeurochemicalState,
    NeurochemicalStimulus,
    Neurotransmitter,
    StimulusType,
)


STIMULUS_EFFECTS: dict[
    StimulusType, dict[Neurotransmitter, float]
] = {
    StimulusType.USER_INTERACTION: {
        Neurotransmitter.OXYTOCIN: 0.15,
        Neurotransmitter.DOPAMINE: 0.10,
        Neurotransmitter.ENDORPHIN: 0.05,
        Neurotransmitter.CORTISOL: -0.05,
    },
    StimulusType.PROLONGED_ABSENCE: {
        Neurotransmitter.OXYTOCIN: -0.10,
        Neurotransmitter.CORTISOL: 0.12,
        Neurotransmitter.SEROTONIN: -0.05,
    },
    StimulusType.ACHIEVEMENT: {
        Neurotransmitter.DOPAMINE: 0.20,
        Neurotransmitter.ENDORPHIN: 0.10,
        Neurotransmitter.SEROTONIN: 0.05,
    },
    StimulusType.PRAISE: {
        Neurotransmitter.DOPAMINE: 0.15,
        Neurotransmitter.SEROTONIN: 0.10,
        Neurotransmitter.OXYTOCIN: 0.05,
    },
    StimulusType.CONFLICT: {
        Neurotransmitter.CORTISOL: 0.20,
        Neurotransmitter.DOPAMINE: -0.10,
        Neurotransmitter.SEROTONIN: -0.10,
        Neurotransmitter.NORADRENALINE: 0.15,
    },
    StimulusType.NOVELTY: {
        Neurotransmitter.DOPAMINE: 0.12,
        Neurotransmitter.NORADRENALINE: 0.10,
    },
    StimulusType.REST: {
        Neurotransmitter.CORTISOL: -0.10,
        Neurotransmitter.ENDORPHIN: 0.05,
        Neurotransmitter.SEROTONIN: 0.05,
        Neurotransmitter.NORADRENALINE: -0.10,
    },
    StimulusType.STRESSOR: {
        Neurotransmitter.CORTISOL: 0.15,
        Neurotransmitter.NORADRENALINE: 0.10,
        Neurotransmitter.SEROTONIN: -0.05,
    },
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _baseline_state(
    profiles: Mapping[Neurotransmitter, NeurochemicalProfile],
) -> NeurochemicalState:
    return NeurochemicalState(
        dopamine=profiles[Neurotransmitter.DOPAMINE].baseline,
        serotonin=profiles[Neurotransmitter.SEROTONIN].baseline,
        oxytocin=profiles[Neurotransmitter.OXYTOCIN].baseline,
        cortisol=profiles[Neurotransmitter.CORTISOL].baseline,
        endorphin=profiles[Neurotransmitter.ENDORPHIN].baseline,
        noradrenaline=profiles[
            Neurotransmitter.NORADRENALINE
        ].baseline,
    )


class NeurochemicalEngine:
    """神经化学引擎。

    持有当前神经化学状态，负责：
    - tick：随时间向基线回归（自然衰减 / 恢复）
    - apply_stimulus：外部刺激改变浓度
    - 派生元状态：reward_signal / stress_level /
      attachment_drive / curiosity / arousal / mood_stability

    这些派生状态将驱动 EmotionEngine 与 ProactiveEngine。
    """

    def __init__(
        self,
        profiles: Mapping[
            Neurotransmitter, NeurochemicalProfile
        ] | None = None,
        initial_state: NeurochemicalState | None = None,
    ) -> None:
        self._profiles = (
            dict(profiles)
            if profiles is not None
            else dict(DEFAULT_PROFILES)
        )

        self._state = (
            initial_state
            if initial_state is not None
            else _baseline_state(self._profiles)
        )

    def tick(
        self,
        hours: float,
    ) -> NeurochemicalState:
        """让所有神经化学物质向基线回归。

        采用与时间步长绑定的指数衰减（EMA）：
            new = baseline + (old - baseline) * exp(-decay_per_hour * hours)

        该形式在任意步长下演化一致（大步长 = 小步长的复合），
        是 LifeLoop 大步长分解积分的数学基础。
        """

        if hours < 0:
            raise ValueError(
                "hours must be non-negative"
            )

        if hours == 0:
            return self._state

        new_values: dict[str, float] = {}

        for (
            nt,
            profile,
        ) in self._profiles.items():
            old = self._state.level(nt)

            decay = math.exp(
                -profile.decay_per_hour * hours
            )

            new = (
                profile.baseline
                + (old - profile.baseline) * decay
            )

            new_values[nt.value] = _clamp(new)

        self._state = NeurochemicalState(**new_values)

        return self._state

    def apply_stimulus(
        self,
        stimulus: NeurochemicalStimulus,
    ) -> NeurochemicalState:
        """应用一次外部刺激。"""

        effects = STIMULUS_EFFECTS.get(
            stimulus.stimulus_type,
            {},
        )

        new_values: dict[str, float] = {}

        for nt in Neurotransmitter:
            old = self._state.level(nt)

            delta = (
                effects.get(nt, 0.0)
                * stimulus.intensity
            )

            new_values[nt.value] = _clamp(
                old + delta
            )

        self._state = NeurochemicalState(**new_values)

        return self._state

    def state(self) -> NeurochemicalState:
        """返回当前快照（不可变）。"""

        return self._state

    def restore(
        self,
        state: NeurochemicalState,
    ) -> None:
        """从持久化恢复状态。"""

        self._state = state

    def reset(self) -> None:
        """重置为基线状态。"""

        self._state = _baseline_state(self._profiles)

    # ---------------------------------------------------------
    # 派生元状态（均归一化到 0.0 ~ 1.0）
    # ---------------------------------------------------------

    def reward_signal(self) -> float:
        """奖励 / 动机信号。"""

        s = self._state

        return _clamp(
            0.6 * s.dopamine + 0.4 * s.endorphin
        )

    def stress_level(self) -> float:
        """压力水平。"""

        s = self._state

        return _clamp(
            0.7 * s.cortisol + 0.3 * (1.0 - s.serotonin)
        )

    def attachment_drive(self) -> float:
        """依恋需求：催产素越低、压力越高、满足感越低则越强。"""

        s = self._state

        return _clamp(
            0.5 * (1.0 - s.oxytocin)
            + 0.3 * s.cortisol
            + 0.2 * (1.0 - s.serotonin)
        )

    def curiosity(
        self,
        novelty: float = 0.0,
    ) -> float:
        """好奇心，可叠加外部新奇度（0.0 ~ 1.0）。"""

        if not 0.0 <= novelty <= 1.0:
            raise ValueError(
                "novelty must be between 0.0 and 1.0"
            )

        s = self._state

        return _clamp(
            0.5 * s.dopamine
            + 0.3 * s.noradrenaline
            + 0.2 * novelty
        )

    def arousal(self) -> float:
        """唤醒 / 警觉程度。"""

        return self._state.noradrenaline

    def mood_stability(self) -> float:
        """情绪稳定性。"""

        return self._state.serotonin
