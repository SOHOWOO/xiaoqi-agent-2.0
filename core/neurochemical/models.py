from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Neurotransmitter(str, Enum):
    """小七的神经化学物质。

    浓度统一为 0.0 ~ 1.0 的归一化值。
    """

    DOPAMINE = "dopamine"
    SEROTONIN = "serotonin"
    OXYTOCIN = "oxytocin"
    CORTISOL = "cortisol"
    ENDORPHIN = "endorphin"
    NORADRENALINE = "noradrenaline"


@dataclass(frozen=True)
class NeurochemicalProfile:
    """某种神经化学物质的动力学参数。"""

    neurotransmitter: Neurotransmitter

    baseline: float
    decay_per_hour: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.baseline <= 1.0:
            raise ValueError(
                "baseline must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.decay_per_hour <= 1.0:
            raise ValueError(
                "decay_per_hour must be between 0.0 and 1.0"
            )


DEFAULT_PROFILES = {
    Neurotransmitter.DOPAMINE: NeurochemicalProfile(
        Neurotransmitter.DOPAMINE, 0.45, 0.15
    ),
    Neurotransmitter.SEROTONIN: NeurochemicalProfile(
        Neurotransmitter.SEROTONIN, 0.55, 0.08
    ),
    Neurotransmitter.OXYTOCIN: NeurochemicalProfile(
        Neurotransmitter.OXYTOCIN, 0.35, 0.10
    ),
    Neurotransmitter.CORTISOL: NeurochemicalProfile(
        Neurotransmitter.CORTISOL, 0.25, 0.20
    ),
    Neurotransmitter.ENDORPHIN: NeurochemicalProfile(
        Neurotransmitter.ENDORPHIN, 0.30, 0.25
    ),
    Neurotransmitter.NORADRENALINE: NeurochemicalProfile(
        Neurotransmitter.NORADRENALINE, 0.40, 0.30
    ),
}


@dataclass(frozen=True)
class NeurochemicalState:
    """某一时刻的神经化学快照。

    不可变，便于在 LifeLoop / 测试之间传递与比较。
    """

    dopamine: float
    serotonin: float
    oxytocin: float
    cortisol: float
    endorphin: float
    noradrenaline: float

    _FIELDS = (
        "dopamine",
        "serotonin",
        "oxytocin",
        "cortisol",
        "endorphin",
        "noradrenaline",
    )

    def __post_init__(self) -> None:
        for name in self._FIELDS:
            value = getattr(self, name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0.0 and 1.0"
                )

    def level(
        self,
        nt: Neurotransmitter,
    ) -> float:
        """按神经递质枚举读取浓度。"""

        return getattr(self, nt.value)

    def as_dict(self) -> dict:
        """返回以 neurotransmitter value 为键的字典。"""

        return {
            nt.value: self.level(nt)
            for nt in Neurotransmitter
        }


class StimulusType(str, Enum):
    """驱动神经化学变化的外部刺激类型。"""

    USER_INTERACTION = "user_interaction"
    PROLONGED_ABSENCE = "prolonged_absence"
    ACHIEVEMENT = "achievement"
    PRAISE = "praise"
    CONFLICT = "conflict"
    NOVELTY = "novelty"
    REST = "rest"
    STRESSOR = "stressor"


@dataclass(frozen=True)
class NeurochemicalStimulus:
    """一次外部刺激。

    intensity 越高，对应 STIMULUS_EFFECTS 中的 delta 影响越大。
    """

    stimulus_type: StimulusType
    intensity: float = 0.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(
                "intensity must be between 0.0 and 1.0"
            )
