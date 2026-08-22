from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, List

from ..emotion.models import EmotionState, EmotionType
from ..memory import (
    MemoryManager,
    MemoryRecord,
    MemorySource,
    MemoryStore,
    MemoryType,
)
from ..time_engine import DEFAULT_TZ
from .models import DiaryEntry
from .persistence import SQLiteDiaryStore
from .writer import DiaryWriter

_EVENT_MEMORY_TYPES = {
    MemoryType.EPISODIC,
    MemoryType.INTERACTION,
    MemoryType.VIRTUAL_LIFE,
}


class DiaryEngine:
    """日记引擎。

    负责：
    - 跨天检测：日期变化时为上一天生成日记
    - 日记生成：结合当日事件、情绪、精力（可接 LLM）
    - 日记持久化：独立 diaries 表 + 同步写入 DIARY 类型记忆
    - 日记回顾：reflect 供主动行为 / 对话使用
    """

    def __init__(
        self,
        diary_store: SQLiteDiaryStore | None = None,
        writer: DiaryWriter | None = None,
        memory_store: MemoryStore | None = None,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        self._diary_store = (
            diary_store
            if diary_store is not None
            else SQLiteDiaryStore()
        )

        self._writer = (
            writer
            if writer is not None
            else DiaryWriter()
        )

        self._memory_store = memory_store

        if memory_store is not None:
            self._memory_manager = (
                memory_manager
                if memory_manager is not None
                else MemoryManager(memory_store)
            )
        else:
            self._memory_manager = None

        self._last_date: date | None = None

    def advance(
        self,
        now: datetime,
        *,
        emotion_state: EmotionState | None = None,
        life_state=None,
        events: Iterable[str] = (),
    ) -> DiaryEntry | None:
        """推进日期。若跨天，为上一天生成并保存日记。"""

        today = now.date()

        if (
            self._last_date is not None
            and today != self._last_date
        ):
            entry = self._build_entry(
                self._last_date,
                emotion_state=emotion_state,
                life_state=life_state,
                events=events,
            )

            self._persist(entry)

            self._last_date = today

            return entry

        self._last_date = today

        return None

    def record_day(
        self,
        day: date,
        *,
        emotion_state: EmotionState | None = None,
        life_state=None,
        events: Iterable[str] = (),
    ) -> DiaryEntry:
        """手动为某天生成并保存日记。"""

        entry = self._build_entry(
            day,
            emotion_state=emotion_state,
            life_state=life_state,
            events=events,
        )

        self._persist(entry)

        return entry

    # ---------------------------------------------------------
    # 内部构建
    # ---------------------------------------------------------

    def _mood_tags(
        self,
        emotion_state: EmotionState | None,
    ) -> tuple[str, ...]:
        if emotion_state is None:
            return ("平静",)

        tags = [
            e.value
            for e in EmotionType
            if emotion_state.level(e) >= 0.5
        ]

        if not tags:
            tags = [
                emotion_state.dominant().value
            ]

        return tuple(tags)

    def _collect_events(
        self,
        day: date,
        events: Iterable[str],
    ) -> List[str]:
        events = list(events)

        if events:
            return events

        if self._memory_store is None:
            return []

        collected: List[str] = []

        for memory in self._memory_store.all():
            if (
                memory.memory_type in _EVENT_MEMORY_TYPES
                and memory.created_at.date() == day
            ):
                collected.append(memory.content)

        return collected[:8]

    def _build_entry(
        self,
        day: date,
        *,
        emotion_state: EmotionState | None,
        life_state,
        events: Iterable[str],
    ) -> DiaryEntry:
        tags = self._mood_tags(emotion_state)
        dominant = (
            emotion_state.dominant().value
            if emotion_state is not None
            else "平静"
        )

        event_list = self._collect_events(
            day,
            events,
        )

        energy = (
            life_state.energy
            if life_state is not None
            else None
        )

        content = self._writer.write(
            date=day,
            events=event_list,
            dominant_emotion=dominant,
            mood_tags=tags,
            energy=energy,
        )

        return DiaryEntry(
            entry_id=f"diary:{day.isoformat()}",
            date=day,
            content=content,
            mood_tags=tags,
            event_refs=tuple(event_list),
            created_at=datetime.now(DEFAULT_TZ),
        )

    def _persist(
        self,
        entry: DiaryEntry,
    ) -> None:
        self._diary_store.save(entry)

        if self._memory_manager is not None:
            memory = MemoryRecord(
                memory_id=(
                    f"diary:{entry.date.isoformat()}"
                ),
                memory_type=MemoryType.DIARY,
                content=entry.content,
                created_at=(
                    entry.created_at
                    or datetime.now(DEFAULT_TZ)
                ),
                source=MemorySource.DIARY,
                importance=0.85,
                confidence=1.0,
            )

            self._memory_manager.add_if_allowed(
                memory
            )

    # ---------------------------------------------------------
    # 查询与回顾
    # ---------------------------------------------------------

    def entries(self) -> List[DiaryEntry]:
        return self._diary_store.all()

    def recent(
        self,
        limit: int = 10,
    ) -> List[DiaryEntry]:
        return self._diary_store.recent(limit)

    def by_date(
        self,
        day: date,
    ) -> DiaryEntry | None:
        return self._diary_store.by_date(day)

    def reflect(
        self,
        query: str | None = None,
        limit: int = 5,
    ) -> List[DiaryEntry]:
        """回顾近期日记；若提供 query 则按关键词过滤。"""

        entries = self._diary_store.recent(
            limit=100
        )

        if not query or not query.strip():
            return entries[-limit:]

        keyword = query.strip().lower()

        matched = [
            entry
            for entry in entries
            if keyword in entry.content.lower()
        ]

        return matched[-limit:]
