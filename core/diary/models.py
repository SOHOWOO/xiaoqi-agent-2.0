from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class DiaryEntry:
    """小七的一篇日记。

    mood_tags 为当天情绪标签，
    event_refs 为当天发生事件的简述。
    """

    entry_id: str
    date: date
    content: str
    mood_tags: tuple[str, ...] = ()
    event_refs: tuple[str, ...] = ()
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.entry_id.strip():
            raise ValueError("entry_id cannot be empty")

        if not self.content.strip():
            raise ValueError("diary content cannot be empty")
