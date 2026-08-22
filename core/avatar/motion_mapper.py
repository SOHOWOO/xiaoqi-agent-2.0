from __future__ import annotations

from typing import Mapping

# 行为/动作 -> Avatar motion。
# idle/smile/wave/nod/thinking/comfort/excited 为第一版动作集；
# 主动行为（chat/comfort/share/remind/play）映射到对应动作。
ACTION_MOTIONS: Mapping[str, str] = {
    "idle": "idle",
    "smile": "smile",
    "wave": "wave",
    "nod": "nod",
    "thinking": "thinking",
    "comfort": "comfort",
    "excited": "excited",
    # 主动行为映射
    "chat": "wave",
    "comfort": "comfort",
    "share": "happy_idle",
    "remind": "nod",
    "play": "excited",
}

DEFAULT_MOTION = "idle"


def map_action(
    action_name: str,
) -> str:
    """把行为/动作名映射为 Avatar motion。"""

    return ACTION_MOTIONS.get(
        action_name,
        DEFAULT_MOTION,
    )
