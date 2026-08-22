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
}

__all__ = [
    "SCENARIOS",
    "LonelyWeekScenario",
    "HappyGrowthScenario",
    "ConflictRecoveryScenario",
    "ProactiveTestScenario",
]
