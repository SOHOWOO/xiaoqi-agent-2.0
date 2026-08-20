from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from docx import Document

from .models import MemoryRecord, MemorySource, MemoryType
from .store import MemoryStore


class CanonicalMemoryImporter:
    """将用户提供的 DOCX 真实记忆导入 Memory Core。"""

    def __init__(self, store: MemoryStore):
        self.store = store

    def import_file(self, path: str | Path) -> list[MemoryRecord]:
        """导入一个 DOCX 文件。"""

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if path.suffix.lower() != ".docx":
            raise ValueError("canonical memory source must be a .docx file")

        document = Document(path)

        records: list[MemoryRecord] = []

        for index, paragraph in enumerate(document.paragraphs, start=1):
            text = paragraph.text.strip()

            if not text:
                continue

            parsed = self._parse_field(text)

            if parsed is None:
                continue

            field_name, value = parsed

            # NEEDS_REVIEW 代表待确认信息，不能作为已确认事实导入。
            if "NEEDS_REVIEW" in value:
                continue

            record = MemoryRecord(
                memory_id=self._make_memory_id(path, index),
                memory_type=MemoryType.CANONICAL,
                content=f"{field_name}：{value}",
                created_at=datetime.now(timezone.utc),
                source=MemorySource.USER_PROVIDED,
                importance=1.0,
                confidence=1.0,
            )

            existing = self.store.get(record.memory_id)

            if existing is not None:
                continue

            self.store.add(record)
            records.append(record)

        return records

    def import_files(
        self,
        paths: Iterable[str | Path],
    ) -> list[MemoryRecord]:
        """批量导入多个 DOCX 文件。"""

        records: list[MemoryRecord] = []

        for path in paths:
            records.extend(self.import_file(path))

        return records

    @staticmethod
    def _parse_field(text: str) -> tuple[str, str] | None:
        """解析“字段：内容”格式。"""

        if "：" not in text:
            return None

        field_name, value = text.split("：", 1)

        field_name = field_name.strip()
        value = value.strip()

        if not field_name or not value:
            return None

        return field_name, value

    @staticmethod
    def _make_memory_id(
        path: Path,
        paragraph_index: int,
    ) -> str:
        """生成稳定的真实记忆 ID。"""

        return (
            f"canonical:"
            f"{path.stem}:"
            f"paragraph:{paragraph_index}"
        )