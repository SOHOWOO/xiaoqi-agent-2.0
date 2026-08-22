from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EpisodicMemory:
    """A memory of a specific event in Xiaoqi's timeline."""

    event: str
    created_at: datetime
    importance: float = 0.5
    emotion: str | None = None

    def score(self) -> float:
        return max(0.0, min(1.0, self.importance))
