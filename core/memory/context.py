from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import MemoryRecord
from .retriever import MemoryRetriever


@dataclass(frozen=True)
class MemoryContext:
    """供上层 Chat Core 使用的记忆上下文。"""

    query: str
    memories: List[MemoryRecord]

    def as_text(self) -> str:
        """将记忆转换成可提供给 LLM 的纯文本。"""

        if not self.memories:
            return ""

        lines = ["【相关记忆】"]

        for memory in self.memories:
            lines.append(
                f"- [{memory.memory_type.value}] {memory.content}"
            )

        return "\n".join(lines)


class MemoryContextBuilder:
    """根据用户输入构建 MemoryContext。"""

    def __init__(self, retriever: MemoryRetriever):
        self.retriever = retriever

    def build(
        self,
        query: str,
        limit: int = 5,
    ) -> MemoryContext:
        memories = self.retriever.search(
            query,
            limit=limit,
        )

        return MemoryContext(
            query=query,
            memories=memories,
        )
