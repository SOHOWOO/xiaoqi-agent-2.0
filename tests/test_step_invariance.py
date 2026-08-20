from datetime import timedelta

from core.simulator import LifeSimulator
from core.time_engine import make_aware


CUSTOM_CONFIG = {
    "workday": {
        "timezone": "Asia/Singapore",
        "slots": [
            {
                "slot_id": "sleep",
                "name": "Sleep",
                "start": "00:00",
                "end": "07:30",
                "events": [],
            },
            {
                "slot_id": "morning_prep",
                "name": "Morning Prep",
                "start": "07:30",
                "end": "08:20",
                "events": [],
            },
            {
                "slot_id": "commute",
                "name": "Commute",
                "start": "08:20",
                "end": "09:00",
                "events": [],
            },
            {
                "slot_id": "morning_clinic",
                "name": "Morning Clinic",
                "start": "09:00",
                "end": "12:00",
                "events": [
                    {
                        "event_type": "clinic_minor_event",
                        "probability": 1.0,
                        "importance": 2,
                        "source": "simulation",
                    }
                ],
            },
            {
                "slot_id": "afternoon_clinic",
                "name": "Afternoon Clinic",
                "start": "13:30",
                "end": "18:00",
                "events": [],
            },
        ],
    }
}


def _event_signature(events):
    return {(e.event_id, e.event_type, e.slot_id) for e in events}


def test_step_size_does_not_change_event_results():
    from_time = make_aware(2026, 8, 20, 7, 40)
    to_time = make_aware(2026, 8, 20, 18, 30)

    whole_sim = LifeSimulator(
        seed=42,
        schedule_config=CUSTOM_CONFIG,
    )
    whole = whole_sim.simulate(from_time, to_time)

    whole_events = _event_signature(whole.events)
    whole_slots = set(whole.slots_seen)

    for step_minutes in (1, 5, 30):
        sim = LifeSimulator(
            seed=42,
            schedule_config=CUSTOM_CONFIG,
        )

        current = from_time
        events = []
        slots = []

        while current < to_time:
            nxt = min(
                current + timedelta(minutes=step_minutes),
                to_time,
            )

            result = sim.simulate(current, nxt)

            events.extend(result.events)
            slots.extend(result.slots_seen)

            current = nxt

        event_sig = _event_signature(events)
        slot_set = set(slots)

        assert event_sig == whole_events, (
            f"step={step_minutes} event mismatch"
        )

        assert slot_set == whole_slots, (
            f"step={step_minutes} slot mismatch"
        )

        assert len(
            [
                e
                for e in events
                if e.event_type == "clinic_minor_event"
            ]
        ) == 1


def test_same_occurrence_has_same_event_id_across_steps():
    from_time = make_aware(2026, 8, 20, 7, 40)
    to_time = make_aware(2026, 8, 20, 18, 30)

    whole = LifeSimulator(
        seed=7,
        schedule_config=CUSTOM_CONFIG,
    ).simulate(from_time, to_time)

    whole_ids = {e.event_id for e in whole.events}

    sim = LifeSimulator(
        seed=7,
        schedule_config=CUSTOM_CONFIG,
    )

    current = from_time
    event_ids = set()

    while current < to_time:
        nxt = min(
            current + timedelta(minutes=7),
            to_time,
        )

        result = sim.simulate(current, nxt)

        event_ids.update(
            e.event_id
            for e in result.events
        )

        current = nxt

    assert event_ids == whole_ids

    assert any(
        "2026-08-20:morning_clinic" in eid
        for eid in whole_ids
    )
