from __future__ import annotations

import threading
from datetime import datetime

from core.chat import ChatService, OpenAICompatibleProvider
from core.life_loop import LifeLoop
from core.memory import (
    MemoryContextBuilder,
    MemoryRetriever,
    SQLiteMemoryStore,
)
from core.memory.importer import CanonicalMemoryImporter
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

        now = datetime.now(DEFAULT_TZ)

        self.life_loop = LifeLoop(
            start_time=now,
            seed=42,
            memory_store=self.memory_store,
        )

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
            self.life_loop.memory_store
        )

        context_builder = MemoryContextBuilder(
            retriever
        )

        self.chat = ChatService(
            life_loop=self.life_loop,
            memory_context_builder=context_builder,
            response_provider=OpenAICompatibleProvider(),
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
            return self.chat.handle_message(message)

    def respond(self, result) -> str:
        with self._lock:
            return self.chat.respond(result)

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
            }

    def life_state_dict(self) -> dict:
        with self._lock:
            state = self.life_loop.life_state

            return {
                "current_time": str(
                    state.current_time
                ),
                "current_activity": state.current_activity,
                "energy": state.energy,
                "fatigue": state.fatigue,
            }

    def close(self) -> None:
        """关闭运行时及 SQLite 连接。"""

        with self._lock:
            self.memory_store.close()
