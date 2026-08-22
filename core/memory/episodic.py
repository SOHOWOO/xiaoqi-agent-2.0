from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from .manager import MemoryManager
from .models import (
    MemoryRecord,
    MemorySource,
    MemoryType,
)
from .store import MemoryStore


class EpisodicMemory:
    """情景记忆服务。

    以时间顺序记录"发生过的事"，支持时序回放。
    对应计划书中的 Episodic Memory（事件记忆）。
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

    def record(
        self,
        *,
        content: str,
        created_at: datetime,
        importance: float = 0.8,
        source: MemorySource = MemorySource.LIFE_SIMULATION,
        memory_id: str | None = None,
    ) -> MemoryRecord:
        """记录一段情景。"""

        memory = MemoryRecord(
            memory_id=memory_id
            or f"episodic:{created_at.isoformat()}:{len(self.store)}",
            memory_type=MemoryType.EPISODIC,
            content=content,
            created_at=created_at,
            source=source,
            importance=importance,
            confidence=1.0,
        )

        self.manager.add_if_allowed(memory)

        return memory

    def timeline(
        self,
        source_types: Iterable[MemoryType] | None = None,
    ) -> List[MemoryRecord]:
        """按时间升序返回情景链。"""

        allowed = (
            {MemoryType.EPISODIC}
            if source_types is None
            else set(source_types)
        )

        episodes = [
            memory
            for memory in self.store.all()
            if memory.memory_type in allowed
        ]

        episodes.sort(key=lambda m: m.created_at)

        return episodes

    def recent(
        self,
        limit: int = 10,
    ) -> List[MemoryRecord]:
        """最近的若干条情景（时间降序）。"""

        episodes = self.timeline()

        return list(reversed(episodes[-limit:]))

    def before(
        self,
        moment: datetime,
    ) -> List[MemoryRecord]:
        """某个时刻之前的情景。"""

        return [
            memory
            for memory in self.timeline()
            if memory.created_at < moment
        ]
