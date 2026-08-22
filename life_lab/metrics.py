from __future__ import annotations

from typing import List


def _freeze(data: dict) -> tuple:
    return tuple(sorted(data.items()))


class HealthMetrics:
    """生命健康检查。

    基于实验记录（get_state 快照列表）判定各项健康指标。
    """

    def check(
        self,
        records: List[dict],
        expected_steps: int,
    ) -> dict:
        result: dict = {}

        # 1. 是否完整跑完
        result["completed"] = (
            len(records) == expected_steps
        )

        # 2. 能量范围
        energies = [
            record["life"]["energy"]
            for record in records
        ]

        result["energy_in_range"] = all(
            0.0 <= e <= 1.0 for e in energies
        )

        result["energy_varies"] = (
            len({round(e, 6) for e in energies}) > 1
        )

        # 3. 情绪是否持续演化
        emotions = [
            _freeze(record["emotion"].as_dict())
            for record in records
        ]

        result["emotion_varies"] = (
            len(set(emotions)) > 1
        )

        # 4. 关系是否合理变化（首末不同且数值有效）
        relationships = [
            record["relationship"]
            for record in records
        ]

        result["relationship_varies"] = (
            relationships[0] != relationships[-1]
        )

        result["relationship_valid"] = all(
            0.0 <= r["attachment"] <= 1.0
            and 0.0 <= r["trust"] <= 1.0
            for r in relationships
        )

        return result
