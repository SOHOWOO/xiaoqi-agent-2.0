from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Iterable, List

from .manager import MemoryManager
from .models import (
    MemoryRecord,
    MemorySource,
    MemoryType,
)
from .store import MemoryStore

_STOP_WORDS = {
    "我的",
    "我",
    "你",
    "今天",
    "明天",
    "昨天",
    "最近",
    "现在",
    "过去",
    "晚上",
    "早上",
    "下午",
    "了",
    "的",
    "是",
    "在",
    "很",
    "也",
    "都",
    "和",
    "与",
}


def _tokenize(text: str) -> set[str]:
    """提取文本的关键词集合（中文 n-gram + 英文单词）。"""

    text = text.lower()
    tokens: set[str] = set()

    segments = re.findall(
        r"[\u4e00-\u9fff]+",
        text,
    )

    for segment in segments:
        if segment not in _STOP_WORDS:
            tokens.add(segment)

        for size in (2, 3):
            for i in range(
                len(segment) - size + 1
            ):
                part = segment[i:i + size]
                if part not in _STOP_WORDS:
                    tokens.add(part)

    tokens.update(
        re.findall(r"[a-z0-9_]+", text)
    )

    return {
        token
        for token in tokens
        if token not in _STOP_WORDS
    }


def jaccard_similarity(
    left: Iterable[str],
    right: Iterable[str],
) -> float:
    """两组关键词的 Jaccard 相似度。"""

    a = set(left)
    b = set(right)

    if not a or not b:
        return 0.0

    return len(a & b) / len(a | b)


class MemoryConsolidator:
    """记忆巩固 / 压缩器。

    把多条内容相近的短期记忆自动归纳为一条长期语义记忆，
    实现计划书中的"自动压缩"：
        今天很累 / 最近工作忙 / 项目压力大
        → 用户近期工作压力较高。压力时期更需要陪伴。
    """

    def __init__(
        self,
        store: MemoryStore,
        manager: MemoryManager | None = None,
        threshold: float = 0.35,
        min_group_size: int = 3,
    ) -> None:
        self.store = store
        self.manager = (
            manager
            if manager is not None
            else MemoryManager(store)
        )

        if not 0.0 < threshold < 1.0:
            raise ValueError(
                "threshold must be in (0.0, 1.0)"
            )

        if min_group_size < 2:
            raise ValueError(
                "min_group_size must be at least 2"
            )

        self.threshold = threshold
        self.min_group_size = min_group_size

    def _candidates(
        self,
        source_types: Iterable[MemoryType],
        limit: int,
    ) -> List[MemoryRecord]:
        """取待巩固的候选记忆（按时间升序）。"""

        allowed = set(source_types)

        candidates = [
            memory
            for memory in self.store.all()
            if memory.memory_type in allowed
        ]

        candidates.sort(
            key=lambda m: m.created_at
        )

        return candidates[-limit:]

    def _cluster(
        self,
        candidates: List[MemoryRecord],
    ) -> List[List[MemoryRecord]]:
        """贪心聚类：按时间顺序，把相似记忆归组。"""

        tokenized = [
            _tokenize(memory.content)
            for memory in candidates
        ]

        used = [False] * len(candidates)
        groups: List[List[MemoryRecord]] = []

        for i, tokens in enumerate(tokenized):
            if used[i]:
                continue

            group = [candidates[i]]
            used[i] = True

            for j in range(i + 1, len(candidates)):
                if used[j]:
                    continue

                if (
                    jaccard_similarity(
                        tokens,
                        tokenized[j],
                    )
                    >= self.threshold
                ):
                    group.append(candidates[j])
                    used[j] = True

            if len(group) >= self.min_group_size:
                groups.append(group)

        return groups

    def _summarize(
        self,
        group: List[MemoryRecord],
        created_at: datetime,
    ) -> str:
        """为记忆组生成归纳文本。"""

        counter: Counter[str] = Counter()

        for memory in group:
            counter.update(
                _tokenize(memory.content)
            )

        candidates = [
            token
            for token, count in counter.items()
            if count >= max(2, len(group) // 2)
            and len(token) >= 2
        ]

        topics = sorted(
            candidates,
            key=lambda token: (
                -counter[token],
                -len(token),
                token,
            ),
        )

        if topics:
            topic_text = "、".join(topics[:3])

            return (
                f"近期「{topic_text}」相关的经历较集中，"
                f"基于 {len(group)} 条记忆自动归纳。"
            )

        return (
            f"最近有 {len(group)} 条相关记忆被归纳，"
            "主题较为分散。"
        )

    def consolidate(
        self,
        created_at: datetime,
        source_types: Iterable[MemoryType] = (
            MemoryType.INTERACTION,
            MemoryType.EPISODIC,
            MemoryType.VIRTUAL_LIFE,
        ),
        limit: int = 500,
    ) -> List[MemoryRecord]:
        """执行一次巩固：返回生成的 SEMANTIC 归纳记忆。"""

        candidates = self._candidates(
            source_types,
            limit,
        )

        generated: List[MemoryRecord] = []

        for group in self._cluster(candidates):
            memory = MemoryRecord(
                memory_id=(
                    "consolidated:"
                    f"{created_at.isoformat()}:"
                    f"{len(generated)}"
                ),
                memory_type=MemoryType.SEMANTIC,
                content=self._summarize(
                    group,
                    created_at,
                ),
                created_at=created_at,
                source=MemorySource.MEMORY_CONSOLIDATION,
                importance=0.85,
                confidence=0.7,
            )

            decision = self.manager.add_if_allowed(
                memory
            )

            if decision.action == "add":
                generated.append(memory)

        return generated
