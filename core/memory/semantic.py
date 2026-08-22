from __future__ import annotations

from datetime import datetime
from typing import List

from .manager import MemoryManager
from .models import (
    MemoryRecord,
    MemorySource,
    MemoryType,
)
from .retriever import MemoryRetriever
from .store import MemoryStore


class SemanticMemory:
    """语义记忆服务。

    存放长期事实（如"用户喜欢AI、喜欢技术"）。
    对应计划书中的 Semantic Memory（长期事实）。
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
        self.retriever = MemoryRetriever(store)

    def add_fact(
        self,
        *,
        topic: str,
        content: str,
        created_at: datetime,
        importance: float = 0.9,
        source: MemorySource = MemorySource.USER_PROVIDED,
        memory_id: str | None = None,
    ) -> MemoryRecord:
        """记录一条长期事实。

        topic 作为事实的主题标签（语义检索的辅助线索）。
        """

        memory = MemoryRecord(
            memory_id=memory_id
            or f"semantic:{topic}:{len(self.store)}",
            memory_type=MemoryType.SEMANTIC,
            content=content,
            created_at=created_at,
            source=source,
            importance=importance,
            confidence=1.0,
        )

        self.manager.add_if_allowed(memory)

        return memory

    def facts(
        self,
        topic: str | None = None,
    ) -> List[MemoryRecord]:
        """按主题（或全部）返回事实。"""

        facts = self.store.by_type(
            MemoryType.SEMANTIC
        )

        if topic is None:
            return facts

        return [
            memory
            for memory in facts
            if f"#{topic}" in memory.content
            or topic in memory.content
        ]

    def find(
        self,
        query: str,
        limit: int = 5,
    ) -> List[MemoryRecord]:
        """语义检索相关事实。"""

        return self.retriever.search(
            query,
            limit=limit,
        )
