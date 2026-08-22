from __future__ import annotations


class UnityWebSocketBridge:
    """
    Unity实时通信桥。

    后续：
    Python
       |
    WebSocket
       |
    Unity Avatar
    """

    def __init__(
        self,
        url: str = "ws://localhost:9000",
    ):
        self.url = url


    def send(
        self,
        event: dict,
    ):
        """
        发送角色事件。
        """

        return {
            "sent": True,
            "event": event,
        }
