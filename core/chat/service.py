from __future__ import annotations

from ..life_loop import LifeLoop
from ..memory import (
    MemoryContextBuilder,
    MemoryManager,
    MemoryRecord,
    MemorySource,
    MemoryType,
)
from ..memory.importance import estimate_importance
from .models import ChatResult


class ChatService:
    """小七的文本对话核心。

    当前阶段不负责调用 LLM。
    它负责：
    - 接收用户消息
    - 检索相关记忆
    - 根据重要程度决定是否保存用户消息
    - 整理当前生活状态
    - 返回 ChatResult
    """

    def __init__(
        self,
        life_loop: LifeLoop,
        memory_context_builder: MemoryContextBuilder,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        self.life_loop = life_loop
        self.memory_context_builder = memory_context_builder

        self.memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager(self.life_loop.memory_store)
        )

        if self.memory_manager.store is not self.life_loop.memory_store:
            raise ValueError(
                "memory_manager must use the same memory_store"
            )

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

        self._store_user_message(text)

        return ChatResult(
            user_message=text,
            memory_context=memory_context,
            life_state=self.life_loop.life_state,
            interaction_state=self.life_loop.interaction_state,
        )

    def _store_user_message(
        self,
        text: str,
    ) -> MemoryRecord | None:
        """根据重要程度决定是否保存用户消息。"""

        importance = estimate_importance(text)

        memory = MemoryRecord(
            memory_id=self._next_interaction_memory_id(),
            memory_type=MemoryType.INTERACTION,
            content=text.strip(),
            created_at=self.life_loop.current_time,
            source=MemorySource.CONVERSATION,
            importance=importance,
            confidence=1.0,
        )

        decision = self.memory_manager.process(memory)

        if decision.action == "add":
            return self.life_loop.memory_store.get(
                memory.memory_id
            )

        return None

    def _next_interaction_memory_id(self) -> str:
        """生成不会与现有记忆冲突的 Interaction Memory ID。"""

        prefix = "interaction:"
        index = 1

        while self.life_loop.memory_store.get(
            f"{prefix}{index}"
        ) is not None:
            index += 1

        return f"{prefix}{index}"
