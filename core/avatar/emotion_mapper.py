from __future__ import annotations

from typing import Mapping

# 内部情绪 -> Avatar 表现（expression / eyes / motion）。
# 第一版为确定性映射；真实接入可按角色模型调整。
EMOTION_PRESENTATIONS: Mapping[str, dict] = {
    "happy": {
        "expression": "smile",
        "eyes": "bright",
        "motion": "happy_idle",
    },
    "lonely": {
        "expression": "soft_sad",
        "eyes": "dim",
        "motion": "quiet_idle",
    },
    "excited": {
        "expression": "big_smile",
        "eyes": "bright",
        "motion": "excited_idle",
    },
    "anxious": {
        "expression": "worried",
        "eyes": "wide",
        "motion": "uneasy_idle",
    },
    "angry": {
        "expression": "frown",
        "eyes": "narrow",
        "motion": "tense_idle",
    },
    "calm": {
        "expression": "neutral",
        "eyes": "normal",
        "motion": "idle",
    },
}

DEFAULT_PRESENTATION = EMOTION_PRESENTATIONS["calm"]


def map_emotion(
    emotion_name: str,
    intensity: float = 1.0,
) -> dict:
    """把内部情绪映射为 Avatar 表现。"""

    base = EMOTION_PRESENTATIONS.get(
        emotion_name,
        DEFAULT_PRESENTATION,
    )

    return {
        **base,
        "intensity": max(0.0, min(1.0, intensity)),
    }


def expression_for(
    emotion_name: str,
) -> str:
    """返回表情名（如 smile）。"""

    return EMOTION_PRESENTATIONS.get(
        emotion_name,
        DEFAULT_PRESENTATION,
    )["expression"]


def motion_for(
    emotion_name: str,
) -> str:
    """返回情绪对应的待机动作名。"""

    return EMOTION_PRESENTATIONS.get(
        emotion_name,
        DEFAULT_PRESENTATION,
    )["motion"]
