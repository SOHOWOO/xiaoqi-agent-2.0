from __future__ import annotations

from typing import List

from ..motivation import ActionPlanner, MotivationEngine
from .models import (
    ProactiveAction,
    ProactiveContext,
    ProactiveSignal,
)
from .scheduler import ProactiveGate


class UnifiedProactiveEngine:
    """统一主动行为引擎（Proactive Engine 3.0）。

    决策链路：
        State -> Motivation(Desire) -> Action Planner -> Proactive

    - MotivationEngine：从神经化学 / 情绪 / 关系 / 记忆 / 作息提炼
      高阶动机（渴望联系 / 想安慰 / 想分享 / 想提醒 / 想玩耍）
    - ActionPlanner：动机 -> 候选信号
    - ProactiveGate：冷却 / 睡眠 / 精力保护门控
    - 排序选优，生成最终主动消息
    """

    def __init__(
        self,
        motivation_engine: MotivationEngine | None = None,
        planner: ActionPlanner | None = None,
        gate: ProactiveGate | None = None,
        max_actions: int = 1,
    ) -> None:
        self.motivation_engine = (
            motivation_engine
            if motivation_engine is not None
            else MotivationEngine()
        )

        self.planner = (
            planner
            if planner is not None
            else ActionPlanner()
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
        """提炼动机、规划、门控、决策，返回要执行的主动行为。"""

        motivations = self.motivation_engine.evaluate(ctx)

        signals: List[ProactiveSignal] = []

        for signal in self.planner.plan(motivations, ctx):
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
