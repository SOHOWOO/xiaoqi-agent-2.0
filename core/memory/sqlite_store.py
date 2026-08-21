from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

from .models import MemoryRecord, MemorySource, MemoryType


class SQLiteMemoryStore:
    """基于 SQLite 的持久化记忆存储。"""

    def __init__(self, db_path: str | Path = "memories/xiaoqi_memory.db") -> None:
        self.db_path = Path(db_path)

        if self.db_path != Path(":memory:"):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(str(self.db_path))
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

        self._connection.commit()

    @staticmethod
    def _to_record(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=row["memory_id"],
            memory_type=MemoryType(row["memory_type"]),
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
            source=MemorySource(row["source"]),
            importance=float(row["importance"]),
            confidence=float(row["confidence"]),
        )

    def add(self, memory: MemoryRecord) -> MemoryRecord:
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
                f"memory_id already exists: {memory.memory_id}"
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
            raise KeyError(f"memory_id not found: {memory_id}")

        self._connection.commit()

        return self.get(memory_id)  # type: ignore[return-value]

    def get(self, memory_id: str) -> MemoryRecord | None:
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

    def recent(self, limit: int = 10) -> List[MemoryRecord]:
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

        records = [self._to_record(row) for row in rows]
        records.reverse()

        return records

    def search(self, keyword: str) -> List[MemoryRecord]:
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

        return [self._to_record(row) for row in rows]

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

        return [self._to_record(row) for row in rows]

    def clear(self) -> None:
        self._connection.execute("DELETE FROM memories")
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def __len__(self) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM memories"
        ).fetchone()

        return int(row["count"])
