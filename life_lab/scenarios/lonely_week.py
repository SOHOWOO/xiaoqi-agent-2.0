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

    def duration(self) -> timedelta:
        return timedelta(days=7)

    def tick_minutes(self) -> int:
        return 15

    def seed(self) -> int:
        return 42

    def steps(self) -> int:
        seconds = self.duration().total_seconds()
        return int(seconds / (self.tick_minutes() * 60))

    def step(self, life) -> None:
        """无用户输入，保持安静环境。"""
        return None
