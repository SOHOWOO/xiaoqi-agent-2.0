from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DiaryEntry:
    content: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    importance: float = 0.5


class DiaryEngine:
    """Creates compact self-reflection records from important events."""

    def __init__(self):
        self.entries: list[DiaryEntry] = []

    def write(self, content: str, importance: float = 0.5) -> DiaryEntry:
        entry = DiaryEntry(content=content, importance=importance)
        self.entries.append(entry)
        return entry
