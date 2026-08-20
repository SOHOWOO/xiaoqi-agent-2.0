from datetime import date, datetime, time

import pytest

from core.schedule_engine import NEEDS_REVIEW, ScheduleEngine
from core.time_engine import DEFAULT_TZ, make_aware


@pytest.fixture
def engine():
    return ScheduleEngine()


def test_workday_slots(engine):
    assert engine.get_slot(make_aware(2026, 8, 20, 9, 0)).slot_id == "morning_clinic"
    assert engine.get_slot(make_aware(2026, 8, 20, 12, 0)).slot_id == "lunch_break"
    assert engine.get_slot(make_aware(2026, 8, 20, 13, 30)).slot_id == "afternoon_clinic"
    assert engine.get_slot(make_aware(2026, 8, 20, 18, 0)).slot_id == "commute_grocery"
    assert engine.get_slot(make_aware(2026, 8, 20, 19, 0)).slot_id == "cooking_dinner"
    assert engine.get_slot(make_aware(2026, 8, 20, 20, 30)).slot_id == "home_leisure"
    assert engine.get_slot(make_aware(2026, 8, 20, 22, 30)).slot_id == "pre_sleep"


def test_workday_morning_boundaries(engine):
    assert engine.get_slot(make_aware(2026, 8, 20, 7, 30)).slot_id == "morning_prep"
    assert engine.get_slot(make_aware(2026, 8, 20, 8, 20)).slot_id == "commute"
    assert engine.get_slot(make_aware(2026, 8, 20, 0, 0)).slot_id == "sleep"
    assert engine.get_slot(make_aware(2026, 8, 20, 7, 29)).slot_id == "sleep"


def test_midnight_boundary(engine):
    assert engine.get_slot(make_aware(2026, 8, 20, 23, 59)).slot_id == "pre_sleep"
    assert engine.get_slot(make_aware(2026, 8, 21, 0, 0)).slot_id == "sleep"


def test_weekend_is_needs_review(engine):
    saturday = make_aware(2026, 8, 22, 12, 0)
    sunday = make_aware(2026, 8, 23, 12, 0)

    assert engine.get_slot(saturday) == NEEDS_REVIEW
    assert engine.get_slot(sunday) == NEEDS_REVIEW
    assert engine.weekend_schedule(saturday) == NEEDS_REVIEW


def test_24_00_end_is_next_midnight(engine):
    slots = engine.slots_for_date(date(2026, 8, 20))
    pre_sleep = next(s for s in slots if s.slot.slot_id == "pre_sleep")

    assert pre_sleep.end.date() == date(2026, 8, 21)
    assert pre_sleep.end.hour == 0
    assert pre_sleep.end.minute == 0

    late = datetime.combine(
        date(2026, 8, 20),
        time(23, 59, 59, 999999),
        tzinfo=DEFAULT_TZ,
    )
    assert engine.get_slot(late).slot_id == "pre_sleep"

    midnight = make_aware(2026, 8, 21, 0, 0)
    assert engine.get_slot(midnight).slot_id == "sleep"
