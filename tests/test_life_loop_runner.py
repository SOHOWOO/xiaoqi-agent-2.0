from datetime import timedelta

import pytest

from core.life_loop import LifeLoop
from core.time_engine import make_aware


def test_life_loop_advances_time():
    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    result = loop.tick(timedelta(minutes=30))

    assert result.life_state.current_time == make_aware(
        2026, 8, 20, 9, 30
    )

    assert loop.current_time == make_aware(
        2026, 8, 20, 9, 30
    )


def test_life_loop_can_tick_repeatedly():
    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    loop.tick(timedelta(minutes=30))
    loop.tick(timedelta(minutes=30))
    loop.tick(timedelta(hours=1))

    assert loop.current_time == make_aware(
        2026, 8, 20, 11, 0
    )


def test_life_loop_rejects_non_positive_tick():
    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    with pytest.raises(ValueError):
        loop.tick(timedelta(0))

    with pytest.raises(ValueError):
        loop.tick(timedelta(minutes=-5))
