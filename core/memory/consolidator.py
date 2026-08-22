from __future__ import annotations

from collections import defaultdict


class MemoryConsolidator:
    """Compress repeated memories into higher level long-term summaries.

    The first version only removed exact duplicates. This version keeps the
    interface simple while adding importance grouping and lightweight merging
    so it can later be replaced by an LLM based summarizer.
    """

    def consolidate(self, memories: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for memory in memories:
            text = memory.strip()
            key = text.lower()
            if text and key not in seen:
                seen.add(key)
                result.append(text)

        return result

    def summarize(self, memories: list[str]) -> list[str]:
        """Create compact summaries from related memory fragments."""
        groups: dict[str, list[str]] = defaultdict(list)

        for memory in memories:
            text = memory.strip()
            if not text:
                continue

            words = text.lower().split()
            key = words[0] if words else text.lower()
            groups[key].append(text)

        summaries: list[str] = []
        for items in groups.values():
            if len(items) == 1:
                summaries.append(items[0])
            else:
                summaries.append("；".join(items))

        return summaries
