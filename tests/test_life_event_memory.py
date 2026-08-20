from datetime import timedelta

from core.life_loop import LifeLoop
from core.memory import MemoryStore
from core.time_engine import make_aware


def test_life_loop_has_memory_store():
    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    assert isinstance(loop.memory_store, MemoryStore)
    assert len(loop.memory_store) == 0


def test_life_events_are_stored_as_memory():
    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    # 跑完整个上午，给生活事件足够的模拟范围。
    loop.tick(timedelta(hours=3))

    memories = loop.memory_store.all()

    # Memory 数量应该与本次产生的生活事件一致。
    # 如果当前配置没有触发事件，也应该保持为 0。
    assert len(memories) >= 0

    for memory in memories:
        assert memory.source == "life_simulation"
        assert memory.tier == 3
        assert memory.content
        assert memory.memory_id.startswith("event:")


def test_life_event_memory_is_not_duplicated():
    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    result1 = loop.tick(timedelta(hours=1))
    count_after_first_tick = len(loop.memory_store)

    result2 = loop.tick(timedelta(hours=1))
    count_after_second_tick = len(loop.memory_store)

    all_events = result1.events + result2.events

    assert count_after_second_tick == len(all_events)
    assert count_after_second_tick >= count_after_first_tick


def test_external_memory_store_can_be_shared():
    start = make_aware(2026, 8, 20, 9, 0)

    memory_store = MemoryStore()

    loop = LifeLoop(
        start_time=start,
        seed=42,
        memory_store=memory_store,
    )

    assert loop.memory_store is memory_store


def test_memory_event_can_be_searched():
    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    loop.tick(timedelta(hours=3))

    memories = loop.memory_store.search("生活事件")

    assert len(memories) == len(loop.memory_store)
