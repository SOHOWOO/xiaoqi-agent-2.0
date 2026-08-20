from __future__ import annotations

from datetime import datetime, timedelta

from .simulator import LifeSimulator
from .state import SimulationResult
from .time_engine import DEFAULT_TZ, ensure_aware


class LifeLoop:
    """小七持续生命循环的薄封装。

    LifeSimulator 负责真正的模拟逻辑，
    LifeLoop 负责持续运行和提供简单的 tick 接口。
    """

    def __init__(
        self,
        start_time: datetime,
        seed: int | None = None,
        schedule_config=None,
        tz=DEFAULT_TZ,
    ):
        self.tz = tz
        self.simulator = LifeSimulator(
            seed=seed,
            schedule_config=schedule_config,
            tz=tz,
        )

        self.current_time = ensure_aware(start_time, tz)

    def tick(self, duration: timedelta) -> SimulationResult:
        """让小七向前生活一段时间。"""

        if duration.total_seconds() <= 0:
            raise ValueError("tick duration must be positive")

        next_time = self.current_time + duration

        result = self.simulator.simulate(
            self.current_time,
            next_time,
        )

        self.current_time = next_time

        return result

    @property
    def life_state(self):
        """当前小七的生活状态。"""
        return self.simulator.life_state

    @property
    def interaction_state(self):
        """当前互动状态。"""
        return self.simulator.interaction_state
