from __future__ import annotations

from pathlib import Path

_EXPERIMENT_NAMES = {
    "lonely_week": "实验 001：7 天失联",
    "happy_growth": "实验 002：关系建立",
    "conflict_recovery": "实验 003：关系恢复",
    "proactive_test": "实验 004：主动动机",
}


class Reporter:
    """生成实验报告（控制台 + summary.md）。"""

    def report(
        self,
        checks: dict,
        *,
        run_id: str,
        folder: str,
        scenario,
    ) -> bool:
        all_pass = all(checks.values())

        title = _EXPERIMENT_NAMES.get(
            scenario.name,
            f"实验：{scenario.name}",
        )

        lines = [
            "=" * 48,
            "小七生命实验报告",
            "=" * 48,
            f"{title}",
            f"运行号：{run_id}",
            f"数据目录：{folder}",
            "",
            "健康检查：",
        ]

        for label, ok in checks.items():
            status = "PASS" if ok else "FAIL"
            lines.append(f"  [{status}] {label}")

        lines.append("")
        lines.append(f"结果：{'PASS' if all_pass else 'FAIL'}")
        lines.append("=" * 48)

        print("\n".join(lines))

        self._write_summary(
            folder,
            title=title,
            run_id=run_id,
            checks=checks,
            all_pass=all_pass,
        )

        return all_pass

    @staticmethod
    def _write_summary(
        folder: str,
        *,
        title: str,
        run_id: str,
        checks: dict,
        all_pass: bool,
    ) -> None:
        """写 summary.md。"""

        lines = [
            f"# {title}",
            "",
            f"- 运行号：{run_id}",
            f"- 数据目录：`{folder}`",
            "",
            "## 健康检查",
            "",
        ]

        for label, ok in checks.items():
            lines.append(
                f"- [{'x' if ok else ' '}] {label}"
            )

        lines.append("")
        lines.append(f"## 结果：{'PASS' if all_pass else 'FAIL'}")
        lines.append("")

        out = Path(folder) / "summary.md"
        out.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )
