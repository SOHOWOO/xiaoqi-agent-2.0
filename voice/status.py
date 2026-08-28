"""小七 · 语音系统真实状态（/api/voice/status）。"""

from __future__ import annotations

import os

from .engines import CosyVoiceTTS, STTEngine
from .profile import get_active_profile
from .providers.alibaba_tts import (
    AlibabaVoiceClone,
    load_tts_config,
)


def _tts_status() -> dict:
    """按 XIAOQI_TTS_PROVIDER 选择状态来源（真实检测，不写死）。"""

    provider = os.getenv("XIAOQI_TTS_PROVIDER", "alibaba")

    if provider == "alibaba":
        config = load_tts_config()
        return {
            "provider": "alibaba",
            "available": bool(config.api_key and config.voice),
            "has_api_key": bool(config.api_key),
            "has_voice_id": bool(config.voice),
            "model": config.model if config.api_key else "",
            "streaming": False,
        }

    if provider == "cosyvoice":
        status = CosyVoiceTTS().status()
        return {
            "provider": "cosyvoice",
            "available": status.available,
            "detail": status.detail,
            "streaming": False,
        }

    # browser 或未知 -> 由前端决定，后端标记 browser
    return {
        "provider": "browser",
        "available": False,
        "streaming": False,
    }


def _voice_clone_status() -> dict:
    """声音克隆状态：只有 API Key + Workspace 都配置才 configured。"""

    clone = AlibabaVoiceClone()
    return {
        "provider": "alibaba",
        "configured": clone.configured,
        "has_api_key": clone.api_key != "",
        "has_workspace_id": clone.workspace_id != "",
    }


def build_voice_status(
    stt: STTEngine | None = None,
) -> dict:
    """根据实际环境返回语音状态，不写死。"""

    stt_engine = stt or STTEngine()

    profile = get_active_profile()

    return {
        "stt": {
            "provider": stt_engine.engine_name,
            "available": stt_engine.available,
            "detail": stt_engine.status().detail,
            "streaming": stt_engine.streaming_available(),
        },
        "tts": _tts_status(),
        "voice_clone": _voice_clone_status(),
        "voice_profile": (
            profile.name if profile is not None else None
        ),
    }
