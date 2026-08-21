from datetime import datetime, timedelta, timezone

import pytest

from core.memory import (
    MemoryRecord,
    MemorySource,
    MemoryType,
)
from core.memory.sqlite_store import SQLiteMemoryStore


def make_memory(
    memory_id: str,
    content: str,
    memory_type: MemoryType = MemoryType.INTERACTION,
    created_at: datetime | None = None,
    importance: float = 0.8,
    confidence: float = 0.9,
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=memory_type,
        content=content,
        created_at=(
            created_at
            if created_at is not None
            else datetime.now(timezone.utc)
        ),
        source=(
            MemorySource.USER_PROVIDED
            if memory_type == MemoryType.CANONICAL
            else MemorySource.CONVERSATION
        ),
        importance=importance,
        confidence=confidence,
    )


def test_add_and_get(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    memory = make_memory(
        "memory:1",
        "我喜欢吃草莓",
    )

    store.add(memory)

    assert store.get("memory:1") == memory

    store.close()


def test_all_returns_all_memories(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    first = make_memory("memory:1", "第一条")
    second = make_memory("memory:2", "第二条")

    store.add(first)
    store.add(second)

    assert store.all() == [first, second]

    store.close()


def test_duplicate_memory_id_raises(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    store.add(make_memory("memory:1", "第一条"))

    with pytest.raises(ValueError):
        store.add(make_memory("memory:1", "重复"))

    store.close()


def test_update_preserves_memory_id(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    original = make_memory(
        "memory:1",
        "我喜欢草莓",
    )
    store.add(original)

    updated = make_memory(
        "different-id",
        "我喜欢草莓和西瓜",
        importance=1.0,
        confidence=0.95,
    )

    result = store.update(
        "memory:1",
        updated,
    )

    assert result.memory_id == "memory:1"
    assert result.content == "我喜欢草莓和西瓜"
    assert result.importance == 1.0
    assert result.confidence == 0.95

    store.close()


def test_update_missing_memory_raises(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    with pytest.raises(KeyError):
        store.update(
            "missing",
            make_memory("memory:1", "内容"),
        )

    store.close()


def test_recent_returns_oldest_to_newest_within_limit(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    base = datetime(2026, 8, 21, tzinfo=timezone.utc)

    first = make_memory(
        "memory:1",
        "第一条",
        created_at=base,
    )
    second = make_memory(
        "memory:2",
        "第二条",
        created_at=base + timedelta(minutes=1),
    )
    third = make_memory(
        "memory:3",
        "第三条",
        created_at=base + timedelta(minutes=2),
    )

    store.add(first)
    store.add(second)
    store.add(third)

    assert store.recent(2) == [second, third]

    store.close()


def test_search_is_case_insensitive(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    store.add(
        make_memory(
            "memory:1",
            "I Like Strawberries",
        )
    )

    results = store.search("strawberries")

    assert len(results) == 1
    assert results[0].memory_id == "memory:1"

    store.close()


def test_by_type(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    canonical = make_memory(
        "canonical:1",
        "姓名：小七",
        memory_type=MemoryType.CANONICAL,
    )
    interaction = make_memory(
        "interaction:1",
        "今天买了草莓",
        memory_type=MemoryType.INTERACTION,
    )
    virtual = make_memory(
        "event:1",
        "小七今天吃了早餐",
        memory_type=MemoryType.VIRTUAL_LIFE,
    )

    store.add(canonical)
    store.add(interaction)
    store.add(virtual)

    assert store.by_type(MemoryType.CANONICAL) == [canonical]
    assert store.by_type(MemoryType.INTERACTION) == [interaction]
    assert store.by_type(MemoryType.VIRTUAL_LIFE) == [virtual]

    store.close()


def test_clear(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    store.add(make_memory("memory:1", "内容"))

    assert len(store) == 1

    store.clear()

    assert len(store) == 0
    assert store.all() == []

    store.close()


def test_memory_survives_store_reopen(tmp_path):
    db_path = tmp_path / "memory.db"

    memory = make_memory(
        "memory:1",
        "这条记忆必须保留下来",
    )

    first_store = SQLiteMemoryStore(db_path)
    first_store.add(memory)
    first_store.close()

    second_store = SQLiteMemoryStore(db_path)

    assert second_store.get("memory:1") == memory
    assert len(second_store) == 1

    second_store.close()


def test_all_memory_fields_survive_round_trip(tmp_path):
    db_path = tmp_path / "memory.db"

    created_at = datetime(
        2026,
        8,
        21,
        3,
        30,
        45,
        123456,
        tzinfo=timezone.utc,
    )

    memory = make_memory(
        "canonical:test",
        "这是完整字段测试",
        memory_type=MemoryType.CANONICAL,
        created_at=created_at,
        importance=0.73,
        confidence=0.91,
    )

    store = SQLiteMemoryStore(db_path)
    store.add(memory)
    store.close()

    reopened = SQLiteMemoryStore(db_path)
    restored = reopened.get("canonical:test")

    assert restored == memory
    assert restored is not None
    assert restored.memory_type == MemoryType.CANONICAL
    assert restored.source == MemorySource.USER_PROVIDED
    assert restored.importance == 0.73
    assert restored.confidence == 0.91

    reopened.close()
