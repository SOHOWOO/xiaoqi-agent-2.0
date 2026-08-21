from __future__ import annotations

from .models import PersonalityProfile


class PersonalityEngine:
    """人格系统核心。"""

    def __init__(
        self,
        profile: PersonalityProfile,
    ):
        self.profile = profile

    def build_context(self) -> str:
        p = self.profile

        return "\n".join(
            [
                "【人格设定】",
                f"你是{p.name}",
                f"名字：{p.name}",
                f"身份：{p.identity}",
                "性格：" + "、".join(p.traits),
                "说话方式：" + "、".join(
                    p.speaking_style
                ),
                "价值观：" + "、".join(
                    p.values
                ),
            ]
        )
