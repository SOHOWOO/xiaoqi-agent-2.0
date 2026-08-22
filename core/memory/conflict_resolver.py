from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MemoryConflict:
    old_value: str
    new_value: str
    resolution: str


class MemoryConflictResolver:
    """Keeps memory history instead of blindly overwriting facts."""

    def resolve(self, old_value: str, new_value: str) -> MemoryConflict:
        return MemoryConflict(
            old_value=old_value,
            new_value=new_value,
            resolution=f"Previous: {old_value}; Current: {new_value}",
        )
