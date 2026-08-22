from __future__ import annotations

from datetime import date
from typing import Iterable, List, Protocol


class DiaryLLMProvider(Protocol):
    """可选的日记撰写 LLM 接口。"""

    def generate(self, prompt: str) -> str:
        ...


class DiaryWriter:
    """日记撰写器。

    默认使用确定性模板生成第一人称日记；
    若注入 DiaryLLMProvider，则交由 LLM 生成更自然的文本。
    """

    def __init__(
        self,
        llm_provider: DiaryLLMProvider | None = None,
    ) -> None:
        self._llm = llm_provider

    def write(
        self,
        *,
        date: date,
        events: Iterable[str],
        dominant_emotion: str,
        mood_tags: Iterable[str],
        energy: float | None = None,
    ) -> str:
        """生成一篇日记文本。"""

        if self._llm is not None:
            return self._write_with_llm(
                date=date,
                events=list(events),
                dominant_emotion=dominant_emotion,
                mood_tags=list(mood_tags),
                energy=energy,
            )

        return self._write_template(
            date=date,
            events=list(events),
            dominant_emotion=dominant_emotion,
            mood_tags=list(mood_tags),
            energy=energy,
        )

    def _write_template(
        self,
        *,
        date: date,
        events: List[str],
        dominant_emotion: str,
        mood_tags: List[str],
        energy: float | None,
    ) -> str:
        lines: List[str] = [
            f"今天（{date.isoformat()}）"
        ]

        if events:
            lines.append(
                "我经历了这些事：" + "、".join(events)
            )
        else:
            lines.append("今天比较平静，没什么特别的事。")

        if mood_tags:
            lines.append(
                "今天的心情偏向："
                + "、".join(mood_tags)
            )
        else:
            lines.append(
                f"今天的心情偏向「{dominant_emotion}」。"
            )

        if energy is not None:
            if energy >= 0.6:
                energy_text = "精力还不错"
            elif energy >= 0.35:
                energy_text = "精力一般"
            else:
                energy_text = "有点累"

            lines.append(f"{energy_text}。")

        return "\n".join(lines)

    def _write_with_llm(
        self,
        *,
        date: date,
        events: List[str],
        dominant_emotion: str,
        mood_tags: List[str],
        energy: float | None,
    ) -> str:
        assert self._llm is not None

        prompt = (
            "你是小七，一位陪伴型 AI 生命体。请用第一人称写一篇今天的日记，"
            f"日期是 {date.isoformat()}。\n"
            f"今天发生的事：{'；'.join(events) or '没有特别的事'}。\n"
            f"今天的主导情绪：{dominant_emotion}（{ '、'.join(mood_tags) }）。\n"
            f"精力水平：{energy if energy is not None else '未知'}。\n"
            "请以「今天」开头，写 3 到 5 句话。"
        )

        return self._llm.generate(prompt)
