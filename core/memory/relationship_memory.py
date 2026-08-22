from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RelationshipMemory:
    """Long-term model of user relationship patterns."""

    facts: dict[str, str] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)

    def remember(self, key: str, value: str, confidence: float = 0.5) -> None:
        self.facts[key] = value
        self.confidence[key] = max(0.0, min(1.0, confidence))

    def get(self, key: str) -> str | None:
        return self.facts.get(key)
