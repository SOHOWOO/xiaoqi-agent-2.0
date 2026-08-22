from datetime import datetime, timedelta

from core.memory import (
    EpisodicMemory,
    MemoryConflictResolver,
    MemoryConsolidator,
    MemoryRecord,
    MemorySource,
    MemoryStore,
    MemoryType,
    RelationshipMemory,
    SemanticMemory,
)
from core.time_engine import DEFAULT_TZ


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(
        2026,
        8,
        22,
        hour,
        minute,
        tzinfo=DEFAULT_TZ,
    )


# ---------------------------------------------------------
# MemoryType 2.0 枚举
# ---------------------------------------------------------


def test_new_memory_types_exist():
    for name in (
        "EPISODIC",
        "SEMANTIC",
        "RELATIONSHIP",
        "DIARY",
    ):
        assert hasattr(MemoryType, name)


# ---------------------------------------------------------
# EpisodicMemory
# ---------------------------------------------------------


def test_episodic_records_and_timeline():
    store = MemoryStore()
    episodic = EpisodicMemory(store)

    episodic.record(
        content="用户完成了服务器部署",
        created_at=_dt(9, 0),
    )
    episodic.record(
        content="小七陪用户聊了很久",
        created_at=_dt(10, 0),
    )

    timeline = episodic.timeline()

    assert len(timeline) == 2
    assert timeline[0].memory_type == MemoryType.EPISODIC
    assert timeline[0].created_at < timeline[1].created_at


def test_episodic_recent_and_before():
    store = MemoryStore()
    episodic = EpisodicMemory(store)

    for minute in range(5):
        episodic.record(
            content=f"事件 {minute}",
            created_at=_dt(9, minute),
        )

    recent = episodic.recent(limit=2)
    assert len(recent) == 2
    assert recent[0].content == "事件 4"

    before = episodic.before(_dt(9, 3))
    assert len(before) == 3


# ---------------------------------------------------------
# SemanticMemory
# ---------------------------------------------------------


def test_semantic_add_fact_and_query():
    store = MemoryStore()
    semantic = SemanticMemory(store)

    semantic.add_fact(
        topic="技术",
        content="用户喜欢AI、喜欢技术",
        created_at=_dt(9, 0),
    )

    facts = semantic.facts(topic="技术")
    assert len(facts) == 1
    assert facts[0].memory_type == MemoryType.SEMANTIC

    found = semantic.find("技术")
    assert len(found) >= 1


# ---------------------------------------------------------
# RelationshipMemory
# ---------------------------------------------------------


def test_relationship_preferences():
    store = MemoryStore()
    relationship = RelationshipMemory(store)

    relationship.add_preference(
        condition="用户压力大时",
        behavior="喜欢安慰",
        created_at=_dt(9, 0),
    )

    preferences = relationship.preferences()

    assert len(preferences) == 1
    assert preferences[0].memory_type == MemoryType.RELATIONSHIP
    assert "压力大" in preferences[0].content
    assert "喜欢安慰" in preferences[0].content


# ---------------------------------------------------------
# MemoryConsolidator
# ---------------------------------------------------------


def test_consolidator_groups_similar_memories():
    store = MemoryStore()
    consolidator = MemoryConsolidator(
        store,
        threshold=0.3,
        min_group_size=3,
    )

    for i, content in enumerate(
        (
            "今天工作很累",
            "今天工作很累想休息",
            "今天工作很累压力大",
        )
    ):
        store.add(
            MemoryRecord(
                memory_id=f"interaction:{i}",
                memory_type=MemoryType.INTERACTION,
                content=content,
                created_at=_dt(9, i),
                source=MemorySource.CONVERSATION,
                importance=0.8,
                confidence=1.0,
            )
        )

    generated = consolidator.consolidate(
        created_at=_dt(12, 0),
    )

    assert len(generated) >= 1

    semantic = store.by_type(MemoryType.SEMANTIC)
    assert len(semantic) == 1
    assert "工作" in semantic[0].content
    assert semantic[0].source == (
        MemorySource.MEMORY_CONSOLIDATION
    )


def test_consolidator_ignores_dissimilar_memories():
    store = MemoryStore()
    consolidator = MemoryConsolidator(
        store,
        threshold=0.3,
        min_group_size=3,
    )

    for i, content in enumerate(
        (
            "今天天气很好",
            "用户喜欢吃火锅",
            "项目延期了",
        )
    ):
        store.add(
            MemoryRecord(
                memory_id=f"interaction:{i}",
                memory_type=MemoryType.INTERACTION,
                content=content,
                created_at=_dt(9, i),
                source=MemorySource.CONVERSATION,
                importance=0.8,
                confidence=1.0,
            )
        )

    generated = consolidator.consolidate(
        created_at=_dt(12, 0),
    )

    assert generated == []
    assert len(store.by_type(MemoryType.SEMANTIC)) == 0


def test_consolidator_rejects_bad_config():
    store = MemoryStore()

    with __import__("pytest").raises(ValueError):
        MemoryConsolidator(
            store,
            threshold=1.5,
        )

    with __import__("pytest").raises(ValueError):
        MemoryConsolidator(
            store,
            min_group_size=1,
        )


# ---------------------------------------------------------
# MemoryConflictResolver
# ---------------------------------------------------------


def _interaction(
    content: str,
    hour: int,
    memory_id: str,
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=MemoryType.INTERACTION,
        content=content,
        created_at=_dt(hour, 0),
        source=MemorySource.CONVERSATION,
        importance=0.8,
        confidence=1.0,
    )


def test_conflict_detects_preference_reversal():
    store = MemoryStore()
    old = _interaction("喜欢咖啡", 8, "i:1")
    store.add(old)

    resolver = MemoryConflictResolver(store)
    new = _interaction("戒咖啡", 9, "i:2")

    conflicts = resolver.detect(new)

    assert len(conflicts) == 1
    assert conflicts[0].memory_id == "i:1"


def test_conflict_not_detected_for_same_sentiment():
    store = MemoryStore()
    store.add(_interaction("喜欢咖啡", 8, "i:1"))

    resolver = MemoryConflictResolver(store)
    new = _interaction("喜欢茶", 9, "i:2")

    assert resolver.detect(new) == []


def test_conflict_resolve_creates_evolution_memory():
    store = MemoryStore()
    store.add(_interaction("喜欢咖啡", 8, "i:1"))

    new = _interaction("戒咖啡", 9, "i:2")
    store.add(new)

    resolver = MemoryConflictResolver(store)

    evolved = resolver.process(
        new,
        created_at=_dt(9, 30),
    )

    assert evolved is not None
    assert evolved.memory_type == MemoryType.SEMANTIC
    assert "咖啡" in evolved.content
    assert "过去喜欢" in evolved.content

    assert store.get("i:1") is not None
    assert store.get("i:2") is not None


def test_conflict_process_returns_none_when_no_conflict():
    store = MemoryStore()
    store.add(_interaction("喜欢咖啡", 8, "i:1"))

    resolver = MemoryConflictResolver(store)
    new = _interaction("喜欢茶", 9, "i:2")

    assert (
        resolver.process(new, created_at=_dt(9, 30))
        is None
    )


def test_conflict_resolver_works_with_sqlite(tmp_path):
    from core.memory import SQLiteMemoryStore

    db = tmp_path / "mem.db"
    store = SQLiteMemoryStore(db)

    store.add(_interaction("喜欢咖啡", 8, "i:1"))

    resolver = MemoryConflictResolver(store)
    new = _interaction("戒咖啡", 9, "i:2")

    evolved = resolver.process(
        new,
        created_at=_dt(9, 30),
    )

    assert evolved is not None

    loaded = store.by_type(MemoryType.SEMANTIC)
    assert len(loaded) == 1

    store.close()


# ---------------------------------------------------------
# 向后兼容：新类型不破坏原有检索
# ---------------------------------------------------------


def test_retriever_handles_new_types():
    store = MemoryStore()
    store.add(_interaction("喜欢咖啡", 8, "i:1"))

    semantic = SemanticMemory(store)
    semantic.add_fact(
        topic="咖啡",
        content="用户过去喜欢咖啡",
        created_at=_dt(9, 0),
    )

    from core.memory import MemoryRetriever

    retriever = MemoryRetriever(store)
    results = retriever.search("咖啡", limit=5)

    assert len(results) >= 1
    for memory in results:
        assert memory.memory_type in MemoryType
