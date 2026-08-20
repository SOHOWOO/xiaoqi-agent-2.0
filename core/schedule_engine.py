from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, time as dt_time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .time_engine import DEFAULT_TZ, ensure_aware

NEEDS_REVIEW = "NEEDS_REVIEW"

DEFAULT_SCHEDULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "source-material"
    / "workday_schedule.json"
)


@dataclass(frozen=True)
class EventRule:
    event_type: str
    probability: float
    importance: int = 1
    source: str = "simulation"


@dataclass
class LifeSlot:
    slot_id: str
    name: str
    start_seconds: int
    end_seconds: int
    events: List[EventRule] = field(default_factory=list)
    day_type: str = "workday"


@dataclass(frozen=True)
class SlotOccurrence:
    slot: LifeSlot
    date: date
    start: datetime
    end: datetime

    @property
    def occurrence_id(self) -> str:
        return f"{self.date.isoformat()}:{self.slot.slot_id}"


def parse_time(value: str) -> int:
    """Parse HH:MM or HH:MM:SS to seconds since midnight."""
    parts = value.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    return hour * 3600 + minute * 60


def load_schedule_config(path: Optional[Path] = None) -> Dict[str, Any]:
    config_path = Path(path) if path else DEFAULT_SCHEDULE_PATH
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


class ScheduleEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config is not None else load_schedule_config()
        self.workday_slots = self._parse_workday_slots(self.config)

    def _parse_workday_slots(self, config: Dict[str, Any]) -> List[LifeSlot]:
        slots_data = config.get("workday", {}).get("slots", [])
        slots: List[LifeSlot] = []

        for item in slots_data:
            events = [
                EventRule(
                    event_type=rule["event_type"],
                    probability=float(rule["probability"]),
                    importance=int(rule.get("importance", 1)),
                    source=rule.get("source", "simulation"),
                )
                for rule in item.get("events", [])
            ]

            slots.append(
                LifeSlot(
                    slot_id=item["slot_id"],
                    name=item["name"],
                    start_seconds=parse_time(item["start"]),
                    end_seconds=parse_time(item["end"]),
                    events=events,
                    day_type=item.get("day_type", "workday"),
                )
            )

        return slots

    def weekend_schedule(self, dt: Optional[datetime] = None) -> str:
        """周末规则未定，必须返回 NEEDS_REVIEW，禁止猜测。"""
        return NEEDS_REVIEW

    def get_slot(self, dt: datetime) -> Union[LifeSlot, str]:
        dt = ensure_aware(dt)

        if dt.weekday() >= 5:
            return self.weekend_schedule(dt)

        midnight = datetime.combine(
            dt.date(),
            dt_time(0, 0),
            tzinfo=dt.tzinfo,
        )

        seconds = (dt - midnight).total_seconds()

        for slot in self.workday_slots:
            if slot.start_seconds <= seconds < slot.end_seconds:
                return slot

        return None

    def slots_for_date(self, day: date) -> Union[List[SlotOccurrence], str]:
        if day.weekday() >= 5:
            return NEEDS_REVIEW

        base = datetime.combine(
            day,
            dt_time(0, 0),
            tzinfo=DEFAULT_TZ,
        )

        occurrences: List[SlotOccurrence] = []

        for slot in self.workday_slots:
            start_dt = base + timedelta(seconds=slot.start_seconds)
            end_dt = base + timedelta(seconds=slot.end_seconds)

            occurrences.append(
                SlotOccurrence(
                    slot=slot,
                    date=day,
                    start=start_dt,
                    end=end_dt,
                )
            )

        return occurrences
