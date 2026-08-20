from core.status import build_life_status, format_life_status
from core.state import LifeState
from core.time_engine import make_aware


def test_build_life_status():
    state = LifeState(
        current_time=make_aware(2026, 8, 20, 10, 30),
        current_slot_id="morning_clinic",
        current_activity="上午门诊",
        fatigue=0.625,
        energy=0.58,
    )

    status = build_life_status(state)

    assert status.slot_id == "morning_clinic"
    assert status.activity == "上午门诊"
    assert status.fatigue == 0.625
    assert status.energy == 0.58


def test_status_condition():
    state = LifeState(
        fatigue=0.9,
        energy=0.3,
    )

    status = build_life_status(state)

    assert status.condition == "疲劳"


def test_format_life_status():
    state = LifeState(
        current_time=make_aware(2026, 8, 20, 10, 30),
        current_slot_id="morning_clinic",
        current_activity="上午门诊",
        fatigue=0.625,
        energy=0.58,
    )

    status = build_life_status(state)
    text = format_life_status(status)

    assert "上午门诊" in text
    assert "疲劳度：0.62" in text
    assert "精力：0.58" in text
    assert "状态：正常" in text
