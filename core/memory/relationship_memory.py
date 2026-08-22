from __future__ import annotations

from datetime import datetime
from typing import List

from .manager import MemoryManager
from .models import (
    MemoryRecord,
    MemorySource,
    MemoryType,
)
from .store import MemoryStore


class RelationshipMemory:
    """关系记忆服务。

    记录与用户有关的偏好、习惯、相处模式，
    如"用户压力大时喜欢安慰"。
    对应计划书中的 Relationship Memory（关系记忆），
    也对应 events.py 中已定义但未实现的
    MemoryTier.TIER_2_RELATIONSHIP_MEMORY。
    """

    def __init__(
        self,
        store: MemoryStore,
        manager: MemoryManager | None = None,
    ) -> None:
        self.store = store
        self.manager = (
            manager
            if manager is not None
            else MemoryManager(store)
        )

    def add_preference(
        self,
        *,
        condition: str,
        behavior: str,
        created_at: datetime,
        importance: float = 0.9,
        memory_id: str | None = None,
    ) -> MemoryRecord:
        """记录一条关系记忆。

        condition 是触发条件（如"用户压力大时"），
        behavior 是用户偏好的相处方式（如"喜欢安慰"）。
        """

        content = f"{condition}，{behavior}"

        memory = MemoryRecord(
            memory_id=memory_id
            or f"relationship:{len(self.store)}",
            memory_type=MemoryType.RELATIONSHIP,
            content=content,
            created_at=created_at,
            source=MemorySource.RELATIONSHIP_ANALYSIS,
            importance=importance,
            confidence=1.0,
        )

        self.manager.add_if_allowed(memory)

        return memory

    def preferences(
        self,
    ) -> List[MemoryRecord]:
        """返回全部关系记忆。"""

        return self.store.by_type(
            MemoryType.RELATIONSHIP
        )

    def recent(
        self,
        limit: int = 10,
    ) -> List[MemoryRecord]:
        """最近的关系记忆（时间降序）。"""

        preferences = self.preferences()
        preferences.sort(
            key=lambda m: m.created_at,
            reverse=True,
        )

        return preferences[:limit]
