from __future__ import annotations

from ..neurochemical.models import NeurochemicalState
from .models import EmotionState


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _default_attachment_drive(
    neuro_state: NeurochemicalState,
) -> float:
    """与 NeurochemicalEngine.attachment_drive 保持一致的默认公式。"""

    return _clamp(
        0.5 * (1.0 - neuro_state.oxytocin)
        + 0.3 * neuro_state.cortisol
        + 0.2 * (1.0 - neuro_state.serotonin)
    )


def map_neurochemical_to_emotions(
    neuro_state: NeurochemicalState,
    attachment_drive: float | None = None,
    novelty: float = 0.0,
) -> EmotionState:
    """把神经化学状态映射为多维情绪。

    - 开心：多巴胺 + 内啡肽 + 血清素
    - 孤独：催产素低 + 依恋需求高 + 血清素低
    - 兴奋：多巴胺 + 去甲肾上腺素
    - 焦虑：皮质醇高 + 血清素低
    - 生气：皮质醇高 + 多巴胺低 + 去甲肾上腺素高
    - 平静：皮质醇低 + 血清素高
    """

    if attachment_drive is None:
        attachment_drive = _default_attachment_drive(
            neuro_state
        )

    d = neuro_state.dopamine
    s = neuro_state.serotonin
    o = neuro_state.oxytocin
    c = neuro_state.cortisol
    e = neuro_state.endorphin
    n = neuro_state.noradrenaline

    return EmotionState(
        happy=_clamp(
            0.4 * d + 0.3 * e + 0.3 * s
        ),
        lonely=_clamp(
            0.5 * (1.0 - o)
            + 0.3 * attachment_drive
            + 0.2 * (1.0 - s)
        ),
        excited=_clamp(
            0.5 * d + 0.5 * n
        ),
        anxious=_clamp(
            0.6 * c + 0.4 * (1.0 - s)
        ),
        angry=_clamp(
            0.4 * c
            + 0.3 * (1.0 - d)
            + 0.3 * n
        ),
        calm=_clamp(
            0.5 * (1.0 - c) + 0.5 * s
        ),
    )
