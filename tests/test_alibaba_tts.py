"""阿里云 Alibaba TTS Provider 测试（全部用 mock，不真实调用 API）。"""

import json
import urllib.error

import pytest

from voice.providers.alibaba_tts import (
    AlibabaTTSError,
    AlibabaTTS,
    AlibabaTTSConfig,
    AlibabaVoiceClone,
    _http_error,
)


# ---------------------------------------------------------
# AlibabaTTS
# ---------------------------------------------------------


def _config(**kw):
    base = dict(
        api_key="sk-test",
        voice="my-voice-id",
        region="singapore",
        model="qwen3-tts-flash",
    )
    base.update(kw)
    return AlibabaTTSConfig(**base)


def test_tts_available_only_with_key_and_voice():
    assert AlibabaTTS(_config()).available is True
    assert AlibabaTTS(_config(voice="")).available is False
    assert AlibabaTTS(_config(api_key="")).available is False


def test_tts_missing_api_key(monkeypatch):
    monkeypatch.delenv("XIAOQI_ALIBABA_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    tts = AlibabaTTS(AlibabaTTSConfig(voice="v", api_key=""))

    with pytest.raises(AlibabaTTSError) as exc:
        tts.synthesize("你好")
    assert exc.value.kind == "NO_API_KEY"


def test_tts_missing_voice_id():
    tts = AlibabaTTS(_config(voice=""))

    with pytest.raises(AlibabaTTSError) as exc:
        tts.synthesize("你好")
    assert exc.value.kind == "NO_VOICE_ID"


def _mock_urlopen_http_error(monkeypatch, code):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(
            request.full_url, code, "err", None, None,
        )

    monkeypatch.setattr(
        "voice.providers.alibaba_tts.urllib.request.urlopen",
        fake_urlopen,
    )


def test_tts_http_401(monkeypatch):
    _mock_urlopen_http_error(monkeypatch, 401)

    tts = AlibabaTTS(_config())

    with pytest.raises(AlibabaTTSError) as exc:
        tts.synthesize("你好")
    assert exc.value.kind == "UNAUTHORIZED"


def test_tts_http_403(monkeypatch):
    _mock_urlopen_http_error(monkeypatch, 403)

    with pytest.raises(AlibabaTTSError) as exc:
        AlibabaTTS(_config()).synthesize("你好")
    assert exc.value.kind == "FORBIDDEN"


def test_tts_http_429(monkeypatch):
    _mock_urlopen_http_error(monkeypatch, 429)

    with pytest.raises(AlibabaTTSError) as exc:
        AlibabaTTS(_config()).synthesize("你好")
    assert exc.value.kind == "RATE_LIMITED"


def test_tts_http_500(monkeypatch):
    _mock_urlopen_http_error(monkeypatch, 500)

    with pytest.raises(AlibabaTTSError) as exc:
        AlibabaTTS(_config()).synthesize("你好")
    assert exc.value.kind == "HTTP_ERROR"


def test_tts_timeout(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise TimeoutError("timeout")

    monkeypatch.setattr(
        "voice.providers.alibaba_tts.urllib.request.urlopen",
        fake_urlopen,
    )

    with pytest.raises(AlibabaTTSError) as exc:
        AlibabaTTS(_config()).synthesize("你好")
    assert exc.value.kind == "TIMEOUT"


def test_tts_api_error_no_audio_url(monkeypatch):
    def fake_post(url, key, payload, **kw):
        return {"code": "InvalidParameter", "message": "bad voice"}

    monkeypatch.setattr(
        "voice.providers.alibaba_tts._post_json",
        fake_post,
    )

    with pytest.raises(AlibabaTTSError) as exc:
        AlibabaTTS(_config()).synthesize("你好")
    assert exc.value.kind == "API_ERROR"


def test_tts_success_returns_audio(monkeypatch):
    sent = {}

    def fake_post(url, key, payload, **kw):
        sent["url"] = url
        sent["payload"] = payload
        return {
            "output": {
                "audio": {"url": "https://audio.test/a.wav"},
            }
        }

    def fake_download(url, timeout):
        return b"RIFF........WAVE"

    monkeypatch.setattr(
        "voice.providers.alibaba_tts._post_json",
        fake_post,
    )
    monkeypatch.setattr(
        "voice.providers.alibaba_tts.AlibabaTTS._download",
        staticmethod(fake_download),
    )

    audio = AlibabaTTS(_config()).synthesize("你好呀")

    assert audio == b"RIFF........WAVE"
    assert "generation" in sent["url"]
    assert "dashscope" in sent["url"]
    assert sent["payload"]["input"]["text"] == "你好呀"
    assert sent["payload"]["input"]["voice"] == "my-voice-id"
    assert sent["payload"]["input"]["language_type"] == "Chinese"
    assert sent["payload"]["model"] == "qwen3-tts-flash"


def test_tts_streaming_not_available():
    assert AlibabaTTS(_config()).streaming_available() is False


# ---------------------------------------------------------
# Voice Clone
# ---------------------------------------------------------


def test_clone_not_configured():
    clone = AlibabaVoiceClone(api_key="")
    assert clone.configured is False


def test_clone_configured_requires_key():
    assert AlibabaVoiceClone(api_key="k").configured is True
    assert AlibabaVoiceClone(api_key="").configured is False


def test_clone_missing_key():
    clone = AlibabaVoiceClone(api_key="")
    with pytest.raises(AlibabaTTSError) as exc:
        clone._endpoint()
    assert exc.value.kind == "NO_API_KEY"


def test_clone_create_success(monkeypatch):
    sent = {}

    def fake_post(url, key, payload, **kw):
        sent["payload"] = payload
        sent["url"] = url
        return {"output": {"voice": "xiaoqiVoice"}}

    monkeypatch.setattr(
        "voice.providers.alibaba_tts._post_json",
        fake_post,
    )

    clone = AlibabaVoiceClone(api_key="k")

    voice_id = clone.create_voice(
        audio_wav=b"\x00\x01WAVE",
        preferred_name="xiaoqi",
    )

    assert voice_id == "xiaoqiVoice"
    assert sent["payload"]["model"] == "qwen-voice-enrollment"
    assert sent["payload"]["input"]["action"] == "create"
    assert sent["payload"]["input"]["preferred_name"] == "xiaoqi"
    # 使用 dashscope 域名，无需 workspace
    assert "dashscope" in sent["url"]
    assert "customization" in sent["url"]


def test_clone_create_failure(monkeypatch):
    def fake_post(url, key, payload, **kw):
        return {"output": {}}

    monkeypatch.setattr(
        "voice.providers.alibaba_tts._post_json",
        fake_post,
    )

    clone = AlibabaVoiceClone(api_key="k")

    with pytest.raises(AlibabaTTSError) as exc:
        clone.create_voice(audio_wav=b"x", preferred_name="xiaoqi")
    assert exc.value.kind == "CLONE_FAILED"


# ---------------------------------------------------------
# _http_error 映射
# ---------------------------------------------------------


def test_http_error_mapping():
    err = urllib.error.HTTPError("u", 401, "", None, None)
    assert _http_error(err).kind == "UNAUTHORIZED"

    err = urllib.error.HTTPError("u", 403, "", None, None)
    assert _http_error(err).kind == "FORBIDDEN"

    err = urllib.error.HTTPError("u", 429, "", None, None)
    assert _http_error(err).kind == "RATE_LIMITED"
