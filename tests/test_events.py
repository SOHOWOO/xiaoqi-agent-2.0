from core.events import MemoryTier, MicroEventEngine, SimulationEvent
from core.time_engine import make_aware


def test_evaluate_is_deterministic():
    e1 = MicroEventEngine(seed=12345)
    e2 = MicroEventEngine(seed=12345)

    assert e1.evaluate(
        "2026-08-20:morning_clinic",
        "clinic_minor_event",
        0.25,
    ) == e2.evaluate(
        "2026-08-20:morning_clinic",
        "clinic_minor_event",
        0.25,
    )

    assert e1.evaluate(
        "2026-08-20:morning_clinic",
        "clinic_minor_event",
        0.25,
    ) == e1.evaluate(
        "2026-08-20:morning_clinic",
        "clinic_minor_event",
        0.25,
    )


def test_evaluate_zero_and_one():
    e = MicroEventEngine(seed=1)

    assert all(
        e.evaluate("occ", "never", 0.0) is False
        for _ in range(5)
    )

    assert all(
        e.evaluate("occ", "always", 1.0) is True
        for _ in range(5)
    )


def test_simulation_event_default_tier_is_3():
    ev = SimulationEvent(
        event_id="x",
        event_type="t",
        slot_id="s",
        start_time=make_aware(2026, 8, 20, 9, 0),
        end_time=make_aware(2026, 8, 20, 9, 30),
        importance=1,
        source="simulation",
    )

    assert ev.tier == MemoryTier.TIER_3_SIMULATED_LIFE
