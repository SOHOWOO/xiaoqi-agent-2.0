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
from .prompt import ChatPromptBuilder
from .provider import ResponseProvider
from .state_analyzer import ConversationStateAnalyzer
from .proactive_bridge import ProactiveBridge


class ChatService:
    """小七的文本对话核心。"""

    def __init__(
        self,
        life_loop: LifeLoop,
        memory_context_builder: MemoryContextBuilder,
        memory_manager: MemoryManager | None = None,
        prompt_builder: ChatPromptBuilder | None = None,
        response_provider: ResponseProvider | None = None,
    ) -> None:
        self.life_loop = life_loop
        self.memory_context_builder = memory_context_builder

        from .state import ConversationState
        self.conversation_state = ConversationState()
        self.state_analyzer = ConversationStateAnalyzer()
        self.proactive_bridge = ProactiveBridge()

        self.memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager(self.life_loop.memory_store)
        )

        if self.memory_manager.store is not self.life_loop.memory_store:
            raise ValueError(
                "memory_manager must use the same memory_store"
            )

        if prompt_builder is None:
            self.prompt_builder = ChatPromptBuilder(
                conversation_state=self.conversation_state
            )
        else:
            self.prompt_builder = prompt_builder

        self.response_provider = response_provider

    def handle_message(
        self,
        text: str,
        memory_limit: int = 5,
    ) -> ChatResult:
        """处理一条用户文本消息并构建上下文。"""

        if not text.strip():
            raise ValueError("message cannot be empty")

        self.conversation_state.update_user_message(
            text,
            self.life_loop.current_time,
        )

        self.state_analyzer.analyze(
            text,
            self.conversation_state,
        )

        self.proactive_bridge.register_from_text(
            text,
            self.life_loop,
        )

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

    def respond(
        self,
        result: ChatResult,
    ) -> str:
        """使用配置的 ResponseProvider 生成文本回复。"""

        if self.response_provider is None:
            raise RuntimeError(
                "response_provider is not configured"
            )

        prompt = self.prompt_builder.build(result)

        response = self.response_provider.generate(prompt)

        self.conversation_state.update_assistant_message(
            response
        )

        return response

    def handle_and_respond(
        self,
        text: str,
        memory_limit: int = 5,
    ) -> str:
        """处理用户消息并直接返回文本回复。"""

        result = self.handle_message(
            text,
            memory_limit=memory_limit,
        )

        return self.respond(result)

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
