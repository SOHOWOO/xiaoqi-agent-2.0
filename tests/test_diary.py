from datetime import date, datetime, timedelta

import pytest

from core.diary import (
    DiaryEngine,
    DiaryEntry,
    DiaryWriter,
    SQLiteDiaryStore,
)
from core.emotion import EmotionEngine, EmotionEvent, EmotionType
from core.memory import (
    MemoryRecord,
    MemorySource,
    MemoryStore,
    MemoryType,
)
from core.time_engine import DEFAULT_TZ


def _dt(day: int, hour: int) -> datetime:
    return datetime(2026, 8, day, hour, 0, tzinfo=DEFAULT_TZ)


# ---------------------------------------------------------
# DiaryWriter
# ---------------------------------------------------------


def test_writer_template_contains_events_and_emotion():
    writer = DiaryWriter()

    text = writer.write(
        date=date(2026, 8, 22),
        events=["用户完成了服务器部署"],
        dominant_emotion="happy",
        mood_tags=["happy", "excited"],
        energy=0.8,
    )

    assert "服务器部署" in text
    assert "happy" in text or "心情" in text
    assert "精力" in text


def test_writer_no_events():
    writer = DiaryWriter()

    text = writer.write(
        date=date(2026, 8, 22),
        events=[],
        dominant_emotion="calm",
        mood_tags=[],
        energy=None,
    )

    assert "没什么特别的事" in text


class _StubLLM:
    def __init__(self, response: str = "今天过得很有意义。"):
        self._response = response
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._response


def test_writer_uses_llm_when_provided():
    llm = _StubLLM()
    writer = DiaryWriter(llm_provider=llm)

    text = writer.write(
        date=date(2026, 8, 22),
        events=["聊天"],
        dominant_emotion="happy",
        mood_tags=["happy"],
        energy=0.7,
    )

    assert text == "今天过得很有意义。"
    assert "小七" in llm.last_prompt


# ---------------------------------------------------------
# DiaryEngine
# ---------------------------------------------------------


def test_advance_generates_diary_on_day_change():
    store = SQLiteDiaryStore(":memory:")
    engine = DiaryEngine(diary_store=store)

    assert engine.advance(_dt(21, 10)) is None

    entry = engine.advance(_dt(22, 10))
    assert entry is not None
    assert entry.date == date(2026, 8, 21)
    assert store.by_date(date(2026, 8, 21)) is not None

    store.close()


def test_advance_no_diary_same_day():
    store = SQLiteDiaryStore(":memory:")
    engine = DiaryEngine(diary_store=store)

    engine.advance(_dt(21, 8))
    assert engine.advance(_dt(21, 20)) is None

    store.close()


def test_record_day_persists_entry():
    store = SQLiteDiaryStore(":memory:")
    engine = DiaryEngine(diary_store=store)

    entry = engine.record_day(
        date(2026, 8, 22),
        events=["部署服务器"],
    )

    assert entry.content
    assert engine.by_date(date(2026, 8, 22)) == entry

    store.close()


def test_diary_writes_diary_memory():
    memory_store = MemoryStore()
    store = SQLiteDiaryStore(":memory:")
    engine = DiaryEngine(
        diary_store=store,
        memory_store=memory_store,
    )

    engine.record_day(
        date(2026, 8, 22),
        events=["部署服务器"],
    )

    diaries = memory_store.by_type(MemoryType.DIARY)
    assert len(diaries) == 1
    assert diaries[0].source == MemorySource.DIARY

    store.close()


def test_diary_includes_emotion_tags():
    emotion = EmotionEngine()
    emotion.apply_event(EmotionEvent(EmotionType.HAPPY, 1.0))

    store = SQLiteDiaryStore(":memory:")
    engine = DiaryEngine(diary_store=store)

    entry = engine.record_day(
        date(2026, 8, 22),
        emotion_state=emotion.state(),
    )

    assert "happy" in entry.mood_tags

    store.close()


def test_diary_reflect_filters_by_keyword():
    store = SQLiteDiaryStore(":memory:")
    engine = DiaryEngine(diary_store=store)

    engine.record_day(date(2026, 8, 21), events=["压力很大"])
    engine.record_day(date(2026, 8, 22), events=["很开心"])

    matched = engine.reflect("压力", limit=5)
    assert len(matched) >= 1
    assert "压力" in matched[0].content

    store.close()


# ---------------------------------------------------------
# SQLiteDiaryStore
# ---------------------------------------------------------


def test_diary_store_round_trip(tmp_path):
    store = SQLiteDiaryStore(tmp_path / "diary.db")

    entry = DiaryEntry(
        entry_id="diary:2026-08-22",
        date=date(2026, 8, 22),
        content="今天很开心。",
        mood_tags=("happy",),
        event_refs=("部署",),
        created_at=_dt(22, 23),
    )

    store.save(entry)
    assert store.by_date(date(2026, 8, 22)) == entry
    assert len(store) == 1

    store.close()


def test_diary_store_save_is_idempotent(tmp_path):
    store = SQLiteDiaryStore(tmp_path / "diary.db")

    store.save(
        DiaryEntry(
            entry_id="diary:2026-08-22",
            date=date(2026, 8, 22),
            content="第一版",
        )
    )
    store.save(
        DiaryEntry(
            entry_id="diary:2026-08-22",
            date=date(2026, 8, 22),
            content="第二版",
        )
    )

    assert len(store) == 1
    assert store.by_date(date(2026, 8, 22)).content == "第二版"

    store.close()


def test_diary_store_recent_order(tmp_path):
    store = SQLiteDiaryStore(tmp_path / "diary.db")

    for day in (20, 21, 22):
        store.save(
            DiaryEntry(
                entry_id=f"diary:2026-08-{day}",
                date=date(2026, 8, day),
                content=f"第 {day} 天",
            )
        )

    recent = store.recent(limit=2)
    assert [e.date.day for e in recent] == [21, 22]

    store.close()
