from datetime import datetime, timezone

from core.memory import (
    MemoryContext,
    MemoryContextBuilder,
    MemoryRecord,
    MemoryRetriever,
    MemorySource,
    MemoryStore,
    MemoryType,
)


def make_memory(
    memory_id,
    memory_type,
    content,
    importance=0.5,
):
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
        importance=importance,
        confidence=1.0,
    )


def test_context_builder_returns_relevant_memories():
    store = MemoryStore()

    store.add(
        make_memory(
            "canonical:food",
            MemoryType.CANONICAL,
            "小七喜欢吃面",
            importance=1.0,
        )
    )

    store.add(
        make_memory(
            "canonical:drink",
            MemoryType.CANONICAL,
            "小七喜欢喝咖啡",
            importance=1.0,
        )
    )

    retriever = MemoryRetriever(store)
    builder = MemoryContextBuilder(retriever)

    context = builder.build("小七喜欢吃什么？")

    assert isinstance(context, MemoryContext)
    assert context.query == "小七喜欢吃什么？"
    assert len(context.memories) >= 1
    assert context.memories[0].content == "小七喜欢吃面"


def test_context_as_text_contains_memory_type_and_content():
    store = MemoryStore()

    store.add(
        make_memory(
            "canonical:food",
            MemoryType.CANONICAL,
            "小七喜欢吃面",
            importance=1.0,
        )
    )

    retriever = MemoryRetriever(store)
    builder = MemoryContextBuilder(retriever)

    context = builder.build("小七喜欢吃什么？")
    text = context.as_text()

    assert "【相关记忆】" in text
    assert "[canonical]" in text
    assert "小七喜欢吃面" in text


def test_empty_context_as_text_is_empty():
    store = MemoryStore()

    retriever = MemoryRetriever(store)
    builder = MemoryContextBuilder(retriever)

    context = builder.build("完全不存在的内容")

    assert context.memories == []
    assert context.as_text() == ""


def test_context_respects_limit():
    store = MemoryStore()

    for index in range(5):
        store.add(
            make_memory(
                f"canonical:food:{index}",
                MemoryType.CANONICAL,
                f"小七喜欢吃面和食物{index}",
                importance=1.0,
            )
        )

    retriever = MemoryRetriever(store)
    builder = MemoryContextBuilder(retriever)

    context = builder.build(
        "小七喜欢吃什么",
        limit=2,
    )

    assert len(context.memories) == 2
