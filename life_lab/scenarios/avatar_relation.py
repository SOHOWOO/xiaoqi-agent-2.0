from __future__ import annotations

from datetime import timedelta

from core.avatar import (
    AvatarController,
    CallbackAvatarBridge,
    expression_for,
)
from core.time_engine import make_aware


class AvatarRelationScenario:
    """实验 010：关系等级影响 Avatar 表现。

    高关系（持续陪伴）-> Avatar 更温暖积极；
    低关系（长期失联）-> Avatar 平淡 / 忧伤。
    对比两种轨迹的 Avatar 表现差异。
    """

    name = "avatar_relation"

    def start(self):
        return make_aware(2026, 8, 22, 8, 0)

    def seed(self) -> int:
        return 42

    def run(self, life, logger) -> list:
        # 阶段 A：7 天持续陪伴（高关系）
        high_bridge = CallbackAvatarBridge()
        high_controller = AvatarController(
            life.event_bus,
            bridge=high_bridge,
        )

        for _ in range(7 * 3):
            life.receive_event(
                {"type": "positive_interaction", "intensity": 1.0}
            )
            life.tick(timedelta(minutes=15))
            logger.record(life.get_state())

        high_events = [
            e.emotion.name
            for e in high_bridge.events
        ]

        # 阶段 B：7 天失联（低关系）
        low_bridge = CallbackAvatarBridge()
        low_controller = AvatarController(
            life.event_bus,
            bridge=low_bridge,
        )

        for _ in range(7 * 24 * 4):
            life.tick(timedelta(minutes=15))
            logger.record(life.get_state())

        low_events = [
            e.emotion.name
            for e in low_bridge.events
        ]

        return [
            {
                "phase": "high",
                "emotions": high_events,
                "expressions": [
                    expression_for(e) for e in high_events
                ],
            },
            {
                "phase": "low",
                "emotions": low_events,
                "expressions": [
                    expression_for(e) for e in low_events
                ],
            },
        ]

    def assess(self, records: list) -> dict:
        high = records[0]
        low = records[1]

        high_positive = any(
            e in ("happy", "excited")
            for e in high["emotions"]
        )
        low_quiet = any(
            e in ("lonely", "calm")
            for e in low["emotions"]
        )

        high_smile = any(
            x in ("smile", "big_smile")
            for x in high["expressions"]
        )

        return {
            "高关系有积极表现": high_positive,
            "低关系平淡或忧伤": low_quiet,
            "高关系出现微笑": high_smile,
        }
