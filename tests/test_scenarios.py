from datetime import timedelta

from core.life_loop import LifeLoop
from life_lab.logger import SimulationLogger
from life_lab.scenarios.conflict_recovery import (
    ConflictRecoveryScenario,
)
from life_lab.scenarios.happy_growth import (
    HappyGrowthScenario,
)
from life_lab.scenarios.proactive_test import (
    ProactiveTestScenario,
)


def _life():
    return LifeLoop(
        start_time=HappyGrowthScenario().start(),
        seed=42,
    )


def _logger(tmp_path):
    return SimulationLogger(tmp_path / "exp")


# ---------------------------------------------------------
# 002 关系建立
# ---------------------------------------------------------


def test_happy_growth_grows_relationship(tmp_path):
    life = _life()
    scenario = HappyGrowthScenario()

    records = scenario.run(life, _logger(tmp_path))

    checks = scenario.assess(records)

    assert checks["关系成长"] is True
    assert checks["关系未封顶"] is True
    assert checks["记忆沉淀"] is True


def test_happy_growth_does_not_saturate_relationship(tmp_path):
    life = _life()
    scenario = HappyGrowthScenario()

    records = scenario.run(life, _logger(tmp_path))

    final = records[-1]["relationship"]
    assert final["attachment"] < 1.0
    assert final["trust"] < 1.0


# ---------------------------------------------------------
# 003 关系恢复
# ---------------------------------------------------------


def test_conflict_recovery_dips_and_recovers(tmp_path):
    life = _life()
    scenario = ConflictRecoveryScenario()

    records = scenario.run(life, _logger(tmp_path))

    checks = scenario.assess(records)

    assert checks["冲突削弱信任"] is True
    assert checks["冲突引发情绪"] is True
    assert checks["恢复重建信任"] is True


def test_conflict_records_diary_and_memory(tmp_path):
    life = _life()
    scenario = ConflictRecoveryScenario()

    scenario.run(life, _logger(tmp_path))

    assert life.diary.entries()  # 跨天应产生日记
    assert len(life.memory_store) > 0


# ---------------------------------------------------------
# 004 主动动机
# ---------------------------------------------------------


def test_proactive_test_produces_contact_motivation(tmp_path):
    life = _life()
    scenario = ProactiveTestScenario()

    records = scenario.run(life, _logger(tmp_path))

    checks = scenario.assess(records)

    assert checks["孤独累积"] is True
    assert checks["产生主动动机"] is True
    assert checks["出现联系动机"] is True


def test_proactive_peek_does_not_consume_gate(tmp_path):
    """实验 004 每小时 peek 不应干扰真实主动触发。"""

    life = _life()
    scenario = ProactiveTestScenario()

    records = scenario.run(life, _logger(tmp_path))

    # peek 不产生 pending 消息；真实触发走 tick 内部 evaluate
    assert all(r["motivations"] is not None for r in records)
