from datetime import timedelta

from core.life_loop import LifeLoop
from core.time_engine import make_aware


def _loop():
    start = make_aware(2026, 8, 22, 8, 0)
    return LifeLoop(start_time=start, seed=42)


def test_get_state_snapshot_shape():
    life = _loop()

    state = life.get_state()

    assert "time" in state
    assert "life" in state
    assert "energy" in state["life"]
    assert "emotion" in state
    assert "neurochemical" in state
    assert "relationship" in state
    assert "memory" in state


def test_get_state_is_readonly_snapshot():
    """快照改动不应影响内部状态。"""

    life = _loop()

    life.tick(timedelta(hours=2))
    snapshot = life.get_state()

    # 尝试修改快照
    snapshot["life"]["energy"] = 0.0
    snapshot["emotion"].as_dict()

    assert life.life_state.energy != 0.0
    assert life.emotion.state() == life.emotion.state()


def test_get_state_emotion_is_frozen():
    from dataclasses import FrozenInstanceError

    import pytest

    life = _loop()
    emotion = life.get_state()["emotion"]

    with pytest.raises(FrozenInstanceError):
        emotion.happy = 1.0


def test_get_state_advances():
    life = _loop()

    before = life.get_state()

    for _ in range(7 * 24 * 4):
        life.tick(timedelta(minutes=15))

    after = life.get_state()

    assert after["time"] > before["time"]
    assert after["memory"]["diary_count"] == 7
