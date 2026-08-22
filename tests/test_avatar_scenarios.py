from core.life_loop import LifeLoop
from life_lab.logger import SimulationLogger
from life_lab.scenarios.avatar_absence import (
    AvatarAbsenceScenario,
)
from life_lab.scenarios.avatar_consistency import (
    AvatarConsistencyScenario,
)
from life_lab.scenarios.avatar_relation import (
    AvatarRelationScenario,
)


def _life():
    return LifeLoop(
        start_time=AvatarConsistencyScenario().start(),
        seed=42,
    )


def _logger(tmp_path):
    return SimulationLogger(tmp_path / "exp")


def test_avatar_consistency(tmp_path):
    life = _life()
    scenario = AvatarConsistencyScenario()

    records = scenario.run(life, _logger(tmp_path))
    checks = scenario.assess(records)

    assert checks["Avatar 事件产生"] is True
    assert checks["Avatar 情绪跟随核心"] is True
    assert checks["正向互动提升快乐"] is True
    assert checks["积极表情出现"] is True


def test_avatar_absence(tmp_path):
    life = _life()
    scenario = AvatarAbsenceScenario()

    records = scenario.run(life, _logger(tmp_path))
    checks = scenario.assess(records)

    assert checks["孤独累积"] is True
    assert checks["Avatar 事件产生"] is True
    assert checks["失联表现忧伤"] is True


def test_avatar_relation(tmp_path):
    life = _life()
    scenario = AvatarRelationScenario()

    records = scenario.run(life, _logger(tmp_path))
    checks = scenario.assess(records)

    assert checks["高关系有积极表现"] is True
    assert checks["低关系平淡或忧伤"] is True
    assert checks["高关系出现微笑"] is True
