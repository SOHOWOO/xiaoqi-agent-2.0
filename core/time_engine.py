from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterator, Tuple
from zoneinfo import ZoneInfo

DEFAULT_TZ_NAME = "Asia/Singapore"
DEFAULT_TZ = ZoneInfo(DEFAULT_TZ_NAME)


def ensure_aware(dt: datetime, tz=DEFAULT_TZ) -> datetime:
    """Return a timezone-aware datetime in the target timezone."""
    if dt.tzinfo is None:
        raise ValueError("naive datetime is not allowed; pass a timezone-aware datetime")
    if dt.tzinfo != tz:
        return dt.astimezone(tz)
    return dt


def make_aware(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz=DEFAULT_TZ,
) -> datetime:
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tz)


def iter_days(
    from_time: datetime, to_time: datetime
) -> Iterator[Tuple[date, datetime, datetime]]:
    """Yield (day, day_start, day_end) for each calendar day intersecting [from, to)."""
    if from_time >= to_time:
        return

    day = from_time.date()
    day_start = datetime.combine(day, time(0, 0), tzinfo=from_time.tzinfo)

    while day_start < to_time:
        day_end = day_start + timedelta(days=1)
        if day_end > from_time:
            yield day, day_start, day_end
        day_start = day_end
        day = day_start.date()
