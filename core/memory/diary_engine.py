from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class DiaryEntry:
    content: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    importance: float = 0.5
    emotions: List[str] = field(default_factory=list)


class DiaryEngine:
    """Creates compact self-reflection records from important events."""

    def __init__(self):
        self.entries: list[DiaryEntry] = []

    def write(
        self,
        content: str,
        importance: float = 0.5,
        emotions: List[str] | None = None,
    ) -> DiaryEntry:
        entry = DiaryEntry(
            content=content,
            importance=importance,
            emotions=emotions or [],
        )
        self.entries.append(entry)
        return entry

    def recent(self, limit: int = 10) -> list[DiaryEntry]:
        return self.entries[-limit:]
