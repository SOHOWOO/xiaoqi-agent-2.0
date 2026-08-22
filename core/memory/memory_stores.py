from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class MemoryItem:
    content: str
    importance: float = 0.5


class BaseMemoryStore:
    """Small abstraction for future persistent memory backends."""

    def __init__(self) -> None:
        self.items: List[MemoryItem] = []

    def add(self, item: MemoryItem) -> None:
        self.items.append(item)

    def all(self) -> List[MemoryItem]:
        return list(self.items)


class EpisodicMemoryStore(BaseMemoryStore):
    """Stores events and experiences."""


class RelationshipMemoryStore(BaseMemoryStore):
    """Stores relationship-related facts."""


class SemanticMemoryStore(BaseMemoryStore):
    """Stores stable facts and preferences."""


class DiaryMemoryStore(BaseMemoryStore):
    """Stores self diary entries."""
