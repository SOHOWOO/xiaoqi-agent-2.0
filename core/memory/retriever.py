from __future__ import annotations

import re
from typing import List

from .models import MemoryRecord, MemoryType
from .store import MemoryStore


class MemoryRetriever:
    """小七的基础记忆检索器。

    支持：
    - 直接关键词查询
    - 中文自然语言查询
    - Canonical 优先级
    - Interaction / Virtual Life 检索
    """

    _TYPE_PRIORITY = {
        MemoryType.CANONICAL: 3,
        MemoryType.INTERACTION: 2,
        MemoryType.VIRTUAL_LIFE: 1,
    }

    # 只放真正的功能词。
    #
    # 注意：
    # “小七”是实体名称，绝对不能作为停用词。
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

    def __init__(self, store: MemoryStore):
        self.store = store

    def _extract_keywords(self, query: str) -> set[str]:
        """从中文/英文自然语言查询中提取轻量关键词。"""

        query = query.strip().lower()

        if not query:
            return set()

        keywords: set[str] = set()

        # ---------------------------------------------------------
        # 1. 空格分词
        # ---------------------------------------------------------
        for word in query.split():
            word = word.strip(
                "，。！？；：、,.!?;:"
            )

            if word and word not in self._STOP_WORDS:
                keywords.add(word)

        # ---------------------------------------------------------
        # 2. 中文连续文本
        # ---------------------------------------------------------
        chinese_segments = re.findall(
            r"[\u4e00-\u9fff]+",
            query,
        )

        for segment in chinese_segments:

            # 整个连续片段本身也是一个候选关键词。
            if segment not in self._STOP_WORDS:
                keywords.add(segment)

            # 提取 2 字以上连续片段。
            for size in range(2, len(segment) + 1):
                for start in range(
                    len(segment) - size + 1
                ):
                    keyword = segment[
                        start:start + size
                    ]

                    if keyword not in self._STOP_WORDS:
                        keywords.add(keyword)

        # ---------------------------------------------------------
        # 3. 英文 / 数字
        # ---------------------------------------------------------
        english_parts = re.findall(
            r"[a-z0-9_]+",
            query,
        )

        for part in english_parts:
            if part not in self._STOP_WORDS:
                keywords.add(part)

        return keywords

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[MemoryRecord]:
        """根据关键词寻找相关记忆。"""

        if not query.strip() or limit <= 0:
            return []

        keywords = self._extract_keywords(query)

        if not keywords:
            return []

        scored: list[
            tuple[int, MemoryRecord]
        ] = []

        for memory in self.store.all():
            content = memory.content.lower()

            score = sum(
                1
                for keyword in keywords
                if keyword in content
            )

            if score > 0:
                scored.append(
                    (score, memory)
                )

        # 排序规则：
        #
        # 1. 匹配关键词越多越优先
        # 2. Canonical > Interaction > Virtual Life
        # 3. importance 越高越优先
        # 4. 创建时间较早的稳定排后
        scored.sort(
            key=lambda item: (
                -item[0],
                -self._TYPE_PRIORITY[
                    item[1].memory_type
                ],
                -item[1].importance,
                item[1].created_at,
            )
        )

        return [
            memory
            for _, memory in scored[:limit]
        ]