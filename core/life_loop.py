from __future__ import annotations

from datetime import datetime, timedelta

from .bus import EventBus, EventType
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
from .neurochemical import (
    NeurochemicalEngine,
    NeurochemicalStimulus,
    StimulusType,
)
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

    # 失联（PROLONGED_ABSENCE）检测阈值与触发间隔（小时）。
    ABSENCE_THRESHOLD_HOURS = 24.0
    ABSENCE_INTERVAL_HOURS = 6.0

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
        event_bus: EventBus | None = None,
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

        # 启动时刻（失联起算基准：从未互动时从此处开始计算失联时长）。
        self._born_at = self.current_time

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

        self.diary.seed(self.current_time.date())

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

        self.event_bus = (
            event_bus
            if event_bus is not None
            else EventBus()
        )

        self._last_dominant_emotion: str | None = None
        self._last_absence_trigger: datetime | None = None

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
            consolidated = self.memory_lifecycle.run(
                next_time
            )

            if consolidated:
                self.event_bus.publish(
                    EventType.MEMORY_CONSOLIDATED.value,
                    {
                        "count": len(consolidated),
                        "contents": [
                            m.content
                            for m in consolidated
                        ],
                    },
                )

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

        self._apply_absence(at_time)

        diary_entry = self.diary.advance(
            at_time,
            emotion_state=self.emotion.state(),
            life_state=self.life_state,
            events=[
                event.event_type
                for event in result.events
            ],
        )

        self._publish_engine_events(
            at_time,
            diary_entry=diary_entry,
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

            self.event_bus.publish(
                EventType.PROACTIVE_TRIGGERED.value,
                {
                    "content": action.content,
                    "action": (
                        action.signal.suggested_action
                    ),
                    "reason": action.signal.reason,
                },
            )

    def _publish_engine_events(
        self,
        at_time: datetime,
        *,
        diary_entry,
    ) -> None:
        """发布情绪 / 神经化学 / 日记 / 状态变化事件。"""

        emotion_state = self.emotion.state()

        dominant = emotion_state.dominant().value

        if (
            self._last_dominant_emotion is not None
            and self._last_dominant_emotion != dominant
        ):
            self.event_bus.publish(
                EventType.EMOTION_CHANGE.value,
                {
                    "from": self._last_dominant_emotion,
                    "to": dominant,
                    "emotion": emotion_state.as_dict(),
                },
            )

        self._last_dominant_emotion = dominant

        self.event_bus.publish(
            EventType.STATE_UPDATE.value,
            {
                "simulated_time": at_time.isoformat(),
                "emotion": emotion_state.as_dict(),
                "dominant_emotion": dominant,
                "neurochemical": (
                    self.neurochemical.state().as_dict()
                ),
                "relationship": (
                    self.relationship_engine
                    .state
                    .as_dict()
                ),
            },
        )

        if diary_entry is not None:
            self.event_bus.publish(
                EventType.DIARY_WRITTEN.value,
                {
                    "date": (
                        diary_entry.date.isoformat()
                    ),
                    "mood_tags": list(
                        diary_entry.mood_tags
                    ),
                },
            )

    def _apply_absence(
        self,
        now: datetime,
    ) -> None:
        """失联检测：长时间无互动时周期性施加 PROLONGED_ABSENCE。

        保持生命链路完整性：
            失联事件 -> 神经化学 -> 情绪 -> 动机 -> 主动行为
        而非直接"if lonely: 发消息"。
        """

        last = (
            self.simulator
            .interaction_state
            .last_user_interaction_at
        )

        if last is None:
            last = self._born_at

        hours = max(
            0.0,
            (now - last).total_seconds() / 3600.0,
        )

        if hours < self.ABSENCE_THRESHOLD_HOURS:
            return

        if self._last_absence_trigger is not None:
            if (
                now - self._last_absence_trigger
            ).total_seconds() < (
                self.ABSENCE_INTERVAL_HOURS * 3600.0
            ):
                return

        self._last_absence_trigger = now

        intensity = min(
            1.0,
            hours / 72.0,
        )

        self.neurochemical.apply_stimulus(
            NeurochemicalStimulus(
                StimulusType.PROLONGED_ABSENCE,
                intensity=intensity,
            )
        )

        self.emotion.update_from_neurochemical(
            self.neurochemical.state()
        )

    def get_state(self) -> dict:
        """只读状态快照。

        供 Life Lab、Debug、Avatar / UI / WebSocket 等外部观测使用。
        返回不可变快照（EmotionState / NeurochemicalState 为 frozen），
        不暴露内部可变引用。
        """

        life_state = self.life_state

        return {
            "time": self.current_time,
            "life": {
                "current_activity": (
                    life_state.current_activity
                ),
                "energy": life_state.energy,
                "fatigue": life_state.fatigue,
            },
            "emotion": self.emotion.state(),
            "neurochemical": (
                self.neurochemical.state()
            ),
            "relationship": (
                self.relationship_engine
                .state
                .as_dict()
            ),
            "memory": {
                "count": len(self.memory_store),
                "diary_count": len(
                    self.diary.entries()
                ),
            },
        }

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

    # -------------------------------------------------------------
    # External events / actions
    # -------------------------------------------------------------

    _RELATIONSHIP_EVENT_MAP = {
        "positive_interaction": "user_interaction",
        "conflict": "conflict",
        "comfort": "comfort",
        "mutual_help": "mutual_help",
        "shared_experience": "shared_experience",
    }

    _NEUROCHEMICAL_EVENT_MAP = {
        "positive_interaction": StimulusType.USER_INTERACTION,
        "conflict": StimulusType.CONFLICT,
        "comfort": StimulusType.PRAISE,
        "mutual_help": StimulusType.ACHIEVEMENT,
        "shared_experience": StimulusType.ACHIEVEMENT,
    }

    def receive_event(
        self,
        event: dict,
    ) -> None:
        """注入一次外部事件到生命链路（正式公开接口）。

        事件驱动顺序：
            外部事件 -> 关系 / 神经化学 -> 情绪 -> 记忆 -> 总线

        event:
            type: positive_interaction / conflict / comfort /
                  mutual_help / shared_experience
            intensity / severity: 0.0 ~ 1.0
            message: 可选描述
        """

        event_type = event.get(
            "type",
            "positive_interaction",
        )

        intensity = float(
            event.get(
                "intensity",
                event.get("severity", 1.0),
            )
        )

        intensity = max(0.0, min(1.0, intensity))

        message = event.get("message", "")

        # 1. 互动时间
        self.simulator.interaction_state.last_user_interaction_at = (
            self.current_time
        )

        # 2. 关系
        rel_type = self._RELATIONSHIP_EVENT_MAP.get(
            event_type,
            "user_interaction",
        )

        self.relationship_engine.update(
            rel_type,
            intensity=intensity,
            now=self.current_time,
        )

        # 3. 神经化学 + 情绪
        stimulus = self._NEUROCHEMICAL_EVENT_MAP.get(
            event_type,
            StimulusType.USER_INTERACTION,
        )

        self.neurochemical.apply_stimulus(
            NeurochemicalStimulus(
                stimulus,
                intensity=intensity,
            )
        )

        self.emotion.update_from_neurochemical(
            self.neurochemical.state()
        )

        # 4. 情景记忆（事件记忆）
        memory = MemoryRecord(
            memory_id=(
                "episodic:interaction:"
                f"{len(self.memory_store)}"
            ),
            memory_type=MemoryType.EPISODIC,
            content=(
                f"用户与小七的互动："
                f"{message or event_type}"
            ),
            created_at=self.current_time,
            source=MemorySource.CONVERSATION,
            importance=0.7,
            confidence=1.0,
        )

        self.memory_manager.add_if_allowed(memory)

        # 5. 总线事件
        self.event_bus.publish(
            "user_event",
            {
                "type": event_type,
                "intensity": intensity,
                "message": message,
            },
        )

    def get_actions(self):
        """只读评估当前会产生的主动行为（不消耗冷却）。

        供 Life Lab / 调试观测内在动机。
        """

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

        return self.unified_proactive.peek(ctx)
        return self.simulator.interaction_state
