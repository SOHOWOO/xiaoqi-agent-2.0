from __future__ import annotations

from datetime import datetime, timedelta

from .memory import MemoryStore
from .simulator import LifeSimulator
from .state import SimulationResult
from .time_engine import DEFAULT_TZ, ensure_aware


class LifeLoop:
    """小七持续生命循环。

    LifeSimulator 负责真正的生活模拟，
    LifeLoop 负责持续推进时间，并把生活事件写入 MemoryStore。
    """

    def __init__(
        self,
        start_time: datetime,
        seed: int | None = None,
        schedule_config=None,
        tz=DEFAULT_TZ,
        memory_store: MemoryStore | None = None,
    ):
        self.tz = tz

        self.simulator = LifeSimulator(
            seed=seed,
            schedule_config=schedule_config,
            tz=tz,
        )

        self.current_time = ensure_aware(start_time, tz)

        # 如果外部没有提供 MemoryStore，就创建一个新的。
        self.memory_store = memory_store if memory_store is not None else MemoryStore()

        # 防止同一个事件被重复写入记忆。
        self._memorized_event_ids: set[str] = set()

    def tick(self, duration: timedelta) -> SimulationResult:
        """让小七向前生活一段时间。"""

        if duration.total_seconds() <= 0:
            raise ValueError("tick duration must be positive")

        next_time = self.current_time + duration

        result = self.simulator.simulate(
            self.current_time,
            next_time,
        )

        # 把本次模拟产生的生活事件写入记忆。
        self._store_events(result)

        self.current_time = next_time

        return result

    def _store_events(self, result: SimulationResult) -> None:
        """将 SimulationResult 中的新事件写入 MemoryStore。"""

        for event in result.events:
            if event.event_id in self._memorized_event_ids:
                continue

            content = (
                f"小七经历了生活事件「{event.event_type}」，"
                f"发生在「{event.slot_id}」期间。"
            )

            self.memory_store.add(
                memory_id=f"event:{event.event_id}",
                created_at=event.start_time,
                content=content,
                source="life_simulation",
                tier=3,
            )

            self._memorized_event_ids.add(event.event_id)

    @property
    def life_state(self):
        """当前小七的生活状态。"""
        return self.simulator.life_state

    @property
    def interaction_state(self):
        """当前互动状态。"""
        return self.simulator.interaction_state
