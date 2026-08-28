"""小七 · 语音引擎（STT / TTS）

所有引擎均为可选依赖：
- faster-whisper 未安装 -> STT unavailable
- CosyVoice 未安装 -> TTS unavailable

未安装时明确标记，不伪造可用。
"""

from __future__ import annotations

import io
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    import faster_whisper  # type: ignore

    _HAS_WHISPER = True
except ImportError:
    _HAS_WHISPER = False

try:
    import cosyvoice  # type: ignore

    _HAS_COSYVOICE = True
except ImportError:
    _HAS_COSYVOICE = False


_WHISPER_MODEL_SIZE = os.getenv("XIAOQI_STT_MODEL", "base")
_COSYVOICE_MODEL_DIR = os.getenv(
    "XIAOQI_COSYVOICE_MODEL_DIR",
    "",
)


@dataclass(frozen=True)
class EngineStatus:
    engine: str
    available: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "engine": self.engine,
            "available": self.available,
            "detail": self.detail,
        }


class STTEngine:
    """语音识别引擎（faster-whisper 或 unavailable）。

    模型惰性加载：仅在 transcribe 时初始化，避免 status/init 卡顿。
    """

    engine_name = "faster-whisper"

    def __init__(self) -> None:
        self._model = None
        self._load_error = ""

    def _ensure_model(self):
        """首次使用时加载模型（含 HF 下载）。"""

        if self._model is not None or self._load_error:
            return

        if not _HAS_WHISPER:
            self._load_error = "faster-whisper 未安装"
            return

        try:
            self._model = faster_whisper.WhisperModel(
                _WHISPER_MODEL_SIZE,
                device="cpu",
                compute_type="int8",
            )
        except Exception as exc:
            self._load_error = str(exc)

    @property
    def available(self) -> bool:
        if _HAS_WHISPER and self._model is None and not self._load_error:
            # 不强制触发下载；available 表示"库可用"而非"模型已载入"
            return True
        return self._model is not None

    def status(self) -> EngineStatus:
        if not _HAS_WHISPER:
            return EngineStatus(
                engine=self.engine_name,
                available=False,
                detail="faster-whisper 未安装",
            )
        if self._load_error:
            return EngineStatus(
                engine=self.engine_name,
                available=False,
                detail=f"加载失败: {self._load_error}",
            )
        return EngineStatus(
            engine=self.engine_name,
            available=True,
            detail=(
                f"{_WHISPER_MODEL_SIZE}"
                if self._model is not None
                else f"{_WHISPER_MODEL_SIZE} (库已装，首次使用自动加载)"
            ),
        )

    def transcribe(self, audio_data: bytes) -> str:
        """音频字节 -> 文本（中文普通话）。"""

        self._ensure_model()

        if self._model is None:
            return "[STT unavailable: install faster-whisper]"

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            segments, _ = self._model.transcribe(
                tmp_path,
                language="zh",
            )
            return " ".join(s.text for s in segments).strip()
        except Exception as exc:
            return f"[STT error: {exc}]"
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def streaming_available(self) -> bool:
        """预留：实时流式 STT 接口。当前为一次性转写。"""

        return False


class CosyVoiceTTS:
    """服务器 TTS 引擎（CosyVoice，可选）。

    未安装 / 未配置模型目录 -> unavailable。
    安装后：输入文本 -> 返回 wav 音频字节。
    """

    engine_name = "cosyvoice"

    def __init__(self) -> None:
        self._model = None
        self._error = ""
        self._profile = None

        if not _HAS_COSYVOICE:
            self._error = "cosyvoice 未安装"
            return

        if not _COSYVOICE_MODEL_DIR:
            self._error = "XIAOQI_COSYVOICE_MODEL_DIR 未配置"
            return

        try:
            # CosyVoice 初始化较慢，延迟到首次 synthesize
            self._model_dir = Path(_COSYVOICE_MODEL_DIR)
        except Exception as exc:
            self._error = str(exc)

    @property
    def available(self) -> bool:
        return _HAS_COSYVOICE and bool(_COSYVOICE_MODEL_DIR)

    def status(self) -> EngineStatus:
        if not _HAS_COSYVOICE:
            return EngineStatus(
                engine=self.engine_name,
                available=False,
                detail="CosyVoice 未安装",
            )
        if not _COSYVOICE_MODEL_DIR:
            return EngineStatus(
                engine=self.engine_name,
                available=False,
                detail="XIAOQI_COSYVOICE_MODEL_DIR 未配置",
            )
        return EngineStatus(
            engine=self.engine_name,
            available=True,
            detail=_COSYVOICE_MODEL_DIR,
        )

    def synthesize(
        self,
        text: str,
        *,
        reference_audio: str | None = None,
    ) -> bytes:
        """文本 -> wav 音频字节。CosyVoice 不可用时抛 RuntimeError。"""

        if not self.available:
            raise RuntimeError(
                "CosyVoice unavailable: install cosyvoice and set "
                "XIAOQI_COSYVOICE_MODEL_DIR"
            )

        if not self._model:
            # 延迟初始化
            import cosyvoice
            from cosyvoice.cli.cosyvoice import CosyVoice as _CV

            self._model = _CV(_COSYVOICE_MODEL_DIR)

        audio_stream = self._model.inference_sft(
            text,
            self._model.sft_dict["中文女"],
        )

        buffer = io.BytesIO()
        for chunk in audio_stream:
            buffer.write(chunk)
        return buffer.getvalue()

    def streaming_available(self) -> bool:
        """预留：实时流式 TTS 接口。当前为整段生成。"""

        return False
