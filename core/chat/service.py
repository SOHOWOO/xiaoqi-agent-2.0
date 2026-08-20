from __future__ import annotations

from ..life_loop import LifeLoop
from ..memory import MemoryContextBuilder
from .models import ChatResult


class ChatService:
    """小七的文本对话核心。

    当前阶段不负责调用 LLM。
    它负责把用户消息、记忆和当前状态
    整理成 ChatResult，供未来 LLM 层消费。
    """

    def __init__(
        self,
        life_loop: LifeLoop,
        memory_context_builder: MemoryContextBuilder,
    ) -> None:
        self.life_loop = life_loop
        self.memory_context_builder = memory_context_builder

    def handle_message(
        self,
        text: str,
        memory_limit: int = 5,
    ) -> ChatResult:
        """处理一条用户文本消息。"""

        if not text.strip():
            raise ValueError("message cannot be empty")

        memory_context = self.memory_context_builder.build(
            text,
            limit=memory_limit,
        )

        return ChatResult(
            user_message=text,
            memory_context=memory_context,
            life_state=self.life_loop.life_state,
            interaction_state=self.life_loop.interaction_state,
        )
