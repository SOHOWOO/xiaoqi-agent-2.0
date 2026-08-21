from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import MemoryRecord


@dataclass(frozen=True)
class ProactiveInterest:
    """未来主动关注事项。"""

    interest_id: str
    content: str
    source_memory_id: str
    created_at: datetime
    importance: float
    triggered: bool = False


class ProactiveInterestManager:
    """根据长期记忆生成主动关注点。"""

    def __init__(self):
        self._interests: dict[str, ProactiveInterest] = {}

    def register(
        self,
        memory: MemoryRecord,
    ) -> ProactiveInterest | None:
        """注册高重要记忆的未来关注事项。"""

        if memory.importance < 0.8:
            return None

        interest = ProactiveInterest(
            interest_id=f"interest:{len(self._interests)+1}",
            content=self._extract_focus(
                memory.content
            ),
            source_memory_id=memory.memory_id,
            created_at=memory.created_at,
            importance=memory.importance,
        )

        self._interests[
            interest.interest_id
        ] = interest

        return interest

    def _extract_focus(
        self,
        text: str,
    ) -> str:
        """提取未来关注点。"""

        keywords = {
            "生日",
            "考试",
            "工作",
            "计划",
            "打算",
            "旅行",
            "喜欢",
            "讨厌",
        }

        for keyword in keywords:
            if keyword in text:
                return text

        return f"关注：{text}"

    def all(
        self,
    ) -> list[ProactiveInterest]:
        return list(
            self._interests.values()
        )
