from datetime import timedelta

from core.simulator import LifeSimulator
from core.time_engine import make_aware


def test_continuous_simulation_matches_single_simulation():
    from_time = make_aware(2026, 8, 20, 9, 0)
    to_time = make_aware(2026, 8, 20, 18, 0)

    # 一次性模拟
    whole_sim = LifeSimulator(seed=42)
    whole = whole_sim.simulate(from_time, to_time)

    # 分段模拟
    step_sim = LifeSimulator(seed=42)
    current = from_time

    while current < to_time:
        nxt = min(current + timedelta(minutes=30), to_time)
        step_sim.simulate(current, nxt)
        current = nxt

    assert abs(
        step_sim.life_state.fatigue - whole.life_state.fatigue
    ) < 1e-9

    assert abs(
        step_sim.life_state.energy - whole.life_state.energy
    ) < 1e-9

    assert step_sim.life_state.current_slot_id == whole.life_state.current_slot_id
    assert step_sim.life_state.current_activity == whole.life_state.current_activity
