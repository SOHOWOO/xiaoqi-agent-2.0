from __future__ import annotations

from datetime import timedelta

from core.time_engine import make_aware


class ProactiveTestScenario:
    """实验 004：主动动机能力。

    7 天无用户输入，制造失联内部状态（PROLONGED_ABSENCE 链路），
    每小时评估一次主动动机（只读 peek，不消耗冷却）。

    验证小七"不是只有输入才行动"——内在状态会驱动主动联系。
    """

    name = "proactive_test"

    def start(self):
        return make_aware(2026, 8, 22, 8, 0)

    def seed(self) -> int:
        return 42

    def run(self, life, logger) -> list:
        records = []

        for hour in range(24 * 7):
            life.tick(timedelta(hours=1))

            # 真实触发的主动消息（tick 内 evaluate 入队）
            proactive = life.get_pending_proactive_messages()

            # 当前可执行的主动动机（只读 peek，不消耗冷却）
            actions = life.get_actions()

            motivations = [
                action.signal.suggested_action
                for action in actions
            ]

            snapshot = life.get_state()
            logger.record(
                snapshot,
                motivations=motivations,
                events=[
                    message.source_interest_id
                    for message in proactive
                ],
            )
            records.append(
                {
                    "snapshot": snapshot,
                    "motivations": motivations,
                    "proactive": [
                        message.source_interest_id
                        for message in proactive
                    ],
                }
            )

        return records

    def assess(self, records: list) -> dict:
        # 收集实验期间真实触发的主动消息来源
        proactive_sources = {
            source
            for r in records
            for source in r["proactive"]
        }

        # 收集 peek 到的动机
        seen_motivations = set()
        for r in records:
            seen_motivations.update(r["motivations"])

        lonely_end = (
            records[-1]["snapshot"]["emotion"]
            .as_dict()["lonely"]
        )
        lonely_start = (
            records[0]["snapshot"]["emotion"]
            .as_dict()["lonely"]
        )

        return {
            "孤独累积": lonely_end > lonely_start,
            "产生主动动机": (
                len(seen_motivations) > 0
                or len(proactive_sources) > 0
            ),
            "出现联系动机": (
                "chat" in seen_motivations
                or any(
                    "craving_contact" in source
                    for source in proactive_sources
                )
            ),
            "动机有内在来源": (
                lonely_end > 0.6
            ),
        }
