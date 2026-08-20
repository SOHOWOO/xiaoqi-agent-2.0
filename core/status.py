from __future__ import annotations

from dataclasses import dataclass

from .state import LifeState


@dataclass(frozen=True)
class LifeStatus:
    """小七当前生活状态的可读摘要。"""

    current_time: str | None
    slot_id: str | None
    activity: str | None
    fatigue: float
    energy: float

    @property
    def condition(self) -> str:
        """根据精力和疲劳给出简单状态。"""
        if self.energy <= 0.2:
            return "非常疲惫"
        if self.fatigue >= 0.8:
            return "疲劳"
        if self.energy >= 0.8:
            return "精力充沛"
        return "正常"


def build_life_status(state: LifeState) -> LifeStatus:
    """把内部 LifeState 转换成稳定、只读的状态摘要。"""

    return LifeStatus(
        current_time=(
            state.current_time.isoformat()
            if state.current_time is not None
            else None
        ),
        slot_id=state.current_slot_id,
        activity=state.current_activity,
        fatigue=round(state.fatigue, 6),
        energy=round(state.energy, 6),
    )


def format_life_status(status: LifeStatus) -> str:
    """生成给人看的简洁状态文本。"""

    if status.activity:
        activity = status.activity
    else:
        activity = "未知"

    if status.current_time:
        current_time = status.current_time
    else:
        current_time = "未知"

    return (
        f"小七现在正在「{activity}」。\n"
        f"时间：{current_time}\n"
        f"疲劳度：{status.fatigue:.2f}\n"
        f"精力：{status.energy:.2f}\n"
        f"状态：{status.condition}"
    )
