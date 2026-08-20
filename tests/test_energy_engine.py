from core.energy_engine import update_energy
from core.schedule_engine import ScheduleEngine
from core.state import LifeState


def test_clinic_increases_fatigue():
    engine = ScheduleEngine()
    slot = next(
        s for s in engine.workday_slots
        if s.slot_id == "morning_clinic"
    )

    state = LifeState(fatigue=0.5, energy=0.7)

    update_energy(state, slot, 1.0)

    assert state.fatigue == 0.62
    assert state.energy == 0.58


def test_lunch_reduces_fatigue():
    engine = ScheduleEngine()
    slot = next(
        s for s in engine.workday_slots
        if s.slot_id == "lunch_break"
    )

    state = LifeState(fatigue=0.5, energy=0.7)

    update_energy(state, slot, 1.0)

    assert state.fatigue == 0.4
    assert abs(state.energy - 0.8) < 1e-9


def test_energy_is_clamped():
    engine = ScheduleEngine()
    slot = next(
        s for s in engine.workday_slots
        if s.slot_id == "sleep"
    )

    state = LifeState(fatigue=0.0, energy=1.0)

    update_energy(state, slot, 10.0)

    assert 0.0 <= state.fatigue <= 1.0
    assert 0.0 <= state.energy <= 1.0
