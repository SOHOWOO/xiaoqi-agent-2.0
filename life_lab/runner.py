from __future__ import annotations

from datetime import datetime, timedelta

from core.life_loop import LifeLoop

from life_lab.logger import SimulationLogger
from life_lab.metrics import HealthMetrics
from life_lab.reporter import Reporter
from life_lab.scenarios.lonely_week import LonelyWeekScenario


def run() -> bool:
    """运行一次离线生命实验，返回 PASS / FAIL。"""

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    folder = f"logs/life_lab/{run_id}"

    logger = SimulationLogger(folder)

    scenario = LonelyWeekScenario()

    steps = scenario.steps()

    life = LifeLoop(
        start_time=scenario.start(),
        seed=scenario.seed(),
    )

    records = []

    for _ in range(steps):
        scenario.step(life)

        life.tick(
            timedelta(minutes=scenario.tick_minutes())
        )

        snapshot = life.get_state()

        logger.record(snapshot)
        records.append(snapshot)

    metrics = HealthMetrics().check(
        records,
        expected_steps=steps,
    )

    return Reporter().report(
        metrics,
        run_id=run_id,
        folder=folder,
        name=scenario.name,
    )


if __name__ == "__main__":
    ok = run()
    raise SystemExit(0 if ok else 1)
