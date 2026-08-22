from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryConflict:
    old_value: str
    new_value: str
    resolution: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MemoryConflictResolver:
    """Resolve changing facts while preserving personal history.

    Memory should evolve over time instead of replacing old experiences.
    Example:
        old: likes coffee
        new: avoids coffee now

    Result keeps both historical and current context.
    """

    def resolve(self, old_value: str, new_value: str) -> MemoryConflict:
        return MemoryConflict(
            old_value=old_value,
            new_value=new_value,
            resolution=(
                f"Historical preference: {old_value}; "
                f"Current preference: {new_value}"
            ),
        )

    def has_changed(self, old_value: str, new_value: str) -> bool:
        return old_value.strip().lower() != new_value.strip().lower()
