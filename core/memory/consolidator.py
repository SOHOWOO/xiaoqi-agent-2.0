from __future__ import annotations


class MemoryConsolidator:
    """Foundation for deduplication and long-term memory compression."""

    def consolidate(self, memories: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for memory in memories:
            key = memory.strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(memory.strip())
        return result
