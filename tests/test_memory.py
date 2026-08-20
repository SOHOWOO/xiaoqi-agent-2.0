from core.memory import MemoryStore
from core.time_engine import make_aware


def test_memory_store_add():
    store = MemoryStore()

    created_at = make_aware(2026, 8, 20, 14, 0)

    memory = store.add(
        content="用户今天有点累",
        created_at=created_at,
        source="user",
    )

    assert memory.memory_id == "memory-1"
    assert memory.content == "用户今天有点累"
    assert memory.source == "user"
    assert len(store) == 1


def test_memory_store_recent():
    store = MemoryStore()

    created_at = make_aware(2026, 8, 20, 14, 0)

    store.add("第一条", created_at, "user")
    store.add("第二条", created_at, "user")
    store.add("第三条", created_at, "assistant")

    recent = store.recent(2)

    assert [memory.content for memory in recent] == [
        "第二条",
        "第三条",
    ]


def test_memory_store_search():
    store = MemoryStore()

    created_at = make_aware(2026, 8, 20, 14, 0)

    store.add("用户喜欢喝咖啡", created_at, "user")
    store.add("用户今天去上班", created_at, "user")

    results = store.search("咖啡")

    assert len(results) == 1
    assert results[0].content == "用户喜欢喝咖啡"


def test_memory_store_rejects_empty_content():
    store = MemoryStore()

    created_at = make_aware(2026, 8, 20, 14, 0)

    try:
        store.add("", created_at, "user")
        assert False
    except ValueError:
        pass


def test_memory_store_clear():
    store = MemoryStore()

    created_at = make_aware(2026, 8, 20, 14, 0)

    store.add("测试记忆", created_at, "user")

    assert len(store) == 1

    store.clear()

    assert len(store) == 0
