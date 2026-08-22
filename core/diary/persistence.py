from __future__ import annotations

import json
import sqlite3
import threading
from datetime import date, datetime
from pathlib import Path
from typing import List

from .models import DiaryEntry


class SQLiteDiaryStore:
    """基于 SQLite 的日记持久化。"""

    def __init__(
        self,
        db_path: str | Path = "memories/xiaoqi_memory.db",
    ) -> None:
        self.db_path = Path(db_path)

        if self.db_path != Path(":memory:"):
            self.db_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()

        self._initialize()

    def _initialize(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS diaries (
                entry_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                content TEXT NOT NULL,
                mood_tags TEXT NOT NULL,
                event_refs TEXT NOT NULL,
                created_at TEXT
            )
            """
        )

        self._connection.commit()

    @staticmethod
    def _to_entry(
        row: sqlite3.Row,
    ) -> DiaryEntry:
        created_raw = row["created_at"]

        return DiaryEntry(
            entry_id=row["entry_id"],
            date=date.fromisoformat(row["date"]),
            content=row["content"],
            mood_tags=tuple(
                json.loads(row["mood_tags"])
            ),
            event_refs=tuple(
                json.loads(row["event_refs"])
            ),
            created_at=(
                datetime.fromisoformat(created_raw)
                if created_raw
                else None
            ),
        )

    def save(
        self,
        entry: DiaryEntry,
    ) -> DiaryEntry:
        """保存一篇日记（按 entry_id 幂等）。"""

        self._connection.execute(
            """
            INSERT INTO diaries (
                entry_id,
                date,
                content,
                mood_tags,
                event_refs,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(entry_id) DO UPDATE SET
                date = excluded.date,
                content = excluded.content,
                mood_tags = excluded.mood_tags,
                event_refs = excluded.event_refs,
                created_at = excluded.created_at
            """,
            (
                entry.entry_id,
                entry.date.isoformat(),
                entry.content,
                json.dumps(
                    list(entry.mood_tags),
                    ensure_ascii=False,
                ),
                json.dumps(
                    list(entry.event_refs),
                    ensure_ascii=False,
                ),
                (
                    entry.created_at.isoformat()
                    if entry.created_at is not None
                    else None
                ),
            ),
        )

        self._connection.commit()

        return entry

    def all(self) -> List[DiaryEntry]:
        """全部日记（按日期升序）。"""

        rows = self._connection.execute(
            """
            SELECT *
            FROM diaries
            ORDER BY date ASC, rowid ASC
            """
        ).fetchall()

        return [
            self._to_entry(row)
            for row in rows
        ]

    def recent(
        self,
        limit: int = 10,
    ) -> List[DiaryEntry]:
        """最近的若干篇日记（日期降序）。"""

        if limit <= 0:
            return []

        rows = self._connection.execute(
            """
            SELECT *
            FROM diaries
            ORDER BY date DESC, rowid DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        entries = [
            self._to_entry(row)
            for row in rows
        ]
        entries.reverse()

        return entries

    def by_date(
        self,
        day: date,
    ) -> DiaryEntry | None:
        """按日期查找日记。"""

        row = self._connection.execute(
            """
            SELECT *
            FROM diaries
            WHERE date = ?
            """,
            (day.isoformat(),),
        ).fetchone()

        if row is None:
            return None

        return self._to_entry(row)

    def clear(self) -> None:
        self._connection.execute(
            "DELETE FROM diaries"
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def __len__(self) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM diaries"
        ).fetchone()

        return int(row["count"])
