from datetime import datetime, timezone

import pytest

from core.chat import ChatResult, ChatService
from core.life_loop import LifeLoop
from core.memory import (
    MemoryContextBuilder,
    MemoryRecord,
    MemoryRetriever,
    MemorySource,
    MemoryStore,
    MemoryType,
)
from core.time_engine import make_aware


def make_memory(
    memory_id: str,
    content: str,
    memory_type: MemoryType = MemoryType.CANONICAL,
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=memory_type,
        content=content,
        created_at=datetime.now(timezone.utc),
        source=(
            MemorySource.USER_PROVIDED
            if memory_type == MemoryType.CANONICAL
            else MemorySource.CONVERSATION
        ),
        importance=1.0,
        confidence=1.0,
    )


def make_chat_service():
    store = MemoryStore()

    store.add(
        make_memory(
            "canonical:name",
            "姓名：小七",
        )
    )

    store.add(
        make_memory(
            "canonical:food",
            "小七喜欢吃面",
        )
    )

    retriever = MemoryRetriever(store)
    context_builder = MemoryContextBuilder(retriever)

    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
        memory_store=store,
    )

    return ChatService(
        life_loop=loop,
        memory_context_builder=context_builder,
    )


def test_chat_service_returns_structured_chat_result():
    chat = make_chat_service()

    result = chat.handle_message("小七喜欢吃什么？")

    assert isinstance(result, ChatResult)
    assert result.user_message == "小七喜欢吃什么？"

    assert result.life_state is chat.life_loop.life_state
    assert result.interaction_state is chat.life_loop.interaction_state


def test_chat_service_retrieves_relevant_memory():
    chat = make_chat_service()

    result = chat.handle_message("小七喜欢吃什么？")

    contents = [
        memory.content
        for memory in result.memory_context.memories
    ]

    assert "小七喜欢吃面" in contents


def test_chat_result_can_produce_memory_text_for_llm():
    chat = make_chat_service()

    result = chat.handle_message("小七喜欢吃什么？")

    text = result.memory_text()

    assert "【相关记忆】" in text
    assert "小七喜欢吃面" in text


def test_chat_service_rejects_empty_message():
    chat = make_chat_service()

    with pytest.raises(ValueError):
        chat.handle_message("")


def test_chat_service_does_not_call_llm():
    chat = make_chat_service()

    result = chat.handle_message("你好，小七")

    assert result.user_message == "你好，小七"
    assert isinstance(result, ChatResult)
