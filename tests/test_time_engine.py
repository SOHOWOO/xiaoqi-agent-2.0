from datetime import date, datetime, timezone

import pytest

from core.time_engine import DEFAULT_TZ, ensure_aware, iter_days, make_aware


def test_ensure_aware_rejects_naive():
    with pytest.raises(ValueError):
        ensure_aware(datetime(2026, 8, 20, 9, 0))


def test_ensure_aware_converts_utc_to_singapore():
    utc = datetime(2026, 8, 20, 1, 0, tzinfo=timezone.utc)
    local = ensure_aware(utc, DEFAULT_TZ)

    assert local.hour == 9
    assert local.tzinfo == DEFAULT_TZ


def test_iter_days_cross_midnight():
    from_time = make_aware(2026, 8, 20, 23, 0)
    to_time = make_aware(2026, 8, 21, 8, 30)

    days = list(iter_days(from_time, to_time))

    assert len(days) == 2
    assert days[0][0] == date(2026, 8, 20)
    assert days[1][0] == date(2026, 8, 21)


def test_iter_days_excludes_to_midnight():
    from_time = make_aware(2026, 8, 20, 23, 0)
    to_time = make_aware(2026, 8, 21, 0, 0)

    days = list(iter_days(from_time, to_time))

    assert len(days) == 1
    assert days[0][0] == date(2026, 8, 20)
