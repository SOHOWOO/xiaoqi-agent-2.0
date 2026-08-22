from __future__ import annotations

from datetime import datetime, timedelta

from .diary import DiaryEngine
from .diary.persistence import SQLiteDiaryStore
from .emotion import EmotionEngine
from .memory import (
    MemoryLifecycle,
    MemoryManager,
    MemoryRecord,
    MemorySource,
    MemoryStore,
    MemoryType,
)
from .neurochemical import NeurochemicalEngine
from .proactive import (
    ProactiveContext,
    ProactiveMessage,
    UnifiedProactiveEngine,
)
from .relationship import RelationshipEngine
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
    - 持久化 / 恢复运行时状态
    """

    # 大步长积分时内部拆分的最大子步时长。
    # 用于精确触发作息状态机切换、能量 / 疲劳 / 神经化学
    # 按序演化与跨天边界事件（日记、主动行为）。
    MAX_TICK_STEP = timedelta(minutes=15)

    def __init__(
        self,
        start_time: datetime,
        seed: int | None = None,
        schedule_config=None,
        tz=DEFAULT_TZ,
        memory_store: MemoryStore | None = None,
        memory_manager: MemoryManager | None = None,
        neurochemical_engine: NeurochemicalEngine | None = None,
        emotion_engine: EmotionEngine | None = None,
        diary_engine: DiaryEngine | None = None,
        proactive_engine: UnifiedProactiveEngine | None = None,
        relationship_engine: RelationshipEngine | None = None,
        memory_lifecycle: MemoryLifecycle | None = None,
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

        self._pending_proactive_messages: list[
            ProactiveMessage
        ] = []

        self.neurochemical = (
            neurochemical_engine
            if neurochemical_engine is not None
            else NeurochemicalEngine()
        )

        self.emotion = (
            emotion_engine
            if emotion_engine is not None
            else EmotionEngine()
        )

        self.diary = (
            diary_engine
            if diary_engine is not None
            else DiaryEngine(
                diary_store=SQLiteDiaryStore(":memory:"),
            )
        )

        self.unified_proactive = (
            proactive_engine
            if proactive_engine is not None
            else UnifiedProactiveEngine()
        )

        self.relationship_engine = (
            relationship_engine
            if relationship_engine is not None
            else RelationshipEngine()
        )

        self.memory_lifecycle = memory_lifecycle

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
        """让小七向前生活一段时间。

        两个时间尺度分离：
        - Simulator：一次性计算生活事件（自身具备步长不变性）
        - Engine 积分：神经化学 / 情绪 / 关系 / 日记 / 主动行为
          按 MAX_TICK_STEP 子步推进，确保作息状态机、衰减与
          跨天边界事件按序正确触发。
        """

        if duration.total_seconds() <= 0:
            raise ValueError(
                "tick duration must be positive"
            )

        result = self._advance_once(duration)

        self._persist_runtime_state()

        return result

    def _split_steps(
        self,
        duration: timedelta,
    ) -> list[timedelta]:
        """把时长拆分为不超过 MAX_TICK_STEP 的引擎积分子步。"""

        steps: list[timedelta] = []

        remaining = duration

        while remaining > timedelta(0):
            step = min(remaining, self.MAX_TICK_STEP)
            steps.append(step)
            remaining -= step

        return steps

    def _advance_once(
        self,
        duration: timedelta,
    ) -> SimulationResult:
        """Simulator 一次模拟 + 引擎子步积分。"""

        next_time = self.current_time + duration

        result = self.simulator.simulate(
            self.current_time,
            next_time,
        )

        cursor = self.current_time

        for step in self._split_steps(duration):
            cursor += step
            self._integrate_engine(
                step,
                at_time=cursor,
                result=result,
            )

        if self.memory_lifecycle is not None:
            self.memory_lifecycle.run(next_time)

        self.current_time = next_time

        self._store_events(result)

        return result

    def _integrate_engine(
        self,
        step: timedelta,
        at_time: datetime,
        result: SimulationResult,
    ) -> None:
        """推进一个引擎积分子步（神经化学 / 情绪 / 关系 / 日记 / 主动）。"""

        hours = step.total_seconds() / 3600.0

        self.neurochemical.tick(hours)

        self.emotion.update_from_neurochemical(
            self.neurochemical.state(),
            elapsed_hours=hours,
        )

        self.relationship_engine.tick(at_time)

        self.diary.advance(
            at_time,
            emotion_state=self.emotion.state(),
            life_state=self.life_state,
            events=[
                event.event_type
                for event in result.events
            ],
        )

        # ---------------------------------------------------------
        # 主动行为（Proactive Engine 2.0）
        # ---------------------------------------------------------

        ctx = ProactiveContext(
            now=at_time,
            life_state=self.life_state,
            emotion_state=self.emotion.state(),
            neuro_state=self.neurochemical.state(),
            relationship_state=self.relationship_engine.state,
            diary=self.diary,
            interests=(
                self.memory_manager
                .get_proactive_interests()
            ),
            last_user_interaction_at=(
                self.simulator
                .interaction_state
                .last_user_interaction_at
            ),
            current_slot_id=(
                self.life_state.current_slot_id
            ),
        )

        proactive_actions = (
            self.unified_proactive.evaluate(ctx)
        )

        for action in proactive_actions:
            self._pending_proactive_messages.append(
                ProactiveMessage(
                    content=action.content,
                    source_interest_id=(
                        action.source_interest_id
                    ),
                )
            )

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
        """获取当前待触发的主动行为。"""

        ctx = ProactiveContext(
            now=self.current_time,
            life_state=self.life_state,
            emotion_state=self.emotion.state(),
            neuro_state=self.neurochemical.state(),
            relationship_state=self.relationship_engine.state,
            diary=self.diary,
            interests=(
                self.memory_manager
                .proactive_manager
                .all()
            ),
            last_user_interaction_at=(
                self.simulator
                .interaction_state
                .last_user_interaction_at
            ),
            current_slot_id=(
                self.life_state.current_slot_id
            ),
        )

        return self.unified_proactive.evaluate(ctx)


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
