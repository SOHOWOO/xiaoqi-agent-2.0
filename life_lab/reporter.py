from __future__ import annotations


class Reporter:
    """生成实验报告并判定 PASS / FAIL。"""

    _LABELS = {
        "completed": "完整跑完所有 Tick",
        "energy_in_range": "能量保持在 0~1",
        "energy_varies": "能量有动态变化",
        "emotion_varies": "情绪持续演化",
        "relationship_varies": "关系随时间合理变化",
        "relationship_valid": "关系数值有效（0~1）",
    }

    def report(
        self,
        metrics: dict,
        *,
        run_id: str,
        folder: str,
        name: str,
    ) -> bool:
        all_pass = all(
            metrics.get(key)
            for key in self._LABELS
        )

        lines = [
            "",
            "=" * 48,
            "小七生命实验报告",
            "=" * 48,
            f"实验：{name}",
            f"运行号：{run_id}",
            f"数据目录：{folder}",
            "",
            "健康检查：",
        ]

        for key, label in self._LABELS.items():
            status = "PASS" if metrics.get(key) else "FAIL"
            lines.append(
                f"  [{status}] {label}"
            )

        lines.append("")
        lines.append("结果：" + ("PASS" if all_pass else "FAIL"))
        lines.append("=" * 48)
        lines.append("")

        print("\n".join(lines))

        return all_pass
