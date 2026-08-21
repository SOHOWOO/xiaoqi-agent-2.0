from __future__ import annotations

from .models import ChatResult
from ..personality import (
    DEFAULT_PERSONALITY,
    PersonalityEngine,
)
from ..relationship import RelationshipEngine
from .state import ConversationState


class ChatPromptBuilder:
    """把 ChatResult 转换成供文本模型使用的 Prompt。"""

    def __init__(
        self,
        personality_engine: PersonalityEngine | None = None,
        relationship_engine: RelationshipEngine | None = None,
        conversation_state: ConversationState | None = None,
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

        self.conversation_state = (
            conversation_state
            if conversation_state is not None
            else ConversationState()
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
            "【对话状态】\n"
            f"- 对话轮数：{self.conversation_state.turn_count}\n"
            f"- 当前情绪环境：{self.conversation_state.emotional_context}\n"
            f"- 最近主题：{self.conversation_state.topics}"
        )

        sections.append(
            "【对话状态】\n"
            f"- 对话轮数：{self.conversation_state.turn_count}\n"
            f"- 最近话题：{', '.join(self.conversation_state.topics)}\n"
            f"- 用户情绪：{self.conversation_state.emotional_context}"
        )

        sections.append(
            f"用户当前消息：\n{result.user_message}"
        )

        self.relationship_engine.interact()

        memory_text = result.memory_text()

        if memory_text:
            sections.append(memory_text)

        proactive_messages = getattr(
            result,
            "proactive_messages",
            [],
        )

        if proactive_messages:
            sections.append(
                "【主动关心事项】\n"
                + "\n".join(
                    [
                        f"- {msg.content}"
                        for msg in proactive_messages
                        if msg is not None
                    ]
                )
            )

        proactive_manager = getattr(
            getattr(result, "life_state", None),
            "proactive_manager",
            None,
        )

        if proactive_manager is not None:
            interests = proactive_manager.all()

            if interests:
                proactive_text = (
                    "【主动关注】\\n"
                    + "\\n".join(
                        [
                            f"- {item.content}"
                            for item in interests[-5:]
                        ]
                    )
                )

                sections.append(
                    proactive_text
                )

        sections.append(
            "【当前生活状态】\n"
            f"- 当前时间：{result.life_state.current_time}\n"
            f"- 当前活动：{result.life_state.current_activity}\n"
            f"- 疲劳：{result.life_state.fatigue}\n"
            f"- 精力：{result.life_state.energy}"
        )

        return "\n\n".join(sections)
