from __future__ import annotations

from datetime import timedelta

from core.avatar import (
    AvatarController,
    CallbackAvatarBridge,
    expression_for,
)
from core.time_engine import make_aware


class AvatarAbsenceScenario:
    """实验 009：失联下的 Avatar 表现。

    7 天无互动 -> 核心 lonely 上升 -> Avatar 表现为安静 / 忧伤。
    """

    name = "avatar_absence"

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

        for _ in range(7 * 24 * 4):
            life.tick(timedelta(minutes=15))

            snapshot = life.get_state()
            logger.record(snapshot)

            records.append(
                {
                    "snapshot": snapshot,
                    "avatar": controller.last_event,
                }
            )

        return records

    def assess(self, records: list) -> dict:
        lonely_first = records[0]["snapshot"]["emotion"].lonely
        lonely_last = records[-1]["snapshot"]["emotion"].lonely

        avatar_events = [
            r["avatar"] for r in records if r["avatar"]
        ]

        # 失联后期 Avatar 应为忧伤 / 安静表现
        late_avatars = [
            e for e in avatar_events[len(avatar_events) // 2:]
        ]

        quiet_expressions = {
            expression_for(e.emotion.name)
            for e in late_avatars
        }

        return {
            "孤独累积": lonely_last > lonely_first,
            "Avatar 事件产生": len(avatar_events) > 0,
            "失联表现忧伤": bool(
                quiet_expressions
                & {"soft_sad", "quiet_idle", "worried"}
            ),
        }
