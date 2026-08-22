from __future__ import annotations

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, List, Optional


# ============================================================
# Open-LLM-VTuber 协议类型（协议对齐层）
#
# 与 Open-LLM-VTuber 的 input_types / output_types 保持一致，
# 但不依赖 OLV 包本身 —— 由 XiaoqiAgent 实现其 AgentInterface。
# 真实接入时，类型签名与 OLV 完全兼容，可直接替换。
# ============================================================


class ImageSource(str, Enum):
    CAMERA = "camera"
    SCREEN = "screen"
    CLIPBOARD = "clipboard"
    UPLOAD = "upload"


class TextSource(str, Enum):
    INPUT = "input"
    CLIPBOARD = "clipboard"


@dataclass
class ImageData:
    source: ImageSource
    data: str
    mime_type: str


@dataclass
class FileData:
    name: str
    data: str
    mime_type: str


@dataclass
class TextData:
    source: TextSource
    content: str
    from_name: Optional[str] = None


class BaseInput:
    pass


@dataclass
class BatchInput(BaseInput):
    """一次批处理输入。

    metadata 支持：
      - proactive_speak: 是否为主动说话输入
      - skip_memory / skip_history: 是否跳过记忆 / 本地历史
    """

    texts: List[TextData]
    images: Optional[List[ImageData]] = None
    files: Optional[List[FileData]] = None
    metadata: Optional[dict] = None


class BaseOutput:
    def __aiter__(self):
        raise NotImplementedError


@dataclass
class Actions:
    """与文本输出同时下发的动作（表情 / 图片 / 音效）。"""

    expressions: Optional[List[str]] = None
    pictures: Optional[List[str]] = None
    sounds: Optional[List[str]] = None

    def to_dict(self) -> dict:
        return {
            k: v
            for k, v in asdict(self).items()
            if v is not None
        }


@dataclass
class DisplayText:
    text: str
    name: Optional[str] = "AI"
    avatar: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "name": self.name,
            "avatar": self.avatar,
        }


@dataclass
class SentenceOutput(BaseOutput):
    """文本型输出：展示文本 + TTS 文本 + 动作。"""

    display_text: DisplayText
    tts_text: str
    actions: Actions

    async def __aiter__(self):
        yield self.display_text, self.tts_text, self.actions


@dataclass
class AudioOutput(BaseOutput):
    """音频型输出：音频路径 + 展示文本 + 转写 + 动作。"""

    audio_path: str
    display_text: DisplayText
    transcript: str
    actions: Actions

    async def __aiter__(self):
        yield self.audio_path, self.display_text, self.transcript, self.actions
