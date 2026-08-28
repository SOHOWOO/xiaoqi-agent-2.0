"""小七 · 语音系统真实状态（/api/voice/status）。"""

from __future__ import annotations

from .engines import CosyVoiceTTS, STTEngine
from .profile import get_active_profile


def build_voice_status(
    stt: STTEngine | None = None,
    tts: CosyVoiceTTS | None = None,
) -> dict:
    """根据实际环境返回语音状态，不写死。"""

    stt_engine = stt or STTEngine()
    tts_engine = tts or CosyVoiceTTS()

    profile = get_active_profile()

    return {
        "stt": stt_engine.status().to_dict(),
        "tts": tts_engine.status().to_dict(),
        "voice_profile": (
            profile.name if profile is not None else None
        ),
        "streaming": {
            "stt": stt_engine.streaming_available(),
            "tts": tts_engine.streaming_available(),
        },
    }
