from __future__ import annotations

from .models import ChatResult
from ..personality import (
    DEFAULT_PERSONALITY,
    PersonalityEngine,
)
from ..relationship import RelationshipEngine


class ChatPromptBuilder:
    """把 ChatResult 转换成供文本模型使用的 Prompt。"""

    def __init__(
        self,
        personality_engine: PersonalityEngine | None = None,
        relationship_engine: RelationshipEngine | None = None,
    ):
        self.personality_engine = (
            personality_engine
            if personality_engine is not None
            else PersonalityEngine(
                DEFAULT_PERSONALITY
            )
        )

        self.relationship_engine = (
            relationship_engine
            if relationship_engine is not None
            else RelationshipEngine()
        )

    def build(
        self,
        result: ChatResult,
    ) -> str:
        """构建包含人格、记忆、状态的 LLM 上下文。"""

        sections: list[str] = []

        sections.append(
            self.personality_engine.build_context()
        )

        sections.append(
            self.relationship_engine.build_context()
        )

        sections.append(
            f"用户当前消息：\n{result.user_message}"
        )

        self.relationship_engine.interact()

        memory_text = result.memory_text()

        if memory_text:
            sections.append(memory_text)

        sections.append(
            "【当前生活状态】\n"
            f"- 当前时间：{result.life_state.current_time}\n"
            f"- 当前活动：{result.life_state.current_activity}\n"
            f"- 疲劳：{result.life_state.fatigue}\n"
            f"- 精力：{result.life_state.energy}"
        )

        return "\n\n".join(sections)
