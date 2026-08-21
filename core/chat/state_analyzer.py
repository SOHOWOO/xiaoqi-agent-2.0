from __future__ import annotations

from .state import ConversationState


class ConversationStateAnalyzer:
    """轻量级对话状态分析器。"""

    EMOTION_MAP = {
        "累": "疲惫",
        "疲惫": "疲惫",
        "压力": "压力",
        "开心": "开心",
        "高兴": "开心",
        "喜欢": "喜欢",
        "期待": "期待",
        "难过": "低落",
        "伤心": "低落",
    }

    TOPIC_KEYWORDS = {
        "工作": "工作",
        "上班": "工作",
        "学习": "学习",
        "考试": "学习",
        "旅行": "旅行",
        "旅游": "旅行",
        "长沙": "长沙",
        "吃": "饮食",
        "喜欢": "偏好",
        "计划": "计划",
        "明天": "计划",
    }

    def analyze(
        self,
        text: str,
        state: ConversationState,
    ) -> None:

        for keyword, emotion in self.EMOTION_MAP.items():
            if keyword in text:
                state.emotional_context = emotion
                break

        for keyword, topic in self.TOPIC_KEYWORDS.items():
            if keyword in text:
                state.add_topic(topic)
