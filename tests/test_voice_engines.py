import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from voice.engines import CosyVoiceTTS, STTEngine
from voice.profile import (
    VoiceProfile,
    load_profile,
)
from voice.status import build_voice_status


def test_stt_engine_unavailable_when_no_whisper():
    engine = STTEngine()
    status = engine.status()

    assert status.engine == "faster-whisper"
    assert status.available is False
    assert status.detail

    text = engine.transcribe(b"\x00\x01\x00\x01")
    assert "unavailable" in text or "error" in text


def test_stt_engine_streaming_not_available():
    engine = STTEngine()
    assert engine.streaming_available() is False


def test_tts_engine_unavailable_when_no_cosyvoice():
    engine = CosyVoiceTTS()
    status = engine.status()

    assert status.engine == "cosyvoice"
    assert status.available is False

    with pytest.raises(RuntimeError):
        engine.synthesize("你好")


def test_tts_streaming_not_available():
    engine = CosyVoiceTTS()
    assert engine.streaming_available() is False


def test_load_nonexistent_profile_returns_none():
    assert load_profile("nonexistent_profile_name") is None


def test_load_default_profile():
    profile = load_profile("xiaoqi")

    assert profile is not None
    assert profile.name == "xiaoqi"
    assert profile.language == "zh"
    assert profile.speed == 1.0
    assert profile.pitch == 1.0


def test_profile_to_dict_and_has_reference():
    profile = VoiceProfile(
        name="xiaoqi",
        reference_audio="reference.wav",
    )

    data = profile.to_dict()
    assert data["name"] == "xiaoqi"
    assert data["has_reference"] is True

    no_ref = VoiceProfile(name="xiaoqi")
    assert no_ref.to_dict()["has_reference"] is False


def test_profile_from_dict_defaults():
    profile = VoiceProfile.from_dict({"name": "test"})

    assert profile.name == "test"
    assert profile.engine == "cosyvoice"
    assert profile.language == "zh"
