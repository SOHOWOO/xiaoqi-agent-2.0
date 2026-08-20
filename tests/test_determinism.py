from core.simulator import LifeSimulator
from core.time_engine import make_aware


def test_same_seed_same_result():
    from_time = make_aware(2026, 8, 20, 7, 40)
    to_time = make_aware(2026, 8, 20, 18, 30)

    s1 = LifeSimulator(seed=12345).simulate(from_time, to_time)
    s2 = LifeSimulator(seed=12345).simulate(from_time, to_time)

    assert [(e.event_id, e.event_type, e.slot_id) for e in s1.events] == \
           [(e.event_id, e.event_type, e.slot_id) for e in s2.events]

    assert s1.slots_seen == s2.slots_seen
    assert s1.life_state.current_slot_id == s2.life_state.current_slot_id
