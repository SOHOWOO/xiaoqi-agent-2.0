from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from .consolidation import MemoryConsolidator
from .manager import MemoryManager
from .models import MemoryRecord, MemoryType
from .store import MemoryStore

_PRUNED_TYPES = {
    MemoryType.INTERACTION,
    MemoryType.EPISODIC,
}


class MemoryLifecycle:
    """记忆生命周期管理。

    负责短期 -> 长期记忆的自动沉淀：
    - 定期巩固：每天把相似短期记忆聚类归纳为语义记忆（Consolidator）
    - 定期遗忘：超过保留期的低价值短期记忆降低权重（沉淀而非删除），
      真实记忆与已归纳的长期记忆不受影响
    """

    def __init__(
        self,
        store: MemoryStore,
        manager: MemoryManager | None = None,
        consolidator: MemoryConsolidator | None = None,
        *,
        consolidate_interval: timedelta = timedelta(days=1),
        forget_after: timedelta = timedelta(days=30),
        min_keep_importance: float = 0.3,
    ) -> None:
        self.store = store
        self.manager = (
            manager
            if manager is not None
            else MemoryManager(store)
        )
        self.consolidator = (
            consolidator
            if consolidator is not None
            else MemoryConsolidator(store, self.manager)
        )

        if consolidate_interval <= timedelta(0):
            raise ValueError(
                "consolidate_interval must be positive"
            )

        if forget_after <= timedelta(0):
            raise ValueError(
                "forget_after must be positive"
            )

        if not 0.0 <= min_keep_importance <= 1.0:
            raise ValueError(
                "min_keep_importance must be between 0.0 and 1.0"
            )

        self.consolidate_interval = consolidate_interval
        self.forget_after = forget_after
        self.min_keep_importance = min_keep_importance

        self._last_consolidate_at: datetime | None = None

    def run(
        self,
        now: datetime,
    ) -> List[MemoryRecord]:
        """执行一次生命周期处理。

        返回本次巩固生成的语义记忆。
        """

        generated = self._maybe_consolidate(now)
        self._prune(now)

        return generated

    # ---------------------------------------------------------
    # 巩固
    # ---------------------------------------------------------

    def _maybe_consolidate(
        self,
        now: datetime,
    ) -> List[MemoryRecord]:
        """按间隔执行记忆巩固。"""

        if self._last_consolidate_at is not None:
            if (
                now - self._last_consolidate_at
                < self.consolidate_interval
            ):
                return []

        self._last_consolidate_at = now

        return self.consolidator.consolidate(
            created_at=now
        )

    # ---------------------------------------------------------
    # 遗忘（沉淀降权）
    # ---------------------------------------------------------

    def _prune(
        self,
        now: datetime,
    ) -> int:
        """把超过保留期且价值低的短期记忆降权。

        返回处理条数。不做硬删除，保证真实记忆与长期记忆安全。
        """

        pruned = 0

        for memory_type in _PRUNED_TYPES:
            for memory in self.store.by_type(memory_type):
                if memory.importance < self.min_keep_importance:
                    continue

                age = now - memory.created_at

                if age < self.forget_after:
                    continue

                lowered = MemoryRecord(
                    memory_id=memory.memory_id,
                    memory_type=memory.memory_type,
                    content=memory.content,
                    created_at=memory.created_at,
                    source=memory.source,
                    importance=min(
                        memory.importance,
                        self.min_keep_importance * 0.5,
                    ),
                    confidence=memory.confidence * 0.8,
                )

                self.store.update(
                    memory.memory_id,
                    lowered,
                )

                pruned += 1

        return pruned
