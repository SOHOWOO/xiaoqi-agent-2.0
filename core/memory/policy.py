from __future__ import annotations

from .models import MemoryType


def can_modify(source_type: MemoryType, target_type: MemoryType) -> bool:
    """判断一种记忆是否可以修改另一种记忆。

    当前规则：
    - 真实记忆不能被虚拟生活记忆修改。
    - 虚拟生活记忆不能修改真实记忆。
    - 不允许通过普通 Memory Core 修改已有真实记忆。
    """

    if target_type == MemoryType.CANONICAL:
        return source_type == MemoryType.CANONICAL

    return True


def is_long_term_candidate(
    memory_type: MemoryType,
    importance: float,
) -> bool:
    """判断一条记忆是否具备进入长期记忆的基本条件。

    这里只做基础规则。
    真正的“这句话值不值得记住”，
    后面交给 Memory Manager / LLM 判断。
    """

    if not 0.0 <= importance <= 1.0:
        raise ValueError("importance must be between 0.0 and 1.0")

    # 真实记忆默认进入长期记忆。
    if memory_type == MemoryType.CANONICAL:
        return True

    # 互动记忆和虚拟生活记忆需要达到重要程度阈值。
    return importance >= 0.7
