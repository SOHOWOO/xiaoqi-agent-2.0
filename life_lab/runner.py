from __future__ import annotations

import sys
from datetime import datetime

from core.life_loop import LifeLoop

from life_lab.logger import SimulationLogger
from life_lab.reporter import Reporter
from life_lab.scenarios import SCENARIOS


def run(scenario_id: str = "001") -> bool:
    """运行一次离线生命实验，返回 PASS / FAIL。

    scenario_id: 001(失联) / 002(成长) / 003(冲突) / 004(主动)
    """

    scenario_cls = SCENARIOS.get(scenario_id)

    if scenario_cls is None:
        raise ValueError(
            f"unknown scenario: {scenario_id!r} "
            f"(available: {', '.join(sorted(SCENARIOS))})"
        )

    scenario = scenario_cls()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    folder = f"logs/life_lab/{scenario_id}_{run_id}"

    logger = SimulationLogger(folder)

    # 隔离：始终使用内存版 LifeLoop，不触碰正常系统持久化数据。
    life = LifeLoop(
        start_time=scenario.start(),
        seed=scenario.seed(),
    )

    records = scenario.run(life, logger)

    checks = scenario.assess(records)

    return Reporter().report(
        checks,
        run_id=run_id,
        folder=folder,
        scenario=scenario,
    )


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]

    scenario_id = args[0] if args else "001"

    ok = run(scenario_id)

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
