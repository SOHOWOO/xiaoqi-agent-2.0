from life_lab.scenarios.avatar_absence import (
    AvatarAbsenceScenario,
)
from life_lab.scenarios.avatar_consistency import (
    AvatarConsistencyScenario,
)
from life_lab.scenarios.avatar_relation import (
    AvatarRelationScenario,
)
from life_lab.scenarios.conflict_recovery import (
    ConflictRecoveryScenario,
)
from life_lab.scenarios.happy_growth import (
    HappyGrowthScenario,
)
from life_lab.scenarios.lonely_week import (
    LonelyWeekScenario,
)
from life_lab.scenarios.proactive_test import (
    ProactiveTestScenario,
)

SCENARIOS = {
    "001": LonelyWeekScenario,
    "002": HappyGrowthScenario,
    "003": ConflictRecoveryScenario,
    "004": ProactiveTestScenario,
    "008": AvatarConsistencyScenario,
    "009": AvatarAbsenceScenario,
    "010": AvatarRelationScenario,
}

__all__ = [
    "SCENARIOS",
    "LonelyWeekScenario",
    "HappyGrowthScenario",
    "ConflictRecoveryScenario",
    "ProactiveTestScenario",
    "AvatarConsistencyScenario",
    "AvatarAbsenceScenario",
    "AvatarRelationScenario",
]
