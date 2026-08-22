from __future__ import annotations

import re
import math
from datetime import datetime, timezone
from typing import Callable, List

from .models import MemoryRecord, MemoryType
from .store import MemoryStore


class MemoryRetriever:
    """小七增强记忆检索器。"""

    _TYPE_PRIORITY = {
        MemoryType.RELATIONSHIP: 4.0,
        MemoryType.CANONICAL: 3.0,
        MemoryType.SEMANTIC: 3.5,
        MemoryType.INTERACTION: 2.0,
        MemoryType.EPISODIC: 2.0,
        MemoryType.VIRTUAL_LIFE: 1.0,
        MemoryType.DIARY: 1.5,
    }

    _STOP_WORDS = {
        "我的",
        "我",
        "你",
        "什么",
        "怎么",
        "为什么",
        "哪里",
        "哪个",
        "多少",
        "是谁",
        "是不是",
        "有没有",
        "可以",
        "吗",
        "呢",
        "啊",
        "了",
        "的",
        "是",
    }

    def __init__(
        self,
        store: MemoryStore,
        now_provider: Callable[[], datetime] | None = None,
    ):
        self.store = store
        self._now_provider = (
            now_provider
            if now_provider is not None
            else lambda: datetime.now(timezone.utc)
        )

    def _extract_keywords(
        self,
        query: str,
    ) -> set[str]:
        query = query.lower().strip()

        if not query:
            return set()

        keywords: set[str] = set()

        for word in query.split():
            word = word.strip(
                "，。！？；：、,.!?;:"
            )
            if word and word not in self._STOP_WORDS:
                keywords.add(word)

        segments = re.findall(
            r"[\u4e00-\u9fff]+",
            query,
        )

        for segment in segments:
            if segment not in self._STOP_WORDS:
                keywords.add(segment)

            for size in range(2, len(segment)+1):
                for i in range(len(segment)-size+1):
                    part = segment[i:i+size]
                    if part not in self._STOP_WORDS:
                        keywords.add(part)

        english = re.findall(
            r"[a-z0-9_]+",
            query,
        )

        keywords.update(
            x for x in english
            if x not in self._STOP_WORDS
        )

        return keywords

    def _recency_score(
        self,
        memory: MemoryRecord,
    ) -> float:
        """越新的记忆越重要。"""

        now = self._now_provider()

        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        else:
            now = now.astimezone(timezone.utc)

        created = memory.created_at

        if created.tzinfo is None:
            created = created.replace(
                tzinfo=timezone.utc
            )

        days = max(
            0,
            (now - created.astimezone(timezone.utc)).days
        )

        return math.exp(
            -days / 180
        )

    def _score(
        self,
        query_keywords: set[str],
        memory: MemoryRecord,
    ) -> float:

        content = memory.content.lower()

        hits = sum(
            1
            for k in query_keywords
            if k in content
        )

        if hits == 0:
            return 0.0

        keyword_score = hits / max(
            len(query_keywords),
            1,
        )

        return (
            keyword_score * 5
            + self._TYPE_PRIORITY.get(
                memory.memory_type,
                1.0,
            )
            + memory.importance * 2
            + self._recency_score(memory)
        )

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[MemoryRecord]:

        if not query.strip():
            return []

        keywords = self._extract_keywords(query)

        if not keywords:
            return []

        scored = []

        for memory in self.store.all():
            score = self._score(
                keywords,
                memory,
            )

            if score > 0:
                scored.append(
                    (score, memory)
                )

        scored.sort(
            key=lambda x: -x[0]
        )

        return [
            memory
            for _, memory in scored[:limit]
        ]
