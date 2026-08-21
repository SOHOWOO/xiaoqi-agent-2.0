from __future__ import annotations

from .models import RelationshipState


class RelationshipEngine:
    """用户关系成长系统。"""

    def __init__(
        self,
        state: RelationshipState | None = None,
    ):
        self.state = (
            state
            if state is not None
            else RelationshipState()
        )


    def interact(self):
        self.state.update()


    def build_context(self) -> str:
        s = self.state

        return "\n".join(
            [
                "【关系状态】",
                f"互动次数：{s.interaction_count}",
                f"熟悉度：{s.familiarity:.2f}",
                f"亲密度：{s.intimacy:.2f}",
                f"关系阶段：{s.stage}",
            ]
        )
