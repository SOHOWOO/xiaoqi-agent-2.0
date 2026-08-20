from core.simulator import LifeSimulator
from core.time_engine import make_aware


def test_cross_date_simulation():
    from_time = make_aware(2026, 8, 20, 23, 0)
    to_time = make_aware(2026, 8, 21, 8, 30)

    result = LifeSimulator(
        seed=42
    ).simulate(from_time, to_time)

    assert "pre_sleep" in result.slots_seen
    assert "sleep" in result.slots_seen
    assert "morning_prep" in result.slots_seen
    assert "commute" in result.slots_seen

    assert result.life_state.current_slot_id == "commute"
