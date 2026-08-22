from datetime import timedelta

from core.life_loop import LifeLoop
from core.time_engine import make_aware


def _loop(hour: int = 8):
    start = make_aware(2026, 8, 22, hour, 0)
    return LifeLoop(start_time=start, seed=42)


def test_absence_raises_loneliness_over_week():
    """7 天失联后，孤独情绪应明显上升（PROLONGED_ABSENCE 生效）。"""

    life = _loop()

    first = life.emotion.state().lonely

    for _ in range(7 * 24 * 4):
        life.tick(timedelta(minutes=15))

    last = life.emotion.state().lonely

    assert last > first
    assert last > 0.6


def test_absence_lowers_oxytocin():
    """失联后催产素应低于启动基线（依恋缺失）。"""

    life = _loop()

    baseline_oxytocin = life.neurochemical.state().oxytocin

    for _ in range(4 * 24 * 4):
        life.tick(timedelta(minutes=15))

    after = life.neurochemical.state().oxytocin

    assert after < baseline_oxytocin


def test_no_absence_before_threshold():
    """24 小时内不失联，不触发 PROLONGED_ABSENCE。"""

    life = _loop()

    baseline_oxytocin = life.neurochemical.state().oxytocin

    for _ in range(23 * 4):
        life.tick(timedelta(minutes=15))

    assert (
        life.neurochemical.state().oxytocin
        == baseline_oxytocin
    )


def test_absence_triggers_proactive_contact():
    """失联应通过动机链路产生主动联系（1~5 次较自然）。"""

    life = _loop()

    total = 0

    for _ in range(7 * 24 * 4):
        life.tick(timedelta(minutes=15))
        total += len(
            life.get_pending_proactive_messages()
        )

    assert 1 <= total <= 5


def test_interaction_resets_absence():
    """用户互动应重置失联状态（之后不再受失联影响）。"""

    life = _loop()

    for _ in range(3 * 24 * 4):
        life.tick(timedelta(minutes=15))

    lonely_before = life.emotion.state().lonely

    # 模拟一次用户互动
    life.simulator.interaction_state.last_user_interaction_at = (
        life.current_time
    )

    for _ in range(24 * 4):
        life.tick(timedelta(minutes=15))

    lonely_after = life.emotion.state().lonely

    assert lonely_after < lonely_before
