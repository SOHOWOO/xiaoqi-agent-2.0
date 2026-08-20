from __future__ import annotations

from datetime import datetime
from typing import List, overload

from .models import MemoryRecord, MemorySource, MemoryType


class MemoryStore:
    """小七的统一记忆存储。"""

    def __init__(self) -> None:
        self._memories: List[MemoryRecord] = []

    @overload
    def add(self, memory: MemoryRecord) -> MemoryRecord:
        ...

    @overload
    def add(
        self,
        content: str,
        created_at: datetime,
        source: str,
        tier: int = 1,
        memory_id: str | None = None,
    ) -> MemoryRecord:
        ...

    def add(
        self,
        memory: MemoryRecord | str | None = None,
        created_at: datetime | None = None,
        source: str | MemorySource | None = None,
        tier: int = 1,
        memory_id: str | None = None,
        *,
        content: str | None = None,
    ) -> MemoryRecord:
        """添加一条记忆。

        支持新 API：

            store.add(MemoryRecord(...))

        以及旧 API：

            store.add("内容", created_at, "user")

        和旧 API 的关键字形式。
        """

        if isinstance(memory, MemoryRecord):
            record = memory

        else:
            if content is None:
                content = memory

            if content is None:
                raise TypeError("content is required")

            if not content.strip():
                raise ValueError("memory content cannot be empty")

            if created_at is None:
                raise TypeError("created_at is required")

            if source is None:
                raise TypeError("source is required")

            if memory_id is None:
                memory_id = f"memory-{len(self._memories) + 1}"

            if source == "user":
                memory_source = "user"

            elif source == "assistant":
                memory_source = "assistant"

            elif source == "conversation":
                memory_source = MemorySource.CONVERSATION

            elif source == "life_simulation":
                memory_source = MemorySource.LIFE_SIMULATION

            elif isinstance(source, MemorySource):
                memory_source = source

            else:
                memory_source = MemorySource.CONVERSATION

            record = MemoryRecord(
                memory_id=memory_id,
                memory_type=MemoryType.INTERACTION,
                content=content,
                created_at=created_at,
                source=memory_source,
                importance=1.0,
                confidence=1.0,
            )

        if any(
            existing.memory_id == record.memory_id
            for existing in self._memories
        ):
            raise ValueError(
                f"memory_id already exists: {record.memory_id}"
            )

        self._memories.append(record)

        return record

    def update(
        self,
        memory_id: str,
        memory: MemoryRecord,
    ) -> MemoryRecord:
        """用新的 MemoryRecord 替换已有记忆。

        更新后保持目标记忆原有 memory_id，
        从而避免 UPDATE 产生重复 ID。
        """

        if not memory_id.strip():
            raise ValueError("memory_id cannot be empty")

        for index, existing in enumerate(self._memories):
            if existing.memory_id == memory_id:
                updated = MemoryRecord(
                    memory_id=memory_id,
                    memory_type=memory.memory_type,
                    content=memory.content,
                    created_at=memory.created_at,
                    source=memory.source,
                    importance=memory.importance,
                    confidence=memory.confidence,
                )

                self._memories[index] = updated
                return updated

        raise KeyError(f"memory_id not found: {memory_id}")

    def all(self) -> List[MemoryRecord]:
        """返回全部记忆。"""

        return list(self._memories)

    def recent(self, limit: int = 10) -> List[MemoryRecord]:
        """返回最近的记忆。"""

        if limit <= 0:
            return []

        return self._memories[-limit:]

    def search(self, keyword: str) -> List[MemoryRecord]:
        """按关键词搜索记忆。"""

        if not keyword.strip():
            return []

        keyword = keyword.lower()

        return [
            memory
            for memory in self._memories
            if keyword in memory.content.lower()
        ]

    def get(self, memory_id: str) -> MemoryRecord | None:
        """根据 ID 获取记忆。"""

        for memory in self._memories:
            if memory.memory_id == memory_id:
                return memory

        return None

    def by_type(
        self,
        memory_type: MemoryType,
    ) -> List[MemoryRecord]:
        """只返回指定类型的记忆。"""

        return [
            memory
            for memory in self._memories
            if memory.memory_type == memory_type
        ]

    def clear(self) -> None:
        """清空全部记忆。"""

        self._memories.clear()

    def __len__(self) -> int:
        return len(self._memories)