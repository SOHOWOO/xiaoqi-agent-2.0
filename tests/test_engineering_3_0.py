from datetime import date, datetime

import pytest

from core.diary import DiaryEngine, DiaryWriter
from core.memory import SQLiteMemoryStore
from core.memory.sqlite_store import STATE_VERSION


# ---------------------------------------------------------
# LLM graceful degradation
# ---------------------------------------------------------


class _FailingLLM:
    def generate(self, prompt: str) -> str:
        raise TimeoutError("LLM timeout")


class _GoodLLM:
    def generate(self, prompt: str) -> str:
        return "今天写得很好。"


def test_llm_failure_falls_back_to_template():
    writer = DiaryWriter(llm_provider=_FailingLLM())

    text = writer.write(
        date=date(2026, 8, 22),
        events=["部署服务器"],
        dominant_emotion="happy",
        mood_tags=["happy"],
        energy=0.8,
    )

    assert writer.last_llm_failed is True
    assert "部署服务器" in text
    assert "精力" in text


def test_llm_success_does_not_flag_failure():
    writer = DiaryWriter(llm_provider=_GoodLLM())

    text = writer.write(
        date=date(2026, 8, 22),
        events=[],
        dominant_emotion="happy",
        mood_tags=[],
        energy=None,
    )

    assert writer.last_llm_failed is False
    assert text == "今天写得很好。"


def test_diary_engine_exposes_llm_failure():
    engine = DiaryEngine(
        writer=DiaryWriter(llm_provider=_FailingLLM())
    )

    engine.record_day(
        date(2026, 8, 22),
        events=["部署"],
    )

    assert engine.llm_failed is True

    engine.clear_llm_failed()
    assert engine.llm_failed is False


# ---------------------------------------------------------
# State versioning
# ---------------------------------------------------------


def test_runtime_state_has_version(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "mem.db")

    store.save_runtime_state(
        current_time=datetime(2026, 8, 22, 12, 0),
        current_slot_id="lunch_break",
        current_activity="午休",
        energy=0.7,
        fatigue=0.4,
        last_user_interaction_at=None,
    )

    loaded = store.load_runtime_state()

    assert loaded["version"] == STATE_VERSION

    store.close()


def test_legacy_runtime_state_without_version(tmp_path):
    """旧库无 version 列时，应自动迁移并可用。"""

    import sqlite3

    db = tmp_path / "legacy.db"

    conn = sqlite3.connect(str(db))
    conn.execute(
        """
        CREATE TABLE runtime_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_time TEXT,
            current_slot_id TEXT,
            current_activity TEXT,
            energy REAL NOT NULL,
            fatigue REAL NOT NULL,
            last_user_interaction_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    store = SQLiteMemoryStore(db)

    loaded = store.load_runtime_state()
    assert loaded is None

    store.save_runtime_state(
        current_time=datetime(2026, 8, 22, 12, 0),
        current_slot_id=None,
        current_activity=None,
        energy=0.5,
        fatigue=0.5,
        last_user_interaction_at=None,
    )

    loaded = store.load_runtime_state()
    assert loaded["version"] == STATE_VERSION

    store.close()


# ---------------------------------------------------------
# SQLite WAL
# ---------------------------------------------------------


def test_sqlite_uses_wal_mode(tmp_path):
    import sqlite3

    store = SQLiteMemoryStore(tmp_path / "wal.db")

    row = store._connection.execute(
        "PRAGMA journal_mode"
    ).fetchone()

    assert row[0].lower() == "wal"

    store.close()
