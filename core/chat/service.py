from __future__ import annotations

from ..life_loop import LifeLoop
from ..runtime import AgentRuntime
from ..memory import (
    MemoryContextBuilder,
    MemoryManager,
    MemoryRecord,
    MemorySource,
    MemoryType,
)
from ..memory.importance import estimate_importance
from .models import ChatResult
from .request import ChatRequest, ChatMessage
from ..llm import (
    LLMProvider,
    LLMRequest,
    LLMMessage,
)
from .prompt import ChatPromptBuilder
from .provider import ResponseProvider
from .state_analyzer import ConversationStateAnalyzer
from ..relationship import RelationshipEngine
from .proactive_trigger import ProactiveTrigger
from .proactive_bridge import ProactiveBridge
from ..life.proactive_scheduler import ProactiveScheduler


class ChatService:
    """小七的文本对话核心。"""

    def __init__(
        self,
        life_loop: LifeLoop,
        memory_context_builder: MemoryContextBuilder,
        memory_manager: MemoryManager | None = None,
        prompt_builder: ChatPromptBuilder | None = None,
        response_provider: ResponseProvider | None = None,
        llm_provider: LLMProvider | None = None,
        runtime: AgentRuntime | None = None,
    ) -> None:
        self.life_loop = life_loop

        self.runtime = (
            runtime
            if runtime is not None
            else AgentRuntime(life_loop)
        )

        self.memory_context_builder = memory_context_builder

        from .state import ConversationState
        self.conversation_state = ConversationState()
        self.state_analyzer = ConversationStateAnalyzer()

        self.relationship_engine = RelationshipEngine()

        self.proactive_trigger = ProactiveTrigger(
            relationship_engine=self.relationship_engine
        )

        self.proactive_bridge = ProactiveBridge()
        self.proactive_scheduler = ProactiveScheduler()

        self.memory_manager = (
            memory_manager
            if memory_manager is not None
            else self.runtime.memory_manager
        )

        if self.memory_manager.store is not self.runtime.memory_store:
            raise ValueError(
                "memory_manager must use the same memory_store"
            )

        if prompt_builder is None:
            self.prompt_builder = ChatPromptBuilder(
                conversation_state=self.conversation_state,
                relationship_engine=self.relationship_engine,
            )
        else:
            self.prompt_builder = prompt_builder

        self.response_provider = response_provider
        self.llm_provider = llm_provider

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
            self.runtime.current_time,
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

        proactive_messages = []

        for event in self.runtime.get_proactive_events():
            message = self.proactive_trigger.handle(event)

            proactive_messages.append(message)

        return ChatResult(
            user_message=text,
            memory_context=memory_context,
            life_state=self.runtime.life_state,
            interaction_state=self.runtime.interaction_state,
            proactive_interests=(
                self.life_loop
                .memory_manager
                .proactive_manager
                .all()
            ),
            proactive_messages=proactive_messages,
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

        request = ChatRequest(
            messages=[
                ChatMessage(
                    role="user",
                    content=prompt,
                )
            ]
        )

        if self.llm_provider is not None:
            llm_request = LLMRequest(
                messages=[
                    LLMMessage(
                        role="user",
                        content=prompt,
                    )
                ]
            )

            llm_response = self.llm_provider.chat(
                llm_request
            )

            response = llm_response.content

        elif self.response_provider is not None:
            import inspect

            generate = self.response_provider.generate

            parameter = next(
                iter(
                    inspect.signature(generate).parameters.values()
                ),
                None,
            )

            if parameter is not None and parameter.annotation is str:
                response = generate(prompt)
            else:
                response = generate(request)

        else:
            raise RuntimeError(
                "no LLM provider configured"
            )

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
            created_at=self.runtime.current_time,
            source=MemorySource.CONVERSATION,
            importance=importance,
            confidence=1.0,
        )

        decision = self.memory_manager.process(memory)

        if decision.action == "add":
            return self.runtime.memory_store.get(
                memory.memory_id
            )

        return None

    def _next_interaction_memory_id(self) -> str:
        """生成不会与现有记忆冲突的 Interaction Memory ID。"""

        prefix = "interaction:"
        index = 1

        while self.runtime.memory_store.get(
            f"{prefix}{index}"
        ) is not None:
            index += 1

        return f"{prefix}{index}"
