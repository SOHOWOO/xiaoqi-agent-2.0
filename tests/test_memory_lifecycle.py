from datetime import datetime, timedelta

import pytest

from core.memory import (
    MemoryLifecycle,
    MemoryRecord,
    MemorySource,
    MemoryStore,
    MemoryType,
)
from core.time_engine import DEFAULT_TZ


def _dt(day: int, hour: int = 12) -> datetime:
    return datetime(2026, 8, day, hour, 0, tzinfo=DEFAULT_TZ)


def _interaction(
    content: str,
    created_at: datetime,
    memory_id: str,
    importance: float = 0.8,
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=MemoryType.INTERACTION,
        content=content,
        created_at=created_at,
        source=MemorySource.CONVERSATION,
        importance=importance,
        confidence=1.0,
    )


def test_consolidate_runs_daily_interval():
    store = MemoryStore()
    lifecycle = MemoryLifecycle(
        store,
        consolidate_interval=timedelta(days=1),
    )

    for i, content in enumerate(
        (
            "今天工作很累",
            "今天工作很累想休息",
            "今天工作很累压力大",
        )
    ):
        store.add(
            _interaction(content, _dt(21, 9 + i), f"i:{i}")
        )

    first = lifecycle.run(_dt(22))
    assert len(first) == 1

    same_day = lifecycle.run(_dt(22, 20))
    assert same_day == []

    next_day = lifecycle.run(_dt(23))
    assert len(store.by_type(MemoryType.SEMANTIC)) >= 1


def test_prune_lowers_stale_low_value_memories():
    store = MemoryStore()

    stale = _interaction(
        "很久以前的小事",
        _dt(1),
        "i:stale",
        importance=0.8,
    )
    fresh = _interaction(
        "最近的重要事情",
        _dt(20),
        "i:fresh",
        importance=0.9,
    )
    store.add(stale)
    store.add(fresh)

    lifecycle = MemoryLifecycle(
        store,
        forget_after=timedelta(days=15),
        min_keep_importance=0.3,
    )

    lifecycle._prune(_dt(22))

    stale_now = store.get("i:stale")
    fresh_now = store.get("i:fresh")

    assert stale_now is not None
    assert stale_now.importance < 0.8
    assert fresh_now.importance == 0.9


def test_prune_keeps_canonical_memories():
    store = MemoryStore()

    canonical = MemoryRecord(
        memory_id="canonical:1",
        memory_type=MemoryType.CANONICAL,
        content="用户喜欢AI",
        created_at=_dt(1),
        source=MemorySource.USER_PROVIDED,
        importance=1.0,
        confidence=1.0,
    )
    store.add(canonical)

    lifecycle = MemoryLifecycle(
        store,
        forget_after=timedelta(days=5),
        min_keep_importance=0.3,
    )

    pruned = lifecycle._prune(_dt(22))

    assert pruned == 0
    assert store.get("canonical:1").importance == 1.0


def test_lifecycle_rejects_bad_config():
    store = MemoryStore()

    with pytest.raises(ValueError):
        MemoryLifecycle(
            store,
            consolidate_interval=timedelta(0),
        )

    with pytest.raises(ValueError):
        MemoryLifecycle(
            store,
            min_keep_importance=1.5,
        )
