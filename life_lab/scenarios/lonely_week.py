from __future__ import annotations

from datetime import timedelta

from core.time_engine import make_aware


class LonelyWeekScenario:
    """实验 001：7 天失联测试。

    小七独立运行 7 天，无用户输入 / 无语音 / 无 LLM / 无 Avatar，
    验证生命核心能否自洽、稳定地长期运行。
    """

    name = "lonely_week"

    def start(self):
        return make_aware(2026, 8, 22, 8, 0)

    def seed(self) -> int:
        return 42

    def tick_minutes(self) -> int:
        return 15

    def steps(self) -> int:
        return 7 * 24 * 4

    def run(self, life, logger) -> list:
        records = []

        for _ in range(self.steps()):
            life.tick(
                timedelta(minutes=self.tick_minutes())
            )

            snapshot = life.get_state()
            logger.record(snapshot)
            records.append(snapshot)

        return records

    def assess(self, records: list) -> dict:
        n = len(records)

        energies = [
            r["life"]["energy"] for r in records
        ]

        emotions = {
            tuple(sorted(r["emotion"].as_dict().items()))
            for r in records
        }

        return {
            "完整跑完所有 Tick": n == self.steps(),
            "能量保持在 0~1": all(
                0.0 <= e <= 1.0 for e in energies
            ),
            "能量有动态变化": (
                len({round(e, 6) for e in energies}) > 1
            ),
            "情绪持续演化": len(emotions) > 1,
            "关系随时间变化": (
                records[0]["relationship"]
                != records[-1]["relationship"]
            ),
            "关系数值有效": all(
                0.0 <= r["relationship"]["attachment"] <= 1.0
                for r in records
            ),
        }
