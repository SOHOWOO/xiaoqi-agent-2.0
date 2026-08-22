from __future__ import annotations

import json
from pathlib import Path


class SimulationLogger:
    """把每次 tick 的状态快照追加写入 state.jsonl。

    只接受 LifeLoop.get_state() 返回的可序列化快照。
    """

    def __init__(
        self,
        folder: str | Path,
    ) -> None:
        self.folder = Path(folder)
        self.folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.file = self.folder / "state.jsonl"
        self._count = 0

    def record(
        self,
        snapshot: dict,
        *,
        events: list | None = None,
        motivations: list | None = None,
    ) -> None:
        """记录一次快照。

        events: 本次 tick 发生的实验事件类型列表
        motivations: 本次评估到的主动动机列表
        """

        data = self._serialize(snapshot)

        if events:
            data["events"] = events

        if motivations:
            data["motivations"] = motivations

        with open(
            self.file,
            "a",
            encoding="utf-8",
        ) as f:
            f.write(
                json.dumps(
                    data,
                    ensure_ascii=False,
                )
                + "\n"
            )

        self._count += 1

    @staticmethod
    def _serialize(
        snapshot: dict,
    ) -> dict:
        """把 get_state() 快照转换为 JSON 可序列化结构。"""

        return {
            "time": snapshot["time"].isoformat(),
            "life": snapshot["life"],
            "emotion": snapshot["emotion"].as_dict(),
            "neurochemical": (
                snapshot["neurochemical"].as_dict()
            ),
            "relationship": snapshot["relationship"],
            "memory": snapshot["memory"],
        }

    @property
    def count(self) -> int:
        return self._count
