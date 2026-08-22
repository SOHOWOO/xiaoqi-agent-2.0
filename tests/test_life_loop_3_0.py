from datetime import timedelta

import pytest

from core.emotion import EmotionType
from core.life_loop import LifeLoop
from core.memory import MemoryType
from core.neurochemical import Neurotransmitter
from core.time_engine import make_aware


def _loop(seed: int = 42):
    start = make_aware(2026, 8, 20, 7, 40)
    return LifeLoop(start_time=start, seed=seed)


def test_tick_split_steps():
    """大步长 tick 应内部拆分为 MAX_TICK_STEP 子步。"""

    loop = _loop()

    steps = loop._split_steps(timedelta(hours=3))

    assert len(steps) == 12
    assert all(s <= loop.MAX_TICK_STEP for s in steps)
    assert sum(steps, timedelta(0)) == timedelta(hours=3)


def test_substep_matches_single_tick_state():
    """一次大步长 tick 与多次小步长 tick 的状态演化一致。

    - 神经化学 / 情绪使用时间绑定指数衰减，天然可分解
    - Simulator 具备步长不变性，生活事件一致
    - 时间推进一致
    """

    single = _loop()
    split = _loop()

    single.tick(timedelta(hours=6))

    for _ in range(6):
        split.tick(timedelta(hours=1))

    assert single.current_time == split.current_time

    s_state = single.neurochemical.state()
    b_state = split.neurochemical.state()

    for nt in Neurotransmitter:
        assert s_state.level(nt) == pytest.approx(
            b_state.level(nt),
            abs=1e-6,
        )

    s_emotion = single.emotion.state()
    b_emotion = split.emotion.state()

    for e in EmotionType:
        assert s_emotion.level(e) == pytest.approx(
            b_emotion.level(e),
            abs=1e-6,
        )


def test_substep_matches_single_tick_events():
    """分步积分不改变生活事件的产生（去重 + 步长不变）。"""

    single = _loop()
    split = _loop()

    single.tick(timedelta(days=2))
    split.tick(timedelta(days=2))

    s_events = single.memory_store.by_type(
        MemoryType.VIRTUAL_LIFE
    )
    b_events = split.memory_store.by_type(
        MemoryType.VIRTUAL_LIFE
    )

    assert len(s_events) == len(b_events)

    s_ids = {m.memory_id for m in s_events}
    b_ids = {m.memory_id for m in b_events}
    assert s_ids == b_ids


def test_tick_rejects_non_positive():
    loop = _loop()

    with pytest.raises(ValueError):
        loop.tick(timedelta(seconds=0))

    with pytest.raises(ValueError):
        loop.tick(timedelta(seconds=-1))
