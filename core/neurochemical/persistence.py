from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from .models import (
    NeurochemicalState,
    Neurotransmitter,
)

_COLUMNS = (
    "dopamine",
    "serotonin",
    "oxytocin",
    "cortisol",
    "endorphin",
    "noradrenaline",
)


class SQLiteNeurochemicalStore:
    """基于 SQLite 的神经化学状态持久化。

    与 SQLiteMemoryStore 共用同一个数据库文件，
    但使用独立的表，避免耦合。
    """

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
            CREATE TABLE IF NOT EXISTS neurochemical_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                dopamine REAL NOT NULL,
                serotonin REAL NOT NULL,
                oxytocin REAL NOT NULL,
                cortisol REAL NOT NULL,
                endorphin REAL NOT NULL,
                noradrenaline REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        self._connection.commit()

    def save(
        self,
        state: NeurochemicalState,
        updated_at: datetime | None = None,
    ) -> None:
        """持久化当前神经化学状态。"""

        updated_at = updated_at or datetime.now()

        self._connection.execute(
            f"""
            INSERT INTO neurochemical_state (
                id,
                {", ".join(_COLUMNS)},
                updated_at
            )
            VALUES (
                1,
                {", ".join("?" for _ in _COLUMNS)},
                ?
            )
            ON CONFLICT(id) DO UPDATE SET
                {", ".join(
                    f"{name} = excluded.{name}"
                    for name in _COLUMNS
                )},
                updated_at = excluded.updated_at
            """,
            (
                *[state.level(nt) for nt in Neurotransmitter],
                updated_at.isoformat(),
            ),
        )

        self._connection.commit()

    def load(self) -> NeurochemicalState | None:
        """读取最近一次持久化的状态。"""

        row = self._connection.execute(
            """
            SELECT *
            FROM neurochemical_state
            WHERE id = 1
            """
        ).fetchone()

        if row is None:
            return None

        return NeurochemicalState(
            **{
                name: float(row[name])
                for name in _COLUMNS
            }
        )

    def close(self) -> None:
        self._connection.close()
