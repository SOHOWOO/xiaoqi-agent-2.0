from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class Memory:
    """小七的一条记忆。"""

    memory_id: str
    created_at: datetime
    content: str
    source: str
    tier: int = 1


class MemoryStore:
    """最小内存记忆存储。

    当前版本使用 Python 内存保存。
    后续可以无缝替换成 SQLite / 向量数据库。
    """

    def __init__(self):
        self._memories: List[Memory] = []

    def add(
        self,
        content: str,
        created_at: datetime,
        source: str,
        tier: int = 1,
        memory_id: Optional[str] = None,
    ) -> Memory:
        if not content.strip():
            raise ValueError("memory content cannot be empty")

        if memory_id is None:
            memory_id = f"memory-{len(self._memories) + 1}"

        memory = Memory(
            memory_id=memory_id,
            created_at=created_at,
            content=content,
            source=source,
            tier=tier,
        )

        self._memories.append(memory)
        return memory

    def all(self) -> List[Memory]:
        """返回全部记忆的独立列表。"""
        return list(self._memories)

    def recent(self, limit: int = 10) -> List[Memory]:
        """返回最近的记忆。"""

        if limit <= 0:
            return []

        return self._memories[-limit:]

    def search(self, keyword: str) -> List[Memory]:
        """按简单关键词搜索记忆。"""

        if not keyword.strip():
            return []

        keyword = keyword.lower()

        return [
            memory
            for memory in self._memories
            if keyword in memory.content.lower()
        ]

    def clear(self) -> None:
        self._memories.clear()

    def __len__(self) -> int:
        return len(self._memories)
