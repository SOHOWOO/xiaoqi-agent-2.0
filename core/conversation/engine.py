from __future__ import annotations

from .models import ConversationState


class ConversationEngine:
    """管理当前聊天上下文。"""

    def __init__(
        self,
        state: ConversationState | None = None,
    ):
        self.state = (
            state
            if state is not None
            else ConversationState()
        )


    def observe(
        self,
        message: str,
    ) -> None:
        """观察用户输入并更新状态。"""

        self.state.add_message(
            message
        )

        text = message.lower()

        if any(
            word in text
            for word in [
                "难过",
                "伤心",
                "累",
                "压力",
            ]
        ):
            self.state.user_emotion = "negative"

        elif any(
            word in text
            for word in [
                "开心",
                "高兴",
                "哈哈",
            ]
        ):
            self.state.user_emotion = "positive"


    def build_context(self) -> str:
        s = self.state

        return "\n".join(
            [
                "【当前对话状态】",
                f"话题：{s.topic or '未知'}",
                f"用户情绪：{s.user_emotion}",
                f"对话轮数：{s.turn_count}",
            ]
        )
