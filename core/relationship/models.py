from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RelationshipState:
    """小七与用户的多维关系状态。

    由互动频率、共同经历、互助事件、时间距离共同驱动，
    而非机械线性计数。
    """

    trust: float = 0.2
    attachment: float = 0.2
    familiarity: float = 0.0
    shared_experience: float = 0.0
    interaction_count: int = 0
    last_interaction_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        for name in (
            "trust",
            "attachment",
            "familiarity",
            "shared_experience",
        ):
            value = getattr(self, name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0.0 and 1.0"
                )

    @property
    def intimacy(self) -> float:
        """综合亲密度：依恋 + 熟悉 + 共同经历的加权。"""

        return min(
            1.0,
            0.5 * self.attachment
            + 0.3 * self.familiarity
            + 0.2 * self.shared_experience,
        )

    @property
    def stage(self) -> str:
        """关系阶段（由综合亲密派生）。"""

        score = self.intimacy

        if score >= 0.85:
            return "亲密"

        if score >= 0.60:
            return "熟悉"

        if score >= 0.30:
            return "认识"

        return "陌生"

    def as_dict(self) -> dict:
        """序列化用于持久化。"""

        return {
            "trust": round(self.trust, 6),
            "attachment": round(self.attachment, 6),
            "familiarity": round(self.familiarity, 6),
            "shared_experience": round(
                self.shared_experience, 6
            ),
            "interaction_count": self.interaction_count,
            "last_interaction_at": (
                self.last_interaction_at.isoformat()
                if self.last_interaction_at is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RelationshipState":
        """从持久化数据恢复。"""

        last_raw = data.get("last_interaction_at")

        return cls(
            trust=float(data.get("trust", 0.2)),
            attachment=float(data.get("attachment", 0.2)),
            familiarity=float(data.get("familiarity", 0.0)),
            shared_experience=float(
                data.get("shared_experience", 0.0)
            ),
            interaction_count=int(
                data.get("interaction_count", 0)
            ),
            last_interaction_at=(
                datetime.fromisoformat(last_raw)
                if last_raw
                else None
            ),
        )
