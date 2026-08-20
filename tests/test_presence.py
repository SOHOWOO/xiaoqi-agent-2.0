from core.presence import Presence, build_presence
from core.schedule_engine import ScheduleEngine
from core.state import LifeState


def test_build_presence_from_life_state():
    engine = ScheduleEngine()

    slot = next(
        s for s in engine.workday_slots
        if s.slot_id == "morning_clinic"
    )

    state = LifeState(
        fatigue=0.68,
        energy=0.52,
    )

    presence = build_presence(slot, state)

    assert presence.slot_id == "morning_clinic"
    assert presence.activity == "上午门诊"
    assert presence.fatigue == 0.68
    assert presence.energy == 0.52


def test_presence_describe():
    presence = Presence(
        slot_id="morning_clinic",
        activity="上午门诊",
        fatigue=0.68,
        energy=0.52,
    )

    assert presence.describe() == (
        "小七现在正在「上午门诊」，疲劳度 0.68，精力 0.52。"
    )


def test_presence_is_independent_from_life_state():
    engine = ScheduleEngine()

    slot = next(
        s for s in engine.workday_slots
        if s.slot_id == "lunch_break"
    )

    state = LifeState(
        fatigue=0.5,
        energy=0.7,
    )

    presence = build_presence(slot, state)

    state.fatigue = 0.9
    state.energy = 0.2

    assert presence.fatigue == 0.5
    assert presence.energy == 0.7
