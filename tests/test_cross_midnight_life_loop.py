from datetime import timedelta

from core.simulator import LifeSimulator
from core.time_engine import make_aware


def test_cross_midnight_life_loop():
    start = make_aware(2026, 8, 20, 23, 0)
    end = make_aware(2026, 8, 21, 9, 0)

    sim = LifeSimulator(seed=42)

    result = sim.simulate(start, end)

    assert result.life_state.current_time == end

    assert "pre_sleep" in result.slots_seen
    assert "sleep" in result.slots_seen
    assert "morning_prep" in result.slots_seen
    assert "commute" in result.slots_seen


def test_cross_midnight_energy_continues():
    start = make_aware(2026, 8, 20, 23, 0)
    end = make_aware(2026, 8, 21, 9, 0)

    sim = LifeSimulator(seed=42)

    initial_fatigue = sim.life_state.fatigue
    initial_energy = sim.life_state.energy

    result = sim.simulate(start, end)

    assert 0.0 <= result.life_state.fatigue <= 1.0
    assert 0.0 <= result.life_state.energy <= 1.0

    assert (
        result.life_state.fatigue != initial_fatigue
        or result.life_state.energy != initial_energy
    )


def test_cross_midnight_matches_split_simulation():
    start = make_aware(2026, 8, 20, 23, 0)
    midnight = make_aware(2026, 8, 21, 0, 0)
    end = make_aware(2026, 8, 21, 9, 0)

    # 一次完成
    whole = LifeSimulator(seed=42)

    whole_result = whole.simulate(
        start,
        end,
    )

    # 跨午夜分两段
    split = LifeSimulator(seed=42)

    split.simulate(
        start,
        midnight,
    )

    split_result = split.simulate(
        midnight,
        end,
    )

    assert (
        split_result.life_state.current_time
        == whole_result.life_state.current_time
    )

    assert (
        split_result.life_state.fatigue
        == whole_result.life_state.fatigue
    )

    assert (
        split_result.life_state.energy
        == whole_result.life_state.energy
    )


def test_cross_midnight_clock_is_monotonic():
    start = make_aware(2026, 8, 20, 23, 30)
    midnight = make_aware(2026, 8, 21, 0, 30)
    end = make_aware(2026, 8, 21, 8, 30)

    sim = LifeSimulator(seed=42)

    result1 = sim.simulate(start, midnight)
    result2 = sim.simulate(midnight, end)

    assert result1.life_state.current_time == midnight
    assert result2.life_state.current_time == end

    assert (
        result2.life_state.current_time
        > result1.life_state.current_time
    )
