from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import MemoryRecord, MemoryType
from .policy import can_modify, is_long_term_candidate
from .store import MemoryStore


class MemoryAction:
    """Memory Manager 支持的决策动作。"""

    ADD = "add"
    UPDATE = "update"
    IGNORE = "ignore"
    REJECT = "reject"


@dataclass(frozen=True)
class MemoryDecision:
    """Memory Manager 的规则决策结果。"""

    action: str
    reason: str
    target_memory_id: Optional[str] = None


class MemoryManager:
    """Memory Core 的统一记忆决策与写入入口。"""

    def __init__(self, store: MemoryStore):
        self.store = store

        from .proactive import ProactiveInterestManager
        self.proactive_manager = ProactiveInterestManager()

    def decide(
        self,
        memory: MemoryRecord,
        target_memory: Optional[MemoryRecord] = None,
    ) -> MemoryDecision:
        """决定一条记忆应该 ADD / UPDATE / IGNORE / REJECT。"""

        # ============================================================
        # 1. 新记忆
        # ============================================================
        if target_memory is None:
            if memory.memory_type == MemoryType.CANONICAL:
                return MemoryDecision(
                    action=MemoryAction.ADD,
                    reason="canonical new memory",
                )

            if is_long_term_candidate(
                memory.memory_type,
                memory.importance,
            ):
                return MemoryDecision(
                    action=MemoryAction.ADD,
                    reason="qualified non-canonical new memory",
                )

            return MemoryDecision(
                action=MemoryAction.IGNORE,
                reason=(
                    "non-canonical memory does not qualify "
                    "for long-term storage"
                ),
            )

        # ============================================================
        # 2. 更新已有记忆
        # ============================================================

        if (
            memory.memory_type == MemoryType.CANONICAL
            and target_memory.memory_type == MemoryType.CANONICAL
        ):
            return MemoryDecision(
                action=MemoryAction.UPDATE,
                reason="canonical update of canonical memory",
                target_memory_id=target_memory.memory_id,
            )

        if not can_modify(
            memory.memory_type,
            target_memory.memory_type,
        ):
            return MemoryDecision(
                action=MemoryAction.REJECT,
                reason="modification not allowed by policy",
                target_memory_id=target_memory.memory_id,
            )

        if is_long_term_candidate(
            memory.memory_type,
            memory.importance,
        ):
            return MemoryDecision(
                action=MemoryAction.UPDATE,
                reason="allowed and qualified update",
                target_memory_id=target_memory.memory_id,
            )

        return MemoryDecision(
            action=MemoryAction.IGNORE,
            reason=(
                "modification allowed but memory does not qualify "
                "for long-term"
            ),
            target_memory_id=target_memory.memory_id,
        )

    def add_if_allowed(
        self,
        memory: MemoryRecord,
    ) -> MemoryDecision:
        """根据策略决定是否新增记忆。"""

        decision = self.decide(memory)

        if decision.action == MemoryAction.ADD:
            self.store.add(memory)

            self.proactive_manager.register(
                memory
            )

        return decision

    def update_if_allowed(
        self,
        memory: MemoryRecord,
        target_memory: MemoryRecord,
    ) -> MemoryDecision:
        """根据策略决定是否更新已有记忆。"""

        decision = self.decide(
            memory,
            target_memory=target_memory,
        )

        if decision.action == MemoryAction.UPDATE:
            assert decision.target_memory_id is not None

            self.store.update(
                decision.target_memory_id,
                memory,
            )

        return decision


    def get_proactive_interests(self):
        """获取当前主动关注事项。"""

        return self.proactive_manager.all()


    def process(
        self,
        memory: MemoryRecord,
        target_memory: Optional[MemoryRecord] = None,
    ) -> MemoryDecision:
        """统一处理入口。

        新记忆：
            process(memory)

        更新：
            process(memory, target_memory)
        """

        if target_memory is None:
            return self.add_if_allowed(memory)

        return self.update_if_allowed(
            memory,
            target_memory,
        )