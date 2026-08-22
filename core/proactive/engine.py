from __future__ import annotations

from typing import List

from .models import (
    ProactiveAction,
    ProactiveContext,
    ProactiveSignal,
)
from .scheduler import ProactiveGate
from .signals import (
    DiarySignalGenerator,
    EmotionSignalGenerator,
    MemorySignalGenerator,
    NeurochemicalSignalGenerator,
    TimeSignalGenerator,
)


class UnifiedProactiveEngine:
    """统一主动行为引擎（Proactive Engine 3.0）。

    多驱动器产生候选信号 → ProactiveGate 门控 → 排序选优 → 生成消息。

    驱动器：
    - 情绪（孤独/焦虑/兴奋）
    - 神经化学（依恋需求 + 久未互动）
    - 时间 / 作息（晚间长时间无互动）
    - 日记回顾
    - 记忆关注（重要事项冷却到期）

    对应计划书：Desire System + Proactive Engine，
    决定"什么时候主动找你"。
    """

    def __init__(
        self,
        generators: list | None = None,
        gate: ProactiveGate | None = None,
        max_actions: int = 1,
    ) -> None:
        self.generators = (
            generators
            if generators is not None
            else [
                EmotionSignalGenerator(),
                NeurochemicalSignalGenerator(),
                TimeSignalGenerator(),
                DiarySignalGenerator(),
                MemorySignalGenerator(),
            ]
        )

        self.gate = (
            gate
            if gate is not None
            else ProactiveGate()
        )

        self.max_actions = max_actions

    def evaluate(
        self,
        ctx: ProactiveContext,
    ) -> List[ProactiveAction]:
        """收集信号、门控、决策，返回要执行的主动行为。"""

        signals: List[ProactiveSignal] = []

        for generator in self.generators:
            for signal in generator.generate(ctx):
                if self.gate.decide(ctx, signal):
                    signals.append(signal)

        signals.sort(
            key=lambda s: s.score,
            reverse=True,
        )

        actions: List[ProactiveAction] = []

        for signal in signals[:self.max_actions]:
            actions.append(
                ProactiveAction(
                    signal=signal,
                    message=self._build_message(signal),
                )
            )
            self.gate.record_trigger(ctx.now)

        return actions

    def _build_message(
        self,
        signal: ProactiveSignal,
    ) -> str:
        action = signal.suggested_action
        payload = signal.payload

        if action == "chat":
            return "今天是不是有点忙？感觉你好久没出现了。"

        if action == "comfort":
            return "我看你最近压力好像有点大……要不要跟我聊聊？我一直都在。"

        if action == "remind":
            if payload:
                return (
                    f"我突然想到你之前提到的「{payload}」，"
                    "最近进展怎么样啦？"
                )
            return "你之前说的那件事，我有点挂念，最近怎么样啦？"

        if action == "share":
            if payload:
                return (
                    "我刚刚翻到昨天的记忆，想起一件开心的事："
                    f"{payload}"
                )
            return "我刚刚想到一些开心的事，想跟你分享一下。"

        if action == "play":
            return "要不要玩点什么放松一下？"

        return "我在想你呢。"
