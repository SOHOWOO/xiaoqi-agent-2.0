from __future__ import annotations

import threading
from datetime import datetime

from core.avatar import (
    AvatarController,
    WebSocketAvatarBridge,
)
from core.chat import ChatService, OpenAICompatibleProvider
from core.diary import DiaryEngine, SQLiteDiaryStore
from core.emotion import EmotionEngine, SQLiteEmotionStore
from core.life_loop import LifeLoop
from core.memory import (
    MemoryContextBuilder,
    MemoryLifecycle,
    MemoryRetriever,
    SQLiteMemoryStore,
)
from core.memory.importer import CanonicalMemoryImporter
from core.neurochemical import (
    NeurochemicalEngine,
    SQLiteNeurochemicalStore,
)
from core.time_engine import DEFAULT_TZ


class WebRuntime:
    """网页运行时：统一管理小七的生活、记忆和对话。

    虚拟生活时间与现实时间 1:1 同步：

        现实 1 秒 = 小七 1 秒

    SQLite 保存 LifeLoop 的运行状态，因此服务器重启后，
    小七会从上次保存的时间继续，并追赶到当前现实时间。
    """

    def __init__(
        self,
        *,
        simulation_minutes_per_real_second: float = 1 / 60,
        load_canonical: bool = True,
        avatar_websocket: bool = False,
        avatar_host: str = "127.0.0.1",
        avatar_port: int = 0,
    ) -> None:
        if simulation_minutes_per_real_second <= 0:
            raise ValueError(
                "simulation_minutes_per_real_second must be positive"
            )

        self._lock = threading.RLock()

        self.simulation_minutes_per_real_second = (
            simulation_minutes_per_real_second
        )

        self.memory_store = SQLiteMemoryStore(
            "memories/xiaoqi_memory.db"
        )

        self.neuro_store = SQLiteNeurochemicalStore(
            "memories/xiaoqi_memory.db"
        )
        self.emotion_store = SQLiteEmotionStore(
            "memories/xiaoqi_memory.db"
        )
        self.diary_store = SQLiteDiaryStore(
            "memories/xiaoqi_memory.db"
        )

        neurochemical = NeurochemicalEngine()

        loaded_neuro = self.neuro_store.load()
        if loaded_neuro is not None:
            neurochemical.restore(loaded_neuro)

        emotion = EmotionEngine()

        loaded_emotion = self.emotion_store.load()
        if loaded_emotion is not None:
            emotion.restore(loaded_emotion)

        diary = DiaryEngine(
            diary_store=self.diary_store,
            memory_store=self.memory_store,
        )

        memory_lifecycle = MemoryLifecycle(
            self.memory_store
        )

        now = datetime.now(DEFAULT_TZ)

        self.life_loop = LifeLoop(
            start_time=now,
            seed=42,
            memory_store=self.memory_store,
            neurochemical_engine=neurochemical,
            emotion_engine=emotion,
            diary_engine=diary,
            memory_lifecycle=memory_lifecycle,
        )

        self._restore_relationship()

        if load_canonical:
            self._load_canonical_memories()

        # ---------------------------------------------------------
        # 启动时追赶现实时间
        # ---------------------------------------------------------
        #
        # LifeLoop 初始化时如果 SQLite 有 runtime_state，
        # 已经恢复到上一次保存的 current_time。
        #
        # 如果数据库里的时间早于现实时间，则推进到现实时间。
        #
        # 如果数据库时间已经等于或晚于现实时间，则绝不倒退。
        #
        self._sync_to_real_time()

        retriever = MemoryRetriever(
            self.life_loop.memory_store,
            now_provider=(
                lambda: self.life_loop.current_time
            ),
        )

        context_builder = MemoryContextBuilder(
            retriever
        )

        self.chat = ChatService(
            life_loop=self.life_loop,
            memory_context_builder=context_builder,
            response_provider=OpenAICompatibleProvider(),
        )

        # ---------------------------------------------------------
        # Avatar 表现层（可选，默认关闭以保持隔离）
        # ---------------------------------------------------------

        self.avatar_controller = None
        self.avatar_bridge = None

        if avatar_websocket:
            self.avatar_bridge = (
                WebSocketAvatarBridge(
                    host=avatar_host,
                    port=avatar_port,
                ).start()
            )

            self.avatar_controller = AvatarController(
                self.life_loop.event_bus,
                bridge=self.avatar_bridge,
            )

    def _load_canonical_memories(self) -> None:
        importer = CanonicalMemoryImporter(
            self.life_loop.memory_store
        )

        importer.import_files(
            sorted(
                __import__("pathlib").Path(
                    "memories/canonical"
                ).glob("*.docx")
            )
        )

    def _sync_to_real_time(self) -> None:
        """将 LifeLoop 推进到当前现实时间，但绝不倒退。"""

        now = datetime.now(DEFAULT_TZ)

        current = self.life_loop.current_time

        if now <= current:
            return

        duration = now - current

        self.life_loop.tick(duration)

        self._persist_engines()

    def _persist_engines(self) -> None:
        """持久化神经化学 / 情绪 / 关系引擎状态。"""

        current = self.life_loop.current_time

        self.neuro_store.save(
            self.life_loop.neurochemical.state(),
            updated_at=current,
        )

        self.emotion_store.save(
            self.life_loop.emotion.state(),
            updated_at=current,
        )

        relationship = (
            self.life_loop.relationship_engine.state
        )

        self.memory_store.save_relationship_state(
            relationship.as_dict()
        )

    def _restore_relationship(self) -> None:
        """启动时恢复关系状态。"""

        data = self.memory_store.load_relationship_state()

        if data is None:
            return

        self.life_loop.relationship_engine.restore(data)

    def advance(self) -> None:
        """根据现实时间推进小七的生活。

        与旧版本不同，这里不再使用 monotonic()。

        使用现实 datetime 的绝对时间差，因此服务器关闭期间
        经过的时间也会在下一次启动时被补回来。
        """

        with self._lock:
            self._sync_to_real_time()

    def handle_message(self, message: str):
        with self._lock:
            self.advance()

            result = self.chat.handle_message(message)

            for msg in result.proactive_messages:
                if msg is not None:
                    self.life_loop._pending_proactive_messages.append(msg)

            return result

    def respond(self, result) -> str:
        with self._lock:
            return self.chat.respond(result)


    def proactive_messages(self) -> list[dict]:
        with self._lock:
            messages = []

            # LifeLoop 产生的主动消息
            messages.extend(
                self.life_loop
                .get_pending_proactive_messages()
            )

            return [
                {
                    "content": msg.content,
                }
                for msg in messages
                if msg is not None
            ]

    def memory_counts(self) -> dict[str, int]:
        with self._lock:
            store = self.life_loop.memory_store

            from core.memory import MemoryType

            return {
                "canonical": len(
                    store.by_type(
                        MemoryType.CANONICAL
                    )
                ),
                "interaction": len(
                    store.by_type(
                        MemoryType.INTERACTION
                    )
                ),
                "virtual_life": len(
                    store.by_type(
                        MemoryType.VIRTUAL_LIFE
                    )
                ),
                "episodic": len(
                    store.by_type(
                        MemoryType.EPISODIC
                    )
                ),
                "semantic": len(
                    store.by_type(
                        MemoryType.SEMANTIC
                    )
                ),
                "relationship": len(
                    store.by_type(
                        MemoryType.RELATIONSHIP
                    )
                ),
                "diary": len(
                    store.by_type(
                        MemoryType.DIARY
                    )
                ),
            }

    def observer_state(self) -> dict:
        """心灵观察站综合数据（只读，接真实核心状态）。"""

        with self._lock:
            emotion = self.life_loop.emotion.state()
            neuro = self.life_loop.neurochemical.state()
            relationship = (
                self.life_loop.relationship_engine.state
            )

            diaries = [
                {
                    "date": entry.date.isoformat(),
                    "content": entry.content,
                    "mood_tags": list(entry.mood_tags),
                }
                for entry in self.life_loop.diary.recent(
                    limit=10
                )
            ]

            memories = [
                {
                    "type": memory.memory_type.value,
                    "content": memory.content,
                    "created_at": (
                        memory.created_at.isoformat()
                    ),
                }
                for memory in (
                    self.life_loop
                    .memory_store
                    .recent(limit=30)
                )
            ]

            schedule = self._schedule_snapshot()

            return {
                "emotion": {
                    "current": emotion.as_dict(),
                    "dominant": emotion.dominant().value,
                    "valence": round(
                        emotion.as_dict()["happy"]
                        + emotion.as_dict()["calm"]
                        - emotion.as_dict()["lonely"]
                        - emotion.as_dict()["angry"],
                        3,
                    ),
                },
                "neurochemical": neuro.as_dict(),
                "relationship": relationship.as_dict(),
                "diaries": diaries,
                "memories": memories,
                "schedule": schedule,
            }

    def schedule_data(self) -> dict:
        """日程数据（真实 ScheduleEngine）。"""

        with self._lock:
            return self._schedule_snapshot()

    def memory_data(self, limit: int = 50) -> list[dict]:
        """记忆数据（真实 MemoryStore）。"""

        with self._lock:
            return [
                {
                    "type": memory.memory_type.value,
                    "content": memory.content,
                    "created_at": (
                        memory.created_at.isoformat()
                    ),
                }
                for memory in (
                    self.life_loop
                    .memory_store
                    .recent(limit=limit)
                )
            ]

    def settings_data(self) -> dict:
        """后端设置（真实值，前端偏好另存 localStorage）。"""

        with self._lock:
            return {
                "simulation_minutes_per_real_second": (
                    self.simulation_minutes_per_real_second
                ),
                "allow_proactive": True,
                "simulated_time": (
                    self.life_loop.current_time.isoformat()
                ),
            }

    # 房间物件交互 -> 行为建议（Web 层）。
    # 未来接 LifeLoop 行为调度 / VRM moveTo 的挂载点。
    ROOM_BEHAVIORS = {
        ("move_to", "bed"): "resting",
        ("move_to", "desk"): "reading",
        ("move_to", "sofa"): "relaxing",
        ("move_to", "window"): "thinking",
        ("interact", "xiaoqi"): "talking",
        ("toggle", "lamp"): "idle",
    }

    def handle_action(self, action: dict) -> dict:
        """处理一次房间交互意图（不直接改写核心状态机）。"""

        with self._lock:
            name = action.get("action")
            target = action.get("target")

            behavior = self.ROOM_BEHAVIORS.get(
                (name, target),
                "idle",
            )

            return {
                "accepted": True,
                "behavior": behavior,
                "target": target,
                "simulated_time": (
                    self.life_loop
                    .current_time
                    .isoformat()
                ),
                "hook": (
                    "web-layer behavior; "
                    "future: LifeLoop scheduler / VRM moveTo"
                ),
            }

    def _schedule_snapshot(self) -> dict:
        """返回当前作息信息。"""

        state = self.life_loop.life_state

        schedule_engine = getattr(
            self.life_loop.simulator,
            "schedule_engine",
            None,
        )

        slots = []
        today_slots = []

        if schedule_engine is not None:
            slots = [
                {
                    "id": slot.slot_id,
                    "name": slot.name,
                    "start": (
                        f"{slot.start_seconds // 3600:02d}:"
                        f"{(slot.start_seconds % 3600) // 60:02d}"
                    ),
                    "end": (
                        f"{slot.end_seconds // 3600:02d}:"
                        f"{(slot.end_seconds % 3600) // 60:02d}"
                    ),
                }
                for slot in schedule_engine.workday_slots
            ]

            try:
                today_slots = [
                    {
                        "id": occurrence.slot_id,
                        "name": occurrence.name,
                        "start": (
                            f"{occurrence.start_seconds // 3600:02d}:"
                            f"{(occurrence.start_seconds % 3600) // 60:02d}"
                        ),
                        "end": (
                            f"{occurrence.end_seconds // 3600:02d}:"
                            f"{(occurrence.end_seconds % 3600) // 60:02d}"
                        ),
                    }
                    for occurrence in (
                        schedule_engine.slots_for_date(
                            state.current_time.date()
                        )
                    )
                ]
            except Exception:
                today_slots = []

        return {
            "current_slot": state.current_slot_id,
            "current_activity": state.current_activity,
            "today": today_slots or slots,
        }

    def life_state_dict(self) -> dict:
        with self._lock:
            state = self.life_loop.life_state

            emotion = self.life_loop.emotion.state()
            neuro = self.life_loop.neurochemical.state()

            return {
                "current_time": str(
                    state.current_time
                ),
                "current_activity": state.current_activity,
                "energy": state.energy,
                "fatigue": state.fatigue,
                "emotion": emotion.as_dict(),
                "dominant_emotion": (
                    emotion.dominant().value
                ),
                "neurochemical": neuro.as_dict(),
            }

    def close(self) -> None:
        """关闭运行时及 SQLite 连接。"""

        with self._lock:
            self.memory_store.close()
            self.neuro_store.close()
            self.emotion_store.close()
            self.diary_store.close()

            if self.avatar_bridge is not None:
                self.avatar_bridge.stop()
