from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MemoryLayer:
    """Simple storage layer for a specific kind of long term memory."""

    name: str
    items: List[str] = field(default_factory=list)

    def add(self, content: str) -> None:
        if content not in self.items:
            self.items.append(content)


class MemoryLayers:
    """Four-layer memory container used by MemoryManager 2.0.

    The first implementation intentionally keeps storage simple. Persistence
    and vector retrieval can be attached later without changing callers.
    """

    def __init__(self) -> None:
        self.episodic = MemoryLayer("episodic")
        self.relationship = MemoryLayer("relationship")
        self.semantic = MemoryLayer("semantic")
        self.diary = MemoryLayer("diary")

    def add(self, channel: str, content: str) -> None:
        layer = getattr(self, channel, None)
        if layer is not None:
            layer.add(content)

    def snapshot(self) -> Dict[str, List[str]]:
        return {
            "episodic": list(self.episodic.items),
            "relationship": list(self.relationship.items),
            "semantic": list(self.semantic.items),
            "diary": list(self.diary.items),
        }
