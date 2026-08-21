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
from .life.proactive_scheduler import ProactiveScheduler
from .life.proactive_engine import ProactiveEngine
from .chat.proactive_trigger import ProactiveTrigger, ProactiveMessage


class LifeLoop:
    """小七持续生命循环。

    LifeSimulator 负责生活模拟。

    LifeLoop 负责：
    - 推进时间
    - 接收生活事件
    - 将生活事件转换为 MemoryRecord
    - 通过 MemoryManager / Policy 决定是否进入长期记忆
    - 持久化 / 恢复运行时状态
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

        self.current_time = ensure_aware(
            start_time,
            tz,
        )

        self.simulator = LifeSimulator(
            seed=seed,
            schedule_config=schedule_config,
            tz=tz,
        )

        self._memorized_event_ids: set[str] = set()

        self.proactive_scheduler = ProactiveScheduler()
        self.proactive_engine = ProactiveEngine()

        self.proactive_trigger = ProactiveTrigger()

        self._pending_proactive_messages: list[
            ProactiveMessage
        ] = []

        # ---------------------------------------------------------
        # 从持久化存储恢复
        # ---------------------------------------------------------

        self._restore_runtime_state()

        # 已经写入 SQLite 的 virtual-life memory
        # 直接作为“已经记忆”的事件恢复。
        self._restore_memorized_event_ids()

        # LifeSimulator 使用自己的集合防止事件重复产生。
        # 两者都恢复，避免重启后同一个事件再次出现。
        self.simulator._emitted_event_keys.update(
            self._memorized_event_ids
        )

        self._persist_runtime_state()

    # -------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------

    def _restore_runtime_state(self) -> None:
        """如果 MemoryStore 支持 runtime state，则恢复它。"""

        loader = getattr(
            self.memory_store,
            "load_runtime_state",
            None,
        )

        if loader is None:
            return

        state = loader()

        if state is None:
            return

        saved_time = state.get("current_time")

        if saved_time is not None:
            saved_time = ensure_aware(
                saved_time,
                self.tz,
            )

            self.current_time = saved_time

            self.simulator.life_state.current_time = (
                saved_time
            )

        self.simulator.life_state.current_slot_id = (
            state.get("current_slot_id")
        )

        self.simulator.life_state.current_activity = (
            state.get("current_activity")
        )

        if state.get("energy") is not None:
            self.simulator.life_state.energy = float(
                state["energy"]
            )

        if state.get("fatigue") is not None:
            self.simulator.life_state.fatigue = float(
                state["fatigue"]
            )

        last_interaction = state.get(
            "last_user_interaction_at"
        )

        if last_interaction is not None:
            self.simulator.interaction_state.last_user_interaction_at = (
                ensure_aware(
                    last_interaction,
                    self.tz,
                )
            )

    def _restore_memorized_event_ids(self) -> None:
        """从已有 VIRTUAL_LIFE memory 恢复事件去重状态。"""

        for memory in self.memory_store.by_type(
            MemoryType.VIRTUAL_LIFE
        ):
            prefix = "event:"

            if not memory.memory_id.startswith(prefix):
                continue

            event_id = memory.memory_id[
                len(prefix):
            ]

            if event_id:
                self._memorized_event_ids.add(
                    event_id
                )

    def _persist_runtime_state(self) -> None:
        """保存当前运行时状态。

        普通 MemoryStore 没有这个 API，因此不会影响
        原有的内存版 LifeLoop。
        """

        saver = getattr(
            self.memory_store,
            "save_runtime_state",
            None,
        )

        if saver is None:
            return

        state = self.simulator.life_state
        interaction = self.simulator.interaction_state

        saver(
            current_time=self.current_time,
            current_slot_id=state.current_slot_id,
            current_activity=state.current_activity,
            energy=state.energy,
            fatigue=state.fatigue,
            last_user_interaction_at=(
                interaction.last_user_interaction_at
            ),
        )

    # -------------------------------------------------------------
    # Simulation
    # -------------------------------------------------------------

    def tick(
        self,
        duration: timedelta,
    ) -> SimulationResult:
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

        proactive_events = self.proactive_engine.evaluate(
            self.memory_manager.get_proactive_interests(),
            next_time,
            life_state=self.life_state,
        )

        result.events.extend(
            proactive_events
        )

        for event in proactive_events:
            message = self.proactive_trigger.handle(
                event
            )

            if message is not None:
                self._pending_proactive_messages.append(
                    message
                )

        self._store_events(result)

        self.current_time = next_time

        self._persist_runtime_state()

        return result

    def get_pending_proactive_messages(
        self,
    ) -> list[ProactiveMessage]:
        """获取等待发送的主动消息。"""

        messages = list(
            self._pending_proactive_messages
        )

        self._pending_proactive_messages.clear()

        return messages


    def get_proactive_events(self):
        """获取当前待触发的主动关注事件。"""

        interests = (
            self.memory_manager
            .proactive_manager
            .all()
        )

        return self.proactive_engine.evaluate(
            interests,
            self.current_time,
            life_state=self.life_state,
        )


    # -------------------------------------------------------------
    # Event memories
    # -------------------------------------------------------------

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

                self.simulator._emitted_event_keys.add(
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
