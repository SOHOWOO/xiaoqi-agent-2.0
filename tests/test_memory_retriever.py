from datetime import datetime, timezone

from core.memory import MemoryStore
from core.memory.models import MemoryRecord, MemorySource, MemoryType
from core.memory.retriever import MemoryRetriever


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


def test_retriever_can_find_memory():
    store = MemoryStore()

    store.add(
        make_memory(
            "canonical:name",
            MemoryType.CANONICAL,
            "姓名：小七",
            importance=1.0,
        )
    )

    retriever = MemoryRetriever(store)

    results = retriever.search("小七")

    assert len(results) == 1
    assert results[0].content == "姓名：小七"


def test_retriever_can_search_different_memory_types():
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
            "interaction:food",
            MemoryType.INTERACTION,
            "臭宝和小七聊过吃面",
            importance=0.8,
        )
    )

    store.add(
        make_memory(
            "virtual:food",
            MemoryType.VIRTUAL_LIFE,
            "小七今天午饭吃了面",
            importance=0.8,
        )
    )

    retriever = MemoryRetriever(store)

    results = retriever.search("面", limit=10)

    assert len(results) == 3


def test_retriever_prioritizes_canonical_memory():
    store = MemoryStore()

    store.add(
        make_memory(
            "virtual:identity",
            MemoryType.VIRTUAL_LIFE,
            "虚拟生活中小七自称小七",
            importance=1.0,
        )
    )

    store.add(
        make_memory(
            "interaction:identity",
            MemoryType.INTERACTION,
            "聊天中臭宝叫她小七",
            importance=1.0,
        )
    )

    store.add(
        make_memory(
            "canonical:identity",
            MemoryType.CANONICAL,
            "真实身份：小七",
            importance=1.0,
        )
    )

    retriever = MemoryRetriever(store)

    results = retriever.search("小七", limit=10)

    assert results[0].memory_type == MemoryType.CANONICAL
