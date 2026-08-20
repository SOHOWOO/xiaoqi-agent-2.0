from __future__ import annotations

from datetime import datetime, timedelta

from .memory import (
    MemoryManager,
    MemoryRecord,
    MemorySource,
    MemoryStore,
    MemoryType,
)
from .simulator import LifeSimulator
from .state import SimulationResult
from .time_engine import DEFAULT_TZ, ensure_aware


class LifeLoop:
    """小七持续生命循环。

    LifeSimulator 负责生活模拟。

    LifeLoop 负责：
    - 推进时间
    - 接收生活事件
    - 将生活事件转换为 MemoryRecord
    - 通过 MemoryManager / Policy 决定是否进入长期记忆
    """

    def __init__(
        self,
        start_time: datetime,
        seed: int | None = None,
        schedule_config=None,
        tz=DEFAULT_TZ,
        memory_store: MemoryStore | None = None,
        memory_manager: MemoryManager | None = None,
    ):
        self.tz = tz

        self.simulator = LifeSimulator(
            seed=seed,
            schedule_config=schedule_config,
            tz=tz,
        )

        self.current_time = ensure_aware(
            start_time,
            tz,
        )

        self.memory_store = (
            memory_store
            if memory_store is not None
            else MemoryStore()
        )

        self.memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager(self.memory_store)
        )

        if self.memory_manager.store is not self.memory_store:
            raise ValueError(
                "memory_manager must use the same memory_store"
            )

        self._memorized_event_ids: set[str] = set()

    def tick(self, duration: timedelta) -> SimulationResult:
        """让小七向前生活一段时间。"""

        if duration.total_seconds() <= 0:
            raise ValueError(
                "tick duration must be positive"
            )

        next_time = self.current_time + duration

        result = self.simulator.simulate(
            self.current_time,
            next_time,
        )

        self._store_events(result)

        self.current_time = next_time

        return result

    def _store_events(
        self,
        result: SimulationResult,
    ) -> None:
        """将生活事件转换为 VIRTUAL_LIFE Memory。"""

        for event in result.events:
            if event.event_id in self._memorized_event_ids:
                continue

            content = (
                f"小七经历了生活事件「{event.event_type}」，"
                f"发生在「{event.slot_id}」期间。"
            )

            memory = MemoryRecord(
                memory_id=f"event:{event.event_id}",
                memory_type=MemoryType.VIRTUAL_LIFE,
                content=content,
                created_at=event.start_time,
                source=MemorySource.LIFE_SIMULATION,
                importance=0.8,
                confidence=1.0,
            )

            decision = self.memory_manager.add_if_allowed(
                memory
            )

            # 只有真正进入 MemoryStore 的事件才标记为已记忆。
            if decision.action == "add":
                self._memorized_event_ids.add(
                    event.event_id
                )

    @property
    def life_state(self):
        """当前小七的生活状态。"""

        return self.simulator.life_state

    @property
    def interaction_state(self):
        """当前互动状态。"""

        return self.simulator.interaction_state