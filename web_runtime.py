from __future__ import annotations

import threading
import time
from datetime import datetime

from core.chat import ChatService, OpenAICompatibleProvider
from core.life_loop import LifeLoop
from core.memory import (
    MemoryContextBuilder,
    MemoryRetriever,
    MemoryStore,
)
from core.memory.importer import CanonicalMemoryImporter
from core.time_engine import DEFAULT_TZ


class WebRuntime:
    """网页运行时：统一管理小七的生活、记忆和对话。"""

    def __init__(
        self,
        *,
        simulation_minutes_per_real_second: float = 60.0,
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

        now = datetime.now(DEFAULT_TZ)

        self.life_loop = LifeLoop(
            start_time=now,
            seed=42,
        )

        if load_canonical:
            self._load_canonical_memories()

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

        self._last_real_time = time.monotonic()

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

    def advance(self) -> None:
        """按真实经过的时间推进模拟生活。"""

        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_real_time

            if elapsed <= 0:
                return

            self._last_real_time = now

            simulation_minutes = (
                elapsed
                * self.simulation_minutes_per_real_second
            )

            from datetime import timedelta

            self.life_loop.tick(
                timedelta(
                    minutes=simulation_minutes
                )
            )

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
