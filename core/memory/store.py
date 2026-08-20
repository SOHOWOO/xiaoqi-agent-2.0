from __future__ import annotations

from typing import List

from .models import MemoryRecord, MemoryType


class MemoryStore:
    """小七的统一记忆存储。"""

    def __init__(self) -> None:
        self._memories: List[MemoryRecord] = []

    def add(self, memory: MemoryRecord) -> MemoryRecord:
        """添加一条记忆。"""

        if any(existing.memory_id == memory.memory_id for existing in self._memories):
            raise ValueError(
                f"memory_id already exists: {memory.memory_id}"
            )

        self._memories.append(memory)
        return memory

    def all(self) -> List[MemoryRecord]:
        """返回全部记忆。"""

        return list(self._memories)

    def get(self, memory_id: str) -> MemoryRecord | None:
        """根据 ID 获取记忆。"""

        for memory in self._memories:
            if memory.memory_id == memory_id:
                return memory

        return None

    def by_type(self, memory_type: MemoryType) -> List[MemoryRecord]:
        """只返回指定类型的记忆。"""

        return [
            memory
            for memory in self._memories
            if memory.memory_type == memory_type
        ]

    def __len__(self) -> int:
        return len(self._memories)
