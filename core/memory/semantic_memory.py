from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SemanticMemory:
    """Stable knowledge and preferences extracted over time."""

    knowledge: dict[str, str] = field(default_factory=dict)

    def set(self, key: str, value: str) -> None:
        self.knowledge[key] = value

    def get(self, key: str) -> str | None:
        return self.knowledge.get(key)
