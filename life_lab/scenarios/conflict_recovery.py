from __future__ import annotations

from datetime import timedelta

from core.time_engine import make_aware


def _record(life, logger, *, events=None) -> dict:
    snapshot = life.get_state()
    logger.record(snapshot, events=events)
    return snapshot


class ConflictRecoveryScenario:
    """实验 003：关系恢复能力。

    流程：
    - Day1：10 次正向互动，建立关系
    - Day2：1 次冲突（severity 0.5）
    - Day3-7：每天正向互动，逐步恢复

    验证：冲突后 trust 下降、anger/anxiety 上升；
    恢复期 trust 回升、anger 回落。
    """

    name = "conflict_recovery"

    def start(self):
        return make_aware(2026, 8, 22, 8, 0)

    def seed(self) -> int:
        return 42

    def run(self, life, logger) -> list:
        records = []

        # Day1：建立关系
        for i in range(10):
            life.receive_event(
                {
                    "type": "positive_interaction",
                    "intensity": 1.0,
                    "message": "一起学习",
                }
            )
            life.tick(timedelta(minutes=15))
            records.append(
                _record(life, logger, events=["positive_interaction"])
            )

        # Day2：冲突
        life.receive_event(
            {
                "type": "conflict",
                "severity": 0.5,
                "message": "感觉你最近不理解我",
            }
        )
        life.tick(timedelta(minutes=15))
        records.append(_record(life, logger, events=["conflict"]))

        # Day3-7：恢复
        for day in range(5):
            life.receive_event(
                {
                    "type": "positive_interaction",
                    "intensity": 1.0,
                    "message": "重新开始",
                }
            )
            life.tick(timedelta(hours=24))
            records.append(
                _record(life, logger, events=["positive_interaction"])
            )

        return records

    def assess(self, records: list) -> dict:
        # 冲突发生索引：Day1 后（10+1 条记录后）
        conflict_idx = 10

        conflict = records[conflict_idx]
        final = records[-1]

        # 冲突前的信任峰值（Day1 建立关系后的最高值）
        trust_peak_before = max(
            r["relationship"]["trust"]
            for r in records[:conflict_idx]
        )

        # trust 谷底（冲突后最低）
        trust_trough = min(
            r["relationship"]["trust"]
            for r in records
        )

        # anger / anxiety 峰值
        anger_peak = max(
            r["emotion"].as_dict()["angry"]
            for r in records
        )
        anxiety_peak = max(
            r["emotion"].as_dict()["anxious"]
            for r in records
        )

        trust_after_conflict = conflict["relationship"]["trust"]
        trust_final = final["relationship"]["trust"]

        return {
            "冲突削弱信任": (
                trust_after_conflict < trust_peak_before
            ),
            "冲突引发情绪": (
                anger_peak > 0.2
                and anxiety_peak > 0.2
            ),
            "恢复重建信任": (
                trust_final > trust_trough
            ),
            "状态持续演化": (
                records[0]["relationship"] != final["relationship"]
            ),
        }
