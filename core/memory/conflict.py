from __future__ import annotations

import re
from datetime import datetime
from typing import List

from .manager import MemoryManager
from .models import (
    MemoryRecord,
    MemorySource,
    MemoryType,
)
from .store import MemoryStore

_POSITIVE = {
    "喜欢",
    "热爱",
    "爱",
    "爱吃",
    "爱喝",
    "想",
    "想要",
    "期待",
}
_NEGATIVE = {
    "讨厌",
    "不喜欢",
    "不爱",
    "戒",
    "戒掉",
    "不吃",
    "不喝",
    "不再",
    "放弃",
    "停止",
    "减少",
    "拒绝",
}

_TOPIC_STOP = {
    "我",
    "你",
    "的",
    "了",
    "是",
    "在",
    "很",
    "也",
    "都",
    "和",
    "与",
    "现在",
    "过去",
    "最近",
    "今天",
}


def _sentiment(text: str) -> str | None:
    """判断文本情感倾向：positive / negative / None。"""

    positive_hits = sum(
        1 for word in _POSITIVE if word in text
    )
    negative_hits = sum(
        1 for word in _NEGATIVE if word in text
    )

    if positive_hits > negative_hits:
        return "positive"

    if negative_hits > positive_hits:
        return "negative"

    return None


def _topic_words(text: str) -> set[str]:
    """提取主题词（去掉情绪词与停用词）。"""

    tokens: set[str] = set()

    segments = re.findall(
        r"[\u4e00-\u9fff]+",
        text,
    )

    for segment in segments:
        if segment not in _TOPIC_STOP:
            tokens.add(segment)

        for i in range(len(segment) - 1):
            part = segment[i:i + 2]
            if part not in _TOPIC_STOP:
                tokens.add(part)

    return {
        token
        for token in tokens
        if token not in _POSITIVE
        and token not in _NEGATIVE
    }


class MemoryConflictResolver:
    """记忆冲突解决器。

    当新记忆与旧记忆矛盾时（如"喜欢咖啡" → "戒咖啡"），
    不覆盖旧记忆，而是生成一条带时间上下文的演变记忆：
        "过去喜欢咖啡，现在已减少或停止。"
    实现计划书中的"冲突解决"（记录变化而非覆盖）。
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

    def detect(
        self,
        new_memory: MemoryRecord,
        candidates: List[MemoryRecord] | None = None,
    ) -> List[MemoryRecord]:
        """找出与新记忆矛盾、且时间不晚于新记忆的旧记忆。"""

        new_sentiment = _sentiment(new_memory.content)

        if new_sentiment is None:
            return []

        new_topics = _topic_words(new_memory.content)

        if not new_topics:
            return []

        if candidates is None:
            candidates = [
                memory
                for memory in self.store.all()
                if memory.memory_type
                in {
                    MemoryType.INTERACTION,
                    MemoryType.EPISODIC,
                    MemoryType.SEMANTIC,
                    MemoryType.RELATIONSHIP,
                }
            ]

        conflicts: List[MemoryRecord] = []

        for memory in candidates:
            if memory.memory_id == new_memory.memory_id:
                continue

            if memory.created_at > new_memory.created_at:
                continue

            old_sentiment = _sentiment(memory.content)

            if old_sentiment is None:
                continue

            if old_sentiment == new_sentiment:
                continue

            if not (
                _topic_words(memory.content)
                & new_topics
            ):
                continue

            conflicts.append(memory)

        return conflicts

    def resolve(
        self,
        new_memory: MemoryRecord,
        conflicting: MemoryRecord,
        created_at: datetime,
    ) -> MemoryRecord | None:
        """为矛盾生成演变记忆并写入。

        返回生成的 SEMANTIC 记忆；若写入失败返回 None。
        """

        old_sentiment = _sentiment(conflicting.content)
        new_sentiment = _sentiment(new_memory.content)

        topics = (
            _topic_words(conflicting.content)
            & _topic_words(new_memory.content)
        )

        topic = (
            sorted(topics)[0]
            if topics
            else "相关事情"
        )

        if (
            old_sentiment == "positive"
            and new_sentiment == "negative"
        ):
            content = (
                f"过去喜欢{topic}，"
                "现在已减少或停止。"
            )

        elif (
            old_sentiment == "negative"
            and new_sentiment == "positive"
        ):
            content = (
                f"过去不太喜欢{topic}，"
                "现在开始接受。"
            )

        else:
            content = (
                f"关于{topic}的偏好发生了变化："
                f"过去——{conflicting.content}；"
                f"现在——{new_memory.content}。"
            )

        memory = MemoryRecord(
            memory_id=(
                "evolution:"
                f"{created_at.isoformat()}:"
                f"{len(self.store)}"
            ),
            memory_type=MemoryType.SEMANTIC,
            content=content,
            created_at=created_at,
            source=MemorySource.MEMORY_CONSOLIDATION,
            importance=0.9,
            confidence=0.8,
        )

        decision = self.manager.add_if_allowed(
            memory
        )

        if decision.action == "add":
            return memory

        return None

    def process(
        self,
        new_memory: MemoryRecord,
        created_at: datetime,
    ) -> MemoryRecord | None:
        """入口：检测矛盾，若存在则生成演变记忆。"""

        conflicts = self.detect(new_memory)

        if not conflicts:
            return None

        return self.resolve(
            new_memory,
            conflicts[0],
            created_at,
        )
