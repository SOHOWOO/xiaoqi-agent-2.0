from __future__ import annotations

from typing import List

from .models import MemoryRecord
from .store import MemoryStore


class MemoryRetriever:
    """小七的基础记忆检索器。

    第一版使用简单关键词匹配。
    后续可以替换成 Embedding / Vector Search，
    而不影响上层 Chat Core。
    """

    def __init__(self, store: MemoryStore):
        self.store = store

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[MemoryRecord]:
        """根据关键词寻找相关记忆。"""

        if not query.strip() or limit <= 0:
            return []

        keywords = {
            word.strip().lower()
            for word in query.split()
            if word.strip()
        }

        if not keywords:
            return []

        scored: list[tuple[int, MemoryRecord]] = []

        for memory in self.store.all():
            content = memory.content.lower()

            score = sum(
                1
                for keyword in keywords
                if keyword in content
            )

            if score > 0:
                scored.append((score, memory))

        scored.sort(
            key=lambda item: (
                -item[0],
                -item[1].importance,
                item[1].created_at,
            )
        )

        return [
            memory
            for _, memory in scored[:limit]
        ]
