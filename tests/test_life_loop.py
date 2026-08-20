from datetime import timedelta

from core.simulator import LifeSimulator
from core.time_engine import make_aware


def test_life_loop_continuous_time():
    start = make_aware(2026, 8, 20, 9, 0)

    sim = LifeSimulator(seed=42)

    result1 = sim.simulate(
        start,
        start + timedelta(minutes=30),
    )

    result2 = sim.simulate(
        start + timedelta(minutes=30),
        start + timedelta(hours=1),
    )

    assert result1.life_state.current_time == start + timedelta(minutes=30)
    assert result2.life_state.current_time == start + timedelta(hours=1)

    assert sim.life_state.current_time == start + timedelta(hours=1)


def test_life_loop_updates_energy_and_fatigue():
    start = make_aware(2026, 8, 20, 9, 0)

    sim = LifeSimulator(seed=42)

    initial_fatigue = sim.life_state.fatigue
    initial_energy = sim.life_state.energy

    result = sim.simulate(
        start,
        start + timedelta(hours=1),
    )

    assert result.life_state.fatigue != initial_fatigue
    assert result.life_state.energy != initial_energy

    assert 0.0 <= result.life_state.fatigue <= 1.0
    assert 0.0 <= result.life_state.energy <= 1.0


def test_life_loop_tick_size_invariance_for_energy():
    start = make_aware(2026, 8, 20, 9, 0)
    end = make_aware(2026, 8, 20, 12, 0)

    # 一次性模拟
    whole = LifeSimulator(seed=42)

    whole_result = whole.simulate(
        start,
        end,
    )

    # 每 15 分钟模拟一次
    stepped = LifeSimulator(seed=42)

    current = start

    while current < end:
        next_time = min(
            current + timedelta(minutes=15),
            end,
        )

        stepped.simulate(
            current,
            next_time,
        )

        current = next_time

    assert stepped.life_state.current_time == end

    assert (
        stepped.life_state.fatigue
        == whole_result.life_state.fatigue
    )

    assert (
        stepped.life_state.energy
        == whole_result.life_state.energy
    )


def test_life_loop_tick_size_invariance_for_events():
    start = make_aware(2026, 8, 20, 7, 40)
    end = make_aware(2026, 8, 20, 18, 30)

    # 一次模拟
    whole = LifeSimulator(seed=42)

    whole_result = whole.simulate(
        start,
        end,
    )

    # 分段模拟
    stepped = LifeSimulator(seed=42)

    current = start
    stepped_events = []

    while current < end:
        next_time = min(
            current + timedelta(minutes=15),
            end,
        )

        result = stepped.simulate(
            current,
            next_time,
        )

        stepped_events.extend(result.events)

        current = next_time

    whole_event_ids = {
        event.event_id
        for event in whole_result.events
    }

    stepped_event_ids = {
        event.event_id
        for event in stepped_events
    }

    assert stepped_event_ids == whole_event_ids


def test_life_loop_state_snapshot_remains_independent():
    start = make_aware(2026, 8, 20, 9, 0)

    sim = LifeSimulator(seed=42)

    result1 = sim.simulate(
        start,
        start + timedelta(hours=1),
    )

    result2 = sim.simulate(
        start + timedelta(hours=1),
        start + timedelta(hours=2),
    )

    assert (
        result1.life_state.current_time
        == start + timedelta(hours=1)
    )

    assert (
        result2.life_state.current_time
        == start + timedelta(hours=2)
    )

    assert (
        result1.life_state.current_time
        != result2.life_state.current_time
    )
def test_life_loop_stores_virtual_life_events_in_memory():
    from core.life_loop import LifeLoop
    from core.memory import (
        MemorySource,
        MemoryType,
    )

    start = make_aware(2026, 8, 20, 7, 40)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    result = loop.tick(
        timedelta(hours=11),
    )

    memories = loop.memory_store.all()

    assert len(memories) == len(result.events)

    for memory in memories:
        assert memory.memory_type == MemoryType.VIRTUAL_LIFE
        assert memory.source == MemorySource.LIFE_SIMULATION
        assert memory.memory_id.startswith("event:")


def test_life_loop_does_not_duplicate_memory_events():
    from core.life_loop import LifeLoop

    start = make_aware(2026, 8, 20, 7, 40)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    result = loop.tick(
        timedelta(hours=11),
    )

    first_count = len(loop.memory_store)

    loop._store_events(result)

    second_count = len(loop.memory_store)

    assert first_count == len(result.events)
    assert second_count == first_count
