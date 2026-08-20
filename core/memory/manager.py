from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import MemoryRecord, MemoryType
from .policy import can_modify, is_long_term_candidate


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
    """纯规则 Memory Manager。

    MemoryManager 不负责理解自然语言，只负责根据已有的
    MemoryRecord、MemoryType、importance 和 policy 规则，
    判断一条记忆应该：

    - ADD：新增到长期记忆
    - UPDATE：更新已有记忆
    - IGNORE：不进入长期记忆
    - REJECT：明确违反修改策略
    """

    def __init__(self, store: MemoryStore):
        self.store = store

    def decide(
        self,
        memory: MemoryRecord,
        target_memory: Optional[MemoryRecord] = None,
    ) -> MemoryDecision:
        """判断一条记忆应该如何处理。

        target_memory=None：
            表示这是新记忆。

        target_memory 不为空：
            表示尝试修改已有记忆。
        """

        # ============================================================
        # 1. 新记忆
        # ============================================================
        if target_memory is None:
            # Canonical 是最高优先级的真实记忆，
            # 当前规则下直接允许进入长期记忆。
            if memory.memory_type == MemoryType.CANONICAL:
                return MemoryDecision(
                    action=MemoryAction.ADD,
                    reason="canonical new memory",
                )

            # 非 canonical 记忆需要通过长期记忆候选规则。
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

        # Canonical → Canonical：
        # 允许真实记忆之间进行正式更新。
        if (
            memory.memory_type == MemoryType.CANONICAL
            and target_memory.memory_type == MemoryType.CANONICAL
        ):
            return MemoryDecision(
                action=MemoryAction.UPDATE,
                reason="canonical update of canonical memory",
                target_memory_id=target_memory.memory_id,
            )

        # 通过 policy 判断 source memory 是否有权修改 target memory。
        #
        # 当前项目 policy 的参数是 MemoryType，而不是 source_type。
        if not can_modify(
            memory.memory_type,
            target_memory.memory_type,
        ):
            return MemoryDecision(
                action=MemoryAction.REJECT,
                reason="modification not allowed by policy",
                target_memory_id=target_memory.memory_id,
            )

        # 修改权限允许以后，还需要满足长期记忆候选条件。
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

    def add_if_allowed(self, memory: MemoryRecord) -> MemoryDecision:
        """如果决策为 ADD，则把记忆写入 MemoryStore。

        UPDATE / IGNORE / REJECT 都不会写入 store。

        注意：
        当前阶段只负责 ADD。
        真正 UPDATE 的执行逻辑后续再单独实现，
        避免 MemoryManager 同时承担太多职责。
        """

        decision = self.decide(memory)

        if decision.action == MemoryAction.ADD:
            self.store.add(memory)

        return decision