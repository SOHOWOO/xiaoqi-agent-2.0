from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, List


class EventBus:
    """非阻塞内存事件总线（xiaoqi-bus）。

    发布-订阅模型。订阅者异常不影响主线程；为阶段 2/3
    对接 Open-LLM-VTuber / Soul-of-Waifu 提供解耦通道。
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, List[Callable]] = defaultdict(list)

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[dict | None], None],
    ) -> Callable[[], None]:
        """订阅事件，返回取消订阅函数。"""

        self._subscribers[event_type].append(callback)

        def unsubscribe() -> None:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

        return unsubscribe

    def publish(
        self,
        event_type: str,
        data: dict | None = None,
    ) -> None:
        """发布事件（非阻塞，捕获订阅者异常）。"""

        for callback in list(
            self._subscribers.get(event_type, [])
        ):
            try:
                callback(data)
            except Exception:
                # 订阅者故障不能影响生命主循环。
                continue

    def subscriber_count(
        self,
        event_type: str,
    ) -> int:
        return len(self._subscribers.get(event_type, []))

    def clear(self) -> None:
        self._subscribers.clear()
