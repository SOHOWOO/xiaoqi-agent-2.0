from datetime import timedelta

import pytest

from core.simulator import LifeSimulator
from core.time_engine import make_aware


def test_simulation_can_advance_continuously():
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

    assert result1.life_state.current_time == start + timedelta(hours=1)
    assert result2.life_state.current_time == start + timedelta(hours=2)


def test_simulation_time_never_moves_backward():
    start = make_aware(2026, 8, 20, 9, 0)

    sim = LifeSimulator(seed=42)

    sim.simulate(
        start,
        start + timedelta(hours=1),
    )

    with pytest.raises(ValueError):
        sim.simulate(
            start,
            start + timedelta(minutes=30),
        )
