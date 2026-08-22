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
        life_loop=None,
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

        self.life_loop = life_loop

    def _emotion_section(self) -> str | None:
        """注入小七当前情绪与神经化学状态。"""

        life_loop = self.life_loop

        if life_loop is None:
            return None

        emotion = getattr(
            life_loop,
            "emotion",
            None,
        )

        if emotion is None:
            return None

        state = emotion.state()

        emotion_desc = (
            "、".join(
                [
                    f"{name}: {value:.2f}"
                    for name, value in sorted(
                        state.as_dict().items(),
                        key=lambda kv: -kv[1],
                    )
                    if value >= 0.3
                ]
            )
            or state.dominant().value
        )

        lines = [
            "【小七当前状态】",
            f"- 主导情绪：{state.dominant().value}",
            f"- 情绪明细：{emotion_desc}",
        ]

        neuro = getattr(
            life_loop,
            "neurochemical",
            None,
        )

        if neuro is not None:
            neuro_state = neuro.state()

            lines.append(
                "- 神经化学："
                + "、".join(
                    [
                        f"{name}: {value:.2f}"
                        for name, value in sorted(
                            neuro_state.as_dict().items(),
                            key=lambda kv: -kv[1],
                        )
                    ]
                )
            )

        diary = getattr(
            life_loop,
            "diary",
            None,
        )

        if diary is not None:
            recent = diary.recent(limit=1)

            if recent:
                latest = recent[-1]

                lines.append(
                    f"- 最近日记（{latest.date.isoformat()}）："
                    f"{latest.content.splitlines()[0]}"
                )

        return "\n".join(lines)

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

        emotion_section = self._emotion_section()

        if emotion_section is not None:
            sections.append(emotion_section)

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

        memory_context = getattr(
            result,
            "memory_context",
            None,
        )

        if memory_context is not None:
            memory_sections = []

            canonical = memory_context.canonical()
            if canonical:
                memory_sections.append(
                    "【长期记忆】\n"
                    + "\n".join(
                        [
                            f"- {m.content}"
                            for m in canonical
                        ]
                    )
                )

            interaction = memory_context.interaction()
            if interaction:
                memory_sections.append(
                    "【互动记忆】\n"
                    + "\n".join(
                        [
                            f"- {m.content}"
                            for m in interaction[-5:]
                        ]
                    )
                )

            virtual = memory_context.virtual_life()
            if virtual:
                memory_sections.append(
                    "【生活经历】\n"
                    + "\n".join(
                        [
                            f"- {m.content}"
                            for m in virtual[-5:]
                        ]
                    )
                )

            if memory_sections:
                sections.extend(memory_sections)

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

        interests = getattr(
            result,
            "proactive_interests",
            [],
        )

        if interests:
            sections.append(
                "【主动关注】\n"
                + "\n".join(
                    [
                        f"- {item.content}"
                        for item in interests[-5:]
                    ]
                )
            )

        sections.append(
            "【当前生活状态】\n"
            f"- 当前时间：{result.life_state.current_time}\n"
            f"- 当前活动：{result.life_state.current_activity}\n"
            f"- 疲劳：{result.life_state.fatigue}\n"
            f"- 精力：{result.life_state.energy}"
        )

        return "\n\n".join(sections)
