from __future__ import annotations

import sqlite3
from datetime import datetime, time
from pathlib import Path
from typing import List

from .models import MemoryRecord, MemorySource, MemoryType


class SQLiteMemoryStore:
    """基于 SQLite 的持久化记忆存储。"""

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
            str(self.db_path)
        )
        self._connection.row_factory = sqlite3.Row

        self._initialize()

    def _initialize(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                source TEXT NOT NULL,
                importance REAL NOT NULL,
                confidence REAL NOT NULL
            )
            """
        )

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_state (
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

        self._connection.commit()

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime | None:
        """兼容完整 ISO datetime，以及旧版 HH:MM:SS 数据。

        正常数据应该始终保存为：
            2026-08-21T03:52:10+08:00

        旧版本可能错误地保存成：
            03:52:10

        对旧格式这里只恢复成 naive datetime，
        后续由 LifeLoop 的 ensure_aware() 统一处理时区。
        """

        if value is None:
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        try:
            parsed_time = time.fromisoformat(value)

            # 旧数据只有 HH:MM:SS，没有日期和时区。
            # 补齐当前默认时区，确保返回值始终是 aware datetime。
            from ..time_engine import DEFAULT_TZ

            today = datetime.now(DEFAULT_TZ).date()

            return datetime.combine(
                today,
                parsed_time,
                tzinfo=DEFAULT_TZ,
            )
        except ValueError as exc:
            raise ValueError(
                f"invalid persisted datetime: {value!r}"
            ) from exc

    @staticmethod
    def _to_record(
        row: sqlite3.Row,
    ) -> MemoryRecord:
        return MemoryRecord(
            memory_id=row["memory_id"],
            memory_type=MemoryType(row["memory_type"]),
            content=row["content"],
            created_at=datetime.fromisoformat(
                row["created_at"]
            ),
            source=MemorySource(row["source"]),
            importance=float(row["importance"]),
            confidence=float(row["confidence"]),
        )

    def add(
        self,
        memory: MemoryRecord,
    ) -> MemoryRecord:
        try:
            self._connection.execute(
                """
                INSERT INTO memories (
                    memory_id,
                    memory_type,
                    content,
                    created_at,
                    source,
                    importance,
                    confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.memory_id,
                    memory.memory_type.value,
                    memory.content,
                    memory.created_at.isoformat(),
                    memory.source.value,
                    memory.importance,
                    memory.confidence,
                ),
            )
            self._connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                f"memory_id already exists: "
                f"{memory.memory_id}"
            ) from exc

        return memory

    def update(
        self,
        memory_id: str,
        memory: MemoryRecord,
    ) -> MemoryRecord:
        cursor = self._connection.execute(
            """
            UPDATE memories
            SET
                memory_type = ?,
                content = ?,
                created_at = ?,
                source = ?,
                importance = ?,
                confidence = ?
            WHERE memory_id = ?
            """,
            (
                memory.memory_type.value,
                memory.content,
                memory.created_at.isoformat(),
                memory.source.value,
                memory.importance,
                memory.confidence,
                memory_id,
            ),
        )

        if cursor.rowcount == 0:
            raise KeyError(
                f"memory_id not found: {memory_id}"
            )

        self._connection.commit()

        return self.get(memory_id)  # type: ignore[return-value]

    def get(
        self,
        memory_id: str,
    ) -> MemoryRecord | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM memories
            WHERE memory_id = ?
            """,
            (memory_id,),
        ).fetchone()

        if row is None:
            return None

        return self._to_record(row)

    def all(self) -> List[MemoryRecord]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM memories
            ORDER BY rowid ASC
            """
        ).fetchall()

        return [self._to_record(row) for row in rows]

    def recent(
        self,
        limit: int = 10,
    ) -> List[MemoryRecord]:
        if limit <= 0:
            return []

        rows = self._connection.execute(
            """
            SELECT *
            FROM memories
            ORDER BY created_at DESC, rowid DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        records = [
            self._to_record(row)
            for row in rows
        ]
        records.reverse()

        return records

    def search(
        self,
        keyword: str,
    ) -> List[MemoryRecord]:
        if not keyword.strip():
            return []

        keyword = keyword.lower()

        rows = self._connection.execute(
            """
            SELECT *
            FROM memories
            WHERE lower(content) LIKE ?
            ORDER BY rowid ASC
            """,
            (f"%{keyword}%",),
        ).fetchall()

        return [
            self._to_record(row)
            for row in rows
        ]

    def by_type(
        self,
        memory_type: MemoryType,
    ) -> List[MemoryRecord]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM memories
            WHERE memory_type = ?
            ORDER BY rowid ASC
            """,
            (memory_type.value,),
        ).fetchall()

        return [
            self._to_record(row)
            for row in rows
        ]

    def clear(self) -> None:
        self._connection.execute(
            "DELETE FROM memories"
        )
        self._connection.commit()

    # ---------------------------------------------------------
    # Runtime state
    # ---------------------------------------------------------

    def save_runtime_state(
        self,
        *,
        current_time: datetime | None,
        current_slot_id: str | None,
        current_activity: str | None,
        energy: float,
        fatigue: float,
        last_user_interaction_at: datetime | None,
    ) -> None:
        """持久化 LifeLoop 当前运行时状态。"""

        # 这里强制要求 datetime。
        # 防止错误的 time / str 再次写进数据库。
        if current_time is not None and not isinstance(
            current_time,
            datetime,
        ):
            raise TypeError(
                "current_time must be datetime or None"
            )

        if (
            last_user_interaction_at is not None
            and not isinstance(
                last_user_interaction_at,
                datetime,
            )
        ):
            raise TypeError(
                "last_user_interaction_at must be "
                "datetime or None"
            )

        self._connection.execute(
            """
            INSERT INTO runtime_state (
                id,
                current_time,
                current_slot_id,
                current_activity,
                energy,
                fatigue,
                last_user_interaction_at
            )
            VALUES (1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                current_time = excluded.current_time,
                current_slot_id = excluded.current_slot_id,
                current_activity = excluded.current_activity,
                energy = excluded.energy,
                fatigue = excluded.fatigue,
                last_user_interaction_at =
                    excluded.last_user_interaction_at
            """,
            (
                (
                    current_time.isoformat()
                    if current_time is not None
                    else None
                ),
                current_slot_id,
                current_activity,
                float(energy),
                float(fatigue),
                (
                    last_user_interaction_at.isoformat()
                    if last_user_interaction_at is not None
                    else None
                ),
            ),
        )

        self._connection.commit()

    def load_runtime_state(self) -> dict | None:
        """读取持久化的运行状态。"""

        row = self._connection.execute(
            """
            SELECT
                current_time,
                current_slot_id,
                current_activity,
                energy,
                fatigue,
                last_user_interaction_at
            FROM runtime_state
            WHERE id = 1
            """
        ).fetchone()

        if row is None:
            return None

        return {
            "current_time": self._parse_datetime(
                row["current_time"]
            ),
            "current_slot_id": row["current_slot_id"],
            "current_activity": row["current_activity"],
            "energy": float(row["energy"]),
            "fatigue": float(row["fatigue"]),
            "last_user_interaction_at": (
                self._parse_datetime(
                    row["last_user_interaction_at"]
                )
            ),
        }

    def close(self) -> None:
        self._connection.close()

    def __len__(self) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM memories"
        ).fetchone()

        return int(row["count"])
