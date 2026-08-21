from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RelationshipState:
    """小七与用户的关系状态。"""

    interaction_count: int = 0

    familiarity: float = 0.0

    intimacy: float = 0.0

    stage: str = "陌生"


    def update(self):
        self.interaction_count += 1

        self.familiarity = min(
            1.0,
            self.familiarity + 0.01,
        )

        self.intimacy = min(
            1.0,
            self.intimacy + 0.005,
        )

        if self.familiarity > 0.7:
            self.stage = "熟悉"

        elif self.familiarity > 0.3:
            self.stage = "认识"

        else:
            self.stage = "陌生"
