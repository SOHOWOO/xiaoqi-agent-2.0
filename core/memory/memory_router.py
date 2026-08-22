from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MemoryChannel = Literal[
    "episodic",
    "relationship",
    "semantic",
    "diary",
]


@dataclass(frozen=True)
class MemoryRoute:
    """Decides which long-term memory layer receives an experience."""

    channel: MemoryChannel
    reason: str


class MemoryRouter:
    """Lightweight first-stage classifier for MemoryManager 2.0.

    This intentionally stays deterministic. A future LLM based classifier can
    replace it without changing the memory interfaces.
    """

    def route(self, content: str, importance: int = 0) -> MemoryRoute:
        text = content.lower()

        if any(word in text for word in ("喜欢", "讨厌", "习惯", "偏好", "always", "usually")):
            return MemoryRoute("semantic", "stable preference or fact")

        if any(word in text for word in ("我们", "关系", "陪伴", "相信", "想念")):
            return MemoryRoute("relationship", "relationship signal")

        if importance >= 8:
            return MemoryRoute("episodic", "high importance event")

        if any(word in text for word in ("今天", "昨天", "完成", "发生")):
            return MemoryRoute("episodic", "time based experience")

        return MemoryRoute("diary", "personal reflection candidate")
