from __future__ import annotations

from datetime import timedelta

from core.avatar import (
    AvatarController,
    CallbackAvatarBridge,
    expression_for,
)
from core.time_engine import make_aware


class AvatarConsistencyScenario:
    """实验 008：情绪表现一致性。

    输入正向互动 -> 核心 happy 上升 -> Avatar 表现为 smile。
    验证内部状态与外部表达一致（Avatar 不是大脑，只是表达）。
    """

    name = "avatar_consistency"

    def start(self):
        return make_aware(2026, 8, 22, 8, 0)

    def seed(self) -> int:
        return 42

    def run(self, life, logger) -> list:
        bridge = CallbackAvatarBridge()
        controller = AvatarController(
            life.event_bus,
            bridge=bridge,
        )

        records = []

        for _ in range(10):
            life.receive_event(
                {
                    "type": "positive_interaction",
                    "intensity": 1.0,
                    "message": "陪小七学习",
                }
            )
            life.tick(timedelta(minutes=15))

            snapshot = life.get_state()
            logger.record(
                snapshot,
                events=["positive_interaction"],
            )
            records.append(
                {
                    "snapshot": snapshot,
                    "avatar": controller.last_event,
                }
            )

        return records

    def assess(self, records: list) -> dict:
        avatar_events = [
            r["avatar"] for r in records if r["avatar"]
        ]

        # 一致性：Avatar 情绪名应等于核心主导情绪
        consistent = all(
            r["avatar"].emotion.name
            == r["snapshot"]["emotion"].dominant().value
            for r in records
            if r["avatar"] is not None
        )

        # 正向互动应让核心情绪朝 happy 移动
        happy_first = records[0]["snapshot"]["emotion"].happy
        happy_last = records[-1]["snapshot"]["emotion"].happy

        return {
            "Avatar 事件产生": len(avatar_events) > 0,
            "Avatar 情绪跟随核心": consistent,
            "正向互动提升快乐": happy_last > happy_first,
            "积极表情出现": any(
                expression_for(e.emotion.name)
                in ("smile", "big_smile")
                for e in avatar_events
            ),
        }
