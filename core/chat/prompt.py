from __future__ import annotations

from .models import ChatResult


class ChatPromptBuilder:
    """把 ChatResult 转换成供文本模型使用的 Prompt。"""

    def build(self, result: ChatResult) -> str:
        """构建稳定、可供 LLM 消费的纯文本上下文。"""

        sections: list[str] = []

        sections.append(
            "你是小七，一名具有持续生活记忆与长期关系记忆的 AI 女友。"
        )

        sections.append(
            f"用户当前消息：\n{result.user_message}"
        )

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
