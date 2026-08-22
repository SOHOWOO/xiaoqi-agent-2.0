from __future__ import annotations

from typing import Mapping

# xiaoqi 情绪（core.emotion.EmotionType）-> OLV 前端 Live2D 表情名。
# OLV 前端常用的 Live2D 表情组（happy / neutral / sad / angry / surprised /
# afraid / disgusted 等）。真实接入时可按角色模型调整。
EMOTION_TO_EXPRESSION: Mapping[str, str] = {
    "happy": "happy",
    "lonely": "sad",
    "excited": "surprised",
    "anxious": "afraid",
    "angry": "angry",
    "calm": "neutral",
}

# 默认表情（未匹配时）
DEFAULT_EXPRESSION = "neutral"


def map_emotion_to_expression(
    emotion: str,
) -> str:
    """把 xiaoqi 主导情绪映射为 OLV 表情名。"""

    return EMOTION_TO_EXPRESSION.get(
        emotion,
        DEFAULT_EXPRESSION,
    )


def expressions_for_emotion(
    emotion: str,
    include_default: bool = False,
) -> list[str]:
    """返回 Actions.expressions 使用的表情列表。"""

    expression = map_emotion_to_expression(emotion)

    if include_default and expression != DEFAULT_EXPRESSION:
        return [expression, DEFAULT_EXPRESSION]

    return [expression]
