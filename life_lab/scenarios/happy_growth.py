from __future__ import annotations

from datetime import timedelta

from core.time_engine import make_aware


class HappyGrowthScenario:
    """实验 002：关系建立能力。

    模拟持续陪伴：7 天，每天 10 次正向互动。
    验证关系（attachment/trust）随互动成长，但不异常封顶。
    """

    name = "happy_growth"

    INTERACTIONS_PER_DAY = 10
    DAYS = 7

    def start(self):
        return make_aware(2026, 8, 22, 8, 0)

    def seed(self) -> int:
        return 42

    def run(self, life, logger) -> list:
        records = []

        for day in range(self.DAYS):
            for i in range(self.INTERACTIONS_PER_DAY):
                life.receive_event(
                    {
                        "type": "positive_interaction",
                        "intensity": 1.0,
                        "message": "今天陪小七学习",
                    }
                )

                life.tick(timedelta(minutes=15))

                snapshot = life.get_state()
                logger.record(
                    snapshot,
                    events=["positive_interaction"],
                )
                records.append(snapshot)

            life.tick(timedelta(hours=23))

            snapshot = life.get_state()
            logger.record(snapshot)
            records.append(snapshot)

        return records

    def assess(self, records: list) -> dict:
        first = records[0]
        last = records[-1]

        attachment_0 = first["relationship"]["attachment"]
        attachment_N = last["relationship"]["attachment"]
        trust_0 = first["relationship"]["trust"]
        trust_N = last["relationship"]["trust"]

        return {
            "关系成长": (
                attachment_N > attachment_0
                and trust_N > trust_0
            ),
            "关系未封顶": (
                attachment_N < 1.0
                and trust_N < 1.0
            ),
            "情绪积极": (
                last["emotion"].as_dict()["happy"]
                > first["emotion"].as_dict()["happy"]
            ),
            "记忆沉淀": (
                last["memory"]["count"] > 0
            ),
        }
