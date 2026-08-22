from datetime import datetime, timedelta

import pytest

from core.bus import BusEvent, EventBus, EventType
from core.life_loop import LifeLoop
from core.time_engine import make_aware


def test_bus_publish_subscribe():
    bus = EventBus()
    received = []

    bus.subscribe("state_update", lambda data: received.append(data))

    bus.publish("state_update", {"energy": 0.7})

    assert received == [{"energy": 0.7}]


def test_bus_unsubscribe():
    bus = EventBus()
    received = []

    unsubscribe = bus.subscribe(
        "emotion_change", lambda data: received.append(data)
    )

    unsubscribe()
    bus.publish("emotion_change", {})

    assert received == []
    assert bus.subscriber_count("emotion_change") == 0


def test_bus_subscriber_exception_does_not_break():
    bus = EventBus()

    def bad(_):
        raise RuntimeError("boom")

    received = []

    bus.subscribe("state_update", bad)
    bus.subscribe("state_update", lambda data: received.append(data))

    bus.publish("state_update", {"x": 1})

    assert received == [{"x": 1}]


def test_life_loop_publishes_state_update():
    start = make_aware(2026, 8, 20, 7, 40)
    bus = EventBus()
    states = []

    loop = LifeLoop(start_time=start, seed=42, event_bus=bus)
    bus.subscribe("state_update", lambda data: states.append(data))

    loop.tick(timedelta(hours=2))

    assert len(states) >= 1
    assert "emotion" in states[0]
    assert "dominant_emotion" in states[0]
    assert "simulated_time" in states[0]


def test_life_loop_publishes_emotion_change_on_transition():
    start = make_aware(2026, 8, 20, 7, 40)
    bus = EventBus()
    changes = []

    loop = LifeLoop(start_time=start, seed=42, event_bus=bus)
    bus.subscribe("emotion_change", lambda data: changes.append(data))

    # 第一次 tick 只记录基线，不触发 emotion_change（无 from）
    loop.tick(timedelta(hours=1))
    assert changes == []

    # 施加情绪事件后再次 tick，应发布 transition
    from core.emotion import EmotionEvent, EmotionType

    loop.emotion.apply_event(EmotionEvent(EmotionType.EXCITED, 1.0))
    loop.tick(timedelta(hours=1))

    assert any(c["to"] == "excited" for c in changes)


def test_life_loop_publishes_proactive_triggered():
    start = make_aware(2026, 8, 20, 7, 40)
    bus = EventBus()
    triggered = []

    loop = LifeLoop(start_time=start, seed=42, event_bus=bus)
    bus.subscribe("proactive_triggered", lambda data: triggered.append(data))

    from core.emotion import EmotionEvent, EmotionType

    loop.emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))
    loop.tick(timedelta(hours=1))

    assert len(triggered) >= 1
    assert "content" in triggered[0]


def test_life_loop_publishes_diary_written_on_day_change():
    start = make_aware(2026, 8, 20, 23, 50)
    bus = EventBus()
    diaries = []

    loop = LifeLoop(start_time=start, seed=42, event_bus=bus)
    bus.subscribe("diary_written", lambda data: diaries.append(data))

    loop.tick(timedelta(hours=2))

    assert len(diaries) >= 1
    assert "date" in diaries[0]


def test_life_loop_publishes_memory_consolidated():
    from core.memory import MemoryLifecycle, MemoryRecord, MemorySource, MemoryType

    start = make_aware(2026, 8, 20, 7, 40)
    bus = EventBus()
    consolidated = []

    loop = LifeLoop(start_time=start, seed=42, event_bus=bus)
    loop.memory_lifecycle = MemoryLifecycle(loop.memory_store)
    bus.subscribe("memory_consolidated", lambda data: consolidated.append(data))

    now = loop.current_time
    for i, content in enumerate(
        ("今天工作很累", "今天工作很累想休息", "今天工作很累压力大")
    ):
        loop.memory_store.add(
            MemoryRecord(
                memory_id=f"i:{i}",
                memory_type=MemoryType.INTERACTION,
                content=content,
                created_at=now - timedelta(days=1),
                source=MemorySource.CONVERSATION,
                importance=0.8,
                confidence=1.0,
            )
        )

    loop.tick(timedelta(hours=1))

    assert len(consolidated) >= 1
    assert consolidated[0]["count"] >= 1


def test_bus_event_serialization():
    event = BusEvent(
        type=EventType.STATE_UPDATE,
        data={"energy": 0.7},
        timestamp=datetime(2026, 8, 22, 12, 0),
    )

    payload = event.to_dict()

    assert payload["type"] == "state_update"
    assert payload["data"]["energy"] == 0.7
    assert "timestamp" in payload
